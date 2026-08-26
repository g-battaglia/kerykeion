"""
Tests for the glyph playground page and the diffs it ships.

The page in ``scripts/glyph_playground.html`` claims something specific: that
the 264 charts it stores as diffs are the charts kerykeion actually draws, not
approximations of them. That claim rests entirely on the diff format round
tripping, so that is what is pinned here — on real renders, not on fixtures of
renders.

What is not pinned here: the JavaScript reassembly (same algorithm, checked in
a browser when the page is built) and the committed HTML being in step with the
current profiles. The page is a tuning instrument, not a golden: it is rebuilt
with ``poe playground`` when the eye needs it, and a stale one is a stale
picture, not a broken promise.

See: scripts/generate_glyph_playground.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.generate_glyph_playground import (
    PAGE_TEMPLATE,
    STEP_COUNT,
    apply_diff,
    compact_diff,
    lines_of,
    render,
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
    [("synastry", "small", True), ("natal", "medium", False), ("synastry", "large", False)],
)
def test_the_page_tells_the_truth_about_the_ceiling(charts, chart, size, binds):
    """Lifting ``min_separation`` has to matter exactly where the page says it does.

    Above ★ every notch renders with the ceiling out of reach, so that the
    clearance is what decides instead of the cap. On the small synastry the
    shipped ceiling genuinely binds and the page prints a warning; elsewhere the
    two draw the same chart and it says so. Either claim going stale — a profile
    re-measured, the lift quietly dropped — is a lie printed under a slider.
    """
    rings = ("natal",) if chart == "natal" else ("dual_outer", "dual_inner")
    air = [step_clearance(0)] * len(rings)

    shipped = render(charts[chart], size, air)
    lifted = render(charts[chart], size, air, rings)

    assert (shipped != lifted) is binds


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


def test_the_page_asks_for_nothing_from_the_network():
    """Self-contained is the whole point: it has to open from a file:// path."""
    assert not re.search(r"(src|href)\s*=\s*[\"'](?!#)(https?:)?//", PAGE_TEMPLATE)
    assert "fetch(" not in PAGE_TEMPLATE
    assert "XMLHttpRequest" not in PAGE_TEMPLATE
