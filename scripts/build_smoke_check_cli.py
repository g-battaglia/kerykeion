#!/usr/bin/env python3
"""Smoke-check the kerykeion CLI against the BUILT WHEEL in a clean room.

Run by ``poe build:smoke`` in an isolated environment holding BOTH wheels — the
library and the CLI — which is what ``pip install "kerykeion[cli]"`` gives a
user. Unlike ``scripts/build_smoke_check.py`` (which imports kerykeion to render
a chart and asserts the library wheel carries no command), this script exercises
the COMMAND through a subprocess, because the point is the entry point as a user
runs it.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "kerykeion_cli", *args], capture_output=True, text=True, check=False)


def _fail(label: str, detail: str) -> int:
    print(f"FAIL: {label}\n{detail}")
    return 1


def main() -> int:
    # The console script the CLI wheel declares: a user types this, not python -m.
    if shutil.which("kerykeion") is None:
        return _fail("console script", "the kerykeion command is not on PATH in the wheel environment")
    rv = _run(["--version"])
    if rv.returncode != 0 or not rv.stdout.strip():
        return _fail("--version", f"rc={rv.returncode} out={rv.stdout!r}\n{rv.stderr}")
    rh = _run(["--help"])
    if rh.returncode != 0 or "usage" not in rh.stdout.lower():
        return _fail("--help", f"rc={rh.returncode}\n{rh.stdout}\n{rh.stderr}")

    # A bad command line is a clean, classified exit — never a traceback.
    rn = _run(["natal"])
    if rn.returncode != 4 or "Traceback" in rn.stderr:
        return _fail("natal without a subject", f"rc={rn.returncode}\n{rn.stderr}")

    # ``info`` reads the installed library rather than the repo: the cheapest
    # proof that the packaged CLI can reach it.
    ri = _run(["info", "literals", "HousesSystemIdentifier", "-f", "json"])
    if ri.returncode != 0 or "HousesSystemIdentifier" not in ri.stdout:
        return _fail("info", f"rc={ri.returncode}\n{ri.stdout}\n{ri.stderr}")
    try:
        tables = json.loads(ri.stdout)
    except json.JSONDecodeError as exc:
        return _fail("info json", f"{exc}\n{ri.stdout}")
    if not tables.get("HousesSystemIdentifier"):
        return _fail("info json", f"empty table: {ri.stdout}")

    # ``status --check`` exercises the backend end to end and exits non-zero if
    # the packaged install cannot actually compute.
    rd = _run(["status", "--check", "--json"])
    if rd.returncode != 0:
        return _fail("status --check", f"rc={rd.returncode}\n{rd.stdout}\n{rd.stderr}")

    print(f"wheel CLI OK: kerykeion on PATH, --version ({rv.stdout.strip()}), --help, clean exit 4, info ({len(tables)} literal tables), status --check green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
