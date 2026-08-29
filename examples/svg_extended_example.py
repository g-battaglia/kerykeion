"""Every opt-in chart mark, each on a subject that has its referent.

``ChartDrawer`` exposes six boolean options that draw things the chart data
already knows: stations, out-of-bounds bodies, separating aspects, the synastry
score, the ayanamsa offset and a substituted house system. All six default to
``False``, so a chart only gains them when it is asked to.

Each mark is silent where there is nothing to mark, which makes a demo of all
six on one chart useless: a tropical natal has no ayanamsa, a temperate one no
polar fallback, a single wheel no relationship score. This script therefore
turns all six on for every chart and picks four subjects that between them
carry every referent:

* **25 August 1990, London** — Mercury sits at 0.012°/day, a stationary
  retrograde; Uranus is past the Sun's maximum declination, so it is out of
  bounds. Stations, the OOB badge and the separating-aspect dashes.
* **Longyearbyen, 78.2° N** — Placidus is undefined inside the polar circle, so
  the cusps were computed with Porphyry instead. The polar-fallback note.
* **Sidereal Lahiri** — the ayanamsa offset printed next to the mode name.
* **A synastry pair** — the relationship score in the info panel.

The script also reads the ``kr:`` state attributes back out of the finished
markup, which is what a consumer of the SVG would do.

Everything runs offline: no network, no GeoNames lookup.
"""

from pathlib import Path

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.charts.svg_metadata import parse_chart_points

#: Every opt-in mark, in one place. Spread onto each ChartDrawer below.
EXTENDED_MARKS = {
    "show_motion_state": True,
    "show_out_of_bounds": True,
    "show_aspect_movement": True,
    "show_relationship_score": True,
    "show_ayanamsa_value": True,
    "show_polar_fallback_note": True,
}


def build_subjects() -> dict:
    """The four cases, all offline."""
    station = AstrologicalSubjectFactory.from_birth_data(
        name="Mercury Station",
        year=1990,
        month=8,
        day=25,
        hour=12,
        minute=0,
        city="London",
        nation="GB",
        lng=-0.1276,
        lat=51.5074,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )

    polar = AstrologicalSubjectFactory.from_birth_data(
        name="Polar Fallback",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=0,
        city="Longyearbyen",
        nation="SJ",
        lng=15.6,
        lat=78.2,
        tz_str="Arctic/Longyearbyen",
        houses_system_identifier="P",  # undefined this far north; Porphyry stands in
        online=False,
        suppress_geonames_warning=True,
    )

    sidereal = AstrologicalSubjectFactory.from_birth_data(
        name="Sidereal Lahiri",
        year=1990,
        month=8,
        day=25,
        hour=12,
        minute=0,
        city="Mumbai",
        nation="IN",
        lng=72.8777,
        lat=19.0760,
        tz_str="Asia/Kolkata",
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
        online=False,
        suppress_geonames_warning=True,
    )

    partner = AstrologicalSubjectFactory.from_birth_data(
        name="Partner",
        year=1991,
        month=11,
        day=5,
        hour=9,
        minute=30,
        city="Rome",
        nation="IT",
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        online=False,
        suppress_geonames_warning=True,
    )

    return {"station": station, "polar": polar, "sidereal": sidereal, "partner": partner}


def report_point_state(svg: str, title: str) -> None:
    """Print the state the SVG carries for the points that state anything.

    ``kr:motionstate``, ``kr:speed``, ``kr:declination`` and ``kr:oob`` ride on
    every ChartPoint with no option to enable — they are data, not decoration.
    The six options below only decide whether the reader sees them drawn.
    """
    print(f"\n  {title}")
    for point in parse_chart_points(svg):
        if point.horoscope != "0":
            continue
        if point.motion_state in ("stationary_retrograde", "stationary_direct") or point.out_of_bounds:
            marks = []
            if point.motion_state:
                marks.append(point.motion_state)
            if point.out_of_bounds:
                marks.append("out of bounds")
            print(f"    {point.slug:<12} {', '.join(marks)}  ({point.speed}°/day, dec {point.declination}°)")


def main() -> None:
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    subjects = build_subjects()

    # ── Stations, out-of-bounds and separating aspects ──────────────────────
    station_data = ChartDataFactory.create_natal_chart_data(subjects["station"])
    station_drawer = ChartDrawer(station_data, **EXTENDED_MARKS)
    station_svg = station_drawer.generate_svg_string()
    station_drawer.save_svg(output_path=output_dir, filename="extended_station")
    # The classic wheel marks the same station at the foot of the glyph, where
    # its retrograde symbol sits.
    station_drawer.save_svg(output_path=output_dir, filename="extended_station_classic", style="classic")
    report_point_state(station_svg, "Mercury Station — 25 August 1990, London")

    # ── The substituted house system ────────────────────────────────────────
    polar_data = ChartDataFactory.create_natal_chart_data(subjects["polar"])
    ChartDrawer(polar_data, **EXTENDED_MARKS).save_svg(output_path=output_dir, filename="extended_polar")
    record = subjects["polar"].polar_house_fallbacks[0]
    print(
        f"\n  Polar Fallback — requested {record.requested_house_system_name}, "
        f"used {record.used_house_system_name} (polar circle at {record.threshold:.3f}°)"
    )

    # ── The ayanamsa offset ─────────────────────────────────────────────────
    sidereal_data = ChartDataFactory.create_natal_chart_data(subjects["sidereal"])
    ChartDrawer(sidereal_data, **EXTENDED_MARKS).save_svg(output_path=output_dir, filename="extended_sidereal")
    print(f"\n  Sidereal Lahiri — ayanamsa {subjects['sidereal'].ayanamsa_value:.4f}°")

    # ── The relationship score ──────────────────────────────────────────────
    # create_synastry_chart_data computes the score unless told not to; the
    # generic factory path does not, and the line then prints nothing rather
    # than a zero it never measured.
    synastry_data = ChartDataFactory.create_synastry_chart_data(subjects["station"], subjects["partner"])
    ChartDrawer(synastry_data, **EXTENDED_MARKS).save_svg(output_path=output_dir, filename="extended_synastry")
    score = synastry_data.relationship_score
    print(f"\n  Synastry — relationship score {score.score_value} ({score.score_description})")

    print(f"\n  Charts written to {output_dir}")


if __name__ == "__main__":
    main()
