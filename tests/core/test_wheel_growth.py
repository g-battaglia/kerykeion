"""
Regression tests for the wheel growing on a canvas that has room for it.

A chart with every point active is drawn on a canvas twice the usual height,
because the aspect grid is a pyramid and 52 points make a tall one. The wheel
is not: it is a fixed 480 across whatever else happens, so on that canvas it
occupied 13% of the page and its glyphs were the same 20 pixels they are on a
chart a quarter the size. It grows now — but only there.

Two things have to hold, and the second is why this file exists at all:

* an ordinary chart is untouched, **byte for byte**. The comparator the SVG
  baselines use allows fifty percent on every number and returns silently when
  the non-numeric skeleton differs, so it would not notice a ``scale()``
  appearing on the wheel. Nothing else in the suite would either.
* the glyph centres follow. ``kr:cx``/``kr:cy`` are rebased into root space by
  an affine map, and its scale and translate both change here. Getting the
  translate wrong shifts every centre by 72 pixels in silence — the existing
  contract test uses a 14-point natal, where the scale is 1 and the bug is
  invisible. That regression has happened before; see release_notes/v6.0.0a64.

See: kerykeion/charts/drawer.py::_wheel_growth_scale
"""

from __future__ import annotations

import re
from typing import get_args

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.schemas.literals import AstrologicalPoint

_BIRTH = dict(
    city="Liverpool", nation="GB", lng=-2.97, lat=53.41,
    tz_str="Europe/London", online=False, suppress_geonames_warning=True,
)
_ALL_POINTS = list(get_args(AstrologicalPoint))

#: Point counts that land in each band, measured: 18 -> 550, 54 -> 814, 76 -> 1067.
_ORDINARY, _MID, _TALL = 18, 54, len(_ALL_POINTS)

WHEEL_TRANSFORM = re.compile(r"kr:node='Full_Wheel' transform='([^']+)'")
CHART_POINT = re.compile(r"kr:cx='([-\d.]+)' kr:cy='([-\d.]+)'")


def _subject(point_count: int):
    return AstrologicalSubjectFactory.from_birth_data(
        "Growth", 1940, 10, 9, 18, 30, active_points=_ALL_POINTS[:point_count], **_BIRTH
    )


def _chart(point_count: int, **kwargs) -> ChartDrawer:
    return ChartDrawer(
        ChartDataFactory.create_natal_chart_data(_subject(point_count)),
        theme="classic",
        **kwargs,
    )


def _wheel_transform(svg: str) -> str:
    match = WHEEL_TRANSFORM.search(svg)
    assert match, "no Full_Wheel group in the output"
    return match.group(1)


# =============================================================================
# ORDINARY CHARTS DO NOT MOVE
# =============================================================================


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_an_ordinary_chart_carries_no_scale_at_all(style):
    """Not "scale(1)" — no scale. The string has to be the one it always was."""
    svg = _chart(_ORDINARY, style=style).generate_svg_string()
    assert _wheel_transform(svg) == "translate(100,50)"


@pytest.mark.parametrize("point_count", [18, 26, 34, 44, 52])
def test_every_canvas_below_the_threshold_is_left_alone(point_count):
    """52 points reach 798, four short of the gate. The band is narrow on purpose."""
    chart = _chart(point_count)
    assert chart.height < 800
    assert chart._wheel_growth_scale() == 1.0
    assert " scale(" not in _wheel_transform(chart.generate_svg_string())


def test_a_chart_that_opted_out_of_auto_size_never_grows():
    """Turning auto_size off freezes the width but not the height.

    So a chart with 76 points and auto_size=False is already drawing its grid
    over its own wheel at nominal size. A gate on height alone would fire on
    exactly the case that has no room at all.
    """
    chart = _chart(_TALL, auto_size=False)
    assert chart.height >= 800
    assert chart._wheel_growth_scale() == 1.0


def test_a_dual_wheel_never_grows():
    """Its planet grid sits hard against the rings: ink touches at 1.05."""
    john = _subject(_ORDINARY)
    paul = AstrologicalSubjectFactory.from_birth_data(
        "Paul", 1942, 6, 18, 15, 30, active_points=_ALL_POINTS[:_TALL], **_BIRTH
    )
    chart = ChartDrawer(
        ChartDataFactory.create_synastry_chart_data(john, paul), theme="classic"
    )
    assert chart._wheel_growth_scale() == 1.0


# =============================================================================
# THE TALL ONES GROW, AND STAY WHERE THEY WERE ANCHORED
# =============================================================================


def test_the_two_bands():
    assert _chart(_MID)._wheel_growth_scale() == pytest.approx(1.15)
    assert _chart(_TALL)._wheel_growth_scale() == pytest.approx(1.45)


@pytest.mark.parametrize("point_count", [_MID, _TALL])
def test_the_wheel_grows_downward_from_nowhere(point_count):
    """The foot of the wheel does not move: it grows into the space above it.

    Anchoring at the top instead is what would push it into the info panel —
    the rows sit under the wheel's centre and the chord narrows as it rises.
    """
    chart = _chart(point_count)
    svg = chart.generate_svg_string()
    transform = _wheel_transform(svg)
    match = re.fullmatch(r"translate\(100,(-?\d+)\) scale\(([\d.]+)\)", transform)
    assert match, transform
    translate_y, scale = int(match.group(1)), float(match.group(2))
    nominal_bottom = chart._vertical_offsets["wheel"] + 2 * chart.main_radius
    assert translate_y + 2 * chart.main_radius * scale == pytest.approx(nominal_bottom, abs=1.0)


@pytest.mark.parametrize("point_count", [_MID, _TALL])
def test_the_canvas_does_not_grow_with_the_wheel(point_count):
    """The whole point is to spend room the page already has, not to ask for more."""
    grown = _chart(point_count)
    frozen = _chart(point_count)
    frozen._wheel_growth_scale = lambda: 1.0  # type: ignore[method-assign]
    assert (grown.width, grown.height) == (frozen.width, frozen.height)


# =============================================================================
# THE GLYPH CENTRES FOLLOW — THE 72-PIXEL TRAP
# =============================================================================


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_the_reported_glyph_centres_move_with_the_wheel(style):
    """kr:cx/kr:cy are root-space, so they must carry the growth exactly.

    Undone by the map that placed them, a point's centre is the same wheel-local
    coordinate whether the wheel is drawn at nominal size or larger. If the
    rebase is handed the old translate instead of the new one, every centre
    lands 72 pixels off and every assertion that only ever sees a 14-point natal
    stays green.
    """
    chart = _chart(_TALL, style=style)
    svg = chart.generate_svg_string()
    scale = chart._wheel_scale
    translate_y = chart._wheel_translate_y
    assert scale > 1.0, "fixture no longer exercises a grown wheel"

    frozen = _chart(_TALL, style=style)
    frozen._wheel_growth_scale = lambda: 1.0  # type: ignore[method-assign]
    frozen_svg = frozen.generate_svg_string()

    grown = [
        ((float(x) - 100.0) / scale, (float(y) - translate_y) / scale)
        for x, y in CHART_POINT.findall(svg)
    ]
    plain = [
        (float(x) - 100.0, float(y) - frozen._wheel_translate_y)
        for x, y in CHART_POINT.findall(frozen_svg)
    ]
    assert grown and len(grown) == len(plain)
    for (gx, gy), (px, py) in zip(grown, plain):
        assert gx == pytest.approx(px, abs=0.01)
        assert gy == pytest.approx(py, abs=0.01)


def test_a_reported_centre_lands_inside_the_wheel():
    """A blunt sanity check the affine map cannot satisfy by accident."""
    chart = _chart(_TALL)
    svg = chart.generate_svg_string()
    top = chart._wheel_translate_y
    bottom = top + 2 * chart.main_radius * chart._wheel_scale
    right = 100.0 + 2 * chart.main_radius * chart._wheel_scale
    centres = CHART_POINT.findall(svg)
    assert centres
    for x, y in centres:
        assert 100.0 <= float(x) <= right, f"cx {x} outside the wheel"
        assert top <= float(y) <= bottom, f"cy {y} outside the wheel"
