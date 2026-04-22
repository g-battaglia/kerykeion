"""
Regression tests for the modern chart collision/decluttering algorithm.

Covers the bug where a planet in a tight cluster could be pushed past its
neighbours, breaking zodiacal order (e.g. Neptune 5° Aquarius ending up
displayed after Uranus 17° Aquarius).

See: kerykeion/charts/draw_modern.py::_resolve_planet_collisions
"""

from __future__ import annotations

import pytest

from kerykeion.charts.draw_modern import (
    PLANET_MIN_SEPARATION,
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
    )
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
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
