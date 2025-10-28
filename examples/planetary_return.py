"""Solar return calculation and visualization with Kerykeion v5."""
from pathlib import Path

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    PlanetaryReturnFactory,
)


def main() -> None:
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    natal = AstrologicalSubjectFactory.from_birth_data(
        name="Grace Hopper",
        year=1906,
        month=12,
        day=9,
        hour=11,
        minute=30,
        lng=-73.9857,
        lat=40.7484,
        tz_str="America/New_York",
        city="New York",
        nation="US",
        online=False,
    )

    factory = PlanetaryReturnFactory(
        natal,
        lng=-73.9857,
        lat=40.7484,
        tz_str="America/New_York",
        online=False,
    )

    solar_return = factory.next_return_from_year(2025, "Solar")

    chart_data = ChartDataFactory.create_return_chart_data(natal, solar_return)
    drawer = ChartDrawer(chart_data=chart_data, theme="light")
    drawer.save_svg(output_path=output_dir, filename="grace_hopper_solar_return", minify=True)

    print("Solar return cast for:", solar_return.iso_formatted_local_datetime)
    print("Return location:", solar_return.city, solar_return.nation)
    print("Total aspects:", len(chart_data.aspects))


if __name__ == "__main__":
    main()
