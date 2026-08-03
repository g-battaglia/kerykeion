"""Every committed SVG baseline with an info panel must carry every row of it.

A row added to `chart.xml` reaches the baselines only if something regenerates
them, and this repo has several regenerators covering overlapping sets. When the
diurnality row landed, fifty-one committed baselines were left behind — eleven of
them the README's own showcase images, which GitHub serves by raw URL, so the
documentation was advertising a panel the library no longer draws, and thirty-two
of them the v6 gallery, whose regenerator is wired into no poe task.

Nothing caught it. The parametrised chart comparison covers most of the tree but
not these; the BCE charts are compared by a line-count assertion with a ±5%
tolerance, which one added line cannot trip; and the three fixtures still exempt
below have no regenerator and no comparison at all.

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
BASELINE_DIRS = [
    REPO_ROOT / "tests" / "data" / "svg",
    REPO_ROOT / "docs" / "charts",
    REPO_ROOT / "tests" / "data" / "v6_gallery",
]

#: How many bottom-left rows `chart.xml` emits, read from the template rather
#: than written down. A hardcoded count catches the change that already happened
#: and is blind to the next one, which is the failure this whole file exists to
#: stop. A chart that has any of the rows has all of them: the template writes
#: the block unconditionally, and a renderer that leaves a slot empty still emits
#: the node with empty text.
PANEL_ROWS = len(
    re.findall(
        r"Bottom_Left_Text_\d+",
        (REPO_ROOT / "kerykeion" / "charts" / "templates" / "chart.xml").read_text(encoding="utf-8"),
    )
)

#: Baselines this repository cannot reproduce, with the reason.
#:
#: An earlier version of this list held five files and blamed the DE441 kernel.
#: That was wrong and a reviewer caught it: ``poe regenerate:svg`` already sets
#: ``LIBEPHEMERIS_PRECISION=extended``, and under that tier this machine computes
#: pre-1-CE subjects and draws them with all six rows. Two of the five were
#: regenerated that way. A wrong exemption is worse than no exemption, because it
#: reads as verified and permanently silences the only guard that would flag the
#: file.
#:
#: These three are exempt for a different reason: no script in the repository
#: produces them, and their second subject is not recoverable from it — the
#: synastry is cast against a subject named "Transit Partner" that appears in no
#: source file, and the transit against 1970-01-01. Regenerating them means
#: deciding what they are supposed to represent, which is a change to the
#: fixtures rather than a refresh of them.
CANNOT_REGENERATE_HERE = {
    "Ancient Greece 500BC - Progression Chart.svg": "no generator in the repo; progressed target not recorded",
    "Ancient Greece 500BC - Synastry Chart.svg": "no generator in the repo; second subject not recorded",
    "Ancient Greece 500BC - Transit Chart.svg": "no generator in the repo; transit moment not recorded",
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
        f"`python scripts/regenerate_docs_charts.py` for docs/charts, "
        f"`python scripts/generate_v6_test_gallery.py` for tests/data/v6_gallery."
    )


def test_the_exemption_list_does_not_outlive_its_reason():
    """An exemption for a file that no longer exists is a lie left in the source."""
    names = {svg.name for directory in BASELINE_DIRS for svg in directory.glob("*.svg")}
    stale_entries = set(CANNOT_REGENERATE_HERE) - names
    assert not stale_entries, f"exempted files that no longer exist: {sorted(stale_entries)}"
