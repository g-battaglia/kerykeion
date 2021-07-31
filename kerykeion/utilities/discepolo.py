"""
    This is part of Kerykeion (C) 2020 Giacomo Battaglia
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kerykeion.main import KrInstance
import swisseph as swe

# General Costants
ORBIT_ROUND = 1

CONJUCTION_VALUE = 10
OPPOSITION_VALUE = 8
SQUARE_VALUE = 5
TRIGON_VALUE = 7


class DiscepoloNumber():
    """
    Calculates the synastry using Ciro Discepolo's algorithm.
    Args: first user object, second user object
    """

    def __init__(self, user_a: KrInstance, user_b: KrInstance):
        self.user_a = user_a
        self.user_b = user_b
        user_a.get_all()
        user_b.get_all()
        self.first_points_list = user_a.planets_list[:7] + [user_a.houses_list[0],
                                                            user_a.houses_list[9]]
        self.second_points_list = user_b.planets_list[:7] + [user_b.houses_list[0],
                                                             user_b.houses_list[9]]

    def synastry_aspect(self, user_a, pl_us1, user_b, pl_us2):
        """ 
        Calculates the aspects between the 2 users.
        Args: first user object, first list of planets and houses,
        second user objcet, second list of planets and houses. 
        """

        distance = abs(swe.difdeg2n(self.first_points_list[pl_us1]["abs_pos"],
                                    self.second_points_list[pl_us2]["abs_pos"]))
        if (int(distance) <= 15) and ((self.first_points_list[pl_us1]["name"] == "Sun" and self.first_points_list[pl_us2]["name"] == "Sun")
                                      or (self.first_points_list[pl_us1]["name"] == "Moon" and self.first_points_list[pl_us2]["name"] == "Moon")
                                      or (self.first_points_list[pl_us1]["name"] == "Moon" and self.first_points_list[pl_us2]["name"] == "Sun")
                                      or (self.first_points_list[pl_us1]["name"] == "Sun" and self.first_points_list[pl_us2]["name"] == "Moon")):
            aspect = "Conjuction"
            return True, aspect, distance
        if int(distance) <= CONJUCTION_VALUE:
            aspect = "Conjuction"
            return True, aspect, distance
        elif (180 - OPPOSITION_VALUE) <= int(distance) <= (180 + OPPOSITION_VALUE):
            aspect = "Oposition"
            return True, aspect, distance - 180
        elif (90 - SQUARE_VALUE) <= int(distance) <= (90 + SQUARE_VALUE):
            aspect = "Square"
            return True, aspect, distance - 90
        elif (120 - TRIGON_VALUE) <= int(distance) <= (120 + TRIGON_VALUE):
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
        elif (self.first_points_list[pl_us1]["name"] == "Sun" and
              self.second_points_list[pl_us2]["name"] == "Sun" and
              self.first_points_list[pl_us1]["quality"] ==
              self.second_points_list[pl_us2]["quality"]):
            aspect = "DESTINO"
            return False, aspect, distance
        else:
            return False, None, None

    def get_synastry(self):
        """
        Asingns points to the aspects and prints them.
        """
        lenght = len(self.first_points_list)
        counter = 0
        points = 0
        aspects = []
        value = 0
        for i in range(lenght):
            for b in range(lenght):
                verdict, aspect, orbit = self.synastry_aspect(self.user_a, i,
                                                              self.user_b, b)
                if verdict == True:
                    if aspect == "Conjuction" and ((self.first_points_list[i]
                                                    ["name"]
                                                    == "Sun" and self.second_points_list[b]["name"]
                                                    == "Moon") or (self.first_points_list[i]["name"]
                                                                   == "Moon" and self.second_points_list[b]["name"]
                                                                   == "Sun")):
                        value = 8
                        if abs(int(orbit)) <= 2:
                            value += 3
                            points += value
                        else:
                            points += value

                    elif (self.first_points_list[b]["name"]
                          == "Sun" and self.second_points_list[i]["name"]
                          == "Sun") or (self.first_points_list[b]["name"]
                                        == "Sun" and self.second_points_list[i]["name"]
                                        == "Moon") or (self.first_points_list[b]["name"]
                                                       == "Moon" and self.second_points_list[i]["name"]
                                                       == "Sun") or (self.first_points_list[b]["name"]
                                                                     == "Moon" and self.second_points_list[i]["name"]
                                                                     == "Moon") or (self.first_points_list[b]["name"]
                                                                                    == "1" and self.second_points_list[i]["name"]
                                                                                    == "1") or (self.first_points_list[b]["name"]
                                                                                                == "Sun" and self.second_points_list[i]["name"]
                                                                                                == "1") or (self.first_points_list[b]["name"]
                                                                                                            == "1" and self.second_points_list[i]["name"]
                                                                                                            == "Sun") or (self.first_points_list[b]["name"]
                                                                                                                          == "Moon" and self.second_points_list[i]["name"]
                                                                                                                          == "1") or (self.first_points_list[b]["name"]
                                                                                                                                      == "1" and self.second_points_list[i]["name"]
                                                                                                                                      == "Moon"):
                        value = 4
                        if (self.first_points_list[i]["name"]
                            == "Sun" and self.second_points_list[b]["name"]
                            == "Sun" and self.first_points_list[i]["sign"]
                                == self.second_points_list[b]["sign"]):
                            value += 5
                            points += value
                        else:
                            points += value

                    elif (self.first_points_list[i]["name"]
                          == "Venus" and self.second_points_list[b]["name"]
                          == "Mars") or (self.first_points_list[i]["name"]
                                         == "Mars" and self.second_points_list[b]["name"]
                                         == "Venus"):
                        value = 4
                        points += value
                    else:
                        value = 0

                    counter += 1
                    orbit = round(orbit, ORBIT_ROUND)
                    aspect = {"user_a_name":     self.user_a.name,
                              "user_a_object":   self.first_points_list[i]["name"],
                              "aspect":         aspect,
                              "user_b_name":     self.user_b.name,
                              "user_b_objcet":   self.second_points_list[b]["name"],
                              "orbit":          orbit,
                              "Value":          value,
                              "counter":        counter
                              }
                    aspects.append(aspect)

                elif verdict == False and aspect == "DESTINO":

                    counter += 1
                    value = 5
                    points += value
                    orbit = round(orbit, ORBIT_ROUND)

                    aspect = {'user_a_name':    self.user_a.name,
                              'user_a_object':  'Sun',
                              'aspect':        'DESTINY',
                              'user_b_name':    self.user_b.name,
                              'user_b_objcet':  'Sun',
                              'orbit':         orbit,
                              'Value':         value,
                              'counter':       counter
                              }

                    aspects.append(aspect)
                elif verdict == False:
                    # aspect = (self.user_a.name, self.first_points_list[i]["name"], aspect,
                    # self.user_b.name, self.second_points_list[b]["name"], orbit, counter)
                    None
                else:
                    aspect = ("ERROR")
                    aspects.append(aspect)

        self.counter = counter
        self.score = points
        self.aspects = aspects


if __name__ == "__main__":

    #lui = KrInstance("Windsor", 1894, 6, 23, 21, 55, "London")
    lui = KrInstance("Kanye", 1977, 6, 8, 8, 45,
                     "Atlanta", lon=50, lat=50, tz_str="Europe/Rome")

    #lei = KrInstance("Simpson", 1896, 6, 19, 22, 30, "Blue Ridge Summit")
    lei = KrInstance("Kanye", 1977, 6, 8, 8, 45,
                     "Atlanta", lon=50, lat=50, tz_str="Europe/Rome")

    sn = DiscepoloNumber(lei, lui)
    sn.get_synastry()
    print(lei.sun)
    print(lui.sun)

    for a in sn.aspects:
        print(a)

    print(sn.score)
