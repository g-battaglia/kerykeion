# -*- coding: utf-8 -*-
"""
The transparent wedge a click lands on has to sit under the line you see.

``draw_house_sectors`` emits one invisible annular wedge per house, and the
frontend uses it to tell which house was clicked. It is bounded by the cusp
lines ``draw_house_cusp_lines`` draws — so if the two disagree, the chart looks
right and answers wrong: a click just inside a cusp selects the neighbour.

They did disagree. The classic engine quantises every angle to the whole degree
(``-int(seventh) + int(cusp)``, the same expression ``draw_planets`` uses for
glyphs), while the wedges kept the exact float degrees — up to 0.7° apart on an
ordinary chart, about 3px at r=240, despite the comment above them claiming the
two coordinate systems matched exactly.

Truncating the wedges brought a second trap with it, which is what the second
test pins: the large-arc flag was still computed from the *exact* span. Cusps
0.4° and 180.6° span 180.2° — flag set — but land 180° apart once truncated, and
SVG then draws the long way round, painting the wedge across the opposite half
of the wheel.

Usage:
    pytest tests/core/test_house_sector_wedges.py -v
"""

import math
import re

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.charts.utils import (
    MINIMUM_WEDGE_SPAN_DEGREES,
    draw_house_sectors,
    house_spans,
    wheel_x,
    wheel_y,
)


class _Cusp:
    """Minimal stand-in for KerykeionPointModel: the wedges read abs_pos only."""

    def __init__(self, abs_pos: float):
        self.abs_pos = abs_pos


def _cusps(*positions: float) -> list:
    assert len(positions) == 12
    return [_Cusp(position) for position in positions]


def _evenly_spaced_from(first_cusp: float) -> list:
    return _cusps(*[(first_cusp + 30.0 * index) % 360.0 for index in range(12)])


#: Fractional parts that differ house by house. Twelve cusps 30° apart all share
#: the same fraction, which `-int(seventh) + int(cusp)` cancels exactly — so an
#: evenly spaced ring produces the identical offsets whatever the first cusp is,
#: and five such parametrisations are one case run five times. These drift the
#: fraction instead, so the 0/360 wrap and the truncation itself are exercised.
_FRACTION_DRIFT = (0.0, 0.15, 0.31, 0.48, 0.62, 0.77, 0.83, 0.91, 0.05, 0.27, 0.55, 0.69)


def _uneven_cusps_from(first_cusp: float) -> list:
    return _cusps(
        *[
            (first_cusp + 30.0 * index + _FRACTION_DRIFT[index]) % 360.0
            for index in range(12)
        ]
    )


#: Every number an SVG path can carry, exponent included. Without the exponent a
#: coordinate written as 2.0037e-11 — which is how a point on the wheel's axis
#: comes out — tokenises as two numbers, and every index after it is off by one.
#: The reader then measures a different arc and answers confidently about it.
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

#: The same, as a capturing group, for readers that pull coordinates in pairs.
_COORD = r"(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"

#: And without a group, for the radii a reader has to step over rather than read.
_SKIP = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"


def _wedge_paths(svg: str) -> list[str]:
    return re.findall(r'<path d="([^"]+)"', svg)


def _arc_flags(svg: str) -> list[int]:
    """The large-arc flag of each wedge's outer arc, in house order."""
    return [int(flag) for flag, _ in _arc_flag_pairs(svg)]


def _arc_flag_pairs(svg: str) -> list[tuple[int, int]]:
    """(large-arc, sweep) of each wedge's outer arc. The two travel together."""
    return [
        (int(large), int(sweep))
        for large, sweep in re.findall(rf"A {_SKIP},{_SKIP} 0 (\d),(\d) ", svg)
    ][::2]


RADIUS = 240.0
FIRST_CIRCLE = 56.0
THIRD_CIRCLE = 112.0


def _draw(houses: list) -> str:
    return draw_house_sectors(
        r=RADIUS,
        houses_list=houses,
        c1=FIRST_CIRCLE,
        c3=THIRD_CIRCLE,
        chart_type="Natal",
    )


def test_a_wedge_is_emitted_for_every_house():
    svg = _draw(_evenly_spaced_from(263.7))
    assert len(_wedge_paths(svg)) == 12
    assert svg.count('kr:node="HouseSector"') == 12


@pytest.mark.parametrize("fractional_cusp", [263.7, 10.9, 0.4, 359.8, 180.2])
def test_the_wedge_boundary_matches_the_cusp_line_it_bounds(fractional_cusp):
    """Both sides quantise the same way, so neither drifts off the other.

    The reference expression is the one ``draw_house_cusp_lines`` uses for its
    own offset — reproduced here rather than imported, so that a change to
    either side has to be made deliberately on both.
    """
    houses = _uneven_cusps_from(fractional_cusp)
    seventh_house = houses[6].abs_pos
    svg = _draw(houses)

    # Both coordinates, not just x: cos is even, so an x-only assertion passes
    # happily on a sign-flipped offset. Mutating `-int(seventh) + int(cusp)` to
    # `int(seventh) - int(cusp)` has to fail here, and it does.
    starts = [(float(x), float(y)) for x, y in re.findall(rf"M {_COORD},{_COORD}", svg)]
    assert len(starts) == 12

    outer_visual_r = RADIUS - FIRST_CIRCLE
    dropin = RADIUS - outer_visual_r
    for index, house in enumerate(houses):
        cusp_line_offset = -int(seventh_house) + int(house.abs_pos)
        expected = (
            wheel_x(0, outer_visual_r, cusp_line_offset) + dropin,
            wheel_y(0, outer_visual_r, cusp_line_offset) + dropin,
        )
        assert starts[index] == pytest.approx(expected, abs=1e-9), (
            f"house {index + 1}: wedge starts at {starts[index]}, cusp line at {expected}"
        )


@pytest.mark.parametrize(
    "cusp, opposite",
    [(10.1, 190.9), (0.4, 180.6), (45.0, 225.4), (100.7, 280.9)],
)
def test_the_arc_flag_agrees_with_the_endpoints_it_steers(cusp, opposite):
    """Exact span said "long way", truncated endpoints said 180°. SVG obeyed the flag.

    Each of these pairs spans just over 180° in exact degrees and exactly 180°
    once truncated. Reading the flag from the exact span therefore set it while
    the endpoints did not warrant it, and the wedge covered the opposite half of
    the wheel.
    """
    # A house from `cusp` to `opposite`, the remaining ten cusps packed into the
    # other half so nothing else is near the boundary.
    rest = [(opposite + 1.0 + index * 1.5) % 360.0 for index in range(10)]
    houses = _cusps(cusp, opposite, *rest)
    svg = _draw(houses)

    flags = _arc_flags(svg)
    assert len(flags) == 12
    for index in range(12):
        next_index = (index + 1) % 12
        truncated_span = (int(houses[next_index].abs_pos) - int(houses[index].abs_pos)) % 360
        expected_flag = 1 if truncated_span > 180 else 0
        assert flags[index] == expected_flag, (
            f"house {index + 1}: truncated span {truncated_span}° wants flag "
            f"{expected_flag}, got {flags[index]}"
        )


# =============================================================================
# A HOUSE TOO THIN TO QUANTISE STILL HAS TO BE CLICKABLE
# =============================================================================
#
# Placidus and Campanus near the polar circle put two cusps inside the same whole
# degree, and quantising collapses them onto one offset. The first answer was to
# widen that one wedge forward by a degree — which is not an answer: it then runs
# into ground the next house already owns, the two overlap, and the frontend
# takes the first HouseSector elementsFromPoint returns, which is the one drawn
# last. The thin house stayed unclickable and its neighbour answered for it.
#
# What these pin instead is that the boundaries are separated and stay SHARED, so
# there is nothing to resolve: no overlap, no gap, and no dependence on which
# wedge happens to be painted on top.


def _boundary_offsets(svg: str) -> list[tuple[float, float]]:
    """Each wedge's start point, and the outer-arc endpoint it runs to."""
    starts = [(float(x), float(y)) for x, y in re.findall(rf"M {_COORD},{_COORD}", svg)]
    ends = [
        (float(x), float(y))
        for x, y in re.findall(rf"A {_SKIP},{_SKIP} 0 \d,0 {_COORD},{_COORD}", svg)
    ]
    return list(zip(starts, ends))


def _collapsing_cusps() -> list:
    """Houses 5 and 6 inside one whole degree — 128.3° and 128.9°."""
    rest = [(130.0 + 20.0 * index) % 360.0 for index in range(10)]
    return _cusps(128.3, 128.9, *rest)


def test_two_cusps_in_one_degree_still_give_two_wedges():
    """Neither may collapse to a zero-area path, which SVG drops outright."""
    svg = _draw(_collapsing_cusps())
    pairs = _boundary_offsets(svg)
    assert len(pairs) == 12
    for index, (start, end) in enumerate(pairs):
        assert start != end, f"house {index + 1} has a zero-area wedge"


def test_the_wedges_stay_adjacent_rather_than_overlapping():
    """Wedge i has to end exactly where wedge i+1 begins.

    This is the property the forward-widening fix broke, and it is the one that
    makes the hit test unambiguous: a shared boundary cannot be owned twice, so
    it does not matter which wedge is painted on top.
    """
    svg = _draw(_collapsing_cusps())
    pairs = _boundary_offsets(svg)
    for index in range(12):
        _, end = pairs[index]
        next_start, _ = pairs[(index + 1) % 12]
        assert end == pytest.approx(next_start, abs=1e-9), (
            f"house {index + 1} ends at {end}, house {(index + 1) % 12 + 1} starts at {next_start}"
        )


def test_an_ordinary_chart_is_not_touched_by_the_separation():
    """Every boundary still lands exactly on the cusp line it was drawn from.

    An earlier version of this docstring said the separation had to be gated
    because calling it unconditionally would shift every offset. That was not
    true even then — a reviewer showed the shift was 5e-14 px, well inside the
    tolerance below — and it is not true now: the separator returns its argument
    when nothing is under the minimum. What the test pins is the outcome, which
    is the part that matters: on an ordinary chart the wedges sit on the lines.
    """
    houses = _uneven_cusps_from(263.7)
    seventh_house = houses[6].abs_pos
    svg = _draw(houses)

    outer_visual_r = RADIUS - FIRST_CIRCLE
    dropin = RADIUS - outer_visual_r
    starts = [start for start, _ in _boundary_offsets(svg)]
    for index, house in enumerate(houses):
        offset = -int(seventh_house) + int(house.abs_pos)
        expected = (
            wheel_x(0, outer_visual_r, offset) + dropin,
            wheel_y(0, outer_visual_r, offset) + dropin,
        )
        assert starts[index] == pytest.approx(expected, abs=1e-12)


def test_three_cusps_in_one_degree_come_apart_too():
    """Widening one wedge by a fixed degree cannot survive a third neighbour.

    It would hand house i ground that houses i+1 AND i+2 both claim. Separating
    the boundaries has no such ceiling: the spread pushes as many as it must.
    """
    rest = [(132.0 + 20.0 * index) % 360.0 for index in range(9)]
    svg = _draw(_cusps(128.2, 128.5, 128.9, *rest))
    pairs = _boundary_offsets(svg)
    for index, (start, end) in enumerate(pairs):
        assert start != end, f"house {index + 1} collapsed"
    for index in range(12):
        _, end = pairs[index]
        next_start, _ = pairs[(index + 1) % 12]
        assert end == pytest.approx(next_start, abs=1e-9)


def test_the_dual_outer_ring_keeps_its_exact_degrees():
    """Full precision there, so nothing collapses and nothing is separated."""
    houses = _uneven_cusps_from(11.4)
    seventh_house = houses[6].abs_pos
    svg = draw_house_sectors(
        r=RADIUS,
        houses_list=houses,
        c1=FIRST_CIRCLE,
        c3=THIRD_CIRCLE,
        chart_type="Synastry",
        quantize_offsets_to_whole_degrees=False,
    )
    outer_visual_r = RADIUS - 72
    dropin = RADIUS - outer_visual_r
    starts = [start for start, _ in _boundary_offsets(svg)]
    for index, house in enumerate(houses):
        offset = -seventh_house + house.abs_pos
        expected = (
            wheel_x(0, outer_visual_r, offset) + dropin,
            wheel_y(0, outer_visual_r, offset) + dropin,
        )
        assert starts[index] == pytest.approx(expected, abs=1e-12)


def test_a_span_a_hair_negative_does_not_paint_the_long_way_round():
    """Two cusps out of order by one ULP must not produce a 360° wedge.

    `% 360` alone answers exactly 360.0 for a span of -1e-15, and 360 > 180 sets
    the large-arc flag: the wedge is drawn across the whole annulus, invisible,
    and with pointer-events:all it swallows every click meant for the houses
    under it.

    Two guards now stand between this input and that outcome — the boundary
    separation reaches it first, and normalize_degree sits behind it — so this
    pins the outcome rather than either mechanism. Which is the honest thing to
    assert: remove the second guard alone and this stays green.
    """
    # The pair has to stay out of order *after* the seventh cusp is subtracted.
    # 47.0 does not: 47.0 - 150.0 and nextafter(47.0, 0) - 150.0 are the same
    # double, so the ULP this test is named for never reached the code and the
    # assertion below passed on an input it was not testing.
    later = 47.3
    earlier = math.nextafter(later, 0.0)
    rest = [(50.0 + 25.0 * index) % 360.0 for index in range(10)]
    houses = _cusps(later, earlier, *rest)
    assert earlier - houses[6].abs_pos < later - houses[6].abs_pos, (
        "the ULP does not survive the subtraction; pick another pair"
    )
    svg = draw_house_sectors(
        r=RADIUS,
        houses_list=houses,
        c1=FIRST_CIRCLE,
        c3=THIRD_CIRCLE,
        chart_type="Synastry",
        quantize_offsets_to_whole_degrees=False,
    )
    assert _arc_flags(svg) == [0] * 12
    # Flags alone would miss a wedge drawn backwards at full length, which is how
    # this failed in practice: read the widths as drawn and count the circle.
    assert sum(_spans_from(svg)) == pytest.approx(360.0, abs=1e-6)


# =============================================================================
# HOUSES THAT RUN BACKWARDS
# =============================================================================
#
# Above roughly 68 degrees a Campanus, Regiomontanus, Sunshine, topocentric or
# APC chart puts its cusps in descending order, and the horizon system does it
# on the equator. The houses are real and so are their widths; what reverses is
# the direction they run through the signs. Read forwards, each six-degree house
# measured 354, the twelve of them wound round the wheel eleven times, and every
# wedge was painted as a near-complete invisible ring with pointer-events:all —
# so a click anywhere on the chart was answered by whichever was drawn last.


#: Campanus at 70N, 1990-06-21 00:00 UTC. Descending, and crowded with it.
_RETROGRADE_CUSPS = (
    304.76, 290.74, 288.71, 287.47, 286.02, 282.30,
    124.76, 110.74, 108.71, 107.47, 106.02, 102.30,
)


def _outer_arc_centre(path: str) -> tuple[float, float]:
    """The centre of the circle the wedge's outer arc is actually drawn on.

    SVG puts two circles of the given radius through any two points, and the
    (large-arc, sweep) pair picks which one. Correcting the span without the
    sweep chooses the mirrored circle: the arc keeps its endpoints and leaves
    the wheel entirely, which no endpoint-only check can see. Recovering the
    centre from the path is the only reading that can.
    """
    numbers = [float(value) for value in re.findall(_NUMBER, path)]
    x1, y1, radius = numbers[0], numbers[1], numbers[2]
    large, sweep = int(numbers[5]), int(numbers[6])
    x2, y2 = numbers[7], numbers[8]
    # F.6.5 of the SVG specification, for the rx == ry == radius case.
    dx, dy = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    scale = max(radius * radius - dx * dx - dy * dy, 0.0) / max(dx * dx + dy * dy, 1e-12)
    coefficient = math.sqrt(scale)
    if large == sweep:
        coefficient = -coefficient
    return (
        coefficient * dy + (x1 + x2) / 2.0,
        -coefficient * dx + (y1 + y2) / 2.0,
    )


def _spans_from(svg: str) -> list[float]:
    """Each wedge's width, taken from the arc as drawn rather than the cusps.

    The centre comes from the arc itself: the wedge coordinates are offset by the
    ring's inset, so the radius is not the centre and assuming it is turns every
    angle into nonsense.
    """
    spans = []
    for path in _wedge_paths(svg):
        numbers = [float(value) for value in re.findall(_NUMBER, path)]
        cx, cy = _outer_arc_centre(path)
        sweep = int(numbers[6])
        start = math.degrees(math.atan2(numbers[1] - cy, numbers[0] - cx))
        end = math.degrees(math.atan2(numbers[8] - cy, numbers[7] - cx))
        spans.append((start - end) % 360.0 if sweep == 0 else (end - start) % 360.0)
    return spans


#: Campanus at 68N, Tromso, 1980-03-21 03:58 UTC. Ordinary in the zodiac — the
#: twelve gaps are all positive and sum to 360 — but once the ring is quantised,
#: house 12 and house 1 land on the same whole degree, and it is the *wrap* pair
#: that collapses.
_WRAP_COLLAPSE_CUSPS = (
    250.3407, 69.8374, 69.9318, 69.9669, 69.9964, 70.0434,
    70.3407, 249.8374, 249.9318, 249.9669, 249.9964, 250.0434,
)


def test_the_wrap_pair_collapsing_does_not_reorder_the_houses():
    """House 12 and house 1 on one degree used to swap places.

    The twelve boundaries were handed to spread_around_wheel, which sorts what it
    is given and breaks ties by list index — an order that is not the order round
    the wheel. With boundary 11 equal to boundary 0, index 0 sorted first, the two
    came back swapped, and the twelfth wedge was drawn backwards across 359
    degrees: invisible, pointer-events:all, last in the document, and therefore
    the answer to every click on the chart. The twelve totalled 720 degrees.

    They are separated in house order now, so the order cannot change.
    """
    svg = _draw(_cusps(*_WRAP_COLLAPSE_CUSPS))
    spans = _spans_from(svg)
    assert len(spans) == 12
    assert sum(spans) == pytest.approx(360.0, abs=1e-6), spans
    assert max(spans) <= 180.0, spans
    assert min(spans) >= MINIMUM_WEDGE_SPAN_DEGREES - 1e-9, spans


def test_a_separated_chart_still_hands_each_wedge_to_the_next():
    """Shared boundaries: no overlap to resolve, no gap to fall through."""
    svg = _draw(_cusps(*_WRAP_COLLAPSE_CUSPS))
    pairs = _boundary_offsets(svg)
    for index in range(12):
        _, end = pairs[index]
        next_start, _ = pairs[(index + 1) % 12]
        assert end == pytest.approx(next_start, abs=1e-9)


def test_house_spans_reads_the_direction_from_all_twelve():
    """One house may run past 180 on its own; only the total tells them apart."""
    ascending = [index * 30.0 for index in range(12)]
    spans, reversed_wedges = house_spans(ascending)
    assert reversed_wedges == [False] * 12
    assert spans == pytest.approx([30.0] * 12)

    spans, reversed_wedges = house_spans(list(_RETROGRADE_CUSPS))
    assert reversed_wedges == [True] * 12
    assert sum(spans) == pytest.approx(360.0)
    assert max(spans) < 180.0

    # Placidus at high latitude: one enormous house, the rest tiny, all forward.
    # Taking the shorter arc pair by pair would halve it; the total is what says
    # the set is ordered, so it stays whole.
    lopsided = [0.0, 200.0, 210.0, 220.0, 230.0, 240.0, 250.0, 260.0, 270.0, 280.0, 290.0, 300.0]
    spans, reversed_wedges = house_spans(lopsided)
    assert reversed_wedges == [False] * 12
    assert max(spans) == pytest.approx(200.0)

    # Polich/Page at 70N: the first cusp runs back while the next five run on, so
    # houses 1 and 2 overlap and no direction tiles. Each wedge keeps its shorter
    # arc, which is the only reading in which none of them swallows the wheel.
    tangled = [
        304.76, 279.48, 280.86, 287.47, 296.49, 311.82,
        124.76, 99.48, 100.86, 107.47, 116.49, 131.82,
    ]
    spans, reversed_wedges = house_spans(tangled)
    assert any(reversed_wedges) and not all(reversed_wedges)
    assert max(spans) <= 180.0


def test_a_retrograde_chart_tiles_the_ring_exactly():
    """Twelve wedges, no overlap, no gap, and 360 degrees between them."""
    svg = _draw(_cusps(*_RETROGRADE_CUSPS))
    spans = _spans_from(svg)
    assert len(spans) == 12
    assert sum(spans) == pytest.approx(360.0, abs=1e-6)
    assert max(spans) < 180.0, "no wedge should still be painted the long way"


def test_a_retrograde_wedge_stays_on_its_own_ring():
    """The half of the fix an endpoint check cannot see.

    Shortening the span without flipping the sweep leaves the endpoints where
    they were and moves the arc onto the mirrored circle. The two candidate
    centres for a chord are 2*sqrt(r^2 - (chord/2)^2) apart, so for a narrow wedge
    that is very nearly twice the radius: 368 units on this fixture, where the
    ring is 184. All twelve arcs have to share one centre.
    """
    svg = _draw(_cusps(*_RETROGRADE_CUSPS))
    centres = [_outer_arc_centre(path) for path in _wedge_paths(svg)]
    assert len(centres) == 12
    mean_x = sum(x for x, _ in centres) / 12.0
    mean_y = sum(y for _, y in centres) / 12.0
    for x, y in centres:
        assert math.hypot(x - mean_x, y - mean_y) < 0.01, (x, y, mean_x, mean_y)


def test_an_ordinary_chart_keeps_the_sweeps_it_always_had():
    """Nothing below the polar circle may move: outer sweep 0, inner sweep 1."""
    svg = _draw(_uneven_cusps_from(263.7))
    assert _arc_flag_pairs(svg)
    for large, sweep in _arc_flag_pairs(svg):
        assert sweep == 0, "an ordinary chart's outer arc has always swept 0"
    assert sum(_spans_from(svg)) == pytest.approx(360.0, abs=1e-6)


@pytest.mark.parametrize(
    "system,lat,lng",
    [
        ("C", 70.0, 20.0),   # Campanus, inside the polar circle
        ("C", 68.0, 20.0),   # Campanus again, where two cusps sit 0.163 apart:
                             # the width has to be traded, not conjured, or the
                             # twelve stop covering exactly one circle
        ("R", 69.0, 20.0),   # Regiomontanus
        ("H", 0.0, 20.0),    # the horizon system, on the equator
        ("Y", 76.0, 20.0),   # APC
        ("P", 45.0, 9.0),    # and one ordinary chart, which must not move
    ],
)
@pytest.mark.parametrize("style", ["classic", "modern"])
def test_a_real_chart_of_every_reversing_system_tiles_its_ring(system, lat, lng, style):
    """End to end, because the two engines draw the wedges independently."""
    total = sum(_rendered_spans(system, lat, lng, style))
    assert total == pytest.approx(360.0, abs=1e-4), f"{system} {style}: {total}"


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_a_chart_whose_cusps_cross_keeps_every_wedge_small(style):
    """Polich/Page at 70N: houses 1 and 2 genuinely overlap, so nothing tiles.

    What must not happen is the one thing that used to: a wedge running 334
    degrees, invisible, with pointer-events:all, taking every click on the wheel.
    """
    spans = _rendered_spans("T", 70.0, 20.0, style)
    assert len(spans) == 12
    assert max(spans) <= 180.0 + 1e-6, spans


def _rendered_spans(system: str, lat: float, lng: float, style: str) -> list[float]:
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Reversed", 1990, 6, 21, 0, 0, city="X", nation="XX", online=False,
        suppress_geonames_warning=True, tz_str="UTC", lat=lat, lng=lng,
        houses_system_identifier=system,
    )
    svg = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject)).generate_svg_string(
        style=style
    )
    sectors = re.findall(
        r"<g kr:node='HouseSector' kr:house='\d+'[^>]*><path d='([^']+)'", svg
    )
    assert len(sectors) == 12
    spans = []
    centres = []
    for path in sectors:
        numbers = [float(value) for value in re.findall(_NUMBER, path)]
        cx, cy = _outer_arc_centre(path)
        centres.append((cx, cy))
        sweep = int(numbers[6])
        start = math.degrees(math.atan2(numbers[1] - cy, numbers[0] - cx))
        end = math.degrees(math.atan2(numbers[8] - cy, numbers[7] - cx))
        spans.append((start - end) % 360.0 if sweep == 0 else (end - start) % 360.0)

    # Every caller of this reader gets the mirrored-circle check for free, and
    # that matters: the span is measured against each wedge's *own* recovered
    # centre, so a wedge lifted off the ring is perfectly self-consistent and its
    # total still comes to 360. Only comparing the twelve centres to each other
    # can see it — and until this line the modern engine had no check at all,
    # so its sweep flip could be reverted with the whole suite staying green.
    mean_x = sum(x for x, _ in centres) / 12.0
    mean_y = sum(y for _, y in centres) / 12.0
    for x, y in centres:
        assert math.hypot(x - mean_x, y - mean_y) < 0.01, (
            f"{system} {style}: a wedge was drawn on a circle of its own, "
            f"centred ({x:.3f}, {y:.3f}) against ({mean_x:.3f}, {mean_y:.3f})"
        )
    return spans


# =============================================================================
# CUSPS THAT CROSS, RATHER THAN MERELY RUN BACKWARDS
# =============================================================================
#
# Polich/Page above the polar circle, and Sunshine/alt, return cusps that are not
# ordered at all: one house runs back while the next few run on, so the houses
# genuinely overlap and no direction makes the twelve tile a circle. The
# separation cannot widen a wedge on such a ring — there is no width to trade —
# and a wedge left at zero puts both ends of its arc on one point. SVG drops the
# arc segment, and what remains is a path of no area still declaring
# pointer-events:all: a house that can never be clicked, which is the exact
# failure the separation exists to prevent. Sunshine at 67N produced six of them
# in a single chart.


@pytest.mark.parametrize(
    "system,lat",
    [
        ("i", 67.0),   # Sunshine/alt: six dead wedges in one chart before the guard
        ("T", 70.0),   # Polich/Page
        ("i", 66.5),  # both engines force six wedges here
        ("T", 74.0),
    ],
)
@pytest.mark.parametrize("style", ["classic", "modern"])
def test_a_chart_whose_cusps_cross_still_gives_every_house_a_target(system, lat, style):
    """No wedge of zero area, and none under the minimum, however tangled.

    Every case here has to actually reach the guard, or it is asserting that a
    chart which never needed it came out fine. Two of the four fixtures used to
    do exactly that — the guard fired zero times on them in either engine — so
    the test below counts the wedges it had to widen and refuses to pass on none.
    """
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Tangled", 1985, 10, 15, 14, 0, city="X", nation="XX", online=False,
        suppress_geonames_warning=True, tz_str="UTC", lat=lat, lng=25.0,
        houses_system_identifier=system,
    )
    svg = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject)).generate_svg_string(
        style=style
    )
    sectors = re.findall(
        r"<g kr:node='HouseSector' kr:house='(\d+)'[^>]*><path d='([^']+)'", svg
    )
    assert len(sectors) == 12
    widened = 0
    for house, path in sectors:
        numbers = [float(value) for value in re.findall(_NUMBER, path)]
        start = (numbers[0], numbers[1])
        end = (numbers[7], numbers[8])
        assert math.hypot(start[0] - end[0], start[1] - end[1]) > 1e-6, (
            f"house {house} has no arc at all: {start} to {end}"
        )
        radius = numbers[2]
        chord = math.hypot(start[0] - end[0], start[1] - end[1])
        span = 2 * math.degrees(math.asin(min(chord / (2 * radius), 1.0)))
        if int(numbers[5]) == 1:
            span = 360.0 - span
        # The path writes six decimals, so the recovered angle carries about
        # 1.4e-6 of its own; the tolerance is that, not slack in the rule.
        assert span >= MINIMUM_WEDGE_SPAN_DEGREES - 1e-5, f"house {house}: {span:.6f} deg"
        if abs(span - MINIMUM_WEDGE_SPAN_DEGREES) < 1e-5:
            widened += 1
    assert widened, (
        f"{system} at {lat}N in {style} never reached the guard, so this case "
        f"proves nothing about it — pick a chart whose cusps actually cross"
    )


def test_a_tangled_ring_is_not_rebuilt_around_a_direction_it_does_not_have():
    """The separator hands back what it was given when the cusps cross.

    Its rebuild walks the twelve in one direction, adding each width to the last.
    That only means something on a ring that runs one way. On a ring whose cusps
    cross there is no such direction, and walking it anyway would move every
    boundary off the cusp line it was drawn from to build a tiling the cusps do
    not describe. The thin wedges are widened where they are, one at a time, by
    the guard in the drawing loop.

    Sunshine/alt at 67N, quantised: two of the twelve widths are zero, so the
    separator is genuinely asked to do something and declines.
    """
    from kerykeion.charts.utils import house_spans, separate_collapsed_wedges

    tangled = [-180.0, -179.0, -179.0, -180.0, -180.0, -180.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    spans, reversed_wedges = house_spans(tangled)
    assert len(set(reversed_wedges)) > 1, "fixture no longer has crossing cusps"
    assert min(spans) < MINIMUM_WEDGE_SPAN_DEGREES, "fixture no longer asks for a widening"

    boundaries, widths = separate_collapsed_wedges(
        tangled, spans, reversed_wedges, MINIMUM_WEDGE_SPAN_DEGREES
    )
    assert boundaries == list(tangled)
    assert widths == list(spans)
