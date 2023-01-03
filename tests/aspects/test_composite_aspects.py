from kerykeion import (
    KrInstance,
    CompositeAspects,
)

from .expected_composite_aspects import EXPECTED_ALL_ASPECTS, EXPECTED_RELEVANT_ASPECTS

class TestNatalAspects:
    def setup_class(self):
        self.first_subject = KrInstance("John", 1940, 10, 9, 10, 30, "Liverpool")
        self.second_subject = KrInstance("Yoko", 1933, 2, 18, 10, 30, "Tokyo")

        self.composite_relevant_aspects = CompositeAspects(self.first_subject, self.second_subject).get_relevant_aspects()
        self.composite_all_aspects = CompositeAspects(self.first_subject, self.second_subject).get_all_aspects()

        self.expected_relevant_aspects = EXPECTED_RELEVANT_ASPECTS
        self.expected_all_aspects = EXPECTED_ALL_ASPECTS
    def test_relevant_aspects_length(self):
        assert len(self.expected_relevant_aspects) == 43

    def test_relevant_aspects(self):
        for i, aspect in enumerate(self.expected_relevant_aspects):
            assert self.composite_relevant_aspects[i]["p1_name"] == aspect["p1_name"]
            assert self.composite_relevant_aspects[i]["p1_abs_pos"] == aspect["p1_abs_pos"]
            assert self.composite_relevant_aspects[i]["p2_name"] == aspect["p2_name"]
            assert self.composite_relevant_aspects[i]["p2_abs_pos"] == aspect["p2_abs_pos"]
            assert self.composite_relevant_aspects[i]["aspect"] == aspect["aspect"]
            assert self.composite_relevant_aspects[i]["orbit"] == aspect["orbit"]
            assert self.composite_relevant_aspects[i]["aspect_degrees"] == aspect["aspect_degrees"]
            assert self.composite_relevant_aspects[i]["color"] == aspect["color"]
            assert self.composite_relevant_aspects[i]["aid"] == aspect["aid"]
            assert self.composite_relevant_aspects[i]["diff"] == aspect["diff"]
            assert self.composite_relevant_aspects[i]["p1"] == aspect["p1"]
            assert self.composite_relevant_aspects[i]["p2"] == aspect["p2"]

    def test_all_aspects_length(self):
        assert len(self.expected_all_aspects) == 64

    def test_all_aspects(self):
        for i, aspect in enumerate(self.expected_all_aspects):
            assert self.composite_all_aspects[i]["p1_name"] == aspect["p1_name"]
            assert self.composite_all_aspects[i]["p1_abs_pos"] == aspect["p1_abs_pos"]
            assert self.composite_all_aspects[i]["p2_name"] == aspect["p2_name"]
            assert self.composite_all_aspects[i]["p2_abs_pos"] == aspect["p2_abs_pos"]
            assert self.composite_all_aspects[i]["aspect"] == aspect["aspect"]
            assert self.composite_all_aspects[i]["orbit"] == aspect["orbit"]
            assert self.composite_all_aspects[i]["aspect_degrees"] == aspect["aspect_degrees"]
            assert self.composite_all_aspects[i]["color"] == aspect["color"]
            assert self.composite_all_aspects[i]["aid"] == aspect["aid"]
            assert self.composite_all_aspects[i]["diff"] == aspect["diff"]
            assert self.composite_all_aspects[i]["p1"] == aspect["p1"]
            assert self.composite_all_aspects[i]["p2"] == aspect["p2"]
