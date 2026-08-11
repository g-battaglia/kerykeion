# -*- coding: utf-8 -*-
"""
Predictive

Shared helpers for the predictive techniques (returns, progressions,
directions, ingresses, eclipses): Julian-day validation and conversion,
active-point gathering and aspect-settings assembly.

Internal API: only ``PTOLEMAIC_ASPECTS`` is re-exported from the top-level
``kerykeion`` namespace. The helpers are imported from
``kerykeion.predictive.utils`` by the factories that share them.
"""

from .utils import PTOLEMAIC_ASPECTS

__all__ = ["PTOLEMAIC_ASPECTS"]
