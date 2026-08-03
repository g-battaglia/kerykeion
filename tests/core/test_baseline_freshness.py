"""Every committed SVG baseline with an info panel must carry every row of it.

A row added to `chart.xml` reaches the baselines only if something regenerates
them, and this repo has several regenerators covering overlapping sets. When the
diurnality row landed, nineteen committed baselines were left behind — eleven of
them the README's own showcase images, which GitHub serves by raw URL, so the
documentation was advertising a panel the library no longer draws.

Nothing caught it. The parametrised chart comparison covers most of the tree but
not these; the BCE charts are compared by a line-count assertion with a ±5%
tolerance, which one added line cannot trip; and the three natal fixtures below
had no regenerator and no comparison at all.

So this test does not compare rendering — it asks a much cheaper question that
the tolerant comparators cannot: is the file structurally the shape the current
template produces? A stale baseline is not a wrong picture, it is a picture of
an older library, and it should be visible as soon as it happens rather than
whenever someone next looks.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
BASELINE_DIRS = [REPO_ROOT / "tests" / "data" / "svg", REPO_ROOT / "docs" / "charts"]

#: The bottom-left rows `chart.xml` emits. A chart that has any of them has all
#: of them: the template writes the whole block unconditionally, and a renderer
#: that leaves a slot empty still emits the node with empty text.
PANEL_ROWS = 6

#: Baselines that cannot be regenerated on an ordinary checkout, with the reason.
#: These five are cast before 1 CE and need the full DE441 kernel; the short-range
#: kernel most machines carry raises rather than computing them, which is why
#: ``poe regenerate:svg`` reports the ancient-Rome step as an expected failure.
#: Regenerate them on a machine with the extended tier and delete the entry.
CANNOT_REGENERATE_HERE = {
    "Ancient Greece 500BC - Progression Chart.svg": "pre-1 CE, needs the DE441 kernel",
    "Ancient Greece 500BC - Synastry Chart.svg": "pre-1 CE, needs the DE441 kernel",
    "Ancient Greece 500BC - Transit Chart.svg": "pre-1 CE, needs the DE441 kernel",
    "Ancient Greece 500BC and Ptolemaic Egypt 200BC - Synastry Chart.svg": "pre-1 CE, needs the DE441 kernel",
    "Ancient Greece 500BC and Ptolemaic Egypt 200BC - Transit Chart.svg": "pre-1 CE, needs the DE441 kernel",
}

_ROW = re.compile(r"Bottom_Left_Text_(\d+)")


def _baselines_with_a_panel() -> list[Path]:
    """Every committed baseline that draws the bottom-left block at all.

    Wheel-only and aspect-grid-only variants use templates without the block, so
    they are excluded by having no rows rather than by matching on their names —
    a filename convention would quietly stop excluding them if one were renamed.
    """
    found = []
    for directory in BASELINE_DIRS:
        for svg in sorted(directory.glob("*.svg")):
            if _ROW.search(svg.read_text(encoding="utf-8")):
                found.append(svg)
    return found


PANELLED = _baselines_with_a_panel()


def test_the_search_actually_finds_baselines():
    """Guards every case below: an empty list would make them all vacuous."""
    assert len(PANELLED) > 100, f"only {len(PANELLED)} panelled baselines found — did the layout move?"


@pytest.mark.parametrize("svg", PANELLED, ids=lambda p: p.name)
def test_every_panelled_baseline_has_every_row(svg: Path):
    if svg.name in CANNOT_REGENERATE_HERE:
        pytest.skip(f"{svg.name}: {CANNOT_REGENERATE_HERE[svg.name]}")

    rows = {int(match) for match in _ROW.findall(svg.read_text(encoding="utf-8"))}
    missing = set(range(PANEL_ROWS)) - rows
    assert not missing, (
        f"{svg.name} is missing bottom-left row(s) {sorted(missing)} — it predates a template change. "
        f"Regenerate it: `poe regenerate:svg` for tests/data/svg, "
        f"`python scripts/regenerate_docs_charts.py` for docs/charts."
    )


def test_the_exemption_list_does_not_outlive_its_reason():
    """An exemption for a file that no longer exists is a lie left in the source."""
    names = {svg.name for directory in BASELINE_DIRS for svg in directory.glob("*.svg")}
    stale_entries = set(CANNOT_REGENERATE_HERE) - names
    assert not stale_entries, f"exempted files that no longer exist: {sorted(stale_entries)}"
