# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia

.. include:: ../README.md
"""

# Local
from .aspects import AspectsFactory
from .astrological_subject_factory import AstrologicalSubjectFactory
from .chart_data_factory import ChartDataFactory
from .schemas import KerykeionException
from .schemas.kr_models import (
    ChartDataModel,
    SingleChartDataModel,
    DualChartDataModel,
    ElementDistributionModel,
    QualityDistributionModel,
    HouseComparisonModel,
)
from .charts.chart_drawer import ChartDrawer
from .composite_subject_factory import CompositeSubjectFactory
from .ephemeris_data_factory import EphemerisDataFactory
from .house_comparison.house_comparison_factory import HouseComparisonFactory
from .planetary_return_factory import PlanetaryReturnFactory, PlanetReturnModel
from .relationship_score_factory import RelationshipScoreFactory
from .report import ReportGenerator
from .settings import KerykeionSettingsModel
from .transits_time_range_factory import TransitsTimeRangeFactory
from .backword import (
    AstrologicalSubject,  # Legacy wrapper
    KerykeionChartSVG,    # Legacy wrapper
    NatalAspects,         # Legacy wrapper
    SynastryAspects,      # Legacy wrapper
)

__all__ = [
    "AspectsFactory",
    "AstrologicalSubjectFactory",
    "ChartDataFactory",
    "ChartDataModel",
    "SingleChartDataModel",
    "DualChartDataModel",
    "ElementDistributionModel",
    "QualityDistributionModel",
    "ChartDrawer",
    "CompositeSubjectFactory",
    "EphemerisDataFactory",
    "HouseComparisonFactory",
    "HouseComparisonModel",
    "KerykeionException",
    "PlanetaryReturnFactory",
    "PlanetReturnModel",
    "RelationshipScoreFactory",
    "ReportGenerator",
    "KerykeionSettingsModel",
    "TransitsTimeRangeFactory",
    # Legacy (v4) exported names for backward compatibility
    "AstrologicalSubject",
    "KerykeionChartSVG",
    "NatalAspects",
    "SynastryAspects",
]
