"""
    This is part of Kerykeion (C) 2020 Giacomo Battaglia
"""

import datetime
from kerykeion.geoname import search
import logging
import math
import os.path
import pytz
from sys import exit
import swisseph as swe
from typing import Union

# swe.set_ephe_path("/")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger('Kerykeion')


class KrInstance():
    """
    Calculates all the astrological information, the coordinates,
    it's utc and julian day and returns an object with all that data.
    Args: name, year, month, day, hours, minuts, city,
    initial of the nation (Ex: "IT"),
    longitude, latitude and the timezone string are set to false so they will
    be calculated, if you want you can set them.
    Default values are set for now at greenwich time.

    """
    now = datetime.datetime.now()

    def __init__(
        self,
        name: str = "Now",
        year: int = now.year,
        month: int = now.month,
        day: int = now.day,
        hours: int = now.hour,
        minuts: int = now.minute,
        city: str = "London",
        nat: str = "",
        lon: Union[int, float] = False,
        lat: Union[int, float] = False,
        tz_str: Union[str, bool] = False
    ):
        logger.debug('Starting Kerykeion')
        self.name = name
        self.year = year
        self.month = month
        self.day = day
        self.hours = hours
        self.minuts = minuts
        self.city = city
        self.nation = nat
        self.city_long = lon
        self.city_lat = lat
        self.city_tz = tz_str

        self.json_dir = os.path.expanduser("~")

        self.julian_day = self.get_jd()
        self.zodiactype = "Tropic"

        # Get all the calculations
        self.get_all()

    def __str__(self):
        return f"Astrological data for: {self.name}, {self.utc} UTC\nBirth location: {self.city}, Lat {self.city_lat}, Lon {self.city_long}"

    def __repr__(self) -> str:
        return f"Astrological data for: {self.name}, {self.utc} UTC\nBirth location: {self.city}, Lat {self.city_lat}, Lon {self.city_long}"

    def get_tz(self):
        """Gets the nearest time zone for the calculation"""
        logger.debug("Conneting to Geonames...")
        try:
            self.city_data = search(self.city, self.nation)[0]
        except:
            logger.error('Error connecting to geonames, try again!')
            exit()

        logger.debug("Geonames done!")

        self.nation = self.city_data["countryCode"]
        self.city_long = float(self.city_data["lng"])
        self.city_lat = float(self.city_data["lat"])
        self.city_tz = self.city_data["timezonestr"]

        # self.country_code = self.city_data["countryCode"]

        if self.city_lat > 66.0:
            self.city_lat = 66.0
            logger.info('Polar circle override for houses, using 66 degrees')

        elif self.city_lat < -66.0:
            self.city_lat = -66.0
            logger.info('Polar circle override for houses, using -66 degrees')

        return self.city_tz

    def get_utc(self):
        """Converts local time to utc time. """

        if not self.city_long or not self.city_lat or not self.city_tz:
            local_time = pytz.timezone(self.get_tz())
        else:
            local_time = pytz.timezone(self.city_tz)

        naive_datetime = datetime.datetime(self.year, self.month,
                                           self.day, self.hours, self.minuts, 0)
        local_datetime = local_time.localize(naive_datetime, is_dst=None)
        utc_datetime = local_datetime.astimezone(pytz.utc)
        self.utc = utc_datetime
        return self.utc

    def get_jd(self):
        """ Calculates julian day from the utc time."""
        utc = self.get_utc()
        self.time_utc = utc.hour + utc.minute/60
        self.time = self.hours + self.minuts/60
        self.julian_day = float(swe.julday(utc.year, utc.month, utc.day,
                                           self.time_utc))

        return self.julian_day

    @staticmethod
    def get_number(name):
        """Internal function, gets number id from the name."""
        name = name.lower()

        if name == "sun":
            return 0
        elif name == "moon":
            return 1
        elif name == "mercury":
            return 2
        elif name == "venus":
            return 3
        elif name == "mars":
            return 4
        elif name == "jupiter":
            return 5
        elif name == "saturn":
            return 6
        elif name == "uranus":
            return 7
        elif name == "neptune":
            return 8
        elif name == "pluto":
            return 9
        elif name == "mean_node":
            return 10  # change!
        elif name == "true_node":
            return 11
        else:
            return int(name)

    @staticmethod
    def position_calc(degree, number_name, label):
        """A function to be used in others to create a dictionary deviding
        the houses or the planets list."""
        if degree < 30:
            dictionary = {label: number_name, "quality": "Cardinal", "element":
                          "Fire", "sign": "Ari", "sign_num": 0, "position": degree, "abs_pos": degree,
                          "emoji": "♈️"}
        elif degree < 60:
            result = degree - 30
            dictionary = {label: number_name, "quality": "Fixed", "element":
                          "Earth", "sign": "Tau", "sign_num": 1, "position": result, "abs_pos": degree,
                          "emoji": "♉️"}
        elif degree < 90:
            result = degree - 60
            dictionary = {label: number_name, "quality": "Mutable", "element":
                          "Air", "sign": "Gem", "sign_num": 2, "position": result, "abs_pos": degree,
                          "emoji": "♊️"}
        elif degree < 120:
            result = degree - 90
            dictionary = {label: number_name, "quality": "Cardinal", "element":
                          "Water", "sign": "Can", "sign_num": 3, "position": result, "abs_pos": degree,
                          "emoji": "♋️"}
        elif degree < 150:
            result = degree - 120
            dictionary = {label: number_name, "quality": "Fixed", "element":
                          "Fire", "sign": "Leo", "sign_num": 4, "position": result, "abs_pos": degree,
                          "emoji": "♌️"}
        elif degree < 180:
            result = degree - 150
            dictionary = {label: number_name, "quality": "Mutable", "element":
                          "Earth", "sign": "Vir", "sign_num": 5, "position": result, "abs_pos": degree,
                          "emoji": "♍️"}
        elif degree < 210:
            result = degree - 180
            dictionary = {label: number_name, "quality": "Cardinal", "element":
                          "Air", "sign": "Lib", "sign_num": 6, "position": result, "abs_pos": degree,
                          "emoji": "♎️"}
        elif degree < 240:
            result = degree - 210
            dictionary = {label: number_name, "quality": "Fixed", "element":
                          "Water", "sign": "Sco", "sign_num": 7, "position": result, "abs_pos": degree,
                          "emoji": "♏️"}
        elif degree < 270:
            result = degree - 240
            dictionary = {label: number_name, "quality": "Mutable", "element":
                          "Fire", "sign": "Sag", "sign_num": 8, "position": result, "abs_pos": degree,
                          "emoji": "♐️"}
        elif degree < 300:
            result = degree - 270
            dictionary = {label: number_name, "quality": "Cardinal", "element":
                          "Earth", "sign": "Cap", "sign_num": 9, "position": result, "abs_pos": degree,
                          "emoji": "♑️"}
        elif degree < 330:
            result = degree - 300
            dictionary = {label: number_name, "quality": "Fixed", "element":
                          "Air", "sign": "Aqu", "sign_num": 10, "position": result, "abs_pos": degree,
                          "emoji": "♒️"}
        elif degree < 360:
            result = degree - 330
            dictionary = {label: number_name, "quality": "Mutable", "element":
                          "Water", "sign": "Pis", "sign_num": 11, "position": result, "abs_pos": degree,
                          "emoji": "♓️"}
        else:
            dictionary = {label: "position_calc error", "sign": "position_calc error",
                          "position": "position_calc error"}

        return dictionary

    def houses(self):
        """Calculatetype positions and store them in dictionaries"""

        # creates the list of the house in 360°
        self.houses_degree_ut = swe.houses(self.julian_day, self.city_lat,
                                           self.city_long)[0]
        # stores the house in signulare dictionaries.
        self.first_house = self.position_calc(
            self.houses_degree_ut[0], "1", "name")
        self.second_house = self.position_calc(
            self.houses_degree_ut[1], "2", "name")
        self.third_house = self.position_calc(
            self.houses_degree_ut[2], "3", "name")
        self.fourth_house = self.position_calc(
            self.houses_degree_ut[3], "4", "name")
        self.fifth_house = self.position_calc(
            self.houses_degree_ut[4], "5", "name")
        self.sixth_house = self.position_calc(
            self.houses_degree_ut[5], "6", "name")
        self.seventh_house = self.position_calc(
            self.houses_degree_ut[6], "7", "name")
        self.eighth_house = self.position_calc(
            self.houses_degree_ut[7], "8", "name")
        self.ninth_house = self.position_calc(
            self.houses_degree_ut[8], "9", "name")
        self.tenth_house = self.position_calc(
            self.houses_degree_ut[9], "10", "name")
        self.eleventh_house = self.position_calc(
            self.houses_degree_ut[10], "11", "name")
        self.twelfth_house = self.position_calc(
            self.houses_degree_ut[11], "12", "name")

        # creates a list of all the dictionaries of thetype.

        houses_degree = [self.first_house["position"], self.second_house["position"],
                         self.third_house["position"], self.fourth_house["position"], self.fifth_house["position"],
                         self.sixth_house["position"], self.seventh_house, self.eighth_house["position"],
                         self.ninth_house["position"], self.tenth_house["position"], self.eleventh_house["position"],
                         self.twelfth_house["position"]]

        # return self.houses_list
        return houses_degree

    def planets_deegrees_lister(self):
        """Sidereal or tropic mode."""
        self.iflag = swe.FLG_SWIEPH+swe.FLG_SPEED

        if self.zodiactype == "sidereal":
            self.iflag += swe.FLG_SIDEREAL
            mode = "SIDM_FAGAN_BRADLEY"
            swe.set_sid_mode(getattr(swe, mode))

        """Calculates the position of the planets and stores it in a list."""

        sun_deg = swe.calc(self.julian_day, 0, self.iflag)[0][0]
        moon_deg = swe.calc(self.julian_day, 1, self.iflag)[0][0]
        mercury_deg = swe.calc(self.julian_day, 2, self.iflag)[0][0]
        venus_deg = swe.calc(self.julian_day, 3, self.iflag)[0][0]
        mars_deg = swe.calc(self.julian_day, 4, self.iflag)[0][0]
        jupiter_deg = swe.calc(self.julian_day, 5, self.iflag)[0][0]
        saturn_deg = swe.calc(self.julian_day, 6, self.iflag)[0][0]
        uranus_deg = swe.calc(self.julian_day, 7, self.iflag)[0][0]
        neptune_deg = swe.calc(self.julian_day, 8, self.iflag)[0][0]
        pluto_deg = swe.calc(self.julian_day, 9, self.iflag)[0][0]
        mean_node_deg = swe.calc(self.julian_day, 10, self.iflag)[0][0]
        true_node_deg = swe.calc(self.julian_day, 11, self.iflag)[0][0]

        # print(swe.calc(self.julian_day, 7, self.iflag)[3])

        self.planets_degrees = [sun_deg, moon_deg, mercury_deg,
                                venus_deg, mars_deg, jupiter_deg, saturn_deg,
                                uranus_deg, neptune_deg, pluto_deg, mean_node_deg,
                                true_node_deg]

        return self.planets_degrees

    def planets(self):
        """ Defines body positon in signs and informations and
         stores them in dictionaries"""
        self.planets_degrees = self.planets_deegrees_lister()
        # stores the planets in signulare dictionaries.
        self.sun = self.position_calc(self.planets_degrees[0], "Sun", "name")
        self.moon = self.position_calc(self.planets_degrees[1], "Moon", "name")
        self.mercury = self.position_calc(
            self.planets_degrees[2], "Mercury", "name")
        self.venus = self.position_calc(
            self.planets_degrees[3], "Venus", "name")
        self.mars = self.position_calc(self.planets_degrees[4], "Mars", "name")
        self.jupiter = self.position_calc(
            self.planets_degrees[5], "Jupiter", "name")
        self.saturn = self.position_calc(
            self.planets_degrees[6], "Saturn", "name")
        self.uranus = self.position_calc(
            self.planets_degrees[7], "Uranus", "name")
        self.neptune = self.position_calc(
            self.planets_degrees[8], "Neptune", "name")
        self.pluto = self.position_calc(
            self.planets_degrees[9], "Pluto", "name")
        self.mean_node = self.position_calc(
            self.planets_degrees[10], "Mean_Node", "name")
        self.true_node = self.position_calc(
            self.planets_degrees[11], "True_Node", "name")

    def planets_in_houses(self):
        """Calculates the house of the planet and updates
        the planets dictionary."""
        self.planets()
        self.houses()

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
                planet["house"] = "1st House"
            elif point_between(self.houses_degree_ut[1], self.houses_degree_ut[2],
                               planet_deg) == True:
                planet["house"] = "2nd House"
            elif point_between(self.houses_degree_ut[2], self.houses_degree_ut[3],
                               planet_deg) == True:
                planet["house"] = "3rd House"
            elif point_between(self.houses_degree_ut[3], self.houses_degree_ut[4],
                               planet_deg) == True:
                planet["house"] = "4th House"
            elif point_between(self.houses_degree_ut[4], self.houses_degree_ut[5],
                               planet_deg) == True:
                planet["house"] = "5th House"
            elif point_between(self.houses_degree_ut[5], self.houses_degree_ut[6],
                               planet_deg) == True:
                planet["house"] = "6th House"
            elif point_between(self.houses_degree_ut[6], self.houses_degree_ut[7],
                               planet_deg) == True:
                planet["house"] = "7th House"
            elif point_between(self.houses_degree_ut[7], self.houses_degree_ut[8],
                               planet_deg) == True:
                planet["house"] = "8th House"
            elif point_between(self.houses_degree_ut[8], self.houses_degree_ut[9],
                               planet_deg) == True:
                planet["house"] = "9th House"
            elif point_between(self.houses_degree_ut[9], self.houses_degree_ut[10],
                               planet_deg) == True:
                planet["house"] = "10th House"
            elif point_between(self.houses_degree_ut[10], self.houses_degree_ut[11],
                               planet_deg) == True:
                planet["house"] = "11th House"
            elif point_between(self.houses_degree_ut[11], self.houses_degree_ut[0],
                               planet_deg) == True:
                planet["house"] = "12th House"
            else:
                planet["house"] = "error!"

            return planet

        self.sun = for_every_planet(self.sun, self.planets_degrees[0])
        self.moon = for_every_planet(self.moon, self.planets_degrees[1])
        self.mercury = for_every_planet(
            self.mercury, self.planets_degrees[2])
        self.venus = for_every_planet(
            self.venus, self.planets_degrees[3])
        self.mars = for_every_planet(self.mars, self.planets_degrees[4])
        self.jupiter = for_every_planet(
            self.jupiter, self.planets_degrees[5])
        self.saturn = for_every_planet(
            self.saturn, self.planets_degrees[6])
        self.uranus = for_every_planet(
            self.uranus, self.planets_degrees[7])
        self.neptune = for_every_planet(
            self.neptune, self.planets_degrees[8])
        self.pluto = for_every_planet(
            self.pluto, self.planets_degrees[9])
        self.mean_node = for_every_planet(
            self.mean_node, self.planets_degrees[10])
        self.true_node = for_every_planet(
            self.true_node, self.planets_degrees[11])

        planets_list = [self.sun, self.moon, self.mercury, self.venus,
                        self.mars, self.jupiter, self.saturn, self.uranus, self.neptune,
                        self.pluto, self.mean_node, self.true_node]

        # Check in retrograde or not:

        planets_ret = []
        for p in planets_list:
            planet_number = self.get_number(p["name"])
            if swe.calc(self.julian_day, planet_number, self.iflag)[0][3] < 0:
                p.update({'retrograde': True})
            else:
                p.update({'retrograde': False})
            planets_ret.append(p)

    def lunar_phase_calc(self):
        """ Function to calculate the lunar phase"""

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
                mphase = x + 1

        sunstep = [0, 30, 40,  50, 60, 70, 80, 90, 120, 130, 140, 150, 160, 170, 180,
                   210, 220, 230, 240, 250, 260, 270, 300, 310, 320, 330, 340, 350]

        for x in range(len(sunstep)):

            low = sunstep[x]

            if x == 27:
                high = 360
            else:
                high = sunstep[x+1]
            if degrees_between >= low and degrees_between < high:
                sphase = x + 1

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

        self.lunar_phase = {
            "degrees_between_s_m": degrees_between,
            "moon_phase": mphase,
            "sun_phase": sphase,
            "moon_emoji": moon_emoji(mphase)
        }

    def make_lists(self):
        """ Internal function to generate the lists"""
        self.planets_list = [self.sun, self.moon, self.mercury, self.venus,
                             self.mars, self.jupiter, self.saturn, self.uranus, self.neptune,
                             self.pluto, self.mean_node, self.true_node]

        self.houses_list = [self.first_house, self.second_house, self.third_house,
                            self.fourth_house, self.fifth_house, self.sixth_house, self.seventh_house,
                            self.eighth_house, self.ninth_house, self.tenth_house, self.eleventh_house,
                            self.twelfth_house]

    def get_all(self):
        """ Gets all data from all the functions """

        self.planets_in_houses()
        # self.retrograde()
        self.lunar_phase_calc()
        self.make_lists()

    # Utility Functions:

    def dangerous_json_dump(self, dump=True, new_output_directory=None):
        import jsonpickle
        import json

        """
        Dumps the Kerykeion object to a json file located in the home folder.
        This json file allows the object to be recreated with jsonpickle.
        It's dangerous since it contains local system information.
        """

        try:
            self.sun
        except:
            self.get_all()

        if new_output_directory:
            self.json_path = os.path.join(
                new_output_directory, f"{self.name}_kerykeion.json")
        else:
            self.json_path = os.path.join(
                self.json_dir, f"{self.name}_kerykeion.json")

        json_string = jsonpickle.encode(self)

        hiden_values = [f' "json_dir": "{self.json_dir}",', f', "json_path": "{self.json_path}"'
                        ]

        for string in hiden_values:
            json_string = json_string.replace(string, "")

        if dump:
            json_string = json.loads(json_string.replace("'", '"'))
            with open(self.json_path, "w") as file:
                json.dump(json_string, file,  indent=4, sort_keys=True)
                logger.info(f"JSON file dumped in {self.json_path}.")
        else:
            pass
        return json_string

    def json_dump(self, dump=False, destination_folder=False):
        from json import dumps

        """
        Dumps the Kerykeion object to a json string foramt,
        if dump=True also dumps to file located in destination
        or the home folder.
        """

        if not self.sun:
            self.get_all()

        obj_dict = self.__dict__.copy()
        keys_to_remove = [
            "utc",
            "iflag",
            "json_dir",
            "planets_list",
            "houses_list",
            "planets_degrees",
            "houses_degree_ut"
        ]

        for key in keys_to_remove:
            obj_dict.pop(key)

        json_obj = dumps(obj_dict)

        if dump:
            if destination_folder:
                json_path = os.path.join(
                    destination_folder, f"{self.name}_kerykeion.json")
            else:
                json_path = os.path.join(
                    self.json_dir, f"{self.name}_kerykeion.json")

            with open(json_path, "w") as file:
                file.write(json_obj)
                logger.info(f"JSON file dumped in {json_path}.")

        return json_obj


if __name__ == "__main__":
    # kanye = KrInstance("Kanye", 1977, 6, 8, 8, 45, "Atlanta",
    #                   lon = 50, lat = 50, tz_str = "Europe/Rome")
    # kanye = KrInstance("Kanye", 1977, 6, 8, 8, 45, "Atlanta")
    # kanye.get_all()
    # print(kanye.sun)
    # print(kanye.city_tz)
    # print(kanye.fifth_house["position"])
    # print(KrInstance().city)
    # print(KrInstance())

    #############################

    # f = kanye.json_dump(dump=True)
    # api_json = kanye.json_api()
    # print(api_json)

    # print(kanye.city)
    # print(f)
    # print(kanye.lunar_phase)
    # kanye.json_dump()

    # for p in kanye.planets_list:
    #     print(p)
    ###############################
    now = KrInstance("Kanye", 1977, 6, 8, 8, 45, "Atlanta",
                     lon=50, lat=50, tz_str="Europe/Rome")

    kanye = KrInstance("Kanye", 1977, 6, 8, 8, 45, "Atlanta")
    print(kanye)
