"""
    This is part of Kerykeion (C) 2022 Giacomo Battaglia
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import pytz
import swisseph as swe

from datetime import datetime
from logging import Logger, getLogger, basicConfig
from kerykeion.fetch_geonames import FetchGeonames
from kerykeion.types import KerykeionException, ZodiacType, KerykeionSubject, LunarPhaseObject
from kerykeion.utilities import get_number_from_name, calculate_position
from pathlib import Path
from typing import Union

# swe.set_ephe_path("/")

basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=20
)


class KrInstance():
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
    - city (str, optional): City or location of birth. Defaults to "London".
    - nat (str, optional): _ Defaults to "".
    - lng (Union[int, float], optional): _ Defaults to False.
    - lat (Union[int, float], optional): _ Defaults to False.
    - tz_str (Union[str, bool], optional): _ Defaults to False.
    - logger (Union[Logger, None], optional): _ Defaults to None.
    - geonames_username (str, optional): _ Defaults to 'century.boy'.
    - online (bool, optional): Sets if you want to use the online mode (using
        geonames) or not. Defaults to True.
    """
    # Deined by the user
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
    __logger: Logger

    # Generated internally
    julian_day: Union[int, float]
    utc: datetime

    now = datetime.now()

    def __init__(
        self,
        name="Now",
        year: int = now.year,
        month: int = now.month,
        day: int = now.day,
        hour: int = now.hour,
        minute: int = now.minute,
        city: str = "London",
        nation: str = "",
        lng: Union[int, float] = 0,
        lat: Union[int, float] = 0,
        tz_str: str = "",
        logger: Union[Logger, None] = None,
        geonames_username: str = 'century.boy',
        zodiac_type: ZodiacType = "Tropic",
        online: bool = True,
    ) -> None:

        self.__logger: Logger = logger or getLogger(
            self.__class__.__name__)
        self.__logger.debug('Starting Kerykeion')

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
        self.__geonames_username = geonames_username
        self.zodiac_type = zodiac_type
        self.online = online
        self.json_dir = Path.home()

        if (not self.online) and (not lng or not lat or not tz_str):
            raise KerykeionException(
                "You need to set the coordinates and timezone if you want to use the offline mode!")

        self.julian_day = self.__get_jd()

        # Get all the calculations
        self.__get_all()

    def __str__(self) -> str:
        return f"Astrological data for: {self.name}, {self.utc} UTC\nBirth location: {self.city}, Lat {self.lat}, Lon {self.lng}"

    def __repr__(self) -> str:
        return f"Astrological data for: {self.name}, {self.utc} UTC\nBirth location: {self.city}, Lat {self.lat}, Lon {self.lng}"

    def __get_tz(self) -> str:
        """Gets the nearest time zone for the calculation"""
        self.__logger.debug("Conneting to Geonames...")

        geonames = FetchGeonames(
            self.city, self.nation, logger=self.__logger, username=self.__geonames_username)
        self.city_data: dict[str, str] = geonames.get_serialized_data()

        if (
            not 'countryCode' in self.city_data or
            not 'timezonestr' in self.city_data or
            not 'lat' in self.city_data or
            not 'lng' in self.city_data
        ):

            raise KerykeionException(
                "No data found for this city, try again! Maybe check your connection?")

        self.nation = self.city_data["countryCode"]
        self.lng = float(self.city_data["lng"])
        self.lat = float(self.city_data["lat"])
        self.tz_str = self.city_data["timezonestr"]

        if self.lat > 66.0:
            self.lat = 66.0
            self.__logger.info(
                'Polar circle override for houses, using 66 degrees')

        elif self.lat < -66.0:
            self.lat = -66.0
            self.__logger.info(
                'Polar circle override for houses, using -66 degrees')

        return self.tz_str

    def __get_utc(self):
        """Converts local time to utc time. """
        if (self.online) and (not self.tz_str or not self.lng or not self.lat):
            tz = self.__get_tz()
            local_time = pytz.timezone(tz)
        else:
            local_time = pytz.timezone(self.tz_str)

        naive_datetime = datetime(
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            0
        )

        local_datetime = local_time.localize(naive_datetime, is_dst=None)
        utc_datetime = local_datetime.astimezone(pytz.utc)
        self.utc = utc_datetime
        return self.utc

    def __get_jd(self):
        """ Calculates julian day from the utc time."""
        utc = self.__get_utc()
        self.utc_time = utc.hour + utc.minute/60
        self.local_time = self.hour + self.minute/60
        self.julian_day = float(swe.julday(utc.year, utc.month, utc.day,
                                           self.utc_time))

        return self.julian_day

    def __houses(self) -> list:
        """Calculatetype positions and store them in dictionaries"""
        point_type = "House"
        # creates the list of the house in 360°
        self.houses_degree_ut = swe.houses(self.julian_day, self.lat,
                                           self.lng)[0]
        # stores the house in singular dictionaries.
        self.first_house = calculate_position(
            self.houses_degree_ut[0], "First House", point_type=point_type
        )
        self.second_house = calculate_position(
            self.houses_degree_ut[1], "Second House", point_type=point_type
        )
        self.third_house = calculate_position(
            self.houses_degree_ut[2], "Third House", point_type=point_type
        )
        self.fourth_house = calculate_position(
            self.houses_degree_ut[3], "Fourth House", point_type=point_type
        )
        self.fifth_house = calculate_position(
            self.houses_degree_ut[4], "Fifth House", point_type=point_type
        )
        self.sixth_house = calculate_position(
            self.houses_degree_ut[5], "Sixth House", point_type=point_type
        )
        self.seventh_house = calculate_position(
            self.houses_degree_ut[6], "Seventh House", point_type=point_type
        )
        self.eighth_house = calculate_position(
            self.houses_degree_ut[7], "Eighth House", point_type=point_type
        )
        self.ninth_house = calculate_position(
            self.houses_degree_ut[8], "Ninth House", point_type=point_type
        )
        self.tenth_house = calculate_position(
            self.houses_degree_ut[9], "Tenth House", point_type=point_type
        )
        self.eleventh_house = calculate_position(
            self.houses_degree_ut[10], "Eleventh House", point_type=point_type
        )
        self.twelfth_house = calculate_position(
            self.houses_degree_ut[11], "Twelfth House", point_type=point_type
        )

        # creates a list of all the dictionaries of thetype.

        houses_degree = [
            self.first_house["position"],
            self.second_house["position"],
            self.third_house["position"],
            self.fourth_house["position"],
            self.fifth_house["position"],
            self.sixth_house["position"],
            self.seventh_house["position"],
            self.eighth_house["position"],
            self.ninth_house["position"],
            self.tenth_house["position"],
            self.eleventh_house["position"],
            self.twelfth_house["position"]
        ]

        # return self.houses_list
        return houses_degree

    def __planets_degrees_lister(self):
        """Sidereal or tropic mode."""
        self.__iflag = swe.FLG_SWIEPH+swe.FLG_SPEED

        if self.zodiac_type == "Sidereal":
            self.__iflag += swe.FLG_SIDEREAL
            mode = "SIDM_FAGAN_BRADLEY"
            swe.set_sid_mode(getattr(swe, mode))

        """Calculates the position of the planets and stores it in a list."""

        sun_deg = swe.calc(self.julian_day, 0, self.__iflag)[0][0]
        moon_deg = swe.calc(self.julian_day, 1, self.__iflag)[0][0]
        mercury_deg = swe.calc(self.julian_day, 2, self.__iflag)[0][0]
        venus_deg = swe.calc(self.julian_day, 3, self.__iflag)[0][0]
        mars_deg = swe.calc(self.julian_day, 4, self.__iflag)[0][0]
        jupiter_deg = swe.calc(self.julian_day, 5, self.__iflag)[0][0]
        saturn_deg = swe.calc(self.julian_day, 6, self.__iflag)[0][0]
        uranus_deg = swe.calc(self.julian_day, 7, self.__iflag)[0][0]
        neptune_deg = swe.calc(self.julian_day, 8, self.__iflag)[0][0]
        pluto_deg = swe.calc(self.julian_day, 9, self.__iflag)[0][0]
        mean_node_deg = swe.calc(self.julian_day, 10, self.__iflag)[0][0]
        true_node_deg = swe.calc(self.julian_day, 11, self.__iflag)[0][0]

        # print(swe.calc(self.julian_day, 7, self.__iflag)[3])

        self.planets_degrees = [
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
            true_node_deg
        ]

        return self.planets_degrees

    def __planets(self) -> None:
        """ Defines body positon in signs and information and
         stores them in dictionaries """
        self.planets_degrees = self.__planets_degrees_lister()
        point_type = "Planet"
        # stores the planets in singular dictionaries.
        self.sun = calculate_position(
            self.planets_degrees[0], "Sun", point_type=point_type
        )
        self.moon = calculate_position(
            self.planets_degrees[1], "Moon", point_type=point_type
        )
        self.mercury = calculate_position(
            self.planets_degrees[2], "Mercury", point_type=point_type
        )
        self.venus = calculate_position(
            self.planets_degrees[3], "Venus", point_type=point_type
        )
        self.mars = calculate_position(
            self.planets_degrees[4], "Mars", point_type=point_type
        )
        self.jupiter = calculate_position(
            self.planets_degrees[5], "Jupiter", point_type=point_type
        )
        self.saturn = calculate_position(
            self.planets_degrees[6], "Saturn", point_type=point_type
        )
        self.uranus = calculate_position(
            self.planets_degrees[7], "Uranus", point_type=point_type
        )
        self.neptune = calculate_position(
            self.planets_degrees[8], "Neptune", point_type=point_type
        )
        self.pluto = calculate_position(
            self.planets_degrees[9], "Pluto", point_type=point_type
        )
        self.mean_node = calculate_position(
            self.planets_degrees[10], "Mean_Node", point_type=point_type
        )
        self.true_node = calculate_position(
            self.planets_degrees[11], "True_Node", point_type=point_type
        )

    def __planets_in_houses(self):
        """Calculates the house of the planet and updates
        the planets dictionary."""
        self.__planets()
        self.__houses()

        def for_every_planet(planet, planet_deg):
            """Function to do the calculation.
            Args: planet dictionary, planet degree"""

            def point_between(p1, p2, p3):
                """Finds if a point is between two other in a circle
                args: first point, second point, point in the middle"""
                p1_p2 = math.fmod(p2 - p1 + 360, 360)
                p1_p3 = math.fmod(p3 - p1 + 360, 360)
                if (p1_p2 <= 180) != (p1_p3 > p1_p2):
                    return True
                else:
                    return False

            if point_between(self.houses_degree_ut[0], self.houses_degree_ut[1],
                             planet_deg) == True:
                planet["house"] = "First House"
            elif point_between(self.houses_degree_ut[1], self.houses_degree_ut[2],
                               planet_deg) == True:
                planet["house"] = "Second House"
            elif point_between(self.houses_degree_ut[2], self.houses_degree_ut[3],
                               planet_deg) == True:
                planet["house"] = "Third House"
            elif point_between(self.houses_degree_ut[3], self.houses_degree_ut[4],
                               planet_deg) == True:
                planet["house"] = "Fourth House"
            elif point_between(self.houses_degree_ut[4], self.houses_degree_ut[5],
                               planet_deg) == True:
                planet["house"] = "Fifth House"
            elif point_between(self.houses_degree_ut[5], self.houses_degree_ut[6],
                               planet_deg) == True:
                planet["house"] = "Sixth House"
            elif point_between(self.houses_degree_ut[6], self.houses_degree_ut[7],
                               planet_deg) == True:
                planet["house"] = "Seventh House"
            elif point_between(self.houses_degree_ut[7], self.houses_degree_ut[8],
                               planet_deg) == True:
                planet["house"] = "Eighth House"
            elif point_between(self.houses_degree_ut[8], self.houses_degree_ut[9],
                               planet_deg) == True:
                planet["house"] = "Ninth House"
            elif point_between(self.houses_degree_ut[9], self.houses_degree_ut[10],
                               planet_deg) == True:
                planet["house"] = "Tenth House"
            elif point_between(self.houses_degree_ut[10], self.houses_degree_ut[11],
                               planet_deg) == True:
                planet["house"] = "Eleventh House"
            elif point_between(self.houses_degree_ut[11], self.houses_degree_ut[0],
                               planet_deg) == True:
                planet["house"] = "Twelfth House"
            else:
                planet["house"] = "error!"

            return planet

        self.sun = for_every_planet(
            self.sun, self.planets_degrees[0]
        )
        self.moon = for_every_planet(
            self.moon, self.planets_degrees[1]
        )
        self.mercury = for_every_planet(
            self.mercury, self.planets_degrees[2]
        )
        self.venus = for_every_planet(
            self.venus, self.planets_degrees[3]
        )
        self.mars = for_every_planet(
            self.mars, self.planets_degrees[4]
        )
        self.jupiter = for_every_planet(
            self.jupiter, self.planets_degrees[5]
        )
        self.saturn = for_every_planet(
            self.saturn, self.planets_degrees[6]
        )
        self.uranus = for_every_planet(
            self.uranus, self.planets_degrees[7]
        )
        self.neptune = for_every_planet(
            self.neptune, self.planets_degrees[8]
        )
        self.pluto = for_every_planet(
            self.pluto, self.planets_degrees[9]
        )
        self.mean_node = for_every_planet(
            self.mean_node, self.planets_degrees[10]
        )
        self.true_node = for_every_planet(
            self.true_node, self.planets_degrees[11]
        )

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
            self.true_node
        ]

        # Check in retrograde or not:
        planets_ret = []
        for p in planets_list:
            planet_number = get_number_from_name(p["name"])
            if swe.calc(self.julian_day, planet_number, self.__iflag)[0][3] < 0:
                p['retrograde'] = True
            else:
                p['retrograde'] = False
            planets_ret.append(p)

    def __lunar_phase_calc(self) -> None:
        """ Function to calculate the lunar phase"""

        # If ther's an error:
        moon_phase, sun_phase = None, None

        # anti-clockwise degrees between sun and moon
        moon, sun = self.planets_degrees[1], self.planets_degrees[0]
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
            0, 30, 40, 50, 60, 70, 80, 90, 120, 130, 140, 150, 160, 170, 180,
            210, 220, 230, 240, 250, 260, 270, 300, 310, 320, 330, 340, 350
        ]

        for x in range(len(sunstep)):

            low = sunstep[x]

            if x == 27:
                high = 360
            else:
                high = sunstep[x+1]
            if degrees_between >= low and degrees_between < high:
                sun_phase = x + 1

        def moon_emoji(phase):
            if phase == 1:
                result = "🌑"
            elif phase < 7:
                result = "🌒"
            elif 7 <= phase <= 9:
                result = "🌓"
            elif phase < 14:
                result = "🌔"
            elif phase == 14:
                result = "🌕"
            elif phase < 20:
                result = "🌖"
            elif 20 <= phase <= 22:
                result = "🌗"
            elif phase <= 28:
                result = "🌘"
            else:
                result = phase

            return result

        lunar_phase_dictionary = {
            "degrees_between_s_m": degrees_between,
            "moon_phase": moon_phase,
            "sun_phase": sun_phase,
            "moon_emoji": moon_emoji(moon_phase)
        }

        self.lunar_phase = LunarPhaseObject(**lunar_phase_dictionary)

    def __make_lists(self):
        """ Internal function to generate the lists"""
        self.planets_list = [self.sun, self.moon, self.mercury, self.venus,
                             self.mars, self.jupiter, self.saturn, self.uranus, self.neptune,
                             self.pluto, self.mean_node, self.true_node]

        self.houses_list = [self.first_house, self.second_house, self.third_house,
                            self.fourth_house, self.fifth_house, self.sixth_house, self.seventh_house,
                            self.eighth_house, self.ninth_house, self.tenth_house, self.eleventh_house,
                            self.twelfth_house]

    def __get_all(self):
        """ Gets all data from all the functions """

        self.__planets_in_houses()
        self.__lunar_phase_calc()
        self.__make_lists()

    def json(self, dump=False, destination_folder: Union[str, None] = None) -> str:
        """
        Dumps the Kerykeion object to a json string foramt,
        if dump=True also dumps to file located in destination
        or the home folder.
        """

        KrData = KerykeionSubject(**self.__dict__)
        json_string = KrData.json(exclude_none=True)
        print(json_string)

        if dump:
            if destination_folder:
                destination_path = Path(destination_folder)
                json_path = destination_path / f"{self.name}_kerykeion.json"

            else:
                json_path = self.json_dir / f"{self.name}_kerykeion.json"

            with open(json_path, "w", encoding="utf-8") as file:
                file.write(json_string)
                self.__logger.info(f"JSON file dumped in {json_path}.")

        return json_string

    def model(self) -> KerykeionSubject:
        """
        Creates a Pydantic model of the Kerykeion object.
        """

        return KerykeionSubject(**self.__dict__)


if __name__ == "__main__":

    kanye = KrInstance(
        "Kanye", 1977, 6, 8, 8, 45,
        lng=50, lat=50, tz_str="Europe/Rome"
    )

    test = KrInstance("Kanye", 1977, 6, 8, 8, 45, "Milano")
    # print(test.sun)
    # print(kanye.geonames_username)

    #print(kanye.model().sun)
    print(kanye.model().lunar_phase)
