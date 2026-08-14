#!/usr/bin/env python3
"""Smoke-check the kerykeion CLI against the BUILT WHEEL in a clean room.

Run by ``poe build:smoke`` in two isolated environments:

* the wheel installed ALONE (no ``[cli]`` extra) — the ``kerykeion`` command is
  installed by the static ``[project.scripts]`` metadata even without the extra,
  so this is the default path for a bare ``pip install kerykeion``. Without the
  extra the command is still useful through a stdlib-only core: ``status``,
  ``--version`` and ``--help`` exit 0, while a full-CLI command (``natal`` …)
  prints the install hint and exits 3 — never a traceback;
* the wheel installed WITH ``[cli]`` — ``--version`` and ``--help`` must exit 0.

The script tells the two environments apart by probing for ``typer`` (the extra
is exactly typer+rich), so the same file covers both. ``poe build:smoke`` runs
it once per environment.

Unlike ``scripts/build_smoke_check.py`` (which lives in the wheel-only env and
imports kerykeion to render a chart), this script exercises the COMMAND through
a subprocess, because the whole point is the entry point's no-extra behaviour.
"""

from __future__ import annotations

import importlib.util
import json
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
    """The bare ``pip install kerykeion`` path: base commands work, full CLI degrades.

    Without the ``[cli]`` extra the command is served by a stdlib-only core:
    ``status``, ``--version`` and ``--help`` exit 0; any full-CLI command still
    prints the install hint and exits 3, never a traceback.
    """
    problems = []

    # --version works and prints the version on stdout (exit 0, no install hint).
    r = _run(["--version"])
    if r.returncode != 0:
        problems.append(f"  --version expected exit 0, got {r.returncode}\n{r.stderr}")
    if not r.stdout.strip():
        problems.append("  --version printed nothing on stdout")
    if "kerykeion[cli]" in r.stderr:
        problems.append("  --version wrongly printed the install hint")

    # status works without the extra (exit 0, backend reported, no traceback).
    r = _run(["status"])
    if r.returncode != 0:
        problems.append(f"  status expected exit 0, got {r.returncode}\n{r.stderr}")
    if "Backend:" not in r.stdout:
        problems.append(f"  status stdout missing 'Backend:'; got:\n{r.stdout!r}")
    if "Traceback" in r.stderr or "Traceback" in r.stdout:
        problems.append("  status printed a traceback")

    # --help works and looks like a help screen (the smoke contract needs 'Usage').
    r = _run(["--help"])
    if r.returncode != 0 or "Usage" not in r.stdout:
        problems.append(
            f"  --help expected exit 0 with 'Usage'; got rc={r.returncode}\n{r.stdout!r}"
        )

    # A full-CLI command still degrades to exit 3 + install hint, no traceback.
    r = _run(["natal"])
    if r.returncode != 3:
        problems.append(f"  natal expected exit 3, got {r.returncode}\n{r.stderr}")
    if "kerykeion[cli]" not in r.stderr:
        problems.append(f"  natal stderr missing the install hint; got:\n{r.stderr!r}")
    if "Traceback" in r.stderr or "Traceback" in r.stdout:
        problems.append("  natal printed a traceback instead of the clean install hint")

    if problems:
        return _fail("wheel-without-extra", "\n".join(problems))
    print("wheel-without-extra OK: status/--version/--help exit 0; full-CLI commands degrade to exit 3")
    return 0


def _smoke_with_extra() -> int:
    """The ``pip install kerykeion[cli]`` path: the CLI is actually functional."""
    rv = _run(["--version"])
    if rv.returncode != 0 or not rv.stdout.strip():
        return _fail("wheel-with-extra --version", f"rc={rv.returncode} out={rv.stdout!r}\n{rv.stderr}")
    rh = _run(["--help"])
    if rh.returncode != 0 or "Usage" not in rh.stdout:
        return _fail("wheel-with-extra --help", f"rc={rh.returncode}\n{rh.stdout}\n{rh.stderr}")

    # ``info`` and ``doctor`` read the installed library rather than the repo, so
    # they are the cheapest proof that the *packaged* CLI can reach it. A wheel
    # that ships the commands but cannot introspect what it installed would pass
    # a --help-only check.
    ri = _run(["info", "literals", "HousesSystemIdentifier", "-f", "json"])
    if ri.returncode != 0 or "HousesSystemIdentifier" not in ri.stdout:
        return _fail("wheel-with-extra info", f"rc={ri.returncode}\n{ri.stdout}\n{ri.stderr}")
    try:
        tables = json.loads(ri.stdout)
    except json.JSONDecodeError as exc:
        return _fail("wheel-with-extra info json", f"{exc}\n{ri.stdout}")
    if not tables.get("HousesSystemIdentifier"):
        return _fail("wheel-with-extra info json", f"empty table: {ri.stdout}")

    # doctor exercises the backend end to end and exits non-zero if the packaged
    # install cannot actually compute.
    rd = _run(["doctor", "-f", "json"])
    if rd.returncode != 0:
        return _fail("wheel-with-extra doctor", f"rc={rd.returncode}\n{rd.stdout}\n{rd.stderr}")

    print(
        f"wheel-with-extra OK: --version ({rv.stdout.strip()}), --help, "
        f"info ({len(tables)} literal tables) and doctor green"
    )
    return 0


def main() -> int:
    cli_present = importlib.util.find_spec("typer") is not None
    # Run whichever half applies to this environment. ``poe build:smoke`` invokes
    # this script in BOTH environments, so both halves get exercised across the
    # two runs.
    return _smoke_with_extra() if cli_present else _smoke_without_extra()


if __name__ == "__main__":
    sys.exit(main())
