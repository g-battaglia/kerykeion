#!/usr/bin/env python3
"""
Kerykeion v6 quickstart — a known-good, offline, end-to-end sanity check.

Run it to confirm the install works and to see the whole
subject -> chart data -> report -> LLM context flow on real output:

    python quickstart.py                # text output only
    python quickstart.py --svg out_dir  # also write an SVG wheel to out_dir/

Everything is offline (online=False with explicit coordinates): no network,
no GeoNames account. To guarantee that, the script forces sealed `leb` mode
before importing kerykeion — otherwise KERYKEION_LEB_MODE=horizons/skyfield
could let the ephemeris backend query Horizons or download DE440 during
subject construction, even with online=False (which only disables GeoNames).
Swap the birth data for your own; keep online=False and always provide
lng/lat/tz_str (plus city/nation for correct display labels).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

# Force sealed mode before the import: the backend reads this at import time.
# Snapshot the caller's value first — overriding it silently would let this
# script report a clean run on an environment where their own `import
# kerykeion` raises ValueError.
_SAVED_LEB_MODE = os.environ.get("KERYKEION_LEB_MODE")
os.environ["KERYKEION_LEB_MODE"] = "leb"

from kerykeion import (
    AstrologicalSubjectFactory,
    BACKEND_NAME,
    ChartDataFactory,
    ChartDrawer,
    ReportGenerator,
    to_context,
)

try:
    # The backend owns the valid-mode list (single source of truth since
    # 6.0.0a85). The literal is only a fallback for version-skewed installs —
    # this skill newer than the installed package — and cannot drift, because
    # every kerykeion that defines the constant imports it right here.
    from kerykeion.ephemeris_backend.backend import VALID_LEB_MODES
except ImportError:
    VALID_LEB_MODES = ("leb", "auto", "skyfield", "horizons")


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def warn_if_leb_mode_overridden() -> None:
    """Say so when this run does not reflect the caller's real configuration.

    Without this, the script prescribed as the install sanity check would
    print a clean bill of health for an environment where the user's own
    `import kerykeion` dies on an invalid KERYKEION_LEB_MODE.
    """
    if _SAVED_LEB_MODE is None or BACKEND_NAME != "libephemeris":
        return
    mode = _SAVED_LEB_MODE.strip().lower()
    if mode == "leb":
        return
    if mode not in VALID_LEB_MODES:
        print(
            f"WARNING: your KERYKEION_LEB_MODE={_SAVED_LEB_MODE!r} is INVALID (valid: "
            f"{', '.join(VALID_LEB_MODES)}).\n         A plain `import kerykeion` raises "
            "ValueError under it;\n         this run only works because the script forces "
            "sealed 'leb' mode."
        )
    else:
        print(
            f"NOTE: run in sealed 'leb' mode, not your {mode!r} mode, so this check "
            "stays offline."
        )


def build_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        name="Example Person",
        year=1990, month=7, day=15, hour=10, minute=30,  # local wall-clock time
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT",  # display labels only; default is Greenwich/GB
        online=False,              # offline: no GeoNames call
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Kerykeion v6 offline quickstart")
    parser.add_argument("--svg", metavar="DIR", help="also render the natal SVG into DIR/")
    args = parser.parse_args()

    warn_if_leb_mode_overridden()
    subject = build_subject()

    # 1) Read positions straight off the subject model
    section("Subject")
    print(f"Sun:  {subject.sun.sign} {subject.sun.position:.2f} deg  (house {subject.sun.house})")
    print(f"Moon: {subject.moon.sign} {subject.moon.position:.2f} deg  element {subject.moon.element}")
    print(f"Asc:  {subject.ascendant.sign} {subject.ascendant.position:.2f} deg")
    print(f"Lunar phase: {subject.lunar_phase.moon_phase_name} {subject.lunar_phase.moon_emoji}")

    # 2) Backend and provenance (populated on libephemeris, None on swisseph)
    section("Backend & provenance")
    print(f"Backend: {BACKEND_NAME}")
    print(f"Sun source: {subject.sun.source}  precision_class: {subject.sun.precision_class}")
    print(f"Ephemeris warnings (omitted optional points): {len(subject.ephemeris_warnings)}")

    # 3) Precompute chart data (needed for SVG, reports, distributions, aspects)
    section("Chart data")
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    elem = chart_data.element_distribution
    print(
        f"Elements: fire={elem.fire} ({elem.fire_percentage}%) "
        f"earth={elem.earth} ({elem.earth_percentage}%) "
        f"air={elem.air} ({elem.air_percentage}%) "
        f"water={elem.water} ({elem.water_percentage}%)"
    )
    print(f"Aspects found: {len(chart_data.aspects)}")

    # 4) Human-readable ASCII report
    section("Report (max 8 aspects)")
    print(ReportGenerator(chart_data).generate_report(max_aspects=8))

    # 5) LLM-ready factual XML (inject into a prompt)
    section("LLM context (truncated)")
    context = to_context(subject)
    print(context[:400] + ("..." if len(context) > 400 else ""))

    # 6) Optional SVG wheel — always ChartDataFactory first, then ChartDrawer
    if args.svg:
        section("SVG")
        out_dir = Path(args.svg)
        out_dir.mkdir(parents=True, exist_ok=True)
        ChartDrawer(chart_data).save_svg(output_path=out_dir, filename="quickstart-natal")
        print(f"SVG written to {(out_dir / 'quickstart-natal.svg').resolve()}")

    print("\nOK — quickstart completed.")


if __name__ == "__main__":
    main()
