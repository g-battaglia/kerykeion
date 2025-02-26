from kerykeion.kr_types.kr_literals import Planet, AxialCusps, AspectName
from kerykeion.kr_types.kr_models import ActiveAspect
from typing import List, Union

DEFAULT_ACTIVE_POINTS: List[Union[Planet, AxialCusps]] = [
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
    # "True_Node",
    "Chiron",
    "Ascendant",
    "Medium_Coeli",
    # "Descendant",
    # "Imum_Coeli",
    "Mean_Lilith",
    "Mean_South_Node",
    # "True_South_Node"
]
"""
Default list of active points in the charts or aspects calculations.
"""

DEFAULT_ACTIVE_ASPECTS: List[ActiveAspect] = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "sextile", "orb": 6},
    {"name": "square", "orb": 5},
    {"name": "quintile", "orb": 1},
    # {"name": "semi-sextile", "orb": 1},
    # {"name": "semi-square", "orb": 1},
    # {"name": "sesquiquadrate", "orb": 1},
    # {"name": "biquintile", "orb": 1},
    # {"name": "quincunx", "orb": 1},
]
"""
Default list of active aspects in the aspects calculations.
The full list of aspects is available in the `kr_types.kr_literals.AspectName` literal.
"""
