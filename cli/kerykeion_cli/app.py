# -*- coding: utf-8 -*-
"""The command tree and its dispatch.

:func:`build_parser` mounts every command and group on the root parser;
:func:`run` parses one command line and calls the chosen command with its
flags as keyword arguments. No kerykeion symbol is imported at module level,
which keeps the cold-import gate green.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from typing import Any, Callable

from kerykeion_cli import errors
from kerykeion_cli.parser import add_command, add_group

try:
    __version__ = _pkg_version("kerykeion-cli")
except PackageNotFoundError:  # a source tree without installation
    __version__ = "0.0.0"

DESCRIPTION = (
    "Astrology from the terminal. Save a subject once (kerykeion subject save ada --date 1990-07-15 "
    "--time 10:30 --lat 41.9 --lng 12.5 --tz Europe/Rome), then pass -s ada to any command. "
    "A terminal gets a text report, a pipe gets JSON; -f text|json|xml|svg and -o FILE choose explicitly."
)

# Namespace entries that are the parser's, not a command's.
_INTERNAL = frozenset({"handler", "menu", "traceback", "warnings_as_errors"})


def build_parser() -> argparse.ArgumentParser:
    """The root parser with every command mounted: charts, analyses, techniques and events, subjects and setup."""
    from kerykeion_cli.commands import analysis, call, charts, info, series, sky, status, subject, technique

    root = argparse.ArgumentParser(prog="kerykeion", description=DESCRIPTION)
    root.add_argument("-V", "--version", action="version", version=__version__, help="Print the kerykeion-cli version and exit.")
    root.add_argument("--traceback", action="store_true", help="Show a full traceback on error (default: a one-line message).")
    root.add_argument("--warnings-as-errors", action="store_true", help="Exit 9 when any ephemeris warning or house fallback occurs.")
    root.set_defaults(menu=root)
    subparsers = root.add_subparsers(metavar="<command>")
    charts_and_analyses: list[tuple[str, Callable[..., Any]]] = [
        ("natal", charts.natal),
        ("now", charts.now),
        ("synastry", charts.synastry),
        ("transit", charts.transit),  # the single-moment dual wheel
        ("composite", charts.composite),
        ("return", charts.return_chart),  # `return` is a keyword, hence the callable's name
        ("progression", charts.progression),
        ("aspects", analysis.aspects),
        ("dominants", analysis.dominants),
        ("moon", analysis.moon),
        ("relationship-score", analysis.relationship_score),
    ]
    for name, func in charts_and_analyses:
        add_command(subparsers, name, func)
    add_group(subparsers, "technique", "Analytical techniques on a stored subject.", technique.COMMANDS)
    add_group(subparsers, "sky", "Sun, Moon and planet events, at a moment or over a range.", sky.COMMANDS)
    series_commands: list[tuple[str, Callable[..., Any]]] = [("ephemeris", series.ephemeris), ("transits", series.transits)]
    for name, func in series_commands:  # the time series
        add_command(subparsers, name, func)
    add_group(subparsers, "subject", "Save and inspect subjects; -s <name> reuses them everywhere.", subject.COMMANDS)
    add_group(subparsers, "info", "What the flags accept: literals, point sets, fixed stars, methods.", info.COMMANDS)
    add_command(subparsers, "status", status.status)
    add_command(subparsers, "call", call.call)
    return root


def run(argv: list[str]) -> int:
    """Parse *argv* and run the chosen command; a group or a bare ``kerykeion`` prints its help."""
    args = build_parser().parse_args(argv)
    errors.set_traceback_enabled(args.traceback)
    errors.set_warnings_as_errors(args.warnings_as_errors)
    handler = getattr(args, "handler", None)
    if handler is None:
        args.menu.print_help()
        return 0
    kwargs = {name: value for name, value in vars(args).items() if name not in _INTERNAL}
    if getattr(handler, "render_flags", False):
        from kerykeion_cli.commands._shared import _RENDER_FLAGS, _render_options

        kwargs["opts"] = _render_options({flag: kwargs.pop(flag, None) for flag in _RENDER_FLAGS})
    handler(**kwargs)
    return 0
