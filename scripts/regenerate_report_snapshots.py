#!/usr/bin/env python3
"""
Regenerate golden-file report snapshots for tests/core/ report tests.

This script generates all report snapshot files used by test_report.py
in the core test suite. It creates snapshots for:
- Natal reports (all canonical subjects)
- Synastry reports (John + Yoko)
- Composite reports (John + Yoko)
- Solar return reports (Johnny Depp)
- Transit reports (Johnny Depp)
- Moon phase overview reports

Run via:  poe regenerate:report-snapshots
"""

import sys
from pathlib import Path
from io import StringIO

# Add the project root to the python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.report import ReportGenerator
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

FIXTURES_DIR = project_root / "tests" / "fixtures"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _capture_and_save(report_gen, output_path):
    """Capture print_report() output and persist it."""
    capture_buffer = StringIO()
    original_stdout = sys.stdout
    sys.stdout = capture_buffer

    try:
        report_gen.print_report()
    finally:
        sys.stdout = original_stdout

    output = capture_buffer.getvalue()
    # Strip trailing newline for fixture comparison convention
    if output.endswith("\n"):
        output = output[:-1]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    print(f"  Written: {output_path.relative_to(project_root)}")


# ---------------------------------------------------------------------------
# Canonical subjects (offline, explicit coordinates)
# ---------------------------------------------------------------------------


def _johnny_depp():
    return AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp",
        1963,
        6,
        9,
        0,
        0,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
    )


def _john_lennon():
    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


def _yoko_ono():
    return AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono",
        1933,
        2,
        18,
        20,
        30,
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
        suppress_geonames_warning=True,
    )


def _paul_mccartney():
    return AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney",
        1942,
        6,
        18,
        14,
        0,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("Regenerating report snapshots...")
    print(f"Output directory: {FIXTURES_DIR}")

    johnny = _johnny_depp()
    john = _john_lennon()
    yoko = _yoko_ono()
    paul = _paul_mccartney()

    # --- Natal reports ---
    print("\n[Natal Reports]")
    for name, subject in [("Johnny Depp", johnny), ("John Lennon", john), ("Yoko Ono", yoko)]:
        # Default (no aspects)
        report_gen = ReportGenerator(subject)
        safe_name = name.lower().replace(" ", "_")
        _capture_and_save(report_gen, FIXTURES_DIR / f"natal_{safe_name}_subject_report.txt")

        # With natal chart data (includes aspects)
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        report_gen = ReportGenerator(chart_data)
        _capture_and_save(report_gen, FIXTURES_DIR / f"natal_{safe_name}_chart_report.txt")

    # --- Synastry report ---
    print("\n[Synastry Reports]")
    synastry_data = ChartDataFactory.create_synastry_chart_data(john, yoko)
    report_gen = ReportGenerator(synastry_data)
    _capture_and_save(report_gen, FIXTURES_DIR / "synastry_john_yoko_report.txt")

    # --- Composite report ---
    print("\n[Composite Reports]")
    composite_factory = CompositeSubjectFactory(john, yoko)
    composite_subject = composite_factory.get_midpoint_composite_subject_model()
    composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)
    report_gen = ReportGenerator(composite_data)
    _capture_and_save(report_gen, FIXTURES_DIR / "composite_john_yoko_report.txt")

    # --- Solar return report ---
    print("\n[Solar Return Reports]")
    solar_factory = PlanetaryReturnFactory(
        johnny,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
    )
    solar_return = solar_factory.next_return_from_date(year=2024, month=1, day=1, return_type="Solar")
    solar_data = ChartDataFactory.create_return_chart_data(johnny, solar_return)
    report_gen = ReportGenerator(solar_data)
    _capture_and_save(report_gen, FIXTURES_DIR / "solar_return_johnny_depp_report.txt")

    # --- Transit report ---
    print("\n[Transit Reports]")
    transit_data = ChartDataFactory.create_transit_chart_data(johnny, john)
    report_gen = ReportGenerator(transit_data)
    _capture_and_save(report_gen, FIXTURES_DIR / "transit_johnny_depp_report.txt")

    print("\nDone! All report snapshots regenerated.")


if __name__ == "__main__":
    main()
