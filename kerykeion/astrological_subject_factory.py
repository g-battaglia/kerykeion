# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import pytz
import swisseph as swe
import logging
import warnings
import math
from datetime import datetime
from pathlib import Path
from typing import Union, Optional, List, Dict, Any, Literal, get_args, cast, TypedDict, Set
from functools import cached_property, lru_cache
from dataclasses import dataclass, field
from typing import Callable


from kerykeion.fetch_geonames import FetchGeonames
from kerykeion.kr_types import (
    KerykeionException,
    ZodiacType,
    AstrologicalSubjectModel,
    LunarPhaseModel,
    KerykeionPointModel,
    PointType,
    SiderealMode,
    HousesSystemIdentifier,
    PerspectiveType,
    AstrologicalPoint,
    Houses,
)
from kerykeion.utilities import (
    get_number_from_name,
    get_kerykeion_point_from_degree,
    get_planet_house,
    check_and_adjust_polar_latitude,
    calculate_moon_phase,
    datetime_to_julian,
    get_house_number
)
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

# Default configuration values
DEFAULT_GEONAMES_USERNAME = "century.boy"
DEFAULT_SIDEREAL_MODE: SiderealMode = "FAGAN_BRADLEY"
DEFAULT_HOUSES_SYSTEM_IDENTIFIER: HousesSystemIdentifier = "P"
DEFAULT_ZODIAC_TYPE: ZodiacType = "Tropic"
DEFAULT_PERSPECTIVE_TYPE: PerspectiveType = "Apparent Geocentric"
DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS = 30

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

NOW = datetime.now()


@dataclass
class ChartConfiguration:
    """Configuration settings for astrological chart calculations"""
    zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE
    sidereal_mode: Optional[SiderealMode] = None
    houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER
    perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE

    def validate(self) -> None:
        """Validate configuration settings"""
        # Validate zodiac type
        if self.zodiac_type not in get_args(ZodiacType):
            raise KerykeionException(
                f"'{self.zodiac_type}' is not a valid zodiac type! Available types are: {get_args(ZodiacType)}"
            )

        # Validate sidereal mode settings
        if self.sidereal_mode and self.zodiac_type == "Tropic":
            raise KerykeionException("You can't set a sidereal mode with a Tropic zodiac type!")

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
    """Information about a geographical location"""
    city: str = "Greenwich"
    nation: str = "GB"
    lat: float = 51.5074
    lng: float = 0.0
    tz_str: str = "Etc/GMT"
    altitude: Optional[float] = None

    # Storage for city data fetched from geonames
    city_data: Dict[str, str] = field(default_factory=dict)

    def fetch_from_geonames(self, username: str, cache_expire_after_days: int) -> None:
        """Fetch location data from geonames API"""
        logging.info(f"Fetching timezone/coordinates for {self.city}, {self.nation} from geonames")

        geonames = FetchGeonames(
            self.city,
            self.nation,
            username=username,
            cache_expire_after_days=cache_expire_after_days
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
        """Prepare location data for astrological calculations"""
        # Adjust latitude for polar regions
        self.lat = check_and_adjust_polar_latitude(self.lat)


class AstrologicalSubjectFactory:
    """
    Factory class for creating astrological subjects with planetary positions,
    houses, and other astrological information for a specific time and location.

    This factory creates and returns AstrologicalSubjectModel instances and provides
    multiple creation methods for different initialization scenarios.
    """

    @classmethod
    def from_birth_data(
        cls,
        name: str = "Now",
        year: int = NOW.year,
        month: int = NOW.month,
        day: int = NOW.day,
        hour: int = NOW.hour,
        minute: int = NOW.minute,
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
        active_points: List[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,
        *,
        seconds: int = 0,

    ) -> AstrologicalSubjectModel:
        """
        Create an astrological subject from standard birth/event details.

        Args:
            name: Subject name
            year, month, day, hour, minute, seconds: Time components
            city: Location name
            nation: Country code
            lng, lat: Coordinates (optional if online=True)
            tz_str: Timezone string (optional if online=True)
            geonames_username: Username for geonames API
            online: Whether to fetch location data online
            zodiac_type: Type of zodiac (Tropical or Sidereal)
            sidereal_mode: Mode for sidereal calculations
            houses_system_identifier: House system for calculations
            perspective_type: Perspective type for calculations
            cache_expire_after_days: Cache duration for geonames data
            is_dst: Daylight saving time flag
            altitude: Location altitude for topocentric calculations
            active_points: Set of points to calculate (optimization)

        Returns:
            An AstrologicalSubjectModel with calculated data
        """
        logging.debug("Starting Kerykeion calculation")

        if "Sun" not in active_points:
            logging.info("Automatically adding 'Sun' to active points")
            active_points.append("Sun")

        if "Moon" not in active_points:
            logging.info("Automatically adding 'Moon' to active points")
            active_points.append("Moon")

        if "Ascendant" not in active_points:
            logging.info("Automatically adding 'Ascendant' to active points")
            active_points.append("Ascendant")

        if "Medium_Coeli" not in active_points:
            logging.info("Automatically adding 'Medium_Coeli' to active points")
            active_points.append("Medium_Coeli")

        if "Mercury" not in active_points:
            logging.info("Automatically adding 'Mercury' to active points")
            active_points.append("Mercury")

        if "Venus" not in active_points:
            logging.info("Automatically adding 'Venus' to active points")
            active_points.append("Venus")

        if "Mars" not in active_points:
            logging.info("Automatically adding 'Mars' to active points")
            active_points.append("Mars")

        if "Jupiter" not in active_points:
            logging.info("Automatically adding 'Jupiter' to active points")
            active_points.append("Jupiter")

        if "Saturn" not in active_points:
            logging.info("Automatically adding 'Saturn' to active points")
            active_points.append("Saturn")

        # Create a calculation data container
        calc_data = {}

        # Basic identity
        calc_data["name"] = name
        calc_data["json_dir"] = str(Path.home())

        # Initialize configuration
        config = ChartConfiguration(
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
        )
        config.validate()

        # Add configuration data to calculation data
        calc_data["zodiac_type"] = config.zodiac_type
        calc_data["sidereal_mode"] = config.sidereal_mode
        calc_data["houses_system_identifier"] = config.houses_system_identifier
        calc_data["perspective_type"] = config.perspective_type

        # Set up geonames username if needed
        if geonames_username is None and online and (not lat or not lng or not tz_str):
            logging.warning(GEONAMES_DEFAULT_USERNAME_WARNING)
            geonames_username = DEFAULT_GEONAMES_USERNAME

        # Initialize location data
        location = LocationData(
            city=city or "Greenwich",
            nation=nation or "GB",
            lat=lat if lat is not None else 51.5074,
            lng=lng if lng is not None else 0.0,
            tz_str=tz_str or "Etc/GMT",
            altitude=altitude
        )

        # If offline mode is requested but required data is missing, raise error
        if not online and (not tz_str or not lat or not lng):
            raise KerykeionException(
                "For offline mode, you must provide timezone (tz_str) and coordinates (lat, lng)"
            )

        # Fetch location data if needed
        if online and (not tz_str or not lat or not lng):
            location.fetch_from_geonames(
                username=geonames_username or DEFAULT_GEONAMES_USERNAME,
                cache_expire_after_days=cache_expire_after_days
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
        calc_data["active_points"] = active_points

        # Calculate time conversions
        cls._calculate_time_conversions(calc_data, location)

        # Initialize Swiss Ephemeris and calculate houses and planets
        cls._setup_ephemeris(calc_data, config)
        cls._calculate_houses(calc_data, active_points)
        cls._calculate_planets(calc_data, active_points)
        cls._calculate_day_of_week(calc_data)

        # Calculate lunar phase
        calc_data["lunar_phase"] = calculate_moon_phase(
            calc_data["moon"].abs_pos,
            calc_data["sun"].abs_pos
        )

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
        online: bool = False,
        lng: float = 0.0,
        lat: float = 51.5074,
        geonames_username: str = DEFAULT_GEONAMES_USERNAME,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: Optional[SiderealMode] = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        altitude: Optional[float] = None,
        active_points: List[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS
    ) -> AstrologicalSubjectModel:
        """
        Create an astrological subject from an ISO formatted UTC time.

        Args:
            name: Subject name
            iso_utc_time: ISO formatted UTC time string
            city: Location name
            nation: Country code
            tz_str: Timezone string
            online: Whether to fetch location data online
            lng, lat: Coordinates
            geonames_username: Username for geonames API
            zodiac_type: Type of zodiac
            sidereal_mode: Mode for sidereal calculations
            houses_system_identifier: House system
            perspective_type: Perspective for calculations
            altitude: Location altitude
            active_points: Set of points to calculate

        Returns:
            AstrologicalSubjectModel instance
        """
        # Parse the ISO time
        dt = datetime.fromisoformat(iso_utc_time.replace('Z', '+00:00'))

        # Get location data if online mode is enabled
        if online:
            if geonames_username == DEFAULT_GEONAMES_USERNAME:
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
            active_points=active_points
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
        active_points: List[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS
    ) -> AstrologicalSubjectModel:
        """
        Create an astrological subject for the current time.

        Args:
            name: Subject name
            city: Location name
            nation: Country code
            lng, lat: Coordinates
            tz_str: Timezone string
            geonames_username: Username for geonames API
            online: Whether to fetch location data online
            zodiac_type: Type of zodiac
            sidereal_mode: Mode for sidereal calculations
            houses_system_identifier: House system
            perspective_type: Perspective for calculations
            active_points: Set of points to calculate

        Returns:
            AstrologicalSubjectModel for current time
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
            active_points=active_points
        )

    @classmethod
    def _calculate_time_conversions(cls, data: Dict[str, Any], location: LocationData) -> None:
        """Calculate time conversions between local time, UTC and Julian day"""
        # Convert local time to UTC
        local_timezone = pytz.timezone(location.tz_str)
        naive_datetime = datetime(
            data["year"], data["month"], data["day"],
            data["hour"], data["minute"], data["seconds"]
        )

        try:
            local_datetime = local_timezone.localize(naive_datetime, is_dst=data.get("is_dst"))
        except pytz.exceptions.AmbiguousTimeError:
            raise KerykeionException(
                "Ambiguous time error! The time falls during a DST transition. "
                "Please specify is_dst=True or is_dst=False to clarify."
            )

        # Store formatted times
        utc_datetime = local_datetime.astimezone(pytz.utc)
        data["iso_formatted_utc_datetime"] = utc_datetime.isoformat()
        data["iso_formatted_local_datetime"] = local_datetime.isoformat()

        # Calculate Julian day
        data["julian_day"] = datetime_to_julian(utc_datetime)

    @classmethod
    def _setup_ephemeris(cls, data: Dict[str, Any], config: ChartConfiguration) -> None:
        """Set up Swiss Ephemeris with appropriate flags"""
        # Set ephemeris path
        swe.set_ephe_path(str(Path(__file__).parent.absolute() / "sweph"))

        # Base flags
        iflag = swe.FLG_SWIEPH + swe.FLG_SPEED

        # Add perspective flags
        if config.perspective_type == "True Geocentric":
            iflag += swe.FLG_TRUEPOS
        elif config.perspective_type == "Heliocentric":
            iflag += swe.FLG_HELCTR
        elif config.perspective_type == "Topocentric":
            iflag += swe.FLG_TOPOCTR
            # Set topocentric coordinates
            swe.set_topo(data["lng"], data["lat"], data["altitude"] or 0)

        # Add sidereal flag if needed
        if config.zodiac_type == "Sidereal":
            iflag += swe.FLG_SIDEREAL
            # Set sidereal mode
            mode = f"SIDM_{config.sidereal_mode}"
            swe.set_sid_mode(getattr(swe, mode))
            logging.debug(f"Using sidereal mode: {mode}")

        # Save house system name and iflag for later use
        data["houses_system_name"] = swe.house_name(
            config.houses_system_identifier.encode('ascii')
        )
        data["_iflag"] = iflag

    @classmethod
    def _calculate_houses(cls, data: Dict[str, Any], active_points: Optional[List[AstrologicalPoint]]) -> None:
        """Calculate house cusps and axis points"""
        # Skip calculation if point is not in active_points
        should_calculate: Callable[[AstrologicalPoint], bool] = lambda point: not active_points or point in active_points
        # Track which axial cusps are actually calculated
        calculated_axial_cusps = []

        # Calculate houses based on zodiac type
        if data["zodiac_type"] == "Sidereal":
            cusps, ascmc = swe.houses_ex(
                tjdut=data["julian_day"],
                lat=data["lat"],
                lon=data["lng"],
                hsys=str.encode(data["houses_system_identifier"]),
                flags=swe.FLG_SIDEREAL
            )
        else:  # Tropical zodiac
            cusps, ascmc = swe.houses(
                tjdut=data["julian_day"],
                lat=data["lat"],
                lon=data["lng"],
                hsys=str.encode(data["houses_system_identifier"])
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

        # Calculate Ascendant if needed
        if should_calculate("Ascendant"):
            data["ascendant"] = get_kerykeion_point_from_degree(ascmc[0], "Ascendant", point_type=point_type)
            data["ascendant"].house = get_planet_house(data["ascendant"].abs_pos, data["_houses_degree_ut"])
            data["ascendant"].retrograde = False
            calculated_axial_cusps.append("Ascendant")

        # Calculate Medium Coeli if needed
        if should_calculate("Medium_Coeli"):
            data["medium_coeli"] = get_kerykeion_point_from_degree(ascmc[1], "Medium_Coeli", point_type=point_type)
            data["medium_coeli"].house = get_planet_house(data["medium_coeli"].abs_pos, data["_houses_degree_ut"])
            data["medium_coeli"].retrograde = False
            calculated_axial_cusps.append("Medium_Coeli")

        # Calculate Descendant if needed
        if should_calculate("Descendant"):
            dsc_deg = math.fmod(ascmc[0] + 180, 360)
            data["descendant"] = get_kerykeion_point_from_degree(dsc_deg, "Descendant", point_type=point_type)
            data["descendant"].house = get_planet_house(data["descendant"].abs_pos, data["_houses_degree_ut"])
            data["descendant"].retrograde = False
            calculated_axial_cusps.append("Descendant")

        # Calculate Imum Coeli if needed
        if should_calculate("Imum_Coeli"):
            ic_deg = math.fmod(ascmc[1] + 180, 360)
            data["imum_coeli"] = get_kerykeion_point_from_degree(ic_deg, "Imum_Coeli", point_type=point_type)
            data["imum_coeli"].house = get_planet_house(data["imum_coeli"].abs_pos, data["_houses_degree_ut"])
            data["imum_coeli"].retrograde = False
            calculated_axial_cusps.append("Imum_Coeli")

    @classmethod
    def _calculate_planets(cls, data: Dict[str, Any], active_points: List[AstrologicalPoint]) -> None:
        """Calculate planetary positions and related information"""
        # Skip calculation if point is not in active_points
        should_calculate: Callable[[AstrologicalPoint], bool] = lambda point: not active_points or point in active_points

        point_type: PointType = "AstrologicalPoint"
        julian_day = data["julian_day"]
        iflag = data["_iflag"]
        houses_degree_ut = data["_houses_degree_ut"]

        # Track which planets are actually calculated
        calculated_planets = []

        # ==================
        # MAIN PLANETS
        # ==================

        # Calculate Sun
        if should_calculate("Sun"):
            sun_deg = swe.calc_ut(julian_day, 0, iflag)[0][0]
            data["sun"] = get_kerykeion_point_from_degree(sun_deg, "Sun", point_type=point_type)
            data["sun"].house = get_planet_house(sun_deg, houses_degree_ut)
            data["sun"].retrograde = swe.calc_ut(julian_day, 0, iflag)[0][3] < 0
            calculated_planets.append("Sun")

        # Calculate Moon
        if should_calculate("Moon"):
            moon_deg = swe.calc_ut(julian_day, 1, iflag)[0][0]
            data["moon"] = get_kerykeion_point_from_degree(moon_deg, "Moon", point_type=point_type)
            data["moon"].house = get_planet_house(moon_deg, houses_degree_ut)
            data["moon"].retrograde = swe.calc_ut(julian_day, 1, iflag)[0][3] < 0
            calculated_planets.append("Moon")

        # Calculate Mercury
        if should_calculate("Mercury"):
            mercury_deg = swe.calc_ut(julian_day, 2, iflag)[0][0]
            data["mercury"] = get_kerykeion_point_from_degree(mercury_deg, "Mercury", point_type=point_type)
            data["mercury"].house = get_planet_house(mercury_deg, houses_degree_ut)
            data["mercury"].retrograde = swe.calc_ut(julian_day, 2, iflag)[0][3] < 0
            calculated_planets.append("Mercury")

        # Calculate Venus
        if should_calculate("Venus"):
            venus_deg = swe.calc_ut(julian_day, 3, iflag)[0][0]
            data["venus"] = get_kerykeion_point_from_degree(venus_deg, "Venus", point_type=point_type)
            data["venus"].house = get_planet_house(venus_deg, houses_degree_ut)
            data["venus"].retrograde = swe.calc_ut(julian_day, 3, iflag)[0][3] < 0
            calculated_planets.append("Venus")

        # Calculate Mars
        if should_calculate("Mars"):
            mars_deg = swe.calc_ut(julian_day, 4, iflag)[0][0]
            data["mars"] = get_kerykeion_point_from_degree(mars_deg, "Mars", point_type=point_type)
            data["mars"].house = get_planet_house(mars_deg, houses_degree_ut)
            data["mars"].retrograde = swe.calc_ut(julian_day, 4, iflag)[0][3] < 0
            calculated_planets.append("Mars")

        # Calculate Jupiter
        if should_calculate("Jupiter"):
            jupiter_deg = swe.calc_ut(julian_day, 5, iflag)[0][0]
            data["jupiter"] = get_kerykeion_point_from_degree(jupiter_deg, "Jupiter", point_type=point_type)
            data["jupiter"].house = get_planet_house(jupiter_deg, houses_degree_ut)
            data["jupiter"].retrograde = swe.calc_ut(julian_day, 5, iflag)[0][3] < 0
            calculated_planets.append("Jupiter")

        # Calculate Saturn
        if should_calculate("Saturn"):
            saturn_deg = swe.calc_ut(julian_day, 6, iflag)[0][0]
            data["saturn"] = get_kerykeion_point_from_degree(saturn_deg, "Saturn", point_type=point_type)
            data["saturn"].house = get_planet_house(saturn_deg, houses_degree_ut)
            data["saturn"].retrograde = swe.calc_ut(julian_day, 6, iflag)[0][3] < 0
            calculated_planets.append("Saturn")

        # Calculate Uranus
        if should_calculate("Uranus"):
            uranus_deg = swe.calc_ut(julian_day, 7, iflag)[0][0]
            data["uranus"] = get_kerykeion_point_from_degree(uranus_deg, "Uranus", point_type=point_type)
            data["uranus"].house = get_planet_house(uranus_deg, houses_degree_ut)
            data["uranus"].retrograde = swe.calc_ut(julian_day, 7, iflag)[0][3] < 0
            calculated_planets.append("Uranus")

        # Calculate Neptune
        if should_calculate("Neptune"):
            neptune_deg = swe.calc_ut(julian_day, 8, iflag)[0][0]
            data["neptune"] = get_kerykeion_point_from_degree(neptune_deg, "Neptune", point_type=point_type)
            data["neptune"].house = get_planet_house(neptune_deg, houses_degree_ut)
            data["neptune"].retrograde = swe.calc_ut(julian_day, 8, iflag)[0][3] < 0
            calculated_planets.append("Neptune")

        # Calculate Pluto
        if should_calculate("Pluto"):
            pluto_deg = swe.calc_ut(julian_day, 9, iflag)[0][0]
            data["pluto"] = get_kerykeion_point_from_degree(pluto_deg, "Pluto", point_type=point_type)
            data["pluto"].house = get_planet_house(pluto_deg, houses_degree_ut)
            data["pluto"].retrograde = swe.calc_ut(julian_day, 9, iflag)[0][3] < 0
            calculated_planets.append("Pluto")

        # ==================
        # LUNAR NODES
        # ==================

        # Calculate Mean Lunar Node
        if should_calculate("Mean_Node"):
            mean_node_deg = swe.calc_ut(julian_day, 10, iflag)[0][0]
            data["mean_node"] = get_kerykeion_point_from_degree(mean_node_deg, "Mean_Node", point_type=point_type)
            data["mean_node"].house = get_planet_house(mean_node_deg, houses_degree_ut)
            data["mean_node"].retrograde = swe.calc_ut(julian_day, 10, iflag)[0][3] < 0
            calculated_planets.append("Mean_Node")

        # Calculate True Lunar Node
        if should_calculate("True_Node"):
            true_node_deg = swe.calc_ut(julian_day, 11, iflag)[0][0]
            data["true_node"] = get_kerykeion_point_from_degree(true_node_deg, "True_Node", point_type=point_type)
            data["true_node"].house = get_planet_house(true_node_deg, houses_degree_ut)
            data["true_node"].retrograde = swe.calc_ut(julian_day, 11, iflag)[0][3] < 0
            calculated_planets.append("True_Node")

        # Calculate Mean South Node (opposite to Mean North Node)
        if should_calculate("Mean_South_Node") and "mean_node" in data:
            mean_south_node_deg = math.fmod(data["mean_node"].abs_pos + 180, 360)
            data["mean_south_node"] = get_kerykeion_point_from_degree(
                mean_south_node_deg, "Mean_South_Node", point_type=point_type
            )
            data["mean_south_node"].house = get_planet_house(mean_south_node_deg, houses_degree_ut)
            data["mean_south_node"].retrograde = data["mean_node"].retrograde
            calculated_planets.append("Mean_South_Node")

        # Calculate True South Node (opposite to True North Node)
        if should_calculate("True_South_Node") and "true_node" in data:
            true_south_node_deg = math.fmod(data["true_node"].abs_pos + 180, 360)
            data["true_south_node"] = get_kerykeion_point_from_degree(
                true_south_node_deg, "True_South_Node", point_type=point_type
            )
            data["true_south_node"].house = get_planet_house(true_south_node_deg, houses_degree_ut)
            data["true_south_node"].retrograde = data["true_node"].retrograde
            calculated_planets.append("True_South_Node")

        # ==================
        # LILITH POINTS
        # ==================

        # Calculate Mean Lilith (Mean Black Moon)
        if should_calculate("Mean_Lilith"):
            try:
                mean_lilith_deg = swe.calc_ut(julian_day, 12, iflag)[0][0]
                data["mean_lilith"] = get_kerykeion_point_from_degree(mean_lilith_deg, "Mean_Lilith", point_type=point_type)
                data["mean_lilith"].house = get_planet_house(mean_lilith_deg, houses_degree_ut)
                data["mean_lilith"].retrograde = swe.calc_ut(julian_day, 12, iflag)[0][3] < 0
                calculated_planets.append("Mean_Lilith")
            except Exception as e:
                logging.error(f"Error calculating Mean Lilith: {e}")
                active_points.remove("Mean_Lilith")


        # Calculate True Lilith (Osculating Black Moon)
        if should_calculate("True_Lilith"):
            try:
                true_lilith_deg = swe.calc_ut(julian_day, 13, iflag)[0][0]
                data["true_lilith"] = get_kerykeion_point_from_degree(true_lilith_deg, "True_Lilith", point_type=point_type)
                data["true_lilith"].house = get_planet_house(true_lilith_deg, houses_degree_ut)
                data["true_lilith"].retrograde = swe.calc_ut(julian_day, 13, iflag)[0][3] < 0
                calculated_planets.append("True_Lilith")
            except Exception as e:
                logging.error(f"Error calculating True Lilith: {e}")
                active_points.remove("True_Lilith")

        # ==================
        # SPECIAL POINTS
        # ==================

        # Calculate Earth - useful for heliocentric charts
        if should_calculate("Earth"):
            try:
                earth_deg = swe.calc_ut(julian_day, 14, iflag)[0][0]
                data["earth"] = get_kerykeion_point_from_degree(earth_deg, "Earth", point_type=point_type)
                data["earth"].house = get_planet_house(earth_deg, houses_degree_ut)
                data["earth"].retrograde = swe.calc_ut(julian_day, 14, iflag)[0][3] < 0
                calculated_planets.append("Earth")
            except Exception as e:
                logging.error(f"Error calculating Earth position: {e}")
                active_points.remove("Earth")

        # Calculate Chiron
        if should_calculate("Chiron"):
            try:
                chiron_deg = swe.calc_ut(julian_day, 15, iflag)[0][0]
                data["chiron"] = get_kerykeion_point_from_degree(chiron_deg, "Chiron", point_type=point_type)
                data["chiron"].house = get_planet_house(chiron_deg, houses_degree_ut)
                data["chiron"].retrograde = swe.calc_ut(julian_day, 15, iflag)[0][3] < 0
                calculated_planets.append("Chiron")
            except Exception as e:
                logging.error(f"Error calculating Chiron position: {e}")
                active_points.remove("Chiron")

        # Calculate Pholus
        if should_calculate("Pholus"):
            try:
                pholus_deg = swe.calc_ut(julian_day, 16, iflag)[0][0]
                data["pholus"] = get_kerykeion_point_from_degree(pholus_deg, "Pholus", point_type=point_type)
                data["pholus"].house = get_planet_house(pholus_deg, houses_degree_ut)
                data["pholus"].retrograde = swe.calc_ut(julian_day, 16, iflag)[0][3] < 0
                calculated_planets.append("Pholus")
            except Exception as e:
                logging.error(f"Error calculating Pholus position: {e}")
                active_points.remove("Pholus")

        # ==================
        # ASTEROIDS
        # ==================

        # Calculate Ceres
        if should_calculate("Ceres"):
            try:
                ceres_deg = swe.calc_ut(julian_day, 17, iflag)[0][0]
                data["ceres"] = get_kerykeion_point_from_degree(ceres_deg, "Ceres", point_type=point_type)
                data["ceres"].house = get_planet_house(ceres_deg, houses_degree_ut)
                data["ceres"].retrograde = swe.calc_ut(julian_day, 17, iflag)[0][3] < 0
                calculated_planets.append("Ceres")
            except Exception as e:
                logging.error(f"Error calculating Ceres position: {e}")
                active_points.remove("Ceres")

        # Calculate Pallas
        if should_calculate("Pallas"):
            try:
                pallas_deg = swe.calc_ut(julian_day, 18, iflag)[0][0]
                data["pallas"] = get_kerykeion_point_from_degree(pallas_deg, "Pallas", point_type=point_type)
                data["pallas"].house = get_planet_house(pallas_deg, houses_degree_ut)
                data["pallas"].retrograde = swe.calc_ut(julian_day, 18, iflag)[0][3] < 0
                calculated_planets.append("Pallas")
            except Exception as e:
                logging.error(f"Error calculating Pallas position: {e}")
                active_points.remove("Pallas")

        # Calculate Juno
        if should_calculate("Juno"):
            try:
                juno_deg = swe.calc_ut(julian_day, 19, iflag)[0][0]
                data["juno"] = get_kerykeion_point_from_degree(juno_deg, "Juno", point_type=point_type)
                data["juno"].house = get_planet_house(juno_deg, houses_degree_ut)
                data["juno"].retrograde = swe.calc_ut(julian_day, 19, iflag)[0][3] < 0
                calculated_planets.append("Juno")
            except Exception as e:
                logging.error(f"Error calculating Juno position: {e}")
                active_points.remove("Juno")

        # Calculate Vesta
        if should_calculate("Vesta"):
            try:
                vesta_deg = swe.calc_ut(julian_day, 20, iflag)[0][0]
                data["vesta"] = get_kerykeion_point_from_degree(vesta_deg, "Vesta", point_type=point_type)
                data["vesta"].house = get_planet_house(vesta_deg, houses_degree_ut)
                data["vesta"].retrograde = swe.calc_ut(julian_day, 20, iflag)[0][3] < 0
                calculated_planets.append("Vesta")
            except Exception as e:
                logging.error(f"Error calculating Vesta position: {e}")
                active_points.remove("Vesta")

        # ==================
        # TRANS-NEPTUNIAN OBJECTS
        # ==================

        # Calculate Eris
        if should_calculate("Eris"):
            try:
                eris_deg = swe.calc_ut(julian_day, swe.AST_OFFSET + 136199, iflag)[0][0]
                data["eris"] = get_kerykeion_point_from_degree(eris_deg, "Eris", point_type=point_type)
                data["eris"].house = get_planet_house(eris_deg, houses_degree_ut)
                data["eris"].retrograde = swe.calc_ut(julian_day, swe.AST_OFFSET + 136199, iflag)[0][3] < 0
                calculated_planets.append("Eris")
            except Exception as e:
                logging.warning(f"Could not calculate Eris position: {e}")
                active_points.remove("Eris")  # Remove if not calculated

        # Calculate Sedna
        if should_calculate("Sedna"):
            try:
                sedna_deg = swe.calc_ut(julian_day, swe.AST_OFFSET + 90377, iflag)[0][0]
                data["sedna"] = get_kerykeion_point_from_degree(sedna_deg, "Sedna", point_type=point_type)
                data["sedna"].house = get_planet_house(sedna_deg, houses_degree_ut)
                data["sedna"].retrograde = swe.calc_ut(julian_day, swe.AST_OFFSET + 90377, iflag)[0][3] < 0
                calculated_planets.append("Sedna")
            except Exception as e:
                logging.warning(f"Could not calculate Sedna position: {e}")
                active_points.remove("Sedna")

        # Calculate Haumea
        if should_calculate("Haumea"):
            try:
                haumea_deg = swe.calc_ut(julian_day, swe.AST_OFFSET + 136108, iflag)[0][0]
                data["haumea"] = get_kerykeion_point_from_degree(haumea_deg, "Haumea", point_type=point_type)
                data["haumea"].house = get_planet_house(haumea_deg, houses_degree_ut)
                data["haumea"].retrograde = swe.calc_ut(julian_day, swe.AST_OFFSET + 136108, iflag)[0][3] < 0
                calculated_planets.append("Haumea")
            except Exception as e:
                logging.warning(f"Could not calculate Haumea position: {e}")
                active_points.remove("Haumea")  # Remove if not calculated

        # Calculate Makemake
        if should_calculate("Makemake"):
            try:
                makemake_deg = swe.calc_ut(julian_day, swe.AST_OFFSET + 136472, iflag)[0][0]
                data["makemake"] = get_kerykeion_point_from_degree(makemake_deg, "Makemake", point_type=point_type)
                data["makemake"].house = get_planet_house(makemake_deg, houses_degree_ut)
                data["makemake"].retrograde = swe.calc_ut(julian_day, swe.AST_OFFSET + 136472, iflag)[0][3] < 0
                calculated_planets.append("Makemake")
            except Exception as e:
                logging.warning(f"Could not calculate Makemake position: {e}")
                active_points.remove("Makemake")  # Remove if not calculated

        # Calculate Ixion
        if should_calculate("Ixion"):
            try:
                ixion_deg = swe.calc_ut(julian_day, swe.AST_OFFSET + 28978, iflag)[0][0]
                data["ixion"] = get_kerykeion_point_from_degree(ixion_deg, "Ixion", point_type=point_type)
                data["ixion"].house = get_planet_house(ixion_deg, houses_degree_ut)
                data["ixion"].retrograde = swe.calc_ut(julian_day, swe.AST_OFFSET + 28978, iflag)[0][3] < 0
                calculated_planets.append("Ixion")
            except Exception as e:
                logging.warning(f"Could not calculate Ixion position: {e}")
                active_points.remove("Ixion")  # Remove if not calculated

        # Calculate Orcus
        if should_calculate("Orcus"):
            try:
                orcus_deg = swe.calc_ut(julian_day, swe.AST_OFFSET + 90482, iflag)[0][0]
                data["orcus"] = get_kerykeion_point_from_degree(orcus_deg, "Orcus", point_type=point_type)
                data["orcus"].house = get_planet_house(orcus_deg, houses_degree_ut)
                data["orcus"].retrograde = swe.calc_ut(julian_day, swe.AST_OFFSET + 90482, iflag)[0][3] < 0
                calculated_planets.append("Orcus")
            except Exception as e:
                logging.warning(f"Could not calculate Orcus position: {e}")
                active_points.remove("Orcus")  # Remove if not calculated

        # Calculate Quaoar
        if should_calculate("Quaoar"):
            try:
                quaoar_deg = swe.calc_ut(julian_day, swe.AST_OFFSET + 50000, iflag)[0][0]
                data["quaoar"] = get_kerykeion_point_from_degree(quaoar_deg, "Quaoar", point_type=point_type)
                data["quaoar"].house = get_planet_house(quaoar_deg, houses_degree_ut)
                data["quaoar"].retrograde = swe.calc_ut(julian_day, swe.AST_OFFSET + 50000, iflag)[0][3] < 0
                calculated_planets.append("Quaoar")
            except Exception as e:
                logging.warning(f"Could not calculate Quaoar position: {e}")
                active_points.remove("Quaoar")  # Remove if not calculated

        # ==================
        # FIXED STARS
        # ==================

        # Calculate Regulus (example fixed star)
        if should_calculate("Regulus"):
            try:
                star_name = b"Regulus"
                swe.fixstar_ut(star_name, julian_day, iflag)
                regulus_deg = swe.fixstar_ut(star_name, julian_day, iflag)[0][0]
                data["regulus"] = get_kerykeion_point_from_degree(regulus_deg, "Regulus", point_type=point_type)
                data["regulus"].house = get_planet_house(regulus_deg, houses_degree_ut)
                data["regulus"].retrograde = False  # Fixed stars are never retrograde
                calculated_planets.append("Regulus")
            except Exception as e:
                logging.warning(f"Could not calculate Regulus position: {e}")
                active_points.remove("Regulus")  # Remove if not calculated

        # Calculate Spica (example fixed star)
        if should_calculate("Spica"):
            try:
                star_name = b"Spica"
                swe.fixstar_ut(star_name, julian_day, iflag)
                spica_deg = swe.fixstar_ut(star_name, julian_day, iflag)[0][0]
                data["spica"] = get_kerykeion_point_from_degree(spica_deg, "Spica", point_type=point_type)
                data["spica"].house = get_planet_house(spica_deg, houses_degree_ut)
                data["spica"].retrograde = False  # Fixed stars are never retrograde
                calculated_planets.append("Spica")
            except Exception as e:
                logging.warning(f"Could not calculate Spica position: {e}")
                active_points.remove("Spica")  # Remove if not calculated

        # ==================
        # ARABIC PARTS / LOTS
        # ==================

        # Calculate Pars Fortunae (Part of Fortune)
        if should_calculate("Pars_Fortunae"):
            # Check if required points are available
            if all(k in data for k in ["ascendant", "sun", "moon"]):
                # Different calculation for day and night charts
                # Day birth (Sun above horizon): ASC + Moon - Sun
                # Night birth (Sun below horizon): ASC + Sun - Moon
                is_day_chart = get_house_number(data["sun"].house) < 7  # Houses 1-6 are above horizon

                if is_day_chart:
                    fortune_deg = math.fmod(data["ascendant"].abs_pos + data["moon"].abs_pos - data["sun"].abs_pos, 360)
                else:
                    fortune_deg = math.fmod(data["ascendant"].abs_pos + data["sun"].abs_pos - data["moon"].abs_pos, 360)

                data["pars_fortunae"] = get_kerykeion_point_from_degree(fortune_deg, "Pars_Fortunae", point_type=point_type)
                data["pars_fortunae"].house = get_planet_house(fortune_deg, houses_degree_ut)
                data["pars_fortunae"].retrograde = False  # Parts are never retrograde
                calculated_planets.append("Pars_Fortunae")

        # Calculate Pars Spiritus (Part of Spirit)
        if should_calculate("Pars_Spiritus"):
            # Check if required points are available
            if all(k in data for k in ["ascendant", "sun", "moon"]):
                # Day birth: ASC + Sun - Moon
                # Night birth: ASC + Moon - Sun
                is_day_chart = get_house_number(data["sun"].house) < 7

                if is_day_chart:
                    spirit_deg = math.fmod(data["ascendant"].abs_pos + data["sun"].abs_pos - data["moon"].abs_pos, 360)
                else:
                    spirit_deg = math.fmod(data["ascendant"].abs_pos + data["moon"].abs_pos - data["sun"].abs_pos, 360)

                data["pars_spiritus"] = get_kerykeion_point_from_degree(spirit_deg, "Pars_Spiritus", point_type=point_type)
                data["pars_spiritus"].house = get_planet_house(spirit_deg, houses_degree_ut)
                data["pars_spiritus"].retrograde = False
                calculated_planets.append("Pars_Spiritus")

        # Calculate Pars Amoris (Part of Eros/Love)
        if should_calculate("Pars_Amoris"):
            # Check if required points are available
            if all(k in data for k in ["ascendant", "venus"]):
                # ASC + Venus - Sun
                if "sun" in data:
                    amoris_deg = math.fmod(data["ascendant"].abs_pos + data["venus"].abs_pos - data["sun"].abs_pos, 360)

                    data["pars_amoris"] = get_kerykeion_point_from_degree(amoris_deg, "Pars_Amoris", point_type=point_type)
                    data["pars_amoris"].house = get_planet_house(amoris_deg, houses_degree_ut)
                    data["pars_amoris"].retrograde = False
                    calculated_planets.append("Pars_Amoris")

        # Calculate Pars Fidei (Part of Faith)
        if should_calculate("Pars_Fidei"):
            # Check if required points are available
            if all(k in data for k in ["ascendant", "jupiter", "saturn"]):
                # ASC + Jupiter - Saturn
                fidei_deg = math.fmod(data["ascendant"].abs_pos + data["jupiter"].abs_pos - data["saturn"].abs_pos, 360)

                data["pars_fidei"] = get_kerykeion_point_from_degree(fidei_deg, "Pars_Fidei", point_type=point_type)
                data["pars_fidei"].house = get_planet_house(fidei_deg, houses_degree_ut)
                data["pars_fidei"].retrograde = False
                calculated_planets.append("Pars_Fidei")

        # Calculate Vertex (a sort of auxiliary Descendant)
        if should_calculate("Vertex"):
            try:
                # Vertex is at ascmc[3] in Swiss Ephemeris
                if data["zodiac_type"] == "Sidereal":
                    _, ascmc = swe.houses_ex(
                        tjdut=data["julian_day"],
                        lat=data["lat"],
                        lon=data["lng"],
                        hsys=str.encode("V"),  # Vertex works best with Vehlow system
                        flags=swe.FLG_SIDEREAL
                    )
                else:
                    _, ascmc = swe.houses(
                        tjdut=data["julian_day"],
                        lat=data["lat"],
                        lon=data["lng"],
                        hsys=str.encode("V")
                    )

                vertex_deg = ascmc[3]
                data["vertex"] = get_kerykeion_point_from_degree(vertex_deg, "Vertex", point_type=point_type)
                data["vertex"].house = get_planet_house(vertex_deg, houses_degree_ut)
                data["vertex"].retrograde = False
                calculated_planets.append("Vertex")

                # Calculate Anti-Vertex (opposite to Vertex)
                anti_vertex_deg = math.fmod(vertex_deg + 180, 360)
                data["anti_vertex"] = get_kerykeion_point_from_degree(anti_vertex_deg, "Anti_Vertex", point_type=point_type)
                data["anti_vertex"].house = get_planet_house(anti_vertex_deg, houses_degree_ut)
                data["anti_vertex"].retrograde = False
                calculated_planets.append("Anti_Vertex")
            except Exception as e:
                logging.warning("Could not calculate Vertex position, error: %s", e)
                active_points.remove("Vertex")

        # Store only the planets that were actually calculated
        data["active_points"] = calculated_planets

    @classmethod
    def _calculate_day_of_week(cls, data: Dict[str, Any]) -> None:
        """Calculate the day of the week for the given Julian Day"""
        # Calculate the day of the week (0=Sunday, 1=Monday, ..., 6=Saturday)
        day_of_week = swe.day_of_week(data["julian_day"])
        # Map to human-readable names
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        data["day_of_week"] = days_of_week[day_of_week]

if __name__ == "__main__":
    # Example usage
    subject = AstrologicalSubjectFactory.from_current_time(name="Test Subject")
    print(subject.sun)
    print(subject.pars_amoris)
    print(subject.eris)
    print(subject.active_points)

    # Create JSON output
    json_string = subject.model_dump_json(exclude_none=True, indent=2)
