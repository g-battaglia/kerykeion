# -*- coding: utf-8 -*-
"""A stored baseline that no test reads is a picture, not a guard.

346 SVG files sit under tests/data/svg. Twenty of them were generated, committed
and compared by nothing at all — seventeen charts demonstrating the optional
marks, and three plain natal charts that had no generator either. A baseline
nobody reads records the library as it was the day it was written and says
nothing when that changes, which is how 73 files came to be drawing a glyph the
library no longer had and 51 went stale on a panel row.

This is the gate. It asks, for each file, whether a test hands it to the
comparison. Inside the golden modules the only witness is the driver
(tests/data/golden_drive.py), which runs every golden test with the comparison
replaced by a recorder; elsewhere, a source line that hands the name to a
comparison or opens the file counts — a literal in a docstring, a comment, or a
key in another gate's exemption table does not, because a file that is only
*mentioned* has no reader either. Anything else has to be listed below with a
reason, and a second test refuses a reason that has stopped being true.
"""

import ast
import os
import tokenize
from pathlib import Path

from tests.data.golden_drive import (
    BASELINES_READ_ONLY_BY_EXTENDED_TIER_TESTS,
    GOLDEN_TEST_MODULES,
    SVG_DIR,
    TIER_ORDER,
    baselines_out_of_this_runs_reach,
    baselines_the_golden_tests_compare,
)

TESTS_ROOT = Path(__file__).parent.parent

#: Baselines with no reader, and why. Empty, and meant to stay that way: the
#: twenty that were here are read by tests/core/test_optional_mark_baselines.py.
#: A new entry is a debt, not a category — write the reason as a sentence someone
#: can act on, or write the test instead.
BASELINES_WITH_NO_READER: dict[str, str] = {}

#: A source line counts as reading a baseline only if it hands the name to a
#: comparison or builds a path to the file — judged on the line's NAME tokens, so
#: a commented-out call or a docstring that mentions SVG_DIR cannot vote.
_READER_TOKENS = {"SVG_DIR", "read_text", "open"}


def _is_a_reader_token(name: str) -> bool:
    return name in _READER_TOKENS or name.startswith("compare_")


def _is_a_driven_module(source: Path) -> bool:
    relative = source.relative_to(TESTS_ROOT.parent).with_suffix("")
    return ".".join(relative.parts) in GOLDEN_TEST_MODULES


def _names_read_on_a_source_line() -> set[str]:
    """Every "....svg" literal on a line whose code compares it or opens it.

    Outside the driven modules only: there the driver is the source of truth, and a
    literal on a compare line inside a test whose body no longer runs the comparison
    would otherwise still count — emptying a reader left the gate green that way.
    """
    found: set[str] = set()
    for source in TESTS_ROOT.rglob("*.py"):
        if _is_a_driven_module(source):
            continue
        readers_on_line: set[int] = set()
        literals: list[tuple[int, str]] = []
        with tokenize.open(source) as handle:
            for token in tokenize.generate_tokens(handle.readline):
                if token.type == tokenize.NAME and _is_a_reader_token(token.string):
                    readers_on_line.add(token.start[0])
                elif token.type == tokenize.STRING:
                    try:
                        value = ast.literal_eval(token.string)
                    except (ValueError, SyntaxError):
                        continue  # a prefix this reader does not evaluate
                    if isinstance(value, str) and value.endswith(".svg"):
                        literals.append((token.start[0], value))
        found |= {name for line, name in literals if line in readers_on_line}
    return {Path(name).name for name in found}


def _baselines_with_a_reader() -> set[str]:
    return (
        _names_read_on_a_source_line()
        | baselines_out_of_this_runs_reach()
        | set(baselines_the_golden_tests_compare())
    )


def _detected_tier() -> int:
    from tests.conftest import _detect_ephemeris_tier

    return TIER_ORDER.get(_detect_ephemeris_tier(), 0)


def test_every_baseline_is_read_by_something():
    stored = {path.name for path in SVG_DIR.glob("*.svg")}
    unread = sorted(stored - _baselines_with_a_reader() - set(BASELINES_WITH_NO_READER))
    assert unread == [], (
        "These baselines are stored but no test reads them, so nothing notices when "
        "the chart they show stops being the chart the library draws:\n  "
        + "\n  ".join(unread)
    )


def test_the_no_reader_list_does_not_outlive_its_reason():
    """An exemption for a file that now has a reader, or no longer exists, is noise."""
    stored = {path.name for path in SVG_DIR.glob("*.svg")}
    with_reader = _baselines_with_a_reader()

    gone = sorted(name for name in BASELINES_WITH_NO_READER if name not in stored)
    assert gone == [], f"Listed as unread but no longer stored: {gone}"

    now_read = sorted(name for name in BASELINES_WITH_NO_READER if name in with_reader)
    assert now_read == [], f"Listed as unread but a test reads them now: {now_read}"

    # The extended-only readers are taken on trust below that tier; on it, the
    # driver must actually see them, or the trust was misplaced.
    gone_too = sorted(name for name in BASELINES_READ_ONLY_BY_EXTENDED_TIER_TESTS if name not in stored)
    assert gone_too == [], f"Declared as read on the extended kernel but no longer stored: {gone_too}"
    if _detected_tier() >= TIER_ORDER["extended"]:
        unseen = sorted(set(BASELINES_READ_ONLY_BY_EXTENDED_TIER_TESTS) - baselines_the_golden_tests_compare())
        assert unseen == [], f"Declared as read on the extended kernel, but no driven test reads them: {unseen}"


def test_a_run_that_asks_for_the_extended_kernel_gets_it():
    """`poe check` runs these gates a second time under LIBEPHEMERIS_PRECISION=extended,
    where the tier exemptions are empty. libephemeris quietly routes to a narrower
    kernel when the requested one is not installed, and a run that asked for extended
    and got medium would pass the same tests with the same exemptions and prove
    nothing. Install the kernel, or do not claim the tier."""
    asked_for = os.environ.get("LIBEPHEMERIS_PRECISION", "").lower()
    if asked_for != "extended":
        return
    from tests.conftest import _detect_ephemeris_tier

    assert _detect_ephemeris_tier() == "extended", (
        f"LIBEPHEMERIS_PRECISION=extended was asked for and the detected tier is "
        f"{_detect_ephemeris_tier()!r}: the full-range kernel is not installed, so the "
        f"extended run of these gates would exempt what it claims to check."
    )
