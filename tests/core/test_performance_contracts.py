"""Behavioral boundaries of the operation-local performance paths."""

from collections import UserDict
from copy import deepcopy
from unittest.mock import patch

import pytest

from kerykeion import AstrologicalSubjectFactory, AspectsFactory, ChartDataFactory, ChartDrawer
from kerykeion.aspects import utils as aspect_utils
from kerykeion.settings import translations


@pytest.fixture(scope="module")
def subjects():
    return [
        AstrologicalSubjectFactory.from_birth_data(
            name,
            year,
            6,
            15,
            12,
            0,
            lng=12.4964,
            lat=41.9028,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        for name, year in (("First", 1990), ("Second", 1992))
    ]


def test_translation_copy_preserves_graph_and_custom_mapping(monkeypatch):
    shared = {"label": "shared"}
    source = {"first": shared, "second": shared, "custom": UserDict({"values": [shared]})}
    source["cycle"] = source
    monkeypatch.setitem(translations.LANGUAGE_SETTINGS, "ZZ", source)
    selected, fallback = translations.load_language_pair("ZZ")
    assert selected["first"] is selected["second"]
    assert selected["cycle"] is selected
    assert type(selected["custom"]) is UserDict
    assert selected["custom"]["values"][0] is selected["first"]
    selected["first"]["label"] = "changed"
    assert shared["label"] == "shared"
    assert "cycle" not in fallback


def test_english_pair_is_independent_even_for_shared_nested_values(monkeypatch):
    nested = {"values": [1]}
    monkeypatch.setitem(translations.LANGUAGE_SETTINGS["EN"], "custom", nested)
    selected, fallback = translations.load_language_pair("EN")
    selected["custom"]["values"].append(2)
    assert fallback["custom"]["values"] == [1]
    assert nested["values"] == [1]


def test_drawer_snapshots_nested_translation_models(subjects, monkeypatch):
    """Pydantic model instances in global settings must not leak into drawers."""
    from kerykeion.schemas.settings_models import KerykeionLanguageCelestialPointModel

    points = KerykeionLanguageCelestialPointModel(**translations.LANGUAGE_SETTINGS["EN"]["celestial_points"])
    monkeypatch.setitem(translations.LANGUAGE_SETTINGS["EN"], "celestial_points", points)
    drawer = ChartDrawer(ChartDataFactory.create_chart_data("Natal", subjects[0]))
    original = drawer.language_settings["celestial_points"]["Sun"]
    points.Sun = "Changed after construction"
    assert drawer.language_settings["celestial_points"]["Sun"] == original
    assert drawer._language_model.celestial_points.Sun == original


def test_drawers_validate_live_translations_without_retaining_mutable_defaults(subjects, monkeypatch):
    data = ChartDataFactory.create_chart_data("Natal", subjects[0])
    first = ChartDrawer(data, language_pack={"info": "Override"})
    first.language_settings["celestial_points"]["Sun"] = "Changed"
    assert translations.LANGUAGE_SETTINGS["EN"]["celestial_points"]["Sun"] != "Changed"
    assert first._fallback_language_dict["celestial_points"]["Sun"] != "Changed"
    first.language_settings["info"] = None
    assert first._translate("info", "missing") == "Override"
    monkeypatch.setitem(translations.LANGUAGE_SETTINGS["EN"], "info", "Live")
    second = ChartDrawer(data)
    assert second.language_settings["info"] == "Live"
    assert first._translate("info", "missing") == "Override"
    assert second.language_settings["celestial_points"]["Sun"] != "Changed"


@pytest.mark.parametrize("kind", ["Natal", "Synastry", "Transit"])
@pytest.mark.parametrize(
    "export", ["generate_svg_string", "generate_wheel_only_svg_string", "generate_aspect_grid_only_svg_string"]
)
def test_exports_do_not_build_unused_fragments(subjects, kind, export, monkeypatch):
    data = ChartDataFactory.create_chart_data(kind, subjects[0], *subjects[1:] if kind != "Natal" else [])
    drawer = ChartDrawer(data)

    def unused(*args, **kwargs):
        raise AssertionError("unused fragment was built")

    monkeypatch.setattr(drawer._renderer, "setup_wheel", unused)
    if export != "generate_svg_string":
        for name in ("setup_aspects", "setup_info_sections", "setup_grids", "setup_house_comparison"):
            monkeypatch.setattr(drawer._renderer, name, unused)
    assert "<svg" in getattr(drawer, export)()


@pytest.mark.parametrize("kind", ["Natal", "Synastry"])
def test_style_and_output_overrides_do_not_leave_stale_geometry(subjects, kind):
    data = ChartDataFactory.create_chart_data(kind, subjects[0], *subjects[1:] if kind != "Natal" else [])
    reused = ChartDrawer(data)
    for style in ("classic", "modern", "classic", "modern"):
        for export in ("generate_svg_string", "generate_wheel_only_svg_string"):
            expected = getattr(ChartDrawer(data, style=style), export)()
            assert getattr(reused, export)(style=style) == expected
        assert reused.generate_aspect_grid_only_svg_string() == ChartDrawer(data).generate_aspect_grid_only_svg_string()


@pytest.mark.parametrize("extra", [0.0, -2.0, 20.0, {"conjunction": 9.0, "square": -2.0}])
def test_prepared_aspects_preserve_overlaps_wrap_and_ties(extra):
    settings = [
        {"name": "conjunction", "degree": 0, "orb": 50},
        {"name": "sextile", "degree": 60, "orb": 50},
        {"name": "square", "degree": 90, "orb": -1},
        {"name": "opposition", "degree": 180, "orb": 15},
    ]
    before = deepcopy(settings)
    prepared = aspect_utils._prepare_aspect_settings(settings, extra)
    for first in (0.0, 1.0, 179.0, 359.0):
        for second in (0.0, 1.0, 30.0, 60.0, 90.0, 180.0, 359.0):
            assert aspect_utils._get_aspect_from_prepared_settings(
                prepared, first, second
            ) == aspect_utils.get_aspect_from_two_points(settings, first, second, extra)
    assert settings == before


class _UnhashableFloat(float):
    __hash__ = None


@pytest.mark.parametrize("method", ["single_chart_aspects", "dual_chart_aspects"])
def test_custom_numeric_orb_adjustments_keep_the_general_path(subjects, method):
    args = subjects if method == "dual_chart_aspects" else subjects[:1]
    calculate = getattr(AspectsFactory, method)
    expected = calculate(*args, point_orb_adjustments={"Sun": 1.5}).model_dump()
    actual = calculate(*args, point_orb_adjustments={"Sun": _UnhashableFloat(1.5)}).model_dump()
    assert actual == expected


@pytest.mark.parametrize("method", ["single_chart_aspects", "dual_chart_aspects"])
@pytest.mark.parametrize("strategy", ["none", "sum", "max_explicit", "min_explicit"])
def test_factory_prepared_aspects_match_public_pair_calculation(subjects, method, strategy):
    args = subjects if method == "dual_chart_aspects" else subjects[:1]
    calculate = getattr(AspectsFactory, method)
    kwargs = dict(point_orb_adjustments={"Sun": 1.5, "Moon": -2.0}, point_orb_adjustment_strategy=strategy)
    actual = calculate(*args, **kwargs).model_dump()

    def reference(prepared, first, second):
        settings = [{"degree": degree, "orb": orb, "name": name} for degree, orb, name in prepared]
        return aspect_utils.get_aspect_from_two_points(settings, first, second)

    with patch("kerykeion.aspects.factory._get_aspect_from_prepared_settings", reference):
        assert calculate(*args, **kwargs).model_dump() == actual


def test_astrocartography_builds_models_after_releasing_backend_session(subjects, monkeypatch):
    from contextlib import contextmanager
    from kerykeion.astro_cartography import factory

    original_session = factory.ephemeris_session
    original_point = factory.ACGLinePointModel
    in_session = False

    @contextmanager
    def tracked_session():
        nonlocal in_session
        with original_session() as flags:
            in_session = True
            try:
                yield flags
            finally:
                in_session = False

    def point(**kwargs):
        assert not in_session
        return original_point(**kwargs)

    monkeypatch.setattr(factory, "ephemeris_session", tracked_session)
    monkeypatch.setattr(factory, "ACGLinePointModel", point)
    lines = factory.AstroCartographyFactory.compute(subjects[0], step=30, planets=["Sun"])
    assert {line.line_type for line in lines} == {"MC", "IC", "ASC", "DSC"}
