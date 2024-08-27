# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""

from kerykeion import AstrologicalSubject
from kerykeion.aspects.synastry_aspects import SynastryAspects
import logging
from pathlib import Path
from typing import Union
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, RelationshipScoreAspectModel, RelationshipScoreModel
from kerykeion.kr_types.kr_literals import RelationshipScoreDescription


class RelationshipScoreFactory:
    """
    Calculates the relevance of the relationship between two subjects using the Ciro Discepolo method.

    Results:
        - 0 to 5: Minimal relationship
        - 5 to 10: Medium relationship
        - 10 to 15: Important relationship
        - 15 to 20: Very important relationship
        - 20 to 35: Exceptional relationship
        - 30 and above: Rare Exceptional relationship

    Documentation: http://www.cirodiscepolo.it/Articoli/Discepoloele.htm

    Args:
        first_subject (Union[AstrologicalSubject, AstrologicalSubjectModel]): First subject instance
        second_subject (Union[AstrologicalSubject, AstrologicalSubjectModel]): Second subject instance
    """

    SCORE_MAPPING = [
        ("Minimal", 5),
        ("Medium", 10),
        ("Important", 15),
        ("Very Important", 20),
        ("Exceptional", 30),
        ("Rare Exceptional", float("inf")),
    ]

    def __init__(
        self,
        first_subject: Union[AstrologicalSubject, AstrologicalSubjectModel],
        second_subject: Union[AstrologicalSubject, AstrologicalSubjectModel],
        use_only_major_aspects: bool = True,
    ):
        if isinstance(first_subject, AstrologicalSubject):
            self.first_subject = first_subject.model()
        if isinstance(second_subject, AstrologicalSubject):
            self.second_subject = second_subject.model()

        self.use_only_major_aspects = use_only_major_aspects

        self.score_value = 0
        self.relationship_score_description: RelationshipScoreDescription = "Minimal"
        self.is_destiny_sign = True
        self.relationship_score_aspects: list[RelationshipScoreAspectModel] = []
        self._synastry_aspects = SynastryAspects(self.first_subject, self.second_subject).all_aspects

    def _evaluate_destiny_sign(self):
        """
        Evaluates if the subjects share the same sun sign quality and adds points if true.
        """
        if self.first_subject.sun["quality"] == self.second_subject.sun["quality"]:
            self.is_destiny_sign = True
            self.score_value += 5
            logging.debug(f"Destiny sign found, adding 5 points, total score: {self.score_value}")

    def _evaluate_aspect(self, aspect, points):
        """
        Evaluates an aspect and adds points to the score.

        Args:
            aspect (dict): Aspect information.
            points (int): Points to add.
        """
        if self.use_only_major_aspects and not aspect["is_major"]:
            return

        self.score_value += points
        self.relationship_score_aspects.append(
            RelationshipScoreAspectModel(
                p1_name=aspect["p1_name"],
                p2_name=aspect["p2_name"],
                aspect=aspect["aspect"],
                orbit=aspect["orbit"],
            )
        )
        logging.debug(f"{aspect['p1_name']}-{aspect['p2_name']} aspect: {aspect['aspect']} with orbit {aspect['orbit']} degrees, adding {points} points, total score: {self.score_value}, total aspects: {len(self.relationship_score_aspects)}")

    def _evaluate_sun_sun_main_aspect(self, aspect):
        """
        Evaluates Sun-Sun main aspects and adds points accordingly:
        - 8 points for conjunction/opposition/square
        - 11 points if the aspect's orbit is <= 2 degrees

        Args:
            aspect (dict): Aspect information.
        """
        if aspect["p1_name"] == "Sun" and aspect["p2_name"] == "Sun" and aspect["aspect"] in {"conjunction", "opposition", "square"}:
            points = 11 if aspect["orbit"] <= 2 else 8
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_moon_conjunction(self, aspect):
        """
        Evaluates Sun-Moon conjunctions and adds points accordingly:
        - 8 points for conjunction
        - 11 points if the aspect's orbit is <= 2 degrees

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Moon", "Sun"} and aspect["aspect"] == "conjunction":
            points = 11 if aspect["orbit"] <= 2 else 8
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_sun_other_aspects(self, aspect):
        """
        Evaluates Sun-Sun aspects that are not conjunctions and adds points accordingly:
        - 4 points for other aspects

        Args:
            aspect (dict): Aspect information.
        """
        if aspect["p1_name"] == "Sun" and aspect["p2_name"] == "Sun" and aspect["aspect"] not in {"conjunction", "opposition", "square"}:
            points = 4
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_moon_other_aspects(self, aspect):
        """
        Evaluates Sun-Moon aspects that are not conjunctions and adds points accordingly:
        - 4 points for other aspects

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Moon", "Sun"} and aspect["aspect"] != "conjunction":
            points = 4
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_ascendant_aspect(self, aspect):
        """
        Evaluates Sun-Ascendant aspects and adds points accordingly:
        - 4 points for any aspect

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Sun", "First_House"}:
            points = 4
            self._evaluate_aspect(aspect, points)

    def _evaluate_moon_ascendant_aspect(self, aspect):
        """
        Evaluates Moon-Ascendant aspects and adds points accordingly:
        - 4 points for any aspect

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Moon", "First_House"}:
            points = 4
            self._evaluate_aspect(aspect, points)

    def _evaluate_venus_mars_aspect(self, aspect):
        """
        Evaluates Venus-Mars aspects and adds points accordingly:
        - 4 points for any aspect

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Venus", "Mars"}:
            points = 4
            self._evaluate_aspect(aspect, points)

    def _evaluate_relationship_score_description(self):
        """
        Evaluates the relationship score description based on the total score.
        """
        for description, threshold in self.SCORE_MAPPING:
            if self.score_value < threshold:
                self.relationship_score_description = description
                break

    def get_relationship_score(self):
        """
        Calculates the relationship score based on synastry aspects.

        Returns:
            RelationshipScoreModel: The calculated relationship score.
        """
        self._evaluate_destiny_sign()

        for aspect in self._synastry_aspects:
            self._evaluate_sun_sun_main_aspect(aspect)
            self._evaluate_sun_moon_conjunction(aspect)
            self._evaluate_sun_moon_other_aspects(aspect)
            self._evaluate_sun_sun_other_aspects(aspect)
            self._evaluate_sun_ascendant_aspect(aspect)
            self._evaluate_moon_ascendant_aspect(aspect)
            self._evaluate_venus_mars_aspect(aspect)

        self._evaluate_relationship_score_description()

        return RelationshipScoreModel(
            score_value=self.score_value,
            score_description=self.relationship_score_description,
            is_destiny_sign=self.is_destiny_sign,
            aspects=self.relationship_score_aspects,
            subjects=[self.first_subject, self.second_subject],
        )


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging

    setup_logging(level="critical")

    john = AstrologicalSubject("John", 1940, 10, 9, 18, 30, "Liverpool", "UK")
    yoko = AstrologicalSubject("Yoko", 1933, 2, 18, 20, 30, "Tokyo", "JP")

    relationship_score_factory = RelationshipScoreFactory(john, yoko)
    relationship_score = relationship_score_factory.get_relationship_score()

    print("John and Yoko relationship score:")
    print(relationship_score.score_value)
    print(relationship_score.score_description)
    print(relationship_score.is_destiny_sign)
    print(len(relationship_score.aspects))
    print(len(relationship_score_factory._synastry_aspects))

    print("------------------->")
    freud = AstrologicalSubject("Freud", 1856, 5, 6, 18, 30, "Freiberg", "DE")
    jung = AstrologicalSubject("Jung", 1875, 7, 26, 18, 30, "Kesswil", "CH")

    relationship_score_factory = RelationshipScoreFactory(freud, jung)
    relationship_score = relationship_score_factory.get_relationship_score()

    print("Freud and Jung relationship score:")
    print(relationship_score.score_value)
    print(relationship_score.score_description)
    print(relationship_score.is_destiny_sign)
    print(len(relationship_score.aspects))
    print(len(relationship_score_factory._synastry_aspects))

    print("------------------->")
    richart_burton = AstrologicalSubject("Richard Burton", 1925, 11, 10, 15, 00, "Pontrhydyfen", "UK")
    liz_taylor = AstrologicalSubject("Elizabeth Taylor", 1932, 2, 27, 2, 30, "London", "UK")

    relationship_score_factory = RelationshipScoreFactory(richart_burton, liz_taylor)
    relationship_score = relationship_score_factory.get_relationship_score()

    print("Richard Burton and Elizabeth Taylor relationship score:")
    print(relationship_score.score_value)
    print(relationship_score.score_description)
    print(relationship_score.is_destiny_sign)
    print(len(relationship_score.aspects))
    print(len(relationship_score_factory._synastry_aspects))

    print("------------------->")
    dario_fo = AstrologicalSubject("Dario Fo", 1926, 3, 24, 12, 25, "Sangiano", "IT")
    franca_rame = AstrologicalSubject("Franca Rame", 1929, 7, 18, 12, 25, "Parabiago", "IT")

    relationship_score_factory = RelationshipScoreFactory(dario_fo, franca_rame)
    relationship_score = relationship_score_factory.get_relationship_score()

    print("Dario Fo and Franca Rame relationship score:")
    print(relationship_score.score_value)
    print(relationship_score.score_description)
    print(relationship_score.is_destiny_sign)
    print(len(relationship_score.aspects))
    print(len(relationship_score_factory._synastry_aspects))
