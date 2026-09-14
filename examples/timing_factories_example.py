"""The five timing factories, one call each, all offline.

Each answers a different "when" about the same day and place (Rome, 4 June 2026):

* ``SunTimesFactory`` — sunrise, sunset, solar noon and the twilights.
* ``PlanetaryHoursFactory`` — the Chaldean hour ruling a given moment.
* ``VoidOfCourseMoonFactory`` — whether the Moon has finished aspecting before
  its next ingress.
* ``LunationFinderFactory`` — the New/Full Moon moments over a range.
* ``MundaneAspectFactory`` — exact transiting-to-transiting aspects over a range.
"""

from kerykeion import (
    LunationFinderFactory,
    MundaneAspectFactory,
    PlanetaryHoursFactory,
    SunTimesFactory,
    VoidOfCourseMoonFactory,
)

ROME_LAT = 41.9028
ROME_LNG = 12.4964
ROME_TZ = "Europe/Rome"


def main() -> None:
    sun_times = SunTimesFactory.from_date(2026, 6, 4, latitude=ROME_LAT, longitude=ROME_LNG, tz_str=ROME_TZ)
    print("Sun times      :", f"sunrise {sun_times.sunrise}  solar noon {sun_times.solar_noon}")
    print("                 sunset  {}  day length {}".format(sun_times.sunset, sun_times.day_length))

    hours = PlanetaryHoursFactory.from_datetime(
        2026, 6, 4, 15, 30, latitude=ROME_LAT, longitude=ROME_LNG, tz_str=ROME_TZ
    )
    print("Planetary hour :", f"day ruler {hours.day_ruler}, hour {hours.current_index} ruled by {hours.current_ruler}")

    voc = VoidOfCourseMoonFactory.from_datetime(2026, 6, 4, 15, 30, tz_str=ROME_TZ)
    state = "void of course" if voc.is_void_of_course else "still aspecting"
    print("Moon           :", f"in {voc.moon_sign}, {state}; ingress into {voc.next_sign} at {voc.ingress}")

    lunations = LunationFinderFactory.from_iso_range("2026-06-01", "2026-07-01", phases=["new", "full"])
    for lunation in lunations.lunations:
        print("Lunation       :", f"{lunation.phase} at {lunation.iso_utc}")

    mundane = MundaneAspectFactory.from_iso_range(
        "2026-06-01",
        "2026-07-01",
        points=["Sun", "Mercury", "Venus", "Mars", "Jupiter"],
        aspects=["conjunction", "square", "opposition", "trine"],
    )
    print(f"Mundane aspects: {len(mundane.aspects)} exact in June 2026")
    for aspect in mundane.aspects[:3]:
        print("                ", f"{aspect.point_a} {aspect.aspect} {aspect.point_b} at {aspect.iso_utc}")


if __name__ == "__main__":
    main()
