"""Compute weekly transits for a natal chart using the new time range factory."""
from datetime import datetime, timedelta, timezone

from kerykeion import (
    AstrologicalSubjectFactory,
    EphemerisDataFactory,
    TransitsTimeRangeFactory,
)


def main() -> None:
    natal = AstrologicalSubjectFactory.from_birth_data(
        name="Research Subject",
        year=1988,
        month=4,
        day=12,
        hour=9,
        minute=15,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        city="Rome",
        nation="IT",
        online=False,
    )

    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=21)

    ephemeris_factory = EphemerisDataFactory(
        start,
        end,
        step_type="days",
        step=3,
        lat=natal.lat or 41.9028,
        lng=natal.lng or 12.4964,
        tz_str=natal.tz_str or "Europe/Rome",
    )
    data_points = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

    transit_factory = TransitsTimeRangeFactory(natal, data_points)
    transits = transit_factory.get_transit_moments()

    date_range = transits.dates or []
    if date_range:
        print(
            "Generated {count} transit snapshots between {start} and {end}.".format(
                count=len(transits.transits),
                start=date_range[0],
                end=date_range[-1],
            )
        )
    else:
        print(f"Generated {len(transits.transits)} transit snapshots.")

    if transits.transits:
        first_transit = transits.transits[0]
        print("First snapshot:", first_transit.date)
        if first_transit.aspects:
            aspect = first_transit.aspects[0]
            print(
                "Example transit aspect:",
                f"{aspect.p1_name} {aspect.aspect} {aspect.p2_name}",
                f"orb {aspect.orbit:.2f}°",
            )


if __name__ == "__main__":
    main()
