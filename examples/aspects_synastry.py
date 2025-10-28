"""Synastry aspect calculation using the unified AspectsFactory."""
from kerykeion import AstrologicalSubjectFactory, AspectsFactory


def main() -> None:
    john = AstrologicalSubjectFactory.from_birth_data(
        name="John",
        year=1990,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lng=-0.1276,
        lat=51.5072,
        tz_str="Europe/London",
        city="London",
        nation="GB",
        online=False,
    )

    jane = AstrologicalSubjectFactory.from_birth_data(
        name="Jane",
        year=1992,
        month=6,
        day=15,
        hour=14,
        minute=30,
        lng=2.3522,
        lat=48.8566,
        tz_str="Europe/Paris",
        city="Paris",
        nation="FR",
        online=False,
    )

    synastry = AspectsFactory.dual_chart_aspects(john, jane)

    print(f"Total aspects: {len(synastry.aspects)}")

    if synastry.aspects:
        first = synastry.aspects[0]
        print(
            "Example aspect: "
            f"{first.p1_name} {first.aspect} {first.p2_name} "
            f"with orb {first.orbit:.2f}°"
        )


if __name__ == "__main__":
    main()
