"""
    This is part of Kerykeion (C) 2022 Giacomo Battaglia
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Literal, Union, Optional
from pydantic import BaseModel
import json


# Exceptions:


class KerykeionException(Exception):
    """
    Custom Kerykeion Exception
    """

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


# Zodiac Types:
ZodiacType = Literal['Tropic', 'Sidereal']

# Sings:
Sign = Literal[
    "Ari",
    "Tau",
    "Gem",
    "Can",
    "Leo",
    "Vir",
    "Lib",
    "Sco",
    "Sag",
    "Cap",
    "Aqu",
    "Pis"
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
    "Twelfth House"
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
    "True_Node"
]

Element = Literal[
    "Air",
    "Fire",
    "Earth",
    "Water"
]

Quality = Literal[
    'Cardinal',
    'Fixed',
    'Mutable',
]


ChartType = Literal[
    'Natal',
    'Composite',
    'Transit'
]


class KerykeionPoint(BaseModel):
    """
    Kerykeion Point Model
    """
    name: Union[Planet, Houses]
    quality:  Quality
    element: Element
    sign: Sign
    sign_num: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    position: float
    abs_pos: float
    emoji: str
    point_type: Literal['Planet', 'House']
    house: Optional[Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
    retrograde: Optional[bool]

    def __str__(self):
        return self.dict().__str__()

    def __repr__(self):
        return self.dict().__str__()

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

if __name__ == "__main__":
    sun = KerykeionPoint(
        name='Sun',
        element='Air',
        quality='Fixed',
        sign='Aqu',
        sign_num=1,
        position=0,
        abs_pos=12.123123,
        emoji='♈',
        point_type='Planet',
        house=1,
        retrograde=False,

    )

    print(json.dumps(sun, default=vars))
    print(sun.abs_pos)
