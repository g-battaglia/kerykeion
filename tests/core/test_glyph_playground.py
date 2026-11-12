"""
Tests for the glyph playground page and the diffs it ships.

The page in ``scripts/glyph_playground.html`` claims something specific: that
the 264 charts it stores as diffs are the charts kerykeion actually draws, not
approximations of them. That claim rests entirely on the diff format round
tripping, so that is what is pinned here — on real renders, not on fixtures of
renders.

The manifest's cap-binding claims are checked against actual display geometry.
What is not pinned here: the JavaScript reassembly (same algorithm, checked in
a browser when the page is built) or every pixel of the committed page. It is
a tuning instrument, not a golden; rebuild it with ``poe playground`` when the
profiles change.

See: scripts/generate_glyph_playground.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree

import pytest

from kerykeion.charts import draw_modern as dm
from scripts import generate_glyph_playground as playground
from scripts.generate_glyph_playground import (
    PAGE_TEMPLATE,
    STEP_COUNT,
    apply_diff,
    compact_diff,
    display_layout,
    lines_of,
    render,
    render_with_layout,
    step_clearance,
    unbound_rings,
)

PAGE = Path(__file__).parent.parent.parent / "scripts" / "glyph_playground.html"


@pytest.fixture(scope="module")
def charts():
    """The two subjects the page draws, built once for the whole module."""
    from kerykeion import AstrologicalSubjectFactory
    from kerykeion.chart_data.factory import ChartDataFactory

    from scripts.generate_glyph_playground import (
        JOHN_LENNON_BIRTH_DATA,
        LIVERPOOL,
        PAUL_MCCARTNEY_BIRTH_DATA,
    )

    john = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True, **LIVERPOOL
    )
    paul = AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney", *PAUL_MCCARTNEY_BIRTH_DATA, suppress_geonames_warning=True, **LIVERPOOL
    )
    return {
        "natal": ChartDataFactory.create_natal_chart_data(john),
        "synastry": ChartDataFactory.create_synastry_chart_data(john, paul),
    }


@pytest.mark.parametrize("size", ["small", "medium", "large"])
@pytest.mark.parametrize("step", [1, 4, STEP_COUNT - 1])
def test_a_single_wheel_diff_rebuilds_its_render(charts, size, step):
    """Apply a diff to its base and the render it came from must come back.

    The widest step matters most: the further a variant moves from its base,
    the more of the diff is structural (a tether that grows an arc changes the
    line count), and only the structural branch can express that.
    """
    base = render(charts["natal"], size, [step_clearance(0)])
    variant = render(charts["natal"], size, [step_clearance(step)], ("natal",))

    rebuilt = apply_diff(lines_of(base), compact_diff(lines_of(base), lines_of(variant)))

    assert rebuilt == variant


@pytest.mark.parametrize(("outer", "inner"), [(0, 5), (7, 0), (3, 8), (8, 8)])
def test_a_dual_wheel_diff_rebuilds_its_render(charts, outer, inner):
    """The rings take their air separately, so a diff has to carry both moves."""
    base = render(charts["synastry"], "large", [step_clearance(0)] * 2)
    variant = render(
        charts["synastry"],
        "large",
        [step_clearance(outer), step_clearance(inner)],
        unbound_rings((outer, "dual_outer"), (inner, "dual_inner")),
    )

    rebuilt = apply_diff(lines_of(base), compact_diff(lines_of(base), lines_of(variant)))

    assert rebuilt == variant


def test_every_air_notch_draws_a_different_wheel(charts):
    """Each notch has to move something, or the scale is decoration.

    Only the notches are compared, not the marked step: where the ceiling does
    not bind, ★ and the 0.45 notch are the same chart on purpose — that is the
    claim the page prints under the slider.
    """
    drawn = {
        step: render(charts["natal"], "medium", [step_clearance(step)], ("natal",)) for step in range(1, STEP_COUNT)
    }

    assert len(set(drawn.values())) == STEP_COUNT - 1


def test_the_marked_step_is_the_chart_the_library_ships(charts):
    """★ is the base every diff is taken from, so it must be an untouched render."""
    from kerykeion.charts.drawer import ChartDrawer

    shipped = ChartDrawer(charts["natal"]).generate_wheel_only_svg_string(style="modern", glyph_size="large")

    assert render(charts["natal"], "large", [step_clearance(0)]) == shipped


@pytest.mark.parametrize(
    ("chart", "size", "binds"),
    [("synastry", "small", False), ("natal", "medium", False), ("synastry", "large", False)],
)
def test_the_page_tells_the_truth_about_the_ceiling(charts, chart, size, binds):
    """A clipped request need not constrain the layout: compare real placements.

    The current fixtures have enough space with either ceiling, including the
    small synastry. This is geometry, not a property of a backend's name.
    """
    rings = ("natal",) if chart == "natal" else ("dual_outer", "dual_inner")
    air = [step_clearance(0)] * len(rings)
    _, shipped = render_with_layout(charts[chart], size, air)
    _, lifted = render_with_layout(charts[chart], size, air, rings)
    assert (shipped != lifted) is binds


@pytest.mark.parametrize(("angle", "binds"), [(0.0, False), (45.0, True)])
def test_synthetic_clusters_detect_an_active_ceiling(angle, binds):
    """The same real ink at the diagonal needs more arc; jammed points expose it.

    Use the unchanged production small-outer profile. No astronomical positions,
    measured spacing floors or ink metrics are adjusted to activate the cap.
    """
    profile = dm.GLYPH_SIZE_PROFILES["small"]["dual_outer"]
    point = SimpleNamespace(
        name="Sun",
        point_type="AstrologicalPoint",
        sign="Aqu",
        position=29.983,
        retrograde=True,
    )
    ink = dm._cluster_row_profile(point, **profile.scale_config())
    radii = {row: dm.CENTER - getattr(profile, row + "_y") for row in ("glyph", "degrees", "sign", "minutes", "rx")}

    def resolve(ceiling):
        """Resolve one fixture using the playground contract."""
        entries = [
            {"point": SimpleNamespace(name=f"P{i}"), "angle": angle + i * 0.01, "row_half_widths": ink}
            for i in range(2)
        ]
        return dm._resolve_planet_collisions(entries, min_separation=ceiling, row_radii=radii)

    shipped = resolve(profile.min_separation)
    lifted = resolve(playground.UNBOUND_CEILING)
    assert (display_layout(shipped) != display_layout(lifted)) is binds
    if binds:
        shipped_gap = (shipped[1]["display_angle"] - shipped[0]["display_angle"]) % 360.0
        lifted_gap = (lifted[1]["display_angle"] - lifted[0]["display_angle"]) % 360.0
        assert shipped_gap == pytest.approx(profile.min_separation)
        assert lifted_gap > profile.min_separation


@pytest.mark.parametrize(("first", "second"), [(0.0, 360.0), (12.00000001, 12.00000002)])
def test_display_layout_uses_rendered_precision_and_circular_equivalence(first, second):
    """Verify display layout uses rendered precision and circular equivalence."""
    point = SimpleNamespace(name="Sun")
    assert display_layout([{"point": point, "display_angle": first}]) == display_layout(
        [{"point": point, "display_angle": second}]
    )


def test_captured_layout_matches_actual_svg_rotations(charts):
    """Verify captured layout matches actual svg rotations."""
    svg, layouts = render_with_layout(charts["natal"], "medium", [step_clearance(0)])
    kr = "{https://www.kerykeion.net/}"
    actual = []
    for element in ElementTree.fromstring(svg).iter():
        if element.get(kr + "node") == "ChartPoint":
            rotation = re.match(r"rotate\(([-+0-9.]+)\s", element.attrib["transform"])
            assert rotation is not None
            actual.append((element.attrib[kr + "slug"], -float(rotation.group(1)) % 360.0))
    assert actual, "the render must contain real point placements"
    assert layouts == (tuple(sorted(actual)),)


@pytest.mark.parametrize("layout_moves", [False, True])
@pytest.mark.parametrize("svg_text_changes", [False, True])
def test_manifest_uses_geometry_not_svg_text(monkeypatch, layout_moves, svg_text_changes):
    """Both false textual positives and false textual negatives are refused."""
    monkeypatch.setattr(playground, "SIZES", ["small"])
    monkeypatch.setattr(playground, "STEP_COUNT", 1)
    monkeypatch.setattr(playground.AstrologicalSubjectFactory, "from_birth_data", lambda *args, **kwargs: object())
    monkeypatch.setattr(playground.ChartDataFactory, "create_natal_chart_data", lambda _: "natal")
    monkeypatch.setattr(playground.ChartDataFactory, "create_synastry_chart_data", lambda *_: "synastry")

    def render_fixture(chart, size, clearances, unbound=()):
        """Render a deterministic glyph-playground fixture."""
        shifted = bool(unbound) and chart == "synastry"
        svg = "<svg><!-- changed text --></svg>" if shifted and svg_text_changes else "<svg/>"
        angle = 20.0 if shifted and layout_moves else 10.0
        return svg, ((("Sun", angle),),)

    monkeypatch.setattr(playground, "render_with_layout", render_fixture)
    data = playground.build_data()
    assert data["manifest"]["ceilingBinds"]["small"] == {"natal": False, "synastry": layout_moves}


def test_the_shipped_page_is_whole():
    """The committed page parses, and holds every chart its UI can ask for.

    A truncated write or a stray ``</`` inside the payload would leave a page
    that opens to a blank stage — silently, since nothing else reads this file.
    """
    page = PAGE.read_text(encoding="utf-8")
    assert "__PLAYGROUND_DATA__" not in page, "the data placeholder was never filled"

    payload = re.search(r"const DATA = JSON\.parse\((\".*?\")\);", page, re.DOTALL)
    assert payload, "the page carries no data blob"
    data = json.loads(json.loads(payload.group(1)))

    expected_bases = {f"{chart}__{size}" for chart in ("natal", "synastry") for size in data["manifest"]["sizes"]}
    assert set(data["bases"]) == expected_bases

    expected_diffs = {f"natal__{size}__c{step}" for size in data["manifest"]["sizes"] for step in range(1, STEP_COUNT)}
    expected_diffs |= {
        f"synastry__{size}__o{outer}_i{inner}"
        for size in data["manifest"]["sizes"]
        for outer in range(STEP_COUNT)
        for inner in range(STEP_COUNT)
        if (outer, inner) != (0, 0)
    }
    assert set(data["diffs"]) == expected_diffs

    # The page reads these back to label its own controls.
    assert data["manifest"]["shippedClearance"] == pytest.approx(step_clearance(0))
    assert set(data["manifest"]["ceilingBinds"]) == set(data["manifest"]["sizes"])
    assert data["manifest"]["ceilingBinds"]["small"]["synastry"] is False


def test_the_page_asks_for_nothing_from_the_network():
    """Self-contained is the whole point: it has to open from a file:// path."""
    assert not re.search(r"(src|href)\s*=\s*[\"'](?!#)(https?:)?//", PAGE_TEMPLATE)
    assert "fetch(" not in PAGE_TEMPLATE
    assert "XMLHttpRequest" not in PAGE_TEMPLATE
