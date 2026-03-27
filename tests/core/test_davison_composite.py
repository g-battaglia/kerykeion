# -*- coding: utf-8 -*-
"""Tests for the Davison composite chart."""

import pytest
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory


@pytest.fixture(scope="module")
def subjects():
    s1 = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", 1940, 10, 9, 18, 30,
        lng=-2.9916, lat=53.4084, tz_str="Europe/London",
        city="Liverpool", nation="GB", online=False,
    )
    s2 = AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono", 1933, 2, 18, 20, 30,
        lng=139.6917, lat=35.6895, tz_str="Asia/Tokyo",
        city="Tokyo", nation="JP", online=False,
    )
    return s1, s2


class TestDavisonComposite:
    def test_davison_creates_valid_chart(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()
        assert davison is not None
        assert davison.composite_chart_type == "Davison"

    def test_davison_has_planets(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()
        assert davison.sun is not None
        assert davison.moon is not None
        assert davison.ascendant is not None
        assert 0 <= davison.sun.abs_pos < 360

    def test_davison_has_subjects(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()
        assert davison.first_subject.name == "John Lennon"
        assert davison.second_subject.name == "Yoko Ono"

    def test_davison_midpoint_date_between_subjects(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()
        # Davison JD should be between the two subjects
        assert s2.julian_day < davison.julian_day < s1.julian_day

    def test_davison_differs_from_midpoint(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        midpoint = factory.get_midpoint_composite_subject_model()
        davison = factory.get_davison_composite_subject_model()
        # Davison and midpoint should give different Sun positions
        assert abs(midpoint.sun.abs_pos - davison.sun.abs_pos) > 0.01

    def test_both_chart_types_available(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        midpoint = factory.get_midpoint_composite_subject_model()
        assert midpoint.composite_chart_type == "Midpoint"
        # Need a new factory since midpoint modifies internal state
        factory2 = CompositeSubjectFactory(s1, s2)
        davison = factory2.get_davison_composite_subject_model()
        assert davison.composite_chart_type == "Davison"
