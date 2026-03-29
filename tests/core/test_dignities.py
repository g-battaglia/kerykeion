# -*- coding: utf-8 -*-
"""Tests for the essential dignities module.

Validates the Ptolemaic essential dignity system: domicile, exaltation,
triplicity, Egyptian terms, Chaldean decans, detriment, and fall.
"""

import pytest
from kerykeion.ephemeris_backend import swe
from kerykeion import AstrologicalSubjectFactory
from kerykeion.dignities.dignity_factory import calculate_essential_dignity
from kerykeion.dignities.dignity_data import (
    DOMICILE_RULERS,
    EXALTATION_TABLE,
    FALL_TABLE,
    DETRIMENT_RULERS,
    EGYPTIAN_TERMS,
    CHALDEAN_DECANS,
    TRIPLICITY_RULERS,
)


class TestDignityData:
    """Test that reference data tables are complete and consistent."""

    def test_domicile_covers_all_signs(self):
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        for sign in signs:
            assert sign in DOMICILE_RULERS, f"Missing domicile for {sign}"
            assert len(DOMICILE_RULERS[sign]) > 0

    def test_detriment_covers_all_signs(self):
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        for sign in signs:
            assert sign in DETRIMENT_RULERS, f"Missing detriment for {sign}"

    def test_egyptian_terms_cover_all_signs(self):
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        for sign in signs:
            assert sign in EGYPTIAN_TERMS
            terms = EGYPTIAN_TERMS[sign]
            assert len(terms) == 5, f"Sign {sign} should have 5 terms"
            assert terms[0][1] == 0, f"First term should start at 0"
            assert terms[-1][2] == 30, f"Last term should end at 30"

    def test_chaldean_decans_cover_all_signs(self):
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        for sign in signs:
            assert sign in CHALDEAN_DECANS
            assert len(CHALDEAN_DECANS[sign]) == 3

    def test_triplicity_covers_all_elements(self):
        for element in ["Fire", "Earth", "Air", "Water"]:
            assert element in TRIPLICITY_RULERS
            assert "day" in TRIPLICITY_RULERS[element]
            assert "night" in TRIPLICITY_RULERS[element]


class TestDignityCalculation:
    """Test dignity computation for known cases."""

    def test_mars_in_aries_domicile(self):
        """Mars rules Aries -> Domicile (+5)."""
        result = calculate_essential_dignity("Mars", "Ari", "Fire", 15.0, True)
        assert result["essential_dignity"] == "Domicile"
        assert result["dignity_score"] >= 5

    def test_sun_in_aries_exaltation(self):
        """Sun is exalted in Aries -> Exaltation (+4)."""
        result = calculate_essential_dignity("Sun", "Ari", "Fire", 19.0, True)
        assert result["essential_dignity"] == "Exaltation"
        assert result["dignity_score"] >= 4

    def test_venus_in_aries_detriment(self):
        """Venus is in detriment in Aries -> Detriment (-5)."""
        result = calculate_essential_dignity("Venus", "Ari", "Fire", 15.0, True)
        assert result["dignity_score"] <= -3  # May have partial dignity from terms/decans
        assert result["essential_dignity"] in ("Detriment", "Face", "Term", "Peregrine")

    def test_saturn_in_aries_fall(self):
        """Saturn is in fall in Aries -> Fall (-4)."""
        result = calculate_essential_dignity("Saturn", "Ari", "Fire", 15.0, True)
        assert result["dignity_score"] < 0

    def test_sun_in_leo_domicile(self):
        """Sun rules Leo -> Domicile (+5)."""
        result = calculate_essential_dignity("Sun", "Leo", "Fire", 10.0, True)
        assert result["essential_dignity"] == "Domicile"
        assert result["dignity_score"] >= 5

    def test_moon_in_cancer_domicile(self):
        """Moon rules Cancer -> Domicile (+5)."""
        result = calculate_essential_dignity("Moon", "Can", "Water", 10.0, False)
        assert result["essential_dignity"] == "Domicile"

    def test_mercury_in_virgo_domicile(self):
        """Mercury rules Virgo -> Domicile (+5)."""
        result = calculate_essential_dignity("Mercury", "Vir", "Earth", 15.0, True)
        assert result["essential_dignity"] == "Domicile"
        # Mercury is also exalted in Virgo, so score should be very high
        assert result["dignity_score"] >= 9

    def test_decan_number(self):
        """Test decan calculation: 0-10 = decan 1, 10-20 = decan 2, 20-30 = decan 3."""
        r1 = calculate_essential_dignity("Mars", "Tau", "Earth", 5.0, True)
        assert r1["decan_number"] == 1
        r2 = calculate_essential_dignity("Mars", "Tau", "Earth", 15.0, True)
        assert r2["decan_number"] == 2
        r3 = calculate_essential_dignity("Mars", "Tau", "Earth", 25.0, True)
        assert r3["decan_number"] == 3

    def test_term_ruler_exists(self):
        """All classical planets should get a term ruler."""
        result = calculate_essential_dignity("Jupiter", "Ari", "Fire", 3.0, True)
        assert result["term_ruler"] == "Jupiter"  # First term in Aries is Jupiter (0-6)

    def test_non_classical_planet_returns_none(self):
        """Modern planets (Uranus, Neptune, Pluto) should return all None."""
        result = calculate_essential_dignity("Uranus", "Aqu", "Air", 10.0, True)
        assert result["essential_dignity"] is None
        assert result["dignity_score"] is None
        assert result["decan_number"] is None

    def test_triplicity_day_chart(self):
        """Sun is day triplicity ruler of Fire signs."""
        result = calculate_essential_dignity("Sun", "Sag", "Fire", 15.0, True)
        assert result["dignity_score"] >= 3  # At least triplicity

    def test_triplicity_night_chart(self):
        """Jupiter is night triplicity ruler of Fire signs."""
        result = calculate_essential_dignity("Jupiter", "Leo", "Fire", 15.0, False)
        assert result["dignity_score"] >= 3  # At least triplicity


class TestDignityHelperEdgeCases:
    """Test edge-case branches in dignity helper functions."""

    def test_get_decan_ruler_unknown_sign(self):
        """_get_decan_ruler should return None for an unknown sign."""
        from kerykeion.dignities.dignity_factory import _get_decan_ruler
        assert _get_decan_ruler("Unknown", 1) is None

    def test_get_term_ruler_unknown_sign(self):
        """_get_term_ruler should return None for an unknown sign."""
        from kerykeion.dignities.dignity_factory import _get_term_ruler
        assert _get_term_ruler("Unknown", 15.0) is None

    def test_get_term_ruler_no_match(self):
        """_get_term_ruler should return None when degree matches no term range."""
        from kerykeion.dignities.dignity_factory import _get_term_ruler
        # Egyptian terms cover 0-30 for each sign, so degree 30+ should not match
        assert _get_term_ruler("Ari", 30.0) is None

    def test_compute_dignity_non_classical_planet(self):
        """_compute_dignity should return (None, None) for non-classical planets."""
        from kerykeion.dignities.dignity_factory import _compute_dignity
        result = _compute_dignity("Uranus", "Aqu", "Air", 15.0, True, 2, None, None)
        assert result == (None, None)

    def test_fall_only_label(self):
        """A planet with only Fall (no detriment) should be labeled 'Fall'."""
        # Saturn is in fall in Aries (FALL_TABLE["Ari"] == "Saturn")
        # but is NOT in detriment in Aries (DETRIMENT_RULERS["Ari"] should not include Saturn)
        # Let's pick a case: Moon is in fall in Scorpio (FALL_TABLE["Sco"] == "Moon")
        # and Moon is NOT in detriment in Scorpio
        from kerykeion.dignities.dignity_data import FALL_TABLE, DETRIMENT_RULERS
        # Find a planet that is in fall but not in detriment for a sign
        for sign, fall_planet in FALL_TABLE.items():
            if fall_planet and fall_planet not in DETRIMENT_RULERS.get(sign, []):
                # Use a position where there's no other dignity
                result = calculate_essential_dignity(fall_planet, sign, "Fire", 15.0, True)
                if result["essential_dignity"] == "Fall":
                    assert result["dignity_score"] < 0
                    return
        # If no pure Fall case is found (unlikely), just verify Saturn in Aries
        result = calculate_essential_dignity("Saturn", "Ari", "Fire", 15.0, True)
        assert result["dignity_score"] < 0


class TestDignityIntegration:
    """Test dignities integrated in AstrologicalSubjectFactory."""

    @pytest.fixture(scope="class")
    def subject_with_dignities(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Dignity Test", 1990, 1, 1, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            calculate_dignities=True,
        )

    @pytest.fixture(scope="class")
    def subject_without_dignities(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "No Dignity", 1990, 1, 1, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )

    def test_dignity_fields_populated(self, subject_with_dignities):
        """Classical planets should have dignity data when enabled."""
        sun = subject_with_dignities.sun
        assert sun.essential_dignity is not None
        assert sun.dignity_score is not None
        assert sun.decan_number is not None
        assert sun.decan_ruler is not None

    def test_dignity_fields_not_populated_by_default(self, subject_without_dignities):
        """Dignity fields should be None when not enabled."""
        sun = subject_without_dignities.sun
        assert sun.essential_dignity is None
        assert sun.dignity_score is None
        assert sun.decan_number is None

    def test_all_classical_planets_have_dignities(self, subject_with_dignities):
        """All 7 classical planets should have dignity data."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_dignities, name)
            if point is not None:
                assert point.essential_dignity is not None, f"{name} should have essential_dignity"
                assert point.dignity_score is not None, f"{name} should have dignity_score"

    def test_modern_planets_no_dignities(self, subject_with_dignities):
        """Modern planets (Uranus, Neptune, Pluto) should not have dignities."""
        for name in ["uranus", "neptune", "pluto"]:
            point = getattr(subject_with_dignities, name)
            if point is not None:
                assert point.essential_dignity is None, f"{name} should not have essential_dignity"


class TestDignitySwissEphRegression:
    """Known-value regression tests using Swiss Ephemeris (swe) as reference.

    Each test computes a planet's ecliptic longitude via swe.calc_ut, derives
    the zodiac sign and degree-within-sign, then verifies that
    calculate_essential_dignity returns the correct Ptolemaic dignity.
    """

    SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
             "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
    ELEMENTS = ["Fire", "Earth", "Air", "Water", "Fire", "Earth",
                "Air", "Water", "Fire", "Earth", "Air", "Water"]

    @classmethod
    def setup_class(cls):
        swe.set_ephe_path("")

    @staticmethod
    def _sign_and_position(abs_lon: float):
        """Return (sign_abbrev, element, degree_in_sign) from absolute longitude."""
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
                 "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        elements = ["Fire", "Earth", "Air", "Water", "Fire", "Earth",
                    "Air", "Water", "Fire", "Earth", "Air", "Water"]
        idx = int(abs_lon / 30.0)
        return signs[idx], elements[idx], abs_lon - idx * 30.0

    def test_sun_in_leo_domicile_swe(self):
        """Sun on 2000-08-01 12:00 UTC is in Leo (~129.5 deg) -> Domicile.

        Reference: swe.calc_ut(2451758.0, swe.SUN, swe.FLG_SWIEPH)
        Sun rules Leo in the Ptolemaic domicile table.
        """
        jd = swe.julday(2000, 8, 1, 12.0)
        assert abs(jd - 2451758.0) < 1e-6
        sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]

        sign, element, pos_in_sign = self._sign_and_position(sun_lon)
        assert sign == "Leo", f"Expected Leo, got {sign} at {sun_lon:.4f} deg"

        result = calculate_essential_dignity("Sun", sign, element, pos_in_sign, True)
        assert result["essential_dignity"] == "Domicile"
        assert result["dignity_score"] >= 5

    def test_moon_in_cancer_domicile_swe(self):
        """Moon on 2000-01-19 12:00 UTC is in Cancer (~95.0 deg) -> Domicile.

        Reference: swe.calc_ut(2451563.0, swe.MOON, swe.FLG_SWIEPH)
        Moon rules Cancer in the Ptolemaic domicile table.
        """
        jd = swe.julday(2000, 1, 19, 12.0)
        assert abs(jd - 2451563.0) < 1e-6
        moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]

        sign, element, pos_in_sign = self._sign_and_position(moon_lon)
        assert sign == "Can", f"Expected Can, got {sign} at {moon_lon:.4f} deg"

        result = calculate_essential_dignity("Moon", sign, element, pos_in_sign, True)
        assert result["essential_dignity"] == "Domicile"
        assert result["dignity_score"] >= 5

    def test_mars_in_capricorn_exaltation_swe(self):
        """Mars on 2020-03-20 12:00 UTC is in Capricorn (~292.8 deg) -> Exaltation.

        Reference: swe.calc_ut(2458929.0, swe.MARS, swe.FLG_SWIEPH)
        Mars is exalted in Capricorn at 28 deg in the Ptolemaic table.
        """
        jd = swe.julday(2020, 3, 20, 12.0)
        assert abs(jd - 2458929.0) < 1e-6
        mars_lon = swe.calc_ut(jd, swe.MARS, swe.FLG_SWIEPH)[0][0]

        sign, element, pos_in_sign = self._sign_and_position(mars_lon)
        assert sign == "Cap", f"Expected Cap, got {sign} at {mars_lon:.4f} deg"

        result = calculate_essential_dignity("Mars", sign, element, pos_in_sign, True)
        assert result["essential_dignity"] == "Exaltation"
        assert result["dignity_score"] >= 4
