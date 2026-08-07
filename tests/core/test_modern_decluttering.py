"""
Regression tests for the modern chart collision/decluttering algorithm.

Covers the bug where a planet in a tight cluster could be pushed past its
neighbours, breaking zodiacal order (e.g. Neptune 5° Aquarius ending up
displayed after Uranus 17° Aquarius).

See: kerykeion/charts/draw_modern.py::_resolve_planet_collisions
"""

from __future__ import annotations

import pytest

from kerykeion.charts import draw_modern
from kerykeion.charts.draw_modern import (
    PLANET_MIN_SEPARATION,
    _isotonic_non_decreasing,
    _normalize_angle,
    _resolve_planet_collisions,
)


# =============================================================================
# HELPERS
# =============================================================================


def _count_display_order_breaks(resolved: list[dict]) -> int:
    """
    Count the number of times the `display_angle` sequence "wraps backwards"
    when planets are traversed in their true zodiacal order.

    If the decluttering preserves zodiacal order, there is AT MOST ONE
    such wrap — the one corresponding to the largest cyclic gap (i.e. the
    natural "cut" of the circle). More than one wrap means a planet has
    been pushed past another, violating the invariant.
    """
    ordered = sorted(resolved, key=lambda p: p["angle"])
    n = len(ordered)
    wraps = 0
    for i in range(n):
        curr = ordered[i]["display_angle"]
        nxt = ordered[(i + 1) % n]["display_angle"]
        if nxt < curr:
            wraps += 1
    return wraps


def _min_pairwise_gap(resolved: list[dict]) -> float:
    """
    Minimum cyclic gap between adjacent planets after decluttering,
    traversing in order of current display_angle.
    """
    displays = sorted(p["display_angle"] for p in resolved)
    n = len(displays)
    return min(_normalize_angle(displays[(i + 1) % n] - displays[i]) for i in range(n))


# =============================================================================
# REGRESSION: cluster Aqua/Pesci (26 Feb 2000)
# =============================================================================


# Synthetic cluster reproducing the 2000-02-26 stellium reported in the issue.
# Values are zodiacal angles (wheel angles) matching abs_pos for a chart
# where the seventh house cusp offset cancels out (i.e. angle == abs_pos).
# The important property is the relative spacing, which triggers the bug.
_ISSUE_CLUSTER = [
    {"angle": 303.155, "point": "True_South_Lunar_Node"},  # 3°09' Aqu
    {"angle": 305.245, "point": "Neptune"},                # 5°15' Aqu
    {"angle": 310.019, "point": "Venus"},                  # 10°01' Aqu
    {"angle": 317.947, "point": "Uranus"},                 # 17°57' Aqu
    {"angle": 337.003, "point": "Sun"},                    # 7°00' Pis
    {"angle": 345.339, "point": "Mercury"},                # 15°20' Pis (RX)
    {"angle": 10.822,  "point": "Mars"},                   # 10°49' Ari
]


def _fixture(cluster: list[dict]) -> list[dict]:
    """Fresh list of dicts (function mutates in place)."""
    return [dict(p, color="#000000") for p in cluster]


def test_cluster_preserves_zodiacal_order():
    """
    The reported bug: Neptune (5° Aqu) ends up displayed after Uranus
    (17° Aqu). After resolution, planets must stay in zodiacal order.
    """
    resolved = _resolve_planet_collisions(
        _fixture(_ISSUE_CLUSTER),
        min_separation=PLANET_MIN_SEPARATION,
    )

    wraps = _count_display_order_breaks(resolved)
    assert wraps <= 1, (
        f"Zodiacal order violated: {wraps} backwards wraps in display order. "
        f"Expected at most 1 (the natural cyclic cut). "
        f"Result: {[(p['point'], round(p['display_angle'], 3)) for p in sorted(resolved, key=lambda p: p['angle'])]}"
    )


def test_cluster_neptune_between_south_node_and_venus():
    """
    Explicit check on the specific symptom: Neptune's display position
    must sit between True_South_Lunar_Node and Venus, following the
    true zodiacal order.
    """
    resolved = _resolve_planet_collisions(
        _fixture(_ISSUE_CLUSTER),
        min_separation=PLANET_MIN_SEPARATION,
    )
    by_name = {p["point"]: p["display_angle"] for p in resolved}

    south_node = by_name["True_South_Lunar_Node"]
    neptune = by_name["Neptune"]
    venus = by_name["Venus"]
    uranus = by_name["Uranus"]

    # Translate into "forward-from-south-node" distances so wrap is irrelevant.
    def fwd(a: float) -> float:
        return _normalize_angle(a - south_node)

    d_neptune = fwd(neptune)
    d_venus = fwd(venus)
    d_uranus = fwd(uranus)

    assert 0 < d_neptune < d_venus < d_uranus, (
        "Neptune must be displayed between South Node and Venus "
        f"(got forward-distances: Neptune={d_neptune:.3f}°, "
        f"Venus={d_venus:.3f}°, Uranus={d_uranus:.3f}°)"
    )


def test_cluster_min_separation_respected():
    """All planets must be at least `sep` degrees apart after resolution."""
    sep = PLANET_MIN_SEPARATION
    resolved = _resolve_planet_collisions(_fixture(_ISSUE_CLUSTER), min_separation=sep)

    # The effective sep is capped by 320 / n (see implementation).
    effective_sep = min(sep, 320.0 / len(resolved))

    min_gap = _min_pairwise_gap(resolved)
    assert min_gap >= effective_sep - 1e-6, (
        f"Minimum gap {min_gap:.4f}° is below sep={effective_sep:.4f}°"
    )


# =============================================================================
# GENERAL PROPERTIES
# =============================================================================


def test_empty_input_returns_empty():
    assert _resolve_planet_collisions([]) == []


def test_single_planet_unchanged():
    resolved = _resolve_planet_collisions([{"angle": 42.0, "point": "P"}])
    assert len(resolved) == 1
    assert resolved[0]["display_angle"] == 42.0


def test_sparse_planets_unchanged():
    """Planets already far apart should not be moved."""
    sparse = [
        {"angle": 10.0, "point": "A"},
        {"angle": 90.0, "point": "B"},
        {"angle": 200.0, "point": "C"},
        {"angle": 300.0, "point": "D"},
    ]
    resolved = _resolve_planet_collisions(sparse)
    for p in resolved:
        assert p["display_angle"] == pytest.approx(p["angle"], abs=1e-9)


def test_order_preserved_random_dense_clusters():
    """
    Property check on random dense clusters: zodiacal order must be preserved
    and min separation must be respected.
    """
    import random

    random.seed(20000226)
    for _ in range(200):
        n = random.randint(2, 25)
        base = random.uniform(0, 360)
        # Tight cluster within up to 40 degrees, triggers many collisions
        width = random.uniform(1.0, 40.0)
        planets = [
            {"angle": _normalize_angle(base + random.uniform(0, width)), "point": f"P{i}"}
            for i in range(n)
        ]
        resolved = _resolve_planet_collisions(planets)
        wraps = _count_display_order_breaks(resolved)
        assert wraps <= 1, (
            f"Order violated with input {[round(p['angle'], 3) for p in planets]} → "
            f"displays={[round(p['display_angle'], 3) for p in sorted(resolved, key=lambda x: x['angle'])]}"
        )
        effective_sep = min(PLANET_MIN_SEPARATION, 320.0 / n)
        assert _min_pairwise_gap(resolved) >= effective_sep - 1e-6


def test_order_preserved_random_fullcircle():
    """
    Property check covering arbitrary distributions on the full circle
    (not only tight clusters). Ensures the fix also behaves on sparse or
    mixed layouts across all 360°.
    """
    import random

    random.seed(42)
    for _ in range(500):
        n = random.randint(2, 25)
        planets = [{"angle": random.uniform(0, 360), "point": f"P{i}"} for i in range(n)]
        resolved = _resolve_planet_collisions(planets)

        wraps = _count_display_order_breaks(resolved)
        assert wraps <= 1, (
            f"Order violated with angles={[round(p['angle'], 3) for p in planets]}"
        )
        effective_sep = min(PLANET_MIN_SEPARATION, 320.0 / n)
        assert _min_pairwise_gap(resolved) >= effective_sep - 1e-6


def test_all_equal_angles():
    """
    Pathological input: every planet at the same angle. Output must still
    have exactly one backward wrap (the cyclic cut) and respect sep.
    """
    for n in (2, 3, 10, 40, 41):
        planets = [{"angle": 42.0, "point": f"P{i}"} for i in range(n)]
        resolved = _resolve_planet_collisions(planets)

        wraps = _count_display_order_breaks(resolved)
        effective_sep = min(PLANET_MIN_SEPARATION, 320.0 / n)
        assert wraps <= 1, f"n={n}: {wraps} wraps, displays={[p['display_angle'] for p in resolved]}"
        assert _min_pairwise_gap(resolved) >= effective_sep - 1e-6, f"n={n}: gap below sep"


def test_two_planet_cluster():
    """Two close planets must both end up `sep` apart without float churn."""
    planets = [
        {"angle": 10.0, "point": "A"},
        {"angle": 13.0, "point": "B"},
    ]
    resolved = _resolve_planet_collisions(planets)
    displays = sorted(p["display_angle"] for p in resolved)
    assert _normalize_angle(displays[1] - displays[0]) >= PLANET_MIN_SEPARATION - 1e-9


def test_long_push_chain_crossing_zero():
    """
    Long cluster whose push chain crosses the 0°/360° boundary, with
    another planet sitting just past 0°. Previous implementation could
    leave a backward wrap in the chain as it re-entered the other planet.
    """
    # 23 planets tightly packed from ~350° forward, plus one at ~5°.
    planets = [{"angle": _normalize_angle(350.0 + 0.5 * i), "point": f"P{i}"} for i in range(23)]
    planets.append({"angle": 5.0, "point": "stray"})

    resolved = _resolve_planet_collisions(planets)

    wraps = _count_display_order_breaks(resolved)
    assert wraps <= 1, f"Push chain wrapped extra times: {[(p['point'], round(p['display_angle'], 3)) for p in sorted(resolved, key=lambda x: x['angle'])]}"

    effective_sep = min(PLANET_MIN_SEPARATION, 320.0 / len(resolved))
    assert _min_pairwise_gap(resolved) >= effective_sep - 1e-6


def test_wrap_around_cluster_at_zero_degrees():
    """
    Cluster spanning the 0°/360° boundary must also preserve order.
    """
    planets = [
        {"angle": 355.0, "point": "A"},
        {"angle": 358.0, "point": "B"},
        {"angle": 1.0, "point": "C"},
        {"angle": 4.0, "point": "D"},
    ]
    resolved = _resolve_planet_collisions(planets)
    # Forward distance from A — every other planet must be strictly further.
    a = next(p["display_angle"] for p in resolved if p["point"] == "A")

    def fwd(x: float) -> float:
        return _normalize_angle(x - a)

    dists = {p["point"]: fwd(p["display_angle"]) for p in resolved if p["point"] != "A"}
    assert 0 < dists["B"] < dists["C"] < dists["D"], (
        f"Order broken across 0° wrap: {dists}"
    )


# =============================================================================
# INTEGRATION: historical chart 2000-02-26 stellium
# =============================================================================


def test_modern_chart_2000_02_26_neptune_order():
    """
    End-to-end regression test on a real chart that reproduces the issue
    conditions: Neptune ~5° Aqu inside a dense cluster with Uranus 17° Aqu,
    Venus 10° Aqu, and True_South_Lunar_Node 3° Aqu.

    Parses the generated modern SVG and asserts that the rendered order of
    ChartPoint glyphs (by display_angle from their ``transform="rotate(...)"``
    attribute) follows the true zodiacal order.
    """
    import re

    from kerykeion import AstrologicalSubjectFactory
    from kerykeion.chart_data_factory import ChartDataFactory
    from kerykeion.charts.chart_drawer import ChartDrawer
    from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

    # The decluttering regression on the 2000-02-26 stellium relies on
    # True_South_Lunar_Node being rendered. It was dropped from defaults in
    # 6.0.0a46 (alignment with reference standard), so we opt back in here
    # at both factory layers (the subject must compute it, and the chart data
    # must propagate it).
    active = DEFAULT_ACTIVE_POINTS + ["True_South_Lunar_Node"]
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Decluttering Repro 2000",
        2000,
        2,
        26,
        12,
        0,
        lat=51.5,
        lng=0.0,
        tz_str="UTC",
        online=False,
        suppress_geonames_warning=True,
        active_points=active,
    )
    chart_data = ChartDataFactory.create_natal_chart_data(subject, active_points=active)
    svg = ChartDrawer(chart_data=chart_data).generate_wheel_only_svg_string(style="modern")

    # Each planet is rendered as:
    #   <g kr:node='ChartPoint' ... kr:slug='NAME' ... transform='rotate(-DEG 50.0 50.0)'>
    # (attribute quotes may be single or double depending on serializer).
    pattern = re.compile(
        r"""<g\s+kr:node=['"]ChartPoint['"][^>]*kr:slug=['"]([^'"]+)['"][^>]*"""
        r"""transform=['"]rotate\(-(\d+\.\d+)\s+50\.0\s+50\.0\)['"]""",
    )
    display_angles = {m.group(1): float(m.group(2)) for m in pattern.finditer(svg)}

    required = ["True_South_Lunar_Node", "Neptune", "Venus", "Uranus"]
    for name in required:
        assert name in display_angles, f"Missing planet in SVG: {name}. Found: {sorted(display_angles)}"

    south_node = display_angles["True_South_Lunar_Node"]
    neptune = display_angles["Neptune"]
    venus = display_angles["Venus"]
    uranus = display_angles["Uranus"]

    def fwd(a: float) -> float:
        return _normalize_angle(a - south_node)

    d_neptune = fwd(neptune)
    d_venus = fwd(venus)
    d_uranus = fwd(uranus)

    assert 0 < d_neptune < d_venus < d_uranus, (
        "Zodiacal order violated in rendered modern chart for 2000-02-26. "
        f"Forward distances from True_South_Lunar_Node: "
        f"Neptune={d_neptune:.3f}°, Venus={d_venus:.3f}°, Uranus={d_uranus:.3f}°"
    )


# =============================================================================
# PLACEMENT OPTIMALITY — the resolver is a least-squares isotonic fit
# =============================================================================
#
# The resolver promises more than "order preserved and gaps respected": every
# planet lands as close to its true position as the separations allow. That is
# the L2-optimal isotonic placement, and it has sharp, testable signatures —
# cramped runs keep their center of mass, an independent PAVA reimplementation
# must agree to the last bit, and no rigid nudge of a run can improve the fit.


def _resolved_line(angles: list[float], separation: float = PLANET_MIN_SEPARATION) -> list[dict]:
    """Resolve angles that all live far from the 0/360 seam, sorted by angle.

    Keeping every input (and every displacement it can incur) inside the open
    interval (40, 320) guarantees the largest gap — where the resolver cuts the
    circle — is the seam itself, so displays can be compared to true angles
    without wraparound bookkeeping.
    """
    planets = [{"angle": angle, "point": f"P{i}"} for i, angle in enumerate(angles)]
    resolved = _resolve_planet_collisions(planets, min_separation=separation)
    return sorted(resolved, key=lambda p: p["angle"])


def _cramped_runs(resolved_by_angle: list[dict], separation: float) -> list[list[dict]]:
    """Maximal runs of neighbours whose display gap sits exactly at *separation*."""
    runs: list[list[dict]] = []
    current_run = [resolved_by_angle[0]]
    for previous, planet in zip(resolved_by_angle, resolved_by_angle[1:]):
        display_gap = planet["display_angle"] - previous["display_angle"]
        if abs(display_gap - separation) <= 1e-6:
            current_run.append(planet)
        else:
            if len(current_run) > 1:
                runs.append(current_run)
            current_run = [planet]
    if len(current_run) > 1:
        runs.append(current_run)
    return runs


def test_isotonic_regression_pools_violators_to_their_mean():
    assert _isotonic_non_decreasing([1.0, 2.0, 3.0]) == [(1.0, 1), (2.0, 1), (3.0, 1)]
    assert _isotonic_non_decreasing([5.0, 1.0]) == [(3.0, 2)]
    # A merge can cascade backwards: pooling (3, 1) to mean 2 does not violate
    # against nothing, but [3, 1, 1] pools twice.
    assert _isotonic_non_decreasing([3.0, 1.0, 1.0]) == [(5.0 / 3.0, 3)]


def test_cramped_runs_are_centered_on_their_true_positions():
    """A cramped run spreads around where its planets actually are.

    The least-squares isotonic placement gives every compressed run a zero
    displacement sum — the run's center of mass stays put. The historical
    forward walk kept the first planet of a run fixed and pushed everyone else
    ahead, which fails this on the very first cluster.
    """
    import random

    random.seed(19401009)
    for _ in range(200):
        count = random.randint(2, 12)
        base = random.uniform(100, 180)
        width = random.uniform(0.5, 25.0)
        angles = sorted(base + random.uniform(0, width) for _ in range(count))
        resolved = _resolved_line(angles)
        for run in _cramped_runs(resolved, PLANET_MIN_SEPARATION):
            displacement_sum = sum(p["display_angle"] - p["angle"] for p in run)
            assert abs(displacement_sum) <= 1e-6 * len(run), (
                f"Run of {len(run)} drifted by {displacement_sum:.6f}° from its "
                f"center of mass; angles={[round(p['angle'], 3) for p in run]}"
            )


def _independent_least_squares_displays(angles: list[float], separation: float) -> list[float]:
    """O(n²) reference PAVA: pool any adjacent violation until none is left.

    Deliberately a different algorithm shape from the production stack-based
    pass, so a bug in one cannot hide in the other.
    """
    reserved = [index * separation for index in range(len(angles))]
    deflated = [angle - space for angle, space in zip(angles, reserved)]
    groups: list[list[float]] = [[value] for value in deflated]
    pooled_something = True
    while pooled_something:
        pooled_something = False
        for index in range(len(groups) - 1):
            left_mean = sum(groups[index]) / len(groups[index])
            right_mean = sum(groups[index + 1]) / len(groups[index + 1])
            if left_mean > right_mean:
                groups[index].extend(groups.pop(index + 1))
                pooled_something = True
                break
    fitted = [sum(group) / len(group) for group in groups for _ in group]
    return [value + space for value, space in zip(fitted, reserved)]


def test_matches_an_independent_pava_implementation():
    import random

    random.seed(26021962)
    for _ in range(300):
        count = random.randint(2, 15)
        angles = sorted(random.uniform(110, 240) for _ in range(count))
        expected = _independent_least_squares_displays(angles, PLANET_MIN_SEPARATION)
        resolved = _resolved_line(angles)
        for planet, expected_display in zip(resolved, expected):
            assert planet["display_angle"] == pytest.approx(expected_display, abs=1e-9)


def test_no_rigid_shift_of_a_cramped_run_improves_the_fit():
    """Sliding a whole cramped run toward free space must never pay off.

    At the least-squares optimum every feasible rigid nudge of a run raises the
    total squared displacement — the operational KKT check, and exactly the
    move an eyeballing reviewer would try ("couldn't this group sit a bit
    further back?").
    """
    import random

    random.seed(7407)
    nudge = 0.05
    for _ in range(100):
        count = random.randint(3, 12)
        base = random.uniform(110, 200)
        angles = sorted(base + random.uniform(0, 18.0) for _ in range(count))
        resolved = _resolved_line(angles)
        for run in _cramped_runs(resolved, PLANET_MIN_SEPARATION):
            run_first, run_last = run[0], run[-1]
            neighbours_before = [p for p in resolved if p["display_angle"] < run_first["display_angle"]]
            neighbours_after = [p for p in resolved if p["display_angle"] > run_last["display_angle"]]
            for direction in (-nudge, nudge):
                if direction < 0 and neighbours_before:
                    room = run_first["display_angle"] - neighbours_before[-1]["display_angle"]
                    if room + direction < PLANET_MIN_SEPARATION - 1e-9:
                        continue
                if direction > 0 and neighbours_after:
                    room = neighbours_after[0]["display_angle"] - run_last["display_angle"]
                    if room - direction < PLANET_MIN_SEPARATION - 1e-9:
                        continue
                cost_change = sum(
                    (p["display_angle"] + direction - p["angle"]) ** 2
                    - (p["display_angle"] - p["angle"]) ** 2
                    for p in run
                )
                assert cost_change >= -1e-9, (
                    f"Nudging a run of {len(run)} by {direction:+.2f}° lowered the "
                    f"squared displacement by {-cost_change:.9f}"
                )


def test_issue_cluster_displacements_shrink_vs_forward_walk():
    """
    On the 2000-02-26 stellium the historical forward walk displaced Venus by
    7.64° at worst, 2.82° on average. The least-squares placement measures
    4.94° / 1.41° (scripts/report_modern_displacement.py has the full-chart
    figures). The bounds sit halfway between the two, so any revert to a
    forward-pushing scheme fails loudly while honest refactors pass.
    """
    from kerykeion.utilities import wrap_180

    resolved = _resolve_planet_collisions(_fixture(_ISSUE_CLUSTER))
    displacements = [abs(wrap_180(p["display_angle"] - p["angle"])) for p in resolved]
    assert max(displacements) < 6.0
    assert sum(displacements) / len(displacements) < 2.0


def test_resolution_is_deterministic():
    """Same input, same floats — no measurement, randomness, or dict-order leaks."""
    import random

    random.seed(313)
    angles = [random.uniform(0, 360) for _ in range(30)]

    def resolve() -> list[float]:
        planets = [{"angle": angle, "point": f"P{i}"} for i, angle in enumerate(angles)]
        return [p["display_angle"] for p in _resolve_planet_collisions(planets)]

    assert resolve() == resolve()


# =============================================================================
# CONTENT-AWARE SEPARATION — pairs reserve what they draw, not the worst case
# =============================================================================


def _stand_in_point(
    name: str = "Sun",
    sign: str = "Aqu",
    position: float = 15.0,
    retrograde: bool = False,
    point_type: str = "AstrologicalPoint",
):
    """The five attributes _cluster_row_profile reads, without a full model."""
    from types import SimpleNamespace

    return SimpleNamespace(
        name=name, point_type=point_type, sign=sign, position=position, retrograde=retrograde
    )


_NATAL_ROW_RADII = {
    "glyph": 39.0,
    "degrees": 35.5,
    "sign": 32.0,
    "minutes": 28.0,
    "rx": 25.0,
}


def _resolved_span(points: list, row_radii: dict) -> float:
    """Span of a jammed cluster of *points* after content-aware resolution."""
    entries = [
        {
            "angle": 150.0 + index * 0.01,
            "point": f"P{index}",
            "row_half_widths": draw_modern._cluster_row_profile(point),
        }
        for index, point in enumerate(points)
    ]
    resolved = _resolve_planet_collisions(entries, row_radii=row_radii)
    displays = sorted(entry["display_angle"] for entry in resolved)
    return displays[-1] - displays[0]


def test_profile_reserves_the_rx_row_only_for_retrograde_points():
    direct = draw_modern._cluster_row_profile(_stand_in_point(retrograde=False))
    retrograde = draw_modern._cluster_row_profile(_stand_in_point(retrograde=True))
    assert set(direct) == {"glyph", "degrees", "sign", "minutes"}
    assert set(retrograde) == {"glyph", "degrees", "sign", "minutes", "rx"}
    rx_half_width, rx_half_height = retrograde["rx"]
    assert rx_half_width > 0
    assert rx_half_height > 0


def test_profile_reserves_the_widest_measured_glyph_for_unknown_symbols():
    """A symbol the ink table has never measured cannot be under-reserved.

    House cusps bypass resolve_glyph_id (their slug is the symbol id), so a
    cusp rendered as a chart point exercises the conservative fallback.
    """
    from kerykeion.charts.glyph_ink_metrics import GLYPH_INK_HALF_HEIGHT, GLYPH_INK_HALF_WIDTH

    cusp = _stand_in_point(name="First_House", point_type="House")
    profile = draw_modern._cluster_row_profile(cusp)
    scale = draw_modern.PLANET_SCALE_BASE
    assert profile["glyph"][0] == pytest.approx(max(GLYPH_INK_HALF_WIDTH.values()) * scale)
    assert profile["glyph"][1] == pytest.approx(max(GLYPH_INK_HALF_HEIGHT.values()) * scale)


def test_formatting_helpers_match_what_the_renderer_draws():
    point = _stand_in_point(position=7.9)  # 7º54'
    assert draw_modern._format_degrees_text(point) == "7º"
    assert draw_modern._format_minutes_text(point) == "54'"


def test_narrow_content_packs_tighter_than_wide_content():
    """Five slim clusters must span less arc than five maximal ones."""
    narrow = [
        _stand_in_point(name="Mean_Lilith", position=1.05, retrograde=False) for _ in range(5)
    ]
    wide = [_stand_in_point(name="Sun", position=29.983, retrograde=True) for _ in range(5)]
    narrow_span = _resolved_span(narrow, _NATAL_ROW_RADII)
    wide_span = _resolved_span(wide, _NATAL_ROW_RADII)
    assert narrow_span < wide_span


def test_content_derived_separation_never_exceeds_the_measured_ceiling():
    """The scalar constants stay a hard ceiling: no pair can fan out further
    than the layout did before content-awareness existed."""
    wide = [_stand_in_point(name="Sun", position=29.983, retrograde=True) for _ in range(6)]
    span = _resolved_span(wide, _NATAL_ROW_RADII)
    assert span <= 5 * PLANET_MIN_SEPARATION + 1e-9


def test_entries_without_profiles_fall_back_to_the_uniform_separation():
    """The content-aware path must be opt-in per entry: plain dicts resolve
    exactly as they always did, profiles or not on the parameter list."""
    angles = [200.0, 200.5, 201.0, 214.0]
    plain = [{"angle": angle, "point": f"P{i}"} for i, angle in enumerate(angles)]
    scalar_result = _resolve_planet_collisions([dict(entry) for entry in plain])
    fallback_result = _resolve_planet_collisions(
        [dict(entry) for entry in plain], row_radii=_NATAL_ROW_RADII
    )
    assert [entry["display_angle"] for entry in scalar_result] == [
        entry["display_angle"] for entry in fallback_result
    ]


# =============================================================================
# THE SEPARATIONS ARE MEASURED — THESE GUARD THE MEASUREMENT
# =============================================================================
#
# The three separation constants are not preferences, they are the output of
# ``scripts/measure_modern_separation.py``: it renders the worst cluster the
# renderer can be asked to draw and reads the real ink boxes back out of a
# browser. Two things can silently invalidate that result — lowering a constant
# below where ink starts touching, and moving the geometry it was measured
# against. One test each.

#: Separation at which the adversarial cluster's ink first touches, per ring,
#: from the harness. Below these, glyphs and text overlap outright; the shipped
#: constants sit a notch above, leaving ~0.25 wheel units of daylight.
_TOUCHING_SEPARATION = {
    "PLANET_MIN_SEPARATION": 6.50,
    "SYN_OUTER_MIN_SEPARATION": 5.25,
    "SYN_INNER_MIN_SEPARATION": 6.75,
}


def test_separations_stay_above_the_measured_collision_floor():
    for name, floor in _TOUCHING_SEPARATION.items():
        value = getattr(draw_modern, name)
        assert value > floor, (
            f"{name} is {value}°, at or below the {floor}° where the adversarial "
            "cluster's ink starts to overlap. Re-run "
            "scripts/measure_modern_separation.py before lowering it further."
        )


#: Everything the measurement depended on: where each cluster row sits, how big
#: its content is drawn, and how wide the rings are. Arc length per degree falls
#: with the radius, so moving a row inward or growing its text eats the gap the
#: separations were chosen to leave.
#:
#: One input is deliberately absent: the glyph set itself. At the shipped
#: separations every binding pair is text against text — the glyph row, drawn
#: furthest out and narrower than the strings below it, has room to spare — so
#: a new point glyph would have to be far wider than any current one to matter.
_MEASURED_GEOMETRY = {
    "CENTER": 50.0,
    "FEASIBLE_TOTAL_DEGREES": 320.0,
    "DEFAULT_CLUSTER_CLEARANCE": 0.45,
    # Natal ring
    "PLANET_SCALE_BASE": 0.135,
    "DEGREES_FONT_SIZE": 2,
    "SIGN_SCALE_BASE": 0.078,
    "MINUTES_FONT_SIZE": 1.85,
    "RX_FONT_SIZE": 1.6,
    # Dual rings
    "SYN_R_INNER_PLANET_INNER": 15.5,
    "SYN_R_INNER_PLANET_OUTER": 29.5,
    "SYN_R_OUTER_PLANET_INNER": 29.5,
    "SYN_R_OUTER_PLANET_OUTER": 43.5,
    "SYN_OUTER_PLANET_GLYPH_Y": 9.0,
    "SYN_OUTER_DEGREES_Y": 12.0,
    "SYN_OUTER_SIGN_Y": 14.5,
    "SYN_OUTER_MINUTES_Y": 16.5,
    "SYN_OUTER_RX_Y": 18.5,
    "SYN_INNER_PLANET_GLYPH_Y": 22.5,
    "SYN_INNER_DEGREES_Y": 25.0,
    "SYN_INNER_SIGN_Y": 27.5,
    "SYN_INNER_MINUTES_Y": 29.5,
    "SYN_INNER_RX_Y": 31.5,
    "SYN_PLANET_SCALE": 0.115,
    "SYN_PLANET_SCALE_INNER": 0.095,
    "SYN_DEGREES_FONT_SIZE": 1.9,
    "SYN_DEGREES_FONT_SIZE_INNER": 1.6,
    "SYN_SIGN_SCALE": 0.062,
    "SYN_MINUTES_FONT_SIZE": 1.4,
    "SYN_RX_FONT_SIZE": 1.2,
}

#: The natal ring's row positions live as defaults on the drawing function
#: rather than as module constants, so they are pinned through the signature.
_MEASURED_NATAL_ROWS = {
    "glyph_y": 11.0,
    "degrees_y": 14.5,
    "sign_y": 18.0,
    "minutes_y": 22.0,
    "rx_y": 25.0,
}

_REMEASURE = (
    "The separations in draw_modern were measured against this geometry. "
    "Re-run scripts/measure_modern_separation.py and update the constants "
    "(and this fixture) to whatever it reports now."
)


@pytest.mark.parametrize(("name", "expected"), sorted(_MEASURED_GEOMETRY.items()))
def test_measured_geometry_is_unchanged(name, expected):
    assert getattr(draw_modern, name) == expected, f"{name} moved. {_REMEASURE}"


def test_measured_natal_row_positions_are_unchanged():
    import inspect

    signature = inspect.signature(draw_modern._draw_single_planet_in_ring)
    actual = {row: signature.parameters[row].default for row in _MEASURED_NATAL_ROWS}
    assert actual == _MEASURED_NATAL_ROWS, f"Natal cluster rows moved. {_REMEASURE}"


def test_dual_rings_respect_their_own_content_derived_separations():
    """Each dual ring spaces its planets by what they draw, at its own radius.

    The two rings used to share a hardcoded 10.0°; now each pair of neighbours
    reserves the arc its actual ink needs — computed per ring, because arc per
    degree falls with the radius — capped at the ring's measured ceiling. This
    renders a synastry chart, rebuilds every pair's requirement from the SVG's
    own metadata, and checks the rendered spacing honours it.
    """
    import re
    from types import SimpleNamespace

    from kerykeion import AstrologicalSubjectFactory
    from kerykeion.chart_data_factory import ChartDataFactory
    from kerykeion.charts.chart_drawer import ChartDrawer

    def subject(name, year, month, day, hour, minute, lat, lng, tz):
        return AstrologicalSubjectFactory.from_birth_data(
            name, year, month, day, hour, minute,
            lat=lat, lng=lng, tz_str=tz, online=False, suppress_geonames_warning=True,
        )

    # 2000-02-26 brings its Aquarius/Pisces stellium, so both rings hold a
    # cluster tight enough to be compressed down to the pairwise requirements.
    first = subject("Ring A", 2000, 2, 26, 12, 0, 51.5, 0.0, "UTC")
    second = subject("Ring B", 1993, 9, 12, 8, 30, 41.9, 12.5, "Europe/Rome")
    chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
    svg = ChartDrawer(chart_data=chart_data).generate_wheel_only_svg_string(style="modern")

    chart_point_pattern = re.compile(
        r"""<g\s+kr:node=['"]ChartPoint['"](?P<attributes>[^>]*)"""
        r"""transform=['"]rotate\(-(?P<display>\d+\.\d+)\s+50\.0\s+50\.0\)['"]""",
    )

    def attribute(blob: str, name: str) -> str | None:
        match = re.search(rf"""kr:{name}=['"]([^'"]+)['"]""", blob)
        return match.group(1) if match else None

    rings: dict[str, list[tuple[float, SimpleNamespace]]] = {"0": [], "1": []}
    for match in chart_point_pattern.finditer(svg):
        blob = match.group("attributes")
        point_stand_in = SimpleNamespace(
            name=attribute(blob, "slug"),
            point_type="AstrologicalPoint",
            sign=attribute(blob, "sign"),
            position=float(attribute(blob, "signposition")),
            retrograde=attribute(blob, "retrograde") == "true",
        )
        rings[attribute(blob, "horoscope") or "0"].append((float(match.group("display")), point_stand_in))

    # horoscope "0" is subject 1 in the inner ring, "1" is subject 2 outside it;
    # the geometry below mirrors what draw_modern_dual_horoscope passes in.
    ring_layouts = {
        "0": dict(
            ceiling=draw_modern.SYN_INNER_MIN_SEPARATION,
            row_radii={
                "glyph": 50.0 - draw_modern.SYN_INNER_PLANET_GLYPH_Y,
                "degrees": 50.0 - draw_modern.SYN_INNER_DEGREES_Y,
                "sign": 50.0 - draw_modern.SYN_INNER_SIGN_Y,
                "minutes": 50.0 - draw_modern.SYN_INNER_MINUTES_Y,
                "rx": 50.0 - draw_modern.SYN_INNER_RX_Y,
            },
            scales=dict(
                planet_scale_base=draw_modern.SYN_PLANET_SCALE_INNER,
                degrees_font_size=draw_modern.SYN_DEGREES_FONT_SIZE_INNER,
                sign_scale_base=draw_modern.SYN_SIGN_SCALE,
                minutes_font_size=draw_modern.SYN_MINUTES_FONT_SIZE,
                rx_font_size=draw_modern.SYN_RX_FONT_SIZE,
            ),
        ),
        "1": dict(
            ceiling=draw_modern.SYN_OUTER_MIN_SEPARATION,
            row_radii={
                "glyph": 50.0 - draw_modern.SYN_OUTER_PLANET_GLYPH_Y,
                "degrees": 50.0 - draw_modern.SYN_OUTER_DEGREES_Y,
                "sign": 50.0 - draw_modern.SYN_OUTER_SIGN_Y,
                "minutes": 50.0 - draw_modern.SYN_OUTER_MINUTES_Y,
                "rx": 50.0 - draw_modern.SYN_OUTER_RX_Y,
            },
            scales=dict(
                planet_scale_base=draw_modern.SYN_PLANET_SCALE,
                degrees_font_size=draw_modern.SYN_DEGREES_FONT_SIZE,
                sign_scale_base=draw_modern.SYN_SIGN_SCALE,
                minutes_font_size=draw_modern.SYN_MINUTES_FONT_SIZE,
                rx_font_size=draw_modern.SYN_RX_FONT_SIZE,
            ),
        ),
    }

    def pair_requirement(layout: dict, one: SimpleNamespace, other: SimpleNamespace) -> float:
        import math

        clearance = draw_modern.DEFAULT_CLUSTER_CLEARANCE
        first_profile = draw_modern._cluster_row_profile(one, **layout["scales"])
        second_profile = draw_modern._cluster_row_profile(other, **layout["scales"])
        required = 0.0
        for row, radius in layout["row_radii"].items():
            if row not in first_profile or row not in second_profile:
                continue
            width_needed = first_profile[row][0] + second_profile[row][0] + clearance
            height_needed = first_profile[row][1] + second_profile[row][1] + clearance
            arc_per_degree = radius * math.pi / 180.0
            required = max(required, math.hypot(width_needed, height_needed) / arc_per_degree)
        return min(layout["ceiling"], required)

    for horoscope_id, layout in ring_layouts.items():
        members = sorted(rings[horoscope_id], key=lambda entry: entry[0])
        assert len(members) > 2, f"Ring {horoscope_id} rendered too few points to judge"
        compressed_pairs = 0
        for (display, planet), (next_display, next_planet) in zip(members, members[1:]):
            gap = _normalize_angle(next_display - display)
            requirement = pair_requirement(layout, planet, next_planet)
            assert gap >= requirement - 1e-6, (
                f"Ring {horoscope_id}: {planet.name} and {next_planet.name} sit "
                f"{gap:.3f}° apart but their ink needs {requirement:.3f}°."
            )
            if gap <= requirement + 0.05:
                compressed_pairs += 1
        # The stellium must actually compress something down onto its
        # requirement, or the assertions above never bit.
        assert compressed_pairs > 0, (
            f"Ring {horoscope_id} has no pair at its content-derived requirement — "
            "the fixture is not dense enough to prove anything."
        )
