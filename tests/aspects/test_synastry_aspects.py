from kerykeion import AstrologicalSubject, SynastryAspects

from .expected_synastry_aspects import EXPECTED_ALL_ASPECTS, EXPECTED_RELEVANT_ASPECTS


class TestNatalAspects:
    def setup_class(self):
        self.first_subject = AstrologicalSubject("John", 1940, 10, 9, 10, 30, "Liverpool", "GB")
        self.second_subject = AstrologicalSubject("Yoko", 1933, 2, 18, 10, 30, "Tokyo", "JP")

        self.synastry_relevant_aspects = SynastryAspects(self.first_subject, self.second_subject).get_relevant_aspects()
        self.synastry_all_aspects = SynastryAspects(self.first_subject, self.second_subject).get_all_aspects()

        self.expected_relevant_aspects = EXPECTED_RELEVANT_ASPECTS
        self.expected_all_aspects = EXPECTED_ALL_ASPECTS

    def test_relevant_aspects_length(self):
        assert len(self.expected_relevant_aspects) == len(self.synastry_relevant_aspects)

    def test_relevant_aspects(self):
        for i, aspect in enumerate(self.expected_relevant_aspects):
            assert self.synastry_relevant_aspects[i]["p1_name"] == aspect["p1_name"]
            assert round(self.synastry_relevant_aspects[i]["p1_abs_pos"], 2) == round(aspect["p1_abs_pos"], 2)
            assert self.synastry_relevant_aspects[i]["p2_name"] == aspect["p2_name"]
            assert round(self.synastry_relevant_aspects[i]["p2_abs_pos"], 2) == round(aspect["p2_abs_pos"], 2)
            assert self.synastry_relevant_aspects[i]["aspect"] == aspect["aspect"]
            assert round(self.synastry_relevant_aspects[i]["orbit"], 2) == round(aspect["orbit"], 2)
            assert round(self.synastry_relevant_aspects[i]["aspect_degrees"], 2) == round(aspect["aspect_degrees"], 2)
            assert self.synastry_relevant_aspects[i]["color"] == aspect["color"]
            assert self.synastry_relevant_aspects[i]["aid"] == aspect["aid"]
            assert round(self.synastry_relevant_aspects[i]["diff"], 2) == round(aspect["diff"], 2)
            assert self.synastry_relevant_aspects[i]["p1"] == aspect["p1"]
            assert self.synastry_relevant_aspects[i]["p2"] == aspect["p2"]

    def test_all_aspects_length(self):
        assert len(self.expected_all_aspects) == len(self.synastry_all_aspects)

    def test_all_aspects(self):
        for i, aspect in enumerate(self.expected_all_aspects):
            assert self.synastry_all_aspects[i]["p1_name"] == aspect["p1_name"]
            assert round(self.synastry_all_aspects[i]["p1_abs_pos"], 2) == round(aspect["p1_abs_pos"], 2)
            assert self.synastry_all_aspects[i]["p2_name"] == aspect["p2_name"]
            assert round(self.synastry_all_aspects[i]["p2_abs_pos"], 2) == round(aspect["p2_abs_pos"], 2)
            assert self.synastry_all_aspects[i]["aspect"] == aspect["aspect"]
            assert round(self.synastry_all_aspects[i]["orbit"], 2) == round(aspect["orbit"], 2)
            assert round(self.synastry_all_aspects[i]["aspect_degrees"], 2) == round(aspect["aspect_degrees"], 2)
            assert self.synastry_all_aspects[i]["color"] == aspect["color"]
            assert self.synastry_all_aspects[i]["aid"] == aspect["aid"]
            assert round(self.synastry_all_aspects[i]["diff"], 2) == round(aspect["diff"], 2)
            assert self.synastry_all_aspects[i]["p1"] == aspect["p1"]
            assert self.synastry_all_aspects[i]["p2"] == aspect["p2"]
