# -*- coding: utf-8 -*-
"""Optional command-line interface for Kerykeion.

The console-script entry point ``kerykeion`` (``[project.scripts]``) and
``python -m kerykeion`` both resolve to :func:`main` here. The full CLI lives in
the ``kerykeion[cli]`` extra (typer + rich), but the command is installed for
EVERY user — static metadata — so this module is deliberately importable
WITHOUT those dependencies and offers a small stdlib-only surface when the
extra is absent:

* ``kerykeion status``        — runtime state (backend, LEB data, calc mode);
* ``kerykeion --version``/``-V``;
* ``kerykeion --help``/``-h`` (and a bare ``kerykeion``).

Any *other* subcommand (the chart/technique/sky suite) prints an install hint
and exits 3 — never a traceback.

Import discipline: this module imports ONLY stdlib at module level. typer,
rich, :mod:`kerykeion.cli.app` and :mod:`kerykeion.cli.diagnostics` are imported
lazily inside functions, so ``import kerykeion.cli`` stays typer-free and cheap
— the invariant pinned by ``tests/core/test_cli.py`` and the cold-import gate.
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
                      Add --json for machine-readable output.
  -V, --version       Print the kerykeion version and exit.
  -h, --help          Show this help and exit.

Full command-line interface:
  The chart, technique, sky, time-series and subject commands (natal, transit,
  synastry, ephemeris, ...) are part of the optional [cli] extra:

      pip install "kerykeion[cli]"

  After installing it, `kerykeion --help` lists every command.
"""


def _version_string() -> str:
    """Installed kerykeion version, without importing kerykeion.

    Reading it via ``importlib.metadata`` (the same source
    ``kerykeion.__version__`` uses) keeps ``--version`` fast in the no-extra
    path: no ~1.5 s backend init, no typer.
    """
    try:
        return importlib.metadata.version("kerykeion")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def _typer_available() -> bool:
    """True iff the [cli] extra's framework is importable.

    Uses :func:`importlib.util.find_spec` (no import side effects) for the
    happy path. The actual ``from kerykeion.cli.app import run`` in :func:`main`
    is still wrapped in try/except to catch a typer install that find_spec sees
    but fails to import. A third-party meta_path finder that raises on unknown
    names should not crash the decision either: treat that as "not usable".
    """
    try:
        return importlib.util.find_spec("typer") is not None
    except (ImportError, ModuleNotFoundError):  # pragma: no cover - defensive
        return False


def _stdlib_dispatch(args: list[str]) -> int:
    """Serve the command with the stdlib alone (no typer/rich).

    Returns the process exit code. Only ``status``, ``--version`` and
    ``--help``/bare do real work; every other invocation is a request for the
    full [cli] suite, signalled with the install hint + exit 3.
    """
    # No arguments -> base help, exit 0 (mirrors the typer app's bare behaviour).
    if not args:
        sys.stdout.write(_BASE_HELP)
        return 0

    first, rest = args[0], args[1:]

    if first in ("--help", "-h"):
        sys.stdout.write(_BASE_HELP)
        return 0

    if first in ("--version", "-V"):
        sys.stdout.write(_version_string() + "\n")
        return 0

    if first == "status":
        # ``status`` accepts only the --json flag; anything else is invalid input.
        unknown = [a for a in rest if a != "--json"]
        if unknown:
            sys.stderr.write(
                f"kerykeion: error: unknown option for 'status': {unknown[0]!r}\n"
                "Hint: 'status' accepts only --json.\n"
            )
            return 4
        from kerykeion.cli import diagnostics

        diagnostics.render(json_out="--json" in rest)
        return 0

    # Anything else - a full-CLI command (natal, transit, ...) or an unknown
    # token - needs the [cli] extra. Surface the install hint, exit 3.
    sys.stderr.write(_INSTALL_HINT)
    return 3


def main(argv: list[str] | None = None) -> int:
    """Console-script entry point (also reached by ``python -m kerykeion``).

    With the ``[cli]`` extra: run the full Typer application. Without it: fall
    back to :func:`_stdlib_dispatch`, which still serves ``status``,
    ``--version`` and ``--help``.
    """
    args = sys.argv[1:] if argv is None else list(argv)

    if _typer_available():
        try:
            from kerykeion.cli.app import run
        except ModuleNotFoundError as exc:
            # find_spec saw typer but importing the app still failed on typer/
            # rich (a broken install) -> degrade to the stdlib core. Any other
            # missing module is a genuine bug; re-raise so it is not swallowed.
            if exc.name in {"typer", "rich"}:
                return _stdlib_dispatch(args)
            raise
        run()
        return 0

    return _stdlib_dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
