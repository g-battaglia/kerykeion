# -*- coding: utf-8 -*-
"""
Pydantic models for Solar and Lunar Return charts.
"""

from typing import Union
from kerykeion.kr_types.kr_literals import (
    ZodiacType,
    SiderealMode,
    HousesSystemIdentifier,
    Planet,
    Houses,
    AxialCusps,
    PerspectiveType,
    ReturnType
)
from kerykeion.kr_types.kr_models import (
    SubscriptableBaseModel,
    KerykeionPointModel,
    LunarPhaseModel,
)



class PlanetReturnsModel(SubscriptableBaseModel):
    """
    Pydantic Model for Astrological Subject
    """
    return_type: ReturnType
    """Type of return: Solar or Lunar"""

    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str
    julian_day: float

    # Data
    city: str
    nation: str
    lng: float
    lat: float
    tz_str: str
    zodiac_type: ZodiacType
    sidereal_mode: Union[SiderealMode, None]
    houses_system_identifier: HousesSystemIdentifier
    houses_system_name: str
    perspective_type: PerspectiveType

    # Planets
    sun: KerykeionPointModel
    moon: KerykeionPointModel
    mercury: KerykeionPointModel
    venus: KerykeionPointModel
    mars: KerykeionPointModel
    jupiter: KerykeionPointModel
    saturn: KerykeionPointModel
    uranus: KerykeionPointModel
    neptune: KerykeionPointModel
    pluto: KerykeionPointModel

    # Axes
    ascendant: KerykeionPointModel
    descendant: KerykeionPointModel
    medium_coeli: KerykeionPointModel
    imum_coeli: KerykeionPointModel

    # Optional Planets:
    chiron: Union[KerykeionPointModel, None]
    mean_lilith: Union[KerykeionPointModel, None]

    # Houses
    first_house: KerykeionPointModel
    second_house: KerykeionPointModel
    third_house: KerykeionPointModel
    fourth_house: KerykeionPointModel
    fifth_house: KerykeionPointModel
    sixth_house: KerykeionPointModel
    seventh_house: KerykeionPointModel
    eighth_house: KerykeionPointModel
    ninth_house: KerykeionPointModel
    tenth_house: KerykeionPointModel
    eleventh_house: KerykeionPointModel
    twelfth_house: KerykeionPointModel

    # Nodes
    mean_node: KerykeionPointModel
    true_node: KerykeionPointModel
    mean_south_node: KerykeionPointModel
    true_south_node: KerykeionPointModel

    planets_names_list: list[Planet]
    """Ordered list of available planets names"""

    axial_cusps_names_list: list[AxialCusps]
    """Ordered list of available axes names"""

    houses_names_list: list[Houses]
    """Ordered list of houses names"""

    lunar_phase: LunarPhaseModel
    """Lunar phase model"""

