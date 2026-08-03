# -*- coding: utf-8 -*-
"""
Diurnality Line SVG Tests

The bottom-left info panel reports whether the Sun stood above or below the
horizon. These tests pin the four things that are easy to get wrong and hard to
notice in a 140 KB SVG:

    - It says the right thing, and it says it neutrally ("Diurnality: Nocturnal"
      rather than any one tradition's vocabulary for what follows from it).
    - It is *absent*, not guessed, where it has no referent: a heliocentric chart
      does not include the Sun at all (it is the centre body), and a midpoint
      composite represents no single sky. A default-to-day helper exists in
      utilities and would silently label both as diurnal.
    - Two-wheel charts carry both values, each behind its own wheel's name. A
      bare "Nocturnal" on a biwheel is worse than no line at all, because the
      reader cannot tell which chart it describes.
    - Nothing moves to make room for it except the moon glyph, and only when a
      line was actually produced — the rows themselves never shift, so a caller
      who opts out gets the panel exactly as it was.

Usage:
    pytest tests/core/test_diurnality_svg.py -v
"""

import re

import pytest

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    CompositeSubjectFactory,
    PlanetaryReturnFactory,
)
from kerykeion.charts.chart_drawer import (
    DIURNALITY_ROW_CLEAR_WIDTH,
    ChartDrawer,
    estimate_text_width,
)

def _row_re(index: int):
    return re.compile(rf"Bottom_Left_Text_{index}'[^>]*>([^<]*)<")
BLOCK_TRANSFORM = re.compile(r"Bottom_Left_Text' transform='translate\(0,([-\d.]+)\)'")
MOON_TRANSFORM = re.compile(r"Lunar_Phase' transform='translate\(10,([-\d.]+)\)'")

# The layout the panel had before the diurnality line existed. Hard-coded rather
# than derived so that a change to either constant has to be an explicit edit here.
LAYOUT_WITHOUT_LINE = ("0", "518")
# With the line: the block does not move at all; only the glyph drops.
LAYOUT_WITH_LINE = ("0", "532")


def _subject(name="John", **kwargs):
    params = dict(
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        city="Liverpool",
        nation="GB",
        lat=53.41058,
        lng=-2.97794,
        tz_str="Europe/London",
        online=False,
    )
    params.update(kwargs)
    return AstrologicalSubjectFactory.from_birth_data(name, **params)


def _composite(kind: str):
    """A midpoint or Davison composite of the same two subjects."""
    factory = CompositeSubjectFactory(
        _subject(), _subject("Paul", year=1942, month=6, day=18, hour=8, minute=0)
    )
    if kind == "Midpoint":
        return factory.get_midpoint_composite_subject_model()
    return factory.get_davison_composite_subject_model()


def _render(chart_data, **drawer_kwargs) -> str:
    return ChartDrawer(chart_data, **drawer_kwargs).generate_svg_string(minify=False)


def _row(svg: str, index: int = 5) -> str:
    """The text of a bottom-left row. Composites put diurnality in row 4."""
    match = _row_re(index).search(svg)
    assert match is not None, f"the Bottom_Left_Text_{index} node is missing from the template"
    return match.group(1)


def _layout(svg: str) -> tuple:
    block = BLOCK_TRANSFORM.search(svg)
    moon = MOON_TRANSFORM.search(svg)
    assert block and moon
    return block.group(1), moon.group(1)


def _solar_return():
    """A natal chart and its next solar return, computed offline."""
    natal = _subject()
    factory = PlanetaryReturnFactory(
        natal, city="Liverpool", nation="GB", lat=53.41058, lng=-2.97794,
        tz_str="Europe/London", online=False,
    )
    return natal, factory.next_return_from_date(2024, 1, 1, return_type="Solar")


class TestDiurnalityValue:
    """The line states the chart's diurnality, in neutral wording."""

    def test_nocturnal_chart(self):
        subject = _subject()
        assert subject.is_diurnal is False, "fixture must be a night chart"
        svg = _render(ChartDataFactory.create_natal_chart_data(subject))
        assert _row(svg) == "Diurnality: Nocturnal"

    def test_diurnal_chart(self):
        subject = _subject(hour=12, minute=0)
        assert subject.is_diurnal is True, "fixture must be a day chart"
        svg = _render(ChartDataFactory.create_natal_chart_data(subject))
        assert _row(svg) == "Diurnality: Diurnal"

    def test_wording_stays_school_neutral(self):
        """Every tradition agrees on where the Sun was; only some name it "sect"."""
        svg = _render(ChartDataFactory.create_natal_chart_data(_subject()))
        assert "sect" not in _row(svg).lower()
        assert "hairesis" not in _row(svg).lower()

    # Every shipped language, both values. Asserting the exact rendered string
    # rather than "does not contain the English one": a language whose
    # translation legitimately coincides with English would fail that test while
    # being perfectly correct, and a language that translates only one of the two
    # values would pass it. The table is the assertion — it pins what ships.
    @pytest.mark.parametrize(
        ("language", "label", "diurnal", "nocturnal"),
        [
            ("EN", "Diurnality", "Diurnal", "Nocturnal"),
            ("IT", "Diurnalità", "Diurno", "Notturno"),
            ("FR", "Diurnalité", "Diurne", "Nocturne"),
            ("ES", "Diurnidad", "Diurno", "Nocturno"),
            ("PT", "Diurnidade", "Diurno", "Noturno"),
            ("DE", "Tag/Nacht", "Tag", "Nacht"),
            ("RU", "День/Ночь", "День", "Ночь"),
            ("TR", "Gündüz/Gece", "Gündüz", "Gece"),
            ("CN", "晝夜", "日間", "夜間"),
            ("HI", "दिवा/रात्रि", "दिवा", "रात्रि"),
        ],
    )
    def test_every_language_renders_both_values(self, language, label, diurnal, nocturnal):
        day = _render(ChartDataFactory.create_natal_chart_data(_subject(hour=12)), chart_language=language)
        night = _render(ChartDataFactory.create_natal_chart_data(_subject()), chart_language=language)
        assert _row(day) == f"{label}: {diurnal}"
        assert _row(night) == f"{label}: {nocturnal}"


class TestDiurnalityOmitted:
    """Where diurnality has no meaning, the line is absent rather than guessed.

    Each case also asserts the layout, because the two go together: the lift that
    makes room for the line must key off whether a line was produced, not off the
    flag. Keying it off the flag lifted the block on exactly these charts — the
    ones the code special-cases — and opened a gap where it meant to close one.
    """

    def test_heliocentric_chart_does_not_include_the_sun(self):
        subject = _subject(perspective_type="Heliocentric")
        svg = _render(ChartDataFactory.create_natal_chart_data(subject))
        assert _row(svg) == ""
        assert _layout(svg) == LAYOUT_WITHOUT_LINE

    def test_midpoint_composite_has_no_single_sky(self):
        composite = _composite("Midpoint")
        assert composite.is_diurnal is None, "a midpoint composite must not claim a diurnality"
        svg = _render(ChartDataFactory.create_composite_chart_data(composite))
        # Row 4, not 5: the composite renderer puts it in the slot it already
        # left blank, so that no empty row opens up above it. Reading row 5 here
        # would pass no matter what this renderer does.
        assert _row(svg, 4) == ""
        assert _layout(svg) == LAYOUT_WITHOUT_LINE

    def test_a_davison_composite_does_have_one(self):
        """The counterpart that makes the test above mean something.

        A Davison composite is a real moment, so it carries a real value and the
        line must appear. Without this, blanking the composite renderer's row —
        or defaulting a `None` to day — passes unnoticed.
        """
        composite = _composite("Davison")
        assert isinstance(composite.is_diurnal, bool)
        svg = _render(ChartDataFactory.create_composite_chart_data(composite))
        assert _row(svg, 4) == f"Diurnality: {'Diurnal' if composite.is_diurnal else 'Nocturnal'}"
        # Row 4 already existed, so nothing had to move for it.
        assert _layout(svg) == LAYOUT_WITHOUT_LINE


class TestDiurnalityOnDualCharts:
    """Both wheels are reported, each behind its own name."""

    def test_transit_labels_both_wheels(self):
        natal = _subject()
        transit = _subject("Now", year=2024, month=6, day=15, hour=12, minute=0)
        row = _row(_render(ChartDataFactory.create_transit_chart_data(natal, transit)))
        assert "Natal Nocturnal" in row
        assert "Transit Diurnal" in row
        # No "Diurnality:" heading here, unlike the single-wheel row: the wheel
        # names already say what each value belongs to, and the label would push
        # the line under the wheel graphics. See build_dual_diurnality_info.
        assert not row.startswith("Diurnality")

    def test_synastry_labels_each_partner_by_name(self):
        john = _subject()
        paul = _subject("Paul", year=1942, month=6, day=18, hour=8, minute=0)
        row = _row(_render(ChartDataFactory.create_synastry_chart_data(john, paul)))
        assert "John Nocturnal" in row
        assert "Paul Diurnal" in row

    # The worst case, not a lucky fixture: two nocturnal charts (the longest
    # value pair in English), names chosen to be wide rather than merely long,
    # and the longest wheel labels the panel ships. An earlier version used one
    # convenient synastry and passed while eight real combinations overran.
    @pytest.mark.parametrize("language", ["EN", "IT", "RU", "DE", "CN"])
    def test_the_widest_dual_row_still_clears_the_wheel(self, language):
        """The row sits where the wheel's chord has closed in on it.

        Measured in pixels, not characters. The previous version of this test
        capped the row at 48 characters, which is not a width: measured advances
        across this panel's own corpus run from 2.7 to 9.9 px per character, so
        the cap authorised anything from 130px to 476px. A 38-character row of
        ideographs measured 250px against 228px of clear width and ran under the
        wheel while this test stayed green in all four languages.
        """
        widest = [
            ChartDataFactory.create_synastry_chart_data(
                _subject("Alessandra Giovanna Bianchi"),
                _subject("Massimiliano Ferrari", hour=23, minute=0),
            ),
            # Ideographs: full-width by design, so the same character count is
            # nearly twice the pixels. This is the case the old cap could not see.
            ChartDataFactory.create_synastry_chart_data(
                _subject("阿部寛田中太郎彦仁美"),
                _subject("山田花子鈴木一郎次郎", hour=23, minute=0),
            ),
            # Capitals are the other class a half-em average gets wrong; an
            # all-capitals name measured 254px against a 225px estimate.
            ChartDataFactory.create_synastry_chart_data(
                _subject("MARIAGRAZIA" * 3), _subject("GIANFRANCO" * 3, hour=23, minute=0)
            ),
            ChartDataFactory.create_transit_chart_data(
                _subject(), _subject("Now", year=2024, month=6, day=15, hour=12, minute=0)
            ),
            ChartDataFactory.create_progression_chart_data(
                _subject(), _subject("P", year=2000, month=10, day=9, hour=18, minute=30)
            ),
            # The longest wheel label the panel ships: "Solar Return" beats
            # "Transit" by five characters, and its translations more.
            ChartDataFactory.create_return_chart_data(*_solar_return()),
        ]
        for data in widest:
            row = _row(_render(data, chart_language=language))
            width = estimate_text_width(row)
            assert width <= DIURNALITY_ROW_CLEAR_WIDTH, (
                f"{language}: {width:.1f}px will overrun the wheel's {DIURNALITY_ROW_CLEAR_WIDTH}px: {row!r}"
            )

    def test_only_the_first_word_of_a_name_reaches_the_row(self):
        """As the comparison grids do to the same two names."""
        john = _subject("Maria Alessandra Giovanna Bianchi")
        paul = _subject("Massimiliano Ferrari-Castiglione", year=1942, month=6, day=18, hour=8, minute=0)
        row = _row(_render(ChartDataFactory.create_synastry_chart_data(john, paul)))
        assert "Maria Nocturnal" in row
        assert "Alessandra" not in row

    def test_a_name_is_cut_only_when_it_would_not_fit(self):
        """The cut is a width budget, not a fixed cap.

        Both halves matter: a ten-character name that fits must survive whole —
        an earlier fixed eight-character cap mangled names it had room for — and
        one that does not fit must lose its tail.
        """
        fits = _row(
            _render(
                ChartDataFactory.create_synastry_chart_data(
                    _subject("Alessandro"), _subject("Antonio", hour=23, minute=0)
                )
            )
        )
        assert "Alessandro Nocturnal" in fits and "…" not in fits

        cut = _row(
            _render(
                ChartDataFactory.create_synastry_chart_data(
                    _subject("Massimiliano" * 4), _subject("Gianfranco" * 4, hour=23, minute=0)
                )
            )
        )
        assert "…" in cut
        assert estimate_text_width(cut) <= DIURNALITY_ROW_CLEAR_WIDTH

    def test_a_name_with_markup_characters_cannot_break_the_svg(self):
        """The synastry line embeds user-controlled names, so it must be escaped.

        Single token on purpose: names are cut at a word boundary, so markup
        after the first space would never reach the row and the test would pass
        without exercising anything.
        """
        john = _subject("A&B<script>x")
        paul = _subject("Paul", year=1942, month=6, day=18, hour=8, minute=0)
        svg = _render(ChartDataFactory.create_synastry_chart_data(john, paul))
        assert "&amp;" in _row(svg)
        assert "<script>" not in svg
        from xml.etree import ElementTree

        ElementTree.fromstring(svg)  # raises if the escaping let the markup through


class TestDiurnalityLayout:
    """What moves when the line appears, and what must not.

    Includes the switched-off case: opting out has to restore the panel exactly.
    """

    @pytest.mark.parametrize("hour", [12, 18])
    def test_line_is_empty(self, hour):
        svg = _render(
            ChartDataFactory.create_natal_chart_data(_subject(hour=hour)),
            show_diurnality=False,
        )
        assert _row(svg) == ""

    def test_block_and_moon_return_to_their_original_offsets(self):
        data = ChartDataFactory.create_natal_chart_data(_subject())
        assert _layout(_render(data, show_diurnality=False)) == LAYOUT_WITHOUT_LINE

    def test_the_glyph_keeps_its_gap_below_the_last_row(self):
        """Read from the rendered output, not restated from the constants.

        The gap is read from rendered output on both sides. Asserting it as
        `532 - 522 == 518 - 508` — as an earlier revision did — is a tautology on
        integer literals that holds whatever the code does.
        """
        data = ChartDataFactory.create_natal_chart_data(_subject())
        off_block, off_moon = (float(v) for v in _layout(_render(data, show_diurnality=False)))
        on_block, on_moon = (float(v) for v in _layout(_render(data, show_diurnality=True)))
        # Last visible row: y=508 without the line, y=522 with it.
        assert off_moon - (off_block + 508.0) == pytest.approx(10.0)
        assert on_moon - (on_block + 522.0) == pytest.approx(10.0)

    def test_showing_the_line_moves_the_glyph_and_nothing_else(self):
        """The five pre-existing rows must not move.

        They sit inside the wheel's chord and the lower a row is the more clear
        width it has, so shifting the block upwards to make room narrows every
        row above — an earlier revision did exactly that and pushed a default
        English progression row under the wheel. The new row needs no room made
        for it; only the moon glyph is in its way.
        """
        data = ChartDataFactory.create_natal_chart_data(_subject())
        assert _layout(_render(data, show_diurnality=False)) == LAYOUT_WITHOUT_LINE
        assert _layout(_render(data, show_diurnality=True)) == LAYOUT_WITH_LINE

    def test_off_leaves_the_other_rows_untouched(self):
        """Nothing but the empty node itself may differ when the line is off."""
        data = ChartDataFactory.create_natal_chart_data(_subject())
        svg_off = _render(data, show_diurnality=False)
        rows = re.findall(r"Bottom_Left_Text_(\d)'[^>]*>([^<]*)<", svg_off)
        assert rows[-1] == ("5", ""), "the node exists but carries nothing"
        assert all(text for _, text in rows[:-1]), "the other rows are untouched"


class TestDiurnalityOnOtherRenderers:
    """The renderers the other classes do not reach.

    Every one of these rows survived a mutation that blanked it: the SVG
    baselines for composites, returns and progressions are compared by a
    text-blind comparator, so they pin nothing here.
    """

    def test_single_wheel_return_carries_its_own(self):
        _, solar = _solar_return()
        row = _row(_render(ChartDataFactory.create_single_wheel_return_chart_data(solar)))
        assert row.startswith("Diurnality: "), row

    def test_dual_wheel_return_names_both_and_labels_the_return_correctly(self):
        natal, solar = _solar_return()
        row = _row(_render(ChartDataFactory.create_return_chart_data(natal, solar)))
        assert "Natal " in row
        # Pins _return_label: collapsing it to the old Solar/else-Lunar binary
        # titled every solar return "Lunar Return" and nothing noticed.
        assert "Solar Return " in row, row

    def test_progression_labels_its_second_wheel_progression_not_transit(self):
        """ProgressionChartRenderer inherits from the transit renderer."""
        progressed = _subject("P", year=2000, month=10, day=9, hour=18, minute=30)
        row = _row(_render(ChartDataFactory.create_progression_chart_data(_subject(), progressed)))
        assert "Progression " in row
        assert "Transit" not in row


def test_a_leading_space_cannot_blank_a_wheel_name():
    """Names are not normalised upstream; the label is what disambiguates."""
    john = _subject(" John Lennon")
    paul = _subject("Paul", year=1942, month=6, day=18, hour=8, minute=0)
    row = _row(_render(ChartDataFactory.create_synastry_chart_data(john, paul)))
    assert row.startswith("John "), row
