"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Literal

# Zodiac Types:
ZodiacType = Literal["Tropic", "Sidereal"]

# Sings:
Sign = Literal[
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"
]

Houses = Literal[
    "First House",
    "Second House",
    "Third House",
    "Fourth House",
    "Fifth House",
    "Sixth House",
    "Seventh House",
    "Eighth House",
    "Ninth House",
    "Tenth House",
    "Eleventh House",
    "Twelfth House",
]

Planet = Literal[
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Mean_Node",
    "True_Node",
]

Element = Literal["Air", "Fire", "Earth", "Water"]

Quality = Literal[
    "Cardinal",
    "Fixed",
    "Mutable",
]


ChartType = Literal["Natal", "Composite", "Transit"]

LunarPhaseEmoji = Literal["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
