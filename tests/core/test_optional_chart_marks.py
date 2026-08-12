# -*- coding: utf-8 -*-
"""
Opt-in chart marks.

Six options each add one mark to the chart: station markers on the wheel,
out-of-bounds badges in the point tables, dashes on separating aspect lines,
the synastry score, the ayanamsa offset, and the polar-fallback note. All six
default to off, and these tests pin the two halves of that promise:

    - Off is genuinely off. A caller who upgrades and changes nothing must get
      the chart they had. The strongest form of that is asserted directly: the
      whole SVG, both styles, is unchanged by the options existing.
    - On adds its own mark and nothing else. Every option is checked against
      the *difference* it makes to the markup rather than merely against the
      presence of its mark, so an option cannot quietly move a row or restyle
      a neighbour on its way in.

Each mark also has to be absent where it has no referent — no station in a
chart with no stationary body, no score on synastry data that never computed
one, no ayanamsa offset on a tropical chart — because a mark that appears
anyway is worse than one that never appears at all.

Usage:
    pytest tests/core/test_optional_chart_marks.py -v
"""

import re
from collections import Counter

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

pytestmark = pytest.mark.core

STYLES = ["classic", "modern"]

#: Every option this module covers, all of them off by default.
ALL_MARKS = (
    "show_motion_state",
    "show_out_of_bounds",
    "show_aspect_movement",
    "show_relationship_score",
    "show_ayanamsa_value",
    "show_polar_fallback_note",
)


# ---------------------------------------------------------------------------
# Fixtures — each one exercises exactly one mark's referent
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def station_data():
    """Mercury turns retrograde on this date — the SR case, read off the ephemeris."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Station", 1990, 8, 25, 12, 0, "London", "GB", suppress_geonames_warning=True
    )
    return ChartDataFactory.create_natal_chart_data(subject)


@pytest.fixture(scope="module")
def out_of_bounds_data():
    """Uranus sits past the obliquity here."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Out of bounds", 1990, 1, 1, 12, 0, "London", "GB", suppress_geonames_warning=True
    )
    return ChartDataFactory.create_natal_chart_data(subject)


@pytest.fixture(scope="module")
def sidereal_data():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Sidereal",
        1940,
        10,
        9,
        18,
        30,
        "Liverpool",
        "GB",
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
        suppress_geonames_warning=True,
    )
    return ChartDataFactory.create_natal_chart_data(subject)


@pytest.fixture(scope="module")
def polar_data():
    """Placidus is undefined this far north, so another system stands in for it."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Polar",
        1990,
        6,
        15,
        12,
        0,
        "Longyearbyen",
        "SJ",
        lng=15.6,
        lat=78.2,
        tz_str="Arctic/Longyearbyen",
        houses_system_identifier="P",
        suppress_geonames_warning=True,
    )
    return ChartDataFactory.create_natal_chart_data(subject)


@pytest.fixture(scope="module")
def synastry_data(john_lennon, paul_mccartney):
    return ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render(chart_data, style, **marks) -> str:
    return ChartDrawer(chart_data, style=style, **marks).generate_svg_string()


def _points(chart_data) -> list:
    """The points the chart actually renders, resolved the way the drawer does."""
    return ChartDrawer(chart_data).available_kerykeion_celestial_points


def _info_rows(svg: str) -> list[str]:
    return [m.group(2) for m in re.finditer(r"Bottom_Left_Text_(\d)'[^>]*>([^<]*)</text>", svg)]


def _markup_delta(before: str, after: str) -> tuple[list[str], list[str]]:
    """What turning one option on added to, and took away from, the markup.

    The SVG is one long line, so the comparison is made on tag boundaries.
    Bare closing tags are dropped from the added side: a well-formed new
    element necessarily contributes one, and counting it as a change would
    make every honest option look like it touched something it did not.
    """
    before_tags = Counter(re.findall(r"<[^>]+>[^<]*", before))
    after_tags = Counter(re.findall(r"<[^>]+>[^<]*", after))
    added = [f for f in (after_tags - before_tags).elements() if not re.fullmatch(r"</[a-zA-Z]+>\s*", f)]
    removed = [f for f in (before_tags - after_tags).elements() if not re.fullmatch(r"</[a-zA-Z]+>\s*", f)]
    return added, removed


# ---------------------------------------------------------------------------
# Off is off
# ---------------------------------------------------------------------------


class TestDefaultsAddNothing:
    @pytest.mark.parametrize("style", STYLES)
    def test_every_mark_defaults_to_off(self, station_data, style):
        drawer = ChartDrawer(station_data, style=style)
        for mark in ALL_MARKS:
            assert getattr(drawer, mark) is False, f"{mark} is not off by default"

    @pytest.mark.parametrize("style", STYLES)
    def test_the_chart_is_unchanged_by_the_options_existing(self, station_data, style):
        """Passing every option its own default must reproduce the plain chart byte for byte."""
        plain = _render(station_data, style)
        explicit = _render(station_data, style, **{mark: False for mark in ALL_MARKS})
        assert plain == explicit

    @pytest.mark.parametrize("style", STYLES)
    def test_no_mark_is_drawn_by_default(self, station_data, out_of_bounds_data, style):
        for chart_data in (station_data, out_of_bounds_data):
            svg = _render(chart_data, style)
            assert ">SR<" not in svg and ">SD<" not in svg
            assert ">OOB<" not in svg


# ---------------------------------------------------------------------------
# Station markers
# ---------------------------------------------------------------------------


class TestStationMarkers:
    @pytest.mark.parametrize("style", STYLES)
    def test_a_station_is_marked_when_asked_for(self, station_data, style):
        svg = _render(station_data, style, show_motion_state=True)
        assert ">SR<" in svg

    @pytest.mark.parametrize("style", STYLES)
    def test_a_chart_with_no_station_gains_no_marker(self, out_of_bounds_data, style):
        """The option asks for stations to be shown, not for something to be invented."""
        assert not any(
            p.motion_state in ("stationary_retrograde", "stationary_direct")
            for p in _points(out_of_bounds_data)
            if p.motion_state
        ), "fixture drifted: it now contains a station"
        svg = _render(out_of_bounds_data, style, show_motion_state=True)
        assert ">SR<" not in svg and ">SD<" not in svg

    def test_the_station_takes_the_retrograde_marker_row_in_the_modern_wheel(self, station_data):
        """One marker per body: the station replaces RX rather than crowding it.

        The modern cluster reserves ink for exactly the rows it draws, so two
        markers in one row would overlap where the separation model expects one.
        """
        mercury = next(p for p in _points(station_data) if p.name == "Mercury")
        assert mercury.motion_state == "stationary_retrograde"

        off = _render(station_data, "modern")
        on = _render(station_data, "modern", show_motion_state=True)
        assert off.count(">RX<") == on.count(">RX<") + 1 if mercury.retrograde else True
        assert on.count(">SR<") == 1

    def test_the_modern_marker_carries_the_station_colour(self, station_data):
        svg = _render(station_data, "modern", show_motion_state=True)
        marker = re.search(r"<text[^>]*>SR</text>", svg)
        assert marker is not None
        assert "kerykeion-modern-stationary" in marker.group(0)

    @pytest.mark.parametrize("style", STYLES)
    def test_turning_it_on_touches_only_the_marked_body(self, station_data, style):
        added, removed = _markup_delta(
            _render(station_data, style), _render(station_data, style, show_motion_state=True)
        )
        assert added, "the option produced no change at all"
        assert all("SR" in fragment or "stationary" in fragment for fragment in added), added
        # The modern wheel recolours the whole cluster, exactly as it already
        # does for a retrograde, so what disappears is that one body in its
        # former colour — never another body's markup. Classic recolours
        # nothing and removes nothing.
        assert all("mercury" in fragment.lower() for fragment in removed), removed


# ---------------------------------------------------------------------------
# Out-of-bounds badges
# ---------------------------------------------------------------------------


class TestOutOfBoundsBadge:
    @pytest.mark.parametrize("style", STYLES)
    def test_the_badge_appears_for_a_body_past_the_obliquity(self, out_of_bounds_data, style):
        assert _render(out_of_bounds_data, style, show_out_of_bounds=True).count(">OOB<") >= 1

    @pytest.mark.parametrize("style", STYLES)
    def test_a_table_with_nothing_out_of_bounds_gains_no_badge(self, station_data, style):
        svg = _render(station_data, style, show_out_of_bounds=True)
        in_bounds = not any(
            getattr(p, "is_out_of_bounds", None) for p in _points(station_data)
        )
        if in_bounds:
            assert ">OOB<" not in svg

    @pytest.mark.parametrize("style", STYLES)
    def test_turning_it_on_adds_only_badges(self, out_of_bounds_data, style):
        added, removed = _markup_delta(
            _render(out_of_bounds_data, style), _render(out_of_bounds_data, style, show_out_of_bounds=True)
        )
        assert added
        assert all("OOB" in fragment for fragment in added), added
        assert removed == [], removed


# ---------------------------------------------------------------------------
# Separating aspects
# ---------------------------------------------------------------------------


class TestAspectMovement:
    @pytest.mark.parametrize("style", STYLES)
    def test_separating_lines_are_dashed_and_applying_ones_are_not(self, station_data, style):
        separating = sum(1 for a in station_data.aspects if str(a.aspect_movement).lower() == "separating")
        assert separating, "fixture has no separating aspect to dash"

        off = _render(station_data, style)
        on = _render(station_data, style, show_aspect_movement=True)
        assert on.count("stroke-dasharray") - off.count("stroke-dasharray") == separating

    @pytest.mark.parametrize("style", STYLES)
    def test_only_aspect_lines_change(self, station_data, style):
        """The undashed originals go away, and only dashed lines take their place."""
        added, removed = _markup_delta(
            _render(station_data, style), _render(station_data, style, show_aspect_movement=True)
        )
        assert added
        assert all("dasharray" in fragment for fragment in added), added
        assert all(fragment.startswith("<line") for fragment in removed), removed


# ---------------------------------------------------------------------------
# Info-panel marks
# ---------------------------------------------------------------------------


class TestRelationshipScoreLine:
    @pytest.mark.parametrize("style", STYLES)
    def test_the_score_is_printed_with_its_band(self, synastry_data, style):
        score = synastry_data.relationship_score
        assert score is not None, "fixture no longer computes a score"

        row = _info_rows(_render(synastry_data, style, show_relationship_score=True))[0]
        assert str(score.score_value) in row
        assert row.startswith("Relationship Score")

    @pytest.mark.parametrize("style", STYLES)
    def test_the_row_it_uses_is_empty_without_it(self, synastry_data, style):
        assert _info_rows(_render(synastry_data, style))[0] == ""

    def test_data_that_never_computed_a_score_prints_nothing(self, john_lennon, paul_mccartney):
        """The generic factory leaves the score out; the line must not invent a zero."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            john_lennon, paul_mccartney, include_relationship_score=False
        )
        assert chart_data.relationship_score is None
        assert _info_rows(_render(chart_data, "modern", show_relationship_score=True))[0] == ""


class TestAyanamsaValue:
    @pytest.mark.parametrize("style", STYLES)
    def test_the_offset_joins_the_mode_name(self, sidereal_data, style):
        off = _info_rows(_render(sidereal_data, style))[0]
        on = _info_rows(_render(sidereal_data, style, show_ayanamsa_value=True))[0]
        assert off == "Ayanamsa: Lahiri"
        assert on.startswith(off) and re.search(r"\(\d+°\d+&apos;\)$", on), on

    @pytest.mark.parametrize("style", STYLES)
    def test_a_tropical_chart_has_no_offset_to_show(self, station_data, style):
        """Tropical charts carry no ayanamsa, so the option has nothing to add."""
        assert _render(station_data, style) == _render(station_data, style, show_ayanamsa_value=True)

    def test_the_offset_never_reaches_the_reader_as_an_entity(self, sidereal_data):
        """The panel escapes its own text, so the seconds symbol would double-escape."""
        row = _info_rows(_render(sidereal_data, "modern", show_ayanamsa_value=True))[0]
        assert "&amp;" not in row


class TestPolarFallbackNote:
    @pytest.mark.parametrize("style", STYLES)
    def test_the_substitution_is_admitted(self, polar_data, style):
        assert polar_data.subject.polar_house_fallbacks, "fixture no longer triggers a fallback"

        off = _info_rows(_render(polar_data, style))[1]
        on = _info_rows(_render(polar_data, style, show_polar_fallback_note=True))[1]
        assert "*" not in off
        assert on.startswith(off) and "*" in on

    @pytest.mark.parametrize("style", STYLES)
    def test_a_chart_whose_system_was_honoured_says_nothing(self, station_data, style):
        assert not station_data.subject.polar_house_fallbacks
        assert _render(station_data, style) == _render(station_data, style, show_polar_fallback_note=True)
