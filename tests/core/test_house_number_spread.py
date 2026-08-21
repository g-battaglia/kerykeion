"""
Regression tests for how far apart two house numbers are pushed.

A quadrant system at high latitude puts four cusps inside three degrees, so
four numbers want the same patch of ring and have to be spread. How much room
each pair needs is not one figure: a number is drawn upright while the arc it
sits on turns, so two of them at the top of the wheel stand side by side and
their *widths* meet, while the same two on the flank stack and only their
*heights* do. Charging every pair the width of "12" is safe and, on the flank,
half again as much as the pair needs — enough to walk a crowd of numbers out of
the houses they belong to, which is what a reader notices.

See: kerykeion/charts/utils.py::_house_number_half_extents
     kerykeion/charts/spreading.py::spread_around_wheel
"""

from __future__ import annotations

import math

import pytest

from kerykeion.charts.glyph_metrics import estimate_text_width
from kerykeion.charts.spreading import spread_around_wheel
from kerykeion.charts.utils import _house_number_half_extents, label_separation_degrees

LABEL_RADIUS = 120.0  # the natal wheel's house-number ring


def _pair_gap(angle_a: float, angle_b: float) -> float:
    """Degrees the spread leaves between two labels that both want the same spot."""
    wanted = [angle_a, angle_b] + [angle_a + 40.0 * i for i in range(2, 12)]
    placed = spread_around_wheel(
        wanted, 0.0, half_extents=_house_number_half_extents(wanted, LABEL_RADIUS)
    )
    return abs((placed[1] - placed[0] + 180.0) % 360.0 - 180.0)


# =============================================================================
# THE REACH TURNS WITH THE ANGLE
# =============================================================================


def _extent_of_house(house_number: int, angle: float) -> float:
    """The reach of one house's label, placed at *angle*.

    The label is the house's own number, so it has to be asked for by position:
    "12" is twice the width of "1" and the same height.
    """
    angles = [0.0] * 12
    angles[house_number - 1] = angle
    return _house_number_half_extents(angles, LABEL_RADIUS)[house_number - 1]


def test_a_two_figure_number_reaches_less_on_the_flank_than_at_the_top():
    """Same label, same radius — only the direction it stacks in changes.

    "12" is wider than it is tall, so on the flank, where its height is what
    meets its neighbour, it asks for less room. This is the case the crowd at
    high latitude actually hits.
    """
    assert _extent_of_house(12, 180.0) < _extent_of_house(12, 90.0)


def test_a_one_figure_number_is_the_other_way_round():
    """Not a special case to be fixed — a digit is taller than it is wide.

    The projection is not "use the smaller dimension": it is the label's own
    box seen from the direction its neighbour approaches. For "1" that is more
    room on the flank, not less, and pretending otherwise would let two of them
    touch.
    """
    assert _extent_of_house(1, 180.0) > _extent_of_house(1, 90.0)


def test_the_projection_collapses_to_one_dimension_at_the_quarter_points():
    """Both flanks alike, and neither of them the same as the top."""
    assert _extent_of_house(12, 0.0) == pytest.approx(_extent_of_house(12, 180.0))
    assert _extent_of_house(12, 90.0) == pytest.approx(_extent_of_house(12, 270.0))
    assert _extent_of_house(12, 0.0) != pytest.approx(_extent_of_house(12, 90.0))


def test_the_flank_asks_for_less_than_the_old_uniform_figure():
    """Where the crowding shows, the new rule is the cheaper one."""
    old_uniform = label_separation_degrees(estimate_text_width("12", 14), LABEL_RADIUS)
    for house in (10, 11, 12):
        for angle in (0.0, 180.0):
            assert 2 * _extent_of_house(house, angle) < old_uniform


def test_a_corner_to_corner_pair_asks_for_more_than_either_flank_or_top():
    """Two upright boxes approaching corner first need more than one dimension.

    The projection onto the tangent adds the width and the height in proportion
    and peaks near the diagonal, so the worst angle for a pair is neither of the
    quarter points. It stays bounded by the box's own diagonal, which is the
    most a rectangle can project in any direction.
    """
    diagonal = label_separation_degrees(
        math.hypot(estimate_text_width("12", 14), 14 * 0.716), LABEL_RADIUS, gutter_px=0.0
    )
    by_angle = {a: 2 * _extent_of_house(12, float(a)) for a in range(0, 360, 5)}
    worst_angle = max(by_angle, key=by_angle.get)
    assert by_angle[worst_angle] > 2 * _extent_of_house(12, 0.0)
    assert by_angle[worst_angle] > 2 * _extent_of_house(12, 90.0)
    assert by_angle[worst_angle] <= diagonal + 1e-9


def test_two_crowded_numbers_on_the_flank_end_closer_than_at_the_top():
    """The whole point: the crowd on the flank keeps more of its own ground."""
    assert _pair_gap(179.0, 180.0) < _pair_gap(89.0, 90.0)


# =============================================================================
# WHAT THE SPREAD STILL GUARANTEES
# =============================================================================


def test_numbers_that_are_already_comfortable_are_not_moved():
    wanted = [i * 30.0 for i in range(12)]
    placed = spread_around_wheel(
        wanted, 0.0, half_extents=_house_number_half_extents(wanted, LABEL_RADIUS)
    )
    for before, after in zip(wanted, placed):
        assert after == pytest.approx(before % 360.0, abs=1e-9)


def test_a_crowd_is_separated_by_at_least_what_its_labels_need():
    wanted = [180.0, 180.4, 180.8, 181.2] + [200.0 + 15.0 * i for i in range(8)]
    extents = _house_number_half_extents(wanted, LABEL_RADIUS)
    placed = spread_around_wheel(wanted, 0.0, half_extents=extents)
    order = sorted(range(len(placed)), key=lambda i: placed[i])
    for a, b in zip(order, order[1:]):
        gap = placed[b] - placed[a]
        assert gap >= extents[a] + extents[b] - 1e-6


def test_the_order_of_the_numbers_survives_the_spread():
    """1 through 12 must still read in order round the wheel."""
    wanted = [180.0, 180.4, 180.8, 181.2] + [200.0 + 15.0 * i for i in range(8)]
    placed = spread_around_wheel(
        wanted, 0.0, half_extents=_house_number_half_extents(wanted, LABEL_RADIUS)
    )
    assert placed[0] < placed[1] < placed[2] < placed[3]


def test_a_uniform_separation_still_works():
    """The old signature is untouched: one figure for every pair."""
    wanted = [180.0, 180.5, 181.0] + [200.0 + 15.0 * i for i in range(9)]
    placed = spread_around_wheel(wanted, 10.0)
    assert placed[1] - placed[0] == pytest.approx(10.0)
    assert placed[2] - placed[1] == pytest.approx(10.0)


def test_more_labels_than_the_circle_holds_share_the_shortfall():
    """Twelve labels wanting 40° each cannot all have it; none may pile up."""
    wanted = [i * 30.0 for i in range(12)]
    placed = spread_around_wheel(wanted, 40.0)
    gaps = [(placed[(i + 1) % 12] - placed[i]) % 360.0 for i in range(12)]
    assert max(gaps) - min(gaps) < 1e-6
    assert sum(gaps) == pytest.approx(360.0)


def test_the_reach_is_zero_at_a_degenerate_radius():
    assert _house_number_half_extents([0.0, 90.0], 0.0) == [0.0, 0.0]
    assert math.isfinite(_house_number_half_extents([0.0], 1.0)[0])
