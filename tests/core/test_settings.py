# -*- coding: utf-8 -*-
"""
Consolidated tests for kerykeion.settings.

Integrates all cases from tests/settings/test_settings.py plus
settings-related edge cases from tests/edge_cases/test_edge_cases.py.
"""

from copy import deepcopy

import pytest

from kerykeion.settings.kerykeion_settings import load_settings_mapping, _deep_merge
from kerykeion.settings.translations import load_language_settings, get_translations


# =============================================================================
# TestLoadSettingsMapping
# =============================================================================


class TestLoadSettingsMapping:
    """Tests for load_settings_mapping."""

    def test_default_loading_returns_dict_with_language_settings(self):
        settings = load_settings_mapping()
        assert isinstance(settings, dict)
        assert "language_settings" in settings

    def test_default_loading_contains_en_info(self):
        settings = load_settings_mapping()
        assert settings["language_settings"]["EN"]["info"] == "Info"

    def test_with_overrides_merges_correctly(self):
        settings = load_settings_mapping({"PT": {"info": "Informações"}})
        assert settings["language_settings"]["PT"]["info"] == "Informações"

    def test_overrides_via_language_settings_key(self):
        settings = load_settings_mapping({"language_settings": {"EN": {"test": "value"}}})
        assert settings is not None
        assert "language_settings" in settings

    def test_deep_merge_preserves_nested_keys(self):
        settings = load_settings_mapping({"EN": {"custom_key": "custom_value"}})
        # Original EN keys should still be present
        assert settings["language_settings"]["EN"]["info"] == "Info"
        assert settings["language_settings"]["EN"]["custom_key"] == "custom_value"

    def test_none_source_returns_defaults(self):
        settings = load_settings_mapping(None)
        assert "language_settings" in settings
        assert "EN" in settings["language_settings"]


# =============================================================================
# TestLoadLanguageSettings
# =============================================================================


class TestLoadLanguageSettings:
    """Tests for load_language_settings."""

    def test_default_returns_dict_with_language_codes(self):
        languages = load_language_settings()
        assert isinstance(languages, dict)
        assert "EN" in languages

    def test_default_en_info(self):
        languages = load_language_settings()
        assert languages["EN"]["info"] == "Info"

    def test_with_override_adds_new_language(self):
        languages = load_language_settings({"PT": {"info": "Informações"}})
        assert languages["PT"]["info"] == "Informações"

    def test_override_doesnt_destroy_existing(self):
        languages = load_language_settings({"PT": {"info": "Informações"}})
        # EN should still exist and be unmodified
        assert "EN" in languages
        assert languages["EN"]["info"] == "Info"

    def test_override_with_language_settings_wrapper(self):
        languages = load_language_settings({"language_settings": {"PT": {"info": "Informações"}}})
        assert languages["PT"]["info"] == "Informações"


# =============================================================================
# TestGetTranslations
# =============================================================================


class TestGetTranslations:
    """Tests for get_translations."""

    def test_default_language_en(self):
        assert get_translations("info", "fallback", language="EN") == "Info"

    def test_specific_language_it(self):
        result = get_translations("info", "fallback", language="IT")
        assert isinstance(result, str)
        assert result != "fallback"

    def test_specific_language_cn(self):
        result = get_translations("info", "fallback", language="CN")
        assert isinstance(result, str)
        assert result != "fallback"

    def test_specific_language_fr(self):
        result = get_translations("info", "fallback", language="FR")
        assert isinstance(result, str)
        assert result != "fallback"

    def test_specific_language_es(self):
        result = get_translations("info", "fallback", language="ES")
        assert isinstance(result, str)
        assert result != "fallback"

    def test_missing_language_falls_back_to_en(self):
        # PT may or may not exist; either way it should not return the fallback
        # for a key that exists in EN
        result = get_translations("info", "fallback", language="PT")
        # Falls back to EN when PT is missing
        assert result != "fallback"

    def test_explicit_language_dict_parameter(self):
        custom_dict = {"info": "Informazione"}
        assert get_translations("info", "fallback", language_dict=custom_dict) == "Informazione"

    def test_with_loaded_override(self):
        languages = load_language_settings({"PT": {"info": "Informações"}})
        assert get_translations("info", "fallback", language_dict=languages["PT"]) == "Informações"

    def test_nested_key_access_dotted_notation(self):
        assert get_translations("weekdays.Monday", "fallback", language="EN") == "Monday"

    def test_missing_key_returns_default_value(self):
        assert get_translations("missing_key", "Default", language="EN") == "Default"

    def test_completely_nonexistent_key_returns_fallback(self):
        result = get_translations("completely_nonexistent_key_xyz123", "fallback_default")
        assert result == "fallback_default"

    def test_no_language_uses_en(self):
        # When neither language nor language_dict is provided, defaults to EN
        result = get_translations("info", "fallback")
        assert result == "Info"


# =============================================================================
# TestDeepMerge
# =============================================================================


class TestDeepMerge:
    """Tests for _deep_merge utility."""

    def test_nested_override_replaces_only_specified_keys(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        overrides = {"a": {"x": 99}}
        merged = _deep_merge(base, overrides)
        assert merged["a"]["x"] == 99
        assert merged["a"]["y"] == 2
        assert merged["b"] == 3

    def test_override_adds_new_keys(self):
        base = {"a": 1}
        overrides = {"b": 2}
        merged = _deep_merge(base, overrides)
        assert merged["a"] == 1
        assert merged["b"] == 2

    def test_override_replaces_non_dict_with_dict(self):
        base = {"a": 1}
        overrides = {"a": {"nested": True}}
        merged = _deep_merge(base, overrides)
        assert merged["a"] == {"nested": True}

    def test_override_replaces_dict_with_non_dict(self):
        base = {"a": {"nested": True}}
        overrides = {"a": 42}
        merged = _deep_merge(base, overrides)
        assert merged["a"] == 42

    def test_empty_overrides_returns_copy_of_base(self):
        base = {"a": 1, "b": {"c": 2}}
        merged = _deep_merge(base, {})
        assert merged == base
        # Ensure it's a copy, not the same object
        assert merged is not base

    def test_empty_base_returns_overrides(self):
        overrides = {"a": 1}
        merged = _deep_merge({}, overrides)
        assert merged == {"a": 1}

    def test_deeply_nested_merge(self):
        base = {"l1": {"l2": {"l3": {"val": "original", "keep": True}}}}
        overrides = {"l1": {"l2": {"l3": {"val": "replaced"}}}}
        merged = _deep_merge(base, overrides)
        assert merged["l1"]["l2"]["l3"]["val"] == "replaced"
        assert merged["l1"]["l2"]["l3"]["keep"] is True
