# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""
from typing import Literal


ZodiacType = Literal["Tropic", "Sidereal"]
"""Literal type for Zodiac Types"""


Sign = Literal["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
"""Literal type for Zodiac Signs"""


SignNumbers = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
"""Literal type for Zodiac Sign Numbers, the signs are numbered in order starting from Aries (0) to Pisces (11)"""


Houses = Literal["First_House", "Second_House", "Third_House", "Fourth_House", "Fifth_House", "Sixth_House", "Seventh_House", "Eighth_House", "Ninth_House", "Tenth_House", "Eleventh_House", "Twelfth_House"]
"""Literal type for Houses"""


HouseNumbers = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
"""Literal type for House Numbers, starting from the First House (1) to the Twelfth House (12)"""


Planet = Literal["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Mean_Node", "True_Node", "Chiron"]
"""Literal type for Planets"""


Element = Literal["Air", "Fire", "Earth", "Water"]
"""Literal type for Elements"""


Quality = Literal["Cardinal", "Fixed", "Mutable"]
"""Literal type for Qualities"""


ChartType = Literal["Natal", "ExternalNatal", "Synastry", "Transit"]
"""Literal type for Chart Types"""


PointType = Literal["Planet", "House"]
"""Literal type for Point Types"""


LunarPhaseEmoji = Literal["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
"""Literal type for Lunar Phases Emoji"""


LunarPhaseName = Literal["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
"""Literal type for Lunar Phases Name"""


SiderealMode = Literal["FAGAN_BRADLEY", "LAHIRI", "DELUCE", "RAMAN", "USHASHASHI", "KRISHNAMURTI", "DJWHAL_KHUL", "YUKTESHWAR", "JN_BHASIN", "BABYL_KUGLER1", "BABYL_KUGLER2", "BABYL_KUGLER3", "BABYL_HUBER", "BABYL_ETPSC", "ALDEBARAN_15TAU", "HIPPARCHOS", "SASSANIAN", "J2000", "J1900", "B1950"]
"""Literal type for Sidereal Modes, as known as Ayanamsa"""


HousesSystemIdentifier = Literal["A", "B", "C", "D", "F", "H", "I", "i", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y"]
"""
Literal type for Houses Systems:

A = equal
B = Alcabitius
C = Campanus
D = equal (MC)
F = Carter poli-equ.
H = horizon/azimut
I = Sunshine
i = Sunshine/alt.
K = Koch
L = Pullen SD
M = Morinus
N = equal/1=Aries
O = Porphyry
P = Placidus
Q = Pullen SR
R = Regiomontanus
S = Sripati
T = Polich/Page
U = Krusinski-Pisa-Goelzer
V = equal/Vehlow
W = equal/whole sign
X = axial rotation system/Meridian houses
Y = APC houses

Usually the standard is Placidus (P)
"""


PerspectiveType = Literal["Apparent Geocentric", "Heliocentric", "Topocentric", "True Geocentric"]
"""
Literal type for perspective types.
- "Apparent Geocentric": Earth-centered, apparent positions.
- "Heliocentric": Sun-centered.
- "Topocentric": Observer's location on Earth's surface.
- "True Geocentric": Earth-centered, true positions.

Usually the standard is "Apparent Geocentric"
"""