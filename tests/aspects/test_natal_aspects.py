from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory
from pytest import approx

from .expected_natal_aspects import EXPECTED_ALL_ASPECTS, EXPECTED_RELEVANT_ASPECTS


class TestNatalAspects:
    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data("Johnny Depp", 1963, 6, 9, 0 , 0, "Owensboro", "US", suppress_geonames_warning=True)

        self.subject_relevant_aspects = AspectsFactory.single_chart_aspects(self.subject).aspects
        self.subject_relevant_aspects = [a.model_dump() for a in self.subject_relevant_aspects]

        self.subject_all_aspects = AspectsFactory.single_chart_aspects(self.subject).aspects
        self.subject_all_aspects = [a.model_dump() for a in self.subject_all_aspects]

        self.expected_relevant_aspects = EXPECTED_RELEVANT_ASPECTS
        self.expected_all_aspects = EXPECTED_ALL_ASPECTS

    def test_relevant_aspects_length(self):
        assert len(self.expected_relevant_aspects) == len(self.subject_relevant_aspects)


    def test_relevant_aspects(self):
        for i, aspect in enumerate(self.expected_relevant_aspects):
            assert self.subject_relevant_aspects[i]["p1_name"] == aspect["p1_name"]
            assert self.subject_relevant_aspects[i]["p1_abs_pos"] == approx(aspect["p1_abs_pos"], abs=1e-2)
            assert self.subject_relevant_aspects[i]["p2_name"] == aspect["p2_name"]
            assert self.subject_relevant_aspects[i]["p2_abs_pos"] == approx(aspect["p2_abs_pos"], abs=1e-2)
            assert self.subject_relevant_aspects[i]["aspect"] == aspect["aspect"]
            assert self.subject_relevant_aspects[i]["aspect_degrees"] == approx(aspect["aspect_degrees"], abs=1e-2)
            assert self.subject_relevant_aspects[i]["aspect_degrees"] == aspect["aspect_degrees"]
            assert self.subject_relevant_aspects[i]["diff"] == approx(aspect["diff"], abs=1e-2)
            assert self.subject_relevant_aspects[i]["p1"] == aspect["p1"]
            assert self.subject_relevant_aspects[i]["p2"] == aspect["p2"]
