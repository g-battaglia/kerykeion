#!/usr/bin/env python3
"""
Kerykeion environment diagnostic. Run when dates raise, the active backend is
unclear, or before filing a bug. Prints versions, the five KERYKEION_* env
vars, and probes ephemeris coverage with throwaway offline subjects. It never
downloads anything and always exits 0 — it is a report, not a gate.
"""
from __future__ import annotations

import os
import sys

ENV_VARS = (
    "KERYKEION_BACKEND",
    "KERYKEION_LEB_MODE",
    "KERYKEION_EPHE_PATH",
    "KERYKEION_GEONAMES_USERNAME",
    "KERYKEION_GEONAMES_CACHE_NAME",
)

# Report the caller's real environment, but run every probe in sealed `leb`
# mode: in `auto`/`skyfield`/`horizons` the backend may download DE440 data or
# query JPL Horizons for an out-of-coverage date, and this diagnostic promises
# to never touch the network. The override must happen before the import —
# the backend reads the variable at import time.
REPORTED_ENV = {name: os.environ.get(name) for name in ENV_VARS}
os.environ["KERYKEION_LEB_MODE"] = "leb"


# backend.py reads KERYKEION_LEB_MODE as `.strip().lower()` and only validates
# it when the resolved backend is libephemeris; swisseph ignores the variable.


def report_environment() -> None:
    print("=== Kerykeion environment report ===")
    print(f"Python:    {sys.version.split()[0]}")
    print("\n--- Environment variables ---")
    for name in ENV_VARS:
        value = REPORTED_ENV[name]
        # An empty string is NOT the same as absent: backend.py defaults only a
        # missing key, so KERYKEION_LEB_MODE='' reaches validation and kills the
        # import. Printing it as "unset" would hide the actual culprit.
        print(f"{name} = {'unset' if value is None else repr(value)}")


def saved_leb_mode() -> str:
    """The caller's effective LEB mode, normalized the way backend.py does."""
    saved = REPORTED_ENV["KERYKEION_LEB_MODE"]
    return "leb" if saved is None else saved.strip().lower()


def report_leb_mode_substitution() -> None:
    """Explain how the forced sealed mode relates to the caller's real one.

    Called after import, so BACKEND_NAME is known. The backend normalizes the
    value (`.strip().lower()`) and validates it exclusively for libephemeris,
    so `"AUTO"`/`" auto "` are valid and swisseph never rejects the variable.
    Both branches matter: an INVALID value means the user's own import is
    broken even though the probes below pass, while a VALID non-default value
    means the probes describe a stricter configuration than the user runs.
    """
    if BACKEND_NAME != "libephemeris":
        return
    mode = saved_leb_mode()
    if mode not in VALID_LEB_MODES:
        raw = REPORTED_ENV["KERYKEION_LEB_MODE"]
        print(
            f"\nWARNING: KERYKEION_LEB_MODE={raw!r} is INVALID (valid: "
            f"{', '.join(VALID_LEB_MODES)}).\n         A normal `import kerykeion` "
            "raises ValueError under this setting; the probes\n         below only "
            "succeed because this diagnostic forces sealed 'leb' mode."
        )
    elif mode != "leb":
        print(
            f"\nNOTE: your KERYKEION_LEB_MODE is {mode!r}, but the probes below run in "
            "sealed\n      'leb' mode so this diagnostic never touches the network. Your "
            "real\n      configuration may resolve dates that the probes report as FAIL."
        )


# A broken configuration (e.g. an invalid KERYKEION_BACKEND, or a backend
# package that is missing) raises at import time — exactly the scenario this
# diagnostic exists for, so report it instead of crashing.
try:
    import kerykeion
    from kerykeion import AstrologicalSubjectFactory, BACKEND_NAME
except Exception as exc:
    report_environment()
    print("\n--- Import failed ---")
    print(f"{type(exc).__name__}: {str(exc)[:300]}")
    print("kerykeion could not be imported under this configuration; fix the")
    print("environment above (KERYKEION_BACKEND is the usual culprit) and re-run.")
    sys.exit(0)

try:
    # The backend owns the valid-mode list (single source of truth since
    # 6.0.0a85). The literal is only a fallback for version-skewed installs —
    # this skill newer than the installed package — and cannot drift, because
    # every kerykeion that defines the constant imports it right here.
    from kerykeion.ephemeris_backend.backend import VALID_LEB_MODES
except ImportError:
    VALID_LEB_MODES = ("leb", "auto", "skyfield", "horizons")


def probe(year: int) -> tuple[bool, str]:
    """Build a minimal throwaway subject (Greenwich, offline) for `year`."""
    try:
        subject = AstrologicalSubjectFactory.from_birth_data(
            name=f"probe-{year}",
            year=year, month=6, day=15, hour=12, minute=0,
            lng=0.0, lat=51.4769, tz_str="UTC",
            city="Greenwich", nation="GB", online=False,
        )
        detail = f"Sun {subject.sun.sign} {subject.sun.position:.2f} (source={subject.sun.source})"
        return True, detail
    except Exception as exc:  # report, don't gate
        message = str(exc).replace("\n", " ")
        if len(message) > 140:
            message = message[:140] + "..."
        return False, f"{type(exc).__name__}: {message}"


def main() -> None:
    report_environment()
    print(f"\nkerykeion: {kerykeion.__version__}")
    print(f"Backend:   {BACKEND_NAME}")
    report_leb_mode_substitution()

    # A fresh install ships the 1849-2150 LEB kernel. On libephemeris the probes
    # run in sealed `leb` mode (forced above) so out-of-coverage dates RAISE
    # instead of triggering a download; swisseph ignores the LEB mode and reads
    # its own .se1 files (or the Moshier fallback).
    engine = "sealed leb mode" if BACKEND_NAME == "libephemeris" else "swisseph .se1 / Moshier"
    print(f"\n--- Ephemeris coverage probes (offline, {engine}, Greenwich) ---")
    for year in (1850, 2024, 2149):
        ok, detail = probe(year)
        print(f"year {year}: {'OK  ' if ok else 'FAIL'} {detail}")

    print("\n--- Extended-coverage probe (year 1600) ---")
    ok, detail = probe(1600)
    if ok:
        print(f"year 1600: OK   {detail}")
        if BACKEND_NAME == "libephemeris":
            print("A wider LEB tier (medium/extended) is installed.")
        else:
            print("Computed by the swisseph backend (LEB tiers do not apply).")
    else:
        print(f"year 1600: FAIL {detail}")
        if BACKEND_NAME != "libephemeris":
            print("The swisseph backend cannot compute year 1600 with its current data files.")
        elif saved_leb_mode() == "leb":
            print("Expected on a default install (1849-2150 kernel). To widen coverage:")
            print('  python -c "import libephemeris; libephemeris.download_leb_for_tier(\'medium\')"')
        else:
            # Their real mode (auto/skyfield/horizons) may well resolve 1600 via
            # Skyfield or Horizons; recommending a tier download would be wrong.
            print(
                f"This probe ran in sealed 'leb' mode, not your {saved_leb_mode()!r} mode — "
                "it means the\ninstalled LEB kernel does not cover 1600, NOT that your "
                "configuration fails there."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
