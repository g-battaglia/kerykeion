# -*- coding: utf-8 -*-
"""
Relocated Chart

Recomputes a subject's houses and angles for a different place on Earth,
keeping the natal moment fixed (relocation / astro-cartography charts).

The main entry point is:
    - RelocatedChartFactory
"""

from .factory import RelocatedChartFactory

__all__ = ["RelocatedChartFactory"]
