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

from functools import cached_property
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
    calculate_moon_phase
)
from pathlib import Path
from typing import Union, get_args

DEFAULT_GEONAMES_USERNAME = "century.boy"
DEFAULT_SIDEREAL_MODE: SiderealMode = "FAGAN_BRADLEY"
DEFAULT_HOUSES_SYSTEM_IDENTIFIER: HousesSystemIdentifier = "P"
DEFAULT_ZODIAC_TYPE: ZodiacType = "Tropic"
DEFAULT_PERSPECTIVE_TYPE: PerspectiveType = "Apparent Geocentric"
DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS = 30
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


class AstrologicalSubject:
    """
    Calculates all the astrological information, the coordinates,
    it's utc and julian day and returns an object with all that data.

    Args:
    - name (str, optional): The name of the subject. Defaults to "Now".
    - year (int, optional): The year of birth. Defaults to the current year.
    - month (int, optional): The month of birth. Defaults to the current month.
    - day (int, optional): The day of birth. Defaults to the current day.
    - hour (int, optional): The hour of birth. Defaults to the current hour.
    - minute (int, optional): Defaults to the current minute.
    - city (str, optional): City or location of birth. Defaults to "London", which is GMT time.
        The city argument is used to get the coordinates and timezone from geonames just in case
        you don't insert them manually (see _get_tz).
        If you insert the coordinates and timezone manually, the city argument is not used for calculations
        but it's still used as a value for the city attribute.
    - nat (str, optional): _ Defaults to "".
    - lng (Union[int, float], optional): Longitude of the birth location. Defaults to 0 (Greenwich, London).
    - lat (Union[int, float], optional): Latitude of the birth location. Defaults to 51.5074 (Greenwich, London).
    - tz_str (Union[str, bool], optional): Timezone of the birth location. Defaults to "GMT".
    - geonames_username (str, optional): The username for the geonames API. Note: Change this to your own username to avoid rate limits!
        You can get one for free here: https://www.geonames.org/login
    - online (bool, optional): Sets if you want to use the online mode, which fetches the timezone and coordinates from geonames.
        If you already have the coordinates and timezone, set this to False. Defaults to True.
    - disable_chiron: Deprecated, use disable_chiron_and_lilith instead.
    - sidereal_mode (SiderealMode, optional): Also known as Ayanamsa.
        The mode to use for the sidereal zodiac, according to the Swiss Ephemeris.
        Defaults to "FAGAN_BRADLEY".
        Available modes are visible in the SiderealMode Literal.
    - houses_system_identifier (HousesSystemIdentifier, optional): The system to use for the calculation of the houses.
        Defaults to "P" (Placidus).
        Available systems are visible in the HousesSystemIdentifier Literal.
    - perspective_type (PerspectiveType, optional): The perspective to use for the calculation of the chart.
        Defaults to "Apparent Geocentric".
        Available perspectives are visible in the PerspectiveType Literal.
    - cache_expire_after_days (int, optional): The number of days after which the geonames cache will expire. Defaults to 30.
    - is_dst (Union[None, bool], optional): Specify if the time is in DST. Defaults to None.
        By default (None), the library will try to guess if the time is in DST or not and raise an AmbiguousTimeError
        if it can't guess. If you know the time is in DST, set this to True, if you know it's not, set it to False.
    - disable_chiron_and_lilith (bool, optional): boolean representing if Chiron and Lilith should be disabled. Default is False.
        Chiron calculation can create some issues with the Swiss Ephemeris when the date is too far in the past.
    """

    # Defined by the user
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    nation: str
    lng: Union[int, float]
    lat: Union[int, float]
    tz_str: str
    geonames_username: str
    online: bool
    zodiac_type: ZodiacType
    sidereal_mode: Union[SiderealMode, None]
    houses_system_identifier: HousesSystemIdentifier
    houses_system_name: str
    perspective_type: PerspectiveType
    is_dst: Union[None, bool]

    # Generated internally
    city_data: dict[str, str]
    julian_day: Union[int, float]
    json_dir: Path
    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str

    # Planets
    sun: KerykeionPointModel
    moon: KerykeionPointModel
    mercury: KerykeionPointModel
    venus: KerykeionPointModel
    mars: KerykeionPointModel
    jupiter: KerykeionPointModel
    saturn: KerykeionPointModel
    uranus: KerykeionPointModel
    neptune: KerykeionPointModel
    pluto: KerykeionPointModel
    true_node: KerykeionPointModel
    mean_node: KerykeionPointModel
    chiron: Union[KerykeionPointModel, None]
    mean_lilith: Union[KerykeionPointModel, None]
    true_south_node: KerykeionPointModel
    mean_south_node: KerykeionPointModel

    # Axes
    asc: KerykeionPointModel
    dsc: KerykeionPointModel
    mc: KerykeionPointModel
    ic: KerykeionPointModel

    # Houses
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

    # Lists
    _houses_list: list[KerykeionPointModel]
    _houses_degree_ut: list[float]
    planets_names_list: list[Planet]
    houses_names_list: list[Houses]
    axial_cusps_names_list: list[AxialCusps]

    # Enable or disable features
    disable_chiron: Union[None, bool]
    disable_chiron_and_lilith: bool

    lunar_phase: LunarPhaseModel

    def __init__(
        self,
        name="Now",
        year: int = NOW.year,
        month: int = NOW.month,
        day: int = NOW.day,
        hour: int = NOW.hour,
        minute: int = NOW.minute,
        city: Union[str, None] = None,
        nation: Union[str, None] = None,
        lng: Union[int, float, None] = None,
        lat: Union[int, float, None] = None,
        tz_str: Union[str, None] = None,
        geonames_username: Union[str, None] = None,
        zodiac_type: Union[ZodiacType, None] = DEFAULT_ZODIAC_TYPE,
        online: bool = True,
        disable_chiron: Union[None, bool] = None, # Deprecated
        sidereal_mode: Union[SiderealMode, None] = None,
        houses_system_identifier: Union[HousesSystemIdentifier, None] = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: Union[PerspectiveType, None] = DEFAULT_PERSPECTIVE_TYPE,
        cache_expire_after_days: Union[int, None] = DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS,
        is_dst: Union[None, bool] = None,
        disable_chiron_and_lilith: bool = False
    ) -> None:
        logging.debug("Starting Kerykeion")

        # Deprecation warnings --->
        if disable_chiron is not None:
            warnings.warn(
                "The 'disable_chiron' argument is deprecated and will be removed in a future version. "
                "Please use 'disable_chiron' instead.",
                DeprecationWarning
            )

            if disable_chiron_and_lilith:
                raise ValueError("Cannot specify both 'disable_chiron' and 'disable_chiron_and_lilith'. Use 'disable_chiron_and_lilith' only.")

            self.disable_chiron_and_lilith = disable_chiron
        # <--- Deprecation warnings

        self.name = name
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.online = online
        self.json_dir = Path.home()
        self.disable_chiron = disable_chiron
        self.sidereal_mode = sidereal_mode
        self.cache_expire_after_days = cache_expire_after_days
        self.is_dst = is_dst
        self.disable_chiron_and_lilith = disable_chiron_and_lilith

        #---------------#
        # General setup #
        #---------------#

        # Geonames username
        if geonames_username is None and online and (not lat or not lng or not tz_str):
            logging.warning(GEONAMES_DEFAULT_USERNAME_WARNING)
            self.geonames_username = DEFAULT_GEONAMES_USERNAME
        else:
            self.geonames_username = geonames_username # type: ignore

        # City
        if not city:
            self.city = "London"
            logging.info("No city specified, using London as default")
        else:
            self.city = city

        # Nation
        if not nation:
            self.nation = "GB"
            logging.info("No nation specified, using GB as default")
        else:
            self.nation = nation

        # Latitude
        if not lat and not self.online:
            self.lat = 51.5074
            logging.info("No latitude specified, using London as default")
        else:
            self.lat = lat # type: ignore

        # Longitude
        if not lng and not self.online:
            self.lng = 0
            logging.info("No longitude specified, using London as default")
        else:
            self.lng = lng # type: ignore

        # Timezone
        if (not self.online) and (not tz_str):
            raise KerykeionException("You need to set the coordinates and timezone if you want to use the offline mode!")
        else:
            self.tz_str = tz_str # type: ignore

        # Zodiac type
        if not zodiac_type:
            self.zodiac_type = DEFAULT_ZODIAC_TYPE
        else:
            self.zodiac_type = zodiac_type

        # Perspective type
        if not perspective_type:
            self.perspective_type = DEFAULT_PERSPECTIVE_TYPE
        else:
            self.perspective_type = perspective_type

        # Houses system identifier
        if not houses_system_identifier:
            self.houses_system_identifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER
        else:
            self.houses_system_identifier = houses_system_identifier

        # Cache expire after days
        if not cache_expire_after_days:
            self.cache_expire_after_days = DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS
        else:
            self.cache_expire_after_days = cache_expire_after_days

        #-----------------------#
        # Swiss Ephemeris setup #
        #-----------------------#

        # We set the swisseph path to the current directory
        swe.set_ephe_path(str(Path(__file__).parent.absolute() / "sweph"))

        # Flags for the Swiss Ephemeris
        self._iflag = swe.FLG_SWIEPH + swe.FLG_SPEED

        # Chart Perspective check and setup --->
        if self.perspective_type not in get_args(PerspectiveType):
            raise KerykeionException(f"\n* ERROR: '{self.perspective_type}' is NOT a valid chart perspective! Available perspectives are: *" + "\n" + str(get_args(PerspectiveType)))

        if self.perspective_type == "True Geocentric":
            self._iflag += swe.FLG_TRUEPOS
        elif self.perspective_type == "Heliocentric":
            self._iflag += swe.FLG_HELCTR
        elif self.perspective_type == "Topocentric":
            self._iflag += swe.FLG_TOPOCTR
            # geopos_is_set, for topocentric
            if (self.online) and (not self.tz_str) and (not self.lat) and (not self.lng):
                self._fetch_and_set_tz_and_coordinates_from_geonames()
            swe.set_topo(self.lng, self.lat, 0)
        # <--- Chart Perspective check and setup

        # House System check and setup --->
        if self.houses_system_identifier not in get_args(HousesSystemIdentifier):
            raise KerykeionException(f"\n* ERROR: '{self.houses_system_identifier}' is NOT a valid house system! Available systems are: *" + "\n" + str(get_args(HousesSystemIdentifier)))

        self.houses_system_name = swe.house_name(self.houses_system_identifier.encode('ascii'))
        # <--- House System check and setup

        # Zodiac Type and Sidereal mode checks and setup --->
        if zodiac_type and not zodiac_type in get_args(ZodiacType):
            raise KerykeionException(f"\n* ERROR: '{zodiac_type}' is NOT a valid zodiac type! Available types are: *" + "\n" + str(get_args(ZodiacType)))

        if self.sidereal_mode and self.zodiac_type == "Tropic":
            raise KerykeionException("You can't set a sidereal mode with a Tropic zodiac type!")

        if self.zodiac_type == "Sidereal" and not self.sidereal_mode:
            self.sidereal_mode = DEFAULT_SIDEREAL_MODE
            logging.info("No sidereal mode set, using default FAGAN_BRADLEY")

        if self.zodiac_type == "Sidereal":
            # Check if the sidereal mode is valid

            if not self.sidereal_mode or not self.sidereal_mode in get_args(SiderealMode):
                raise KerykeionException(f"\n* ERROR: '{self.sidereal_mode}' is NOT a valid sidereal mode! Available modes are: *" + "\n" + str(get_args(SiderealMode)))

            self._iflag += swe.FLG_SIDEREAL
            mode = "SIDM_" + self.sidereal_mode
            swe.set_sid_mode(getattr(swe, mode))
            logging.debug(f"Using sidereal mode: {mode}")
        # <--- Zodiac Type and Sidereal mode checks and setup

        #------------------------#
        # Start the calculations #
        #------------------------#

        # UTC, julian day and local time setup --->
        if (self.online) and (not self.tz_str) and (not self.lat) and (not self.lng):
            self._fetch_and_set_tz_and_coordinates_from_geonames()

        self.lat = check_and_adjust_polar_latitude(self.lat)

        # Local time to UTC
        local_time = pytz.timezone(self.tz_str)
        naive_datetime = datetime(self.year, self.month, self.day, self.hour, self.minute, 0)

        try:
            local_datetime = local_time.localize(naive_datetime, is_dst=self.is_dst)
        except pytz.exceptions.AmbiguousTimeError:
            raise KerykeionException("Ambiguous time! Please specify if the time is in DST or not with the is_dst argument.")

        utc_object = local_datetime.astimezone(pytz.utc)
        self.iso_formatted_utc_datetime = utc_object.isoformat()

        # ISO formatted local datetime
        self.iso_formatted_local_datetime = local_datetime.isoformat()

        # Julian day calculation
        utc_float_hour_with_minutes = utc_object.hour + (utc_object.minute / 60)
        self.julian_day = float(swe.julday(utc_object.year, utc_object.month, utc_object.day, utc_float_hour_with_minutes))
        # <--- UTC, julian day and local time setup

        # Planets and Houses setup
        self._initialize_houses()
        self._initialize_planets()

        # Lunar Phase
        self.lunar_phase = calculate_moon_phase(
            self.moon.abs_pos,
            self.sun.abs_pos
        )

        # Deprecated properties
        self.utc_time
        self.local_time

    def __str__(self) -> str:
        return f"Astrological data for: {self.name}, {self.iso_formatted_utc_datetime} UTC\nBirth location: {self.city}, Lat {self.lat}, Lon {self.lng}"

    def __repr__(self) -> str:
        return f"Astrological data for: {self.name}, {self.iso_formatted_utc_datetime} UTC\nBirth location: {self.city}, Lat {self.lat}, Lon {self.lng}"

    def __getitem__(self, item):
        return getattr(self, item)

    def get(self, item, default=None):
        return getattr(self, item, default)

    def _fetch_and_set_tz_and_coordinates_from_geonames(self) -> None:
        """Gets the nearest time zone for the calculation"""
        logging.info("Fetching timezone/coordinates from geonames")

        geonames = FetchGeonames(
            self.city,
            self.nation,
            username=self.geonames_username,
            cache_expire_after_days=self.cache_expire_after_days
        )
        self.city_data: dict[str, str] = geonames.get_serialized_data()

        if (
            not "countryCode" in self.city_data
            or not "timezonestr" in self.city_data
            or not "lat" in self.city_data
            or not "lng" in self.city_data
        ):
            raise KerykeionException("No data found for this city, try again! Maybe check your connection?")

        self.nation = self.city_data["countryCode"]
        self.lng = float(self.city_data["lng"])
        self.lat = float(self.city_data["lat"])
        self.tz_str = self.city_data["timezonestr"]

    def _initialize_houses(self) -> None:
        """
        Calculate positions and store them in dictionaries

        https://www.astro.com/faq/fq_fh_owhouse_e.htm
        https://github.com/jwmatthys/pd-swisseph/blob/master/swehouse.c#L685
        hsys = letter code for house system;
            A  equal
            E  equal
            B  Alcabitius
            C  Campanus
            D  equal (MC)
            F  Carter "Poli-Equatorial"
            G  36 Gauquelin sectors
            H  horizon / azimut
            I  Sunshine solution Treindl
            i  Sunshine solution Makransky
            K  Koch
            L  Pullen SD "sinusoidal delta", ex Neo-Porphyry
            M  Morinus
            N  equal/1=Aries
            O  Porphyry
            P  Placidus
            Q  Pullen SR "sinusoidal ratio"
            R  Regiomontanus
            S  Sripati
            T  Polich/Page ("topocentric")
            U  Krusinski-Pisa-Goelzer
            V  equal Vehlow
            W  equal, whole sign
            X  axial rotation system/ Meridian houses
            Y  APC houses
        """

        _ascmc = (-1.0, -1.0)

        if self.zodiac_type == "Sidereal":
            cusps, ascmc = swe.houses_ex(
                tjdut=self.julian_day,
                lat=self.lat, lon=self.lng,
                hsys=str.encode(self.houses_system_identifier),
                flags=swe.FLG_SIDEREAL
            )
            self._houses_degree_ut = cusps
            _ascmc = ascmc

        elif self.zodiac_type == "Tropic":
            cusps, ascmc = swe.houses(
                tjdut=self.julian_day, lat=self.lat,
                lon=self.lng,
                hsys=str.encode(self.houses_system_identifier)
            )
            self._houses_degree_ut = cusps
            _ascmc = ascmc

        else:
            raise KerykeionException("Not a valid zodiac type: " + self.zodiac_type)

        point_type: PointType = "House"

        # stores the house in singular dictionaries.
        self.first_house = get_kerykeion_point_from_degree(self._houses_degree_ut[0], "First_House", point_type=point_type)
        self.second_house = get_kerykeion_point_from_degree(self._houses_degree_ut[1], "Second_House", point_type=point_type)
        self.third_house = get_kerykeion_point_from_degree(self._houses_degree_ut[2], "Third_House", point_type=point_type)
        self.fourth_house = get_kerykeion_point_from_degree(self._houses_degree_ut[3], "Fourth_House", point_type=point_type)
        self.fifth_house = get_kerykeion_point_from_degree(self._houses_degree_ut[4], "Fifth_House", point_type=point_type)
        self.sixth_house = get_kerykeion_point_from_degree(self._houses_degree_ut[5], "Sixth_House", point_type=point_type)
        self.seventh_house = get_kerykeion_point_from_degree(self._houses_degree_ut[6], "Seventh_House", point_type=point_type)
        self.eighth_house = get_kerykeion_point_from_degree(self._houses_degree_ut[7], "Eighth_House", point_type=point_type)
        self.ninth_house = get_kerykeion_point_from_degree(self._houses_degree_ut[8], "Ninth_House", point_type=point_type)
        self.tenth_house = get_kerykeion_point_from_degree(self._houses_degree_ut[9], "Tenth_House", point_type=point_type)
        self.eleventh_house = get_kerykeion_point_from_degree(self._houses_degree_ut[10], "Eleventh_House", point_type=point_type)
        self.twelfth_house = get_kerykeion_point_from_degree(self._houses_degree_ut[11], "Twelfth_House", point_type=point_type)

        self.houses_names_list = list(get_args(Houses))

        # Deprecated
        self._houses_list = [
            self.first_house,
            self.second_house,
            self.third_house,
            self.fourth_house,
            self.fifth_house,
            self.sixth_house,
            self.seventh_house,
            self.eighth_house,
            self.ninth_house,
            self.tenth_house,
            self.eleventh_house,
            self.twelfth_house,
        ]

        # AxialCusps
        point_type: PointType = "AxialCusps"

        # Calculate ascendant and medium coeli
        self.ascendant = get_kerykeion_point_from_degree(_ascmc[0], "Ascendant", point_type=point_type)
        self.medium_coeli = get_kerykeion_point_from_degree(_ascmc[1], "Medium_Coeli", point_type=point_type)
        # For descendant and imum coeli there exist no Swiss Ephemeris library calculation function,
        # but they are simply opposite the the ascendant and medium coeli
        dsc_deg = math.fmod(_ascmc[0] + 180, 360)
        ic_deg = math.fmod(_ascmc[1] + 180, 360)
        self.descendant = get_kerykeion_point_from_degree(dsc_deg, "Descendant", point_type=point_type)
        self.imum_coeli = get_kerykeion_point_from_degree(ic_deg, "Imum_Coeli", point_type=point_type)

    def _initialize_planets(self) -> None:
        """Defines body positon in signs and information and
        stores them in dictionaries"""

        point_type: PointType = "Planet"

        sun_deg = swe.calc_ut(self.julian_day, 0, self._iflag)[0][0]
        moon_deg = swe.calc_ut(self.julian_day, 1, self._iflag)[0][0]
        mercury_deg = swe.calc_ut(self.julian_day, 2, self._iflag)[0][0]
        venus_deg = swe.calc_ut(self.julian_day, 3, self._iflag)[0][0]
        mars_deg = swe.calc_ut(self.julian_day, 4, self._iflag)[0][0]
        jupiter_deg = swe.calc_ut(self.julian_day, 5, self._iflag)[0][0]
        saturn_deg = swe.calc_ut(self.julian_day, 6, self._iflag)[0][0]
        uranus_deg = swe.calc_ut(self.julian_day, 7, self._iflag)[0][0]
        neptune_deg = swe.calc_ut(self.julian_day, 8, self._iflag)[0][0]
        pluto_deg = swe.calc_ut(self.julian_day, 9, self._iflag)[0][0]
        mean_node_deg = swe.calc_ut(self.julian_day, 10, self._iflag)[0][0]
        true_node_deg = swe.calc_ut(self.julian_day, 11, self._iflag)[0][0]
        # For south nodes there exist no Swiss Ephemeris library calculation function,
        # but they are simply opposite the north node.
        mean_south_node_deg = math.fmod(mean_node_deg + 180, 360)
        true_south_node_deg = math.fmod(true_node_deg + 180, 360)

        # AC/DC axis and MC/IC axis were already calculated previously...

        self.sun = get_kerykeion_point_from_degree(sun_deg, "Sun", point_type=point_type)
        self.moon = get_kerykeion_point_from_degree(moon_deg, "Moon", point_type=point_type)
        self.mercury = get_kerykeion_point_from_degree(mercury_deg, "Mercury", point_type=point_type)
        self.venus = get_kerykeion_point_from_degree(venus_deg, "Venus", point_type=point_type)
        self.mars = get_kerykeion_point_from_degree(mars_deg, "Mars", point_type=point_type)
        self.jupiter = get_kerykeion_point_from_degree(jupiter_deg, "Jupiter", point_type=point_type)
        self.saturn = get_kerykeion_point_from_degree(saturn_deg, "Saturn", point_type=point_type)
        self.uranus = get_kerykeion_point_from_degree(uranus_deg, "Uranus", point_type=point_type)
        self.neptune = get_kerykeion_point_from_degree(neptune_deg, "Neptune", point_type=point_type)
        self.pluto = get_kerykeion_point_from_degree(pluto_deg, "Pluto", point_type=point_type)
        self.mean_node = get_kerykeion_point_from_degree(mean_node_deg, "Mean_Node", point_type=point_type)
        self.true_node = get_kerykeion_point_from_degree(true_node_deg, "True_Node", point_type=point_type)
        self.mean_south_node = get_kerykeion_point_from_degree(mean_south_node_deg, "Mean_South_Node", point_type=point_type)
        self.true_south_node = get_kerykeion_point_from_degree(true_south_node_deg, "True_South_Node", point_type=point_type)

        # Note that in whole-sign house systems ac/dc or mc/ic axes may not align with house cusps.
        # Therefore, for the axes we need to calculate house positions explicitly too.
        self.ascendant.house = get_planet_house(self.ascendant.abs_pos, self._houses_degree_ut)
        self.descendant.house = get_planet_house(self.descendant.abs_pos, self._houses_degree_ut)
        self.medium_coeli.house = get_planet_house(self.medium_coeli.abs_pos, self._houses_degree_ut)
        self.imum_coeli.house = get_planet_house(self.imum_coeli.abs_pos, self._houses_degree_ut)

        self.sun.house = get_planet_house(sun_deg, self._houses_degree_ut)
        self.moon.house = get_planet_house(moon_deg, self._houses_degree_ut)
        self.mercury.house = get_planet_house(mercury_deg, self._houses_degree_ut)
        self.venus.house = get_planet_house(venus_deg, self._houses_degree_ut)
        self.mars.house = get_planet_house(mars_deg, self._houses_degree_ut)
        self.jupiter.house = get_planet_house(jupiter_deg, self._houses_degree_ut)
        self.saturn.house = get_planet_house(saturn_deg, self._houses_degree_ut)
        self.uranus.house = get_planet_house(uranus_deg, self._houses_degree_ut)
        self.neptune.house = get_planet_house(neptune_deg, self._houses_degree_ut)
        self.pluto.house = get_planet_house(pluto_deg, self._houses_degree_ut)
        self.mean_node.house = get_planet_house(mean_node_deg, self._houses_degree_ut)
        self.true_node.house = get_planet_house(true_node_deg, self._houses_degree_ut)
        self.mean_south_node.house = get_planet_house(mean_south_node_deg, self._houses_degree_ut)
        self.true_south_node.house = get_planet_house(true_south_node_deg, self._houses_degree_ut)


        # Deprecated
        planets_list = [
            self.sun,
            self.moon,
            self.mercury,
            self.venus,
            self.mars,
            self.jupiter,
            self.saturn,
            self.uranus,
            self.neptune,
            self.pluto,
            self.mean_node,
            self.true_node,
            self.mean_south_node,
            self.true_south_node,
        ]

        if not self.disable_chiron_and_lilith:
            chiron_deg = swe.calc_ut(self.julian_day, 15, self._iflag)[0][0]
            mean_lilith_deg = swe.calc_ut(self.julian_day, 12, self._iflag)[0][0]

            self.chiron = get_kerykeion_point_from_degree(chiron_deg, "Chiron", point_type=point_type)
            self.mean_lilith = get_kerykeion_point_from_degree(mean_lilith_deg, "Mean_Lilith", point_type=point_type)

            self.chiron.house = get_planet_house(chiron_deg, self._houses_degree_ut)
            self.mean_lilith.house = get_planet_house(mean_lilith_deg, self._houses_degree_ut)

            # Deprecated
            planets_list.append(self.chiron)
            planets_list.append(self.mean_lilith)

        else:
            self.chiron = None
            self.mean_lilith = None

        # FIXME: Update after removing planets_list
        self.planets_names_list = [planet["name"] for planet in planets_list]
        self.axial_cusps_names_list = [
            axis["name"] for axis in [self.ascendant, self.descendant, self.medium_coeli, self.imum_coeli]
        ]

        # Check in retrograde or not:
        for planet in planets_list:
            planet_number = get_number_from_name(planet["name"])

            # Swiss ephemeris library does not offer calculation of direction of south nodes.
            # But south nodes have same direction as north nodes. We can use those to calculate direction.
            if planet_number == 1000:   # Number of Mean South Node
                planet_number = 10      # Number of Mean North Node
            elif planet_number == 1100: # Number of True South Node
                planet_number = 11      # Number of True North Node


            if swe.calc_ut(self.julian_day, planet_number, self._iflag)[0][3] < 0:
                planet["retrograde"] = True
            else:
                planet["retrograde"] = False

        # AC/DC and MC/IC axes are never retrograde. For consistency, set them to be not retrograde.
        self.ascendant.retrograde = False
        self.descendant.retrograde = False
        self.medium_coeli.retrograde = False
        self.imum_coeli.retrograde = False


    def json(self, dump=False, destination_folder: Union[str, None] = None, indent: Union[int, None] = None) -> str:
        """
        Dumps the Kerykeion object to a json string foramt,
        if dump=True also dumps to file located in destination
        or the home folder.
        """

        KrData = AstrologicalSubjectModel(**self.__dict__)
        json_string = KrData.model_dump_json(exclude_none=True, indent=indent)

        if dump:
            if destination_folder:
                destination_path = Path(destination_folder)
                json_path = destination_path / f"{self.name}_kerykeion.json"

            else:
                json_path = self.json_dir / f"{self.name}_kerykeion.json"

            with open(json_path, "w", encoding="utf-8") as file:
                file.write(json_string)
                logging.info(f"JSON file dumped in {json_path}.")

        return json_string

    def model(self) -> AstrologicalSubjectModel:
        """
        Creates a Pydantic model of the Kerykeion object.
        """

        return AstrologicalSubjectModel(**self.__dict__)

    @cached_property
    def utc_time(self) -> float:
        """
        Deprecated property, use iso_formatted_utc_datetime instead, will be removed in the future.
        Returns the UTC time as a float.
        """
        dt = datetime.fromisoformat(self.iso_formatted_utc_datetime)

        # Extract the hours, minutes, and seconds
        hours = dt.hour
        minutes = dt.minute
        seconds = dt.second + dt.microsecond / 1_000_000

        # Convert time to float hours
        float_time = hours + minutes / 60 + seconds / 3600

        return float_time

    @cached_property
    def local_time(self) -> float:
        """
        Deprecated property, use iso_formatted_local_datetime instead, will be removed in the future.
        Returns the local time as a float.
        """
        dt = datetime.fromisoformat(self.iso_formatted_local_datetime)

        # Extract the hours, minutes, and seconds
        hours = dt.hour
        minutes = dt.minute
        seconds = dt.second + dt.microsecond / 1_000_000

        # Convert time to float hours
        float_time = hours + minutes / 60 + seconds / 3600

        return float_time


    @staticmethod
    def get_from_iso_utc_time(
        name: str,
        iso_utc_time: str,
        city: str = "Greenwich",
        nation: str = "GB",
        tz_str: str = "Etc/GMT",
        online: bool = False,
        lng: Union[int, float] = 0,
        lat: Union[int, float] = 51.5074,
        geonames_username: str = DEFAULT_GEONAMES_USERNAME,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        disable_chiron_and_lilith: bool = False,
        sidereal_mode: Union[SiderealMode, None] = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE

    ) -> "AstrologicalSubject":
        """
        Creates an AstrologicalSubject object from an iso formatted UTC time.
        This method is offline by default, set online=True to fetch the timezone and coordinates from geonames.

        Args:
        - name (str): The name of the subject.
        - iso_utc_time (str): The iso formatted UTC time.
        - city (str, optional): City or location of birth. Defaults to "Greenwich".
        - nation (str, optional): Nation of birth. Defaults to "GB".
        - tz_str (str, optional): Timezone of the birth location. Defaults to "Etc/GMT".
        - online (bool, optional): Sets if you want to use the online mode, which fetches the timezone and coordinates from geonames.
            If you already have the coordinates and timezone, set this to False. Defaults to False.
        - lng (Union[int, float], optional): Longitude of the birth location. Defaults to 0 (Greenwich, London).
        - lat (Union[int, float], optional): Latitude of the birth location. Defaults to 51.5074 (Greenwich, London).
        - geonames_username (str, optional): The username for the geonames API. Note: Change this to your own username to avoid rate limits!
            You can get one for free here: https://www.geonames.org/login
        - zodiac_type (ZodiacType, optional): The zodiac type to use. Defaults to "Tropic".
        - disable_chiron_and_lilith: boolean representing if Chiron and Lilith should be disabled. Default is False.
            Chiron calculation can create some issues with the Swiss Ephemeris when the date is too far in the past.
        - sidereal_mode (SiderealMode, optional): Also known as Ayanamsa.
            The mode to use for the sidereal zodiac, according to the Swiss Ephemeris.
            Defaults to None.
            Available modes are visible in the SiderealMode Literal.
        - houses_system_identifier (HousesSystemIdentifier, optional): The system to use for the calculation of the houses.
            Defaults to "P" (Placidus).
            Available systems are visible in the HousesSystemIdentifier Literal.
        - perspective_type (PerspectiveType, optional): The perspective to use for the calculation of the chart.
            Defaults to "Apparent Geocentric".

        Returns:
        - AstrologicalSubject: The AstrologicalSubject object.
        """
        dt = datetime.fromisoformat(iso_utc_time)

        if online == True:
            if geonames_username == DEFAULT_GEONAMES_USERNAME:
                logging.warning(GEONAMES_DEFAULT_USERNAME_WARNING)

            geonames = FetchGeonames(
                city,
                nation,
                username=geonames_username,
            )

            city_data: dict[str, str] = geonames.get_serialized_data()
            lng = float(city_data["lng"])
            lat = float(city_data["lat"])

        subject = AstrologicalSubject(
            name=name,
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            city=city,
            nation=city,
            lng=lng,
            lat=lat,
            tz_str=tz_str,
            online=False,
            geonames_username=geonames_username,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
            disable_chiron_and_lilith=disable_chiron_and_lilith
        )

        return subject

if __name__ == "__main__":
    import json
    from kerykeion.utilities import setup_logging

    setup_logging(level="debug")

    # With Chiron enabled
    johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", zodiac_type=None)
    print(json.loads(johnny.json(dump=True)))
