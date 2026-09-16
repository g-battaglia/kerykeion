"""Dignities, nakshatras and motion state: per-point traditional factors."""

from kerykeion import AstrologicalSubjectFactory


def main() -> None:
    tropical = AstrologicalSubjectFactory.from_birth_data(
        name="Jane",
        year=1990,
        month=7,
        day=15,
        hour=10,
        minute=30,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        online=False,
        calculate_dignities=True,
    )
    print(f"Sun dignity: {tropical.sun.essential_dignity} (score {tropical.sun.dignity_score})")
    print(f"Mars motion: {tropical.mars.motion_state} (speed {tropical.mars.speed:.3f}°/day)")

    sidereal = AstrologicalSubjectFactory.from_birth_data(
        name="Jane",
        year=1990,
        month=7,
        day=15,
        hour=10,
        minute=30,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        online=False,
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
        calculate_nakshatra=True,
    )
    print(f"Moon nakshatra: {sidereal.moon.nakshatra} pada {sidereal.moon.nakshatra_pada}")


if __name__ == "__main__":
    main()
