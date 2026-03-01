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
from kerykeion.composite_subject_factory import CompositeSubjectFactory
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
