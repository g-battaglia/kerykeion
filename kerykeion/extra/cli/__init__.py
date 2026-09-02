# -*- coding: utf-8 -*-
"""Optional command-line interface for Kerykeion.

The ``kerykeion`` console script and ``python -m kerykeion`` both resolve to
:func:`main`. The full CLI needs the ``kerykeion[cli]`` extra (typer + rich),
but the command is installed for every user, so this module imports only the
stdlib at module level and serves ``status``, ``--version`` and ``--help`` on
its own; any other command prints an install hint and exits 3.

(It is not *fast*: importing a submodule imports ``kerykeion`` first — about
1.3 s of backend selection. Making that lazy is a change to ``kerykeion/__init__.py``.)
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import sys

__all__ = ["main"]

_INSTALL_HINT = (
    "That command is part of the kerykeion command-line interface, which needs "
    "the optional [cli] extra.\n"
    "Install it with:\n"
    '    pip install "kerykeion[cli]"\n'
    "\n"
    "Without the extra, only these work: `kerykeion status`, "
    "`kerykeion --version`, `kerykeion --help`.\n"
)

_BASE_HELP = """\
Usage: kerykeion [--version] [-h | --help] <command>

kerykeion - astrology from the terminal.

Base commands (work without any extras):
  status              Show the runtime state of kerykeion (active backend,
                      ephemeris data files, calc mode) and exit.
                      Add --json for machine-readable output, --check to
                      also run the install checks (exit 6 if one fails).
  -V, --version       Print the kerykeion version and exit.
  -h, --help          Show this help and exit.

Full command-line interface:
  The chart, technique, sky, time-series and subject commands (natal, transit,
  synastry, ephemeris, ...) are part of the optional [cli] extra:

      pip install "kerykeion[cli]"

  After installing it, `kerykeion --help` lists every command.
"""


def _version_string() -> str:
    try:
        return importlib.metadata.version("kerykeion")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def _typer_available() -> bool:
    """True iff typer is importable (``find_spec`` has no import side effects)."""
    try:
        return importlib.util.find_spec("typer") is not None
    except (ImportError, ModuleNotFoundError):  # pragma: no cover - a hostile meta_path finder
        return False


def _stdlib_dispatch(args: list[str]) -> int:
    """Serve ``status``/``--version``/``--help`` with the stdlib alone; anything else gets the install hint (exit 3)."""
    first, rest = (args[0], args[1:]) if args else ("--help", [])
    if first in ("--help", "-h"):
        sys.stdout.write(_BASE_HELP)
        return 0
    if first in ("--version", "-V"):
        sys.stdout.write(_version_string() + "\n")
        return 0
    if first == "status":
        unknown = [a for a in rest if a not in ("--json", "--check")]
        if unknown:
            sys.stderr.write(
                f"kerykeion: error: unknown option for 'status': {unknown[0]!r}\n"
                "Hint: 'status' accepts only --json and --check.\n"
            )
            return 4
        from kerykeion.extra.cli import diagnostics

        return diagnostics.render(json_out="--json" in rest, check="--check" in rest)
    sys.stderr.write(_INSTALL_HINT)
    return 3


def main(argv: list[str] | None = None) -> int:
    """Console-script entry point: the Typer app with the ``[cli]`` extra, the stdlib fallback without."""
    args = sys.argv[1:] if argv is None else list(argv)
    if not _typer_available():
        return _stdlib_dispatch(args)
    try:
        from kerykeion.extra.cli.app import run
    except ModuleNotFoundError as exc:
        if exc.name in {"typer", "rich"}:  # find_spec saw typer but the install is broken
            return _stdlib_dispatch(args)
        raise
    if argv is None:
        run()
        return 0
    # Click reads sys.argv directly; an explicit argv is swapped in for the call.
    saved, sys.argv = sys.argv, ["kerykeion", *args]
    try:
        run()
    finally:
        sys.argv = saved
    return 0


if __name__ == "__main__":
    sys.exit(main())
