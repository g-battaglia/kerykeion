"""
Comprehensive tests for RelationshipScoreFactory module.
This test suite aims to achieve 100% code coverage.
"""

import pytest
from kerykeion import AstrologicalSubjectFactory
from kerykeion.relationship_score_factory import RelationshipScoreFactory


class TestRelationshipScoreFactory:
    """Test cases for RelationshipScoreFactory covering all code paths."""

    def setup_method(self):
        """Setup for each test method."""
        # Create two basic astrological subjects for testing
        self.subject1 = AstrologicalSubjectFactory.from_birth_data(
            name="Subject 1",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            city="New York",
            nation="US",
            suppress_geonames_warning=True
        )

        self.subject2 = AstrologicalSubjectFactory.from_birth_data(
            name="Subject 2",
            year=1992,
            month=8,
            day=20,
            hour=14,
            minute=45,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            city="New York",
            nation="US",
            suppress_geonames_warning=True
        )

    def test_basic_relationship_score_creation(self):
        """Test basic relationship score factory creation."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        assert factory.first_subject == self.subject1
        assert factory.second_subject == self.subject2
        assert factory.use_only_major_aspects  # Default value
        assert factory.score_value == 0  # Initial value

    def test_relationship_score_with_major_aspects_only(self):
        """Test relationship score using only major aspects."""
        factory = RelationshipScoreFactory(
            self.subject1,
            self.subject2,
            use_only_major_aspects=True
        )

        score = factory.get_relationship_score()

        assert hasattr(score, 'score_value')
        assert hasattr(score, 'score_description')
        assert hasattr(score, 'is_destiny_sign')
        assert hasattr(score, 'aspects')
        assert hasattr(score, 'subjects')
        assert isinstance(score.score_value, (int, float))
        assert isinstance(score.score_description, str)

    def test_relationship_score_with_all_aspects(self):
        """Test relationship score using all aspects."""
        factory = RelationshipScoreFactory(
            self.subject1,
            self.subject2,
            use_only_major_aspects=False
        )

        score = factory.get_relationship_score()

        assert hasattr(score, 'score_value')
        assert hasattr(score, 'score_description')
        assert isinstance(score.score_value, (int, float))

    def test_destiny_sign_evaluation(self):
        """Test destiny sign evaluation (same sun sign quality)."""
        # Create subjects with same sun sign quality
        subject_same_quality_1 = AstrologicalSubjectFactory.from_birth_data(
            name="Same Quality 1",
            year=1990, month=3, day=21, hour=12, minute=0,  # Aries (Cardinal)
            lat=40.7128, lng=-74.0060, tz_str="America/New_York",
            city="New York", nation="US",
            suppress_geonames_warning=True
        )

        subject_same_quality_2 = AstrologicalSubjectFactory.from_birth_data(
            name="Same Quality 2",
            year=1990, month=6, day=21, hour=12, minute=0,  # Cancer (Cardinal)
            lat=40.7128, lng=-74.0060, tz_str="America/New_York",
            city="New York", nation="US",
            suppress_geonames_warning=True
        )

        factory = RelationshipScoreFactory(subject_same_quality_1, subject_same_quality_2)
        score = factory.get_relationship_score()

        # Should have some score from destiny sign if qualities match
        assert score.score_value >= 0

    def test_score_descriptions_boundaries(self):
        """Test score description boundaries."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        # Test internal score description evaluation
        # Set different score values and check descriptions
        test_cases = [
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

        for score_value, expected_description in test_cases:
            factory.score_value = score_value
            factory._evaluate_relationship_score_description()
            assert factory.relationship_score_description == expected_description

    def test_sun_sun_main_aspects(self):
        """Test sun-sun main aspect evaluation."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        # Mock aspect for sun-sun conjunction
        mock_aspect = {
            "p1_name": "Sun",
            "p2_name": "Sun",
            "aspect": "conjunction",
            "orbit": 1.5  # Tight orb
        }

        initial_score = factory.score_value
        factory._evaluate_sun_sun_main_aspect(mock_aspect)

        # Should add points for sun-sun conjunction
        assert factory.score_value > initial_score

    def test_sun_moon_conjunction(self):
        """Test sun-moon conjunction evaluation."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        mock_aspect = {
            "p1_name": "Sun",
            "p2_name": "Moon",
            "aspect": "conjunction",
            "orbit": 1.0
        }

        initial_score = factory.score_value
        factory._evaluate_sun_moon_conjunction(mock_aspect)

        # Should add points for sun-moon conjunction
        assert factory.score_value > initial_score

    def test_sun_ascendant_aspect(self):
        """Test sun-ascendant aspect evaluation."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        mock_aspect = {
            "p1_name": "Sun",
            "p2_name": "Ascendant",
            "aspect": "trine",
            "orbit": 2.0
        }

        initial_score = factory.score_value
        factory._evaluate_sun_ascendant_aspect(mock_aspect)

        # Should add points for sun-ascendant aspect
        assert factory.score_value > initial_score

    def test_moon_ascendant_aspect(self):
        """Test moon-ascendant aspect evaluation."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        mock_aspect = {
            "p1_name": "Moon",
            "p2_name": "Ascendant",
            "aspect": "sextile",
            "orbit": 3.0
        }

        initial_score = factory.score_value
        factory._evaluate_moon_ascendant_aspect(mock_aspect)

        # Should add points for moon-ascendant aspect
        assert factory.score_value > initial_score

    def test_venus_mars_aspect(self):
        """Test venus-mars aspect evaluation."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        mock_aspect = {
            "p1_name": "Venus",
            "p2_name": "Mars",
            "aspect": "opposition",
            "orbit": 2.5
        }

        initial_score = factory.score_value
        factory._evaluate_venus_mars_aspect(mock_aspect)

        # Should add points for venus-mars aspect
        assert factory.score_value > initial_score

    def test_evaluate_aspect_with_major_aspects_only(self):
        """Test aspect evaluation with major aspects filter."""
        factory = RelationshipScoreFactory(
            self.subject1,
            self.subject2,
            use_only_major_aspects=True
        )

        # Test major aspect - should be processed
        major_aspect = {
            "p1_name": "Mercury",
            "p2_name": "Venus",
            "aspect": "trine",  # Major aspect
            "orbit": 2.0
        }

        initial_score = factory.score_value
        factory._evaluate_aspect(major_aspect, 5)
        assert factory.score_value == initial_score + 5

        # Test minor aspect - should be ignored with major_only=True
        minor_aspect = {
            "p1_name": "Jupiter",
            "p2_name": "Saturn",
            "aspect": "quintile",  # Minor aspect
            "orbit": 1.0
        }

        score_before_minor = factory.score_value
        factory._evaluate_aspect(minor_aspect, 3)
        assert factory.score_value == score_before_minor  # Should not change

    def test_evaluate_aspect_with_all_aspects(self):
        """Test aspect evaluation including minor aspects."""
        factory = RelationshipScoreFactory(
            self.subject1,
            self.subject2,
            use_only_major_aspects=False
        )

        # Test minor aspect - should be processed
        minor_aspect = {
            "p1_name": "Jupiter",
            "p2_name": "Saturn",
            "aspect": "quintile",  # Minor aspect
            "orbit": 1.0
        }

        initial_score = factory.score_value
        factory._evaluate_aspect(minor_aspect, 3)
        assert factory.score_value == initial_score + 3

    def test_high_precision_vs_standard_orb(self):
        """Test different scoring for tight vs wide orbs."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        # High precision orb (≤2°)
        tight_aspect = {
            "p1_name": "Sun",
            "p2_name": "Sun",
            "aspect": "conjunction",
            "orbit": 1.5  # ≤ 2°
        }

        # Standard orb (>2°)
        wide_aspect = {
            "p1_name": "Sun",
            "p2_name": "Sun",
            "aspect": "conjunction",
            "orbit": 3.0  # > 2°
        }

        # Test that tight orbs get more points
        factory._evaluate_sun_sun_main_aspect(tight_aspect)
        tight_score = factory.score_value

        factory.score_value = 0  # Reset
        factory._evaluate_sun_sun_main_aspect(wide_aspect)
        wide_score = factory.score_value

        # Tight orb should score higher than wide orb
        assert tight_score >= wide_score

    def test_relationship_score_aspects_list(self):
        """Test that aspects are properly recorded."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        mock_aspect = {
            "p1_name": "Mercury",
            "p2_name": "Venus",
            "aspect": "sextile",
            "orbit": 2.0
        }

        initial_count = len(factory.relationship_score_aspects)
        factory._evaluate_aspect(mock_aspect, 4)

        # Should add aspect to the list
        assert len(factory.relationship_score_aspects) == initial_count + 1

        # Check aspect details
        recorded_aspect = factory.relationship_score_aspects[-1]
        assert recorded_aspect.p1_name == "Mercury"
        assert recorded_aspect.p2_name == "Venus"
        assert recorded_aspect.aspect == "sextile"
        assert recorded_aspect.orbit == 2.0

    def test_same_subject_relationship(self):
        """Test relationship score between same subject."""
        factory = RelationshipScoreFactory(self.subject1, self.subject1)
        score = factory.get_relationship_score()

        # Should get high score for identical subjects
        assert score.score_value > 0
        assert score.score_description in [
            "Minimal", "Medium", "Important",
            "Very Important", "Exceptional", "Rare Exceptional"
        ]

    def test_destiny_sign_flag(self):
        """Test destiny sign flag functionality."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        # Initially should be false (default)
        assert not factory.is_destiny_sign

        # Test evaluation
        factory._evaluate_destiny_sign()

        # Flag should remain boolean
        assert isinstance(factory.is_destiny_sign, bool)

    def test_score_consistency(self):
        """Test that scores are consistent across multiple calculations."""
        factory1 = RelationshipScoreFactory(self.subject1, self.subject2)
        factory2 = RelationshipScoreFactory(self.subject1, self.subject2)

        score1 = factory1.get_relationship_score()
        score2 = factory2.get_relationship_score()

        # Should be identical for same subjects
        assert score1.score_value == score2.score_value
        assert score1.score_description == score2.score_description

    def test_synastry_aspects_initialization(self):
        """Test that synastry aspects are properly initialized."""
        factory = RelationshipScoreFactory(self.subject1, self.subject2)

        # Should have synastry aspects computed
        assert hasattr(factory, '_synastry_aspects')
        assert isinstance(factory._synastry_aspects, list)

    def test_major_aspects_constant(self):
        """Test major aspects constant."""
        expected_major_aspects = {"conjunction", "opposition", "square", "trine", "sextile"}
        assert RelationshipScoreFactory.MAJOR_ASPECTS == expected_major_aspects

    def test_score_mapping_constant(self):
        """Test score mapping constant."""
        RelationshipScoreFactory(self.subject1, self.subject2)

        assert hasattr(RelationshipScoreFactory, 'SCORE_MAPPING')
        assert isinstance(RelationshipScoreFactory.SCORE_MAPPING, list)
        assert len(RelationshipScoreFactory.SCORE_MAPPING) == 6  # 6 categories


if __name__ == "__main__":
    pytest.main(["-vv", __file__])
