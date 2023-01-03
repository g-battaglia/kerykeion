"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Literal, Union, Optional
from pydantic import BaseModel

from .kr_literals import *


class LunarPhaseObject(BaseModel):
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


class KerykeionPoint(BaseModel):
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


class KerykeionSubject(BaseModel):
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
    sun: KerykeionPoint
    moon: KerykeionPoint
    mercury: KerykeionPoint
    venus: KerykeionPoint
    mars: KerykeionPoint
    jupiter: KerykeionPoint
    saturn: KerykeionPoint
    uranus: KerykeionPoint
    neptune: KerykeionPoint
    pluto: KerykeionPoint

    # Houses
    first_house: KerykeionPoint
    second_house: KerykeionPoint
    third_house: KerykeionPoint
    fourth_house: KerykeionPoint
    fifth_house: KerykeionPoint
    sixth_house: KerykeionPoint
    seventh_house: KerykeionPoint
    eighth_house: KerykeionPoint
    ninth_house: KerykeionPoint
    tenth_house: KerykeionPoint
    eleventh_house: KerykeionPoint
    twelfth_house: KerykeionPoint

    # Nodes
    mean_node: KerykeionPoint
    true_node: KerykeionPoint

    # Lunar Phase
    lunar_phase: LunarPhaseObject


if __name__ == "__main__":
    sun = KerykeionPoint(
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
