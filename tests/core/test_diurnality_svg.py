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

import functools
import json
import re
import unicodedata
from collections import UserString
from html import unescape
from pathlib import Path

import pytest

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    CompositeSubjectFactory,
    PlanetaryReturnFactory,
)
from kerykeion.report.generator import ReportGenerator, _return_type_label
from kerykeion.settings.config_constants import return_label_keys
from kerykeion.settings.translation_strings import LANGUAGE_SETTINGS
from kerykeion.secondary_progressions import SecondaryProgressionFactory, SolarArcFactory
from kerykeion.charts.drawer import (
    DIURNALITY_ROW_CLEAR_WIDTH,
    ChartDrawer,
    _INFO_ROW_FIRST_Y,
    _INFO_ROW_STEP,
    _MOON_GLYPH_FOOTPRINT,
    estimate_text_width,
    info_row_clear_width,
)


def _row_re(index: int):
    return re.compile(rf"Bottom_Left_Text_{index}'[^>]*>([^<]*)<")


BLOCK_TRANSFORM = re.compile(r"Bottom_Left_Text' transform='translate\(0,([-\d.]+)\)'")
MOON_TRANSFORM = re.compile(r"Lunar_Phase' transform='translate\(10,([-\d.]+)\)'")

# Hard-coded rather than derived, so a change to either constant has to be an
# explicit edit here.
#
# On a natal chart the glyph no longer trails the text: it leads the block, and
# the block slides down 7px so its last line closes level with the foot of the
# aspect grid. Both cases still read the same, which is the point — turning the
# diurnality line off costs a row but moves nothing, because the rows pack
# downwards and the glyph is anchored above them rather than below.
#: Block offset and moon-glyph y, with the diurnality line and without it. The
#: block never moves — its rows pack to the bottom, so the last one stays level
#: with the foot of the aspect grid however many there are. The glyph does move:
#: it follows the first line rather than sitting at a fixed height, so a shorter
#: block does not leave it hanging halfway up the panel captioning air. One row
#: fewer, one row lower: 438 + 14 = 452.
LAYOUT_WITH_LINE = ("7", "438")
LAYOUT_WITHOUT_LINE = ("7", "452")
#: Every other chart type keeps the older arrangement: the glyph under the
#: block, and the block on the template baselines — except that a panel drawing
#: no glyph takes the 30px the glyph is not using, so its block sits that much
#: lower and ends where a panel with one ends.
LAYOUT_NON_NATAL = ("0", "532")
LAYOUT_NON_NATAL_NO_DISC = ("30", "532")


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


def _row(svg: str, index: int | None = None) -> str:
    """The diurnality line, found by what it says rather than by where it sits.

    It used to be read from slot 5: the panel packs its filled rows to the
    bottom and diurnality was the last line every renderer wrote. The natal
    block now leads with the moon and ends with the ayanamsa, so the line moved
    — and an assertion keyed to a slot number fails for a layout change that has
    nothing to do with the value it is checking. Passing *index* still reads a
    specific slot, for the tests that are about the packing itself.
    """
    if index is not None:
        match = _row_re(index).search(svg)
        assert match is not None, f"the Bottom_Left_Text_{index} node is missing from the template"
        return match.group(1)
    for slot in range(6):
        found = _row_re(slot).search(svg)
        if found and any(word in found.group(1) for word in _DIURNALITY_WORDS):
            return found.group(1)
    # A custom language pack spells the two values however it likes, so nothing
    # above matches. The rows pack downwards, and on every chart type but natal
    # this line is the last one that is not the phase — the phase closes the
    # block so the disc drawn under it has the right caption. Read the last
    # filled slot, skipping that one.
    filled = [m.group(1) for slot in range(6) if (m := _row_re(slot).search(svg)) and m.group(1)]
    for text in reversed(filled):
        if not _is_phase_row(text):
            return text
    return ""


def _row_slot(svg: str, text: str) -> int:
    """Which of the six slots *text* was drawn in."""
    for slot in range(6):
        match = _row_re(slot).search(svg)
        if match and match.group(1) == text:
            return slot
    raise AssertionError(f"row not found in any slot: {text!r}")


#: Every word any shipped language uses for the two values of the line.
_DIURNALITY_WORDS = frozenset(
    pack[key] for pack in LANGUAGE_SETTINGS.values() for key in ("diurnal", "nocturnal")
)


def _states_diurnality(svg: str) -> bool:
    """Whether the panel names a diurnality anywhere.

    Asked of the content rather than of a slot. With the rows packed to the
    bottom, a line the chart does not state leaves no blank behind at a fixed
    index — the line above simply moves down into it — so "row 5 is empty" is
    no longer the same question as "the chart states no diurnality", and it is
    the second one these tests mean.
    """
    return any(
        any(word in _row(svg, index) for word in _DIURNALITY_WORDS)
        for index in range(6)
    )


def _filled_row_baselines(svg: str) -> dict:
    """The y of every bottom-left row that carries text, keyed by the text."""
    return {
        text: y
        for y, text in re.findall(
            r"Bottom_Left_Text_\d'[^>]*y='([\d.]+)'[^>]*>([^<]*)</text>", svg
        )
        if text
    }


def _moon_gap(svg: str) -> float:
    """Pixels between the foot of the moon glyph and the first line under it."""
    block, moon = (float(v) for v in _layout(svg))
    first_row_y = min(float(y) for y in _filled_row_baselines(svg).values())
    return (block + first_row_y) - (moon + 20.0)


def _layout(svg: str) -> tuple:
    block = BLOCK_TRANSFORM.search(svg)
    moon = MOON_TRANSFORM.search(svg)
    assert block and moon
    return block.group(1), moon.group(1)


def _draws_a_disc(svg: str) -> bool:
    """Whether the Lunar_Phase group has anything in it.

    The group is in the template unconditionally, so its presence proves
    nothing: a panel that draws no disc still ships an empty one. Asking the
    transform instead of the contents is what let a survey of this defect count
    54 synastry charts that draw no moon at all.
    """
    body = re.search(r"<g kr:node='Lunar_Phase'[^>]*>(.*?)</g>", svg, re.S)
    return bool(body and body.group(1).strip())


def _disc_to_its_own_caption(svg: str) -> float:
    """Pixels between the disc and the row that names it, positive when apart.

    Measured to whichever edge faces the row: the natal panel draws the disc
    above its caption, every other panel below it. Zero would mean touching;
    what this catches is a disc left captioning some other row, which is how
    a transit put its picture three lines away from its own words.
    """
    block, moon = (float(v) for v in _layout(svg))
    rows = {text: block + float(y) for text, y in
            ((t, y) for t, y in _filled_row_baselines(svg).items())}
    caption = [y for text, y in rows.items() if _is_phase_row(text)]
    assert caption, f"no phase row to caption the disc: {list(rows)}"
    target = caption[0]
    return target - (moon + 20.0) if moon + 20.0 <= target else moon - target


#: Every translation of the phase label, whole. Matching on single words instead
#: finds the wrong row: "Lunar" is in the English label and also in "Lunar
#: Return", which names a wheel on the diurnality line one row up, so a lunar
#: return would have had the tests reading that row as the phase's.
_PHASE_LABELS = {
    str(settings.get("lunar_phase", ""))
    for settings in LANGUAGE_SETTINGS.values()
    if settings.get("lunar_phase")
}


def _is_phase_row(text: str) -> bool:
    """Whether *text* is the row naming the lunar phase, in any language."""
    return any(label in text for label in _PHASE_LABELS)


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


def _translate_phase_name(subject, language: str) -> str:
    """The phase's name as the panel spells it in *language*."""
    key = subject.lunar_phase.moon_phase_name.lower().replace(" ", "_")
    return LANGUAGE_SETTINGS[language].get(key, subject.lunar_phase.moon_phase_name)


def _lunar_return():
    """The next lunar return of the same nativity.

    Kept beside the solar one because it is the case where the wheel's name and
    the phase label share a word — "Lunar Return" against "Lunar phase" — which
    is what made the row stutter and what a label matched word by word finds in
    the wrong place.
    """
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
    return factory.next_return_from_date(2024, 1, 1, return_type="Lunar")


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
        assert not _states_diurnality(svg)
        # Two rows short here, not one — a heliocentric chart states neither a
        # diurnality nor a perspective-dependent line — so the constants above do
        # not apply. What does apply is the invariant behind them.
        assert _layout(svg)[0] == LAYOUT_WITH_LINE[0], "the block must not move"
        assert _moon_gap(svg) == pytest.approx(15.0)

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
        svg = _render(ChartDataFactory.create_natal_chart_data(subject))
        assert _states_diurnality(svg) is expected, f"{perspective}: {_row(svg)!r}"

    def test_midpoint_composite_has_no_single_sky(self):
        """A midpoint composite is no moment: no diurnality row, and no disc."""
        composite = _composite("Midpoint")
        assert composite.is_diurnal is None, "a midpoint composite must not claim a diurnality"
        svg = _render(ChartDataFactory.create_composite_chart_data(composite))
        # Asked of the content: the composite renderer writes into row 4 and
        # leaves row 5 blank, and the packing then closes that gap, so no fixed
        # slot answers this question any more.
        assert not _states_diurnality(svg)
        # No disc on this panel, so the block takes the room one would have had.
        assert not _draws_a_disc(svg)
        assert _layout(svg) == LAYOUT_NON_NATAL_NO_DISC

    def test_a_davison_composite_does_have_one(self):
        """The counterpart that makes the test above mean something.

        A Davison composite is a real moment, so it carries a real value and the
        line must appear. Without this, blanking the composite renderer's row —
        or defaulting a `None` to day — passes unnoticed.
        """
        composite = _composite("Davison")
        assert isinstance(composite.is_diurnal, bool)
        svg = _render(ChartDataFactory.create_composite_chart_data(composite))
        assert _row(svg) == f"Diurnality: {'Diurnal' if composite.is_diurnal else 'Nocturnal'}"
        # Row 4 already existed, so nothing had to move for it. The block sits
        # 30px down like its midpoint counterpart: neither draws a disc.
        assert not _draws_a_disc(svg)
        assert _layout(svg) == LAYOUT_NON_NATAL_NO_DISC


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
            svg = _render(data, chart_language=language)
            row = _row(svg)
            # Against the row this line actually lands on. The dual panels moved
            # it up one slot when the phase took the last one, and the chord
            # narrows going up: measuring every panel against row 5's width let
            # a row 28px too wide for its own slot keep this guard green.
            budget = min(DIURNALITY_ROW_CLEAR_WIDTH, info_row_clear_width(_row_slot(svg, row)))
            width = _measured_width(row)
            assert width <= budget, (
                f"{language}: {width:.1f}px will overrun the wheel's {budget:.1f}px: {row!r}"
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
        svg = _render(ChartDataFactory.create_synastry_chart_data(_subject("   "), _subject("  ", hour=23)))
        assert not _states_diurnality(svg)

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
        svg = _render(ChartDataFactory.create_synastry_chart_data(_subject(name), _subject("Antonio", hour=23)))
        assert not _states_diurnality(svg), f"{label}: {_row(svg)!r}"

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

        wide_svg = _render(data, language_pack={"nocturnal": "W" * 11, "diurnal": "W" * 11})
        assert "W" not in _row(wide_svg), f"should have been dropped, got {_row(wide_svg)!r}"

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
        assert not _states_diurnality(svg)

    def test_block_and_moon_return_to_their_original_offsets(self):
        data = ChartDataFactory.create_natal_chart_data(_subject())
        assert _layout(_render(data, show_diurnality=False)) == LAYOUT_WITHOUT_LINE

    def test_the_glyph_keeps_its_gap_above_the_first_row(self):
        """Read from the rendered output, not restated from the constants.

        The moon leads the natal block now, so the gap that has to hold is the
        one between the bottom of the glyph and the first line under it — the
        glyph is 20px tall from its own origin. Reading both sides from the
        render rather than restating the constants: asserting it as arithmetic
        on integer literals is a tautology that holds whatever the code does.
        """
        data = ChartDataFactory.create_natal_chart_data(_subject())
        for show in (False, True):
            svg = _render(data, show_diurnality=show)
            block, moon = (float(v) for v in _layout(svg))
            # The first row that actually carries text, read from the render:
            # the block leads with blank slots now, and the glyph answers to the
            # first line a reader can see rather than to the first slot in the
            # template.
            rows = re.findall(
                r"Bottom_Left_Text_\d'[^>]*y='([\d.]+)'[^>]*>([^<]*)</text>", svg
            )
            first_row_y = min(float(y) for y, text in rows if text)
            assert (block + first_row_y) - (moon + 20.0) == pytest.approx(15.0)


    def test_showing_the_line_moves_the_glyph_and_nothing_else(self):
        """The other rows must not move — only the glyph answers to the count.

        They sit inside the wheel's chord and the lower a row is the more clear
        width it has, so shifting the block upwards to make room narrows every
        row above; an earlier revision did exactly that and pushed a default
        English progression row under the wheel. Packing to the bottom is what
        keeps that from happening: the rows that are drawn land on the same
        baselines whether the line is there or not, and the blank opens at the
        top. The glyph then follows the first of them, which is the one thing
        that is allowed to move.
        """
        data = ChartDataFactory.create_natal_chart_data(_subject())
        assert _layout(_render(data, show_diurnality=False)) == LAYOUT_WITHOUT_LINE
        assert _layout(_render(data, show_diurnality=True)) == LAYOUT_WITH_LINE

        # The block ends where it ended: adding a line opens the blank at the
        # top and pushes the rows above the new one up, never any row down.
        without = _filled_row_baselines(_render(data, show_diurnality=False))
        with_line = _filled_row_baselines(_render(data, show_diurnality=True))
        assert max(float(y) for y in without.values()) == max(
            float(y) for y in with_line.values()
        )
        for text, y in without.items():
            assert float(with_line[text]) <= float(y), f"{text!r} was pushed down"

    def test_off_leaves_the_other_rows_untouched(self):
        """Dropping the line costs a row, and the blank goes to the top.

        It used to stay in the last slot, which left the panel ending one row
        short of where it ends everywhere else. The rows pack downwards now, so
        the text still finishes on the bottom line and the gap opens above it.
        """
        data = ChartDataFactory.create_natal_chart_data(_subject())
        svg_off = _render(data, show_diurnality=False)
        rows = [text for _, text in re.findall(r"Bottom_Left_Text_(\d)'[^>]*>([^<]*)<", svg_off)]
        assert rows[0] == "", "the node exists but carries nothing"
        # However many blanks there are — the lunation day left the panel too —
        # they are all at the top and none of them is between two filled rows.
        filled = [index for index, text in enumerate(rows) if text]
        assert filled, "the block drew nothing at all"
        assert filled == list(range(filled[0], len(rows))), f"a blank row in the middle: {rows}"


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
        assert re.search(rf"<title[^>]*>[^<]*{expected} Return", single), re.search(r"<title[^>]*>[^<]*", single).group(0)

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
        assert not _states_diurnality(_render(ChartDataFactory.create_progression_chart_data(natal, directed)))

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

    @pytest.mark.parametrize("return_type", [["Solar"], {"a": 1}, {"Solar"}, bytearray(b"Solar")])
    def test_an_unhashable_return_type_does_not_raise(self, return_type):
        """`getattr` promises nothing about the type; the old gate did.

        An unhashable value went straight into `dict.get` and raised TypeError
        where the previous code returned a label — a new failure mode introduced
        by the very change that widened this function to duck-typed subjects.

        Every parameter here must be *unhashable*. An earlier version included
        `123`, which is hashable and so returned the default with or without the
        guard: it read as a fifth hostile case and pinned nothing.
        """
        assert return_label_keys(_DuckTypedReturn(return_type)) == ("Return", "Return")

    def test_a_string_that_is_not_a_str_is_still_taken_at_its_word(self):
        """Screening on `isinstance(str)` would fail this, and did.

        The first guard against the case above tested the *type* rather than the
        problem, and so refused a `UserString` — and any lazy-translation proxy
        of that shape — which hashes and compares equal to `str` and matches the
        map perfectly. Catching the lookup's own TypeError keeps them working:
        widening this function to duck-typed subjects and then narrowing it back
        by the side door would have undone the point of the change.

        `UserString` alone, because it is the only one of these that ever
        discriminated. A `str`-mixin enum was pinned here too and satisfied the
        `isinstance` screen as readily as the fix — `issubclass(_, str)` is True
        for it — so it read as evidence for a claim it could not support. That is
        the vacuous-parameter defect the previous commit removed, one commit
        later, and the commit message repeated it.
        """
        assert return_label_keys(_DuckTypedReturn(UserString("Solar")))[1] == "Solar Return"


class TestTheDiscCaptionsItsOwnRow:
    """The picture and the words that name it must be adjacent.

    They were not. The disc was placed by chart type — the natal panel put it
    above the block, every other panel ten pixels under the block's LAST line —
    while the row naming it sat third or fourth from the end. On a transit the
    picture ended up 24px and two rows away from its caption, on a return 38px
    and three. The rule now is the same everywhere and it is about the row, not
    about the type: the phase row closes the block, so the disc under it has
    nothing else it could be captioning.

    Why the row moved rather than the disc: the wheel's chord narrows going up,
    leaving 147px on the first row against 229 on the last, and a dual panel's
    phase line carries the wheel's name too. Of 140 language-by-phase
    combinations, 113 would overrun in the first row against 15 in the last.
    """

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _all_charts():
        """Built once for the whole class: nine parametrized cases were
        recomputing a solar return and a progression each time."""
        natal = _subject()
        natal_return, solar = _solar_return()
        lunar = _lunar_return()
        progressed = SecondaryProgressionFactory.compute(natal, target_year=2020)
        return {
            "natal": ChartDataFactory.create_natal_chart_data(natal),
            "transit": ChartDataFactory.create_transit_chart_data(
                natal, _subject("Now", year=2024, month=6, day=15, hour=12, minute=0)
            ),
            "progression": ChartDataFactory.create_progression_chart_data(natal, progressed),
            "single_return": ChartDataFactory.create_single_wheel_return_chart_data(solar),
            "dual_return": ChartDataFactory.create_return_chart_data(natal_return, solar),
            # The one whose wheel name shares a word with the phase label, and
            # so the one that catches both a stuttering row and a test that
            # looks for the label by single words.
            "dual_lunar_return": ChartDataFactory.create_return_chart_data(natal_return, lunar),
        }

    def _charts(self):
        """The disc-drawing panels, built once per test through the cache above."""
        return self._all_charts()

    @pytest.mark.parametrize(
        "kind",
        ["natal", "transit", "progression", "single_return", "dual_return", "dual_lunar_return"],
    )
    def test_the_disc_sits_against_the_row_that_names_it(self, kind):
        """No panel may put another line between the disc and its caption."""
        svg = _render(self._charts()[kind])
        assert _draws_a_disc(svg), "this panel is supposed to draw one"
        gap = _disc_to_its_own_caption(svg)
        # 15px is the clear air the natal panel has always kept above its
        # caption, and the widest adjacency the library uses; a row is 14px, so
        # anything beyond this has a whole line of something else in between.
        assert 0 <= gap <= 15.0, (
            f"{kind}: the disc stands {gap:.0f}px from its own caption, further "
            f"than the {_INFO_ROW_STEP:.0f}px between two rows — it is "
            "captioning somebody else's line"
        )

    @pytest.mark.parametrize(
        "kind",
        ["transit", "progression", "single_return", "dual_return", "dual_lunar_return"],
    )
    def test_the_phase_closes_the_block_on_every_dual_and_return_panel(self, kind):
        """Stated separately from the gap, because it is the reason for it.

        The gap alone would also be satisfied by moving the disc, which is the
        arrangement this replaced and which no width can support.
        """
        svg = _render(self._charts()[kind])
        rows = _filled_row_baselines(svg)
        last = max(float(y) for y in rows.values())
        phase = [y for text, y in rows.items() if _is_phase_row(text)]
        assert phase and float(phase[0]) == last, (
            f"{kind}: the phase row is not the last one; the disc is drawn "
            "below the block and would caption whatever ended up there"
        )

    @pytest.mark.parametrize("kind", ["synastry", "composite_midpoint", "composite_davison"])
    def test_a_panel_with_no_disc_closes_where_one_with_a_disc_does(self, kind):
        """The block takes the room the disc is not using.

        The disc holds 30px under the block — a 10px gap plus its own 20px of
        height — so a panel that draws none used to stop 30px short and leave a
        strip of empty page under its last line while every other panel ran on
        to the same edge. The rows pack to the bottom precisely so the panel has
        one bottom edge; it should not depend on whether there is a moon to draw.
        """
        panels = {
            "synastry": ChartDataFactory.create_synastry_chart_data(
                _subject(), _subject("Paul", year=1942, month=6, day=18, hour=8, minute=0)
            ),
            "composite_midpoint": ChartDataFactory.create_composite_chart_data(_composite("Midpoint")),
            "composite_davison": ChartDataFactory.create_composite_chart_data(_composite("Davison")),
        }
        svg = _render(panels[kind])
        assert not _draws_a_disc(svg), "fixture must be a panel that draws no disc"
        block = float(_layout(svg)[0])
        last_row = block + max(float(y) for y in _filled_row_baselines(svg).values())

        # Where a panel that does draw one ends: the foot of its disc.
        with_disc = _render(
            ChartDataFactory.create_transit_chart_data(
                _subject(), _subject("Now", year=2024, month=6, day=15, hour=12, minute=0)
            )
        )
        assert _draws_a_disc(with_disc)
        disc_foot = float(_layout(with_disc)[1]) + 20.0
        assert last_row == pytest.approx(disc_foot), (
            f"{kind}: the panel closes at {last_row:.0f} where one with a disc "
            f"closes at {disc_foot:.0f}"
        )

    def test_a_composite_draws_no_disc_because_it_writes_no_row(self):
        """A picture with no caption says nothing about what it depicts.

        The composite panel spends its six rows elsewhere and has never written
        a phase line, yet it drew the disc — eighteen charts carrying a moon
        that named nothing. The synastry panel, equally short of room, has
        always left it out.
        """
        for kind in ("Midpoint", "Davison"):
            svg = _render(ChartDataFactory.create_composite_chart_data(_composite(kind)))
            assert not _draws_a_disc(svg), f"{kind} composite still draws an unlabelled disc"
            assert not any(
                _is_phase_row(text) for text in _filled_row_baselines(svg)
            ), "if the row is written the disc should come back with it"

    def test_a_dual_return_reads_the_return_moon_not_the_nativity(self):
        """The chart is cast on the return, so the phase is the return's.

        It took the natal subject's, labelled with a bare "Lunar phase" while
        the row beside it named the two wheels apart — so the nativity's moon
        read as the return's. The transit and progression panels, in this same
        row, have always taken the second wheel and said whose it is.
        """
        natal, solar = _solar_return()
        assert natal.lunar_phase.moon_phase_name != solar.lunar_phase.moon_phase_name, (
            "fixture is useless unless the two moons differ"
        )
        svg = _render(ChartDataFactory.create_return_chart_data(natal, solar))
        row = next(
            text for text in _filled_row_baselines(svg)
            if _is_phase_row(text)
        )
        assert solar.lunar_phase.moon_phase_name in row, f"row reads {row!r}"
        assert natal.lunar_phase.moon_phase_name not in row, f"row still reads the nativity: {row!r}"
        assert _return_type_label(solar) in row, (
            f"the row must say whose moon it is: {row!r}"
        )

    @pytest.mark.parametrize("language", sorted(LANGUAGE_SETTINGS))
    def test_trimming_takes_the_wheel_name_and_leaves_the_phase(self, language):
        """What the row exists to say must survive the cut, in every language.

        `truncate_to_width` cuts from the end, so trimming the whole line spends
        the budget on "Solar Return Lunar phase:" and amputates the one word a
        reader came for. The wheel's name is the qualifier and pays first — the
        rule the diurnality row two lines down already states outright.

        Every shipped language, deliberately: an earlier list held only the
        three the estimator measured honestly, and Hindi — which it over-read
        at more than twice its rendered width and amputated — was precisely
        the language left out.
        """
        natal, solar = _solar_return()
        svg = _render(ChartDataFactory.create_return_chart_data(natal, solar),
                      chart_language=language)
        row = next(text for text in _filled_row_baselines(svg) if _is_phase_row(text))
        phase_name = _translate_phase_name(solar, language)
        assert phase_name in unescape(row), (
            f"{language}: the phase name was cut away, leaving {row!r}"
        )

    def test_hindi_is_measured_not_guessed(self):
        """The row fits, so nothing may be cut — the wheel qualifier included.

        The estimator used to charge every Devanagari code point the block
        ceiling of 1.04 em, matras and viramas included, and read this 159px
        row as 363 in a slot that clears 229: the "सौर वापसी" qualifier was
        dropped and the phase name cut mid-word, with a third of the slot to
        spare. Devanagari sits in the measured table now, like Cyrillic before
        it, and the whole row must survive.
        """
        natal, solar = _solar_return()
        svg = _render(ChartDataFactory.create_return_chart_data(natal, solar), chart_language="HI")
        row = unescape(next(t for t in _filled_row_baselines(svg) if _is_phase_row(t)))
        assert "…" not in row, f"a row that fits was trimmed: {row!r}"
        assert _translate_phase_name(solar, "HI") in row, row
        assert row.startswith(LANGUAGE_SETTINGS["HI"]["solar_return"]), (
            f"the wheel qualifier was dropped: {row!r}"
        )

    def test_a_phase_no_room_can_hold_is_end_trimmed_not_drawn_under_the_wheel(self):
        """The trim's last resort, reachable by a caller's language pack alone.

        When even the bare phase does not fit its row, the qualifier is already
        gone and there is nothing left to pay but the phase itself: a shortened
        row beats one drawn under the wheel graphics. No shipped language
        reaches this branch — which is why only a mutation of it could tell,
        until this test.
        """
        natal, solar = _solar_return()
        key = solar.lunar_phase.moon_phase_name.lower().replace(" ", "_")
        svg = _render(
            ChartDataFactory.create_return_chart_data(natal, solar),
            language_pack={key: "W" * 60},
        )
        row = unescape(next(t for t in _filled_row_baselines(svg) if _is_phase_row(t)))
        assert "…" in row, f"a phase wider than its row was left whole: {row!r}"
        assert estimate_text_width(row) <= info_row_clear_width(5), (
            f"still wider than the row after the cut: {row!r}"
        )

    def test_a_lunar_return_does_not_say_lunar_twice(self):
        """"Lunar Return Lunar phase" reads as a stutter, and so does the French.

        The wheel's name is there to say which of the two wheels the phase
        belongs to, which it still does once the word the label already carries
        is dropped from it.
        """
        natal = _subject()
        svg = _render(ChartDataFactory.create_return_chart_data(natal, _lunar_return()))
        row = unescape(next(text for text in _filled_row_baselines(svg) if _is_phase_row(text)))
        label = LANGUAGE_SETTINGS["EN"]["lunar_phase"]
        for word in label.split():
            assert row.count(word) <= 1, f"{word!r} appears twice: {row!r}"
        # Still says whose phase it is, which is the point of the qualifier.
        assert "Return" in row, row

    @pytest.mark.parametrize("language", sorted(LANGUAGE_SETTINGS))
    def test_the_phase_row_stays_inside_the_wheel(self, language):
        """It had never been trimmed, and in Hindi it ran past the graphics.

        The house row and the relationship-score row are both trimmed to the
        room their own row has; this one was not, in any language.
        """
        natal, solar = _solar_return()
        svg = _render(ChartDataFactory.create_return_chart_data(natal, solar), chart_language=language)
        rows = _filled_row_baselines(svg)
        index = {float(y): i for i, y in enumerate(
            _INFO_ROW_FIRST_Y + _INFO_ROW_STEP * i for i in range(6))}
        for text, y in rows.items():
            if _is_phase_row(text):
                budget = info_row_clear_width(index[float(y)])
                # Measured from real type advances, not from the function the
                # builder allocates with: phrased in the estimator's own terms
                # the assertion holds however wrongly it measures, which is what
                # `_measured_width` exists to avoid.
                width = _measured_width(unescape(text), 10)
                assert width <= budget, (
                    f"{language}: {text!r} overruns its row by {width - budget:.0f}px"
                )

class TestThePerspectiveRowFitsItsSlot:
    """The slot reshuffle moved the perspective up where the chord is narrower.

    It was the one row builder with no width fitting at all: the Russian
    apparent-geocentric string, 198px by the reference fonts' own advances, ran
    19px under the wheel graphics from slot 3's 179px on every dual return.
    """

    @pytest.mark.parametrize("language", sorted(LANGUAGE_SETTINGS))
    def test_the_perspective_row_stays_inside_the_wheel(self, language):
        """Measured with real advances, the row fits the slot it landed on."""
        natal, solar = _solar_return()
        svg = _render(ChartDataFactory.create_return_chart_data(natal, solar), chart_language=language)
        label = LANGUAGE_SETTINGS[language].get("perspective_type", "Perspective")
        row, y = next(
            (t, y) for t, y in _filled_row_baselines(svg).items() if unescape(t).startswith(label)
        )
        index = round((float(y) - _INFO_ROW_FIRST_Y) / _INFO_ROW_STEP)
        width = _measured_width(unescape(row), 10)
        budget = info_row_clear_width(index)
        assert width <= budget, (
            f"{language}: {row!r} overruns row {index} by {width - budget:.0f}px"
        )

    @staticmethod
    def _chart_data(kind):
        """Chart data for each panel with a fixed-slot perspective row."""
        if kind == "transit":
            return ChartDataFactory.create_transit_chart_data(
                _subject(), _subject("Now", year=2024, month=6, day=15, hour=12, minute=0)
            )
        if kind == "synastry":
            return ChartDataFactory.create_synastry_chart_data(
                _subject(), _subject("Paul", year=1942, month=6, day=18, hour=2, minute=0)
            )
        if kind == "composite_midpoint":
            return ChartDataFactory.create_composite_chart_data(_composite("Midpoint"))
        if kind == "composite_davison":
            return ChartDataFactory.create_composite_chart_data(_composite("Davison"))
        natal, solar = _solar_return()
        if kind == "single_return":
            return ChartDataFactory.create_single_wheel_return_chart_data(solar)
        return ChartDataFactory.create_return_chart_data(natal, solar)

    @staticmethod
    def _perspective_row(svg):
        """The rendered perspective row, the slot it landed on, the block's drop."""
        row, y = next(
            (unescape(t), y)
            for t, y in _filled_row_baselines(svg).items()
            if unescape(t).startswith("Perspective")
        )
        index = round((float(y) - _INFO_ROW_FIRST_Y) / _INFO_ROW_STEP)
        drop = float(BLOCK_TRANSFORM.search(svg).group(1))
        # The raw transform equals the drop only while the wheel itself sits at
        # its template origin — true of every fixture here, and load-bearing:
        # past the wheel's edge the clamp makes every slot's budget 320px, and
        # an assertion fed that number would pass for any slot choice at all
        # instead of failing loudly.
        assert drop <= _MOON_GLYPH_FOOTPRINT, (
            f"block dropped {drop:.0f}px — a right-panel layout; this helper's "
            "budget readback would go vacuous, use a smaller fixture"
        )
        return row, index, drop

    @pytest.mark.parametrize(
        "kind",
        ["transit", "synastry", "composite_midpoint", "composite_davison", "single_return", "dual_return"],
    )
    def test_every_fitted_call_site_bites(self, kind):
        """A value too wide for any slot is cut to its own slot's room — everywhere.

        Rendered through a language pack no shipped translation approaches, so
        the assertion has teeth on every panel, including the four whose shipped
        strings fit whole and which therefore stood on no test at all. The
        budget is read back from the SVG itself — the slot the row landed on,
        at the height the block actually sits — so a call site that stops
        fitting, or fits against the wrong slot in the wrong direction, fails
        here by measurement rather than by fixture bookkeeping.
        """
        svg = _render(self._chart_data(kind), language_pack={"apparent_geocentric": "W" * 40})
        row, index, drop = self._perspective_row(svg)
        assert row.endswith("…"), f"{kind}: a 400px value was left whole: {row!r}"
        budget = info_row_clear_width(index, drop)
        assert estimate_text_width(row) <= budget, (
            f"{kind}: {row!r} was fitted to some other slot than row {index} at drop {drop:.0f}"
        )

    def test_the_chord_function_survives_a_row_below_the_wheel(self):
        """Row 5 plus a disc-less panel's 30px drop sits below the wheel's edge.

        There is no chord there to bind it: the budget continues to the tangent
        value instead of raising a math domain error on a height the wheel does
        not reach.
        """
        assert info_row_clear_width(5, _MOON_GLYPH_FOOTPRINT) == pytest.approx(320.0)

    @pytest.mark.parametrize(
        "kind,slot,floor",
        [
            # floor: the widest budget any *wrong* fit would use. For the
            # synastry that is the template height (drop forgotten); for the
            # composite the candidates are the template height, slot 2 (the row
            # it is written in) and slot 3 (the Davison branch taken on a
            # midpoint) — the last is the widest. The value is built to clear
            # the floor and sit inside the true dropped chord, so every one of
            # those wrong budgets cuts it and only the right one leaves it whole.
            ("synastry", 4, info_row_clear_width(4)),
            ("composite_midpoint", 4, info_row_clear_width(3, _MOON_GLYPH_FOOTPRINT)),
        ],
    )
    def test_a_disc_less_panel_is_fitted_at_the_height_it_sits(self, kind, slot, floor):
        """These panels never draw a disc: their block takes the disc's 30px and
        their rows sit on a wider chord. Fitted at the template height, the
        Russian perspective was cut in a slot it fit with 55px to spare — the
        amputation this class exists to prevent, reintroduced by its own fix.
        """
        ceiling = info_row_clear_width(slot, _MOON_GLYPH_FOOTPRINT)
        value = "W"
        while estimate_text_width(f"Perspective: {value}") <= floor + 8:
            value += "W"
        full = f"Perspective: {value}"
        assert floor + 8 < estimate_text_width(full) <= ceiling - 8, "the fixture window collapsed"
        svg = _render(self._chart_data(kind), language_pack={"apparent_geocentric": value})
        row, index, drop = self._perspective_row(svg)
        assert index == slot, f"{kind}: landed on row {index}, this test believes {slot}"
        assert row == full, (
            f"{kind}: cut although the chord at drop {drop:.0f} holds it whole: {row!r}"
        )


class TestTheEstimatorMeasuresWhatItUsedToGuess:
    """Combining marks are measured at their hmtx advance, not the block ceiling.

    Charged the ceiling, every matra and virama of a Hindi row cost a full
    1.04 em — the row read at over twice its rendered width, and the trims that
    share the estimator amputated text that fit with a third of the slot spare.
    """

    def test_a_combining_mark_adds_nothing_to_the_estimate(self):
        """A virama or non-spacing matra costs the zero the fonts declare."""
        base = estimate_text_width("क")
        assert estimate_text_width("क\u094d") == base  # virama
        assert estimate_text_width("क\u0941") == base  # matra u, non-spacing

    def test_a_spacing_matra_costs_its_measured_advance(self):
        """A spacing matra costs real width — its own, not the block ceiling."""
        # AA (U+093E) is a spacing mark, ~0.3 em in the reference fonts — real
        # width, so it must cost something, and far less than the old ceiling.
        alone = estimate_text_width("क")
        with_matra = estimate_text_width("क\u093e")
        assert alone < with_matra < alone + 5.0
