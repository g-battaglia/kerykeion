#!/usr/bin/env python
"""
Script to test vertical orientation for all chart types.
This helps identify layout issues with the vertical A4 portrait template.
"""

from pathlib import Path
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory


OUTPUT_DIR = Path("vertical_test_charts")
OUTPUT_DIR.mkdir(exist_ok=True)


def create_test_subjects():
    """Create test subjects for different chart types."""
    subject1 = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940, month=10, day=9,
        hour=18, minute=30,
        city="Liverpool", nation="GB",
        suppress_geonames_warning=True
    )
    
    subject2 = AstrologicalSubjectFactory.from_birth_data(
        name="Paul McCartney",
        year=1942, month=6, day=18,
        hour=15, minute=30,
        city="Liverpool", nation="GB",
        suppress_geonames_warning=True
    )
    
    return subject1, subject2


def test_natal_chart_vertical():
    """Test Natal chart in vertical orientation."""
    subject1, _ = create_test_subjects()
    chart_data = ChartDataFactory.create_natal_chart_data(subject1)
    
    # Horizontal (baseline)
    chart_h = ChartDrawer(chart_data, orientation="horizontal")
    chart_h.save_svg(output_path=str(OUTPUT_DIR), filename="natal_horizontal")
    
    # Vertical
    chart_v = ChartDrawer(chart_data, orientation="vertical")
    chart_v.save_svg(output_path=str(OUTPUT_DIR), filename="natal_vertical")
    
    print("✅ Natal Chart generated")


def test_transit_chart_vertical():
    """Test Transit chart in vertical orientation."""
    subject1, subject2 = create_test_subjects()
    chart_data = ChartDataFactory.create_transit_chart_data(subject1, subject2)
    
    # Horizontal (baseline)
    chart_h = ChartDrawer(chart_data, orientation="horizontal")
    chart_h.save_svg(output_path=str(OUTPUT_DIR), filename="transit_horizontal")
    
    # Vertical - with aspect list for better vertical layout
    try:
        chart_v = ChartDrawer(
            chart_data, 
            orientation="vertical",
            double_chart_aspect_grid_type="list"
        )
        chart_v.save_svg(output_path=str(OUTPUT_DIR), filename="transit_vertical")
        print("✅ Transit Chart generated")
    except Exception as e:
        print(f"❌ Transit Chart vertical failed: {e}")


def test_synastry_chart_vertical():
    """Test Synastry chart in vertical orientation."""
    subject1, subject2 = create_test_subjects()
    chart_data = ChartDataFactory.create_synastry_chart_data(subject1, subject2)
    
    # Horizontal (baseline)
    chart_h = ChartDrawer(chart_data, orientation="horizontal")
    chart_h.save_svg(output_path=str(OUTPUT_DIR), filename="synastry_horizontal")
    
    # Vertical - with aspect list for better vertical layout
    try:
        chart_v = ChartDrawer(
            chart_data, 
            orientation="vertical",
            double_chart_aspect_grid_type="list"
        )
        chart_v.save_svg(output_path=str(OUTPUT_DIR), filename="synastry_vertical")
        print("✅ Synastry Chart generated")
    except Exception as e:
        print(f"❌ Synastry Chart vertical failed: {e}")


def test_composite_chart_vertical():
    """Test Composite chart in vertical orientation."""
    subject1, subject2 = create_test_subjects()
    
    factory = CompositeSubjectFactory(subject1, subject2)
    composite_subject = factory.get_midpoint_composite_subject_model()
    chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
    
    # Horizontal (baseline)
    chart_h = ChartDrawer(chart_data, orientation="horizontal")
    chart_h.save_svg(output_path=str(OUTPUT_DIR), filename="composite_horizontal")
    
    # Vertical
    try:
        chart_v = ChartDrawer(chart_data, orientation="vertical")
        chart_v.save_svg(output_path=str(OUTPUT_DIR), filename="composite_vertical")
        print("✅ Composite Chart generated")
    except Exception as e:
        print(f"❌ Composite Chart vertical failed: {e}")


def test_solar_return_chart_vertical():
    """Test Solar Return chart in vertical orientation."""
    subject1, _ = create_test_subjects()
    
    return_factory = PlanetaryReturnFactory(
        subject1,
        lng=-2.9833, lat=53.4000,
        tz_str="Europe/London",
        online=False,
    )
    
    solar_return = return_factory.next_return_from_iso_formatted_time(
        "2025-01-09T18:30:00+01:00",
        return_type="Solar",
    )
    
    chart_data = ChartDataFactory.create_return_chart_data(subject1, solar_return)
    
    # Horizontal (baseline)
    chart_h = ChartDrawer(chart_data, orientation="horizontal")
    chart_h.save_svg(output_path=str(OUTPUT_DIR), filename="solar_return_horizontal")
    
    # Vertical
    try:
        chart_v = ChartDrawer(chart_data, orientation="vertical")
        chart_v.save_svg(output_path=str(OUTPUT_DIR), filename="solar_return_vertical")
        print("✅ Solar Return Chart generated")
    except Exception as e:
        print(f"❌ Solar Return Chart vertical failed: {e}")


if __name__ == "__main__":
    print("Testing vertical orientation for all chart types...")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")
    print("-" * 50)
    
    test_natal_chart_vertical()
    test_transit_chart_vertical()
    test_synastry_chart_vertical()
    test_composite_chart_vertical()
    test_solar_return_chart_vertical()
    
    print("-" * 50)
    print(f"Generated charts in: {OUTPUT_DIR.resolve()}")
    print("Please compare horizontal vs vertical versions to identify issues.")
