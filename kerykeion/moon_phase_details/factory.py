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
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
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
    compute_sun_rise_set_swe,
    compute_lunar_phase_jd,
    compute_sun_position,
)
from kerykeion.utilities import datetime_to_julian, julian_to_datetime


logger = logging.getLogger(__name__)


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
    iso_utc = getattr(subject, "iso_formatted_utc_datetime", None)
    if not iso_utc:
        iso_utc = getattr(subject, "iso_formatted_local_datetime", None)
    return safe_parse_iso_datetime(iso_utc)


def _compute_major_phase_name(degrees_between: float) -> str:
    """
    Compute the nearest major lunar phase name given the Sun–Moon separation.

    Major phases are:
        - New Moon (0°)
        - First Quarter (90°)
        - Full Moon (180°)
        - Last Quarter (270°)
    """
    angle = degrees_between % 360.0
    major_phases = [
        (0.0, "New Moon"),
        (90.0, "First Quarter"),
        (180.0, "Full Moon"),
        (270.0, "Last Quarter"),
    ]

    def angular_distance(a: float, b: float) -> float:
        diff = (a - b) % 360.0
        return min(diff, 360.0 - diff)

    closest_phase = min(major_phases, key=lambda item: angular_distance(angle, item[0]))
    return closest_phase[1]


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
    # Calculate next phase occurrence
    next_jd = compute_lunar_phase_jd(base_jd, target_angle, forward=True)
    # Calculate last phase occurrence
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


def _compute_sun_times(
    subject: AstrologicalSubjectModel,
) -> Optional[Tuple[datetime, datetime]]:
    """
    Compute precise sunrise and sunset local datetimes using Swiss Ephemeris.

    Uses Swiss Ephemeris `swe.rise_trans` (via `compute_sun_rise_set_swe`)
    to obtain sunrise and sunset for the subject's local civil day.
    """
    lat = getattr(subject, "lat", None)
    lng = getattr(subject, "lng", None)
    tz_str = getattr(subject, "tz_str", None)

    if lat is None or lng is None or tz_str is None:
        return None

    try:
        # Use pytz to preserve DST rules
        import pytz

        tzinfo = pytz.timezone(tz_str)
    except RuntimeError as exc:
        # Expected error: polar regions, ephemeris unavailable, etc.
        logger.debug("Sun times calculation failed (expected for polar regions): %s", exc)
        return None
    except (ImportError, AttributeError) as exc:  # pragma: no cover - defensive
        logger.error("Error importing pytz: %s. Cannot compute sunrise/sunset.", exc)
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(
            "Error loading timezone '%s': %s. Cannot compute accurate sunrise/sunset times.",
            tz_str,
            exc,
        )
        return None

    # Get the subject's UTC datetime and convert to local for date determination
    dt_utc = _get_utc_datetime(subject)
    dt_local = dt_utc.astimezone(tzinfo)

    # Calculate JD for midnight local time (start of the day)
    # IMPORTANT: Use tzinfo.localize() instead of datetime(..., tzinfo=tzinfo)
    # to properly handle DST transitions with pytz
    midnight_naive = datetime(
        year=dt_local.year,
        month=dt_local.month,
        day=dt_local.day,
    )
    midnight_local = tzinfo.localize(midnight_naive)
    midnight_utc = midnight_local.astimezone(timezone.utc)
    jd_midnight = datetime_to_julian(midnight_utc)

    # Compute both sunrise and sunset using Swiss Ephemeris
    sunrise_jd, sunset_jd = compute_sun_rise_set_swe(jd_midnight, lat, lng)

    if sunrise_jd is None or sunset_jd is None:
        return None

    # Convert JD back to datetime in local timezone
    sunrise_utc = julian_to_datetime(sunrise_jd).replace(tzinfo=timezone.utc)
    sunset_utc = julian_to_datetime(sunset_jd).replace(tzinfo=timezone.utc)

    sunrise_local = sunrise_utc.astimezone(tzinfo)
    sunset_local = sunset_utc.astimezone(tzinfo)

    return sunrise_local, sunset_local


def _compute_sun_position(
    subject: AstrologicalSubjectModel,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Compute apparent Sun altitude, azimuth and distance using Swiss Ephemeris.
    """
    lat = getattr(subject, "lat", None)
    lng = getattr(subject, "lng", None)

    if lat is None or lng is None:
        return None, None, None

    dt_utc = _get_utc_datetime(subject)
    jd_ut = datetime_to_julian(dt_utc)

    return compute_sun_position(jd_ut, lat, lng)


def _compute_next_solar_eclipse(
    subject: AstrologicalSubjectModel,
) -> Optional[MoonPhaseSolarEclipseModel]:
    """
    Compute the next global solar eclipse after the subject's time using Swiss Ephemeris.
    """
    base_dt = _get_utc_datetime(subject)
    jd_start = datetime_to_julian(base_dt)

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
    sun: object,
    moon: object,
    base_dt: datetime,
    upcoming_phases: MoonPhaseUpcomingPhasesModel,
) -> Tuple[float, str, str, str, str, str, int, str, MoonPhaseIlluminationDetailsModel]:
    """
    Compute lunar phase metrics including phase fraction, illumination, and age.
    
    Args:
        lunar_phase: Lunar phase model from subject.
        sun: Sun planetary data.
        moon: Moon planetary data.
        base_dt: Current datetime in UTC.
        upcoming_phases: Model with last/next occurrences of major phases.
    
    Returns:
        Tuple of (phase, phase_name, emoji, stage, major_phase, illumination_str,
                  age_days, lunar_cycle_str, illumination_details)
    """
    # Phase fraction based on angular separation between Sun and Moon
    degrees_between = float(lunar_phase.degrees_between_s_m)
    phase = degrees_between / 360.0
    phase_name = lunar_phase.moon_phase_name
    emoji = lunar_phase.moon_emoji

    # Waxing vs waning stage
    stage = "waxing" if 0.0 <= degrees_between < 180.0 else "waning"

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
    age_days_precise = 0.0
    if upcoming_phases.new_moon and upcoming_phases.new_moon.last:
        last_new_moon_ts = upcoming_phases.new_moon.last.timestamp
        if last_new_moon_ts:
            last_new_moon_dt = datetime.fromtimestamp(last_new_moon_ts, tz=timezone.utc)
            age_days_precise = (base_dt - last_new_moon_dt).total_seconds() / 86400.0
    else:
        # Fallback to approximation if we don't have last new moon data
        age_days_precise = phase * SYNODIC_MONTH_DAYS
    
    age_days = int(round(age_days_precise))
    
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
        lunar_cycle_str,
        illumination_details,
    )


def _build_moon_zodiac_info(
    sun: object,
    moon: object,
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
    def _build_timestamp_fields(subject: AstrologicalSubjectModel) -> Tuple[int, str]:
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

        # Initialize all fields as None
        phase: Optional[float] = None
        phase_name = None
        emoji = None
        stage: Optional[str] = None
        major_phase: Optional[str] = None
        illumination_str: Optional[str] = None
        age_days: Optional[int] = None
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
                lunar_cycle_str,
                illumination_details,
            ) = _compute_lunar_phase_metrics(lunar_phase, sun, moon, base_dt, upcoming_phases)

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
            lunar_cycle=lunar_cycle_str,
            emoji=emoji,
            zodiac=zodiac,
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

        sunrise_ts: Optional[int] = None
        sunrise_str: Optional[str] = None
        sunset_ts: Optional[int] = None
        sunset_str: Optional[str] = None
        solar_noon_str: Optional[str] = None
        day_length_str: Optional[str] = None
        position: Optional[MoonPhaseSunPositionModel] = None

        # Sunrise / Sunset, solar noon, day length
        try:
            sun_times = _compute_sun_times(subject)
            if sun_times is not None:
                sunrise_local, sunset_local = sun_times

                sunrise_ts = int(sunrise_local.timestamp())
                sunrise_str = sunrise_local.strftime("%H:%M")

                sunset_ts = int(sunset_local.timestamp())
                sunset_str = sunset_local.strftime("%H:%M")

                # Solar noon as midpoint between sunrise and sunset
                solar_noon_local = sunrise_local + (sunset_local - sunrise_local) / 2
                solar_noon_str = solar_noon_local.strftime("%H:%M")

                # Day length in H:MM
                delta = sunset_local - sunrise_local
                total_minutes = int(round(delta.total_seconds() / 60))
                hours = total_minutes // 60
                minutes = total_minutes % 60
                day_length_str = f"{hours}:{minutes:02d}"
        except RuntimeError as exc:
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
        except RuntimeError as exc:
            # Expected error: ephemeris unavailable, date out of range, etc.
            logger.debug("Sun position calculation failed (expected): %s", exc)
        except (AttributeError, ValueError, TypeError) as exc:  # pragma: no cover - defensive
            logger.error("Unexpected error calculating Sun position: %s", exc, exc_info=True)

        return MoonPhaseSunInfoModel(
            sunrise=sunrise_ts,
            sunrise_timestamp=sunrise_str,
            sunset=sunset_ts,
            sunset_timestamp=sunset_str,
            solar_noon=solar_noon_str,
            day_length=day_length_str,
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
        lat = getattr(subject, "lat", None)
        lng = getattr(subject, "lng", None)

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
    from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

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
