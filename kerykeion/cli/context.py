# -*- coding: utf-8 -*-
"""Per-invocation context shared across command callables.

Two things live here and nowhere else:

* :func:`was_given` — the single place that consults Click's ``ParameterSource``
  to tell "the user typed this flag" apart from "this is the flag's default".
  Without it, a flag with a meaningful default (e.g. ``--zodiac Tropical``)
  would silently overwrite a profile's ``Sidereal``.
* :func:`kk` — a cached lazy accessor for the ``kerykeion`` package, so a command
  pays the ~1.5s import cost only when it actually runs, and the import-graph
  cold-import gate (which stubs the root) stays green.

Click's ``ParameterSource`` is imported defensively: typer vendorizes click, but
click is also a real installed package here (a transitive of libephemeris); if
neither path resolves, :func:`was_given` returns False (conservative — defaults
do not override), never raises.
"""

from __future__ import annotations

import functools
from typing import Any


def _load_commandline_sentinel():
    try:
        # click is a real installed package here (a transitive of libephemeris),
        # and typer vendorizes its own copy; either path resolves ParameterSource.
        from click.core import ParameterSource

        return ParameterSource.COMMANDLINE
    except Exception:  # pragma: no cover - typer/click is a hard [cli] dependency
        return None


_COMMANDLINE = _load_commandline_sentinel()


def was_given(ctx: Any, param_name: str) -> bool:
    """True iff *param_name* was explicitly passed on this command line.

    Returns False when the source cannot be determined, so flags with defaults
    do not clobber values coming from a profile or config.
    """
    if ctx is None or _COMMANDLINE is None:
        return False
    getter = getattr(ctx, "get_parameter_source", None)
    if getter is None:
        return False
    try:
        return getter(param_name) == _COMMANDLINE
    except (KeyError, ValueError, AttributeError, TypeError):
        return False


@functools.cache
def kk():
    """Cached lazy accessor for the ``kerykeion`` package (import on first call)."""
    import kerykeion

    return kerykeion
