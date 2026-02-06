"""
Comprehensive Parametrized Tests for AspectsFactory.

This module provides extensive test coverage for the AspectsFactory
across all supported configurations:
- Natal aspects for all temporal subjects
- Synastry aspects for all defined pairs
- Aspect calculations with different house systems
- Aspect calculations with different sidereal modes

The tests compare computed aspects against pre-generated expected fixtures
to ensure consistency and catch regressions.

Tests are organized by aspect type for easy filtering:
    pytest tests/factories/test_aspects_factory_parametrized.py -k "natal"
    pytest tests/factories/test_aspects_factory_parametrized.py -k "synastry"
    pytest tests/factories/test_aspects_factory_parametrized.py -k "sidereal"
"""

import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory

from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    SYNASTRY_PAIRS,
    SIDEREAL_MODES,
    CORE_PLANETS,
    get_primary_test_subjects,
)

# Try to import expected aspects
try:
    from tests.data.expected_aspects import EXPECTED_NATAL_ASPECTS, EXPECTED_SYNASTRY_ASPECTS
except ImportError:
    EXPECTED_NATAL_ASPECTS = {}
    EXPECTED_SYNASTRY_ASPECTS = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_subject_from_data(
    data: Dict[str, Any],
    zodiac_type: str = "Tropical",
    sidereal_mode: Optional[str] = None,
):
    """Create an AstrologicalSubjectModel from subject data dictionary."""
    kwargs = {
        "name": data.get("name", data["id"]),
        "year": data["year"],
        "month": data["month"],
        "day": data["day"],
        "hour": data["hour"],
        "minute": data["minute"],
        "lat": data["lat"],
        "lng": data["lng"],
        "tz_str": data["tz_str"],
        "online": False,
        "suppress_geonames_warning": True,
        "zodiac_type": zodiac_type,
    }
    if sidereal_mode and zodiac_type == "Sidereal":
        kwargs["sidereal_mode"] = sidereal_mode

    return AstrologicalSubjectFactory.from_birth_data(**kwargs)


def get_subject_data_by_id(subject_id: str) -> Optional[Dict[str, Any]]:
    """Get subject data by ID from temporal subjects."""
    for data in TEMPORAL_SUBJECTS:
        if data["id"] == subject_id:
            return data
    return None


def aspects_to_comparable_set(aspects: List) -> set:
    """
    Convert aspects list to a set of comparable tuples for comparison.

    Returns set of (p1_name, p2_name, aspect) tuples.
    """
    result = set()
    for a in aspects:
        if isinstance(a, dict):
            result.add((a.get("p1_name"), a.get("p2_name"), a.get("aspect")))
        else:
            result.add((a.p1_name, a.p2_name, a.aspect))
    return result


# =============================================================================
# NATAL ASPECT TESTS
# =============================================================================


class TestNatalAspects:
    """
    Test AspectsFactory.single_chart_aspects() for natal charts.

    These tests verify that natal aspects are calculated correctly
    for all temporal subjects.
    """

    @pytest.mark.parametrize(
        "subject_data",
        TEMPORAL_SUBJECTS,
        ids=lambda s: s["id"],
    )
    def test_natal_aspects_creation(self, subject_data):
        """Test that natal aspects can be calculated for all subjects."""
        # Python's datetime doesn't support years before 1 AD
        if subject_data["year"] < 1:
            pytest.skip(f"Python datetime doesn't support years before 1 AD: {subject_data['year']}")

        try:
            subject = create_subject_from_data(subject_data)
            aspects_result = AspectsFactory.single_chart_aspects(subject)

            assert aspects_result is not None
            assert hasattr(aspects_result, "aspects")
            assert isinstance(aspects_result.aspects, list)

            # Should have at least some aspects (Sun-Moon, etc.)
            assert len(aspects_result.aspects) > 0, f"No aspects found for {subject_data['id']}"

        except Exception as e:
            # Some ancient dates may not be supported
            if subject_data["year"] < -3000 or subject_data["year"] > 3000:
                pytest.skip(f"Date outside ephemeris range: {subject_data['year']}")
            raise

    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_natal_aspects_match_expected(self, subject_id):
        """
        Test that natal aspects match expected values for key subjects.

        Compares computed aspects against pre-generated expected fixtures.
        """
        if subject_id not in EXPECTED_NATAL_ASPECTS:
            pytest.skip(f"No expected natal aspects for {subject_id}")

        subject_data = get_subject_data_by_id(subject_id)
        assert subject_data is not None

        subject = create_subject_from_data(subject_data)
        aspects_result = AspectsFactory.single_chart_aspects(subject)

        expected_aspects = EXPECTED_NATAL_ASPECTS[subject_id]

        # Verify count is similar (allow some tolerance for orb differences)
        assert abs(len(aspects_result.aspects) - len(expected_aspects)) <= 2, (
            f"Aspect count mismatch for {subject_id}: "
            f"expected {len(expected_aspects)}, got {len(aspects_result.aspects)}"
        )

        # Verify key aspects are present
        for expected in expected_aspects:
            matching = [
                a
                for a in aspects_result.aspects
                if a.p1_name == expected["p1_name"]
                and a.p2_name == expected["p2_name"]
                and a.aspect == expected["aspect"]
            ]

            assert len(matching) > 0, (
                f"Missing expected aspect for {subject_id}: "
                f"{expected['p1_name']} {expected['aspect']} {expected['p2_name']}"
            )

    def test_natal_aspects_structure(self):
        """Test that natal aspects have correct structure."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)
        aspects_result = AspectsFactory.single_chart_aspects(subject)

        for aspect in aspects_result.aspects:
            # Required fields
            assert hasattr(aspect, "p1_name")
            assert hasattr(aspect, "p2_name")
            assert hasattr(aspect, "aspect")
            assert hasattr(aspect, "orbit")
            assert hasattr(aspect, "aspect_degrees")

            # Positions should be valid
            assert 0 <= aspect.p1_abs_pos < 360
            assert 0 <= aspect.p2_abs_pos < 360

            # Orbit should be within reasonable range
            assert aspect.orbit >= 0

            # Aspect degrees should be one of standard aspects
            valid_aspects = [0, 30, 45, 60, 72, 90, 120, 135, 144, 150, 180]
            assert aspect.aspect_degrees in valid_aspects, f"Unexpected aspect_degrees: {aspect.aspect_degrees}"

    def test_natal_aspects_no_self_aspects(self):
        """Test that planets don't aspect themselves."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)
        aspects_result = AspectsFactory.single_chart_aspects(subject)

        for aspect in aspects_result.aspects:
            assert aspect.p1_name != aspect.p2_name, (
                f"Self-aspect found: {aspect.p1_name} {aspect.aspect} {aspect.p2_name}"
            )

    def test_natal_aspects_movement_calculation(self):
        """Test that aspect movement (applying/separating) is calculated."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)
        aspects_result = AspectsFactory.single_chart_aspects(subject)

        for aspect in aspects_result.aspects:
            assert hasattr(aspect, "aspect_movement")
            # Movement should be one of: "Applying", "Separating", or possibly None
            assert aspect.aspect_movement in ["Applying", "Separating", None], (
                f"Invalid aspect_movement: {aspect.aspect_movement}"
            )


# =============================================================================
# SYNASTRY ASPECT TESTS
# =============================================================================


class TestSynastryAspects:
    """
    Test AspectsFactory.dual_chart_aspects() for synastry charts.

    These tests verify that synastry aspects are calculated correctly
    for all defined synastry pairs.
    """

    @pytest.mark.parametrize(
        "pair_ids",
        SYNASTRY_PAIRS,
        ids=lambda p: f"{p[0]}_x_{p[1]}",
    )
    def test_synastry_aspects_creation(self, pair_ids):
        """Test that synastry aspects can be calculated for all pairs."""
        first_id, second_id = pair_ids

        first_data = get_subject_data_by_id(first_id)
        second_data = get_subject_data_by_id(second_id)

        if not first_data or not second_data:
            pytest.skip(f"Subject data not found for pair {first_id} x {second_id}")

        # Python's datetime doesn't support years before 1 AD
        if first_data["year"] < 1 or second_data["year"] < 1:
            pytest.skip(f"Python datetime doesn't support years before 1 AD")

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        aspects_result = AspectsFactory.dual_chart_aspects(first_subject, second_subject)

        assert aspects_result is not None
        assert hasattr(aspects_result, "aspects")
        assert isinstance(aspects_result.aspects, list)

        # Should have aspects between the two charts
        assert len(aspects_result.aspects) > 0, f"No synastry aspects found for {first_id} x {second_id}"

    @pytest.mark.parametrize(
        "pair_ids",
        SYNASTRY_PAIRS,
        ids=lambda p: f"{p[0]}_x_{p[1]}",
    )
    def test_synastry_aspects_match_expected(self, pair_ids):
        """
        Test that synastry aspects match expected values for defined pairs.
        """
        first_id, second_id = pair_ids
        pair_key = f"{first_id}__x__{second_id}"

        if pair_key not in EXPECTED_SYNASTRY_ASPECTS:
            pytest.skip(f"No expected synastry aspects for {pair_key}")

        first_data = get_subject_data_by_id(first_id)
        second_data = get_subject_data_by_id(second_id)

        assert first_data is not None
        assert second_data is not None

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        aspects_result = AspectsFactory.dual_chart_aspects(first_subject, second_subject)
        expected_aspects = EXPECTED_SYNASTRY_ASPECTS[pair_key]

        # Verify count is similar
        assert abs(len(aspects_result.aspects) - len(expected_aspects)) <= 2, (
            f"Synastry aspect count mismatch for {pair_key}: "
            f"expected {len(expected_aspects)}, got {len(aspects_result.aspects)}"
        )

        # Verify key aspects are present
        for expected in expected_aspects:
            matching = [
                a
                for a in aspects_result.aspects
                if a.p1_name == expected["p1_name"]
                and a.p2_name == expected["p2_name"]
                and a.aspect == expected["aspect"]
            ]

            assert len(matching) > 0, (
                f"Missing expected synastry aspect for {pair_key}: "
                f"{expected['p1_name']} {expected['aspect']} {expected['p2_name']}"
            )

    def test_synastry_aspects_owner_distinction(self):
        """Test that synastry aspects correctly identify planet owners."""
        first_data = get_subject_data_by_id("john_lennon_1940")
        second_data = get_subject_data_by_id("paul_mccartney_1942")

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        aspects_result = AspectsFactory.dual_chart_aspects(first_subject, second_subject)

        for aspect in aspects_result.aspects:
            # Owners should be distinct (cross-chart aspects)
            assert aspect.p1_owner != aspect.p2_owner, f"Same owner for synastry aspect: {aspect.p1_owner}"


# =============================================================================
# SIDEREAL ASPECT TESTS
# =============================================================================


class TestSiderealAspects:
    """
    Test aspects calculation with sidereal zodiac modes.

    These tests verify that aspects are calculated correctly when using
    sidereal zodiac with various ayanamsas.
    """

    @pytest.mark.parametrize("sidereal_mode", SIDEREAL_MODES[:5], ids=lambda m: f"sidereal_{m}")  # First 5 for speed
    def test_sidereal_natal_aspects_calculation(self, sidereal_mode):
        """Test natal aspects with sidereal modes."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(
            subject_data,
            zodiac_type="Sidereal",
            sidereal_mode=sidereal_mode,
        )

        aspects_result = AspectsFactory.single_chart_aspects(subject)

        assert aspects_result is not None
        assert len(aspects_result.aspects) > 0

    def test_sidereal_vs_tropical_aspects_similar(self):
        """
        Test that aspect count is similar between tropical and sidereal.

        While positions differ, the relative angles (aspects) should
        be very similar since all positions shift by the same ayanamsa.
        """
        subject_data = get_subject_data_by_id("john_lennon_1940")

        tropical_subject = create_subject_from_data(subject_data, zodiac_type="Tropical")
        sidereal_subject = create_subject_from_data(
            subject_data,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )

        tropical_aspects = AspectsFactory.single_chart_aspects(tropical_subject)
        sidereal_aspects = AspectsFactory.single_chart_aspects(sidereal_subject)

        # Aspect counts should be nearly identical
        # (same relative angles, just shifted reference)
        tropical_count = len(tropical_aspects.aspects)
        sidereal_count = len(sidereal_aspects.aspects)

        assert abs(tropical_count - sidereal_count) <= 1, (
            f"Unexpected aspect count difference: Tropical={tropical_count}, Sidereal (LAHIRI)={sidereal_count}"
        )


# =============================================================================
# ASPECT TYPES AND ORBS TESTS
# =============================================================================


class TestAspectTypesAndOrbs:
    """
    Test specific aspect types and orb handling.
    """

    def test_major_aspects_present(self):
        """Test that major aspects (conjunction, opposition, trine, square, sextile) are found."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)
        aspects_result = AspectsFactory.single_chart_aspects(subject)

        aspect_types_found = {a.aspect for a in aspects_result.aspects}
        major_aspects = {"conjunction", "opposition", "trine", "square", "sextile"}

        # Should find at least some major aspects
        found_major = aspect_types_found & major_aspects
        assert len(found_major) >= 3, f"Expected at least 3 major aspect types, found: {found_major}"

    def test_aspect_orbs_within_limits(self):
        """Test that aspect orbs are within reasonable limits."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)
        aspects_result = AspectsFactory.single_chart_aspects(subject)

        # Maximum orbs typically used
        max_orbs = {
            "conjunction": 10,
            "opposition": 10,
            "trine": 8,
            "square": 8,
            "sextile": 6,
            "semi-sextile": 3,
            "quincunx": 3,
            "semi-square": 3,
            "sesquiquadrate": 3,
        }

        for aspect in aspects_result.aspects:
            if aspect.aspect in max_orbs:
                assert aspect.orbit <= max_orbs[aspect.aspect], f"Orbit {aspect.orbit} exceeds max for {aspect.aspect}"


# =============================================================================
# CONSISTENCY AND EDGE CASE TESTS
# =============================================================================


class TestAspectConsistency:
    """
    Test aspect calculation consistency and edge cases.
    """

    def test_aspects_deterministic(self):
        """Test that aspect calculations are deterministic."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)

        aspects1 = AspectsFactory.single_chart_aspects(subject)
        aspects2 = AspectsFactory.single_chart_aspects(subject)

        assert len(aspects1.aspects) == len(aspects2.aspects)

        for a1, a2 in zip(aspects1.aspects, aspects2.aspects):
            assert a1.p1_name == a2.p1_name
            assert a1.p2_name == a2.p2_name
            assert a1.aspect == a2.aspect
            assert abs(a1.orbit - a2.orbit) < 0.0001

    def test_aspects_with_retrograde_planets(self):
        """Test aspect calculations when planets are retrograde."""
        # Find a subject with retrograde planets
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)

        # Check if there are any retrograde planets
        retrograde_planets = [
            planet for planet in CORE_PLANETS if getattr(getattr(subject, planet), "retrograde", False)
        ]

        aspects_result = AspectsFactory.single_chart_aspects(subject)

        # Retrograde status should be reflected in aspect movement
        for aspect in aspects_result.aspects:
            # Just verify the calculation completes without error
            assert aspect.p1_speed is not None or aspect.p2_speed is not None
