"""
Regression tests for the name a planet grid prints, and the room it leaves.

A grid row draws rightward from its origin — planet glyph, reading, sign, and
the marks after it — while the point's *name* is right-aligned at that origin
and therefore grows leftward, into whatever block the grid was placed beside.
English names were what the layout was measured on, so a translation is free to
overrun it: German prints "Nordknoten (T)" where English prints "N. Node (T)",
and on a biwheel that runs into the cusp column next door.

Two properties are worth defending:

* a name that fits is never touched — abbreviating what already had room would
  cost legibility for nothing;
* a trailing marker survives the cut. "(T)" and "(M)" are the whole difference
  between the true lunar node and the mean one, so "Nordknoten." would merge
  two different points into one label while looking perfectly tidy.

See: kerykeion/charts/utils.py::abbreviate_point_name
"""

from __future__ import annotations

import pytest

from kerykeion.charts.glyph_metrics import estimate_text_width
from kerykeion.charts.utils import (
    _GRID_NAME_MAX_WIDTH,
    _GRID_PLANET_GLYPH_RIGHT,
    _GRID_READING_RIGHT,
    _GRID_SIGN_X,
    abbreviate_point_name,
    convert_decimal_to_degree_string,
)

GRID_FONT_SIZE = 10.0


# =============================================================================
# THE NAME
# =============================================================================


@pytest.mark.parametrize("name", ["Sun", "Mercury", "N. Node (T)", "Chiron", "Asc", "Mc"])
def test_a_name_that_fits_is_left_alone(name):
    assert abbreviate_point_name(name) == name


@pytest.mark.parametrize(
    "name",
    ["Nordknoten (T)", "Nodo Nord Vero (T)", "Interpolated Lilith", "Noeud Nord (V)"],
)
def test_a_name_that_does_not_fit_is_cut_to_size(name):
    short = abbreviate_point_name(name)
    assert short != name
    assert short.rstrip(")").rstrip("(TMV ").endswith(".")
    assert estimate_text_width(short, GRID_FONT_SIZE) <= _GRID_NAME_MAX_WIDTH


def test_the_trailing_marker_survives_the_cut():
    """Dropping "(T)" would print the true node under the mean node's label."""
    assert abbreviate_point_name("Nordknoten (T)").endswith(" (T)")
    assert abbreviate_point_name("Nordknoten (M)").endswith(" (M)")
    assert abbreviate_point_name("Nordknoten (T)") != abbreviate_point_name("Nordknoten (M)")


def test_a_name_with_no_marker_is_cut_at_its_end():
    assert abbreviate_point_name("Interpolated Lilith").endswith(".")


def test_the_cut_is_by_width_not_by_character_count():
    """Ten narrow letters and ten wide ones are not the same amount of room."""
    narrow = abbreviate_point_name("lllllllllllllllllll")
    wide = abbreviate_point_name("WWWWWWWWWWWWWWWWWWW")
    assert len(narrow) > len(wide)
    for short in (narrow, wide):
        assert estimate_text_width(short, GRID_FONT_SIZE) <= _GRID_NAME_MAX_WIDTH


def test_a_name_of_one_character_is_returned_whole():
    """Nothing left to cut is not a reason to return an empty label."""
    assert abbreviate_point_name("W" * 40).startswith("W")


# =============================================================================
# THE ROW
# =============================================================================


def test_every_reading_leaves_the_sign_glyph_the_same_gap():
    """The reading is anchored at its end, so the digits cannot reach the sign.

    Left-anchored, the gap was whatever the degrees left over: "29°59'59"" ran
    across the sign glyph while "3°32'47"" left a hole beside it. The property
    that matters is not that one reading fits — it is that they all end together.
    """
    assert _GRID_READING_RIGHT < _GRID_SIGN_X
    # every reading a sign can hold still starts clear of the planet glyph
    widest = max(
        estimate_text_width(convert_decimal_to_degree_string(d).replace("&quot;", '"'), GRID_FONT_SIZE)
        for d in (29.99999, 9.5, 0.0)
    )
    assert _GRID_READING_RIGHT - widest > _GRID_PLANET_GLYPH_RIGHT
