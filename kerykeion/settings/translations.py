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


def load_language_settings(overrides: Optional[Mapping[str, Any]] = None) -> dict[str, dict[str, Any]]:
    """Return the available language settings merged with optional overrides."""
    languages = deepcopy(LANGUAGE_SETTINGS)
    if overrides:
        data = overrides.get("language_settings", overrides)
        languages = _deep_merge(languages, data)
    return languages


def get_translations(
    value: str,
    default: T,
    *,
    language: Optional[str] = None,
    language_dict: Optional[Mapping[str, Any]] = None,
) -> T:
    """Fetch a translation by key, falling back to English when missing."""
    primary = _select_language(language_dict, language)
    result = _deep_get(primary, value)
    if result is _SENTINEL:
        fallback = LANGUAGE_SETTINGS.get("EN", {})
        result = _deep_get(fallback, value)
    return default if result is _SENTINEL or result is None else result  # type: ignore[return-value]


def _select_language(language_dict: Optional[Mapping[str, Any]], language: Optional[str]) -> Mapping[str, Any]:
    if language_dict is not None:
        return language_dict
    fallback = LANGUAGE_SETTINGS.get("EN", {})
    if language is None:
        return fallback
    return LANGUAGE_SETTINGS.get(language, fallback)


def _deep_merge(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
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


__all__ = ["get_translations", "load_language_settings"]
