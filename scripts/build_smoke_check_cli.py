#!/usr/bin/env python3
"""Smoke-check the kerykeion CLI against the BUILT WHEEL in a clean room.

Run by ``poe build:smoke`` in two isolated environments:

* the wheel installed ALONE (no ``[cli]`` extra) — the ``kerykeion`` command is
  installed by the static ``[project.scripts]`` metadata even without the extra,
  so this is the default path for a bare ``pip install kerykeion``. It must
  degrade to the install hint (exit 3, no traceback), not crash;
* the wheel installed WITH ``[cli]`` — ``--version`` and ``--help`` must exit 0.

The script tells the two environments apart by probing for ``typer`` (the extra
is exactly typer+rich), so the same file covers both. ``poe build:smoke`` runs
it once per environment.

Unlike ``scripts/build_smoke_check.py`` (which lives in the wheel-only env and
imports kerykeion to render a chart), this script exercises the COMMAND through
a subprocess, because the whole point is the entry point's install-hint guard.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "kerykeion", *args], capture_output=True, text=True, check=False
    )


def _fail(label: str, detail: str) -> int:
    print(f"FAIL: {label}\n{detail}")
    return 1


def _smoke_without_extra() -> int:
    """The bare ``pip install kerykeion`` path: command present, CLI absent."""
    r = _run(["--version"])
    problems = []
    if r.returncode != 3:
        problems.append(f"  expected exit 3, got {r.returncode}")
    if "kerykeion[cli]" not in r.stderr:
        problems.append(f"  stderr missing the install hint; got:\n{r.stderr!r}")
    if "Traceback" in r.stderr or "Traceback" in r.stdout:
        problems.append("  a traceback was printed instead of a clean install hint")
    if problems:
        return _fail("wheel-without-extra", "\n".join(problems))
    print("wheel-without-extra OK: command degrades to exit 3 with the install hint")
    return 0


def _smoke_with_extra() -> int:
    """The ``pip install kerykeion[cli]`` path: --version and --help work."""
    rv = _run(["--version"])
    if rv.returncode != 0 or not rv.stdout.strip():
        return _fail("wheel-with-extra --version", f"rc={rv.returncode} out={rv.stdout!r}\n{rv.stderr}")
    rh = _run(["--help"])
    if rh.returncode != 0 or "Usage" not in rh.stdout:
        return _fail("wheel-with-extra --help", f"rc={rh.returncode}\n{rh.stdout}\n{rh.stderr}")
    print(f"wheel-with-extra OK: --version ({rv.stdout.strip()}) and --help green")
    return 0


def main() -> int:
    cli_present = importlib.util.find_spec("typer") is not None
    # Run whichever half applies to this environment. ``poe build:smoke`` invokes
    # this script in BOTH environments, so both halves get exercised across the
    # two runs.
    return _smoke_with_extra() if cli_present else _smoke_without_extra()


if __name__ == "__main__":
    sys.exit(main())
