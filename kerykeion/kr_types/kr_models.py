# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""


from typing import Union, Optional
from pydantic import BaseModel

from kerykeion.kr_types import (
    LunarPhaseEmoji,
    LunarPhaseName,
    Planet,
    Houses,
    Quality,
    Element,
    Sign,
    ZodiacType,
    SignNumbers,
    PointType,
    SiderealMode,
    HousesSystemIdentifier,
    Houses,
    SignsEmoji
)


class SubscriptableBaseModel(BaseModel):
    """
    Pydantic BaseModel with subscriptable support, so you can access the fields as if they were a dictionary.
    """

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

    def get(self, key, default = None):
        return getattr(self, key, default)


class LunarPhaseModel(SubscriptableBaseModel):
    degrees_between_s_m: Union[float, int]
    moon_phase: int
    sun_phase: int
    moon_emoji: LunarPhaseEmoji
    moon_phase_name: LunarPhaseName


class KerykeionPointModel(SubscriptableBaseModel):
    """
    Kerykeion Point Model
    """

    name: Union[Planet, Houses]
    quality: Quality
    element: Element
    sign: Sign
    sign_num: SignNumbers
    position: float
    abs_pos: float
    emoji: str
    point_type: PointType
    house: Optional[Houses] = None
    retrograde: Optional[bool] = None


class AstrologicalSubjectModel(SubscriptableBaseModel):
    # Data
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
    perspective_type: str
    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str
    julian_day: float

    # Deprecated properties -->
    utc_time: float
    local_time: float
    # <-- Deprecated properties

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

    lunar_phase: LunarPhaseModel
    """Lunar phase model"""
    
    planets_names_list: list[Planet]
    """Ordered list of available planets names"""

    houses_names_list: list[Houses]
    """Ordered list of houses names"""


class EphemerisDictModel(SubscriptableBaseModel):
    date: str
    planets: list[KerykeionPointModel]
    houses: list[KerykeionPointModel]


class AspectModel(SubscriptableBaseModel):
    p1_name: str
    p1_abs_pos: float
    p2_name: str
    p2_abs_pos: float
    aspect: str
    orbit: float
    aspect_degrees: int
    aid: int
    diff: float
    p1: int
    p2: int


class ZodiacSignModel(SubscriptableBaseModel):
    sign: Sign
    quality: Quality
    element: Element
    emoji: SignsEmoji
    sign_num: SignNumbers