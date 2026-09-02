# -*- coding: utf-8 -*-
"""``kerykeion status`` — a thin wrapper over :mod:`kerykeion_cli.diagnostics`."""

from __future__ import annotations

from typing import Annotated

from kerykeion_cli import diagnostics
from kerykeion_cli.parser import Opt


def status(
    json_out: Annotated[bool, Opt(("--json",), "Emit the status as JSON (default: human-readable text).")] = False,
    check: Annotated[
        bool, Opt(("--check",), "Also run the install checks (a real calculation included); exit 6 if one fails.")
    ] = False,
) -> None:
    """Backend, ephemeris data and calc mode in use; --check judges the install."""
    code = diagnostics.render(json_out=json_out, check=check)
    if code:
        raise SystemExit(code)
