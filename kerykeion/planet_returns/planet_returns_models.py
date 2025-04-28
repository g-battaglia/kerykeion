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
)
from kerykeion.kr_types.kr_models import (
    SubscriptableBaseModel,
    KerykeionPointModel,
    LunarPhaseModel,
)


class SolarReturnModel(SubscriptableBaseModel):
    """
    Pydantic model for a Solar Return chart.
    """
    # Chart metadata
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
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
    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str
    julian_day: float

    # Deprecated properties
    utc_time: float
    local_time: float

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

    # Nodes
    mean_node: KerykeionPointModel
    true_node: KerykeionPointModel
    mean_south_node: KerykeionPointModel
    true_south_node: KerykeionPointModel

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

    # Lists and phase
    planets_names_list: list[Planet]
    axial_cusps_names_list: list[AxialCusps]
    houses_names_list: list[Houses]
    lunar_phase: LunarPhaseModel


class LunarReturnModel(SubscriptableBaseModel):
    """
    Pydantic model for a Lunar Return chart.
    """
    # Chart metadata
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
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
    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str
    julian_day: float

    # Deprecated properties
    utc_time: float
    local_time: float

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

    # Nodes
    mean_node: KerykeionPointModel
    true_node: KerykeionPointModel
    mean_south_node: KerykeionPointModel
    true_south_node: KerykeionPointModel

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

    # Lists and phase
    planets_names_list: list[Planet]
    axial_cusps_names_list: list[AxialCusps]
    houses_names_list: list[Houses]
    lunar_phase: LunarPhaseModel
