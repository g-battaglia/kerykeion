"""Global configuration, chart defaults, and translation utilities."""

from kerykeion.schemas import KerykeionSettingsModel
from .chart_defaults import (
    DEFAULT_CHART_COLORS,
    DEFAULT_CELESTIAL_POINTS_SETTINGS,
    DEFAULT_CHART_ASPECTS_SETTINGS,
)
from .config_constants import (
    ALL_ACTIVE_POINTS,
    DEFAULT_ACTIVE_ASPECTS,
    DEFAULT_ACTIVE_POINTS,
    V5_DEFAULT_ACTIVE_POINTS,
)
# load_settings_mapping stays importable for compatibility but is NOT part of
# __all__: it was born deprecated ("removed in 7.0.0") and a new major must
# not freeze dead API in its public surface.
from .loader import LANGUAGE_SETTINGS, SettingsSource, load_settings_mapping
from .translations import get_translations, load_language_pair, load_language_settings

__all__ = [
    "KerykeionSettingsModel",
    "DEFAULT_CHART_COLORS",
    "DEFAULT_CELESTIAL_POINTS_SETTINGS",
    "DEFAULT_CHART_ASPECTS_SETTINGS",
    "DEFAULT_ACTIVE_POINTS",
    "DEFAULT_ACTIVE_ASPECTS",
    "ALL_ACTIVE_POINTS",
    "V5_DEFAULT_ACTIVE_POINTS",
    "LANGUAGE_SETTINGS",
    "load_language_pair",
    "load_language_settings",
    "get_translations",
    "SettingsSource",
]
