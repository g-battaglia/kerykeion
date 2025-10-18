# -*- coding: utf-8 -*-
"""
Backward compatibility module for kerykeion_exception.

DEPRECATED: This module will be removed in Kerykeion v6.0.
Please update your imports:
    OLD: from kerykeion.kr_types.kerykeion_exception import ...
    NEW: from kerykeion.schemas.kerykeion_exception import ...
"""
import warnings

warnings.warn(
    "The 'kerykeion.kr_types.kerykeion_exception' module is deprecated and will be removed in v6.0. "
    "Please update your imports to use 'kerykeion.schemas.kerykeion_exception' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from schemas.kerykeion_exception for backward compatibility
from kerykeion.schemas.kerykeion_exception import *  # noqa: F401, F403
