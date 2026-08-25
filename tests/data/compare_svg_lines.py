# -*- coding: utf-8 -*-
"""The one comparison between a generated chart and its stored baseline.

There were four of these. This one asserted; the copy in test_chart_drawer.py
`return`ed without asserting whenever a line's number COUNT or non-numeric
skeleton differed, abandoned the whole file when the line count changed in favour
of a +-5% length ratio, skipped when the baseline was missing, and compared what
was left at `rel_tol=0.5` — fifty per cent, so +-150 units on a coordinate of 300.
Two more copies loosened it again or had no callers at all.

What that cost is on the record: 51 baselines went stale on the diurnality row, 73
were drawn with a glyph set the library no longer had, and the relationship-score
baseline showed a score the code had stopped rendering. None of it was numeric
drift. Every one was structural, and structural difference was the exact thing the
comparator returned early on.

So: structure is fatal, always and on every backend. Line count, count of numbers
in a line, and the line with its numbers blanked out must all match, or the test
fails and names the line. Numbers are then compared with NO relative component and
a tolerance of a ten-thousandth, which absorbs a 0.36-arcsecond flip on a DMS
label and the last digit of a coordinate printed at six decimal places, and
nothing else.

Numbers are compared only on the backend the baselines were generated with. That
is not a loophole, it is the fact that the two backends compute different charts:
measured across this file's 369 golden tests, structural strictness costs 6
baselines on swisseph and 5 on libephemeris, but numeric strictness costs 155 on
swisseph against 5 on libephemeris — return moments solved differently, bodies one
backend does not carry. A single tolerance wide enough to cover that is the 0.5
this module exists to retire. On a foreign backend the structural assertions still
run, in full, and then the test reports SKIPPED with the reason: not compared is
not the same as compared and equal, and the suite says which one happened.
"""

import os
import re
from pathlib import Path

import pytest

#: The backend the stored baselines were generated with. Numeric comparison runs
#: only here; see the module docstring for the measurement behind that.
BASELINE_BACKEND = "libephemeris"

#: No relative component: a 50% allowance on a coordinate of 300 is 150 units, and
#: that is how a chart can be redrawn into a different chart and still pass.
DEFAULT_REL_TOL = 0.0
#: A ten-thousandth of a unit, or of a degree on a DMS label — 0.36 arcseconds.
#: Coordinates are printed at :.6f, so this is a hundred times the last digit.
DEFAULT_ABS_TOL = 1e-4

# Seconds mark: &quot; (current output), a literal ", or the pre-fix apostrophe
# (older baselines were generated while the quote-replace pass corrupted it).
_DMS_PATTERN = re.compile(r"(\d+)°(\d+)'(\d+)(?:&quot;|\"|')")
_NON_VISUAL_KR_ATTR_PATTERN = re.compile(r"\s+kr:c[xy]=(['\"])[^'\"]*\1")
_NUMBER_PATTERN = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
# A hex colour is not a number, but `#000e10` reads as `000e10` — zero times ten
# to the tenth — and `#1e9999` as an infinity that fails against itself. Each
# hex digit is rewritten as a letter before the numbers are read, so a colour is
# compared as text, exactly, and never as a value.
_HEX_COLOUR_PATTERN = re.compile(r"#([0-9a-fA-F]{3,8})\b")
_HEX_DIGIT_AS_LETTER = str.maketrans("0123456789", "ghijklmnop")


def _dms_to_decimal(match: re.Match) -> str:
    """Convert a DMS string like 23°33'39' to its decimal-degree equivalent."""
    d, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
    return f"{d + m / 60 + s / 3600:.6f}"


def _strip_non_visual_metadata_attrs(svg_line: str) -> str:
    """Remove metadata-only attributes that do not affect rendered SVG geometry."""
    return _NON_VISUAL_KR_ATTR_PATTERN.sub("", svg_line)


def _hex_colours_as_letters(svg_line: str) -> str:
    """Rewrite every ``#rrggbb`` so that no digit in it can be read as a number."""
    return _HEX_COLOUR_PATTERN.sub(lambda m: "#" + m.group(1).translate(_HEX_DIGIT_AS_LETTER), svg_line)


def active_backend() -> str:
    """Which ephemeris is actually computing, resolved the way the library does."""
    from kerykeion.ephemeris_backend.backend import BACKEND_NAME

    return BACKEND_NAME


def numbers_are_comparable() -> bool:
    """Is the active backend the one the baselines were generated with?"""
    return active_backend() == BASELINE_BACKEND


def _excerpt(line: str, limit: int = 170) -> str:
    return line if len(line) <= limit else line[:limit] + "…"


def compare_svg_lines(
    expected_line: str,
    actual_line: str,
    rel_tol: float = DEFAULT_REL_TOL,
    abs_tol: float = DEFAULT_ABS_TOL,
    *,
    compare_numbers: bool = True,
    where: str = "",
) -> None:
    """Assert two SVG lines are the same line.

    DMS values (e.g. 23°33'39') are collapsed into single decimal numbers before
    comparison so that an arcsecond difference is not read as an integer diff of 1.

    Args:
        expected_line: The stored baseline's line.
        actual_line: The freshly generated line.
        rel_tol: Relative tolerance. Zero by default, deliberately.
        abs_tol: Absolute tolerance, in whatever unit the number is in.
        compare_numbers: False on a backend that did not produce the baselines;
            the structural assertions still run.
        where: File name, for the failure message.
    """
    location = f" in {where}" if where else ""
    expected_line = _hex_colours_as_letters(_strip_non_visual_metadata_attrs(expected_line))
    actual_line = _hex_colours_as_letters(_strip_non_visual_metadata_attrs(actual_line))

    expected_processed = _DMS_PATTERN.sub(_dms_to_decimal, expected_line)
    actual_processed = _DMS_PATTERN.sub(_dms_to_decimal, actual_line)

    expected_numbers = [float(x) for x in re.findall(_NUMBER_PATTERN, expected_processed)]
    actual_numbers = [float(x) for x in re.findall(_NUMBER_PATTERN, actual_processed)]

    assert len(expected_numbers) == len(actual_numbers), (
        f"A line carries a different count of numbers{location} — an attribute or a "
        f"whole element came or went, which is a change to the chart and not to its "
        f"precision.\n  baseline: {_excerpt(expected_line)}\n  generated: {_excerpt(actual_line)}"
    )

    expected_text = re.sub(_NUMBER_PATTERN, "NUM", expected_processed)
    actual_text = re.sub(_NUMBER_PATTERN, "NUM", actual_processed)
    assert expected_text == actual_text, (
        f"A line differs where it has no numbers{location} — a different label, class, "
        f"node or attribute name. Regenerate with `uv run poe regenerate:svg` if the "
        f"change is intended.\n  baseline: {_excerpt(expected_line)}\n  generated: {_excerpt(actual_line)}"
    )

    if not compare_numbers:
        return

    for index, (baseline, generated) in enumerate(zip(expected_numbers, actual_numbers)):
        assert abs(generated - baseline) <= max(rel_tol * abs(baseline), abs_tol), (
            f"Number {index} moved{location}: {baseline} -> {generated} "
            f"(allowed {max(rel_tol * abs(baseline), abs_tol)})\n"
            f"  baseline: {_excerpt(expected_line)}\n  generated: {_excerpt(actual_line)}"
        )


def compare_svg_file(
    baseline_path: Path,
    generated_svg: str,
    *,
    rel_tol: float = DEFAULT_REL_TOL,
    abs_tol: float = DEFAULT_ABS_TOL,
) -> None:
    """Assert a generated chart is the chart stored at ``baseline_path``.

    A missing baseline FAILS. It used to skip, so a renamed or never-generated
    file left a test reporting green while comparing nothing.

    On a backend that did not produce the baselines the structural assertions run
    and the test is then reported as skipped, naming the backend: the numeric half
    genuinely did not run and the summary should say so rather than counting it as
    a pass.
    """
    baseline_path = Path(baseline_path)
    name = baseline_path.name

    if os.environ.get("KERYKEION_REGEN_BASELINES"):
        from tests.data.regeneration_guard import require_library_from_this_checkout

        # The same two refusals as the scripts: the library must be this checkout's,
        # and the backend the one the baselines are declared to come from.
        require_library_from_this_checkout(__file__)
        assert numbers_are_comparable(), (
            f"Refusing to rewrite {name}: the baselines are {BASELINE_BACKEND} charts and "
            f"this run is on {active_backend()}. A baseline written by the other backend "
            f"would fail every run on the one it claims to come from."
        )
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(generated_svg, encoding="utf-8")
        return

    assert baseline_path.exists(), (
        f"No baseline at {baseline_path}. A golden test with no baseline compares "
        f"nothing; generate it with `uv run poe regenerate:svg`."
    )

    baseline_lines = baseline_path.read_text(encoding="utf-8").splitlines()
    generated_lines = generated_svg.splitlines()

    assert len(baseline_lines) == len(generated_lines), (
        f"{name} is {len(generated_lines)} lines and its baseline is "
        f"{len(baseline_lines)}: elements were added or removed. Read the diff and "
        f"regenerate with `uv run poe regenerate:svg` if the change is intended."
    )

    compare_numbers = numbers_are_comparable()
    for baseline_line, generated_line in zip(baseline_lines, generated_lines):
        compare_svg_lines(
            baseline_line,
            generated_line,
            rel_tol=rel_tol,
            abs_tol=abs_tol,
            compare_numbers=compare_numbers,
            where=name,
        )

    if not compare_numbers:
        pytest.skip(
            f"Structure compared; numbers not. The baselines were generated with "
            f"{BASELINE_BACKEND} and this run is on {active_backend()}, which computes "
            f"different charts — not less precise ones."
        )
