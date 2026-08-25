# -*- coding: utf-8 -*-
"""A stored baseline that no test reads is a picture, not a guard.

346 SVG files sit under tests/data/svg. Twenty of them were generated, committed
and compared by nothing at all — seventeen charts demonstrating the optional
marks, and three plain natal charts that had no generator either. A baseline nobody reads
records the library as it was the day it was written and says nothing when that
changes, which is how 73 files came to be drawing a glyph the library no longer
had and 51 went stale on a panel row.

This is the gate. It asks, for each file, whether a test hands it to the
comparison. Most of the answer comes from running the golden tests with the
comparison replaced by a recorder (tests/data/golden_drive.py); the rest from the
source lines that name a baseline where they read or compare it — a literal in a
docstring, or a key in another gate's exemption table, does not count, because a
file that is only *mentioned* has no reader either. Anything else has to be listed
below with a reason, and a second test refuses a reason that has stopped being true.
"""

import ast
import functools
import tokenize
from pathlib import Path

from tests.data.golden_drive import GOLDEN_TEST_MODULES, drive_every_golden_test
from tests.data.test_subjects_matrix import GEOGRAPHIC_SUBJECTS, TEMPORAL_SUBJECTS

SVG_DIR = Path(__file__).parent.parent / "data" / "svg"
TESTS_ROOT = Path(__file__).parent.parent

#: Baselines with no reader, and why. Empty, and meant to stay that way: the
#: twenty that were here are read by tests/core/test_optional_mark_baselines.py.
#: A new entry is a debt, not a category — write the reason as a sentence someone
#: can act on, or write the test instead.
BASELINES_WITH_NO_READER: dict[str, str] = {}

#: A source line counts as reading a baseline only if it hands the name to a
#: comparison or builds a path to the file — judged on the line's NAME tokens, so
#: a commented-out call or a docstring that mentions SVG_DIR cannot vote. The first
#: version of this scan took any quoted "….svg" anywhere under tests/, so the four
#: progression baselines were "read" by being keys in test_baseline_freshness.py's
#: cannot-regenerate table, and deleting their actual tests left the gate green.
_NAMES_THAT_READ = {"SVG_DIR", "read_text", "open"}

#: Baselines read by a test the driver can only run on the full-range kernel — a
#: test marked for a higher tier whose subject is not in the matrix, so the tier
#: gate below cannot see it. Counted as read on a lower tier; on the extended
#: kernel each of these MUST be recorded by the driver, and the second test says so.
READ_ONLY_ON_THE_EXTENDED_KERNEL: dict[str, str] = {
    "Historical Subject - Natal Chart - Classic.svg": (
        "test_chart_drawer.py::TestChartOptions::test_historical_date is @extended: a 1500 "
        "chart cannot be cast on the medium kernel"
    ),
}


def _reads(name: str) -> bool:
    return name in _NAMES_THAT_READ or name.startswith("compare_")


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
                if token.type == tokenize.NAME and _reads(token.string):
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


#: base < medium < extended. A subject dated outside the loaded kernel's range
#: cannot be cast at all, so the test that reads its baseline skips before it ever
#: names the file — which is not the same as the file having no reader.
_TIER_ORDER = {"base": 0, "medium": 1, "extended": 2}


def _names_gated_by_ephemeris_tier() -> set[str]:
    """Baselines whose subject this run's ephemeris cannot reach.

    Declared, not guessed: every matrix subject carries the tier it needs, and the
    detected tier is what tests/conftest.py already probes for. On an extended
    kernel this set is empty and every one of these files must be recorded by the
    driver like any other — which is why `poe check` runs this gate a second time
    as `test:gates:extended`: on the default tier a lost reader for one of these
    files is invisible here, by construction.
    """
    from tests.conftest import _detect_ephemeris_tier

    available = _TIER_ORDER.get(_detect_ephemeris_tier(), 0)
    declared = set(READ_ONLY_ON_THE_EXTENDED_KERNEL) if available < _TIER_ORDER["extended"] else set()
    out_of_reach = {
        subject["name"]
        for subject in (*TEMPORAL_SUBJECTS, *GEOGRAPHIC_SUBJECTS)
        if _TIER_ORDER.get(subject.get("tier", "base"), 0) > available
    }
    return declared | {
        path.name
        for path in SVG_DIR.glob("*.svg")
        for name in out_of_reach
        if path.name.startswith(name + " -") or path.name.startswith(name + " and ")
    }


def _names_out_of_the_backends_reach() -> set[str]:
    """Baselines whose chart this run's ephemeris backend cannot compute at all.

    The full point set needs per-body asteroid files that the swisseph setup cannot
    download; tests/conftest.py already probes for that and skips the all-points
    tests when the probe fails. The same probe, the same files.
    """
    from tests.conftest import _tnos_available

    if _tnos_available():
        return set()
    return {path.name for path in SVG_DIR.glob("*.svg") if "All Active Points" in path.name}


def _names_this_run_cannot_reach() -> set[str]:
    """Out of reach by kernel tier or by backend: not the same as having no reader."""
    return _names_gated_by_ephemeris_tier() | _names_out_of_the_backends_reach()


@functools.lru_cache(maxsize=1)
def _names_the_golden_tests_ask_for() -> frozenset[str]:
    """The baselines the golden tests actually reach for, by running them.

    Failures are irrelevant here. A test that fails still names the baseline it
    wanted, and its own test is what reports the failure; a test that fails before
    it gets there names nothing, and its baseline shows up below as unread — which
    is the truth.
    """
    asked: set[str] = set()

    def recording(baseline_path, _generated_svg, **_kwargs):
        asked.add(Path(baseline_path).name)

    drive_every_golden_test(recording)
    return frozenset(asked)


@functools.lru_cache(maxsize=1)
def _baselines_with_a_reader() -> frozenset[str]:
    # Cached: driving the golden suite costs seconds, and both tests below ask.
    return frozenset(
        _names_read_on_a_source_line()
        | _names_this_run_cannot_reach()
        | _names_the_golden_tests_ask_for()
    )


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
    from tests.conftest import _detect_ephemeris_tier

    if _TIER_ORDER.get(_detect_ephemeris_tier(), 0) >= _TIER_ORDER["extended"]:
        unseen = sorted(set(READ_ONLY_ON_THE_EXTENDED_KERNEL) - _names_the_golden_tests_ask_for())
        assert unseen == [], f"Declared as read on the extended kernel, but no driven test reads them: {unseen}"
    gone_too = sorted(name for name in READ_ONLY_ON_THE_EXTENDED_KERNEL if name not in stored)
    assert gone_too == [], f"Declared as read on the extended kernel but no longer stored: {gone_too}"
