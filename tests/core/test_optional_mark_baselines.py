# -*- coding: utf-8 -*-
"""The optional chart marks, and the baselines nobody was reading.

Eighteen SVG baselines were generated, committed and never compared by anything.
They are the charts that demonstrate the drawer's optional marks — the station
glyph, the out-of-bounds badge, the separating-aspect dashes, the ayanamsa offset,
the polar substitution note, the relationship score — and the "all marks on" charts
that carry every one of them at once.

A baseline no test reads is not a regression guard; it is a picture of the library
as it was on the day it was written, which is how 73 files came to be drawing a
glyph the library no longer had. These are the tests that read them.

Each also asserts the mark it exists for is actually PRESENT. A golden comparison
alone would pass just as well if the option silently stopped doing anything and
the baseline were regenerated to match — which is exactly what happened to the
relationship-score chart.
"""

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer

from tests.core.test_chart_drawer import SVG_DIR, _make_john, _make_paul
from tests.data.compare_svg_lines import compare_svg_file
from tests.data.golden_places import golden_place

#: Every optional mark at once, as the regenerator switches them on.
ALL_MARKS_ON = dict(
    show_motion_state=True,
    show_out_of_bounds=True,
    show_aspect_movement=True,
    show_relationship_score=True,
    show_ayanamsa_value=True,
    show_polar_fallback_note=True,
)


def _station_subject():
    """Mercury turns retrograde on this date — the station mark has something to mark."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Mercury Station", 1990, 8, 25, 12, 0,
        suppress_geonames_warning=True, **golden_place("London", "GB"),
    )


def _out_of_bounds_subject():
    """A sky with a body past the obliquity, so the badge is not an empty promise."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Out Of Bounds", 1990, 1, 1, 12, 0,
        suppress_geonames_warning=True, **golden_place("London", "GB"),
    )


def _polar_subject(name="Polar Fallback"):
    """Placidus is undefined this far north, so the substitution note has a cause."""
    return AstrologicalSubjectFactory.from_birth_data(
        name, 1990, 6, 15, 12, 0, "Longyearbyen", "SJ",
        lng=15.6, lat=78.2, tz_str="Arctic/Longyearbyen",
        houses_system_identifier="P", suppress_geonames_warning=True,
    )


def _render(subject, style, **drawer_kwargs):
    data = ChartDataFactory.create_natal_chart_data(subject)
    return ChartDrawer(data, **drawer_kwargs).generate_svg_string(style=style)


# The classic baselines were written from subjects NAMED after the mark, because
# save_svg takes its filename from the subject's name; the modern ones were written
# with an explicit filename from a subject named plainly. The panel prints the name,
# so the two carry different titles and a test has to reproduce the right one.
def _station_named_for(style: str, mark: str):
    subject = _station_subject()
    if style == "classic":
        subject.name = f"Mercury Station - {mark}"
    return subject


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_motion_state_baseline(style):
    svg = _render(_station_named_for(style, "Motion State"), style, show_motion_state=True)
    assert "motion" in svg.lower()
    compare_svg_file(SVG_DIR / f"Mercury Station - Motion State - Natal Chart - {style.capitalize()}.svg", svg)


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_aspect_movement_baseline(style):
    svg = _render(_station_named_for(style, "Aspect Movement"), style, show_aspect_movement=True)
    compare_svg_file(SVG_DIR / f"Mercury Station - Aspect Movement - Natal Chart - {style.capitalize()}.svg", svg)


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_out_of_bounds_baseline(style):
    svg = _render(_out_of_bounds_subject(), style, show_out_of_bounds=True)
    compare_svg_file(SVG_DIR / f"Out Of Bounds - Natal Chart - {style.capitalize()}.svg", svg)


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_polar_fallback_note_baseline(style):
    subject = _polar_subject()
    svg = _render(subject, style, show_polar_fallback_note=True)
    # The note exists because the substitution did: Placidus at 78.2N is cast in
    # Porphyry, and the chart says so rather than printing cusps it did not use.
    assert subject.polar_house_fallbacks
    compare_svg_file(SVG_DIR / f"Polar Fallback - Natal Chart - {style.capitalize()}.svg", svg)


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_ayanamsa_value_baseline(style):
    subject = _make_john("Ayanamsa Value", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
    svg = _render(subject, style, show_ayanamsa_value=True)
    assert subject.ayanamsa_value is not None
    compare_svg_file(SVG_DIR / f"John Lennon - Ayanamsa Value - Natal Chart - {style.capitalize()}.svg", svg)


def test_relationship_score_modern_baseline():
    john, paul = _make_john("Relationship Score"), _make_paul()
    data = ChartDataFactory.create_synastry_chart_data(john, paul)
    svg = ChartDrawer(data, show_relationship_score=True).generate_svg_string(style="modern")
    assert "Relationship Score" in svg
    compare_svg_file(SVG_DIR / "John Lennon - Relationship Score - Synastry Chart - Modern.svg", svg)


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_all_marks_on_a_station_chart(style):
    subject = _station_subject()
    subject.name = "Mercury Station - All Marks"
    svg = _render(subject, style, **ALL_MARKS_ON)
    compare_svg_file(SVG_DIR / f"Mercury Station - All Marks - Natal Chart - {style.capitalize()}.svg", svg)


def test_all_marks_on_a_sidereal_chart():
    subject = _make_john("All Marks Sidereal", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
    svg = _render(subject, "classic", **ALL_MARKS_ON)
    compare_svg_file(SVG_DIR / "John Lennon - All Marks Sidereal - Natal Chart - Classic.svg", svg)


def test_all_marks_on_a_polar_chart():
    svg = _render(_polar_subject("Polar Fallback - All Marks"), "classic", **ALL_MARKS_ON)
    compare_svg_file(SVG_DIR / "Polar Fallback - All Marks - Natal Chart - Classic.svg", svg)


@pytest.mark.parametrize("style", ["classic", "modern"])
def test_all_marks_on_a_synastry_chart(style):
    first = _make_john("All Marks Synastry")
    second = _make_paul()
    data = ChartDataFactory.create_synastry_chart_data(first, second)
    svg = ChartDrawer(data, **ALL_MARKS_ON).generate_svg_string(style=style)
    compare_svg_file(
        SVG_DIR / f"John Lennon - All Marks Synastry - Synastry Chart - {style.capitalize()}.svg", svg
    )


# Three plain natal baselines were committed with neither a generator nor a
# reader, so they kept a picture of an older library — they were still drawing the
# font-traced Jupiter six commits after it was redrawn. The regenerator learned to
# write them; these read them. The birth data matches the regenerator's, which read
# it off the panels of the files it replaced.
@pytest.mark.parametrize(
    "name,birth,place",
    [
        ("Johnny Depp", (1963, 6, 9, 0, 0), ("Owensboro", "US")),
        ("Yoko Ono", (1933, 2, 18, 20, 30), ("Tokyo", "JP")),
    ],
    ids=["johnny_depp", "yoko_ono"],
)
def test_plain_natal_baselines_that_had_no_reader(name, birth, place):
    subject = AstrologicalSubjectFactory.from_birth_data(
        name, *birth, suppress_geonames_warning=True, **golden_place(*place)
    )
    compare_svg_file(SVG_DIR / f"{name} - Natal Chart - Classic.svg", _render(subject, "classic"))


def test_paul_mccartney_plain_natal_baseline():
    """The third of them, and the one whose subject the golden helpers already build."""
    svg = _render(_make_paul(), "classic")
    compare_svg_file(SVG_DIR / "Paul McCartney - Natal Chart - Classic.svg", svg)
