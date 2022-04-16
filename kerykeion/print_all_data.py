"""
    This is part of Kerykeion (C) 2022 Giacomo Battaglia
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kerykeion import KrInstance

def print_all_data(user: KrInstance) -> None:
    output = ("\n")
    output += ("NAME: " + user.name + "\n")
    output += ("PLANET     POSITION\n")
    output += ("                      \n") 
    output += (f"Sun:       {user.sun['sign']} {round(user.sun['position'], 3)} in {user.sun['house']}\n")
    output += (f"Moon:      {user.moon['sign']} {round(user.moon['position'], 3)} in {user.moon['house']}\n")
    output += (f"Mercury:   {user.mercury['sign']} {round(user.mercury['position'], 3)} in {user.mercury['house']}\n")
    output += (f"Venus:     {user.venus['sign']} {round(user.venus['position'], 3)} in {user.venus['house']}\n")
    output += (f"Mars:      {user.mars['sign']} {round(user.mars['position'], 3)} in {user.mars['house']}\n")
    output += (f"Jupiter:   {user.jupiter['sign']} {round(user.jupiter['position'], 3)} in {user.jupiter['house']}\n")
    output += (f"Saturn:    {user.saturn['sign']} {round(user.saturn['position'], 3)} in {user.saturn['house']}\n")
    output += (f"Uranus:    {user.uranus['sign']} {round(user.uranus['position'], 3)} in {user.uranus['house']}\n")
    output += (f"Neptune:   {user.neptune['sign']} {round(user.neptune['position'], 3)} in {user.neptune['house']}\n")
    output += (f"Pluto:     {user.pluto['sign']} {round(user.pluto['position'], 3)} in {user.pluto['house']}\n")
    #output += (f"Juno:      {p[10]['sign']} {round(p[10]['pos'], 3)} in {p[10]['house']}\n\n")
    output += ("\nPLACIDUS HOUSES\n")
    output += (f"House Cusp 1:     {user.first_house['sign']}  {round(user.first_house['position'], 3)}\n")
    output += (f"House Cusp 2:     {user.second_house['sign']}  {round(user.second_house['position'], 3)}\n")
    output += (f"House Cusp 3:     {user.third_house['sign']}  {round(user.third_house['position'], 3)}\n")
    output += (f"House Cusp 4:     {user.fourth_house['sign']}  {round(user.fourth_house['position'], 3)}\n")
    output += (f"House Cusp 5:     {user.fifth_house['sign']}  {round(user.fifth_house['position'], 3)}\n")
    output += (f"House Cusp 6:     {user.sixth_house['sign']}  {round(user.sixth_house['position'], 3)}\n")
    output += (f"House Cusp 7:     {user.seventh_house['sign']}  {round(user.seventh_house['position'], 3)}\n")
    output += (f"House Cusp 8:     {user.eighth_house['sign']}  {round(user.eighth_house['position'], 3)}\n")
    output += (f"House Cusp 9:     {user.ninth_house['sign']}  {round(user.ninth_house['position'], 3)}\n")
    output += (f"House Cusp 10:    {user.tenth_house['sign']}  {round(user.tenth_house['position'], 3)}\n")
    output += (f"House Cusp 11:    {user.eleventh_house['sign']}  {round(user.eleventh_house['position'], 3)}\n")
    output += (f"House Cusp 12:    {user.twelfth_house['sign']}  {round(user.twelfth_house['position'], 3)}\n")
    output += ("\n")
    print(output)

if __name__ == "__main__":
    user = KrInstance("Brigitte Bardot", 1934, 9, 28, 13, 15, "Paris", "FR")
    print_all_data(user)
