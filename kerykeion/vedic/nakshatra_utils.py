# -*- coding: utf-8 -*-
"""Calculate Nakshatra placement for an astrological point.

Nakshatras divide the sidereal zodiac into 27 equal segments of 13°20'.
The absolute sidereal longitude (0-360) is used to determine which
nakshatra a point falls in, along with the pada (quarter 1-4) and
the Vimsottari Dasha lord.

Note: For accurate Nakshatra calculation, the input position should be
a sidereal longitude. When used with tropical charts, the result is
approximate (the position is treated as-is without ayanamsa correction).
"""

from __future__ import annotations

from .nakshatra_data import NAKSHATRAS, get_dasha_lord


def calculate_nakshatra(abs_pos: float) -> dict:
    """Calculate Nakshatra data for a given absolute zodiacal position.

    Args:
        abs_pos: Absolute position in the zodiac (0-360 degrees).
            For best results, use sidereal longitude.

    Returns:
        Dict with keys:
            nakshatra: Name of the nakshatra (e.g. "Rohini")
            nakshatra_number: Number 1-27
            nakshatra_pada: Pada (quarter) 1-4
            nakshatra_lord: Vimsottari Dasha lord planet name
    """
    # Normalize to 0-360
    pos = abs_pos % 360.0

    # Derive nakshatra AND pada from the same global quarter index (108
    # padas of 3°20' each). Computing the pada from the remainder
    # `pos - index * NAKSHATRA_SPAN` inherits the span constant's float
    # error, misclassifying exactly-representable boundary degrees (e.g.
    # 20.0° landed in pada 2 instead of 3); the direct 108-quarter mapping
    # keeps both values exact and mutually consistent at every boundary.
    global_pada_index = int(pos * 108.0 / 360.0)
    if global_pada_index >= 108:
        global_pada_index = (
            107  # Edge case: pos == 360.0 (tiny negative inputs — float modulo returns the modulus itself)
        )

    nakshatra_index = global_pada_index // 4
    pada = global_pada_index % 4 + 1

    name, _deity = NAKSHATRAS[nakshatra_index]
    lord = get_dasha_lord(nakshatra_index)

    return {
        "nakshatra": name,
        "nakshatra_number": nakshatra_index + 1,  # 1-based
        "nakshatra_pada": pada,
        "nakshatra_lord": lord,
    }
