"""
Kerykeion Workspace - Quick Start Template

This file serves as a starting point for your personal experiments with Kerykeion.
Feel free to modify, extend, or completely replace this code with your own.

For more examples, check:
- examples/ directory in the repository
- Documentation: https://kerykeion.readthedocs.io
- README.md in this workspace folder
"""

from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer


def main() -> None:
    """
    Quick example: Create a natal chart and print some basic information.

    Modify this function to suit your needs!
    """

    # Create an astrological subject
    # Replace with your own birth data or use this as a template
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="Example Person",
        year=1990,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lng=-0.1276,  # London coordinates
        lat=51.5072,
        tz_str="Europe/London",
        city="London",
        nation="GB",
        online=False,  # Set to True to use GeoNames for city lookup
    )

    # Print some basic information
    print(f"Subject: {subject.name}")
    print(f"Birth: {subject.iso_formatted_local_datetime}")
    print(f"Location: {subject.city}, {subject.nation}")
    print(f"\nSun: {subject.sun.sign} at {subject.sun.position:.2f}°")
    print(f"Moon: {subject.moon.sign} at {subject.moon.position:.2f}°")
    print(f"Ascendant: {subject.first_house.sign} at {subject.first_house.position:.2f}°")

    # Create chart data
    chart_data = ChartDataFactory.create_natal_chart_data(subject)

    # Display element distribution
    elements = chart_data.element_distribution
    print("\nElement Distribution:")
    print(f"  Fire: {elements.fire_percentage:.1f}%")
    print(f"  Earth: {elements.earth_percentage:.1f}%")
    print(f"  Air: {elements.air_percentage:.1f}%")
    print(f"  Water: {elements.water_percentage:.1f}%")

    # Generate and save SVG chart
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    drawer = ChartDrawer(chart_data=chart_data, theme="classic")
    drawer.save_svg(
        output_path=output_dir,
        filename="example_chart",
        minify=True
    )

    print(f"\n✓ Chart saved to: {output_dir / 'example_chart.svg'}")
    print("\nModify this script to explore Kerykeion's features!")


if __name__ == "__main__":
    main()
