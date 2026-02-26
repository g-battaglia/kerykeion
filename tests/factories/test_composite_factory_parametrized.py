"""
Comprehensive Parametrized Tests for CompositeSubjectFactory.

This module provides extensive test coverage for the CompositeSubjectFactory
across all defined synastry pairs.

The tests compare computed composite chart values against pre-generated
expected fixtures to ensure consistency and catch regressions.
"""

import pytest
from pathlib import Path
from typing import Any, Dict, Optional

from kerykeion import AstrologicalSubjectFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory

from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    SYNASTRY_PAIRS,
    CORE_PLANETS,
    HOUSES,
    get_primary_test_subjects,
)

# Configuration directory for expected data
CONFIGURATIONS_DIR = Path(__file__).parent.parent / "data" / "configurations"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def load_expected_composites() -> Optional[Dict[str, Any]]:
    """Load expected composite chart data."""
    fixture_path = CONFIGURATIONS_DIR / "composite" / "expected_composite_charts.py"

    if not fixture_path.exists():
        return None

    import importlib.util

    spec = importlib.util.spec_from_file_location("fixture", fixture_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return getattr(module, "EXPECTED_COMPOSITE_CHARTS", None)


def get_subject_data_by_id(subject_id: str) -> Optional[Dict[str, Any]]:
    """Get subject data by ID from temporal subjects."""
    for data in TEMPORAL_SUBJECTS:
        if data["id"] == subject_id:
            return data
    return None


def create_subject_from_data(data: Dict[str, Any]):
    """Create an AstrologicalSubjectModel from subject data dictionary."""
    return AstrologicalSubjectFactory.from_birth_data(
        name=data.get("name", data["id"]),
        year=data["year"],
        month=data["month"],
        day=data["day"],
        hour=data["hour"],
        minute=data["minute"],
        lat=data["lat"],
        lng=data["lng"],
        tz_str=data["tz_str"],
        online=False,
        suppress_geonames_warning=True,
    )


def assert_position_within_tolerance(
    actual: float,
    expected: float,
    tolerance: float = 0.0001,
    message: str = "",
):
    """Assert that two position values are within tolerance."""
    diff = abs(actual - expected)
    assert diff <= tolerance, f"{message}: Expected {expected}, got {actual}, diff={diff} > tolerance={tolerance}"


# =============================================================================
# COMPOSITE CHART CREATION TESTS
# =============================================================================


class TestCompositeChartCreation:
    """
    Test CompositeSubjectFactory for creating composite charts.
    """

    @pytest.mark.parametrize(
        "pair_ids",
        SYNASTRY_PAIRS,
        ids=lambda p: f"{p[0]}_x_{p[1]}",
    )
    def test_composite_creation(self, pair_ids):
        """Test that composite charts can be created for all synastry pairs."""
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

        factory = CompositeSubjectFactory(first_subject, second_subject)
        composite = factory.get_midpoint_composite_subject_model()

        assert composite is not None

        # Verify all planets are present
        for planet in CORE_PLANETS:
            planet_obj = getattr(composite, planet, None)
            assert planet_obj is not None, f"Planet {planet} missing in composite"
            assert 0 <= planet_obj.abs_pos < 360

    def test_composite_structure(self):
        """Test that composite chart has correct structure."""
        first_data = get_subject_data_by_id("john_lennon_1940")
        second_data = get_subject_data_by_id("paul_mccartney_1942")

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        factory = CompositeSubjectFactory(first_subject, second_subject)
        composite = factory.get_midpoint_composite_subject_model()

        # Check planets
        for planet in CORE_PLANETS:
            planet_obj = getattr(composite, planet)
            assert hasattr(planet_obj, "abs_pos")
            assert hasattr(planet_obj, "sign")
            assert hasattr(planet_obj, "position")

        # Check houses
        for house in HOUSES:
            house_obj = getattr(composite, house)
            assert hasattr(house_obj, "abs_pos")
            assert hasattr(house_obj, "sign")


# =============================================================================
# MIDPOINT CALCULATION TESTS
# =============================================================================


class TestMidpointCalculations:
    """
    Test that composite positions are correctly calculated as midpoints.
    """

    def test_sun_midpoint(self):
        """Test that composite Sun is the midpoint of both Suns."""
        first_data = get_subject_data_by_id("john_lennon_1940")
        second_data = get_subject_data_by_id("paul_mccartney_1942")

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        factory = CompositeSubjectFactory(first_subject, second_subject)
        composite = factory.get_midpoint_composite_subject_model()

        # Calculate expected midpoint
        sun1 = first_subject.sun.abs_pos
        sun2 = second_subject.sun.abs_pos

        # Midpoint calculation (accounting for 0/360 boundary)
        diff = abs(sun1 - sun2)
        if diff > 180:
            # Take the shorter arc
            expected_midpoint = ((sun1 + sun2) / 2 + 180) % 360
        else:
            expected_midpoint = (sun1 + sun2) / 2

        # Allow for alternate midpoint (opposite point)
        alt_midpoint = (expected_midpoint + 180) % 360

        actual = composite.sun.abs_pos

        diff_from_expected = min(
            abs(actual - expected_midpoint),
            abs(actual - alt_midpoint),
        )
        if diff_from_expected > 180:
            diff_from_expected = 360 - diff_from_expected

        assert diff_from_expected < 1, (
            f"Composite Sun {actual} is not near expected midpoint {expected_midpoint} or {alt_midpoint}"
        )

    def test_all_planets_are_midpoints(self):
        """Test that all composite planet positions are valid midpoints."""
        first_data = get_subject_data_by_id("john_lennon_1940")
        second_data = get_subject_data_by_id("paul_mccartney_1942")

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        factory = CompositeSubjectFactory(first_subject, second_subject)
        composite = factory.get_midpoint_composite_subject_model()

        for planet in CORE_PLANETS:
            planet1 = getattr(first_subject, planet)
            planet2 = getattr(second_subject, planet)
            composite_planet = getattr(composite, planet)

            pos1 = planet1.abs_pos
            pos2 = planet2.abs_pos
            composite_pos = composite_planet.abs_pos

            # Calculate both possible midpoints
            diff = abs(pos1 - pos2)
            if diff > 180:
                midpoint1 = ((pos1 + pos2) / 2 + 180) % 360
            else:
                midpoint1 = (pos1 + pos2) / 2
            midpoint2 = (midpoint1 + 180) % 360

            # Composite should be near one of the midpoints
            diff1 = abs(composite_pos - midpoint1)
            diff2 = abs(composite_pos - midpoint2)
            if diff1 > 180:
                diff1 = 360 - diff1
            if diff2 > 180:
                diff2 = 360 - diff2

            assert min(diff1, diff2) < 1, (
                f"{planet}: Composite pos {composite_pos} not near midpoints {midpoint1} or {midpoint2}"
            )


# =============================================================================
# EXPECTED DATA COMPARISON TESTS
# =============================================================================


class TestCompositeExpectedData:
    """
    Test composite charts against pre-generated expected fixtures.
    """

    @pytest.mark.parametrize(
        "pair_ids",
        SYNASTRY_PAIRS,
        ids=lambda p: f"{p[0]}_x_{p[1]}",
    )
    def test_composite_positions_match_expected(self, pair_ids):
        """Test that composite positions match expected values."""
        first_id, second_id = pair_ids
        pair_key = f"{first_id}__x__{second_id}"

        expected_data = load_expected_composites()

        if expected_data is None:
            pytest.skip("No expected composite data available")

        if pair_key not in expected_data:
            pytest.skip(f"No expected data for {pair_key}")

        first_data = get_subject_data_by_id(first_id)
        second_data = get_subject_data_by_id(second_id)

        if not first_data or not second_data:
            pytest.skip(f"Subject data not found for {pair_key}")

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        factory = CompositeSubjectFactory(first_subject, second_subject)
        composite = factory.get_midpoint_composite_subject_model()

        expected = expected_data[pair_key]

        # Compare planet positions
        for planet in CORE_PLANETS:
            actual_planet = getattr(composite, planet)
            expected_planet = expected.get("planets", {}).get(planet, {})

            if not expected_planet:
                continue

            assert_position_within_tolerance(
                actual_planet.abs_pos,
                expected_planet["abs_pos"],
                tolerance=0.0001,
                message=f"{planet} abs_pos for composite {pair_key}",
            )


# =============================================================================
# CONSISTENCY TESTS
# =============================================================================


class TestCompositeConsistency:
    """
    Test composite chart calculation consistency.
    """

    def test_composite_is_commutative(self):
        """Test that order of subjects doesn't affect composite (mostly)."""
        first_data = get_subject_data_by_id("john_lennon_1940")
        second_data = get_subject_data_by_id("paul_mccartney_1942")

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        # Create composite both ways
        factory1 = CompositeSubjectFactory(first_subject, second_subject)
        factory2 = CompositeSubjectFactory(second_subject, first_subject)

        composite1 = factory1.get_midpoint_composite_subject_model()
        composite2 = factory2.get_midpoint_composite_subject_model()

        # Planet positions should be the same
        for planet in CORE_PLANETS:
            pos1 = getattr(composite1, planet).abs_pos
            pos2 = getattr(composite2, planet).abs_pos

            assert_position_within_tolerance(
                pos1, pos2, tolerance=0.0001, message=f"{planet} position differs when order is reversed"
            )

    def test_composite_deterministic(self):
        """Test that composite calculations are deterministic."""
        first_data = get_subject_data_by_id("john_lennon_1940")
        second_data = get_subject_data_by_id("paul_mccartney_1942")

        first_subject = create_subject_from_data(first_data)
        second_subject = create_subject_from_data(second_data)

        factory1 = CompositeSubjectFactory(first_subject, second_subject)
        factory2 = CompositeSubjectFactory(first_subject, second_subject)

        composite1 = factory1.get_midpoint_composite_subject_model()
        composite2 = factory2.get_midpoint_composite_subject_model()

        for planet in CORE_PLANETS:
            pos1 = getattr(composite1, planet).abs_pos
            pos2 = getattr(composite2, planet).abs_pos

            assert pos1 == pos2, f"{planet} position is not deterministic"

    def test_composite_with_same_subject(self):
        """Test composite of a subject with itself."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data)

        factory = CompositeSubjectFactory(subject, subject)
        composite = factory.get_midpoint_composite_subject_model()

        # Composite with self should equal the natal chart
        for planet in CORE_PLANETS:
            natal_pos = getattr(subject, planet).abs_pos
            composite_pos = getattr(composite, planet).abs_pos

            assert_position_within_tolerance(
                composite_pos, natal_pos, tolerance=0.0001, message=f"{planet} composite with self should equal natal"
            )
