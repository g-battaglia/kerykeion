# -*- coding: utf-8 -*-
"""
Astrological Subject Factory Module

This module provides factory classes for creating astrological subjects with comprehensive
astrological calculations including planetary positions, house cusps, aspects, and various
astrological points.

The main factory class AstrologicalSubjectFactory offers multiple creation methods for
different initialization scenarios, supporting both online and offline calculation modes,
various zodiac systems (Tropical/Sidereal), house systems, and coordinate perspectives.

Key Features:
    - Planetary position calculations for all traditional and modern planets
    - House cusp calculations with multiple house systems
    - Lunar nodes, Lilith points, asteroids, and trans-Neptunian objects
    - Arabic parts (lots) calculations
    - Fixed star positions
    - Automatic location data fetching via GeoNames API
    - Comprehensive timezone and coordinate handling
    - Flexible point selection for performance optimization

Classes:
    ChartConfiguration: Configuration settings for astrological calculations
    LocationData: Geographical location information and utilities
    AstrologicalSubjectFactory: Main factory for creating astrological subjects

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

import pytz
import swisseph as swe
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, get_args
from dataclasses import dataclass, field
from contextlib import contextmanager


from kerykeion.fetch_geonames import FetchGeonames
from kerykeion.schemas import (
    KerykeionException,
    ZodiacType,
    AstrologicalSubjectModel,
    PointType,
    SiderealMode,
    HousesSystemIdentifier,
    PerspectiveType,
    AstrologicalPoint,
    Houses,
)
from kerykeion.utilities import (
    get_kerykeion_point_from_degree,
    get_planet_house,
    check_and_adjust_polar_latitude,
    calculate_moon_phase,
    datetime_to_julian,
    get_house_number,
    normalize_zodiac_type,
)
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

# Default configuration values
DEFAULT_GEONAMES_USERNAME = "century.boy"
DEFAULT_SIDEREAL_MODE: SiderealMode = "FAGAN_BRADLEY"
DEFAULT_HOUSES_SYSTEM_IDENTIFIER: HousesSystemIdentifier = "P"
DEFAULT_ZODIAC_TYPE: ZodiacType = "Tropical"
DEFAULT_PERSPECTIVE_TYPE: PerspectiveType = "Apparent Geocentric"
DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS = 30

# =============================================================================
# PLANET CONFIGURATION MAPPINGS
# =============================================================================
# These mappings define the Swiss Ephemeris IDs for each celestial body.
# Using a centralized configuration eliminates repetitive code and makes
# it easier to add new celestial bodies in the future.

# Standard planets with direct Swiss Ephemeris IDs (0-20)
STANDARD_PLANETS: Dict[AstrologicalPoint, int] = {
    "Sun": 0,
    "Moon": 1,
    "Mercury": 2,
    "Venus": 3,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
    "Mean_North_Lunar_Node": 10,
    "True_North_Lunar_Node": 11,
    "Mean_Lilith": 12,
    "True_Lilith": 13,
    "Earth": 14,
    "Chiron": 15,
    "Pholus": 16,
    "Ceres": 17,
    "Pallas": 18,
    "Juno": 19,
    "Vesta": 20,
}

# Trans-Neptunian Objects requiring AST_OFFSET
# These use Swiss Ephemeris asteroid offset + minor planet number
TNO_PLANETS: Dict[AstrologicalPoint, int] = {
    "Eris": 136199,
    "Sedna": 90377,
    "Haumea": 136108,
    "Makemake": 136472,
    "Ixion": 28978,
    "Orcus": 90482,
    "Quaoar": 50000,
}

# Fixed stars (use different calculation method)
FIXED_STARS: List[AstrologicalPoint] = ["Regulus", "Spica"]

# Opposite points derived from other calculations
OPPOSITE_POINTS: Dict[AstrologicalPoint, AstrologicalPoint] = {
    "Mean_South_Lunar_Node": "Mean_North_Lunar_Node",
    "True_South_Lunar_Node": "True_North_Lunar_Node",
}

# Arabic Parts configuration: (name, required_points, formula_type)
# formula_type: "fortune" = day/night variant, "simple" = single formula
ARABIC_PARTS_CONFIG: Dict[AstrologicalPoint, Dict[str, Any]] = {
    "Pars_Fortunae": {
        "required": ["Ascendant", "Sun", "Moon"],
        "day_formula": lambda asc, sun, moon: asc + moon - sun,
        "night_formula": lambda asc, sun, moon: asc + sun - moon,
    },
    "Pars_Spiritus": {
        "required": ["Ascendant", "Sun", "Moon"],
        "day_formula": lambda asc, sun, moon: asc + sun - moon,
        "night_formula": lambda asc, sun, moon: asc + moon - sun,
    },
    "Pars_Amoris": {
        "required": ["Ascendant", "Venus", "Sun"],
        "formula": lambda asc, venus, sun: asc + venus - sun,
    },
    "Pars_Fidei": {
        "required": ["Ascendant", "Jupiter", "Saturn"],
        "formula": lambda asc, jupiter, saturn: asc + jupiter - saturn,
    },
}

# Warning messages
GEONAMES_DEFAULT_USERNAME_WARNING = (
    "\n********\n"
    "NO GEONAMES USERNAME SET!\n"
    "Using the default geonames username is not recommended, please set a custom one!\n"
    "You can get one for free here:\n"
    "https://www.geonames.org/login\n"
    "Keep in mind that the default username is limited to 2000 requests per hour and is shared with everyone else using this library.\n"
    "********"
)


@contextmanager
def ephemeris_context(
    ephe_path: str,
    config: "ChartConfiguration",
    lng: float,
    lat: float,
    alt: Optional[float] = None,
):
    """Context manager that isolates Swiss Ephemeris configuration.

    Responsibilities:
        - Set ephemeris path and calculation flags
        - Configure perspective (true geo / helio / topo)
        - Configure sidereal mode when needed
        - Apply topocentric observer only inside the with-block
        - Yield iflag for calculations
        - Reset topocentric coordinates afterward (defensive)

    Args:
        ephe_path: Path containing Swiss Ephemeris data files.
        config: Validated chart configuration.
        lng: Observer longitude (used for topocentric charts).
        lat: Observer latitude (used for topocentric charts).
        alt: Observer altitude (meters) for topocentric charts.

    Yields:
        int: iflag to be passed to swe.calc_ut / swe.fixstar_ut.
    """
    swe.set_ephe_path(ephe_path)
    iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

    topo_used = False

    # Perspective configuration
    if config.perspective_type == "True Geocentric":
        iflag |= swe.FLG_TRUEPOS
    elif config.perspective_type == "Heliocentric":
        iflag |= swe.FLG_HELCTR
    elif config.perspective_type == "Topocentric":
        iflag |= swe.FLG_TOPOCTR
        swe.set_topo(lng, lat, alt or 0.0)
        topo_used = True

    # Sidereal configuration
    if config.zodiac_type == "Sidereal":
        iflag |= swe.FLG_SIDEREAL
        swe.set_sid_mode(getattr(swe, f"SIDM_{config.sidereal_mode}"))

    try:
        yield iflag
    finally:
        # Defensive cleanup: reset topo if it was set
        if topo_used:
            swe.set_topo(0.0, 0.0, 0.0)


@dataclass
class ChartConfiguration:
    """
    Configuration settings for astrological chart calculations.

    This class encapsulates all the configuration parameters needed for astrological
    calculations, including zodiac type, coordinate systems, house systems, and
    calculation perspectives. It provides validation to ensure compatible settings
    combinations.

    Attributes:
        zodiac_type (ZodiacType): The zodiac system to use ('Tropical' or 'Sidereal').
            Defaults to 'Tropical'.
        sidereal_mode (Optional[SiderealMode]): The sidereal calculation mode when using
            sidereal zodiac. Only required/used when zodiac_type is 'Sidereal'.
            Defaults to None (auto-set to FAGAN_BRADLEY for sidereal).
        houses_system_identifier (HousesSystemIdentifier): The house system to use for
            house cusp calculations. Defaults to 'P' (Placidus).
        perspective_type (PerspectiveType): The coordinate perspective for calculations.
            Options include 'Apparent Geocentric', 'True Geocentric', 'Heliocentric',
            or 'Topocentric'. Defaults to 'Apparent Geocentric'.

    Raises:
        KerykeionException: When invalid configuration combinations are detected,
            such as setting sidereal_mode with tropical zodiac, or using invalid
            enumeration values.

    Example:
        >>> config = ChartConfiguration(
        ...     zodiac_type="Sidereal",
        ...     sidereal_mode="LAHIRI",
        ...     houses_system_identifier="K",
        ...     perspective_type="Topocentric"
        ... )
    """

    zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE
    sidereal_mode: Optional[SiderealMode] = None
    houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER
    perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """
        Validate configuration settings for internal consistency.

        Performs comprehensive validation of all configuration parameters to ensure
        they form a valid, compatible combination. This includes checking enumeration
        values, zodiac/sidereal mode compatibility, and setting defaults where needed.

        Raises:
            KerykeionException: If any configuration parameter is invalid or if
                incompatible parameter combinations are detected.

        Side Effects:
            - Sets default sidereal_mode to FAGAN_BRADLEY if zodiac_type is Sidereal
              and no sidereal_mode is specified
            - Logs informational message when setting default sidereal mode
        """
        # Validate zodiac type
        try:
            normalized_zodiac_type = normalize_zodiac_type(self.zodiac_type)
        except ValueError as exc:
            raise KerykeionException(str(exc)) from exc
        else:
            if normalized_zodiac_type != self.zodiac_type:
                self.zodiac_type = normalized_zodiac_type

        # Validate sidereal mode settings
        if self.sidereal_mode and self.zodiac_type == "Tropical":
            raise KerykeionException("You can't set a sidereal mode with a Tropical zodiac type!")

        if self.zodiac_type == "Sidereal":
            if not self.sidereal_mode:
                self.sidereal_mode = DEFAULT_SIDEREAL_MODE
                logging.info("No sidereal mode set, using default FAGAN_BRADLEY")
            elif self.sidereal_mode not in get_args(SiderealMode):
                raise KerykeionException(
                    f"'{self.sidereal_mode}' is not a valid sidereal mode! Available modes are: {get_args(SiderealMode)}"
                )

        # Validate houses system
        if self.houses_system_identifier not in get_args(HousesSystemIdentifier):
            raise KerykeionException(
                f"'{self.houses_system_identifier}' is not a valid house system! Available systems are: {get_args(HousesSystemIdentifier)}"
            )

        # Validate perspective type
        if self.perspective_type not in get_args(PerspectiveType):
            raise KerykeionException(
                f"'{self.perspective_type}' is not a valid chart perspective! Available perspectives are: {get_args(PerspectiveType)}"
            )


@dataclass
class LocationData:
    """
    Information about a geographical location for astrological calculations.

    This class handles all location-related data including coordinates, timezone
    information, and interaction with the GeoNames API for automatic location
    data retrieval. It provides methods for fetching location data online and
    preparing coordinates for astrological calculations.

    Attributes:
        city (str): Name of the city or location. Defaults to "Greenwich".
        nation (str): ISO country code (2-letter). Defaults to "GB" (United Kingdom).
        lat (float): Latitude in decimal degrees. Positive for North, negative for South.
            Defaults to 51.5074 (Greenwich).
        lng (float): Longitude in decimal degrees. Positive for East, negative for West.
            Defaults to 0.0 (Greenwich).
        tz_str (str): IANA timezone identifier (e.g., 'Europe/London', 'America/New_York').
            Defaults to "Etc/GMT".
        altitude (Optional[float]): Altitude above sea level in meters. Used for
            topocentric calculations. Defaults to None (sea level assumed).
        city_data (Dict[str, str]): Raw data retrieved from GeoNames API. Used internally
            for caching and validation. Defaults to empty dictionary.

    Note:
        When using online mode, the initial coordinate and timezone values may be
        overridden by data fetched from the GeoNames API based on city and nation.
        For polar regions, latitude values are automatically adjusted to prevent
        calculation errors.

    Example:
        >>> location = LocationData(city="Rome", nation="IT")
        >>> location.fetch_from_geonames("your_username", 30)
        >>> location.prepare_for_calculation()
    """

    city: str = "Greenwich"
    nation: str = "GB"
    lat: float = 51.5074
    lng: float = 0.0
    tz_str: str = "Etc/GMT"
    altitude: Optional[float] = None

    # Storage for city data fetched from geonames
    city_data: Dict[str, str] = field(default_factory=dict)

    def fetch_from_geonames(self, username: str, cache_expire_after_days: int) -> None:
        """
        Fetch location data from GeoNames API.

        Retrieves accurate coordinates, timezone, and country code information
        for the specified city and country from the GeoNames web service.
        Updates the instance attributes with the fetched data.

        Args:
            username (str): GeoNames API username. Must be registered at geonames.org.
                Free accounts are limited to 2000 requests per hour.
            cache_expire_after_days (int): Number of days to cache the location data
                locally before refreshing from the API.

        Raises:
            KerykeionException: If required data is missing from the API response,
                typically due to network issues, invalid location names, or API limits.

        Side Effects:
            - Updates city_data with raw API response
            - Updates nation, lng, lat, and tz_str with fetched values
            - May create or update local cache files

        Note:
            The method validates that all required fields (countryCode, timezonestr,
            lat, lng) are present in the API response before updating instance attributes.
        """
        logging.info(f"Fetching timezone/coordinates for {self.city}, {self.nation} from geonames")

        geonames = FetchGeonames(
            self.city, self.nation, username=username, cache_expire_after_days=cache_expire_after_days
        )

        self.city_data = geonames.get_serialized_data()

        # Validate data
        required_fields = ["countryCode", "timezonestr", "lat", "lng"]
        missing_fields = [field for field in required_fields if field not in self.city_data]

        if missing_fields:
            raise KerykeionException(
                f"Missing data from geonames: {', '.join(missing_fields)}. "
                "Check your connection or try a different location."
            )

        # Update location data
        self.nation = self.city_data["countryCode"]
        self.lng = float(self.city_data["lng"])
        self.lat = float(self.city_data["lat"])
        self.tz_str = self.city_data["timezonestr"]

    def prepare_for_calculation(self) -> None:
        """
        Prepare location data for astrological calculations.

        Performs final adjustments to location data to ensure compatibility
        with Swiss Ephemeris calculations. This includes handling special cases
        like polar regions where extreme latitudes can cause calculation errors.

        Side Effects:
            - Adjusts latitude values for polar regions (beyond ±66.5°) to
              prevent Swiss Ephemeris calculation failures
            - May log warnings about latitude adjustments

        Note:
            This method should be called after all location data has been set,
            either manually or via fetch_from_geonames(), and before performing
            any astrological calculations.
        """
        # Adjust latitude for polar regions
        self.lat = check_and_adjust_polar_latitude(self.lat)


class AstrologicalSubjectFactory:
    """
    Factory class for creating comprehensive astrological subjects.

    This factory creates AstrologicalSubjectModel instances with complete astrological
    information including planetary positions, house cusps, aspects, lunar phases, and
    various specialized astrological points. It provides multiple class methods for
    different initialization scenarios and supports both online and offline calculation modes.

    The factory handles complex astrological calculations using the Swiss Ephemeris library,
    supports multiple coordinate systems and house systems, and can automatically fetch
    location data from online sources.

    Supported Astrological Points:
        - Traditional Planets: Sun through Pluto
        - Lunar Nodes: Mean and True North/South Nodes
        - Lilith Points: Mean and True Black Moon
        - Asteroids: Ceres, Pallas, Juno, Vesta
        - Centaurs: Chiron, Pholus
        - Trans-Neptunian Objects: Eris, Sedna, Haumea, Makemake, Ixion, Orcus, Quaoar
        - Fixed Stars: Regulus, Spica (extensible)
        - Arabic Parts: Pars Fortunae, Pars Spiritus, Pars Amoris, Pars Fidei
        - Special Points: Vertex, Anti-Vertex, Earth (for heliocentric charts)
        - House Cusps: All 12 houses with configurable house systems
        - Angles: Ascendant, Medium Coeli, Descendant, Imum Coeli

    Supported Features:
        - Multiple zodiac systems (Tropical/Sidereal with various ayanamshas)
        - Multiple house systems (Placidus, Koch, Equal, Whole Sign, etc.)
        - Multiple coordinate perspectives (Geocentric, Heliocentric, Topocentric)
        - Automatic timezone and coordinate resolution via GeoNames API
        - Lunar phase calculations
        - Day/night chart detection for Arabic parts
        - Performance optimization through selective point calculation
        - Comprehensive error handling and validation

    Class Methods:
        from_birth_data: Create subject from standard birth data (most flexible)
        from_iso_utc_time: Create subject from ISO UTC timestamp
        from_current_time: Create subject for current moment

    Example:
        >>> # Create natal chart
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     name="John Doe",
        ...     year=1990, month=6, day=15,
        ...     hour=14, minute=30,
        ...     city="Rome", nation="IT",
        ...     online=True
        ... )
        >>> print(f"Sun: {subject.sun.sign} {subject.sun.abs_pos}°")
        >>> print(f"Active points: {len(subject.active_points)}")

        >>> # Create chart for current time
        >>> now_subject = AstrologicalSubjectFactory.from_current_time(
        ...     name="Current Moment",
        ...     city="London", nation="GB"
        ... )

    Thread Safety:
        This factory is not thread-safe due to its use of the Swiss Ephemeris library
        which maintains global state. Use separate instances in multi-threaded applications
        or implement appropriate locking mechanisms.
    """

    @classmethod
    def from_birth_data(
        cls,
        name: str = "Now",
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        city: Optional[str] = None,
        nation: Optional[str] = None,
        lng: Optional[float] = None,
        lat: Optional[float] = None,
        tz_str: Optional[str] = None,
        geonames_username: Optional[str] = None,
        online: bool = True,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: Optional[SiderealMode] = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        cache_expire_after_days: int = DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS,
        is_dst: Optional[bool] = None,
        altitude: Optional[float] = None,
        active_points: Optional[List[AstrologicalPoint]] = None,
        calculate_lunar_phase: bool = True,
        *,
        seconds: int = 0,
        suppress_geonames_warning: bool = False,
    ) -> AstrologicalSubjectModel:
        """
        Create an astrological subject from standard birth or event data.

        This is the most flexible and commonly used factory method. It creates a complete
        astrological subject with planetary positions, house cusps, and specialized points
        for a specific date, time, and location. Supports both online location resolution
        and offline calculation modes.

        Args:
            name (str, optional): Name or identifier for the subject. Defaults to "Now".
            year (int, optional): Year of birth/event. Defaults to current year.
            month (int, optional): Month of birth/event (1-12). Defaults to current month.
            day (int, optional): Day of birth/event (1-31). Defaults to current day.
            hour (int, optional): Hour of birth/event (0-23). Defaults to current hour.
            minute (int, optional): Minute of birth/event (0-59). Defaults to current minute.
            seconds (int, optional): Seconds of birth/event (0-59). Defaults to 0.
            city (str, optional): City name for location lookup. Used with online=True.
                Defaults to None (Greenwich if not specified).
            nation (str, optional): ISO country code (e.g., 'US', 'GB', 'IT'). Used with
                online=True. Defaults to None ('GB' if not specified).
            lng (float, optional): Longitude in decimal degrees. East is positive, West
                is negative. If not provided and online=True, fetched from GeoNames.
            lat (float, optional): Latitude in decimal degrees. North is positive, South
                is negative. If not provided and online=True, fetched from GeoNames.
            tz_str (str, optional): IANA timezone identifier (e.g., 'Europe/London').
                If not provided and online=True, fetched from GeoNames.
            geonames_username (str, optional): Username for GeoNames API. Required for
                online location lookup. Get one free at geonames.org.
            online (bool, optional): Whether to fetch location data online. If False,
                lng, lat, and tz_str must be provided. Defaults to True.
            zodiac_type (ZodiacType, optional): Zodiac system - 'Tropical' or 'Sidereal'.
                Defaults to 'Tropical'.
            sidereal_mode (SiderealMode, optional): Sidereal calculation mode (e.g.,
                'FAGAN_BRADLEY', 'LAHIRI'). Only used with zodiac_type='Sidereal'.
            houses_system_identifier (HousesSystemIdentifier, optional): House system
                for cusp calculations (e.g., 'P'=Placidus, 'K'=Koch, 'E'=Equal).
                Defaults to 'P' (Placidus).
            perspective_type (PerspectiveType, optional): Calculation perspective:
                - 'Apparent Geocentric': Standard geocentric with light-time correction
                - 'True Geocentric': Geometric geocentric positions
                - 'Heliocentric': Sun-centered coordinates
                - 'Topocentric': Earth surface perspective (requires altitude)
                Defaults to 'Apparent Geocentric'.
            cache_expire_after_days (int, optional): Days to cache GeoNames data locally.
                Defaults to 30.
            is_dst (bool, optional): Daylight Saving Time flag for ambiguous times.
                If None, pytz attempts automatic detection. Set explicitly for
                times during DST transitions.
            altitude (float, optional): Altitude above sea level in meters. Used for
                topocentric calculations and atmospheric corrections. Defaults to None
                (sea level assumed).
            active_points (Optional[List[AstrologicalPoint]], optional): List of astrological
                points to calculate. Omitting points can improve performance for
                specialized applications. If None, uses DEFAULT_ACTIVE_POINTS.
            calculate_lunar_phase (bool, optional): Whether to calculate lunar phase.
                Requires Sun and Moon in active_points. Defaults to True.
            suppress_geonames_warning (bool, optional): If True, suppresses the warning
                message when using the default GeoNames username. Useful for testing
                or automated processes. Defaults to False.

        Returns:
            AstrologicalSubjectModel: Complete astrological subject with calculated
                positions, houses, and metadata. Access planetary positions via
                attributes like .sun, .moon, .mercury, etc.

        Raises:
            KerykeionException:
                - If offline mode is used without required location data
                - If invalid zodiac/sidereal mode combinations are specified
                - If GeoNames data is missing or invalid
                - If timezone localization fails (ambiguous DST times)

        Examples:
            >>> # Basic natal chart with online location lookup
            >>> chart = AstrologicalSubjectFactory.from_birth_data(
            ...     name="Jane Doe",
            ...     year=1985, month=3, day=21,
            ...     hour=15, minute=30,
            ...     city="Paris", nation="FR",
            ...     geonames_username="your_username"
            ... )

            >>> # Offline calculation with manual coordinates
            >>> chart = AstrologicalSubjectFactory.from_birth_data(
            ...     name="John Smith",
            ...     year=1990, month=12, day=25,
            ...     hour=0, minute=0,
            ...     lng=-74.006, lat=40.7128, tz_str="America/New_York",
            ...     online=False
            ... )

            >>> # Sidereal chart with specific points
            >>> chart = AstrologicalSubjectFactory.from_birth_data(
            ...     name="Vedic Chart",
            ...     year=2000, month=6, day=15, hour=12,
            ...     city="Mumbai", nation="IN",
            ...     zodiac_type="Sidereal",
            ...     sidereal_mode="LAHIRI",
            ...     active_points=["Sun", "Moon", "Mercury", "Venus", "Mars",
            ...                   "Jupiter", "Saturn", "Ascendant"]
            ... )

        Note:
            - For high-precision calculations, consider providing seconds parameter
            - Use topocentric perspective for observer-specific calculations
            - Some Arabic parts automatically activate required base points
            - The method handles polar regions by adjusting extreme latitudes
            - Time zones are handled with full DST awareness via pytz
        """
        # Resolve time defaults using current time
        if year is None or month is None or day is None or hour is None or minute is None or seconds is None:
            now = datetime.now()
            year = year if year is not None else now.year
            month = month if month is not None else now.month
            day = day if day is not None else now.day
            hour = hour if hour is not None else now.hour
            minute = minute if minute is not None else now.minute
            seconds = seconds if seconds is not None else now.second

        # Create a calculation data container
        calc_data: Dict[str, Any] = {}

        # Basic identity
        calc_data["name"] = name
        calc_data["json_dir"] = str(Path.home())

        # Create a deep copy of active points to avoid modifying the original list
        if active_points is None:
            active_points_list: List[AstrologicalPoint] = list(DEFAULT_ACTIVE_POINTS)
        else:
            active_points_list = list(active_points)

        calc_data["active_points"] = active_points_list

        # Initialize configuration
        config = ChartConfiguration(
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
        )

        # Add configuration data to calculation data
        calc_data["zodiac_type"] = config.zodiac_type
        calc_data["sidereal_mode"] = config.sidereal_mode
        calc_data["houses_system_identifier"] = config.houses_system_identifier
        calc_data["perspective_type"] = config.perspective_type

        # Set up geonames username if needed
        if geonames_username is None and online and (not lat or not lng or not tz_str):
            if not suppress_geonames_warning:
                logging.warning(GEONAMES_DEFAULT_USERNAME_WARNING)
            geonames_username = DEFAULT_GEONAMES_USERNAME

        # Initialize location data
        location = LocationData(
            city=city or "Greenwich",
            nation=nation or "GB",
            lat=lat if lat is not None else 51.5074,
            lng=lng if lng is not None else 0.0,
            tz_str=tz_str or "Etc/GMT",
            altitude=altitude,
        )

        # If offline mode is requested but required data is missing, raise error
        if not online and (not tz_str or lat is None or lng is None):
            raise KerykeionException("For offline mode, you must provide timezone (tz_str) and coordinates (lat, lng)")

        # Fetch location data if needed
        if online and (not tz_str or lat is None or lng is None):
            location.fetch_from_geonames(
                username=geonames_username or DEFAULT_GEONAMES_USERNAME, cache_expire_after_days=cache_expire_after_days
            )

        # Prepare location for calculations
        location.prepare_for_calculation()

        # Add location data to calculation data
        calc_data["city"] = location.city
        calc_data["nation"] = location.nation
        calc_data["lat"] = location.lat
        calc_data["lng"] = location.lng
        calc_data["tz_str"] = location.tz_str
        calc_data["altitude"] = location.altitude

        # Store calculation parameters
        calc_data["year"] = year
        calc_data["month"] = month
        calc_data["day"] = day
        calc_data["hour"] = hour
        calc_data["minute"] = minute
        calc_data["seconds"] = seconds
        calc_data["is_dst"] = is_dst

        # Calculate time conversions
        AstrologicalSubjectFactory._calculate_time_conversions(calc_data, location)
        # Initialize Swiss Ephemeris and calculate houses and planets with context manager
        ephe_path = str(Path(__file__).parent.absolute() / "sweph")
        with ephemeris_context(
            ephe_path=ephe_path,
            config=config,
            lng=calc_data["lng"],
            lat=calc_data["lat"],
            alt=calc_data["altitude"],
        ) as iflag:
            calc_data["_iflag"] = iflag
            # House system name (previously set in _setup_ephemeris)
            calc_data["houses_system_name"] = swe.house_name(config.houses_system_identifier.encode("ascii"))
            calculated_axial_cusps = AstrologicalSubjectFactory._calculate_houses(calc_data, active_points_list)
            AstrologicalSubjectFactory._calculate_planets(calc_data, active_points_list, calculated_axial_cusps)
        AstrologicalSubjectFactory._calculate_day_of_week(calc_data)

        # Calculate lunar phase (optional - only if requested and Sun and Moon are available)
        if calculate_lunar_phase and "moon" in calc_data and "sun" in calc_data:
            calc_data["lunar_phase"] = calculate_moon_phase(
                calc_data["moon"].abs_pos,  # type: ignore[attr-defined,union-attr]
                calc_data["sun"].abs_pos,  # type: ignore[attr-defined,union-attr]
            )
        else:
            calc_data["lunar_phase"] = None

        # Create and return the AstrologicalSubjectModel
        return AstrologicalSubjectModel(**calc_data)

    @classmethod
    def from_iso_utc_time(
        cls,
        name: str,
        iso_utc_time: str,
        city: str = "Greenwich",
        nation: str = "GB",
        tz_str: str = "Etc/GMT",
        online: bool = True,
        lng: float = 0.0,
        lat: float = 51.5074,
        geonames_username: str = DEFAULT_GEONAMES_USERNAME,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: Optional[SiderealMode] = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        altitude: Optional[float] = None,
        active_points: Optional[List[AstrologicalPoint]] = None,
        calculate_lunar_phase: bool = True,
        suppress_geonames_warning: bool = False,
    ) -> AstrologicalSubjectModel:
        """
        Create an astrological subject from an ISO formatted UTC timestamp.

        This method is ideal for creating astrological subjects from standardized
        time formats, such as those stored in databases or received from APIs.
        It automatically handles timezone conversion from UTC to the specified
        local timezone.

        Args:
            name (str): Name or identifier for the subject.
            iso_utc_time (str): ISO 8601 formatted UTC timestamp. Supported formats:
                - "2023-06-15T14:30:00Z" (with Z suffix)
                - "2023-06-15T14:30:00+00:00" (with UTC offset)
                - "2023-06-15T14:30:00.123Z" (with milliseconds)
            city (str, optional): City name for location. Defaults to "Greenwich".
            nation (str, optional): ISO country code. Defaults to "GB".
            tz_str (str, optional): IANA timezone identifier for result conversion.
                The ISO time is assumed to be in UTC and will be converted to this
                timezone. Defaults to "Etc/GMT".
            online (bool, optional): Whether to fetch coordinates online. If True,
                coordinates are fetched via GeoNames API. Defaults to True.
            lng (float, optional): Longitude in decimal degrees. Used when online=False
                or as fallback. Defaults to 0.0 (Greenwich).
            lat (float, optional): Latitude in decimal degrees. Used when online=False
                or as fallback. Defaults to 51.5074 (Greenwich).
            geonames_username (str, optional): GeoNames API username. Required when
                online=True. Defaults to DEFAULT_GEONAMES_USERNAME.
            zodiac_type (ZodiacType, optional): Zodiac system. Defaults to 'Tropical'.
            sidereal_mode (SiderealMode, optional): Sidereal mode when zodiac_type
                is 'Sidereal'. Defaults to None.
            houses_system_identifier (HousesSystemIdentifier, optional): House system.
                Defaults to 'P' (Placidus).
            perspective_type (PerspectiveType, optional): Calculation perspective.
                Defaults to 'Apparent Geocentric'.
            altitude (float, optional): Altitude in meters for topocentric calculations.
                Defaults to None (sea level).
            active_points (Optional[List[AstrologicalPoint]], optional): Points to calculate.
                If None, uses DEFAULT_ACTIVE_POINTS.
            calculate_lunar_phase (bool, optional): Whether to calculate lunar phase.
                Defaults to True.

        Returns:
            AstrologicalSubjectModel: Astrological subject with positions calculated
                for the specified UTC time converted to local timezone.

        Raises:
            ValueError: If the ISO timestamp format is invalid or cannot be parsed.
            KerykeionException: If location data cannot be fetched or is invalid.

        Examples:
            >>> # From API timestamp with online location lookup
            >>> subject = AstrologicalSubjectFactory.from_iso_utc_time(
            ...     name="Event Chart",
            ...     iso_utc_time="2023-12-25T12:00:00Z",
            ...     city="Tokyo", nation="JP",
            ...     tz_str="Asia/Tokyo",
            ...     geonames_username="your_username"
            ... )

            >>> # From database timestamp with manual coordinates
            >>> subject = AstrologicalSubjectFactory.from_iso_utc_time(
            ...     name="Historical Event",
            ...     iso_utc_time="1969-07-20T20:17:00Z",
            ...     lng=-95.0969, lat=37.4419,  # Houston
            ...     tz_str="America/Chicago",
            ...     online=False
            ... )

        Note:
            - The method assumes the input timestamp is in UTC
            - Local time conversion respects DST rules for the target timezone
            - Milliseconds in the timestamp are supported but truncated to seconds
            - When online=True, the city/nation parameters override lng/lat
        """
        # Parse the ISO time
        dt = datetime.fromisoformat(iso_utc_time.replace("Z", "+00:00"))

        # Get location data if online mode is enabled
        if online:
            if geonames_username == DEFAULT_GEONAMES_USERNAME:
                if not suppress_geonames_warning:
                    logging.warning(GEONAMES_DEFAULT_USERNAME_WARNING)

            geonames = FetchGeonames(
                city,
                nation,
                username=geonames_username,
            )

            city_data = geonames.get_serialized_data()
            lng = float(city_data["lng"])
            lat = float(city_data["lat"])

        # Convert UTC to local time
        local_time = pytz.timezone(tz_str)
        local_datetime = dt.astimezone(local_time)

        # Create the subject with local time
        return cls.from_birth_data(
            name=name,
            year=local_datetime.year,
            month=local_datetime.month,
            day=local_datetime.day,
            hour=local_datetime.hour,
            minute=local_datetime.minute,
            seconds=local_datetime.second,
            city=city,
            nation=nation,
            lng=lng,
            lat=lat,
            tz_str=tz_str,
            online=False,  # Already fetched data if needed
            geonames_username=geonames_username,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
            altitude=altitude,
            active_points=active_points,
            calculate_lunar_phase=calculate_lunar_phase,
            suppress_geonames_warning=suppress_geonames_warning,
        )

    @classmethod
    def from_current_time(
        cls,
        name: str = "Now",
        city: Optional[str] = None,
        nation: Optional[str] = None,
        lng: Optional[float] = None,
        lat: Optional[float] = None,
        tz_str: Optional[str] = None,
        geonames_username: Optional[str] = None,
        online: bool = True,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: Optional[SiderealMode] = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        active_points: Optional[List[AstrologicalPoint]] = None,
        calculate_lunar_phase: bool = True,
        suppress_geonames_warning: bool = False,
    ) -> AstrologicalSubjectModel:
        """
        Create an astrological subject for the current moment in time.

        This convenience method creates a "now" chart, capturing the current
        astrological conditions at the moment of execution. Useful for horary
        astrology, electional astrology, or real-time astrological monitoring.

        Args:
            name (str, optional): Name for the current moment chart.
                Defaults to "Now".
            city (str, optional): City name for location lookup. If not provided
                and online=True, defaults to Greenwich.
            nation (str, optional): ISO country code. If not provided and
                online=True, defaults to 'GB'.
            lng (float, optional): Longitude in decimal degrees. If not provided
                and online=True, fetched from GeoNames API.
            lat (float, optional): Latitude in decimal degrees. If not provided
                and online=True, fetched from GeoNames API.
            tz_str (str, optional): IANA timezone identifier. If not provided
                and online=True, fetched from GeoNames API.
            geonames_username (str, optional): GeoNames API username for location
                lookup. Required when online=True and location is not fully specified.
            online (bool, optional): Whether to fetch location data online.
                Defaults to True.
            zodiac_type (ZodiacType, optional): Zodiac system to use.
                Defaults to 'Tropical'.
            sidereal_mode (SiderealMode, optional): Sidereal calculation mode.
                Only used when zodiac_type is 'Sidereal'. Defaults to None.
            houses_system_identifier (HousesSystemIdentifier, optional): House
                system for calculations. Defaults to 'P' (Placidus).
            perspective_type (PerspectiveType, optional): Calculation perspective.
                Defaults to 'Apparent Geocentric'.
            active_points (Optional[List[AstrologicalPoint]], optional): Astrological points
                to calculate. If None, uses DEFAULT_ACTIVE_POINTS.
            calculate_lunar_phase (bool, optional): Whether to calculate lunar phase.
                Defaults to True.

        Returns:
            AstrologicalSubjectModel: Astrological subject representing current
                astrological conditions at the specified or default location.

        Raises:
            KerykeionException: If online location lookup fails or if offline mode
                is used without sufficient location data.

        Examples:
            >>> # Current moment for your location
            >>> now_chart = AstrologicalSubjectFactory.from_current_time(
            ...     name="Current Transits",
            ...     city="New York", nation="US",
            ...     geonames_username="your_username"
            ... )

            >>> # Horary chart with specific coordinates
            >>> horary = AstrologicalSubjectFactory.from_current_time(
            ...     name="Horary Question",
            ...     lng=-0.1278, lat=51.5074,  # London
            ...     tz_str="Europe/London",
            ...     online=False
            ... )

            >>> # Current sidereal positions
            >>> sidereal_now = AstrologicalSubjectFactory.from_current_time(
            ...     name="Sidereal Now",
            ...     city="Mumbai", nation="IN",
            ...     zodiac_type="Sidereal",
            ...     sidereal_mode="LAHIRI"
            ... )

        Note:
            - The exact time is captured at method execution, including seconds
            - For horary astrology, consider the moment of understanding the question
            - System clock accuracy affects precision; ensure accurate system time
            - Time zone detection is automatic when using online location lookup
        """
        now = datetime.now()

        return cls.from_birth_data(
            name=name,
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            seconds=now.second,
            city=city,
            nation=nation,
            lng=lng,
            lat=lat,
            tz_str=tz_str,
            geonames_username=geonames_username,
            online=online,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
            active_points=active_points,
            calculate_lunar_phase=calculate_lunar_phase,
            suppress_geonames_warning=suppress_geonames_warning,
        )

    @staticmethod
    def _calculate_time_conversions(data: Dict[str, Any], location: LocationData) -> None:
        """
        Calculate time conversions between local time, UTC, and Julian Day Number.

        Handles timezone-aware conversion from local civil time to UTC and astronomical
        Julian Day Number, including proper DST handling and timezone localization.

        Args:
            data (Dict[str, Any]): Calculation data dictionary containing time components
                (year, month, day, hour, minute, seconds) and optional DST flag.
            location (LocationData): Location data containing timezone information.

        Raises:
            KerykeionException: If DST ambiguity occurs during timezone transitions
                and is_dst parameter is not explicitly set to resolve the ambiguity.

        Side Effects:
            Updates data dictionary with:
            - iso_formatted_utc_datetime: ISO 8601 UTC timestamp
            - iso_formatted_local_datetime: ISO 8601 local timestamp
            - julian_day: Julian Day Number for astronomical calculations

        Note:
            During DST transitions, times may be ambiguous (fall back) or non-existent
            (spring forward). The method raises an exception for ambiguous times unless
            the is_dst parameter is explicitly set to True or False.
        """
        # Convert local time to UTC
        local_timezone = pytz.timezone(location.tz_str)
        naive_datetime = datetime(
            data["year"], data["month"], data["day"], data["hour"], data["minute"], data["seconds"]
        )

        try:
            local_datetime = local_timezone.localize(naive_datetime, is_dst=data.get("is_dst"))
        except pytz.exceptions.AmbiguousTimeError:
            raise KerykeionException(
                "Ambiguous time error! The time falls during a DST transition. "
                "Please specify is_dst=True or is_dst=False to clarify."
            )
        except pytz.exceptions.NonExistentTimeError:
            raise KerykeionException(
                "Non-existent time error! The time does not exist due to DST transition (spring forward). "
                "Please specify a valid time."
            )

        # Store formatted times
        utc_datetime = local_datetime.astimezone(pytz.utc)
        data["iso_formatted_utc_datetime"] = utc_datetime.isoformat()
        data["iso_formatted_local_datetime"] = local_datetime.isoformat()

        # Calculate Julian day
        data["julian_day"] = datetime_to_julian(utc_datetime)

    @staticmethod
    def _calculate_houses(
        data: Dict[str, Any], active_points: Optional[List[AstrologicalPoint]]
    ) -> List[AstrologicalPoint]:
        """
        Calculate house cusps and angular points (Ascendant, MC, etc.).

        Computes the 12 house cusps using the specified house system and calculates
        the four main angles of the chart. Only calculates angular points that are
        included in the active_points list for performance optimization.

        Args:
            data (Dict[str, Any]): Calculation data dictionary containing configuration
                and location information. Updated with calculated house and angle data.
            active_points (Optional[List[AstrologicalPoint]]): List of points to calculate.
                If None, all points are calculated. Angular points not in this list
                are skipped for performance.

        Side Effects:
            Updates data dictionary with:
            - House cusp objects: first_house through twelfth_house
            - Angular points: ascendant, medium_coeli, descendant, imum_coeli
            - houses_names_list: List of all house names
            - _houses_degree_ut: Raw house cusp degrees for internal use

        House Systems Supported:
            All systems supported by Swiss Ephemeris including Placidus, Koch,
            Equal House, Whole Sign, Regiomontanus, Campanus, Topocentric, etc.

        Angular Points Calculated:
            - Ascendant: Eastern horizon point (1st house cusp)
            - Medium Coeli (Midheaven): Southern meridian point (10th house cusp)
            - Descendant: Western horizon point (opposite Ascendant)
            - Imum Coeli: Northern meridian point (opposite Medium Coeli)

        Note:
            House calculations respect the zodiac type (Tropical/Sidereal) and use
            the appropriate Swiss Ephemeris function. Angular points include house
            position and retrograde status (always False for angles).
        """

        # Skip calculation if point is not in active_points
        def should_calculate(point: AstrologicalPoint) -> bool:
            return not active_points or point in active_points

        # Track which axial cusps are actually calculated
        calculated_axial_cusps: List[AstrologicalPoint] = []

        # Calculate houses based on zodiac type
        if data["zodiac_type"] == "Sidereal":
            cusps, ascmc = swe.houses_ex(
                tjdut=data["julian_day"],
                lat=data["lat"],
                lon=data["lng"],
                hsys=str.encode(data["houses_system_identifier"]),
                flags=swe.FLG_SIDEREAL,
            )
        else:  # Tropical zodiac
            cusps, ascmc = swe.houses(
                tjdut=data["julian_day"],
                lat=data["lat"],
                lon=data["lng"],
                hsys=str.encode(data["houses_system_identifier"]),
            )

        # Store house degrees
        data["_houses_degree_ut"] = cusps

        # Create house objects
        point_type: PointType = "House"
        data["first_house"] = get_kerykeion_point_from_degree(cusps[0], "First_House", point_type=point_type)
        data["second_house"] = get_kerykeion_point_from_degree(cusps[1], "Second_House", point_type=point_type)
        data["third_house"] = get_kerykeion_point_from_degree(cusps[2], "Third_House", point_type=point_type)
        data["fourth_house"] = get_kerykeion_point_from_degree(cusps[3], "Fourth_House", point_type=point_type)
        data["fifth_house"] = get_kerykeion_point_from_degree(cusps[4], "Fifth_House", point_type=point_type)
        data["sixth_house"] = get_kerykeion_point_from_degree(cusps[5], "Sixth_House", point_type=point_type)
        data["seventh_house"] = get_kerykeion_point_from_degree(cusps[6], "Seventh_House", point_type=point_type)
        data["eighth_house"] = get_kerykeion_point_from_degree(cusps[7], "Eighth_House", point_type=point_type)
        data["ninth_house"] = get_kerykeion_point_from_degree(cusps[8], "Ninth_House", point_type=point_type)
        data["tenth_house"] = get_kerykeion_point_from_degree(cusps[9], "Tenth_House", point_type=point_type)
        data["eleventh_house"] = get_kerykeion_point_from_degree(cusps[10], "Eleventh_House", point_type=point_type)
        data["twelfth_house"] = get_kerykeion_point_from_degree(cusps[11], "Twelfth_House", point_type=point_type)

        # Store house names
        data["houses_names_list"] = list(get_args(Houses))

        # Calculate axis points
        point_type = "AstrologicalPoint"

        # NOTE: Swiss Ephemeris does not provide direct speeds for angles (ASC/MC),
        # but in realtà si muovono molto velocemente rispetto ai pianeti.
        # Per rappresentare questo in modo coerente, assegniamo ai quattro assi
        # una speed sintetica fissa, molto più alta di quella planetaria tipica.
        # Questo permette a calculate_aspect_movement di considerarli sempre come
        # "più veloci" rispetto ai pianeti quando serve.
        axis_speed = 360.0  # gradi/giorno, valore simbolico ma coerente

        # Calculate Ascendant if needed
        if should_calculate("Ascendant"):
            data["ascendant"] = get_kerykeion_point_from_degree(
                ascmc[0], "Ascendant", point_type=point_type, speed=axis_speed
            )
            data["ascendant"].house = get_planet_house(data["ascendant"].abs_pos, data["_houses_degree_ut"])
            data["ascendant"].retrograde = False
            calculated_axial_cusps.append("Ascendant")

        # Calculate Medium Coeli if needed
        if should_calculate("Medium_Coeli"):
            data["medium_coeli"] = get_kerykeion_point_from_degree(
                ascmc[1], "Medium_Coeli", point_type=point_type, speed=axis_speed
            )
            data["medium_coeli"].house = get_planet_house(data["medium_coeli"].abs_pos, data["_houses_degree_ut"])
            data["medium_coeli"].retrograde = False
            calculated_axial_cusps.append("Medium_Coeli")

        # Calculate Descendant if needed
        if should_calculate("Descendant"):
            dsc_deg = math.fmod(ascmc[0] + 180, 360)
            data["descendant"] = get_kerykeion_point_from_degree(
                dsc_deg, "Descendant", point_type=point_type, speed=axis_speed
            )
            data["descendant"].house = get_planet_house(data["descendant"].abs_pos, data["_houses_degree_ut"])
            data["descendant"].retrograde = False
            calculated_axial_cusps.append("Descendant")

        # Calculate Imum Coeli if needed
        if should_calculate("Imum_Coeli"):
            ic_deg = math.fmod(ascmc[1] + 180, 360)
            data["imum_coeli"] = get_kerykeion_point_from_degree(
                ic_deg, "Imum_Coeli", point_type=point_type, speed=axis_speed
            )
            data["imum_coeli"].house = get_planet_house(data["imum_coeli"].abs_pos, data["_houses_degree_ut"])
            data["imum_coeli"].retrograde = False
            calculated_axial_cusps.append("Imum_Coeli")

        return calculated_axial_cusps

    @staticmethod
    def _calculate_single_planet(
        data: Dict[str, Any],
        planet_name: AstrologicalPoint,
        planet_id: int,
        julian_day: float,
        iflag: int,
        houses_degree_ut: List[float],
        point_type: PointType,
        calculated_planets: List[AstrologicalPoint],
        active_points: List[AstrologicalPoint],
    ) -> None:
        """
        Calculate a single celestial body's position with comprehensive error handling.

        Computes the position of a single planet, asteroid, or other celestial object
        using Swiss Ephemeris, creates a Kerykeion point object, determines house
        position, and assesses retrograde status. Handles calculation errors gracefully
        by logging and removing failed points from the active list.

        Args:
            data (Dict[str, Any]): Main calculation data dictionary to store results.
            planet_name (AstrologicalPoint): Name identifier for the celestial body.
            planet_id (int): Swiss Ephemeris numerical identifier for the object.
            julian_day (float): Julian Day Number for the calculation moment.
            iflag (int): Swiss Ephemeris calculation flags (perspective, zodiac, etc.).
            houses_degree_ut (List[float]): House cusp degrees for house determination.
            point_type (PointType): Classification of the point type for the object.
            calculated_planets (List[str]): Running list of successfully calculated objects.
            active_points (List[AstrologicalPoint]): Active points list (modified on error).

        Side Effects:
            - Adds calculated object to data dictionary using lowercase planet_name as key
            - Appends planet_name to calculated_planets list on success
            - Removes planet_name from active_points list on calculation failure
            - Logs error messages for calculation failures

        Calculated Properties:
            - Zodiacal position (longitude) in degrees
            - House position based on house cusp positions
            - Retrograde status based on velocity (negative = retrograde)
            - Sign, degree, and minute components

        Error Handling:
            If Swiss Ephemeris calculation fails (e.g., for distant asteroids outside
            ephemeris range), the method logs the error and removes the object from
            active_points to prevent cascade failures.

        Note:
            The method uses the Swiss Ephemeris calc_ut function which returns position
            and velocity data. Retrograde determination is based on the velocity
            component being negative (element index 3).
        """
        try:
            # Calculate planet position using Swiss Ephemeris (ecliptic coordinates)
            planet_calc = swe.calc_ut(julian_day, planet_id, iflag)[0]

            # Get declination from equatorial coordinates
            planet_eq = swe.calc_ut(julian_day, planet_id, iflag | swe.FLG_EQUATORIAL)[0]
            declination = planet_eq[1]  # Declination from equatorial coordinates

            # Create Kerykeion point from degree
            data[planet_name.lower()] = get_kerykeion_point_from_degree(
                planet_calc[0], planet_name, point_type=point_type, speed=planet_calc[3], declination=declination
            )

            # Calculate house position
            data[planet_name.lower()].house = get_planet_house(planet_calc[0], houses_degree_ut)

            # Determine if planet is retrograde
            data[planet_name.lower()].retrograde = planet_calc[3] < 0

            # Track calculated planet
            calculated_planets.append(planet_name)

        except Exception as e:
            logging.error(f"Error calculating {planet_name}: {e}")
            if planet_name in active_points:
                active_points.remove(planet_name)

    @staticmethod
    def _ensure_point_calculated(
        point: AstrologicalPoint,
        data: Dict[str, Any],
        julian_day: float,
        iflag: int,
        houses_degree_ut: List[float],
        point_type: PointType,
        active_points: List[AstrologicalPoint],
    ) -> None:
        """
        Ensure a required point is calculated for Arabic Parts computation.

        If the point is not already in the data dictionary, calculates it using
        the appropriate method (Swiss Ephemeris for planets, houses for Ascendant).

        Args:
            point: The point to ensure is calculated
            data: Main calculation data dictionary
            julian_day: Julian Day Number
            iflag: Swiss Ephemeris calculation flags
            houses_degree_ut: House cusp degrees
            point_type: Classification of the point type
            active_points: List of active points (may be modified)
        """
        point_key = point.lower()
        if point_key in data:
            return  # Already calculated

        # Handle Ascendant specially (from houses calculation)
        if point == "Ascendant":
            if data["zodiac_type"] == "Sidereal":
                cusps, ascmc = swe.houses_ex(
                    tjdut=data["julian_day"],
                    lat=data["lat"],
                    lon=data["lng"],
                    hsys=str.encode(data["houses_system_identifier"]),
                    flags=swe.FLG_SIDEREAL,
                )
            else:
                cusps, ascmc = swe.houses(
                    tjdut=data["julian_day"],
                    lat=data["lat"],
                    lon=data["lng"],
                    hsys=str.encode(data["houses_system_identifier"]),
                )
            data["ascendant"] = get_kerykeion_point_from_degree(ascmc[0], "Ascendant", point_type=point_type)
            data["ascendant"].house = get_planet_house(ascmc[0], houses_degree_ut)
            data["ascendant"].retrograde = False
            return

        # For planets, use STANDARD_PLANETS mapping
        if point in STANDARD_PLANETS:
            planet_id = STANDARD_PLANETS[point]
            planet_calc = swe.calc_ut(julian_day, planet_id, iflag)[0]
            # Get declination from equatorial coordinates (matching _calculate_single_planet)
            planet_eq = swe.calc_ut(julian_day, planet_id, iflag | swe.FLG_EQUATORIAL)[0]
            declination = planet_eq[1]
            data[point_key] = get_kerykeion_point_from_degree(
                planet_calc[0], point, point_type=point_type, speed=planet_calc[3], declination=declination
            )
            data[point_key].house = get_planet_house(planet_calc[0], houses_degree_ut)
            data[point_key].retrograde = planet_calc[3] < 0

    @staticmethod
    def _calculate_arabic_part(
        part_name: AstrologicalPoint,
        config: Dict[str, Any],
        data: Dict[str, Any],
        julian_day: float,
        iflag: int,
        houses_degree_ut: List[float],
        point_type: PointType,
        active_points: List[AstrologicalPoint],
        calculated_planets: List[AstrologicalPoint],
    ) -> None:
        """
        Calculate an Arabic Part (Lot) using its configuration.

        This method handles:
        - Auto-activation of required prerequisite points
        - Day/night chart detection for parts with day/night variants
        - Formula application and result storage

        Args:
            part_name: Name of the Arabic Part to calculate
            config: Configuration dict with required points and formula(s)
            data: Main calculation data dictionary
            julian_day: Julian Day Number
            iflag: Swiss Ephemeris calculation flags
            houses_degree_ut: House cusp degrees
            point_type: Classification of the point type
            active_points: List of active points (may be modified)
            calculated_planets: List of successfully calculated points
        """
        required_points = config["required"]

        # Auto-activate and calculate missing required points
        missing_points = [p for p in required_points if p not in active_points]
        if missing_points:
            logging.info(f"Automatically adding required points for {part_name}: {missing_points}")
            active_points.extend(missing_points)

        # Ensure all required points are calculated
        for point in required_points:
            AstrologicalSubjectFactory._ensure_point_calculated(
                point, data, julian_day, iflag, houses_degree_ut, point_type, active_points
            )

        # Verify all required points are available
        required_keys = [p.lower() for p in required_points]
        if not all(k in data for k in required_keys):
            return  # Cannot calculate if missing dependencies

        # Get point positions
        positions = [data[p.lower()].abs_pos for p in required_points]

        # Determine if day or night chart (for parts with day/night variants)
        if "day_formula" in config and "night_formula" in config:
            if data.get("sun") and data["sun"].house:
                is_day_chart = get_house_number(data["sun"].house) < 7
            else:
                is_day_chart = True  # Default to day chart

            formula = config["day_formula"] if is_day_chart else config["night_formula"]
        else:
            formula = config["formula"]

        # Calculate the part degree
        part_deg = math.fmod(formula(*positions), 360)
        if part_deg < 0:
            part_deg += 360

        # Store the result
        part_key = part_name.lower()
        data[part_key] = get_kerykeion_point_from_degree(part_deg, part_name, point_type=point_type)
        data[part_key].house = get_planet_house(part_deg, houses_degree_ut)
        data[part_key].retrograde = False  # Arabic Parts are never retrograde
        calculated_planets.append(part_name)

    @staticmethod
    def _calculate_planets(
        data: Dict[str, Any],
        active_points: List[AstrologicalPoint],
        calculated_axial_cusps: Optional[List[AstrologicalPoint]] = None,
    ) -> None:
        """
        Calculate positions for all requested celestial bodies and special points.

        This comprehensive method calculates positions for a wide range of astrological
        points including traditional planets, lunar nodes, asteroids, trans-Neptunian
        objects, fixed stars, Arabic parts, and specialized points like Vertex.

        The calculation is performed selectively based on the active_points list for
        performance optimization. Some Arabic parts automatically activate their
        prerequisite points if needed.

        Args:
            data (Dict[str, Any]): Main calculation data dictionary. Updated with all
                calculated planetary positions and related metadata.
            active_points (List[AstrologicalPoint]): Mutable list of points to calculate.
                Modified during execution to remove failed calculations and add
                automatically required points for Arabic parts.

        Celestial Bodies Calculated:
            Traditional Planets:
                - Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn
                - Uranus, Neptune, Pluto

            Lunar Nodes:
                - Mean Node, True Node (North nodes)
                - Mean South Node, True South Node (calculated as opposites)

            Lilith Points:
                - Mean Lilith (Mean Black Moon Lilith)
                - True Lilith (Osculating Black Moon Lilith)

            Asteroids:
                - Ceres, Pallas, Juno, Vesta (main belt asteroids)

            Centaurs:
                - Chiron, Pholus

            Trans-Neptunian Objects:
                - Eris, Sedna, Haumea, Makemake
                - Ixion, Orcus, Quaoar

            Fixed Stars:
                - Regulus, Spica (examples, extensible)

            Arabic Parts (Lots):
                - Pars Fortunae (Part of Fortune)
                - Pars Spiritus (Part of Spirit)
                - Pars Amoris (Part of Love/Eros)
                - Pars Fidei (Part of Faith)

            Special Points:
                - Earth (for heliocentric perspectives)
                - Vertex and Anti-Vertex

        Side Effects:
            - Updates data dictionary with all calculated positions
            - Modifies active_points list by removing failed calculations
            - Adds prerequisite points for Arabic parts calculations
            - Updates data["active_points"] with successfully calculated objects

        Error Handling:
            Individual calculation failures (e.g., asteroids outside ephemeris range)
            are handled gracefully with logging and removal from active_points.
            This prevents cascade failures while maintaining calculation integrity.

        Arabic Parts Logic:
            - Day/night birth detection based on Sun's house position
            - Automatic activation of required base points (Sun, Moon, Ascendant, etc.)
            - Classical formulae with day/night variations where applicable
            - All parts marked as non-retrograde (conceptual points)

        Performance Notes:
            - Only points in active_points are calculated (selective computation)
            - Failed calculations are removed to prevent repeated attempts
            - Some expensive calculations (like distant TNOs) may timeout
            - Fixed stars use different calculation methods than planets

        Note:
            The method maintains a running list of successfully calculated planets
            and updates the active_points list to reflect actual availability.
            This ensures that dependent calculations and aspects only use valid data.
        """

        # Skip calculation if point is not in active_points
        def should_calculate(point: AstrologicalPoint) -> bool:
            return not active_points or point in active_points

        point_type: PointType = "AstrologicalPoint"
        julian_day = data["julian_day"]
        iflag = data["_iflag"]
        houses_degree_ut = data["_houses_degree_ut"]

        # Track which planets are actually calculated
        calculated_planets: List[AstrologicalPoint] = []

        # =============================================================================
        # STANDARD PLANETS (using centralized mapping)
        # =============================================================================
        # This loop replaces ~150 lines of repetitive individual planet calculations.
        # All standard planets (Sun through Vesta) use the same calculation pattern.
        # South lunar nodes are calculated after True_North_Lunar_Node to preserve
        # the original calculation order (Mean_North, True_North, Mean_South, True_South).
        for planet_name, planet_id in STANDARD_PLANETS.items():
            if should_calculate(planet_name):
                AstrologicalSubjectFactory._calculate_single_planet(
                    data,
                    planet_name,
                    planet_id,
                    julian_day,
                    iflag,
                    houses_degree_ut,
                    point_type,
                    calculated_planets,
                    active_points,
                )

                # Special handling for lunar nodes: calculate declination
                if planet_name in ("Mean_North_Lunar_Node", "True_North_Lunar_Node"):
                    node_key = planet_name.lower()
                    if node_key in data:
                        # Calculate declination using equatorial coordinates
                        node_eq = swe.calc_ut(julian_day, planet_id, iflag | swe.FLG_EQUATORIAL)[0]
                        data[node_key].declination = node_eq[1]

                # Calculate corresponding south node immediately after each north node
                if planet_name == "Mean_North_Lunar_Node":
                    south_node: AstrologicalPoint = "Mean_South_Lunar_Node"
                    north_key = planet_name.lower()
                    if should_calculate(south_node) and north_key in data:
                        north_data = data[north_key]
                        south_deg = math.fmod(north_data.abs_pos + 180, 360)
                        data[south_node.lower()] = get_kerykeion_point_from_degree(
                            south_deg,
                            south_node,
                            point_type=point_type,
                            speed=-north_data.speed if north_data.speed is not None else None,
                            declination=-north_data.declination if north_data.declination is not None else None,
                        )
                        data[south_node.lower()].house = get_planet_house(south_deg, houses_degree_ut)
                        data[south_node.lower()].retrograde = north_data.retrograde
                        calculated_planets.append(south_node)

                if planet_name == "True_North_Lunar_Node":
                    south_node_true: AstrologicalPoint = "True_South_Lunar_Node"
                    north_key = planet_name.lower()
                    if should_calculate(south_node_true) and north_key in data:
                        north_data = data[north_key]
                        south_deg = math.fmod(north_data.abs_pos + 180, 360)
                        data[south_node_true.lower()] = get_kerykeion_point_from_degree(
                            south_deg,
                            south_node_true,
                            point_type=point_type,
                            speed=-north_data.speed if north_data.speed is not None else None,
                            declination=-north_data.declination if north_data.declination is not None else None,
                        )
                        data[south_node_true.lower()].house = get_planet_house(south_deg, houses_degree_ut)
                        data[south_node_true.lower()].retrograde = north_data.retrograde
                        calculated_planets.append(south_node_true)

        # =============================================================================
        # TRANS-NEPTUNIAN OBJECTS (using centralized mapping)
        # =============================================================================
        # TNOs require AST_OFFSET and may fail for dates outside ephemeris range
        for tno_name, asteroid_num in TNO_PLANETS.items():
            if should_calculate(tno_name):
                try:
                    AstrologicalSubjectFactory._calculate_single_planet(
                        data,
                        tno_name,
                        swe.AST_OFFSET + asteroid_num,
                        julian_day,
                        iflag,
                        houses_degree_ut,
                        point_type,
                        calculated_planets,
                        active_points,
                    )
                except Exception as e:
                    logging.warning(f"Could not calculate {tno_name} position: {e}")
                    if tno_name in active_points:
                        active_points.remove(tno_name)

        # =============================================================================
        # FIXED STARS (using centralized list)
        # =============================================================================
        # Fixed stars use different calculation method (swe.fixstar_ut)
        for star_name in FIXED_STARS:
            if should_calculate(star_name):
                try:
                    # Ecliptic longitude for zodiac placement
                    pos_ecl = swe.fixstar_ut(star_name, julian_day, iflag)[0]
                    star_deg = pos_ecl[0]
                    star_speed = pos_ecl[3] if len(pos_ecl) > 3 else 0.0
                    # Equatorial coordinates for true declination
                    pos_eq = swe.fixstar_ut(star_name, julian_day, iflag | swe.FLG_EQUATORIAL)[0]
                    star_dec = pos_eq[1] if len(pos_eq) > 1 else None

                    star_key = star_name.lower()
                    data[star_key] = get_kerykeion_point_from_degree(
                        star_deg, star_name, point_type=point_type, speed=star_speed, declination=star_dec
                    )
                    data[star_key].house = get_planet_house(star_deg, houses_degree_ut)
                    data[star_key].retrograde = False  # Fixed stars are never retrograde
                    calculated_planets.append(star_name)
                except Exception as e:
                    logging.warning(f"Could not calculate {star_name} position: {e}")
                    if star_name in active_points:
                        active_points.remove(star_name)

        # =============================================================================
        # ARABIC PARTS / LOTS (using centralized configuration)
        # =============================================================================
        # This loop replaces ~260 lines of repetitive Arabic Parts calculations.
        # Each part is configured in ARABIC_PARTS_CONFIG with its formula and requirements.
        for part_name, part_config in ARABIC_PARTS_CONFIG.items():
            if should_calculate(part_name):
                AstrologicalSubjectFactory._calculate_arabic_part(
                    part_name,
                    part_config,
                    data,
                    julian_day,
                    iflag,
                    houses_degree_ut,
                    point_type,
                    active_points,
                    calculated_planets,
                )

        # =============================================================================
        # VERTEX AND ANTI-VERTEX
        # =============================================================================
        if should_calculate("Vertex") or should_calculate("Anti_Vertex"):
            try:
                # Vertex is at ascmc[3] in Swiss Ephemeris
                if data["zodiac_type"] == "Sidereal":
                    _, ascmc = swe.houses_ex(
                        tjdut=data["julian_day"],
                        lat=data["lat"],
                        lon=data["lng"],
                        hsys=str.encode("V"),  # Vertex works best with Vehlow system
                        flags=swe.FLG_SIDEREAL,
                    )
                else:
                    _, ascmc = swe.houses(
                        tjdut=data["julian_day"], lat=data["lat"], lon=data["lng"], hsys=str.encode("V")
                    )

                vertex_deg = ascmc[3]

                # Calculate Vertex if requested
                if should_calculate("Vertex"):
                    data["vertex"] = get_kerykeion_point_from_degree(vertex_deg, "Vertex", point_type=point_type)
                    data["vertex"].house = get_planet_house(vertex_deg, houses_degree_ut)
                    data["vertex"].retrograde = False
                    calculated_planets.append("Vertex")

                # Calculate Anti-Vertex if requested
                if should_calculate("Anti_Vertex"):
                    anti_vertex_deg = math.fmod(vertex_deg + 180, 360)
                    data["anti_vertex"] = get_kerykeion_point_from_degree(
                        anti_vertex_deg, "Anti_Vertex", point_type=point_type
                    )
                    data["anti_vertex"].house = get_planet_house(anti_vertex_deg, houses_degree_ut)
                    data["anti_vertex"].retrograde = False
                    calculated_planets.append("Anti_Vertex")

            except Exception as e:
                logging.warning("Could not calculate Vertex/Anti-Vertex position, error: %s", e)
                if "Vertex" in active_points:
                    active_points.remove("Vertex")
                if "Anti_Vertex" in active_points:
                    active_points.remove("Anti_Vertex")

        # Store only the planets that were actually calculated
        all_calculated_points = calculated_planets.copy()
        if calculated_axial_cusps:
            all_calculated_points.extend(calculated_axial_cusps)
        data["active_points"] = all_calculated_points

    @staticmethod
    def _calculate_day_of_week(data: Dict[str, Any]) -> None:
        """
        Calculate the day of the week for the given astronomical event.

        Determines the day of the week corresponding to the local datetime
        using the standard library for consistency.

        Args:
            data (Dict[str, Any]): Calculation data dictionary containing
                iso_formatted_local_datetime. Updated with the calculated day_of_week string.

        Side Effects:
            Updates data dictionary with:
            - day_of_week: Human-readable day name (e.g., "Monday", "Tuesday")
        """
        dt = datetime.fromisoformat(data["iso_formatted_local_datetime"])
        data["day_of_week"] = dt.strftime("%A")


if __name__ == "__main__":
    from kerykeion.schemas.kr_literals import AstrologicalPoint

    # Example usage
    new_active_points: List[AstrologicalPoint] = [
        "Sun",
        "Moon",
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
        "Mean_North_Lunar_Node",
        "True_North_Lunar_Node",
        "Mean_South_Lunar_Node",
        "True_South_Lunar_Node",
        "Chiron",
        "Mean_Lilith",
        "True_Lilith",
        "Earth",
        "Pholus",
        "Ceres",
        "Pallas",
        "Juno",
        "Vesta",
        "Eris",
        "Sedna",
        "Haumea",
        "Makemake",
        "Ixion",
        "Orcus",
        "Quaoar",
        "Regulus",
        "Spica",
        "Pars_Fortunae",
        "Pars_Spiritus",
        "Pars_Amoris",
        "Pars_Fidei",
        "Vertex",
        "Anti_Vertex",
        "Ascendant",
        "Medium_Coeli",
        "Descendant",
        "Imum_Coeli",
    ]
    subject = AstrologicalSubjectFactory.from_current_time(name="Test Subject", active_points=new_active_points)
    print(subject.sun)
    print(subject.pars_amoris)
    print(subject.eris)
    print(subject.active_points)
    print(subject.pars_fidei)
    print("----")
    print(subject.anti_vertex)

    # Create JSON output
    json_string = subject.model_dump_json(exclude_none=True, indent=2)

    # Write JSON to home
    with open(Path.home() / "kerykeion_subject_example.json", "w", encoding="utf-8") as f:
        f.write(json_string)
