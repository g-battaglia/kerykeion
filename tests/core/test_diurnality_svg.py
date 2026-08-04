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

import json
import re
import unicodedata
from html import unescape
from pathlib import Path

import pytest

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    CompositeSubjectFactory,
    PlanetaryReturnFactory,
)
from kerykeion.report import ReportGenerator, _return_type_label
from kerykeion.settings.config_constants import return_label_keys
from kerykeion.settings.translation_strings import LANGUAGE_SETTINGS
from kerykeion.secondary_progressions import SecondaryProgressionFactory, SolarArcFactory
from kerykeion.charts.chart_drawer import (
    DIURNALITY_ROW_CLEAR_WIDTH,
    ChartDrawer,
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


_ADVANCES = json.loads((Path(__file__).parents[1] / "data" / "glyph_advances.json").read_text())["advances"]


def _measured_width(text: str, font_size: float = 10.0) -> float:
    """Width of *text* from real type metrics, not from the estimator.

    The point of reading a committed table of advance widths rather than calling
    `estimate_text_width` is that the builder allocates its budget *with* that
    function, so an assertion phrased in its terms is satisfied by construction:
    `fixed + sum(names)` equals the budget whatever the function returns, and
    every row passes however wrongly it is measured. An earlier version of this
    test did exactly that and stayed green while seven rows overran.

    The figures are the widest advance across Times, Helvetica and Arial Unicode
    (see the file's own comment), so this measures what those three will actually
    render. Characters none of them have are charged a full em, matching the
    estimator's own rule for scripts it cannot measure.

    Unescapes first: the node's source text spells `&` as `&amp;`, five
    characters for one glyph, and measuring the source charged a name of twelve
    ampersands 615px when it renders as 60. The escaping is the renderer's, not
    the reader's — `estimate_text_width` is correctly applied before it.

    Combining and format characters are skipped, as they are in the estimator.
    That is not borrowing the estimator's arithmetic but agreeing with type: a
    Devanagari matra stacks on the letter before it, and the zero-width joiner
    in an emoji sequence fuses two code points into one glyph. Charging them a
    full em made a six-emoji name measure 255px for what renders as about 140.
    """
    return sum(
        _ADVANCES.get(f"{ord(c):04X}", 1.0) * font_size
        for c in unescape(text)
        if unicodedata.category(c) not in ("Mn", "Me", "Cf")
    )


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
    factory = CompositeSubjectFactory(_subject(), _subject("Paul", year=1942, month=6, day=18, hour=8, minute=0))
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
        natal,
        city="Liverpool",
        nation="GB",
        lat=53.41058,
        lng=-2.97794,
        tz_str="Europe/London",
        online=False,
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

    @pytest.mark.parametrize(
        "perspective,expected",
        [
            ("Apparent Geocentric", True),
            ("True Geocentric", True),
            ("Topocentric", True),
            ("Heliocentric", False),
            ("Selenocentric", False),
            ("Marscentric", False),
            ("Jupitercentric", False),
            ("Barycentric", False),
        ],
    )
    def test_only_a_chart_cast_from_the_earth_states_a_diurnality(self, perspective, expected):
        """Seven of the eleven perspectives draw a Sun that is not the measured one.

        `is_diurnal` comes from a tropical *geocentric* Sun. A heliocentric chart
        draws no Sun at all, which was the case this feature already handled. The
        planetocentric ones are worse: they draw a Sun, and it is a different
        body. On this Liverpool chart the measured Sun is at 196° and the
        Marscentric wheel draws 354°, so the panel asserted "Nocturnal" over a
        Sun it was not describing — one row below `Perspective: Marscentric`.

        Topocentric and True Geocentric differ from Apparent Geocentric by
        parallax and aberration, fractions of a degree, so they keep the line.
        """
        subject = _subject(perspective_type=perspective)
        row = _row(_render(ChartDataFactory.create_natal_chart_data(subject)))
        assert bool(row) is expected, f"{perspective}: {row!r}"

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


class TestDiurnalityInTheTextReport:
    """The report applies the same omission rule, and nothing pinned it.

    `subject_states_a_diurnality` is shared by the SVG panel and the report so
    the two cannot drift — but only the panel had tests, so a divergence in the
    report would have shown up as a user noticing it. These mirror the SVG cases.
    """

    @staticmethod
    def _report(subject) -> str:
        return str(ReportGenerator(subject).generate_report())

    def test_an_ordinary_chart_reports_it(self):
        assert "Diurnality" in self._report(_subject())

    @pytest.mark.parametrize("perspective", ["Heliocentric", "Marscentric", "Selenocentric", "Barycentric"])
    def test_a_chart_not_cast_from_the_earth_does_not(self, perspective):
        assert "Diurnality" not in self._report(_subject(perspective_type=perspective))

    def test_a_midpoint_composite_does_not(self):
        assert "Diurnality" not in self._report(_composite("Midpoint"))

    def test_a_davison_composite_does(self):
        # The counterpart: without it, suppressing every composite would pass.
        assert "Diurnality" in self._report(_composite("Davison"))


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
            width = _measured_width(row)
            assert width <= DIURNALITY_ROW_CLEAR_WIDTH, (
                f"{language}: {width:.1f}px will overrun the wheel's {DIURNALITY_ROW_CLEAR_WIDTH}px: {row!r}"
            )

    # Every name class that has broken this guard, and the ones that have not
    # yet. The guard has been wrong three times — a character cap that could not
    # see ideographs, an em average that undercharged lowercase w and Cyrillic
    # ж ю ы, and a 1.0-em fallback that undercharged Arabic. Each time the
    # verification sweep that found the next one was run by hand and thrown away,
    # so the next class was free to break it again. This is that sweep, committed.
    NAME_CLASSES = {
        "ideographs": ("阿部寛田中太郎彦仁美", "山田花子鈴木一郎次郎"),
        "hangul": ("김철수박영희정민수", "이민호최지우강동원"),
        "arabic": ("محمدعبدالرحمن", "فاطمةالزهراء"),
        "arabic-presentation": ("ﶩﶪﶫﶬﶭﶮﶯﶰ", "ﷲﷺﷻﷴﷵﷶﷷﷸ"),
        "hebrew": ("דודבןגוריון", "שרהלויכהן"),
        "devanagari": ("राजेशकुमारशर्मा", "प्रियादेवीसिंह"),
        "thai": ("สมชายใจดีมาก", "สุดารัตน์ทองดี"),
        "greek": ("ΑΘΗΝΑΠΑΠΑΔΟΠΟΥΛΟΥ", "Γεώργιοςαντωνίου"),
        "cyrillic-lower": ("жжжжжжжжжжжж", "юююююююююююю"),
        "cyrillic-upper": ("ЖЮЖЮЖЮЖЮЖЮ", "ШЩШЩШЩШЩ"),
        "latin-upper": ("MARIAGRAZIAMARIA", "GIANFRANCOGIAN"),
        "latin-widest": ("MMMMMMMMMMMM", "WWWWWWWWWWWW"),
        "latin-lower-wide": ("mmmmmmmmmmmm", "wwwwwwwwwwww"),
        "digraphs": ("ǆǆǆǆǆǆǆǆǆǆ", "ǱǱǱǱǱǱǱǱǱǱ"),
        "combining": ("Ana\u0301sta\u0301sia\u0301", "Jose\u0301Mari\u0301a"),
        "soft-hyphen": ("Ana" + "\u00ad" * 20, "Bo" + "\u00ad" * 20),
        "emoji": ("👩‍🚀🌟🔮🪐🌙☀️", "🧿✨🌞🌛🪄🕯️"),
        "markup": ("&&&&&&&&&&&&", "<<<<<<<<<<<<"),
        "whitespace-only": (" ", "  "),
        "ordinary-latin": ("Alessandra Giovanna Bianchi", "Massimiliano Ferrari"),
    }

    @pytest.mark.parametrize("script", sorted(NAME_CLASSES))
    @pytest.mark.parametrize("language", ["EN", "IT", "RU", "DE", "CN", "HI"])
    def test_no_name_in_any_script_overruns_the_wheel(self, script, language):
        """The sweep that keeps finding the next hole, run every time.

        Measured against `tests/data/glyph_advances.json`, not against the
        estimator that sized the row — see `_measured_width` for why that
        distinction is the whole point.
        """
        first, second = self.NAME_CLASSES[script]
        data = ChartDataFactory.create_synastry_chart_data(_subject(first), _subject(second, hour=23, minute=0))
        row = _row(_render(data, chart_language=language))
        width = _measured_width(row)
        assert width <= DIURNALITY_ROW_CLEAR_WIDTH, (
            f"{script}/{language}: {width:.1f}px overruns the wheel's {DIURNALITY_ROW_CLEAR_WIDTH}px — {row!r}"
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
        assert _measured_width(cut) <= DIURNALITY_ROW_CLEAR_WIDTH

    def test_a_whitespace_only_name_blanks_the_row_rather_than_orphaning_a_value(self):
        """A value with no owner is the ambiguity the labels exist to prevent.

        `_truncate_name(..., truncate_at_space=True)` returns "" for a name that
        is nothing but spaces — a reachable input, since the field is a plain
        string with no normalisation upstream — and the row rendered as
        " Nocturnal ·  Nocturnal": two values, neither attached to a chart. Worse
        than no line, so there is no line.
        """
        row = _row(_render(ChartDataFactory.create_synastry_chart_data(_subject("   "), _subject("  ", hour=23))))
        assert row == ""

    @pytest.mark.parametrize(
        "name,label",
        [
            ("   ", "spaces"),
            ("\u200b", "zero-width space"),
            ("\u200e", "left-to-right mark"),
            ("\u200d", "zero-width joiner"),
            ("\u2060", "word joiner"),
            ("\u00ad", "soft hyphen"),
            ("\u0301", "a lone combining acute"),
            ("\u00a0", "non-breaking space"),
        ],
    )
    def test_a_name_with_no_ink_blanks_the_row(self, name, label):
        """`str.strip()` was not the right question.

        It removes spaces and, incidentally, the non-breaking space — and none of
        the rest. A wheel name of one zero-width space rendered
        "\u200b Nocturnal \u00b7 Antonio Nocturnal": a value with no owner, which
        is what the whitespace guard existed to prevent. A pasted name is far
        likelier to carry a zero-width character than to be nothing but spaces.
        """
        row = _row(_render(ChartDataFactory.create_synastry_chart_data(_subject(name), _subject("Antonio", hour=23))))
        assert row == "", f"{label}: {row!r}"

    def test_an_ordinary_name_is_not_caught_by_that(self):
        row = _row(
            _render(ChartDataFactory.create_synastry_chart_data(_subject("Marco"), _subject("Antonio", hour=23)))
        )
        assert "Marco" in row and "Antonio" in row

    def test_a_language_pack_cannot_push_the_row_past_its_floor(self):
        """The values are fixed text; the names have a floor; both must fit.

        `truncate_to_width` keeps one character plus an ellipsis rather than
        returning nothing, so `fixed` alone was never the thing that had to fit.
        A pack whose values eat the row rendered 260px into 228px of clearance —
        the guard compared the wrong quantity and passed.
        """
        data = ChartDataFactory.create_synastry_chart_data(_subject("Alessandro"), _subject("Antonio", hour=23))

        wide = _row(_render(data, language_pack={"nocturnal": "W" * 11, "diurnal": "W" * 11}))
        assert wide == "", f"should have been dropped, got {wide!r}"

        # And a pack that does leave room still renders, cut to fit.
        fits = _row(_render(data, language_pack={"nocturnal": "W" * 8, "diurnal": "W" * 8}))
        assert fits, "a pack that fits must still produce a row"
        assert _measured_width(fits) <= DIURNALITY_ROW_CLEAR_WIDTH

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

    @pytest.mark.parametrize(
        "return_type,expected",
        [
            ("Solar", "Solar Return"),
            ("Lunar", "Lunar Return"),
            ("Heliocentric", "Heliocentric Return"),
            ("Lunar_Node_Crossing", "Node Return"),
        ],
    )
    def test_every_return_type_gets_its_own_label(self, return_type, expected):
        """All four, not just the two that had a branch.

        `_return_label` was a Solar/else-Lunar binary, so a heliocentric return
        and a node crossing both announced themselves as "Lunar Return" — in the
        chart's own Type line and, once this feature shipped, on the diurnality
        row beside it, contradicting the `return_type` in the same response.
        """
        natal, solar = _solar_return()
        relabelled = solar.model_copy(update={"return_type": return_type})

        # The single wheel prints the label in full, on its own Type line.
        single = _render(ChartDataFactory.create_single_wheel_return_chart_data(relabelled))
        assert f"Type: {expected}" in single

        # The dual wheel prints it beside the diurnality value, where the row's
        # width budget may cut it — so match the stem, not the whole label.
        row = _row(_render(ChartDataFactory.create_return_chart_data(natal, relabelled)))
        assert "Natal " in row
        assert expected.split(" ")[0] in row, row

    @pytest.mark.parametrize(
        "return_type,expected",
        [("Solar", "Solar"), ("Lunar", "Lunar"), ("Heliocentric", "Heliocentric"), ("Lunar_Node_Crossing", "Node")],
    )
    def test_the_title_and_the_grids_agree_with_the_type_line(self, return_type, expected):
        """One mapping, five call sites — fixing the panel alone was not enough.

        A heliocentric return rendered `Type: Heliocentric Return` under a title
        ending "Lunar Return 2024-10", with the dual chart's outer planet grid
        and its house-comparison columns also labelled Lunar. Every heading now
        routes through `return_label_keys`.
        """
        natal, solar = _solar_return()
        relabelled = solar.model_copy(update={"return_type": return_type})
        others = {"Solar", "Lunar", "Heliocentric", "Node"} - {expected}

        single = _render(ChartDataFactory.create_single_wheel_return_chart_data(relabelled))
        assert re.search(rf"<title>[^<]*{expected} Return", single), re.search(r"<title>[^<]*", single).group(0)

        dual = _render(
            ChartDataFactory.create_return_chart_data(natal, relabelled),
            show_house_position_comparison=True,
        )
        # Present, not merely "the others absent": dropping the outer-grid title
        # entirely would satisfy an absence-only assertion.
        assert f"{expected} Return" in dual, f"{return_type} chart never names itself"
        for other in others:
            assert not re.search(rf"\b{other} Return\b", dual), f"{return_type} chart still says {other} Return"

    @pytest.mark.parametrize("language", sorted(LANGUAGE_SETTINGS))
    def test_no_heading_names_a_body_the_chart_is_not(self, language):
        """The bug the English-only check missed.

        `return_aspects` is the aspect grid's heading — the largest text block on
        a dual return — and the Italian pack hardcoded "Ritorno Solare" in it, so
        a lunar, heliocentric or node return rendered in Italian carried a
        heading naming the wrong body while every other label was right. Nine of
        the ten packs were already generic; checking one language could not see
        it.
        """
        natal, solar = _solar_return()
        for return_type in ("Lunar", "Heliocentric", "Lunar_Node_Crossing"):
            svg = _render(
                ChartDataFactory.create_return_chart_data(natal, solar.model_copy(update={"return_type": return_type})),
                chart_language=language,
            )
            solar_label = LANGUAGE_SETTINGS[language]["solar_return"]
            assert solar_label not in svg, f"{language}/{return_type} names {solar_label!r}"

    def test_a_solar_arc_direction_states_no_diurnality(self):
        """The directed wheel's value answers for the nativity, not for itself.

        Solar arc keeps the natal instant and moves every point forward by the
        Sun's arc, so `is_diurnal` describes the birth: on this Rome 1950
        nativity directed to 2020 it says the Sun is up while the directed Sun
        sits in the third house, below the horizon. The row said
        "Natal Diurnal · Progression Diurnal" — two values, one of them about a
        different chart than the wheel beside it.

        Nothing on the subject distinguishes it from a secondary progression:
        same model, same renderer, same `chart_type`. The instant does — sharing
        the nativity's is what makes it symbolic.
        """
        natal = _subject("Demo", year=1950, month=6, day=15, hour=5, minute=0)
        directed = SolarArcFactory.compute_directed_subject(natal, target_year=2020)
        assert directed.iso_formatted_utc_datetime == natal.iso_formatted_utc_datetime
        assert _row(_render(ChartDataFactory.create_progression_chart_data(natal, directed))) == ""

    def test_a_secondary_progression_still_states_one(self):
        """The counterpart that makes the test above mean something.

        A progressed chart is cast for a real later moment, so its value does
        describe its own wheel. Without this, suppressing the whole renderer
        would pass.
        """
        natal = _subject("Demo", year=1950, month=6, day=15, hour=5, minute=0)
        progressed = SecondaryProgressionFactory.compute(natal, target_year=2020)
        assert progressed.iso_formatted_utc_datetime != natal.iso_formatted_utc_datetime
        assert "Progression " in _row(_render(ChartDataFactory.create_progression_chart_data(natal, progressed)))

    def test_two_subjects_sharing_an_instant_are_not_a_direction(self):
        """Twins in a synastry share a moment without one deriving from the other.

        The rule is scoped to the renderer that can draw a direction, so a shared
        instant means nothing here and the row stands.
        """
        row = _row(
            _render(
                ChartDataFactory.create_synastry_chart_data(
                    _subject("Twin A", year=1950, month=6, day=15, hour=5, minute=0),
                    _subject("Twin B", year=1950, month=6, day=15, hour=5, minute=0),
                )
            )
        )
        assert "Twin" in row and row.count("·") == 1, row

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


class _DuckTypedReturn:
    """Not a `PlanetReturnModel` — just something that says what it is."""

    def __init__(self, return_type):
        self.return_type = return_type


class TestTheReturnLabelMappingItself:
    """The mapping reached directly, not through a rendered chart.

    Every other test here goes through a `PlanetReturnModel`, whose `return_type`
    is always one of the four keyed values — so they all agree no matter how the
    fallback behaves, and none of them can see it. That blind spot is exactly
    where the Solar/else-Lunar binary this branch removed grew back: an
    `isinstance` gate discarded the `return_type` of anything that was not that
    model, so a subject *declaring* Solar was labelled Lunar. `report.py` reads
    subjects with `getattr` on purpose and documents duck-typing as supported,
    which makes it the surface that regressed.
    """

    @pytest.mark.parametrize(
        "return_type,expected",
        [
            ("Solar", "Solar Return"),
            ("Lunar", "Lunar Return"),
            ("Heliocentric", "Heliocentric Return"),
            ("Lunar_Node_Crossing", "Node Return"),
        ],
    )
    def test_a_duck_typed_subject_is_taken_at_its_word(self, return_type, expected):
        assert return_label_keys(_DuckTypedReturn(return_type))[1] == expected
        assert _return_type_label(_DuckTypedReturn(return_type)) == expected

    @pytest.mark.parametrize("return_type", ["", None, "Something_Upstream_Added"])
    def test_an_unknown_type_is_named_neither_lunar_nor_wrongly(self, return_type):
        """Naming no body beats naming the wrong one.

        The old fallback handed back the lunar label, so an unmapped value —
        a `ReturnType` added upstream, or a subject carrying none — was
        announced as a Lunar Return in the panel, the Type line, the title and
        both grids at once.
        """
        assert return_label_keys(_DuckTypedReturn(return_type)) == ("Return", "Return")
        assert _return_type_label(_DuckTypedReturn(return_type)) == "Return"

    def test_a_subject_with_no_return_type_at_all_is_not_a_lunar_return(self):
        assert return_label_keys(_subject()) == ("Return", "Return")
        assert _return_type_label(_subject()) == "Return"

    def test_the_neutral_label_is_a_key_the_language_packs_actually_have(self):
        """A neutral label still has to be neutral *in the reader's language*.

        The first version of this returned a lowercase `return` key. No pack has
        one and none ever could: packs are dumped from `KerykeionLanguageModel`
        and `return` is a Python keyword, so it cannot be a field and is dropped
        even when a caller passes it — the drawing would have printed English
        "Return" beside the Italian "Ritorno" the house-comparison grid renders
        from the key that does exist.
        """
        key, _ = return_label_keys(_DuckTypedReturn("Something_Upstream_Added"))
        missing = [language for language, pack in LANGUAGE_SETTINGS.items() if not pack.get(key)]
        assert not missing, f"{key!r} is not translated in: {missing}"
        assert LANGUAGE_SETTINGS["IT"][key] == "Ritorno"

    @pytest.mark.parametrize("return_type", [["Solar"], {"a": 1}, {"Solar"}, 123, bytearray(b"Solar")])
    def test_a_return_type_that_is_not_a_string_does_not_raise(self, return_type):
        """`getattr` promises nothing about the type; the old gate did.

        An unhashable value went straight into `dict.get` and raised TypeError
        where the previous code returned a label — a new failure mode introduced
        by the very change that widened this function to duck-typed subjects.
        """
        assert return_label_keys(_DuckTypedReturn(return_type)) == ("Return", "Return")
