"""Solar arc directions: a uniform progressed-Sun arc applied to natal points."""

from kerykeion import AstrologicalSubjectFactory, SolarArcFactory


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

    directed = SolarArcFactory.compute_directed_subject(natal, target_year=2030)
    print(f"Directed Sun: {directed.sun.sign} at {directed.sun.abs_pos:.2f}°")

    result = SolarArcFactory.compute(
        natal,
        target_iso_utc_datetime="2026-04-25T00:00:00Z",
    )
    print(f"\nDirected-to-natal aspects: {len(result.directed_to_natal_aspects)}")
    for asp in result.directed_to_natal_aspects[:5]:
        print(f"  D.{asp.directed_point} {asp.aspect} N.{asp.natal_point} (orb {asp.orb:.2f}°)")


if __name__ == "__main__":
    main()
