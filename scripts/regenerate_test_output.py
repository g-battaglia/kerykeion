#!/usr/bin/env python3
"""
Script to regenerate the expected output fixtures for report snapshot tests.

Generates golden files for:
- Natal chart report          (existing)
- Synastry chart report       (new)
- Transit chart report        (new)
- Composite chart report      (new)
- Solar return chart report   (new)
- Dual return chart report    (new)

Run via:  poe regenerate:output
"""

import sys
from pathlib import Path
from io import StringIO

# Add the project root to the python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

FIXTURES_DIR = project_root / "tests" / "fixtures"


# ---------------------------------------------------------------------------
# Helper: capture print_report() output and save to fixture file
# ---------------------------------------------------------------------------


def _capture_and_save(report_gen, output_path):
    """Capture the stdout output of ``report_gen.print_report()`` and persist it.

    The test convention is::

        captured = capsys.readouterr().out          # includes trailing newline from print()
        expected = Path(...).read_text(encoding="utf-8")
        assert captured == expected + "\\n"

    So we strip the final newline before saving.
    """
    capture_buffer = StringIO()
    original_stdout = sys.stdout
    sys.stdout = capture_buffer

    try:
        report_gen.print_report()
    finally:
        sys.stdout = original_stdout

    output = capture_buffer.getvalue()
    content_to_save = output[:-1] if output.endswith("\n") else output

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content_to_save, encoding="utf-8")
    print(f"Regenerated {output_path}")


# ---------------------------------------------------------------------------
# Shared subjects — mirrors the report.py __main__ block
# ---------------------------------------------------------------------------


def _natal_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        name="Sample Natal Subject",
        year=1990,
        month=7,
        day=21,
        hour=14,
        minute=45,
        city="Liverpool",
        nation="GB",
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
    )


def _partner_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        name="Yoko Ono",
        year=1933,
        month=2,
        day=18,
        hour=20,
        minute=30,
        city="Tokyo",
        nation="JP",
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
    )


def _transit_subject():
    return AstrologicalSubjectFactory.from_birth_data(
        name="1980 Transit",
        year=1980,
        month=12,
        day=8,
        hour=22,
        minute=50,
        city="New York",
        nation="US",
        lat=40.7128,
        lng=-74.0060,
        tz_str="America/New_York",
        online=False,
    )


# ---------------------------------------------------------------------------
# Regeneration functions
# ---------------------------------------------------------------------------


def regenerate_report():
    """Natal chart snapshot (existing — New Moon Test)."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "New Moon - Test",
        2025,
        11,
        20,
        1,
        46,
        lng=-79.99589,
        lat=40.44062,
        tz_str="America/New_York",
        online=False,
    )
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    _capture_and_save(
        ReportGenerator(chart_data),
        FIXTURES_DIR / "new_moon_test_natal_report.txt",
    )


def regenerate_synastry_report():
    """Synastry chart snapshot."""
    natal = _natal_subject()
    partner = _partner_subject()
    chart_data = ChartDataFactory.create_synastry_chart_data(natal, partner)
    _capture_and_save(
        ReportGenerator(chart_data),
        FIXTURES_DIR / "synastry_report.txt",
    )


def regenerate_transit_report():
    """Transit chart snapshot."""
    natal = _natal_subject()
    transit = _transit_subject()
    chart_data = ChartDataFactory.create_transit_chart_data(natal, transit)
    _capture_and_save(
        ReportGenerator(chart_data),
        FIXTURES_DIR / "transit_report.txt",
    )


def regenerate_composite_report():
    """Composite chart snapshot."""
    natal = _natal_subject()
    partner = _partner_subject()
    composite_subject = CompositeSubjectFactory(
        natal,
        partner,
        chart_name="John & Yoko Composite Chart",
    ).get_midpoint_composite_subject_model()
    chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
    _capture_and_save(
        ReportGenerator(chart_data),
        FIXTURES_DIR / "composite_report.txt",
    )


def regenerate_solar_return_report():
    """Single-wheel solar return chart snapshot."""
    natal = _natal_subject()
    factory = PlanetaryReturnFactory(
        natal,
        city=natal.city,
        nation=natal.nation,
        lat=natal.lat,
        lng=natal.lng,
        tz_str=natal.tz_str,
        online=False,
    )
    solar_return = factory.next_return_from_iso_formatted_time(
        natal.iso_formatted_local_datetime,
        "Solar",
    )
    chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
    _capture_and_save(
        ReportGenerator(chart_data),
        FIXTURES_DIR / "solar_return_report.txt",
    )


def regenerate_dual_return_report():
    """Dual-wheel return chart snapshot (natal vs solar return)."""
    natal = _natal_subject()
    factory = PlanetaryReturnFactory(
        natal,
        city=natal.city,
        nation=natal.nation,
        lat=natal.lat,
        lng=natal.lng,
        tz_str=natal.tz_str,
        online=False,
    )
    solar_return = factory.next_return_from_iso_formatted_time(
        natal.iso_formatted_local_datetime,
        "Solar",
    )
    chart_data = ChartDataFactory.create_return_chart_data(natal, solar_return)
    _capture_and_save(
        ReportGenerator(chart_data),
        FIXTURES_DIR / "dual_return_report.txt",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    regenerate_report()
    regenerate_synastry_report()
    regenerate_transit_report()
    regenerate_composite_report()
    regenerate_solar_return_report()
    regenerate_dual_return_report()
