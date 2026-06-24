"""
Simple helpers to access chart translation strings.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Optional, TypeVar

from .translation_strings import LANGUAGE_SETTINGS

T = TypeVar("T")

_SENTINEL = object()

# Cache for the common case (no overrides). A fresh deepcopy of the cache is
# returned on every call so callers can mutate the result freely without
# poisoning the shared defaults used by later charts.
_DEFAULT_LANG_CACHE: dict[str, dict[str, Any]] | None = None


def load_language_settings(overrides: Optional[Mapping[str, Any]] = None) -> dict[str, dict[str, Any]]:
    """Return the available language settings merged with optional overrides.

    The returned dict is always an independent copy: mutating it never
    affects the module-level defaults or subsequent calls.
    """
    global _DEFAULT_LANG_CACHE

    if not overrides:
        if _DEFAULT_LANG_CACHE is None:
            _DEFAULT_LANG_CACHE = deepcopy(LANGUAGE_SETTINGS)
        return deepcopy(_DEFAULT_LANG_CACHE)

    languages = deepcopy(LANGUAGE_SETTINGS)
    data = overrides.get("language_settings", overrides)
    languages = _deep_merge(languages, data)
    return languages


def load_language_pair(
    language: str,
    overrides: Optional[Mapping[str, Any]] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(selected_language_data, english_fallback_data)`` for one chart.

    Unlike :func:`load_language_settings` (which deep-copies the whole ~10-language
    table on every call), this materializes only the two language blocks a chart
    actually needs — the requested ``language`` and the English fallback. In the
    common no-override case it returns direct references into ``LANGUAGE_SETTINGS``:
    the caller feeds them to a Pydantic model that copies on construction and never
    mutates the input, so no defensive copy is needed. Only an override path
    deep-copies (via :func:`_deep_merge`) the single block being merged.

    The override shape and merge semantics match :func:`load_language_settings`
    (overrides keyed by language code, optionally wrapped under ``language_settings``).
    """
    en: dict[str, Any] = LANGUAGE_SETTINGS.get("EN", {})
    selected: Optional[dict[str, Any]] = LANGUAGE_SETTINGS.get(language)

    if overrides:
        data = overrides.get("language_settings", overrides)
        en_override = data.get("EN")
        if en_override:
            en = _deep_merge(en, en_override)
        selected_override = data.get(language)
        if selected_override is not None:
            base = selected if selected is not None else {}
            selected = _deep_merge(base, selected_override)

    if selected is None:
        selected = en
    return selected, en


def get_translations(
    value: str,
    default: T,
    *,
    language: Optional[str] = None,
    language_dict: Optional[Mapping[str, Any]] = None,
    fallback_dict: Optional[Mapping[str, Any]] = None,
) -> T:
    """Fetch a translation by dot-separated key, falling back to English when missing.

    Args:
        value: Dot-separated key path (e.g., "planets.Sun").
        default: Value returned if key is missing in both language and English.
        language: Two-letter language code (e.g., "IT", "FR"). Ignored if language_dict is set.
        language_dict: Explicit language mapping to use instead of the built-in settings.
        fallback_dict: Explicit fallback mapping consulted before the built-in English
            defaults. Lets a caller resolve a key against a primary and a (normalized)
            fallback language in a single call — e.g. ``ChartDrawer`` passes its
            selected-language and English model dumps — instead of two stacked calls.
    """
    primary = _select_language(language_dict, language)
    result = _deep_get(primary, value)
    # Treat a literal None in the primary the same as "missing" so it falls
    # through to the fallback chain. This preserves the precedence of the old
    # two-call ChartDrawer path (a None selected-language label deferred to the
    # English fallback rather than rendering the caller's bare default).
    if (result is _SENTINEL or result is None) and fallback_dict is not None:
        result = _deep_get(fallback_dict, value)
    if result is _SENTINEL or result is None:
        fallback = LANGUAGE_SETTINGS.get("EN", {})
        result = _deep_get(fallback, value)
    return default if result is _SENTINEL or result is None else result  # type: ignore[return-value]


def _select_language(language_dict: Optional[Mapping[str, Any]], language: Optional[str]) -> Mapping[str, Any]:
    """Resolve the language mapping: explicit dict > language code > English fallback."""
    if language_dict is not None:
        return language_dict
    fallback = LANGUAGE_SETTINGS.get("EN", {})
    if language is None:
        return fallback
    return LANGUAGE_SETTINGS.get(language, fallback)


def _deep_merge(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge overrides into base, returning a new dict."""
    merged: dict[str, Any] = {}
    for key, value in base.items():
        merged[key] = deepcopy(value)
    for key, value in overrides.items():
        if key in merged and isinstance(merged[key], Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _deep_get(mapping: Mapping[str, Any], dotted_key: str):
    current: Any = mapping
    for segment in dotted_key.split("."):
        if isinstance(current, Mapping) and segment in current:
            current = current[segment]
        else:
            return _SENTINEL
    return current


__all__ = ["get_translations", "load_language_pair", "load_language_settings"]
