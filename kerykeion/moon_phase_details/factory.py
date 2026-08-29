# -*- coding: utf-8 -*-
"""
Moon Phase Details Factory

This module defines the `MoonPhaseDetailsFactory`, a lightweight helper that
builds a complete `MoonPhaseOverviewModel` from an existing
`AstrologicalSubjectModel`.

Compared to the legacy `LunarPhaseModel` attached to subjects, this factory
produces a richer, UI-oriented structure that includes:

    - Normalized phase information and qualitative labels
    - Approximate illumination and age in days
    - Surrounding major phases (previous/next New, First Quarter, Full, Last Quarter)
    - Next global solar and lunar eclipses (via Swiss Ephemeris)
    - Approximate sunrise, sunset, solar noon and day length for the subject location
    - Moonrise and moonset for the subject's civil day (absent on the days that have neither)
    - Apparent Sun position (altitude, azimuth, distance)
    - Simple Sun/Moon zodiac signs snapshot

The goal is to keep the public API very simple:

    - You create an `AstrologicalSubjectModel` with `AstrologicalSubjectFactory`
    - You pass that subject to `MoonPhaseDetailsFactory.from_subject(...)`
    - You get back a `MoonPhaseOverviewModel` ready for serialization or UI use
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    KerykeionPointModel,
    LunarPhaseModel,
    MoonPhaseOverviewModel,
    MoonPhaseMoonSummaryModel,
    MoonPhaseZodiacModel,
    MoonPhaseMoonDetailedModel,
    MoonPhaseIlluminationDetailsModel,
    MoonPhaseLocationModel,
    MoonPhaseUpcomingPhasesModel,
    MoonPhaseMajorPhaseWindowModel,
    MoonPhaseEventMomentModel,
    MoonPhaseSunInfoModel,
    MoonPhaseSolarEclipseModel,
    MoonPhaseEclipseModel,
    MoonPhaseSunPositionModel,
)
from kerykeion.moon_phase_details.utils import (
    safe_parse_iso_datetime,
    describe_solar_eclipse_type,
    describe_lunar_eclipse_type,
    compute_next_solar_eclipse_jd,
    compute_next_lunar_eclipse_jd,
    compute_rise_set_ephe,
    compute_sun_rise_set_ephe,
    compute_sun_transit_ephe,
    compute_lunar_phase_jd,
    compute_sun_position,
)
from kerykeion.ephemeris_backend.backend import ephemeris_session, ephe
from kerykeion.schemas.literals import LunarPhaseEmoji, LunarPhaseName, LunarPhaseStage
from kerykeion.utilities.core import (
    datetime_to_julian,
    julian_to_datetime,
    localize_naive,
    lunar_major_phase_from_degrees,
    lunar_stage_from_degrees,
)


logger = logging.getLogger(__name__)


# Backend error the "expected calculation failed → degrade to None" handlers
# below must catch (libephemeris ``Error`` incl. ``EphemerisRangeError`` near the
# ephemeris edge; pyswisseph ``swisseph.Error``), NOT ``RuntimeError`` which no
# backend raises. Resolved once so the ``except`` clauses stay mypy-clean.
_BACKEND_ERRORS: tuple = tuple({RuntimeError, getattr(ephe, "Error", RuntimeError)})


# Mean synodic month length in days (lunation period)
# This is the average time from New Moon to New Moon.
# Value from Chapront ELP 2000-82B lunar theory
# Source: https://eclipse.gsfc.nasa.gov/SEhelp/moonorbit.html
# Note: Actual lunations vary between ~29.27 and ~29.83 days due to orbital eccentricity
SYNODIC_MONTH_DAYS = 29.530588853


def _get_utc_datetime(subject: AstrologicalSubjectModel) -> datetime:
    """
    Extract UTC datetime from an AstrologicalSubjectModel.

    This helper tries to get the UTC datetime first, falling back to local
    datetime if UTC is not available.

    Args:
        subject: The astrological subject model.

    Returns:
        datetime: Parsed UTC datetime object.
    """
    iso_utc = subject.iso_formatted_utc_datetime
    if not iso_utc:
        iso_utc = subject.iso_formatted_local_datetime
    return safe_parse_iso_datetime(iso_utc)


def _compute_major_phase_name(degrees_between: float) -> LunarPhaseName:
    """
    Compute the nearest major lunar phase name given the Sun–Moon separation.

    Major phases are:
        - New Moon (0°)
        - First Quarter (90°)
        - Full Moon (180°)
        - Last Quarter (270°)

    A thin alias over :func:`kerykeion.utilities.core.lunar_major_phase_from_degrees`,
    which is the one definition: the subjects' ``LunarPhaseModel.major_phase`` reads
    the same function, so this endpoint and a chart cast for the same instant cannot
    disagree.
    """
    return lunar_major_phase_from_degrees(degrees_between)


def _create_event_moment(
    event_dt: datetime,
    reference_dt: datetime,
    is_past: bool,
) -> MoonPhaseEventMomentModel:
    """
    Create a MoonPhaseEventMomentModel with consistent timestamp formatting.

    Args:
        event_dt: The event datetime (aware, UTC).
        reference_dt: Reference datetime for calculating time difference (aware, UTC).
        is_past: True if event is in the past, False if in the future.

    Returns:
        MoonPhaseEventMomentModel with timestamp, datestamp, and days_ago/days_ahead.
    """
    timestamp = int(event_dt.timestamp())
    datestamp = event_dt.strftime("%a, %d %b %Y %H:%M:%S %z")

    if is_past:
        days_diff = (reference_dt - event_dt).total_seconds() / 86400.0
        return MoonPhaseEventMomentModel(
            timestamp=timestamp,
            datestamp=datestamp,
            days_ago=int(round(days_diff)),
        )
    else:
        days_diff = (event_dt - reference_dt).total_seconds() / 86400.0
        return MoonPhaseEventMomentModel(
            timestamp=timestamp,
            datestamp=datestamp,
            days_ahead=int(round(days_diff)),
        )


def _build_major_phase_window(
    base_datetime: datetime,
    base_jd: float,
    target_angle: float,
) -> MoonPhaseMajorPhaseWindowModel:
    """
    Build last/next window for a specific major lunar phase using precise Swiss Ephemeris calculations.

    This replaces the previous mean synodic month approximation with exact
    ephemeris calculations for maximum accuracy.

    Args:
        base_datetime: Reference datetime.
        base_jd: Reference Julian Day.
        target_angle: Target Sun-Moon angle (0=New, 90=First Quarter, 180=Full, 270=Last Quarter).

    Returns:
        MoonPhaseMajorPhaseWindowModel with precise last/next occurrences.
    """
    # Calculate the surrounding occurrences inside a serialized session
    # (the solver mutates the global ephemeris path).
    with ephemeris_session():
        next_jd = compute_lunar_phase_jd(base_jd, target_angle, forward=True)
        last_jd = compute_lunar_phase_jd(base_jd, target_angle, forward=False)

    if next_jd is None or last_jd is None:
        # Fallback to None if calculation fails
        return MoonPhaseMajorPhaseWindowModel(last=None, next=None)

    # Convert JD to datetime
    next_dt = julian_to_datetime(next_jd).replace(tzinfo=timezone.utc)
    last_dt = julian_to_datetime(last_jd).replace(tzinfo=timezone.utc)

    # Create event moments using helper
    last_event = _create_event_moment(last_dt, base_datetime, is_past=True)
    next_event = _create_event_moment(next_dt, base_datetime, is_past=False)

    return MoonPhaseMajorPhaseWindowModel(last=last_event, next=next_event)


def _build_upcoming_phases(
    subject: AstrologicalSubjectModel,
) -> MoonPhaseUpcomingPhasesModel:
    """
    Calculate precise last and next occurrences of the four major lunar phases.

    Uses Swiss Ephemeris with binary search for exact phase timings,
    providing accurate information instead of mean synodic month approximations.
    """
    base_dt = _get_utc_datetime(subject)
    base_jd = datetime_to_julian(base_dt)

    return MoonPhaseUpcomingPhasesModel(
        new_moon=_build_major_phase_window(base_dt, base_jd, 0.0),
        first_quarter=_build_major_phase_window(base_dt, base_jd, 90.0),
        full_moon=_build_major_phase_window(base_dt, base_jd, 180.0),
        last_quarter=_build_major_phase_window(base_dt, base_jd, 270.0),
    )


def _local_civil_day_window(
    subject: AstrologicalSubjectModel,
) -> Optional[tuple[ZoneInfo, float, float]]:
    """
    Resolve the subject's civil day: its timezone and its two midnights.

    Every rise/set question in this module is asked *of a day* — the subject's
    local civil day — and the day is the same one for the Sun and the Moon, so
    it is derived once here. The second midnight matters for the Moon: it rises
    about 50 minutes later each day, so on roughly one day in thirty the next
    moonrise after local midnight already belongs to tomorrow, and only the
    window can tell the caller that today simply has none.

    Returns:
        Optional[tuple[ZoneInfo, float, float]]: ``(tzinfo, jd_midnight,
            jd_next_midnight)`` with both Julian Days in UT, or ``None`` when
            the coordinates or the timezone cannot be resolved at all.
    """
    lat = subject.lat
    lng = subject.lng
    tz_str = subject.tz_str

    if lat is None or lng is None or tz_str is None:
        return None

    try:
        # ZoneInfo evaluates the zone's rules on demand, so DST stays correct at any
        # date instead of freezing at the end of a precomputed transition table.
        tzinfo = ZoneInfo(tz_str)
    except (KeyError, ValueError) as exc:
        # Expected error: the subject's tz_str is not a known IANA timezone
        # (ZoneInfoNotFoundError subclasses KeyError) or is a malformed key
        # (ValueError). Neither is a RuntimeError, so they need naming explicitly.
        logger.debug("Unknown timezone '%s': %s. Cannot compute rise/set times.", tz_str, exc)
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(
            "Error loading timezone '%s': %s. Cannot compute accurate rise/set times.",
            tz_str,
            exc,
        )
        return None

    # Get the subject's UTC datetime and convert to local for date determination
    dt_utc = _get_utc_datetime(subject)
    dt_local = dt_utc.astimezone(tzinfo)

    # Calculate JD for midnight local time (start of the day)
    # IMPORTANT: resolve the wall time through localize_naive rather than attaching
    # the tzinfo directly, so DST edge cases are decided instead of defaulted.
    midnight_naive = datetime(
        year=dt_local.year,
        month=dt_local.month,
        day=dt_local.day,
    )
    # Civil midnight can be ambiguous (fall-back fold) or nonexistent (spring-forward
    # gap at 00:00 — America/Sao_Paulo 2018-11-04, Africa/Cairo 2023-04-28). The
    # smaller-offset reading answers both correctly: inside a fold it is the
    # post-transition occurrence, and across a gap it is the first instant of the
    # civil day that actually exists. A bare localize silently took a default here.
    midnight_local = localize_naive(midnight_naive, tzinfo, is_dst=False)
    midnight_utc = midnight_local.astimezone(timezone.utc)
    jd_midnight = datetime_to_julian(midnight_utc)

    # Tomorrow's midnight is resolved the same way rather than as
    # ``jd_midnight + 1``: across a DST transition the civil day is 23 or 25
    # hours long, and a fixed 24 would either clip an event out of the day or
    # let tomorrow's in.
    next_naive = datetime(
        year=dt_local.year,
        month=dt_local.month,
        day=dt_local.day,
    ) + timedelta(days=1)
    next_midnight_local = localize_naive(next_naive, tzinfo, is_dst=False)
    jd_next_midnight = datetime_to_julian(next_midnight_local.astimezone(timezone.utc))

    return tzinfo, jd_midnight, jd_next_midnight


def _compute_moon_times(
    subject: AstrologicalSubjectModel,
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Compute moonrise and moonset as local datetimes, for the subject's civil day.

    The same `rise_trans` call the Sun uses — same refracted upper limb, same
    standard atmosphere — pointed at the Moon.

    Unlike the Sun, the Moon does not rise and set once every civil day: it is
    about 50 minutes later each day, so roughly one day in thirty has no
    moonrise, and another has no moonset. The backend always answers with the
    NEXT event, which on those days belongs to tomorrow; anything outside
    ``[midnight, next midnight)`` is therefore reported as ``None`` rather than
    passed off as today's.

    Returns:
        tuple[Optional[datetime], Optional[datetime]]: ``(moonrise, moonset)``
            as timezone-aware datetimes in the subject's local zone, each
            ``None`` when the event does not fall inside this civil day (or
            cannot be computed at all).
    """
    window = _local_civil_day_window(subject)
    if window is None:
        return None, None
    tzinfo, jd_midnight, jd_next_midnight = window
    lat = subject.lat
    lng = subject.lng

    try:
        # Serialized session: the helper mutates the global ephemeris path.
        with ephemeris_session():
            moonrise_jd, moonset_jd = compute_rise_set_ephe(jd_midnight, lat, lng, body=ephe.MOON)
    except _BACKEND_ERRORS as exc:
        # Expected: the ephemeris edge, a polar latitude, missing data.
        logger.debug("Moonrise/moonset calculation failed (expected): %s", exc)
        return None, None
    except (AttributeError, ValueError, TypeError) as exc:  # pragma: no cover - defensive
        logger.error("Unexpected error calculating moonrise/moonset: %s", exc, exc_info=True)
        return None, None

    def _inside_the_day(event_jd: Optional[float]) -> Optional[datetime]:
        if event_jd is None or not (jd_midnight <= event_jd < jd_next_midnight):
            return None
        return julian_to_datetime(event_jd).replace(tzinfo=timezone.utc).astimezone(tzinfo)

    return _inside_the_day(moonrise_jd), _inside_the_day(moonset_jd)


def _compute_sun_times(
    subject: AstrologicalSubjectModel,
) -> Optional[tuple[Optional[datetime], Optional[datetime], Optional[datetime]]]:
    """
    Compute sunrise, sunset and solar noon as local datetimes.

    Uses the backend's `rise_trans` (via `compute_sun_rise_set_ephe` and
    `compute_sun_transit_ephe`) for the subject's local civil day.

    Returns ``None`` only when the location or timezone cannot be resolved at
    all. Otherwise a 3-tuple, in which the first two elements are ``None`` on a
    polar day or night — there is no rise/set pair — while the third can still
    carry the meridian transit. Callers must test the elements, not the tuple:
    ``(None, None, None)`` is reachable and truthy.

    Solar noon is returned from here rather than derived by the caller because
    it needs `jd_midnight`: deriving it outside meant either re-deriving local
    midnight — the DST reasoning in `_local_civil_day_window` is subtle enough
    that a second copy would drift — or settling for the midpoint of the pair,
    which is a different quantity (see `compute_sun_transit_ephe`).
    """
    window = _local_civil_day_window(subject)
    if window is None:
        return None
    tzinfo, jd_midnight, _jd_next_midnight = window
    lat = subject.lat
    lng = subject.lng

    # Compute sunrise, sunset and the meridian transit inside a serialized
    # session (the helpers mutate the global ephemeris path).
    with ephemeris_session():
        sunrise_jd, sunset_jd = compute_sun_rise_set_ephe(jd_midnight, lat, lng)

        if sunrise_jd is not None and sunset_jd is not None and sunset_jd <= sunrise_jd:
            # Midnight-sun transition days: the only set after local midnight
            # precedes the sunrise (the Sun was still up at 00:00). Pair the
            # sunrise with its actual following sunset — same handling as
            # sun_times.utils — or day_length goes negative.
            _, paired_sunset_jd = compute_sun_rise_set_ephe(sunrise_jd + 1e-6, lat, lng)
            sunset_jd = paired_sunset_jd if paired_sunset_jd is not None and paired_sunset_jd > sunrise_jd else None

        transit_jd = compute_sun_transit_ephe(jd_midnight, lat, lng)

    solar_noon_local = (
        julian_to_datetime(transit_jd).replace(tzinfo=timezone.utc).astimezone(tzinfo)
        if transit_jd is not None
        else None
    )

    if sunrise_jd is None or sunset_jd is None:
        # Polar day or night: no pair, so no rise, set or day length — but the Sun
        # still culminates, and the transit above already found when. Returning it
        # rather than dropping the whole result is what makes the model docstring
        # true; the earlier version computed the transit here and threw it away.
        return None, None, solar_noon_local

    # Convert JD back to datetime in local timezone
    sunrise_utc = julian_to_datetime(sunrise_jd).replace(tzinfo=timezone.utc)
    sunset_utc = julian_to_datetime(sunset_jd).replace(tzinfo=timezone.utc)

    sunrise_local = sunrise_utc.astimezone(tzinfo)
    sunset_local = sunset_utc.astimezone(tzinfo)
    return sunrise_local, sunset_local, solar_noon_local


def _compute_sun_position(
    subject: AstrologicalSubjectModel,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Compute apparent Sun altitude, azimuth and distance using Swiss Ephemeris.
    """
    lat = subject.lat
    lng = subject.lng

    if lat is None or lng is None:
        return None, None, None

    dt_utc = _get_utc_datetime(subject)
    jd_ut = datetime_to_julian(dt_utc)

    with ephemeris_session():
        return compute_sun_position(jd_ut, lat, lng)


def _compute_next_solar_eclipse(
    subject: AstrologicalSubjectModel,
) -> Optional[MoonPhaseSolarEclipseModel]:
    """
    Compute the next global solar eclipse after the subject's time using Swiss Ephemeris.
    """
    base_dt = _get_utc_datetime(subject)
    jd_start = datetime_to_julian(base_dt)

    with ephemeris_session():
        result = compute_next_solar_eclipse_jd(jd_start)
    if result is None:
        return None

    retflag, eclipse_jd = result
    eclipse_dt_utc = julian_to_datetime(eclipse_jd).replace(tzinfo=timezone.utc)

    return MoonPhaseSolarEclipseModel(
        timestamp=int(eclipse_dt_utc.timestamp()),
        datestamp=eclipse_dt_utc.strftime("%a, %d %b %Y %H:%M:%S %z"),
        type=describe_solar_eclipse_type(retflag),
        visibility_regions=None,
    )


def _compute_next_lunar_eclipse(
    subject: AstrologicalSubjectModel,
) -> Optional[MoonPhaseEclipseModel]:
    """
    Compute the next global lunar eclipse after the subject's time using Swiss Ephemeris.
    """
    base_dt = _get_utc_datetime(subject)
    jd_start = datetime_to_julian(base_dt)

    with ephemeris_session():
        result = compute_next_lunar_eclipse_jd(jd_start)
    if result is None:
        return None

    retflag, eclipse_jd = result
    eclipse_dt_utc = julian_to_datetime(eclipse_jd).replace(tzinfo=timezone.utc)

    return MoonPhaseEclipseModel(
        timestamp=int(eclipse_dt_utc.timestamp()),
        datestamp=eclipse_dt_utc.strftime("%a, %d %b %Y %H:%M:%S %z"),
        type=describe_lunar_eclipse_type(retflag),
        visibility_regions=None,
    )


def _compute_lunar_phase_metrics(
    lunar_phase: LunarPhaseModel,
    base_dt: datetime,
    upcoming_phases: MoonPhaseUpcomingPhasesModel,
) -> tuple[
    float,
    LunarPhaseName,
    LunarPhaseEmoji,
    LunarPhaseStage,
    LunarPhaseName,
    str,
    int,
    float,
    str,
    MoonPhaseIlluminationDetailsModel,
]:
    """
    Compute lunar phase metrics including phase fraction, illumination, and age.

    Args:
        lunar_phase: Lunar phase model from subject.
        base_dt: Current datetime in UTC.
        upcoming_phases: Model with last/next occurrences of major phases.

    Returns:
        Tuple of (phase, phase_name, emoji, stage, major_phase, illumination_str,
                  age_days, age_days_precise, lunar_cycle_str, illumination_details)
    """
    # Phase fraction based on angular separation between Sun and Moon
    degrees_between = float(lunar_phase.degrees_between_s_m)
    phase = degrees_between / 360.0
    phase_name = lunar_phase.moon_phase_name
    emoji = lunar_phase.moon_emoji

    # Waxing vs waning stage — the subjects' LunarPhaseModel.stage reads the
    # same function, so the two surfaces cannot disagree about the same instant.
    stage = lunar_stage_from_degrees(degrees_between)

    # Nearest major phase
    major_phase = _compute_major_phase_name(degrees_between)

    # Illumination using standard phase-angle formula
    # Formula: k = 0.5 * (1 - cos(phase_angle))
    # At 0° (New Moon): k = 0 (0% illuminated)
    # At 180° (Full Moon): k = 1 (100% illuminated)
    illum_fraction = 0.5 * (1.0 - math.cos(math.radians(degrees_between)))
    illumination_percent = round(illum_fraction * 100)
    illumination_str = f"{illumination_percent}%"

    # Calculate PRECISE lunar age using actual time since last new moon
    # This replaces the previous approximation: phase * SYNODIC_MONTH_DAYS
    # Improvement: from ±6-12 hours precision to ~1 second precision
    # Start from the approximation so a missing/None timestamp can never
    # leave the age at a bogus 0.0; the precise value overrides it whenever
    # the last-new-moon instant is actually known.
    age_days_precise = phase * SYNODIC_MONTH_DAYS
    if upcoming_phases.new_moon and upcoming_phases.new_moon.last:
        last_new_moon_ts = upcoming_phases.new_moon.last.timestamp
        if last_new_moon_ts is not None:
            last_new_moon_dt = datetime.fromtimestamp(last_new_moon_ts, tz=timezone.utc)
            age_days_precise = (base_dt - last_new_moon_dt).total_seconds() / 86400.0

    age_days = round(age_days_precise)

    # Lunar cycle percentage - keep high precision for this metric
    lunar_cycle_str = f"{round(phase * 100, 3)}%"

    illumination_details = MoonPhaseIlluminationDetailsModel(
        percentage=illumination_percent,
        visible_fraction=illum_fraction,
        phase_angle=degrees_between,
    )

    return (
        phase,
        phase_name,
        emoji,
        stage,
        major_phase,
        illumination_str,
        age_days,
        age_days_precise,
        lunar_cycle_str,
        illumination_details,
    )


def _build_moon_zodiac_info(
    sun: Optional[KerykeionPointModel],
    moon: Optional[KerykeionPointModel],
) -> Optional[MoonPhaseZodiacModel]:
    """
    Build zodiac information block for Sun and Moon signs.

    Args:
        sun: Sun planetary data with sign attribute.
        moon: Moon planetary data with sign attribute.

    Returns:
        MoonPhaseZodiacModel or None if sign data is unavailable.
    """
    if sun is not None and moon is not None and sun.sign and moon.sign:
        return MoonPhaseZodiacModel(
            sun_sign=sun.sign,
            moon_sign=moon.sign,
        )
    return None


class MoonPhaseDetailsFactory:
    """
    Factory for generating high-level moon phase context models.

    This factory has a single, simple entry point:

        - `from_subject(subject: AstrologicalSubjectModel, ...)`

    It assumes you already created an `AstrologicalSubjectModel` using
    `AstrologicalSubjectFactory` (or equivalent), and enriches it with
    contextual moon/sun information in a `MoonPhaseOverviewModel`.
    """

    @classmethod
    def from_subject(
        cls,
        subject: AstrologicalSubjectModel,
        *,
        using_default_location: bool = False,
        location_precision: int = 0,
    ) -> MoonPhaseOverviewModel:
        """
        Build a `MoonPhaseOverviewModel` from an existing astrological subject.

        Args:
            subject: AstrologicalSubjectModel with at least Sun, Moon, and
                time/location data. The subject's `lunar_phase` attribute is
                used when available.
            using_default_location: Whether the location used comes from a
                default configuration (useful for API consumers).
            location_precision: Optional precision indicator for the location.

        Returns:
            MoonPhaseOverviewModel with moon summary, sun summary and
            basic location metadata.
        """
        timestamp, datestamp = cls._build_timestamp_fields(subject)
        moon_summary = cls._build_moon_summary(subject)
        sun_info = cls._build_sun_info(subject)
        location = cls._build_location(
            subject,
            using_default_location=using_default_location,
            location_precision=location_precision,
        )

        return MoonPhaseOverviewModel(
            timestamp=timestamp,
            datestamp=datestamp,
            sun=sun_info,
            moon=moon_summary,
            location=location,
        )

    @staticmethod
    def _build_timestamp_fields(subject: AstrologicalSubjectModel) -> tuple[int, str]:
        """
        Build Unix timestamp and RFC-2822-like datestamp from the subject.
        """
        dt_utc = _get_utc_datetime(subject)
        ts = int(dt_utc.timestamp())
        datestamp = dt_utc.strftime("%a, %d %b %Y %H:%M:%S %z")
        return ts, datestamp

    @staticmethod
    def _build_moon_summary(subject: AstrologicalSubjectModel) -> MoonPhaseMoonSummaryModel:
        """
        Build the high-level moon summary block from the subject's state.

        This method orchestrates the creation of moon phase information by:
        1. Extracting basic lunar phase data from the subject
        2. Computing precise phase metrics (illumination, age, stage)
        3. Building zodiac information
        4. Calculating upcoming major phases
        5. Finding next lunar eclipse
        """
        lunar_phase: Optional[LunarPhaseModel] = getattr(subject, "lunar_phase", None)
        sun = getattr(subject, "sun", None)
        moon = getattr(subject, "moon", None)

        # Moonrise / moonset for the subject's civil day. Computed outside the
        # `lunar_phase is not None` branch below on purpose: the horizon
        # crossings are a fact about the place and the day, and they exist even
        # for a subject that carries no lunar phase (a heliocentric chart, or
        # one built without the Sun in active_points).
        moonrise_local, moonset_local = _compute_moon_times(subject)
        moonrise_str = moonrise_local.isoformat() if moonrise_local is not None else None
        moonset_str = moonset_local.isoformat() if moonset_local is not None else None
        moonrise_ts = int(moonrise_local.timestamp()) if moonrise_local is not None else None
        moonset_ts = int(moonset_local.timestamp()) if moonset_local is not None else None

        # Initialize all fields as None
        phase: Optional[float] = None
        phase_name: Optional[LunarPhaseName] = None
        emoji: Optional[LunarPhaseEmoji] = None
        stage: Optional[LunarPhaseStage] = None
        major_phase: Optional[LunarPhaseName] = None
        illumination_str: Optional[str] = None
        age_days: Optional[int] = None
        age_days_precise: Optional[float] = None
        lunar_cycle_str: Optional[str] = None
        detailed: Optional[MoonPhaseMoonDetailedModel] = None
        next_lunar_eclipse: Optional[MoonPhaseEclipseModel] = None
        zodiac: Optional[MoonPhaseZodiacModel] = None

        if lunar_phase is not None and sun is not None and moon is not None:
            # Get current UTC datetime for age calculation
            base_dt = _get_utc_datetime(subject)

            # Calculate precise upcoming phases first (needed for age calculation)
            upcoming_phases = _build_upcoming_phases(subject)

            # Compute all phase metrics
            (
                phase,
                phase_name,
                emoji,
                stage,
                major_phase,
                illumination_str,
                age_days,
                age_days_precise,
                lunar_cycle_str,
                illumination_details,
            ) = _compute_lunar_phase_metrics(lunar_phase, base_dt, upcoming_phases)

            # Build detailed moon information
            detailed = MoonPhaseMoonDetailedModel(
                position=None,
                visibility=None,
                upcoming_phases=upcoming_phases,
                illumination_details=illumination_details,
            )

            # Compute next lunar eclipse using Swiss Ephemeris
            next_lunar_eclipse = _compute_next_lunar_eclipse(subject)

            # Build zodiac information
            zodiac = _build_moon_zodiac_info(sun, moon)

        return MoonPhaseMoonSummaryModel(
            phase=phase,
            phase_name=phase_name,
            major_phase=major_phase,
            stage=stage,
            illumination=illumination_str,
            age_days=age_days,
            age_days_precise=age_days_precise,
            lunar_cycle=lunar_cycle_str,
            emoji=emoji,
            zodiac=zodiac,
            moonrise=moonrise_str,
            moonrise_timestamp=moonrise_ts,
            moonset=moonset_str,
            moonset_timestamp=moonset_ts,
            next_lunar_eclipse=next_lunar_eclipse,
            detailed=detailed,
        )

    @staticmethod
    def _build_sun_info(subject: AstrologicalSubjectModel) -> MoonPhaseSunInfoModel:
        """
        Build high-level Sun information block from an AstrologicalSubjectModel.

        Populates:
            - Sunrise / sunset local timestamps and human-readable times
            - Solar noon and day length
            - Apparent solar position (altitude, azimuth, distance)
            - Next global solar eclipse (timestamp, label)
        """
        next_solar = _compute_next_solar_eclipse(subject)

        sunrise_local: Optional[datetime] = None
        sunset_local: Optional[datetime] = None
        solar_noon_local: Optional[datetime] = None
        day_length: Optional[timedelta] = None
        position: Optional[MoonPhaseSunPositionModel] = None

        # Sunrise / Sunset, solar noon, day length
        try:
            sun_times = _compute_sun_times(subject)
            if sun_times is not None:
                sunrise_local, sunset_local, solar_noon_local = sun_times
                if sunrise_local is not None and sunset_local is not None:
                    # Both endpoints are converted to UTC BEFORE the subtraction:
                    # when two aware datetimes share the same tzinfo object — and
                    # ZoneInfo caches, so they always do here — Python subtracts
                    # their wall-clock fields and never consults the offsets.
                    # Across a DST transition that silently reports the clock
                    # elapsed rather than the time elapsed.
                    sunrise_utc = sunrise_local.astimezone(timezone.utc)
                    sunset_utc = sunset_local.astimezone(timezone.utc)
                    day_length = sunset_utc - sunrise_utc
        except _BACKEND_ERRORS as exc:
            # Expected error: polar regions, ephemeris unavailable, etc.
            logger.debug("Sunrise/sunset calculation failed (expected): %s", exc)
        except (AttributeError, ValueError, TypeError) as exc:  # pragma: no cover - defensive
            logger.error("Unexpected error calculating sunrise/sunset: %s", exc, exc_info=True)

        # Apparent solar position
        try:
            altitude, azimuth, distance_km = _compute_sun_position(subject)
            if altitude is not None or azimuth is not None or distance_km is not None:
                position = MoonPhaseSunPositionModel(
                    altitude=altitude,
                    azimuth=azimuth,
                    distance=distance_km,
                )
        except _BACKEND_ERRORS as exc:
            # Expected error: ephemeris unavailable, date out of range, etc.
            logger.debug("Sun position calculation failed (expected): %s", exc)
        except (AttributeError, ValueError, TypeError) as exc:  # pragma: no cover - defensive
            logger.error("Unexpected error calculating Sun position: %s", exc, exc_info=True)

        return MoonPhaseSunInfoModel(
            sunrise=sunrise_local,
            sunset=sunset_local,
            solar_noon=solar_noon_local,
            day_length=day_length,
            position=position,
            next_solar_eclipse=next_solar,
        )

    @staticmethod
    def _build_location(
        subject: AstrologicalSubjectModel,
        *,
        using_default_location: bool,
        location_precision: int,
    ) -> MoonPhaseLocationModel:
        """
        Build the location block from the subject coordinates, when available.
        """
        lat = subject.lat
        lng = subject.lng

        if lat is None or lng is None:
            latitude_str = None
            longitude_str = None
        else:
            latitude_str = f"{lat}"
            longitude_str = f"{lng}"

        return MoonPhaseLocationModel(
            latitude=latitude_str,
            longitude=longitude_str,
            precision=location_precision,
            using_default_location=using_default_location,
        )


__all__ = ["MoonPhaseDetailsFactory"]


if __name__ == "__main__":
    # Inline manual test example.
    # Run with: python -m kerykeion.moon_phase_details.factory
    from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory

    test_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Moon Phase Example",
        year=2025,
        month=4,
        day=1,
        hour=7,
        minute=51,
        city="London",
        nation="GB",
        lng=-0.1276,  # London actual coordinates
        lat=51.5074,
        tz_str="Europe/London",  # Correct timezone for London (handles BST)
        online=False,
        suppress_geonames_warning=True,
    )

    overview = MoonPhaseDetailsFactory.from_subject(
        test_subject,
        using_default_location=True,
        location_precision=0,
    )

    print(overview.model_dump_json(exclude_none=True, indent=2))
