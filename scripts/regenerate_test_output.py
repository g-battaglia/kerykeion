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
- Extended snapshot matrix     (active points/aspects presets, geographic, temporal)

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
from kerykeion.settings.config_constants import (
    ALL_ACTIVE_ASPECTS,
    ALL_ACTIVE_POINTS,
    DISCEPOLO_SCORE_ACTIVE_ASPECTS,
    TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
)

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


def _natal_subject(**kwargs):
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
        **kwargs,
    )


def _partner_subject(**kwargs):
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
        **kwargs,
    )


def _transit_subject(**kwargs):
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
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Extended subject helpers — geographic diversity
# ---------------------------------------------------------------------------


def _tokyo_subject(**kwargs):
    """Tokyo, Asia — same birth date as geographic matrix (1990-06-15 12:00)."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Tokyo Subject",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=0,
        city="Tokyo",
        nation="JP",
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
        **kwargs,
    )


def _buenos_aires_subject(**kwargs):
    """Buenos Aires, Southern hemisphere (1990-06-15 12:00)."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Buenos Aires Subject",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=0,
        city="Buenos Aires",
        nation="AR",
        lat=-34.6037,
        lng=-58.3816,
        tz_str="America/Argentina/Buenos_Aires",
        online=False,
        **kwargs,
    )


def _quito_subject(**kwargs):
    """Quito, Equator (1990-06-15 12:00)."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Quito Subject",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=0,
        city="Quito",
        nation="EC",
        lat=0.1807,
        lng=-78.4678,
        tz_str="America/Guayaquil",
        online=False,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Extended subject helpers — temporal diversity
# ---------------------------------------------------------------------------


def _ancient_rome_subject(**kwargs):
    """Rome, 100 AD."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Ancient Rome Subject",
        year=100,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=41.9028,
        lng=12.4964,
        tz_str="Europe/Rome",
        online=False,
        suppress_geonames_warning=True,
        **kwargs,
    )


def _einstein_subject(**kwargs):
    """Einstein birth — Ulm, 1879."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Einstein Subject",
        year=1879,
        month=3,
        day=14,
        hour=11,
        minute=30,
        city="Ulm",
        nation="DE",
        lat=48.4011,
        lng=9.9876,
        tz_str="Europe/Berlin",
        online=False,
        **kwargs,
    )


def _future_2050_subject(**kwargs):
    """Tokyo, 2050."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Future 2050 Subject",
        year=2050,
        month=7,
        day=20,
        hour=12,
        minute=0,
        city="Tokyo",
        nation="JP",
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
        **kwargs,
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


# ===========================================================================
# Extended snapshots — active points presets (base Liverpool subject)
# ===========================================================================


def regenerate_natal_traditional_points():
    """Natal chart with TRADITIONAL_ASTROLOGY_ACTIVE_POINTS (9 points)."""
    subject = _natal_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_traditional_points_report.txt",
    )


def regenerate_natal_all_points():
    """Natal chart with ALL_ACTIVE_POINTS (32 points)."""
    subject = _natal_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_all_points_report.txt",
    )


def regenerate_natal_all_points_all_aspects():
    """Natal chart with ALL points + ALL aspects."""
    subject = _natal_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=ALL_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_all_points_all_aspects_report.txt",
    )


# ===========================================================================
# Extended snapshots — active aspects presets (base Liverpool subject)
# ===========================================================================


def regenerate_natal_all_aspects():
    """Natal chart with default points + ALL_ACTIVE_ASPECTS (11 aspects)."""
    subject = _natal_subject()
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=ALL_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_all_aspects_report.txt",
    )


def regenerate_natal_discepolo_aspects():
    """Natal chart with default points + DISCEPOLO_SCORE_ACTIVE_ASPECTS (8 aspects)."""
    subject = _natal_subject()
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=DISCEPOLO_SCORE_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_discepolo_aspects_report.txt",
    )


# ===========================================================================
# Extended snapshots — geographic diversity (ALL points + ALL aspects)
# ===========================================================================


def regenerate_natal_tokyo():
    """Natal chart — Tokyo (Asia), ALL points + ALL aspects."""
    subject = _tokyo_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=ALL_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_tokyo_all_report.txt",
    )


def regenerate_natal_buenos_aires():
    """Natal chart — Buenos Aires (Southern hemisphere), ALL points + ALL aspects."""
    subject = _buenos_aires_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=ALL_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_buenos_aires_all_report.txt",
    )


def regenerate_natal_quito():
    """Natal chart — Quito (Equator), ALL points + ALL aspects."""
    subject = _quito_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=ALL_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_quito_all_report.txt",
    )


# ===========================================================================
# Extended snapshots — temporal diversity (ALL points + ALL aspects)
# ===========================================================================


def regenerate_natal_ancient_rome():
    """Natal chart — Rome 100 AD, ALL points + ALL aspects."""
    subject = _ancient_rome_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=ALL_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_ancient_rome_all_report.txt",
    )


def regenerate_natal_einstein():
    """Natal chart — Einstein (Ulm 1879), ALL points + ALL aspects."""
    subject = _einstein_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=ALL_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_einstein_all_report.txt",
    )


def regenerate_natal_future_2050():
    """Natal chart — Tokyo 2050, ALL points + ALL aspects."""
    subject = _future_2050_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_natal_chart_data(subject, active_aspects=ALL_ACTIVE_ASPECTS)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "natal_future_2050_all_report.txt",
    )


# ===========================================================================
# Extended snapshots — synastry with configuration presets
# ===========================================================================


def regenerate_synastry_traditional_points():
    """Synastry with TRADITIONAL points."""
    natal = _natal_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
    partner = _partner_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
    chart = ChartDataFactory.create_synastry_chart_data(natal, partner)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "synastry_traditional_points_report.txt",
    )


def regenerate_synastry_all_points_all_aspects():
    """Synastry with ALL points + ALL aspects."""
    natal = _natal_subject(active_points=ALL_ACTIVE_POINTS)
    partner = _partner_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_synastry_chart_data(
        natal,
        partner,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "synastry_all_points_all_aspects_report.txt",
    )


# ===========================================================================
# Extended snapshots — transit with configuration presets
# ===========================================================================


def regenerate_transit_traditional_points():
    """Transit with TRADITIONAL points."""
    natal = _natal_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
    transit = _transit_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
    chart = ChartDataFactory.create_transit_chart_data(natal, transit)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "transit_traditional_points_report.txt",
    )


def regenerate_transit_all_points_all_aspects():
    """Transit with ALL points + ALL aspects."""
    natal = _natal_subject(active_points=ALL_ACTIVE_POINTS)
    transit = _transit_subject(active_points=ALL_ACTIVE_POINTS)
    chart = ChartDataFactory.create_transit_chart_data(
        natal,
        transit,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "transit_all_points_all_aspects_report.txt",
    )


# ===========================================================================
# Extended snapshots — composite with configuration presets
# ===========================================================================


def regenerate_composite_traditional_points():
    """Composite with TRADITIONAL points."""
    natal = _natal_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
    partner = _partner_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
    composite_subject = CompositeSubjectFactory(
        natal,
        partner,
        chart_name="John & Yoko Composite Chart",
    ).get_midpoint_composite_subject_model()
    chart = ChartDataFactory.create_composite_chart_data(composite_subject)
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "composite_traditional_points_report.txt",
    )


def regenerate_composite_all_points_all_aspects():
    """Composite with ALL points + ALL aspects."""
    natal = _natal_subject(active_points=ALL_ACTIVE_POINTS)
    partner = _partner_subject(active_points=ALL_ACTIVE_POINTS)
    composite_subject = CompositeSubjectFactory(
        natal,
        partner,
        chart_name="John & Yoko Composite Chart",
    ).get_midpoint_composite_subject_model()
    chart = ChartDataFactory.create_composite_chart_data(
        composite_subject,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "composite_all_points_all_aspects_report.txt",
    )


# ===========================================================================
# Extended snapshots — return with configuration presets
# ===========================================================================


def regenerate_solar_return_all_points():
    """Single-wheel solar return with ALL points."""
    natal = _natal_subject(active_points=ALL_ACTIVE_POINTS)
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
    chart = ChartDataFactory.create_single_wheel_return_chart_data(
        solar_return,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "solar_return_all_points_report.txt",
    )


def regenerate_dual_return_all_points_all_aspects():
    """Dual-wheel return with ALL points + ALL aspects."""
    natal = _natal_subject(active_points=ALL_ACTIVE_POINTS)
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
    chart = ChartDataFactory.create_return_chart_data(
        natal,
        solar_return,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    _capture_and_save(
        ReportGenerator(chart),
        FIXTURES_DIR / "dual_return_all_points_all_aspects_report.txt",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Original snapshots ---
    regenerate_report()
    regenerate_synastry_report()
    regenerate_transit_report()
    regenerate_composite_report()
    regenerate_solar_return_report()
    regenerate_dual_return_report()

    # --- Extended: active points presets (natal, Liverpool) ---
    regenerate_natal_traditional_points()
    regenerate_natal_all_points()
    regenerate_natal_all_points_all_aspects()

    # --- Extended: active aspects presets (natal, Liverpool) ---
    regenerate_natal_all_aspects()
    regenerate_natal_discepolo_aspects()

    # --- Extended: geographic diversity (natal, ALL+ALL) ---
    regenerate_natal_tokyo()
    regenerate_natal_buenos_aires()
    regenerate_natal_quito()

    # --- Extended: temporal diversity (natal, ALL+ALL) ---
    regenerate_natal_ancient_rome()
    regenerate_natal_einstein()
    regenerate_natal_future_2050()

    # --- Extended: synastry ---
    regenerate_synastry_traditional_points()
    regenerate_synastry_all_points_all_aspects()

    # --- Extended: transit ---
    regenerate_transit_traditional_points()
    regenerate_transit_all_points_all_aspects()

    # --- Extended: composite ---
    regenerate_composite_traditional_points()
    regenerate_composite_all_points_all_aspects()

    # --- Extended: return ---
    regenerate_solar_return_all_points()
    regenerate_dual_return_all_points_all_aspects()
