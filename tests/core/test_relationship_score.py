# -*- coding: utf-8 -*-
"""
Comprehensive tests for RelationshipScoreFactory.

Integrates all test cases from tests/factories/test_relationship_score_factory_complete.py
and adds additional coverage for score boundaries, evaluation methods, destiny sign logic,
breakdown structure, aspect filtering, symmetry, and edge cases.
"""

import pytest
from pytest import approx

from kerykeion import AstrologicalSubjectFactory
from kerykeion.relationship_score_factory import (
    RelationshipScoreFactory,
    DESTINY_SIGN_POINTS,
    HIGH_PRECISION_ORBIT_THRESHOLD,
    MAJOR_ASPECT_POINTS_HIGH_PRECISION,
    MAJOR_ASPECT_POINTS_STANDARD,
    MINOR_ASPECT_POINTS,
    SUN_ASCENDANT_ASPECT_POINTS,
    MOON_ASCENDANT_ASPECT_POINTS,
    VENUS_MARS_ASPECT_POINTS,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def john():
    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon",
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


@pytest.fixture(scope="module")
def yoko():
    return AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono",
        1933,
        2,
        18,
        20,
        30,
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def subject1():
    """Generic subject born 1990-06-15 in New York."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Subject 1",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=30,
        lat=40.7128,
        lng=-74.0060,
        tz_str="America/New_York",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def subject2():
    """Generic subject born 1992-08-20 in New York."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Subject 2",
        year=1992,
        month=8,
        day=20,
        hour=14,
        minute=45,
        lat=40.7128,
        lng=-74.0060,
        tz_str="America/New_York",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def cardinal_aries():
    """Subject with Aries Sun (Cardinal quality)."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Cardinal Aries",
        year=1990,
        month=3,
        day=21,
        hour=12,
        minute=0,
        lat=40.7128,
        lng=-74.0060,
        tz_str="America/New_York",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def cardinal_cancer():
    """Subject with Cancer Sun (Cardinal quality)."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Cardinal Cancer",
        year=1990,
        month=6,
        day=25,
        hour=12,
        minute=0,
        lat=40.7128,
        lng=-74.0060,
        tz_str="America/New_York",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def fixed_taurus():
    """Subject with Taurus Sun (Fixed quality)."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Fixed Taurus",
        year=1990,
        month=4,
        day=25,
        hour=12,
        minute=0,
        lat=40.7128,
        lng=-74.0060,
        tz_str="America/New_York",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="module")
def ancient_subject():
    """Subject from a much earlier era (year 1800)."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Ancient Subject",
        year=1800,
        month=1,
        day=1,
        hour=0,
        minute=0,
        lat=51.5074,
        lng=-0.1278,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


# ---------------------------------------------------------------------------
# 1. Basic Score Creation
# ---------------------------------------------------------------------------


class TestBasicScoreCreation:
    """Verify that RelationshipScoreFactory produces a valid score model."""

    def test_score_model_is_not_none(self, john, yoko):
        factory = RelationshipScoreFactory(john, yoko)
        score_model = factory.get_relationship_score()
        assert score_model is not None

    def test_score_value_is_numeric(self, john, yoko):
        factory = RelationshipScoreFactory(john, yoko)
        score_model = factory.get_relationship_score()
        assert isinstance(score_model.score_value, (int, float))

    def test_score_description_is_string(self, john, yoko):
        factory = RelationshipScoreFactory(john, yoko)
        score_model = factory.get_relationship_score()
        assert isinstance(score_model.score_description, str)
        assert len(score_model.score_description) > 0

    def test_factory_stores_subjects(self, john, yoko):
        factory = RelationshipScoreFactory(john, yoko)
        assert factory.first_subject == john
        assert factory.second_subject == yoko

    def test_initial_score_is_zero(self, john, yoko):
        factory = RelationshipScoreFactory(john, yoko)
        assert factory.score_value == 0

    def test_default_uses_major_aspects_only(self, john, yoko):
        factory = RelationshipScoreFactory(john, yoko)
        assert factory.use_only_major_aspects is True

    def test_score_model_has_required_attributes(self, john, yoko):
        factory = RelationshipScoreFactory(john, yoko)
        score_model = factory.get_relationship_score()
        assert hasattr(score_model, "score_value")
        assert hasattr(score_model, "score_description")
        assert hasattr(score_model, "is_destiny_sign")
        assert hasattr(score_model, "aspects")
        assert hasattr(score_model, "subjects")
        assert hasattr(score_model, "score_breakdown")

    def test_score_is_non_negative(self, john, yoko):
        factory = RelationshipScoreFactory(john, yoko)
        score_model = factory.get_relationship_score()
        assert score_model.score_value >= 0

    def test_consistency_across_calls(self, subject1, subject2):
        """Same inputs produce identical scores."""
        s1 = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        s2 = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        assert s1.score_value == s2.score_value
        assert s1.score_description == s2.score_description
        assert s1.is_destiny_sign == s2.is_destiny_sign


# ---------------------------------------------------------------------------
# 2. Score Description Boundaries
# ---------------------------------------------------------------------------

VALID_DESCRIPTIONS = {
    "Minimal",
    "Medium",
    "Important",
    "Very Important",
    "Exceptional",
    "Rare Exceptional",
}


class TestScoreDescriptionBoundaries:
    """Ensure every score maps to the correct categorical description."""

    BOUNDARY_CASES = [
        (0, "Minimal"),
        (3, "Minimal"),
        (5, "Medium"),
        (8, "Medium"),
        (10, "Important"),
        (12, "Important"),
        (15, "Very Important"),
        (18, "Very Important"),
        (20, "Exceptional"),
        (25, "Exceptional"),
        (30, "Rare Exceptional"),
        (50, "Rare Exceptional"),
    ]

    @pytest.mark.parametrize("score_value,expected", BOUNDARY_CASES)
    def test_description_for_score(self, subject1, subject2, score_value, expected):
        factory = RelationshipScoreFactory(subject1, subject2)
        factory.score_value = score_value
        factory._evaluate_relationship_score_description()
        assert factory.relationship_score_description == expected

    def test_john_yoko_has_valid_description(self, john, yoko):
        score = RelationshipScoreFactory(john, yoko).get_relationship_score()
        assert score.score_description in VALID_DESCRIPTIONS

    def test_score_mapping_has_six_categories(self):
        assert len(RelationshipScoreFactory.SCORE_MAPPING) == 6

    def test_score_mapping_is_list(self):
        assert isinstance(RelationshipScoreFactory.SCORE_MAPPING, list)


# ---------------------------------------------------------------------------
# 3. All Evaluation Methods
# ---------------------------------------------------------------------------


class TestAllEvaluationMethods:
    """Verify each private evaluation method modifies the score correctly."""

    def test_sun_sun_main_aspect_conjunction(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Sun", "p2_name": "Sun", "aspect": "conjunction", "orbit": 1.5}
        factory._evaluate_sun_sun_main_aspect(aspect)
        assert factory.score_value == MAJOR_ASPECT_POINTS_HIGH_PRECISION

    def test_sun_sun_main_aspect_opposition(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Sun", "p2_name": "Sun", "aspect": "opposition", "orbit": 3.0}
        factory._evaluate_sun_sun_main_aspect(aspect)
        assert factory.score_value == MAJOR_ASPECT_POINTS_STANDARD

    def test_sun_sun_main_aspect_square(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Sun", "p2_name": "Sun", "aspect": "square", "orbit": 2.0}
        factory._evaluate_sun_sun_main_aspect(aspect)
        assert factory.score_value == MAJOR_ASPECT_POINTS_HIGH_PRECISION

    def test_sun_moon_conjunction_tight(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Sun", "p2_name": "Moon", "aspect": "conjunction", "orbit": 1.0}
        factory._evaluate_sun_moon_conjunction(aspect)
        assert factory.score_value == MAJOR_ASPECT_POINTS_HIGH_PRECISION

    def test_sun_moon_conjunction_wide(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Moon", "p2_name": "Sun", "aspect": "conjunction", "orbit": 4.0}
        factory._evaluate_sun_moon_conjunction(aspect)
        assert factory.score_value == MAJOR_ASPECT_POINTS_STANDARD

    def test_sun_sun_other_aspects(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Sun", "p2_name": "Sun", "aspect": "trine", "orbit": 3.0}
        factory._evaluate_sun_sun_other_aspects(aspect)
        assert factory.score_value == MINOR_ASPECT_POINTS

    def test_sun_moon_other_aspects(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Sun", "p2_name": "Moon", "aspect": "sextile", "orbit": 2.5}
        factory._evaluate_sun_moon_other_aspects(aspect)
        assert factory.score_value == MINOR_ASPECT_POINTS

    def test_sun_ascendant_aspect(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Sun", "p2_name": "Ascendant", "aspect": "trine", "orbit": 2.0}
        factory._evaluate_sun_ascendant_aspect(aspect)
        assert factory.score_value == SUN_ASCENDANT_ASPECT_POINTS

    def test_moon_ascendant_aspect(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Moon", "p2_name": "Ascendant", "aspect": "sextile", "orbit": 3.0}
        factory._evaluate_moon_ascendant_aspect(aspect)
        assert factory.score_value == MOON_ASCENDANT_ASPECT_POINTS

    def test_venus_mars_aspect(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Venus", "p2_name": "Mars", "aspect": "opposition", "orbit": 2.5}
        factory._evaluate_venus_mars_aspect(aspect)
        assert factory.score_value == VENUS_MARS_ASPECT_POINTS

    def test_evaluate_aspect_records_aspect(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Mercury", "p2_name": "Venus", "aspect": "sextile", "orbit": 2.0}
        factory._evaluate_aspect(aspect, 4, rule="test", description="test")
        assert len(factory.relationship_score_aspects) == 1
        recorded = factory.relationship_score_aspects[0]
        assert recorded.p1_name == "Mercury"
        assert recorded.p2_name == "Venus"
        assert recorded.aspect == "sextile"
        assert recorded.orbit == approx(2.0)

    def test_non_matching_aspect_ignored(self, subject1, subject2):
        """An aspect that doesn't match any evaluation rule leaves score unchanged."""
        factory = RelationshipScoreFactory(subject1, subject2)
        aspect = {"p1_name": "Jupiter", "p2_name": "Saturn", "aspect": "trine", "orbit": 4.0}
        factory._evaluate_sun_sun_main_aspect(aspect)
        factory._evaluate_sun_moon_conjunction(aspect)
        factory._evaluate_sun_ascendant_aspect(aspect)
        factory._evaluate_moon_ascendant_aspect(aspect)
        factory._evaluate_venus_mars_aspect(aspect)
        assert factory.score_value == 0


# ---------------------------------------------------------------------------
# 4. Destiny Sign Evaluation
# ---------------------------------------------------------------------------


class TestDestinySignEvaluation:
    """Destiny sign triggers when both subjects share the same sun sign quality."""

    def test_same_quality_triggers_destiny(self, cardinal_aries, cardinal_cancer):
        factory = RelationshipScoreFactory(cardinal_aries, cardinal_cancer)
        factory._evaluate_destiny_sign()
        assert factory.is_destiny_sign is True
        assert factory.score_value == DESTINY_SIGN_POINTS

    def test_different_quality_does_not_trigger(self, cardinal_aries, fixed_taurus):
        factory = RelationshipScoreFactory(cardinal_aries, fixed_taurus)
        factory._evaluate_destiny_sign()
        assert factory.is_destiny_sign is False
        assert factory.score_value == 0

    def test_destiny_flag_is_bool(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        factory._evaluate_destiny_sign()
        assert isinstance(factory.is_destiny_sign, bool)

    def test_initially_false(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        assert factory.is_destiny_sign is False

    def test_destiny_sign_appears_in_breakdown(self, cardinal_aries, cardinal_cancer):
        score = RelationshipScoreFactory(cardinal_aries, cardinal_cancer).get_relationship_score()
        if score.is_destiny_sign:
            destiny_items = [b for b in score.score_breakdown if b.rule == "destiny_sign"]
            assert len(destiny_items) == 1
            assert destiny_items[0].points == DESTINY_SIGN_POINTS


# ---------------------------------------------------------------------------
# 5. Score Breakdown Structure
# ---------------------------------------------------------------------------


class TestScoreBreakdownStructure:
    """Validate the shape and consistency of the score breakdown."""

    def test_breakdown_is_list(self, subject1, subject2):
        score = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        assert isinstance(score.score_breakdown, list)

    def test_breakdown_items_have_expected_keys(self, subject1, subject2):
        score = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        for item in score.score_breakdown:
            assert hasattr(item, "rule")
            assert hasattr(item, "description")
            assert hasattr(item, "points")
            assert hasattr(item, "details")

    def test_breakdown_points_are_positive(self, subject1, subject2):
        score = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        for item in score.score_breakdown:
            assert item.points > 0

    def test_breakdown_sum_equals_total_score(self, subject1, subject2):
        score = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        breakdown_sum = sum(item.points for item in score.score_breakdown)
        assert breakdown_sum == score.score_value

    def test_breakdown_sum_equals_total_john_yoko(self, john, yoko):
        score = RelationshipScoreFactory(john, yoko).get_relationship_score()
        breakdown_sum = sum(item.points for item in score.score_breakdown)
        assert breakdown_sum == score.score_value

    def test_breakdown_rules_are_known(self, subject1, subject2):
        valid_rules = {
            "destiny_sign",
            "sun_sun_major",
            "sun_moon_conjunction",
            "sun_sun_minor",
            "sun_moon_other",
            "sun_ascendant",
            "moon_ascendant",
            "venus_mars",
        }
        score = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        for item in score.score_breakdown:
            assert item.rule in valid_rules, f"Unknown rule: {item.rule}"

    def test_non_destiny_items_have_orbit_detail(self, subject1, subject2):
        score = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        for item in score.score_breakdown:
            if item.rule != "destiny_sign":
                assert item.details is not None
                assert "orbit:" in item.details.lower()

    def test_breakdown_rule_strings_are_nonempty(self, subject1, subject2):
        score = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        for item in score.score_breakdown:
            assert isinstance(item.rule, str)
            assert len(item.rule) > 0

    def test_breakdown_description_strings_are_nonempty(self, subject1, subject2):
        score = RelationshipScoreFactory(subject1, subject2).get_relationship_score()
        for item in score.score_breakdown:
            assert isinstance(item.description, str)
            assert len(item.description) > 0


# ---------------------------------------------------------------------------
# 6. Score With Different Aspect Modes
# ---------------------------------------------------------------------------


class TestScoreWithDifferentAspects:
    """Compare major-only versus all-aspects modes."""

    def test_major_only_returns_valid_score(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2, use_only_major_aspects=True)
        score = factory.get_relationship_score()
        assert isinstance(score.score_value, (int, float))
        assert score.score_value >= 0

    def test_all_aspects_returns_valid_score(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2, use_only_major_aspects=False)
        score = factory.get_relationship_score()
        assert isinstance(score.score_value, (int, float))
        assert score.score_value >= 0

    def test_all_aspects_ge_major_only(self, subject1, subject2):
        """Including minor aspects should produce a score >= major-only."""
        major = RelationshipScoreFactory(subject1, subject2, use_only_major_aspects=True).get_relationship_score()
        all_ = RelationshipScoreFactory(subject1, subject2, use_only_major_aspects=False).get_relationship_score()
        assert all_.score_value >= major.score_value

    def test_major_filter_blocks_minor_aspect(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2, use_only_major_aspects=True)
        minor = {"p1_name": "Jupiter", "p2_name": "Saturn", "aspect": "quintile", "orbit": 1.0}
        factory._evaluate_aspect(minor, 3, rule="test", description="test")
        assert factory.score_value == 0  # quintile blocked

    def test_minor_aspect_passes_when_all(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2, use_only_major_aspects=False)
        minor = {"p1_name": "Jupiter", "p2_name": "Saturn", "aspect": "quintile", "orbit": 1.0}
        factory._evaluate_aspect(minor, 3, rule="test", description="test")
        assert factory.score_value == 3

    def test_major_aspect_passes_regardless(self, subject1, subject2):
        for mode in (True, False):
            factory = RelationshipScoreFactory(subject1, subject2, use_only_major_aspects=mode)
            major = {"p1_name": "Mercury", "p2_name": "Venus", "aspect": "trine", "orbit": 2.0}
            factory._evaluate_aspect(major, 5, rule="test", description="test")
            assert factory.score_value == 5

    def test_major_aspects_constant(self):
        expected = {"conjunction", "opposition", "square", "trine", "sextile"}
        assert RelationshipScoreFactory.MAJOR_ASPECTS == expected


# ---------------------------------------------------------------------------
# 7. Symmetry
# ---------------------------------------------------------------------------


class TestSymmetry:
    """Score(A,B) may differ from Score(B,A) — verify both directions work."""

    def test_both_directions_produce_valid_scores(self, john, yoko):
        ab = RelationshipScoreFactory(john, yoko).get_relationship_score()
        ba = RelationshipScoreFactory(yoko, john).get_relationship_score()
        assert isinstance(ab.score_value, (int, float))
        assert isinstance(ba.score_value, (int, float))
        assert ab.score_value >= 0
        assert ba.score_value >= 0

    def test_both_directions_have_descriptions(self, john, yoko):
        ab = RelationshipScoreFactory(john, yoko).get_relationship_score()
        ba = RelationshipScoreFactory(yoko, john).get_relationship_score()
        assert ab.score_description in VALID_DESCRIPTIONS
        assert ba.score_description in VALID_DESCRIPTIONS

    def test_both_directions_have_breakdowns(self, john, yoko):
        ab = RelationshipScoreFactory(john, yoko).get_relationship_score()
        ba = RelationshipScoreFactory(yoko, john).get_relationship_score()
        assert isinstance(ab.score_breakdown, list)
        assert isinstance(ba.score_breakdown, list)

    def test_destiny_sign_symmetric(self, john, yoko):
        """Destiny sign depends only on quality, so it should be the same."""
        ab = RelationshipScoreFactory(john, yoko).get_relationship_score()
        ba = RelationshipScoreFactory(yoko, john).get_relationship_score()
        assert ab.is_destiny_sign == ba.is_destiny_sign


# ---------------------------------------------------------------------------
# 8. Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Self-compatibility, cross-era subjects, and other boundary scenarios."""

    def test_same_subject_self_compatibility(self, john):
        score = RelationshipScoreFactory(john, john).get_relationship_score()
        assert score.score_value >= 0
        assert score.score_description in VALID_DESCRIPTIONS

    def test_self_compatibility_has_breakdown(self, john):
        score = RelationshipScoreFactory(john, john).get_relationship_score()
        breakdown_sum = sum(item.points for item in score.score_breakdown)
        assert breakdown_sum == score.score_value

    def test_subjects_from_different_eras(self, john, ancient_subject):
        score = RelationshipScoreFactory(john, ancient_subject).get_relationship_score()
        assert score.score_value >= 0
        assert score.score_description in VALID_DESCRIPTIONS

    def test_synastry_aspects_initialized(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        assert hasattr(factory, "_synastry_aspects")
        assert isinstance(factory._synastry_aspects, list)

    def test_high_precision_scores_higher_than_wide(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        tight = {"p1_name": "Sun", "p2_name": "Sun", "aspect": "conjunction", "orbit": 1.5}
        factory._evaluate_sun_sun_main_aspect(tight)
        tight_score = factory.score_value

        factory.score_value = 0
        wide = {"p1_name": "Sun", "p2_name": "Sun", "aspect": "conjunction", "orbit": 3.0}
        factory._evaluate_sun_sun_main_aspect(wide)
        wide_score = factory.score_value

        assert tight_score >= wide_score

    def test_aspects_list_populated_after_scoring(self, subject1, subject2):
        factory = RelationshipScoreFactory(subject1, subject2)
        score = factory.get_relationship_score()
        # aspects list and breakdown should be in sync
        assert len(score.aspects) == len([b for b in score.score_breakdown if b.rule != "destiny_sign"])

    def test_score_model_subjects_list(self, john, yoko):
        score = RelationshipScoreFactory(john, yoko).get_relationship_score()
        assert len(score.subjects) == 2
        assert score.subjects[0] == john
        assert score.subjects[1] == yoko

    def test_score_value_type_after_all_evaluations(self, john, yoko):
        score = RelationshipScoreFactory(john, yoko).get_relationship_score()
        # Must remain numeric even after all internal mutations
        assert isinstance(score.score_value, (int, float))

    def test_axis_orb_limit_kwarg_accepted(self, subject1, subject2):
        """Ensure the optional axis_orb_limit keyword is forwarded."""
        factory = RelationshipScoreFactory(subject1, subject2, axis_orb_limit=5.0)
        score = factory.get_relationship_score()
        assert score.score_value >= 0


# =============================================================================
# REGRESSION: Exact Score Values for Famous Couples
# =============================================================================


class TestExactRegressionScores:
    """
    Exact regression values for historically significant couples.

    These tests use city/nation with suppress_geonames_warning to match
    the original test data that was generated with GeoNames lookups.
    """

    @pytest.fixture(scope="class")
    def john_lennon(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "John", 1940, 10, 9, 18, 30, "Liverpool", "UK", suppress_geonames_warning=True
        )

    @pytest.fixture(scope="class")
    def yoko_ono(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Yoko", 1933, 2, 18, 20, 30, "Tokyo", "JP", suppress_geonames_warning=True
        )

    @pytest.fixture(scope="class")
    def freud(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Freud", 1856, 5, 6, 18, 30, "Freiberg", "DE", suppress_geonames_warning=True
        )

    @pytest.fixture(scope="class")
    def jung(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Jung", 1875, 7, 26, 18, 30, "Kesswil", "CH", suppress_geonames_warning=True
        )

    @pytest.fixture(scope="class")
    def richard_burton(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Richard Burton", 1925, 11, 10, 15, 0, "Pontrhydyfen", "UK", suppress_geonames_warning=True
        )

    @pytest.fixture(scope="class")
    def liz_taylor(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Elizabeth Taylor", 1932, 2, 27, 2, 30, "London", "UK", suppress_geonames_warning=True
        )

    @pytest.fixture(scope="class")
    def dario_fo(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Dario Fo", 1926, 3, 24, 12, 25, "Sangiano", "IT", suppress_geonames_warning=True
        )

    @pytest.fixture(scope="class")
    def franca_rame(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Franca Rame", 1929, 7, 18, 12, 25, "Parabiago", "IT", suppress_geonames_warning=True
        )

    def test_john_lennon_yoko_ono_exact_score(self, john_lennon, yoko_ono):
        """Regression: John Lennon & Yoko Ono score = 12, 'Important'."""
        score = RelationshipScoreFactory(john_lennon, yoko_ono).get_relationship_score()
        assert score.score_value == 12
        assert score.score_description == "Important"

    def test_freud_jung_exact_score(self, freud, jung):
        """Regression: Freud & Jung score = 32, 'Rare Exceptional'."""
        score = RelationshipScoreFactory(freud, jung).get_relationship_score()
        assert score.score_value == 32
        assert score.score_description == "Rare Exceptional"

    def test_burton_taylor_exact_score(self, richard_burton, liz_taylor):
        """Regression: Richard Burton & Liz Taylor score = 23, 'Exceptional'."""
        score = RelationshipScoreFactory(richard_burton, liz_taylor).get_relationship_score()
        assert score.score_value == 23
        assert score.score_description == "Exceptional"

    def test_dario_franca_exact_score(self, dario_fo, franca_rame):
        """Regression: Dario Fo & Franca Rame score = 13, 'Important'."""
        score = RelationshipScoreFactory(dario_fo, franca_rame).get_relationship_score()
        assert score.score_value == 13
        assert score.score_description == "Important"


if __name__ == "__main__":
    pytest.main(["-vv", __file__])
