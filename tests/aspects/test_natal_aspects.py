from kerykeion import (
    AstrologicalSubject,
    NatalAspects,
)

from .expected_natal_aspects import EXPECTED_ALL_ASPECTS, EXPECTED_RELEVANT_ASPECTS


class TestNatalAspects:
    def setup_class(self):
        self.subject = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US", geonames_username="century.boy")
        self.subject_relevant_aspects = NatalAspects(self.subject).relevant_aspects
        self.subject_all_aspects = NatalAspects(self.subject).all_aspects

        self.expected_relevant_aspects = EXPECTED_RELEVANT_ASPECTS
        self.expected_all_aspects = EXPECTED_ALL_ASPECTS

    def test_relevant_aspects_length(self):
        assert len(self.expected_relevant_aspects) == len(self.subject_relevant_aspects)

    def test_relevant_aspects(self):
        for i, aspect in enumerate(self.expected_relevant_aspects):
            assert self.subject_relevant_aspects[i]["p1_name"] == aspect["p1_name"]
            assert round(self.subject_relevant_aspects[i]["p1_abs_pos"], 2) == round(aspect["p1_abs_pos"], 2)
            assert self.subject_relevant_aspects[i]["p2_name"] == aspect["p2_name"]
            assert round(self.subject_relevant_aspects[i]["p2_abs_pos"], 2) == round(aspect["p2_abs_pos"], 2)
            assert self.subject_relevant_aspects[i]["aspect"] == aspect["aspect"]
            assert round(self.subject_relevant_aspects[i]["aspect_degrees"], 2) == round(aspect["aspect_degrees"], 2)
            assert self.subject_relevant_aspects[i]["aspect_degrees"] == aspect["aspect_degrees"]
            assert self.subject_relevant_aspects[i]["aid"] == aspect["aid"]
            assert round(self.subject_relevant_aspects[i]["diff"], 2) == round(aspect["diff"], 2)
            assert self.subject_relevant_aspects[i]["p1"] == aspect["p1"]
            assert self.subject_relevant_aspects[i]["p2"] == aspect["p2"]

    def test_all_aspects_length(self):
        assert len(self.expected_all_aspects) == len(self.subject_all_aspects)

    def test_all_aspects(self):
        for i, aspect in enumerate(self.expected_all_aspects):
            assert self.subject_all_aspects[i]["p1_name"] == aspect["p1_name"]
            assert round(self.subject_all_aspects[i]["p1_abs_pos"], 2) == round(aspect["p1_abs_pos"], 2)
            assert self.subject_all_aspects[i]["p2_name"] == aspect["p2_name"]
            assert round(self.subject_all_aspects[i]["p2_abs_pos"], 2) == round(aspect["p2_abs_pos"], 2)
            assert self.subject_all_aspects[i]["aspect"] == aspect["aspect"]
            assert round(self.subject_all_aspects[i]["orbit"], 2) == round(aspect["orbit"], 2)
            assert round(self.subject_all_aspects[i]["aspect_degrees"], 2) == round(aspect["aspect_degrees"], 2)
            assert self.subject_all_aspects[i]["aid"] == aspect["aid"]
            assert round(self.subject_all_aspects[i]["diff"], 2) == round(aspect["diff"], 2)
            assert self.subject_all_aspects[i]["p1"] == aspect["p1"]
            assert self.subject_all_aspects[i]["p2"] == aspect["p2"]


if __name__ == "__main__":
    import pytest
    import logging

    # Set the log level to CRITICAL
    logging.basicConfig(level=logging.CRITICAL)

    pytest.main(["-vv", "--log-level=CRITICAL", "--log-cli-level=CRITICAL", __file__])
