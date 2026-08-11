# -*- coding: utf-8 -*-
"""
Motion

Per-point motion-state classification: retrograde, stationary, slow, fast
or average, derived from a body's instantaneous speed against its mean
daily motion.

The main entry point is:
    - classify_motion_state
"""

from .state import MEAN_DAILY_MOTION_DEGREES, classify_motion_state

__all__ = ["MEAN_DAILY_MOTION_DEGREES", "classify_motion_state"]
