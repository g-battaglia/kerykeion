# -*- coding: utf-8 -*-
"""A stored baseline that no test reads is a picture, not a guard.

346 SVG files sit under tests/data/svg. Eighteen of them were generated, committed
and compared by nothing at all — the charts demonstrating the optional marks, and
three plain natal charts that had no generator either. A baseline nobody reads
records the library as it was the day it was written and says nothing when that
changes, which is how 73 files came to be drawing a glyph the library no longer
had and 51 went stale on a panel row.

This is the gate. It does not run the suite: it asks, statically, whether each file
is named by something. A name can be a literal in a test, or a name the parametrized
matrix builds from its own subject lists. Anything else has to be listed below with
a reason, and a second test refuses a reason that has stopped being true.
"""

import re
from pathlib import Path

from tests.data.test_subjects_matrix import GEOGRAPHIC_SUBJECTS, TEMPORAL_SUBJECTS

SVG_DIR = Path(__file__).parent.parent / "data" / "svg"
TESTS_ROOT = Path(__file__).parent.parent

#: Baselines with no reader, and why. Empty, and meant to stay that way: the
#: eighteen that were here are read by tests/core/test_optional_mark_baselines.py.
#: A new entry is a debt, not a category — write the reason as a sentence someone
#: can act on, or write the test instead.
BASELINES_WITH_NO_READER: dict[str, str] = {}


def _names_written_as_literals() -> set[str]:
    """Every "....svg" that appears verbatim in a test source."""
    found: set[str] = set()
    for source in TESTS_ROOT.rglob("*.py"):
        text = source.read_text(encoding="utf-8")
        found |= set(re.findall(r'"([^"\n]+\.svg)"', text))
        found |= set(re.findall(r"'([^'\n]+\.svg)'", text))
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
    driver like any other.
    """
    from tests.conftest import _detect_ephemeris_tier

    available = _TIER_ORDER.get(_detect_ephemeris_tier(), 0)
    out_of_reach = {
        subject["name"]
        for subject in (*TEMPORAL_SUBJECTS, *GEOGRAPHIC_SUBJECTS)
        if _TIER_ORDER.get(subject.get("tier", "base"), 0) > available
    }
    return {
        path.name
        for path in SVG_DIR.glob("*.svg")
        for name in out_of_reach
        if path.name.startswith(name + " -") or path.name.startswith(name + " and ")
    }


def _parameter_sets(function):
    """The argument tuples a @pytest.mark.parametrize'd test would be called with.

    Only what this gate needs: one or more parametrize marks, positional argnames,
    plain iterables of values. A test using anything richer falls out of the driver
    and its baselines have to be named some other way, which the assertion says.
    """
    marks = [
        mark
        for mark in getattr(function, "pytestmark", ())
        if mark.name == "parametrize"
    ]
    if not marks:
        return [()], []
    sets = [()]
    names: list[str] = []
    for mark in reversed(marks):
        argnames, argvalues = mark.args[0], mark.args[1]
        keys = [key.strip() for key in argnames.split(",")] if isinstance(argnames, str) else list(argnames)
        names.extend(keys)
        expanded = []
        for existing in sets:
            for value in argvalues:
                row = tuple(value) if len(keys) > 1 else (value,)
                expanded.append(existing + row)
        sets = expanded
    return sets, names


def _names_the_golden_tests_ask_for() -> set[str]:
    """The baselines the golden tests actually reach for, by running them.

    Most golden tests build their filename in an f-string from a loop variable or a
    parametrized case — a theme, a language, a house system, a sidereal mode — so
    reading the sources for literals finds barely half of them. The reliable
    question is which files the comparison is handed, so ask it: drive the golden
    tests with the comparison replaced by a recorder.

    Failures are irrelevant here. A test that fails still names the baseline it
    wanted, and its own test is what reports the failure.
    """
    import importlib
    import inspect

    import tests.data.compare_svg_lines as comparison

    asked: set[str] = set()

    def recording(baseline_path, generated_svg, **kwargs):
        asked.add(Path(baseline_path).name)

    modules = [
        importlib.import_module(name)
        for name in (
            "tests.core.test_chart_drawer",
            "tests.core.test_optional_mark_baselines",
            "tests.core.test_chart_parametrized",
            "tests.core.test_bce_dates",
        )
    ]
    original = comparison.compare_svg_file
    comparison.compare_svg_file = recording
    patched = [module for module in modules if hasattr(module, "compare_svg_file")]
    for module in patched:
        module.compare_svg_file = recording
    drawer = modules[0]
    cached_subjects = dict(drawer._subject_cache)

    def drive(function, instance):
        offset = 1 if instance is not None else 0
        parameter_sets, names = _parameter_sets(function)
        if len(inspect.signature(function).parameters) - offset != len(names):
            return  # takes fixtures this driver cannot supply
        for arguments in parameter_sets:
            try:
                function(instance, *arguments) if instance is not None else function(*arguments)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException:
                # BaseException, not Exception: a driven test that calls pytest.skip
                # — the deep-historical charts do, on a kernel that cannot reach the
                # date — raises Skipped, which is not an Exception and would end this
                # gate as skipped instead of letting it record the other 300 names.
                pass

    try:
        for module in modules:
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if inspect.isclass(attribute) and attribute_name.startswith("Test"):
                    for name in dir(attribute):
                        if name.startswith("test_"):
                            drive(getattr(attribute, name), attribute())
                elif inspect.isfunction(attribute) and attribute_name.startswith("test_"):
                    drive(attribute, None)
    finally:
        comparison.compare_svg_file = original
        for module in patched:
            module.compare_svg_file = original
        drawer._subject_cache.clear()
        drawer._subject_cache.update(cached_subjects)
    return asked


def _baselines_with_a_reader() -> set[str]:
    return (
        _names_written_as_literals()
        | _names_gated_by_ephemeris_tier()
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
