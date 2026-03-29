"""
Tests for the OccultationFactory.

Verifies that global and local lunar occultation searches return
well-formed OccultationModel results using the Swiss Ephemeris.
"""

import pytest
from kerykeion.ephemeris_backend import swe

from kerykeion.occultations import OccultationFactory, OccultationModel


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def factory():
    return OccultationFactory()


@pytest.fixture(scope="module")
def start_jd():
    """Julian Day for 2024-01-01 00:00 UT."""
    return swe.julday(2024, 1, 1, 0.0)


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
        assert isinstance(_global_search(factory, start_jd, swe.VENUS, 2), list)

    def test_returns_requested_count(self, factory, start_jd):
        assert len(_global_search(factory, start_jd, swe.VENUS, 2)) == 2

    def test_result_is_occultation_model(self, factory, start_jd):
        results = _global_search(factory, start_jd, swe.VENUS, 1)
        assert len(results) >= 1
        assert isinstance(results[0], OccultationModel)

    def test_model_fields(self, factory, start_jd):
        occ = _global_search(factory, start_jd, swe.VENUS, 1)[0]
        assert occ.planet_name == "Venus"
        assert occ.type in ("Total", "Annular", "Partial", "Unknown")
        assert occ.maximum_jd > start_jd
        assert "T" in occ.datestamp and occ.datestamp.endswith("Z")

    def test_results_are_chronological(self, factory, start_jd):
        jds = [r.maximum_jd for r in _global_search(factory, start_jd, swe.SATURN, 2)]
        assert jds == sorted(jds)

    def test_subscriptable(self, factory, start_jd):
        occ = _global_search(factory, start_jd, swe.VENUS, 1)[0]
        assert occ["planet_name"] == occ.planet_name


# ---------------------------------------------------------------------------
# Local search tests
# ---------------------------------------------------------------------------

class TestSearchLocal:
    def test_returns_list(self, factory, start_jd):
        assert isinstance(_local_search(factory, start_jd, swe.VENUS, 1), list)

    def test_returns_results(self, factory, start_jd):
        assert len(_local_search(factory, start_jd, swe.VENUS, 1)) >= 1

    def test_local_model_fields(self, factory, start_jd):
        results = _local_search(factory, start_jd, swe.VENUS, 1)
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


class TestOccultationBreakAndErrorPaths:
    """Test break-on-zero and exception paths in the search methods."""

    def test_global_retflags_zero_breaks(self, factory, start_jd):
        """search_global should return empty list when retflags == 0."""
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.occultations.occultation_factory.swe.lun_occult_when_glob",
            return_value=(0, zero_tret),
        ):
            results = factory.search_global(start_jd, swe.VENUS, count=3)
            assert results == []

    def test_global_exception_breaks(self, factory, start_jd):
        """search_global should stop on exception from swe.lun_occult_when_glob."""
        from unittest.mock import patch
        with patch(
            "kerykeion.occultations.occultation_factory.swe.lun_occult_when_glob",
            side_effect=RuntimeError("swe failure"),
        ):
            results = factory.search_global(start_jd, swe.VENUS, count=3)
            assert results == []

    def test_local_retflags_zero_breaks(self, factory, start_jd):
        """search_local should return empty list when retflags == 0."""
        from unittest.mock import patch
        zero_tret = [0.0] * 10
        with patch(
            "kerykeion.occultations.occultation_factory.swe.lun_occult_when_loc",
            return_value=(0, zero_tret, [0.0] * 10),
        ):
            results = factory.search_local(start_jd, swe.VENUS, lat=41.9, lng=12.5, count=3)
            assert results == []

    def test_local_exception_breaks(self, factory, start_jd):
        """search_local should stop on exception from swe.lun_occult_when_loc."""
        from unittest.mock import patch
        with patch(
            "kerykeion.occultations.occultation_factory.swe.lun_occult_when_loc",
            side_effect=RuntimeError("swe failure"),
        ):
            results = factory.search_local(start_jd, swe.VENUS, lat=41.9, lng=12.5, count=3)
            assert results == []


class TestSweReference:
    """Compare factory results with direct swe.lun_occult_when_glob() calls."""

    def test_venus_global_first_result_matches_swe(self, factory, start_jd):
        results = _global_search(factory, start_jd, swe.VENUS, 1)
        assert len(results) >= 1
        _retflags, tret = swe.lun_occult_when_glob(start_jd, swe.VENUS, swe.FLG_SWIEPH, 0, False)
        assert results[0].maximum_jd == pytest.approx(tret[0], abs=0.01)

    def test_saturn_global_first_result_matches_swe(self, factory, start_jd):
        results = _global_search(factory, start_jd, swe.SATURN, 1)
        assert len(results) >= 1
        _retflags, tret = swe.lun_occult_when_glob(start_jd, swe.SATURN, swe.FLG_SWIEPH, 0, False)
        assert results[0].maximum_jd == pytest.approx(tret[0], abs=0.01)
