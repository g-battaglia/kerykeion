# -*- coding: utf-8 -*-
"""
Backward compatibility module for kr_literals.

DEPRECATED: This module will be removed in Kerykeion v6.0.
Please update your imports:
    OLD: from kerykeion.kr_types.kr_literals import ...
    NEW: from kerykeion.schemas.kr_literals import ...
"""

import warnings

warnings.warn(
    "The 'kerykeion.kr_types.kr_literals' module is deprecated and will be removed in v6.0. "
    "Please update your imports to use 'kerykeion.schemas.kr_literals' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from schemas.kr_literals for backward compatibility
from kerykeion.schemas.kr_literals import *  # noqa: F401, F403
