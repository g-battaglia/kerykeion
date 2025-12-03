
import sys
import os
from pathlib import Path

# Add the project root to the python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory

def generate_vertical_chart():
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="Albert Einstein",
        year=1879,
        month=3,
        day=14,
        hour=11,
        minute=30,
        city="Ulm",
        nation="DE",
        lng=9.99,
        lat=48.40,
        tz_str="Europe/Berlin",
        suppress_geonames_warning=True
    )

    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    
    # Initialize ChartDrawer with vertical orientation
    chart = ChartDrawer(chart_data, orientation="vertical")
    
    chart.save_svg(output_path=".", filename="chart_vertical_repro")
    output_file = Path("chart_vertical_repro.svg").resolve()
    print(f"Generated chart at: {output_file}")

    # Read the generated file and print the first few lines to check viewBox
    with open(output_file, 'r') as f:
        content = f.read()
        print("\n--- SVG Header ---")
        print(content[:500])
        print("------------------")

if __name__ == "__main__":
    generate_vertical_chart()
