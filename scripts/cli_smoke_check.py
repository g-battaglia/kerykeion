#!/usr/bin/env python3
"""Smoke-check the kerykeion CLI in the development environment.

Complements ``scripts/build_smoke_check_cli.py``: that one proves the BUILT
WHEELS behave in a clean room; this one proves the live entry point still works
from the repo checkout, that the two distributions agree on a version, and that
``import kerykeion`` never imports the CLI. Run by ``poe cli:smoke``. Exits
non-zero on any failure.
"""

from __future__ import annotations

import subprocess
import sys
from importlib.metadata import entry_points, version


def _fail(label: str, detail: str) -> None:
    print(f"FAIL: {label}\n{detail}")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    # ``python -m kerykeion_cli`` is the same code path as the ``kerykeion``
    # console script (both reach ``kerykeion_cli.main``), and it does not depend
    # on the console script being on $PATH.
    return subprocess.run([sys.executable, "-m", "kerykeion_cli", *args], capture_output=True, text=True, check=False)


def main() -> int:
    failures = 0
    want = version("kerykeion-cli")

    # 0. One version, two wheels: the CLI is released with the library it pins.
    library = version("kerykeion")
    if want != library:
        _fail("version pair", f"kerykeion-cli {want} against kerykeion {library}")
        failures += 1

    # 1. The library never imports the CLI: ``import kerykeion`` stays free of it.
    r = subprocess.run(
        [sys.executable, "-c", "import kerykeion, sys; assert 'kerykeion_cli' not in sys.modules, 'cli auto-imported'"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        _fail("bare kerykeion import pulled the CLI", r.stderr or r.stdout)
        failures += 1

    # 2. The console_scripts entry point is registered and points at main.
    eps = [e for e in entry_points(group="console_scripts") if e.name == "kerykeion"]
    if not eps or eps[0].value != "kerykeion_cli:main":
        _fail("entry point", f"console_scripts kerykeion missing/wrong: {eps!r}")
        failures += 1

    # 3. ``--version`` prints exactly the installed version.
    r = _run(["--version"])
    if r.returncode != 0 or r.stdout.strip() != want:
        _fail("--version", f"rc={r.returncode} out={r.stdout!r} want={want!r}\n{r.stderr}")
        failures += 1

    # 4. ``--help`` and a bare ``kerykeion`` show the help screen and exit 0.
    for args in (["--help"], []):
        r = _run(args)
        if r.returncode != 0 or "usage" not in r.stdout.lower():
            _fail(" ".join(args) or "bare", f"rc={r.returncode}\n{r.stdout}\n{r.stderr}")
            failures += 1

    if failures:
        print(f"cli smoke: {failures} failure(s)")
        return 1
    print(f"cli smoke OK: kerykeion {want} (--version, --help, bare, entry point, library import isolation)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
