#!/usr/bin/env python3
"""
Kerykeion v6 quickstart — a known-good, offline, end-to-end sanity check.

Run it to confirm the install works and to see the whole
subject -> chart data -> report -> LLM context flow on real output:

    python quickstart.py                # text output only
    python quickstart.py --svg out_dir  # also write an SVG wheel to out_dir/

Everything is offline (online=False with explicit coordinates): no network,
no GeoNames account. Swap the birth data for your own; keep online=False and
always provide lng/lat/tz_str (plus city/nation for correct display labels).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from kerykeion import (
    AstrologicalSubjectFactory,
    BACKEND_NAME,
    ChartDataFactory,
    ChartDrawer,
    ReportGenerator,
    to_context,
)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


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
