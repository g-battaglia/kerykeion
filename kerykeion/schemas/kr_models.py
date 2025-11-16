# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from typing import Union, Optional, List, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from kerykeion.schemas.kr_literals import AspectName

from kerykeion.schemas import (
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
    AspectMovementType
)
from kerykeion.schemas.kr_literals import ReturnType


class SubscriptableBaseModel(BaseModel):
    """
    Pydantic BaseModel with subscriptable support, so you can access the fields as if they were a dictionary.
    """

    def __getitem__(self, key):
        """Get an attribute using dictionary-style access."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Set an attribute using dictionary-style access."""
        setattr(self, key, value)

    def __delitem__(self, key):
        """Delete an attribute using dictionary-style access."""
        delattr(self, key)

    def get(self, key, default = None):
        """Get an attribute with a default value if not found."""
        return getattr(self, key, default)


class LunarPhaseModel(SubscriptableBaseModel):
    """
    Model representing lunar phase information.

    Attributes:
        degrees_between_s_m: Angular separation between Sun and Moon in degrees.
        moon_phase: Numerical phase identifier for the Moon.
        moon_emoji: Emoji representation of the lunar phase.
        moon_phase_name: Text name of the lunar phase.
    """
    degrees_between_s_m: Union[float, int]
    moon_phase: int
    moon_emoji: LunarPhaseEmoji
    moon_phase_name: LunarPhaseName


class KerykeionPointModel(SubscriptableBaseModel):
    """
    Model representing an astrological celestial point or house cusp.

    This model contains comprehensive information about celestial objects
    (planets, points) or house cusps including their zodiacal position,
    sign placement, and metadata.

    Attributes:
        name: The name of the celestial point or house.
        quality: Astrological quality (Cardinal, Fixed, Mutable).
        element: Astrological element (Fire, Earth, Air, Water).
        sign: The zodiac sign the point is located in.
        sign_num: Numerical identifier for the zodiac sign (0-11).
        position: Position within the sign (0-30 degrees).
        abs_pos: Absolute position in the zodiac (0-360 degrees).
        emoji: Unicode emoji representing the point or sign.
        point_type: Type of the celestial point (Planet, House, etc.).
        house: House placement of the point (optional).
        retrograde: Whether the point is in retrograde motion (optional).
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
    speed: Optional[float] = None
    declination: Optional[float] = None


class AstrologicalBaseModel(SubscriptableBaseModel):
    """
    Base model containing common fields for all astrological subjects.

    This model serves as the foundation for all astrological chart types,
    providing standard location, time, and configuration data. It supports
    both complete charts (with full location/time data) and composite charts
    (where some fields may be optional).

    Attributes:
        name: Subject identifier or name.
        city: Location city (optional for composite charts).
        nation: Country code (optional for composite charts).
        lng: Longitude coordinate (optional for composite charts).
        lat: Latitude coordinate (optional for composite charts).
        tz_str: Timezone string (optional for composite charts).
        iso_formatted_local_datetime: Local datetime in ISO format (optional).
        iso_formatted_utc_datetime: UTC datetime in ISO format (optional).
        julian_day: Julian day number for astronomical calculations (optional).
        day_of_week: Day of the week (optional).
        zodiac_type: Type of zodiac system used (Tropical or Sidereal).
        sidereal_mode: Sidereal calculation mode (if applicable).
        houses_system_identifier: House system used for calculations.
        perspective_type: Astrological perspective (geocentric, heliocentric, etc.).
        active_points: List of celestial points included in calculations.
    """
    # Common identification data
    name: str

    # Common location data (optional for composite charts)
    city: Optional[str] = None
    nation: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
    tz_str: Optional[str] = None

    # Common time data (optional for composite charts)
    iso_formatted_local_datetime: Optional[str] = None
    iso_formatted_utc_datetime: Optional[str] = None
    julian_day: Optional[float] = None
    day_of_week: Optional[str] = None

    # Common configuration
    zodiac_type: ZodiacType
    sidereal_mode: Union[SiderealMode, None]
    houses_system_identifier: HousesSystemIdentifier
    houses_system_name: str
    perspective_type: PerspectiveType

    # Common celestial points
    # Main planets (all optional to support selective calculations)
    sun: Optional[KerykeionPointModel] = None
    moon: Optional[KerykeionPointModel] = None
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

    # Lunar Nodes
    mean_north_lunar_node: Optional[KerykeionPointModel] = None
    true_north_lunar_node: Optional[KerykeionPointModel] = None
    mean_south_lunar_node: Optional[KerykeionPointModel] = None
    true_south_lunar_node: Optional[KerykeionPointModel] = None

    # Common lists and settings
    houses_names_list: List[Houses] = Field(description="Ordered list of houses names")
    active_points: List[AstrologicalPoint] = Field(description="List of active points in the chart or aspects calculations.")

    # Common lunar phase data (optional)
    lunar_phase: Optional[LunarPhaseModel] = Field(default=None, description="Lunar phase model")


class AstrologicalSubjectModel(AstrologicalBaseModel):
    """
    Pydantic Model for Astrological Subject
    """
    # Override base model to make location and time data required for subjects
    city: str
    nation: str
    lng: float
    lat: float
    tz_str: str
    iso_formatted_local_datetime: str
    iso_formatted_utc_datetime: str
    julian_day: float
    day_of_week: str

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
    aspect_movement: AspectMovementType = Field(
        description="Indicates whether the aspect is applying (orb decreasing), "
                    "separating (orb increasing), or fixed (no relative motion)."
    )


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


class SingleChartAspectsModel(SubscriptableBaseModel):
    """
    Model representing all aspects within a single astrological chart.

    This model can be used for any type of single chart analysis including:
    - Natal charts
    - Planetary return charts
    - Composite charts
    - Any other single chart type

    Contains the filtered and relevant aspects for the astrological subject
    based on configured orb settings.
    """
    subject: Union["AstrologicalSubjectModel", "CompositeSubjectModel", "PlanetReturnModel"] = Field(description="The astrological subject for which aspects were calculated.")
    aspects: List[AspectModel] = Field(description="List of calculated aspects within the chart, filtered based on orb settings.")
    active_points: List[AstrologicalPoint] = Field(description="List of active points used in the calculation.")
    active_aspects: List["ActiveAspect"] = Field(description="List of active aspects with their orb settings.")


class DualChartAspectsModel(SubscriptableBaseModel):
    """
    Model representing all aspects between two astrological charts.

    This model can be used for any type of dual chart analysis including:
    - Synastry (relationship compatibility)
    - Transit comparisons
    - Composite vs natal comparisons
    - Any other dual chart comparison

    Contains the filtered and relevant aspects between the two charts
    based on configured orb settings.
    """
    first_subject: Union["AstrologicalSubjectModel", "CompositeSubjectModel", "PlanetReturnModel"] = Field(description="The first astrological subject.")
    second_subject: Union["AstrologicalSubjectModel", "CompositeSubjectModel", "PlanetReturnModel"] = Field(description="The second astrological subject.")
    aspects: List[AspectModel] = Field(description="List of calculated aspects between the two charts, filtered based on orb settings.")
    active_points: List[AstrologicalPoint] = Field(description="List of active points used in the calculation.")
    active_aspects: List["ActiveAspect"] = Field(description="List of active aspects with their orb settings.")


# Legacy aliases for backward compatibility
NatalAspectsModel = SingleChartAspectsModel
SynastryAspectsModel = DualChartAspectsModel


class TransitsTimeRangeModel(SubscriptableBaseModel):
    """
    Model representing a collection of transit moments for an astrological subject.

    This model holds a time series of transit snapshots, allowing analysis of
    planetary movements and their aspects to a natal chart over a period of time.
    """
    transits: List[TransitMomentModel] = Field(description="List of transit moments.")
    subject: Optional[AstrologicalSubjectModel] = Field(description="Astrological subject data.")
    dates: Optional[List[str]] = Field(description="ISO 8601 formatted dates of all transit moments.")


class PointInHouseModel(SubscriptableBaseModel):
    """
    Represents an astrological point from one subject positioned within another subject's house.

    Captures point characteristics and its placement within the target subject's house system
    for house comparison analysis.

    Attributes:
        point_name: Name of the astrological point
        point_degree: Degree position within its sign
        point_sign: Zodiacal sign containing the point
        point_owner_name: Name of the subject who owns this point
        point_owner_house_number: House number in owner's chart
        point_owner_house_name: House name in owner's chart
        projected_house_number: House number in target subject's chart
        projected_house_name: House name in target subject's chart
        projected_house_owner_name: Name of the target subject
    """

    point_name: str
    """Name of the astrological point"""
    point_degree: float
    """Degree position of the point within its zodiacal sign"""
    point_sign: str
    """Zodiacal sign containing the point"""
    point_owner_name: str
    """Name of the subject who owns this point"""
    point_owner_house_number: Optional[int]
    """House number in owner's chart"""
    point_owner_house_name: Optional[str]
    """House name in owner's chart"""
    projected_house_number: int
    """House number in target subject's chart"""
    projected_house_name: str
    """House name in target subject's chart"""
    projected_house_owner_name: str
    """Name of the target subject"""


class HouseComparisonModel(SubscriptableBaseModel):
    """
    Bidirectional house comparison analysis between two astrological subjects.

    Contains results of how astrological points from each subject interact with
    the house system of the other subject.

    Attributes:
        first_subject_name: Name of the first subject
        second_subject_name: Name of the second subject
        first_points_in_second_houses: First subject's points in second subject's houses
        second_points_in_first_houses: Second subject's points in first subject's houses
    """

    first_subject_name: str
    """Name of the first subject"""
    second_subject_name: str
    """Name of the second subject"""
    first_points_in_second_houses: List[PointInHouseModel]
    """First subject's points positioned in second subject's houses"""
    second_points_in_first_houses: List[PointInHouseModel]
    """Second subject's points positioned in first subject's houses"""


class ElementDistributionModel(SubscriptableBaseModel):
    """
    Model representing element distribution in a chart.

    Attributes:
        fire: Fire element points total
        earth: Earth element points total
        air: Air element points total
        water: Water element points total
        fire_percentage: Fire element percentage
        earth_percentage: Earth element percentage
        air_percentage: Air element percentage
        water_percentage: Water element percentage
    """
    fire: float
    earth: float
    air: float
    water: float
    fire_percentage: int
    earth_percentage: int
    air_percentage: int
    water_percentage: int


class QualityDistributionModel(SubscriptableBaseModel):
    """
    Model representing quality distribution in a chart.

    Attributes:
        cardinal: Cardinal quality points total
        fixed: Fixed quality points total
        mutable: Mutable quality points total
        cardinal_percentage: Cardinal quality percentage
        fixed_percentage: Fixed quality percentage
        mutable_percentage: Mutable quality percentage
    """
    cardinal: float
    fixed: float
    mutable: float
    cardinal_percentage: int
    fixed_percentage: int
    mutable_percentage: int


class SingleChartDataModel(SubscriptableBaseModel):
    """
    Chart data model for single-subject astrological charts.

    This model contains all pure data from single-subject charts including planetary
    positions, internal aspects, element/quality distributions, and location data.
    Used for chart types that analyze a single astrological subject.

    Supported chart types:
    - Natal: Birth chart with internal planetary aspects
    - Composite: Midpoint relationship chart with internal aspects
    - SingleReturnChart: Single planetary return with internal aspects

    Attributes:
        chart_type: Type of single chart (Natal, Composite, SingleReturnChart)
        subject: The astrological subject being analyzed
        aspects: Internal aspects within the chart
        element_distribution: Distribution of elemental energies
        quality_distribution: Distribution of modal qualities
        active_points: Celestial points included in calculations
        active_aspects: Aspect types and orb settings used
    """

    # Chart identification
    chart_type: Literal["Natal", "Composite", "SingleReturnChart"]

    # Single chart subject
    subject: Union["AstrologicalSubjectModel", "CompositeSubjectModel", "PlanetReturnModel"]

    # Internal aspects analysis
    aspects: List[AspectModel]

    # Element and quality distributions
    element_distribution: "ElementDistributionModel"
    quality_distribution: "QualityDistributionModel"

    # Configuration and metadata
    active_points: List[AstrologicalPoint]
    active_aspects: List["ActiveAspect"]


class DualChartDataModel(SubscriptableBaseModel):
    """
    Chart data model for dual-subject astrological charts.

    This model contains all pure data from dual-subject charts including both subjects,
    inter-chart aspects, house comparisons, relationship analysis, and combined
    element/quality distributions. Used for chart types that compare or overlay
    two astrological subjects.

    Supported chart types:
    - Transit: Natal chart with current planetary transits
    - Synastry: Relationship compatibility between two people
    - Return: Natal chart with planetary return comparison

    Attributes:
        chart_type: Type of dual chart (Transit, Synastry, Return)
        first_subject: Primary astrological subject (natal, base chart)
        second_subject: Secondary astrological subject (transit, partner, return)
        aspects: Inter-chart aspects between the two subjects
        house_comparison: House overlay analysis between subjects
        relationship_score: Compatibility scoring (synastry only)
        element_distribution: Combined elemental distribution
        quality_distribution: Combined modal distribution
        active_points: Celestial points included in calculations
        active_aspects: Aspect types and orb settings used
    """

    # Chart identification
    chart_type: Literal["Transit", "Synastry", "DualReturnChart"]

    # Dual chart subjects
    first_subject: Union["AstrologicalSubjectModel", "CompositeSubjectModel", "PlanetReturnModel"]
    second_subject: Union["AstrologicalSubjectModel", "PlanetReturnModel"]

    # Inter-chart aspects analysis
    aspects: List[AspectModel]

    # House comparison analysis
    house_comparison: Optional["HouseComparisonModel"] = None

    # Relationship analysis (synastry only)
    relationship_score: Optional["RelationshipScoreModel"] = None

    # Combined element and quality distributions
    element_distribution: "ElementDistributionModel"
    quality_distribution: "QualityDistributionModel"

    # Configuration and metadata
    active_points: List[AstrologicalPoint]
    active_aspects: List["ActiveAspect"]


# Union type for all chart data models
ChartDataModel = Union[SingleChartDataModel, DualChartDataModel]
