# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""

import pytz
import swisseph as swe
import logging

from datetime import datetime
from kerykeion.fetch_geonames import FetchGeonames
from kerykeion.kr_types import (
    KerykeionException,
    ZodiacType,
    AstrologicalSubjectModel,
    LunarPhaseModel,
    KerykeionPointModel,
    PointType,
    SiderealMode
)
from kerykeion.utilities import (
    get_number_from_name, 
    calculate_position, 
    get_planet_house,
    get_moon_emoji_from_phase_int,
    get_moon_phase_name_from_phase_int,
)
from pathlib import Path
from typing import Union

DEFAULT_GEONAMES_USERNAME = "century.boy"
DEFAULT_SIDEREAL_MODE = "FAGAN_BRADLEY"


class AstrologicalSubject:
    """
    Calculates all the astrological information, the coordinates,
    it's utc and julian day and returns an object with all that data.

    Args:
    - name (str, optional): _ Defaults to "Now".
    - year (int, optional): _ Defaults to now.year.
    - month (int, optional): _ Defaults to now.month.
    - day (int, optional): _ Defaults to now.day.
    - hour (int, optional): _ Defaults to now.hour.
    - minute (int, optional): _ Defaults to now.minute.
    - city (str, optional): City or location of birth. Defaults to "London", which is GMT time.
        The city argument is used to get the coordinates and timezone from geonames just in case
        you don't insert them manually (see _get_tz).
        If you insert the coordinates and timezone manually, the city argument is not used for calculations
        but it's still used as a value for the city attribute.
    - nat (str, optional): _ Defaults to "".
    - lng (Union[int, float], optional): _ Defaults to False.
    - lat (Union[int, float], optional): _ Defaults to False.
    - tz_str (Union[str, bool], optional): _ Defaults to False.
    - geonames_username (str, optional): _ Defaults to 'century.boy'.
    - online (bool, optional): Sets if you want to use the online mode (using
        geonames) or not. Defaults to True.
    - utc_datetime (datetime, optional): An alternative way of constructing the object, 
        if you know the UTC datetime but do not have easy access to e.g. timezone identifier
        _ Defaults to None.
    - disable_chiron (bool, optional): Disables the calculation of Chiron. Defaults to False.
        Chiron calculation can create some issues with the Swiss Ephemeris when the date is too far in the past.
    - sidereal_mode (SiderealMode, optional): Also known as Ayanamsa. 
        The mode to use for the sidereal zodiac, according to the Swiss Ephemeris.
        Defaults to "FAGAN_BRADLEY".
        Available modes are visible in the SiderealMode Literal.
    """

    # Defined by the user
    name: str
    utc_datetime: Union[datetime, None]
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
    sidereal_mode: SiderealMode

    # Generated internally
    city_data: dict[str, str]
    julian_day: Union[int, float]
    utc_time: float
    local_time: float
    utc: datetime
    json_dir: Path

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
    houses_list: list[KerykeionPointModel]
    planets_list: list[KerykeionPointModel]
    planets_degrees_ut: list[float]
    houses_degree_ut: list[float]

    now = datetime.now()

    def __init__(
        self,
        name="Now",
        year: int = now.year,
        month: int = now.month,
        day: int = now.day,
        hour: int = now.hour,
        minute: int = now.minute,
        city: Union[str, None] = None,
        nation: Union[str, None] = None,
        lng: Union[int, float, None] = None,
        lat: Union[int, float, None] = None,
        tz_str: Union[str, None] = None,
        geonames_username: Union[str, None] = None,
        zodiac_type: ZodiacType = "Tropic",
        online: bool = True,
        utc_datetime: Union[datetime, None] = None,
        disable_chiron: bool = False,
        sidereal_mode: Union[SiderealMode, None] = None
    ) -> None:
        logging.debug("Starting Kerykeion")

        # We set the swisseph path to the current directory
        swe.set_ephe_path(str(Path(__file__).parent.absolute() / "sweph"))
        
        # Flags for the Swiss Ephemeris
        self._iflag = swe.FLG_SWIEPH + swe.FLG_SPEED

        self.name = name
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.city = city
        self.nation = nation
        self.lng = lng
        self.lat = lat
        self.tz_str = tz_str
        self.zodiac_type = zodiac_type
        self.online = online
        self.json_dir = Path.home()
        self.geonames_username = geonames_username
        self.utc_datetime = utc_datetime
        self.disable_chiron = disable_chiron
        self.sidereal_mode = sidereal_mode

        # Sidereal mode check and setup --->
        if self.sidereal_mode and self.zodiac_type == "Tropic":
            raise KerykeionException("You can't set a sidereal mode with a Tropic zodiac type!")
        
        if self.zodiac_type == "Sidereal" and not self.sidereal_mode:
            self.sidereal_mode = DEFAULT_SIDEREAL_MODE
            logging.info("No sidereal mode set, using default FAGAN_BRADLEY")

        if self.zodiac_type == "Sidereal":
            self._iflag += swe.FLG_SIDEREAL
            mode = "SIDM_" + sidereal_mode
            swe.set_sid_mode(getattr(swe, mode))
            logging.debug(f"Using sidereal mode: {mode}")
        # <--- Sidereal mode check and setup

        # This message is set to encourage the user to set a custom geonames username
        if geonames_username is None and online:
            logging.warning(
                "\n"
                "********" +
                "\n" +
                "NO GEONAMES USERNAME SET!" +
                "\n" +
                "Using the default geonames username is not recommended, please set a custom one!" +
                "\n" +
                "You can get one for free here:" +
                "\n" +
                "https://www.geonames.org/login" +
                "\n" +
                "Keep in mind that the default username is limited to 2000 requests per hour and is shared with everyone else using this library." +
                "\n" +
                "********"
            )

            self.geonames_username = DEFAULT_GEONAMES_USERNAME

        if not self.city:
            self.city = "London"
            logging.info("No city specified, using London as default")

        if not self.nation:
            self.nation = "GB"
            logging.info("No nation specified, using GB as default")

        if not self.lat:
            self.lat = 51.5074
            logging.info("No latitude specified, using London as default")

        if not self.lng:
            self.lng = 0
            logging.info("No longitude specified, using London as default")

        if (not self.online) and (not tz_str):
            raise KerykeionException("You need to set the coordinates and timezone if you want to use the offline mode!")

        self._check_if_poles()

        # Initialize everything
        self._get_utc()
        self._get_jd()
        self._planets_degrees_lister()
        self._planets()
        self._houses()

        self._planets_in_houses()
        self._lunar_phase_calc()

    def __str__(self) -> str:
        return f"Astrological data for: {self.name}, {self.utc} UTC\nBirth location: {self.city}, Lat {self.lat}, Lon {self.lng}"

    def __repr__(self) -> str:
        return f"Astrological data for: {self.name}, {self.utc} UTC\nBirth location: {self.city}, Lat {self.lat}, Lon {self.lng}"

    def __getitem__(self, item):
        return getattr(self, item)

    def get(self, item, default=None):
        return getattr(self, item, default)

    def _fetch_tz_from_geonames(self) -> None:
        """Gets the nearest time zone for the calculation"""
        logging.info("Fetching timezone/coordinates from geonames")

        geonames = FetchGeonames(
            self.city,
            self.nation,
            username=self.geonames_username,
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

        self._check_if_poles()

    def _get_utc(self) -> None:
        """Converts local time to utc time."""

        # If the coordinates are not set, get them from geonames.
        if (self.online) and (not self.tz_str):
            self._fetch_tz_from_geonames()

        # If UTC datetime is provided, then use it directly
        if (self.utc_datetime):
            self.utc = self.utc_datetime
            return

        local_time = pytz.timezone(self.tz_str)

        naive_datetime = datetime(self.year, self.month, self.day, self.hour, self.minute, 0)

        local_datetime = local_time.localize(naive_datetime, is_dst=None)
        self.utc = local_datetime.astimezone(pytz.utc)

    def _get_jd(self) -> None:
        """Calculates julian day from the utc time."""
        self.utc_time = self.utc.hour + self.utc.minute / 60
        self.local_time = self.hour + self.minute / 60
        self.julian_day = float(swe.julday(self.utc.year, self.utc.month, self.utc.day, self.utc_time))

    def _houses(self) -> None:
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

        if self.zodiac_type == "Sidereal":
            self.houses_degree_ut = swe.houses_ex(
                tjdut=self.julian_day, lat=self.lat, lon=self.lng, hsys=str.encode('P'), flags=swe.FLG_SIDEREAL
            )[0]
        elif self.zodiac_type == "Tropic":
            self.houses_degree_ut = swe.houses(
                tjdut=self.julian_day, lat=self.lat, lon=self.lng, hsys=str.encode('P')
            )[0]

        point_type: PointType = "House"

        # stores the house in singular dictionaries.
        self.first_house = calculate_position(self.houses_degree_ut[0], "First_House", point_type=point_type)
        self.second_house = calculate_position(self.houses_degree_ut[1], "Second_House", point_type=point_type)
        self.third_house = calculate_position(self.houses_degree_ut[2], "Third_House", point_type=point_type)
        self.fourth_house = calculate_position(self.houses_degree_ut[3], "Fourth_House", point_type=point_type)
        self.fifth_house = calculate_position(self.houses_degree_ut[4], "Fifth_House", point_type=point_type)
        self.sixth_house = calculate_position(self.houses_degree_ut[5], "Sixth_House", point_type=point_type)
        self.seventh_house = calculate_position(self.houses_degree_ut[6], "Seventh_House", point_type=point_type)
        self.eighth_house = calculate_position(self.houses_degree_ut[7], "Eighth_House", point_type=point_type)
        self.ninth_house = calculate_position(self.houses_degree_ut[8], "Ninth_House", point_type=point_type)
        self.tenth_house = calculate_position(self.houses_degree_ut[9], "Tenth_House", point_type=point_type)
        self.eleventh_house = calculate_position(self.houses_degree_ut[10], "Eleventh_House", point_type=point_type)
        self.twelfth_house = calculate_position(self.houses_degree_ut[11], "Twelfth_House", point_type=point_type)

        self.houses_list = [
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

    def _planets_degrees_lister(self):
        """Sidereal or tropic mode."""

        # Calculates the position of the planets and stores it in a list.
        sun_deg = swe.calc(self.julian_day, 0, self._iflag)[0][0]
        moon_deg = swe.calc(self.julian_day, 1, self._iflag)[0][0]
        mercury_deg = swe.calc(self.julian_day, 2, self._iflag)[0][0]
        venus_deg = swe.calc(self.julian_day, 3, self._iflag)[0][0]
        mars_deg = swe.calc(self.julian_day, 4, self._iflag)[0][0]
        jupiter_deg = swe.calc(self.julian_day, 5, self._iflag)[0][0]
        saturn_deg = swe.calc(self.julian_day, 6, self._iflag)[0][0]
        uranus_deg = swe.calc(self.julian_day, 7, self._iflag)[0][0]
        neptune_deg = swe.calc(self.julian_day, 8, self._iflag)[0][0]
        pluto_deg = swe.calc(self.julian_day, 9, self._iflag)[0][0]
        mean_node_deg = swe.calc(self.julian_day, 10, self._iflag)[0][0]
        true_node_deg = swe.calc(self.julian_day, 11, self._iflag)[0][0]
        
        if not self.disable_chiron:
            chiron_deg = swe.calc(self.julian_day, 15, self._iflag)[0][0]
        else:
            chiron_deg = 0

        self.planets_degrees_ut = [
            sun_deg,
            moon_deg,
            mercury_deg,
            venus_deg,
            mars_deg,
            jupiter_deg,
            saturn_deg,
            uranus_deg,
            neptune_deg,
            pluto_deg,
            mean_node_deg,
            true_node_deg,
        ]
        
        if not self.disable_chiron:
            self.planets_degrees_ut.append(chiron_deg)

    def _planets(self) -> None:
        """Defines body positon in signs and information and
        stores them in dictionaries"""

        point_type: PointType = "Planet"
        # stores the planets in singular dictionaries.
        self.sun = calculate_position(self.planets_degrees_ut[0], "Sun", point_type=point_type)
        self.moon = calculate_position(self.planets_degrees_ut[1], "Moon", point_type=point_type)
        self.mercury = calculate_position(self.planets_degrees_ut[2], "Mercury", point_type=point_type)
        self.venus = calculate_position(self.planets_degrees_ut[3], "Venus", point_type=point_type)
        self.mars = calculate_position(self.planets_degrees_ut[4], "Mars", point_type=point_type)
        self.jupiter = calculate_position(self.planets_degrees_ut[5], "Jupiter", point_type=point_type)
        self.saturn = calculate_position(self.planets_degrees_ut[6], "Saturn", point_type=point_type)
        self.uranus = calculate_position(self.planets_degrees_ut[7], "Uranus", point_type=point_type)
        self.neptune = calculate_position(self.planets_degrees_ut[8], "Neptune", point_type=point_type)
        self.pluto = calculate_position(self.planets_degrees_ut[9], "Pluto", point_type=point_type)
        self.mean_node = calculate_position(self.planets_degrees_ut[10], "Mean_Node", point_type=point_type)
        self.true_node = calculate_position(self.planets_degrees_ut[11], "True_Node", point_type=point_type)
        
        if not self.disable_chiron:
            self.chiron = calculate_position(self.planets_degrees_ut[12], "Chiron", point_type=point_type)
        else:
            self.chiron = None

    def _planets_in_houses(self) -> None:
        """Calculates the house of the planet and updates
        the planets dictionary."""

        self.sun.house = get_planet_house(self.planets_degrees_ut[0], self.houses_degree_ut)
        self.moon.house = get_planet_house(self.planets_degrees_ut[1], self.houses_degree_ut)
        self.mercury.house = get_planet_house(self.planets_degrees_ut[2], self.houses_degree_ut)
        self.venus.house = get_planet_house(self.planets_degrees_ut[3], self.houses_degree_ut)
        self.mars.house = get_planet_house(self.planets_degrees_ut[4], self.houses_degree_ut)
        self.jupiter.house = get_planet_house(self.planets_degrees_ut[5], self.houses_degree_ut)
        self.saturn.house = get_planet_house(self.planets_degrees_ut[6], self.houses_degree_ut)
        self.uranus.house = get_planet_house(self.planets_degrees_ut[7], self.houses_degree_ut)
        self.neptune.house = get_planet_house(self.planets_degrees_ut[8], self.houses_degree_ut)
        self.pluto.house = get_planet_house(self.planets_degrees_ut[9], self.houses_degree_ut)
        self.mean_node.house = get_planet_house(self.planets_degrees_ut[10], self.houses_degree_ut)
        self.true_node.house = get_planet_house(self.planets_degrees_ut[11], self.houses_degree_ut)

        if not self.disable_chiron:
            self.chiron.house = get_planet_house(self.planets_degrees_ut[12], self.houses_degree_ut)
        else:
            self.chiron = None

        self.planets_list = [
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
        ]
        
        if not self.disable_chiron:
            self.planets_list.append(self.chiron)

        # Check in retrograde or not:
        planets_ret = []
        for planet in self.planets_list:
            planet_number = get_number_from_name(planet["name"])
            if swe.calc(self.julian_day, planet_number, self._iflag)[0][3] < 0:
                planet["retrograde"] = True
            else:
                planet["retrograde"] = False
            planets_ret.append(planet)

    def _lunar_phase_calc(self) -> None:
        """Function to calculate the lunar phase"""

        # If ther's an error:
        moon_phase, sun_phase = None, None

        # anti-clockwise degrees between sun and moon
        moon, sun = self.planets_degrees_ut[1], self.planets_degrees_ut[0]
        degrees_between = moon - sun

        if degrees_between < 0:
            degrees_between += 360.0

        step = 360.0 / 28.0

        for x in range(28):
            low = x * step
            high = (x + 1) * step

            if degrees_between >= low and degrees_between < high:
                moon_phase = x + 1

        sunstep = [
            0,
            30,
            40,
            50,
            60,
            70,
            80,
            90,
            120,
            130,
            140,
            150,
            160,
            170,
            180,
            210,
            220,
            230,
            240,
            250,
            260,
            270,
            300,
            310,
            320,
            330,
            340,
            350,
        ]

        for x in range(len(sunstep)):
            low = sunstep[x]

            if x == 27:
                high = 360
            else:
                high = sunstep[x + 1]
            if degrees_between >= low and degrees_between < high:
                sun_phase = x + 1

        lunar_phase_dictionary = {
            "degrees_between_s_m": degrees_between,
            "moon_phase": moon_phase,
            "sun_phase": sun_phase,
            "moon_emoji": get_moon_emoji_from_phase_int(moon_phase),
            "moon_phase_name": get_moon_phase_name_from_phase_int(moon_phase)
        }

        self.lunar_phase = LunarPhaseModel(**lunar_phase_dictionary)

    def _check_if_poles(self):
        """
            Utility function to check if the location is in the polar circle.
            If it is, it sets the latitude to 66 or -66 degrees.
        """
        if self.lat > 66.0:
            self.lat = 66.0
            logging.info("Polar circle override for houses, using 66 degrees")

        elif self.lat < -66.0:
            self.lat = -66.0
            logging.info("Polar circle override for houses, using -66 degrees")

    def json(self, dump=False, destination_folder: Union[str, None] = None) -> str:
        """
        Dumps the Kerykeion object to a json string foramt,
        if dump=True also dumps to file located in destination
        or the home folder.
        """

        KrData = AstrologicalSubjectModel(**self.__dict__)
        json_string = KrData.model_dump_json(exclude_none=True)

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


if __name__ == "__main__":
    import json
    from kerykeion.utilities import setup_logging

    setup_logging(level="debug")
    
    # With Chiron enabled
    johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US")
    print(json.loads(johnny.json(dump=True)))

    print('\n')
    print(johnny.chiron)

    # With Chiron disabled
    johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", disable_chiron=True)
    print(json.loads(johnny.json(dump=True)))

    print('\n')
    print(johnny.chiron)

    # With Sidereal Zodiac
    johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")
