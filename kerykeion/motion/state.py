# -*- coding: utf-8 -*-
"""Per-point motion-state classification.

Classifies a body's instantaneous ecliptic speed against its mean daily
motion: stationary (inside a band around zero speed), retrograde (negative),
slow (below 80%), fast (above 120%), or average. The thresholds are the common
convention used by chart tables that flag "fast"/"slow"/"station" planets.

A station is reported as one of two distinct events whenever the caller can
supply a second speed sample: ``stationary_retrograde`` (the body slows,
stops and turns backwards) and ``stationary_direct`` (it slows, stops and
resumes forward motion). The two are read very differently, and the sign of
the speed alone cannot tell them apart — both stations are approached from
one side and left on the other. What separates them is the *trend*: speed
falling through the band means the retrograde phase is opening, speed rising
through it means the retrograde phase is closing. Without a second sample the
generic ``stationary`` is returned rather than a guess.

Mean motions are geocentric values, so the classification is only attached
for Earth-centred perspectives — a heliocentric speed measured against a
geocentric mean would be meaningless (and nothing is ever retrograde there).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from typing import Callable, Optional

from kerykeion.schemas.literals import MotionState

__all__ = [
    "MEAN_DAILY_MOTION_DEGREES",
    "STATION_TREND_DELTA_DAYS",
    "classify_motion_state",
]

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

# Offset of the second speed sample used to tell the two stations apart.
# A station is a simple zero crossing of the velocity, so the sign of the
# change over a day is unambiguous for every body that stations at all —
# from Mercury (days) to Pluto (months).
STATION_TREND_DELTA_DAYS = 1.0


def classify_motion_state(
    point_name: str,
    speed: Optional[float],
    *,
    speed_sampler: Optional[Callable[[float], Optional[float]]] = None,
) -> Optional[MotionState]:
    """Motion state of ``point_name`` moving at ``speed`` degrees/day.

    Returns ``None`` for bodies without a tabulated mean motion (nodes,
    asteroids, fixed stars, house cusps) or when the speed is unknown —
    absence of a claim, never a guess.

    ``speed_sampler`` is called with a day offset and returns the body's
    speed there. It is consulted only for a body already inside the
    stationary band, so the extra ephemeris call costs nothing on the
    overwhelming majority of charts. When it is absent, returns ``None``, or
    reports an unchanged speed, the station is reported as the generic
    ``stationary``.

    Example:
        >>> classify_motion_state("Mercury", -0.5)
        'retrograde'
        >>> classify_motion_state("Mercury", 0.05)
        'stationary'
        >>> classify_motion_state("Mercury", 0.05, speed_sampler=lambda days: -0.1)
        'stationary_retrograde'
        >>> classify_motion_state("Mercury", -0.05, speed_sampler=lambda days: 0.1)
        'stationary_direct'
        >>> classify_motion_state("Moon", 14.5)
        'average'
    """
    if speed is None:
        return None
    mean = MEAN_DAILY_MOTION_DEGREES.get(point_name)
    if mean is None:
        return None

    # The band brackets zero speed on both sides and is tested first: a body
    # creeping backwards at a hundredth of its mean motion is standing still
    # in every sense an astrologer means by the word, and calling it plain
    # "retrograde" would hide the very event the reader is looking for.
    if abs(speed) < mean * STATIONARY_FRACTION:
        if speed_sampler is not None:
            later = speed_sampler(STATION_TREND_DELTA_DAYS)
            if later is not None:
                if later < speed:
                    return "stationary_retrograde"
                if later > speed:
                    return "stationary_direct"
        return "stationary"
    if speed < 0:
        return "retrograde"
    if speed > mean * FAST_FRACTION:
        return "fast"
    if speed < mean * SLOW_FRACTION:
        return "slow"
    return "average"
