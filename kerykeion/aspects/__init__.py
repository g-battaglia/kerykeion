# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia

The aspects module contains the classes and functions for calculating
 aspects between planets and points in a chart.
"""


from .synastry_aspects_factory import SynastryAspectsFactory
from .natal_aspects_factory import NatalAspectsFactory

__all__ = [
    "SynastryAspectsFactory",
    "NatalAspectsFactory",
]
