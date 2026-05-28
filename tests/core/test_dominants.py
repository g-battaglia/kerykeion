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
from kerykeion.dominants.utils import part_of_fortune_degree, prenatal_syzygy
from kerykeion.schemas.kerykeion_exception import KerykeionException
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
    in ``kerykeion.dignities.dignity_data`` applied to Lennon's five places:
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
    from kerykeion.charts.charts_utils import calculate_element_points, calculate_quality_points
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

    def _boom(_julian_day):
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
