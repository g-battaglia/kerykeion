# -*- coding: utf-8 -*-
"""
Secondary progressions module.

Exposes :class:`SecondaryProgressionFactory` and :class:`SolarArcFactory`
plus the result Pydantic models (:class:`SecondaryProgressionsResultModel`,
:class:`SolarArcSubjectModel`, ...).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from .secondary_progression_factory import (
    ProgressedToNatalAspectModel,
    SecondaryProgressionFactory,
    SecondaryProgressionsResultModel,
)
from .solar_arc_factory import (
    SolarArcDirectedAspectModel,
    SolarArcDirectedPointModel,
    SolarArcFactory,
    SolarArcSubjectModel,
)

__all__ = [
    "ProgressedToNatalAspectModel",
    "SecondaryProgressionFactory",
    "SecondaryProgressionsResultModel",
    "SolarArcDirectedAspectModel",
    "SolarArcDirectedPointModel",
    "SolarArcFactory",
    "SolarArcSubjectModel",
]

# Deprecated pre-6.0.0b1 names. TODO remove in 6.0.0 stable.
from kerykeion._deprecation import deprecated_alias_getattr  # noqa: E402

__getattr__ = deprecated_alias_getattr(
    __name__,
    {
        "ProgressedToNatalAspect": ProgressedToNatalAspectModel,
        "SecondaryProgressionsResult": SecondaryProgressionsResultModel,
        "SolarArcDirectedAspect": SolarArcDirectedAspectModel,
        "SolarArcDirectedPoint": SolarArcDirectedPointModel,
    },
)
