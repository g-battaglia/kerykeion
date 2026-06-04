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

# =============================================================================
# CORE FACTORIES
# =============================================================================
from .astrological_subject_factory import AstrologicalSubjectFactory
from .composite_subject_factory import CompositeSubjectFactory
from .planetary_return_factory import PlanetaryReturnFactory
from .chart_data_factory import ChartDataFactory
from .ephemeris_data_factory import EphemerisDataFactory
from .transits_time_range_factory import TransitsTimeRangeFactory
from .moon_phase_details import MoonPhaseDetailsFactory
from .sun_times import SunTimesFactory
from .planetary_hours import PlanetaryHoursFactory
from .void_of_course_moon import VoidOfCourseMoonFactory

# =============================================================================
# STANDALONE FACTORIES
# =============================================================================
from .planetary_phenomena import PlanetaryPhenomenaFactory
from .eclipses import EclipseFactory
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
from .planetary_nodes import PlanetaryNodesFactory
from .heliacal import HeliacalFactory
from .occultations import OccultationFactory
from .relocated_chart_factory import RelocatedChartFactory
from .fixed_stars import FixedStarDiscoveryFactory
from .primary_directions import PrimaryDirectionsFactory
from .astro_cartography import AstroCartographyFactory
from .midpoints import MidpointFactory, MidpointModel, MidpointAspectModel
from .secondary_progressions import (
    ProgressedToNatalAspect,
    SecondaryProgressionFactory,
    SecondaryProgressionsResult,
    SolarArcFactory,
    SolarArcDirectedAspect,
    SolarArcSubjectModel,
    SolarArcDirectedPoint,
)

# =============================================================================
# ANALYSIS FACTORIES
# =============================================================================
from .aspects import AspectsFactory
from .relationship_score_factory import RelationshipScoreFactory
from .house_comparison.house_comparison_factory import HouseComparisonFactory
from .dominants import DominantsFactory, DominantStrategy, BaseDominantStrategy
from .zodiacal_releasing import ZodiacalReleasingFactory

# =============================================================================
# VISUALIZATION
# =============================================================================
from .charts.chart_drawer import ChartDrawer
from .report import ReportGenerator

# =============================================================================
# DATA MODELS
# =============================================================================
from .schemas import KerykeionException
from .schemas.kr_models import (
    MoonPhaseOverviewModel,
    ChartDataModel,
    SingleChartDataModel,
    DualChartDataModel,
    ElementDistributionModel,
    QualityDistributionModel,
    HouseComparisonModel,
    PlanetReturnModel,
    SunTimesModel,
    PlanetaryHourModel,
    PlanetaryHoursModel,
    VoidOfCourseAspectModel,
    VoidOfCourseMoonModel,
    DominantsModel,
    DominantScoreModel,
    DominantBreakdownItemModel,
    ZodiacalReleasingModel,
    ZRPeriodModel,
)
from .schemas.kr_literals import DominantMethod

# =============================================================================
# SETTINGS AND UTILITIES
# =============================================================================
from .settings import KerykeionSettingsModel
from .context_serializer import to_context
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
    "LunationFinderFactory",
    "LunationModel",
    "LunationsCollectionModel",
    "RetrogradeStationFactory",
    "StationModel",
    "RetrogradeStationsCollectionModel",
    "SignIngressFactory",
    "IngressModel",
    "SignIngressesCollectionModel",
    "PlanetaryNodesFactory",
    "HeliacalFactory",
    "OccultationFactory",
    "RelocatedChartFactory",
    "FixedStarDiscoveryFactory",
    "PrimaryDirectionsFactory",
    "AstroCartographyFactory",
    "MidpointFactory",
    "MidpointModel",
    "MidpointAspectModel",
    "ProgressedToNatalAspect",
    "SecondaryProgressionFactory",
    "SecondaryProgressionsResult",
    "SolarArcFactory",
    "SolarArcDirectedAspect",
    "SolarArcDirectedPoint",
    "SolarArcSubjectModel",
    # Analysis Factories
    "AspectsFactory",
    "RelationshipScoreFactory",
    "HouseComparisonFactory",
    "DominantsFactory",
    "DominantStrategy",
    "BaseDominantStrategy",
    "ZodiacalReleasingFactory",
    # Visualization
    "ChartDrawer",
    "ReportGenerator",
    # Data Models
    "KerykeionException",
    "ChartDataModel",
    "SingleChartDataModel",
    "DualChartDataModel",
    "ElementDistributionModel",
    "QualityDistributionModel",
    "HouseComparisonModel",
    "PlanetReturnModel",
    "MoonPhaseOverviewModel",
    "SunTimesModel",
    "PlanetaryHourModel",
    "PlanetaryHoursModel",
    "VoidOfCourseAspectModel",
    "VoidOfCourseMoonModel",
    "DominantsModel",
    "DominantScoreModel",
    "DominantBreakdownItemModel",
    "ZodiacalReleasingModel",
    "ZRPeriodModel",
    "DominantMethod",
    # Settings and Utilities
    "KerykeionSettingsModel",
    "to_context",
    "PTOLEMAIC_ASPECTS",
    # Ephemeris Backend
    "BACKEND_NAME",
]
