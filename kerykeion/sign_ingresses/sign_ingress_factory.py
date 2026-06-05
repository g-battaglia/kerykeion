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

from kerykeion.ephemeris_backend import swe, EPHE_DATA_PATH, EPHEMERIS_LOCK

from kerykeion.schemas.kr_models import SubscriptableBaseModel
from kerykeion.utilities import (
    datetime_to_julian,
    get_kerykeion_point_from_degree,
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
# Backstop on samples per scan (~2700 years at the default step). Ranges that
# would exceed it are rejected explicitly rather than silently truncated.
_MAX_SAMPLES = 2_000_000
# A planet can cross a boundary, station, and cross back within one sampling
# interval (both endpoints in the same sign). When the midpoint reveals a hidden
# sign, the interval is subdivided down to this resolution to catch both hits.
_MIN_SEGMENT_DAYS = 1.0 / 96.0  # 15 minutes
_MAX_SUBDIVISION_DEPTH = 8


def _to_utc_naive(dt: datetime) -> datetime:
    """Normalize an offset-aware datetime to naive UTC (see lunation factory)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _jd_to_iso(jd: float) -> str:
    """Convert a Julian Day (UT) to an ISO 8601 UTC string with seconds.

    Uses ``swe.revjul`` rather than Python ``datetime`` (limited to years
    1..9999) so the BCE range Kerykeion supports formats correctly, with an
    extended-year sign for negative years.
    """
    year, month, day, hour_frac = swe.revjul(jd)
    secs = min(int(hour_frac * 3600 + 0.5), 86399)  # nearest second, no 24:00 carry
    hours, rem = divmod(secs, 3600)
    minutes, seconds = divmod(rem, 60)
    year_str = f"-{abs(year):04d}" if year < 0 else f"{year:04d}"
    return f"{year_str}-{month:02d}-{day:02d}T{hours:02d}:{minutes:02d}:{seconds:02d}Z"


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


def _ensure_scannable(start_jd: float, end_jd: float) -> None:
    """Reject ranges too long to scan, so a caller never receives a silently
    truncated result whose ``end_jd`` still claims the full requested range."""
    if (end_jd - start_jd) / _SAMPLE_STEP_DAYS > _MAX_SAMPLES:
        raise ValueError(
            f"Date range too large to scan at the current resolution "
            f"(> {_MAX_SAMPLES} samples). Narrow the date range."
        )


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
        # A date-only end_date means "through the end of that UTC day". Check for
        # both T/t (fromisoformat accepts a lowercase 't') and a space separator.
        if "T" not in end_date and "t" not in end_date and " " not in end_date:
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
        # None = default set; an explicit empty list = scan nothing.
        if planets is not None:
            invalid = sorted(set(planets) - set(_PLANET_IDS))
            if invalid:
                raise ValueError(
                    f"Unknown planets: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_PLANET_IDS)}"
                )
            # Deduplicate (preserve order): duplicates would repeat the scan and
            # emit every event multiple times.
            bodies = [(name, _PLANET_IDS[name]) for name in dict.fromkeys(planets)]
        else:
            bodies = list(_INGRESS_PLANETS)

        ingresses: List[IngressModel] = []
        if end_jd > start_jd and bodies:
            _ensure_scannable(start_jd, end_jd)
            # Hold the lock across the whole scan: set_ephe_path / calc_ut / close
            # mutate process-global backend state shared with chart calculations.
            with EPHEMERIS_LOCK:
                swe.set_ephe_path(_EPHE_PATH)
                try:
                    for name, body in bodies:
                        ingresses.extend(
                            SignIngressFactory._scan_planet(name, body, start_jd, end_jd)
                        )
                finally:
                    swe.close()
            ingresses.sort(key=lambda i: i.julian_day)

        return SignIngressesCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            ingresses=ingresses,
        )

    @staticmethod
    def _scan_planet(
        name: str, body: int, start_jd: float, end_jd: float
    ) -> List[IngressModel]:
        """Walk the range for one planet, emitting every sign-boundary crossing."""
        found: List[IngressModel] = []
        jd = start_jd
        prev_sign = int(_lon(jd, body) // 30)
        while jd < end_jd:
            jd_next = min(jd + _SAMPLE_STEP_DAYS, end_jd)
            cur_sign = int(_lon(jd_next, body) // 30)
            SignIngressFactory._emit_segment(name, body, jd, prev_sign, jd_next, cur_sign, found, 0)
            prev_sign = cur_sign
            jd = jd_next
        return found

    @staticmethod
    def _emit_segment(
        name: str,
        body: int,
        a: float,
        sign_a: int,
        b: float,
        sign_b: int,
        found: List[IngressModel],
        depth: int,
    ) -> None:
        """Emit ingresses within ``[a, b]``, subdividing to catch crossings the
        endpoints hide (a forward + retrograde re-crossing inside one interval)."""
        if sign_a == sign_b:
            # Equal endpoints can still hide a there-and-back excursion across a
            # boundary near a station. Probe the midpoint; if it sits in another
            # sign, two crossings are hidden here — recurse into both halves.
            if depth >= _MAX_SUBDIVISION_DEPTH or (b - a) <= _MIN_SEGMENT_DAYS:
                return
            mid = (a + b) / 2.0
            sign_mid = int(_lon(mid, body) // 30)
            if sign_mid != sign_a:
                SignIngressFactory._emit_segment(name, body, a, sign_a, mid, sign_mid, found, depth + 1)
                SignIngressFactory._emit_segment(name, body, mid, sign_mid, b, sign_b, found, depth + 1)
            return

        diff = (sign_b - sign_a) % 12
        if diff != 1 and diff != 11 and depth < _MAX_SUBDIVISION_DEPTH and (b - a) > _MIN_SEGMENT_DAYS:
            # More than one boundary between the endpoints (a fast body, or a
            # multi-crossing interval): split so each half resolves one boundary.
            mid = (a + b) / 2.0
            sign_mid = int(_lon(mid, body) // 30)
            SignIngressFactory._emit_segment(name, body, a, sign_a, mid, sign_mid, found, depth + 1)
            SignIngressFactory._emit_segment(name, body, mid, sign_mid, b, sign_b, found, depth + 1)
            return

        # Adjacent signs: a single boundary. diff==1 is forward (top of sign_a),
        # diff==11 is retrograde (bottom of sign_a).
        retro = diff == 11
        boundary = ((sign_a * 30) if retro else ((sign_a + 1) * 30)) % 360.0
        jd_ingress = _bisect_ingress(body, a, b, boundary)
        found.append(
            SignIngressFactory._build(name, jd_ingress, sign_a, sign_b, retro, boundary)
        )

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
