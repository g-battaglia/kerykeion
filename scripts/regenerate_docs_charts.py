#!/usr/bin/env python3
"""
Regenerate the chart SVGs used in docs/charts/ (README showcase grid).

Two groups. CHARTS is the style x theme grid, one John Lennon natal per file.
MARK_CHARTS showcases the opt-in marks, and cannot reuse that subject: a mark
draws nothing where it has no referent, so each of these casts the chart that
actually has one. See both lists below.

All SVGs are saved with inlined CSS variables (remove_css_variables=True)
so they render correctly on GitHub without external stylesheets.

Usage:
    python scripts/regenerate_docs_charts.py
"""

from pathlib import Path
from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer

#: Every mark, switched on together. A chart only shows the ones it has a
#: referent for, so turning them all on is how one flag set serves four very
#: different subjects without any of them claiming something it does not have.
MARKS_ALL_ON = {
    "show_motion_state": True,
    "show_out_of_bounds": True,
    "show_aspect_movement": True,
    "show_relationship_score": True,
    "show_ayanamsa_value": True,
    "show_polar_fallback_note": True,
}

# Every file in docs/charts/, not a subset. The README embeds these by raw URL,
# so one left behind is a documentation image showing a chart the library no
# longer draws — which is what happened to eleven of them when the info panel
# gained a row and only these four were listed here.
CHARTS = [
    ("classic_default_natal", "classic", "classic"),
    ("classic_dark_natal", "classic", "dark"),
    ("classic_black_and_white_natal", "classic", "black-and-white"),
    # Same style and theme, so these two render byte-identically. Both filenames
    # were already committed and the README links `modern_classic_natal`, so
    # neither is dropped here; listing both is what keeps them in step. Retiring
    # one is a docs change, not a regeneration one.
    ("modern_default_natal", "modern", "classic"),
    ("modern_classic_natal", "modern", "classic"),
    ("modern_dark_natal", "modern", "dark"),
    ("modern_black_and_white_natal", "modern", "black-and-white"),
]

#: Charts that showcase the opt-in marks. Each entry names its own subject and
#: the options to switch on, because there is no one chart that carries every
#: referent: a natal chart has no relationship score, a tropical one no
#: ayanamsa, a temperate one no polar fallback. Both styles for each, since the
#: two draw the wheel marks differently and a reader comparing them should be
#: able to see both.
MARK_CHARTS = [
    ("marks_wheel", "Mercury Station", MARKS_ALL_ON),
    ("marks_sidereal", "Sidereal", MARKS_ALL_ON),
    ("marks_polar", "Polar", MARKS_ALL_ON),
    ("marks_synastry", "Synastry", MARKS_ALL_ON),
]


def _mark_chart_data(subject_key: str):
    """Chart data for one mark showcase, cast so the mark has something to mark."""
    if subject_key == "Mercury Station":
        # 25 August 1990: Mercury crawls at 0.012°/day, a stationary retrograde,
        # and Uranus sits past the Sun's maximum declination. One chart, three
        # marks — the stations, the out-of-bounds badge and the aspect dashes.
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Mercury Station",
            year=1990, month=8, day=25, hour=12, minute=0,
            city="London", nation="GB", tz_str="Europe/London",
            lat=51.5074, lng=-0.1276,
            online=False, suppress_geonames_warning=True,
        )
        return ChartDataFactory.create_natal_chart_data(subject)

    if subject_key == "Sidereal":
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="John Lennon",
            year=1940, month=10, day=9, hour=18, minute=30,
            city="Liverpool", nation="GB", tz_str="Europe/London",
            lat=53.4084, lng=-2.9916,
            zodiac_type="Sidereal", sidereal_mode="LAHIRI",
            online=False, suppress_geonames_warning=True,
        )
        return ChartDataFactory.create_natal_chart_data(subject)

    if subject_key == "Polar":
        # Placidus is undefined inside the polar circle, so the cusps were
        # computed with another system and the note says so.
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Longyearbyen",
            year=1990, month=6, day=15, hour=12, minute=0,
            city="Longyearbyen", nation="SJ", tz_str="Arctic/Longyearbyen",
            lat=78.2, lng=15.6,
            houses_system_identifier="P",
            online=False, suppress_geonames_warning=True,
        )
        return ChartDataFactory.create_natal_chart_data(subject)

    if subject_key == "Synastry":
        first = AstrologicalSubjectFactory.from_birth_data(
            name="John Lennon",
            year=1940, month=10, day=9, hour=18, minute=30,
            city="Liverpool", nation="GB", tz_str="Europe/London",
            lat=53.4084, lng=-2.9916,
            online=False, suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            name="Paul McCartney",
            year=1942, month=6, day=18, hour=15, minute=30,
            city="Liverpool", nation="GB", tz_str="Europe/London",
            lat=53.4084, lng=-2.9916,
            online=False, suppress_geonames_warning=True,
        )
        return ChartDataFactory.create_synastry_chart_data(first, second)

    raise ValueError(f"unknown mark-chart subject: {subject_key}")


def main():
    output_dir = Path(__file__).parent.parent / "docs" / "charts"
    output_dir.mkdir(parents=True, exist_ok=True)

    lennon = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        city="Liverpool",
        nation="GB",
        tz_str="Europe/London",
        lat=53.4084,
        lng=-2.9916,
        online=False,
        suppress_geonames_warning=True,
    )

    natal_data = ChartDataFactory.create_natal_chart_data(lennon)

    for filename, style, theme in CHARTS:
        drawer = ChartDrawer(natal_data, theme=theme)
        drawer.save_svg(
            output_path=str(output_dir),
            filename=filename,
            style=style,
            remove_css_variables=True,
        )

    for filename, subject_key, marks in MARK_CHARTS:
        chart_data = _mark_chart_data(subject_key)
        for style in ("classic", "modern"):
            ChartDrawer(chart_data, theme="classic", **marks).save_svg(
                output_path=str(output_dir),
                filename=f"{filename}_{style}",
                style=style,
                remove_css_variables=True,
            )

    print(f"\nAll docs charts regenerated in {output_dir}")


if __name__ == "__main__":
    main()
