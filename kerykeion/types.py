"""
    This is part of Kerykeion (C) 2022 Giacomo Battaglia
"""
from typing import Any, Literal, Union

from pkg_resources import UnknownExtra

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
KerykeionPlanetDictionaryKey = Literal[
    'name',
    'quality',
    'element',
    'sign',
    'sign_num',
    'position',
    'abs_pos',
    'emoji',
    'house',
    'retrograde'
]
KerykeionPlanetDictionaryValue = Union[KerykeionPlanetDictionaryKey, int, float, str, Any]
KerykeionPlanetDictionary = dict[KerykeionPlanetDictionaryKey, KerykeionPlanetDictionaryValue]

if __name__ == "__main__":
    print()