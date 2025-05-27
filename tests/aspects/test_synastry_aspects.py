from kerykeion import AstrologicalSubjectFactory, SynastryAspects
from pytest import approx

from .expected_synastry_aspects import EXPECTED_ALL_ASPECTS, EXPECTED_RELEVANT_ASPECTS


class TestSynastryAspects:
    def setup_class(self):
        self.first_subject = AstrologicalSubjectFactory.from_birth_data("John", 1940, 10, 9, 10, 30, "Liverpool", "GB", geonames_username="century.boy")
        print(self.first_subject.model_dump_json(indent=4))
        self.second_subject = AstrologicalSubjectFactory.from_birth_data("Yoko", 1933, 2, 18, 10, 30, "Tokyo", "JP", geonames_username="century.boy")

        self.synastry_relevant_aspects = SynastryAspects(self.first_subject, self.second_subject).relevant_aspects
        self.synastry_all_aspects = SynastryAspects(self.first_subject, self.second_subject).all_aspects

        self.expected_relevant_aspects = EXPECTED_RELEVANT_ASPECTS
        self.expected_all_aspects = EXPECTED_ALL_ASPECTS

    def test_relevant_aspects_length(self):
        assert len(self.expected_relevant_aspects) == len(self.synastry_relevant_aspects)


    def test_relevant_aspects(self):
        for i, aspect in enumerate(self.expected_relevant_aspects):
            assert self.synastry_relevant_aspects[i]["p1_name"] == aspect["p1_name"]
            assert self.synastry_relevant_aspects[i]["p1_abs_pos"] == approx(aspect["p1_abs_pos"], abs=1e-2)
            assert self.synastry_relevant_aspects[i]["p2_name"] == aspect["p2_name"]
            assert self.synastry_relevant_aspects[i]["p2_abs_pos"] == approx(aspect["p2_abs_pos"], abs=1e-2)
            assert self.synastry_relevant_aspects[i]["aspect"] == aspect["aspect"]
            assert self.synastry_relevant_aspects[i]["orbit"] == approx(aspect["orbit"], abs=1e-2)
            assert self.synastry_relevant_aspects[i]["aspect_degrees"] == approx(aspect["aspect_degrees"], abs=1e-2)
            assert self.synastry_relevant_aspects[i]["diff"] == approx(aspect["diff"], abs=1e-2)
            assert self.synastry_relevant_aspects[i]["p1"] == aspect["p1"]
            assert self.synastry_relevant_aspects[i]["p2"] == aspect["p2"]


if __name__ == "__main__":
    import pytest
    import logging

    # Set the log level to CRITICAL
    logging.basicConfig(level=logging.CRITICAL)

    pytest.main(["-vv", "--log-level=CRITICAL", "--log-cli-level=CRITICAL", __file__])
