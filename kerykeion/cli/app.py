# -*- coding: utf-8 -*-
"""Typer application assembly for the kerykeion CLI.

Placeholder during the staged build-out: ``run`` exists so the console-script
entry point is exercisable end-to-end before any command is wired. Real command
registration (the Typer app, the subject resolver, the renderers) arrives in
the later phases. This module imports NO kerykeion symbol and NO typer at
module level yet — that invariant is permanent for module-level code; runtime
imports live inside the command callables.
"""

from __future__ import annotations

import sys


def run() -> None:
    """Entry point invoked by :func:`kerykeion.cli.main`.

    Returns normally; the caller decides the exit code. (The real Typer app
    will raise ``SystemExit`` via Click on its own; mirroring that contract
    here would make ``main``'s ``return 0`` unreachable.)
    """
    sys.stderr.write("kerykeion CLI: bootstrap complete, commands not wired yet.\n")
