from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import ActiveAspect
from typing import List


DEFAULT_ACTIVE_POINTS: List[AstrologicalPoint] = [
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
    # "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
    # "Mean_South_Lunar_Node",
    "True_South_Lunar_Node",
    "Chiron",
    "Mean_Lilith",
    # "True_Lilith",
    # "Earth",
    # "Pholus",
    # "Ceres",
    # "Pallas",
    # "Juno",
    # "Vesta",
    # "Eris",
    # "Sedna",
    # "Haumea",
    # "Makemake",
    # "Ixion",
    # "Orcus",
    # "Quaoar",
    # "Regulus",
    # "Spica",
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
    # "Vertex",
    # "Anti_Vertex",
    # "Pars_Fortunae",
    # "Pars_Spiritus",
    # "Pars_Amoris",
    # "Pars_Fidei"
]
"""
Default list of active points in the charts or aspects calculations.
The full list of points is available in the `schemas.kr_literals.AstrologicalPoint` literal.
"""

ALL_ACTIVE_POINTS: List[AstrologicalPoint] = [
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
    "Mean_North_Lunar_Node",
    "True_North_Lunar_Node",
    "Mean_South_Lunar_Node",
    "True_South_Lunar_Node",
    "Chiron",
    "Mean_Lilith",
    "True_Lilith",
    "Earth",
    "Pholus",
    "Ceres",
    "Pallas",
    "Juno",
    "Vesta",
    "Eris",
    "Sedna",
    "Haumea",
    "Makemake",
    "Ixion",
    "Orcus",
    "Quaoar",
    "Regulus",
    "Spica",
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
    "Vertex",
    "Anti_Vertex",
    "Pars_Fortunae",
    "Pars_Spiritus",
    "Pars_Amoris",
    "Pars_Fidei"
]
"""
Full list of active points in the charts or aspects calculations.
The full list of points is available in the `schemas.kr_literals.AstrologicalPoint` literal.
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
The full list of aspects is available in the `schemas.kr_literals.AspectName` literal.
"""

ALL_ACTIVE_ASPECTS: List[ActiveAspect] = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "sextile", "orb": 6},
    {"name": "square", "orb": 5},
    {"name": "quintile", "orb": 1},
    {"name": "semi-sextile", "orb": 1},
    {"name": "semi-square", "orb": 1},
    {"name": "sesquiquadrate", "orb": 1},
    {"name": "biquintile", "orb": 1},
    {"name": "quincunx", "orb": 1},
]
"""
Full list of active aspects in the charts or aspects calculations.
The full list of aspects is available in the `schemas.kr_literals.AspectName` literal.
"""

DISCEPOLO_SCORE_ACTIVE_ASPECTS: List[ActiveAspect] = [
    {"name": "conjunction", "orb": 8},
    {"name": "semi-sextile", "orb": 2},
    {"name": "semi-square", "orb": 2},
    {"name": "sextile", "orb": 4},
    {"name": "square", "orb": 5},
    {"name": "trine", "orb": 7},
    {"name": "sesquiquadrate", "orb": 2},
    {"name": "opposition", "orb": 8},
]
"""
List of active aspects with their orbs according to Ciro Discepolo's affinity scoring methodology.
"""
