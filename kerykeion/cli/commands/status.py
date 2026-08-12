# -*- coding: utf-8 -*-
"""``kerykeion status`` - the Typer ([cli]) path.

A thin wrapper over :mod:`kerykeion.cli.diagnostics`, which holds the actual
introspection logic and is shared with the no-extra stdlib dispatch. Keeping
the logic out of this module means the two paths that serve ``status`` (with
and without the extra) can never drift apart.
"""

from __future__ import annotations

from typing import Annotated

import typer

from kerykeion.cli import diagnostics


def status(
    json_out: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit the status as JSON (default: human-readable text).",
        ),
    ] = False,
) -> None:
    """Show the runtime state of kerykeion: active backend, ephemeris data, calc mode.

    Works the same with or without the ``[cli]`` extra. Without the extra it is
    one of the few commands available (alongside ``--version`` and ``--help``);
    the diagnostics core is stdlib-only.
    """
    diagnostics.render(json_out=json_out)
