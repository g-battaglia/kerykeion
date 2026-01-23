# -*- coding: utf-8 -*-
"""
Backward compatibility module for chart_template_model.

DEPRECATED: This module will be removed in Kerykeion v6.0.
Please update your imports:
    OLD: from kerykeion.kr_types.chart_template_model import ...
    NEW: from kerykeion.schemas.chart_template_model import ...
"""

import warnings

warnings.warn(
    "The 'kerykeion.kr_types.chart_template_model' module is deprecated and will be removed in v6.0. "
    "Please update your imports to use 'kerykeion.schemas.chart_template_model' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from schemas.chart_template_model for backward compatibility
from kerykeion.schemas.chart_template_model import *  # noqa: F401, F403
