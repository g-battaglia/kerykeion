# -*- coding: utf-8 -*-
"""Typer application assembly for the kerykeion CLI.

Imported lazily by :func:`kerykeion.cli.main`. typer is imported at module
level on purpose — that is what lets the entry point detect a missing ``[cli]``
extra. No kerykeion symbol is imported at module level, which keeps the
cold-import gate green and ``import kerykeion`` typer-free.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from typing import Annotated

import typer

from kerykeion.cli.typer_app import KerykeionTyper

try:
    __version__ = _pkg_version("kerykeion")
except PackageNotFoundError:  # a source tree without installation
    __version__ = "0.0.0"

app = KerykeionTyper(
    name="kerykeion",
    help="Command-line interface for the Kerykeion astrology library.",
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
    from kerykeion.cli import errors

    errors.set_traceback_enabled(traceback)
    errors.set_warnings_as_errors(warnings_as_errors)
    if version:
        typer.echo(__version__)
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


def _register_commands() -> None:
    from kerykeion.cli.commands import analysis, call, charts, info, series, sky, status, subject, technique

    app.command(name="status")(status.status)  # stdlib-only; also served without the extra
    app.command(name="doctor")(info.doctor)  # status with a verdict
    app.add_typer(subject.subject_app, name="subject")
    for name, command in (
        ("natal", charts.natal),
        ("now", charts.now),
        ("synastry", charts.synastry),
        ("transit", charts.transit),  # the single-moment dual wheel
        ("composite", charts.composite),
        ("return", charts.return_chart),  # `return` is a keyword, hence the callable's name
        ("progression", charts.progression),
        ("ephemeris", series.ephemeris),
        ("transits", series.transits),  # the time series
        ("aspects", analysis.aspects),
        ("dominants", analysis.dominants),
        ("moon", analysis.moon),
        ("relationship-score", analysis.relationship_score),
        ("call", call.call),
    ):
        app.command(name=name)(command)
    app.add_typer(technique.technique_app, name="technique")
    app.add_typer(sky.sky_app, name="sky")
    app.add_typer(info.info_app, name="info")


_register_commands()


def run() -> None:
    """Entry point invoked by :func:`kerykeion.cli.main`; anything that escapes Click becomes a classified exit."""
    try:
        app()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 — the whole point is to catch all
        from kerykeion.cli.errors import handle_uncaught

        handle_uncaught(exc)
