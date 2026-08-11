"""Horary Indicators: assemble significators and considerations."""

from kerykeion import AstrologicalSubjectFactory, HoraryIndicatorsFactory


def main() -> None:
    question = AstrologicalSubjectFactory.from_birth_data(
        name="Question",
        year=2026,
        month=6,
        day=4,
        hour=15,
        minute=30,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        city="Rome",
        nation="IT",
        online=False,
    )

    indicators = HoraryIndicatorsFactory.from_subject(question, is_moon_void=False)

    print("Querent (1st house):")
    q = indicators.querent
    print(f"  Sign: {q.sign}, Ruler: {q.ruler}, in house {q.ruler_house_number}")

    print("Quesited (7th house):")
    qs = indicators.quesited
    print(f"  Sign: {qs.sign}, Ruler: {qs.ruler}, in house {qs.ruler_house_number}")

    print(f"\nAscendant degree: {indicators.ascendant_degree:.2f}°")

    print("\nConsiderations:")
    for c in indicators.considerations:
        print(f"  [{c.status}] {c.key}")

    print(f"\nMutual receptions: {len(indicators.mutual_receptions)}")
    for r in indicators.mutual_receptions:
        print(f"  {r.first_planet} ↔ {r.second_planet} ({r.reception_type})")


if __name__ == "__main__":
    main()
