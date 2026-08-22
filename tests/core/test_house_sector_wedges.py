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

import re

import pytest

from kerykeion.charts.utils import draw_house_sectors, wheel_x, wheel_y


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


def _wedge_paths(svg: str) -> list[str]:
    return re.findall(r'<path d="([^"]+)"', svg)


def _arc_flags(svg: str) -> list[int]:
    """The large-arc flag of each wedge's outer arc, in house order."""
    return [int(flag) for flag in re.findall(r"A [\d.]+,[\d.]+ 0 (\d),0 ", svg)]


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
    starts = [(float(x), float(y)) for x, y in re.findall(r"M ([\d.-]+),([\d.-]+)", svg)]
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
