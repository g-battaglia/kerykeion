# -*- coding: utf-8 -*-
"""
Backward compatibility module for Kerykeion v4.x imports.

DEPRECATED: This module is scheduled for removal in a future release.
Please update your imports:
    OLD: from kerykeion.kr_types import ...
    NEW: from kerykeion.schemas import ...
"""

import warnings

# Issue deprecation warning when this module is imported
warnings.warn(
    "The 'kerykeion.kr_types' module is deprecated and will be removed in a future release. "
    "Please update your imports to use 'kerykeion.schemas' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from schemas for backward compatibility
from kerykeion.schemas import *  # noqa: F401, F403
from kerykeion.schemas.kerykeion_exception import *  # noqa: F401, F403
from kerykeion.schemas.kr_literals import *  # noqa: F401, F403
from kerykeion.schemas.kr_models import *  # noqa: F401, F403
from kerykeion.schemas.settings_models import *  # noqa: F401, F403
from kerykeion.schemas.chart_template_model import *  # noqa: F401, F403

# Delegate __all__ to the canonical list so this deprecated shim can never drift
# out of sync with kerykeion.schemas (the previous hardcoded list silently omitted
# many newer public symbols from `from kerykeion.kr_types import *`).
from kerykeion import schemas as _schemas

__all__ = list(_schemas.__all__)
