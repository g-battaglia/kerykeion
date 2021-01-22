"""
    This is part of Kerykeion (C) 2020 Giacomo Battaglia
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kerykeion.astrocore import Calculator
import swisseph as swe

DEBUG = False
def dprint(*str):
    if DEBUG:
        print(str)

bergman = Calculator("Ingrid_Bergman", 1993, 6, 20, 12, 15, "Stockholm")
rossellini = Calculator("Rossellini", 1994, 6, 1, 19, 50, "Roma")

class Synastry():
    """
    Calculates the synastry using Ciro Discepolo's algorithm.
    Args: first user object, second user object
    """

    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2
        user1.get_all()
        user2.get_all()
        self.first_points_list = user1.planets_list[:7] + [user1.house_list[0],
         user1.house_list[9]]
        self.second_points_list = user2.planets_list[:7] + [user2.house_list[0],
         user2.house_list[9]]


    def synastry_aspect(self, user1, pl_us1, user2, pl_us2):
        """ 
        Calculates the aspects between the 2 users.
        Args: first user object, first list of planets and houses,
        second user objcet, second list of planets and houses. 
        """

        distance = abs(swe.difdeg2n(self.first_points_list[pl_us1]["abs_pos"],
        self.second_points_list[pl_us2]["abs_pos"]))
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
                verdict, aspect, orbit = self.synastry_aspect(self.user1, i,
                 self.user2, b)
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
                    == 1 and self.second_points_list[i]["name"]
                    == 1) or (self.first_points_list[b]["name"] 
                    == "Sun" and self.second_points_list[i]["name"]
                    == 1) or (self.first_points_list[b]["name"] 
                    == 1 and self.second_points_list[i]["name"]
                    == "Sun") or (self.first_points_list[b]["name"] 
                    == "Moon" and self.second_points_list[i]["name"]
                    == 1) or (self.first_points_list[b]["name"] 
                    == 1 and self.second_points_list[i]["name"]
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
                    orbit = round(orbit, 3)
                    aspect = {"user1_name":     self.user1.name,
                              "user1_object":   self.first_points_list[i]["name"],
                              "aspect":         aspect,
                              "user2_name":     self.user2.name,
                              "user2_objcet":   self.second_points_list[b]["name"],
                              "orbit":          orbit,
                              "Value":          value,
                              "counter":        counter}
                    aspects.append(aspect)
                elif verdict == False and aspect == "DESTINO":
                    
                    counter += 1
                    value = 5
                    points += value

                    aspect = {'user1_name':    self.user1.name,
                              'user1_object':  'Sun',
                              'aspect':        'DESTINY',
                              'user2_name':    self.user2.name,
                              'user2_objcet':  'Sun',
                              'orbit':         orbit,
                              'Value':         value,
                              'counter':       counter
                            }

                    aspects.append(aspect) 
                elif verdict == False:
                    #aspect = (self.user1.name, self.first_points_list[i]["name"], aspect,
                     #self.user2.name, self.second_points_list[b]["name"], orbit, counter)
                     None
                else:
                    aspect = ("ERROR")
                    aspects.append(aspect)

        self.counter = counter
        self.score   = points
        self.aspects = aspects

if __name__ == "__main__":
    sn = Synastry(bergman, rossellini)
    sn.get_synastry()
    print(sn.score)
