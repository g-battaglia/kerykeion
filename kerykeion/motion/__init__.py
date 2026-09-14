# -*- coding: utf-8 -*-
"""
Motion

Per-point motion-state classification: retrograde, stationary, slow, fast
or average, derived from a body's instantaneous speed against its mean
daily motion.

The main entry point is:
    - classify_motion_state
"""

from .state import (
    FAST_FRACTION,
    MEAN_DAILY_MOTION_DEGREES,
    SLOW_FRACTION,
    STATIONARY_FRACTION,
    MotionState,
    classify_motion_state,
)

__all__ = [
    "MEAN_DAILY_MOTION_DEGREES",
    "classify_motion_state",
    # Importable from `kerykeion.motion` before it became a package; the
    # thresholds are what make classify_motion_state's output interpretable.
    "STATIONARY_FRACTION",
    "SLOW_FRACTION",
    "FAST_FRACTION",
    # The literal classify_motion_state returns; annotating a caller needs it.
    "MotionState",
]
