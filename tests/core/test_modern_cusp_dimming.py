"""
Regression tests for the cusp line dimming under a cluster's reading.

An angle's cluster sits on its own cusp by construction, so "As 19º ♈ 45'" is
always written across the angular line, and any point within a couple of degrees
of a cusp lands on one too. Where that happens the line turns to a SOLID dimmed
tone (``COLOR_CUSP_DIM`` / ``COLOR_CUSP_DIM_OUTER`` — the pre-composited value
of the old 0.35 opacity over each ring's fill) for the length of the reading:
it passes behind the words instead of through them, keeps the text's contrast,
and cannot be washed out by a host that shows through the chart.

Four properties are worth defending, because each was got wrong on the way here:

* the trigger is geometric, never "this point is that axis" — an Ascendant is
  not always the first-house cusp, and a planet near an angle covers the line
  just as squarely;
* a mark 180° away does NOT count, though its sine is just as small;
* which side of a mark faces the line turns with the angle: height on the
  horizon, width at the Midheaven;
* all or nothing per reading — a line dimmed under some rows and solid under the
  others reads as a defect.

See: kerykeion/charts/draw_modern.py::_reading_span_on_line
"""

from __future__ import annotations

import re

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.charts.draw_modern import (
    CENTER,
    CUSP_DIM_MARGIN,
    HOUSE_LINE_INNER_Y,
    HOUSE_LINE_OUTER_Y,
    _reading_span_on_line,
)

ROW_RADII = {"glyph": 39.0, "degrees": 35.5, "sign": 32.0, "minutes": 28.0, "rx": 25.0}
PROFILE = {
    "glyph": (1.48, 1.01),
    "degrees": (1.50, 1.00),
    "sign": (0.94, 0.90),
    "minutes": (1.20, 0.93),
}
# Read from the geometry, not restated: the ring radii move when the bands
# are retuned, and a hard-coded 6.5 turns that into a failure here.
LINE_TOP, LINE_BOTTOM = HOUSE_LINE_OUTER_Y, HOUSE_LINE_INNER_Y

POINTS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus",
    "Neptune", "Pluto", "True_North_Lunar_Node", "Chiron",
]
WITH_AXES = POINTS + ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"]


def _cluster(display_angle: float) -> dict:
    return {"display_angle": display_angle, "row_half_widths": PROFILE}


def _span(line_angle: float, cluster_angle: float):
    return _reading_span_on_line(
        line_angle, LINE_TOP, LINE_BOTTOM, [_cluster(cluster_angle)], ROW_RADII
    )


# =============================================================================
# THE GEOMETRY
# =============================================================================


def test_a_reading_on_its_own_cusp_dims_the_line():
    span = _span(0.0, 0.0)
    assert span is not None
    lo, hi = span
    # from the outermost row's top to the innermost row's bottom, plus the margin
    assert lo == pytest.approx(CENTER - 39.0 - 1.01 - CUSP_DIM_MARGIN, abs=1e-6)
    assert hi == pytest.approx(CENTER - 28.0 + 0.93 + CUSP_DIM_MARGIN, abs=1e-6)


def test_the_opposite_cusp_is_left_alone():
    """180° away has a small sine for the wrong reason: it is the far side."""
    assert _span(180.0, 0.0) is None
    assert _span(0.0, 180.0) is None


def test_a_reading_far_enough_round_the_wheel_does_not_dim():
    # 8° at the glyph's radius is over five units of arc: nothing touches
    assert _span(8.0, 0.0) is None


def test_the_facing_side_turns_with_the_angle():
    """On the horizon height separates the pair, at the Midheaven width does.

    The rows here are wider than they are tall, so a cluster drawn at 90° keeps
    the line at bay further out than the same cluster drawn at 0°. Anything that
    measures only one of the two dimensions loses this.
    """
    horizon_limit = next(g for g in [x / 100 for x in range(1, 800)]
                         if _span(g, 0.0) is None)
    midheaven_limit = next(g for g in [x / 100 for x in range(1, 800)]
                           if _span(90.0 + g, 90.0) is None)
    assert midheaven_limit > horizon_limit


def test_all_or_nothing_per_reading():
    """One row touching commits the whole cluster, not just that row."""
    # a gap where only the innermost rows are close enough on their own
    gap = 1.6
    span = _span(gap, 0.0)
    assert span is not None
    lo, hi = span
    assert lo == pytest.approx(CENTER - 39.0 - 1.01 - CUSP_DIM_MARGIN, abs=1e-6)


def test_no_clusters_leaves_the_line_whole():
    assert _reading_span_on_line(0.0, LINE_TOP, LINE_BOTTOM, [], ROW_RADII) is None


def test_a_cluster_outside_the_segment_is_ignored():
    """A dual chart's inner ring must not dim the outer ring's cusps."""
    assert _reading_span_on_line(0.0, LINE_TOP, 12.0, [_cluster(0.0)], {"minutes": 10.0}) is None


# =============================================================================
# THE DRAWING
# =============================================================================


def _wheel(**kwargs) -> str:
    subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", 1940, 10, 9, 18, 30, city="Liverpool", nation="GB",
        lng=-2.97, lat=53.41, tz_str="Europe/London")
    data = ChartDataFactory.create_natal_chart_data(subject, **kwargs)
    return ChartDrawer(data, theme="classic", style="modern").generate_wheel_only_svg_string()


def _dimmed(svg: str) -> list[str]:
    return re.findall(r"<line[^>]*modern-cusp-dim[^>]*/>", svg)


def test_the_axes_readings_dim_their_own_cusps():
    """Ascendant and Medium Coeli are the two axes the modern wheel draws."""
    assert len(_dimmed(_wheel(active_points=WITH_AXES))) == 2


def test_a_wheel_without_axis_readings_keeps_its_lines_whole():
    assert _dimmed(_wheel(active_points=POINTS)) == []


def test_dual_house_lines_hang_from_the_ruler():
    """The dual rings' lines share the natal anchor — the ruler's inner edge.

    They sat 1.15 units short of it, and every dual wheel's axes visibly
    stopped mid-air (Giacomo, on the rendered chart). One constant, pinned
    so a retune of the dual bands cannot quietly re-open the gap.
    """
    from kerykeion.charts.draw_modern import SYN_HOUSE_LINE_OUTER_Y1

    assert SYN_HOUSE_LINE_OUTER_Y1 == HOUSE_LINE_OUTER_Y


def test_dimming_never_breaks_the_line():
    """The dim is a solid themable tone: same width, no opacity, no gaps.

    Solid on purpose — a stroke-opacity dim composited with whatever sat
    behind the chart, and on a see-through host the axis washed out entirely
    (the defect Giacomo photographed on the dual wheels).
    """
    svg = _wheel(active_points=WITH_AXES)
    for line in _dimmed(svg):
        assert "modern-cusp-dim" in line
        assert "stroke-opacity" not in line
        assert "stroke-width='0.6'" in line
    # the pieces of a split line still cover it end to end
    for angle in ("-0.000000", "-257.312566"):
        pieces = re.findall(
            rf"<line x1='50\.0' y1='([\d.]+)' x2='50\.0' y2='([\d.]+)'"
            rf"[^>]*stroke-width='0\.6'[^>]*rotate\({angle} ", svg)
        outer_ring = sorted((float(a), float(b)) for a, b in pieces if float(b) <= LINE_BOTTOM)
        assert outer_ring[0][0] == pytest.approx(LINE_TOP)
        assert outer_ring[-1][1] == pytest.approx(LINE_BOTTOM)
        for (_, end), (start, _) in zip(outer_ring, outer_ring[1:]):
            assert start == pytest.approx(end, abs=1e-6)
