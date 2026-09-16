"""Eclipse search: global and location-specific solar and lunar eclipses."""

from kerykeion import EclipseFactory


def _show(title: str, results) -> None:
    print(title)
    for eclipse in results.solar_eclipses[:3]:
        print(f"  solar ({eclipse.type}): {eclipse.datestamp} in {eclipse.sign} {eclipse.degree:.1f}°")
    for eclipse in results.lunar_eclipses[:3]:
        print(f"  lunar ({eclipse.type}): {eclipse.datestamp} in {eclipse.sign} {eclipse.degree:.1f}°")


def main() -> None:
    _show(
        "Upcoming eclipses (global):",
        EclipseFactory.search_global(start_year=2025, count=3),
    )
    print()
    _show(
        "Eclipses visible from Rome:",
        EclipseFactory.search_from_location(lat=41.9028, lng=12.4964, start_year=2025, count=3),
    )


if __name__ == "__main__":
    main()
