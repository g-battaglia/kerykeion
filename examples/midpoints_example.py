"""Midpoints: pairwise midpoints and their aspect activations."""

from kerykeion import AstrologicalSubjectFactory, MidpointFactory


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

    midpoints = MidpointFactory.compute(subject)
    print(f"Midpoints: {len(midpoints)}")
    for midpoint in midpoints[:5]:
        print(
            f"  {midpoint.point_a}/{midpoint.point_b} at "
            f"{midpoint.midpoint_sign} {midpoint.midpoint_position:.2f}°"
        )


if __name__ == "__main__":
    main()
