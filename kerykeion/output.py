"""
    This is part of Kerykeion (C) 2020 Giacomo Battaglia
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kerykeion.astrocore import AstroData, Calculator

def output(user):
    p = user.planets_house()
    h = user.houses()
    finale = ("-----------------------------------------------------\n")
    finale += ("NAME: " + user.name + "\n")
    finale += ("PLANET     POSITION\n")
    finale += ("                      \n")
    finale += (f"Sun:       {p[0]['sign']} {round(p[0]['pos'], 3)} in {p[0]['house']}\n")
    finale += (f"Moon:      {p[1]['sign']} {round(p[1]['pos'], 3)} in {p[1]['house']}\n")
    finale += (f"Mercury:   {p[2]['sign']} {round(p[2]['pos'], 3)} in {p[2]['house']}\n")
    finale += (f"Venus:     {p[3]['sign']} {round(p[3]['pos'], 3)} in {p[3]['house']}\n")
    finale += (f"Mars:      {p[4]['sign']} {round(p[4]['pos'], 3)} in {p[4]['house']}\n")
    finale += (f"Jupiter:   {p[5]['sign']} {round(p[5]['pos'], 3)} in {p[5]['house']}\n")
    finale += (f"Saturn:    {p[6]['sign']} {round(p[6]['pos'], 3)} in {p[6]['house']}\n")
    finale += (f"Uranus:    {p[7]['sign']} {round(p[7]['pos'], 3)} in {p[7]['house']}\n")
    finale += (f"Neptune:   {p[8]['sign']} {round(p[8]['pos'], 3)} in {p[8]['house']}\n")
    finale += (f"Pluto:     {p[9]['sign']} {round(p[9]['pos'], 3)} in {p[9]['house']}\n")
    #finale += (f"Juno:      {p[10]['sign']} {round(p[10]['pos'], 3)} in {p[10]['house']}\n\n")
    finale += ("\nPLACIDUS HAUSES\n")
    finale += (f"House Cusp 1:     {h[0]['sign']}  {round(h[0]['pos'], 3)}\n")
    finale += (f"House Cusp 2:     {h[1]['sign']}  {round(h[1]['pos'], 3)}\n")
    finale += (f"House Cusp 3:     {h[2]['sign']}  {round(h[2]['pos'], 3)}\n")
    finale += (f"House Cusp 4:     {h[3]['sign']}  {round(h[3]['pos'], 3)}\n")
    finale += (f"House Cusp 5:     {h[4]['sign']}  {round(h[4]['pos'], 3)}\n")
    finale += (f"House Cusp 6:     {h[5]['sign']}  {round(h[5]['pos'], 3)}\n")
    finale += (f"House Cusp 7:     {h[6]['sign']}  {round(h[6]['pos'], 3)}\n")
    finale += (f"House Cusp 8:     {h[7]['sign']}  {round(h[7]['pos'], 3)}\n")
    finale += (f"House Cusp 9:     {h[8]['sign']}  {round(h[8]['pos'], 3)}\n")
    finale += (f"House Cusp 10:    {h[9]['sign']}  {round(h[9]['pos'], 3)}\n")
    finale += (f"House Cusp 11:    {h[10]['sign']}  {round(h[10]['pos'], 3)}\n")
    finale += (f"House Cusp 12:    {h[11]['sign']}  {round(h[11]['pos'], 3)}\n")
    finale += ("\n")
    return finale

user = Calculator("Brigitte Bardot", 1934, 9, 28, 13, 15, "Paris", "FR")


if __name__ == "__main__":
    print(output(user))