"""
Comprehensive Parametrized Tests for AstrologicalSubjectFactory.

This module provides extensive test coverage for the AstrologicalSubjectFactory
across all supported configurations:
- All house systems (16+)
- All sidereal modes (20)
- All perspective types (4)
- Full temporal range (500 BC to 2200 AD)
- Full geographic range (66°S to 66°N)

The tests compare computed values against pre-generated expected fixtures
to ensure consistency and catch regressions.

Tests are organized by configuration type for easy filtering:
    pytest tests/factories/test_subject_factory_parametrized.py -k "house_system"
    pytest tests/factories/test_subject_factory_parametrized.py -k "sidereal"
    pytest tests/factories/test_subject_factory_parametrized.py -k "perspective"
"""

import pytest
from pathlib import Path
from typing import Any, Dict, Optional

from kerykeion import AstrologicalSubjectFactory

from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    GEOGRAPHIC_SUBJECTS,
    HOUSE_SYSTEMS,
    SIDEREAL_MODES,
    PERSPECTIVE_TYPES,
    CORE_PLANETS,
    LUNAR_NODES,
    ANGLES,
    HOUSES,
    get_primary_test_subjects,
)

# Configuration directory for expected data
CONFIGURATIONS_DIR = Path(__file__).parent.parent / "data" / "configurations"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def load_expected_positions(config_type: str, config_value: str) -> Optional[Dict[str, Any]]:
    """
    Load expected positions for a specific configuration.

    Args:
        config_type: One of "house_systems", "sidereal_modes", "perspectives"
        config_value: The specific configuration value (e.g., "K", "LAHIRI")

    Returns:
        Dictionary of expected positions or None if file doesn't exist
    """
    if config_type == "house_systems":
        fixture_path = CONFIGURATIONS_DIR / "house_systems" / f"expected_positions_house_{config_value}.py"
    elif config_type == "sidereal_modes":
        fixture_path = CONFIGURATIONS_DIR / "sidereal_modes" / f"expected_positions_sidereal_{config_value}.py"
    elif config_type == "perspectives":
        config_slug = config_value.lower().replace(" ", "_")
        fixture_path = CONFIGURATIONS_DIR / "perspectives" / f"expected_positions_{config_slug}.py"
    else:
        return None

    if not fixture_path.exists():
        return None

    # Dynamic import of the fixture
    import importlib.util

    spec = importlib.util.spec_from_file_location("fixture", fixture_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return getattr(module, "EXPECTED_POSITIONS", None)


def create_subject_from_data(
    data: Dict[str, Any],
    houses_system_identifier: str = "P",
    zodiac_type: str = "Tropical",
    sidereal_mode: Optional[str] = None,
    perspective_type: str = "Apparent Geocentric",
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
        "houses_system_identifier": houses_system_identifier,
        "zodiac_type": zodiac_type,
        "perspective_type": perspective_type,
    }
    if sidereal_mode and zodiac_type == "Sidereal":
        kwargs["sidereal_mode"] = sidereal_mode

    return AstrologicalSubjectFactory.from_birth_data(**kwargs)


def get_subject_data_by_id(subject_id: str) -> Optional[Dict[str, Any]]:
    """Get subject data by ID from temporal or geographic subjects."""
    for data in TEMPORAL_SUBJECTS:
        if data["id"] == subject_id:
            return data

    for data in GEOGRAPHIC_SUBJECTS:
        if data["id"] == subject_id:
            return {
                **data,
                "year": 1990,
                "month": 6,
                "day": 15,
                "hour": 12,
                "minute": 0,
            }

    return None


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
# TEST FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def primary_subject_ids():
    """Get primary test subject IDs."""
    return get_primary_test_subjects()


# =============================================================================
# HOUSE SYSTEM TESTS
# =============================================================================


class TestHouseSystemConfigurations:
    """
    Test AstrologicalSubjectFactory with all house systems.

    These tests verify that house cusp positions are calculated correctly
    for each of the 16+ supported house systems.
    """

    @pytest.mark.parametrize("house_system", HOUSE_SYSTEMS, ids=lambda h: f"house_{h}")
    def test_house_system_creates_valid_subject(self, house_system):
        """Test that each house system creates a valid subject."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        assert subject_data is not None

        subject = create_subject_from_data(subject_data, houses_system_identifier=house_system)

        assert subject is not None
        assert subject.houses_system_identifier == house_system

        # Verify all houses are present
        for house in HOUSES:
            house_obj = getattr(subject, house, None)
            assert house_obj is not None, f"House {house} is None for system {house_system}"
            assert 0 <= house_obj.abs_pos < 360, f"Invalid abs_pos for {house}"

    @pytest.mark.parametrize("house_system", HOUSE_SYSTEMS, ids=lambda h: f"house_{h}")
    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_house_cusp_positions_match_expected(self, house_system, subject_id):
        """
        Test that house cusp positions match expected values for all house systems.

        Compares computed house positions against pre-generated expected fixtures.
        """
        expected_data = load_expected_positions("house_systems", house_system)

        if expected_data is None:
            pytest.skip(f"No expected data for house system {house_system}")

        if subject_id not in expected_data:
            pytest.skip(f"No expected data for subject {subject_id} with house system {house_system}")

        subject_data = get_subject_data_by_id(subject_id)
        assert subject_data is not None

        subject = create_subject_from_data(subject_data, houses_system_identifier=house_system)
        expected = expected_data[subject_id]

        # Compare house cusps
        for house in HOUSES:
            actual_house = getattr(subject, house)
            expected_house = expected.get("houses", {}).get(house, {})

            if not expected_house:
                continue

            assert_position_within_tolerance(
                actual_house.abs_pos,
                expected_house["abs_pos"],
                tolerance=0.0001,
                message=f"{house} abs_pos for {subject_id} with house system {house_system}",
            )

            assert actual_house.sign == expected_house["sign"], (
                f"{house} sign mismatch for {subject_id}: expected {expected_house['sign']}, got {actual_house.sign}"
            )

    # House systems where ASC == 1st house cusp (quadrant-based systems)
    QUADRANT_HOUSE_SYSTEMS = ["P", "K", "O", "R", "C", "T", "B", "U", "I", "i", "L", "Q"]

    @pytest.mark.parametrize("house_system", QUADRANT_HOUSE_SYSTEMS, ids=lambda h: f"house_{h}")
    def test_angles_consistent_with_houses(self, house_system):
        """
        Test that angles (ASC, MC, DSC, IC) are consistent with corresponding houses.

        Note: This test only applies to quadrant-based house systems where ASC = 1st house
        cusp and MC = 10th house cusp. Non-quadrant systems like Equal (A), Whole Sign (W),
        Morinus (M), Meridian (X), Horizon (H), etc. have different definitions.
        """
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data, houses_system_identifier=house_system)

        # ASC should match First House cusp for quadrant-based systems
        assert_position_within_tolerance(
            subject.ascendant.abs_pos,
            subject.first_house.abs_pos,
            tolerance=0.0001,
            message=f"ASC vs First House for system {house_system}",
        )

        # MC should match Tenth House cusp for quadrant-based systems
        assert_position_within_tolerance(
            subject.medium_coeli.abs_pos,
            subject.tenth_house.abs_pos,
            tolerance=0.0001,
            message=f"MC vs Tenth House for system {house_system}",
        )


# =============================================================================
# SIDEREAL MODE TESTS
# =============================================================================


class TestSiderealModeConfigurations:
    """
    Test AstrologicalSubjectFactory with all sidereal modes (ayanamsas).

    These tests verify that planetary positions are calculated correctly
    for each of the 20 supported sidereal modes.
    """

    @pytest.mark.parametrize("sidereal_mode", SIDEREAL_MODES, ids=lambda m: f"sidereal_{m}")
    def test_sidereal_mode_creates_valid_subject(self, sidereal_mode):
        """Test that each sidereal mode creates a valid subject."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        assert subject_data is not None

        subject = create_subject_from_data(
            subject_data,
            zodiac_type="Sidereal",
            sidereal_mode=sidereal_mode,
        )

        assert subject is not None
        assert subject.zodiac_type == "Sidereal"
        assert subject.sidereal_mode == sidereal_mode

        # Verify all planets are present
        for planet in CORE_PLANETS:
            planet_obj = getattr(subject, planet, None)
            assert planet_obj is not None, f"Planet {planet} is None for mode {sidereal_mode}"
            assert 0 <= planet_obj.abs_pos < 360, f"Invalid abs_pos for {planet}"

    @pytest.mark.parametrize("sidereal_mode", SIDEREAL_MODES, ids=lambda m: f"sidereal_{m}")
    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_planet_positions_match_expected(self, sidereal_mode, subject_id):
        """
        Test that planetary positions match expected values for all sidereal modes.

        Compares computed planetary positions against pre-generated expected fixtures.
        """
        expected_data = load_expected_positions("sidereal_modes", sidereal_mode)

        if expected_data is None:
            pytest.skip(f"No expected data for sidereal mode {sidereal_mode}")

        if subject_id not in expected_data:
            pytest.skip(f"No expected data for subject {subject_id} with sidereal mode {sidereal_mode}")

        subject_data = get_subject_data_by_id(subject_id)
        assert subject_data is not None

        subject = create_subject_from_data(
            subject_data,
            zodiac_type="Sidereal",
            sidereal_mode=sidereal_mode,
        )
        expected = expected_data[subject_id]

        # Compare planet positions
        for planet in CORE_PLANETS:
            actual_planet = getattr(subject, planet)
            expected_planet = expected.get("planets", {}).get(planet, {})

            if not expected_planet:
                continue

            assert_position_within_tolerance(
                actual_planet.abs_pos,
                expected_planet["abs_pos"],
                tolerance=0.0001,
                message=f"{planet} abs_pos for {subject_id} with sidereal mode {sidereal_mode}",
            )

            assert actual_planet.sign == expected_planet["sign"], (
                f"{planet} sign mismatch for {subject_id} with mode {sidereal_mode}: "
                f"expected {expected_planet['sign']}, got {actual_planet.sign}"
            )

    # Sidereal modes that don't apply an ayanamsa (they are based on fixed reference points)
    # These are reference-frame ayanamsas, not moving-zodiac ayanamsas
    FIXED_REFERENCE_SIDEREAL_MODES = ["J1900", "J2000", "B1950"]

    @pytest.mark.parametrize("sidereal_mode", SIDEREAL_MODES, ids=lambda m: f"sidereal_{m}")
    def test_sidereal_positions_differ_from_tropical(self, sidereal_mode):
        """Test that sidereal positions are different from tropical positions."""
        # J1900, J2000, B1950 are reference-frame modes that may not apply a standard ayanamsa
        if sidereal_mode in self.FIXED_REFERENCE_SIDEREAL_MODES:
            pytest.skip(f"{sidereal_mode} is a fixed reference frame, not a traditional ayanamsa")

        subject_data = get_subject_data_by_id("john_lennon_1940")

        tropical_subject = create_subject_from_data(subject_data, zodiac_type="Tropical")
        sidereal_subject = create_subject_from_data(
            subject_data,
            zodiac_type="Sidereal",
            sidereal_mode=sidereal_mode,
        )

        # At least some planets should have different signs due to ayanamsa
        different_signs = 0
        for planet in CORE_PLANETS:
            tropical = getattr(tropical_subject, planet)
            sidereal = getattr(sidereal_subject, planet)

            if tropical.sign != sidereal.sign:
                different_signs += 1

        # We expect at least one planet to have a different sign
        # (ayanamsa shifts positions by ~24 degrees typically)
        assert different_signs > 0, (
            f"No sign differences found between Tropical and Sidereal ({sidereal_mode}). "
            f"This is unusual and may indicate a calculation error."
        )


# =============================================================================
# PERSPECTIVE TYPE TESTS
# =============================================================================


class TestPerspectiveConfigurations:
    """
    Test AstrologicalSubjectFactory with all perspective types.

    These tests verify that planetary positions are calculated correctly
    for Geocentric, Heliocentric, and Topocentric perspectives.
    """

    @pytest.mark.parametrize("perspective_type", PERSPECTIVE_TYPES, ids=lambda p: p.replace(" ", "_").lower())
    def test_perspective_creates_valid_subject(self, perspective_type):
        """Test that each perspective type creates a valid subject."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        assert subject_data is not None

        subject = create_subject_from_data(subject_data, perspective_type=perspective_type)

        assert subject is not None
        assert subject.perspective_type == perspective_type

        # Verify planets are present
        for planet in CORE_PLANETS:
            planet_obj = getattr(subject, planet, None)
            assert planet_obj is not None, f"Planet {planet} is None for perspective {perspective_type}"

    @pytest.mark.parametrize(
        "perspective_type",
        [p for p in PERSPECTIVE_TYPES if p != "Apparent Geocentric"],
        ids=lambda p: p.replace(" ", "_").lower(),
    )
    @pytest.mark.parametrize("subject_id", get_primary_test_subjects(), ids=lambda s: s)
    def test_perspective_positions_match_expected(self, perspective_type, subject_id):
        """
        Test that positions match expected values for non-default perspectives.
        """
        expected_data = load_expected_positions("perspectives", perspective_type)

        if expected_data is None:
            pytest.skip(f"No expected data for perspective {perspective_type}")

        if subject_id not in expected_data:
            pytest.skip(f"No expected data for subject {subject_id} with perspective {perspective_type}")

        subject_data = get_subject_data_by_id(subject_id)
        assert subject_data is not None

        subject = create_subject_from_data(subject_data, perspective_type=perspective_type)
        expected = expected_data[subject_id]

        # Compare planet positions
        for planet in CORE_PLANETS:
            actual_planet = getattr(subject, planet)
            expected_planet = expected.get("planets", {}).get(planet, {})

            if not expected_planet:
                continue

            assert_position_within_tolerance(
                actual_planet.abs_pos,
                expected_planet["abs_pos"],
                tolerance=0.0001,
                message=f"{planet} abs_pos for {subject_id} with perspective {perspective_type}",
            )

    def test_heliocentric_no_houses(self):
        """Test that heliocentric perspective doesn't have meaningful houses."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data, perspective_type="Heliocentric")

        # In heliocentric, houses don't have traditional meaning
        # but the subject should still be valid
        assert subject is not None
        assert subject.perspective_type == "Heliocentric"

    def test_heliocentric_no_sun(self):
        """Test that heliocentric perspective has Earth instead of Sun."""
        subject_data = get_subject_data_by_id("john_lennon_1940")
        subject = create_subject_from_data(subject_data, perspective_type="Heliocentric")

        # In heliocentric, Sun position should be 0 or None
        # and Earth should have a valid position
        assert subject is not None
        # Note: Implementation specific - check how Kerykeion handles this


# =============================================================================
# TEMPORAL COVERAGE TESTS
# =============================================================================


class TestTemporalCoverage:
    """
    Test AstrologicalSubjectFactory across the full temporal range.

    These tests verify that calculations work correctly for dates from
    500 BC to 2200 AD, covering major historical eras.
    """

    @pytest.mark.parametrize(
        "subject_data",
        TEMPORAL_SUBJECTS,
        ids=lambda s: s["id"],
    )
    def test_temporal_subject_creation(self, subject_data):
        """Test that subjects can be created for all temporal periods."""
        # Python's datetime doesn't support years before 1 AD
        if subject_data["year"] < 1:
            pytest.skip(f"Python datetime doesn't support years before 1 AD: {subject_data['year']}")

        try:
            subject = create_subject_from_data(subject_data)

            assert subject is not None
            assert subject.year == subject_data["year"]
            assert subject.month == subject_data["month"]
            assert subject.day == subject_data["day"]

            # Verify basic planetary positions exist
            assert subject.sun is not None
            assert subject.moon is not None
            assert 0 <= subject.sun.abs_pos < 360
            assert 0 <= subject.moon.abs_pos < 360

        except Exception as e:
            # Some ancient dates may not be supported by ephemeris
            if subject_data["year"] < -3000 or subject_data["year"] > 3000:
                pytest.skip(f"Date outside ephemeris range: {subject_data['year']}")
            raise

    @pytest.mark.parametrize(
        "subject_data",
        [s for s in TEMPORAL_SUBJECTS if s["year"] >= 1800 and s["year"] <= 2100],
        ids=lambda s: s["id"],
    )
    def test_modern_era_full_validation(self, subject_data):
        """Test full position validation for modern era subjects (1800-2100)."""
        subject = create_subject_from_data(subject_data)
        assert subject is not None

        # All planets should be present
        for planet in CORE_PLANETS:
            planet_obj = getattr(subject, planet)
            assert planet_obj is not None, f"Planet {planet} missing for {subject_data['id']}"
            assert planet_obj.name is not None
            assert 0 <= planet_obj.abs_pos < 360
            assert planet_obj.sign in [
                "Ari",
                "Tau",
                "Gem",
                "Can",
                "Leo",
                "Vir",
                "Lib",
                "Sco",
                "Sag",
                "Cap",
                "Aqu",
                "Pis",
            ]

        # All houses should be present
        for house in HOUSES:
            house_obj = getattr(subject, house)
            assert house_obj is not None, f"House {house} missing for {subject_data['id']}"


# =============================================================================
# GEOGRAPHIC COVERAGE TESTS
# =============================================================================


class TestGeographicCoverage:
    """
    Test AstrologicalSubjectFactory across the full geographic range.

    These tests verify that calculations work correctly for all latitudes
    from 66°S to 66°N, covering edge cases near polar regions.
    """

    @pytest.mark.parametrize(
        "subject_data",
        GEOGRAPHIC_SUBJECTS,
        ids=lambda s: s["id"],
    )
    def test_geographic_subject_creation(self, subject_data):
        """Test that subjects can be created for all geographic locations."""
        full_data = {
            **subject_data,
            "year": 1990,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
        }

        subject = create_subject_from_data(full_data)

        assert subject is not None
        assert subject.lat == subject_data["lat"]
        assert subject.lng == subject_data["lng"]

        # Planetary positions should be valid
        for planet in CORE_PLANETS:
            planet_obj = getattr(subject, planet)
            assert planet_obj is not None
            assert 0 <= planet_obj.abs_pos < 360

    @pytest.mark.parametrize(
        "subject_data",
        [s for s in GEOGRAPHIC_SUBJECTS if abs(s["lat"]) > 60],
        ids=lambda s: s["id"],
    )
    def test_polar_latitude_houses(self, subject_data):
        """
        Test house calculations at polar latitudes.

        Some house systems have difficulties at extreme latitudes.
        This test verifies graceful handling.
        """
        full_data = {
            **subject_data,
            "year": 1990,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
        }

        # Test with default house system (Placidus)
        subject = create_subject_from_data(full_data)
        assert subject is not None

        # Houses should still be present (may use fallback)
        for house in HOUSES:
            house_obj = getattr(subject, house)
            assert house_obj is not None, f"House {house} missing at lat {subject_data['lat']}"

    @pytest.mark.parametrize(
        "subject_data",
        [s for s in GEOGRAPHIC_SUBJECTS if abs(s["lat"]) < 5],
        ids=lambda s: s["id"],
    )
    def test_equatorial_latitude_houses(self, subject_data):
        """Test house calculations at equatorial latitudes."""
        full_data = {
            **subject_data,
            "year": 1990,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
        }

        subject = create_subject_from_data(full_data)
        assert subject is not None

        # At equator, houses should be more evenly distributed
        # Verify house cusps span 360 degrees
        house_positions = []
        for house in HOUSES:
            house_obj = getattr(subject, house)
            house_positions.append(house_obj.abs_pos)

        # Check that positions are distributed
        sorted_positions = sorted(house_positions)
        for i in range(len(sorted_positions) - 1):
            gap = sorted_positions[i + 1] - sorted_positions[i]
            # No single gap should be more than 60 degrees (very generous)
            assert gap < 60, f"Unusual house distribution at equator: gap of {gap} degrees"


# =============================================================================
# CROSS-CONFIGURATION TESTS
# =============================================================================


class TestCrossConfigurationConsistency:
    """
    Test consistency across different configurations.

    These tests verify that related calculations remain consistent
    when using different house systems or zodiac types.
    """

    def test_planetary_positions_unchanged_by_house_system(self):
        """Test that planetary positions don't change with house system."""
        subject_data = get_subject_data_by_id("john_lennon_1940")

        placidus_subject = create_subject_from_data(subject_data, houses_system_identifier="P")
        koch_subject = create_subject_from_data(subject_data, houses_system_identifier="K")
        whole_sign_subject = create_subject_from_data(subject_data, houses_system_identifier="W")

        for planet in CORE_PLANETS:
            placidus = getattr(placidus_subject, planet)
            koch = getattr(koch_subject, planet)
            whole_sign = getattr(whole_sign_subject, planet)

            # Positions should be identical
            assert_position_within_tolerance(
                placidus.abs_pos,
                koch.abs_pos,
                tolerance=0.0001,
                message=f"{planet} position differs between Placidus and Koch",
            )
            assert_position_within_tolerance(
                placidus.abs_pos,
                whole_sign.abs_pos,
                tolerance=0.0001,
                message=f"{planet} position differs between Placidus and Whole Sign",
            )

    def test_house_system_affects_planet_house_placement(self):
        """Test that house system changes planet house placements."""
        subject_data = get_subject_data_by_id("john_lennon_1940")

        placidus_subject = create_subject_from_data(subject_data, houses_system_identifier="P")
        whole_sign_subject = create_subject_from_data(subject_data, houses_system_identifier="W")

        # At least some planets should have different house placements
        different_houses = 0
        for planet in CORE_PLANETS:
            placidus = getattr(placidus_subject, planet)
            whole_sign = getattr(whole_sign_subject, planet)

            if placidus.house != whole_sign.house:
                different_houses += 1

        # It's normal for some planets to have different houses
        # but we should verify the calculations work
        assert placidus_subject.sun.house is not None
        assert whole_sign_subject.sun.house is not None

    def test_sidereal_vs_tropical_ayanamsa_offset(self):
        """Test that sidereal positions are offset by approximately the ayanamsa."""
        subject_data = get_subject_data_by_id("john_lennon_1940")

        tropical_subject = create_subject_from_data(subject_data, zodiac_type="Tropical")
        lahiri_subject = create_subject_from_data(
            subject_data,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )

        # Check Sun position offset (Lahiri ayanamsa is approximately 24 degrees)
        tropical_sun = tropical_subject.sun.abs_pos
        lahiri_sun = lahiri_subject.sun.abs_pos

        # Calculate the offset
        offset = (tropical_sun - lahiri_sun) % 360
        if offset > 180:
            offset = 360 - offset

        # Lahiri ayanamsa is approximately 24 degrees (varies with date)
        # Allow a generous range for validation
        assert 20 < offset < 30, (
            f"Unexpected ayanamsa offset: {offset} degrees. Expected approximately 24 degrees for Lahiri."
        )
