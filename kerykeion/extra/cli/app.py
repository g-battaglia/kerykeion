# -*- coding: utf-8 -*-
"""Typer application assembly for the kerykeion CLI.

Imported lazily by :func:`kerykeion.extra.cli.main`. typer is imported at module
level on purpose — that is what lets the entry point detect a missing ``[cli]``
extra. No kerykeion symbol is imported at module level, which keeps the
cold-import gate green and ``import kerykeion`` typer-free.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from typing import Annotated

import typer

from kerykeion.extra.cli.typer_app import KerykeionTyper

try:
    __version__ = _pkg_version("kerykeion")
except PackageNotFoundError:  # a source tree without installation
    __version__ = "0.0.0"

app = KerykeionTyper(
    name="kerykeion",
    help=(
        "Astrology from the terminal.\n\n"
        "Start with a subject: kerykeion subject save ada --date 1990-07-15 --time 10:30 "
        "--lat 41.9 --lng 12.5 --tz Europe/Rome. Then pass -s ada to any command below.\n\n"
        "A terminal gets a text report, a pipe gets JSON; -f text|json|xml|svg and -o FILE choose explicitly."
    ),
    pretty_exceptions_enable=False,  # the CLI renders its own errors
    rich_markup_mode="rich",
    add_completion=False,
    # No no_args_is_help: that exits 2 before the callback; a bare `kerykeion` shows help and exits 0 below.
)


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: Annotated[
        bool, typer.Option("--version", "-V", help="Print the kerykeion version and exit.", is_eager=True)
    ] = False,
    traceback: Annotated[
        bool, typer.Option("--traceback", help="Show a full traceback on error (default: a one-line message).")
    ] = False,
    warnings_as_errors: Annotated[
        bool, typer.Option("--warnings-as-errors", help="Exit 9 when any ephemeris warning or house fallback occurs.")
    ] = False,
) -> None:
    from kerykeion.extra.cli import errors

    errors.set_traceback_enabled(traceback)
    errors.set_warnings_as_errors(warnings_as_errors)
    if version:
        typer.echo(__version__)
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


def _register_commands() -> None:
    """The help screen is a menu: one panel per kind of question, groups and commands side by side."""
    from kerykeion.extra.cli.commands import analysis, call, charts, info, series, sky, status, subject, technique

    charts_panel = "Charts"
    analyses_panel = "Analyses"
    events_panel = "Techniques, sky events and time series"
    setup_panel = "Subjects and setup"
    for panel, name, command in (
        (charts_panel, "natal", charts.natal),
        (charts_panel, "now", charts.now),
        (charts_panel, "synastry", charts.synastry),
        (charts_panel, "transit", charts.transit),  # the single-moment dual wheel
        (charts_panel, "composite", charts.composite),
        (charts_panel, "return", charts.return_chart),  # `return` is a keyword, hence the callable's name
        (charts_panel, "progression", charts.progression),
        (analyses_panel, "aspects", analysis.aspects),
        (analyses_panel, "dominants", analysis.dominants),
        (analyses_panel, "moon", analysis.moon),
        (analyses_panel, "relationship-score", analysis.relationship_score),
        (events_panel, "ephemeris", series.ephemeris),
        (events_panel, "transits", series.transits),  # the time series
        (setup_panel, "status", status.status),  # stdlib-only; also served without the extra
        (setup_panel, "doctor", info.doctor),  # status with a verdict
        (setup_panel, "call", call.call),
    ):
        app.command(name=name, rich_help_panel=panel)(command)
    app.add_typer(technique.technique_app, name="technique", rich_help_panel=events_panel)
    app.add_typer(sky.sky_app, name="sky", rich_help_panel=events_panel)
    app.add_typer(subject.subject_app, name="subject", rich_help_panel=setup_panel)
    app.add_typer(info.info_app, name="info", rich_help_panel=setup_panel)


_register_commands()


def run() -> None:
    """Entry point invoked by :func:`kerykeion.extra.cli.main`; anything that escapes Click becomes a classified exit."""
    try:
        app()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 — the whole point is to catch all
        from kerykeion.extra.cli.errors import handle_uncaught

        handle_uncaught(exc)
