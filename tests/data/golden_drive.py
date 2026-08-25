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
class with ``setup_class`` gets it called first, as pytest would. A driven test
that fails, or skips, is that test's business: the gate is told, if it asked, and
carries on to the next one. ``Skipped`` is a ``BaseException``, not an
``Exception``, and a gate that let it through would end as skipped itself at the
first deep-historical chart the loaded kernel cannot reach.
"""

import importlib
import inspect
from typing import Callable, Optional

#: The modules whose tests read SVG baselines through ``compare_svg_file``.
GOLDEN_TEST_MODULES = (
    "tests.core.test_chart_drawer",
    "tests.core.test_optional_mark_baselines",
    "tests.core.test_chart_parametrized",
    "tests.core.test_bce_dates",
)


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
) -> None:
    """Call every golden test with ``compare_svg_file`` replaced by ``on_comparison``.

    Args:
        on_comparison: Called in place of ``compare_svg_file(baseline_path,
            generated_svg, **kwargs)`` — the gate's observer.
        on_failure: Called with the test's qualified name and the exception when a
            driven test raises anything, including ``Skipped``. ``KeyboardInterrupt``
            and ``SystemExit`` are never swallowed.
    """
    import tests.data.compare_svg_lines as comparison

    modules = [importlib.import_module(name) for name in GOLDEN_TEST_MODULES]
    patched = [module for module in modules if hasattr(module, "compare_svg_file")]
    drawer = modules[0]
    cached_subjects = dict(drawer._subject_cache)

    def drive(function, instance, qualified_name):
        offset = 1 if instance is not None else 0
        sets, names = parameter_sets(function)
        if len(inspect.signature(function).parameters) - offset != len(names):
            return  # takes fixtures this driver cannot supply
        for arguments in sets:
            try:
                function(instance, *arguments) if instance is not None else function(*arguments)
            except (KeyboardInterrupt, SystemExit):
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
                    setup = getattr(attribute, "setup_class", None)
                    if setup is not None:
                        try:
                            setup()
                        except (KeyboardInterrupt, SystemExit):
                            raise
                        except BaseException as failure:
                            if on_failure is not None:
                                on_failure(f"{attribute_name}::setup_class", failure)
                            continue
                    for name in dir(attribute):
                        if name.startswith("test_"):
                            drive(getattr(attribute, name), attribute(), f"{attribute_name}::{name}")
                elif inspect.isfunction(attribute) and attribute_name.startswith("test_"):
                    drive(attribute, None, attribute_name)
    finally:
        comparison.compare_svg_file = original
        for module in patched:
            module.compare_svg_file = original
        drawer._subject_cache.clear()
        drawer._subject_cache.update(cached_subjects)
