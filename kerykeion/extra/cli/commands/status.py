# -*- coding: utf-8 -*-
"""``kerykeion status`` on the Typer path — a thin wrapper over :mod:`kerykeion.extra.cli.diagnostics`, shared with the no-extra path."""

from __future__ import annotations

from typing import Annotated

import typer

from kerykeion.extra.cli import diagnostics


def status(
    json_out: Annotated[bool, typer.Option("--json", help="Emit the status as JSON (default: human-readable text).")] = False,
    check: Annotated[
        bool, typer.Option("--check", help="Also run the install checks (a real calculation included); exit 6 if one fails.")
    ] = False,
) -> None:
    """Backend, ephemeris data and calc mode in use; --check judges the install."""
    code = diagnostics.render(json_out=json_out, check=check)
    if code:
        raise SystemExit(code)
