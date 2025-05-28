# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects.synastry_aspects import SynastryAspects
import logging
from pathlib import Path
from typing import Union
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel
import warnings


class RelationshipScore:
    """
    Calculates the relevance of the relationship between two subjects using the Ciro Discepolo method.

    Results:
        - 0 to 5: Minimal relationship
        - 5 to 10: Medium relationship
        - 10 to 15: Important relationship
        - 15 to 20: Very important relationship
        - 20 and 35: Exceptional relationship
        - 35 and above: Rare Exceptional relationship

    Documentation: http://www.cirodiscepolo.it/Articoli/Discepoloele.htm

    Args:
        first_subject (AstrologicalSubject): First subject instance
        second_subject (AstrologicalSubject): Second subject instance
    """

    def __init__(
        self,
        first_subject: AstrologicalSubjectModel,
        second_subject: AstrologicalSubjectModel,
        new_settings_file: Union[Path, None] = None,
    ):
        warnings.warn(
            "The RelationshipScore class is deprecated and will be removed in a future version. Use RelationshipScoreFactory instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.first_subject = first_subject
        self.second_subject = second_subject
        self.score = 0
        self.is_destiny_sign = False
        self.relevant_aspects: list = []
        self.relevant_default_aspects: list = []
        self.__all_synastry_aspects = SynastryAspects(first_subject, second_subject, new_settings_file=new_settings_file).all_aspects

        # Calculate all aspects at initialization
        self._calculate_all()

    def __str__(self) -> str:
        return f"CoupleScoreInstance: {self.first_subject.name} and {self.second_subject.name}, score: {self.score}"

    def __dict__(self) -> dict: # type: ignore
        return {
            "first_subject_name": self.first_subject.name,
            "second_subject_name": self.second_subject.name,
            "score": self.score,
            "relevant_aspects": self.relevant_aspects,
            "relevant_default_aspects": self.relevant_default_aspects,
            "is_destiny_sign": self.is_destiny_sign,
        }

    def _log_aspect(self, aspect: dict, points: int) -> None:
        logging.debug(f"{points} Points: {aspect['p1_name']} {aspect['aspect']} {aspect['p2_name']}, rounded orbit: {int(aspect['orbit'])}")

    def _evaluate_destiny_sign(self) -> int:
        """
        Adds 5 points if the subjects share the same sun sign quality.
        """
        if self.first_subject.sun["quality"] == self.second_subject.sun["quality"]:
            logging.debug(f'5 points: Destiny sign, {self.first_subject.sun["sign"]} and {self.second_subject.sun["sign"]}')
            self.is_destiny_sign = True
            return 5
        return 0

    def _check_if_sun_sun_aspect(self, aspect: dict) -> int:
        """
        Adds points for Sun-Sun aspects:
        - 8 points for conjunction/opposition/square
        - 11 points if the aspect's orbit is <= 2 degrees
        """
        aspect_types = ["conjunction", "opposition", "square"]

        if aspect["p1_name"] == "Sun" and aspect["p2_name"] == "Sun" and aspect["aspect"] in aspect_types:
            self.relevant_default_aspects.append(aspect)
            score = 11 if aspect["orbit"] <= 2 else 8

            self._log_aspect(aspect, score)
            self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

            return score
        return 0

    def _check_if_sun_moon_conjunction(self, aspect: dict) -> int:
        """
        Adds points for Sun-Moon conjunction:
        - 8 points for conjunction
        - 11 points if the aspect's orbit is <= 2 degrees
        """
        planets = {"Moon", "Sun"}

        if {aspect["p1_name"], aspect["p2_name"]} == planets and aspect["aspect"] == "conjunction":
            self.relevant_default_aspects.append(aspect)
            score = 11 if aspect["orbit"] <= 2 else 8

            self._log_aspect(aspect, score)
            self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

            return score
        return 0

    def _check_if_sun_moon_asc_aspect(self, aspect: dict) -> int:
        """
        Adds 4 points for aspects involving Sun, Moon, and Ascendant.
        """
        planets = ["Sun", "Moon", "First_House"]

        if self._check_if_sun_sun_aspect(aspect) or self._check_if_sun_moon_conjunction(aspect):
            return 0

        if aspect["p1_name"] in planets and aspect["p2_name"] in planets:
            self.relevant_default_aspects.append(aspect)
            score = 4

            self._log_aspect(aspect, score)
            self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

            return score
        return 0

    def _check_if_venus_mars_aspect(self, aspect: dict) -> int:
        """
        Adds 4 points for Venus-Mars aspects.
        """
        planets = {"Venus", "Mars"}

        if {aspect["p1_name"], aspect["p2_name"]} == planets:
            score = 4
            self.relevant_default_aspects.append(aspect)

            self._log_aspect(aspect, score)
            self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

            return score
        return 0

    def _create_aspects_dictionary(self, aspect: dict, score: int) -> dict:
        """
        Creates a dictionary representation of an aspect with its score.
        """
        return {
            "points": score,
            "p1_name": aspect["p1_name"],
            "p2_name": aspect["p2_name"],
            "aspect": aspect["aspect"],
            "orbit": aspect["orbit"],
        }

    def _calculate_all(self) -> None:
        """
        Calculates the total score based on all relevant aspects.
        """
        self.score += self._evaluate_destiny_sign()

        for aspect in self.__all_synastry_aspects:
            self.score += self._check_if_sun_sun_aspect(aspect)
            self.score += self._check_if_sun_moon_conjunction(aspect)
            self.score += self._check_if_sun_moon_asc_aspect(aspect)
            self.score += self._check_if_venus_mars_aspect(aspect)
