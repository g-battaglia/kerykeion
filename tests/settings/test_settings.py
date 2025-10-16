from kerykeion.settings import (
    LANGUAGE_SETTINGS,
    get_translations,
    load_language_settings,
    load_settings_mapping,
)


def test_load_settings_mapping_default() -> None:
    settings = load_settings_mapping()

    assert settings["language_settings"]["EN"]["info"] == "Info"


def test_load_settings_mapping_with_overrides() -> None:
    settings = load_settings_mapping({"PT": {"info": "Informações"}})

    assert settings["language_settings"]["PT"]["info"] == "Informações"


def test_load_language_settings_default() -> None:
    languages = load_language_settings()

    assert languages["EN"]["info"] == "Info"


def test_load_language_settings_with_override() -> None:
    languages = load_language_settings({"PT": {"info": "Informações"}})

    assert languages["PT"]["info"] == "Informações"


def test_get_translations_default_language() -> None:
    assert get_translations("info", "fallback", language="EN") == "Info"


def test_get_translations_nested_key() -> None:
    assert get_translations("weekdays.Monday", "fallback", language="EN") == "Monday"


def test_get_translations_missing_language_falls_back() -> None:
    assert get_translations("info", "fallback", language="PT") == "Informações"


def test_get_translations_with_explicit_language_dict() -> None:
    custom_dict = {"info": "Informazione"}

    assert get_translations("info", "fallback", language_dict=custom_dict) == "Informazione"


def test_get_translations_with_loaded_override() -> None:
    languages = load_language_settings({"PT": {"info": "Informações"}})

    assert get_translations("info", "fallback", language_dict=languages["PT"]) == "Informações"


def test_get_translations_returns_default_when_missing() -> None:
    assert get_translations("missing_key", "Default", language="EN") == "Default"
