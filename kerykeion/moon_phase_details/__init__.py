# -*- coding: utf-8 -*-
"""
Moon Phase Details

This module exposes the high-level factory for building rich moon
phase context data structures, suitable for API responses and user
interfaces.

The main entry point is:
    - MoonPhaseDetailsFactory

It composes low-level astronomical helpers from
`kerykeion.moon_phase_details.utils` with Kerykeion's existing
astrological subject models to produce a `MoonPhaseOverviewModel`
instance.
"""

from .factory import MoonPhaseDetailsFactory

__all__ = ["MoonPhaseDetailsFactory"]

