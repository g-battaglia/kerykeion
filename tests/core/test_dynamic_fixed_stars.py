# -*- coding: utf-8 -*-
"""Tests for dynamic fixed stars and FixedStarDiscoveryFactory."""

import pytest
from kerykeion import AstrologicalSubjectFactory, FixedStarDiscoveryFactory


@pytest.fixture(scope="module")
def subject_default_stars():
    """Subject with default active_points including some fixed stars."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Stars Default", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


@pytest.fixture(scope="module")
def subject_extra_stars():
    """Subject with extra dynamic fixed stars beyond the default 23."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Stars Extra", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        active_fixed_stars=["Galactic Center", "Polaris", "Castor"],
    )


@pytest.fixture(scope="module")
def subject_all_stars():
    """Subject with all default active_points (includes 23 hardcoded stars)."""
    from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS
    return AstrologicalSubjectFactory.from_birth_data(
        "Stars All", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        active_points=ALL_ACTIVE_POINTS,
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
        # At least one of the requested extras should be found
        # (Galactic Center is guaranteed to be in sefstars.txt)
        assert any("Galactic" in name or "Polaris" in name or "Castor" in name
                    for name in star_names), (
            f"None of the extra stars found. Got: {star_names}"
        )

    def test_extra_stars_have_valid_positions(self, subject_extra_stars):
        """Extra dynamic stars should have valid astrological positions."""
        for star in subject_extra_stars.fixed_stars:
            assert 0 <= star.abs_pos < 360
            assert star.sign is not None

    def test_default_named_fields_still_work(self, subject_all_stars):
        """Default hardcoded star fields should still be populated."""
        assert subject_all_stars.regulus is not None
        assert subject_all_stars.spica is not None
        assert 0 <= subject_all_stars.regulus.abs_pos < 360


    def test_nonexistent_star_silently_skipped(self):
        """Non-existent star names should not crash, just be silently skipped."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Nonexistent Star", 1990, 6, 15, 14, 30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            active_fixed_stars=["NonExistentStarXYZ123", "AnotherFakeStar"],
        )
        # Should not crash; fake stars are simply not in the list
        assert isinstance(subject.fixed_stars, list)


class TestFixedStarDiscovery:
    def test_find_prominent_stars(self, subject_all_stars):
        """Auto-discovery should find stars conjunct natal planets."""
        prominent = FixedStarDiscoveryFactory.find_prominent_stars(
            subject_all_stars, orb=2.0
        )
        assert isinstance(prominent, list)
        # With a 2-degree orb and 10+ planets, we should find at least a few stars
        # (there are ~1000 stars spread across 360 degrees)
        assert len(prominent) >= 1, "A 2-degree orb with 10+ natal points should discover at least one star"

    def test_prominent_stars_have_positions(self, subject_all_stars):
        """Prominent stars should have full position data."""
        prominent = FixedStarDiscoveryFactory.find_prominent_stars(
            subject_all_stars, orb=2.0
        )
        for star in prominent:
            assert 0 <= star.abs_pos < 360
            assert star.sign is not None
            assert star.retrograde is False

    def test_tight_orb_fewer_stars(self, subject_all_stars):
        """Tighter orb should find fewer or equal stars."""
        wide = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=3.0)
        narrow = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=0.5)
        assert len(narrow) <= len(wide)

    def test_sorted_by_magnitude(self, subject_all_stars):
        """Results should be sorted by magnitude (brightest first)."""
        prominent = FixedStarDiscoveryFactory.find_prominent_stars(
            subject_all_stars, orb=3.0
        )
        mags = [s.magnitude for s in prominent if s.magnitude is not None]
        assert len(mags) >= 2, "A 3-degree orb should discover at least 2 stars with magnitude data"
        assert mags == sorted(mags), "Stars should be sorted by magnitude (brightest first)"
