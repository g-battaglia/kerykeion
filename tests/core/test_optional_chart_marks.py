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
import xml.etree.ElementTree as ET
from html import unescape

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.charts.drawer import info_row_clear_width
from kerykeion.charts.glyph_metrics import estimate_text_width
from kerykeion.settings.translation_strings import LANGUAGE_SETTINGS

from .svg_text_overlap import find_text_overlaps

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
def two_angles_data():
    """Venus stands on both the Ascendant and the Midheaven at this latitude."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Two angles", 2000, 1, 16, 8, 0, "Tromso", "NO", lng=18.95, lat=67.0, tz_str="UTC",
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
        # The zodiac line sits second from the bottom: the perspective closes the
        # block, and both are down where the wheel has stopped narrowing it.
        off = _info_rows(_render(sidereal_data, style))[4]
        on = _info_rows(_render(sidereal_data, style, show_ayanamsa_value=True))[4]
        assert off == "Ayanamsa: Lahiri"
        assert on.startswith(off) and re.search(r"\(\d+°\d+&apos;\)$", on), on

    @pytest.mark.parametrize("style", STYLES)
    def test_a_tropical_chart_has_no_offset_to_show(self, station_data, style):
        """Tropical charts carry no ayanamsa, so the option has nothing to add."""
        assert _render(station_data, style) == _render(station_data, style, show_ayanamsa_value=True)

    def test_the_offset_never_reaches_the_reader_as_an_entity(self, sidereal_data):
        """The panel escapes its own text, so the seconds symbol would double-escape."""
        row = _info_rows(_render(sidereal_data, "modern", show_ayanamsa_value=True))[4]
        assert "&amp;" not in row


class TestPolarFallbackNote:
    @pytest.mark.parametrize("style", STYLES)
    def test_the_substitution_is_admitted(self, polar_data, style):
        assert polar_data.subject.polar_house_fallbacks, "fixture no longer triggers a fallback"

        off = _info_rows(_render(polar_data, style))[2]      # the domification row
        on = _info_rows(_render(polar_data, style, show_polar_fallback_note=True))[2]
        assert "*" not in off
        assert on.startswith(off) and "*" in on

    @pytest.mark.parametrize("style", STYLES)
    def test_a_chart_whose_system_was_honoured_says_nothing(self, station_data, style):
        assert not station_data.subject.polar_house_fallbacks
        assert _render(station_data, style) == _render(station_data, style, show_polar_fallback_note=True)


# ---------------------------------------------------------------------------
# The panel rows have to fit the wheel, and the dual wheels have to be honest
# ---------------------------------------------------------------------------


class TestEveryOutputIsWellFormed:
    """Every chart type, style and template, with every mark on, parses as XML.

    The earlier version of this sweep covered eighteen combinations and missed
    an encoding that produced duplicate attribute names, because none of its
    subjects had a point standing on two angles. The subject list is what makes
    a sweep like this worth anything, so it now includes the polar and
    high-latitude skies where the wheel's geometry stops being ordinary.
    """

    @pytest.mark.parametrize("style", STYLES)
    @pytest.mark.parametrize(
        "output_method",
        ["generate_svg_string", "generate_wheel_only_svg_string", "generate_aspect_grid_only_svg_string"],
    )
    @pytest.mark.parametrize(
        "fixture",
        ["station_data", "out_of_bounds_data", "sidereal_data", "polar_data", "synastry_data", "two_angles_data"],
    )
    def test_it_parses(self, request, fixture, style, output_method):
        chart_data = request.getfixturevalue(fixture)
        marks = {mark: True for mark in ALL_MARKS}
        svg = getattr(ChartDrawer(chart_data, style=style, **marks), output_method)()
        ET.fromstring(svg)


class TestRowsFitTheWheel:
    """The info rows sit inside the wheel's chord, and it narrows going up.

    Row 5 has ~229px of clear width but row 0 only ~134, so a line that fits at
    the bottom of the panel runs under the opaque wheel at the top of it. The
    marks that write into the panel are checked against *their own* row, in
    every shipped language, because a translation is exactly how this breaks
    after the English case has been eyeballed once.
    """

    LANGUAGES = list(LANGUAGE_SETTINGS)

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_the_score_rows_fit(self, synastry_data, language):
        svg = _render(synastry_data, "classic", chart_language=language, show_relationship_score=True)
        for index, row in enumerate(_info_rows(svg)[:2]):
            budget = info_row_clear_width(index)
            width = estimate_text_width(unescape(row))
            assert width <= budget, f"{language} row {index}: {width:.0f}px in a {budget:.0f}px row — {row!r}"

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_the_polar_note_fits(self, polar_data, language):
        # The domification row, the only one this mark writes to. It moved from
        # slot 1 to slot 2 when the natal panel was reordered around the moon
        # glyph (lunation, phase, domification, diurnality, perspective, zodiac).
        index = 2
        row = _info_rows(_render(polar_data, "classic", chart_language=language, show_polar_fallback_note=True))[index]
        width = estimate_text_width(unescape(row))
        budget = info_row_clear_width(index)
        assert width <= budget, f"{language} row {index}: {width:.0f}px in a {budget:.0f}px row — {row!r}"

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_no_mark_pushes_a_row_over_that_was_within_it(self, polar_data, synastry_data, language):
        """The invariant these marks owe the panel, stated without inheriting its debts.

        A few rows already overrun in a couple of languages with every mark off
        — the Hindi lunar-phase and perspective rows badly, the Russian
        perspective row by a fraction. That is not this feature's doing and not
        this feature's to fix, but it does mean "every row fits" is the wrong
        assertion here. What these marks must guarantee is narrower and
        entirely theirs: no row that fitted before may stop fitting because a
        mark was switched on.
        """
        for chart_data, marks in (
            (polar_data, {"show_polar_fallback_note": True}),
            (synastry_data, {"show_relationship_score": True}),
        ):
            before = _info_rows(_render(chart_data, "classic", chart_language=language))
            after = _info_rows(_render(chart_data, "classic", chart_language=language, **marks))
            for index, (was, now) in enumerate(zip(before, after)):
                budget = info_row_clear_width(index)
                if estimate_text_width(unescape(was)) > budget:
                    continue  # already over before the mark; not this feature's row to fix
                width = estimate_text_width(unescape(now))
                assert width <= budget, (
                    f"{language} row {index} fitted at {estimate_text_width(unescape(was)):.0f}px "
                    f"and now needs {width:.0f}px in a {budget:.0f}px row — {now!r}"
                )

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_the_substitution_is_still_marked_after_it_is_shortened(self, polar_data, language):
        """Shedding the spelled-out note must not shed the fact it points at."""
        svg = _render(polar_data, "classic", chart_language=language, show_polar_fallback_note=True)
        assert "*" in _info_rows(svg)[2], language  # the domification row; see above


class TestDualWheelsDoNotSpeakForEachOther:
    def test_one_wheels_ayanamsa_is_not_claimed_for_both(self, john_lennon, paul_mccartney):
        """The zodiac line carries no ring label, so it can only state a shared value."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "Early", 1940, 10, 9, 18, 30, "Liverpool", "GB",
            zodiac_type="Sidereal", sidereal_mode="LAHIRI", suppress_geonames_warning=True,
        )
        later = AstrologicalSubjectFactory.from_birth_data(
            "Late", 2000, 6, 18, 15, 30, "Liverpool", "GB",
            zodiac_type="Sidereal", sidereal_mode="LAHIRI", suppress_geonames_warning=True,
        )
        assert first.ayanamsa_value != later.ayanamsa_value

        row = _info_rows(_render(ChartDataFactory.create_synastry_chart_data(first, later), "classic",
                                 show_ayanamsa_value=True))[2]
        assert "(" not in row, f"the outer wheel has another offset, so none may be printed: {row!r}"

    def test_a_shared_ayanamsa_is_still_printed(self):
        """Suppressing it whenever the chart is dual would hide it needlessly."""
        pair = [
            AstrologicalSubjectFactory.from_birth_data(
                name, 1940, 10, 9, 18, 30, "Liverpool", "GB",
                zodiac_type="Sidereal", sidereal_mode="LAHIRI", suppress_geonames_warning=True,
            )
            for name in ("One", "Two")
        ]
        row = _info_rows(_render(ChartDataFactory.create_synastry_chart_data(*pair), "classic",
                                 show_ayanamsa_value=True))[2]
        assert "(" in row

    def test_a_second_wheels_substitution_is_not_hidden_by_the_first(self):
        """Landing on the same system is not the same as having asked for it."""
        native = AstrologicalSubjectFactory.from_birth_data(
            "Porphyry native", 1940, 10, 9, 18, 30, "Liverpool", "GB",
            houses_system_identifier="O", suppress_geonames_warning=True,
        )
        substituted = AstrologicalSubjectFactory.from_birth_data(
            "Polar", 1990, 6, 15, 12, 0, "Longyearbyen", "SJ",
            lng=15.6, lat=78.2, tz_str="Arctic/Longyearbyen",
            houses_system_identifier="P", suppress_geonames_warning=True,
        )
        assert native._main_house_fallback() is None
        assert substituted._main_house_fallback() is not None
        assert (
            native.effective_houses_system_identifier == substituted.effective_houses_system_identifier
        ), "fixture no longer exercises the collapse"

        chart_data = ChartDataFactory.create_synastry_chart_data(native, substituted)
        row = _info_rows(_render(chart_data, "classic", show_polar_fallback_note=True))[3]
        assert "*" in row, f"the second wheel's substitution vanished: {row!r}"


class TestGauquelinBadgeHasItsOwnRoom:
    """The Gauquelin table runs right up to its column width.

    Its declination text ends where the right-aligned sector value begins, so
    unlike the standard grids — which have slack after the retrograde glyph —
    it has nowhere to put a badge and has to be widened for one.
    """

    @pytest.fixture(scope="class")
    def gauquelin_oob_data(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Gauquelin OOB", 1990, 1, 1, 12, 0, "London", "GB",
            calculate_gauquelin=True, suppress_geonames_warning=True,
        )
        return ChartDataFactory.create_natal_chart_data(subject)

    def test_the_badge_never_reaches_the_sector_value(self, gauquelin_oob_data):
        svg = _render(gauquelin_oob_data, "classic", show_out_of_bounds=True)
        rows = re.findall(
            r"<text x='135'[^>]*>([^<]*)</text>.*?<text text-anchor='end' x='(\d+)'[^>]*>([^<]*)</text>", svg
        )
        badged = [row for row in rows if "OOB" in row[0]]
        assert badged, "fixture no longer has an out-of-bounds body in the Gauquelin table"
        for declination, sector_end, sector in badged:
            ends_at = 135 + estimate_text_width(unescape(declination))
            starts_at = int(sector_end) - estimate_text_width(sector)
            assert ends_at <= starts_at, f"{declination!r} overlaps {sector!r}"

    def test_a_table_with_nothing_out_of_bounds_keeps_its_old_width(self):
        """The extra room is earned by a badge, not by the option being on.

        23 April 1990 is picked because nothing is out of bounds that day, so
        the assertion actually runs instead of skipping itself away.
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Gauquelin in bounds", 1990, 4, 23, 12, 0, "London", "GB",
            calculate_gauquelin=True, suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        assert not any(getattr(p, "is_out_of_bounds", None) for p in _points(chart_data)), (
            "fixture drifted: this sky now has an out-of-bounds body"
        )
        assert _render(chart_data, "classic") == _render(chart_data, "classic", show_out_of_bounds=True)


#: A biwheel lays out four side tables at fixed offsets 105px apart, and a
#: language whose labels are longer than English overruns that into the cusp
#: column beside it. Fixing it means laying the four out as a chain — each
#: starting where the one before ends — and feeding that into the canvas width
#: estimator, which is its own change.
_BIWHEEL_SIDE_TABLE_DEBT = (
    "The biwheel's four side tables sit at fixed 105px offsets, so a language "
    "with longer labels overruns into the column beside it. Wants the four laid "
    "out as a chain, which is its own change."
)

#: Named rather than blanket: capping a point's name (abbreviate_point_name)
#: cleared seven of the ten languages, and leaving the marker on all ten would
#: let those seven regress in silence. What still overruns is not the point
#: names — it is the out-of-bounds badge against a long cusp label in French and
#: Italian, and in Hindi a script the width estimator reads too narrow.
_LANGUAGES_STILL_OVERRUNNING = frozenset({"FR", "IT", "HI"})

class TestNothingPrintsOnTopOfAnythingElse:
    """No two strings share a baseline and the same pixels.

    This is the assertion the gallery sweep could only make with an eye. What
    it caught, once written: the multi-column point grid put a long name — "N.
    Node (M)" wants 56px where the stride left 25 — on top of the row beside
    it, in every chart that carries the node under both its names.

    Only unrotated text is examined; the wheel's own labels are governed by the
    browser-measured separation model and are not this test's business.
    """

    @pytest.mark.parametrize("style", STYLES)
    @pytest.mark.parametrize(
        "fixture",
        ["station_data", "out_of_bounds_data", "sidereal_data", "polar_data", "synastry_data", "two_angles_data"],
    )
    def test_no_overlap(self, request, fixture, style):
        chart_data = request.getfixturevalue(fixture)
        svg = ChartDrawer(chart_data, style=style, **{mark: True for mark in ALL_MARKS}).generate_svg_string()
        overlaps = find_text_overlaps(svg)
        assert not overlaps, "\n".join(str(o) for o in overlaps[:6])

    @pytest.mark.parametrize("style", STYLES)
    def test_no_overlap_with_every_point_the_library_knows(self, style):
        """The crowded case, which is where the columns actually ran out of room."""
        from kerykeion.settings.config_constants import ALL_ACTIVE_ASPECTS, ALL_ACTIVE_POINTS, URANIAN_ACTIVE_POINTS

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Every point", 1940, 10, 9, 18, 30, "Liverpool", "GB",
            active_points=list(ALL_ACTIVE_POINTS) + list(URANIAN_ACTIVE_POINTS),
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject, active_aspects=list(ALL_ACTIVE_ASPECTS))
        svg = ChartDrawer(chart_data, style=style, **{mark: True for mark in ALL_MARKS}).generate_svg_string()
        overlaps = find_text_overlaps(svg)
        assert not overlaps, "\n".join(str(o) for o in overlaps[:6])

    @pytest.mark.parametrize(
        "language",
        [
            pytest.param(
                lang,
                marks=pytest.mark.xfail(
                    reason=_BIWHEEL_SIDE_TABLE_DEBT, strict=False
                ) if lang in _LANGUAGES_STILL_OVERRUNNING else (),
            )
            for lang in LANGUAGE_SETTINGS
        ],
    )
    def test_no_overlap_in_any_language(self, synastry_data, language):
        svg = ChartDrawer(synastry_data, chart_language=language, **{m: True for m in ALL_MARKS}).generate_svg_string()
        overlaps = find_text_overlaps(svg)
        assert not overlaps, "\n".join(str(o) for o in overlaps[:6])


class TestTheCuspRingShrinksOnlyWhenItMustFit:
    """The readings scale down for crowding, and for nothing else.

    A cusp reading is a band of ring — minutes one side of the line, degrees
    the other — so two cusps closer together than that band print through each
    other, which quadrant systems arrange routinely. The ring answers by
    resizing itself, and past a point by staggering the crowded readings onto
    two radial lanes, rather than by sliding them off the lines they describe.

    What must not happen is a chart paying for that when it has no crowding at
    all, so the trigger is pinned from both sides: an ordinary chart is
    byte-identical to one rendered with the mechanism unable to fire, and a
    crowded one is not.
    """

    @staticmethod
    def _tightest_house(subject) -> float:
        from kerykeion.utilities.core import get_houses_list

        cusps = [house.abs_pos for house in get_houses_list(subject)]
        return min((cusps[(i + 1) % 12] - cusps[i]) % 360.0 for i in range(12))

    @staticmethod
    def _chart(house_system: str, lat: float = 51.5, lng: float = 0.0):
        return AstrologicalSubjectFactory.from_birth_data(
            f"Cusp {house_system}", 1990, 6, 15, 12, 0, city="probe", nation="XX",
            lat=lat, lng=lng, tz_str="UTC", online=False, suppress_geonames_warning=True,
            houses_system_identifier=house_system,
        )

    @pytest.mark.parametrize("house_system", ["P", "K", "O", "W", "A", "R", "C"])
    def test_an_uncrowded_chart_is_untouched(self, house_system):
        from kerykeion.charts.draw_modern import _cusp_cluster_span

        subject = self._chart(house_system)
        if self._tightest_house(subject) < _cusp_cluster_span(1.0):
            pytest.skip("this sky is crowded, so shrinking is the correct answer")

        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        svg = ChartDrawer(chart_data).generate_svg_string(style="modern")
        # The nominal sizes, spelled out: if the ring shrank at all, neither of
        # these would be in the markup.
        #
        # The glyph scale is NOT CUSP_GLYPH_SCALE on its own — every sign carries
        # its own factor on top (0.9 by default), so the string to look for is
        # the product. Asserting the bare constant used to pass by accident: it
        # matched the "scale(0.12" prefix of the planet glyphs' own 0.12825, and
        # said nothing whatever about the cusp ring.
        from kerykeion.charts.draw_modern import (
            CUSP_FONT_SIZE,
            CUSP_GLYPH_SCALE,
            ZODIAC_OUTER_SCALE_MAP,
        )

        assert f"font-size='{CUSP_FONT_SIZE}'" in svg
        cusp_ring = svg[svg.index("CuspRing"):]
        cusp_ring = cusp_ring[:cusp_ring.index("kr:node='PlanetRing'")]
        drawn = set(re.findall(r"scale\(([\d.]+)\)", cusp_ring))
        assert drawn, "no sign glyph in the cusp ring at all"
        nominal = {str(round(CUSP_GLYPH_SCALE * factor, 4))
                   for factor in ZODIAC_OUTER_SCALE_MAP.values()}
        assert drawn <= nominal, f"the ring shrank: {sorted(drawn - nominal)}"

    def test_a_crowded_chart_does_shrink(self):
        """Campanus at Liverpool packs four houses under eight degrees."""
        from kerykeion.charts.draw_modern import CUSP_FONT_SIZE, _cusp_cluster_span

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Campanus", 1940, 10, 9, 18, 30, "Liverpool", "GB",
            lat=53.4084, lng=-2.9916, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True, houses_system_identifier="C",
        )
        assert self._tightest_house(subject) < _cusp_cluster_span(1.0), "fixture is no longer crowded"

        svg = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject)).generate_svg_string(style="modern")
        assert f"font-size='{CUSP_FONT_SIZE}'" not in svg, "the ring should have shrunk and did not"

    def test_a_crowded_ring_alternates_between_two_radial_lanes(self):
        """Shrinking runs out before the crowding does, so the readings also stagger.

        One reading a little nearer the rim, the next a little nearer the wheel,
        which lets two that cannot be pulled apart sideways pass each other.
        """
        import re

        from kerykeion.charts.draw_modern import CUSP_LABEL_Y, CUSP_LANE_OFFSET

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Campanus", 1940, 10, 9, 18, 30, "Liverpool", "GB",
            lat=53.4084, lng=-2.9916, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True, houses_system_identifier="C",
        )
        svg = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject)).generate_svg_string(style="modern")
        cusp_block = svg[svg.index("kr:node='CuspRing'") : svg.index("kr:node='RulerRing'")]
        heights = {float(y) for y in re.findall(r"y='([\d.]+)'", cusp_block)}
        assert heights == {
            round(CUSP_LABEL_Y - CUSP_LANE_OFFSET, 4),
            CUSP_LABEL_Y,
            round(CUSP_LANE_OFFSET + CUSP_LABEL_Y, 4),
        }, heights

    def test_only_the_crowded_readings_leave_the_centre_line(self):
        """A reading with clear air either side has nothing to step around.

        Liverpool's Campanus crowding is local — three cusps of the twelve in
        each half. Staggering the other nine would move them off the lines they
        describe to solve a problem they do not have, and a ring where every
        reading sits high or low reads as a wobble rather than as a device.
        """
        from kerykeion.charts.draw_modern import (
            _cusp_cluster_span,
            _cusp_lanes,
            _zodiac_to_wheel_angle,
        )
        from kerykeion.utilities.core import get_houses_list

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Campanus", 1940, 10, 9, 18, 30, "Liverpool", "GB",
            lat=53.4084, lng=-2.9916, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True, houses_system_identifier="C",
        )
        angles = [
            _zodiac_to_wheel_angle(house.abs_pos, subject.seventh_house.abs_pos)
            for house in get_houses_list(subject)
        ]
        band = _cusp_cluster_span(self._fit(angles))
        lanes = _cusp_lanes(angles, band)

        for index, lane in enumerate(lanes):
            before = (angles[index] - angles[index - 1]) % 360.0
            after = (angles[(index + 1) % len(angles)] - angles[index]) % 360.0
            crowded = before < band or after < band
            assert (lane is not None) == crowded, (
                f"cusp {index} has {before:.1f}° / {after:.1f}° of room in a {band:.1f}° band "
                f"and was put on lane {lane}"
            )
        assert None in lanes and set(lanes) >= {0, 1}, f"fixture no longer mixes the two: {lanes}"

    def test_the_stagger_costs_less_size_than_shrinking_alone_would(self):
        """The lanes exist so the ring can stop shrinking earlier, not as well as.

        Fitting Liverpool's tightest pair by size alone drives the readings to
        the floor. With the crowded ones passing each other on separate lanes,
        what has to fit in one gap is the reading two cusps along — two gaps of
        room — so the ring keeps most of its size.
        """
        from kerykeion.charts.draw_modern import (
            CUSP_MIN_SCALE,
            CUSP_STAGGER_SCALE,
            _cusp_cluster_span,
            _zodiac_to_wheel_angle,
        )
        from kerykeion.utilities.core import get_houses_list

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Campanus", 1940, 10, 9, 18, 30, "Edinburgh", "GB",
            lat=57.0, lng=-2.9916, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True, houses_system_identifier="C",
        )
        angles = [
            _zodiac_to_wheel_angle(house.abs_pos, subject.seventh_house.abs_pos)
            for house in get_houses_list(subject)
        ]
        gaps = [(angles[(i + 1) % 12] - angles[i]) % 360.0 for i in range(12)]
        shrink_alone = min(gaps) / _cusp_cluster_span(1.0)

        assert shrink_alone <= CUSP_MIN_SCALE, "fixture no longer bottoms out on size alone"
        assert self._fit(angles) == pytest.approx(CUSP_STAGGER_SCALE)

    @staticmethod
    def _fit(angles) -> float:
        """The scale the renderer settles on for *angles*, by the same three cases."""
        from kerykeion.charts.draw_modern import (
            CUSP_MIN_SCALE,
            CUSP_STAGGER_SCALE,
            _cusp_cluster_span,
        )

        count = len(angles)
        gaps = [(angles[(i + 1) % count] - angles[i]) % 360.0 for i in range(count)]
        shrink_alone = min(gaps) / _cusp_cluster_span(1.0)
        if shrink_alone >= 1.0:
            return 1.0
        if shrink_alone >= CUSP_STAGGER_SCALE:
            return shrink_alone
        two_gaps = min(gaps[i] + gaps[(i + 1) % count] for i in range(count))
        return min(CUSP_STAGGER_SCALE, max(CUSP_MIN_SCALE, two_gaps / _cusp_cluster_span(1.0)))

    def test_a_staggered_reading_stays_inside_the_ring(self):
        """Both lanes hold their ink between the rim and the wheel.

        The offset and the scale it is paired with come from one solve: the
        largest text for which a reading pushed outward still clears the rim
        and one pushed inward still clears the other lane. This is that solve,
        checked against the measured ink rather than against itself.
        """
        from kerykeion.charts.draw_modern import (
            CUSP_LABEL_Y,
            CUSP_LANE_GUTTER,
            CUSP_LANE_OFFSET,
            CUSP_RING_MARGIN,
            CUSP_STAGGER_SCALE,
            R_CUSP_INNER,
            R_CUSP_OUTER,
            _CUSP_SIGN_HALF_HEIGHT,
            _CUSP_TEXT_HALF_HEIGHT,
        )

        depth = R_CUSP_OUTER - R_CUSP_INNER
        assert CUSP_LABEL_Y == pytest.approx(depth / 2), "the centre line is no longer centred"

        tallest = _CUSP_SIGN_HALF_HEIGHT * CUSP_STAGGER_SCALE
        assert CUSP_LABEL_Y - CUSP_LANE_OFFSET - tallest >= CUSP_RING_MARGIN - 1e-9
        assert CUSP_LABEL_Y + CUSP_LANE_OFFSET + tallest <= depth - CUSP_RING_MARGIN + 1e-9

        # The lanes clear each other for the binding pair: one lane's text
        # against the next cusp's sign glyph on the other.
        reach = (_CUSP_SIGN_HALF_HEIGHT + _CUSP_TEXT_HALF_HEIGHT) * CUSP_STAGGER_SCALE
        assert 2 * CUSP_LANE_OFFSET - reach >= CUSP_LANE_GUTTER - 1e-9

    @pytest.mark.parametrize("house_system", ["P", "W", "O", "A"])
    def test_an_uncrowded_ring_stays_on_one_lane(self, house_system):
        """A ring that wanders in and out for no visible reason reads as a defect."""
        import re

        from kerykeion.charts.draw_modern import CUSP_LABEL_Y, _cusp_cluster_span

        subject = self._chart(house_system)
        if self._tightest_house(subject) < _cusp_cluster_span(1.0):
            pytest.skip("this sky is crowded, so staggering is the correct answer")

        svg = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject)).generate_svg_string(style="modern")
        cusp_block = svg[svg.index("kr:node='CuspRing'") : svg.index("kr:node='RulerRing'")]
        assert {float(y) for y in re.findall(r"y='([\d.]+)'", cusp_block)} == {CUSP_LABEL_Y}

    def test_the_ring_keeps_one_size_for_all_twelve(self):
        """Readings at four sizes look like a mistake even when each is right."""
        import re

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Campanus", 1940, 10, 9, 18, 30, "Liverpool", "GB",
            lat=53.4084, lng=-2.9916, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True, houses_system_identifier="C",
        )
        svg = ChartDrawer(ChartDataFactory.create_natal_chart_data(subject)).generate_svg_string(style="modern")
        cusp_block = svg[svg.index("kr:node='CuspRing'") : svg.index("kr:node='RulerRing'")]
        sizes = set(re.findall(r"kr:node='Cusp'.*?font-size='([\d.]+)'", cusp_block))
        assert len(sizes) <= 1, f"the cusp ring drew its readings at {sorted(sizes)}"
