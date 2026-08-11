# -*- coding: utf-8 -*-
"""
Canonical home of all public Kerykeion models, literals and settings.

Every public Pydantic model in the package is importable from
``kerykeion.schemas``. Models defined in this package (``kr_models``,
``settings_models``, ...) are imported eagerly; models defined next to their
feature factory (lunations, eclipses, astro-cartography, ...) are re-exported
lazily via PEP 562 so that ``import kerykeion.schemas`` stays lightweight and
free of import cycles.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from importlib import import_module
from typing import TYPE_CHECKING

from .kerykeion_exception import KerykeionException
from .kr_literals import (
    ZodiacType,
    Sign,
    SignNumbers,
    AspectMovementType,
    MotionState,
    ClassicalPlanet,
    VocAspectName,
    VocTargetPlanet,
    Houses,
    HouseNumbers,
    AstrologicalPoint,
    Element,
    Quality,
    ChartType,
    PointType,
    LunarPhaseEmoji,
    LunarPhaseName,
    SiderealMode,
    HousesSystemIdentifier,
    PerspectiveType,
    SignsEmoji,
    KerykeionChartTheme,
    KerykeionChartStyle,
    KerykeionChartLanguage,
    RelationshipScoreDescription,
    CompositeChartType,
    AspectName,
    ReturnType,
    DominantMethod,
)
from .kr_models import (
    SubscriptableBaseModel,
    LunarPhaseModel,
    KerykeionPointModel,
    NutationObliquityModel,
    EphemerisWarningModel,
    PolarHouseFallbackModel,
    AstrologicalBaseModel,
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    PlanetReturnModel,
    EphemerisDictModel,
    AspectModel,
    ZodiacSignModel,
    RelationshipScoreAspectModel,
    ScoreBreakdownItemModel,
    RelationshipScoreModel,
    ActiveAspect,
    TransitMomentModel,
    TransitsTimeRangeModel,
    DominantScoreModel,
    DominantBreakdownItemModel,
    DominantsModel,
    TriplicityLordsModel,
    # Chart data
    AngularityModel,
    StelliumModel,
    ChartDataModel,
    SingleChartDataModel,
    DualChartDataModel,
    SingleChartAspectsModel,
    DualChartAspectsModel,
    ElementDistributionModel,
    QualityDistributionModel,
    # House comparison
    HouseComparisonModel,
    PointInHouseModel,
    # Transit events (time-range scan)
    TransitEventModel,
    TransitEventsTimeRangeModel,
    # Sun times / planetary hours
    SunTimesModel,
    PlanetaryHourModel,
    PlanetaryHoursModel,
    # Void of course Moon
    VoidOfCourseAspectModel,
    VoidOfCourseMoonModel,
    VoidOfCourseWindowModel,
    VoidOfCourseWindowsCollectionModel,
    # Planetary phenomena
    PlanetaryPhenomenaModel,
    PlanetaryPhenomenaCollectionModel,
    # Zodiacal releasing
    ZodiacalReleasingModel,
    ZRPeriodModel,
    # Annual profections
    ProfectionsModel,
    ProfectionYearModel,
    # Firdaria
    FirdariaModel,
    FirdariaPeriodModel,
    FirdariaSubPeriodModel,
    # Mutual receptions
    MutualReceptionModel,
    MutualReceptionsModel,
    # Horary indicators
    HoraryIndicatorsModel,
    HorarySignificatorModel,
    HoraryConsiderationModel,
    # Moon phase details
    MoonPhaseOverviewModel,
    MoonPhaseEclipseModel,
    MoonPhaseEventMomentModel,
    MoonPhaseEventsModel,
    MoonPhaseIlluminationDetailsModel,
    MoonPhaseLocationModel,
    MoonPhaseMajorPhaseWindowModel,
    MoonPhaseMoonDetailedModel,
    MoonPhaseMoonPositionModel,
    MoonPhaseMoonSummaryModel,
    MoonPhaseOptimalViewingPeriodModel,
    MoonPhaseSolarEclipseModel,
    MoonPhaseSunInfoModel,
    MoonPhaseSunPositionModel,
    MoonPhaseUpcomingPhasesModel,
    MoonPhaseViewingConditionsModel,
    MoonPhaseViewingEquipmentModel,
    MoonPhaseVisibilityModel,
    MoonPhaseZodiacModel,
)
from .chart_template_model import ChartTemplateModel
from .settings_models import (
    KerykeionSettingsModel,
    KerykeionSettingsCelestialPointModel,
    KerykeionLanguageCelestialPointModel,
    KerykeionLanguageModel,
)

# Public models defined next to their feature factory, re-exported here
# lazily (see __getattr__ below) to avoid import cycles and keep this
# package import light.
_FEATURE_MODEL_HOMES = {
    "LunationModel": "kerykeion.lunations.lunation_factory",
    "LunationsCollectionModel": "kerykeion.lunations.lunation_factory",
    "StationModel": "kerykeion.retrograde_stations.retrograde_station_factory",
    "RetrogradeStationsCollectionModel": "kerykeion.retrograde_stations.retrograde_station_factory",
    "IngressModel": "kerykeion.sign_ingresses.sign_ingress_factory",
    "SignIngressesCollectionModel": "kerykeion.sign_ingresses.sign_ingress_factory",
    "MundaneAspectModel": "kerykeion.mundane_aspects.factory",
    "MundaneAspectsCollectionModel": "kerykeion.mundane_aspects.factory",
    "MidpointModel": "kerykeion.midpoints.midpoint_factory",
    "MidpointAspectModel": "kerykeion.midpoints.midpoint_factory",
    "ProgressedPointModel": "kerykeion.secondary_progressions.secondary_progression_factory",
    "ProgressedToNatalAspectModel": "kerykeion.secondary_progressions.secondary_progression_factory",
    "SecondaryProgressionsResultModel": "kerykeion.secondary_progressions.secondary_progression_factory",
    "SolarArcDirectedAspectModel": "kerykeion.secondary_progressions.solar_arc_factory",
    "SolarArcDirectedPointModel": "kerykeion.secondary_progressions.solar_arc_factory",
    "SolarArcSubjectModel": "kerykeion.secondary_progressions.solar_arc_factory",
    "SolarEclipseModel": "kerykeion.eclipses.eclipse_factory",
    "LunarEclipseModel": "kerykeion.eclipses.eclipse_factory",
    "EclipseSearchResultModel": "kerykeion.eclipses.eclipse_factory",
    "OccultationModel": "kerykeion.occultations.occultation_factory",
    "HeliacalEventModel": "kerykeion.heliacal.heliacal_factory",
    "PlanetaryNodeModel": "kerykeion.planetary_nodes.nodes_factory",
    "PlanetaryNodesCollectionModel": "kerykeion.planetary_nodes.nodes_factory",
    "PrimaryDirectionModel": "kerykeion.primary_directions.directions_factory",
    "SpeculumEntryModel": "kerykeion.primary_directions.directions_factory",
    "ACGLineModel": "kerykeion.astro_cartography.acg_factory",
    "ACGLinePointModel": "kerykeion.astro_cartography.acg_factory",
    "FixedStarMetadataModel": "kerykeion.fixed_stars.catalog",
}

if TYPE_CHECKING:  # static analyzers see the lazy re-exports as plain imports
    from kerykeion.lunations.lunation_factory import LunationModel, LunationsCollectionModel
    from kerykeion.retrograde_stations.retrograde_station_factory import (
        StationModel,
        RetrogradeStationsCollectionModel,
    )
    from kerykeion.sign_ingresses.sign_ingress_factory import IngressModel, SignIngressesCollectionModel
    from kerykeion.mundane_aspects.factory import MundaneAspectModel, MundaneAspectsCollectionModel
    from kerykeion.midpoints.midpoint_factory import MidpointModel, MidpointAspectModel
    from kerykeion.secondary_progressions.secondary_progression_factory import (
        ProgressedPointModel,
        ProgressedToNatalAspectModel,
        SecondaryProgressionsResultModel,
    )
    from kerykeion.secondary_progressions.solar_arc_factory import (
        SolarArcDirectedAspectModel,
        SolarArcDirectedPointModel,
        SolarArcSubjectModel,
    )
    from kerykeion.eclipses.eclipse_factory import (
        SolarEclipseModel,
        LunarEclipseModel,
        EclipseSearchResultModel,
    )
    from kerykeion.occultations.occultation_factory import OccultationModel
    from kerykeion.heliacal.heliacal_factory import HeliacalEventModel
    from kerykeion.planetary_nodes.nodes_factory import PlanetaryNodeModel, PlanetaryNodesCollectionModel
    from kerykeion.primary_directions.directions_factory import PrimaryDirectionModel, SpeculumEntryModel
    from kerykeion.astro_cartography.acg_factory import ACGLineModel, ACGLinePointModel
    from kerykeion.fixed_stars.catalog import FixedStarMetadataModel


def __getattr__(name: str):
    if name in _FEATURE_MODEL_HOMES:
        value = getattr(import_module(_FEATURE_MODEL_HOMES[name]), name)
        globals()[name] = value  # cache so subsequent lookups skip __getattr__
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_FEATURE_MODEL_HOMES))


__all__ = [
    # Exceptions
    "KerykeionException",
    # Settings and Chart Types
    "ChartTemplateModel",
    "KerykeionSettingsModel",
    "KerykeionSettingsCelestialPointModel",
    "KerykeionLanguageCelestialPointModel",
    "KerykeionLanguageModel",
    # Main Literal Types (from kr_literals)
    "ZodiacType",
    "Sign",
    "SignNumbers",
    "AspectMovementType",
    "MotionState",
    "ClassicalPlanet",
    "VocAspectName",
    "VocTargetPlanet",
    "Houses",
    "HouseNumbers",
    "AstrologicalPoint",
    "Element",
    "Quality",
    "ChartType",
    "PointType",
    "LunarPhaseEmoji",
    "LunarPhaseName",
    "SiderealMode",
    "HousesSystemIdentifier",
    "PerspectiveType",
    "SignsEmoji",
    "KerykeionChartTheme",
    "KerykeionChartStyle",
    "KerykeionChartLanguage",
    "RelationshipScoreDescription",
    "CompositeChartType",
    "AspectName",
    "ReturnType",
    "DominantMethod",
    # Main Model Classes (from kr_models)
    "SubscriptableBaseModel",
    "LunarPhaseModel",
    "KerykeionPointModel",
    "EphemerisWarningModel",
    "PolarHouseFallbackModel",
    "AstrologicalBaseModel",
    "AstrologicalSubjectModel",
    "CompositeSubjectModel",
    "PlanetReturnModel",
    "EphemerisDictModel",
    "AspectModel",
    "ZodiacSignModel",
    "RelationshipScoreAspectModel",
    "ScoreBreakdownItemModel",
    "RelationshipScoreModel",
    "ActiveAspect",
    "NutationObliquityModel",
    "TransitMomentModel",
    "TransitsTimeRangeModel",
    "DominantScoreModel",
    "DominantBreakdownItemModel",
    "DominantsModel",
    "TriplicityLordsModel",
    # Chart data (from kr_models)
    "ChartDataModel",
    "AngularityModel",
    "StelliumModel",
    "SingleChartDataModel",
    "DualChartDataModel",
    "SingleChartAspectsModel",
    "DualChartAspectsModel",
    "ElementDistributionModel",
    "QualityDistributionModel",
    # House comparison (from kr_models)
    "HouseComparisonModel",
    "PointInHouseModel",
    # Transit events (from kr_models)
    "TransitEventModel",
    "TransitEventsTimeRangeModel",
    # Sun times / planetary hours (from kr_models)
    "SunTimesModel",
    "PlanetaryHourModel",
    "PlanetaryHoursModel",
    # Void of course Moon (from kr_models)
    "VoidOfCourseAspectModel",
    "VoidOfCourseMoonModel",
    "VoidOfCourseWindowModel",
    "VoidOfCourseWindowsCollectionModel",
    # Planetary phenomena (from kr_models)
    "PlanetaryPhenomenaModel",
    "PlanetaryPhenomenaCollectionModel",
    # Zodiacal releasing (from kr_models)
    "ZodiacalReleasingModel",
    "ZRPeriodModel",
    "ProfectionsModel",
    "ProfectionYearModel",
    "FirdariaModel",
    "FirdariaPeriodModel",
    "FirdariaSubPeriodModel",
    "MutualReceptionModel",
    "MutualReceptionsModel",
    "HoraryIndicatorsModel",
    "HorarySignificatorModel",
    "HoraryConsiderationModel",
    # Moon phase details (from kr_models)
    "MoonPhaseOverviewModel",
    "MoonPhaseEclipseModel",
    "MoonPhaseEventMomentModel",
    "MoonPhaseEventsModel",
    "MoonPhaseIlluminationDetailsModel",
    "MoonPhaseLocationModel",
    "MoonPhaseMajorPhaseWindowModel",
    "MoonPhaseMoonDetailedModel",
    "MoonPhaseMoonPositionModel",
    "MoonPhaseMoonSummaryModel",
    "MoonPhaseOptimalViewingPeriodModel",
    "MoonPhaseSolarEclipseModel",
    "MoonPhaseSunInfoModel",
    "MoonPhaseSunPositionModel",
    "MoonPhaseUpcomingPhasesModel",
    "MoonPhaseViewingConditionsModel",
    "MoonPhaseViewingEquipmentModel",
    "MoonPhaseVisibilityModel",
    "MoonPhaseZodiacModel",
    # Feature-module models (lazy re-exports, defined next to their factory)
    "LunationModel",
    "LunationsCollectionModel",
    "StationModel",
    "RetrogradeStationsCollectionModel",
    "IngressModel",
    "SignIngressesCollectionModel",
    "MundaneAspectModel",
    "MundaneAspectsCollectionModel",
    "MidpointModel",
    "MidpointAspectModel",
    "ProgressedPointModel",
    "ProgressedToNatalAspectModel",
    "SecondaryProgressionsResultModel",
    "SolarArcDirectedAspectModel",
    "SolarArcDirectedPointModel",
    "SolarArcSubjectModel",
    "SolarEclipseModel",
    "LunarEclipseModel",
    "EclipseSearchResultModel",
    "OccultationModel",
    "HeliacalEventModel",
    "PlanetaryNodeModel",
    "PlanetaryNodesCollectionModel",
    "PrimaryDirectionModel",
    "SpeculumEntryModel",
    "ACGLineModel",
    "ACGLinePointModel",
    "FixedStarMetadataModel",
]
