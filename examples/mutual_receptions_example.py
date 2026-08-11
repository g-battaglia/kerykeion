"""Mutual Receptions: detect domicile and exaltation receptions."""

from kerykeion import AstrologicalSubjectFactory, MutualReceptionsFactory


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

    receptions = MutualReceptionsFactory.from_subject(natal)

    if not receptions.receptions:
        print("No mutual receptions found among the classical planets.")
    else:
        for r in receptions.receptions:
            print(f"{r.first_planet} ↔ {r.second_planet} (by {r.reception_type})")


if __name__ == "__main__":
    main()
