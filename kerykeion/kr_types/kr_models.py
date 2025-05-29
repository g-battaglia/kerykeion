# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from typing import Union, Optional, List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from kerykeion.kr_types.kr_literals import AspectName

from kerykeion.kr_types import (
    LunarPhaseEmoji,
    LunarPhaseName,
    AstrologicalPoint,
    Houses,
    Quality,
    Element,
    Sign,
    ZodiacType,
    SignNumbers,
    PointType,
    SiderealMode,
    HousesSystemIdentifier,
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

    name: Union[AstrologicalPoint, Houses]
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


class AstrologicalBaseModel(SubscriptableBaseModel):
    """
    Base Model with common fields for all astrological subjects
    """
    # Common identification data
    name: str

    # Common location data
    city: str
    nation: str
    lng: float
    lat: float
    tz_str: str

    # Common time data
    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str
    julian_day: float
    day_of_week: str

    # Common configuration
    zodiac_type: ZodiacType
    sidereal_mode: Union[SiderealMode, None]
    houses_system_identifier: HousesSystemIdentifier
    houses_system_name: str
    perspective_type: PerspectiveType

    # Common celestial points
    # Main planets
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

    # Common axes
    ascendant: Optional[KerykeionPointModel] = None
    descendant: Optional[KerykeionPointModel] = None
    medium_coeli: Optional[KerykeionPointModel] = None
    imum_coeli: Optional[KerykeionPointModel] = None

    # Common optional planets
    chiron: Optional[KerykeionPointModel] = None
    earth: Optional[KerykeionPointModel] = None
    pholus: Optional[KerykeionPointModel] = None

    # Lilith Points
    mean_lilith: Optional[KerykeionPointModel] = None
    true_lilith: Optional[KerykeionPointModel] = None

    # Asteroids
    ceres: Optional[KerykeionPointModel] = None
    pallas: Optional[KerykeionPointModel] = None
    juno: Optional[KerykeionPointModel] = None
    vesta: Optional[KerykeionPointModel] = None

    # Trans-Neptunian Objects
    eris: Optional[KerykeionPointModel] = None
    sedna: Optional[KerykeionPointModel] = None
    haumea: Optional[KerykeionPointModel] = None
    makemake: Optional[KerykeionPointModel] = None
    ixion: Optional[KerykeionPointModel] = None
    orcus: Optional[KerykeionPointModel] = None
    quaoar: Optional[KerykeionPointModel] = None

    # Fixed Stars
    regulus: Optional[KerykeionPointModel] = None
    spica: Optional[KerykeionPointModel] = None

    # Arabic Parts
    pars_fortunae: Optional[KerykeionPointModel] = None
    pars_spiritus: Optional[KerykeionPointModel] = None
    pars_amoris: Optional[KerykeionPointModel] = None
    pars_fidei: Optional[KerykeionPointModel] = None

    # Special Points
    vertex: Optional[KerykeionPointModel] = None
    anti_vertex: Optional[KerykeionPointModel] = None

    # Common houses
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

    # Common nodes
    mean_node: Optional[KerykeionPointModel] = None
    true_node: Optional[KerykeionPointModel] = None
    mean_south_node: Optional[KerykeionPointModel] = None
    true_south_node: Optional[KerykeionPointModel] = None

    # Common lists and settings
    houses_names_list: List[Houses] = Field(description="Ordered list of houses names")
    active_points: List[AstrologicalPoint] = Field(description="List of active points in the chart or aspects calculations.")

    # Common lunar phase data
    lunar_phase: LunarPhaseModel = Field(description="Lunar phase model")


class AstrologicalSubjectModel(AstrologicalBaseModel):
    """
    Pydantic Model for Astrological Subject
    """
    # Specific birth/event data
    year: int
    month: int
    day: int
    hour: int
    minute: int


class CompositeSubjectModel(AstrologicalBaseModel):
    """
    Pydantic Model for Composite Subject
    """
    # Specific composite data
    first_subject: AstrologicalSubjectModel
    second_subject: AstrologicalSubjectModel
    composite_chart_type: str


class PlanetReturnModel(AstrologicalBaseModel):
    """
    Pydantic Model for Planet Return
    """
    # Specific return data
    return_type: ReturnType = Field(description="Type of return: Solar or Lunar")


class EphemerisDictModel(SubscriptableBaseModel):
    date: str
    planets: List[KerykeionPointModel]
    houses: List[KerykeionPointModel]


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
    aspects: List[RelationshipScoreAspectModel]
    subjects: List[AstrologicalSubjectModel]


class ActiveAspect(TypedDict):
    name: AspectName
    orb: int


class TransitMomentModel(SubscriptableBaseModel):
    """
    Model representing a snapshot of astrological transits at a specific moment in time.

    Captures all active aspects between moving celestial bodies and
    the fixed positions in a person's natal chart at a specific date and time.
    """
    date: str = Field(description="ISO 8601 formatted date and time of the transit moment.")
    aspects: List[AspectModel] = Field(description="List of aspects active at this specific moment.")


class TransitsTimeRangeModel(SubscriptableBaseModel):
    """
    Model representing a collection of transit moments for an astrological subject.

    This model holds a time series of transit snapshots, allowing analysis of
    planetary movements and their aspects to a natal chart over a period of time.
    """
    transits: List[TransitMomentModel] = Field(description="List of transit moments.")
    subject: Optional[AstrologicalSubjectModel] = Field(description="Astrological subject data.")
    dates: Optional[List[str]] = Field(description="ISO 8601 formatted dates of all transit moments.")
