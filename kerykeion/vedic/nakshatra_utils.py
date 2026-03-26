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

from .nakshatra_data import NAKSHATRAS, NAKSHATRA_SPAN, PADA_SPAN, get_dasha_lord


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

    # Determine nakshatra index (0-26)
    nakshatra_index = int(pos / NAKSHATRA_SPAN)
    if nakshatra_index >= 27:
        nakshatra_index = 26  # Edge case: exactly 360.0

    # Position within the nakshatra
    pos_in_nakshatra = pos - (nakshatra_index * NAKSHATRA_SPAN)

    # Determine pada (1-4)
    pada = int(pos_in_nakshatra / PADA_SPAN) + 1
    if pada > 4:
        pada = 4  # Edge case

    name, _deity = NAKSHATRAS[nakshatra_index]
    lord = get_dasha_lord(nakshatra_index)

    return {
        "nakshatra": name,
        "nakshatra_number": nakshatra_index + 1,  # 1-based
        "nakshatra_pada": pada,
        "nakshatra_lord": lord,
    }
