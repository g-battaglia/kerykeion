# -*- coding: utf-8 -*-
"""Find zodiac sign ingresses (a planet crossing a 30° boundary) over a range.

An *ingress* is the instant a body crosses from one zodiac sign into the next —
its ecliptic longitude passes a multiple of 30°. A retrograde planet near a sign
boundary can cross it more than once (forward, back, forward); each crossing is a
real ingress and is reported.

``cross_ut`` (libephemeris) targets a fixed longitude directly, but it is absent
on the swisseph backend, so — like ``LunationFinderFactory`` — this stays
backend-agnostic: it samples longitude via ``swe.calc_ut`` across the range and,
whenever the sign index changes between two samples, bisects to the exact 30°
crossing. The half-day step keeps even the Moon (~13°/day) below one sign per
step, so no boundary is skipped.

Swiss Ephemeris / libephemeris functions used:
    - swe.calc_ut(jd, planet_id, FLG_SWIEPH)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH

from kerykeion.schemas.kr_models import SubscriptableBaseModel
from kerykeion.utilities import (
    datetime_to_julian,
    get_kerykeion_point_from_degree,
    julian_to_datetime,
)
from pydantic import Field

logger = logging.getLogger(__name__)

_EPHE_PATH = EPHE_DATA_PATH

# Default set: Sun..Pluto. The Moon is opt-in — ~13 ingresses/month is noise for
# most use cases — but accepted when explicitly requested. Names match
# kerykeion's AstrologicalPoint vocabulary.
_INGRESS_PLANETS: List[tuple[str, int]] = [
    ("Sun", swe.SUN),
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
]

# Valid request vocabulary includes the Moon (opt-in).
_PLANET_IDS = {name: pid for name, pid in _INGRESS_PLANETS}
_PLANET_IDS["Moon"] = swe.MOON

# Sampling step (days). The Moon (~13°/day) advances < 7° per half-day, so a sign
# (30°) is never jumped; slower bodies have ample margin.
_SAMPLE_STEP_DAYS = 0.5
_BISECTION_ITERS = 40
# Runaway guard (≈ 270 years at the default step).
_MAX_SAMPLES = 200_000


def _to_utc_naive(dt: datetime) -> datetime:
    """Normalize an offset-aware datetime to naive UTC (see lunation factory)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _jd_to_iso(jd: float) -> str:
    """Convert a Julian Day (UT) to an ISO 8601 UTC string with seconds."""
    try:
        dt = julian_to_datetime(jd)
        return (
            f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
            f"T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}Z"
        )
    except Exception:  # pragma: no cover - defensive
        return ""


def _ang_diff(a: float, b: float) -> float:
    """Signed smallest angular difference ``a - b`` in ``(-180, 180]``."""
    return ((a - b + 180.0) % 360.0) - 180.0


def _lon(jd: float, body: int) -> float:
    """Ecliptic longitude (deg, 0-360) of ``body`` at ``jd``."""
    return float(swe.calc_ut(jd, body, swe.FLG_SWIEPH)[0][0]) % 360.0


def _sign_name(sign_num: int) -> str:
    """Zodiac sign name for an index (0=Aries), via the shared degree helper."""
    return get_kerykeion_point_from_degree(
        (sign_num % 12) * 30 + 15, "Sun", "AstrologicalPoint"
    ).sign


def _bisect_ingress(body: int, a: float, b: float, boundary: float) -> float:
    """Bisect ``[a, b]`` to the JD where longitude equals the 30° ``boundary``."""
    fa = _ang_diff(_lon(a, body), boundary)
    for _ in range(_BISECTION_ITERS):
        mid = (a + b) / 2.0
        fm = _ang_diff(_lon(mid, body), boundary)
        if fm == 0.0:
            return mid
        if (fa < 0.0) != (fm < 0.0):
            b = mid
        else:
            a, fa = mid, fm
    return (a + b) / 2.0


# =============================================================================
# MODELS
# =============================================================================


class IngressModel(SubscriptableBaseModel):
    """A single zodiac sign ingress (30° boundary crossing)."""

    planet: str = Field(description="Planet name (kerykeion AstrologicalPoint vocabulary)")
    julian_day: float = Field(description="Julian Day (UT) of the exact ingress")
    iso_utc: str = Field(description="ISO 8601 UTC datetime of the exact ingress")
    sign: str = Field(description="Sign being entered")
    sign_num: int = Field(description="Entered sign number (0=Aries)")
    from_sign: str = Field(description="Sign being left")
    from_sign_num: int = Field(description="Left sign number (0=Aries)")
    retrograde: bool = Field(description="True if the ingress occurs in retrograde motion")
    ecliptic_longitude: float = Field(description="The 30° boundary crossed (0-360)")


class SignIngressesCollectionModel(SubscriptableBaseModel):
    """Ordered list of sign ingresses within a Julian Day range."""

    start_jd: float
    end_jd: float
    ingresses: List[IngressModel]


# =============================================================================
# FACTORY
# =============================================================================


class SignIngressFactory:
    """Find zodiac sign ingresses within a date range, ordered chronologically.

    Example:
        >>> from kerykeion import SignIngressFactory
        >>> result = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31")
        >>> result.ingresses[0].planet, result.ingresses[0].sign
    """

    @staticmethod
    def from_iso_range(
        start_date: str,
        end_date: str,
        planets: Optional[List[str]] = None,
    ) -> SignIngressesCollectionModel:
        """Find ingresses between two ISO date(time) strings (treated as UTC).

        Args:
            start_date: ISO date or datetime, e.g. ``"2026-01-01"``.
            end_date: ISO date or datetime, e.g. ``"2026-12-31"``.
            planets: Optional subset of planet names. Defaults to Sun..Pluto
                (Moon excluded unless explicitly requested).
        """
        start_dt = _to_utc_naive(datetime.fromisoformat(start_date))
        end_dt = _to_utc_naive(datetime.fromisoformat(end_date))
        # A date-only end_date means "through the end of that UTC day".
        if "T" not in end_date and " " not in end_date:
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_jd = datetime_to_julian(start_dt)
        end_jd = datetime_to_julian(end_dt)
        return SignIngressFactory.from_julian_day(start_jd, end_jd, planets)

    @staticmethod
    def from_julian_day(
        start_jd: float,
        end_jd: float,
        planets: Optional[List[str]] = None,
    ) -> SignIngressesCollectionModel:
        """Find all sign ingresses in ``[start_jd, end_jd]``, ordered chronologically.

        Args:
            start_jd: Julian Day (UT) range start.
            end_jd: Julian Day (UT) range end.
            planets: Optional subset of planet names. Defaults to Sun..Pluto.
        """
        if planets:
            invalid = sorted(set(planets) - set(_PLANET_IDS))
            if invalid:
                raise ValueError(
                    f"Unknown planets: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_PLANET_IDS)}"
                )
            bodies = [(name, _PLANET_IDS[name]) for name in planets]
        else:
            bodies = list(_INGRESS_PLANETS)

        swe.set_ephe_path(_EPHE_PATH)
        ingresses: List[IngressModel] = []

        if end_jd > start_jd:
            for name, body in bodies:
                ingresses.extend(
                    SignIngressFactory._scan_planet(name, body, start_jd, end_jd)
                )
            ingresses.sort(key=lambda i: i.julian_day)

        swe.close()
        return SignIngressesCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            ingresses=ingresses,
        )

    @staticmethod
    def _scan_planet(
        name: str, body: int, start_jd: float, end_jd: float
    ) -> List[IngressModel]:
        """Walk the range for one planet, bisecting each sign-index change."""
        found: List[IngressModel] = []
        jd = start_jd
        prev_lon = _lon(jd, body)
        prev_sign = int(prev_lon // 30)
        samples = 0
        while jd < end_jd and samples < _MAX_SAMPLES:
            jd_next = min(jd + _SAMPLE_STEP_DAYS, end_jd)
            cur_lon = _lon(jd_next, body)
            cur_sign = int(cur_lon // 30)
            if cur_sign != prev_sign:
                # Direction over the step decides which boundary was crossed:
                # forward (delta>0) crosses the top of prev_sign, retrograde the
                # bottom. The half-day step guarantees a single boundary here.
                retro = _ang_diff(cur_lon, prev_lon) < 0.0
                boundary = ((prev_sign * 30) if retro else ((prev_sign + 1) * 30)) % 360.0
                jd_ingress = _bisect_ingress(body, jd, jd_next, boundary)
                found.append(
                    SignIngressFactory._build(
                        name, jd_ingress, prev_sign, cur_sign, retro, boundary
                    )
                )
            prev_lon, prev_sign = cur_lon, cur_sign
            jd = jd_next
            samples += 1
        return found

    @staticmethod
    def _build(
        name: str,
        jd: float,
        from_sign_num: int,
        to_sign_num: int,
        retro: bool,
        boundary: float,
    ) -> IngressModel:
        """Build an IngressModel for a boundary crossing at ``jd``."""
        return IngressModel(
            planet=name,
            julian_day=jd,
            iso_utc=_jd_to_iso(jd),
            sign=_sign_name(to_sign_num),
            sign_num=to_sign_num % 12,
            from_sign=_sign_name(from_sign_num),
            from_sign_num=from_sign_num % 12,
            retrograde=retro,
            ecliptic_longitude=round(boundary, 6),
        )
