# -*- coding: utf-8 -*-
"""
Context

Serialization of Kerykeion models into semantic XML for AI consumption.
The output is strictly factual: positions, signs, houses and aspects, with
no qualitative or interpretive language.

The main entry point is:
    - to_context
"""

from .serializer import (
    aspect_to_context,
    astrological_subject_to_context,
    dual_chart_data_to_context,
    element_distribution_to_context,
    house_comparison_to_context,
    kerykeion_point_to_context,
    lunar_phase_to_context,
    midpoints_to_context,
    moon_phase_overview_to_context,
    point_in_house_to_context,
    quality_distribution_to_context,
    single_chart_data_to_context,
    solar_arc_to_context,
    to_context,
    transit_moment_to_context,
    transits_time_range_to_context,
)

__all__ = [
    "to_context",
    "kerykeion_point_to_context",
    "lunar_phase_to_context",
    "aspect_to_context",
    "point_in_house_to_context",
    "house_comparison_to_context",
    "element_distribution_to_context",
    "quality_distribution_to_context",
    "astrological_subject_to_context",
    "single_chart_data_to_context",
    "dual_chart_data_to_context",
    "transit_moment_to_context",
    "transits_time_range_to_context",
    "moon_phase_overview_to_context",
    "solar_arc_to_context",
    "midpoints_to_context",
]
