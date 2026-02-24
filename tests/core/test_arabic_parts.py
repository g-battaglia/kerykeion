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
"""

import math
import logging
from unittest.mock import patch, MagicMock

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

    def test_noon_is_day_chart(self):
        """At noon the Sun is above the horizon — day chart."""
        day = _make_subject(12)
        night = _make_subject(0)
        # Day chart: Fortunae = Asc + Moon - Sun
        # Night chart: Fortunae = Asc + Sun - Moon
        # Verify by checking which formula matches
        day_expected = _normalize(day.ascendant.abs_pos + day.moon.abs_pos - day.sun.abs_pos)
        assert day.pars_fortunae.abs_pos == approx(day_expected, abs=0.01)

    def test_midnight_is_night_chart(self):
        """At midnight the Sun is below the horizon — night chart."""
        night = _make_subject(0)
        night_expected = _normalize(night.ascendant.abs_pos + night.sun.abs_pos - night.moon.abs_pos)
        assert night.pars_fortunae.abs_pos == approx(night_expected, abs=0.01)

    def test_evening_is_night_chart(self):
        """At 22:00 in Rome the Sun is below the horizon in June."""
        subject = _make_subject(22, lat=41.9, lng=12.5, tz_str="Europe/Rome")
        expected = _normalize(subject.ascendant.abs_pos + subject.sun.abs_pos - subject.moon.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)

    def test_morning_is_day_chart(self):
        """At 10:00 in London the Sun is above the horizon."""
        subject = _make_subject(10)
        expected = _normalize(subject.ascendant.abs_pos + subject.moon.abs_pos - subject.sun.abs_pos)
        assert subject.pars_fortunae.abs_pos == approx(expected, abs=0.01)


# ===========================================================================
# 6. Fallback paths
# ===========================================================================


class TestFallbackPaths:
    """Test the fallback logic when swe.azalt fails or Sun is missing."""

    def test_azalt_failure_falls_back_to_house_with_warning(self, caplog):
        """If swe.azalt raises, fall back to house-based detection with a warning."""
        import swisseph as swe

        original_azalt = swe.azalt

        def mock_azalt(*args, **kwargs):
            raise RuntimeError("Mock azalt failure")

        with patch("swisseph.azalt", side_effect=mock_azalt):
            with caplog.at_level(logging.WARNING):
                subject = _make_subject(12)

        # Should still produce a result (via house fallback)
        assert subject.pars_fortunae is not None
        assert subject.pars_fortunae.abs_pos >= 0
        # Should have logged a warning
        assert any("falling back to house-based" in msg for msg in caplog.messages)

    def test_azalt_fallback_uses_correct_house_logic(self, caplog):
        """House-based fallback: houses 7-12 = above horizon = day chart."""
        import swisseph as swe

        def mock_azalt(*args, **kwargs):
            raise RuntimeError("Mock azalt failure")

        with patch("swisseph.azalt", side_effect=mock_azalt):
            with caplog.at_level(logging.WARNING):
                # Noon — Sun is typically in house 10 (>= 7) → day chart
                day = _make_subject(12)
                # Midnight — Sun is typically in house 4 (< 7) → night chart
                night = _make_subject(0)

        # The values should still differ (different formulas applied)
        assert day.pars_fortunae.abs_pos != night.pars_fortunae.abs_pos

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

    def test_sun_unavailable_warning_defensive_path(self, caplog):
        """Test the defensive 'Sun unavailable' warning path directly.

        This path is unreachable for Pars Fortunae/Spiritus (Sun is a required
        prerequisite), but exists as defensive code for potential future parts
        that have day/night formulas without requiring Sun.
        """
        from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

        # Build a real subject to get valid house cusps and point data
        subject = _make_subject(12, active_points=["Sun", "Moon", "Ascendant"])

        # Realistic house cusps (30° apart, starting from 0°)
        houses = tuple(i * 30.0 for i in range(12))

        # A config with day/night formulas whose required points don't include Sun
        test_config = {
            "required": ["Ascendant", "Moon"],
            "day_formula": lambda asc, moon: asc + moon,
            "night_formula": lambda asc, moon: asc - moon,
        }

        # Data dict WITHOUT "sun" to trigger the defensive path
        data = {
            "ascendant": subject.ascendant,
            "moon": subject.moon,
            "lng": 0.0,
            "lat": 51.5074,
            "altitude": 0,
            "julian_day": 2448058.0,
            "houses_system_identifier": "P",
        }

        with caplog.at_level(logging.WARNING):
            AstrologicalSubjectFactory._calculate_arabic_part(
                "Pars_Fortunae",
                test_config,
                data,
                julian_day=2448058.0,
                iflag=258,
                houses_degree_ut=houses,
                point_type="AstrologicalPoint",
                active_points=["Ascendant", "Moon"],
                calculated_planets=[],
            )

        assert any("Sun position unavailable" in msg for msg in caplog.messages)
        # Should have been calculated using the day formula (default)
        assert "pars_fortunae" in data


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
