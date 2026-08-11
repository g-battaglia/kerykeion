"""Firdaria: compute Persian planetary periods for a natal chart."""

from kerykeion import AstrologicalSubjectFactory, FirdariaFactory


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

    firdaria = FirdariaFactory.from_subject(natal, target_date="2026-06-04")
    print(f"Sect: {'Day' if firdaria.is_diurnal else 'Night'}")

    if firdaria.current:
        print(f"Current lord: {firdaria.current.lord} ({firdaria.current.years} years)")
        print(f"  Ages {firdaria.current.age_start}–{firdaria.current.age_end}")
        print(f"  {firdaria.current.start} to {firdaria.current.end}")
    if firdaria.current_sub:
        print(f"Current sub-lord: {firdaria.current_sub.lord}")
        print(f"  {firdaria.current_sub.start} to {firdaria.current_sub.end}")

    print(f"\nAll periods ({len(firdaria.periods)}):")
    for p in firdaria.periods:
        print(f"  {p.lord:12s}  {p.years:2d} years  ages {p.age_start:3d}–{p.age_end:3d}")


if __name__ == "__main__":
    main()
