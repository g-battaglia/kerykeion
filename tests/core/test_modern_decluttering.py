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


@pytest.mark.parametrize("glyph_size", ["small", "medium", "large"])
def test_modern_chart_2000_02_26_neptune_order(glyph_size):
    """
    End-to-end regression test on a real chart that reproduces the issue
    conditions: Neptune ~5° Aqu inside a dense cluster with Uranus 17° Aqu,
    Venus 10° Aqu, and True_South_Lunar_Node 3° Aqu.

    Parses the generated modern SVG and asserts that the rendered order of
    ChartPoint glyphs (by display_angle from their ``transform="rotate(...)"``
    attribute) follows the true zodiacal order — at every glyph size, since a
    bigger cluster is exactly the pressure that pushed planets past each other
    in the original bug.
    """
    from kerykeion import AstrologicalSubjectFactory
    from kerykeion.chart_data.factory import ChartDataFactory
    from kerykeion.charts.drawer import ChartDrawer
    from kerykeion.charts.svg_metadata import parse_chart_points
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
    svg = ChartDrawer(chart_data=chart_data).generate_wheel_only_svg_string(
        style="modern", glyph_size=glyph_size
    )

    display_angles = {tag.slug: tag.display_angle for tag in parse_chart_points(svg)}

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
#: from the harness (floor mode, measured in the wheel's pinned font stack with
#: stroke-aware glyph boxes). Below these, glyphs and text overlap outright;
#: the shipped constants sit at the separation where the harness reports a
#: quarter of a unit of daylight — margin that doubles as slack for platforms
#: whose fallback sans inks wider than the measured stack.
#:
#: These are outputs, and they move when the ink does. Enlarging the clusters
#: pushed all three up (6.25/5.00/6.25 -> 7.00/5.25/8.25), and because the
#: recorded numbers had not been re-measured this test went on passing against
#: figures the drawing had left behind — while the inner dual ring was in fact
#: shipping a ceiling below its own overlap point. Re-run the harness whenever a
#: size or a row position changes — and once per glyph size, since every profile
#: carries its own floor; it is the only thing that makes this test mean
#: anything.
#:
#: Measured 2026-08-26, headless Chromium, sweep 4.0–14.0 in 0.25 steps. Two of
#: the three medium floors reproduced the recorded figures exactly; the natal
#: medium reads 7.25 where 7.00 stood — one sweep step, within raster variance
#: between the browser that measured then and the one that measured now, and
#: recorded as measured because this run is the reproducible one.
_TOUCHING_SEPARATION = {
    ("small", "natal"): 6.50,
    ("small", "dual_outer"): 4.75,
    ("small", "dual_inner"): 7.25,
    ("medium", "natal"): 7.25,
    ("medium", "dual_outer"): 5.25,
    ("medium", "dual_inner"): 8.25,
    ("large", "natal"): 9.00,
    ("large", "dual_outer"): 7.25,
    ("large", "dual_inner"): 11.75,
}


@pytest.mark.parametrize(("size", "ring"), sorted(_TOUCHING_SEPARATION))
def test_separations_stay_above_the_measured_collision_floor(size, ring):
    value = draw_modern.GLYPH_SIZE_PROFILES[size][ring].min_separation
    floor = _TOUCHING_SEPARATION[(size, ring)]
    assert value > floor, (
        f"{size}/{ring} ships a ceiling of {value}°, at or below the {floor}° "
        "where the adversarial cluster's ink starts to overlap. Re-run "
        "scripts/measure_modern_separation.py --glyph-size before lowering it."
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
    # Natal ring rows (the single source both the renderer and row_radii read)
    "NATAL_PLANET_GLYPH_Y": 10.22,
    "NATAL_DEGREES_Y": 14.21,
    "NATAL_SIGN_Y": 17.89,
    "NATAL_MINUTES_Y": 21.89,
    "NATAL_RX_Y": 25.25,
    # Natal ring
    "PLANET_SCALE_BASE": 0.18144,
    "DEGREES_FONT_SIZE": 2.24,
    "SIGN_SCALE_BASE": 0.10309,
    "MINUTES_FONT_SIZE": 2.072,
    "RX_FONT_SIZE": 1.792,
    # Dual rings
    "SYN_R_INNER_PLANET_INNER": 15.5,
    "SYN_R_INNER_PLANET_OUTER": 29.5,
    "SYN_R_OUTER_PLANET_INNER": 29.5,
    "SYN_R_OUTER_PLANET_OUTER": 44.652,
    "SYN_OUTER_PLANET_GLYPH_Y": 8.38,
    "SYN_OUTER_DEGREES_Y": 11.82,
    "SYN_OUTER_SIGN_Y": 14.76,
    "SYN_OUTER_MINUTES_Y": 17.37,
    "SYN_OUTER_RX_Y": 19.54,
    "SYN_INNER_PLANET_GLYPH_Y": 22.68,
    "SYN_INNER_DEGREES_Y": 26.12,
    "SYN_INNER_SIGN_Y": 29.06,
    "SYN_INNER_MINUTES_Y": 31.67,
    "SYN_INNER_RX_Y": 33.84,
    "SYN_PLANET_SCALE": 0.132,
    "SYN_PLANET_SCALE_INNER": 0.132,
    "SYN_DEGREES_FONT_SIZE": 2.12,
    "SYN_DEGREES_FONT_SIZE_INNER": 2.12,
    "SYN_SIGN_SCALE": 0.062,
    "SYN_MINUTES_FONT_SIZE": 1.22,
    "SYN_RX_FONT_SIZE": 1.02,
}

_REMEASURE = (
    "The separations in draw_modern were measured against this geometry. "
    "Re-run scripts/measure_modern_separation.py and update the constants "
    "(and this fixture) to whatever it reports now."
)


@pytest.mark.parametrize(("name", "expected"), sorted(_MEASURED_GEOMETRY.items()))
def test_measured_geometry_is_unchanged(name, expected):
    assert getattr(draw_modern, name) == expected, f"{name} moved. {_REMEASURE}"


@pytest.mark.parametrize("glyph_size", ["small", "medium", "large"])
def test_dual_rings_respect_their_own_content_derived_separations(glyph_size):
    """Each dual ring spaces its planets by what they draw, at its own radius.

    The two rings used to share a hardcoded 10.0°; now each pair of neighbours
    reserves the arc its actual ink needs — computed per ring, because arc per
    degree falls with the radius — capped at the ring's measured ceiling. This
    renders a synastry chart, rebuilds every pair's requirement from the SVG's
    own metadata, and checks the rendered spacing honours it.

    Parametrised over the glyph sizes: run at large this is what proves the
    per-size ceilings are sufficient in the renderer's own hands, not merely
    plausible on the harness bench.
    """
    from types import SimpleNamespace

    from kerykeion import AstrologicalSubjectFactory
    from kerykeion.chart_data.factory import ChartDataFactory
    from kerykeion.charts.drawer import ChartDrawer
    from kerykeion.charts.svg_metadata import parse_chart_points

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
    svg = ChartDrawer(chart_data=chart_data).generate_wheel_only_svg_string(
        style="modern", glyph_size=glyph_size
    )

    rings: dict[str, list[tuple[float, SimpleNamespace]]] = {"0": [], "1": []}
    for tag in parse_chart_points(svg):
        point_stand_in = SimpleNamespace(
            name=tag.slug,
            point_type="AstrologicalPoint",
            sign=tag.sign,
            position=tag.sign_position,
            retrograde=tag.retrograde,
        )
        rings[tag.horoscope].append((tag.display_angle, point_stand_in))

    # horoscope "0" is subject 1 in the inner ring, "1" is subject 2 outside it;
    # the layouts are the very profiles draw_modern_dual_horoscope reads, so the
    # test follows every size the renderer can be asked for.
    def layout_from(profile) -> dict:
        return dict(
            ceiling=profile.min_separation,
            row_radii={
                "glyph": 50.0 - profile.glyph_y,
                "degrees": 50.0 - profile.degrees_y,
                "sign": 50.0 - profile.sign_y,
                "minutes": 50.0 - profile.minutes_y,
                "rx": 50.0 - profile.rx_y,
            },
            scales=profile.scale_config(),
        )

    profiles = draw_modern.GLYPH_SIZE_PROFILES[glyph_size]
    ring_layouts = {
        "0": layout_from(profiles["dual_inner"]),
        "1": layout_from(profiles["dual_outer"]),
    }

    def pair_requirement(
        layout: dict, one: SimpleNamespace, other: SimpleNamespace, pair_mid_angle: float
    ) -> float:
        # The production formula, on profiles rebuilt from the SVG's metadata:
        # the test verifies the rendered spacing against the same contract the
        # resolver enforces, not against a private reimplementation of it.
        return draw_modern._pair_required_separation(
            draw_modern._cluster_row_profile(one, **layout["scales"]),
            draw_modern._cluster_row_profile(other, **layout["scales"]),
            pair_mid_angle,
            row_radii=layout["row_radii"],
            clearance=draw_modern.DEFAULT_CLUSTER_CLEARANCE,
            ceiling=layout["ceiling"],
        )

    for horoscope_id, layout in ring_layouts.items():
        members = sorted(rings[horoscope_id], key=lambda entry: entry[0])
        assert len(members) > 2, f"Ring {horoscope_id} rendered too few points to judge"
        compressed_pairs = 0
        for (display, planet), (next_display, next_planet) in zip(members, members[1:]):
            gap = _normalize_angle(next_display - display)
            pair_mid_angle = display + gap / 2.0
            requirement = pair_requirement(layout, planet, next_planet, pair_mid_angle)
            # Tolerance: the SVG serializes display angles to 6 decimals, and
            # the requirement is re-evaluated here at the truncated midpoint.
            assert gap >= requirement - 5e-3, (
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


# =============================================================================
# THE AIR YIELDS BEFORE THE POSITIONS DO
# =============================================================================
#
# Every adjacent pair asks for its ink plus DEFAULT_CLUSTER_CLEARANCE of
# daylight. On a full wheel those asks can sum past what a circle has, and the
# placement's last resort is to scale every separation down together — which
# eats into the ink reservations, so clusters overlap *and* land far from their
# true degrees. The clearance is the cheaper thing to spend: it is air, and the
# ink is the reading. So an over-subscribed wheel now gives up the air first,
# as far as none, before anything compresses the ink.


def _packed_ring(count: int, spread: float = 0.4) -> list[dict]:
    """`count` clusters packed into a narrow arc, with varied content.

    Varied on purpose: identical clusters would make every pair's requirement
    identical, and the ladder is about a *sum* of differing requirements.
    """
    entries = []
    for index in range(count):
        point = _stand_in_point(
            sign=("Aqu", "Vir", "Cap", "Leo")[index % 4],
            position=15.0 + (index % 40) * 0.7,
            retrograde=index % 3 == 0,
        )
        entries.append(
            {
                "angle": 150.0 + index * spread,
                "point": f"P{index}",
                "row_half_widths": draw_modern._cluster_row_profile(point),
            }
        )
    return entries


def _total_demand(entries: list[dict], air: float) -> float:
    """What the wheel is asked for at *air* units of clearance, in degrees."""
    ordered = sorted(entries, key=lambda entry: entry["angle"])
    pairs = list(zip(ordered, ordered[1:] + [ordered[0]]))
    return sum(
        draw_modern._pair_required_separation(
            first["row_half_widths"],
            second["row_half_widths"],
            (first["angle"] + second["angle"]) / 2.0,
            row_radii=_NATAL_ROW_RADII,
            clearance=air,
            ceiling=PLANET_MIN_SEPARATION,
        )
        for first, second in pairs
    )


def test_an_uncrowded_wheel_never_spends_its_air():
    """The common case must be untouched: fourteen points ask for a quarter of
    the wheel, and every pair keeps its full clearance."""
    entries = _packed_ring(10, spread=30.0)
    assert _total_demand(entries, draw_modern.DEFAULT_CLUSTER_CLEARANCE) < 320.0, (
        "fixture is already over-subscribed — it cannot prove the dormant case"
    )

    resolved = _resolve_planet_collisions(entries, row_radii=_NATAL_ROW_RADII)
    ordered = sorted(resolved, key=lambda entry: entry["display_angle"])
    for first, second in zip(ordered, ordered[1:]):
        gap = second["display_angle"] - first["display_angle"]
        with_full_air = draw_modern._pair_required_separation(
            first["row_half_widths"],
            second["row_half_widths"],
            (first["display_angle"] + second["display_angle"]) / 2.0,
            row_radii=_NATAL_ROW_RADII,
            clearance=draw_modern.DEFAULT_CLUSTER_CLEARANCE,
            ceiling=PLANET_MIN_SEPARATION,
        )
        assert gap >= with_full_air - 1e-6


#: The ring counts below moved from 52/54 to 64/66 when the planet glyph was
#: re-anchored on its real 24-unit box: every symbol reserves two native units
#: less on each side than it did under the old 28-unit convention, so the same
#: fixture stopped reaching the ladder at all. The band is 62 to 70 points; the
#: counts sit inside it rather than on its edge.
#:
#: How far a pair may still fall short of its bare ink on an over-subscribed
#: wheel, in degrees. Not zero, and the reason is worth stating: the affordable
#: clearance is solved once on the *true* orientations, while the refinement
#: below re-evaluates every pair at the orientations it was actually placed at
#: and ratchets the requirements upward from there. A wheel that fit when the
#: air was priced can therefore be marginally over again by the time it is
#: placed, and `place` compresses the remainder.
#:
#: The figure is derived from the per-pair ceiling, not chosen: it was 0.19°
#: against a ~6.9° requirement when the ceiling was 6.5, and 0.37° against 7.75
#: now that a re-measured collision floor has pushed the ceiling there. Both are
#: a shade under 5% of what the pair asks for, and the arithmetic is why —
#: raising the ceiling raises every pair's demand, so an over-subscribed wheel
#: has proportionally more to give up before the ladder runs out of air.
#:
#: So: re-derive this when the ceiling moves, and re-run the sweep when the ink
#: tables move. What must never happen is nudging it upward to make a failure go
#: away — the threshold is the property, and a residue that climbs without the
#: ceiling climbing means the ladder has started compressing ink for real.
_INK_COMPRESSION_RESIDUE = 0.40


def test_an_oversubscribed_wheel_gives_up_air_before_ink():
    """Past the budget, the clearance goes first and the ink very nearly stays.

    The fixture is checked into the band it needs to be in — over budget with
    the air, under it without — so a drift in the ink tables that moved it out
    would fail here rather than quietly make the test prove nothing.
    """
    # 47 is the lowest count that reaches the ladder at the current cluster size
    # and ceiling — it was 52 at the previous size, and 64 before that. The
    # window narrows every time the ink grows, because the residue climbs with
    # the count (0.23° at 46, 0.37° at 47, 0.40° at 48): more ink per point
    # leaves the ladder less air to spend before it starts squeezing. The lowest
    # count in the band is the honest choice — it is the gentlest case that
    # still exercises the ladder, so a residue here is not an artefact of
    # over-packing the fixture.
    entries = _packed_ring(47)
    with_air = _total_demand(entries, draw_modern.DEFAULT_CLUSTER_CLEARANCE)
    without_air = _total_demand(entries, 0.0)
    assert with_air > draw_modern.FEASIBLE_TOTAL_DEGREES, (
        f"fixture only asks for {with_air:.1f}° — it never reaches the ladder"
    )
    assert without_air <= draw_modern.FEASIBLE_TOTAL_DEGREES, (
        f"fixture asks {without_air:.1f}° even with no air — beyond what the "
        "ladder can rescue, so it cannot prove the ink survives"
    )

    resolved = _resolve_planet_collisions(entries, row_radii=_NATAL_ROW_RADII)
    ordered = sorted(resolved, key=lambda entry: entry["display_angle"])
    worst_shortfall = 0.0
    for first, second in zip(ordered, ordered[1:]):
        gap = second["display_angle"] - first["display_angle"]
        bare_ink = draw_modern._pair_required_separation(
            first["row_half_widths"],
            second["row_half_widths"],
            (first["display_angle"] + second["display_angle"]) / 2.0,
            row_radii=_NATAL_ROW_RADII,
            clearance=0.0,
            ceiling=PLANET_MIN_SEPARATION,
        )
        worst_shortfall = max(worst_shortfall, bare_ink - gap)

    assert worst_shortfall <= _INK_COMPRESSION_RESIDUE, (
        f"the tightest pair falls {worst_shortfall:.3f}° short of its bare ink. "
        "Spending the air is meant to keep this to the refinement residue; a "
        "larger figure means the ink is being compressed again."
    )


def test_spending_the_air_is_reported(caplog):
    """A layout that quietly drops its own guarantee is indistinguishable from
    one that never needed to, so it says when it does — and stays silent when
    it does not."""
    import logging

    with caplog.at_level(logging.INFO, logger=draw_modern.logger.name):
        _resolve_planet_collisions(_packed_ring(52), row_radii=_NATAL_ROW_RADII)
    assert any("air between clusters was reduced" in record.message for record in caplog.records), (
        f"the reduction was not reported; captured: {[r.message for r in caplog.records]}"
    )

    caplog.clear()
    with caplog.at_level(logging.INFO, logger=draw_modern.logger.name):
        _resolve_planet_collisions(_packed_ring(10, spread=30.0), row_radii=_NATAL_ROW_RADII)
    assert not [r for r in caplog.records if "air between clusters" in r.message], (
        "an uncrowded wheel reported spending air it never spent"
    )


# =============================================================================
# GLYPH-SIZE PROFILES
# =============================================================================

#: The small and large profiles, pinned literal by literal. These are the
#: printed output of scripts/derive_modern_cluster_profiles.py — the derivation
#: tests below prove they still ARE that output; this fixture makes any drift
#: name the exact number that moved. min_separation is the exception no formula
#: owns: measured by the harness per size, policy and floors documented at
#: _TOUCHING_SEPARATION.
_PROFILE_GEOMETRY = {
    ("small", "natal"): {
        "sizes": (0.163296, 2.016, 0.092781, 1.8648, 1.6128),
        "rows": (9.7328, 13.3238, 16.6358, 20.2358, 23.2598),
        "min_separation": 7.0,
        "indicator": {"start_y": 5.348, "tick_length": 0.9675, "arc_radius": 43.752},
    },
    ("small", "dual_outer"): {
        "sizes": (0.1188, 1.908, 0.0558, 1.098, 0.918),
        "rows": (8.0768, 11.1728, 13.8188, 16.1678, 18.1208),
        "min_separation": 5.25,
        "indicator": {"start_y": 5.348, "tick_length": 0.63, "arc_radius": 44.022},
    },
    ("small", "dual_inner"): {
        "sizes": (0.1188, 1.908, 0.0558, 1.098, 0.918),
        "rows": (22.462, 25.558, 28.204, 30.553, 32.506),
        "min_separation": 8.0,
        "indicator": {"start_y": 20.5, "tick_length": 0.27, "arc_radius": 29.23},
    },
    ("large", "natal"): {
        "sizes": (0.22644927536231882, 2.79567, 0.128663, 2.585995, 2.236536),
        "rows": (10.1551, 14.5798, 18.3845, 22.3458, 25.6815),
        "min_separation": 9.5,
        "indicator": {"start_y": 5.348, "tick_length": 0.6959, "arc_radius": 44.0046},
    },
    ("large", "dual_outer"): {
        "sizes": (0.18115942028985507, 2.90953, 0.08509, 1.674352, 1.399868),
        "rows": (8.5197, 12.3143, 15.264, 17.6455, 19.6148),
        "min_separation": 7.75,
        "indicator": {"start_y": 5.348, "tick_length": 0.2881, "arc_radius": 44.3639},
    },
    ("large", "dual_inner"): {
        "sizes": (0.18115942028985507, 2.90953, 0.08509, 1.674352, 1.399868),
        "rows": (23.4697, 27.0889, 29.8331, 31.9873, 33.7656),
        "min_separation": 12.5,
        "indicator": {"start_y": 20.5, "tick_length": 0.25, "arc_radius": 29.4311},
    },
}

_SIZE_FIELDS = (
    "planet_scale_base",
    "degrees_font_size",
    "sign_scale_base",
    "minutes_font_size",
    "rx_font_size",
)
_ROW_FIELDS = ("glyph_y", "degrees_y", "sign_y", "minutes_y", "rx_y")


@pytest.mark.parametrize(("size", "ring"), sorted(_PROFILE_GEOMETRY))
def test_profile_geometry_is_unchanged(size, ring):
    profile = draw_modern.GLYPH_SIZE_PROFILES[size][ring]
    expected = _PROFILE_GEOMETRY[(size, ring)]
    for field, value in zip(_SIZE_FIELDS, expected["sizes"]):
        assert getattr(profile, field) == pytest.approx(value, abs=5e-7), (
            f"{size}/{ring}.{field} moved. Re-run "
            "scripts/derive_modern_cluster_profiles.py and paste its output."
        )
    for field, value in zip(_ROW_FIELDS, expected["rows"]):
        assert getattr(profile, field) == value, f"{size}/{ring}.{field} moved."
    assert profile.min_separation == expected["min_separation"]
    assert profile.indicator is not None
    for key, value in expected["indicator"].items():
        assert profile.indicator[key] == pytest.approx(value, abs=5e-7), (
            f"{size}/{ring} indicator {key} moved."
        )


def test_medium_profile_is_the_shipped_constants():
    """Medium carries the shipped constants, field for field.

    Equality, not ``is``: CPython folds equal float literals of one module
    into a single constant, so an identity check cannot tell a reference from
    a re-typed copy anyway — what actually guards the default path is this
    equality tied to _MEASURED_GEOMETRY's own pins, plus the byte-identical
    baseline suite. ``indicator is None`` for the natal ring is load-bearing,
    though: it keeps the ``if indicator_config:`` branch in _draw_planet_ring
    falsy, exactly as the pre-profile call site was.
    """
    natal = draw_modern.GLYPH_SIZE_PROFILES["medium"]["natal"]
    for field, constant in zip(
        _SIZE_FIELDS + _ROW_FIELDS + ("min_separation",),
        (
            draw_modern.PLANET_SCALE_BASE,
            draw_modern.DEGREES_FONT_SIZE,
            draw_modern.SIGN_SCALE_BASE,
            draw_modern.MINUTES_FONT_SIZE,
            draw_modern.RX_FONT_SIZE,
            draw_modern.NATAL_PLANET_GLYPH_Y,
            draw_modern.NATAL_DEGREES_Y,
            draw_modern.NATAL_SIGN_Y,
            draw_modern.NATAL_MINUTES_Y,
            draw_modern.NATAL_RX_Y,
            draw_modern.PLANET_MIN_SEPARATION,
        ),
    ):
        assert getattr(natal, field) == constant, f"medium natal {field} drifted from the constant"
    assert natal.indicator is None

    outer = draw_modern.GLYPH_SIZE_PROFILES["medium"]["dual_outer"]
    inner = draw_modern.GLYPH_SIZE_PROFILES["medium"]["dual_inner"]
    assert outer.planet_scale_base == draw_modern.SYN_PLANET_SCALE
    assert inner.planet_scale_base == draw_modern.SYN_PLANET_SCALE_INNER
    assert outer.min_separation == draw_modern.SYN_OUTER_MIN_SEPARATION
    assert inner.min_separation == draw_modern.SYN_INNER_MIN_SEPARATION
    assert outer.indicator is not None and inner.indicator is not None
    assert outer.indicator["tick_length"] == draw_modern.SYN_INDICATOR_OUTER_TICK
    assert outer.indicator["arc_radius"] == draw_modern.SYN_INDICATOR_OUTER_ARC_R
    assert inner.indicator["tick_length"] == draw_modern.SYN_INDICATOR_INNER_TICK
    assert inner.indicator["arc_radius"] == draw_modern.SYN_INDICATOR_INNER_ARC_R
    for field, constant in zip(
        _ROW_FIELDS,
        (
            draw_modern.SYN_OUTER_PLANET_GLYPH_Y,
            draw_modern.SYN_OUTER_DEGREES_Y,
            draw_modern.SYN_OUTER_SIGN_Y,
            draw_modern.SYN_OUTER_MINUTES_Y,
            draw_modern.SYN_OUTER_RX_Y,
        ),
    ):
        assert getattr(outer, field) == constant, f"medium dual_outer {field} drifted from the constant"
    for field, constant in zip(
        _ROW_FIELDS,
        (
            draw_modern.SYN_INNER_PLANET_GLYPH_Y,
            draw_modern.SYN_INNER_DEGREES_Y,
            draw_modern.SYN_INNER_SIGN_Y,
            draw_modern.SYN_INNER_MINUTES_Y,
            draw_modern.SYN_INNER_RX_Y,
        ),
    ):
        assert getattr(inner, field) == constant, f"medium dual_inner {field} drifted from the constant"


def test_derivation_reproduces_medium():
    """The scaling rule is a fixed point at k=1: it must re-lay the shipped rows.

    By construction the decomposition telescopes, so this cannot fail on a
    perturbed ink table — what it pins is the script's own coherence: the
    layout loop, the tether handling and the decomposition must be inverses
    of each other, or medium itself comes out somewhere else. The teeth
    against ink/radius/policy changes are in
    test_derivation_reproduces_the_shipped_profiles: at k != 1 every one of
    those moves re-prices the small and large literals.
    """
    from scripts.derive_modern_cluster_profiles import RINGS, decompose, derive

    for ring in RINGS.values():
        decomposition = decompose(ring)  # raises if ink + air != band
        assert decomposition.ink + decomposition.air == pytest.approx(
            decomposition.band, abs=1e-9
        )
        reproduced = derive(ring, 1.0)
        for shipped, derived in zip(ring.rows, reproduced.rows):
            assert derived == pytest.approx(shipped, abs=1e-9), ring.name


@pytest.mark.parametrize(("size", "ring_name"), sorted(_PROFILE_GEOMETRY))
def test_derivation_reproduces_the_shipped_profiles(size, ring_name):
    """The module literals are the script's output — re-run it and compare.

    Kills a hand edit of any profile literal, and equally a change to the
    derivation policy (dropping the tether scaling, the corner anchor, the
    tick floor) that would silently re-price every profile.
    """
    from scripts.derive_modern_cluster_profiles import RINGS, derive, size_factors

    profile = draw_modern.GLYPH_SIZE_PROFILES[size][ring_name]
    derived = derive(RINGS[ring_name], size_factors(ring_name)[size])
    for field, value in zip(_SIZE_FIELDS, derived.sizes):
        assert getattr(profile, field) == pytest.approx(value, abs=5e-7), (
            f"{size}/{ring_name}.{field} no longer matches the derivation"
        )
    for field, value in zip(_ROW_FIELDS, derived.rows):
        assert getattr(profile, field) == pytest.approx(value, abs=5e-5), (
            f"{size}/{ring_name}.{field} no longer matches the derivation"
        )
    assert profile.indicator is not None
    assert profile.indicator["tick_length"] == pytest.approx(derived.tick, abs=5e-5)
    assert profile.indicator["arc_radius"] == pytest.approx(derived.arc_radius, abs=5e-5)
    # min_separation is deliberately NOT compared: the script prints an analytic
    # seed, but the shipped value is the harness's measurement (see
    # _TOUCHING_SEPARATION); the two agreeing would be a coincidence.


def test_large_is_exact_classic_parity():
    """The headline contract: large draws the planet glyph at the classic size.

    The classic engine draws its 24-unit glyph box at scale 1.0 on a single
    wheel and 0.8 on a dual; the modern wheel lives behind the 0.92 zodiac
    wrapper and the 4.8 page scale. The base is WRITTEN as that expression, so
    the assertion is exact — replace it with the rounded decimal and this
    fails on the identity check, not on a tolerance.
    """
    large = draw_modern.GLYPH_SIZE_PROFILES["large"]
    single = large["natal"].planet_scale_base
    dual = large["dual_outer"].planet_scale_base
    assert single == 1.0 / (draw_modern.ZODIAC_BG_SCALE * draw_modern.MODERN_PAGE_SCALE)
    assert dual == 0.8 / (draw_modern.ZODIAC_BG_SCALE * draw_modern.MODERN_PAGE_SCALE)
    assert large["dual_inner"].planet_scale_base == dual
    box = 24
    assert box * single * draw_modern.ZODIAC_BG_SCALE * draw_modern.MODERN_PAGE_SCALE == pytest.approx(24.0, abs=1e-12)
    assert box * dual * draw_modern.ZODIAC_BG_SCALE * draw_modern.MODERN_PAGE_SCALE == pytest.approx(19.2, abs=1e-12)


@pytest.mark.parametrize("size", ["small", "medium", "large"])
@pytest.mark.parametrize("ring_name", ["natal", "dual_outer", "dual_inner"])
def test_no_cluster_row_leaves_its_ring(size, ring_name):
    """Worst-case ink of every row stays inside the ring's band, at every size.

    The band runs from the tether's deepest reach to the ring's inner edge.
    The tight spot is the large dual-inner bottom margin (0.03 units): a size
    nudge there without a row move fails here first.
    """
    from scripts.derive_modern_cluster_profiles import (
        RINGS,
        worst_glyph_half_height,
        worst_sign_half_height,
    )

    ring = RINGS[ring_name]
    profile = draw_modern.GLYPH_SIZE_PROFILES[size][ring_name]
    if profile.indicator is None:
        tether_reach = ring.start_y + ring.arc_drop + ring.tick
    else:
        tether_reach = (
            (50.0 - profile.indicator["arc_radius"]) + profile.indicator["tick_length"]
        )
    inner_edge = ring.inner_edge_y

    halves = (
        worst_glyph_half_height() * profile.planet_scale_base,
        0.5 * profile.degrees_font_size,
        worst_sign_half_height() * profile.sign_scale_base,
        0.5 * profile.minutes_font_size,
        0.5 * profile.rx_font_size,
    )
    rows = tuple(getattr(profile, field) for field in _ROW_FIELDS)

    # Rows must descend and stay clear of each other's ink.
    for i in range(4):
        assert rows[i] + halves[i] <= rows[i + 1] - halves[i + 1] + 1e-9, (
            f"{size}/{ring_name}: rows {i} and {i + 1} overlap ink"
        )
    # The glyph row keeps its row-ward ink clear of the tether's end...
    assert rows[0] - halves[0] >= tether_reach - 1e-4, (
        f"{size}/{ring_name}: the glyph row reaches past the tether's end"
    )
    # ...and the last row's ink stays inside the ring.
    assert rows[4] + halves[4] <= inner_edge + 1e-9, (
        f"{size}/{ring_name}: the {_ROW_FIELDS[4]} row leaves the ring"
    )

def test_an_all_points_wheel_at_large_compresses_and_says_so(caplog):
    """40+ points at the large ceilings over-subscribe the wheel — by design.

    The resolver's documented last resort fires (air reduced, then ink
    compressed as far as the ladder allows) and LOGS it. This pins the
    degradation as a stated behaviour rather than a surprise: the large
    all-points wheel is expected to fan tighter than its ceilings, and the
    log line is the receipt.
    """
    import logging

    from kerykeion import AstrologicalSubjectFactory
    from kerykeion.chart_data.factory import ChartDataFactory
    from kerykeion.charts.drawer import ChartDrawer
    from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

    subject = AstrologicalSubjectFactory.from_birth_data(
        "All Points Large", 2000, 2, 26, 12, 0,
        lat=51.5, lng=0.0, tz_str="UTC", online=False,
        suppress_geonames_warning=True, active_points=ALL_ACTIVE_POINTS,
    )
    chart_data = ChartDataFactory.create_natal_chart_data(subject, active_points=ALL_ACTIVE_POINTS)
    with caplog.at_level(logging.INFO, logger="kerykeion"):
        ChartDrawer(chart_data=chart_data).generate_wheel_only_svg_string(
            style="modern", glyph_size="large"
        )
    assert "air between clusters was reduced" in caplog.text, (
        "the large all-points wheel no longer reports its compression — either "
        "the ceilings shrank (check the harness) or the log line moved"
    )
