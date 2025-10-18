# -*- coding: utf-8 -*-
"""
Backward compatibility module for kr_models.

DEPRECATED: This module will be removed in Kerykeion v6.0.
Please update your imports:
    OLD: from kerykeion.kr_types.kr_models import ...
    NEW: from kerykeion.schemas.kr_models import ...
"""
import warnings

warnings.warn(
    "The 'kerykeion.kr_types.kr_models' module is deprecated and will be removed in v6.0. "
    "Please update your imports to use 'kerykeion.schemas.kr_models' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from schemas.kr_models for backward compatibility
from kerykeion.schemas.kr_models import *  # noqa: F401, F403
