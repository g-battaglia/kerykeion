# -*- coding: utf-8 -*-
"""
Relationship Score Factory Module

This module calculates relationship scores between two astrological subjects using the
Ciro Discepolo method. It analyzes synastry aspects to generate numerical compatibility
scores with descriptive categories.

Key Features:
    - Point-based scoring system using synastry aspects
    - Configurable major/minor aspect filtering
    - Orbital precision weighting
    - Categorical score descriptions

Score Categories:
    - 0-5: Minimal relationship
    - 5-10: Medium relationship
    - 10-15: Important relationship
    - 15-20: Very important relationship
    - 20-30: Exceptional relationship
    - 30+: Rare exceptional relationship

Classes:
    RelationshipScoreFactory: Main factory for calculating relationship scores

Example:
    >>> from kerykeion import AstrologicalSubjectFactory
    >>> from kerykeion.relationship_score_factory import RelationshipScoreFactory
    >>>
    >>> person1 = AstrologicalSubjectFactory.from_birth_data("John", 1990, 5, 15, 12, 0, "New York", "US")
    >>> person2 = AstrologicalSubjectFactory.from_birth_data("Jane", 1988, 8, 22, 14, 30, "London", "GB")
    >>> factory = RelationshipScoreFactory(person1, person2)
    >>> score = factory.get_relationship_score()
    >>> print(f"Score: {score.score_value} ({score.score_description})")

Reference:
    Ciro Discepolo Method: http://www.cirodiscepolo.it/Articoli/Discepoloele.htm

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects.synastry_aspects_factory import SynastryAspectsFactory
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
    Calculates relationship scores between two subjects using the Ciro Discepolo method.

    The scoring system evaluates synastry aspects between planetary positions to generate
    numerical compatibility scores with categorical descriptions.

    Score Ranges:
        - 0-5: Minimal relationship
        - 5-10: Medium relationship
        - 10-15: Important relationship
        - 15-20: Very important relationship
        - 20-30: Exceptional relationship
        - 30+: Rare exceptional relationship

    Args:
        first_subject (AstrologicalSubjectModel): First astrological subject
        second_subject (AstrologicalSubjectModel): Second astrological subject
        use_only_major_aspects (bool, optional): Filter to major aspects only. Defaults to True.

    Reference:
        http://www.cirodiscepolo.it/Articoli/Discepoloele.htm
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
        self._synastry_aspects = SynastryAspectsFactory.from_subjects(self.first_subject, self.second_subject).all_aspects

    def _evaluate_destiny_sign(self):
        """
        Checks if subjects share the same sun sign quality and adds points.

        Adds 5 points if both subjects have sun signs with matching quality
        (cardinal, fixed, or mutable).
        """
        if self.first_subject.sun["quality"] == self.second_subject.sun["quality"]: # type: ignore
            self.is_destiny_sign = True
            self.score_value += DESTINY_SIGN_POINTS
            logging.debug(f"Destiny sign found, adding {DESTINY_SIGN_POINTS} points, total score: {self.score_value}")

    def _evaluate_aspect(self, aspect, points):
        """
        Processes an aspect and adds points to the total score.

        Args:
            aspect (dict): Aspect data containing planetary positions and geometry
            points (int): Points to add to the total score
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
        Evaluates Sun-Sun conjunction, opposition, or square aspects.

        Adds 8 points for standard orbs, 11 points for tight orbs (≤2°).

        Args:
            aspect (dict): Aspect data
        """
        if aspect["p1_name"] == "Sun" and aspect["p2_name"] == "Sun" and aspect["aspect"] in {"conjunction", "opposition", "square"}:
            points = MAJOR_ASPECT_POINTS_HIGH_PRECISION if aspect["orbit"] <= HIGH_PRECISION_ORBIT_THRESHOLD else MAJOR_ASPECT_POINTS_STANDARD
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_moon_conjunction(self, aspect):
        """
        Evaluates Sun-Moon conjunction aspects.

        Adds 8 points for standard orbs, 11 points for tight orbs (≤2°).

        Args:
            aspect (dict): Aspect data
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Moon", "Sun"} and aspect["aspect"] == "conjunction":
            points = MAJOR_ASPECT_POINTS_HIGH_PRECISION if aspect["orbit"] <= HIGH_PRECISION_ORBIT_THRESHOLD else MAJOR_ASPECT_POINTS_STANDARD
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_sun_other_aspects(self, aspect):
        """
        Evaluates Sun-Sun aspects other than conjunction, opposition, or square.

        Adds 4 points for any qualifying aspect.

        Args:
            aspect (dict): Aspect data
        """
        if aspect["p1_name"] == "Sun" and aspect["p2_name"] == "Sun" and aspect["aspect"] not in {"conjunction", "opposition", "square"}:
            points = MINOR_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_moon_other_aspects(self, aspect):
        """
        Evaluates Sun-Moon aspects other than conjunctions.

        Adds 4 points for any qualifying aspect.

        Args:
            aspect (dict): Aspect data
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Moon", "Sun"} and aspect["aspect"] != "conjunction":
            points = MINOR_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_sun_ascendant_aspect(self, aspect):
        """
        Evaluates Sun-Ascendant aspects.

        Adds 4 points for any aspect between Sun and Ascendant.

        Args:
            aspect (dict): Aspect data
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Sun", "Ascendant"}:
            points = SUN_ASCENDANT_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_moon_ascendant_aspect(self, aspect):
        """
        Evaluates Moon-Ascendant aspects.

        Adds 4 points for any aspect between Moon and Ascendant.

        Args:
            aspect (dict): Aspect data
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Moon", "Ascendant"}:
            points = MOON_ASCENDANT_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_venus_mars_aspect(self, aspect):
        """
        Evaluates Venus-Mars aspects.

        Adds 4 points for any aspect between Venus and Mars.

        Args:
            aspect (dict): Aspect data
        """
        if {aspect["p1_name"], aspect["p2_name"]} == {"Venus", "Mars"}:
            points = VENUS_MARS_ASPECT_POINTS
            self._evaluate_aspect(aspect, points)

    def _evaluate_relationship_score_description(self):
        """
        Determines the categorical description based on the numerical score.

        Maps the total score to predefined description ranges.
        """
        for description, threshold in self.SCORE_MAPPING:
            if self.score_value < threshold:
                self.relationship_score_description = description
                break

    def get_relationship_score(self):
        """
        Calculates the complete relationship score using all evaluation methods.

        Returns:
            RelationshipScoreModel: Score object containing numerical value, description,
                destiny sign status, contributing aspects, and subject data.
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
