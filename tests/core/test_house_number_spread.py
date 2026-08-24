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
import re

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.charts.glyph_metrics import estimate_text_width
from kerykeion.charts.spreading import spread_around_wheel
from kerykeion.charts.utils import (
    _house_number_half_extents,
    label_separation_degrees,
    wheel_x,
    wheel_y,
)

#: The ring the natal wheel draws its house numbers on: ``r - 48``, the inset
#: ``draw_houses_cusps_and_text_number`` uses for the text. Not ``r - c3``, the
#: radius the cusp *line* ends at, which is 120 and where the extents used to be
#: measured — a reach in degrees is a reach in pixels over the arc a degree
#: covers, so that radius made every extent 1.6x too large.
LABEL_RADIUS = 192.0


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


def test_a_tight_crowd_spreads_into_the_empty_wheel_beside_it():
    """The budget is the circle, not the crowd's own width.

    The shrink used to be measured against ``unrolled[-1] - unrolled[0]`` — the
    span the labels already occupied. A crowd was therefore told it had only its
    own width to work with, scaled its requirement down to exactly the spacing it
    already had, and came back untouched: twelve labels 3.6° apart asking for
    4.31° stayed 3.6° apart with 320° of wheel standing empty next to them.
    """
    wanted = [i * 3.6 for i in range(12)]
    placed = spread_around_wheel(wanted, 4.31)
    # Circular gaps: a crowd centred on 19.8° and widened to 47.4° reaches back
    # past 0°, and the label that lands at 356.1° is next to the one at 0.4°.
    gaps = [(placed[i + 1] - placed[i]) % 360.0 for i in range(11)]
    assert min(gaps) >= 4.31 - 1e-9, gaps
    # And it stays centred where it was: least movement, not slid to one side.
    unwrapped = [value if value < 180.0 else value - 360.0 for value in placed]
    assert sum(unwrapped) / len(unwrapped) == pytest.approx(sum(wanted) / len(wanted), abs=1e-6)


def test_a_tight_crowd_with_per_label_extents_spreads_too():
    """Same defect, reached through the ``half_extents`` signature."""
    wanted = [i * 2.0 for i in range(8)]
    extents = [2.0] * 8
    placed = spread_around_wheel(wanted, 0.0, half_extents=extents)
    gaps = [(placed[i + 1] - placed[i]) % 360.0 for i in range(7)]
    assert min(gaps) >= 4.0 - 1e-9, gaps


def test_the_result_never_lands_on_360():
    """``[0, 360)`` is half-open, and plain ``% 360.0`` does not honour that.

    A tiny negative intermediate makes Python's float modulo return exactly
    360.0. The first entry of a crowd starting at 0.0 hit precisely that.
    """
    for wanted in ([i * 3.6 for i in range(12)], [0.0, 0.1, 0.2], [359.9, 0.0, 0.1]):
        for placed in (spread_around_wheel(wanted, 4.31), spread_around_wheel(wanted, 0.5)):
            assert all(0.0 <= value < 360.0 for value in placed), placed


def test_the_seam_is_not_squeezed_when_the_crowd_is_widened():
    """The fit cannot see the seam, so the ceiling has to be imposed after it.

    Letting the row grow to the circle's budget — the fix above — created its own
    failure: the isotonic fit honours every gap it was handed, but the seam pair
    is not among them (the straightened row has no seam), so the overflow landed
    in exactly the gap nobody was watching. Over 20 000 random twelve-label cases
    the crowded branch came out *worse* than the implementation it replaced in
    3121 of them, the worst leaving 0.012° where the old code left 15.9°.
    """
    for separation in (25.0, 32.5, 40.0, 45.0):
        # Labels wanting far more room than the circle holds: 12 x 40° = 480°.
        wanted = [index * 30.0 for index in range(12)]
        placed = spread_around_wheel(wanted, separation)
        gaps = [(placed[(i + 1) % 12] - placed[i]) % 360.0 for i in range(12)]
        # No gap — the seam included — may be crushed while the others keep room.
        assert min(gaps) >= max(gaps) - 1e-6, (
            f"separation {separation}: gaps {[round(g, 3) for g in gaps]}"
        )


def test_a_wide_crowd_keeps_room_at_the_seam():
    """A row already spanning most of the circle must not close the last gap."""
    wanted = [index * 28.0 for index in range(12)]  # spans 308°, seam is 52°
    placed = spread_around_wheel(wanted, 30.0)
    gaps = [(placed[(i + 1) % 12] - placed[i]) % 360.0 for i in range(12)]
    assert min(gaps) > 1.0, f"a gap collapsed: {[round(g, 3) for g in gaps]}"
    assert sum(gaps) == pytest.approx(360.0)


def test_the_span_ceiling_does_not_steal_from_a_pair_that_needs_more():
    """Constraining the total must not scale the requirements along with it.

    The ceiling was first imposed by squeezing the finished placement, which
    scales the ramp carrying every pair's requirement together with the freedom
    the fit had left — so a pair owed 91° came out with 90.5°. Squeezing only the
    fit's own component leaves the ramp intact, and every gap stays at its
    requirement plus a non-negative remainder.
    """
    angles = [0.0, 120.0, 240.0]
    extents = [90.0, 89.0, 1.0]
    placed = spread_around_wheel(angles, 0.0, half_extents=extents)
    gaps = [(placed[(i + 1) % 3] - placed[i]) % 360.0 for i in range(3)]
    required = [extents[i] + extents[(i + 1) % 3] for i in range(3)]
    for index, (gap, need) in enumerate(zip(gaps, required)):
        assert gap >= need - 1e-9, f"pair {index}: {gap}° given, {need}° required"


@pytest.mark.parametrize("count", [3, 5, 8, 12])
def test_every_pair_keeps_its_room_whenever_the_circle_has_it(count):
    """Sweep both signatures: if the requirements fit in 360°, all of them hold."""
    for step in (1, 7, 13):
        angles = [(index * step * 3.7) % 360.0 for index in range(count)]
        extents = [1.0 + (index * 5.0) % 40.0 for index in range(count)]
        required = [extents[i] + extents[(i + 1) % count] for i in range(count)]
        if sum(required) > 360.0:
            continue  # crowded branch shares the shortfall; covered above
        placed = spread_around_wheel(angles, 0.0, half_extents=extents)
        order = sorted(range(count), key=lambda i: placed[i])
        for position in range(count):
            i, j = order[position], order[(position + 1) % count]
            gap = (placed[j] - placed[i]) % 360.0
            assert gap >= extents[i] + extents[j] - 1e-7, (
                f"count={count} step={step}: {gap}° between labels needing "
                f"{extents[i] + extents[j]}°"
            )


# =============================================================================
# WHERE THE NUMBER ACTUALLY LANDS
# =============================================================================
#
# The three cases above this line ask the helpers for the right answer. These
# ask the drawing, because every defect in this area so far has been a coupling
# one: the helper was right and the caller handed it the wrong radius, or the
# wrong span, or an offset in a convention the line beside it does not use.


_HOUSE_NUMBER = re.compile(
    "<g kr:node='HouseNumber' kr:house='([0-9]+)' kr:horoscope='([01])'>"
    "<text[^>]*><tspan x='([-0-9.e]+)' y='([-0-9.e]+)'"
)

_CHART_CENTRE = 240.0

_HOUSE_ATTRS = (
    "first_house", "second_house", "third_house", "fourth_house", "fifth_house",
    "sixth_house", "seventh_house", "eighth_house", "ninth_house", "tenth_house",
    "eleventh_house", "twelfth_house",
)


def _rendered_numbers(svg: str, ring: str = "0") -> list[tuple[int, float, float]]:
    """House number, angle round the wheel, radius from the centre."""
    out = []
    for house, horoscope, x, y in _HOUSE_NUMBER.findall(svg):
        if horoscope != ring:
            continue
        # The tspan is nudged by (-3, +3) off the anchor the layout computed.
        dx = float(x) + 3.0 - _CHART_CENTRE
        dy = float(y) - 3.0 - _CHART_CENTRE
        out.append((int(house), math.degrees(math.atan2(dy, dx)) % 360.0, math.hypot(dx, dy)))
    return out


def _natal_svg(**birth) -> str:
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Numbers", 1990, 6, 15, 0, 1, city="X", nation="XX",
        online=False, suppress_geonames_warning=True, tz_str="UTC", **birth
    )
    return ChartDrawer(ChartDataFactory.create_natal_chart_data(subject)).generate_svg_string(
        style="classic"
    )


def test_the_numbers_are_drawn_on_the_ring_the_extents_were_measured_at():
    """The coupling itself, asserted rather than assumed.

    LABEL_RADIUS is what the module measures reach against; if the text lands
    somewhere else, every extent is scaled by the ratio between the two and the
    crowd is separated by the wrong amount in the only units that matter.
    """
    numbers = _rendered_numbers(_natal_svg(lat=45.0, lng=9.0, houses_system_identifier="P"))
    assert len(numbers) == 12
    for _, _, radius in numbers:
        assert radius == pytest.approx(LABEL_RADIUS, abs=0.5)


@pytest.mark.parametrize(
    "system,lat,lng",
    [
        ("C", 67.0, 20.0),   # the case that printed 10 before 9, and 4 before 3
        ("C", 70.0, 20.0),   # and one where the houses run backwards outright
        ("H", 0.0, 20.0),    # the horizon system reverses on the equator
        ("Y", 76.0, 20.0),
        ("P", 67.0, 20.0),
        ("K", 66.0, 20.0),
        ("R", 65.0, 20.0),
        ("O", 67.0, 20.0),
        ("P", 45.0, 9.0),
    ],
)
def test_the_numbers_read_round_the_wheel_in_order(system, lat, lng):
    """1 to 12 with nothing out of place, however crowded the quadrant.

    Two cusps inside one whole degree give their numbers the same truncated
    base, and whatever is added to that base then decides which of the two comes
    first. Adding half of an *exact* span put them in the order of their
    fractions, which is not the order of the houses.
    """
    numbers = _rendered_numbers(_natal_svg(lat=lat, lng=lng, houses_system_identifier=system))
    assert len(numbers) == 12
    by_angle = [house for house, _, _ in sorted(numbers, key=lambda item: item[1])]
    start = by_angle.index(1)
    rotated = by_angle[start:] + by_angle[:start]
    # The wheel runs counter-clockwise in screen terms, so reading atan2 upwards
    # normally gives 1, 12, 11 ...; where the houses themselves run backwards it
    # gives 1, 2, 3 ... The house order is what is being checked, not its sign.
    assert rotated in (list(range(1, 13)), [1] + list(range(12, 1, -1))), rotated


def test_every_number_sits_inside_its_own_house():
    """Order alone does not catch a set that is uniformly on the wrong side.

    Centre all twelve on the far end of their houses and they still read 1 to 12
    round the wheel: the whole ring turns together, so the cyclic order survives
    while every number has left the house it names. What has to be checked is
    containment, and against a definition of the wedge that owes nothing to the
    code under test — the arc between two consecutive cusps that holds no other
    cusp is the house, whichever way round the chart runs.
    """
    for system, lat, lng in (("C", 70.0, 20.0), ("H", 0.0, 20.0), ("P", 45.0, 9.0)):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Inside", 1990, 6, 15, 0, 1, city="X", nation="XX", online=False,
            suppress_geonames_warning=True, tz_str="UTC", lat=lat, lng=lng,
            houses_system_identifier=system,
        )
        svg = ChartDrawer(
            ChartDataFactory.create_natal_chart_data(subject)
        ).generate_svg_string(style="classic")
        drawn = {house: angle for house, angle, _ in _rendered_numbers(svg)}

        houses = [getattr(subject, name) for name in _HOUSE_ATTRS]
        seventh = int(houses[6].abs_pos)
        offsets = [float(-seventh + int(house.abs_pos)) for house in houses]

        # The offset frame maps onto the screen by a rotation, possibly mirrored.
        # Two samples fix both, and inverting is then exact.
        radius = 192.0
        def screen(offset: float) -> float:
            x = wheel_x(0, radius, offset) + 48.0 - _CHART_CENTRE
            y = wheel_y(0, radius, offset) + 48.0 - _CHART_CENTRE
            return math.degrees(math.atan2(y, x)) % 360.0

        mirrored = ((screen(1.0) - screen(0.0) + 180.0) % 360.0 - 180.0) < 0
        zero = screen(0.0)

        def to_offset(angle: float) -> float:
            return ((zero - angle) if mirrored else (angle - zero)) % 360.0

        for index in range(12):
            start, end = offsets[index], offsets[(index + 1) % 12]
            others = [offsets[other] for other in range(12) if other not in (index, (index + 1) % 12)]
            forward = (end - start) % 360.0
            forward_clean = not any(0.0 < (other - start) % 360.0 < forward for other in others)
            backward = (start - end) % 360.0
            backward_clean = not any(0.0 < (start - other) % 360.0 < backward for other in others)
            if forward_clean == backward_clean:
                continue  # cusps cross here; the house has no unambiguous arc
            span = forward if forward_clean else backward
            if span < 10.0:
                # No label fits in an arc this narrow, so the spread pushes it out
                # on purpose and containment is not the property to check. What is
                # being caught here displaces a number by 177 degrees, not by two.
                continue
            inside = ((to_offset(drawn[index + 1]) - start) % 360.0) if forward_clean else (
                (start - to_offset(drawn[index + 1])) % 360.0
            )
            assert inside <= span + 1e-6, (
                f"{system} at {lat}N: house {index + 1} is labelled {inside:.2f}deg "
                f"into an arc of {span:.2f}deg"
            )


def test_a_crowd_is_not_pushed_further_than_its_labels_need():
    """The over-separation the wrong radius caused, measured where it shows.

    Placidus at 67N gives four numbers barely a degree apart. Spread at the
    right radius they end up about ten pixels apart, the width of the inked
    figures; measured at the cusp line's radius instead, every extent was 1.6x
    too large and the same four were pushed out to sixteen.
    """
    numbers = _rendered_numbers(_natal_svg(lat=67.0, lng=20.0, houses_system_identifier="P"))
    ordered = sorted(numbers, key=lambda item: item[1])
    gaps_px = []
    for (_, angle_a, radius_a), (_, angle_b, radius_b) in zip(ordered, ordered[1:]):
        arc = (angle_b - angle_a) % 360.0
        gaps_px.append(math.radians(arc) * (radius_a + radius_b) / 2.0)
    tightest = min(gaps_px)
    # 14px font, cap height ratio 0.716 -> 10.02px is what "just touching" means.
    assert 9.0 <= tightest <= 12.5, f"tightest pair {tightest:.2f}px"


def test_the_outer_ring_of_a_dual_chart_labels_its_own_lines():
    """Its cusp lines keep their fraction, so its numbers have to as well.

    A truncated base against an exact line drifts the two apart by up to a whole
    degree, which at this radius is four pixels of daylight between a number and
    the wedge it names. The wedge is rebuilt here through the same wheel_x/wheel_y
    the drawing uses, so the check does not depend on knowing which way round the
    chart runs.
    """
    john = AstrologicalSubjectFactory.from_birth_data(
        "John", 1940, 10, 9, 18, 30, city="Liverpool", nation="GB", lng=-2.97, lat=53.41,
        tz_str="Europe/London", online=False, suppress_geonames_warning=True,
    )
    paul = AstrologicalSubjectFactory.from_birth_data(
        "Paul", 1942, 6, 18, 15, 30, city="Liverpool", nation="GB", lng=-2.97, lat=53.41,
        tz_str="Europe/London", online=False, suppress_geonames_warning=True,
    )
    svg = ChartDrawer(ChartDataFactory.create_synastry_chart_data(john, paul)).generate_svg_string(
        style="classic"
    )
    numbers = {house: angle for house, angle, _ in _rendered_numbers(svg, ring="1")}
    assert len(numbers) == 12

    outer_radius = _CHART_CENTRE - 8.0

    def screen_angle(offset: float) -> float:
        x = wheel_x(0, outer_radius, offset) + 8.0 - _CHART_CENTRE
        y = wheel_y(0, outer_radius, offset) + 8.0 - _CHART_CENTRE
        return math.degrees(math.atan2(y, x)) % 360.0

    houses = [getattr(paul, name) for name in (
        "first_house", "second_house", "third_house", "fourth_house", "fifth_house",
        "sixth_house", "seventh_house", "eighth_house", "ninth_house", "tenth_house",
        "eleventh_house", "twelfth_house",
    )]
    zero = john.seventh_house.abs_pos
    drifts = []
    for index, house in enumerate(houses):
        start_offset = house.abs_pos - zero
        span = (houses[(index + 1) % 12].abs_pos - house.abs_pos) % 360.0
        wanted = screen_angle(start_offset + span / 2.0)
        drawn = numbers[index + 1]
        drifts.append(abs((drawn - wanted + 180.0) % 360.0 - 180.0))
    # Nothing here is crowded enough to be moved by the spread, so every number
    # should sit on the exact middle of its own wedge. Truncating the base put
    # them up to a degree off it.
    assert max(drifts) < 0.05, [round(d, 4) for d in drifts]


# =============================================================================
# THE OTHER ENGINE, AND THE OTHER RING
# =============================================================================
#
# Everything above reads the classic wheel with one subject. Three of the four
# places that centre a number on a house live elsewhere — the modern engine's
# own ring, and the outer ring of a dual chart — and each could be reverted to
# the forward-only midpoint with the whole suite staying green, because no case
# rendered modern at all and the only dual chart had both subjects running
# forwards.


_MODERN_NUMBER = re.compile(
    "<g kr:node='HouseNumber' kr:house='([0-9]+)' kr:horoscope='([01])'>"
    "<text[^>]*transform='rotate\\(-([0-9.]+) "
)


def _house_arc_containing(angles: list[float], index: int) -> tuple[float, float] | None:
    """The arc between two consecutive cusps that holds no other cusp.

    Independent of the code under test: whichever way the houses run, the house
    is the gap between its own cusp and the next with nothing in between. Returns
    None where the cusps cross and the house has no unambiguous arc.
    """
    start, end = angles[index], angles[(index + 1) % 12]
    others = [angles[other] for other in range(12) if other not in (index, (index + 1) % 12)]
    forward = (end - start) % 360.0
    forward_clean = not any(0.0 < (other - start) % 360.0 < forward for other in others)
    backward = (start - end) % 360.0
    backward_clean = not any(0.0 < (start - other) % 360.0 < backward for other in others)
    if forward_clean == backward_clean:
        return None
    return (start, forward) if forward_clean else (start, -backward)


@pytest.mark.parametrize(
    "system,lat,lng",
    [
        ("C", 70.0, 20.0),   # a ring that runs backwards
        ("H", 0.0, 20.0),    # the horizon system on the equator, likewise
        ("P", 45.0, 9.0),    # and an ordinary chart
    ],
)
def test_the_modern_ring_centres_its_numbers_on_their_own_houses(system, lat, lng):
    """The modern engine has a house ring of its own, and it was unpinned.

    Reverted to the forward midpoint, Campanus at 70N puts the numbers 6 and 12
    a hundred and fifty-seven degrees from the houses they name — and every test
    in this file stayed green, because none of them rendered modern.
    """
    from kerykeion.charts.draw_modern import _zodiac_to_wheel_angle

    subject = AstrologicalSubjectFactory.from_birth_data(
        "Modern", 1990, 6, 15, 0, 1, city="X", nation="XX", online=False,
        suppress_geonames_warning=True, tz_str="UTC", lat=lat, lng=lng,
        houses_system_identifier=system,
    )
    svg = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject)).generate_svg_string(
        style="modern"
    )
    drawn = {
        int(house): float(angle)
        for house, ring, angle in _MODERN_NUMBER.findall(svg)
        if ring == "0"
    }
    assert len(drawn) == 12, sorted(drawn)

    houses = [getattr(subject, name) for name in _HOUSE_ATTRS]
    seventh = houses[6].abs_pos
    angles = [_zodiac_to_wheel_angle(house.abs_pos, seventh) for house in houses]
    for index in range(12):
        arc = _house_arc_containing(angles, index)
        if arc is None:
            continue
        start, signed_span = arc
        span = abs(signed_span)
        if span < 10.0:
            continue  # too narrow to hold a label; the spread pushes it out on purpose
        inside = (
            (drawn[index + 1] - start) % 360.0
            if signed_span > 0
            else (start - drawn[index + 1]) % 360.0
        )
        assert inside <= span + 1e-6, (
            f"{system}: house {index + 1} is labelled {inside:.2f}deg into {span:.2f}deg"
        )


def test_the_outer_ring_follows_a_second_subject_that_runs_backwards():
    """The dual chart's outer numbers, on a partner whose houses reverse.

    The only dual chart tested until now had both subjects running forwards, so
    the direction term on that ring was dead weight as far as the suite could
    tell: reverting it left all twelve outer numbers thirty degrees outside their
    own wedges and nothing went red.
    """
    from kerykeion.charts.utils import wheel_x, wheel_y

    first = AstrologicalSubjectFactory.from_birth_data(
        "Ordinary", 1940, 10, 9, 18, 30, city="X", nation="XX", lng=-2.97, lat=53.41,
        tz_str="UTC", online=False, suppress_geonames_warning=True,
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "Reversed", 1990, 6, 21, 0, 0, city="X", nation="XX", lng=20.0, lat=70.0,
        tz_str="UTC", online=False, suppress_geonames_warning=True,
        houses_system_identifier="C",
    )
    partner_cusps = [getattr(second, name).abs_pos for name in _HOUSE_ATTRS]
    forward_total = sum((partner_cusps[(i + 1) % 12] - partner_cusps[i]) % 360.0 for i in range(12))
    assert abs(forward_total - 360.0) > 1.0, "fixture no longer has a reversed second subject"

    svg = ChartDrawer(
        ChartDataFactory.create_synastry_chart_data(first, second)
    ).generate_svg_string(style="classic")
    drawn = {house: angle for house, angle, _ in _rendered_numbers(svg, ring="1")}
    assert len(drawn) == 12

    outer_radius = _CHART_CENTRE - 8.0
    zero = first.seventh_house.abs_pos

    def screen(offset: float) -> float:
        x = wheel_x(0, outer_radius, offset) + 8.0 - _CHART_CENTRE
        y = wheel_y(0, outer_radius, offset) + 8.0 - _CHART_CENTRE
        return math.degrees(math.atan2(y, x)) % 360.0

    angles = [screen(cusp - zero) for cusp in partner_cusps]
    checked = 0
    for index in range(12):
        arc = _house_arc_containing(angles, index)
        if arc is None:
            continue
        start, signed_span = arc
        span = abs(signed_span)
        if span < 10.0:
            continue
        inside = (
            (drawn[index + 1] - start) % 360.0
            if signed_span > 0
            else (start - drawn[index + 1]) % 360.0
        )
        assert inside <= span + 1e-6, (
            f"outer house {index + 1}: {inside:.2f}deg into an arc of {span:.2f}deg"
        )
        checked += 1
    assert checked >= 2, f"only {checked} houses were wide enough to check"
