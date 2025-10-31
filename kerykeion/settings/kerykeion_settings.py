"""
Utilities for loading Kerykeion configuration settings from Python sources.

The translation strings are now stored directly in :mod:`translation_strings`,
so the loader simply wraps those dictionaries (or any user-provided overrides).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Optional, cast

from .translation_strings import LANGUAGE_SETTINGS

SettingsSource = Optional[Mapping[str, Any]]


def load_settings_mapping(settings_source: Optional[SettingsSource] = None) -> Mapping[str, Any]:
    """
    Resolve the configuration mapping from the provided source.

    Args:
        settings_source (Mapping | None): Optional overrides for the bundled
            language settings. When provided, keys and nested dictionaries are
            merged on top of the default values.

    Returns:
        Mapping[str, Any]: The resolved configuration dictionary.
    """
    language_settings = deepcopy(LANGUAGE_SETTINGS)

    if settings_source:
        overrides = cast(Mapping[str, Any], settings_source)
        if "language_settings" in overrides:
            overrides = cast(Mapping[str, Any], overrides["language_settings"])
        language_settings = _deep_merge(language_settings, overrides)

    return {"language_settings": language_settings}


def _deep_merge(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {key: deepcopy(value) for key, value in base.items()}
    for key, value in overrides.items():
        if key in merged and isinstance(merged[key], Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(cast(Mapping[str, Any], merged[key]), cast(Mapping[str, Any], value))
        else:
            merged[key] = deepcopy(value)
    return merged

# Keep the public surface area explicit for downstream imports.
__all__ = ["SettingsSource", "load_settings_mapping", "LANGUAGE_SETTINGS"]
