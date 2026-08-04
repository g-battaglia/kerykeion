"""
Tests for the OccultationFactory.

Verifies that global and local lunar occultation searches return
well-formed OccultationModel results using the Swiss Ephemeris.
"""

import pytest
from kerykeion.ephemeris_backend import ephe, ephemeris_session

from kerykeion.occultations import OccultationFactory, OccultationModel
from kerykeion.schemas.kerykeion_exception import KerykeionException


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def factory():
    return OccultationFactory()


@pytest.fixture(scope="module")
def start_jd():
    """Julian Day for 2024-01-01 00:00 UT."""
    return ephe.julday(2024, 1, 1, 0.0)


# ---------------------------------------------------------------------------
# Global search tests
# ---------------------------------------------------------------------------

_occ_cache: dict = {}


def _global_search(factory, start_jd, planet_id, count=1):
    key = ("global", planet_id, count)
    if key not in _occ_cache:
        _occ_cache[key] = factory.search_global(start_jd, planet_id, count=count)
    return _occ_cache[key]


def _local_search(factory, start_jd, planet_id, count=1):
    key = ("local", planet_id, count)
    if key not in _occ_cache:
        _occ_cache[key] = factory.search_local(start_jd, planet_id, lat=41.9, lng=12.5, count=count)
    return _occ_cache[key]


class TestSearchGlobal:
    def test_returns_list(self, factory, start_jd):
        assert isinstance(_global_search(factory, start_jd, ephe.VENUS, 2), list)

    def test_returns_requested_count(self, factory, start_jd):
        assert len(_global_search(factory, start_jd, ephe.VENUS, 2)) == 2

    def test_result_is_occultation_model(self, factory, start_jd):
        results = _global_search(factory, start_jd, ephe.VENUS, 1)
        assert len(results) >= 1
        assert isinstance(results[0], OccultationModel)

    def test_model_fields(self, factory, start_jd):
        occ = _global_search(factory, start_jd, ephe.VENUS, 1)[0]
        assert occ.planet_name == "Venus"
        assert occ.type in ("Total", "Annular", "Partial", "Unknown")
        assert occ.maximum_jd > start_jd
        assert "T" in occ.datestamp and occ.datestamp.endswith("Z")

    def test_results_are_chronological(self, factory, start_jd):
        jds = [r.maximum_jd for r in _global_search(factory, start_jd, ephe.SATURN, 2)]
        assert jds == sorted(jds)

    def test_subscriptable(self, factory, start_jd):
        occ = _global_search(factory, start_jd, ephe.VENUS, 1)[0]
        assert occ["planet_name"] == occ.planet_name


# ---------------------------------------------------------------------------
# Local search tests
# ---------------------------------------------------------------------------

class TestSearchLocal:
    def test_returns_list(self, factory, start_jd):
        assert isinstance(_local_search(factory, start_jd, ephe.VENUS, 1), list)

    def test_returns_results(self, factory, start_jd):
        assert len(_local_search(factory, start_jd, ephe.VENUS, 1)) >= 1

    def test_local_model_fields(self, factory, start_jd):
        results = _local_search(factory, start_jd, ephe.VENUS, 1)
        assert len(results) >= 1
        occ = results[0]
        assert occ.planet_name == "Venus"
        assert occ.maximum_jd > start_jd
        assert occ.datestamp.endswith("Z")


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------

class TestImports:
    def test_importable_from_package(self):
        from kerykeion import OccultationFactory as OF
        assert OF is OccultationFactory

    def test_importable_from_subpackage(self):
        from kerykeion.occultations import OccultationFactory as OF
        assert OF is OccultationFactory

    def test_model_importable(self):
        from kerykeion.occultations import OccultationModel as OM
        assert OM is OccultationModel


# ---------------------------------------------------------------------------
# SWE reference tests
# ---------------------------------------------------------------------------

class TestClassifyOccultation:
    """Test the _classify_occultation helper."""

    def test_classify_unknown_flag(self):
        """Flag 0 (no matching bits) should return 'Unknown'."""
        from kerykeion.occultations.occultation_factory import _classify_occultation
        assert _classify_occultation(0) == "Unknown"


class TestJdToIso:
    """_jd_to_iso must match the eclipse/lunation/station/ingress formatters."""

    def test_jd_to_iso_bce_year(self):
        """BCE Julian Days must format with a signed 4-digit extended year and
        real seconds, e.g. -0044-03-15T12:00:00Z (not the old '-44-...')."""
        from kerykeion.occultations.occultation_factory import _jd_to_iso

        jd = ephe.julday(-44, 3, 15, 12.0)
        assert _jd_to_iso(jd) == "-0044-03-15T12:00:00Z"

    def test_jd_to_iso_ce_year_with_seconds(self):
        """CE formatting keeps the unsigned year and rounds to the nearest
        second instead of truncating."""
        from kerykeion.occultations.occultation_factory import _jd_to_iso

        jd = ephe.julday(2026, 8, 12, 17.0 + 30.0 / 60.0 + 42.0 / 3600.0)
        assert _jd_to_iso(jd) == "2026-08-12T17:30:42Z"


class TestOccultationBreakAndErrorPaths:
    """Test break-on-zero and exception paths in the search methods."""

    def test_global_retflags_zero_breaks(self, factory, start_jd):
        """search_global should return empty list when retflags == 0
        ("no further occultation" is a legitimate terminal result)."""
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.occultations.occultation_factory.ephe.lun_occult_when_glob",
            return_value=(0, zero_tret),
        ):
            results = factory.search_global(start_jd, ephe.VENUS, count=3)
            assert results == []

    def test_global_backend_failure_raises(self, factory, start_jd):
        """A backend failure must abort the search as KerykeionException
        (with the failing JD), never silently return partial results."""
        from unittest.mock import patch
        with patch(
            "kerykeion.occultations.occultation_factory.ephe.lun_occult_when_glob",
            side_effect=RuntimeError("ephe failure"),
        ):
            with pytest.raises(KerykeionException, match="ephemeris range"):
                factory.search_global(start_jd, ephe.VENUS, count=3)

    def test_global_mid_scan_failure_raises_not_truncates(self, factory, start_jd):
        """If the backend fails after some events were already found (e.g. the
        scan walked past the ephemeris range edge), the whole search must raise
        rather than return a truncated list claiming full coverage."""
        from unittest.mock import patch
        good = (4, [start_jd + 5.0] + [0.0] * 9)  # 4 = ECL_TOTAL
        with patch(
            "kerykeion.occultations.occultation_factory.ephe.lun_occult_when_glob",
            side_effect=[good, RuntimeError("jd outside ephemeris range")],
        ):
            with pytest.raises(KerykeionException, match=r"JD "):
                factory.search_global(start_jd, ephe.VENUS, count=3)

    def test_local_retflags_zero_breaks(self, factory, start_jd):
        """search_local should return empty list when retflags == 0
        ("no further occultation" is a legitimate terminal result)."""
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.occultations.occultation_factory.ephe.lun_occult_when_loc",
            return_value=(0, zero_tret, [0.0] * 10),
        ):
            results = factory.search_local(start_jd, ephe.VENUS, lat=41.9, lng=12.5, count=3)
            assert results == []

    def test_local_backend_failure_raises(self, factory, start_jd):
        """A backend failure must abort the search as KerykeionException."""
        from unittest.mock import patch
        with patch(
            "kerykeion.occultations.occultation_factory.ephe.lun_occult_when_loc",
            side_effect=RuntimeError("ephe failure"),
        ):
            with pytest.raises(KerykeionException, match="ephemeris range"):
                factory.search_local(start_jd, ephe.VENUS, lat=41.9, lng=12.5, count=3)

    def test_count_too_large_rejected_upfront(self, factory, start_jd):
        """Absurd counts are rejected upfront, never silently truncated."""
        with pytest.raises(ValueError):
            factory.search_global(start_jd, ephe.VENUS, count=1_001)
        with pytest.raises(ValueError):
            factory.search_local(start_jd, ephe.VENUS, lat=41.9, lng=12.5, count=1_001)

    def test_negative_count_rejected_upfront(self, factory, start_jd):
        with pytest.raises(ValueError, match="non-negative"):
            factory.search_global(start_jd, ephe.VENUS, count=-1)
        with pytest.raises(ValueError, match="non-negative"):
            factory.search_local(start_jd, ephe.VENUS, lat=41.9, lng=12.5, count=-1)


class TestPlanetNameResolution:
    """planet_id also accepts planet names (resolved via the project-wide
    STANDARD_PLANETS map); raw Swiss Ephemeris ints stay supported."""

    def test_global_accepts_planet_name(self, factory, start_jd):
        """search_global("Venus") must search the same body as ephe.VENUS."""
        from unittest.mock import patch
        captured = {}

        def fake_glob(cursor, planet_id, flags, ecl_type, backwards):
            captured["planet_id"] = planet_id
            return (4, [start_jd + 5.0] + [0.0] * 9)  # 4 = ECL_TOTAL

        with patch(
            "kerykeion.occultations.occultation_factory.ephe.lun_occult_when_glob",
            side_effect=fake_glob,
        ):
            results = factory.search_global(start_jd, "Venus", count=1)
        assert captured["planet_id"] == ephe.VENUS
        assert len(results) == 1
        assert results[0].planet_name == "Venus"

    def test_local_accepts_planet_name(self, factory, start_jd):
        from unittest.mock import patch
        captured = {}

        def fake_loc(cursor, planet_id, geopos, flags, backwards):
            captured["planet_id"] = planet_id
            return (4, [start_jd + 5.0] + [0.0] * 9, [0.0] * 10)

        with patch(
            "kerykeion.occultations.occultation_factory.ephe.lun_occult_when_loc",
            side_effect=fake_loc,
        ):
            results = factory.search_local(start_jd, "Mars", lat=41.9, lng=12.5, count=1)
        assert captured["planet_id"] == ephe.MARS
        assert len(results) == 1

    def test_unknown_planet_name_raises(self, factory, start_jd):
        with pytest.raises(KerykeionException, match="Unknown planet name"):
            factory.search_global(start_jd, "Vulcan", count=1)
        with pytest.raises(KerykeionException, match="Unknown planet name"):
            factory.search_local(start_jd, "Vulcan", lat=41.9, lng=12.5, count=1)

    def test_wrong_type_raises_type_error(self, factory, start_jd):
        with pytest.raises(TypeError, match="planet_id"):
            factory.search_global(start_jd, 3.5, count=1)


class TestSweReference:
    """Compare factory results with direct ephe.lun_occult_when_glob() calls."""

    def test_venus_global_first_result_matches_swe(self, factory, start_jd):
        results = _global_search(factory, start_jd, ephe.VENUS, 1)
        assert len(results) >= 1
        with ephemeris_session():
            _retflags, tret = ephe.lun_occult_when_glob(start_jd, ephe.VENUS, ephe.FLG_SWIEPH, 0, False)
        assert results[0].maximum_jd == pytest.approx(tret[0], abs=0.01)

    def test_saturn_global_first_result_matches_swe(self, factory, start_jd):
        results = _global_search(factory, start_jd, ephe.SATURN, 1)
        assert len(results) >= 1
        with ephemeris_session():
            _retflags, tret = ephe.lun_occult_when_glob(start_jd, ephe.SATURN, ephe.FLG_SWIEPH, 0, False)
        assert results[0].maximum_jd == pytest.approx(tret[0], abs=0.01)


class TestOccultationValidation:
    """Round 35: the location search rejects an impossible latitude, and the body
    resolver rejects non-physically-occultable calculated points (lunar nodes,
    Lilith/apogee variants, Uranian hypotheticals) that would otherwise fabricate a
    meaningless 'occultation' of a point that has no disk to be covered."""

    @pytest.mark.parametrize("lat", [200.0, -95.0, 139.69])
    def test_local_search_invalid_latitude_raises(self, factory, start_jd, lat):
        with pytest.raises(KerykeionException):
            factory.search_local(start_jd, "Venus", lat=lat, lng=12.0, count=1)

    @pytest.mark.parametrize("lng", [181.0, -181.0, float("nan"), float("inf"), float("-inf")])
    def test_local_search_invalid_longitude_raises(self, factory, start_jd, lng):
        with pytest.raises(KerykeionException, match="Longitude"):
            factory.search_local(start_jd, "Venus", lat=41.9, lng=lng, count=0)

    @pytest.mark.parametrize("julian_day", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_julian_day_rejected_even_for_zero_count(self, factory, julian_day):
        with pytest.raises(ValueError, match="finite"):
            factory.search_global(julian_day, "Venus", count=0)

    @pytest.mark.parametrize(
        "name", ["Mean_North_Lunar_Node", "True_Lilith", "Interpolated_Perigee", "Cupido", "Earth"]
    )
    def test_non_occultable_body_raises(self, factory, start_jd, name):
        with pytest.raises(KerykeionException):
            factory.search_global(start_jd, name, count=1)

    @pytest.mark.parametrize("planet_id", [ephe.MEAN_NODE, ephe.TRUE_NODE, ephe.MOON, ephe.EARTH])
    def test_non_occultable_raw_body_id_raises(self, factory, start_jd, planet_id):
        with pytest.raises(KerykeionException, match="not a physically occultable body"):
            factory.search_global(start_jd, planet_id, count=0)

    @pytest.mark.parametrize("name", ["Venus", "Mars", "Jupiter"])
    def test_occultable_body_still_works(self, factory, start_jd, name):
        results = factory.search_global(start_jd, name, count=1)
        assert len(results) >= 1
