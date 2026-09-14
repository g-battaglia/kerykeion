# -*- coding: utf-8 -*-
"""
Sun Times

High-level factory for sunrise / sunset / solar-noon / day-length at a place and
civil date, computed directly from the active ephemeris backend's rise/set
routine (no astrological subject is built).

The main entry point is:
    - SunTimesFactory
"""

from .factory import SunTimesFactory

__all__ = ["SunTimesFactory"]
