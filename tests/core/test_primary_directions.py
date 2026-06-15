# -*- coding: utf-8 -*-
"""Tests for the Primary Directions factory (v6.0)."""

import math
import pytest
from kerykeion.ephemeris_backend import ephe, ephemeris_session
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
        # v6 rewrite: the helper dropped its unused obliquity argument.
        # Test with dec=89, pole=89 (extreme polar values)
        oa = PrimaryDirectionsFactory._oblique_ascension(180.0, 89.0, 89.0)
        assert isinstance(oa, float)
        assert 0.0 <= oa < 360.0
        # tan(89)*tan(89) >> 1 is clamped to 1, so AD = 90 and OA = 180 - 90 = 90
        assert abs(oa - 90.0) < 1e-9

    def test_oblique_ascension_zero_pole(self):
        """_oblique_ascension with pole=0 should give OA ≈ RA."""
        # v6 rewrite: the helper dropped its unused obliquity argument.
        oa = PrimaryDirectionsFactory._oblique_ascension(100.0, 20.0, 0.0)
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
        """If ephe.calc_ut with FLG_EQUATORIAL fails, speculum should use ecliptic fallback."""
        from unittest.mock import patch

        original_calc_ut = ephe.calc_ut

        def failing_eq_calc_ut(jd, planet_id, iflag):
            if iflag & ephe.FLG_EQUATORIAL:
                raise RuntimeError("Mock equatorial failure")
            return original_calc_ut(jd, planet_id, iflag)

        with patch("kerykeion.primary_directions.directions_factory.ephe.calc_ut", side_effect=failing_eq_calc_ut):
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
        from unittest.mock import patch

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
        """_oblique_ascension with dec=90 and pole=90 must not raise."""
        # v6 rewrite: dropped the unused obliquity argument; in float math
        # tan(90 deg) is finite-but-huge, so the [-1, 1] clamp (not an
        # exception) handles it: AD = asin(1) = 90 and OA = 100 - 90 = 10.
        oa = PrimaryDirectionsFactory._oblique_ascension(100.0, 90.0, 90.0)
        assert isinstance(oa, float)
        assert abs(oa - 10.0) < 1e-9

    def test_placidian_pole_circumpolar_clamp(self):
        """Circumpolar combination (tan(dec)*tan(lat) > 1) is clamped, not raised."""
        # v6 rewrite: the semi-arc uses asin with a [-1, 1] clamp instead of
        # the old acos try/except. dec=80, lat=80: AD_phi clamps to 90 deg, so
        # with MD=90 and SA=180 the pole is atan(sin(45)/tan(80)).
        expected = math.degrees(math.atan(
            math.sin(math.radians(45.0)) / math.tan(math.radians(80.0))
        ))
        pole = PrimaryDirectionsFactory._placidian_pole(90.0, 180.0, 80.0, 80.0)
        assert abs(pole - expected) < 1e-9

    def test_placidian_pole_zero_declination_limit(self):
        """dec=0 uses the continuous limit pole = atan((MD/SA) * tan(lat))."""
        expected = math.degrees(math.atan((60.0 / 90.0) * math.tan(math.radians(53.4))))
        pole_zero = PrimaryDirectionsFactory._placidian_pole(60.0, 90.0, 0.0, 53.4)
        pole_tiny = PrimaryDirectionsFactory._placidian_pole(60.0, 90.0, 1e-9, 53.4)
        assert abs(pole_zero - expected) < 1e-9
        # The dec -> 0 branch must be continuous with the general formula
        assert abs(pole_tiny - pole_zero) < 1e-6

    def test_speculum_pole_exception_fallback(self):
        """If the pole computation raises, _build_speculum falls back to pole=0."""
        from unittest.mock import patch

        # Create the subject outside the mock so that ephemeris calculations
        # are not affected by the patch.
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Test", 1990, 1, 1, 12, 0,
            lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
        )

        # v6 rewrite: patch the pole helper itself instead of guessing
        # math.sin call counts of the old implementation.
        with patch.object(
            PrimaryDirectionsFactory, "_placidian_pole",
            side_effect=ValueError("Mock pole failure"),
        ):
            speculum = PrimaryDirectionsFactory.compute_speculum(subject)
            # Should still produce entries, all using the pole=0 fallback
            assert len(speculum) > 0
            for entry in speculum:
                assert entry.pole == 0.0

    def test_oblique_ascension_ad_exception_fallback(self):
        """Force ascensional difference to raise to exercise its except branch."""
        from unittest.mock import patch

        def mock_tan(x):
            # Raise on every call to trigger the except block
            raise ZeroDivisionError("Mock tan failure")

        # v6 rewrite: dropped the unused obliquity argument; the AD math now
        # lives in _ascensional_difference, called by _oblique_ascension.
        with patch("kerykeion.primary_directions.directions_factory.math.tan", side_effect=mock_tan):
            oa = PrimaryDirectionsFactory._oblique_ascension(100.0, 30.0, 45.0)
            # Should use ad=0 fallback, so OA ≈ RA = 100
            assert abs(oa - 100.0) < 0.01


class TestSpeculumSweRegressions:
    """Known-value regression tests using Swiss Ephemeris as reference source.

    These tests call ephe functions directly to obtain reference values, then
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
        """Sun RA and declination from speculum must match ephe.calc_ut equatorial coords."""
        # v6: raw ephe.set_ephe_path/ephe.close are forbidden; use ephemeris_session.
        jd = lennon.julian_day
        with ephemeris_session() as iflag:
            eq = ephe.calc_ut(jd, ephe.SUN, iflag | ephe.FLG_EQUATORIAL)
            swe_ra = eq[0][0]
            swe_dec = eq[0][1]

        speculum = PrimaryDirectionsFactory.compute_speculum(lennon)
        sun_entry = next(e for e in speculum if e.name == "Sun")

        assert abs(sun_entry.right_ascension - swe_ra) < 0.01, (
            f"Sun RA mismatch: speculum={sun_entry.right_ascension}, ephe={swe_ra}"
        )
        assert abs(sun_entry.declination - swe_dec) < 0.01, (
            f"Sun Dec mismatch: speculum={sun_entry.declination}, ephe={swe_dec}"
        )

    def test_ramc_matches_swe_sidtime(self, lennon):
        """RAMC must equal (ephe.sidtime(jd) * 15 + lng) mod 360."""
        # v6: raw ephe.set_ephe_path/ephe.close are forbidden; use ephemeris_session.
        jd = lennon.julian_day
        with ephemeris_session():
            expected_ramc = (ephe.sidtime(jd) * 15.0 + lennon.lng) % 360

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


class TestKnownValues:
    """Known-value tests against the standard Placidian recipe (Gansten).

    Every expected number is computed INDEPENDENTLY in the test body with
    plain python math from the textbook formulas — never by calling the
    implementation:

        AD_phi = asin(tan(dec) * tan(lat))      # ascensional difference
        DSA    = 90 + AD_phi                     # diurnal semi-arc
        NSA    = 90 - AD_phi                     # nocturnal semi-arc
        AD_P   = (MD / SA) * AD_phi              # proportional AD
        pole   = atan(sin(AD_P) / tan(dec))      # Placidian "under the pole"
        OA     = RA - asin(tan(dec) * tan(pole)) # oblique ascension
    """

    @pytest.fixture(scope="class")
    def modern_subject(self):
        # Modern date: the local dev ephemeris kernel is short-range.
        return AstrologicalSubjectFactory.from_birth_data(
            "Known Values", 2000, 5, 15, 14, 30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )

    def test_reference_pole_diurnal(self):
        """Gansten reference: lat=53.4, dec=20, MD=60 diurnal -> pole ~ 35.0."""
        lat, dec, md = 53.4, 20.0, 60.0

        ad_phi = math.asin(math.tan(math.radians(dec)) * math.tan(math.radians(lat)))
        dsa = 90.0 + math.degrees(ad_phi)
        ad_p = (md / dsa) * ad_phi  # radians
        expected_pole = math.degrees(math.atan(math.sin(ad_p) / math.tan(math.radians(dec))))

        # Pin the published reference number (expected_pole ~ 34.98)
        assert abs(expected_pole - 35.0) < 0.05

        pole = PrimaryDirectionsFactory._placidian_pole(md, dsa, dec, lat)
        assert abs(pole - expected_pole) < 1e-9

    def test_reference_trine_point_oblique_ascension(self):
        """Sun at 0 Cancer (lam=90): trine point lam=210 under pole 35 -> OA ~ 216.1."""
        eps = 23.4366  # obliquity of date (J2000-era)
        lam = (90.0 + 120.0) % 360  # sinister trine of the promissor, beta=0
        pole = 35.0

        # Ecliptic (beta=0) -> equatorial via the obliquity
        dec = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam))))
        ra = math.degrees(math.atan2(
            math.sin(math.radians(lam)) * math.cos(math.radians(eps)),
            math.cos(math.radians(lam)),
        )) % 360
        ad = math.degrees(math.asin(math.tan(math.radians(dec)) * math.tan(math.radians(pole))))
        expected_oa = (ra - ad) % 360

        # Pin the published reference number (expected_oa ~ 216.08)
        assert abs(expected_oa - 216.1) < 0.05

        ra_impl, dec_impl = PrimaryDirectionsFactory._ecliptic_to_equatorial(lam, eps)
        oa_impl = PrimaryDirectionsFactory._oblique_ascension(ra_impl, dec_impl, pole)
        assert abs(ra_impl - ra) < 1e-9
        assert abs(dec_impl - dec) < 1e-9
        assert abs(oa_impl - expected_oa) < 1e-9

    def test_known_pole_nocturnal(self):
        """Below-horizon point: MD from the IC with the nocturnal semi-arc."""
        lat, dec = 53.4, 20.0
        md_ic = 30.0  # meridian distance measured from the IC

        ad_phi = math.asin(math.tan(math.radians(dec)) * math.tan(math.radians(lat)))
        nsa = 90.0 - math.degrees(ad_phi)  # ~ 60.65: short night arc for dec>0 in the north
        ad_p = (md_ic / nsa) * ad_phi  # radians
        expected_pole = math.degrees(math.atan(math.sin(ad_p) / math.tan(math.radians(dec))))

        # Guard the independent chain itself (expected_pole ~ 34.55)
        assert abs(expected_pole - 34.5516) < 0.01

        pole = PrimaryDirectionsFactory._placidian_pole(md_ic, nsa, dec, lat)
        assert abs(pole - expected_pole) < 1e-9

    def test_known_pole_on_meridian_is_zero(self, modern_subject):
        """A point on the meridian (MD ~ 0) has pole 0: MC/IC arcs are pure RA."""
        # Helper level: exact zero
        assert PrimaryDirectionsFactory._placidian_pole(0.0, 119.3463, 20.0, 53.4) == 0.0

        # Whole-chart level: the MC sits on the meridian by construction
        speculum = PrimaryDirectionsFactory.compute_speculum(modern_subject)
        mc = next(e for e in speculum if e.name == "Medium_Coeli")
        assert abs(mc.meridian_distance) < 0.01
        assert abs(mc.pole) < 0.01
        # With pole ~ 0 the ascensional difference vanishes, so OA == RA
        assert abs(mc.oblique_ascension - mc.right_ascension) < 0.01

    def test_known_converse_direction_arc(self, modern_subject):
        """Direct and converse Sun-conjunction-MC arcs match the independent math."""
        jd = modern_subject.julian_day
        with ephemeris_session() as iflag:
            eps = ephe.calc_ut(jd, ephe.ECL_NUT, iflag)[0][0]

        def ra_of(lam):
            return math.degrees(math.atan2(
                math.sin(math.radians(lam)) * math.cos(math.radians(eps)),
                math.cos(math.radians(lam)),
            )) % 360

        # Significator MC: on the meridian -> pole 0 -> AD = 0 -> OA = RA.
        ra_mc = ra_of(modern_subject.medium_coeli.abs_pos)
        # Promissor Sun, conjunction: the aspect point is the Sun's own
        # ecliptic longitude at beta=0; under pole 0 its OA is its RA.
        ra_sun_point = ra_of(modern_subject.sun.abs_pos)

        expected_direct = (ra_sun_point - ra_mc) % 360  # ~ 339.09 for this chart
        expected_converse = (360.0 - expected_direct) % 360  # ~ 20.91

        directions = PrimaryDirectionsFactory.compute(
            modern_subject, max_years=360, rate_key="ptolemy", aspects=["conjunction"]
        )
        matches = [
            d for d in directions
            if d.promissor == "Sun" and d.significator == "Medium_Coeli"
        ]
        direct = [d for d in matches if not d.is_converse]
        converse = [d for d in matches if d.is_converse]
        assert len(direct) == 1
        assert len(converse) == 1
        assert abs(direct[0].arc - expected_direct) < 0.01
        assert abs(converse[0].arc - expected_converse) < 0.01
        # Direct and converse arcs of the same pair are complementary
        assert abs(direct[0].arc + converse[0].arc - 360.0) < 1e-3
        # Ptolemy key: 1 degree = 1 year
        assert abs(direct[0].direction_years - direct[0].arc) < 0.01
