"""
Tests for the OccultationFactory.

Verifies that global and local lunar occultation searches return
well-formed OccultationModel results using the Swiss Ephemeris.
"""

import pytest
swe = pytest.importorskip("swisseph")

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

class TestSearchGlobal:
    def test_returns_list(self, factory, start_jd):
        results = factory.search_global(start_jd, swe.VENUS, count=3)
        assert isinstance(results, list)

    def test_returns_requested_count(self, factory, start_jd):
        results = factory.search_global(start_jd, swe.VENUS, count=3)
        assert len(results) == 3

    def test_result_is_occultation_model(self, factory, start_jd):
        results = factory.search_global(start_jd, swe.VENUS, count=1)
        assert len(results) >= 1
        occ = results[0]
        assert isinstance(occ, OccultationModel)

    def test_model_fields(self, factory, start_jd):
        results = factory.search_global(start_jd, swe.VENUS, count=1)
        occ = results[0]
        assert occ.planet_name == "Venus"
        assert occ.type in ("Total", "Annular", "Partial", "Unknown")
        assert occ.maximum_jd > start_jd
        assert "T" in occ.datestamp and occ.datestamp.endswith("Z")

    def test_results_are_chronological(self, factory, start_jd):
        results = factory.search_global(start_jd, swe.SATURN, count=3)
        jds = [r.maximum_jd for r in results]
        assert jds == sorted(jds), "Results should be in chronological order"

    def test_subscriptable(self, factory, start_jd):
        """OccultationModel inherits dict-style access from SubscriptableBaseModel."""
        results = factory.search_global(start_jd, swe.VENUS, count=1)
        occ = results[0]
        assert occ["planet_name"] == occ.planet_name

    def test_different_planets(self, factory, start_jd):
        for pid in (swe.MERCURY, swe.MARS, swe.JUPITER):
            results = factory.search_global(start_jd, pid, count=1)
            assert len(results) >= 1
            assert results[0].planet_name == swe.get_planet_name(pid)


# ---------------------------------------------------------------------------
# Local search tests
# ---------------------------------------------------------------------------

class TestSearchLocal:
    def test_returns_list(self, factory, start_jd):
        results = factory.search_local(start_jd, swe.VENUS, lat=41.9, lng=12.5, count=2)
        assert isinstance(results, list)

    def test_returns_results(self, factory, start_jd):
        results = factory.search_local(start_jd, swe.VENUS, lat=41.9, lng=12.5, count=2)
        assert len(results) >= 1

    def test_local_model_fields(self, factory, start_jd):
        results = factory.search_local(start_jd, swe.VENUS, lat=41.9, lng=12.5, count=1)
        # Local occultation visibility depends on observer location; may legitimately
        # return fewer results than requested, but test_returns_results already
        # asserts >= 1 for this same query, so we assert here too.
        assert len(results) >= 1, "Local Venus occultation search should find at least 1 result"
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
        """Factory search_global first result maximum_jd must match raw swe tret[0]."""
        results = factory.search_global(start_jd, swe.VENUS, count=1)
        assert len(results) >= 1

        # Direct swe call with identical parameters
        _retflags, tret = swe.lun_occult_when_glob(
            start_jd,
            swe.VENUS,
            swe.FLG_SWIEPH,
            0,
            False,
        )
        expected_jd = tret[0]

        assert results[0].maximum_jd == pytest.approx(expected_jd, abs=0.01), (
            f"Factory JD {results[0].maximum_jd} != swe JD {expected_jd}"
        )

    def test_saturn_global_first_result_matches_swe(self, factory, start_jd):
        """Same check for Saturn to ensure generalisation across planets."""
        results = factory.search_global(start_jd, swe.SATURN, count=1)
        assert len(results) >= 1

        _retflags, tret = swe.lun_occult_when_glob(
            start_jd,
            swe.SATURN,
            swe.FLG_SWIEPH,
            0,
            False,
        )
        expected_jd = tret[0]

        assert results[0].maximum_jd == pytest.approx(expected_jd, abs=0.01)
