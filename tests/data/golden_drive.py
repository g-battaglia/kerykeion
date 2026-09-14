# -*- coding: utf-8 -*-
"""Run every golden chart test with the comparison replaced.

Two gates need to know what the golden tests DO rather than what their sources
say: which baselines they hand to the comparison, and whether any of them reaches
for the network on the way. Most golden tests build their filename in an f-string
from a loop variable or a parametrized case — a theme, a language, a house system
— so reading the sources for literals finds barely half of them, and a static
reading cannot see a network call at all. The reliable question is what happens
when the test runs, so run it, with the comparison swapped for whatever the gate
wants to observe.

Parametrized tests are expanded from their own marks and driven once per case; a
class with ``setup_class`` gets it called first, as pytest would — and if that
setup fails, its tests are still looked at for whether the driver could call
them, because that answer depends on their signatures and not on the kernel that
could not cast the class's subject. A driven test
that fails, or skips, is that test's business: the gate is told, if it asked, and
carries on to the next one. ``Skipped`` is a ``BaseException``, not an
``Exception``, and a gate that let it through would end as skipped itself at the
first deep-historical chart the loaded kernel cannot reach.

A test that takes a fixture the driver cannot supply is NOT driven, and the
driver says so through ``on_unreachable`` rather than passing over it: a golden
test the guard never runs is one the guard cannot vouch for, and the first
version of this driver skipped five baseline readers that way without a word.
"""

import functools
import importlib
import inspect
from pathlib import Path
from typing import Callable, Optional

import pytest

#: pytest.exit() raises this; it must never be swallowed as a driven test's failure.
Exit = pytest.exit.Exception

SVG_DIR = Path(__file__).parent / "svg"

#: The modules whose tests read SVG baselines through ``compare_svg_file``.
GOLDEN_TEST_MODULES = (
    "tests.core.test_chart_drawer",
    "tests.core.test_optional_mark_baselines",
    "tests.core.test_chart_parametrized",
    "tests.core.test_bce_dates",
    "tests.core.test_lunar_phase_svg",
)

#: base < medium < extended. A subject dated outside the loaded kernel's range
#: cannot be cast at all, so the test that reads its baseline skips before it ever
#: names the file — which is not the same as the file having no reader.
TIER_ORDER = {"base": 0, "medium": 1, "extended": 2}

#: Baselines read by a test the driver can only run on the full-range kernel — a
#: test marked for a higher tier whose subject is not in the matrix, so the tier
#: gate below cannot see it. Counted as out of reach on a lower tier; on the
#: extended kernel each of these MUST be recorded by the driver, and the reader
#: gate says so.
BASELINES_READ_ONLY_BY_EXTENDED_TIER_TESTS: dict[str, str] = {
    "Historical Subject - Natal Chart - Classic.svg": (
        "test_chart_drawer.py::TestChartOptions::test_historical_date is @extended: a 1500 "
        "chart cannot be cast on the medium kernel"
    ),
}


def baselines_out_of_this_runs_reach() -> set[str]:
    """Baselines whose chart this run's kernel tier or backend cannot produce.

    Declared, not guessed: every matrix subject carries the tier it needs, and the
    detected tier is what tests/conftest.py already probes for. The full point set
    needs per-body asteroid files the swisseph setup cannot download; the conftest
    probes for that too and skips the all-points tests when the probe fails. Out of
    reach is not the same as having no reader, and the gates subtract this set.
    """
    from tests.conftest import _detect_ephemeris_tier, _tnos_available
    from tests.data.test_subjects_matrix import GEOGRAPHIC_SUBJECTS, TEMPORAL_SUBJECTS

    stored = [path.name for path in SVG_DIR.glob("*.svg")]
    available = TIER_ORDER.get(_detect_ephemeris_tier(), 0)
    out_of_reach: set[str] = set()
    if available < TIER_ORDER["extended"]:
        out_of_reach |= set(BASELINES_READ_ONLY_BY_EXTENDED_TIER_TESTS)
    subjects_beyond_the_kernel = {
        subject["name"]
        for subject in (*TEMPORAL_SUBJECTS, *GEOGRAPHIC_SUBJECTS)
        if TIER_ORDER.get(subject.get("tier", "base"), 0) > available
    }
    out_of_reach |= {
        name
        for name in stored
        for subject in subjects_beyond_the_kernel
        if name.startswith(subject + " -") or name.startswith(subject + " and ")
    }
    if not _tnos_available():
        out_of_reach |= {name for name in stored if "All Active Points" in name}
    return out_of_reach


@functools.lru_cache(maxsize=1)
def baselines_the_golden_tests_compare() -> frozenset[str]:
    """The baselines the golden tests actually hand to the comparison, by running them.

    Cached: driving the suite costs seconds, and more than one gate asks. A test
    that fails still names the baseline it wanted; a test that fails before it
    gets there names nothing, and its baseline shows up as unread — the truth.
    """
    compared: set[str] = set()

    def recording(baseline_path, _generated_svg, **_kwargs):
        compared.add(Path(baseline_path).name)

    drive_every_golden_test(recording)
    return frozenset(compared)


def parameter_sets(function):
    """The argument tuples a ``@pytest.mark.parametrize``'d test is called with.

    Only what the driver needs: one or more parametrize marks, positional
    argnames, plain iterables of values. A test using anything richer falls out of
    the driver, and the gate that relies on it says which names it could not reach.
    """
    marks = [mark for mark in getattr(function, "pytestmark", ()) if mark.name == "parametrize"]
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


def drive_every_golden_test(
    on_comparison: Callable[..., None],
    on_failure: Optional[Callable[[str, BaseException], None]] = None,
    on_unreachable: Optional[Callable[[str], None]] = None,
) -> None:
    """Call every golden test with ``compare_svg_file`` replaced by ``on_comparison``.

    Args:
        on_comparison: Called in place of ``compare_svg_file(baseline_path,
            generated_svg, **kwargs)`` — the gate's observer.
        on_failure: Called with the test's qualified name and the exception when a
            driven test raises anything, including ``Skipped``. ``KeyboardInterrupt``,
            ``SystemExit`` and ``pytest.exit`` are never swallowed.
        on_unreachable: Called with the qualified name of a test the driver cannot
            call — one that takes a fixture other than its parametrize arguments.
    """
    import tests.data.compare_svg_lines as comparison

    modules = [importlib.import_module(name) for name in GOLDEN_TEST_MODULES]
    patched = [module for module in modules if hasattr(module, "compare_svg_file")]
    drawer = modules[0]
    cached_subjects = dict(drawer._subject_cache)

    def drive(function, instance, qualified_name, setup_failure=None):
        offset = 1 if instance is not None else 0
        sets, names = parameter_sets(function)
        if len(inspect.signature(function).parameters) - offset != len(names):
            if on_unreachable is not None:
                on_unreachable(qualified_name)
            return
        if setup_failure is not None:
            # The class could not be set up — on this kernel, say — so the test
            # cannot run; but whether the driver COULD call it was just decided
            # above, on the signature alone, and that answer does not depend on
            # the kernel. Report the failure per test and move on.
            if on_failure is not None:
                on_failure(qualified_name, setup_failure)
            return
        for arguments in sets:
            try:
                function(instance, *arguments) if instance is not None else function(*arguments)
            except (KeyboardInterrupt, SystemExit, Exit):
                raise
            except BaseException as failure:
                if on_failure is not None:
                    on_failure(qualified_name, failure)

    original = comparison.compare_svg_file
    comparison.compare_svg_file = on_comparison
    for module in patched:
        module.compare_svg_file = on_comparison
    try:
        for module in modules:
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if inspect.isclass(attribute) and attribute_name.startswith("Test"):
                    setup_failure = None
                    setup = getattr(attribute, "setup_class", None)
                    if setup is not None:
                        try:
                            setup()
                        except (KeyboardInterrupt, SystemExit, Exit):
                            raise
                        except BaseException as failure:
                            setup_failure = failure
                    for name in dir(attribute):
                        if name.startswith("test_"):
                            drive(getattr(attribute, name), attribute(), f"{attribute_name}::{name}", setup_failure)
                elif inspect.isfunction(attribute) and attribute_name.startswith("test_"):
                    drive(attribute, None, attribute_name)
    finally:
        comparison.compare_svg_file = original
        for module in patched:
            module.compare_svg_file = original
        drawer._subject_cache.clear()
        drawer._subject_cache.update(cached_subjects)
