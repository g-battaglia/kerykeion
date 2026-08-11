# -*- coding: utf-8 -*-
"""
Kerykeion - A Python Library for Astrology
==========================================

Kerykeion is a comprehensive astrology library that provides tools for:

- **Birth Chart Calculations**: Calculate planetary positions, houses, and aspects
- **Chart Visualization**: Generate beautiful SVG charts (natal, synastry, transit)
- **Compatibility Analysis**: Calculate relationship scores and synastry aspects
- **Planetary Returns**: Compute solar and lunar return charts
- **Transit Analysis**: Track planetary transits over time ranges
- **Composite Charts**: Generate midpoint composite charts
- **Predictive Techniques**: Secondary progressions, solar arc, primary directions, midpoints
- **Advanced Astronomy**: Eclipses, heliacal events, occultations, planetary phenomena
- **Astro-Cartography**: Planetary angular lines across the globe

Quick Start
-----------
>>> from kerykeion import AstrologicalSubjectFactory
>>> subject = AstrologicalSubjectFactory.from_birth_data(
...     "John", 1990, 1, 1, 12, 0,
...     city="Rome",
...     nation="IT",
...     lng=12.4964,
...     lat=41.9028,
...     tz_str="Europe/Rome",
...     online=False,
... )
>>> print(subject.sun.sign)  # Get Sun sign
>>> print(subject.ascendant.sign)  # Get Ascendant

Main Classes
------------
- AstrologicalSubjectFactory: Create astrological subjects (recommended)
- ChartDrawer: Generate SVG chart visualizations
- AspectsFactory: Calculate planetary aspects
- RelationshipScoreFactory: Calculate compatibility scores
- CompositeSubjectFactory: Create composite charts
- PlanetaryReturnFactory: Calculate solar/lunar returns
- TransitsTimeRangeFactory: Track transits over time
- SecondaryProgressionFactory: Day-for-a-year progressions
- SolarArcFactory: Solar arc directions
- PrimaryDirectionsFactory: Placidus semi-arc primary directions
- MidpointFactory: Cosmobiology midpoint analysis
- EclipseFactory: Solar and lunar eclipse search
- AstroCartographyFactory: ACG planetary lines

.. include:: ../README.md

This is part of Kerykeion (C) 2025-2026 Giacomo Battaglia
"""

from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _package_version

try:
    __version__ = _package_version("kerykeion")
except _PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0.0.0"

# =============================================================================
# CORE FACTORIES
# =============================================================================
from .astrological_subject_factory import AstrologicalSubjectFactory
from .composite_subject import CompositeSubjectFactory
from .planetary_returns import PlanetaryReturnFactory
from .chart_data import ChartDataFactory
from .ephemeris_data import EphemerisDataFactory
from .transits import TransitsTimeRangeFactory
from .moon_phase_details import MoonPhaseDetailsFactory
from .sun_times import SunTimesFactory
from .planetary_hours import PlanetaryHoursFactory
from .void_of_course_moon import VoidOfCourseMoonFactory

# =============================================================================
# STANDALONE FACTORIES
# =============================================================================
from .planetary_phenomena import PlanetaryPhenomenaFactory
from .eclipses import (
    EclipseFactory,
    EclipseSearchResultModel,
    LunarEclipseModel,
    SolarEclipseModel,
)
from .lunations import LunationFinderFactory, LunationModel, LunationsCollectionModel
from .retrograde_stations import (
    RetrogradeStationFactory,
    StationModel,
    RetrogradeStationsCollectionModel,
)
from .sign_ingresses import (
    SignIngressFactory,
    IngressModel,
    SignIngressesCollectionModel,
)
from .mundane_aspects import (
    MundaneAspectFactory,
    MundaneAspectModel,
    MundaneAspectsCollectionModel,
)
from .planetary_nodes import PlanetaryNodesFactory, PlanetaryNodeModel, PlanetaryNodesCollectionModel
from .heliacal import HeliacalFactory, HeliacalEventModel
from .occultations import OccultationFactory, OccultationModel
from .relocated_chart import RelocatedChartFactory
from .fixed_stars import FixedStarDiscoveryFactory, FixedStarMetadataModel
from .primary_directions import PrimaryDirectionsFactory, PrimaryDirectionModel, SpeculumEntryModel
from .astro_cartography import AstroCartographyFactory, ACGLineModel, ACGLinePointModel
from .midpoints import MidpointFactory, MidpointModel, MidpointAspectModel
from .secondary_progressions import (
    ProgressedPointModel,
    ProgressedToNatalAspectModel,
    SecondaryProgressionFactory,
    SecondaryProgressionsResultModel,
    SolarArcFactory,
    SolarArcDirectedAspectModel,
    SolarArcSubjectModel,
    SolarArcDirectedPointModel,
)

# =============================================================================
# ANALYSIS FACTORIES
# =============================================================================
from .aspects import AspectsFactory
from .relationship_score import RelationshipScoreFactory
from .house_comparison import HouseComparisonFactory
from .dominants import DominantsFactory, DominantStrategy, BaseDominantStrategy
from .zodiacal_releasing import ZodiacalReleasingFactory
from .profections import ProfectionsFactory
from .firdaria import FirdariaFactory
from .receptions import MutualReceptionsFactory
from .horary import HoraryIndicatorsFactory

# =============================================================================
# VISUALIZATION
# =============================================================================
from .charts import ChartDrawer
from .report import ReportGenerator

# =============================================================================
# DATA MODELS
# =============================================================================
from .schemas import KerykeionException
from .schemas.models import (
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    KerykeionPointModel,
    EphemerisWarningModel,
    AspectModel,
    MoonPhaseOverviewModel,
    ChartDataModel,
    AngularityModel,
    StelliumModel,
    SingleChartDataModel,
    DualChartDataModel,
    SingleChartAspectsModel,
    DualChartAspectsModel,
    ElementDistributionModel,
    QualityDistributionModel,
    HouseComparisonModel,
    PlanetReturnModel,
    TransitEventModel,
    TransitEventsTimeRangeModel,
    TransitsTimeRangeModel,
    PlanetaryPhenomenaModel,
    PlanetaryPhenomenaCollectionModel,
    SunTimesModel,
    PlanetaryHourModel,
    PlanetaryHoursModel,
    VoidOfCourseAspectModel,
    VoidOfCourseMoonModel,
    VoidOfCourseWindowModel,
    VoidOfCourseWindowsCollectionModel,
    DominantsModel,
    DominantScoreModel,
    DominantBreakdownItemModel,
    TriplicityLordsModel,
    ZodiacalReleasingModel,
    ZRPeriodModel,
    ProfectionsModel,
    ProfectionYearModel,
    FirdariaModel,
    FirdariaPeriodModel,
    FirdariaSubPeriodModel,
    MutualReceptionModel,
    MutualReceptionsModel,
    HoraryIndicatorsModel,
    HorarySignificatorModel,
    HoraryConsiderationModel,
    RelationshipScoreModel,
    EphemerisDictModel,
)
from .schemas.literals import DominantMethod

# =============================================================================
# SETTINGS AND UTILITIES
# =============================================================================
from .settings import KerykeionSettingsModel
from .context import to_context
from ._predictive_utils import PTOLEMAIC_ASPECTS

# =============================================================================
# EPHEMERIS BACKEND
# =============================================================================
from .ephemeris_backend import BACKEND_NAME


__all__ = [
    # Core Factories
    "AstrologicalSubjectFactory",
    "CompositeSubjectFactory",
    "PlanetaryReturnFactory",
    "ChartDataFactory",
    "EphemerisDataFactory",
    "TransitsTimeRangeFactory",
    "MoonPhaseDetailsFactory",
    "SunTimesFactory",
    "PlanetaryHoursFactory",
    "VoidOfCourseMoonFactory",
    # Standalone Factories
    "PlanetaryPhenomenaFactory",
    "EclipseFactory",
    "EclipseSearchResultModel",
    "SolarEclipseModel",
    "LunarEclipseModel",
    "LunationFinderFactory",
    "LunationModel",
    "LunationsCollectionModel",
    "RetrogradeStationFactory",
    "StationModel",
    "RetrogradeStationsCollectionModel",
    "SignIngressFactory",
    "IngressModel",
    "SignIngressesCollectionModel",
    "MundaneAspectFactory",
    "MundaneAspectModel",
    "MundaneAspectsCollectionModel",
    "PlanetaryNodesFactory",
    "PlanetaryNodeModel",
    "PlanetaryNodesCollectionModel",
    "HeliacalFactory",
    "HeliacalEventModel",
    "OccultationFactory",
    "OccultationModel",
    "RelocatedChartFactory",
    "FixedStarDiscoveryFactory",
    "FixedStarMetadataModel",
    "PrimaryDirectionsFactory",
    "PrimaryDirectionModel",
    "SpeculumEntryModel",
    "AstroCartographyFactory",
    "ACGLineModel",
    "ACGLinePointModel",
    "MidpointFactory",
    "MidpointModel",
    "MidpointAspectModel",
    "ProgressedPointModel",
    "ProgressedToNatalAspectModel",
    "SecondaryProgressionFactory",
    "SecondaryProgressionsResultModel",
    "SolarArcFactory",
    "SolarArcDirectedAspectModel",
    "SolarArcDirectedPointModel",
    "SolarArcSubjectModel",
    # Analysis Factories
    "AspectsFactory",
    "RelationshipScoreFactory",
    "HouseComparisonFactory",
    "DominantsFactory",
    "DominantStrategy",
    "BaseDominantStrategy",
    "ZodiacalReleasingFactory",
    "ProfectionsFactory",
    "FirdariaFactory",
    "MutualReceptionsFactory",
    "HoraryIndicatorsFactory",
    # Visualization
    "ChartDrawer",
    "ReportGenerator",
    # Data Models
    "KerykeionException",
    "AstrologicalSubjectModel",
    "CompositeSubjectModel",
    "KerykeionPointModel",
    "EphemerisWarningModel",
    "AspectModel",
    "ChartDataModel",
    "AngularityModel",
    "StelliumModel",
    "SingleChartDataModel",
    "DualChartDataModel",
    "SingleChartAspectsModel",
    "DualChartAspectsModel",
    "ElementDistributionModel",
    "QualityDistributionModel",
    "HouseComparisonModel",
    "PlanetReturnModel",
    "TransitEventModel",
    "TransitEventsTimeRangeModel",
    "TransitsTimeRangeModel",
    "PlanetaryPhenomenaModel",
    "PlanetaryPhenomenaCollectionModel",
    "MoonPhaseOverviewModel",
    "SunTimesModel",
    "PlanetaryHourModel",
    "PlanetaryHoursModel",
    "VoidOfCourseAspectModel",
    "VoidOfCourseMoonModel",
    "VoidOfCourseWindowModel",
    "VoidOfCourseWindowsCollectionModel",
    "DominantsModel",
    "TriplicityLordsModel",
    "DominantScoreModel",
    "DominantBreakdownItemModel",
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
    "RelationshipScoreModel",
    "EphemerisDictModel",
    "DominantMethod",
    # Settings and Utilities
    "KerykeionSettingsModel",
    "to_context",
    "PTOLEMAIC_ASPECTS",
    # Ephemeris Backend
    "BACKEND_NAME",
]


# =============================================================================
# REMOVED v5 API — helpful migration errors (PEP 562)
# =============================================================================
_MIGRATION_GUIDE_URL = "https://www.kerykeion.net/content/docs/migration"

_V5_REMOVED_NAMES = {
    "AstrologicalSubject": (
        "'AstrologicalSubject' was removed in v6. Use the factory instead:\n"
        "    from kerykeion import AstrologicalSubjectFactory\n"
        "    subject = AstrologicalSubjectFactory.from_birth_data(...)"
    ),
    "KerykeionChartSVG": (
        "'KerykeionChartSVG' was removed in v6. Compute chart data first, then draw it:\n"
        "    from kerykeion import ChartDataFactory, ChartDrawer\n"
        "    chart_data = ChartDataFactory.create_natal_chart_data(subject)\n"
        "    svg = ChartDrawer(chart_data).generate_svg_string()"
    ),
    "NatalAspects": (
        "'NatalAspects' was removed in v6. Use AspectsFactory instead:\n"
        "    from kerykeion import AspectsFactory\n"
        "    aspects = AspectsFactory.single_chart_aspects(subject)"
    ),
    "SynastryAspects": (
        "'SynastryAspects' was removed in v6. Use AspectsFactory instead:\n"
        "    from kerykeion import AspectsFactory\n"
        "    aspects = AspectsFactory.dual_chart_aspects(first_subject, second_subject)"
    ),
}


def __getattr__(name: str):
    # ImportError (not AttributeError) so that `from kerykeion import AstrologicalSubject`
    # surfaces this message verbatim instead of Python's generic "cannot import name".
    # Trade-off: hasattr()/getattr(..., default) also raise for these names —
    # feature-detect with try/except ImportError instead.
    if name in _V5_REMOVED_NAMES:
        raise ImportError(f"{_V5_REMOVED_NAMES[name]}\nMigration guide: {_MIGRATION_GUIDE_URL}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
