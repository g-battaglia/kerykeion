"""
Utilities for loading Kerykeion configuration settings from Python sources.

The translation strings are now stored directly in :mod:`translation_strings`,
so the loader simply wraps those dictionaries (or any user-provided overrides).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Optional, cast

from .translation_strings import LANGUAGE_SETTINGS
from .translations import _deep_merge

SettingsSource = Optional[Mapping[str, Any]]


def load_settings_mapping(settings_source: SettingsSource = None) -> Mapping[str, Any]:
    """
    Resolve the configuration mapping from the provided source.

    .. deprecated::
        Unused by the library itself (translations are served with caching by
        :mod:`kerykeion.settings.translations`); it deep-copies the whole
        language dictionary on every call. It will be removed in
        kerykeion 7.0.0 — use ``load_language_settings`` from
        :mod:`kerykeion.settings.translations` instead.

    Args:
        settings_source (Mapping | None): Optional overrides for the bundled
            language settings. When provided, keys and nested dictionaries are
            merged on top of the default values.

    Returns:
        Mapping[str, Any]: The resolved configuration dictionary.
    """
    import warnings

    warnings.warn(
        "load_settings_mapping is deprecated and will be removed in kerykeion 7.0.0; "
        "use kerykeion.settings.translations.load_language_settings instead",
        DeprecationWarning,
        stacklevel=2,
    )
    language_settings = deepcopy(LANGUAGE_SETTINGS)

    if settings_source:
        overrides = cast(Mapping[str, Any], settings_source)
        if "language_settings" in overrides:
            overrides = cast(Mapping[str, Any], overrides["language_settings"])
        language_settings = _deep_merge(language_settings, overrides)

    return {"language_settings": language_settings}


# Keep the public surface area explicit for downstream imports.
__all__ = ["SettingsSource", "load_settings_mapping", "LANGUAGE_SETTINGS"]
