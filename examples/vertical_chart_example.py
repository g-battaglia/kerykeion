"""
Example script demonstrating vertical chart generation with Kerykeion.

This script creates a natal chart in vertical A4 portrait orientation (794×1123px).
The vertical format is suitable for printing on A4 paper in portrait mode.
"""

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from pathlib import Path

def main():
    """Generate a vertical natal chart and save it as SVG."""
    
    # Create astrological subject
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        city="Liverpool",
        nation="GB"
    )
    
    # Generate chart data
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    
    # Create vertical chart drawer with A4 portrait orientation
    vertical_chart = ChartDrawer(
        chart_data=chart_data,
        theme="classic",
        orientation="vertical"  # This generates A4 portrait layout (794×1123px)
    )
    
    # Save vertical chart
    output_path = Path.home() / "kerykeion_vertical_chart.svg"
    vertical_chart.save_svg(output_path.parent, output_path.stem)
    
    print(f"✅ Vertical chart saved to: {output_path}")
    print(f"📐 Dimensions: {vertical_chart.width}×{vertical_chart.height}px (A4 portrait)")
    
    # For comparison, create a horizontal chart
    horizontal_chart = ChartDrawer(
        chart_data=chart_data,
        theme="classic",
        orientation="horizontal"  # Default horizontal layout
    )
    
    output_path_h = Path.home() / "kerykeion_horizontal_chart.svg"
    horizontal_chart.save_svg(output_path_h.parent, output_path_h.stem)
    
    print(f"✅ Horizontal chart saved to: {output_path_h}")
    print(f"📐 Dimensions: {horizontal_chart.width}×{horizontal_chart.height}px (landscape)")

if __name__ == "__main__":
    main()
