# -*- coding: utf-8 -*-
"""Tests for heliocentric returns and lunar node crossing."""

import pytest
from kerykeion import AstrologicalSubjectFactory, PlanetaryReturnFactory


@pytest.fixture(scope="module")
def factory():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )
    return PlanetaryReturnFactory(
        subject, lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


class TestHeliocentricReturn:
    def test_mars_heliocentric_return(self, factory):
        import swisseph as swe
        start_jd = swe.julday(2025, 1, 1, 0.0)
        result = factory.next_heliocentric_return("Mars", start_jd)
        assert result is not None
        assert result.return_type == "Heliocentric"
        assert result.julian_day > start_jd

    def test_jupiter_heliocentric_return(self, factory):
        import swisseph as swe
        start_jd = swe.julday(2025, 1, 1, 0.0)
        result = factory.next_heliocentric_return("Jupiter", start_jd)
        assert result is not None
        assert result.return_type == "Heliocentric"
        # Jupiter return should be ~12 years from birth
        assert result.julian_day > start_jd

    def test_heliocentric_return_has_chart_data(self, factory):
        import swisseph as swe
        start_jd = swe.julday(2025, 1, 1, 0.0)
        result = factory.next_heliocentric_return("Mars", start_jd)
        assert result.sun is not None
        assert result.moon is not None
        assert result.ascendant is not None


class TestLunarNodeCrossing:
    def test_next_crossing(self, factory):
        import swisseph as swe
        start_jd = swe.julday(2025, 1, 1, 0.0)
        result = factory.next_lunar_node_crossing(start_jd)
        assert result is not None
        assert result.return_type == "Lunar_Node_Crossing"
        assert result.julian_day > start_jd

    def test_crossing_has_chart_data(self, factory):
        import swisseph as swe
        start_jd = swe.julday(2025, 1, 1, 0.0)
        result = factory.next_lunar_node_crossing(start_jd)
        assert result.sun is not None
        assert result.moon is not None

    def test_crossing_within_month(self, factory):
        """Moon crosses its node roughly every 2 weeks."""
        import swisseph as swe
        start_jd = swe.julday(2025, 1, 1, 0.0)
        result = factory.next_lunar_node_crossing(start_jd)
        # Should be within ~15 days
        assert result.julian_day - start_jd < 15
