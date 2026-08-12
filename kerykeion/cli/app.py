# -*- coding: utf-8 -*-
"""Typer application assembly for the kerykeion CLI.

This is the Typer app that :func:`kerykeion.cli.main` imports lazily. It imports
typer at module level ON PURPOSE: that import is what lets the entry-point guard
(:func:`kerykeion.cli.main`) detect a missing ``[cli]`` extra and print the
install hint (exit 3) instead of dumping a ``ModuleNotFoundError`` traceback.

No kerykeion symbol is imported at module level — every command reaches the
library through a lazy accessor. This is what keeps the import-graph cold-import
gate (``scripts/check_import_graph.py --fresh-imports``) green, and what keeps
``import kerykeion`` typer-free (this module is only imported when the CLI runs).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from typing import Annotated

import typer

try:
    __version__ = _pkg_version("kerykeion")
except PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0.0.0"

from kerykeion.cli.typer_app import KerykeionTyper  # noqa: E402 — after stdlib import block


def _make_app() -> typer.Typer:
    app = KerykeionTyper(
        name="kerykeion",
        help="Command-line interface for the Kerykeion astrology library.",
        # Click/typer's pretty exception display would wrap and colorize our own
        # SystemExit/error messages. The CLI renders errors itself.
        pretty_exceptions_enable=False,
        rich_markup_mode="rich",
        add_completion=False,
        # No ``no_args_is_help``: that intercepts the bare invocation before the
        # callback and exits 2 (click's "missing command"), which is harsher
        # than ``--help``'s exit 0. We handle the bare case in the callback so a
        # plain ``kerykeion`` shows help and exits 0, matching ``--help``.
    )

    @app.callback(invoke_without_command=True)
    def _root(
        ctx: typer.Context,
        version: Annotated[
            bool,
            typer.Option(
                "--version",
                "-V",
                help="Print the kerykeion version and exit.",
                is_eager=True,
            ),
        ] = False,
        traceback: Annotated[
            bool,
            typer.Option(
                "--traceback",
                help="Show a full traceback on error (default: a one-line message).",
            ),
        ] = False,
        warnings_as_errors: Annotated[
            bool,
            typer.Option(
                "--warnings-as-errors",
                help="Exit 9 when any ephemeris warning or house fallback occurs.",
            ),
        ] = False,
    ) -> None:
        from kerykeion.cli import errors

        # These are read by later code (the error boundary, the warning emitter),
        # so they must be set before the chosen command runs.
        errors.set_traceback_enabled(traceback)
        errors.set_warnings_as_errors(warnings_as_errors)

        # ``--version`` short-circuits before any subcommand is required.
        if version:
            typer.echo(__version__)
            raise typer.Exit(0)
        # Reached with neither --version nor a subcommand: show help and exit 0.
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(0)

    return app


def _register_commands(app: typer.Typer) -> None:
    """Attach every command group to *app*.

    Imported here (not at module top) so the groups are only loaded when the CLI
    actually runs, keeping the import-graph cold-import gate green.
    """
    from kerykeion.cli.commands import call, charts, series, sky, subject, technique

    app.add_typer(subject.subject_app, name="subject")
    app.command(name="natal")(charts.natal)
    app.command(name="now")(charts.now)
    app.command(name="synastry")(charts.synastry)
    app.command(name="transit")(charts.transit)
    app.command(name="composite")(charts.composite)
    # ``return`` is a Python keyword, so the callable is ``return_chart``; the
    # command name the user types is still ``return``.
    app.command(name="return")(charts.return_chart)
    app.command(name="progression")(charts.progression)
    # Time series: top-level (not under a group).
    app.command(name="ephemeris")(series.ephemeris)
    # ``transits`` (plural) is the time-series; ``transit`` (singular) above is
    # the single-moment dual-wheel chart.
    app.command(name="transits")(series.transits)
    # Guarded dispatcher over the public API.
    app.command(name="call")(call.call)
    # Analytical-technique and astronomical-event groups.
    app.add_typer(technique.technique_app, name="technique")
    app.add_typer(sky.sky_app, name="sky")


app = _make_app()
_register_commands(app)


def run() -> None:
    """Entry point invoked by :func:`kerykeion.cli.main`.

    ``app()`` raises ``SystemExit`` (via Click) with the command's exit code, so
    nothing runs after this in :func:`kerykeion.cli.main`. Anything that escapes
    Click (a runtime error from the library, with pretty exceptions disabled)
    reaches :func:`handle_uncaught` and becomes a clean, classified exit.
    """
    try:
        app()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 — the whole point is to catch all
        from kerykeion.cli.errors import handle_uncaught

        handle_uncaught(exc)
