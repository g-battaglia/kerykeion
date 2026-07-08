# -*- coding: utf-8 -*-
"""
Kerykeion Data Models
=====================

This module contains all Pydantic models used throughout the Kerykeion library
for representing astrological data structures.

Model Hierarchy:
    SubscriptableBaseModel
    ├── LunarPhaseModel - Moon phase information
    ├── KerykeionPointModel - Celestial points (planets, houses, etc.)
    ├── AstrologicalBaseModel - Base for all chart subjects
    │   ├── AstrologicalSubjectModel - Individual birth/event charts
    │   ├── CompositeSubjectModel - Composite relationship charts
    │   └── PlanetReturnModel - Solar/Lunar return charts
    ├── AspectModel - Planetary aspect data
    ├── ZodiacSignModel - Zodiac sign properties
    ├── RelationshipScoreModel - Synastry compatibility scores
    ├── HouseComparisonModel - House overlay analysis
    ├── SingleChartDataModel - Single chart visualization data
    └── DualChartDataModel - Dual chart visualization data

All models inherit from SubscriptableBaseModel which provides dictionary-style
access to fields while maintaining Pydantic validation.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from datetime import datetime, timedelta
from typing import Union, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, field_validator, model_validator
from kerykeion.schemas.kr_literals import AspectName, ClassicalPlanet, VocAspectName, VocTargetPlanet

# Import directly from kr_literals (NOT from the kerykeion.schemas package
# __init__): importing from the package while the package is importing this
# module works only because of the import order in schemas/__init__.py, and
# any reordering there would break the whole package with a partial-import
# error.
from kerykeion.schemas.kr_literals import (
    LunarPhaseEmoji,
    LunarPhaseName,
    AstrologicalPoint,
    Houses,
    Quality,
    Element,
    Sign,
    ZodiacType,
    SignNumbers,
    PointType,
    SiderealMode,
    HousesSystemIdentifier,
    SignsEmoji,
    RelationshipScoreDescription,
    PerspectiveType,
    AspectMovementType,
)
from kerykeion.schemas.kr_literals import ReturnType, DominantMethod

# Type alias for any astrological subject model (birth chart, composite, or return)
AnySubjectModel = Union["AstrologicalSubjectModel", "CompositeSubjectModel", "PlanetReturnModel"]


class SubscriptableBaseModel(BaseModel):
    """
    Pydantic BaseModel with subscriptable support, so you can access the fields as if they were a dictionary.
    """

    def __getitem__(self, key):
        """Get an attribute using dictionary-style access."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Set an attribute using dictionary-style access."""
        setattr(self, key, value)

    def __delitem__(self, key):
        """Delete an attribute using dictionary-style access."""
        delattr(self, key)

    def get(self, key, default=None):
        """Get an attribute with a default value if not found."""
        return getattr(self, key, default)


class LunarPhaseModel(SubscriptableBaseModel):
    """
    Model representing lunar phase information.

    Attributes:
        degrees_between_s_m: Angular separation between Sun and Moon in degrees.
        moon_phase: Numerical phase identifier for the Moon.
        moon_emoji: Emoji representation of the lunar phase.
        moon_phase_name: Text name of the lunar phase.
    """

    degrees_between_s_m: Union[float, int]
    moon_phase: int
    moon_emoji: LunarPhaseEmoji
    moon_phase_name: LunarPhaseName


class MoonPhaseSunPositionModel(SubscriptableBaseModel):
    """
    Apparent solar position details for a given moment.

    Attributes:
        altitude: Sun altitude above the horizon in degrees.
        azimuth: Sun azimuth angle in degrees.
        distance: Distance from Earth to Sun in kilometers.
    """

    altitude: Optional[float] = None
    azimuth: Optional[float] = None
    distance: Optional[float] = None


class MoonPhaseSolarEclipseModel(SubscriptableBaseModel):
    """
    Information about a solar eclipse event relative to the current moment.

    This model is intentionally generic so it can be populated either by
    internal calculations or external services.
    """

    timestamp: Optional[int] = None
    datestamp: Optional[str] = None
    type: Optional[str] = None
    visibility_regions: Optional[str] = None


class MoonPhaseSunInfoModel(SubscriptableBaseModel):
    """
    Summary information about the Sun for the lunar phase context.

    ``sunrise``, ``sunset`` and ``solar_noon`` are timezone-aware ``datetime``
    objects in the subject's **local** timezone (the moon-phase context is
    presented for the subject's civil day); ``day_length`` is a ``timedelta``.
    This differs from :class:`SunTimesModel`, whose instants are in UTC. All
    fields are optional and are populated as available — e.g. during polar
    day/night a full sunrise→sunset pair may be missing, leaving ``solar_noon``
    and ``day_length`` as ``None``.

    Attributes:
        sunrise: Moment of sunrise (subject-local), or ``None``.
        sunset: Moment of sunset (subject-local), or ``None``.
        solar_noon: Midpoint between sunrise and sunset (subject-local), or ``None``.
        day_length: Duration from sunrise to sunset, or ``None``.
        position: Apparent solar position (altitude/azimuth/distance).
        next_solar_eclipse: Next global solar eclipse, if computed.
    """

    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    solar_noon: Optional[datetime] = None
    day_length: Optional[timedelta] = None
    position: Optional[MoonPhaseSunPositionModel] = None
    next_solar_eclipse: Optional[MoonPhaseSolarEclipseModel] = None

    @field_validator("sunrise", "sunset", "solar_noon")
    @classmethod
    def _require_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Enforce the documented timezone-aware (subject-local) contract.

        The annotation stays ``Optional[datetime]`` so ``get_type_hints()`` /
        FastAPI schema introspection is unaffected; only naive values are rejected.
        """
        if v is not None and v.tzinfo is None:
            raise ValueError("sun times must be timezone-aware datetimes")
        return v


class MoonPhaseZodiacModel(SubscriptableBaseModel):
    """
    Simple zodiac snapshot for the current Sun–Moon configuration.

    Attributes:
        sun_sign: Zodiac sign of the Sun.
        moon_sign: Zodiac sign of the Moon.
    """

    sun_sign: Sign
    moon_sign: Sign


class MoonPhaseMoonPositionModel(SubscriptableBaseModel):
    """
    Apparent lunar position details for a given moment.

    Attributes:
        altitude: Moon altitude above the horizon in degrees.
        azimuth: Moon azimuth angle in degrees.
        distance: Distance from Earth to Moon (kilometers).
        parallactic_angle: Parallactic angle in degrees.
        phase_angle: Phase angle Sun–Moon in degrees.
    """

    altitude: Optional[float] = None
    azimuth: Optional[float] = None
    distance: Optional[float] = None
    parallactic_angle: Optional[float] = None
    phase_angle: Optional[float] = None


class MoonPhaseViewingEquipmentModel(SubscriptableBaseModel):
    """
    Recommended observing equipment for the current lunar phase.
    """

    filters: Optional[str] = None
    telescope: Optional[str] = None
    best_magnification: Optional[str] = None


class MoonPhaseViewingConditionsModel(SubscriptableBaseModel):
    """
    Qualitative viewing conditions and equipment recommendations.
    """

    phase_quality: Optional[str] = None
    recommended_equipment: Optional[MoonPhaseViewingEquipmentModel] = None


class MoonPhaseVisibilityModel(SubscriptableBaseModel):
    """
    Visibility information for the current Moon.
    """

    visible_hours: Optional[float] = None
    best_viewing_time: Optional[str] = None
    visibility_rating: Optional[str] = None
    illumination: Optional[str] = None
    viewing_conditions: Optional[MoonPhaseViewingConditionsModel] = None


class MoonPhaseEventMomentModel(SubscriptableBaseModel):
    """
    Generic representation of a key lunar event (e.g. last / next Full Moon).
    """

    timestamp: Optional[int] = None
    datestamp: Optional[str] = None
    days_ago: Optional[int] = None
    days_ahead: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None


class MoonPhaseMajorPhaseWindowModel(SubscriptableBaseModel):
    """
    Container for the last and next occurrence of a major lunar phase.
    """

    last: Optional[MoonPhaseEventMomentModel] = None
    next: Optional[MoonPhaseEventMomentModel] = None


class MoonPhaseUpcomingPhasesModel(SubscriptableBaseModel):
    """
    Overview of surrounding major lunar phases (new, first quarter, full, last quarter).
    """

    new_moon: Optional[MoonPhaseMajorPhaseWindowModel] = None
    first_quarter: Optional[MoonPhaseMajorPhaseWindowModel] = None
    full_moon: Optional[MoonPhaseMajorPhaseWindowModel] = None
    last_quarter: Optional[MoonPhaseMajorPhaseWindowModel] = None


class MoonPhaseIlluminationDetailsModel(SubscriptableBaseModel):
    """
    Numeric illumination details for the Moon at the given moment.

    Note:
        ``phase_angle`` holds the Sun–Moon **elongation** (the geocentric
        Sun–Earth–Moon separation: ~0° at New Moon, ~180° at Full Moon), not the
        astronomical phase angle (Sun–Moon–Earth, which is ~180° − elongation).
        ``visible_fraction`` is computed correctly from this elongation.
    """

    percentage: Optional[float] = None
    visible_fraction: Optional[float] = None
    phase_angle: Optional[float] = None


class MoonPhaseMoonDetailedModel(SubscriptableBaseModel):
    """
    Detailed Moon information grouped under a single node.
    """

    position: Optional[MoonPhaseMoonPositionModel] = None
    visibility: Optional[MoonPhaseVisibilityModel] = None
    upcoming_phases: Optional[MoonPhaseUpcomingPhasesModel] = None
    illumination_details: Optional[MoonPhaseIlluminationDetailsModel] = None


class MoonPhaseOptimalViewingPeriodModel(SubscriptableBaseModel):
    """
    Suggested optimal viewing window for the Moon.
    """

    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_hours: Optional[float] = None
    viewing_quality: Optional[str] = None
    recommendations: Optional[list[str]] = None


class MoonPhaseEventsModel(SubscriptableBaseModel):
    """
    Convenience container for event-style lunar information.
    """

    moonrise_visible: Optional[bool] = None
    moonset_visible: Optional[bool] = None
    optimal_viewing_period: Optional[MoonPhaseOptimalViewingPeriodModel] = None


class MoonPhaseEclipseModel(SubscriptableBaseModel):
    """
    Information about a lunar eclipse event relative to the current moment.
    """

    timestamp: Optional[int] = None
    datestamp: Optional[str] = None
    type: Optional[str] = None
    visibility_regions: Optional[str] = None


class MoonPhaseMoonSummaryModel(SubscriptableBaseModel):
    """
    High-level summary of the current lunar phase and basic context.

    This model mirrors the structure used by web APIs for moon phase
    information and is designed to be populated by MoonPhaseDetailsFactory.
    """

    phase: Optional[float] = None
    phase_name: Optional[LunarPhaseName] = None
    major_phase: Optional[str] = None
    stage: Optional[str] = None
    illumination: Optional[str] = None
    age_days: Optional[int] = None
    lunar_cycle: Optional[str] = None
    emoji: Optional[LunarPhaseEmoji] = None
    zodiac: Optional[MoonPhaseZodiacModel] = None
    moonrise: Optional[str] = None
    moonrise_timestamp: Optional[int] = None
    moonset: Optional[str] = None
    moonset_timestamp: Optional[int] = None
    next_lunar_eclipse: Optional[MoonPhaseEclipseModel] = None
    detailed: Optional[MoonPhaseMoonDetailedModel] = None
    events: Optional[MoonPhaseEventsModel] = None


class MoonPhaseLocationModel(SubscriptableBaseModel):
    """
    Location metadata for lunar phase context.
    """

    latitude: Optional[str] = None
    longitude: Optional[str] = None
    precision: Optional[int] = None
    using_default_location: Optional[bool] = None
    note: Optional[str] = None


class MoonPhaseOverviewModel(SubscriptableBaseModel):
    """
    Top-level lunar phase context model.

    This model groups together timestamp information, Sun summary, Moon summary,
    and basic location data into a single structure suitable for API responses
    or serialization.
    """

    timestamp: int
    datestamp: str
    sun: Optional[MoonPhaseSunInfoModel] = None
    moon: MoonPhaseMoonSummaryModel
    location: Optional[MoonPhaseLocationModel] = None


# ---------------------------------------------------------------------------
# Sun times · planetary (Chaldean) hours · void-of-course Moon
# ---------------------------------------------------------------------------
# Models backing SunTimesFactory, PlanetaryHoursFactory and
# VoidOfCourseMoonFactory. All instants are timezone-aware UTC ``datetime``
# objects (so consumers can localise freely); durations are ``timedelta``.


class SunTimesModel(SubscriptableBaseModel):
    """
    Sunrise, sunset, solar noon and day length for a civil date at a location.

    All instants are timezone-aware ``datetime`` objects in UTC. During polar day
    or polar night the Sun may not provide a complete sunrise -> sunset pair, so
    ``solar_noon`` and ``day_length`` are ``None`` and the matching
    ``is_polar_day`` / ``is_polar_night`` flag is set. On transition dates,
    ``sunrise`` or ``sunset`` can be present independently, and a paired
    ``sunset`` may fall on the following civil date (so ``day_length`` can
    exceed 24 hours) when daylight spans local midnight at high latitudes.

    Attributes:
        date: Civil date (``YYYY-MM-DD``) in the requested timezone.
        timezone: IANA timezone identifier the date is anchored to.
        latitude: Observer latitude in degrees (north positive).
        longitude: Observer longitude in degrees (east positive).
        sunrise: Moment of sunrise (upper limb, atmospheric refraction applied), or ``None``.
        sunset: Moment of sunset (upper limb, atmospheric refraction applied), or ``None``.
        solar_noon: Midpoint between a paired sunrise and later sunset, or ``None``.
        day_length: Duration from sunrise to a later paired sunset, or ``None``.
        is_polar_day: ``True`` when the Sun stays above the horizon all day.
        is_polar_night: ``True`` when the Sun stays below the horizon all day.
        civil_dawn / civil_dusk: Sun at -6 degrees (morning / evening), or ``None``.
        nautical_dawn / nautical_dusk: Sun at -12 degrees, or ``None``.
        astronomical_dawn / astronomical_dusk: Sun at -18 degrees, or ``None``.
    """

    date: str
    timezone: str
    latitude: float
    longitude: float
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    solar_noon: Optional[datetime] = None
    day_length: Optional[timedelta] = None
    is_polar_day: bool = False
    is_polar_night: bool = False
    civil_dawn: Optional[datetime] = None
    civil_dusk: Optional[datetime] = None
    nautical_dawn: Optional[datetime] = None
    nautical_dusk: Optional[datetime] = None
    astronomical_dawn: Optional[datetime] = None
    astronomical_dusk: Optional[datetime] = None


class PlanetaryHourModel(SubscriptableBaseModel):
    """
    A single planetary hour within the day's 24-hour Chaldean sequence.

    Attributes:
        index: 1-based position in the sequence (1-24).
        ruler: Classical planet ruling the hour.
        is_diurnal: ``True`` for the 12 day hours (sunrise→sunset), ``False`` for
            the 12 night hours (sunset→next sunrise).
        start: Hour start, timezone-aware UTC datetime.
        end: Hour end, timezone-aware UTC datetime.
    """

    index: int
    ruler: ClassicalPlanet
    is_diurnal: bool
    start: datetime
    end: datetime


class PlanetaryHoursModel(SubscriptableBaseModel):
    """
    The planetary (Chaldean) hours for the planetary day containing a moment.

    Day and night are split at true sunrise/sunset: the twelve day hours divide
    sunrise→sunset and the twelve night hours divide sunset→next sunrise, so the
    hours are generally unequal in length. The first hour of the day is ruled by
    the planet of the weekday; the remaining hours follow the descending Chaldean
    order (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon), cycling.

    Attributes:
        date: Civil date of the planetary day's sunrise, in the requested timezone.
        timezone: IANA timezone identifier.
        latitude: Observer latitude in degrees.
        longitude: Observer longitude in degrees.
        day_ruler: Planet ruling the whole planetary day (determined by weekday).
        current_index: 1-based index of the hour containing the requested moment.
        current_ruler: Ruler of the hour containing the requested moment.
        sunrise: Sunrise opening the day hours (UTC).
        sunset: Sunset dividing day and night hours (UTC).
        next_sunrise: Sunrise closing the night hours (UTC).
        hours: All 24 planetary hours in chronological order.
    """

    date: str
    timezone: str
    latitude: float
    longitude: float
    day_ruler: ClassicalPlanet
    current_index: int
    current_ruler: ClassicalPlanet
    sunrise: datetime
    sunset: datetime
    next_sunrise: datetime
    hours: list[PlanetaryHourModel] = Field(default_factory=list)


_VOC_ASPECT_DEGREES: dict[VocAspectName, float] = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}


class VoidOfCourseAspectModel(SubscriptableBaseModel):
    """
    An exact Ptolemaic aspect the Moon perfects to another body.

    Attributes:
        planet: The body the Moon aspects (Sun, Mercury, Venus, Mars, Jupiter, Saturn).
        aspect: Aspect name (conjunction, sextile, square, trine, opposition).
        aspect_degrees: The aspect's exact angle in degrees (0, 60, 90, 120, 180).
        exact_time: Moment the aspect perfects, timezone-aware UTC datetime.
    """

    planet: VocTargetPlanet
    aspect: VocAspectName
    aspect_degrees: float
    exact_time: datetime

    @model_validator(mode="after")
    def _validate_voc_aspect_degrees(self) -> "VoidOfCourseAspectModel":
        expected_degrees = _VOC_ASPECT_DEGREES[self.aspect]
        if self.aspect_degrees != expected_degrees:
            raise ValueError(f"aspect_degrees must be {expected_degrees:g} for {self.aspect!r}.")
        return self


class VoidOfCourseMoonModel(SubscriptableBaseModel):
    """
    Void-of-course state of the Moon at a given moment.

    The Moon is *void of course* from the instant it perfects its last exact
    Ptolemaic aspect to a traditional planet while in its current sign, until it
    ingresses into the next sign. Because it depends only on geocentric ecliptic
    longitudes, the result is independent of the observer's location.

    Attributes:
        is_void_of_course: ``True`` if the queried moment lies in the void window.
        moon_sign: The sign the Moon currently occupies.
        next_sign: The sign the Moon ingresses into next.
        ingress: Moment the Moon enters ``next_sign`` (UTC); equals ``void_end``.
        void_start: Start of the void window — the Moon's last in-sign aspect, or
            the sign-entry moment if the Moon makes no aspect during the sign.
        void_end: End of the void window, equal to ``ingress``.
        last_aspect: The last exact aspect before ingress, or ``None`` when the
            Moon makes no aspect while in the sign.
        next_aspect: The Moon's first exact aspect *after* it ingresses into
            ``next_sign`` — the aspect that ends the void-of-course lull. In
            practice always present; ``None`` only in the degenerate case the Moon
            makes no aspect at all while traversing the next sign.
    """

    is_void_of_course: bool
    moon_sign: Sign
    next_sign: Sign
    ingress: datetime
    void_start: datetime
    void_end: datetime
    last_aspect: Optional[VoidOfCourseAspectModel] = None
    next_aspect: Optional[VoidOfCourseAspectModel] = None


class KerykeionPointModel(SubscriptableBaseModel):
    """
    Model representing an astrological celestial point or house cusp.

    This model contains comprehensive information about celestial objects
    (planets, points) or house cusps including their zodiacal position,
    sign placement, and metadata.

    Attributes:
        name: The name of the celestial point or house.
        quality: Astrological quality (Cardinal, Fixed, Mutable).
        element: Astrological element (Fire, Earth, Air, Water).
        sign: The zodiac sign the point is located in.
        sign_num: Numerical identifier for the zodiac sign (0-11).
        position: Position within the sign (0-30 degrees).
        abs_pos: Absolute position in the zodiac (0-360 degrees).
        emoji: Unicode emoji representing the point or sign.
        point_type: Type of the celestial point (Planet, House, etc.).
        house: House placement of the point (optional).
        retrograde: Whether the point is in retrograde motion (optional).
        speed: Daily motion in degrees/day along the ecliptic. Negative values
            indicate retrograde motion. For house cusps this is the cusp
            progression rate driven by diurnal rotation. For fixed stars this
            is the slow drift due to precession (~50 arcsec/year). Added in v5.12.
        declination: Declination in degrees north (+) or south (-) of the
            celestial equator, computed from equatorial coordinates via
            ``ephe.calc_ut`` with ``FLG_EQUATORIAL``. Useful for parallel and
            contra-parallel aspects. Added in v5.12.
        magnitude: Apparent visual magnitude of fixed stars (lower = brighter;
            e.g. Sirius = -1.46, Regulus = 1.35). Only populated for fixed
            star points; ``None`` for planets and calculated points. Retrieved
            via ``ephe.fixstar2_mag``. Added in v5.12.
    """

    name: Union[AstrologicalPoint, Houses, str]
    quality: Quality
    element: Element
    sign: Sign
    sign_num: SignNumbers
    position: float
    abs_pos: float
    emoji: str
    point_type: PointType
    house: Optional[Houses] = None
    retrograde: Optional[bool] = None
    speed: Optional[float] = Field(
        default=None,
        description="Daily motion in degrees/day. Negative = retrograde. Populated for planets, house cusps, and fixed stars.",
    )
    declination: Optional[float] = Field(
        default=None, description="Declination in degrees north (+) or south (-) of the celestial equator."
    )
    ecliptic_latitude: Optional[float] = Field(
        default=None,
        description="Ecliptic latitude in degrees north (+) or south (-) of the ecliptic plane. "
        "The body's true distance off the ecliptic (the Sun is ~0; the Moon reaches ±5°, Pluto ±17°). "
        "Populated for planets and bodies; used for accurate local-space azimuth/altitude. Added in v6.0.",
    )
    magnitude: Optional[float] = Field(
        default=None, description="Apparent visual magnitude (fixed stars only). Lower = brighter."
    )
    near_point: Optional[str] = Field(default=None, description="Nearest chart point for fixed-star discovery results.")
    orb: Optional[float] = Field(
        default=None, description="Orb from the nearest chart point in fixed-star discovery results."
    )
    aspect: Optional[str] = Field(default=None, description="Aspect name for discovery results, usually 'conjunction'.")
    longitude: Optional[float] = Field(
        default=None, description="Ecliptic longitude for discovery consumers. Mirrors abs_pos."
    )
    latitude: Optional[float] = Field(default=None, description="Ecliptic latitude for fixed-star discovery results.")
    degree: Optional[float] = Field(
        default=None, description="Degree within sign for discovery consumers. Mirrors position."
    )
    # Essential Dignities (v6.0)
    decan_number: Optional[int] = Field(
        default=None, description="Decan number (1-3) within the sign, each spanning 10 degrees."
    )
    decan_ruler: Optional[str] = Field(default=None, description="Ruling planet of the Chaldean decan.")
    term_ruler: Optional[str] = Field(default=None, description="Ruling planet of the Egyptian term (bound).")
    essential_dignity: Optional[str] = Field(
        default=None,
        description="Highest active essential dignity (e.g. 'Domicile', 'Exaltation', 'Detriment', 'Fall', 'Peregrine').",
    )
    dignity_score: Optional[int] = Field(
        default=None,
        description=(
            "Net Ptolemaic essential dignity score: the SUM of every applicable "
            "dignity (domicile +5, exaltation +4, triplicity +3, term +2, face +1) "
            "and debility (detriment -5, fall -4). Because several can coincide "
            "(e.g. Mercury in Virgo is domicile + exaltation + term), the achievable "
            "range is -9 to +11, not +/-5."
        ),
    )
    # Nakshatra (Vedic lunar mansions, v6.0)
    nakshatra: Optional[str] = Field(
        default=None, description="Name of the Nakshatra (Vedic lunar mansion), e.g. 'Rohini'."
    )
    nakshatra_number: Optional[int] = Field(default=None, description="Nakshatra number (1-27).")
    nakshatra_pada: Optional[int] = Field(
        default=None, description="Pada (quarter) within the Nakshatra (1-4), each spanning 3°20'."
    )
    nakshatra_lord: Optional[str] = Field(default=None, description="Vimsottari Dasha lord of the Nakshatra.")
    gauquelin_sector: Optional[float] = Field(
        default=None,
        description="Gauquelin sector position (1-36). Sectors are numbered clockwise from the eastern horizon. "
        "Sectors near 1 and 36 (the 'plus zones') are traditionally considered most powerful.",
    )
    # Local Space / Astro-Cartography (v6.0)
    azimuth: Optional[float] = Field(
        default=None,
        description="Azimuth (compass bearing) in degrees from the observer's location. "
        "0=South, 90=West, 180=North, 270=East (Swiss Ephemeris convention). "
        "Populated when calculate_local_space=True. Added in v6.0.",
    )
    altitude_above_horizon: Optional[float] = Field(
        default=None,
        description="Altitude above the horizon in degrees from the observer's location. "
        "Positive=above horizon, negative=below. Populated when calculate_local_space=True. Added in v6.0.",
    )
    # Out of Bounds (v6.0)
    is_out_of_bounds: Optional[bool] = Field(
        default=None,
        description="True when the planet's declination exceeds the Sun's maximum declination "
        "(the true obliquity of the ecliptic, ~23.44 deg). OOB planets are considered to "
        "operate outside normal boundaries in psychological/evolutionary astrology. Added in v6.0.",
    )


class NutationObliquityModel(SubscriptableBaseModel):
    """
    Nutation and obliquity parameters for a given moment.

    These values describe the orientation of Earth's axis and its
    short-period oscillations, computed via ``ephe.calc_ut(jd, ephe.ECL_NUT)``.

    Added in v6.0.
    """

    true_obliquity: float = Field(description="True (apparent) obliquity of the ecliptic in degrees.")
    mean_obliquity: float = Field(description="Mean obliquity of the ecliptic in degrees (without nutation).")
    nutation_longitude: float = Field(description="Nutation in longitude (delta-psi) in degrees.")
    nutation_obliquity: float = Field(description="Nutation in obliquity (delta-epsilon) in degrees.")


class AstrologicalBaseModel(SubscriptableBaseModel):
    """
    Base model containing common fields for all astrological subjects.

    This model serves as the foundation for all astrological chart types,
    providing standard location, time, and configuration data. It supports
    both complete charts (with full location/time data) and composite charts
    (where some fields may be optional).

    Attributes:
        name: Subject identifier or name.
        city: Location city (optional for composite charts).
        nation: Country code (optional for composite charts).
        lng: Longitude coordinate (optional for composite charts).
        lat: Latitude coordinate (optional for composite charts).
        tz_str: Timezone string (optional for composite charts).
        iso_formatted_local_datetime: Local datetime in ISO format (optional).
        iso_formatted_utc_datetime: UTC datetime in ISO format (optional).
        julian_day: Julian day number for astronomical calculations (optional).
        day_of_week: Day of the week (optional).
        zodiac_type: Type of zodiac system used (Tropical or Sidereal).
        sidereal_mode: Sidereal calculation mode (if applicable).
        houses_system_identifier: House system used for calculations.
        houses_system_name: Human-readable name for the house system.
        perspective_type: Astrological perspective (geocentric, heliocentric, etc.).
        ayanamsa_value: The computed ayanamsa offset in degrees for sidereal
            charts. This is the angular difference between tropical 0 Aries and
            sidereal 0 Aries at the chart's date/time, as determined by the
            selected sidereal mode. ``None`` for tropical charts. Added in v5.12.
        active_points: List of celestial points included in calculations.

    Celestial & house fields:
        Concrete subjects (``AstrologicalSubjectModel``, ``CompositeSubjectModel``,
        ``PlanetReturnModel``) add the computed chart points, each a
        :class:`KerykeionPointModel`: the planets and luminaries
        (``sun`` … ``pluto``), the chart axes (``ascendant``, ``medium_coeli``,
        ``descendant``, ``imum_coeli``), the lunar nodes and apogees
        (``mean_north_lunar_node`` / ``true_north_lunar_node`` and their south
        counterparts, ``mean_lilith`` / ``true_lilith``), ``chiron``, the Arabic Parts / lots
        (``pars_fortunae``, ``pars_spiritus``, ``pars_amoris``, ``pars_fidei``),
        and the twelve houses (``first_house`` … ``twelfth_house``). Which of these
        are populated is governed by ``active_points`` (and ``active_fixed_stars``
        for the ``fixed_stars`` array below).

    Fixed Stars (v6 -- unified array):
        All fixed stars (any name from the libephemeris catalog) live in
        ``fixed_stars: list[KerykeionPointModel]``. No more typed per-star
        fields. Use ``subject.find_fixed_star("Regulus")`` for lookup by name.
        Stars are populated when their names are passed via the
        ``active_fixed_stars`` parameter to ``AstrologicalSubjectFactory``.
    """

    # Common identification data
    name: str

    # Common location data (optional for composite charts)
    city: Optional[str] = None
    nation: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
    tz_str: Optional[str] = None

    # Common time data (optional for composite charts)
    iso_formatted_local_datetime: Optional[str] = None
    iso_formatted_utc_datetime: Optional[str] = None
    julian_day: Optional[float] = None
    day_of_week: Optional[str] = None

    # Common configuration
    zodiac_type: ZodiacType
    sidereal_mode: Optional[SiderealMode] = None
    houses_system_identifier: HousesSystemIdentifier
    houses_system_name: str
    perspective_type: PerspectiveType
    ayanamsa_value: Optional[float] = Field(
        default=None,
        description="Ayanamsa offset in degrees for sidereal charts (tropical 0 Aries minus sidereal 0 Aries). None for tropical charts.",
    )
    custom_ayanamsa_t0: Optional[float] = Field(
        default=None,
        description="Reference epoch (Julian Day) for USER sidereal mode. None unless sidereal_mode is USER.",
    )
    custom_ayanamsa_ayan_t0: Optional[float] = Field(
        default=None,
        description="Ayanamsa value in degrees at the reference epoch for USER sidereal mode. None unless sidereal_mode is USER.",
    )

    @model_validator(mode="after")
    def _validate_user_ayanamsa(self) -> "AstrologicalBaseModel":
        if self.zodiac_type == "Sidereal" and self.sidereal_mode is None:
            # Enforce the invariant in the model rather than masking it at display
            # time: a sidereal chart must declare the ayanamsa used for its
            # positions. The factory auto-defaults this, so only direct/manual
            # construction (the ambiguous case) is rejected.
            raise ValueError("sidereal_mode is required when zodiac_type='Sidereal'.")
        if self.sidereal_mode == "USER":
            if self.custom_ayanamsa_t0 is None or self.custom_ayanamsa_ayan_t0 is None:
                raise ValueError(
                    "custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0 are both required when sidereal_mode is 'USER'."
                )
        has_t0 = self.custom_ayanamsa_t0 is not None
        has_ayan = self.custom_ayanamsa_ayan_t0 is not None
        if has_t0 != has_ayan:
            raise ValueError("custom_ayanamsa_t0 and custom_ayanamsa_ayan_t0 must be both set or both None.")
        return self

    # Common celestial points
    # Main planets (all optional to support selective calculations)
    sun: Optional[KerykeionPointModel] = None
    moon: Optional[KerykeionPointModel] = None
    mercury: Optional[KerykeionPointModel] = None
    venus: Optional[KerykeionPointModel] = None
    mars: Optional[KerykeionPointModel] = None
    jupiter: Optional[KerykeionPointModel] = None
    saturn: Optional[KerykeionPointModel] = None
    uranus: Optional[KerykeionPointModel] = None
    neptune: Optional[KerykeionPointModel] = None
    pluto: Optional[KerykeionPointModel] = None

    # Common axes
    ascendant: Optional[KerykeionPointModel] = None
    descendant: Optional[KerykeionPointModel] = None
    medium_coeli: Optional[KerykeionPointModel] = None
    imum_coeli: Optional[KerykeionPointModel] = None

    # Common optional planets
    chiron: Optional[KerykeionPointModel] = None
    earth: Optional[KerykeionPointModel] = None
    pholus: Optional[KerykeionPointModel] = None

    # Lilith Points
    mean_lilith: Optional[KerykeionPointModel] = None
    true_lilith: Optional[KerykeionPointModel] = None
    interpolated_lilith: Optional[KerykeionPointModel] = None

    # Priapus Points (opposite of Lilith, v6.0)
    mean_priapus: Optional[KerykeionPointModel] = None
    true_priapus: Optional[KerykeionPointModel] = None

    # Lunar apse points (v6.0)
    interpolated_perigee: Optional[KerykeionPointModel] = None
    white_moon: Optional[KerykeionPointModel] = None

    # Asteroids
    ceres: Optional[KerykeionPointModel] = None
    pallas: Optional[KerykeionPointModel] = None
    juno: Optional[KerykeionPointModel] = None
    vesta: Optional[KerykeionPointModel] = None

    # Trans-Neptunian Objects
    eris: Optional[KerykeionPointModel] = None
    sedna: Optional[KerykeionPointModel] = None
    haumea: Optional[KerykeionPointModel] = None
    makemake: Optional[KerykeionPointModel] = None
    ixion: Optional[KerykeionPointModel] = None
    orcus: Optional[KerykeionPointModel] = None
    quaoar: Optional[KerykeionPointModel] = None

    # Uranian / Hamburg School hypothetical planets
    cupido: Optional[KerykeionPointModel] = None
    hades: Optional[KerykeionPointModel] = None
    zeus: Optional[KerykeionPointModel] = None
    kronos: Optional[KerykeionPointModel] = None
    apollon: Optional[KerykeionPointModel] = None
    admetos: Optional[KerykeionPointModel] = None
    vulkanus: Optional[KerykeionPointModel] = None
    poseidon: Optional[KerykeionPointModel] = None

    # Fixed Stars (v6 -- unified array, source: libephemeris catalog)
    # All fixed stars live here. Use ``find_fixed_star(name)`` for lookup.
    fixed_stars: list[KerykeionPointModel] = Field(
        default_factory=list,
        description="All calculated fixed stars (any name from the libephemeris catalog "
        "passed via the ``active_fixed_stars`` parameter). Use ``find_fixed_star(name)`` "
        "for case-insensitive lookup by IAU name or slug.",
    )

    # Active Midpoints (v6 -- sensitive points selected by the user)
    # Populated via the MidpointFactory workflow:
    #   ``MidpointFactory.compute_active_midpoint_points(subject, ["Sun_Moon", ...])``
    # then assigned to this field. The entries are KerykeionPointModel
    # objects with ``point_type='Midpoint'`` so the chart drawer can render
    # them like any other active point.
    active_midpoints: list[KerykeionPointModel] = Field(
        default_factory=list,
        description="Pairwise midpoints computed via "
        "``MidpointFactory.compute_active_midpoint_points`` and assigned to the subject. "
        "Each entry is a synthetic point on the shorter arc between two natal points; "
        "``point_type='Midpoint'`` and ``name`` follows the ``A_B_Midpoint`` convention.",
    )

    # Arabic Parts
    pars_fortunae: Optional[KerykeionPointModel] = None
    pars_spiritus: Optional[KerykeionPointModel] = None
    pars_amoris: Optional[KerykeionPointModel] = None
    pars_fidei: Optional[KerykeionPointModel] = None

    # Special Points
    vertex: Optional[KerykeionPointModel] = None
    anti_vertex: Optional[KerykeionPointModel] = None

    # Common houses
    first_house: KerykeionPointModel
    second_house: KerykeionPointModel
    third_house: KerykeionPointModel
    fourth_house: KerykeionPointModel
    fifth_house: KerykeionPointModel
    sixth_house: KerykeionPointModel
    seventh_house: KerykeionPointModel
    eighth_house: KerykeionPointModel
    ninth_house: KerykeionPointModel
    tenth_house: KerykeionPointModel
    eleventh_house: KerykeionPointModel
    twelfth_house: KerykeionPointModel

    # Lunar Nodes
    mean_north_lunar_node: Optional[KerykeionPointModel] = None
    true_north_lunar_node: Optional[KerykeionPointModel] = None
    mean_south_lunar_node: Optional[KerykeionPointModel] = None
    true_south_lunar_node: Optional[KerykeionPointModel] = None

    # Common lists and settings
    houses_names_list: list[Houses] = Field(description="Ordered list of houses names")
    active_points: list[AstrologicalPoint] = Field(
        description="List of active points in the chart or aspects calculations."
    )

    # Common lunar phase data (optional)
    lunar_phase: Optional[LunarPhaseModel] = Field(default=None, description="Lunar phase model")

    # Gauquelin sector cusps (v6.0)
    gauquelin_sector_cusps: Optional[list[float]] = Field(
        default=None,
        description="36 Gauquelin sector cusp positions as zodiacal longitudes (0-360). "
        "Cusp[i] is the boundary where sector i+1 starts. Sectors are unequal "
        "divisions of the diurnal arc. Populated when calculate_gauquelin=True. Added in v6.0.",
    )

    # Nutation/Obliquity (v6.0)
    nutation: Optional[NutationObliquityModel] = Field(
        default=None,
        description="Nutation and obliquity parameters for the chart moment. "
        "Populated when calculate_nutation=True. Added in v6.0.",
    )

    def find_fixed_star(self, name: str) -> Optional[KerykeionPointModel]:
        """Case-insensitive lookup in ``fixed_stars`` by IAU name or slug.

        Slug matching is normalized: spaces, dashes and underscores are
        interchangeable, casing is ignored. Returns ``None`` if no match.
        """
        target = name.strip().lower().replace(" ", "_").replace("-", "_")
        for star in self.fixed_stars:
            star_slug = (star.name or "").strip().lower().replace(" ", "_").replace("-", "_")
            if star_slug == target:
                return star
        return None


class AstrologicalSubjectModel(AstrologicalBaseModel):
    """
    Complete astrological subject model for individual birth or event charts.

    This model represents a fully-specified astrological chart with all required
    location and time data. It extends AstrologicalBaseModel by making location
    and time fields mandatory.

    Used for:
        - Natal (birth) charts
        - Event charts
        - Horary charts

    Attributes:
        year: Birth/event year.
        month: Birth/event month (1-12).
        day: Birth/event day of month.
        hour: Birth/event hour (0-23).
        minute: Birth/event minute (0-59).
        city: City name (required).
        nation: Country code (required).
        lat: Latitude coordinate (required).
        lng: Longitude coordinate (required).
        tz_str: Timezone string e.g. 'Europe/Rome' (required).
    """

    # Override base model to make location and time data required for subjects
    city: str
    nation: str
    lng: float
    lat: float
    tz_str: str
    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str
    julian_day: float
    day_of_week: str

    # Specific birth/event data
    year: int
    month: int
    day: int
    hour: int
    minute: int

    # Sect (diurnal/nocturnal classification)
    is_diurnal: bool


class CompositeSubjectModel(AstrologicalBaseModel):
    """
    Composite chart model for relationship analysis.

    A composite chart is created by calculating the midpoint between
    corresponding planets/points of two individual charts. It represents
    the relationship as a separate entity.

    Attributes:
        first_subject: First person's astrological data.
        second_subject: Second person's astrological data.
        composite_chart_type: Type identifier for the composite calculation method.
    """

    # Specific composite data
    first_subject: AstrologicalSubjectModel
    second_subject: AstrologicalSubjectModel
    composite_chart_type: str


class PlanetReturnModel(AstrologicalBaseModel):
    """
    Planetary return chart model.

    A planetary return occurs when a transiting planet returns to the exact
    position it held in the natal chart. Solar returns (yearly) and lunar
    returns (monthly) are the most commonly used.

    Attributes:
        return_type: Type of return - 'Solar', 'Lunar', 'Heliocentric' or
            'Lunar_Node_Crossing'.
    """

    # Specific return data
    return_type: ReturnType = Field(
        description="Type of return: Solar, Lunar, Heliocentric or Lunar_Node_Crossing"
    )


class EphemerisDictModel(SubscriptableBaseModel):
    """
    Ephemeris data for a specific date.

    Contains planetary positions and house cusps for a given moment,
    typically used for generating ephemeris tables or transit lookups.

    Attributes:
        date: ISO formatted date string.
        planets: List of planetary positions.
        houses: List of house cusp positions.
    """

    date: str
    planets: list[KerykeionPointModel]
    houses: list[KerykeionPointModel]


class AspectModel(SubscriptableBaseModel):
    """
    Model representing an astrological aspect between two celestial points.

    An aspect is an angular relationship between two planets or points,
    measured along the ecliptic. Major aspects include conjunction (0°),
    opposition (180°), trine (120°), square (90°), and sextile (60°).

    Attributes:
        p1_name: Name of the first point (e.g., 'Sun').
        p1_owner: Owner/chart of the first point (e.g., 'John').
        p1_abs_pos: Absolute zodiacal position of first point (0-360°).
        p2_name: Name of the second point.
        p2_owner: Owner/chart of the second point.
        p2_abs_pos: Absolute zodiacal position of second point.
        aspect: Name of the aspect (e.g., 'conjunction', 'trine').
        orbit: Orb (deviation from exact aspect) in degrees.
        aspect_degrees: Exact degrees of the aspect type.
        diff: Angular difference between the points.
        p1: Numeric ID of first point.
        p2: Numeric ID of second point.
        p1_speed: Daily motion speed of first point in degrees.
        p2_speed: Daily motion speed of second point in degrees.
        aspect_movement: Whether aspect is applying, separating, or static.
    """

    p1_name: str
    p1_owner: str
    p1_abs_pos: float
    p2_name: str
    p2_owner: str
    p2_abs_pos: float
    aspect: str
    orbit: float
    aspect_degrees: int
    diff: float
    p1: int
    p2: int
    p1_speed: float = Field(default=0.0, description="Speed of the first point")
    p2_speed: float = Field(default=0.0, description="Speed of the second point")
    aspect_movement: AspectMovementType = Field(
        description="Indicates whether the aspect is applying (orb decreasing), "
        "separating (orb increasing), or static (no relative motion)."
    )


class ZodiacSignModel(SubscriptableBaseModel):
    """
    Model representing a zodiac sign with its properties.

    Contains the essential characteristics of a zodiac sign including
    its quality (Cardinal, Fixed, Mutable), element (Fire, Earth, Air, Water),
    and visual representation.

    Attributes:
        sign: Sign name (e.g., 'Ari', 'Tau', 'Gem').
        quality: Astrological quality (Cardinal, Fixed, Mutable).
        element: Astrological element (Fire, Earth, Air, Water).
        emoji: Unicode emoji for the sign.
        sign_num: Numerical position (0=Aries through 11=Pisces).
    """

    sign: Sign
    quality: Quality
    element: Element
    emoji: SignsEmoji
    sign_num: SignNumbers


class RelationshipScoreAspectModel(SubscriptableBaseModel):
    """
    Simplified aspect model for relationship scoring.

    Used in synastry analysis to track which aspects contribute
    to the compatibility score.

    Attributes:
        p1_name: First point name.
        p2_name: Second point name.
        aspect: Aspect type name.
        orbit: Orb in degrees.
    """

    p1_name: str
    p2_name: str
    aspect: str
    orbit: float


class ScoreBreakdownItemModel(SubscriptableBaseModel):
    """Single breakdown item explaining how points were earned."""

    rule: str = Field(description="Rule identifier (e.g., 'destiny_sign', 'sun_sun_major')")
    description: str = Field(description="Human-readable description of the rule")
    points: int = Field(description="Points awarded for this rule")
    details: Optional[str] = Field(default=None, description="Optional details (e.g., 'orbit: 1.5°')")


class RelationshipScoreModel(SubscriptableBaseModel):
    """Compatibility score result with breakdown and aspect details."""

    score_value: int
    score_description: RelationshipScoreDescription
    is_destiny_sign: bool
    aspects: list[RelationshipScoreAspectModel]
    score_breakdown: list[ScoreBreakdownItemModel] = Field(
        default_factory=list, description="Detailed breakdown of how the score was calculated"
    )
    subjects: list[AstrologicalSubjectModel]


class ActiveAspect(TypedDict):
    """Configuration for an active aspect type (name + orb in degrees)."""

    name: AspectName
    orb: float


class TransitMomentModel(SubscriptableBaseModel):
    """
    Model representing a snapshot of astrological transits at a specific moment in time.

    Captures all active aspects between moving celestial bodies and
    the fixed positions in a person's natal chart at a specific date and time.
    """

    date: str = Field(description="ISO 8601 formatted date and time of the transit moment.")
    aspects: list[AspectModel] = Field(description="List of aspects active at this specific moment.")


class SingleChartAspectsModel(SubscriptableBaseModel):
    """
    Model representing all aspects within a single astrological chart.

    This model can be used for any type of single chart analysis including:
    - Natal charts
    - Planetary return charts
    - Composite charts
    - Any other single chart type

    Contains the filtered and relevant aspects for the astrological subject
    based on configured orb settings.
    """

    subject: AnySubjectModel = Field(description="The astrological subject for which aspects were calculated.")
    aspects: list[AspectModel] = Field(
        description="List of calculated aspects within the chart, filtered based on orb settings."
    )
    # v6: stars from the libephemeris catalog are not part of the AstrologicalPoint
    # Literal (it would explode to thousands of entries). They appear here as
    # plain strings — the planet validation literal is widened to accept either.
    active_points: list[Union[AstrologicalPoint, str]] = Field(
        description="List of active points used in the calculation. Planets/asteroids/etc. "
        "use the AstrologicalPoint literal; catalog fixed stars use plain strings.",
    )
    active_aspects: list["ActiveAspect"] = Field(description="List of active aspects with their orb settings.")


class DualChartAspectsModel(SubscriptableBaseModel):
    """
    Model representing all aspects between two astrological charts.

    This model can be used for any type of dual chart analysis including:
    - Synastry (relationship compatibility)
    - Transit comparisons
    - Composite vs natal comparisons
    - Any other dual chart comparison

    Contains the filtered and relevant aspects between the two charts
    based on configured orb settings.
    """

    first_subject: AnySubjectModel = Field(description="The first astrological subject.")
    second_subject: AnySubjectModel = Field(description="The second astrological subject.")
    aspects: list[AspectModel] = Field(
        description="List of calculated aspects between the two charts, filtered based on orb settings."
    )
    # v6: see SingleChartAspectsModel.active_points — catalog fixed stars are plain strings.
    active_points: list[Union[AstrologicalPoint, str]] = Field(
        description="List of active points used in the calculation. Catalog fixed stars use plain strings.",
    )
    active_aspects: list["ActiveAspect"] = Field(description="List of active aspects with their orb settings.")


class TransitsTimeRangeModel(SubscriptableBaseModel):
    """
    Model representing a collection of transit moments for an astrological subject.

    This model holds a time series of transit snapshots, allowing analysis of
    planetary movements and their aspects to a natal chart over a period of time.
    """

    transits: list[TransitMomentModel] = Field(description="List of transit moments.")
    subject: Optional[AstrologicalSubjectModel] = Field(default=None, description="Astrological subject data.")
    dates: Optional[list[str]] = Field(default=None, description="ISO 8601 formatted dates of all transit moments.")


class TransitEventModel(SubscriptableBaseModel):
    """A single transit event — a grouped occurrence of an aspect between two points.

    Groups consecutive transit moments where the same aspect is active into
    a single event with applying start, exact moment, and separating end.
    """

    p1_name: str = Field(description="Transit planet name")
    p2_name: str = Field(description="Natal planet name")
    aspect: str = Field(description="Aspect name (e.g. 'conjunction')")
    applying_start: Optional[str] = Field(
        default=None,
        description="ISO datetime of the first in-orb sample. None when the applying phase "
        "was not sampled: either the event was truncated at the range start, or the "
        "sampling step was too coarse to capture the applying side of a fast pass "
        "(a Moon transit sampled daily, for instance — see the undersampling warning).",
    )
    exact_moment: str = Field(description="ISO datetime of closest approach (minimum orb)")
    separating_end: Optional[str] = Field(
        default=None,
        description="ISO datetime of the last in-orb sample. None when the separating phase "
        "falls outside the analysed range (event truncated at the range end).",
    )
    min_orb: float = Field(description="Minimum orb reached at exact_moment (degrees)")
    orb_rate: Optional[float] = Field(
        default=None,
        description="Rate of orb change right after the exact moment (degrees per day). "
        "None when the exact moment is the last in-orb sample.",
    )


class TransitEventsTimeRangeModel(SubscriptableBaseModel):
    """Collection of transit events over a time range."""

    events: list[TransitEventModel] = Field(description="Transit events, sorted by exact_moment")
    subject: Optional[AstrologicalSubjectModel] = Field(default=None, description="Natal subject")


class PointInHouseModel(SubscriptableBaseModel):
    """
    Represents an astrological point from one subject positioned within another subject's house.

    Captures point characteristics and its placement within the target subject's house system
    for house comparison analysis.

    Attributes:
        point_name: Name of the astrological point
        point_degree: Degree position within its sign
        point_sign: Zodiacal sign containing the point
        point_owner_name: Name of the subject who owns this point
        point_owner_house_number: House number in owner's chart
        point_owner_house_name: House name in owner's chart
        projected_house_number: House number in target subject's chart
        projected_house_name: House name in target subject's chart
        projected_house_owner_name: Name of the target subject
    """

    point_name: str
    """Name of the astrological point"""
    point_degree: float
    """Degree position of the point within its zodiacal sign"""
    point_sign: str
    """Zodiacal sign containing the point"""
    point_owner_name: str
    """Name of the subject who owns this point"""
    point_owner_house_number: Optional[int] = None
    """House number in owner's chart"""
    point_owner_house_name: Optional[str] = None
    """House name in owner's chart"""
    projected_house_number: int
    """House number in target subject's chart"""
    projected_house_name: str
    """House name in target subject's chart"""
    projected_house_owner_name: str
    """Name of the target subject"""


class HouseComparisonModel(SubscriptableBaseModel):
    """
    Bidirectional house comparison analysis between two astrological subjects.

    Contains results of how astrological points from each subject interact with
    the house system of the other subject.

    Attributes:
        first_subject_name: Name of the first subject
        second_subject_name: Name of the second subject
        first_points_in_second_houses: First subject's points in second subject's houses
        second_points_in_first_houses: Second subject's points in first subject's houses
    """

    first_subject_name: str
    """Name of the first subject"""
    second_subject_name: str
    """Name of the second subject"""
    first_points_in_second_houses: list[PointInHouseModel]
    """First subject's points positioned in second subject's houses"""
    second_points_in_first_houses: list[PointInHouseModel]
    """Second subject's points positioned in first subject's houses"""
    first_cusps_in_second_houses: list[PointInHouseModel] = Field(default_factory=list)
    """First subject's house cusps positioned in second subject's houses"""
    second_cusps_in_first_houses: list[PointInHouseModel] = Field(default_factory=list)
    """Second subject's house cusps positioned in first subject's houses"""


class ElementDistributionModel(SubscriptableBaseModel):
    """
    Model representing element distribution in a chart.

    Attributes:
        fire: Fire element points total
        earth: Earth element points total
        air: Air element points total
        water: Water element points total
        fire_percentage: Fire element percentage
        earth_percentage: Earth element percentage
        air_percentage: Air element percentage
        water_percentage: Water element percentage
    """

    fire: float
    earth: float
    air: float
    water: float
    fire_percentage: int
    earth_percentage: int
    air_percentage: int
    water_percentage: int


class QualityDistributionModel(SubscriptableBaseModel):
    """
    Model representing quality distribution in a chart.

    Attributes:
        cardinal: Cardinal quality points total
        fixed: Fixed quality points total
        mutable: Mutable quality points total
        cardinal_percentage: Cardinal quality percentage
        fixed_percentage: Fixed quality percentage
        mutable_percentage: Mutable quality percentage
    """

    cardinal: float
    fixed: float
    mutable: float
    cardinal_percentage: int
    fixed_percentage: int
    mutable_percentage: int


class SingleChartDataModel(SubscriptableBaseModel):
    """
    Chart data model for single-subject astrological charts.

    This model contains all pure data from single-subject charts including planetary
    positions, internal aspects, element/quality distributions, and location data.
    Used for chart types that analyze a single astrological subject.

    Supported chart types:
    - Natal: Birth chart with internal planetary aspects
    - Composite: Midpoint relationship chart with internal aspects
    - SingleReturnChart: Single planetary return with internal aspects

    Attributes:
        chart_type: Type of single chart (Natal, Composite, SingleReturnChart)
        subject: The astrological subject being analyzed
        aspects: Internal aspects within the chart
        element_distribution: Distribution of elemental energies
        quality_distribution: Distribution of modal qualities
        active_points: Celestial points included in calculations
        active_aspects: Aspect types and orb settings used
    """

    # Chart identification
    chart_type: Literal["Natal", "Composite", "SingleReturnChart"]

    # Single chart subject
    subject: AnySubjectModel

    # Internal aspects analysis
    aspects: list[AspectModel]

    # Element and quality distributions
    element_distribution: "ElementDistributionModel"
    quality_distribution: "QualityDistributionModel"

    # Configuration and metadata
    # Union with str: catalog fixed stars aspect the regular points (see the
    # aspects models), so their plain names must be representable here too.
    active_points: list[Union[AstrologicalPoint, str]]
    active_aspects: list["ActiveAspect"]


class DualChartDataModel(SubscriptableBaseModel):
    """
    Chart data model for dual-subject astrological charts.

    This model contains all pure data from dual-subject charts including both subjects,
    inter-chart aspects, house comparisons, relationship analysis, and
    element/quality distributions. Used for chart types that compare or overlay
    two astrological subjects.

    Distribution semantics differ by chart type: for **Synastry** the
    element/quality distributions are the COMBINED weighted points of both
    partners (a relationship reads both people together). For **Transit /
    DualReturnChart / Progression** they describe the FIRST (natal) subject
    only — the second subject is a different moment of the same person, so its
    points are not summed into the natal's temperament.

    Supported chart types:
    - Transit: Natal chart with current planetary transits
    - Synastry: Relationship compatibility between two people
    - DualReturnChart: Natal chart with planetary return comparison
    - Progression: Natal chart with secondary progression comparison

    Attributes:
        chart_type: Type of dual chart (Transit, Synastry, DualReturnChart, Progression)
        first_subject: Primary astrological subject (natal, base chart)
        second_subject: Secondary astrological subject (transit, partner, return)
        aspects: Inter-chart aspects between the two subjects
        house_comparison: House overlay analysis between subjects
        relationship_score: Compatibility scoring (synastry only)
        element_distribution: Elemental distribution — combined (both subjects)
            for Synastry, first-subject only for Transit/DualReturnChart/Progression
        quality_distribution: Modal distribution — combined (both subjects) for
            Synastry, first-subject only for Transit/DualReturnChart/Progression
        active_points: Celestial points included in calculations
        active_aspects: Aspect types and orb settings used
    """

    # Chart identification
    chart_type: Literal["Transit", "Synastry", "DualReturnChart", "Progression"]

    # Dual chart subjects
    first_subject: Union["AstrologicalSubjectModel", "CompositeSubjectModel", "PlanetReturnModel"]
    second_subject: Union["AstrologicalSubjectModel", "PlanetReturnModel"]

    # Inter-chart aspects analysis
    aspects: list[AspectModel]

    # House comparison analysis
    house_comparison: Optional["HouseComparisonModel"] = None

    # Relationship analysis (synastry only)
    relationship_score: Optional["RelationshipScoreModel"] = None

    # Combined element and quality distributions
    element_distribution: "ElementDistributionModel"
    quality_distribution: "QualityDistributionModel"

    # Configuration and metadata
    # Union with str: catalog fixed stars aspect the regular points (see the
    # aspects models), so their plain names must be representable here too.
    active_points: list[Union[AstrologicalPoint, str]]
    active_aspects: list["ActiveAspect"]


# Union type for all chart data models
ChartDataModel = Union[SingleChartDataModel, DualChartDataModel]


# =============================================================================
# PLANETARY PHENOMENA MODELS (v6.0)
# =============================================================================


class PlanetaryPhenomenaModel(SubscriptableBaseModel):
    """Observational phenomena for a single planet at a specific moment.

    Data comes from Swiss Ephemeris ``ephe.pheno_ut()``.
    """

    name: str = Field(description="Planet name")
    phase_angle: float = Field(description="Sun-planet-Earth angle in degrees")
    phase: float = Field(description="Illuminated fraction of the disk (0.0-1.0)")
    elongation: float = Field(description="Angular distance from the Sun in degrees")
    apparent_diameter: float = Field(description="Angular size as seen from Earth in degrees")
    apparent_magnitude: float = Field(description="Visual brightness (lower = brighter)")
    is_morning_star: Optional[bool] = Field(
        default=None, description="True if planet rises before the Sun (Mercury/Venus only)"
    )
    is_evening_star: Optional[bool] = Field(
        default=None, description="True if planet sets after the Sun (Mercury/Venus only)"
    )


class PlanetaryPhenomenaCollectionModel(SubscriptableBaseModel):
    """Collection of planetary phenomena for a specific datetime."""

    iso_datetime: str = Field(description="ISO 8601 formatted datetime")
    julian_day: float = Field(description="Julian Day number")
    phenomena: list[PlanetaryPhenomenaModel] = Field(description="Phenomena for each planet")


# =============================================================================
# DOMINANTS MODELS (v6.0)
# =============================================================================
# Public result types for the dominants calculator (see kerykeion.dominants).
# The shape is intentionally FIXED and school-agnostic: every category is always
# present so the type stays stable for runtime introspection (FastAPI /
# typing.get_type_hints). A school that does not compute a given category leaves
# its list empty and the matching ``dominant_*`` winner ``None``.


class DominantScoreModel(SubscriptableBaseModel):
    """A single ranked entry within one dominant category.

    The dominants calculator expresses every category (planets, signs, elements,
    modes, houses, polarities, hemispheres, quadrants) as a list of these scored
    entries, ordered from strongest to weakest. The representation is identical
    regardless of the calculation school, so consumers can render any category
    uniformly.

    Attributes:
        name: Identifier of the scored item within its category. The vocabulary
            depends on the category, e.g. a planet/point name ("Sun"), a sign
            code ("Ari"), an element ("Fire"), a mode ("Cardinal"), a house
            ("First_House"), a polarity ("Yang"/"Yin"), a hemisphere
            ("North"/"South"/"East"/"West") or a quadrant ("First_Quadrant").
        score: Raw, school-specific strength. Values are only comparable within
            the same category of the same result, because different schools use
            different scales.
        percentage: Share of the category total, normalized so a category's
            values sum to approximately 100. Convenient for display.
        rank: 1-based position within the category, where ``1`` is the most
            dominant. Ties are broken deterministically by each school.
        is_dominant: ``True`` when the entry qualifies as a dominant of its
            category (within the top-N and/or above the school's threshold).
    """

    name: str
    score: float
    percentage: float
    rank: int
    is_dominant: bool


class DominantBreakdownItemModel(SubscriptableBaseModel):
    """One transparency line explaining how a score was accumulated.

    Breakdown items are only populated when the caller asks for them
    (``include_score_breakdown=True``); they let a user audit *why* a planet or
    sign scored as it did. For the Almuten Figuris they also carry the
    per-place / per-dignity detail (``category="place"``).

    Attributes:
        category: The scoring dimension the item belongs to (e.g. "angularity",
            "aspect", "dignity", "rulership", "place").
        target: The item the points were awarded to (e.g. a planet name).
        rule: The specific rule that fired (e.g. "conjunction Ascendant",
            "Domicile", "ruler of MC").
        points: Signed points contributed by this rule.
        detail: Optional human-readable context (e.g. "orb 1.2°", "Sun place").
    """

    category: str
    target: str
    rule: str
    points: float
    detail: Optional[str] = None


class DominantsModel(SubscriptableBaseModel):
    """Result of a dominants calculation, in a fixed, school-agnostic shape.

    Every category is always present so the public type is stable for runtime
    introspection: a school that does not compute a given category simply leaves
    its list empty and the matching ``dominant_*`` winner ``None``. This lets one
    response schema serve every built-in school and any user-supplied custom
    strategy.

    Attributes:
        strategy_name: Human-readable name of the strategy that produced the
            result (e.g. "modern", "almuten_figuris", or a custom strategy's
            ``name``).
        method: The built-in method identifier, or ``None`` when a custom
            strategy was used.
        planets: Ranked planetary/point dominants.
        signs: Ranked sign dominants.
        elements: Ranked element dominants (Fire/Earth/Air/Water).
        qualities: Ranked mode/quality dominants (Cardinal/Fixed/Mutable).
        houses: Ranked house dominants.
        polarities: Ranked polarity dominants (Yang/Yin).
        hemispheres: Ranked hemisphere dominants (North/South/East/West).
        quadrants: Ranked quadrant dominants.
        dominant_planet: Convenience winner of ``planets`` (or ``None``).
        dominant_sign: Convenience winner of ``signs`` (or ``None``).
        dominant_element: Convenience winner of ``elements`` (or ``None``).
        dominant_quality: Convenience winner of ``qualities`` (or ``None``).
        dominant_house: Convenience winner of ``houses`` (or ``None``).
        score_breakdown: Optional audit trail of how the scores were earned.
    """

    strategy_name: str
    method: Optional[DominantMethod] = None
    planets: list[DominantScoreModel] = Field(default_factory=list)
    signs: list[DominantScoreModel] = Field(default_factory=list)
    elements: list[DominantScoreModel] = Field(default_factory=list)
    qualities: list[DominantScoreModel] = Field(default_factory=list)
    houses: list[DominantScoreModel] = Field(default_factory=list)
    polarities: list[DominantScoreModel] = Field(default_factory=list)
    hemispheres: list[DominantScoreModel] = Field(default_factory=list)
    quadrants: list[DominantScoreModel] = Field(default_factory=list)
    dominant_planet: Optional[str] = None
    dominant_sign: Optional[Sign] = None
    dominant_element: Optional[Element] = None
    dominant_quality: Optional[Quality] = None
    dominant_house: Optional[Houses] = None
    score_breakdown: list[DominantBreakdownItemModel] = Field(default_factory=list)


class TriplicityLordsModel(SubscriptableBaseModel):
    """The three Dorothean triplicity lords of an element, ordered by sect.

    In the Dorothean (Persian/Hellenistic) triplicity scheme each element has
    three rulers: a diurnal lord, a nocturnal lord, and a participating lord
    that operates in both sects. For a given chart sect the in-sect lord is the
    ``primary``, the out-of-sect lord is the ``secondary``, and ``participating``
    supports throughout. This is the rulership set for the classical
    triplicity-lords technique (e.g. dividing a topic into thirds of time); it
    is distinct from the Ptolemaic essential-dignity score, which awards +3 to
    the in-sect (``primary``) lord only.

    Attributes:
        element: The triplicity element (Fire/Earth/Air/Water).
        sect: ``"day"`` or ``"night"`` — the sect used to order the lords.
        primary: In-sect triplicity lord (first lord).
        secondary: Out-of-sect triplicity lord (second lord).
        participating: Participating lord (third lord, active in both sects).
    """

    element: Element
    sect: Literal["day", "night"]
    primary: ClassicalPlanet
    secondary: ClassicalPlanet
    participating: ClassicalPlanet


class ZRPeriodModel(SubscriptableBaseModel):
    """One zodiacal-releasing period at a given level of subdivision.

    Periods nest: an L1 (years) period contains L2 (months) sub-periods, each of
    which may contain L3 sub-periods, and so on. Deeper levels are only populated
    along the period that contains the requested target date, to keep the tree
    bounded.

    Attributes:
        sign: Three-letter sign code ruling the period.
        ruler: Traditional (domicile) ruler of the sign.
        level: Subdivision level (1 = years, 2 = months, 3 = days, …).
        start: Start date (ISO ``YYYY-MM-DD``).
        end: End date (ISO ``YYYY-MM-DD``).
        years: Nominal length in years at this level (the sign's general years
            divided by ``12 ** (level - 1)``).
        is_angular: ``True`` when the sign is angular from the natal Lot of
            Fortune (1st/4th/7th/10th from Fortune) — the peak periods. Per
            Hellenistic doctrine the angularity reference is Fortune for every
            released lot, including Spirit.
        is_loosing_the_bond: ``True`` when this period begins after a "loosing of
            the bond" jump to the opposite sign.
        subperiods: Nested sub-periods one level deeper (possibly empty).
    """

    sign: Sign
    ruler: Optional[str] = None
    level: int
    start: str
    end: str
    years: float
    is_angular: bool = False
    is_loosing_the_bond: bool = False
    subperiods: "list[ZRPeriodModel]" = Field(default_factory=list)


class ZodiacalReleasingModel(SubscriptableBaseModel):
    """Result of a zodiacal-releasing calculation from a lot.

    Attributes:
        lot: The lot the release is measured from ("fortune" or "spirit").
        lot_sign: Sign of the lot — the first L1 period starts here.
        lot_degree: Absolute longitude of the lot in the subject's zodiac.
        periods: The top-level (L1) periods, each with nested sub-periods.
        current_path: The chain of periods containing the target date, from L1
            down to the deepest computed level (empty when no target date given).
    """

    lot: str
    lot_sign: Sign
    lot_degree: float
    periods: list[ZRPeriodModel] = Field(default_factory=list)
    current_path: list[ZRPeriodModel] = Field(default_factory=list)
