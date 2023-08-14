# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia
"""


from typing import Literal, Union, Optional
from pydantic import BaseModel

from .kr_literals import *


class LunarPhaseModel(BaseModel):
    degrees_between_s_m: Union[int, float]
    moon_phase: int
    sun_phase: int
    moon_emoji: LunarPhaseEmoji

    def __str__(self):
        return (
            super()
            .dict(
                exclude_none=True,
                exclude_unset=True,
                exclude_defaults=True,
                by_alias=False,
            )
            .__str__()
        )

    def __repr__(self):
        return (
            super()
            .dict(
                exclude_none=True,
                exclude_unset=True,
                exclude_defaults=True,
                by_alias=False,
            )
            .__str__()
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

    def get(self, key, default):
        return getattr(self, key, default)


class KerykeionPointModel(BaseModel):
    """
    Kerykeion Point Model
    """

    name: Union[Planet, Houses]
    quality: Quality
    element: Element
    sign: Sign
    sign_num: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    position: float
    abs_pos: float
    emoji: str
    point_type: Literal["Planet", "House"]
    house: Optional[Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]] = None
    retrograde: Optional[bool] = None

    def __str__(self):
        return (
            super()
            .dict(
                exclude_none=True,
                exclude_unset=True,
                exclude_defaults=True,
                by_alias=False,
            )
            .__str__()
        )

    def __repr__(self):
        return (
            super()
            .dict(
                exclude_none=True,
                exclude_unset=True,
                exclude_defaults=True,
                by_alias=False,
            )
            .__str__()
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

    def get(self, key, default):
        return getattr(self, key, default)


class AstrologicalSubjectModel(BaseModel):
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
    local_time: float
    utc_time: float
    julian_day: float

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

    # Lunar Phase
    lunar_phase: LunarPhaseModel


if __name__ == "__main__":
    sun = KerykeionPointModel(
        name="Sun",
        element="Air",
        quality="Fixed",
        sign="Aqu",
        sign_num=1,
        position=0,
        abs_pos=12.123123,
        emoji="♈",
        point_type="Planet",
    )

    print(sun.json())
    print(sun)
