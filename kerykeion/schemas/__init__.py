# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from .kerykeion_exception import KerykeionException
from .kr_literals import (
    ZodiacType,
    Sign,
    SignNumbers,
    AspectMovementType,
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
    KerykeionChartLanguage,
    RelationshipScoreDescription,
    CompositeChartType,
    AspectName,
    # Deprecated aliases
    Planet,
    AxialCusps,
)
from .kr_models import (
    SubscriptableBaseModel,
    LunarPhaseModel,
    KerykeionPointModel,
    AstrologicalBaseModel,
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    PlanetReturnModel,
    EphemerisDictModel,
    AspectModel,
    ZodiacSignModel,
    RelationshipScoreAspectModel,
    RelationshipScoreModel,
    ActiveAspect,
    TransitMomentModel,
    TransitsTimeRangeModel,
)
from .chart_template_model import ChartTemplateModel
from .settings_models import KerykeionSettingsModel

__all__ = [
    # Exceptions
    "KerykeionException",

    # Settings and Chart Types
    "ChartTemplateModel",
    "KerykeionSettingsModel",

    # Main Literal Types (from kr_literals)
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

    # Deprecated aliases (for v4.x compatibility, will be removed in v6.0)
    "Planet",
    "AxialCusps",

    # Main Model Classes (from kr_models)
    "SubscriptableBaseModel",
    "LunarPhaseModel",
    "KerykeionPointModel",
    "AstrologicalBaseModel",
    "AstrologicalSubjectModel",
    "CompositeSubjectModel",
    "PlanetReturnModel",
    "EphemerisDictModel",
    "AspectModel",
    "ZodiacSignModel",
    "RelationshipScoreAspectModel",
    "RelationshipScoreModel",
    "ActiveAspect",
    "TransitMomentModel",
    "TransitsTimeRangeModel",
]
