"""Dedicated tests for Arabic Parts (Lots) calculations.

Covers:
- Formula correctness for all four parts (Fortunae, Spiritus, Amoris, Fidei)
- Day/night chart detection via Sun altitude (swe.azalt)
- Day/night formula symmetry (Fortunae day = Spiritus night and vice versa)
- Fallback to house-based detection when swe.azalt fails
- Warning when Sun position is unavailable
- Result properties (range, house, sign, retrograde)
- Auto-activation of required prerequisite points
- Different geographic locations and edge cases
- Sidereal mode
- All parts calculated simultaneously
- is_diurnal field on AstrologicalSubjectModel
- is_diurnal independent of zodiac_type and perspective_type
"""

import math
import logging
from unittest.mock import patch

import pytest
from pytest import approx

from kerykeion import AstrologicalSubjectFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_subject(hour, minute=0, *, lat=51.5074, lng=0.0, tz_str="Etc/GMT", active_points=None, **kwargs):
    """Shortcut to create a subject for June 15 1990 at the given hour."""
    return AstrologicalSubjectFactory.from_birth_data(
        name="Test",
        year=1990,
        month=6,
        day=15,
        hour=hour,
        minute=minute,
        lat=lat,
        lng=lng,
        tz_str=tz_str,
        online=False,
        suppress_geonames_warning=True,
        active_points=active_points
        or [
            "Sun",
            "Moon",
            "Ascendant",
            "Pars_Fortunae",
            "Pars_Spiritus",
            "Pars_Amoris",
            "Pars_Fidei",
            "Venus",
            "Jupiter",
            "Saturn",
        ],
        **kwargs,
    )


def _normalize(deg):
    """Normalize a degree value to [0, 360)."""
    result = math.fmod(deg, 360)
    if result < 0:
        result += 360
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def day_subject():
    """Noon in London — Sun above the horizon (day chart)."""
    return _make_subject(12)


@pytest.fixture
def night_subject():
    """Midnight in London — Sun below the horizon (night chart)."""
    return _make_subject(0)


# ===========================================================================
# 1. Formula correctness
# ===========================================================================


class TestFormulaCorrectness:
    """Verify the exact formula applied for each Arabic Part."""

    def test_pars_fortunae_day_formula(self, day_subject):
        """Day chart: Pars Fortunae = Asc + Moon - Sun."""
        s = day_subject
        expected = _normalize(s.ascendant.abs_pos + s.moon.abs_pos - s.sun.abs_pos)
        assert s.pars_fortunae.abs_pos == approx(expected, abs=0.01)

    def test_pars_fortunae_night_formula(self, night_subject):
        """Night chart: Pars Fortunae = Asc + Sun - Moon."""
        s = night_subject
        expected = _normalize(s.ascendant.abs_pos + s.sun.abs_pos - s.moon.abs_pos)
        assert s.pars_fortunae.abs_pos == approx(expected, abs=0.01)

    def test_pars_spiritus_day_formula(self, day_subject):
        """Day chart: Pars Spiritus = Asc + Sun - Moon."""
        s = day_subject
        expected = _normalize(s.ascendant.abs_pos + s.sun.abs_pos - s.moon.abs_pos)
        assert s.pars_spiritus.abs_pos == approx(expected, abs=0.01)

    def test_pars_spiritus_night_formula(self, night_subject):
        """Night chart: Pars Spiritus = Asc + Moon - Sun."""
        s = night_subject
        expected = _normalize(s.ascendant.abs_pos + s.moon.abs_pos - s.sun.abs_pos)
        assert s.pars_spiritus.abs_pos == approx(expected, abs=0.01)

    def test_pars_amoris_formula(self, day_subject):
        """Pars Amoris = Asc + Venus - Sun (no day/night variant)."""
        s = day_subject
        expected = _normalize(s.ascendant.abs_pos + s.venus.abs_pos - s.sun.abs_pos)
        assert s.pars_amoris.abs_pos == approx(expected, abs=0.01)

    def test_pars_amoris_same_day_and_night(self, day_subject, night_subject):
        """Pars Amoris uses the same formula regardless of day/night."""
        for s in (day_subject, night_subject):
            expected = _normalize(s.ascendant.abs_pos + s.venus.abs_pos - s.sun.abs_pos)
            assert s.pars_amoris.abs_pos == approx(expected, abs=0.01)

    def test_pars_fidei_formula(self, day_subject):
        """Pars Fidei = Asc + Jupiter - Saturn (no day/night variant)."""
        s = day_subject
        expected = _normalize(s.ascendant.abs_pos + s.jupiter.abs_pos - s.saturn.abs_pos)
        assert s.pars_fidei.abs_pos == approx(expected, abs=0.01)

    def test_pars_fidei_same_day_and_night(self, day_subject, night_subject):
        """Pars Fidei uses the same formula regardless of day/night."""
        for s in (day_subject, night_subject):
            expected = _normalize(s.ascendant.abs_pos + s.jupiter.abs_pos - s.saturn.abs_pos)
            assert s.pars_fidei.abs_pos == approx(expected, abs=0.01)


# ===========================================================================
# 2. Day/night symmetry between Fortunae and Spiritus
# ===========================================================================


class TestDayNightSymmetry:
    """Pars Fortunae and Pars Spiritus swap formulas between day and night."""

    def test_fortunae_day_equals_spiritus_night(self):
        """Fortunae(day) and Spiritus(night) use the same formula: Asc + Moon - Sun."""
        day = _make_subject(12)
        night = _make_subject(0)

        # Both use Asc + Moon - Sun for their respective chart type
        fortunae_day = _normalize(day.ascendant.abs_pos + day.moon.abs_pos - day.sun.abs_pos)
        spiritus_night = _normalize(night.ascendant.abs_pos + night.moon.abs_pos - night.sun.abs_pos)

        assert day.pars_fortunae.abs_pos == approx(fortunae_day, abs=0.01)
        assert night.pars_spiritus.abs_pos == approx(spiritus_night, abs=0.01)

    def test_fortunae_night_equals_spiritus_day(self):
        """Fortunae(night) and Spiritus(day) use the same formula: Asc + Sun - Moon."""
        day = _make_subject(12)
        night = _make_subject(0)

        # Both use Asc + Sun - Moon for their respective chart type
        spiritus_day = _normalize(day.ascendant.abs_pos + day.sun.abs_pos - day.moon.abs_pos)
        fortunae_night = _normalize(night.ascendant.abs_pos + night.sun.abs_pos - night.moon.abs_pos)

        assert day.pars_spiritus.abs_pos == approx(spiritus_day, abs=0.01)
        assert night.pars_fortunae.abs_pos == approx(fortunae_night, abs=0.01)

    def test_day_and_night_produce_different_values(self):
        """For the same chart, Fortunae and Spiritus should differ (unless Moon == Sun)."""
        s = _make_subject(12)
        # They use inverted formulas, so unless Moon and Sun have the same position,
        # the results must be different.
        if s.sun.abs_pos != approx(s.moon.abs_pos, abs=0.01):
            assert s.pars_fortunae.abs_pos != approx(s.pars_spiritus.abs_pos, abs=0.01)


# ===========================================================================
# 3. Result properties
# ===========================================================================


class TestResultProperties:
    """Verify structural properties of calculated Arabic Parts."""

    @pytest.mark.parametrize(
        "part_name",
        [
            "pars_fortunae",
            "pars_spiritus",
            "pars_amoris",
            "pars_fidei",
        ],
    )
    def test_abs_pos_in_valid_range(self, day_subject, part_name):
        """abs_pos must be in [0, 360)."""
        part = getattr(day_subject, part_name)
        assert part is not None
        assert 0 <= part.abs_pos < 360

    @pytest.mark.parametrize(
        "part_name",
        [
            "pars_fortunae",
            "pars_spiritus",
            "pars_amoris",
            "pars_fidei",
        ],
    )
    def test_retrograde_is_false(self, day_subject, part_name):
        """Arabic Parts are conceptual points, never retrograde."""
        part = getattr(day_subject, part_name)
        assert part.retrograde is False

    @pytest.mark.parametrize(
        "part_name",
        [
            "pars_fortunae",
            "pars_spiritus",
            "pars_amoris",
            "pars_fidei",
        ],
    )
    def test_house_is_assigned(self, day_subject, part_name):
        """Each part must be assigned to a house."""
        part = getattr(day_subject, part_name)
        assert part.house is not None
        assert "House" in part.house

    @pytest.mark.parametrize(
        "part_name",
        [
            "pars_fortunae",
            "pars_spiritus",
            "pars_amoris",
            "pars_fidei",
        ],
    )
    def test_sign_is_assigned(self, day_subject, part_name):
        """Each part must have a zodiac sign."""
        part = getattr(day_subject, part_name)
        assert part.sign is not None
        assert len(part.sign) > 0

    @pytest.mark.parametrize(
        "part_name,expected_name",
        [
            ("pars_fortunae", "Pars_Fortunae"),
            ("pars_spiritus", "Pars_Spiritus"),
            ("pars_amoris", "Pars_Amoris"),
            ("pars_fidei", "Pars_Fidei"),
        ],
    )
    def test_name_matches(self, day_subject, part_name, expected_name):
        """The .name attribute must match the point identifier."""
        part = getattr(day_subject, part_name)
        assert part.name == expected_name


# ===========================================================================
# 4. Auto-activation of prerequisites
# ===========================================================================


class TestAutoActivation:
    """Arabic Parts auto-activate the points they depend on."""

    def test_pars_fortunae_auto_activates_sun_moon_ascendant(self):
        """Requesting only Pars_Fortunae should auto-add Sun, Moon, Ascendant."""
        subject = _make_subject(12, active_points=["Pars_Fortunae"])
        assert subject.pars_fortunae is not None
        assert subject.sun is not None
        assert subject.moon is not None
        assert subject.ascendant is not None

    def test_pars_spiritus_auto_activates_sun_moon_ascendant(self):
        """Requesting only Pars_Spiritus should auto-add Sun, Moon, Ascendant."""
        subject = _make_subject(12, active_points=["Pars_Spiritus"])
        assert subject.pars_spiritus is not None
        assert subject.sun is not None
        assert subject.moon is not None

    def test_pars_amoris_auto_activates_venus_sun_ascendant(self):
        """Requesting only Pars_Amoris should auto-add Venus, Sun, Ascendant."""
        subject = _make_subject(12, active_points=["Pars_Amoris"])
        assert subject.pars_amoris is not None
        assert subject.venus is not None
        assert subject.sun is not None

    def test_pars_fidei_auto_activates_jupiter_saturn_ascendant(self):
        """Requesting only Pars_Fidei should auto-add Jupiter, Saturn, Ascendant."""
        subject = _make_subject(12, active_points=["Pars_Fidei"])
        assert subject.pars_fidei is not None
        assert subject.jupiter is not None
        assert subject.saturn is not None


# ===========================================================================
# 5. Day/night detection via Sun altitude
# ===========================================================================


class TestDayNightDetection:
    """Verify the Sun altitude-based day/night detection."""

    def test_noon_is_diurnal(self):
        """At noon the Sun is above the horizon — diurnal chart."""
        day = _make_subject(12)
        # Diurnal chart: Fortunae = Asc + Moon - Sun
        day_expected = _normalize(day.ascendant.abs_pos + day.moon.abs_pos - day.sun.abs_pos)
        assert day.pars_fortunae.abs_pos == approx(day_expected, abs=0.01)

    def test_midnight_is_nocturnal(self):
        """At midnight the Sun is below the horizon — nocturnal chart."""
        night = _make_subject(0)
        night_expected = _normalize(night.ascendant.abs_pos + night.sun.abs_pos - night.moon.abs_pos)
        assert night.pars_fortunae.abs_pos == approx(night_expected, abs=0.01)

    def test_evening_is_nocturnal(self):
        """At 22:00 in Rome the Sun is below the horizon in June."""
        subject = _make_subject(22, lat=41.9, lng=12.5, tz_str="Europe/Rome")
        expected = _normalize(subject.ascendant.abs_pos + subject.sun.abs_pos - subject.moon.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)

    def test_morning_is_diurnal(self):
        """At 10:00 in London the Sun is above the horizon."""
        subject = _make_subject(10)
        expected = _normalize(subject.ascendant.abs_pos + subject.moon.abs_pos - subject.sun.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)


# ===========================================================================
# 6. Fallback paths
# ===========================================================================


class TestFallbackPaths:
    """Test the fallback logic in _compute_is_diurnal when swe.azalt or swe.calc_ut fails."""

    def test_azalt_failure_defaults_to_diurnal(self, caplog):
        """If swe.azalt raises, default to diurnal."""

        def mock_azalt(*args, **kwargs):
            raise RuntimeError("Mock azalt failure")

        with patch("swisseph.azalt", side_effect=mock_azalt):
            with caplog.at_level(logging.WARNING):
                subject = _make_subject(12)

        assert subject.is_diurnal is True
        assert any("defaulting to diurnal" in msg.lower() for msg in caplog.messages)

    def test_azalt_failure_at_night_also_defaults_to_diurnal(self, caplog):
        """When azalt fails at midnight, defaults to diurnal (conservative fallback)."""

        def mock_azalt(*args, **kwargs):
            raise RuntimeError("Mock azalt failure")

        with patch("swisseph.azalt", side_effect=mock_azalt):
            with caplog.at_level(logging.WARNING):
                midnight = _make_subject(0)

        assert midnight.is_diurnal is True

    def test_sun_calculation_failure_propagates_from_ensure_point(self):
        """If Sun calculation fails in _ensure_point_calculated, the exception propagates.

        This is expected: _ensure_point_calculated does not catch exceptions,
        and the caller (_calculate_planets) handles them at a higher level.
        """
        import swisseph as swe

        original_calc = swe.calc_ut

        def mock_calc_ut(jd, planet_num, flags):
            if planet_num == 0:  # Sun
                raise Exception("Mock: Sun calculation failed")
            return original_calc(jd, planet_num, flags)

        with patch("swisseph.calc_ut", side_effect=mock_calc_ut):
            with pytest.raises(Exception, match="Mock: Sun calculation failed"):
                AstrologicalSubjectFactory.from_birth_data(
                    name="No Sun",
                    year=1990,
                    month=6,
                    day=15,
                    hour=0,
                    minute=0,
                    lat=51.5074,
                    lng=0.0,
                    tz_str="Etc/GMT",
                    online=False,
                    suppress_geonames_warning=True,
                    active_points=["Pars_Fortunae", "Moon", "Ascendant"],
                )

    def test_compute_is_diurnal_direct_defensive_path(self, caplog):
        """Test _compute_is_diurnal fallback when swe.calc_ut fails."""
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        def mock_calc_ut(*args, **kwargs):
            raise RuntimeError("Mock calc_ut failure")

        with patch("swisseph.calc_ut", side_effect=mock_calc_ut):
            with caplog.at_level(logging.WARNING):
                result = AstrologicalSubjectFactory._compute_is_diurnal(
                    julian_day=2448058.0,
                    lat=51.5074,
                    lng=0.0,
                    altitude=0,
                )

        assert result is True
        assert any("defaulting to diurnal" in msg.lower() for msg in caplog.messages)


# ===========================================================================
# 7. Geographic edge cases
# ===========================================================================


class TestGeographicEdgeCases:
    """Verify Arabic Parts at different latitudes."""

    def test_equator(self):
        """Arabic Parts at the equator (lat=0)."""
        subject = _make_subject(12, lat=0.0, lng=0.0)
        assert subject.pars_fortunae is not None
        assert 0 <= subject.pars_fortunae.abs_pos < 360

    def test_high_latitude_north(self):
        """Arabic Parts at high northern latitude (Tromso, Norway)."""
        subject = _make_subject(12, lat=69.65, lng=18.96)
        assert subject.pars_fortunae is not None
        assert 0 <= subject.pars_fortunae.abs_pos < 360

    def test_southern_hemisphere(self):
        """Arabic Parts in the southern hemisphere (Buenos Aires)."""
        subject = _make_subject(12, lat=-34.6, lng=-58.4)
        assert subject.pars_fortunae is not None
        expected = _normalize(subject.ascendant.abs_pos + subject.moon.abs_pos - subject.sun.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)

    def test_southern_hemisphere_midnight(self):
        """Night chart in the southern hemisphere."""
        subject = _make_subject(0, lat=-34.6, lng=-58.4)
        assert subject.pars_fortunae is not None
        expected = _normalize(subject.ascendant.abs_pos + subject.sun.abs_pos - subject.moon.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)


# ===========================================================================
# 8. Sidereal mode
# ===========================================================================


class TestSiderealMode:
    """Arabic Parts with sidereal zodiac."""

    def test_sidereal_parts_are_calculated(self):
        """Arabic Parts should work in sidereal mode."""
        subject = _make_subject(
            12,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        assert subject.pars_fortunae is not None
        assert subject.pars_spiritus is not None
        assert 0 <= subject.pars_fortunae.abs_pos < 360

    def test_sidereal_formula_correctness(self):
        """Sidereal Parts should still follow the same formulas."""
        subject = _make_subject(
            12,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        expected = _normalize(subject.ascendant.abs_pos + subject.moon.abs_pos - subject.sun.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)

    def test_sidereal_differs_from_tropical(self):
        """Sidereal and tropical should produce different abs_pos values."""
        tropical = _make_subject(12)
        sidereal = _make_subject(12, zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        # The ayanamsa offset means positions differ
        assert tropical.pars_fortunae.abs_pos != approx(sidereal.pars_fortunae.abs_pos, abs=0.1)


# ===========================================================================
# 9. All parts simultaneously
# ===========================================================================


class TestAllPartsTogether:
    """Verify all four Arabic Parts calculated in a single chart."""

    def test_all_four_parts_present(self, day_subject):
        """All four parts should be present when requested."""
        assert day_subject.pars_fortunae is not None
        assert day_subject.pars_spiritus is not None
        assert day_subject.pars_amoris is not None
        assert day_subject.pars_fidei is not None

    def test_all_four_parts_have_distinct_positions(self, day_subject):
        """All four parts should (in general) have different positions."""
        positions = {
            day_subject.pars_fortunae.abs_pos,
            day_subject.pars_spiritus.abs_pos,
            day_subject.pars_amoris.abs_pos,
            day_subject.pars_fidei.abs_pos,
        }
        # At minimum, Fortunae and Fidei should differ (completely different inputs)
        assert day_subject.pars_fortunae.abs_pos != approx(day_subject.pars_fidei.abs_pos, abs=0.01)

    def test_parts_not_calculated_when_not_requested(self):
        """Parts should be None when not in active_points."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Minimal",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lat=51.5074,
            lng=0.0,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon"],
        )
        assert subject.pars_fortunae is None
        assert subject.pars_spiritus is None
        assert subject.pars_amoris is None
        assert subject.pars_fidei is None


# ===========================================================================
# 10. is_diurnal field
# ===========================================================================


class TestIsDiurnalField:
    """Verify the is_diurnal field on AstrologicalSubjectModel."""

    def test_noon_is_diurnal_true(self):
        """At noon the Sun is above the horizon — is_diurnal should be True."""
        subject = _make_subject(12)
        assert subject.is_diurnal is True

    def test_midnight_is_diurnal_false(self):
        """At midnight the Sun is below the horizon — is_diurnal should be False."""
        subject = _make_subject(0)
        assert subject.is_diurnal is False

    def test_evening_is_diurnal_false(self):
        """At 22:00 in June at London latitude, Sun is below horizon."""
        subject = _make_subject(22)
        assert subject.is_diurnal is False

    def test_morning_is_diurnal_true(self):
        """At 10:00 in June at London latitude, Sun is above horizon."""
        subject = _make_subject(10)
        assert subject.is_diurnal is True

    def test_is_diurnal_in_model_dump(self):
        """is_diurnal should appear in model_dump()."""
        subject = _make_subject(12)
        dump = subject.model_dump()
        assert "is_diurnal" in dump
        assert dump["is_diurnal"] is True

    def test_is_diurnal_in_json_output(self):
        """is_diurnal should appear in model_dump_json()."""
        import json

        subject = _make_subject(12)
        json_str = subject.model_dump_json()
        data = json.loads(json_str)
        assert "is_diurnal" in data
        assert data["is_diurnal"] is True

    def test_sidereal_same_is_diurnal_as_tropical(self):
        """is_diurnal should be the same for sidereal and tropical charts.

        The sect classification is based on the physical position of the Sun
        relative to the horizon, which is independent of zodiac type.
        """
        tropical = _make_subject(12)
        sidereal = _make_subject(12, zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        assert tropical.is_diurnal == sidereal.is_diurnal

    def test_sidereal_midnight_same_is_diurnal_as_tropical(self):
        """At midnight, both sidereal and tropical should be nocturnal."""
        tropical = _make_subject(0)
        sidereal = _make_subject(0, zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        assert tropical.is_diurnal == sidereal.is_diurnal
        assert tropical.is_diurnal is False

    def test_heliocentric_uses_geocentric_sun(self):
        """Heliocentric charts should still have correct is_diurnal.

        The sect classification uses the geocentric position of the Sun
        (where the observer is on Earth), regardless of chart perspective.
        """
        from kerykeion import AstrologicalSubjectFactory

        # Heliocentric chart at noon
        helio = AstrologicalSubjectFactory.from_birth_data(
            name="Heliocentric",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lat=51.5074,
            lng=0.0,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
            perspective_type="Heliocentric",
        )
        # Should still be diurnal (noon, Sun above horizon from Earth's perspective)
        assert helio.is_diurnal is True

    def test_is_diurnal_consistent_with_arabic_parts_formula(self):
        """is_diurnal should be consistent with the formula applied to Pars Fortunae."""
        subject = _make_subject(12)
        # Day chart: Pars Fortunae = Asc + Moon - Sun
        expected = _normalize(subject.ascendant.abs_pos + subject.moon.abs_pos - subject.sun.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)
        assert subject.is_diurnal is True

    def test_is_diurnal_consistent_with_night_formula(self):
        """At night, is_diurnal should be False and night formula should apply."""
        subject = _make_subject(0)
        # Night chart: Pars Fortunae = Asc + Sun - Moon
        expected = _normalize(subject.ascendant.abs_pos + subject.sun.abs_pos - subject.moon.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)
        assert subject.is_diurnal is False

    def test_is_diurnal_not_on_composite(self):
        """CompositeSubjectModel should not have is_diurnal field."""
        from kerykeion import CompositeSubjectFactory

        first = _make_subject(12, active_points=["Sun", "Moon", "Ascendant"])
        second = _make_subject(6, active_points=["Sun", "Moon", "Ascendant"])

        composite = CompositeSubjectFactory(first, second)
        model = composite.get_midpoint_composite_subject_model()

        # CompositeSubjectModel does not have is_diurnal (no meaningful sect)
        # getattr returns None if attribute doesn't exist (Pydantic v2 behavior for missing fields)
        assert getattr(model, "is_diurnal", None) is None

    def test_southern_hemisphere_summer_day(self):
        """In southern hemisphere summer, daytime hours should be diurnal."""
        # Buenos Aires in December (summer) at noon
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Buenos Aires Summer",
            year=1990,
            month=12,
            day=15,
            hour=12,
            minute=0,
            lat=-34.6,
            lng=-58.4,
            tz_str="America/Argentina/Buenos_Aires",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.is_diurnal is True

    def test_southern_hemisphere_winter_night(self):
        """In southern hemisphere winter at midnight, should be nocturnal."""
        # Buenos Aires in June (winter) at midnight
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Buenos Aires Winter",
            year=1990,
            month=6,
            day=15,
            hour=0,
            minute=0,
            lat=-34.6,
            lng=-58.4,
            tz_str="America/Argentina/Buenos_Aires",
            online=False,
            suppress_geonames_warning=True,
        )
        assert subject.is_diurnal is False

    def test_topocentric_same_as_geocentric(self):
        """Topocentric perspective should have same is_diurnal as apparent geocentric."""
        geocentric = _make_subject(12, active_points=["Sun"])
        topocentric = _make_subject(
            12,
            perspective_type="Topocentric",
            altitude=100.0,
            active_points=["Sun"],
        )
        # The difference is negligible for the Sun (parallax ~0.002°)
        assert geocentric.is_diurnal == topocentric.is_diurnal
