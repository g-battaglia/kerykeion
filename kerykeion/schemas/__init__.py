# -*- coding: utf-8 -*-
"""
Canonical home of all public Kerykeion models, literals and settings.

Every public Pydantic model in the package is importable from
``kerykeion.schemas``. Models defined in this package (``models``,
``settings_models``, ...) are imported eagerly; models defined next to their
feature factory (lunations, eclipses, astro-cartography, ...) are re-exported
lazily via PEP 562 so that ``import kerykeion.schemas`` stays lightweight and
free of import cycles.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from importlib import import_module
from typing import TYPE_CHECKING

from .exceptions import KerykeionException
from .literals import (
    ZodiacType,
    Sign,
    SIGN_CODES,
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
    LunarPhaseStage,
    SiderealMode,
    HousesSystemIdentifier,
    PerspectiveType,
    SignsEmoji,
    KerykeionChartTheme,
    KerykeionChartStyle,
    KerykeionGlyphSize,
    KerykeionChartLanguage,
    RelationshipScoreDescription,
    CompositeChartType,
    CompositeHouseAnchor,
    CompositeHouseFrame,
    AspectName,
    ReturnType,
    DominantMethod,
    SolarPhase,
    ApsisKind,
)
from .models import (
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
    SolarPhaseThresholdsModel,
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
    "LunationModel": "kerykeion.lunations.factory",
    "LunationsCollectionModel": "kerykeion.lunations.factory",
    "StationModel": "kerykeion.retrograde_stations.factory",
    "RetrogradeStationsCollectionModel": "kerykeion.retrograde_stations.factory",
    "RetrogradePeriodModel": "kerykeion.retrograde_stations.factory",
    "RetrogradePeriodsCollectionModel": "kerykeion.retrograde_stations.factory",
    "IngressModel": "kerykeion.sign_ingresses.factory",
    "SignIngressesCollectionModel": "kerykeion.sign_ingresses.factory",
    "SignPeriodModel": "kerykeion.sign_ingresses.factory",
    "SignPeriodsCollectionModel": "kerykeion.sign_ingresses.factory",
    "MundaneAspectModel": "kerykeion.mundane_aspects.factory",
    "MundaneAspectsCollectionModel": "kerykeion.mundane_aspects.factory",
    "MidpointModel": "kerykeion.midpoints.factory",
    "MidpointAspectModel": "kerykeion.midpoints.factory",
    "ProgressedPointModel": "kerykeion.secondary_progressions.factory",
    "ProgressedToNatalAspectModel": "kerykeion.secondary_progressions.factory",
    "SecondaryProgressionsResultModel": "kerykeion.secondary_progressions.factory",
    "SolarArcDirectedAspectModel": "kerykeion.secondary_progressions.solar_arc",
    "SolarArcDirectedPointModel": "kerykeion.secondary_progressions.solar_arc",
    "SolarArcSubjectModel": "kerykeion.secondary_progressions.solar_arc",
    "SolarEclipseModel": "kerykeion.eclipses.factory",
    "LunarEclipseModel": "kerykeion.eclipses.factory",
    "EclipseSearchResultModel": "kerykeion.eclipses.factory",
    "OccultationModel": "kerykeion.occultations.factory",
    "HeliacalEventModel": "kerykeion.heliacal.factory",
    "PlanetaryNodeModel": "kerykeion.planetary_nodes.factory",
    "PlanetaryNodesCollectionModel": "kerykeion.planetary_nodes.factory",
    "PrimaryDirectionModel": "kerykeion.primary_directions.factory",
    "SpeculumEntryModel": "kerykeion.primary_directions.factory",
    "ACGLineModel": "kerykeion.astro_cartography.factory",
    "ACGLinePointModel": "kerykeion.astro_cartography.factory",
    "FixedStarMetadataModel": "kerykeion.fixed_stars.catalog",
}

if TYPE_CHECKING:  # static analyzers see the lazy re-exports as plain imports
    from kerykeion.lunations.factory import LunationModel, LunationsCollectionModel
    from kerykeion.retrograde_stations.factory import (
        StationModel,
        RetrogradeStationsCollectionModel,
        RetrogradePeriodModel,
        RetrogradePeriodsCollectionModel,
    )
    from kerykeion.sign_ingresses.factory import (
        IngressModel,
        SignIngressesCollectionModel,
        SignPeriodModel,
        SignPeriodsCollectionModel,
    )
    from kerykeion.mundane_aspects.factory import MundaneAspectModel, MundaneAspectsCollectionModel
    from kerykeion.midpoints.factory import MidpointModel, MidpointAspectModel
    from kerykeion.secondary_progressions.factory import (
        ProgressedPointModel,
        ProgressedToNatalAspectModel,
        SecondaryProgressionsResultModel,
    )
    from kerykeion.secondary_progressions.solar_arc import (
        SolarArcDirectedAspectModel,
        SolarArcDirectedPointModel,
        SolarArcSubjectModel,
    )
    from kerykeion.eclipses.factory import (
        SolarEclipseModel,
        LunarEclipseModel,
        EclipseSearchResultModel,
    )
    from kerykeion.occultations.factory import OccultationModel
    from kerykeion.heliacal.factory import HeliacalEventModel
    from kerykeion.planetary_nodes.factory import PlanetaryNodeModel, PlanetaryNodesCollectionModel
    from kerykeion.primary_directions.factory import PrimaryDirectionModel, SpeculumEntryModel
    from kerykeion.astro_cartography.factory import ACGLineModel, ACGLinePointModel
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
    # Main Literal Types (from literals)
    "ZodiacType",
    "Sign",
    "SIGN_CODES",
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
    "LunarPhaseStage",
    "SiderealMode",
    "HousesSystemIdentifier",
    "PerspectiveType",
    "SignsEmoji",
    "KerykeionChartTheme",
    "KerykeionChartStyle",
    "KerykeionGlyphSize",
    "KerykeionChartLanguage",
    "RelationshipScoreDescription",
    "CompositeChartType",
    "CompositeHouseAnchor",
    "CompositeHouseFrame",
    "AspectName",
    "ReturnType",
    "DominantMethod",
    # Main Model Classes (from models)
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
    # Chart data (from models)
    "ChartDataModel",
    "AngularityModel",
    "StelliumModel",
    "SingleChartDataModel",
    "DualChartDataModel",
    "SingleChartAspectsModel",
    "DualChartAspectsModel",
    "ElementDistributionModel",
    "QualityDistributionModel",
    # House comparison (from models)
    "HouseComparisonModel",
    "PointInHouseModel",
    # Transit events (from models)
    "TransitEventModel",
    "TransitEventsTimeRangeModel",
    # Sun times / planetary hours (from models)
    "SunTimesModel",
    "PlanetaryHourModel",
    "PlanetaryHoursModel",
    # Void of course Moon (from models)
    "VoidOfCourseAspectModel",
    "VoidOfCourseMoonModel",
    "VoidOfCourseWindowModel",
    "VoidOfCourseWindowsCollectionModel",
    # Planetary phenomena (from models)
    "SolarPhase",
    "SolarPhaseThresholdsModel",
    "ApsisKind",
    "PlanetaryPhenomenaModel",
    "PlanetaryPhenomenaCollectionModel",
    # Zodiacal releasing (from models)
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
    # Moon phase details (from models)
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
    "RetrogradePeriodModel",
    "RetrogradePeriodsCollectionModel",
    "IngressModel",
    "SignIngressesCollectionModel",
    "SignPeriodModel",
    "SignPeriodsCollectionModel",
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
