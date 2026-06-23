# -*- coding: utf-8 -*-
"""Tests for the Dorothean triplicity-lords helper (get_triplicity_lords).

These are pure-logic tests over the static rulership tables; they require no
ephemeris backend.
"""

import pytest

from kerykeion import KerykeionException, TriplicityLordsModel
from kerykeion.dignities import get_triplicity_lords
from kerykeion.dignities.dignity_data import TRIPLICITY_RULERS

ELEMENTS = ["Fire", "Earth", "Air", "Water"]


class TestTriplicityLords:
    def test_returns_typed_model(self):
        result = get_triplicity_lords("Fire", is_diurnal=True)
        assert isinstance(result, TriplicityLordsModel)

    @pytest.mark.parametrize("element", ELEMENTS)
    def test_day_chart_ordering(self, element):
        rulers = TRIPLICITY_RULERS[element]
        result = get_triplicity_lords(element, is_diurnal=True)
        assert result.element == element
        assert result.sect == "day"
        assert result.primary == rulers["day"]
        assert result.secondary == rulers["night"]
        assert result.participating == rulers["participating"]

    @pytest.mark.parametrize("element", ELEMENTS)
    def test_night_chart_ordering(self, element):
        rulers = TRIPLICITY_RULERS[element]
        result = get_triplicity_lords(element, is_diurnal=False)
        assert result.element == element
        assert result.sect == "night"
        assert result.primary == rulers["night"]
        assert result.secondary == rulers["day"]
        assert result.participating == rulers["participating"]

    def test_known_dorothean_values_fire(self):
        day = get_triplicity_lords("Fire", is_diurnal=True)
        assert (day.primary, day.secondary, day.participating) == ("Sun", "Jupiter", "Saturn")
        night = get_triplicity_lords("Fire", is_diurnal=False)
        assert (night.primary, night.secondary, night.participating) == ("Jupiter", "Sun", "Saturn")

    def test_known_dorothean_values_water(self):
        day = get_triplicity_lords("Water", is_diurnal=True)
        assert (day.primary, day.secondary, day.participating) == ("Venus", "Mars", "Moon")
        night = get_triplicity_lords("Water", is_diurnal=False)
        assert (night.primary, night.secondary, night.participating) == ("Mars", "Venus", "Moon")

    def test_participating_is_sect_independent(self):
        for element in ELEMENTS:
            day = get_triplicity_lords(element, is_diurnal=True)
            night = get_triplicity_lords(element, is_diurnal=False)
            assert day.participating == night.participating

    def test_invalid_element_raises(self):
        with pytest.raises(KerykeionException):
            get_triplicity_lords("Spirit", is_diurnal=True)  # type: ignore[arg-type]
