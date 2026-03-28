"""
Tests for the OccultationFactory.

Verifies that global and local lunar occultation searches return
well-formed OccultationModel results using the Swiss Ephemeris.
"""

import swisseph as swe
import pytest

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
