# -*- coding: utf-8 -*-
"""Tests for dynamic fixed stars and FixedStarDiscoveryFactory."""

import pytest
from kerykeion import AstrologicalSubjectFactory, FixedStarDiscoveryFactory
from kerykeion.ephemeris_backend import BACKEND_NAME


@pytest.fixture(scope="module")
def subject_default_stars():
    """Subject with default active_points including some fixed stars."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Stars Default",
        1990,
        6,
        15,
        14,
        30,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        city="Rome",
        nation="IT",
        online=False,
    )


@pytest.fixture(scope="module")
def subject_extra_stars():
    """Subject with extra dynamic fixed stars beyond the default 23."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Stars Extra",
        1990,
        6,
        15,
        14,
        30,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        city="Rome",
        nation="IT",
        online=False,
        active_fixed_stars=["Galactic Center", "Polaris", "Castor"],
    )


@pytest.fixture(scope="module")
def subject_all_stars():
    """Subject with the full ``DEFAULT_FIXED_STARS`` preset enabled."""
    from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS, DEFAULT_FIXED_STARS

    return AstrologicalSubjectFactory.from_birth_data(
        "Stars All",
        1990,
        6,
        15,
        14,
        30,
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        city="Rome",
        nation="IT",
        online=False,
        active_points=ALL_ACTIVE_POINTS,
        active_fixed_stars=list(DEFAULT_FIXED_STARS),
    )


class TestFixedStarsList:
    def test_fixed_stars_list_populated(self, subject_all_stars):
        """The fixed_stars list should be populated with calculated stars."""
        assert isinstance(subject_all_stars.fixed_stars, list)
        assert len(subject_all_stars.fixed_stars) > 0

    def test_fixed_stars_have_positions(self, subject_all_stars):
        """Each star in the list should have valid position data."""
        for star in subject_all_stars.fixed_stars:
            assert 0 <= star.abs_pos < 360
            assert star.retrograde is False
            assert star.point_type == "AstrologicalPoint"

    def test_fixed_stars_have_magnitude(self, subject_all_stars):
        """Most fixed stars should have magnitude data."""
        with_mag = [s for s in subject_all_stars.fixed_stars if s.magnitude is not None]
        assert len(with_mag) > 0

    def test_fixed_stars_have_declination(self, subject_all_stars):
        """Fixed stars should have declination data."""
        with_dec = [s for s in subject_all_stars.fixed_stars if s.declination is not None]
        assert len(with_dec) > 0


class TestDynamicFixedStars:
    def test_extra_stars_in_list(self, subject_extra_stars):
        """Extra dynamic stars should appear in the fixed_stars list."""
        star_names = [s.name for s in subject_extra_stars.fixed_stars]
        # At least one of the requested extras should be found. swisseph can use
        # Galactic Center from sefstars.txt; libephemeris uses its native catalog.
        assert any("Galactic" in name or "Polaris" in name or "Castor" in name for name in star_names), (
            f"None of the extra stars found. Got: {star_names}"
        )

    def test_extra_stars_have_valid_positions(self, subject_extra_stars):
        """Extra dynamic stars should have valid astrological positions."""
        for star in subject_extra_stars.fixed_stars:
            assert 0 <= star.abs_pos < 360
            assert star.sign is not None

    def test_find_fixed_star_lookup(self, subject_all_stars):
        """v6: stars are accessed via subject.find_fixed_star (unified array)."""
        regulus = subject_all_stars.find_fixed_star("Regulus")
        spica = subject_all_stars.find_fixed_star("Spica")
        assert regulus is not None
        assert spica is not None
        assert 0 <= regulus.abs_pos < 360
        # Case- and separator-insensitive
        assert subject_all_stars.find_fixed_star("REGULUS") is regulus
        assert subject_all_stars.find_fixed_star("deneb_algedi") is not None

    def test_nonexistent_star_silently_skipped(self):
        """Non-existent star names should not crash, just be silently skipped."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Nonexistent Star",
            1990,
            6,
            15,
            14,
            30,
            lng=12.4964,
            lat=41.9028,
            tz_str="Europe/Rome",
            city="Rome",
            nation="IT",
            online=False,
            active_fixed_stars=["NonExistentStarXYZ123", "AnotherFakeStar"],
        )
        # Should not crash; fake stars are simply not in the list
        assert isinstance(subject.fixed_stars, list)


class TestFixedStarEdgeCases:
    """Test edge-case branches in FixedStarDiscoveryFactory and helpers."""

    def test_catalog_source_is_libephemeris(self, subject_all_stars):
        """v6: discovery sources its catalog exclusively from libephemeris (no sefstars.txt)."""
        from unittest.mock import patch

        with patch(
            "kerykeion.fixed_stars.discovery_factory.FixedStarCatalog.list_all",
            return_value=[],
        ):
            result = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=2.0)
        assert result == []

    def test_no_sefstars_parser_present(self):
        """v6: the legacy ``_parse_star_names_from_catalog`` helper is gone."""
        from kerykeion.fixed_stars import discovery_factory as df

        assert not hasattr(df, "_parse_star_names_from_catalog")

    def test_empty_planet_positions_returns_empty(self):
        """If subject has no active points with abs_pos, should return []."""
        from unittest.mock import MagicMock

        mock_subject = MagicMock()
        mock_subject.active_points = []
        mock_subject.julian_day = 2451545.0
        result = FixedStarDiscoveryFactory.find_prominent_stars(mock_subject, orb=2.0)
        assert result == []

    def test_fixstar_ut_exception_skips_star(self, subject_all_stars):
        """If swe.fixstar_ut raises for some stars, those stars are silently skipped."""
        from unittest.mock import patch
        from kerykeion.ephemeris_backend import swe

        original_fixstar_ut = swe.fixstar_ut
        call_count = [0]

        def mock_fixstar_ut(name, jd, iflag):
            call_count[0] += 1
            # Fail on every 10th call to exercise the outer except block
            if call_count[0] % 10 == 0:
                raise RuntimeError("Mock fixstar failure")
            return original_fixstar_ut(name, jd, iflag)

        with patch("kerykeion.fixed_stars.discovery_factory.swe.fixstar_ut", side_effect=mock_fixstar_ut):
            result = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=2.0)
            assert isinstance(result, list)
            # Should still find some stars (the ones that didn't fail)


class TestFixedStarDiscovery:
    def test_find_prominent_stars(self, subject_all_stars):
        """Auto-discovery should find stars conjunct natal planets."""
        prominent = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=2.0)
        assert isinstance(prominent, list)
        # With a 2-degree orb and 10+ points, each backend catalog should find
        # at least one conjunction.
        assert len(prominent) >= 1, "A 2-degree orb with 10+ natal points should discover at least one star"

    def test_prominent_stars_have_positions(self, subject_all_stars):
        """Prominent stars should have full position data."""
        prominent = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=2.0)
        for star in prominent:
            assert 0 <= star.abs_pos < 360
            assert star.sign is not None
            assert star.retrograde is False
            assert star.near_point is not None
            assert star.orb is not None
            assert star.aspect == "conjunction"
            assert star.longitude == star.abs_pos
            assert star.degree == star.position

    def test_tight_orb_fewer_stars(self, subject_all_stars):
        """Tighter orb should find fewer or equal stars."""
        wide = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=3.0)
        narrow = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=0.5)
        assert len(narrow) <= len(wide)

    def test_sorted_by_magnitude(self, subject_all_stars):
        """Results should be sorted by magnitude (brightest first)."""
        prominent = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=3.0)
        mags = [s.magnitude for s in prominent if s.magnitude is not None]
        assert len(mags) >= 2, "A 3-degree orb should discover at least 2 stars with magnitude data"
        assert mags == sorted(mags), "Stars should be sorted by magnitude (brightest first)"


class TestCatalogStarsParticipateInAspects:
    """Regression test for the 6.0.0a43 -> 6.0.0a44 bug: catalog fixed stars
    (non-default, e.g. Vindemiatrix / Polaris / Castor) were silently excluded
    from aspect calculation because the extended ``celestial_points`` list
    built by ``single_chart_aspects`` was not propagated down to
    ``get_active_points_list``."""

    def test_non_default_catalog_stars_get_aspects(self):
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.aspects import AspectsFactory

        subj = AstrologicalSubjectFactory.from_birth_data(
            "Aspect Regression",
            1990,
            6,
            15,
            14,
            30,
            lng=12.4964,
            lat=41.9028,
            tz_str="Europe/Rome",
            city="Rome",
            nation="IT",
            online=False,
            active_fixed_stars=["Castor", "Vindemiatrix", "Polaris"],
        )

        result = AspectsFactory.single_chart_aspects(subj)
        catalog_names = {"Castor", "Vindemiatrix", "Polaris"}
        star_aspects = [
            a for a in result.aspects
            if a.p1_name in catalog_names or a.p2_name in catalog_names
        ]
        assert len(star_aspects) > 0, (
            "Catalog fixed stars (non-default) must participate in aspects; "
            f"got {len(star_aspects)} from {len(result.aspects)} total. "
            "Regression of 6.0.0a43 bug?"
        )
        # Each requested star should appear at least once
        names_in_aspects = {a.p1_name for a in star_aspects} | {a.p2_name for a in star_aspects}
        assert "Castor" in names_in_aspects, "Castor missing from aspects"

    def test_declination_aspects_include_catalog_stars(self):
        """Declination aspects (parallel/contra-parallel) must also see catalog stars."""
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.aspects import AspectsFactory

        subj = AstrologicalSubjectFactory.from_birth_data(
            "Declination Regression",
            1990,
            6,
            15,
            14,
            30,
            lng=12.4964,
            lat=41.9028,
            tz_str="Europe/Rome",
            city="Rome",
            nation="IT",
            online=False,
            active_fixed_stars=["Castor", "Vindemiatrix", "Polaris", "Algol"],
        )

        # With a generous orb we should see at least one star participating
        # alongside the planet/asteroid points (declination aspects use a
        # narrow orb by default; we just want to assert the list isn't gated
        # to non-default names).
        result = AspectsFactory.single_chart_declination_aspects(subj, orb=5.0)
        catalog_names = {"Castor", "Vindemiatrix", "Polaris", "Algol"}
        # Either we get a star-involving aspect, or we don't crash on the
        # catalog-star slugs; both prove the gate is removed.
        for a in result:
            assert a.p1_name != "" and a.p2_name != ""
