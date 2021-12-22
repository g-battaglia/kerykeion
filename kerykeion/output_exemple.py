"""
    This is part of Kerykeion (C) 2020 Giacomo Battaglia
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kerykeion.main import KrInstance

def output(user):
    p = user.planets_in_houses()
    h = user.houses()
    finale = ("-----------------------------------------------------\n")
    finale += ("NAME: " + user.name + "\n")
    finale += ("PLANET     POSITION\n")
    finale += ("                      \n") 
    finale += (f"Sun:       {user.sun['sign']} {round(user.sun['position'], 3)} in {user.sun['house']}\n")
    finale += (f"Moon:      {user.moon['sign']} {round(user.moon['position'], 3)} in {user.moon['house']}\n")
    finale += (f"Mercury:   {user.mercury['sign']} {round(user.mercury['position'], 3)} in {user.mercury['house']}\n")
    finale += (f"Venus:     {user.venus['sign']} {round(user.venus['position'], 3)} in {user.venus['house']}\n")
    finale += (f"Mars:      {user.mars['sign']} {round(user.mars['position'], 3)} in {user.mars['house']}\n")
    finale += (f"Jupiter:   {user.jupiter['sign']} {round(user.jupiter['position'], 3)} in {user.jupiter['house']}\n")
    finale += (f"Saturn:    {user.saturn['sign']} {round(user.saturn['position'], 3)} in {user.saturn['house']}\n")
    finale += (f"Uranus:    {user.uranus['sign']} {round(user.uranus['position'], 3)} in {user.uranus['house']}\n")
    finale += (f"Neptune:   {user.neptune['sign']} {round(user.neptune['position'], 3)} in {user.neptune['house']}\n")
    finale += (f"Pluto:     {user.pluto['sign']} {round(user.pluto['position'], 3)} in {user.pluto['house']}\n")
    #finale += (f"Juno:      {p[10]['sign']} {round(p[10]['pos'], 3)} in {p[10]['house']}\n\n")
    finale += ("\nPLACIDUS HOUSES\n")
    finale += (f"House Cusp 1:     {user.first_house['sign']}  {round(user.first_house['position'], 3)}\n")
    finale += (f"House Cusp 2:     {user.second_house['sign']}  {round(user.second_house['position'], 3)}\n")
    finale += (f"House Cusp 3:     {user.third_house['sign']}  {round(user.third_house['position'], 3)}\n")
    finale += (f"House Cusp 4:     {user.fourth_house['sign']}  {round(user.fourth_house['position'], 3)}\n")
    finale += (f"House Cusp 5:     {user.fifth_house['sign']}  {round(user.fifth_house['position'], 3)}\n")
    finale += (f"House Cusp 6:     {user.sixth_house['sign']}  {round(user.sixth_house['position'], 3)}\n")
    finale += (f"House Cusp 7:     {user.seventh_house['sign']}  {round(user.seventh_house['position'], 3)}\n")
    finale += (f"House Cusp 8:     {user.eighth_house['sign']}  {round(user.eighth_house['position'], 3)}\n")
    finale += (f"House Cusp 9:     {user.ninth_house['sign']}  {round(user.ninth_house['position'], 3)}\n")
    finale += (f"House Cusp 10:    {user.tenth_house['sign']}  {round(user.tenth_house['position'], 3)}\n")
    finale += (f"House Cusp 11:    {user.eleventh_house['sign']}  {round(user.eleventh_house['position'], 3)}\n")
    finale += (f"House Cusp 12:    {user.twelfth_house['sign']}  {round(user.twelfth_house['position'], 3)}\n")
    finale += ("\n")
    return finale





if __name__ == "__main__":
    user = KrInstance("Brigitte Bardot", 1934, 9, 28, 13, 15, "Paris", "FR")
    print(output(user))
