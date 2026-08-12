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


def _make_app() -> typer.Typer:
    app = typer.Typer(
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
    ) -> None:
        # ``--version`` short-circuits before any subcommand is required.
        if version:
            typer.echo(__version__)
            raise typer.Exit(0)
        # Reached with neither --version nor a subcommand: show help and exit 0.
        # (``no_args_is_help`` already covers the fully-bare case; this branch
        # also catches e.g. ``kerykeion --no-color`` once that option exists.)
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(0)

    return app


app = _make_app()


def run() -> None:
    """Entry point invoked by :func:`kerykeion.cli.main`.

    ``app()`` raises ``SystemExit`` (via Click) with the command's exit code, so
    nothing runs after this in :func:`kerykeion.cli.main`.
    """
    app()
