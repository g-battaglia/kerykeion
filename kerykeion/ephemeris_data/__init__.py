# -*- coding: utf-8 -*-
"""
Ephemeris Data

Time-series ephemeris generation: planetary positions and house cusps
sampled at a fixed interval across a date range.

The main entry point is:
    - EphemerisDataFactory
"""

from .factory import EphemerisDataFactory

__all__ = ["EphemerisDataFactory"]
