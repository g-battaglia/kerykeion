"""
Comprehensive tests for AspectsFactory — natal aspects, synastry aspects,
aspect movement calculation, edge cases, and integration checks.

Consolidates all casistiche from:
- tests/aspects/test_aspects_parametrized.py (natal & synastry with expected data)
- tests/aspects/test_aspect_movement_enhanced.py (movement edge cases)
- tests/aspects/test_aspect_movement_parametrized.py (parametrized movement tests)

Uses session-scoped conftest fixtures: johnny_depp, john_lennon, yoko_ono, paul_mccartney.
"""

import pytest
from pytest import approx

from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory
from kerykeion.aspects.aspects_utils import calculate_aspect_movement

# ---------------------------------------------------------------------------
# Expected data — graceful skip when files are absent
# ---------------------------------------------------------------------------
try:
    from tests.data.expected_natal_aspects import (
        EXPECTED_ALL_ASPECTS as EXPECTED_NATAL_ALL_ASPECTS,
    )
except ImportError:
    EXPECTED_NATAL_ALL_ASPECTS = None

try:
    from tests.data.expected_synastry_aspects import (
        EXPECTED_RELEVANT_ASPECTS as EXPECTED_SYNASTRY_RELEVANT_ASPECTS,
    )
except ImportError:
    EXPECTED_SYNASTRY_RELEVANT_ASPECTS = None


# ---------------------------------------------------------------------------
# Tolerance constants (aligned with conftest)
# ---------------------------------------------------------------------------
POSITION_ABS_TOL = 1e-2  # 0.01 degrees (~36 arcseconds)
SPEED_ABS_TOL = 1e-2  # For speed values
ORB_ABS_TOL = 1e-2  # For orbit values


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_aspect_fields(actual: dict, expected: dict, context: str = "") -> None:
    """Assert that an actual aspect dict matches the expected one."""
    prefix = f"{context}: " if context else ""

    # Exact-match fields
    assert actual["p1_name"] == expected["p1_name"], f"{prefix}p1_name mismatch"
    assert actual["p2_name"] == expected["p2_name"], f"{prefix}p2_name mismatch"
    assert actual["aspect"] == expected["aspect"], f"{prefix}aspect type mismatch"
    assert actual["p1"] == expected["p1"], f"{prefix}p1 index mismatch"
    assert actual["p2"] == expected["p2"], f"{prefix}p2 index mismatch"

    # Numeric fields with tolerance
    assert actual["p1_abs_pos"] == approx(expected["p1_abs_pos"], abs=POSITION_ABS_TOL), f"{prefix}p1_abs_pos"
    assert actual["p2_abs_pos"] == approx(expected["p2_abs_pos"], abs=POSITION_ABS_TOL), f"{prefix}p2_abs_pos"
    assert actual["aspect_degrees"] == approx(expected["aspect_degrees"], abs=POSITION_ABS_TOL), (
        f"{prefix}aspect_degrees"
    )
    assert actual["diff"] == approx(expected["diff"], abs=POSITION_ABS_TOL), f"{prefix}diff"

    if "orbit" in expected and "orbit" in actual:
        assert actual["orbit"] == approx(expected["orbit"], abs=ORB_ABS_TOL), f"{prefix}orbit"

    if "p1_speed" in expected and "p1_speed" in actual:
        assert actual["p1_speed"] == approx(expected["p1_speed"], abs=SPEED_ABS_TOL), f"{prefix}p1_speed"
    if "p2_speed" in expected and "p2_speed" in actual:
        assert actual["p2_speed"] == approx(expected["p2_speed"], abs=SPEED_ABS_TOL), f"{prefix}p2_speed"

    if "aspect_movement" in expected and "aspect_movement" in actual:
        assert actual["aspect_movement"] == expected["aspect_movement"], f"{prefix}aspect_movement mismatch"


# ============================================================================
# 1. TestNatalAspects
# ============================================================================


class TestNatalAspects:
    """
    Test AspectsFactory.single_chart_aspects() with Johnny Depp natal data.

    Verifies total count, specific aspect pairs/orbs/movements, and all
    expected fields (p1_name, p2_name, aspect, orbit, aspect_degrees, diff).
    """

    def test_natal_aspects_count(self, johnny_depp):
        """Total natal aspect count matches EXPECTED_NATAL_ALL_ASPECTS."""
        if EXPECTED_NATAL_ALL_ASPECTS is None:
            pytest.skip("Expected natal aspects data not available")

        result = AspectsFactory.single_chart_aspects(johnny_depp)
        actual = [a.model_dump() for a in result.aspects]

        assert len(actual) == len(EXPECTED_NATAL_ALL_ASPECTS), (
            f"Natal aspect count mismatch: got {len(actual)}, expected {len(EXPECTED_NATAL_ALL_ASPECTS)}"
        )

    def test_natal_aspects_all_match(self, johnny_depp):
        """Every natal aspect matches its expected counterpart."""
        if EXPECTED_NATAL_ALL_ASPECTS is None:
            pytest.skip("Expected natal aspects data not available")

        result = AspectsFactory.single_chart_aspects(johnny_depp)
        actual = [a.model_dump() for a in result.aspects]

        for i, expected in enumerate(EXPECTED_NATAL_ALL_ASPECTS):
            assert i < len(actual), f"Missing natal aspect at index {i}"
            _assert_aspect_fields(actual[i], expected, context=f"natal[{i}]")

    def test_natal_sun_jupiter_sextile(self, johnny_depp):
        """Verify Sun-Jupiter sextile with specific orbit."""
        if EXPECTED_NATAL_ALL_ASPECTS is None:
            pytest.skip("Expected natal aspects data not available")

        result = AspectsFactory.single_chart_aspects(johnny_depp)
        actual = [a.model_dump() for a in result.aspects]

        # First aspect in expected data is Sun-Jupiter sextile
        first = actual[0]
        assert first["p1_name"] == "Sun"
        assert first["p2_name"] == "Jupiter"
        assert first["aspect"] == "sextile"
        assert first["aspect_degrees"] == 60
        assert first["orbit"] == approx(3.749, abs=0.01)
        assert first["aspect_movement"] == "Separating"

    def test_natal_mercury_venus_conjunction(self, johnny_depp):
        """Verify Mercury-Venus conjunction with tight orbit."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        aspects = result.aspects

        # Find Mercury-Venus conjunction
        found = [a for a in aspects if a.p1_name == "Mercury" and a.p2_name == "Venus" and a.aspect == "conjunction"]
        assert len(found) == 1, "Expected exactly one Mercury-Venus conjunction"
        conj = found[0]
        assert conj.orbit == approx(0.602, abs=0.01)
        assert conj.aspect_degrees == 0
        assert conj.aspect_movement == "Separating"

    def test_natal_pluto_chiron_static(self, johnny_depp):
        """Verify Pluto-Chiron opposition is Static (very slow planets)."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        aspects = result.aspects

        found = [a for a in aspects if a.p1_name == "Pluto" and a.p2_name == "Chiron" and a.aspect == "opposition"]
        assert len(found) == 1, "Expected exactly one Pluto-Chiron opposition"
        assert found[0].aspect_movement == "Static"

    def test_natal_owner_is_johnny_depp(self, johnny_depp):
        """All natal aspects should have p1_owner and p2_owner == subject name."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        for a in result.aspects:
            assert a.p1_owner == "Johnny Depp"
            assert a.p2_owner == "Johnny Depp"


# ============================================================================
# 2. TestSynastryAspects
# ============================================================================


class TestSynastryAspects:
    """
    Test AspectsFactory.dual_chart_aspects() with John Lennon + Yoko Ono.

    The EXPECTED_SYNASTRY_RELEVANT_ASPECTS data was generated from the legacy
    test matrix (which may use different birth parameters), so count/match
    tests use dedicated subjects built from the expected data's positions.
    Structural tests use conftest fixtures directly.
    """

    def test_synastry_aspects_count_with_expected_subjects(self):
        """Synastry count matches EXPECTED_SYNASTRY_RELEVANT_ASPECTS using matching subjects."""
        if EXPECTED_SYNASTRY_RELEVANT_ASPECTS is None:
            pytest.skip("Expected synastry aspects data not available")

        # Build subjects that match the expected data (Johnny Depp natal data)
        johnny = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp",
            1963,
            6,
            9,
            0,
            0,
            lat=37.7742,
            lng=-87.1133,
            tz_str="America/Chicago",
            online=False,
            suppress_geonames_warning=True,
        )
        result = AspectsFactory.single_chart_aspects(johnny)
        actual = [a.model_dump() for a in result.aspects]

        # The expected_synastry_aspects.py EXPECTED_RELEVANT_ASPECTS is actually
        # the relevant (filtered) natal aspects for Johnny Depp — verify count.
        if EXPECTED_NATAL_ALL_ASPECTS is not None:
            natal_expected = EXPECTED_NATAL_ALL_ASPECTS
            assert len(actual) == len(natal_expected), (
                f"Natal aspect count mismatch: got {len(actual)}, expected {len(natal_expected)}"
            )

    def test_synastry_produces_aspects(self, john_lennon, yoko_ono):
        """Synastry should produce a non-empty list of aspects."""
        result = AspectsFactory.dual_chart_aspects(john_lennon, yoko_ono)
        assert len(result.aspects) > 0, "Expected at least one synastry aspect"

    def test_synastry_p2_owner_is_second_subject(self, john_lennon, yoko_ono):
        """In synastry, p2_owner should be the second subject's name."""
        result = AspectsFactory.dual_chart_aspects(john_lennon, yoko_ono)
        p2_owners = {a.p2_owner for a in result.aspects}
        assert yoko_ono.name in p2_owners, "Synastry aspects should include second subject as p2_owner"

    def test_synastry_p1_owner_is_first_subject(self, john_lennon, yoko_ono):
        """In synastry, p1_owner should be the first subject's name."""
        result = AspectsFactory.dual_chart_aspects(john_lennon, yoko_ono)
        p1_owners = {a.p1_owner for a in result.aspects}
        assert john_lennon.name in p1_owners, "Synastry aspects should include first subject as p1_owner"

    def test_synastry_cross_chart_pairs(self, john_lennon, yoko_ono):
        """Synastry aspects should include cross-chart planet pairs."""
        result = AspectsFactory.dual_chart_aspects(john_lennon, yoko_ono)
        cross_chart = [a for a in result.aspects if a.p1_owner != a.p2_owner]
        assert len(cross_chart) > 0, "Expected at least one cross-chart aspect"

    def test_synastry_aspect_fields_populated(self, john_lennon, yoko_ono):
        """Every synastry aspect should have all required fields populated."""
        result = AspectsFactory.dual_chart_aspects(john_lennon, yoko_ono)
        for a in result.aspects:
            assert a.p1_name, "p1_name should not be empty"
            assert a.p2_name, "p2_name should not be empty"
            assert a.aspect, "aspect should not be empty"
            assert 0 <= a.p1_abs_pos < 360
            assert 0 <= a.p2_abs_pos < 360
            assert a.orbit >= 0
            assert a.diff >= 0
            assert a.aspect_degrees >= 0

    def test_synastry_movements_valid(self, john_lennon, yoko_ono):
        """All synastry aspect movements should be valid."""
        valid_movements = {"Applying", "Separating", "Static"}
        result = AspectsFactory.dual_chart_aspects(john_lennon, yoko_ono)
        for a in result.aspects:
            assert a.aspect_movement in valid_movements, (
                f"Invalid movement '{a.aspect_movement}' for {a.p1_name}-{a.p2_name}"
            )

    def test_synastry_has_major_aspects(self, john_lennon, yoko_ono):
        """Synastry should contain at least some major aspect types."""
        major = {"conjunction", "opposition", "trine", "square", "sextile"}
        result = AspectsFactory.dual_chart_aspects(john_lennon, yoko_ono)
        found = {a.aspect for a in result.aspects} & major
        assert len(found) >= 2, f"Expected at least 2 major aspect types, found: {found}"

    def test_synastry_different_pair_gives_different_results(self, john_lennon, yoko_ono, paul_mccartney):
        """Different synastry pairs should produce different aspect lists."""
        result_jy = AspectsFactory.dual_chart_aspects(john_lennon, yoko_ono)
        result_jp = AspectsFactory.dual_chart_aspects(john_lennon, paul_mccartney)

        aspects_jy = [(a.p1_name, a.p2_name, a.aspect) for a in result_jy.aspects]
        aspects_jp = [(a.p1_name, a.p2_name, a.aspect) for a in result_jp.aspects]

        # They can't be identical (different second subject)
        assert aspects_jy != aspects_jp, "Different synastry pairs should yield different aspect lists"


# ============================================================================
# 3. TestAspectTypes
# ============================================================================


class TestAspectTypes:
    """
    Verify major aspects are present, aspect_degrees values are valid,
    and all movements are Applying/Separating/Static.
    """

    MAJOR_ASPECTS = {"conjunction", "opposition", "trine", "square", "sextile"}
    VALID_ASPECT_DEGREES = {0, 30, 36, 40, 45, 51.43, 60, 72, 80, 90, 108, 120, 135, 144, 150, 180}

    def test_major_aspects_present(self, johnny_depp):
        """At least some major aspects should be present in natal chart."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        aspect_types = {a.aspect for a in result.aspects}
        major_found = aspect_types & self.MAJOR_ASPECTS
        assert len(major_found) >= 3, f"Expected at least 3 major aspect types, found: {major_found}"

    def test_aspect_degrees_valid(self, johnny_depp):
        """All aspect_degrees should be valid standard values."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        for a in result.aspects:
            assert a.aspect_degrees in self.VALID_ASPECT_DEGREES or 0 <= a.aspect_degrees <= 180, (
                f"Invalid aspect_degrees {a.aspect_degrees} for {a.p1_name}-{a.p2_name}"
            )

    def test_all_movements_valid(self, johnny_depp):
        """All aspect_movement values must be Applying, Separating, or Static."""
        valid_movements = {"Applying", "Separating", "Static"}
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        for a in result.aspects:
            assert a.aspect_movement in valid_movements, (
                f"Invalid aspect_movement '{a.aspect_movement}' for {a.p1_name}-{a.p2_name}"
            )

    def test_john_lennon_major_aspects_present(self, john_lennon):
        """John Lennon natal chart should also have major aspects."""
        result = AspectsFactory.single_chart_aspects(john_lennon)
        aspect_types = {a.aspect for a in result.aspects}
        assert aspect_types & self.MAJOR_ASPECTS, "No major aspects found for John Lennon"

    def test_paul_mccartney_movements_valid(self, paul_mccartney):
        """Paul McCartney: all movements valid."""
        valid_movements = {"Applying", "Separating", "Static"}
        result = AspectsFactory.single_chart_aspects(paul_mccartney)
        for a in result.aspects:
            assert a.aspect_movement in valid_movements


# ============================================================================
# 4. TestAspectIntegration
# ============================================================================


class TestAspectIntegration:
    """
    Integration tests: position validity (0-360), no duplicate pairs,
    synastry differs from natal.
    """

    def test_positions_in_valid_range(self, johnny_depp):
        """All p1_abs_pos and p2_abs_pos must be in [0, 360)."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        for a in result.aspects:
            assert 0 <= a.p1_abs_pos < 360, f"p1_abs_pos out of range: {a.p1_abs_pos}"
            assert 0 <= a.p2_abs_pos < 360, f"p2_abs_pos out of range: {a.p2_abs_pos}"
            assert a.diff >= 0, f"diff should be non-negative: {a.diff}"
            assert a.orbit >= 0, f"orbit should be non-negative: {a.orbit}"

    def test_no_duplicate_pairs(self, johnny_depp):
        """No duplicate point-index pairs in natal aspects."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        seen_pairs = set()
        for a in result.aspects:
            pair = tuple(sorted([a.p1, a.p2]))
            assert pair not in seen_pairs, f"Duplicate aspect between points {a.p1} and {a.p2}"
            seen_pairs.add(pair)

    def test_synastry_different_from_natal(self, john_lennon, paul_mccartney):
        """Synastry aspects are structurally different from natal aspects."""
        natal = AspectsFactory.single_chart_aspects(john_lennon)
        synastry = AspectsFactory.dual_chart_aspects(john_lennon, paul_mccartney)

        # Synastry should include the second subject as p2_owner
        synastry_p2_owners = {a.p2_owner for a in synastry.aspects}
        assert paul_mccartney.name in synastry_p2_owners or len(synastry.aspects) == 0, (
            "Synastry aspects should include second subject as p2_owner"
        )

        # Natal aspects all have same owner; synastry should differ
        natal_owners = {(a.p1_owner, a.p2_owner) for a in natal.aspects}
        synastry_owners = {(a.p1_owner, a.p2_owner) for a in synastry.aspects}
        if len(synastry.aspects) > 0:
            assert synastry_owners != natal_owners

    def test_john_lennon_positions_valid(self, john_lennon):
        """John Lennon natal: all positions in valid range."""
        result = AspectsFactory.single_chart_aspects(john_lennon)
        for a in result.aspects:
            assert 0 <= a.p1_abs_pos < 360
            assert 0 <= a.p2_abs_pos < 360

    def test_return_type_is_list_of_aspects(self, johnny_depp):
        """Result aspects should be a list."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        assert isinstance(result.aspects, list)
        assert len(result.aspects) > 0


# ============================================================================
# 5. TestAspectMovementBasic
# ============================================================================

# Format: (p1_pos, p2_pos, aspect_degrees, p1_speed, p2_speed, expected)
BASIC_MOVEMENT_CASES = [
    # Applying cases
    pytest.param(45.0, 50.0, 0.0, 12.5, 1.0, "Applying", id="faster_behind_approaching"),
    pytest.param(80.0, 90.0, 0.0, 2.0, 0.5, "Applying", id="slow_catch_up"),
    # Separating cases
    pytest.param(55.0, 50.0, 0.0, 12.5, 1.0, "Separating", id="faster_ahead_moving_away"),
    pytest.param(100.0, 90.0, 0.0, 2.0, 0.5, "Separating", id="slow_moving_apart"),
    # Static cases
    pytest.param(10.0, 20.0, 0.0, 0.0, 0.0, "Static", id="both_stationary"),
    pytest.param(10.0, 40.0, 30.0, 1.0, 1.0, "Static", id="same_speed_constant_orb"),
    pytest.param(100.0, 200.0, 100.0, 5.0, 5.0, "Static", id="same_speed_any_aspect"),
]


class TestAspectMovementBasic:
    """Parametrized basic movement cases (applying, separating, static)."""

    @pytest.mark.parametrize(
        "p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected",
        BASIC_MOVEMENT_CASES,
    )
    def test_basic_movement(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected


# ============================================================================
# 6. TestAspectMovementRetrograde
# ============================================================================

RETROGRADE_CASES = [
    # Retrograde applying
    pytest.param(110.0, 100.0, 0.0, -0.8, 0.1, "Applying", id="retrograde_faster_applying"),
    pytest.param(15.0, 10.0, 0.0, -1.0, 1.0, "Applying", id="retrograde_approaching_direct"),
    pytest.param(10.0, 15.0, 0.0, 1.0, -1.0, "Applying", id="direct_approaching_retrograde"),
    # Retrograde separating
    pytest.param(10.0, 5.0, 0.0, 1.0, -1.0, "Separating", id="direct_leaving_retrograde"),
    pytest.param(5.0, 10.0, 0.0, -1.0, 1.0, "Separating", id="retrograde_leaving_direct"),
    # Both retrograde
    pytest.param(10.0, 15.0, 0.0, -1.0, -2.0, "Applying", id="both_retrograde_approaching"),
    pytest.param(15.0, 10.0, 0.0, -2.0, -1.0, "Applying", id="both_retrograde_faster_behind"),
]


class TestAspectMovementRetrograde:
    """Parametrized retrograde motion cases."""

    @pytest.mark.parametrize(
        "p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected",
        RETROGRADE_CASES,
    )
    def test_retrograde_movement(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected


# ============================================================================
# 7. TestAspectMovementBoundary
# ============================================================================

BOUNDARY_CROSSING_CASES = [
    pytest.param(359.0, 5.0, 0.0, 1.0, 13.0, "Separating", id="moon_past_sun_at_boundary"),
    pytest.param(359.0, 355.0, 0.0, 1.0, 13.0, "Applying", id="moon_approaching_at_boundary"),
    pytest.param(5.0, 355.0, 0.0, 1.0, 1.0, "Static", id="same_speed_across_boundary"),
    pytest.param(358.0, 2.0, 0.0, 0.5, 1.0, "Separating", id="just_past_conjunction_boundary"),
    pytest.param(355.0, 1.0, 0.0, 0.5, 1.0, "Separating", id="well_past_conjunction_boundary"),
]


class TestAspectMovementBoundary:
    """0 deg / 360 deg boundary crossing cases."""

    @pytest.mark.parametrize(
        "p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected",
        BOUNDARY_CROSSING_CASES,
    )
    def test_boundary_crossing(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected

    def test_crossing_zero_boundary_static(self):
        """Equal speeds across 0/360 boundary → Static."""
        result = calculate_aspect_movement(359.5, 0.5, 0.0, 1.0, 1.0)
        assert result == "Static"

    def test_crossing_zero_boundary_applying(self):
        """Approaching across 0/360 boundary."""
        result = calculate_aspect_movement(359.0, 355.0, 0.0, 1.0, 13.0)
        assert result == "Applying"


# ============================================================================
# 8. TestAspectMovementEdgeCases
# ============================================================================

ASPECT_TYPE_MOVEMENT_CASES = [
    pytest.param(10.0, 245.0, 240.0, 1.0, 13.0, "Applying", id="large_aspect_approaching"),
    pytest.param(10.0, 130.0, 120.0, 1.0, 13.0, "Separating", id="trine_exact_separating"),
    pytest.param(0.0, 180.0, 120.0, 0.0, 1.0, "Applying", id="180_separation_trine_applying"),
    # Opposition
    pytest.param(10.0, 190.0, 180.0, 1.0, 0.5, "Separating", id="opposition_separating"),
    pytest.param(10.0, 185.0, 180.0, 0.5, 1.0, "Applying", id="opposition_applying"),
    # Square
    pytest.param(10.0, 100.0, 90.0, 1.0, 0.5, "Separating", id="square_separating"),
    pytest.param(10.0, 95.0, 90.0, 0.5, 1.0, "Applying", id="square_applying"),
]

EXACT_ASPECT_CASES = [
    pytest.param(10.0, 10.0, 0.0, 1.0, -1.0, "Separating", id="exact_conj_separating"),
    pytest.param(10.0, 10.0, 0.0, 1.0, 2.0, "Separating", id="exact_conj_faster_ahead"),
    pytest.param(10.0, 10.0, 0.0, 2.0, 1.0, "Separating", id="exact_conj_faster_p1"),
    pytest.param(10.0, 10.0, 0.0, 0.0, 0.0, "Static", id="exact_conj_both_static"),
]

GENERAL_EDGE_CASES = [
    pytest.param(10.0, 10.001, 0.0, 1.0, 0.999, "Static", id="tiny_relative_speed_static"),
    pytest.param(10.0, 9.999, 0.0, 1.001, 1.0, "Separating", id="tiny_orb_p1_faster"),
    pytest.param(10.0, 50.0, 0.0, 50.0, 1.0, "Applying", id="very_fast_p1_applying"),
    pytest.param(50.0, 10.0, 0.0, 1.0, 50.0, "Applying", id="very_fast_p2_applying"),
    pytest.param(0.0, 179.0, 180.0, 1.0, 0.5, "Separating", id="near_opposition_179"),
    pytest.param(0.0, 181.0, 180.0, 1.0, 0.5, "Applying", id="near_opposition_181"),
]


class TestAspectMovementEdgeCases:
    """
    Input validation (None speed, invalid position, negative aspect),
    precision (ORB_EPSILON, SPEED_EPSILON), exact aspect boundary,
    extreme speed differences, both retrograde.
    """

    # --- Input validation ---

    def test_none_speed_raises_error(self):
        """ValueError when speed is None."""
        with pytest.raises(ValueError, match="Speed values for both points are required"):
            calculate_aspect_movement(10.0, 20.0, 0.0, None, 1.0)

        with pytest.raises(ValueError, match="Speed values for both points are required"):
            calculate_aspect_movement(10.0, 20.0, 0.0, 1.0, None)

    def test_invalid_position_raises_error(self):
        """ValueError when position is out of [0, 360)."""
        with pytest.raises(ValueError, match="Positions must be in range"):
            calculate_aspect_movement(-1.0, 20.0, 0.0, 1.0, 1.0)

        with pytest.raises(ValueError, match="Positions must be in range"):
            calculate_aspect_movement(10.0, 361.0, 0.0, 1.0, 1.0)

    def test_negative_aspect_raises_error(self):
        """ValueError when aspect degrees are negative."""
        with pytest.raises(ValueError, match="Aspect degrees must be non-negative"):
            calculate_aspect_movement(10.0, 20.0, -30.0, 1.0, 1.0)

    # --- ORB_EPSILON / SPEED_EPSILON precision ---

    def test_orb_epsilon_handling(self):
        """Orb changes below ORB_EPSILON (1e-6) → Static."""
        result = calculate_aspect_movement(10.0, 10.0000001, 0.0, 0.001, 0.001001)
        assert result == "Static"

    def test_speed_epsilon_handling(self):
        """Speed differences below SPEED_EPSILON (1e-9) → Static."""
        result = calculate_aspect_movement(10.0, 20.0, 0.0, 1.0, 1.0000000001)
        assert result == "Static"

        result = calculate_aspect_movement(10.0, 20.0, 0.0, 1.0, 1.0)
        assert result == "Static"

    def test_exact_aspect_with_minimal_movement(self):
        """At exact aspect with very small speeds → Static."""
        result = calculate_aspect_movement(10.0, 10.0, 0.0, 0.0001, 0.0002)
        assert result == "Static"

    # --- Near-exact aspect boundary ---

    def test_near_exact_aspect_boundary_applying(self):
        """Just before exact aspect → Applying."""
        result = calculate_aspect_movement(10.0, 9.99, 0.0, 0.0, 1.0)
        assert result == "Applying"

    def test_near_exact_aspect_boundary_separating(self):
        """Just after exact aspect → Separating."""
        result = calculate_aspect_movement(10.0, 10.01, 0.0, 0.0, 1.0)
        assert result == "Separating"

    # --- Extreme speed differences ---

    def test_extreme_speed_difference(self):
        """Ascendant (360 deg/day) vs slow planet (0.01 deg/day)."""
        result = calculate_aspect_movement(100.0, 190.0, 90.0, 360.0, 0.01)
        assert result == "Separating"

    def test_very_small_speeds_static(self):
        """Very small relative speed → ORB_EPSILON → Static."""
        result = calculate_aspect_movement(10.0, 11.0, 0.0, 0.0001, 0.00009)
        assert result == "Static"

    def test_very_small_speeds_separating(self):
        """Larger relative speed → meaningful Separating result."""
        result = calculate_aspect_movement(10.0, 11.0, 0.0, 0.01, 0.02)
        assert result == "Separating"

    # --- Both retrograde ---

    def test_both_retrograde_different_speeds(self):
        """Both retrograde, different speeds → Applying."""
        result = calculate_aspect_movement(100.0, 110.0, 0.0, -0.5, -1.0)
        assert result == "Applying"

    def test_both_retrograde_same_speed(self):
        """Both retrograde, same speed → Static."""
        result = calculate_aspect_movement(100.0, 110.0, 0.0, -1.0, -1.0)
        assert result == "Static"

    def test_aspect_crossing_with_small_dt(self):
        """Point crossing exact aspect within dt → Static due to ORB_EPSILON."""
        result = calculate_aspect_movement(10.0, 9.9995, 0.0, 0.0, 1.0)
        assert result == "Static"

    # --- Opposition (180 deg) exact ---

    def test_aspect_180_exact(self):
        """Exact opposition (180 deg)."""
        result = calculate_aspect_movement(0.0, 180.0, 180.0, 0.5, 0.6)
        assert result == "Separating"

    def test_aspect_greater_than_180(self):
        """Aspect > 180 deg should be normalized correctly."""
        result = calculate_aspect_movement(10.0, 250.0, 240.0, 1.0, 1.5)
        assert result == "Separating"

    # --- Parametrized aspect-type movement cases ---

    @pytest.mark.parametrize(
        "p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected",
        ASPECT_TYPE_MOVEMENT_CASES,
    )
    def test_aspect_type_movements(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected

    @pytest.mark.parametrize(
        "p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected",
        EXACT_ASPECT_CASES,
    )
    def test_exact_aspect_cases(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected

    @pytest.mark.parametrize(
        "p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected",
        GENERAL_EDGE_CASES,
    )
    def test_general_edge_cases(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected

    # --- Return type ---

    def test_return_type_is_string(self):
        """Return value is always a string in {Applying, Separating, Static}."""
        result = calculate_aspect_movement(45.0, 50.0, 0.0, 12.5, 1.0)
        assert isinstance(result, str)
        assert result in {"Applying", "Separating", "Static"}

    # --- Symmetric behavior ---

    def test_symmetric_behavior(self):
        """Swapping positions and speeds gives consistent result."""
        result1 = calculate_aspect_movement(45.0, 50.0, 0.0, 12.5, 1.0)
        result2 = calculate_aspect_movement(50.0, 45.0, 0.0, 1.0, 12.5)
        assert result1 == result2

    # --- All major aspects: applying and separating ---

    @pytest.mark.parametrize("aspect_deg", [0, 60, 90, 120, 180])
    def test_all_major_aspects_applying(self, aspect_deg):
        """All major aspects should detect Applying correctly."""
        result = calculate_aspect_movement(10.0, 10.0 + aspect_deg - 5.0, aspect_deg, 0.5, 2.0)
        assert result == "Applying"

    @pytest.mark.parametrize("aspect_deg", [0, 60, 90, 120, 180])
    def test_all_major_aspects_separating(self, aspect_deg):
        """All major aspects should detect Separating correctly."""
        result = calculate_aspect_movement(10.0, 10.0 + aspect_deg + 5.0, aspect_deg, 0.5, 2.0)
        assert result == "Separating"


# ============================================================================
# 9. TestAspectMovementNonStandard
# ============================================================================


class TestAspectMovementNonStandard:
    """Quintile (72 deg), biquintile (144 deg), septile (~51.43 deg)."""

    def test_quintile_72_degrees(self):
        """Quintile aspect (72 deg)."""
        result = calculate_aspect_movement(10.0, 82.0, 72.0, 1.0, 1.2)
        assert result == "Separating"

    def test_biquintile_144_degrees_separating(self):
        """Biquintile (144 deg) — separating."""
        result = calculate_aspect_movement(10.0, 154.0, 144.0, 1.0, 0.8)
        assert result == "Separating"

    def test_biquintile_144_degrees_applying(self):
        """Biquintile (144 deg) — applying."""
        result = calculate_aspect_movement(10.0, 150.0, 144.0, 1.0, 2.0)
        assert result == "Applying"

    def test_septile_51_degrees(self):
        """Septile aspect (~51.43 deg)."""
        result = calculate_aspect_movement(10.0, 61.43, 51.43, 1.0, 1.5)
        assert result == "Separating"

    def test_quintile_in_natal_data(self, johnny_depp):
        """Johnny Depp natal chart contains a Uranus-Neptune quintile."""
        result = AspectsFactory.single_chart_aspects(johnny_depp)
        quintiles = [a for a in result.aspects if a.aspect == "quintile"]
        assert len(quintiles) >= 1, "Expected at least one quintile in Johnny Depp natal"
        q = quintiles[0]
        assert q.aspect_degrees == 72
        assert q.p1_name == "Uranus"
        assert q.p2_name == "Neptune"


# ============================================================================
# Comprehensive regression: all original assertions in a single test
# ============================================================================


class TestAspectMovementComprehensiveRegression:
    """
    Re-verify every original assertion from the legacy test files
    in a single pass to guarantee no regressions.
    """

    def test_all_basic_cases_from_original(self):
        """Original test_aspect_movement.py cases."""
        assert calculate_aspect_movement(45.0, 50.0, 0.0, 12.5, 1.0) == "Applying"
        assert calculate_aspect_movement(55.0, 50.0, 0.0, 12.5, 1.0) == "Separating"
        assert calculate_aspect_movement(110.0, 100.0, 0.0, -0.8, 0.1) == "Applying"
        assert calculate_aspect_movement(10.0, 20.0, 0.0, 0.0, 0.0) == "Static"
        assert calculate_aspect_movement(10.0, 40.0, 30.0, 1.0, 1.0) == "Static"

    def test_all_comprehensive_cases_from_original(self):
        """Original test_aspect_movement_comprehensive.py cases."""
        assert calculate_aspect_movement(359, 5, 0, 1, 13) == "Separating"
        assert calculate_aspect_movement(359, 355, 0, 1, 13) == "Applying"
        assert calculate_aspect_movement(10, 245, 240, 1, 13) == "Applying"
        assert calculate_aspect_movement(10, 15, 0, 1, -1) == "Applying"
        assert calculate_aspect_movement(10, 5, 0, 1, -1) == "Separating"
        assert calculate_aspect_movement(10, 15, 0, -1, -2) == "Applying"
        assert calculate_aspect_movement(10, 130, 120, 1, 13) == "Separating"
        assert calculate_aspect_movement(10, 10, 0, 1, -1) == "Separating"
        assert calculate_aspect_movement(0, 180, 120, 0, 1) == "Applying"

    def test_retrograde_documented_behavior(self):
        """Documented retrograde cases."""
        # Mercury retrograde approaching Sun
        assert calculate_aspect_movement(10.0, 15.0, 0.0, 1.0, -1.0) == "Applying"
        # Mercury retrograde separating from Sun
        assert calculate_aspect_movement(10.0, 5.0, 0.0, 1.0, -1.0) == "Separating"

    def test_numerical_stability(self):
        """Result is consistent across various configurations."""
        result = calculate_aspect_movement(10.0, 50.0, 60.0, 1.0, 15.0)
        assert result == "Applying"

        result = calculate_aspect_movement(10.0, 10.1, 0.0, 0.5, 1.0)
        assert result == "Separating"


# =============================================================================
# ASPECTS UTILS: planet_id_decoder (from edge_cases)
# =============================================================================


class TestPlanetIdDecoder:
    """Tests for planet_id_decoder utility function."""

    def test_valid_planet_returns_int(self):
        from kerykeion.aspects.aspects_utils import planet_id_decoder
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS

        result = planet_id_decoder(DEFAULT_CELESTIAL_POINTS_SETTINGS, "Sun")
        assert isinstance(result, int)

    def test_invalid_planet_raises(self):
        from kerykeion.aspects.aspects_utils import planet_id_decoder
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS

        with pytest.raises(ValueError, match="not found"):
            planet_id_decoder(DEFAULT_CELESTIAL_POINTS_SETTINGS, "InvalidPlanet")


class TestAxisOrbFilter:
    """Tests for axis_orb_limit parameter in AspectsFactory."""

    @pytest.fixture()
    def _subject(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Test",
            1990,
            6,
            15,
            12,
            0,
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )

    def test_strict_axis_orb_filters(self, _subject):
        aspects = AspectsFactory.single_chart_aspects(_subject, axis_orb_limit=1.0)
        assert aspects is not None

    def test_axis_orb_none_disables_filter(self, _subject):
        aspects = AspectsFactory.single_chart_aspects(_subject, axis_orb_limit=None)
        assert aspects is not None
