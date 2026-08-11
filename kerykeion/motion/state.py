# -*- coding: utf-8 -*-
"""Per-point motion-state classification.

Classifies a body's instantaneous ecliptic speed against its mean daily
motion: retrograde (negative), stationary (below 5% of the mean), slow
(below 80%), fast (above 120%), or average. The thresholds are the common
convention used by chart tables that flag "fast"/"slow"/"station" planets.

Mean motions are geocentric values, so the classification is only attached
for Earth-centred perspectives — a heliocentric speed measured against a
geocentric mean would be meaningless (and nothing is ever retrograde there).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from typing import Optional

from kerykeion.schemas.literals import MotionState

__all__ = ["MEAN_DAILY_MOTION_DEGREES", "classify_motion_state"]

# Mean geocentric daily motion in degrees/day.
MEAN_DAILY_MOTION_DEGREES: dict[str, float] = {
    "Sun": 0.9856,
    "Moon": 13.176,
    "Mercury": 1.383,
    "Venus": 1.2,
    "Mars": 0.524,
    "Jupiter": 0.083,
    "Saturn": 0.033,
    "Uranus": 0.012,
    "Neptune": 0.006,
    "Pluto": 0.004,
}

# Fractions of the mean daily motion bounding each state.
STATIONARY_FRACTION = 0.05
SLOW_FRACTION = 0.8
FAST_FRACTION = 1.2


def classify_motion_state(point_name: str, speed: Optional[float]) -> Optional[MotionState]:
    """Motion state of ``point_name`` moving at ``speed`` degrees/day.

    Returns ``None`` for bodies without a tabulated mean motion (nodes,
    asteroids, fixed stars, house cusps) or when the speed is unknown —
    absence of a claim, never a guess.

    Example:
        >>> classify_motion_state("Mercury", -0.5)
        'retrograde'
        >>> classify_motion_state("Mercury", 0.05)
        'stationary'
        >>> classify_motion_state("Moon", 14.5)
        'average'
    """
    if speed is None:
        return None
    mean = MEAN_DAILY_MOTION_DEGREES.get(point_name)
    if mean is None:
        return None

    if speed < 0:
        return "retrograde"
    # The stationary band brackets zero speed regardless of direction, but a
    # negative speed has already answered "retrograde": a station is only
    # reported while the body still edges forward.
    if abs(speed) < mean * STATIONARY_FRACTION:
        return "stationary"
    if speed > mean * FAST_FRACTION:
        return "fast"
    if speed < mean * SLOW_FRACTION:
        return "slow"
    return "average"
