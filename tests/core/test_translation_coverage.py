# -*- coding: utf-8 -*-
"""
Every label a chart can print has to exist in every language.

Two whole categories of string had drifted out of the translation table without
anything noticing, and both failed the same silent way: the chart still rendered,
it just rendered English in the middle of a Russian chart.

    - Seven of the eleven ``PerspectiveType`` values had no field on
      ``KerykeionLanguageModel`` and no entry in any of the ten packs. A chart
      cast Barycentric fell back to the raw literal in every language.
    - ``chart_contents``, read by the SVG ``<desc>`` for screen readers, existed
      only at its call site. Not in the model, not in a single pack — so a
      caller could not even override it: the model drops unknown keys before
      ``model_dump``, which is precisely what made it invisible.

A missing translation is not a crash, so only a test that walks the literals
themselves can catch it. These do that: add a twelfth perspective and this file
fails until the label follows it into all ten packs.

Usage:
    pytest tests/core/test_translation_coverage.py -v
"""

from typing import get_args

import pytest

from kerykeion.schemas import PerspectiveType
from kerykeion.schemas.settings_models import KerykeionLanguageModel
from kerykeion.settings.translation_strings import LANGUAGE_SETTINGS


def _field_name(perspective: str) -> str:
    """The model/pack key for a perspective literal ("True Geocentric" -> "true_geocentric")."""
    return perspective.lower().replace(" ", "_")


PERSPECTIVES = get_args(PerspectiveType)
LANGUAGES = sorted(LANGUAGE_SETTINGS)


def test_every_perspective_has_a_field_on_the_language_model():
    """The literal is the source of truth; the model has to keep up with it."""
    missing = [p for p in PERSPECTIVES if _field_name(p) not in KerykeionLanguageModel.model_fields]
    assert not missing, f"PerspectiveType values with no translation field: {missing}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_language_translates_every_perspective(language):
    """Ten packs, eleven perspectives, no gaps — an untranslated one prints English."""
    pack = LANGUAGE_SETTINGS[language]
    missing = [p for p in PERSPECTIVES if _field_name(p) not in pack]
    assert not missing, f"{language} is missing perspective labels: {missing}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_language_carries_the_accessibility_summary(language):
    """``chart_contents`` reaches a screen reader, so it cannot stay English-only."""
    assert "chart_contents" in LANGUAGE_SETTINGS[language]


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_accessibility_summary_keeps_its_placeholders(language):
    """A pack that drops {points}/{aspects} would silently announce a bare sentence."""
    pattern = LANGUAGE_SETTINGS[language]["chart_contents"]
    assert "{points}" in pattern and "{aspects}" in pattern
    # Formats without raising: the drawer falls back on KeyError/IndexError, and a
    # pack that needs the fallback is a pack that is already broken.
    assert pattern.format(points=14, aspects=31)


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_pack_still_validates_against_the_model(language):
    """New required fields must be present everywhere, not just in English."""
    KerykeionLanguageModel(**LANGUAGE_SETTINGS[language])


# =============================================================================
# A MALFORMED PATTERN COSTS THE LINE, NOT THE CHART
# =============================================================================
#
# The pack supplies the pattern now, and str.format has a different exception
# for each way of writing it wrong. The guard caught three of the five: an
# unbalanced brace, a missing key, a bad index. It did not catch the two that a
# hand-written pattern is most likely to contain, so a chart in that language
# raised instead of losing one line of its <desc>.


@pytest.mark.parametrize(
    "pattern",
    [
        "{points",  # ValueError — unbalanced brace
        "{aspects} of {missing}",  # KeyError — a name nothing supplies
        "{points.foo}",  # AttributeError — an attribute an int does not have
        "{points[0]}",  # TypeError — an int is not subscriptable
    ],
)
def test_a_broken_summary_pattern_does_not_take_the_chart_with_it(pattern):
    from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

    subject = AstrologicalSubjectFactory.from_birth_data(
        "Malformed", 1940, 10, 9, 18, 30, city="Liverpool", nation="GB",
        lng=-2.97, lat=53.41, tz_str="Europe/London",
        online=False, suppress_geonames_warning=True,
    )
    drawer = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject), theme="classic")

    real_translate = drawer._translate

    def _broken(key, default=None):
        return pattern if key == "chart_contents" else real_translate(key, default)

    drawer._translate = _broken  # type: ignore[method-assign]
    svg = drawer.generate_svg_string()

    # The chart renders, and the line falls back to the English it was built on.
    assert "<svg" in svg
    assert "points," in svg and "aspects." in svg
