# -*- coding: utf-8 -*-
"""``kerykeion info <sub>`` — what the flags accept.

Derived at runtime from the library (the literal aliases, the point/star
presets, the dominant strategies), so it cannot drift from what the flags
validate against.
"""

from __future__ import annotations

import difflib
import typing
from typing import Annotated, Optional

from kerykeion.extra.cli.commands._shared import _emit
from kerykeion.extra.cli.options import FormatOpt, OutputOpt
from kerykeion.extra.cli.parser import Arg



def _literal_tables() -> dict[str, list[str]]:
    """Every public string ``Literal`` alias in ``kerykeion.schemas.literals``, by name."""
    from kerykeion.schemas import literals as module

    tables = {}
    for name in dir(module):
        args = typing.get_args(getattr(module, name)) if not name.startswith("_") else ()
        if args and all(isinstance(arg, str) for arg in args):
            tables[name] = list(args)
    return dict(sorted(tables.items()))


def literals(
    name: Annotated[Optional[str], Arg(help="One alias to show (e.g. HousesSystemIdentifier). Omit for all.")] = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Accepted values by literal name (house systems, ayanamsas, ...)."""
    tables = _literal_tables()
    if name is None:
        _emit(tables, fmt, output)
        return
    match = {key.lower(): key for key in tables}.get(name.strip().lower())
    if match is None:
        close = difflib.get_close_matches(name, list(tables), n=1)
        hint = f" (did you mean {close[0]!r}?)" if close else ""
        raise ValueError(f"no literal named {name!r}{hint}. Run `kerykeion info literals` for the list.")
    _emit({match: tables[match]}, fmt, output)


def points(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """The --points presets and their contents."""
    from kerykeion.extra.cli import subject_resolver

    _emit(subject_resolver._point_sets(), fmt, output)


def stars(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """The --fixed-stars presets and their contents."""
    from kerykeion.extra.cli import subject_resolver

    _emit(subject_resolver._fixed_star_sets(), fmt, output)


def houses(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """What --houses accepts: letters (case matters) and names."""
    from kerykeion.extra.cli import subject_resolver

    letters = sorted(subject_resolver.literal_values("HousesSystemIdentifier"))
    _emit({"letters": letters, "names": dict(sorted(subject_resolver._HOUSES_BY_NAME.items()))}, fmt, output)


def methods(fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """Strategy and method names per flag, as the library reports them."""
    from kerykeion import DominantsFactory
    from kerykeion.extra.cli.rendering.options import SVG_VARIANTS, chart_choices

    _emit(
        {
            "dominants_method": list(DominantsFactory.available_methods()),
            "lot": ["fortune", "spirit"],
            "directions_rate": ["ptolemy", "naibod"],
            "nodes_method": ["mean", "osculating"],
            "chart_theme": list(chart_choices("theme")),
            "chart_language": list(chart_choices("chart_language")),
            "chart_style": list(chart_choices("style")),
            "svg_variant": sorted(SVG_VARIANTS),
        },
        fmt,
        output,
    )


COMMANDS = [
    ("literals", literals),
    ("points", points),
    ("stars", stars),
    ("houses", houses),
    ("methods", methods),
]
