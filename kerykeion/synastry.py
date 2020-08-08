"""
    This is part of Kerykeion (C) 2020 Giacomo Battaglia
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kerykeion.astrocore import AstroData, Calculator
import swisseph as swe

bergman = Calculator("Ingrid_Bergman", 15, 8, 29, 3, 30, "Stockholm")
rossellini = Calculator("Rossellini", 1906, 5, 8, 12, 50, "Roma")

class Synastry():
    """
    Calculates the synastry using the Ciro Discepolo way.
    Args: first user object, second user object
    """

    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2
        user1.get_all()
        user2.get_all()
        self.pl_ho_info1 = user1.planets_list[:7] + [user1.house_list[0],
         user1.house_list[9]]
        self.pl_ho_info2 = user2.planets_list[:7] + [user2.house_list[0],
         user2.house_list[9]]

    def synastry_aspect(self, user1, pl_us1, user2, pl_us2):
        """ 
        Calculates the aspects between the 2 users.
        Args: first user object, first list of planets and houses,
        second user objcet, second list of planets and houses. 
        """

        distance = abs(swe.difdeg2n(self.pl_ho_info1[pl_us1]["abs_pos"],
        self.pl_ho_info2[pl_us2]["abs_pos"]))
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
        elif (self.pl_ho_info1[pl_us1]["name"] == "Sun" and
         self.pl_ho_info2[pl_us2]["name"] == "Sun" and
         self.pl_ho_info1[pl_us1]["quality"] ==
         self.pl_ho_info2[pl_us2]["quality"]):
            aspect = "DESTINO"
            return False, aspect, distance
        else:
            return False, None, None

    def synastry_result(self):
        """
        Asingns points to the aspects and prints them.
        """
        lenght = len(self.pl_ho_info1)
        counter = 0
        points = 0
        for i in range(lenght):
            for b in range(lenght):
                verdict, aspect, orbit = self.synastry_aspect(self.user1, i,
                 self.user2, b)
                if verdict == True:
                    if aspect == "Conjuction" and ((self.pl_ho_info1[i]
                    ["name"] 
                    == "Sun" and self.pl_ho_info2[b]["name"] 
                    == "Moon") or (self.pl_ho_info1[i]["name"] 
                    == "Moon" and self.pl_ho_info2[b]["name"]
                    == "Sun")):
                        points += 8
                        if abs(int(orbit)) <= 2:
                            points += 3
                    elif (self.pl_ho_info1[b]["name"] 
                    == "Sun" and self.pl_ho_info2[i]["name"]
                    == "Sun") or (self.pl_ho_info1[b]["name"] 
                    == "Sun" and self.pl_ho_info2[i]["name"]
                    == "Moon") or (self.pl_ho_info1[b]["name"] 
                    == "Moon" and self.pl_ho_info2[i]["name"]
                    == "Sun") or (self.pl_ho_info1[b]["name"] 
                    == "Moon" and self.pl_ho_info2[i]["name"]
                    == "Moon") or (self.pl_ho_info1[b]["name"] 
                    == 1 and self.pl_ho_info2[i]["name"]
                    == 1) or (self.pl_ho_info1[b]["name"] 
                    == "Sun" and self.pl_ho_info2[i]["name"]
                    == 1) or (self.pl_ho_info1[b]["name"] 
                    == 1 and self.pl_ho_info2[i]["name"]
                    == "Sun") or (self.pl_ho_info1[b]["name"] 
                    == "Moon" and self.pl_ho_info2[i]["name"]
                    == 1) or (self.pl_ho_info1[b]["name"] 
                    == 1 and self.pl_ho_info2[i]["name"]
                    == "Moon"):
                        points += 4
                        if (self.pl_ho_info1[i]["name"] 
                        == "Sun" and self.pl_ho_info2[b]["name"] 
                        == "Sun" and self.pl_ho_info1[i]["sign"] 
                        == self.pl_ho_info2[b]["sign"]):
                            points += 5
                    elif (self.pl_ho_info1[i]["name"] 
                    == "Venus" and self.pl_ho_info2[b]["name"] 
                    == "Mars") or (self.pl_ho_info1[i]["name"] 
                    == "Mars" and self.pl_ho_info2[b]["name"] 
                    == "Venus"):
                        points += 4
                    counter += 1
                    print("-----------------------------\n",
                     self.user1.name, self.pl_ho_info1[i]["name"],
                      aspect, self.user2.name, self.pl_ho_info2[b]["name"],
                       "orbit:", round(orbit, 3), "Points:", points,
                        "\n-----------------------------", counter)
                elif verdict == False and aspect == "DESTINO":
                    counter += 1
                    points += 5
                    print("-----------------------------\n",
                    "destino", points, orbit)
                elif verdict == False:
                    #print(self.user1.name, self.pl_ho_info1[i]["name"], aspect,
                     #self.user2.name, self.pl_ho_info2[b]["name"], orbit, counter)
                     None
                else:
                    print("ERROR")
        print(points)

if __name__ == "__main__":
    Synastry(bergman, rossellini).synastry_result()
