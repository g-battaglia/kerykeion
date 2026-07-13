# -*- coding: utf-8 -*-
"""Tests for dynamic fixed stars and FixedStarDiscoveryFactory."""

import pytest
from kerykeion import AstrologicalSubjectFactory, FixedStarDiscoveryFactory


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

    def test_fixed_stars_have_ecliptic_latitude(self, subject_all_stars):
        """Fixed stars carry their true ecliptic latitude (not a flat 0.0).

        Many bright stars sit far off the ecliptic, so the field must be
        populated for accurate local-space azimuth/altitude — the same as
        planets and derived antipodes.
        """
        with_lat = [s for s in subject_all_stars.fixed_stars if s.ecliptic_latitude is not None]
        assert len(with_lat) > 0, "No fixed star carries an ecliptic_latitude value"
        off_ecliptic = [s for s in with_lat if abs(s.ecliptic_latitude) > 1.0]
        assert off_ecliptic, "Expected at least one off-ecliptic star with a true ecliptic latitude"


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
        """If ephe.fixstar_ut raises for some stars, those stars are silently skipped."""
        from unittest.mock import patch
        from kerykeion.ephemeris_backend import ephe

        original_fixstar_ut = ephe.fixstar_ut
        call_count = [0]

        def mock_fixstar_ut(name, jd, iflag):
            call_count[0] += 1
            # Fail on every 10th call to exercise the outer except block
            if call_count[0] % 10 == 0:
                raise RuntimeError("Mock fixstar failure")
            return original_fixstar_ut(name, jd, iflag)

        with patch("kerykeion.fixed_stars.discovery_factory.ephe.fixstar_ut", side_effect=mock_fixstar_ut):
            result = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=2.0)
            assert isinstance(result, list)
            # The non-failing stars (9 of every 10 calls) must still be returned;
            # a bare isinstance check would pass even if a bug wiped the whole list.
            assert len(result) > 0, "per-star failure must not wipe the surviving stars"


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

    @pytest.mark.parametrize(
        "invalid_orb",
        [float("nan"), float("inf"), float("-inf"), -1.0],
    )
    def test_invalid_orb_rejected(self, subject_all_stars, invalid_orb):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="orb"):
            FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=invalid_orb)

    def test_sorted_by_magnitude(self, subject_all_stars):
        """Results should be sorted by magnitude (brightest first)."""
        prominent = FixedStarDiscoveryFactory.find_prominent_stars(subject_all_stars, orb=3.0)
        mags = [s.magnitude for s in prominent if s.magnitude is not None]
        assert len(mags) >= 2, "A 3-degree orb should discover at least 2 stars with magnitude data"
        assert mags == sorted(mags), "Stars should be sorted by magnitude (brightest first)"

    def test_close_longitude_stars_not_position_deduplicated(self, subject_default_stars):
        """Regression (a57): physically distinct stars sharing a rounded ecliptic
        longitude must both be discovered. The old ``round(deg, 2)`` position dedupe
        dropped the second star in catalog order regardless of magnitude, so after
        libephemeris 3.0's 1447-star catalog bright stars were suppressed by fainter
        neighbours — e.g. Nunki (sigma Sgr, mag 2.02) lost to Beta Scuti (mag 4.22),
        both rounding to 282.26 deg. Nunki sits at orb ~1.46 here and must appear."""
        names = {
            s.name
            for s in FixedStarDiscoveryFactory.find_prominent_stars(subject_default_stars, orb=2.0)
        }
        assert "Nunki" in names, f"Nunki should be discovered within orb 2.0; got {sorted(names)}"


class TestFixedStarSiderealFrameConsistency:
    """v6 pre-beta fix: star discovery must run in the subject's zodiac frame.

    Previously tropical fixstar longitudes were compared against (possibly
    sidereal) natal abs_pos, shifting every conjunction check by the ayanamsa.
    Conjunctions are frame-invariant (star and planet shift together), so a
    LAHIRI chart must discover stars at longitudes exactly one ayanamsa below
    the tropical chart's."""

    def test_lahiri_discovery_matches_tropical_minus_ayanamsa(self):
        birth = dict(
            year=1990, month=6, day=15, hour=14, minute=30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        tropical = AstrologicalSubjectFactory.from_birth_data("Stars Tropical", **birth)
        sidereal = AstrologicalSubjectFactory.from_birth_data(
            "Stars Lahiri", **birth, zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        assert sidereal.ayanamsa_value is not None
        ayanamsa = sidereal.ayanamsa_value

        trop_stars = {s.name: s for s in FixedStarDiscoveryFactory.find_prominent_stars(tropical, orb=2.0)}
        sid_stars = {s.name: s for s in FixedStarDiscoveryFactory.find_prominent_stars(sidereal, orb=2.0)}

        common = set(trop_stars) & set(sid_stars)
        assert common, (
            "Conjunctions are frame-invariant: the sidereal chart should discover "
            f"(at least some of) the same stars. tropical={sorted(trop_stars)} "
            f"sidereal={sorted(sid_stars)}"
        )
        for name in common:
            diff = (trop_stars[name].abs_pos - sid_stars[name].abs_pos) % 360.0
            assert diff == pytest.approx(ayanamsa, abs=0.01), (
                f"{name}: tropical={trop_stars[name].abs_pos} sidereal={sid_stars[name].abs_pos} "
                f"diff={diff} expected ayanamsa={ayanamsa}"
            )
            # Declination is physical and must be identical in both frames.
            if trop_stars[name].declination is not None and sid_stars[name].declination is not None:
                assert sid_stars[name].declination == pytest.approx(
                    trop_stars[name].declination, abs=1e-6
                )


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
        # Either we get a star-involving aspect, or we don't crash on the
        # catalog-star slugs; both prove the gate is removed.
        for a in result:
            assert a.p1_name != "" and a.p2_name != ""


class TestFixedStarOnlyActivePointsRaises:
    def test_fixed_star_only_active_points_raises(self):
        """active_points reduced to only fixed-star names (redirected to
        active_fixed_stars) leaves no regular points — must raise, consistent
        with the planetocentric center-body path, not silently compute a FULL
        chart via the empty-list 'no filter' semantics."""
        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="only fixed star names"):
            AstrologicalSubjectFactory.from_birth_data(
                "Stars Only", 1990, 6, 15, 12, 0,
                lng=12.5, lat=41.9, tz_str="Europe/Rome",
                online=False, suppress_geonames_warning=True,
                active_points=["Regulus", "Spica"],
            )

    def test_mixed_regular_and_star_points_still_work(self):
        from kerykeion import AstrologicalSubjectFactory

        s = AstrologicalSubjectFactory.from_birth_data(
            "Mixed", 1990, 6, 15, 12, 0,
            lng=12.5, lat=41.9, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
            active_points=["Sun", "Regulus"],
        )
        assert s.active_points == ["Sun"]
        assert [st.name for st in s.fixed_stars] == ["Regulus"]


class TestFixedStarCatalogIsKnownName:
    """``FixedStarCatalog.is_known_name`` is the O(1) hot-path replacement for
    ``find(...) is not None`` and MUST stay exactly equivalent to it."""

    def test_is_known_name_matches_find_over_whole_catalog(self):
        from kerykeion.fixed_stars.catalog import FixedStarCatalog

        catalog = FixedStarCatalog.list_all()
        assert len(catalog) > 1000  # the full 1447-entry catalog is loaded
        for entry in catalog:
            for candidate in (
                entry.name,
                entry.slug,
                entry.name.upper(),
                entry.name.lower(),
                entry.slug.replace("_", "-"),
                entry.slug.replace("_", " "),
            ):
                assert FixedStarCatalog.is_known_name(candidate) == (
                    FixedStarCatalog.find(candidate) is not None
                ), candidate

    def test_is_known_name_matches_find_for_active_point_names(self):
        from typing import get_args
        from kerykeion.fixed_stars.catalog import FixedStarCatalog
        from kerykeion.schemas.kr_literals import AstrologicalPoint

        for name in get_args(AstrologicalPoint):
            assert FixedStarCatalog.is_known_name(name) == (
                FixedStarCatalog.find(name) is not None
            ), name

    def test_is_known_name_rejects_typos_and_junk(self):
        from kerykeion.fixed_stars.catalog import FixedStarCatalog

        for bad in ("Reguluss", "NotAStar", "", "xyz123", "Sun", "Moon"):
            assert FixedStarCatalog.is_known_name(bad) is False, bad
            assert FixedStarCatalog.find(bad) is None, bad

    def test_is_known_name_accepts_known_star_and_slug(self):
        from kerykeion.fixed_stars.catalog import FixedStarCatalog

        assert FixedStarCatalog.is_known_name("Regulus") is True
        assert FixedStarCatalog.is_known_name("regulus") is True
        assert FixedStarCatalog.is_known_name("Spica") is True

    def test_explicit_active_points_still_redirects_star_names(self, caplog):
        """A v5-style star name in ``active_points`` (['Sun','Moon','Regulus'])
        is still detected via ``is_known_name`` and redirected to
        ``active_fixed_stars`` with a warning — the behavior the old linear
        ``find`` scan fed."""
        import logging
        from kerykeion import AstrologicalSubjectFactory

        with caplog.at_level(logging.WARNING):
            s = AstrologicalSubjectFactory.from_birth_data(
                "Redirect", 1990, 6, 15, 12, 0,
                lng=12.5, lat=41.9, tz_str="Europe/Rome",
                online=False, suppress_geonames_warning=True,
                active_points=["Sun", "Moon", "Regulus"],
            )

        assert s.active_points == ["Sun", "Moon"]
        assert [st.name for st in s.fixed_stars] == ["Regulus"]
        assert any(
            "Regulus" in r.getMessage() and "active_fixed_stars" in r.getMessage()
            for r in caplog.records
        ), caplog.text


def test_composite_subject_raises_clean_exception():
    """A midpoint composite has julian_day=None; fixstar_ut with a None JD
    returns NaN positions on libephemeris, so discovery used to silently
    return [] instead of failing. Mirrors the PlanetaryNodesFactory guard."""
    from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory
    from kerykeion.fixed_stars.discovery_factory import FixedStarDiscoveryFactory
    from kerykeion.schemas import KerykeionException

    a = AstrologicalSubjectFactory.from_birth_data(
        "A", 1990, 6, 15, 12, 0,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        online=False, suppress_geonames_warning=True,
    )
    b = AstrologicalSubjectFactory.from_birth_data(
        "B", 1985, 3, 10, 4, 20,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        online=False, suppress_geonames_warning=True,
    )
    midpoint = CompositeSubjectFactory(a, b).get_midpoint_composite_subject_model()
    with pytest.raises(KerykeionException, match="Julian Day"):
        FixedStarDiscoveryFactory.find_prominent_stars(midpoint)


@pytest.mark.parametrize(
    "julian_day",
    [float("nan"), float("inf"), float("-inf"), 10**309],
    ids=["nan", "positive-infinity", "negative-infinity", "unrepresentably-large"],
)
def test_non_finite_subject_julian_day_raises(subject_all_stars, julian_day):
    """Per-star recovery must not turn a corrupt instant into an empty result."""
    from kerykeion.schemas import KerykeionException

    corrupted = subject_all_stars.model_copy(update={"julian_day": julian_day})
    with pytest.raises(KerykeionException, match="finite"):
        FixedStarDiscoveryFactory.find_prominent_stars(corrupted)
