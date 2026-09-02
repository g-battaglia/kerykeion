# -*- coding: utf-8 -*-
"""``kerykeion status`` on the Typer path — a thin wrapper over :mod:`kerykeion.extra.cli.diagnostics`, shared with the no-extra path."""

from __future__ import annotations

from typing import Annotated

import typer

from kerykeion.extra.cli import diagnostics


def status(
    json_out: Annotated[
        bool, typer.Option("--json", help="Emit the status as JSON (default: human-readable text).")
    ] = False,
) -> None:
    """Show the runtime state of kerykeion: active backend, ephemeris data, calc mode."""
    diagnostics.render(json_out=json_out)
