"""Secondary progressions: day-for-a-year progressed charts and contacts."""

from kerykeion import AstrologicalSubjectFactory, SecondaryProgressionFactory


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
        online=False,
    )

    progressed = SecondaryProgressionFactory.compute(
        natal,
        target_iso_utc_datetime="2026-04-25T00:00:00Z",
    )
    print(f"Progressed Sun: {progressed.sun.sign} at {progressed.sun.position:.2f}°")
    print(f"Progressed Moon: {progressed.moon.sign} at {progressed.moon.position:.2f}°")

    result = SecondaryProgressionFactory.compute_full(
        natal,
        target_iso_utc_datetime="2026-04-25T00:00:00Z",
        aspect_orb=1.5,
    )
    print(f"\nProgressed-to-natal aspects: {len(result.progressed_to_natal_aspects)}")
    for asp in result.progressed_to_natal_aspects[:5]:
        print(f"  P.{asp.progressed_point} {asp.aspect} N.{asp.natal_point} (orb {asp.orb:.2f}°)")


if __name__ == "__main__":
    main()
