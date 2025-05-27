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
    Planet,
    Houses,
    AxialCusps,
)
from kerykeion.utilities import (
    get_number_from_name,
    get_kerykeion_point_from_degree,
    get_planet_house,
    check_and_adjust_polar_latitude,
    calculate_moon_phase,
    datetime_to_julian
)

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
    city: str = "London"
    nation: str = "GB"
    lat: float = 51.5074
    lng: float = 0.0
    tz_str: str = "Europe/London"
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


class AstrologicalSubject:
    """
    A comprehensive astrological calculator that computes planetary positions,
    houses, and other astrological information for a specific time and location.

    This class handles the calculation of all astrological data and provides
    methods to access and manipulate this data in various formats.

    Attributes:
        name (str): Name of the astrological subject
        julian_day (float): Julian day number for the chart time
        iso_formatted_utc_datetime (str): ISO format UTC time
        iso_formatted_local_datetime (str): ISO format local time

        Configuration attributes:
        - zodiac_type: Type of zodiac system (Tropical or Sidereal)
        - houses_system_identifier: House system used for calculations
        - perspective_type: Perspective for calculations
        - sidereal_mode: Mode for sidereal calculations

        Location attributes:
        - city, nation: Location name and country
        - lat, lng: Coordinates
        - tz_str: Timezone identifier

        Planets and points:
        - sun, moon, mercury, etc.: Planet positions and info
        - ascendant, descendant, etc.: Chart angles
        - houses: All house cusps

        Calculated results:
        - lunar_phase: Moon phase information
    """

    def __init__(
        self,
        name: str = "Now",
        year: int = NOW.year,
        month: int = NOW.month,
        day: int = NOW.day,
        hour: int = NOW.hour,
        minute: int = NOW.minute,
        seconds: int = 0,
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
        active_points: Optional[Set[str]] = None
    ) -> None:
        """
        Initialize an AstrologicalSubject with birth/event details.

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
        """
        logging.debug("Starting Kerykeion calculation")

        # Basic identity
        self.name = name
        self.json_dir = Path.home()

        # Initialize configuration
        self.config = ChartConfiguration(
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
        )
        self.config.validate()

        # Set up geonames username if needed
        if geonames_username is None and online and (not lat or not lng or not tz_str):
            logging.warning(GEONAMES_DEFAULT_USERNAME_WARNING)
            geonames_username = DEFAULT_GEONAMES_USERNAME

        # Initialize location data
        self.location = LocationData(
            city=city or "London",
            nation=nation or "GB",
            lat=lat if lat is not None else 51.5074,
            lng=lng if lng is not None else 0.0,
            tz_str=tz_str or "Europe/London",
            altitude=altitude
        )

        # If offline mode is requested but required data is missing, raise error
        if not online and (not tz_str or not lat or not lng):
            raise KerykeionException(
                "For offline mode, you must provide timezone (tz_str) and coordinates (lat, lng)"
            )

        # Fetch location data if needed
        if online and (not tz_str or not lat or not lng):
            self.location.fetch_from_geonames(
                username=geonames_username or DEFAULT_GEONAMES_USERNAME,
                cache_expire_after_days=cache_expire_after_days
            )

        # Prepare location for calculations
        self.location.prepare_for_calculation()

        # Store calculation parameters
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.seconds = seconds
        self.is_dst = is_dst
        self.active_points = active_points

        # Calculate time conversions
        self._calculate_time_conversions()

        # Initialize Swiss Ephemeris
        self._setup_ephemeris()

        # Calculate houses and planets
        self._calculate_houses()
        self._calculate_planets()

        # Calculate lunar phase
        self.lunar_phase = calculate_moon_phase(
            self.moon.abs_pos,
            self.sun.abs_pos
        )

    def _calculate_time_conversions(self) -> None:
        """Calculate time conversions between local time, UTC and Julian day"""
        # Convert local time to UTC
        local_timezone = pytz.timezone(self.location.tz_str)
        naive_datetime = datetime(
            self.year, self.month, self.day,
            self.hour, self.minute, self.seconds
        )

        try:
            local_datetime = local_timezone.localize(naive_datetime, is_dst=self.is_dst)
        except pytz.exceptions.AmbiguousTimeError:
            raise KerykeionException(
                "Ambiguous time error! The time falls during a DST transition. "
                "Please specify is_dst=True or is_dst=False to clarify."
            )

        # Store formatted times
        utc_datetime = local_datetime.astimezone(pytz.utc)
        self.iso_formatted_utc_datetime = utc_datetime.isoformat()
        self.iso_formatted_local_datetime = local_datetime.isoformat()

        # Calculate Julian day
        self.julian_day = datetime_to_julian(utc_datetime)

    def _setup_ephemeris(self) -> None:
        """Set up Swiss Ephemeris with appropriate flags"""
        # Set ephemeris path
        swe.set_ephe_path(str(Path(__file__).parent.absolute() / "sweph"))

        # Base flags
        self._iflag = swe.FLG_SWIEPH + swe.FLG_SPEED

        # Add perspective flags
        if self.config.perspective_type == "True Geocentric":
            self._iflag += swe.FLG_TRUEPOS
        elif self.config.perspective_type == "Heliocentric":
            self._iflag += swe.FLG_HELCTR
        elif self.config.perspective_type == "Topocentric":
            self._iflag += swe.FLG_TOPOCTR
            # Set topocentric coordinates
            swe.set_topo(self.location.lng, self.location.lat, self.location.altitude or 0)

        # Add sidereal flag if needed
        if self.config.zodiac_type == "Sidereal":
            self._iflag += swe.FLG_SIDEREAL
            # Set sidereal mode
            mode = f"SIDM_{self.config.sidereal_mode}"
            swe.set_sid_mode(getattr(swe, mode))
            logging.debug(f"Using sidereal mode: {mode}")

        # Save house system name
        self.houses_system_name = swe.house_name(
            self.config.houses_system_identifier.encode('ascii')
        )

    def _calculate_houses(self) -> None:
        """Calculate house cusps and axis points"""
        # Calculate houses based on zodiac type
        if self.config.zodiac_type == "Sidereal":
            cusps, ascmc = swe.houses_ex(
                tjdut=self.julian_day,
                lat=self.location.lat,
                lon=self.location.lng,
                hsys=str.encode(self.config.houses_system_identifier),
                flags=swe.FLG_SIDEREAL
            )
        else:  # Tropical zodiac
            cusps, ascmc = swe.houses(
                tjdut=self.julian_day,
                lat=self.location.lat,
                lon=self.location.lng,
                hsys=str.encode(self.config.houses_system_identifier)
            )

        # Store house degrees
        self._houses_degree_ut = cusps

        # Create house objects
        point_type: PointType = "House"
        self.first_house = get_kerykeion_point_from_degree(cusps[0], "First_House", point_type=point_type)
        self.second_house = get_kerykeion_point_from_degree(cusps[1], "Second_House", point_type=point_type)
        self.third_house = get_kerykeion_point_from_degree(cusps[2], "Third_House", point_type=point_type)
        self.fourth_house = get_kerykeion_point_from_degree(cusps[3], "Fourth_House", point_type=point_type)
        self.fifth_house = get_kerykeion_point_from_degree(cusps[4], "Fifth_House", point_type=point_type)
        self.sixth_house = get_kerykeion_point_from_degree(cusps[5], "Sixth_House", point_type=point_type)
        self.seventh_house = get_kerykeion_point_from_degree(cusps[6], "Seventh_House", point_type=point_type)
        self.eighth_house = get_kerykeion_point_from_degree(cusps[7], "Eighth_House", point_type=point_type)
        self.ninth_house = get_kerykeion_point_from_degree(cusps[8], "Ninth_House", point_type=point_type)
        self.tenth_house = get_kerykeion_point_from_degree(cusps[9], "Tenth_House", point_type=point_type)
        self.eleventh_house = get_kerykeion_point_from_degree(cusps[10], "Eleventh_House", point_type=point_type)
        self.twelfth_house = get_kerykeion_point_from_degree(cusps[11], "Twelfth_House", point_type=point_type)

        # Store house names
        self.houses_names_list = list(get_args(Houses))

        # Calculate axis points
        point_type = "AxialCusps"
        self.ascendant = get_kerykeion_point_from_degree(ascmc[0], "Ascendant", point_type=point_type)
        self.medium_coeli = get_kerykeion_point_from_degree(ascmc[1], "Medium_Coeli", point_type=point_type)

        # Calculate descendant and imum coeli (opposite to ascendant and MC)
        dsc_deg = math.fmod(ascmc[0] + 180, 360)
        ic_deg = math.fmod(ascmc[1] + 180, 360)
        self.descendant = get_kerykeion_point_from_degree(dsc_deg, "Descendant", point_type=point_type)
        self.imum_coeli = get_kerykeion_point_from_degree(ic_deg, "Imum_Coeli", point_type=point_type)

        # Set houses for axis points
        self.ascendant.house = get_planet_house(self.ascendant.abs_pos, self._houses_degree_ut)
        self.descendant.house = get_planet_house(self.descendant.abs_pos, self._houses_degree_ut)
        self.medium_coeli.house = get_planet_house(self.medium_coeli.abs_pos, self._houses_degree_ut)
        self.imum_coeli.house = get_planet_house(self.imum_coeli.abs_pos, self._houses_degree_ut)

        # Axis points are never retrograde
        self.ascendant.retrograde = False
        self.descendant.retrograde = False
        self.medium_coeli.retrograde = False
        self.imum_coeli.retrograde = False

        # Store axis names
        self.axial_cusps_names_list = [
            "Ascendant", "Descendant", "Medium_Coeli", "Imum_Coeli"
        ]

        # Compatibility aliases
        self.asc = self.ascendant
        self.dsc = self.descendant
        self.mc = self.medium_coeli
        self.ic = self.imum_coeli

    def _calculate_planets(self) -> None:
        """Calculate planetary positions and related information"""
        # Skip calculation if point is not in active_points
        should_calculate = lambda point: not self.active_points or point in self.active_points

        point_type: PointType = "Planet"

        # Calculate all standard planets
        if should_calculate("sun"):
            sun_deg = swe.calc_ut(self.julian_day, 0, self._iflag)[0][0]
            self.sun = get_kerykeion_point_from_degree(sun_deg, "Sun", point_type=point_type)
            self.sun.house = get_planet_house(sun_deg, self._houses_degree_ut)
            self.sun.retrograde = swe.calc_ut(self.julian_day, 0, self._iflag)[0][3] < 0

        if should_calculate("moon"):
            moon_deg = swe.calc_ut(self.julian_day, 1, self._iflag)[0][0]
            self.moon = get_kerykeion_point_from_degree(moon_deg, "Moon", point_type=point_type)
            self.moon.house = get_planet_house(moon_deg, self._houses_degree_ut)
            self.moon.retrograde = swe.calc_ut(self.julian_day, 1, self._iflag)[0][3] < 0

        if should_calculate("mercury"):
            mercury_deg = swe.calc_ut(self.julian_day, 2, self._iflag)[0][0]
            self.mercury = get_kerykeion_point_from_degree(mercury_deg, "Mercury", point_type=point_type)
            self.mercury.house = get_planet_house(mercury_deg, self._houses_degree_ut)
            self.mercury.retrograde = swe.calc_ut(self.julian_day, 2, self._iflag)[0][3] < 0

        if should_calculate("venus"):
            venus_deg = swe.calc_ut(self.julian_day, 3, self._iflag)[0][0]
            self.venus = get_kerykeion_point_from_degree(venus_deg, "Venus", point_type=point_type)
            self.venus.house = get_planet_house(venus_deg, self._houses_degree_ut)
            self.venus.retrograde = swe.calc_ut(self.julian_day, 3, self._iflag)[0][3] < 0

        if should_calculate("mars"):
            mars_deg = swe.calc_ut(self.julian_day, 4, self._iflag)[0][0]
            self.mars = get_kerykeion_point_from_degree(mars_deg, "Mars", point_type=point_type)
            self.mars.house = get_planet_house(mars_deg, self._houses_degree_ut)
            self.mars.retrograde = swe.calc_ut(self.julian_day, 4, self._iflag)[0][3] < 0

        if should_calculate("jupiter"):
            jupiter_deg = swe.calc_ut(self.julian_day, 5, self._iflag)[0][0]
            self.jupiter = get_kerykeion_point_from_degree(jupiter_deg, "Jupiter", point_type=point_type)
            self.jupiter.house = get_planet_house(jupiter_deg, self._houses_degree_ut)
            self.jupiter.retrograde = swe.calc_ut(self.julian_day, 5, self._iflag)[0][3] < 0

        if should_calculate("saturn"):
            saturn_deg = swe.calc_ut(self.julian_day, 6, self._iflag)[0][0]
            self.saturn = get_kerykeion_point_from_degree(saturn_deg, "Saturn", point_type=point_type)
            self.saturn.house = get_planet_house(saturn_deg, self._houses_degree_ut)
            self.saturn.retrograde = swe.calc_ut(self.julian_day, 6, self._iflag)[0][3] < 0

        if should_calculate("uranus"):
            uranus_deg = swe.calc_ut(self.julian_day, 7, self._iflag)[0][0]
            self.uranus = get_kerykeion_point_from_degree(uranus_deg, "Uranus", point_type=point_type)
            self.uranus.house = get_planet_house(uranus_deg, self._houses_degree_ut)
            self.uranus.retrograde = swe.calc_ut(self.julian_day, 7, self._iflag)[0][3] < 0

        if should_calculate("neptune"):
            neptune_deg = swe.calc_ut(self.julian_day, 8, self._iflag)[0][0]
            self.neptune = get_kerykeion_point_from_degree(neptune_deg, "Neptune", point_type=point_type)
            self.neptune.house = get_planet_house(neptune_deg, self._houses_degree_ut)
            self.neptune.retrograde = swe.calc_ut(self.julian_day, 8, self._iflag)[0][3] < 0

        if should_calculate("pluto"):
            pluto_deg = swe.calc_ut(self.julian_day, 9, self._iflag)[0][0]
            self.pluto = get_kerykeion_point_from_degree(pluto_deg, "Pluto", point_type=point_type)
            self.pluto.house = get_planet_house(pluto_deg, self._houses_degree_ut)
            self.pluto.retrograde = swe.calc_ut(self.julian_day, 9, self._iflag)[0][3] < 0

        # Calculate nodes
        if should_calculate("mean_node"):
            mean_node_deg = swe.calc_ut(self.julian_day, 10, self._iflag)[0][0]
            self.mean_node = get_kerykeion_point_from_degree(mean_node_deg, "Mean_Node", point_type=point_type)
            self.mean_node.house = get_planet_house(mean_node_deg, self._houses_degree_ut)
            self.mean_node.retrograde = swe.calc_ut(self.julian_day, 10, self._iflag)[0][3] < 0

        if should_calculate("true_node"):
            true_node_deg = swe.calc_ut(self.julian_day, 11, self._iflag)[0][0]
            self.true_node = get_kerykeion_point_from_degree(true_node_deg, "True_Node", point_type=point_type)
            self.true_node.house = get_planet_house(true_node_deg, self._houses_degree_ut)
            self.true_node.retrograde = swe.calc_ut(self.julian_day, 11, self._iflag)[0][3] < 0

        # Calculate South Nodes (opposite to North Nodes)
        if should_calculate("mean_south_node"):
            mean_south_node_deg = math.fmod(self.mean_node.abs_pos + 180, 360)
            self.mean_south_node = get_kerykeion_point_from_degree(
                mean_south_node_deg, "Mean_South_Node", point_type=point_type
            )
            self.mean_south_node.house = get_planet_house(mean_south_node_deg, self._houses_degree_ut)
            self.mean_south_node.retrograde = self.mean_node.retrograde

        if should_calculate("true_south_node"):
            true_south_node_deg = math.fmod(self.true_node.abs_pos + 180, 360)
            self.true_south_node = get_kerykeion_point_from_degree(
                true_south_node_deg, "True_South_Node", point_type=point_type
            )
            self.true_south_node.house = get_planet_house(true_south_node_deg, self._houses_degree_ut)
            self.true_south_node.retrograde = self.true_node.retrograde

        if should_calculate("chiron"):
            chiron_deg = swe.calc_ut(self.julian_day, 15, self._iflag)[0][0]
            self.chiron = get_kerykeion_point_from_degree(chiron_deg, "Chiron", point_type=point_type)
            self.chiron.house = get_planet_house(chiron_deg, self._houses_degree_ut)
            self.chiron.retrograde = swe.calc_ut(self.julian_day, 15, self._iflag)[0][3] < 0

        if should_calculate("mean_lilith"):
            mean_lilith_deg = swe.calc_ut(self.julian_day, 12, self._iflag)[0][0]
            self.mean_lilith = get_kerykeion_point_from_degree(mean_lilith_deg, "Mean_Lilith", point_type=point_type)
            self.mean_lilith.house = get_planet_house(mean_lilith_deg, self._houses_degree_ut)
            self.mean_lilith.retrograde = swe.calc_ut(self.julian_day, 12, self._iflag)[0][3] < 0
        else:
            self.chiron = None
            self.mean_lilith = None

        # Build planets list
        self.planets_names_list = [
            "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
            "Uranus", "Neptune", "Pluto", "Mean_Node", "True_Node",
            "Mean_South_Node", "True_South_Node"
        ]

    def __str__(self) -> str:
        return (
            f"Astrological data for: {self.name}, {self.iso_formatted_utc_datetime} UTC\n"
            f"Birth location: {self.location.city}, Lat {self.location.lat}, Lon {self.location.lng}"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def json(self, dump: bool = False, destination_folder: Optional[str] = None, indent: Optional[int] = None) -> str:
        """
        Convert the astrological data to JSON format.

        Args:
            dump: Whether to save the JSON to a file
            destination_folder: Where to save the file (if dump=True)
            indent: Indentation level for the JSON

        Returns:
            JSON string representation of the data
        """
        model = self.model()
        json_string = model.model_dump_json(exclude_none=True, indent=indent)

        if dump:
            if destination_folder:
                destination_path = Path(destination_folder)
            else:
                destination_path = self.json_dir

            json_path = destination_path / f"{self.name}_kerykeion.json"

            with open(json_path, "w", encoding="utf-8") as file:
                file.write(json_string)
                logging.info(f"JSON file dumped in {json_path}.")

        return json_string

    def model(self) -> AstrologicalSubjectModel:
        """
        Create a Pydantic model of the astrological data.

        Returns:
            AstrologicalSubjectModel with all calculated data
        """
        # Convert dataclass to dict
        model_dict = {}

        # Add all relevant attributes
        for key, value in self.__dict__.items():
            # Skip internal attributes
            if key.startswith('_'):
                continue

            # Skip configuration classes
            if key in ('config', 'location'):
                continue

            model_dict[key] = value

        # Add location attributes
        for key, value in self.location.__dict__.items():
            if key != 'city_data':  # Skip internal storage
                model_dict[key] = value

        # Add configuration attributes
        for key, value in self.config.__dict__.items():
            model_dict[key] = value

        return AstrologicalSubjectModel(**model_dict)

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
        active_points: Optional[Set[str]] = None
    ) -> "AstrologicalSubject":
        """
        Create an AstrologicalSubject from an ISO formatted UTC time.

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
            AstrologicalSubject instance
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
        return cls(
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
        active_points: Optional[Set[str]] = None
    ) -> "AstrologicalSubject":
        """
        Create an AstrologicalSubject for the current time.

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
            AstrologicalSubject for current time
        """
        now = datetime.now()

        return cls(
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

if __name__ == "__main__":
    # Example usage
    subject = AstrologicalSubject.from_current_time(name="Test Subject")
    print(subject)
    print(subject.json(dump=True, destination_folder=".", indent=2))
