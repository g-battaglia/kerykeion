from kerykeion.kr_types.kr_literals import Planet, AxialCusps
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
