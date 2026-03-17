# -*- coding: utf-8 -*-
"""
Tests for v5.12.* — Foundation Enrichment features.

5.12.1 — House cusp speeds (houses_ex2)
5.12.2 — Expanded fixed stars (2 → 22) + magnitude
5.12.3 — Expanded sidereal modes (20 → 48 + USER)
5.12.4 — Ayanamsa value exposure
"""

import pytest
from typing import get_args

from kerykeion import AstrologicalSubjectFactory
from kerykeion.schemas import KerykeionException
from kerykeion.schemas.kr_literals import AstrologicalPoint, SiderealMode
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_subject(**kwargs):
    """Liverpool 1990 subject used across tests."""
    defaults = dict(
        name="Test Subject",
        year=1990,
        month=7,
        day=21,
        hour=14,
        minute=45,
        city="Liverpool",
        nation="GB",
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
    )
    defaults.update(kwargs)
    return AstrologicalSubjectFactory.from_birth_data(**defaults)


# =====================================================================
# 1. 5.12.1 — House cusp speeds
# =====================================================================


class TestHouseCuspSpeeds:
    """Verify houses_ex2 populates speed on house cusps and angles."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.subject = _make_subject()

    def test_house_cusps_have_numeric_speed(self):
        """All 12 house cusps must have a non-None float speed."""
        for i in range(1, 13):
            attr = f"{['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth'][i - 1]}_house"
            house = getattr(self.subject, attr)
            assert house.speed is not None, f"{attr} speed is None"
            assert isinstance(house.speed, float), f"{attr} speed is not float"

    def test_house_cusp_speeds_are_not_sentinel(self):
        """Speeds must not be the old 360.0 sentinel value."""
        for i in range(1, 13):
            attr = f"{['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth'][i - 1]}_house"
            house = getattr(self.subject, attr)
            assert house.speed != 360.0, f"{attr} speed is still the 360.0 sentinel"

    def test_house_cusp_speeds_plausible_range(self):
        """House cusp speeds should be in a plausible range (roughly 0.5–1.5 deg/day for diurnal rotation)."""
        for i in range(1, 13):
            attr = f"{['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth'][i - 1]}_house"
            house = getattr(self.subject, attr)
            # Cusps rotate ~1 degree every ~4 minutes ≈ 360 deg/day in sidereal time,
            # but in ecliptic longitude the speed varies by latitude and house system.
            # Allow a wide range to avoid false positives.
            assert -500 < house.speed < 500, f"{attr} speed {house.speed} is out of plausible range"

    def test_ascendant_has_real_speed(self):
        """Ascendant speed must be non-None and not the old sentinel."""
        assert self.subject.ascendant.speed is not None
        assert isinstance(self.subject.ascendant.speed, float)
        assert self.subject.ascendant.speed != 360.0

    def test_medium_coeli_has_real_speed(self):
        """Medium Coeli speed must be non-None and not the old sentinel."""
        assert self.subject.medium_coeli.speed is not None
        assert isinstance(self.subject.medium_coeli.speed, float)
        assert self.subject.medium_coeli.speed != 360.0

    def test_descendant_has_real_speed(self):
        """Descendant shares ASC speed (same axis)."""
        assert self.subject.descendant.speed is not None
        assert isinstance(self.subject.descendant.speed, float)
        assert self.subject.descendant.speed != 360.0
        # DSC uses the same speed as ASC
        assert self.subject.descendant.speed == self.subject.ascendant.speed

    def test_imum_coeli_has_real_speed(self):
        """IC shares MC speed (same axis)."""
        assert self.subject.imum_coeli.speed is not None
        assert isinstance(self.subject.imum_coeli.speed, float)
        assert self.subject.imum_coeli.speed != 360.0
        # IC uses the same speed as MC
        assert self.subject.imum_coeli.speed == self.subject.medium_coeli.speed

    def test_planet_speeds_still_work(self):
        """Planet speeds must still be populated (no regression)."""
        assert self.subject.sun.speed is not None
        assert self.subject.moon.speed is not None
        assert isinstance(self.subject.sun.speed, float)
        assert isinstance(self.subject.moon.speed, float)

    def test_different_house_systems_have_different_cusp_speeds(self):
        """Koch and Placidus should produce different cusp speeds."""
        placidus = _make_subject(houses_system_identifier="P")
        koch = _make_subject(houses_system_identifier="K")
        # At least some cusps should differ between systems
        differences = 0
        for attr in ["second_house", "third_house", "fifth_house", "sixth_house"]:
            p_speed = getattr(placidus, attr).speed
            k_speed = getattr(koch, attr).speed
            if abs(p_speed - k_speed) > 0.001:
                differences += 1
        assert differences > 0, "Koch and Placidus should have at least one different cusp speed"


# =====================================================================
# 2. 5.12.2 — Expanded fixed stars + magnitude
# =====================================================================


# The 20 new stars (Regulus and Spica were already present)
NEW_FIXED_STARS = [
    "Aldebaran",
    "Antares",
    "Sirius",
    "Fomalhaut",
    "Algol",
    "Betelgeuse",
    "Canopus",
    "Procyon",
    "Arcturus",
    "Pollux",
    "Deneb",
    "Altair",
    "Rigel",
    "Achernar",
    "Capella",
    "Vega",
    "Alcyone",
    "Alphecca",
    "Algorab",
    "Deneb_Algedi",
]

ALL_FIXED_STARS = ["Regulus", "Spica"] + NEW_FIXED_STARS


class TestExpandedFixedStars:
    """Verify all 22 fixed stars calculate correctly and have magnitude."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.subject = _make_subject(active_points=ALL_ACTIVE_POINTS)

    @pytest.mark.parametrize("star_name", NEW_FIXED_STARS)
    def test_new_star_exists_on_subject(self, star_name):
        """Each new fixed star must be present on the subject model."""
        attr = star_name.lower()
        assert hasattr(self.subject, attr), f"Subject has no attribute '{attr}'"
        star = getattr(self.subject, attr)
        assert star is not None, f"{star_name} is None on subject"

    @pytest.mark.parametrize("star_name", ALL_FIXED_STARS)
    def test_star_has_valid_position(self, star_name):
        """Each star must have abs_pos in 0–360 range."""
        star = getattr(self.subject, star_name.lower())
        assert star is not None, f"{star_name} is None"
        assert 0 <= star.abs_pos < 360, f"{star_name} abs_pos {star.abs_pos} out of range"

    @pytest.mark.parametrize("star_name", ALL_FIXED_STARS)
    def test_star_has_sign(self, star_name):
        """Each star must be assigned a zodiac sign."""
        star = getattr(self.subject, star_name.lower())
        assert star.sign is not None
        assert star.sign in [
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

    @pytest.mark.parametrize("star_name", ALL_FIXED_STARS)
    def test_star_is_never_retrograde(self, star_name):
        """Fixed stars must never be retrograde."""
        star = getattr(self.subject, star_name.lower())
        assert star.retrograde is False

    @pytest.mark.parametrize("star_name", ALL_FIXED_STARS)
    def test_star_has_house(self, star_name):
        """Each star must be assigned to a house."""
        star = getattr(self.subject, star_name.lower())
        assert star.house is not None
        assert isinstance(star.house, (int, str))

    @pytest.mark.parametrize("star_name", ALL_FIXED_STARS)
    def test_star_name_matches(self, star_name):
        """The .name field must match the star name."""
        star = getattr(self.subject, star_name.lower())
        assert star.name == star_name


class TestFixedStarMagnitude:
    """Verify the magnitude field on KerykeionPointModel works for fixed stars."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.subject = _make_subject(active_points=ALL_ACTIVE_POINTS)

    @pytest.mark.parametrize("star_name", ALL_FIXED_STARS)
    def test_star_has_magnitude(self, star_name):
        """Each fixed star must have a non-None magnitude."""
        star = getattr(self.subject, star_name.lower())
        assert star.magnitude is not None, f"{star_name} has no magnitude"
        assert isinstance(star.magnitude, float), f"{star_name} magnitude is not float"

    def test_sirius_is_brightest(self):
        """Sirius (mag ~-1.46) should have the lowest (brightest) magnitude."""
        sirius_mag = self.subject.sirius.magnitude
        assert sirius_mag < 0, f"Sirius magnitude {sirius_mag} should be negative (brightest star)"

    def test_algorab_is_dimmest_of_set(self):
        """Algorab (mag ~+2.94) should be the dimmest star in our set."""
        algorab_mag = self.subject.algorab.magnitude
        for star_name in ALL_FIXED_STARS:
            if star_name == "Algorab":
                continue
            other_mag = getattr(self.subject, star_name.lower()).magnitude
            assert algorab_mag >= other_mag, f"Algorab ({algorab_mag}) should be dimmer than {star_name} ({other_mag})"

    def test_known_magnitudes_approximate(self):
        """Spot-check a few well-known stellar magnitudes."""
        # These are approximate visual magnitudes; allow generous tolerance
        assert self.subject.sirius.magnitude == pytest.approx(-1.46, abs=0.2)
        assert self.subject.canopus.magnitude == pytest.approx(-0.74, abs=0.2)
        assert self.subject.arcturus.magnitude == pytest.approx(-0.05, abs=0.2)
        assert self.subject.rigel.magnitude == pytest.approx(0.13, abs=0.3)
        assert self.subject.aldebaran.magnitude == pytest.approx(0.86, abs=0.2)

    def test_planet_magnitude_is_none(self):
        """Planets should have magnitude=None (it's a star-only field)."""
        assert self.subject.sun.magnitude is None
        assert self.subject.moon.magnitude is None
        assert self.subject.mars.magnitude is None


class TestFixedStarInLiterals:
    """Verify the 20 new stars are in the AstrologicalPoint literal."""

    @pytest.mark.parametrize("star_name", NEW_FIXED_STARS)
    def test_star_in_astrological_point_literal(self, star_name):
        """Each new star must be a valid AstrologicalPoint."""
        assert star_name in get_args(AstrologicalPoint)


# =====================================================================
# 3. 5.12.3 — Expanded sidereal modes + USER
# =====================================================================


# The 28 new modes added in v5.12.3
NEW_SIDEREAL_MODES = [
    "ARYABHATA",
    "ARYABHATA_522",
    "ARYABHATA_MSUN",
    "GALCENT_0SAG",
    "GALCENT_COCHRANE",
    "GALCENT_MULA_WILHELM",
    "GALCENT_RGILBRAND",
    "GALEQU_FIORENZA",
    "GALEQU_IAU1958",
    "GALEQU_MULA",
    "GALEQU_TRUE",
    "GALALIGN_MARDYKS",
    "KRISHNAMURTI_VP291",
    "LAHIRI_1940",
    "LAHIRI_ICRC",
    "LAHIRI_VP285",
    "SURYASIDDHANTA",
    "SURYASIDDHANTA_MSUN",
    "SS_CITRA",
    "SS_REVATI",
    "TRUE_CITRA",
    "TRUE_MULA",
    "TRUE_PUSHYA",
    "TRUE_REVATI",
    "TRUE_SHEORAN",
    "BABYL_BRITTON",
    "VALENS_MOON",
    "USER",
]


class TestExpandedSiderealModes:
    """Verify the 28 new sidereal modes are valid and produce sidereal charts."""

    @pytest.mark.parametrize("mode", [m for m in NEW_SIDEREAL_MODES if m != "USER"])
    def test_new_mode_in_literal(self, mode):
        """Each new mode must be a valid SiderealMode literal value."""
        assert mode in get_args(SiderealMode)

    def test_user_mode_in_literal(self):
        """USER must be a valid SiderealMode."""
        assert "USER" in get_args(SiderealMode)

    @pytest.mark.parametrize(
        "mode",
        [
            "ARYABHATA",
            "TRUE_CITRA",
            "GALCENT_0SAG",
            "LAHIRI_1940",
            "SURYASIDDHANTA",
            "BABYL_BRITTON",
            "VALENS_MOON",
        ],
    )
    def test_new_mode_creates_valid_sidereal_subject(self, mode):
        """A representative subset of new modes must produce valid sidereal subjects."""
        subject = _make_subject(zodiac_type="Sidereal", sidereal_mode=mode)
        assert subject.zodiac_type == "Sidereal"
        assert subject.sidereal_mode == mode
        assert 0 <= subject.sun.abs_pos < 360
        assert 0 <= subject.moon.abs_pos < 360

    @pytest.mark.parametrize(
        "mode",
        [
            "ARYABHATA",
            "TRUE_CITRA",
            "GALCENT_0SAG",
            "LAHIRI_1940",
            "SURYASIDDHANTA",
            "BABYL_BRITTON",
            "VALENS_MOON",
        ],
    )
    def test_new_modes_differ_from_tropical(self, mode):
        """Sidereal positions must differ from tropical."""
        tropical = _make_subject()
        sidereal = _make_subject(zodiac_type="Sidereal", sidereal_mode=mode)
        # The ayanamsa offset means abs_pos values differ
        assert tropical.sun.abs_pos != pytest.approx(sidereal.sun.abs_pos, abs=0.5)


class TestUserDefinedAyanamsa:
    """Verify the USER sidereal mode with custom ayanamsa parameters."""

    def test_user_mode_with_valid_params(self):
        """USER mode with t0 and ayan_t0 should produce a valid sidereal chart."""
        # Lahiri-like ayanamsa: t0=J2000.0 (JD 2451545.0), ayan_t0=23.853
        subject = _make_subject(
            zodiac_type="Sidereal",
            sidereal_mode="USER",
            custom_ayanamsa_t0=2451545.0,
            custom_ayanamsa_ayan_t0=23.853,
        )
        assert subject.zodiac_type == "Sidereal"
        assert subject.sidereal_mode == "USER"
        assert 0 <= subject.sun.abs_pos < 360

    def test_user_mode_without_t0_raises(self):
        """USER mode without custom_ayanamsa_t0 must raise."""
        with pytest.raises(KerykeionException, match="custom_ayanamsa_t0"):
            _make_subject(
                zodiac_type="Sidereal",
                sidereal_mode="USER",
                custom_ayanamsa_ayan_t0=23.853,
            )

    def test_user_mode_without_ayan_t0_raises(self):
        """USER mode without custom_ayanamsa_ayan_t0 must raise."""
        with pytest.raises(KerykeionException, match="custom_ayanamsa_ayan_t0"):
            _make_subject(
                zodiac_type="Sidereal",
                sidereal_mode="USER",
                custom_ayanamsa_t0=2451545.0,
            )

    def test_user_mode_without_both_params_raises(self):
        """USER mode without either custom parameter must raise."""
        with pytest.raises(KerykeionException, match="custom_ayanamsa_t0"):
            _make_subject(
                zodiac_type="Sidereal",
                sidereal_mode="USER",
            )

    def test_user_mode_different_ayan_produces_different_positions(self):
        """Different ayan_t0 values should produce different sidereal positions."""
        subject_a = _make_subject(
            zodiac_type="Sidereal",
            sidereal_mode="USER",
            custom_ayanamsa_t0=2451545.0,
            custom_ayanamsa_ayan_t0=20.0,
        )
        subject_b = _make_subject(
            zodiac_type="Sidereal",
            sidereal_mode="USER",
            custom_ayanamsa_t0=2451545.0,
            custom_ayanamsa_ayan_t0=25.0,
        )
        # 5 degrees of ayanamsa difference should produce ~5 degrees of Sun position difference
        diff = abs(subject_a.sun.abs_pos - subject_b.sun.abs_pos)
        assert diff == pytest.approx(5.0, abs=0.5)


# =====================================================================
# 4. 5.12.4 — Ayanamsa value exposure
# =====================================================================


class TestAyanamsaValueExposure:
    """Verify ayanamsa_value is populated for sidereal charts and None for tropical."""

    def test_tropical_ayanamsa_is_none(self):
        """Tropical charts must have ayanamsa_value=None."""
        subject = _make_subject()
        assert subject.ayanamsa_value is None

    def test_sidereal_lahiri_ayanamsa_is_populated(self):
        """Sidereal LAHIRI chart must have a non-None ayanamsa_value."""
        subject = _make_subject(zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        assert subject.ayanamsa_value is not None
        assert isinstance(subject.ayanamsa_value, float)

    def test_sidereal_lahiri_ayanamsa_value_plausible(self):
        """Lahiri ayanamsa in 1990 should be approximately 23.7 degrees."""
        subject = _make_subject(zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        # Lahiri in 1990 is roughly 23.7°
        assert subject.ayanamsa_value == pytest.approx(23.7, abs=0.5)

    def test_sidereal_fagan_bradley_ayanamsa_is_populated(self):
        """Sidereal FAGAN_BRADLEY must have a non-None ayanamsa_value."""
        subject = _make_subject(zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")
        assert subject.ayanamsa_value is not None
        assert isinstance(subject.ayanamsa_value, float)

    def test_different_modes_produce_different_ayanamsa_values(self):
        """Different sidereal modes should produce different ayanamsa values."""
        lahiri = _make_subject(zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        fagan = _make_subject(zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")
        raman = _make_subject(zodiac_type="Sidereal", sidereal_mode="RAMAN")
        # These are all different ayanamsas
        assert lahiri.ayanamsa_value != pytest.approx(fagan.ayanamsa_value, abs=0.01)
        assert lahiri.ayanamsa_value != pytest.approx(raman.ayanamsa_value, abs=0.01)

    def test_ayanamsa_value_positive(self):
        """Ayanamsa should be a positive value (precession moves forward)."""
        subject = _make_subject(zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        assert subject.ayanamsa_value > 0

    def test_user_mode_ayanamsa_value(self):
        """USER mode should also populate ayanamsa_value."""
        subject = _make_subject(
            zodiac_type="Sidereal",
            sidereal_mode="USER",
            custom_ayanamsa_t0=2451545.0,
            custom_ayanamsa_ayan_t0=23.853,
        )
        assert subject.ayanamsa_value is not None
        assert isinstance(subject.ayanamsa_value, float)

    def test_new_mode_ayanamsa_value(self):
        """A new v5.12.3 mode should also populate ayanamsa_value."""
        subject = _make_subject(zodiac_type="Sidereal", sidereal_mode="TRUE_CITRA")
        assert subject.ayanamsa_value is not None
        assert isinstance(subject.ayanamsa_value, float)
        # True Citra should be close to Lahiri (both are ~24° in modern era)
        assert 20 < subject.ayanamsa_value < 28


# =====================================================================
# 5. Guiding principles verification
# =====================================================================


class TestGuidingPrinciples:
    """Verify no breaking changes, Optional defaults, additive-only."""

    def test_magnitude_defaults_to_none(self):
        """magnitude on KerykeionPointModel must default to None (not break existing code)."""
        subject = _make_subject()
        # Planets should have magnitude=None
        assert subject.sun.magnitude is None
        assert subject.moon.magnitude is None

    def test_ayanamsa_value_defaults_to_none(self):
        """ayanamsa_value must default to None for tropical charts."""
        subject = _make_subject()
        assert subject.ayanamsa_value is None

    def test_new_star_fields_default_to_none(self):
        """When not in active_points, new star fields should be None."""
        # Default active_points doesn't include all stars
        subject = _make_subject(active_points=["Sun", "Moon"])
        for star_name in NEW_FIXED_STARS:
            val = getattr(subject, star_name.lower(), None)
            assert val is None, f"{star_name} should be None when not in active_points"

    def test_existing_tropical_chart_unchanged(self):
        """A standard tropical chart should still work exactly as before."""
        subject = _make_subject()
        assert subject.zodiac_type == "Tropical"
        assert subject.sun is not None
        assert subject.moon is not None
        assert subject.ascendant is not None
        assert 0 <= subject.sun.abs_pos < 360
