# -*- coding: utf-8 -*-
"""
Tests for the dominants calculator (kerykeion.dominants).

Covered:
    - Almuten Figuris: a hand-verified anchor (scores derived from the static
      Ptolemaic dignity tables), the accidental layer, and the 5-place setup.
    - Modern weighted method: component tests of the angularity formula plus
      integration invariants on a known chart (Aries-rising ⇒ Mars dominant).
    - Elemental balance: parity with the library's element/quality distribution.
    - Factory: strategy resolution, the custom-strategy plug-in seam, and errors.
    - Public contract: get_type_hints resolvability, JSON round-trip, stable shape.
    - Edge cases: prenatal-syzygy determinism, ephemeris-gap degradation, sidereal.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import json
import typing
from types import SimpleNamespace

import pytest
from pytest import approx

from kerykeion import (
    AstrologicalSubjectFactory,
    BaseDominantStrategy,
    DominantBreakdownItemModel,
    DominantScoreModel,
    DominantsFactory,
    DominantsModel,
)
from kerykeion.dominants.base import Category
from kerykeion.dominants.strategies.modern import ModernDominantStrategy
from kerykeion.dominants.utils import part_of_fortune_degree, prenatal_syzygy, zodiac_breakdown
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.utilities import get_kerykeion_point_from_degree

pytestmark = pytest.mark.core

_CLASSICAL = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
_CATEGORIES = ("planets", "signs", "elements", "qualities", "houses", "polarities", "hemispheres", "quadrants")


# =============================================================================
# ALMUTEN FIGURIS
# =============================================================================


def test_almuten_essential_anchor(john_lennon):
    """Essential-dignity tally over the five hylegiacal places (hand-verified).

    The expected scores are derived purely from the published Ptolemaic tables
    in ``kerykeion.dignities.data`` applied to Lennon's five places:
        Sun 16°Lib · Moon 3°Aqu · Asc 19°Ari · Fortune 2°Cap · Syzygy 8°Lib (New)
    Saturn wins (domicile in Aquarius, exaltation in Libra ×2, domicile in
    Capricorn), ahead of Mercury (triplicity/term of Air, repeatedly).
    """
    result = DominantsFactory.from_subject(john_lennon, strategy="almuten_figuris")

    assert result.method == "almuten_figuris"
    assert result.dominant_planet == "Saturn"

    totals = {item.name: item.score for item in result.planets}
    assert totals == {
        "Saturn": 19.0,
        "Mercury": 17.0,
        "Venus": 11.0,
        "Mars": 9.0,
        "Jupiter": 6.0,
        "Sun": 5.0,
        "Moon": 4.0,
    }
    # All seven classical planets are present and ranked 1..7 in descending order.
    assert {item.name for item in result.planets} == _CLASSICAL
    assert [item.rank for item in result.planets] == [1, 2, 3, 4, 5, 6, 7]


def test_almuten_winner_placement_fills_convenience_fields(john_lennon):
    """The Almuten's own sign/element/quality/house populate the winner fields."""
    result = DominantsFactory.from_subject(john_lennon, strategy="almuten_figuris")
    saturn = john_lennon.saturn
    assert result.dominant_sign == saturn.sign
    assert result.dominant_element == saturn.element
    assert result.dominant_quality == saturn.quality
    assert result.dominant_house == saturn.house


def test_almuten_accidentals_change_ranking(john_lennon):
    """The optional accidental layer (house + day ruler) shifts the winner.

    Lennon was born on a Wednesday (Mercury's day) with Mercury angular, so the
    accidental layer lifts Mercury above the essential-only winner, Saturn.
    """
    essential = DominantsFactory.from_subject(john_lennon, strategy="almuten_figuris")
    accidental = DominantsFactory.from_subject(
        john_lennon, strategy="almuten_figuris", include_accidental_dignities=True
    )
    assert essential.dominant_planet == "Saturn"
    assert accidental.dominant_planet == "Mercury"
    # Totals strictly increase (or hold) once accidental points are added.
    essential_scores = {p.name: p.score for p in essential.planets}
    accidental_scores = {p.name: p.score for p in accidental.planets}
    assert all(accidental_scores[name] >= essential_scores[name] for name in _CLASSICAL)


def test_almuten_breakdown_records_places(john_lennon):
    """With breakdown on, every contribution is a per-place dignity line."""
    result = DominantsFactory.from_subject(john_lennon, strategy="almuten_figuris", include_score_breakdown=True)
    assert result.score_breakdown, "breakdown should not be empty"
    assert all(item.category == "place" for item in result.score_breakdown)
    # Saturn must have at least one domicile (5-point) contribution.
    saturn_domiciles = [i for i in result.score_breakdown if i.target == "Saturn" and i.rule == "Domicile"]
    assert saturn_domiciles and all(i.points == 5.0 for i in saturn_domiciles)


# =============================================================================
# MODERN WEIGHTED METHOD
# =============================================================================


def test_modern_angularity_falloff():
    """Angularity is 4.0 exactly on the Ascendant, 0 at the orb edge, 2.0 on IC."""
    point = get_kerykeion_point_from_degree(100.0, "Mars", "AstrologicalPoint")

    on_ascendant = {"Ascendant": 100.0, "Medium_Coeli": None, "Descendant": None, "Imum_Coeli": None}
    assert ModernDominantStrategy._angularity_scores([point], on_ascendant, [], False)["Mars"] == approx(4.0)

    # 15° away from the only angle → outside the orb → zero.
    far = {"Ascendant": 115.0, "Medium_Coeli": None, "Descendant": None, "Imum_Coeli": None}
    assert ModernDominantStrategy._angularity_scores([point], far, [], False)["Mars"] == approx(0.0)

    # Exactly on the IC (weight 0.5) → 4.0 * 0.5 = 2.0.
    on_ic = {"Ascendant": None, "Medium_Coeli": None, "Descendant": None, "Imum_Coeli": 100.0}
    assert ModernDominantStrategy._angularity_scores([point], on_ic, [], False)["Mars"] == approx(2.0)


def _modern_dignity(point_name: str, abs_degree: float, *, is_diurnal: bool = True) -> float:
    """Run the modern dignity scorer on a single synthetic point."""
    subject = SimpleNamespace(is_diurnal=is_diurnal)
    point = get_kerykeion_point_from_degree(abs_degree, point_name, "AstrologicalPoint")
    return ModernDominantStrategy._dignity_scores(subject, [point], [], False)[point_name]


def test_modern_dignity_term_never_masks_detriment():
    """A planet in its own term while in detriment scores 0.25 - 1.00 = -0.75.

    These are exactly the degree windows where the single "highest dignity"
    label used to hide the debility and award a bare +0.25:
        - Mars 28-30° Libra: own Egyptian term, detriment in Libra.
        - Venus 7-11° Scorpio: own term, detriment (checked in a NIGHT chart
          so Venus's Water *day*-triplicity rulership stays out of the way).
        - Saturn 26-30° Cancer: own term, detriment.
        - Mercury 17-21° Sagittarius: own term, detriment.
    """
    assert _modern_dignity("Mars", 180 + 28.5) == approx(0.25 - 1.00)
    assert _modern_dignity("Venus", 210 + 8.0, is_diurnal=False) == approx(0.25 - 1.00)
    assert _modern_dignity("Saturn", 90 + 27.0) == approx(0.25 - 1.00)
    assert _modern_dignity("Mercury", 240 + 18.0) == approx(0.25 - 1.00)


def test_modern_dignity_triplicity_never_masks_debility():
    """A triplicity rulership earns +0.40 but never hides detriment/fall.

    Venus at 8° Scorpio in a DAY chart is the Dorothean day ruler of Water
    (label "Triplicity", outranking its own term) yet still in detriment:
    0.40 - 1.00 = -0.60 (previously the masked +0.40). The Moon at 3°
    Capricorn in a NIGHT chart rules the Earth triplicity while in detriment:
    0.40 - 1.00 = -0.60.
    """
    assert _modern_dignity("Venus", 210 + 8.0, is_diurnal=True) == approx(0.40 - 1.00)
    assert _modern_dignity("Moon", 270 + 3.0, is_diurnal=False) == approx(0.40 - 1.00)


def test_modern_dignity_double_debility_is_additive():
    """Mercury in Pisces is in BOTH detriment (opposite Gemini) and fall
    (opposite its Virgo exaltation), so both documented penalties apply.

    At 17° Pisces it also sits in its own term: 0.25 - 1.00 - 0.75 = -1.50
    (previously the masked +0.25). At 5° Pisces it holds no dignity at all:
    -1.00 - 0.75 = -1.75 (previously -1.00, since the single "Detriment"
    label could only carry one of the two debilities).
    """
    assert _modern_dignity("Mercury", 330 + 17.0) == approx(0.25 - 1.00 - 0.75)
    assert _modern_dignity("Mercury", 330 + 5.0) == approx(-1.00 - 0.75)


def test_modern_dignity_unmasked_cases_unchanged():
    """Plain dignities/debilities keep their documented values.

    Mars at 5° Aries: domicile, no debility → +1.00. The Sun at 10° Libra
    (day chart): fall, no dignity (the 6-14° term is Mercury's, decan 2 is
    Saturn's, the Air day-triplicity is Saturn's) → -0.75. Uranus is not a
    classical planet, so it carries no essential dignity anywhere → 0.0.
    """
    assert _modern_dignity("Mars", 0 + 5.0) == approx(1.00)
    assert _modern_dignity("Sun", 180 + 10.0) == approx(-0.75)
    assert _modern_dignity("Uranus", 210 + 8.0) == approx(0.0)


def test_modern_dignity_breakdown_lists_each_component():
    """With the audit trail on, dignity and debility appear as separate lines."""
    subject = SimpleNamespace(is_diurnal=True)
    point = get_kerykeion_point_from_degree(180 + 28.5, "Mars", "AstrologicalPoint")
    breakdown = []
    scores = ModernDominantStrategy._dignity_scores(subject, [point], breakdown, True)

    assert scores["Mars"] == approx(-0.75)
    contributions = {(item.rule, item.points) for item in breakdown if item.target == "Mars"}
    assert contributions == {("Term", 0.25), ("Detriment", -1.00)}


def test_modern_mars_dominant_for_aries_rising(john_lennon):
    """Lennon has Aries rising, so its modern ruler Mars is a dominant planet."""
    result = DominantsFactory.from_subject(john_lennon, strategy="modern")

    assert result.method == "modern"
    assert len(result.planets) == 10  # all ten planets present
    assert [item.rank for item in result.planets] == list(range(1, 11))
    dominant_names = [item.name for item in result.planets if item.is_dominant]
    assert "Mars" in dominant_names
    assert result.dominant_planet is not None
    assert result.dominant_element in {"Fire", "Earth", "Air", "Water"}
    assert result.dominant_quality in {"Cardinal", "Fixed", "Mutable"}


def test_modern_full_category_set(john_lennon):
    """The modern method fills the complete Astrotheme-style category set."""
    result = DominantsFactory.from_subject(john_lennon, strategy="modern")
    for category in _CATEGORIES:
        assert isinstance(getattr(result, category), list)
    # Polarity has exactly Yang and Yin; hemispheres cover the four directions.
    assert {item.name for item in result.polarities} == {"Yang", "Yin"}
    assert {item.name for item in result.hemispheres} == {"North", "South", "East", "West"}
    # Each independent hemisphere axis flags exactly one winner.
    dominant_hemispheres = {item.name for item in result.hemispheres if item.is_dominant}
    assert len(dominant_hemispheres) == 2


def test_modern_percentages_sum_to_100(john_lennon):
    """Percentages are normalized to 100 within each populated category."""
    result = DominantsFactory.from_subject(john_lennon, strategy="modern")
    for category in ("planets", "elements", "qualities", "polarities"):
        items = getattr(result, category)
        assert sum(item.percentage for item in items) == approx(100.0, abs=0.5)


# =============================================================================
# ELEMENTAL BALANCE
# =============================================================================


def test_elemental_matches_distribution(john_lennon):
    """The elemental school agrees with the library's distribution helpers."""
    from kerykeion.charts.utils import calculate_element_points, calculate_quality_points
    from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS

    for method in ("weighted", "pure_count"):
        elements = calculate_element_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS, john_lennon.active_points, john_lennon, method=method
        )
        qualities = calculate_quality_points(
            DEFAULT_CELESTIAL_POINTS_SETTINGS, john_lennon.active_points, john_lennon, method=method
        )
        result = DominantsFactory.from_subject(john_lennon, strategy="elemental", distribution_method=method)

        # The dominant must be one of the elements/qualities achieving the max
        # total (ties are broken deterministically, but either is acceptable).
        top_elements = {key for key, value in elements.items() if value == max(elements.values())}
        top_qualities = {key for key, value in qualities.items() if value == max(qualities.values())}
        assert result.dominant_element.lower() in top_elements
        assert result.dominant_quality.lower() in top_qualities
        # Elemental school scores only elements/qualities/polarities.
        assert result.planets == []
        assert {item.name for item in result.polarities} == {"Yang", "Yin"}


def test_elemental_matches_chart_distribution_with_active_stars():
    """The elemental school must count active fixed stars like ChartDataFactory
    does, or the dominants numbers silently diverge from the chart's element
    distribution for a star-bearing subject."""
    from kerykeion import AstrologicalSubjectFactory
    from kerykeion.chart_data.factory import ChartDataFactory

    subject = AstrologicalSubjectFactory.from_birth_data(
        "Star Dominant", 1990, 6, 15, 12, 0,
        lng=12.5, lat=41.9, tz_str="Europe/Rome",
        online=False, suppress_geonames_warning=True,
        active_fixed_stars=["Regulus", "Spica"],
    )
    chart = ChartDataFactory.create_natal_chart_data(subject)
    dominants = DominantsFactory.from_subject(subject, strategy="elemental")

    chart_pct = {k: round(getattr(chart.element_distribution, f"{k}_percentage")) for k in ("fire", "earth", "air", "water")}
    dom_pct = {item.name.lower(): round(item.percentage) for item in dominants.elements}
    assert chart_pct == dom_pct


# =============================================================================
# FACTORY: RESOLUTION, CUSTOM STRATEGY, ERRORS
# =============================================================================


class _StubStrategy(BaseDominantStrategy):
    """Minimal custom strategy used to exercise the plug-in seam."""

    name = "stub_school"

    def compute(self, subject, config):
        return self.build_model(categories={"planets": Category(scores={"Sun": 99.0}, dominant={"Sun"})})


def test_custom_strategy_plug_in(john_lennon):
    """A custom strategy instance is accepted and drives the result."""
    result = DominantsFactory.from_subject(john_lennon, strategy=_StubStrategy())
    assert result.strategy_name == "stub_school"
    assert result.method is None  # custom strategies report no built-in method
    assert result.dominant_planet == "Sun"


def test_unknown_method_raises(john_lennon):
    """An unknown method name raises a clear KerykeionException."""
    with pytest.raises(KerykeionException, match="Unknown dominant method"):
        DominantsFactory.from_subject(john_lennon, strategy="not_a_method")


def test_invalid_strategy_type_raises(john_lennon):
    """A non-strategy, non-string object is rejected."""
    with pytest.raises(KerykeionException):
        DominantsFactory.from_subject(john_lennon, strategy=object())  # type: ignore[arg-type]


def test_available_methods():
    """The registry exposes exactly the three built-in schools."""
    assert DominantsFactory.available_methods() == ["almuten_figuris", "elemental", "modern"]


def test_from_birth_data_convenience():
    """from_birth_data builds the subject and delegates to from_subject."""
    result = DominantsFactory.from_birth_data(
        "Test",
        1990,
        5,
        15,
        12,
        0,
        lat=41.9028,
        lng=12.4964,
        tz_str="Europe/Rome",
        online=False,
        suppress_geonames_warning=True,
        strategy="elemental",
    )
    assert isinstance(result, DominantsModel)
    assert result.dominant_element in {"Fire", "Earth", "Air", "Water"}


# =============================================================================
# PUBLIC CONTRACT (FastAPI introspection, serialization, stable shape)
# =============================================================================


def test_get_type_hints_resolves():
    """get_type_hints must succeed on every public model (FastAPI contract)."""
    for model in (DominantsModel, DominantScoreModel, DominantBreakdownItemModel):
        hints = typing.get_type_hints(model)
        assert hints  # non-empty, fully resolved


def test_json_round_trip(john_lennon):
    """The result serializes to JSON and rebuilds identically."""
    result = DominantsFactory.from_subject(john_lennon, strategy="modern", include_score_breakdown=True)
    dumped = result.model_dump()
    json.dumps(dumped)  # must be JSON-serializable
    rebuilt = DominantsModel(**dumped)
    assert rebuilt.dominant_planet == result.dominant_planet
    assert len(rebuilt.planets) == len(result.planets)


def test_stable_shape_across_schools(john_lennon):
    """Every school returns the same fixed set of category lists."""
    for method in DominantsFactory.available_methods():
        result = DominantsFactory.from_subject(john_lennon, strategy=method)
        for category in _CATEGORIES:
            assert isinstance(getattr(result, category), list)


def test_breakdown_is_opt_in(john_lennon):
    """The audit trail is empty unless explicitly requested."""
    assert DominantsFactory.from_subject(john_lennon, strategy="modern").score_breakdown == []
    assert DominantsFactory.from_subject(john_lennon, strategy="modern", include_score_breakdown=True).score_breakdown


# =============================================================================
# EDGE CASES
# =============================================================================


def test_prenatal_syzygy_deterministic(john_lennon):
    """The prenatal syzygy is reproducible and correctly typed for Lennon."""
    first = prenatal_syzygy(john_lennon)
    second = prenatal_syzygy(john_lennon)
    assert first is not None
    assert first.kind == second.kind == "New"  # Lennon is waxing gibbous before birth
    assert first.degree == approx(second.degree, abs=1e-6)


def test_part_of_fortune_computed_when_absent(john_lennon):
    """The Part of Fortune is derived from Asc/Sun/Moon when not pre-calculated."""
    degree = part_of_fortune_degree(john_lennon)
    assert degree is not None and 0.0 <= degree < 360.0


def test_syzygy_gap_degrades_gracefully(john_lennon, monkeypatch):
    """An ephemeris failure drops the syzygy place without crashing the Almuten."""
    import kerykeion.dominants.utils as utils_module

    # Use a non-RuntimeError, non-builtin exception to mirror the backend's real
    # out-of-range error (libephemeris raises EphemerisRangeError — a plain
    # Exception subclass, not a RuntimeError): the catch must be backend-agnostic.
    class _SimulatedRangeError(Exception):
        pass

    def _boom(_julian_day, _iflag=None):
        raise _SimulatedRangeError("simulated out-of-range date")

    monkeypatch.setattr(utils_module, "_sun_moon_longitudes", _boom)
    assert prenatal_syzygy(john_lennon) is None

    # The Almuten still resolves over the remaining four places.
    result = DominantsFactory.from_subject(john_lennon, strategy="almuten_figuris")
    assert result.dominant_planet in _CLASSICAL


def test_prenatal_syzygy_full_moon(yoko_ono):
    """A waning chart resolves to a Full-Moon prenatal syzygy (the other branch).

    Yoko Ono is born after a Full Moon and at night, so the syzygy degree is
    taken from the Moon (the luminary above the horizon at birth). This anchors
    the 'Full' branch and the nocturnal sect choice, which the New-Moon Lennon
    fixture does not exercise.
    """
    syzygy = prenatal_syzygy(yoko_ono)
    assert syzygy is not None
    assert syzygy.kind == "Full"
    assert 0.0 <= syzygy.degree < 360.0
    # The Almuten still resolves to a valid classical planet using the Full place.
    result = DominantsFactory.from_subject(yoko_ono, strategy="almuten_figuris")
    assert result.dominant_planet in _CLASSICAL


def test_sidereal_chart_returns_valid_winner():
    """A sidereal chart yields a valid Almuten and leaves the sect unchanged."""
    tropical = AstrologicalSubjectFactory.from_birth_data(
        "Lennon T",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )
    sidereal = AstrologicalSubjectFactory.from_birth_data(
        "Lennon S",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
    )
    result = DominantsFactory.from_subject(sidereal, strategy="almuten_figuris")
    assert result.dominant_planet in _CLASSICAL
    # Sect is a horizon (not zodiac) property, so it is identical in both frames.
    assert sidereal.is_diurnal == tropical.is_diurnal


class TestAlmutenRankingConsistency:
    """Round-2 regression: the ranked planets list's rank 1 must equal the
    flagged Almuten (dominant_planet), even on score ties (base ranks ties
    alphabetically; the winner uses the traditional Almuten order)."""

    def test_rank1_equals_dominant_planet_on_tie(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.dominants import DominantsFactory

        # This chart produces a Jupiter/Mercury/Saturn tie at total 14.0.
        s = AstrologicalSubjectFactory.from_birth_data(
            "t", 1950, 10, 16, 3, 0, lat=40.0, lng=-3.0,
            tz_str="Europe/Madrid", online=False, suppress_geonames_warning=True,
        )
        r = DominantsFactory.from_subject(s, strategy="almuten_figuris")
        assert r.planets[0].name == r.dominant_planet
        assert r.planets[0].is_dominant is True

    def test_rank1_equals_dominant_planet_sweep(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.dominants import DominantsFactory

        for y in range(1955, 2000, 5):
            s = AstrologicalSubjectFactory.from_birth_data(
                "x", y, 6, 10, 2, 10, lat=41.9, lng=12.5,
                tz_str="Europe/Rome", online=False, suppress_geonames_warning=True,
            )
            r = DominantsFactory.from_subject(s, strategy="almuten_figuris")
            assert r.planets[0].name == r.dominant_planet, f"mismatch for year {y}"


class TestZodiacBreakdownBoundary:
    """Round 27: zodiac_breakdown documents "any real number". A tiny-negative
    input hits float64's `(-1e-15) % 360.0 == 360.0`, which made sign_num == 12
    and indexed past SIGN_CODES (IndexError). The fold-back keeps it in [0,360)."""

    def test_tiny_negative_does_not_crash(self):
        z = zodiac_breakdown(-1e-15)
        assert z.sign == "Ari"
        assert z.sign_num == 0
        assert z.position == approx(0.0)

    def test_boundaries_stay_in_range(self):
        assert zodiac_breakdown(0.0).sign == "Ari"
        assert zodiac_breakdown(360.0).sign == "Ari"  # full circle folds to 0°
        assert zodiac_breakdown(359.9999).sign == "Pis"
        # -1e-9 % 360.0 == 359.9999... (< 360, no fold) -> last sliver of Pisces;
        # only the exact-360.0 float edge (-1e-15) folds back to Aries 0°.
        assert zodiac_breakdown(-1e-9).sign == "Pis"
