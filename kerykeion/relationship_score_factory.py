# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects.synastry_aspects import SynastryAspects
import logging
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, RelationshipScoreAspectModel, RelationshipScoreModel
from kerykeion.kr_types.kr_literals import RelationshipScoreDescription

# Scoring constants
DESTINY_SIGN_POINTS = 5
HIGH_PRECISION_ORBIT_THRESHOLD = 2
MAJOR_ASPECT_POINTS_HIGH_PRECISION = 11
MAJOR_ASPECT_POINTS_STANDARD = 8
MINOR_ASPECT_POINTS = 4
SUN_ASCENDANT_ASPECT_POINTS = 4
MOON_ASCENDANT_ASPECT_POINTS = 4
VENUS_MARS_ASPECT_POINTS = 4


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
        first_subject (AstrologicalSubjectModel): First subject instance
        second_subject (AstrologicalSubjectModel): Second subject instance
    """

    SCORE_MAPPING = [
        ("Minimal", 5),
        ("Medium", 10),
        ("Important", 15),
        ("Very Important", 20),
        ("Exceptional", 30),
        ("Rare Exceptional", float("inf")),
    ]

    MAJOR_ASPECTS = {"conjunction", "opposition", "square", "trine", "sextile"}

    def __init__(
        self,
        first_subject: AstrologicalSubjectModel,
        second_subject: AstrologicalSubjectModel,
        use_only_major_aspects: bool = True,
    ):
        self.use_only_major_aspects = use_only_major_aspects
        self.first_subject: AstrologicalSubjectModel = first_subject
        self.second_subject: AstrologicalSubjectModel = second_subject

        self.score_value = 0
        self.relationship_score_description: RelationshipScoreDescription = "Minimal"
        self.is_destiny_sign = True
        self.relationship_score_aspects: list[RelationshipScoreAspectModel] = []
        self._synastry_aspects = SynastryAspects(self.first_subject, self.second_subject).all_aspects

    def _evaluate_destiny_sign(self):
        """
        Evaluates if the subjects share the same sun sign quality and adds points if true.
        """
        if self.first_subject.sun["quality"] == self.second_subject.sun["quality"]: # type: ignore
            self.is_destiny_sign = True
            self.score_value += DESTINY_SIGN_POINTS
            logging.debug(f"Destiny sign found, adding {DESTINY_SIGN_POINTS} points, total score: {self.score_value}")

    def _evaluate_aspect(self, aspect, points):
        """
        Evaluates an aspect and adds points to the score.

        Args:
            aspect (dict): Aspect information.
            points (int): Points to add.
        """
        if self.use_only_major_aspects and aspect["aspect"] not in self.MAJOR_ASPECTS:
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
            points = MAJOR_ASPECT_POINTS_HIGH_PRECISION if aspect["orbit"] <= HIGH_PRECISION_ORBIT_THRESHOLD else MAJOR_ASPECT_POINTS_STANDARD
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
            points = MAJOR_ASPECT_POINTS_HIGH_PRECISION if aspect["orbit"] <= HIGH_PRECISION_ORBIT_THRESHOLD else MAJOR_ASPECT_POINTS_STANDARD
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_sun_other_aspects(self, aspect):
        """
        Evaluates Sun-Sun aspects that are not conjunctions and adds points accordingly:
        - 4 points for other aspects

        Args:
            aspect (dict): Aspect information.
        """
        if aspect["p1_name"] == "Sun" and aspect["p2_name"] == "Sun" and aspect["aspect"] not in {"conjunction", "opposition", "square"}:
            points = MINOR_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_moon_other_aspects(self, aspect):
        """
        Evaluates Sun-Moon aspects that are not conjunctions and adds points accordingly:
        - 4 points for other aspects

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Moon", "Sun"} and aspect["aspect"] != "conjunction":
            points = MINOR_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_ascendant_aspect(self, aspect):
        """
        Evaluates Sun-Ascendant aspects and adds points accordingly:
        - 4 points for any aspect

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Sun", "Ascendant"}:
            points = SUN_ASCENDANT_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_moon_ascendant_aspect(self, aspect):
        """
        Evaluates Moon-Ascendant aspects and adds points accordingly:
        - 4 points for any aspect

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Moon", "Ascendant"}:
            points = MOON_ASCENDANT_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_venus_mars_aspect(self, aspect):
        """
        Evaluates Venus-Mars aspects and adds points accordingly:
        - 4 points for any aspect

        Args:
            aspect (dict): Aspect information.
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Venus", "Mars"}:
            points = VENUS_MARS_ASPECT_POINTS
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

    john = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", lng=53.416666, lat=-3, tz_str="Europe/London")
    yoko = AstrologicalSubjectFactory.from_birth_data("Yoko Ono", 1933, 2, 18, 20, 30, "Tokyo", "JP", lng=35.68611, lat=139.7525, tz_str="Asia/Tokyo")

    factory = RelationshipScoreFactory(john, yoko)
    score = factory.get_relationship_score()

    # Remove subjects key
    score.subjects = []
    print(score.model_dump_json(indent=4))
