"""Primary directions: Placidus semi-arc directions with a speculum."""

from kerykeion import AstrologicalSubjectFactory, PrimaryDirectionsFactory


def main() -> None:
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="Grace Hopper",
        year=1906,
        month=12,
        day=9,
        hour=11,
        minute=30,
        lng=-73.9857,
        lat=40.7484,
        tz_str="America/New_York",
        online=False,
    )

    directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
    print(f"Primary directions: {len(directions)}")
    for direction in directions[:5]:
        print(
            f"  {direction.promissor} {direction.aspect} {direction.significator} "
            f"at age {direction.direction_years:.1f} ({direction.rate_key})"
        )

    speculum = PrimaryDirectionsFactory.compute_speculum(subject)
    print(f"\nSpeculum entries: {len(speculum)}")


if __name__ == "__main__":
    main()
