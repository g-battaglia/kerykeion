# -*- coding: utf-8 -*-
"""Calculate essential dignities for astrological points.

Essential dignities evaluate how well a planet can express itself in its
current zodiacal position. The Ptolemaic scoring system assigns:
    +5  Domicile (planet rules the sign)
    +4  Exaltation
    +3  Triplicity (by sect)
    +2  Term (Egyptian bounds)
    +1  Face (Chaldean decan)
     0  Peregrine (no dignity)
    -4  Fall
    -5  Detriment
"""

from __future__ import annotations

import math
from typing import Optional

from .dignity_data import (
    CHALDEAN_DECANS,
    DETRIMENT_RULERS,
    DIGNITY_PLANETS,
    DOMICILE_RULERS,
    EGYPTIAN_TERMS,
    EXALTATION_TABLE,
    FALL_TABLE,
    TRIPLICITY_RULERS,
)


def _get_decan(position: float) -> int:
    """Return the decan number (1-3) from the position within a sign (0-30)."""
    if position < 10:
        return 1
    elif position < 20:
        return 2
    else:
        return 3


def _get_decan_ruler(sign: str, decan_number: int) -> Optional[str]:
    """Return the Chaldean decan ruler for the given sign and decan."""
    rulers = CHALDEAN_DECANS.get(sign)
    if rulers and 1 <= decan_number <= 3:
        return rulers[decan_number - 1]
    return None


def _get_term_ruler(sign: str, position: float) -> Optional[str]:
    """Return the Egyptian term (bound) ruler for the given sign and degree."""
    terms = EGYPTIAN_TERMS.get(sign)
    if not terms:
        return None
    degree = math.floor(position)
    for ruler, start, end in terms:
        if start <= degree < end:
            return ruler
    return None


def _compute_dignity(
    planet_name: str,
    sign: str,
    element: str,
    position: float,
    is_diurnal: bool,
    decan_number: int,
    decan_ruler: Optional[str],
    term_ruler: Optional[str],
) -> tuple[Optional[str], Optional[int]]:
    """Compute the highest essential dignity and aggregate score.

    Returns:
        (dignity_name, score) where dignity_name is the single highest
        dignity classification, and score is the net sum of all dignities.
    """
    if planet_name not in DIGNITY_PLANETS:
        return None, None

    score = 0
    highest_dignity = "Peregrine"
    highest_rank = 0

    # Domicile (+5)
    domicile_rulers = DOMICILE_RULERS.get(sign, [])
    if planet_name in domicile_rulers:
        score += 5
        if 5 > highest_rank:
            highest_rank = 5
            highest_dignity = "Domicile"

    # Detriment (-5)
    detriment_rulers = DETRIMENT_RULERS.get(sign, [])
    if planet_name in detriment_rulers:
        score -= 5

    # Exaltation (+4)
    exalt_entry = EXALTATION_TABLE.get(sign, (None, None))
    if exalt_entry[0] == planet_name:
        score += 4
        if 4 > highest_rank:
            highest_rank = 4
            highest_dignity = "Exaltation"

    # Fall (-4)
    fall_planet = FALL_TABLE.get(sign)
    if fall_planet == planet_name:
        score -= 4

    # Triplicity (+3) — by sect
    trip_rulers = TRIPLICITY_RULERS.get(element, {})
    sect_key = "day" if is_diurnal else "night"
    if trip_rulers.get(sect_key) == planet_name:
        score += 3
        if 3 > highest_rank:
            highest_rank = 3
            highest_dignity = "Triplicity"

    # Term (+2)
    if term_ruler == planet_name:
        score += 2
        if 2 > highest_rank:
            highest_rank = 2
            highest_dignity = "Term"

    # Face/Decan (+1)
    if decan_ruler == planet_name:
        score += 1
        if 1 > highest_rank:
            highest_rank = 1
            highest_dignity = "Face"

    # If only debilities apply, label accordingly
    if highest_rank == 0 and score < 0:
        if planet_name in detriment_rulers:
            highest_dignity = "Detriment"
        elif fall_planet == planet_name:
            highest_dignity = "Fall"

    return highest_dignity, score


def calculate_essential_dignity(
    planet_name: str,
    sign: str,
    element: str,
    position: float,
    is_diurnal: bool,
) -> dict:
    """Calculate essential dignity data for a planet.

    Args:
        planet_name: Name of the planet (e.g. "Mars").
        sign: 3-letter sign abbreviation (e.g. "Ari").
        element: Element of the sign (e.g. "Fire").
        position: Degree within the sign (0-30).
        is_diurnal: Whether the chart is diurnal (day chart).

    Returns:
        Dict with keys: decan_number, decan_ruler, term_ruler,
        essential_dignity, dignity_score. All None for non-classical planets.
    """
    if planet_name not in DIGNITY_PLANETS:
        return {
            "decan_number": None,
            "decan_ruler": None,
            "term_ruler": None,
            "essential_dignity": None,
            "dignity_score": None,
        }

    decan_number = _get_decan(position)
    decan_ruler = _get_decan_ruler(sign, decan_number)
    term_ruler = _get_term_ruler(sign, position)

    dignity, score = _compute_dignity(
        planet_name, sign, element, position,
        is_diurnal, decan_number, decan_ruler, term_ruler,
    )

    return {
        "decan_number": decan_number,
        "decan_ruler": decan_ruler,
        "term_ruler": term_ruler,
        "essential_dignity": dignity,
        "dignity_score": score,
    }
