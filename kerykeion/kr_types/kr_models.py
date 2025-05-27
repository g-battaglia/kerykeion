# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""


from typing import Union, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel
from kerykeion.kr_types.kr_literals import AspectName

from kerykeion.kr_types import (
    AxialCusps,
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
    SignsEmoji,
    RelationshipScoreDescription,
    PerspectiveType,
    ReturnType
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

    name: Union[Planet, Houses, AxialCusps]
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
    """
    Pydantic Model for Astrological Subject
    """

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
    perspective_type: PerspectiveType
    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str
    julian_day: float

    # Planets
    sun: KerykeionPointModel
    moon: KerykeionPointModel
    mercury: Optional[KerykeionPointModel] = None
    venus: Optional[KerykeionPointModel] = None
    mars: Optional[KerykeionPointModel] = None
    jupiter: Optional[KerykeionPointModel] = None
    saturn: Optional[KerykeionPointModel] = None
    uranus: Optional[KerykeionPointModel] = None
    neptune: Optional[KerykeionPointModel] = None
    pluto: Optional[KerykeionPointModel] = None

    # Axes
    ascendant: Optional[KerykeionPointModel] = None
    descendant: Optional[KerykeionPointModel] = None
    medium_coeli: Optional[KerykeionPointModel] = None
    imum_coeli: Optional[KerykeionPointModel] = None

    # Optional Planets:
    chiron: Optional[KerykeionPointModel] = None
    mean_lilith: Optional[KerykeionPointModel] = None

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
    mean_node: Optional[KerykeionPointModel] = None
    true_node: Optional[KerykeionPointModel] = None
    mean_south_node: Optional[KerykeionPointModel] = None
    true_south_node: Optional[KerykeionPointModel] = None

    planets_names_list: list[Planet]
    """Ordered list of available planets names"""

    axial_cusps_names_list: list[AxialCusps]
    """Ordered list of available axes names"""

    houses_names_list: list[Houses]
    """Ordered list of houses names"""

    lunar_phase: LunarPhaseModel
    """Lunar phase model"""

    active_points: list[Union[Planet, AxialCusps]]
    """List of active points in the chart or aspects calculations."""

class EphemerisDictModel(SubscriptableBaseModel):
    date: str
    planets: list[KerykeionPointModel]
    houses: list[KerykeionPointModel]


class AspectModel(SubscriptableBaseModel):
    p1_name: str
    p1_owner: str
    p1_abs_pos: float
    p2_name: str
    p2_owner: str
    p2_abs_pos: float
    aspect: str
    orbit: float
    aspect_degrees: int
    diff: float
    p1: int
    p2: int


class ZodiacSignModel(SubscriptableBaseModel):
    sign: Sign
    quality: Quality
    element: Element
    emoji: SignsEmoji
    sign_num: SignNumbers


class RelationshipScoreAspectModel(SubscriptableBaseModel):
    p1_name: str
    p2_name: str
    aspect: str
    orbit: float


class RelationshipScoreModel(SubscriptableBaseModel):
    score_value: int
    score_description: RelationshipScoreDescription
    is_destiny_sign: bool
    aspects: list[RelationshipScoreAspectModel]
    subjects: list[AstrologicalSubjectModel]


class CompositeSubjectModel(SubscriptableBaseModel):
    """
    Pydantic Model for Composite Subject
    """

    # Data
    name: str
    first_subject: AstrologicalSubjectModel
    second_subject: AstrologicalSubjectModel
    composite_chart_type: str

    zodiac_type: ZodiacType
    sidereal_mode: Union[SiderealMode, None]
    houses_system_identifier: HousesSystemIdentifier
    houses_system_name: str
    perspective_type: PerspectiveType

    # Planets
    sun: KerykeionPointModel
    moon: KerykeionPointModel
    mercury: Optional[KerykeionPointModel] = None
    venus: Optional[KerykeionPointModel] = None
    mars: Optional[KerykeionPointModel] = None
    jupiter: Optional[KerykeionPointModel] = None
    saturn: Optional[KerykeionPointModel] = None
    uranus: Optional[KerykeionPointModel] = None
    neptune: Optional[KerykeionPointModel] = None
    pluto: Optional[KerykeionPointModel] = None

    # Axes
    ascendant: Optional[KerykeionPointModel] = None
    descendant: Optional[KerykeionPointModel] = None
    medium_coeli: Optional[KerykeionPointModel] = None
    imum_coeli: Optional[KerykeionPointModel] = None

    # Optional Planets:
    chiron: Optional[KerykeionPointModel] = None
    mean_lilith: Optional[KerykeionPointModel] = None

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
    mean_node: Optional[KerykeionPointModel] = None
    true_node: Optional[KerykeionPointModel] = None
    mean_south_node: Optional[KerykeionPointModel] = None
    true_south_node: Optional[KerykeionPointModel] = None

    planets_names_list: list[Planet]
    """Ordered list of available planets names"""

    axial_cusps_names_list: list[AxialCusps]
    """Ordered list of available axes names"""

    houses_names_list: list[Houses]
    """Ordered list of houses names"""

    lunar_phase: LunarPhaseModel
    """Lunar phase model"""

    active_points: list[Union[Planet, AxialCusps]]
    """List of active points in the chart or aspects calculations."""


class ActiveAspect(TypedDict):
    name: AspectName
    orb: int


class TransitMomentModel(SubscriptableBaseModel):
    """
    Model representing a snapshot of astrological transits at a specific moment in time.

    Captures all active aspects between moving celestial bodies and
    the fixed positions in a person's natal chart at a specific date and time.

    Attributes:
        date: ISO 8601 formatted date and time of the transit moment.
        aspects: List of astrological aspects active at this specific moment.
    """

    date: str
    """ISO 8601 formatted date and time of the transit moment."""

    aspects: list[AspectModel]
    """List of aspects active at this specific moment."""


class TransitsTimeRangeModel(SubscriptableBaseModel):
    """
    Model representing a collection of transit moments for an astrological subject.

    This model holds a time series of transit snapshots, allowing analysis of
    planetary movements and their aspects to a natal chart over a period of time.

    Attributes:
        transits: List of transit moments occurring during the specified time period.
        subject: The astrological subject model for whom the transits are calculated.
        dates: List of all dates in ISO 8601 format for which transits were calculated.
    """

    transits: list[TransitMomentModel]
    """List of transit moments."""

    subject: Optional[AstrologicalSubjectModel]
    """Astrological subject data."""

    dates: Optional[list[str]]
    """ISO 8601 formatted dates of all transit moments."""


class PlanetReturnModel(SubscriptableBaseModel):
    """
    Pydantic Model for Astrological Subject
    """
    name: str
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
    mercury: Optional[KerykeionPointModel] = None
    venus: Optional[KerykeionPointModel] = None
    mars: Optional[KerykeionPointModel] = None
    jupiter: Optional[KerykeionPointModel] = None
    saturn: Optional[KerykeionPointModel] = None
    uranus: Optional[KerykeionPointModel] = None
    neptune: Optional[KerykeionPointModel] = None
    pluto: Optional[KerykeionPointModel] = None

    # Axes
    ascendant: Optional[KerykeionPointModel] = None
    descendant: Optional[KerykeionPointModel] = None
    medium_coeli: Optional[KerykeionPointModel] = None
    imum_coeli: Optional[KerykeionPointModel] = None

    # Optional Planets:
    chiron: Optional[KerykeionPointModel] = None
    mean_lilith: Optional[KerykeionPointModel] = None

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
    mean_node: Optional[KerykeionPointModel] = None
    true_node: Optional[KerykeionPointModel] = None
    mean_south_node: Optional[KerykeionPointModel] = None
    true_south_node: Optional[KerykeionPointModel] = None

    planets_names_list: list[Planet]
    """Ordered list of available planets names"""

    axial_cusps_names_list: list[AxialCusps]
    """Ordered list of available axes names"""

    houses_names_list: list[Houses]
    """Ordered list of houses names"""

    lunar_phase: LunarPhaseModel
    """Lunar phase model"""

    active_points: list[Union[Planet, AxialCusps]]
    """List of active points in the chart or aspects calculations."""

