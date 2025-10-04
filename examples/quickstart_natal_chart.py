"""Quickstart example for Kerykeion v5: natal chart calculation and SVG export."""
from pathlib import Path

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer


def main() -> None:
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    ada = AstrologicalSubjectFactory.from_birth_data(
        name="Ada Lovelace",
        year=1815,
        month=12,
        day=10,
        hour=4,
        minute=20,
        lng=-0.1246,
        lat=51.5014,
        tz_str="Europe/London",
        city="London",
        nation="GB",
        online=False,
    )

    chart_data = ChartDataFactory.create_natal_chart_data(ada)

    drawer = ChartDrawer(chart_data=chart_data, theme="classic")
    drawer.save_svg(output_path=output_dir, filename="ada_lovelace_natal", minify=True, remove_css_variables=True)

    element_distribution = chart_data.element_distribution
    print(
        "Saved natal chart for Ada Lovelace. Element balance: "
        f"Fire {element_distribution.fire_percentage:.1f}%, "
        f"Earth {element_distribution.earth_percentage:.1f}%, "
        f"Air {element_distribution.air_percentage:.1f}%, "
        f"Water {element_distribution.water_percentage:.1f}%"
    )


if __name__ == "__main__":
    main()
