# -*- coding: utf-8 -*-
"""Find exact mundane (transiting-to-transiting) aspects over a date range.

A printed astrological calendar's *aspectarian* lists the instant each aspect
between two moving bodies perfects. This factory produces exactly that: every
exact planet-to-planet aspect within a range, with its Julian Day / ISO UTC
timestamp and both bodies' zodiacal state at the event.

Aspect *times* are zodiac-independent (an ayanamsha shifts both longitudes
equally, leaving their separation unchanged); the reported longitudes and signs
follow the requested zodiac.

Swiss Ephemeris / libephemeris functions used (via :mod:`.utils`):
    - ephe.calc_ut(jd, planet_id, iflag)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from kerykeion._predictive_utils import is_iso_date_only, jd_to_iso_utc as _jd_to_iso, validate_julian_range
from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion.mundane_aspects.utils import MundaneAspectEvent, _lon_speed, scan_mundane_aspects
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import SIGN_CODES, Sign, SiderealMode, ZodiacType
from kerykeion.schemas.kr_models import SubscriptableBaseModel
from kerykeion.settings.chart_defaults import DEFAULT_CHART_ASPECTS_SETTINGS
from kerykeion.settings.config_constants import POINT_NUMBER_MAP
from kerykeion.utilities import datetime_to_julian
from pydantic import Field

# Canonical body order (fastest mean geocentric motion first, the traditional
# aspectarian convention): each emitted event's ``point_a`` is the pair member
# that appears earlier here. Also the request vocabulary.
_CANONICAL_ORDER: Tuple[str, ...] = (
    "Moon",
    "Mercury",
    "Venus",
    "Sun",
    "Mars",
    "Jupiter",
    "Saturn",
    "Chiron",
    "Uranus",
    "Neptune",
    "Pluto",
    "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
)
_POINT_IDS: dict[str, int] = {name: POINT_NUMBER_MAP[name] for name in _CANONICAL_ORDER}

# Default scan set: the classical ten minus the Moon. The Moon perfects every
# aspect family to every body roughly once per 27.3-day lap (~75 events/month
# on its own) — noise for most consumers, so it is opt-in by listing it in
# ``points``, the same convention as ``SignIngressFactory``.
_DEFAULT_POINTS: Tuple[str, ...] = (
    "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
)

# Longitude-aspect vocabulary (name → exact degrees) from the shared chart
# defaults. Declination aspects (parallel/contra-parallel) are not longitude
# events and are therefore not in this map — requesting one raises ValueError.
_ASPECT_DEGREES: dict[str, float] = {
    setting["name"]: float(setting["degree"]) for setting in DEFAULT_CHART_ASPECTS_SETTINGS
}

# The five Ptolemaic majors, the default aspect set.
_DEFAULT_ASPECTS: Tuple[str, ...] = ("conjunction", "sextile", "square", "trine", "opposition")


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
                "sidereal_mode='USER' requires custom ayanamsha parameters, which MundaneAspectFactory does not accept."
            )
        if not hasattr(ephe, f"SIDM_{sidereal_mode}"):
            raise KerykeionException(f"Unknown sidereal_mode: {sidereal_mode!r}.")


# =============================================================================
# MODELS
# =============================================================================


class MundaneAspectModel(SubscriptableBaseModel):
    """A single exact mundane aspect between two transiting bodies."""

    point_a: str = Field(description="First body (canonical fast-to-slow order)")
    point_b: str = Field(description="Second body")
    aspect: str = Field(description="Aspect name, e.g. 'square'")
    aspect_degrees: float = Field(description="The aspect's exact angle in degrees")
    julian_day: float = Field(description="Julian Day (UT) of the exact perfection")
    iso_utc: str = Field(description="ISO 8601 UTC datetime of the exact perfection")
    point_a_longitude: float = Field(description="Ecliptic longitude of point_a at the event (requested zodiac)")
    point_b_longitude: float = Field(description="Ecliptic longitude of point_b at the event (requested zodiac)")
    point_a_sign: Sign = Field(description="Sign of point_a at the event")
    point_b_sign: Sign = Field(description="Sign of point_b at the event")
    point_a_retrograde: bool = Field(description="True if point_a is retrograde at the event")
    point_b_retrograde: bool = Field(description="True if point_b is retrograde at the event")


class MundaneAspectsCollectionModel(SubscriptableBaseModel):
    """Ordered list of mundane aspects within a Julian Day range."""

    start_jd: float
    end_jd: float
    aspects: List[MundaneAspectModel]


# =============================================================================
# FACTORY
# =============================================================================


class MundaneAspectFactory:
    """Find exact mundane (planet-to-planet) aspects within a date range.

    Example:
        >>> from kerykeion import MundaneAspectFactory
        >>> result = MundaneAspectFactory.from_iso_range("2020-12-01", "2020-12-31")
        >>> [(a.point_a, a.aspect, a.point_b) for a in result.aspects if a.point_a == "Jupiter"]
        [('Jupiter', 'conjunction', 'Saturn')]
    """

    @staticmethod
    def from_iso_range(
        start_date: str,
        end_date: str,
        points: Optional[List[str]] = None,
        aspects: Optional[List[str]] = None,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> MundaneAspectsCollectionModel:
        """Find mundane aspects between two ISO date(time) strings (treated as UTC).

        Args:
            start_date: ISO date or datetime, e.g. ``"2026-01-01"``.
            end_date: ISO date or datetime; a date-only value means "through the
                end of that UTC day".
            points: Optional subset of body names. Defaults to Sun..Pluto
                (Moon excluded unless explicitly requested).
            aspects: Optional aspect names. Defaults to the five Ptolemaic
                majors (conjunction, sextile, square, trine, opposition).
            zodiac_type: ``"Tropical"`` (default) or ``"Sidereal"``. Event times
                are zodiac-independent; longitudes/signs follow the request.
            sidereal_mode: Ayanamsha when ``zodiac_type='Sidereal'``.
        """
        try:
            start_dt = _to_utc_naive(datetime.fromisoformat(start_date))
            end_dt = _to_utc_naive(datetime.fromisoformat(end_date))
        except (ValueError, TypeError) as exc:
            # Same contract as SignIngressFactory.from_iso_range.
            raise KerykeionException(
                f"Invalid ISO date/datetime for mundane aspect range "
                f"(start_date={start_date!r}, end_date={end_date!r}): {exc}"
            ) from exc
        if is_iso_date_only(end_date):
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return MundaneAspectFactory.from_julian_day(
            datetime_to_julian(start_dt),
            datetime_to_julian(end_dt),
            points,
            aspects,
            zodiac_type,
            sidereal_mode,
        )

    @staticmethod
    def from_julian_day(
        start_jd: float,
        end_jd: float,
        points: Optional[List[str]] = None,
        aspects: Optional[List[str]] = None,
        zodiac_type: ZodiacType = "Tropical",
        sidereal_mode: Optional[SiderealMode] = None,
    ) -> MundaneAspectsCollectionModel:
        """Find all mundane aspects in ``[start_jd, end_jd]``, ordered chronologically.

        Raises:
            KerykeionException: For an invalid zodiac configuration, or if the
                ephemeris backend fails mid-scan (most often a date outside the
                available ephemeris range).
            ValueError: If a body/aspect name is unknown, either Julian bound
                is non-finite, or the range is too large to scan.
        """
        validate_julian_range(start_jd, end_jd)

        # None = default set; an explicit empty list = scan nothing.
        if points is not None:
            invalid = sorted(set(points) - set(_POINT_IDS))
            if invalid:
                raise ValueError(
                    f"Unknown points: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_CANONICAL_ORDER)}"
                )
            requested = set(points)
        else:
            requested = set(_DEFAULT_POINTS)
        # Canonical (fast-to-slow) order fixes point_a/point_b per pair and
        # makes results independent of the caller's list order.
        bodies = [(name, _POINT_IDS[name]) for name in _CANONICAL_ORDER if name in requested]

        if aspects is not None:
            invalid = sorted(set(aspects) - set(_ASPECT_DEGREES))
            if invalid:
                raise ValueError(
                    f"Unknown aspects: {', '.join(invalid)}. "
                    f"Valid: {', '.join(_ASPECT_DEGREES)}"
                )
            aspect_pairs = [(name, _ASPECT_DEGREES[name]) for name in dict.fromkeys(aspects)]
        else:
            aspect_pairs = [(name, _ASPECT_DEGREES[name]) for name in _DEFAULT_ASPECTS]

        _validate_zodiac(zodiac_type, sidereal_mode)

        models: List[MundaneAspectModel] = []
        if end_jd > start_jd and len(bodies) >= 2 and aspect_pairs:
            # The session holds the ephemeris lock across the whole scan and
            # resets global state on exit; its iflag already includes FLG_SPEED
            # (plus FLG_SIDEREAL for sidereal zodiacs).
            with ephemeris_session(zodiac_type=zodiac_type, sidereal_mode=sidereal_mode) as iflag:
                events = scan_mundane_aspects(start_jd, end_jd, bodies, aspect_pairs, iflag)
                point_ids = dict(bodies)
                models = [MundaneAspectFactory._build(event, point_ids, iflag) for event in events]

        return MundaneAspectsCollectionModel(
            start_jd=start_jd,
            end_jd=end_jd,
            aspects=models,
        )

    @staticmethod
    def _build(
        event: MundaneAspectEvent,
        point_ids: dict[str, int],
        iflag: int,
    ) -> MundaneAspectModel:
        """Build the public model for an event: one position lookup per body."""
        lon_a, speed_a = _lon_speed(event.julian_day, point_ids[event.point_a], iflag)
        lon_b, speed_b = _lon_speed(event.julian_day, point_ids[event.point_b], iflag)
        return MundaneAspectModel(
            point_a=event.point_a,
            point_b=event.point_b,
            aspect=event.aspect,
            aspect_degrees=event.degrees,
            julian_day=event.julian_day,
            iso_utc=_jd_to_iso(event.julian_day),
            point_a_longitude=round(lon_a, 6),
            point_b_longitude=round(lon_b, 6),
            point_a_sign=SIGN_CODES[int(lon_a // 30) % 12],
            point_b_sign=SIGN_CODES[int(lon_b // 30) % 12],
            point_a_retrograde=speed_a < 0.0,
            point_b_retrograde=speed_b < 0.0,
        )
