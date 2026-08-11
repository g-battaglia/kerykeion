# -*- coding: utf-8 -*-
"""Find zodiac sign ingresses (a planet crossing a 30° boundary) over a range.

An *ingress* is the instant a body crosses from one zodiac sign into the next —
its ecliptic longitude passes a multiple of 30°. A retrograde planet near a sign
boundary can cross it more than once (forward, back, forward); each crossing is a
real ingress and is reported.

``cross_ut`` (libephemeris) targets a fixed longitude directly, but it is absent
on the swisseph backend, so — like ``LunationFinderFactory`` — this stays
backend-agnostic: it samples longitude via ``ephe.calc_ut`` across the range and,
whenever the sign index changes between two samples, bisects to the exact 30°
crossing. The per-planet step (see ``_PLANET_STEP_DAYS``) keeps every body well
below one sign per step, so no boundary is skipped.

Swiss Ephemeris / libephemeris functions used:
    - ephe.calc_ut(jd, planet_id, FLG_SWIEPH)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional

from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion.settings.config_constants import POINT_NUMBER_MAP
from kerykeion.predictive.utils import is_iso_date_only, jd_to_iso_utc as _jd_to_iso, validate_julian_bounds

from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.literals import SiderealMode, ZodiacType
from kerykeion.schemas.models import SubscriptableBaseModel
from kerykeion.utilities import (
    datetime_to_julian,
    get_kerykeion_point_from_degree,
    wrap_180,
)
from pydantic import Field

logger = logging.getLogger(__name__)

# Default set: Sun..Pluto. The Moon is opt-in — ~13 ingresses/month is noise for
# most use cases — but accepted when explicitly requested. Names match
# kerykeion's AstrologicalPoint vocabulary.
_INGRESS_PLANETS: List[tuple[str, int]] = [
    (name, POINT_NUMBER_MAP[name])
    for name in ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
]

# Valid request vocabulary includes the Moon (opt-in).
_PLANET_IDS = {name: pid for name, pid in _INGRESS_PLANETS}
_PLANET_IDS["Moon"] = ephe.MOON

# Sampling step (days), sized per planet. Two constraints: (a) never jump a
# whole sign at peak speed (trivially satisfied — even Mercury moves < 7°/step),
# and (b) never outrun a there-and-back boundary excursion near a station: an
# excursion penetrating δ degrees past a boundary lasts ~2*sqrt(2δ/accel), so
# with step ≤ that duration a sampled endpoint lands inside the excursion and
# the sign change is seen directly. The steps below keep the guaranteed-catch
# penetration threshold at or below the old uniform half-day step's (~0.003°
# for Mercury): slower bodies accelerate away from stations far more gently, so
# their excursions last days-to-weeks and tolerate much coarser sampling.
# Unlisted bodies fall back to the Moon-safe half-day step.
_SAMPLE_STEP_DAYS = 0.5
_PLANET_STEP_DAYS = {
    "Moon": 0.5,      # ~13°/day, never retrograde excursions but fast
    "Sun": 3.0,       # ~1°/day, never retrogrades
    "Mercury": 0.5,   # station accel ~0.1°/day² — excursions can last hours
    "Venus": 1.0,     # station accel ~0.02°/day²
    "Mars": 2.0,      # station accel ~0.007°/day²
    "Jupiter": 4.0,   # station accel ~0.0025°/day²
    "Saturn": 5.0,    # station accel ~0.0011°/day²
    "Uranus": 7.0,    # station accel ~0.0006°/day²
    "Neptune": 7.0,
    "Pluto": 7.0,
}
# Bisection to ~0.02 s on the widest (7-day) bracket — the ISO output is
# rounded to the second, so further halvings buy nothing.
_BISECTION_ITERS = 27
# Backstop on per-planet samples per scan (~2700 years at the finest half-day
# step, proportionally longer for slow-body-only requests). Ranges that would
# exceed it are rejected explicitly rather than silently truncated.
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


def _validate_zodiac(zodiac_type: ZodiacType, sidereal_mode: Optional[SiderealMode]) -> None:
    """Validate the zodiac configuration before opening an ephemeris session.

    Same contract as ``VoidOfCourseMoonFactory``'s validator: pure validation,
    no global ephemeris state touched.
    """
    if zodiac_type not in ("Tropical", "Sidereal"):
        raise KerykeionException(f"Unknown zodiac_type: {zodiac_type!r} (expected 'Tropical' or 'Sidereal').")

    if zodiac_type == "Sidereal":
        if sidereal_mode is None:
            raise KerykeionException("sidereal_mode is required when zodiac_type='Sidereal'.")
        if sidereal_mode == "USER":
            raise KerykeionException(
                "sidereal_mode='USER' requires custom ayanamsha parameters, which SignIngressFactory does not accept."
            )
        if not hasattr(ephe, f"SIDM_{sidereal_mode}"):
            raise KerykeionException(f"Unknown sidereal_mode: {sidereal_mode!r}.")


def _ang_diff(a: float, b: float) -> float:
    """Signed smallest angular difference ``a - b`` in ``[-180, 180)``."""
    return wrap_180(a - b)


def _lon(jd: float, body: int, iflag: int) -> float:
    """Ecliptic longitude (deg, 0-360) of ``body`` at ``jd`` in the session frame.

    ``iflag`` carries the enclosing session's zodiac (``FLG_SIDEREAL`` for a
    sidereal scan), so the sampled longitude — and hence every sign boundary
    the scan bisects — is expressed in the requested frame. A sidereal scan's
    30° boundaries sit ~24° (one ayanamsha) away from the tropical ones, so the
    ingress TIMES legitimately shift.
    """
    try:
        return float(ephe.calc_ut(jd, body, iflag)[0][0]) % 360.0
    except Exception as exc:
        # Range errors (libephemeris EphemerisRangeError, swisseph.Error)
        # propagate raw from calc_ut — normalize them to the documented
        # exception type, like the lunation factory does.
        raise KerykeionException(
            f"Sign ingress search failed at JD {jd:.5f}: {exc}. This usually "
            f"means the date falls outside the available ephemeris range; "
            f"narrow the date range."
        ) from exc


def _sign_name(sign_num: int) -> str:
    """Zodiac sign name for an index (0=Aries), via the shared degree helper."""
    return get_kerykeion_point_from_degree(
        (sign_num % 12) * 30 + 15, "Sun", "AstrologicalPoint"
    ).sign


def _bisect_ingress(body: int, a: float, b: float, boundary: float, iflag: int) -> float:
    """Bisect ``[a, b]`` to the JD where longitude equals the 30° ``boundary``."""
    fa = _ang_diff(_lon(a, body, iflag), boundary)
    for _ in range(_BISECTION_ITERS):
        mid = (a + b) / 2.0
        fm = _ang_diff(_lon(mid, body, iflag), boundary)
        if fm == 0.0:
            return mid
        if (fa < 0.0) != (fm < 0.0):
            b = mid
        else:
            a, fa = mid, fm
    return (a + b) / 2.0


def _ensure_scannable(start_jd: float, end_jd: float, bodies: List[tuple[str, int]]) -> None:
    """Reject ranges too long to scan, so a caller never receives a silently
    truncated result whose ``end_jd`` still claims the full requested range.

    The bound follows the finest per-planet step actually requested: a
    slow-bodies-only scan costs 6-14x less per year than a Moon/Mercury scan
    and is admitted accordingly.
    """
    finest_step = min(
        (_PLANET_STEP_DAYS.get(name, _SAMPLE_STEP_DAYS) for name, _ in bodies),
        default=_SAMPLE_STEP_DAYS,
    )
    if (end_jd - start_jd) / finest_step > _MAX_SAMPLES:
        raise ValueError(
            f"Date range too large to scan at the current resolution "
            f"(> {_MAX_SAMPLES} samples). Narrow the date range."
        )


# =============================================================================
# MODELS
# =============================================================================


SeasonMarker = Literal["march_equinox", "june_solstice", "september_equinox", "december_solstice"]

# Sun crossing a cardinal (tropical) boundary IS the astronomical season
# definition. Month-based names stay hemisphere-neutral — "march_equinox" is
# spring in the north and autumn in the south; consumers localize.
_SEASON_MARKERS: dict[float, SeasonMarker] = {
    0.0: "march_equinox",
    90.0: "june_solstice",
    180.0: "september_equinox",
    270.0: "december_solstice",
}


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
    season_marker: Optional[SeasonMarker] = Field(
        default=None,
        description=(
            "Set on Sun ingresses at the cardinal boundaries (0/90/180/270°): "
            "the equinox/solstice this ingress marks. Hemisphere-neutral names."
        ),
    )


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
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> SignIngressesCollectionModel:
        """Find ingresses between two ISO date(time) strings (treated as UTC).

        Args:
            start_date: ISO date or datetime, e.g. ``"2026-01-01"``.
            end_date: ISO date or datetime, e.g. ``"2026-12-31"``.
            planets: Optional subset of planet names. Defaults to Sun..Pluto
                (Moon excluded unless explicitly requested).
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. A sidereal
                scan reports sidereal signs and its ingress TIMES shift (the
                boundary is ~24° away); ``season_marker`` is tropical-only and
                is ``None`` on every sidereal ingress.
            sidereal_mode: Ayanamsha when ``zodiac_type='Sidereal'``.
        """
        try:
            start_dt = _to_utc_naive(datetime.fromisoformat(start_date))
            end_dt = _to_utc_naive(datetime.fromisoformat(end_date))
        except (ValueError, TypeError) as exc:
            # Wrap the bare datetime error as the library's own exception, so a
            # caller catching KerykeionException around this entry point is not
            # broken by a malformed ISO start_date/end_date. Same contract as
            # LunationFinderFactory.from_iso_range.
            raise KerykeionException(
                f"Invalid ISO date/datetime for ingress range "
                f"(start_date={start_date!r}, end_date={end_date!r}): {exc}"
            ) from exc
        # Parse as a date so every valid datetime separator remains exact.
        if is_iso_date_only(end_date):
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_jd = datetime_to_julian(start_dt)
        end_jd = datetime_to_julian(end_dt)
        return SignIngressFactory.from_julian_day(start_jd, end_jd, planets, zodiac_type, sidereal_mode)

    @staticmethod
    def from_julian_day(
        start_jd: float,
        end_jd: float,
        planets: Optional[List[str]] = None,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> SignIngressesCollectionModel:
        """Find all sign ingresses in ``[start_jd, end_jd]``, ordered chronologically.

        Args:
            start_jd: Julian Day (UT) range start.
            end_jd: Julian Day (UT) range end.
            planets: Optional subset of planet names. Defaults to Sun..Pluto.
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. Sidereal
                ingress TIMES shift with the ayanamsha; ``season_marker`` is
                tropical-only.
            sidereal_mode: Ayanamsha when ``zodiac_type='Sidereal'``.

        Raises:
            KerykeionException: For an invalid zodiac configuration, or if the
                ephemeris backend fails mid-scan (most often a date outside the
                available ephemeris range); the scan never returns silently
                truncated results.
            ValueError: If a planet name is unknown, either Julian bound is
                non-finite, or the range is too large to scan.
        """
        validate_julian_bounds(start_jd, end_jd)

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

        _validate_zodiac(zodiac_type, sidereal_mode)
        # season_marker is meaningful ONLY in the tropical frame: the Sun
        # crossing a SIDEREAL cardinal boundary is not the equinox/solstice.
        tropical = zodiac_type != "Sidereal"

        ingresses: List[IngressModel] = []
        if end_jd > start_jd and bodies:
            _ensure_scannable(start_jd, end_jd, bodies)
            # The session holds the ephemeris lock across the whole scan (calc_ut
            # reads process-global backend state shared with chart calculations)
            # and resets that state on exit without degrading the backend. Its
            # iflag carries FLG_SIDEREAL for a sidereal scan.
            with ephemeris_session(zodiac_type=zodiac_type, sidereal_mode=sidereal_mode) as iflag:
                for name, body in bodies:
                    ingresses.extend(
                        SignIngressFactory._scan_planet(name, body, start_jd, end_jd, iflag, tropical)
                    )
            ingresses.sort(key=lambda i: i.julian_day)

        return SignIngressesCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            ingresses=ingresses,
        )

    @staticmethod
    def _scan_planet(
        name: str, body: int, start_jd: float, end_jd: float, iflag: int, tropical: bool
    ) -> List[IngressModel]:
        """Walk the range for one planet, emitting every sign-boundary crossing."""
        found: List[IngressModel] = []
        step = _PLANET_STEP_DAYS.get(name, _SAMPLE_STEP_DAYS)
        jd = start_jd
        prev_sign = int(_lon(jd, body, iflag) // 30)
        while jd < end_jd:
            jd_next = min(jd + step, end_jd)
            cur_sign = int(_lon(jd_next, body, iflag) // 30)
            SignIngressFactory._emit_segment(name, body, jd, prev_sign, jd_next, cur_sign, found, 0, iflag, tropical)
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
        iflag: int,
        tropical: bool,
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
            sign_mid = int(_lon(mid, body, iflag) // 30)
            if sign_mid != sign_a:
                SignIngressFactory._emit_segment(name, body, a, sign_a, mid, sign_mid, found, depth + 1, iflag, tropical)
                SignIngressFactory._emit_segment(name, body, mid, sign_mid, b, sign_b, found, depth + 1, iflag, tropical)
            return

        diff = (sign_b - sign_a) % 12
        if diff != 1 and diff != 11 and depth < _MAX_SUBDIVISION_DEPTH and (b - a) > _MIN_SEGMENT_DAYS:
            # More than one boundary between the endpoints (a fast body, or a
            # multi-crossing interval): split so each half resolves one boundary.
            mid = (a + b) / 2.0
            sign_mid = int(_lon(mid, body, iflag) // 30)
            SignIngressFactory._emit_segment(name, body, a, sign_a, mid, sign_mid, found, depth + 1, iflag, tropical)
            SignIngressFactory._emit_segment(name, body, mid, sign_mid, b, sign_b, found, depth + 1, iflag, tropical)
            return

        # Adjacent signs: a single boundary. diff==1 is forward (top of sign_a),
        # diff==11 is retrograde (bottom of sign_a).
        retro = diff == 11
        boundary = ((sign_a * 30) if retro else ((sign_a + 1) * 30)) % 360.0
        jd_ingress = _bisect_ingress(body, a, b, boundary, iflag)
        found.append(
            SignIngressFactory._build(name, jd_ingress, sign_a, sign_b, retro, boundary, tropical)
        )

    @staticmethod
    def _build(
        name: str,
        jd: float,
        from_sign_num: int,
        to_sign_num: int,
        retro: bool,
        boundary: float,
        tropical: bool,
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
            # Only the Sun's cardinal crossings mark seasons, and ONLY in the
            # tropical frame — a sidereal cardinal boundary is not the
            # equinox/solstice, so season_marker stays None for every sidereal
            # ingress. In a tropical scan the boundary IS the tropical longitude.
            season_marker=(
                _SEASON_MARKERS.get(boundary % 360.0) if (name == "Sun" and tropical) else None
            ),
        )
