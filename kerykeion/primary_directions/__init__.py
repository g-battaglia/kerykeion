# -*- coding: utf-8 -*-
"""
Primary Directions module (v6.0)

Implements the classical predictive technique of Primary Directions using
the Placidus semi-arc method. Supports both Ptolemy (1 degree = 1 year)
and Naibod (0.98564 degrees = 1 year) rate keys.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from .directions_factory import PrimaryDirectionsFactory

__all__ = ["PrimaryDirectionsFactory"]
