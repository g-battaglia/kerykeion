# -*- coding: utf-8 -*-
"""Optional command-line interface for Kerykeion.

The console-script entry point ``kerykeion`` (``[project.scripts]``) and
``python -m kerykeion.cli`` both resolve to :func:`main` here. The full CLI
lives in the ``kerykeion[cli]`` extra (typer + rich); this module is
deliberately importable WITHOUT those dependencies so that:

* ``import kerykeion`` stays lightweight and never pulls in typer;
* the bare ``kerykeion`` command prints a helpful install hint instead of
  crashing with a ``ModuleNotFoundError`` when the extra is absent.

Nothing under ``kerykeion.cli`` imports typer, rich, or any kerykeion symbol at
module import time — every command reaches the library through a lazy accessor.
This is what keeps the import-graph cold-import gate
(``scripts/check_import_graph.py --fresh-imports``) green.
"""

from __future__ import annotations

import sys

__all__ = ["main"]


def main() -> int:
    """Console-script entry point.

    Imports the Typer application lazily so that:

    * ``import kerykeion.cli`` never pulls in typer (the module-import path that
      ``pkgutil.walk_packages`` and the cold-import gate exercise);
    * a bare ``pip install kerykeion`` (no extras) still installs the
      ``kerykeion`` command, which prints an install hint and exits 3 instead of
      dumping a traceback.
    """
    try:
        from kerykeion.cli.app import run
    except ModuleNotFoundError as exc:
        # ``[project.scripts]`` is static metadata: the ``kerykeion`` command is
        # installed even without the [cli] extra, so this is the default path
        # for users who skipped the docs. Match only the extra's own deps so a
        # genuine bug (a missing kerykeion submodule) still raises normally.
        if exc.name in {"typer", "rich"}:
            sys.stderr.write(
                "The kerykeion command-line interface needs the [cli] extra.\n"
                "Install it with:\n"
                '    pip install "kerykeion[cli]"\n'
            )
            return 3
        raise
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
