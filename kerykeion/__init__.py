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

Quick Start
-----------
>>> from kerykeion import AstrologicalSubject
>>> subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "Rome")
>>> print(subject.sun.sign)  # Get Sun sign
>>> print(subject.ascendant.sign)  # Get Ascendant

For the new Factory-based API:
>>> from kerykeion import AstrologicalSubjectFactory
>>> subject = AstrologicalSubjectFactory.create_subject("John", 1990, 1, 1, 12, 0, "Rome", "IT")

Main Classes
------------
- AstrologicalSubjectFactory: Create astrological subjects (recommended)
- AstrologicalSubject: Legacy wrapper for backward compatibility
- ChartDrawer: Generate SVG chart visualizations
- AspectsFactory: Calculate planetary aspects
- RelationshipScoreFactory: Calculate compatibility scores
- CompositeSubjectFactory: Create composite charts
- PlanetaryReturnFactory: Calculate solar/lunar returns
- TransitsTimeRangeFactory: Track transits over time

.. include:: ../README.md

This is part of Kerykeion (C) 2025 Giacomo Battaglia
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

# =============================================================================
# ANALYSIS FACTORIES
# =============================================================================
from .aspects import AspectsFactory
from .relationship_score_factory import RelationshipScoreFactory
from .house_comparison.house_comparison_factory import HouseComparisonFactory

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
    ChartDataModel,
    SingleChartDataModel,
    DualChartDataModel,
    ElementDistributionModel,
    QualityDistributionModel,
    HouseComparisonModel,
    PlanetReturnModel,
)

# =============================================================================
# SETTINGS AND UTILITIES
# =============================================================================
from .settings import KerykeionSettingsModel
from .context_serializer import to_context

# =============================================================================
# LEGACY API (v4 backward compatibility)
# =============================================================================
from .backword import (
    AstrologicalSubject,  # Legacy wrapper for AstrologicalSubjectFactory
    KerykeionChartSVG,  # Legacy wrapper for ChartDrawer
    NatalAspects,  # Legacy wrapper for AspectsFactory (natal)
    SynastryAspects,  # Legacy wrapper for AspectsFactory (synastry)
)


__all__ = [
    # Core Factories
    "AstrologicalSubjectFactory",
    "CompositeSubjectFactory",
    "PlanetaryReturnFactory",
    "ChartDataFactory",
    "EphemerisDataFactory",
    "TransitsTimeRangeFactory",
    # Analysis Factories
    "AspectsFactory",
    "RelationshipScoreFactory",
    "HouseComparisonFactory",
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
    # Settings and Utilities
    "KerykeionSettingsModel",
    "to_context",
    # Legacy API (v4 backward compatibility)
    "AstrologicalSubject",
    "KerykeionChartSVG",
    "NatalAspects",
    "SynastryAspects",
]
