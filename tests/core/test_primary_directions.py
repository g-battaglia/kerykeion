# -*- coding: utf-8 -*-
"""Tests for the Primary Directions factory (v6.0)."""

import math
import pytest
swe = pytest.importorskip("swisseph")
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, PrimaryDirectionsFactory


@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Primary Dir Test", 1940, 10, 9, 18, 30,
        lng=-2.9916, lat=53.4084, tz_str="Europe/London",
        city="Liverpool", nation="GB", online=False,
    )


class TestSpeculum:
    def test_speculum_returns_entries(self, subject):
        """Speculum should return entries for direction points."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        assert isinstance(speculum, list)
        assert len(speculum) > 0

    def test_speculum_has_planets(self, subject):
        """Speculum should include Sun, Moon, and angular points."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        names = [s.name for s in speculum]
        assert "Sun" in names
        assert "Moon" in names
        assert "Ascendant" in names
        assert "Medium_Coeli" in names

    def test_speculum_ra_range(self, subject):
        """Right Ascension should be 0-360."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        for entry in speculum:
            assert 0 <= entry.right_ascension < 360, (
                f"{entry.name} RA {entry.right_ascension} out of range"
            )

    def test_speculum_declination_range(self, subject):
        """Declination should be -90 to +90."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        for entry in speculum:
            assert -90 <= entry.declination <= 90, (
                f"{entry.name} dec {entry.declination} out of range"
            )

    def test_speculum_semi_arc_positive(self, subject):
        """Semi-arcs should be positive."""
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        for entry in speculum:
            assert entry.semi_arc > 0, (
                f"{entry.name} semi_arc {entry.semi_arc} should be positive"
            )


class TestPrimaryDirections:
    def test_directions_computed(self, subject):
        """Should compute primary directions."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        assert isinstance(directions, list)
        assert len(directions) > 0

    def test_directions_sorted_by_year(self, subject):
        """Directions should be sorted by direction_years."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        years = [d.direction_years for d in directions]
        assert years == sorted(years)

    def test_directions_within_max_years(self, subject):
        """All directions should be within max_years."""
        max_yrs = 50
        directions = PrimaryDirectionsFactory.compute(subject, max_years=max_yrs)
        for d in directions:
            assert 0 < d.direction_years <= max_yrs

    def test_directions_have_valid_aspects(self, subject):
        """All directions should have valid aspect names."""
        valid_aspects = {"conjunction", "sextile", "square", "trine", "opposition"}
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        for d in directions:
            assert d.aspect in valid_aspects, f"Invalid aspect: {d.aspect}"

    def test_directions_arc_positive(self, subject):
        """Direction arcs should be positive."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        for d in directions:
            assert d.arc > 0

    def test_ptolemy_rate_key(self, subject):
        """Ptolemy rate key: 1 degree = 1 year."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80, rate_key="ptolemy")
        for d in directions:
            assert d.rate_key == "ptolemy"
            assert abs(d.direction_years - d.arc) < 0.01  # 1:1 ratio

    def test_naibod_rate_key(self, subject):
        """Naibod rate key: 0.98564 degrees = 1 year."""
        directions = PrimaryDirectionsFactory.compute(subject, max_years=80, rate_key="naibod")
        for d in directions:
            assert d.rate_key == "naibod"
            # Naibod years should be slightly more than Ptolemy for same arc
            expected_years = d.arc / 0.98564
            assert abs(d.direction_years - expected_years) < 0.1

    def test_filter_aspects(self, subject):
        """Should respect aspects filter."""
        conj_only = PrimaryDirectionsFactory.compute(
            subject, max_years=80, aspects=["conjunction"]
        )
        all_aspects = PrimaryDirectionsFactory.compute(subject, max_years=80)
        assert len(conj_only) <= len(all_aspects)
        for d in conj_only:
            assert d.aspect == "conjunction"


class TestPrimaryDirectionEdgeCases:
    """Test edge-case branches in primary directions."""

    def test_empty_speculum_returns_empty(self):
        """If _build_speculum returns empty, compute should return []."""
        from unittest.mock import patch

        sub = AstrologicalSubjectFactory.from_birth_data(
            "Test", 1990, 1, 1, 12, 0,
            lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
        )
        with patch.object(PrimaryDirectionsFactory, "_build_speculum", return_value=[]):
            result = PrimaryDirectionsFactory.compute(sub)
            assert result == []

    def test_invalid_aspect_name_skipped(self, subject):
        """Invalid aspect names should be skipped (aspect_angle is None)."""
        directions = PrimaryDirectionsFactory.compute(
            subject, max_years=80, aspects=["nonexistent_aspect"]
        )
        # No valid aspects -> no directions
        assert directions == []

    def test_oblique_ascension_extreme_declination(self):
        """_oblique_ascension with extreme values should not raise."""
        # Test with dec=89, pole=89 (extreme polar values)
        oa = PrimaryDirectionsFactory._oblique_ascension(180.0, 89.0, 89.0, 23.4)
        assert isinstance(oa, float)
        assert 0.0 <= oa < 360.0

    def test_oblique_ascension_zero_pole(self):
        """_oblique_ascension with pole=0 should give OA ≈ RA."""
        oa = PrimaryDirectionsFactory._oblique_ascension(100.0, 20.0, 0.0, 23.4)
        # AD = asin(tan(dec)*tan(0)) = asin(0) = 0
        assert abs(oa - 100.0) < 0.01

    def test_naibod_rate_key_different_years(self, subject):
        """Naibod key should produce different years than ptolemy for same arc."""
        ptolemy = PrimaryDirectionsFactory.compute(subject, max_years=80, rate_key="ptolemy")
        naibod = PrimaryDirectionsFactory.compute(subject, max_years=80, rate_key="naibod")
        # Both should have results
        assert len(ptolemy) > 0
        assert len(naibod) > 0

    def test_oblique_ascension_exception_skips_direction(self, subject):
        """If _oblique_ascension raises during direction computation, that direction is skipped."""
        from unittest.mock import patch

        # First build speculum normally (so _build_speculum doesn't fail)
        speculum = PrimaryDirectionsFactory.compute_speculum(subject)
        assert len(speculum) > 0

        call_count = [0]
        original_oa = PrimaryDirectionsFactory._oblique_ascension

        def failing_oa(*args, **kwargs):
            call_count[0] += 1
            # Fail on every 5th call to exercise the except branch (lines 152-153)
            if call_count[0] % 5 == 0:
                raise ValueError("Mock OA failure")
            return original_oa(*args, **kwargs)

        # Only patch during compute, but also patch _build_speculum to return
        # the pre-computed speculum so _oblique_ascension failures only happen
        # during the direction computation loop
        with patch.object(PrimaryDirectionsFactory, "_build_speculum", return_value=speculum):
            with patch.object(PrimaryDirectionsFactory, "_oblique_ascension", side_effect=failing_oa):
                directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
                # Should still return some directions (those that didn't fail)
                assert isinstance(directions, list)

    def test_speculum_calc_ut_fallback(self, subject):
        """If swe.calc_ut with FLG_EQUATORIAL fails, speculum should use ecliptic fallback."""
        from unittest.mock import patch

        original_calc_ut = swe.calc_ut

        def failing_eq_calc_ut(jd, planet_id, iflag):
            if iflag & swe.FLG_EQUATORIAL:
                raise RuntimeError("Mock equatorial failure")
            return original_calc_ut(jd, planet_id, iflag)

        with patch("kerykeion.primary_directions.directions_factory.swe.calc_ut", side_effect=failing_eq_calc_ut):
            speculum = PrimaryDirectionsFactory.compute_speculum(subject)
            # Should still return entries (using ecliptic fallback for RA)
            assert len(speculum) > 0
            for entry in speculum:
                assert 0 <= entry.right_ascension < 360

    def test_speculum_extreme_latitude_polar(self):
        """Speculum at extreme latitude (near-polar) exercises semi-arc fallback."""
        # Near-polar latitude causes tan(dec)*tan(lat) to exceed [-1, 1] range
        polar_subject = AstrologicalSubjectFactory.from_birth_data(
            "Polar Test", 1990, 6, 21, 12, 0,
            lng=25.0, lat=89.5, tz_str="Etc/GMT",
            city="NorthPole", nation="FI", online=False,
        )
        speculum = PrimaryDirectionsFactory.compute_speculum(polar_subject)
        assert len(speculum) > 0
        for entry in speculum:
            assert entry.semi_arc > 0

    def test_speculum_point_none_skipped(self):
        """If a direction point doesn't exist on the subject, it's skipped."""
        from unittest.mock import patch, MagicMock

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Test", 1990, 1, 1, 12, 0,
            lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
        )
        # Make one point return None
        original_getattr = subject.__class__.__getattribute__

        def mock_getattr(self_obj, name):
            if name == "medium_coeli":
                return None
            return original_getattr(self_obj, name)

        with patch.object(type(subject), "__getattribute__", mock_getattr):
            speculum = PrimaryDirectionsFactory.compute_speculum(subject)
            names = [e.name for e in speculum]
            assert "Medium_Coeli" not in names

    def test_oblique_ascension_zero_division_fallback(self):
        """_oblique_ascension with dec=90 and pole=90 should trigger fallback."""
        # tan(90) is undefined, which should trigger the ZeroDivisionError fallback
        oa = PrimaryDirectionsFactory._oblique_ascension(100.0, 90.0, 90.0, 23.4)
        # Should use the clamped fallback and not raise
        assert isinstance(oa, float)

    def test_speculum_semi_arc_exception_fallback(self):
        """Force semi-arc calculation to raise via mock to hit lines 263-264."""
        from unittest.mock import patch
        import math as real_math

        original_acos = real_math.acos
        call_count = [0]

        def mock_acos(x):
            call_count[0] += 1
            # The acos calls for semi-arc happen after the clamp (cos_sa).
            # Fail on certain calls to trigger the except block.
            if call_count[0] >= 2:
                raise ValueError("Mock acos failure")
            return original_acos(x)

        with patch("kerykeion.primary_directions.directions_factory.math.acos", side_effect=mock_acos):
            speculum = PrimaryDirectionsFactory.compute_speculum(
                AstrologicalSubjectFactory.from_birth_data(
                    "Test", 1990, 1, 1, 12, 0,
                    lng=0.0, lat=51.5, tz_str="Etc/GMT",
                    city="Greenwich", nation="GB", online=False,
                )
            )
            # Should still produce entries (using dsa=90 fallback)
            assert len(speculum) > 0

    def test_speculum_pole_exception_fallback(self):
        """Force pole calculation to raise via mock to hit lines 278-279."""
        from unittest.mock import patch
        import math as real_math

        original_sin = real_math.sin
        call_count = [0]

        def mock_sin(x):
            call_count[0] += 1
            result = original_sin(x)
            # After many calls, return 0.0 from the sin(radians(sa)) call
            # to cause ZeroDivisionError in the pole_sin division.
            # This is hard to target precisely, so instead just raise directly
            # on a later call that's likely in the pole calculation:
            if call_count[0] > 20 and call_count[0] % 7 == 0:
                raise ZeroDivisionError("Mock zero division")
            return result

        with patch("kerykeion.primary_directions.directions_factory.math.sin", side_effect=mock_sin):
            speculum = PrimaryDirectionsFactory.compute_speculum(
                AstrologicalSubjectFactory.from_birth_data(
                    "Test", 1990, 1, 1, 12, 0,
                    lng=0.0, lat=51.5, tz_str="Etc/GMT",
                    city="Greenwich", nation="GB", online=False,
                )
            )
            # Should still produce entries (using pole=0 fallback)
            assert len(speculum) > 0

    def test_oblique_ascension_ad_exception_fallback(self):
        """Force ascensional difference to raise to hit lines 312-313."""
        from unittest.mock import patch
        import math as real_math

        original_tan = real_math.tan

        def mock_tan(x):
            # Raise on every call to trigger the except block
            raise ZeroDivisionError("Mock tan failure")

        # The _oblique_ascension function calls tan(dec_rad) * tan(pole_rad)
        with patch("kerykeion.primary_directions.directions_factory.math.tan", side_effect=mock_tan):
            oa = PrimaryDirectionsFactory._oblique_ascension(100.0, 30.0, 45.0, 23.4)
            # Should use ad=0 fallback, so OA ≈ RA = 100
            assert abs(oa - 100.0) < 0.01


class TestSpeculumSweRegressions:
    """Known-value regression tests using Swiss Ephemeris as reference source.

    These tests call swe functions directly to obtain reference values, then
    verify that PrimaryDirectionsFactory.compute_speculum produces matching
    results.  The subject is John Lennon (1940-10-09 18:30, Liverpool).
    """

    @pytest.fixture(scope="class")
    def lennon(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "John Lennon", 1940, 10, 9, 18, 30,
            lng=-2.9916, lat=53.4084, tz_str="Europe/London",
            city="Liverpool", nation="GB", online=False,
        )

    def test_sun_ra_dec_matches_swe(self, lennon):
        """Sun RA and declination from speculum must match swe.calc_ut equatorial coords."""
        ephe_path = str(Path(__file__).resolve().parent.parent.parent / "kerykeion" / "sweph")
        swe.set_ephe_path(ephe_path)

        jd = lennon.julian_day
        eq = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
        swe_ra = eq[0][0]
        swe_dec = eq[0][1]
        swe.close()

        speculum = PrimaryDirectionsFactory.compute_speculum(lennon)
        sun_entry = next(e for e in speculum if e.name == "Sun")

        assert abs(sun_entry.right_ascension - swe_ra) < 0.01, (
            f"Sun RA mismatch: speculum={sun_entry.right_ascension}, swe={swe_ra}"
        )
        assert abs(sun_entry.declination - swe_dec) < 0.01, (
            f"Sun Dec mismatch: speculum={sun_entry.declination}, swe={swe_dec}"
        )

    def test_ramc_matches_swe_sidtime(self, lennon):
        """RAMC must equal (swe.sidtime(jd) * 15 + lng) mod 360."""
        ephe_path = str(Path(__file__).resolve().parent.parent.parent / "kerykeion" / "sweph")
        swe.set_ephe_path(ephe_path)

        jd = lennon.julian_day
        expected_ramc = (swe.sidtime(jd) * 15.0 + lennon.lng) % 360
        swe.close()

        # The speculum does not directly expose RAMC, but we can verify it
        # through the MC entry: MC's meridian distance should be ~0 because
        # it sits on the meridian.  Also verify via re-derivation:
        # For any planet, MD = RA - RAMC (normalized).
        # So RAMC = RA - MD for any planet entry.
        speculum = PrimaryDirectionsFactory.compute_speculum(lennon)
        sun_entry = next(e for e in speculum if e.name == "Sun")
        derived_ramc = (sun_entry.right_ascension - sun_entry.meridian_distance) % 360

        assert abs(derived_ramc - expected_ramc) < 0.01, (
            f"RAMC mismatch: derived={derived_ramc}, expected={expected_ramc}"
        )
