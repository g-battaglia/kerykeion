"""Annual Profections: compute profection years for a natal chart."""

from kerykeion import AstrologicalSubjectFactory, ProfectionsFactory


def main() -> None:
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

    profections = ProfectionsFactory.from_subject(natal, target_date="2026-06-04")
    current = profections.current
    print(f"Age {current.age}: {current.house}th house ({current.sign})")
    print(f"Lord of the Year: {current.lord}")
    print(f"Year: {current.year_start} to {current.year_end}")

    print(f"\nFull table ({len(profections.years)} years):")
    for year in profections.years:
        marker = " ★" if year.age == current.age else ""
        print(f"  Age {year.age:3d}  House {year.house:2d}  {year.sign:3s}  {year.lord}{marker}")


if __name__ == "__main__":
    main()
