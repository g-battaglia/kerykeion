# -*- coding: utf-8 -*-
"""
Backward compatibility module for Kerykeion v4.x imports.

DEPRECATED: This module will be removed in Kerykeion v6.0.
Please update your imports:
    OLD: from kerykeion.kr_types import ...
    NEW: from kerykeion.schemas import ...
"""

import warnings

# Issue deprecation warning when this module is imported
warnings.warn(
    "The 'kerykeion.kr_types' module is deprecated and will be removed in v6.0. "
    "Please update your imports to use 'kerykeion.schemas' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from schemas for backward compatibility
from kerykeion.schemas import *  # noqa: F401, F403
from kerykeion.schemas.kerykeion_exception import *  # noqa: F401, F403
from kerykeion.schemas.kr_literals import *  # noqa: F401, F403
from kerykeion.schemas.kr_models import *  # noqa: F401, F403
from kerykeion.schemas.settings_models import *  # noqa: F401, F403
from kerykeion.schemas.chart_template_model import *  # noqa: F401, F403

__all__ = [
    # Re-export from schemas
    "KerykeionException",
    # kr_literals
    "ZodiacType",
    "Sign",
    "SignNumbers",
    "AspectMovementType",
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
    "KerykeionChartLanguage",
    "RelationshipScoreDescription",
    "CompositeChartType",
    "AspectName",
    # kr_models
    "AstrologicalSubjectModel",
    "CompositeSubjectModel",
    "KerykeionPointModel",
    "AspectModel",
    "ActiveAspect",
    "SingleChartAspectsModel",
    "DualChartAspectsModel",
    "ElementDistributionModel",
    "QualityDistributionModel",
    "SingleChartDataModel",
    "DualChartDataModel",
    # settings_models
    "KerykeionSettingsModel",
    # chart_template_model
    "ChartTemplateModel",
]
