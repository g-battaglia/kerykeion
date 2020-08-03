"""
    This is part of Kerykeion (C) 2020 Giacomo Battaglia
"""

import swisseph as swe
from kerykeion.geoname import search
import pytz, datetime, math

swe.set_ephe_path("/")

class AstroData():
    """ 
    Colects all data from users and calculates the coordinates,
    it's utc and julian day.
    Args: name, year, month, day, hours, minuts, city, initial of the nation
    (ex: IT) 
    """

    def __init__(self, name, year, month, day, hours, minuts, city, nat=""):
        self.name = name
        self.year = year
        self.month = month
        self.day = day
        self.hours = hours
        self.minuts = minuts
        self.city = city
        self.nation = nat

    def get_tz(self):
        """Gets the nerest time zone for the calculation"""
        city_data = search(self.city, self.nation)[0]
        #z_conv = zt.n_tz(float(city_data["lat"]), float(city_data["lng"]),
        # zt.timezones())[2]
        self.city_long = float(city_data["lng"])
        self.city_lat = float(city_data["lat"])
        self.city_tz = city_data["timezonestr"]
        return self.city_tz    

    def get_utc(self):
        """Converts local time to utc time. """
        local_time = pytz.timezone(self.get_tz())
        naive_datetime = datetime.datetime(self.year, self.month,
         self.day, self.hours, self.minuts, 0)
        local_datetime = local_time.localize(naive_datetime, is_dst=None)
        utc_datetime = local_datetime.astimezone(pytz.utc)
        self.utc = utc_datetime
        return self.utc

    def get_jd(self):
        """ Calculates julian day from the utc time."""
        utc = self.get_utc()
        time_utc = utc.hour + utc.minute/60
        self.time = self.hours + self.minuts/60
        self.j_day = float(swe.julday(utc.year, utc.month, utc.day,
         time_utc))
        
        return self.j_day


class Calculator(AstroData):
    """
    Calculates all the astrological informations.
    Args: name, year, month, day, hours, minuts, city, initial of the nation
    (ex: IT)
    """

    def __init__(self, name, year, month, day, hours, minuts, city, nat=""):
        super().__init__(name, year, month, day, hours, minuts, city, nat)
        self.j_day = self.get_jd()
    
    def pos_calc(self, degree, number_name, label):
        """A function to be used in others tu create a dictionary deviding 
        the houses or the planets list."""
        if degree < 30:
            hou_dic = {label: number_name, "quality": "Cardinal", "element":
             "Fire", "sign" : "Ari", "pos": degree, "abs_pos" : degree,
              "emoji": "♈️"}
        elif degree < 60:
            result = degree - 30
            hou_dic = {label: number_name, "quality": "Fixed", "element":
             "Earth", "sign" : "Tau", "pos": result, "abs_pos" : degree,
              "emoji": "♉️"}
        elif degree < 90:
            result = degree - 60
            hou_dic = {label: number_name, "quality": "Mutable", "element":
             "Air", "sign" : "Gem", "pos": result, "abs_pos" : degree,
              "emoji": "♊️"}
        elif degree < 120:
            result = degree - 90
            hou_dic = {label: number_name, "quality": "Cardinal", "element":
             "Water", "sign" : "Can", "pos": result, "abs_pos" : degree,
              "emoji": "♋️"}
        elif degree < 150:
            result = degree - 120
            hou_dic = {label: number_name, "quality": "Fixed", "element":
             "Fire", "sign" : "Leo", "pos": result, "abs_pos" : degree,
              "emoji": "♌️"}
        elif degree < 180:
            result = degree - 150
            hou_dic = {label: number_name, "quality": "Mutable", "element":
             "Earth", "sign" : "Vir", "pos": result, "abs_pos" : degree,
              "emoji": "♍️"}
        elif degree < 210:
            result = degree - 180
            hou_dic = {label: number_name, "quality": "Cardinal", "element":
             "Air", "sign" : "Lib", "pos": result, "abs_pos" : degree,
              "emoji": "♎️"}
        elif degree < 240:
            result = degree - 210
            hou_dic = {label: number_name, "quality": "Fixed", "element":
             "Water", "sign" : "Sco", "pos": result, "abs_pos" : degree,
              "emoji": "♏️"}
        elif degree < 270:
            result = degree - 240
            hou_dic = {label: number_name, "quality": "Mutable", "element":
             "Fire", "sign" : "Sag", "pos": result, "abs_pos" : degree,
              "emoji": "♐️"}
        elif degree < 300:
            result = degree - 270
            hou_dic = {label: number_name, "quality": "Cardinal", "element":
             "Earth", "sign" : "Cap", "pos": result, "abs_pos" : degree,
              "emoji": "♑️"}
        elif degree < 330:
            result = degree - 300
            hou_dic = {label: number_name, "quality": "Fixed", "element":
             "Air", "sign" : "Aqu", "pos": result, "abs_pos" : degree,
              "emoji": "♒️"}
        elif degree < 360:
            result = degree - 330
            hou_dic = {label: number_name, "quality": "Mutable", "element":
             "Water", "sign" : "Pis", "pos": result, "abs_pos" : degree,
              "emoji": "♓️"}
        else:
            hou_dic = {label: "pos_calc error", "sign" : "pos_calc error",
             "pos": "pos_calc error"}
        
        return hou_dic
    
    def houses(self):
        """Calculatetype positions and store them in dictionaries""" 
        
        #creates the list of the house in 360°
        self.hou_degs = swe.houses(self.j_day, self.city_lat,
         self.city_long)[0]
        #stores the house in signulare dictionaries.
        self.fir_house = self.pos_calc(self.hou_degs[0], "1", "name")
        self.sec_house = self.pos_calc(self.hou_degs[1], "2", "name")
        self.thr_house = self.pos_calc(self.hou_degs[2], "3", "name")
        self.for_house = self.pos_calc(self.hou_degs[3], "4", "name")
        self.fif_house = self.pos_calc(self.hou_degs[4], "5", "name")
        self.six_house = self.pos_calc(self.hou_degs[5], "6", "name")
        self.sev_house = self.pos_calc(self.hou_degs[6], "7", "name")
        self.eig_house = self.pos_calc(self.hou_degs[7], "8", "name")
        self.nin_house = self.pos_calc(self.hou_degs[8], "9", "name")
        self.ten_house = self.pos_calc(self.hou_degs[9], "10", "name")
        self.ele_house = self.pos_calc(self.hou_degs[10], "11", "name")
        self.twe_house = self.pos_calc(self.hou_degs[11], "12", "name")
        #creates a list of all the dictionaries of thetype.
        self.house_list = [self.fir_house, self.sec_house, self.thr_house,
         self.for_house, self.fif_house, self.six_house, self.sev_house,
         self.eig_house, self.nin_house, self.ten_house, self.ele_house,
         self.twe_house]

        return self.house_list

    def planets_lister(self):
        """Calculates the position of the planets and stores it in a list."""
        self.sun_deg = swe.calc(self.j_day, 0)[0]
        self.moon_deg = swe.calc(self.j_day, 1)[0]
        self.mercury_deg = swe.calc(self.j_day, 2)[0]
        self.venus_deg = swe.calc(self.j_day, 3)[0]
        self.mars_deg = swe.calc(self.j_day, 4)[0]
        self.jupiter_deg = swe.calc(self.j_day, 5)[0]
        self.saturn_deg = swe.calc(self.j_day, 6)[0]
        self.uranus_deg = swe.calc(self.j_day, 7)[0]
        self.neptune_deg = swe.calc(self.j_day, 8)[0]
        self.pluto_deg = swe.calc(self.j_day, 9)[0]
        self.juno_deg = swe.calc(self.j_day, 0)[0]

        self.planets_degs = [self.sun_deg, self.moon_deg, self.mercury_deg,
         self.venus_deg, self.mars_deg, self.jupiter_deg, self.saturn_deg,
         self.uranus_deg, self.neptune_deg, self.pluto_deg, self.juno_deg]

        return self.planets_degs

    def planets(self):
        """ Defines body positon in signs and informations and
         stores them in dictionaries"""
        self.planets_degs = self.planets_lister()
        #stores the planets in signulare dictionaries.
        self.sun = self.pos_calc(self.planets_degs[0], "Sun", "name")
        self.moon = self.pos_calc(self.planets_degs[1], "Moon", "name")
        self.mercury = self.pos_calc(self.planets_degs[2], "Mercury", "name")
        self.venus = self.pos_calc(self.planets_degs[3], "Venus", "name")
        self.mars = self.pos_calc(self.planets_degs[4], "Mars", "name")
        self.jupiter = self.pos_calc(self.planets_degs[5], "Jupiter", "name")
        self.saturn = self.pos_calc(self.planets_degs[6], "Saturn", "name")
        self.uranus = self.pos_calc(self.planets_degs[7], "Uranus", "name")
        self.neptune = self.pos_calc(self.planets_degs[8], "Neptune", "name")
        self.pluto = self.pos_calc(self.planets_degs[9], "Pluto", "name")
        self.juno = self.pos_calc(self.planets_degs[10], "Juno", "name")

        self.planets_list = [self.sun, self.moon, self.mercury, self.venus,
         self.mars, self.jupiter, self.saturn, self.uranus, self.neptune,
          self.pluto, self.juno]

        return self.planets_list

    def planets_house(self):
        """Calculates the house of the planet and updates 
        the planets dictionary."""
        self.planets()
        self.houses()

        def for_every_planet(planet, deg_planet):
            """Functio to do the calculation.
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

            if point_between(self.hou_degs[0], self.hou_degs[1],
             deg_planet) == True:
                planet["house"] = "1st House"
            elif point_between(self.hou_degs[1], self.hou_degs[2],
             deg_planet) == True:
                planet["house"] = "2nd House"
            elif point_between(self.hou_degs[2], self.hou_degs[3],
             deg_planet) == True:
                planet["house"] = "3rd House"
            elif point_between(self.hou_degs[3], self.hou_degs[4],
             deg_planet) == True:
                planet["house"] = "4th House"
            elif point_between(self.hou_degs[4], self.hou_degs[5],
             deg_planet) == True:
                planet["house"] = "5th House"
            elif point_between(self.hou_degs[5], self.hou_degs[6],
             deg_planet) == True:
                planet["house"] = "6th House"
            elif point_between(self.hou_degs[6], self.hou_degs[7],
             deg_planet) == True:
                planet["house"] = "7th House"
            elif point_between(self.hou_degs[7], self.hou_degs[8],
             deg_planet) == True:
                planet["house"] = "8th House"
            elif point_between(self.hou_degs[8], self.hou_degs[9],
             deg_planet) == True:
                planet["house"] = "9th House"
            elif point_between(self.hou_degs[9], self.hou_degs[10],
             deg_planet) == True:
                planet["house"] = "10th House"
            elif point_between(self.hou_degs[10], self.hou_degs[11],
             deg_planet) == True:
                planet["house"] = "11th House"
            elif point_between(self.hou_degs[11], self.hou_degs[0],
             deg_planet) == True:
                planet["house"] = "12th House"
            else:
                planet["house"] = "error!"

            return planet
            

        self.sun = for_every_planet(self.sun, self.sun_deg)
        self.moon = for_every_planet(self.moon, self.moon_deg)
        self.mercury = for_every_planet(self.mercury, self.mercury_deg)
        self.venus = for_every_planet(self.venus, self.venus_deg)
        self.mars = for_every_planet(self.mars, self.mars_deg)
        self.jupiter = for_every_planet(self.jupiter, self.jupiter_deg)
        self.saturn = for_every_planet(self.saturn, self.saturn_deg)
        self.uranus = for_every_planet(self.uranus, self.uranus_deg)
        self.neptune = for_every_planet(self.neptune, self.neptune_deg)
        self.pluto = for_every_planet(self.pluto, self.pluto_deg)
        self.juno = for_every_planet(self.juno, self.juno_deg)

        self.planets_list = [self.sun, self.moon, self.mercury, self.venus,
         self.mars, self.jupiter, self.saturn, self.uranus, self.neptune,
          self.pluto, self.juno]

        return self.planets_list
    
    def asp_calc(self, point_one, point_two):
        """ 
        Calculates the aspects between the 2 points.
        Args: first point, second point. 
        """

        distance = abs(swe.difdeg2n(point_one, point_two))
        if int(distance) <= 10:
            aspect = "Conjuction"
            return True, aspect, distance
        elif 172 <= int(distance) <= 188:
            aspect = "Oposition"
            return True, aspect, distance - 180
        elif 85 <= int(distance) <= 95:
            aspect = "Square"
            return True, aspect, distance - 90
        elif 113 <= int(distance) <= 127:
            aspect = "Trigon"
            return True, aspect, distance - 120
        elif 57 <= int(distance) <= 63:
            aspect = "Sextil"
            return True, aspect, distance - 60
        elif 28 <= int(distance) <= 32:
            aspect = "Semisextil"
            return True, aspect, distance - 30
        elif 43 <= int(distance) <= 47:
            aspect = "Semisquare"
            return True, aspect, distance - 45
        elif 133 <= int(distance) <= 137:
            aspect = "Sesquiquadrate"
            return True, aspect, distance - 135
        elif 149 <= int(distance) <= 151:
            aspect = "Quincunx"
            return True, aspect, distance - 150
        elif 71.5 <= int(distance) <= 72.5:
            aspect = "Quintile"
            return True, aspect, distance - 72
        elif 143.5 <= int(distance) <= 144.5:
            aspect = "BiQuintile"
            return True, aspect, distance - 144
        else:
            return False, None, None
    
    def aspects(self):
        """
        Return all the aspects of the points in the natal chart in a dictionary,
        first all the individual aspects of each planet, second the aspects
        whitout repetitions.
        """
        self.planets_house()
        self.point_list = self.planets_list + self.house_list

        all_aspects = {}
        once_aspects = {}
        #both_aspects = {}

        for first in range(len(self.point_list)):
            all_aspects[self.point_list[first]["name"]] = []
            #Generates all aspects list
            for second in range(len(self.point_list)):
                verdict, aspect, orbit = self.asp_calc(self.point_list[first]["abs_pos"],
                self.point_list[second]["abs_pos"])
                
                if verdict == True and self.point_list[first] != self.point_list[second]:
                    all_aspects[self.point_list[first]["name"]].append(f"{aspect, self.point_list[second]['name'], orbit}")
                    pass


        for first in range(len(self.point_list)):
        #Generates the aspects list whitout repetitions
            once_aspects[self.point_list[first]["name"]] = []
            for second in range(first + 1, len(self.point_list)):
                
                verdict, aspect, orbit = self.asp_calc(self.point_list[first]["abs_pos"],
                self.point_list[second]["abs_pos"])
                
                if verdict == True:
                    once_aspects[self.point_list[first]["name"]].append(f"{aspect, self.point_list[second]['name'], orbit}")

        both_aspects = {"all": all_aspects, "once": once_aspects}
        return both_aspects
                    

if __name__ == "__main__":
    kanye = Calculator("Kanye", 1977, 6, 8, 8, 45, "Atlanta")
    print(kanye.aspects()["all"]["Sun"])