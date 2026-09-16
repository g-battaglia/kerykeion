"""Relocation and astro-cartography: the same moment cast for another place."""

from kerykeion import (
    AstrologicalSubjectFactory,
    AstroCartographyFactory,
    RelocatedChartFactory,
)


def main() -> None:
    natal = AstrologicalSubjectFactory.from_birth_data(
        name="John",
        year=1990,
        month=6,
        day=15,
        hour=14,
        minute=30,
        lng=-2.9833,
        lat=53.4,
        tz_str="Europe/London",
        online=False,
    )

    relocated = RelocatedChartFactory.relocate(
        natal,
        new_lat=40.7128,
        new_lng=-74.006,
        new_city="New York",
        new_nation="US",
    )
    print(f"Natal Ascendant: {natal.first_house.sign}")
    print(f"Relocated Ascendant: {relocated.first_house.sign}")

    lines = AstroCartographyFactory.compute(natal, step=2)
    print(f"\nACG lines: {len(lines)}")
    for line in lines[:5]:
        print(f"  {line.planet} {line.line_type}: {len(line.points)} points")


if __name__ == "__main__":
    main()
