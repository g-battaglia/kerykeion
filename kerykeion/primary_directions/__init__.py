# -*- coding: utf-8 -*-
"""
Primary Directions module (v6.0)

Implements the classical predictive technique of Primary Directions using
the Placidus semi-arc method. Each degree of right ascension directed
equals one year of life (Ptolemy rate key).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from .directions_factory import PrimaryDirectionsFactory

__all__ = ["PrimaryDirectionsFactory"]
