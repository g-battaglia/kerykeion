# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia

The aspects module contains the classes and functions for calculating
 aspects between planets and points in a chart.
"""


from .aspects_factory import (
    AspectsFactory,
    # Legacy aliases for backward compatibility
    NatalAspectsFactory, 
    SynastryAspectsFactory
)

__all__ = [
    "AspectsFactory",
    # Legacy names maintained for backward compatibility
    "SynastryAspectsFactory",
    "NatalAspectsFactory",
]
