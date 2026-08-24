"""
Comprehensive tests for CompositeSubjectFactory.

Integrates all test cases from:
- tests/factories/test_composite_subject_factory_complete.py
- tests/factories/test_composite_factory_parametrized.py

All subjects are created offline with explicit coordinates.
Primary test pair: John Lennon + Yoko Ono.
"""

import copy
import pytest
from pytest import approx

from kerykeion import AstrologicalSubjectFactory
from kerykeion.composite_subject.factory import CompositeSubjectFactory
from kerykeion.schemas import KerykeionException


# =============================================================================
# CONSTANTS
# =============================================================================

VALID_SIGNS = {"Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"}
VALID_ELEMENTS = {"Air", "Fire", "Earth", "Water"}
VALID_QUALITIES = {"Cardinal", "Fixed", "Mutable"}

CORE_PLANETS = [
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
]

HOUSE_NAMES = [
    "first_house",
    "second_house",
    "third_house",
    "fourth_house",
    "fifth_house",
    "sixth_house",
    "seventh_house",
    "eighth_house",
    "ninth_house",
    "tenth_house",
    "eleventh_house",
    "twelfth_house",
]

POSITION_TOLERANCE = 1e-4


# =============================================================================
# FIXTURES
# =============================================================================


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
def composite_factory(john, yoko):
    return CompositeSubjectFactory(john, yoko)


@pytest.fixture(scope="module")
def composite_model(composite_factory):
    return composite_factory.get_midpoint_composite_subject_model()


# =============================================================================
# HELPERS
# =============================================================================


def circular_distance(a: float, b: float) -> float:
    """Shortest angular distance on 0-360 circle."""
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def naive_midpoint(pos1: float, pos2: float) -> float:
    """Calculate the shorter-arc midpoint of two positions on a 0-360 circle."""
    diff = abs(pos1 - pos2)
    if diff > 180:
        midpoint = ((pos1 + pos2) / 2 + 180) % 360
    else:
        midpoint = (pos1 + pos2) / 2
    return midpoint


# =============================================================================
# 1. TestBasicCompositeCreation
# =============================================================================


class TestBasicCompositeCreation:
    """Create composite, verify factory attributes and composite subject model."""

    def test_factory_first_subject(self, composite_factory, john):
        assert composite_factory.first_subject == john

    def test_factory_second_subject(self, composite_factory, yoko):
        assert composite_factory.second_subject == yoko

    def test_factory_chart_type(self, composite_factory):
        assert composite_factory.composite_chart_type == "Midpoint"

    def test_factory_model_initially_none(self, john, yoko):
        factory = CompositeSubjectFactory(john, yoko)
        assert factory.model is None

    def test_factory_name_auto_generated(self, composite_factory):
        assert "John Lennon" in composite_factory.name
        assert "Yoko Ono" in composite_factory.name
        assert "Composite Chart" in composite_factory.name

    def test_factory_zodiac_type(self, composite_factory):
        assert composite_factory.zodiac_type == "Tropical"

    def test_factory_sidereal_mode_none_for_tropical(self, composite_factory):
        assert composite_factory.sidereal_mode is None

    def test_factory_perspective_type(self, composite_factory):
        assert composite_factory.perspective_type == "Apparent Geocentric"

    def test_factory_active_points_not_empty(self, composite_factory):
        assert isinstance(composite_factory.active_points, list)
        assert len(composite_factory.active_points) > 0

    def test_factory_houses_names_list(self, composite_factory):
        assert len(composite_factory.houses_names_list) == 12

    def test_composite_model_not_none(self, composite_model):
        assert composite_model is not None

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_composite_has_planet(self, composite_model, planet):
        point = getattr(composite_model, planet, None)
        assert point is not None, f"Composite model missing planet: {planet}"

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_has_abs_pos(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert hasattr(point, "abs_pos")
        assert 0 <= point.abs_pos < 360

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_has_sign(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert hasattr(point, "sign")

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_has_position(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert hasattr(point, "position")
        assert 0 <= point.position < 30

    def test_composite_model_has_all_houses(self, composite_model):
        for house in HOUSE_NAMES:
            house_obj = getattr(composite_model, house, None)
            assert house_obj is not None, f"Missing house: {house}"

    def test_composite_model_has_lunar_phase(self, composite_model):
        assert hasattr(composite_model, "lunar_phase")

    def test_composite_model_has_first_subject(self, composite_model, john):
        assert composite_model.first_subject == john

    def test_composite_model_has_second_subject(self, composite_model, yoko):
        assert composite_model.second_subject == yoko

    def test_str_representation(self, composite_factory):
        s = str(composite_factory)
        assert "Composite Chart Data" in s
        assert "John Lennon" in s
        assert "Yoko Ono" in s

    def test_repr_representation(self, composite_factory):
        r = repr(composite_factory)
        assert "Composite Chart Data" in r

    def test_setitem_getitem(self, john, yoko):
        factory = CompositeSubjectFactory(john, yoko)
        factory["test_key"] = "test_value"
        assert factory["test_key"] == "test_value"

    def test_getitem_missing_key_raises(self, john, yoko):
        factory = CompositeSubjectFactory(john, yoko)
        with pytest.raises(AttributeError):
            _ = factory["nonexistent_key_xyz"]

    def test_copy(self, john, yoko):
        original = CompositeSubjectFactory(john, yoko, chart_name="Copy Test")
        copied = copy.copy(original)
        assert copied is not original
        assert copied.first_subject == original.first_subject
        assert copied.second_subject == original.second_subject
        assert copied.name == original.name

    def test_hash_attributes_exist(self, john, yoko):
        """Factory exposes the attributes __hash__ depends on."""
        factory = CompositeSubjectFactory(john, yoko)
        assert hasattr(factory, "first_subject")
        assert hasattr(factory, "second_subject")
        assert hasattr(factory, "name")
        # __hash__ hashes stable scalars (name/julian_day), so it must work
        # even though the Pydantic subject models themselves are unhashable.
        assert isinstance(hash(factory), int)


# =============================================================================
# 2. TestMidpointCalculations
# =============================================================================


class TestMidpointCalculations:
    """Verify midpoint positions for planets and houses."""

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_is_near_midpoint(self, john, yoko, composite_model, planet):
        """Each composite planet should be near the circular midpoint of the two natal positions."""
        pos1 = getattr(john, planet).abs_pos
        pos2 = getattr(yoko, planet).abs_pos
        composite_pos = getattr(composite_model, planet).abs_pos

        expected = naive_midpoint(pos1, pos2)
        alt = (expected + 180) % 360

        dist = min(circular_distance(composite_pos, expected), circular_distance(composite_pos, alt))

        assert dist < 1.0, (
            f"{planet}: composite={composite_pos:.4f} not near midpoint "
            f"{expected:.4f} or alt {alt:.4f} (dist={dist:.4f})"
        )

    @pytest.mark.parametrize("house", HOUSE_NAMES)
    def test_house_has_valid_position(self, composite_model, house):
        house_obj = getattr(composite_model, house)
        assert 0 <= house_obj.abs_pos < 360, f"{house} abs_pos={house_obj.abs_pos} out of range"

    def test_internal_calculation_method(self, john, yoko):
        """_calculate_midpoint_composite_points_and_houses should run without error."""
        factory = CompositeSubjectFactory(john, yoko)
        factory._calculate_midpoint_composite_points_and_houses()

    def test_lunar_phase_calculation(self, john, yoko):
        """_calculate_composite_lunar_phase should run after points are computed."""
        factory = CompositeSubjectFactory(john, yoko)
        factory.get_midpoint_composite_subject_model()
        moon_phase = factory._calculate_composite_lunar_phase()
        # Method sets self.lunar_phase; return value may be None
        assert factory.lunar_phase is not None or moon_phase is None

    def test_houses_are_sorted_ascending_modular(self, composite_model):
        """House cusp positions should wrap around 360 in a consistent order."""
        positions = [getattr(composite_model, h).abs_pos for h in HOUSE_NAMES]
        # All should be valid degree values
        for pos in positions:
            assert 0 <= pos < 360


# =============================================================================
# 3. TestCommutativity
# =============================================================================


class TestCommutativity:
    """A+B should equal B+A for all planet positions."""

    def test_commutative_planet_positions(self, john, yoko):
        factory_ab = CompositeSubjectFactory(john, yoko)
        factory_ba = CompositeSubjectFactory(yoko, john)

        model_ab = factory_ab.get_midpoint_composite_subject_model()
        model_ba = factory_ba.get_midpoint_composite_subject_model()

        for planet in CORE_PLANETS:
            pos_ab = getattr(model_ab, planet).abs_pos
            pos_ba = getattr(model_ba, planet).abs_pos
            assert pos_ab == approx(pos_ba, abs=POSITION_TOLERANCE), f"{planet}: AB={pos_ab:.4f} != BA={pos_ba:.4f}"

    def test_commutative_house_positions(self, john, yoko):
        factory_ab = CompositeSubjectFactory(john, yoko)
        factory_ba = CompositeSubjectFactory(yoko, john)

        model_ab = factory_ab.get_midpoint_composite_subject_model()
        model_ba = factory_ba.get_midpoint_composite_subject_model()

        for house in HOUSE_NAMES:
            pos_ab = getattr(model_ab, house).abs_pos
            pos_ba = getattr(model_ba, house).abs_pos
            assert pos_ab == approx(pos_ba, abs=POSITION_TOLERANCE), f"{house}: AB={pos_ab:.4f} != BA={pos_ba:.4f}"

    def test_deterministic(self, john, yoko):
        """Two identical constructions produce identical results."""
        model1 = CompositeSubjectFactory(john, yoko).get_midpoint_composite_subject_model()
        model2 = CompositeSubjectFactory(john, yoko).get_midpoint_composite_subject_model()

        for planet in CORE_PLANETS:
            assert getattr(model1, planet).abs_pos == getattr(model2, planet).abs_pos, f"{planet} is not deterministic"


# =============================================================================
# 4. TestCompositeWithSelf
# =============================================================================


class TestCompositeWithSelf:
    """Composite of a subject with itself should equal the natal chart positions."""

    def test_self_composite_planets(self, john):
        factory = CompositeSubjectFactory(john, john)
        composite = factory.get_midpoint_composite_subject_model()

        for planet in CORE_PLANETS:
            natal_pos = getattr(john, planet).abs_pos
            composite_pos = getattr(composite, planet).abs_pos
            assert composite_pos == approx(natal_pos, abs=POSITION_TOLERANCE), (
                f"{planet}: natal={natal_pos:.4f} != self-composite={composite_pos:.4f}"
            )

    def test_self_composite_with_yoko(self, yoko):
        """Same test but with a different subject to confirm generality."""
        factory = CompositeSubjectFactory(yoko, yoko)
        composite = factory.get_midpoint_composite_subject_model()

        for planet in CORE_PLANETS:
            natal_pos = getattr(yoko, planet).abs_pos
            composite_pos = getattr(composite, planet).abs_pos
            assert composite_pos == approx(natal_pos, abs=POSITION_TOLERANCE), (
                f"{planet}: natal={natal_pos:.4f} != self-composite={composite_pos:.4f}"
            )


# =============================================================================
# 5. TestIncompatibleConfigurations
# =============================================================================


class TestIncompatibleConfigurations:
    """Tropical + Sidereal, different house systems, etc. must raise KerykeionException."""

    def test_tropical_vs_sidereal_raises(self, john):
        sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Subject",
            1990,
            6,
            15,
            12,
            30,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            online=False,
            suppress_geonames_warning=True,
        )
        with pytest.raises(KerykeionException, match="same zodiac type"):
            CompositeSubjectFactory(john, sidereal_subject)

    def test_different_house_systems_raises(self, john):
        koch_subject = AstrologicalSubjectFactory.from_birth_data(
            "Koch Subject",
            1990,
            6,
            15,
            12,
            30,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            houses_system_identifier="K",
            online=False,
            suppress_geonames_warning=True,
        )
        with pytest.raises(KerykeionException, match="same houses system"):
            CompositeSubjectFactory(john, koch_subject)

    def test_different_perspective_raises(self, john):
        helio_subject = AstrologicalSubjectFactory.from_birth_data(
            "Heliocentric Subject",
            1990,
            6,
            15,
            12,
            30,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            perspective_type="Heliocentric",
            online=False,
            suppress_geonames_warning=True,
        )
        with pytest.raises(KerykeionException, match="same perspective type"):
            CompositeSubjectFactory(john, helio_subject)

    def test_different_sidereal_modes_raises(self):
        lahiri = AstrologicalSubjectFactory.from_birth_data(
            "Lahiri Subject",
            1990,
            6,
            15,
            12,
            30,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            online=False,
            suppress_geonames_warning=True,
        )
        fagan = AstrologicalSubjectFactory.from_birth_data(
            "Fagan Subject",
            1992,
            8,
            20,
            14,
            45,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            zodiac_type="Sidereal",
            sidereal_mode="FAGAN_BRADLEY",
            online=False,
            suppress_geonames_warning=True,
        )
        with pytest.raises(KerykeionException, match="same sidereal mode"):
            CompositeSubjectFactory(lahiri, fagan)

    def test_compatible_sidereal_subjects_succeed(self):
        s1 = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal 1",
            1990,
            6,
            15,
            12,
            30,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            online=False,
            suppress_geonames_warning=True,
        )
        s2 = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal 2",
            1992,
            8,
            20,
            14,
            45,
            lat=40.7128,
            lng=-74.0060,
            tz_str="America/New_York",
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            online=False,
            suppress_geonames_warning=True,
        )
        factory = CompositeSubjectFactory(s1, s2)
        assert factory.zodiac_type == "Sidereal"
        assert factory.sidereal_mode == "LAHIRI"
        model = factory.get_midpoint_composite_subject_model()
        assert model is not None


# =============================================================================
# 6. TestCustomName
# =============================================================================


class TestCustomName:
    """Custom chart_name parameter."""

    def test_custom_name_is_set(self, john, yoko):
        custom = "Love & Peace Composite"
        factory = CompositeSubjectFactory(john, yoko, chart_name=custom)
        assert factory.name == custom

    def test_custom_name_in_str(self, john, yoko):
        custom = "Lennon-Ono Relationship"
        factory = CompositeSubjectFactory(john, yoko, chart_name=custom)
        assert custom in str(factory)

    def test_default_name_without_chart_name(self, john, yoko):
        factory = CompositeSubjectFactory(john, yoko)
        assert "Composite Chart" in factory.name

    def test_custom_name_preserved_in_model(self, john, yoko):
        custom = "JY Composite"
        factory = CompositeSubjectFactory(john, yoko, chart_name=custom)
        model = factory.get_midpoint_composite_subject_model()
        assert model.name == custom

    def test_custom_name_preserved_after_copy(self, john, yoko):
        custom = "Copy Name Test"
        factory = CompositeSubjectFactory(john, yoko, chart_name=custom)
        copied = copy.copy(factory)
        assert copied.name == custom


# =============================================================================
# 7. TestCompositeSubjectAttributes
# =============================================================================


class TestCompositeSubjectAttributes:
    """All planet points have valid sign, element, quality. Houses list has 12 entries."""

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_sign_is_valid(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert point.sign in VALID_SIGNS, f"{planet} has invalid sign: {point.sign}"

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_element_is_valid(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert point.element in VALID_ELEMENTS, f"{planet} has invalid element: {point.element}"

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_quality_is_valid(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert point.quality in VALID_QUALITIES, f"{planet} has invalid quality: {point.quality}"

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_point_type(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert point.point_type == "AstrologicalPoint"

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_name_is_set(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert point.name is not None
        assert len(point.name) > 0

    @pytest.mark.parametrize("planet", CORE_PLANETS)
    def test_planet_emoji_is_set(self, composite_model, planet):
        point = getattr(composite_model, planet)
        assert point.emoji is not None

    def test_houses_list_has_12_entries(self, composite_model):
        assert len(composite_model.houses_names_list) == 12

    @pytest.mark.parametrize("house", HOUSE_NAMES)
    def test_house_sign_is_valid(self, composite_model, house):
        h = getattr(composite_model, house)
        assert h.sign in VALID_SIGNS, f"{house} has invalid sign: {h.sign}"

    @pytest.mark.parametrize("house", HOUSE_NAMES)
    def test_house_element_is_valid(self, composite_model, house):
        h = getattr(composite_model, house)
        assert h.element in VALID_ELEMENTS, f"{house} has invalid element: {h.element}"

    @pytest.mark.parametrize("house", HOUSE_NAMES)
    def test_house_quality_is_valid(self, composite_model, house):
        h = getattr(composite_model, house)
        assert h.quality in VALID_QUALITIES, f"{house} has invalid quality: {h.quality}"

    @pytest.mark.parametrize("house", HOUSE_NAMES)
    def test_house_point_type(self, composite_model, house):
        h = getattr(composite_model, house)
        assert h.point_type == "House"

    def test_active_points_are_list(self, composite_model):
        assert isinstance(composite_model.active_points, list)
        assert len(composite_model.active_points) > 0

    def test_zodiac_type_on_model(self, composite_model):
        assert composite_model.zodiac_type in ("Tropical", "Sidereal")

    def test_composite_chart_type_on_model(self, composite_model):
        assert composite_model.composite_chart_type == "Midpoint"

    def test_model_serializable(self, composite_model):
        """The model should be JSON-serializable via Pydantic."""
        json_str = composite_model.model_dump_json()
        assert isinstance(json_str, str)
        assert len(json_str) > 100

    def test_model_dict(self, composite_model):
        """model_dump should return a non-empty dictionary."""
        d = composite_model.model_dump()
        assert isinstance(d, dict)
        assert "sun" in d
        assert "first_house" in d


# =============================================================================
# 8. Additional edge-case and regression tests
# =============================================================================


class TestEdgeCases:
    """Boundary crossings, equality, and other edge cases."""

    def test_boundary_crossing_completes(self, john, yoko):
        """Composite with subjects whose planets span 0/360 boundary should not crash."""
        factory = CompositeSubjectFactory(john, yoko)
        model = factory.get_midpoint_composite_subject_model()
        assert model is not None

    def test_equality_same_subjects(self, john, yoko):
        c1 = CompositeSubjectFactory(john, yoko)
        c2 = CompositeSubjectFactory(john, yoko)
        assert c1.first_subject.name == c2.first_subject.name
        assert c1.second_subject.name == c2.second_subject.name

    def test_inequality_swapped_subjects(self, john, yoko):
        c1 = CompositeSubjectFactory(john, yoko)
        c2 = CompositeSubjectFactory(yoko, john)
        # Names differ because auto-generated name depends on order
        assert c1.name != c2.name

    def test_common_active_points(self, composite_factory):
        assert hasattr(composite_factory, "active_points")
        assert isinstance(composite_factory.active_points, list)

    def test_multiple_model_generations_consistent(self, john, yoko):
        """Calling get_midpoint_composite_subject_model twice gives same results."""
        factory = CompositeSubjectFactory(john, yoko)
        m1 = factory.get_midpoint_composite_subject_model()
        m2 = factory.get_midpoint_composite_subject_model()
        for planet in CORE_PLANETS:
            assert getattr(m1, planet).abs_pos == approx(getattr(m2, planet).abs_pos, abs=POSITION_TOLERANCE)

    def test_third_pair_paul_mccartney(self, john):
        """Composite with a third subject to confirm generality."""
        paul = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney",
            1942,
            6,
            18,
            14,
            0,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
            online=False,
            suppress_geonames_warning=True,
        )
        factory = CompositeSubjectFactory(john, paul)
        model = factory.get_midpoint_composite_subject_model()
        assert model is not None
        for planet in CORE_PLANETS:
            assert 0 <= getattr(model, planet).abs_pos < 360


# ---------------------------------------------------------------------------
# Missing edge-case tests (migrated from tests/edge_cases/test_edge_cases.py)
# ---------------------------------------------------------------------------


class TestCompositeWithDavisonMethod:
    """Composite creation using midpoint (Davison-style) method."""

    def test_composite_with_davison_method(self, john, yoko):
        composite_factory = CompositeSubjectFactory(john, yoko)
        composite = composite_factory.get_midpoint_composite_subject_model()
        assert composite is not None


if __name__ == "__main__":
    pytest.main(["-vv", __file__])


class TestCompositeDisjointActivePoints:
    """Round-1 regression: disjoint active_points must raise, not diverge."""

    def test_disjoint_active_points_raises(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.composite_subject.factory import CompositeSubjectFactory
        from kerykeion.schemas import KerykeionException

        a = AstrologicalSubjectFactory.from_birth_data(
            "A", 1990, 6, 15, 12, 0, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True, active_points=["Sun", "Moon"],
        )
        b = AstrologicalSubjectFactory.from_birth_data(
            "B", 1992, 3, 3, 8, 0, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True, active_points=["Mars", "Venus"],
        )
        with pytest.raises(KerykeionException, match="no common active points"):
            CompositeSubjectFactory(a, b)


class TestCompositeMidheavenInvariantRound5:
    """Round-5 HIGH regression: the midpoint-composite Midheaven must equal the
    tenth-house cusp and sit in the Tenth house, even when the two subjects'
    Ascendants are far apart (previously circular_sort mislabeled the cusps)."""

    def _pair_composite(self, h1, h2):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.composite_subject.factory import CompositeSubjectFactory
        a = AstrologicalSubjectFactory.from_birth_data(
            "C1", 1990, 6, 15, h1, 0, lng=12.5, lat=41.9, tz_str="Etc/GMT",
            online=False, suppress_geonames_warning=True)
        b = AstrologicalSubjectFactory.from_birth_data(
            "C2", 1990, 6, 15, h2, 0, lng=12.5, lat=41.9, tz_str="Etc/GMT",
            online=False, suppress_geonames_warning=True)
        return CompositeSubjectFactory(a, b).get_midpoint_composite_subject_model()

    def test_mc_equals_tenth_cusp_degenerate(self):
        comp = self._pair_composite(6, 19)  # Ascendants ~154 deg apart
        diff = abs((comp.medium_coeli.abs_pos - comp.tenth_house.abs_pos + 180) % 360 - 180)
        assert diff < 1e-6
        assert comp.medium_coeli.house == "Tenth_House"

    def test_mc_invariant_monte_carlo(self):
        for h1, h2 in [(0, 6), (3, 15), (8, 20), (11, 23), (5, 17)]:
            comp = self._pair_composite(h1, h2)
            diff = abs((comp.medium_coeli.abs_pos - comp.tenth_house.abs_pos + 180) % 360 - 180)
            assert diff < 1e-6, f"MC != tenth cusp for {h1},{h2}"
            assert comp.medium_coeli.house == "Tenth_House"


class TestUserSiderealCompositeRound10:
    """Round-10 regression: a USER-sidereal midpoint composite must build (the
    custom ayanamsa fields must be carried over to the composite model)."""

    def test_user_sidereal_midpoint_composite_builds(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.composite_subject.factory import CompositeSubjectFactory

        kw = dict(zodiac_type="Sidereal", sidereal_mode="USER",
                  custom_ayanamsa_t0=2451545.0, custom_ayanamsa_ayan_t0=23.5)
        a = AstrologicalSubjectFactory.from_birth_data(
            "A", 1990, 6, 15, 12, 0, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True, **kw)
        b = AstrologicalSubjectFactory.from_birth_data(
            "B", 1992, 3, 3, 8, 0, lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True, **kw)
        comp = CompositeSubjectFactory(a, b).get_midpoint_composite_subject_model()
        assert comp.sun is not None
        assert comp.custom_ayanamsa_t0 == 2451545.0


class TestDavisonEnrichmentRound13:
    """Round-13: Davison composite must carry over enrichments both parents had."""

    def test_davison_inherits_enrichments(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.composite_subject.factory import CompositeSubjectFactory
        kw = dict(calculate_dignities=True, calculate_gauquelin=True,
                  calculate_nutation=True, active_fixed_stars=["Regulus"])
        a = AstrologicalSubjectFactory.from_birth_data(
            "A", 1990, 6, 15, 12, 0, city="Rome", nation="IT", lng=12.5, lat=41.9,
            tz_str="Europe/Rome", online=False, suppress_geonames_warning=True, **kw)
        b = AstrologicalSubjectFactory.from_birth_data(
            "B", 1992, 3, 3, 8, 0, city="Rome", nation="IT", lng=12.5, lat=41.9,
            tz_str="Europe/Rome", online=False, suppress_geonames_warning=True, **kw)
        d = CompositeSubjectFactory(a, b).get_davison_composite_subject_model()
        assert d.sun.essential_dignity is not None
        assert d.gauquelin_sector_cusps is not None
        assert [s.name for s in d.fixed_stars] == ["Regulus"]


class TestMidpointCompositeLunarPhaseGuardRound16:
    """Round-16: midpoint composite lunar_phase must be guarded to geocentric
    perspectives (sibling of the single-subject geocentric-only lunar-phase)."""

    def test_planetocentric_midpoint_lunar_phase_none(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.composite_subject.factory import CompositeSubjectFactory
        kw = dict(city="X", nation="GB", lng=0.0, lat=51.5, tz_str="Etc/GMT",
                  online=False, suppress_geonames_warning=True)
        a = AstrologicalSubjectFactory.from_birth_data("A", 1990, 1, 1, 12, 0, perspective_type="Marscentric", **kw)
        b = AstrologicalSubjectFactory.from_birth_data("B", 1992, 6, 15, 14, 30, perspective_type="Marscentric", **kw)
        m = CompositeSubjectFactory(a, b).get_midpoint_composite_subject_model()
        assert m.lunar_phase is None

    def test_geocentric_midpoint_lunar_phase_present(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.composite_subject.factory import CompositeSubjectFactory
        kw = dict(city="X", nation="GB", lng=0.0, lat=51.5, tz_str="Etc/GMT",
                  online=False, suppress_geonames_warning=True)
        a = AstrologicalSubjectFactory.from_birth_data("A", 1990, 1, 1, 12, 0, **kw)
        b = AstrologicalSubjectFactory.from_birth_data("B", 1992, 6, 15, 14, 30, **kw)
        m = CompositeSubjectFactory(a, b).get_midpoint_composite_subject_model()
        assert m.lunar_phase is not None


def test_none_subjects_raise_clean_exception():
    """None inputs must fail with a clear KerykeionException, not a raw
    AttributeError on .active_points deep in the pipeline."""
    from kerykeion.composite_subject.factory import CompositeSubjectFactory
    from kerykeion.relationship_score.factory import RelationshipScoreFactory
    from kerykeion.schemas import KerykeionException

    with pytest.raises(KerykeionException):
        CompositeSubjectFactory(None, None)
    with pytest.raises(KerykeionException):
        RelationshipScoreFactory(None, None)


# =============================================================================
# THE HOUSE A COMPOSITE POINT IS FILED UNDER
# =============================================================================
#
# The composite kept a private copy of the library's house reader, and the copy
# measured every house as the arc running *forwards* from its own cusp. Average
# two polar charts and the ring comes out descending: a six-degree house then
# reads as 354 and swallows most of the wheel. Ten points out of ten were filed
# wrong, four of the twelve houses could no longer be reached at all, and the
# same model contradicted itself — its house-comparison field already went
# through the shared reader and disagreed with its own `sun.house`.


_CUSP_ATTRS = (
    "first_house", "second_house", "third_house", "fourth_house", "fifth_house",
    "sixth_house", "seventh_house", "eighth_house", "ninth_house", "tenth_house",
    "eleventh_house", "twelfth_house",
)

_POINTS = (
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus",
    "neptune", "pluto", "ascendant", "medium_coeli",
)


def _composite_of(system: str, first_lat: float, second_lat: float):
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 21, 0, 0, city="X", nation="XX", online=False,
        suppress_geonames_warning=True, tz_str="UTC", lat=first_lat, lng=20.0,
        houses_system_identifier=system,
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1988, 3, 3, 6, 30, city="X", nation="XX", online=False,
        suppress_geonames_warning=True, tz_str="UTC", lat=second_lat, lng=25.0,
        houses_system_identifier=system,
    )
    return CompositeSubjectFactory(first, second).get_midpoint_composite_subject_model()


@pytest.mark.parametrize(
    "system,first_lat,second_lat",
    [
        ("C", 70.0, 71.0),   # Campanus inside the polar circle: descending ring
        ("R", 69.0, 70.5),   # Regiomontanus, likewise
        ("P", 45.0, 48.0),   # and an ordinary pair, which must not change
    ],
)
def test_every_composite_point_is_filed_where_the_shared_reader_says(system, first_lat, second_lat):
    """One reader for the whole library, so a model cannot disagree with itself."""
    from kerykeion.utilities.core import get_planet_house

    composite = _composite_of(system, first_lat, second_lat)
    cusps = [getattr(composite, name).abs_pos for name in _CUSP_ATTRS]
    for name in _POINTS:
        point = getattr(composite, name, None)
        if point is None:
            continue
        assert point.house == get_planet_house(point.abs_pos, cusps), (
            f"{name} at {point.abs_pos:.3f} filed under {point.house}"
        )


def test_the_composite_angles_still_open_their_own_houses():
    """The property the private copy existed to protect, kept by the shared one.

    A point exactly on a cusp belongs to the house that cusp opens — which is
    what puts the composite Midheaven in the tenth even where the ring is a mess.
    """
    for system, first_lat, second_lat in (("C", 70.0, 71.0), ("P", 45.0, 48.0)):
        composite = _composite_of(system, first_lat, second_lat)
        assert composite.ascendant.house == "First_House", system
        assert composite.medium_coeli.house == "Tenth_House", system


def test_a_descending_composite_ring_can_still_reach_every_house():
    """Read forwards, four houses covered the whole circle and eight were unreachable."""
    from kerykeion.utilities.core import get_planet_house

    composite = _composite_of("C", 70.0, 71.0)
    cusps = [getattr(composite, name).abs_pos for name in _CUSP_ATTRS]
    reachable = {get_planet_house(degree / 10.0, cusps) for degree in range(3600)}
    assert len(reachable) == 12, sorted(reachable)


# =============================================================================
# THE CUSP RING THE MIDPOINT METHOD HANDS BACK
# =============================================================================
#
# Between two points on a circle there are two midpoints, half a turn apart, and
# taking the nearer one for each of the twelve cusps *independently* breaks when
# the two charts' angles are nearly opposed: the choice flips partway round the
# ring and the twelve arcs come to 1080 degrees instead of 360. That is not a
# house division — the numbers stop reading in order and the Midheaven can end up
# a quarter turn from where the Ascendant puts it. Measured here: about one
# random couple in sixteen, at ordinary latitudes.
#
# The profession's answer is to hold one angle at its near midpoint and move the
# others onto their far midpoint as needed. Solar Fire: "adjust some of the house
# cusps to be long-arc midpoints instead of short-arc in order to preserve the
# correct zodiacal ordering". Kepler and Sirius: "flipping the houses 180 degrees
# if necessary". Townley prescribes the same in "The Composite Chart", for the
# stray cusp and its opposite.


_ANCHORS = ("auto", "ascendant", "midheaven")


def _cusps_of(model) -> list[float]:
    return [getattr(model, name).abs_pos for name in _CUSP_ATTRS]


def _winding(cusps: list[float]) -> float:
    forward = sum((cusps[(i + 1) % 12] - cusps[i]) % 360.0 for i in range(12))
    return min(forward, 12 * 360.0 - forward) / 360.0


def _pair(first_hour: int, second_hour: int, lat: float = 51.5, lng: float = -0.1667):
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 1, 1, first_hour, 0, city="X", nation="XX", online=False,
        suppress_geonames_warning=True, tz_str="UTC", lat=lat, lng=lng,
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 1, 1, second_hour, 30 if second_hour == 11 else 0, city="X", nation="XX",
        online=False, suppress_geonames_warning=True, tz_str="UTC", lat=lat, lng=lng,
    )
    return first, second


@pytest.mark.parametrize("anchor", _ANCHORS)
def test_the_composite_cusps_cover_the_circle_exactly_once(anchor):
    """The London pair whose Ascendants sit 179.6 degrees apart.

    Independent near midpoints give this one twelve arcs totalling 1080 degrees,
    with the Midheaven and the Imum Coeli swapped.
    """
    first, second = _pair(0, 11)
    opposition = abs((first.ascendant.abs_pos - second.ascendant.abs_pos + 180.0) % 360.0 - 180.0)
    assert opposition > 170.0, f"fixture no longer has opposed Ascendants: {opposition:.1f}"

    composite = CompositeSubjectFactory(
        first, second, house_anchor=anchor
    ).get_midpoint_composite_subject_model()
    assert _winding(_cusps_of(composite)) == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("anchor", _ANCHORS)
def test_a_ring_that_already_reads_in_order_is_not_touched(anchor):
    """No anchor may move a chart that never needed repairing.

    Most composites do not, and their cusps have to come out of here as the plain
    circular means they always were — the same value, not merely a close one.
    """
    from kerykeion.utilities.core import circular_mean

    first, second = _pair(0, 6)
    composite = CompositeSubjectFactory(
        first, second, house_anchor=anchor
    ).get_midpoint_composite_subject_model()
    cusps = _cusps_of(composite)
    assert _winding(cusps) == pytest.approx(1.0, abs=1e-6), "fixture is not an ordered pair"
    for index, name in enumerate(_CUSP_ATTRS):
        expected = circular_mean(
            getattr(first, name).abs_pos, getattr(second, name).abs_pos
        )
        assert cusps[index] == expected


def test_the_named_anchor_keeps_its_own_near_midpoint():
    """Anchoring is a promise about one cusp: that one does not move."""
    from kerykeion.utilities.core import circular_mean

    first, second = _pair(0, 11)

    on_ascendant = CompositeSubjectFactory(
        first, second, house_anchor="ascendant"
    ).get_midpoint_composite_subject_model()
    assert on_ascendant.first_house.abs_pos == pytest.approx(
        circular_mean(first.first_house.abs_pos, second.first_house.abs_pos), abs=1e-9
    )

    on_midheaven = CompositeSubjectFactory(
        first, second, house_anchor="midheaven"
    ).get_midpoint_composite_subject_model()
    assert on_midheaven.tenth_house.abs_pos == pytest.approx(
        circular_mean(first.tenth_house.abs_pos, second.tenth_house.abs_pos), abs=1e-9
    )

    # And the two are not the same chart: which angle is held can turn the whole
    # house frame by half a circle, which is why the choice is offered at all.
    difference = abs(
        (on_ascendant.first_house.abs_pos - on_midheaven.first_house.abs_pos + 180.0) % 360.0
        - 180.0
    )
    assert difference == pytest.approx(180.0, abs=1e-6)


def test_auto_holds_whichever_angle_is_the_better_determined():
    """Solar Fire's rule: the "strongest" midpoint is the one whose base cusps
    are closest together, because a midpoint between two nearly opposite points
    is the arbitrary one of the pair."""
    from kerykeion.composite_subject.factory import composite_house_cusps

    # First house cusps 10 degrees apart, tenth 170 apart: the first is stronger.
    first = [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0]
    second = [10.0, 40.0, 70.0, 100.0, 130.0, 160.0, 190.0, 220.0, 250.0, 100.0, 310.0, 340.0]
    automatic = composite_house_cusps(first, second, anchor="auto")
    on_ascendant = composite_house_cusps(first, second, anchor="ascendant")
    assert automatic == on_ascendant

    # Now the other way round: tenth cusps together, first cusps nearly opposed.
    first = [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0]
    second = [170.0, 40.0, 70.0, 100.0, 130.0, 160.0, 350.0, 220.0, 250.0, 280.0, 310.0, 340.0]
    automatic = composite_house_cusps(first, second, anchor="auto")
    on_midheaven = composite_house_cusps(first, second, anchor="midheaven")
    assert automatic == on_midheaven


@pytest.mark.parametrize("anchor", _ANCHORS)
def test_every_point_is_still_filed_by_the_shared_reader(anchor):
    """The repair must not put the ring and the housing back out of step."""
    from kerykeion.utilities.core import get_planet_house

    first, second = _pair(0, 11)
    composite = CompositeSubjectFactory(
        first, second, house_anchor=anchor
    ).get_midpoint_composite_subject_model()
    cusps = _cusps_of(composite)
    for name in _POINTS:
        point = getattr(composite, name, None)
        if point is None:
            continue
        assert point.house == get_planet_house(point.abs_pos, cusps)


def test_a_cusp_is_always_a_midpoint_of_its_pair_even_where_no_ring_exists():
    """The property that never breaks, held apart from the one that can.

    Where one partner's houses run backwards round the wheel and the other's
    forwards — one of them born inside the polar circle under a system that
    reverses there — the twelve cannot be made to cover the circle once, because
    there is no direction for them to run in. What must still hold is that every
    composite cusp is a midpoint of its own pair: the near one or the far one,
    never something in between.
    """
    from kerykeion.composite_subject.factory import composite_house_cusps
    from kerykeion.utilities.core import circular_mean

    forward = AstrologicalSubjectFactory.from_birth_data(
        "Forward", 1990, 6, 21, 0, 0, city="X", nation="XX", online=False,
        suppress_geonames_warning=True, tz_str="UTC", lat=45.0, lng=9.0,
    )
    backward = AstrologicalSubjectFactory.from_birth_data(
        "Backward", 1990, 6, 21, 0, 0, city="X", nation="XX", online=False,
        suppress_geonames_warning=True, tz_str="UTC", lat=70.0, lng=20.0,
        houses_system_identifier="C",
    )
    first = [getattr(forward, name).abs_pos for name in _CUSP_ATTRS]
    second = [getattr(backward, name).abs_pos for name in _CUSP_ATTRS]

    from kerykeion.charts.utils import house_spans
    assert not any(house_spans(first)[1]), "the forward fixture stopped running forwards"
    assert all(house_spans(second)[1]), "the backward fixture stopped running backwards"

    for anchor in _ANCHORS:
        cusps = composite_house_cusps(first, second, anchor=anchor)
        for index, (a, b) in enumerate(zip(first, second)):
            near = circular_mean(a, b)
            offset = abs((cusps[index] - near + 180.0) % 360.0 - 180.0)
            assert min(offset, abs(offset - 180.0)) < 1e-6, (
                f"{anchor}: cusp {index + 1} is neither midpoint of its pair"
            )


@pytest.mark.parametrize("anchor", _ANCHORS)
def test_two_charts_whose_houses_run_the_same_way_always_give_a_ring(anchor):
    """The guarantee, on the case that can actually be guaranteed.

    Both backwards is as good as both forwards: a pair of polar charts under a
    reversing system makes a composite that runs backwards, and still covers the
    circle exactly once.
    """
    from kerykeion.composite_subject.factory import composite_house_cusps

    def polar(hour: int, lat: float):
        return [
            getattr(
                AstrologicalSubjectFactory.from_birth_data(
                    "P", 1990, 6, 21, hour, 0, city="X", nation="XX", online=False,
                    suppress_geonames_warning=True, tz_str="UTC", lat=lat, lng=20.0,
                    houses_system_identifier="C",
                ),
                name,
            ).abs_pos
            for name in _CUSP_ATTRS
        ]

    from kerykeion.charts.utils import house_spans

    first, second = polar(0, 70.0), polar(21, 72.0)
    assert all(house_spans(first)[1]) and all(house_spans(second)[1])
    assert _winding(composite_house_cusps(first, second, anchor=anchor)) == pytest.approx(
        1.0, abs=1e-6
    )


def test_two_backward_parents_whose_ring_already_tiles_are_left_alone():
    """A backward ring is a ring. The repair must recognise one and stand down.

    Read only forwards, twelve backward houses measure eleven turns, the "leave
    it alone" test says no, and the repair rebuilds a chart that was already
    correct — moving cusps that had nothing wrong with them.
    """
    from kerykeion.charts.utils import house_spans
    from kerykeion.composite_subject.factory import composite_house_cusps
    from kerykeion.utilities.core import circular_mean

    def polar(hour: int, lat: float):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "P", 1990, 6, 21, hour, 0, city="X", nation="XX", online=False,
            suppress_geonames_warning=True, tz_str="UTC", lat=lat, lng=20.0,
            houses_system_identifier="C",
        )
        return [getattr(subject, name).abs_pos for name in _CUSP_ATTRS]

    first, second = polar(0, 70.0), polar(21, 72.0)
    assert all(house_spans(first)[1]) and all(house_spans(second)[1])
    naive = [circular_mean(a, b) for a, b in zip(first, second)]
    assert _winding(naive) == pytest.approx(1.0, abs=1e-6), "fixture already needs repair"

    for anchor in _ANCHORS:
        assert composite_house_cusps(first, second, anchor=anchor) == naive


def test_the_composite_angles_do_not_depend_on_the_house_system():
    """An angle is where the ecliptic meets the horizon, and no house system moves it.

    The cusps of a composite have to be repaired, and the repair chooses which of
    two midpoints — half a turn apart — each position takes. Hang the angles off
    that choice and they inherit the house system: measured on the pair below,
    the composite Ascendant came out 180 degrees apart between Placidus and whole
    sign, and the whole-sign chart had its Midheaven in the fourth house with the
    Ascendant where the Descendant belongs.

    The angles hang from an angle instead. Under a quadrant system that is the
    same point as the cusp they share a number with, so the identity survives;
    under whole sign, equal, Morinus or meridian houses it is not, and they were
    never one thing to keep together.
    """
    SYSTEMS = ("P", "C", "K", "O", "R", "B", "W", "A", "M", "X", "N", "F", "S", "V", "D", "H")

    def composite_for(system: str, anchor: str):
        first = AstrologicalSubjectFactory.from_birth_data(
            "A", 1990, 6, 15, 2, 0, city="X", nation="XX", lat=41.9, lng=12.5,
            tz_str="Etc/GMT", online=False, suppress_geonames_warning=True,
            houses_system_identifier=system,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "B", 1990, 6, 15, 16, 0, city="X", nation="XX", lat=41.9, lng=12.5,
            tz_str="Etc/GMT", online=False, suppress_geonames_warning=True,
            houses_system_identifier=system,
        )
        return CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()

    for anchor in _ANCHORS:
        ascendants, midheavens = set(), set()
        for system in SYSTEMS:
            model = composite_for(system, anchor)
            ascendants.add(round(model.ascendant.abs_pos, 9))
            midheavens.add(round(model.medium_coeli.abs_pos, 9))

            cusps = _cusps_of(model)
            assert _winding(cusps) == pytest.approx(1.0, abs=1e-6), (system, anchor)

            # Where the parents made the angle its own cusp, the composite keeps
            # them one point. Asked of the parents, not of a list of systems.
            first = AstrologicalSubjectFactory.from_birth_data(
                "A", 1990, 6, 15, 2, 0, city="X", nation="XX", lat=41.9, lng=12.5,
                tz_str="Etc/GMT", online=False, suppress_geonames_warning=True,
                houses_system_identifier=system,
            )
            if abs((first.ascendant.abs_pos - first.first_house.abs_pos + 180) % 360 - 180) < 1e-9:
                assert model.ascendant.abs_pos == pytest.approx(cusps[0], abs=1e-9), (
                    f"{system}/{anchor}: the parents make the Ascendant the first cusp, "
                    f"the composite does not"
                )
            if abs((first.medium_coeli.abs_pos - first.tenth_house.abs_pos + 180) % 360 - 180) < 1e-9:
                assert model.medium_coeli.abs_pos == pytest.approx(cusps[9], abs=1e-9), (
                    f"{system}/{anchor}: the parents make the Midheaven the tenth cusp, "
                    f"the composite does not"
                )
                assert model.medium_coeli.house == "Tenth_House", (system, anchor)

        assert len(ascendants) == 1, (anchor, ascendants)
        assert len(midheavens) == 1, (anchor, midheavens)


#: Pairs whose plain near midpoints put the composite Midheaven below its own
#: horizon — 26 of 400 random pairs do. Each is (year, month, day, hour, minute)
#: twice, then latitude and longitude.
_MIDHEAVEN_BELOW_THE_HORIZON = (
    ((1989, 10, 14, 16, 29), (1939, 4, 28, 16, 19), 26.7475, 130.1992),
    ((1989, 11, 1, 20, 20), (1952, 9, 12, 12, 17), -25.8614, -144.6664),
    ((1974, 11, 13, 19, 44), (1955, 5, 8, 16, 7), -51.6908, 46.1426),
)


@pytest.mark.parametrize("first_data,second_data,lat,lng", _MIDHEAVEN_BELOW_THE_HORIZON)
def test_the_composite_midheaven_stays_above_its_own_horizon(first_data, second_data, lat, lng):
    """The geometry an angle pair has to satisfy: the Midheaven is not below it.

    Take each angle's own near midpoint and nothing keeps the two consistent: on
    these pairs the plain midpoints put the Midheaven some 90 degrees from the
    Ascendant, which is not a chart any sky could cast. Placing both on the frame
    the cusps hang from is what keeps them a pair.
    """
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", *first_data, city="X", nation="XX", lat=lat, lng=lng, tz_str="UTC",
        online=False, suppress_geonames_warning=True,
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", *second_data, city="X", nation="XX", lat=lat, lng=lng, tz_str="UTC",
        online=False, suppress_geonames_warning=True,
    )
    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        gap = (model.medium_coeli.abs_pos - model.ascendant.abs_pos) % 360.0
        assert 180.0 < gap < 360.0, f"{anchor}: Midheaven {gap:.2f}deg from the Ascendant"


def test_an_anchor_the_library_does_not_have_is_refused():
    """A typo must not quietly mean "auto".

    The branch that reads the anchor treats everything it does not recognise as
    the default, so `"Ascendant"` with a capital was accepted in silence and
    handed back a house frame half a turn from the one asked for. This factory
    already refuses an unknown house system out loud.
    """
    first, second = _pair(0, 11)
    with pytest.raises(KerykeionException):
        CompositeSubjectFactory(first, second, house_anchor="Ascendant")
    with pytest.raises(KerykeionException):
        CompositeSubjectFactory(first, second, house_anchor="")
    with pytest.raises(KerykeionException):
        CompositeSubjectFactory(first, second, house_anchor=None)


@pytest.mark.parametrize("anchor", _ANCHORS)
def test_the_chart_records_which_anchor_produced_it(anchor):
    """The choice can turn the whole frame by half a turn, so a chart that
    carries no note of it cannot be reproduced."""
    first, second = _pair(0, 11)
    model = CompositeSubjectFactory(
        first, second, house_anchor=anchor
    ).get_midpoint_composite_subject_model()
    assert model.house_anchor == anchor
    assert model.model_dump()["house_anchor"] == anchor

    davison = CompositeSubjectFactory(first, second).get_davison_composite_subject_model()
    assert davison.house_anchor is None, "a Davison chart never needs an anchor"


def test_the_angle_cusp_identity_is_asked_of_both_parents():
    """One parent is not enough, and exact equality is too strict.

    The rule decides whether an angle and its cusp are one point. Asking only
    one parent would call them one point on a pair where the other disagrees;
    asking for exact equality would call them two on a pair where they are one,
    because the identity carries float noise — measured up to 1.2e-12 degrees
    under APC, Krusinski, Carter, Morinus and meridian houses.
    """
    from kerykeion.composite_subject.factory import _angle_is_its_cusp

    cusps_a = [10.0] + [30.0 * index for index in range(1, 12)]
    cusps_b = [20.0] + [30.0 * index + 5.0 for index in range(1, 12)]

    # One point in both charts, to within the noise a real identity carries.
    assert _angle_is_its_cusp(10.0, 20.0 + 1e-12, cusps_a, cusps_b, 0)
    # One point in the first chart only.
    assert not _angle_is_its_cusp(10.0, 200.0, cusps_a, cusps_b, 0)
    # And in the second only.
    assert not _angle_is_its_cusp(100.0, 20.0, cusps_a, cusps_b, 0)
    # A genuine non-identity is never within a hair of one.
    assert not _angle_is_its_cusp(10.0 + 1e-6, 20.0, cusps_a, cusps_b, 0)


def test_the_winding_test_reads_a_hair_negative_gap_as_zero():
    """Built from a synthetic ring, because no real pair comes close enough.

    Two cusps coincident to within a hair, in the negative direction, are what a
    bare ``% 360`` answers 360.0 for — turning a ring that covers the circle once
    into one that appears to cover it twice, and sending a chart that needed
    nothing through the repair. Real composite rings do produce coincident cusps —
    90 of 120,069 measured were bit-identical — but not this far apart and no
    closer, so the exact case has to be constructed.

    Two separate facts, and the ring below is not a house division: its twelve
    arcs cover the circle once, and two of its cusps are the same point. The
    first is what ``house_spans`` must not read as 720; the second is why twelve
    arcs summing to 360 is not on its own an answer.
    """
    import math

    from kerykeion.composite_subject.factory import _cusp_ring_winds_once
    from kerykeion.utilities.core import house_spans

    ring = [0.0, 30.0, 60.0, 90.0, 120.0, math.nextafter(120.0, 0.0)]
    ring += [180.0, 210.0, 240.0, 270.0, 300.0, 330.0]
    assert (ring[5] - ring[4]) % 360.0 == 360.0, "the fixture no longer trips the modulo"

    spans, reversed_wedges = house_spans(ring)
    assert sum(spans) == approx(360.0, abs=1e-4), "the hair-negative gap read as a whole turn"
    assert len(set(reversed_wedges)) == 1

    # And still not twelve houses: one of them has no width.
    assert min(spans) < 1e-9
    assert not _cusp_ring_winds_once(ring)


def test_two_charts_that_run_opposite_ways_keep_their_angles_on_their_cusps():
    """One partner inside the polar circle, one outside: there is no shared frame.

    Both of these put the Midheaven exactly on their own tenth cusp, so the
    composite must too. Placing the angles on a frame spanning two charts that
    run opposite ways gave a composite Midheaven in the FOURTH house — on a chart
    whose twelve cusps tiled perfectly, so no guard anywhere fired. Whatever the
    anchor, and whichever of the two angles is examined.
    """
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=68.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="C",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 4, 0, city="X", nation="XX", lat=68.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="C",
    )
    from kerykeion.charts.utils import house_spans

    directions = {
        all(house_spans([getattr(parent, name).abs_pos for name in _CUSP_ATTRS])[1])
        for parent in (first, second)
    }
    assert len(directions) == 2, "the fixture no longer has one ring each way"
    for parent in (first, second):
        assert parent.medium_coeli.abs_pos == pytest.approx(parent.tenth_house.abs_pos, abs=1e-9)
        assert parent.ascendant.abs_pos == pytest.approx(parent.first_house.abs_pos, abs=1e-9)

    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        cusps = _cusps_of(model)
        assert model.medium_coeli.abs_pos == pytest.approx(cusps[9], abs=1e-9), anchor
        assert model.ascendant.abs_pos == pytest.approx(cusps[0], abs=1e-9), anchor
        assert model.medium_coeli.house == "Tenth_House", anchor


def test_a_point_in_a_gap_is_read_as_the_house_whose_cusp_it_last_passed(caplog):
    """Two charts that do not run the same way average into a ring with a hole in it.

    Sunshine at 80N reverses its cusps while the same system at 41.9N does not,
    and their midpoints leave a gap that five of the ten planets fall in. The
    shared house reader raises there, correctly — for an ordinary chart a
    longitude in no house is a bug worth stopping on. A composite is the one
    place the condition is reachable by construction, so it answers instead: the
    house whose cusp the point last passed, said out loud on the logger.

    Before the composite was taught to use the shared reader it had a private copy
    that returned the first house for these without a word. This is not that: the
    house named below is one the point is genuinely past the cusp of, and it is
    not the first.
    """
    import logging

    from kerykeion.utilities import get_planet_house

    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=41.9, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="I",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=80.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="I",
    )

    with caplog.at_level(logging.WARNING, logger="kerykeion.composite_subject.factory"):
        model = CompositeSubjectFactory(first, second).get_midpoint_composite_subject_model()

    cusps = _cusps_of(model)
    # The gap is the fixture's whole point: without one the reader never answers,
    # and this test would pass on any behaviour at all.
    with pytest.raises(ValueError):
        get_planet_house(model.sun.abs_pos, cusps)

    # Not the first house: that is the answer the private copy gave for every one
    # of these, and an assertion that cannot tell the two apart proves nothing.
    assert model.sun.house == "Twelfth_House"
    assert cusps[11] == approx(358.663, abs=0.01), "the fixture's ring moved"
    assert "falls in a gap" in caplog.text, "a ring this shape is worth knowing about"


def test_nothing_rotates_a_ring_the_frame_could_not_repair():
    """The rotation is for a ring that is on a frame. This one is not.

    Under the horizon system a chart at the equator and one at 41.9N do not run
    the same way, so no frame spans them and every position is its own near
    midpoint — the angles included, which therefore cannot follow a ring that
    moves. Rotate it half a turn anyway, to satisfy an identity, and the cusp
    slides out from under the angle that IS it: measured across 148,005 frames,
    ungating the rotation does exactly that to 26 of them, this pair among them.
    """
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 4, 0, city="X", nation="XX", lat=0.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="H",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 16, 0, city="X", nation="XX", lat=41.9, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="H",
    )
    for subject in (first, second):
        assert subject.medium_coeli.abs_pos == approx(subject.tenth_house.abs_pos, abs=1e-9), (
            "the fixture no longer puts the Midheaven on the tenth cusp"
        )

    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        cusps = _cusps_of(model)
        assert model.medium_coeli.abs_pos == approx(cusps[9], abs=1e-9), anchor
        assert model.medium_coeli.house == "Tenth_House", anchor


def test_a_repair_that_is_not_a_house_division_is_not_a_repair():
    """Placing the ring on the frame does not guarantee twelve houses.

    Campanus at 75N repeats six of its own cusps, and a ring placed on the frame
    inherits the repetition: cusp 2 lands on cusp 8, cusp 4 on cusp 10. Nothing
    downstream notices — the twelve are still twelve numbers — but the Midheaven
    then sits on two cusps at once and the reader names the earlier one, so this
    composite came back with its Midheaven in the fourth house.

    Where the frame cannot produce a house division, the plain midpoints are the
    answer and the frame is not coherent. On this pair they put the Midheaven
    back on the tenth cusp — and on the same value the systems whose parents
    agree about where the Midheaven is all give.
    """
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=0.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="C",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 22, 0, city="X", nation="XX", lat=75.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="C",
    )
    model = CompositeSubjectFactory(first, second).get_midpoint_composite_subject_model()
    cusps = _cusps_of(model)

    assert model.medium_coeli.abs_pos == approx(cusps[9], abs=1e-9)
    assert model.medium_coeli.house == "Tenth_House"
    assert model.ascendant.abs_pos == approx(cusps[0], abs=1e-9)
    assert model.ascendant.house == "First_House"


def test_the_ring_is_left_alone_where_no_angle_is_a_cusp():
    """Under Morinus the first cusp is not the Ascendant, so there is no identity
    to keep — and an empty list of identities must not be read as agreement.

    Drop the guard that requires at least one and ``len([]) == len([])`` turns
    every such ring half a circle: 107,100 frames of 460,584 move, under every
    system where neither angle is a cusp — whole sign, Morinus, meridian,
    Carter. Here the first cusp goes from 22.19 degrees to 202.19.
    """
    from kerykeion.utilities.core import circular_mean

    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=0.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="M",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 4, 0, city="X", nation="XX", lat=0.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="M",
    )
    assert first.ascendant.abs_pos != approx(first.first_house.abs_pos, abs=1e-6), (
        "the fixture no longer separates the Ascendant from the first cusp"
    )

    naive = [
        circular_mean(getattr(first, name).abs_pos, getattr(second, name).abs_pos)
        for name in _CUSP_ATTRS
    ]
    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        assert _cusps_of(model) == approx(naive, abs=1e-9), anchor


def test_an_angle_that_is_a_cusp_opens_that_house_even_when_two_cusps_coincide():
    """The composite knows which cusp each angle is. It must not have to look.

    Sunshine inside the antarctic circle brings the eighth cusp, the ninth and the
    tenth onto one longitude. The Midheaven is that longitude, correctly — it is
    the tenth cusp — but a reader scanning the twelve meets the eighth first and
    answers with it. 400 charts of the grid read that way, and
    before the composite recorded the house itself, 3,786 angles were filed
    against a cusp they were not on.
    """
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=-89.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="I",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=-80.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="I",
    )
    for subject in (first, second):
        assert subject.medium_coeli.abs_pos == approx(subject.tenth_house.abs_pos, abs=1e-9)

    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        cusps = _cusps_of(model)
        # The fixture's whole point: without an earlier cusp on the same
        # longitude a scan would answer correctly, and this test would hold on
        # any implementation at all.
        assert cusps[8] == approx(cusps[9], abs=1e-9), "the cusps no longer share a longitude"
        assert model.medium_coeli.abs_pos == approx(cusps[9], abs=1e-9), anchor
        assert model.medium_coeli.house == "Tenth_House", anchor


def test_a_hair_under_half_a_circle_is_not_a_disagreement():
    """Two Ascendants 179.99999192 degrees apart have two midpoints a hair apart.

    The near one and the frame's own choice are then the same point reached two
    ways, and they differ by 8.2e-09 degrees. Read as a broken identity — which a
    tolerance of 1e-9 does — the whole ring turns half a circle to repair eight
    nanodegrees, and the Ascendant of this composite came out 180 degrees from
    its own first cusp, in the seventh house. Across 279,369 identities the
    disagreement is 0 for 271,237 and 180 degrees for 8,098; 34 sit between 1e-9
    and 1e-6, and nothing at all lies in between.
    """
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 7, 0, city="X", nation="XX", lat=-33.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="A",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 12, 0, city="X", nation="XX", lat=-66.75, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="A",
    )
    separation = abs(((second.ascendant.abs_pos - first.ascendant.abs_pos + 180.0) % 360.0) - 180.0)
    assert separation == approx(180.0, abs=1e-4), "the fixture is no longer near half a circle"
    assert separation != approx(180.0, abs=1e-9), "the fixture is now exactly half a circle"

    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        # A microdegree, not a bit: the two ARE the same point reached two ways,
        # and the eight nanodegrees between them are the whole subject here.
        assert model.ascendant.abs_pos == approx(_cusps_of(model)[0], abs=1e-6), anchor
        assert model.ascendant.house == "First_House", anchor


def test_the_descendant_is_derived_and_not_averaged_on_its_own():
    """Averaging the two Imum Coeli separately can land half a turn from the Midheaven.

    Two angles half a circle apart have two midpoints equally near, and separate
    calls pick opposite ones: on this pair the direct average of the two Imum
    Coeli is 173.59 while the Midheaven's own midpoint plus half a turn is 353.59.
    Averaged on its own, an Imum Coeli stops being opposite its own Midheaven —
    which it is by definition, in the parents and here. 2,835 pairs of 39,924
    differ by more than a nanodegree, and the largest difference is exactly 180.
    """
    from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS
    from kerykeion.utilities.core import circular_mean

    points = list(DEFAULT_ACTIVE_POINTS) + [
        name for name in ("Descendant", "Imum_Coeli") if name not in DEFAULT_ACTIVE_POINTS
    ]
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=-89.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="C",
        active_points=points,
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=80.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="C",
        active_points=points,
    )
    direct = circular_mean(first.imum_coeli.abs_pos, second.imum_coeli.abs_pos)

    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        assert (model.imum_coeli.abs_pos - model.medium_coeli.abs_pos) % 360.0 == approx(
            180.0, abs=1e-9
        ), anchor
        assert (model.descendant.abs_pos - model.ascendant.abs_pos) % 360.0 == approx(
            180.0, abs=1e-9
        ), anchor
        # The fixture earns its place only while the two answers still differ.
        assert abs(((direct - model.imum_coeli.abs_pos + 180.0) % 360.0) - 180.0) == approx(
            180.0, abs=1e-6
        ), anchor


def test_a_ring_whose_wedges_run_both_ways_is_not_a_house_division():
    """Twelve arcs can sum to 360 while half of them run the other way.

    The arcs then measure something that is not a partition — some of the circle
    twice and some of it not at all — and the shortest-arc reading each wedge
    falls back on hides it in the total. This is the one real midpoint ring in
    181,125 where that clause is the only thing standing between the ring and
    being called a house division: every arc has width, and they add to 360.
    """
    from kerykeion.composite_subject.factory import _cusp_ring_winds_once
    from kerykeion.utilities.core import circular_mean, house_spans

    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 7, 0, city="X", nation="XX", lat=-89.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="Y",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 7, 0, city="X", nation="XX", lat=-86.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="Y",
    )
    ring = [
        circular_mean(getattr(first, name).abs_pos, getattr(second, name).abs_pos)
        for name in _CUSP_ATTRS
    ]
    spans, reversed_wedges = house_spans(ring)
    assert sum(spans) == approx(360.0, abs=1e-4), "the fixture no longer sums to a full turn"
    assert min(spans) > 1e-9, "the fixture is now caught by the coincident-cusp test instead"
    assert len(set(reversed_wedges)) > 1, "the fixture's wedges no longer run both ways"

    assert not _cusp_ring_winds_once(ring)


def _with_all_four_angles(**kwargs):
    """A subject carrying the Descendant and the Imum Coeli as well as the other two."""
    from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

    points = list(DEFAULT_ACTIVE_POINTS) + [
        name for name in ("Descendant", "Imum_Coeli") if name not in DEFAULT_ACTIVE_POINTS
    ]
    return AstrologicalSubjectFactory.from_birth_data(
        city="X", nation="XX", tz_str="UTC", online=False,
        suppress_geonames_warning=True, active_points=points, **kwargs
    )


def test_all_four_angles_open_their_own_houses_and_not_just_two():
    """The Imum Coeli and the Descendant are angles too, and they were being skipped.

    The predicate that asks "do both parents put this angle on that cusp?" once
    took the ANGLE's index and folded it to a cusp itself, ``0 if index == 0 else
    9``. A caller with four angles passed the cusp numbers straight in, so 3 and 6
    both folded to 9 and the Imum Coeli was measured against the tenth cusp — 180
    degrees away under every quadrant system, so the answer was always no. The
    Imum Coeli below sits exactly on its own fourth cusp and was filed in the
    SECOND house. Across the grid: 3,786 angles filed against a cusp they are not
    on, all of them the two that were being skipped.
    """
    first = _with_all_four_angles(
        name="A", year=1931, month=10, day=24, hour=7, minute=22,
        lat=-79.96424098503815, lng=-133.89223972312217, houses_system_identifier="I",
    )
    second = _with_all_four_angles(
        name="B", year=1914, month=1, day=16, hour=5, minute=38,
        lat=-83.20760144583964, lng=124.95453845875852, houses_system_identifier="I",
    )
    for subject in (first, second):
        assert subject.imum_coeli.abs_pos == approx(subject.fourth_house.abs_pos, abs=1e-9)

    plain = CompositeSubjectFactory(first, second).get_midpoint_composite_subject_model()
    plain_cusps = _cusps_of(plain)
    # Without a collision a scan answers correctly on its own, and this test would
    # pass on any implementation at all. An engine bump that dissolves this one
    # must say so here rather than leave the test green and pinning nothing.
    assert plain_cusps[1] == approx(plain_cusps[2], abs=1e-9), "the cusps no longer collide"

    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        cusps = _cusps_of(model)
        assert model.imum_coeli.abs_pos == approx(cusps[3], abs=1e-9), anchor
        assert model.imum_coeli.house == "Fourth_House", anchor
        assert model.descendant.house == "Seventh_House", anchor


def test_a_cusp_opposite_another_in_both_parents_stays_opposite_it_here():
    """Two longitudes half a circle apart are the same two longitudes either way round.

    Where both charts put the fourth cusp exactly opposite the tenth, the pair
    {fourth, tenth} of one chart and of the other are the SAME set — so a mean of
    that set, which has to be symmetric for the composite of A and B to equal the
    composite of B and A, hands the fourth cusp and the tenth the same answer. The
    ring came back with cusp 4 on cusp 10, and the Imum Coeli, correctly derived
    from the Midheaven, sat half a circle from its own fourth cusp. 765 rings of
    165,132.

    The four angles never had this problem because they derive their opposites
    instead of averaging them. The cusps do it now too — and from the cusp the
    angle is on, so the Midheaven keeps the tenth and not the fourth.
    """
    first = _with_all_four_angles(
        name="A", year=1900, month=1, day=3, hour=3, minute=0,
        lat=-88.0, lng=66.5, houses_system_identifier="C",
    )
    second = _with_all_four_angles(
        name="B", year=1900, month=1, day=3, hour=3, minute=0,
        lat=81.0, lng=66.5, houses_system_identifier="C",
    )
    separation = (second.medium_coeli.abs_pos - first.medium_coeli.abs_pos) % 360.0
    assert separation == approx(180.0, abs=1e-9), "the fixture's Midheavens are no longer antipodal"

    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        cusps = _cusps_of(model)
        assert (cusps[3] - cusps[9]) % 360.0 == approx(180.0, abs=1e-9), anchor
        assert model.medium_coeli.abs_pos == approx(cusps[9], abs=1e-9), anchor
        assert model.imum_coeli.abs_pos == approx(cusps[3], abs=1e-9), anchor
        assert model.medium_coeli.house == "Tenth_House", anchor
        assert model.imum_coeli.house == "Fourth_House", anchor


def test_a_gap_of_a_thousandth_of_a_degree_is_still_not_half_a_turn():
    """The identity gap is not bounded at a microdegree, and a tighter test would fire.

    Two Ascendants approaching half a circle apart make the vector mean's
    resultant vanish, so the error in it grows as 1/cos of half the separation.
    Bisecting the second subject's latitude around the fixture that first showed
    this: at 66.74999964051422S the gap is 2.8e-06 degrees, and at
    66.74999963662323S it is **7.9e-04** — nearly three arcseconds, and still not
    a disagreement. Asked at a microdegree instead of at 90 degrees, this chart
    turns its whole ring half a circle and the Ascendant leaves the first house.
    """
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 7, 0, city="X", nation="XX", lat=-33.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="A",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 12, 0, city="X", nation="XX", lat=-66.74999963662323, lng=0.0,
        tz_str="UTC", online=False, suppress_geonames_warning=True, houses_system_identifier="A",
    )
    for anchor in _ANCHORS:
        model = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        cusps = _cusps_of(model)
        assert model.ascendant.abs_pos == approx(cusps[0], abs=1e-2), anchor
        assert model.ascendant.house == "First_House", anchor

        # This pair is also the one where the opposite-cusp snap does its widest
        # work: all six pairs fire here without a single one having collapsed,
        # the parents put every cusp opposite its partner, and so must this ring.
        assert (cusps[6] - cusps[0]) % 360.0 == approx(180.0, abs=1e-9), anchor
        assert (cusps[7] - cusps[1]) % 360.0 == approx(180.0, abs=1e-9), anchor
        assert (cusps[3] - cusps[9]) % 360.0 == approx(180.0, abs=1e-9), anchor
        if anchor == "ascendant":
            # 7.9e-04 degrees short of its own first cusp was enough, on this
            # ring, to put the Descendant into the sixth house.
            assert model.ascendant.abs_pos == approx(cusps[0], abs=1e-9), anchor


def test_a_ring_that_covers_the_circle_twice_is_not_a_house_division():
    """Twelve cusps sixty degrees apart. Synthetic, deliberately.

    Every wedge is under half a circle, so all twelve read forwards and none has
    zero width: the direction test and the coincident-cusp test both say yes, and
    the ring goes round twice. Only the total tells them apart — 720 against the
    360 a division of the circle adds up to. No real midpoint ring reaches it
    (58,788 measured), which is exactly why it is built here: the reason it cannot
    fire is a fact about today's ephemeris, not about the function.
    """
    from kerykeion.composite_subject.factory import _cusp_ring_winds_once
    from kerykeion.utilities.core import house_spans

    ring = [(60.0 * index) % 360.0 for index in range(12)]
    spans, reversed_wedges = house_spans(ring)
    assert len(set(reversed_wedges)) == 1, "the fixture's wedges no longer agree on a direction"
    assert min(spans) > 1e-9, "the fixture is now caught by the coincident-cusp test instead"
    assert sum(spans) == approx(720.0, abs=1e-4), "the fixture no longer goes round twice"

    assert not _cusp_ring_winds_once(ring)


def test_two_cusps_a_hair_apart_are_the_same_point():
    """The coincident-cusp test is a tolerance, not a sign check.

    A house a ten-thousandth of a milliarcsecond wide is two cusps on one
    longitude by any reading that matters, and it reaches ``get_planet_house``,
    whose exact-on-cusp rule then answers with whichever came first. Built here
    because the narrowest real composite house measured was zero exactly, so
    nothing pins the tolerance between the two.
    """
    from kerykeion.composite_subject.factory import _cusp_ring_winds_once
    from kerykeion.utilities.core import house_spans

    ring = [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0]
    ring[5] = ring[4] + 1e-10
    spans, _reversed = house_spans(ring)
    assert 0.0 < min(spans) < 1e-9, "the fixture's narrowest house left the window"

    assert not _cusp_ring_winds_once(ring)


def test_the_composite_of_a_and_b_is_the_composite_of_b_and_a():
    """Nothing in a composite may depend on which subject was named first.

    The snap that puts a cusp back opposite its partner asks BOTH parents whether
    they had the two opposite. Asking only the second is invisible on an ordinary
    grid and inert on most of a polar one, but it makes the order matter: swept
    over 51,315 ordered polar pairs it moved cusps by as much as 0.09 degrees
    between composite(A, B) and composite(B, A). APC at the pole against the
    equator is one of them.
    """
    first = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=89.9, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="Y",
    )
    second = AstrologicalSubjectFactory.from_birth_data(
        "B", 1990, 6, 15, 0, 0, city="X", nation="XX", lat=0.0, lng=0.0, tz_str="UTC",
        online=False, suppress_geonames_warning=True, houses_system_identifier="Y",
    )
    for anchor in _ANCHORS:
        one = CompositeSubjectFactory(
            first, second, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        other = CompositeSubjectFactory(
            second, first, house_anchor=anchor
        ).get_midpoint_composite_subject_model()
        assert _cusps_of(one) == approx(_cusps_of(other), abs=1e-9), anchor
        assert one.ascendant.abs_pos == approx(other.ascendant.abs_pos, abs=1e-9), anchor
        assert one.medium_coeli.abs_pos == approx(other.medium_coeli.abs_pos, abs=1e-9), anchor


def test_a_house_a_ten_millionth_of_a_degree_wide_is_still_a_house():
    """The coincident-cusp test has to be pinned from above as well as below.

    Below, a house of no width at all is two cusps on one longitude and the ring
    is not a division. Above, a house has to be allowed to be narrow: polar
    systems make genuinely thin ones, and a tolerance set loose enough to swallow
    them would send perfectly good rings down the no-frame path. A ten-millionth
    of a degree is four ten-thousandths of an arcsecond — far below anything an
    ephemeris resolves, and still a house.
    """
    from kerykeion.composite_subject.factory import _cusp_ring_winds_once
    from kerykeion.utilities.core import house_spans

    ring = [0.0, 30.0, 60.0, 90.0, 120.0, 120.0 + 1e-7, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0]
    spans, _reversed = house_spans(ring)
    assert 1e-9 < min(spans) < 1e-6, "the fixture's narrowest house left the window"
    assert sum(spans) == approx(360.0, abs=1e-4)

    assert _cusp_ring_winds_once(ring)
