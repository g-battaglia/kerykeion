# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""

from kerykeion import AstrologicalSubject
from kerykeion.aspects.synastry_aspects import SynastryAspects
import logging
from pathlib import Path
from typing import Union


class RelationshipScore:
    """
    Calculates the relevance of the relationship of the two subjects according to
    Ciro Discepolo method.

    Results:
        - From 0 to 5 = Null relationship
        - From 5 a 10 = Mediocre relationship
        - From 10 to 15 = Important relationship
        - From 15 to 20 = Very important relationship
        - From 20 to su = Exceptional relationship

    Documentation at:
    http://www.cirodiscepolo.it/Articoli/Discepoloele.htm

    Args:
        first_subject (AstrologicalSubject): First subject kerykeion instance
        second_subject (AstrologicalSubject): Second subject kerykeion instance

    """

    first_subject: AstrologicalSubject
    second_subject: AstrologicalSubject
    score: int
    is_destiny_sign: bool
    relevant_aspects: list
    relevant_default_aspects: list

    def __init__(
        self,
        first_subject: AstrologicalSubject,
        second_subject: AstrologicalSubject,
        new_settings_file: Union[Path, None] = None,
    ):
        self.first_subject = first_subject
        self.second_subject = second_subject
        self.score = 0
        self.is_destiny_sign = False
        self.relevant_aspects = []
        self.relevant_default_aspects = []
        self.__all_synastry_aspects = SynastryAspects(
            first_subject, second_subject, new_settings_file=new_settings_file
        ).all_aspects

        # Calculates all at initialization
        self._get_all()

    def __str__(self) -> str:
        return f"CuppleScoreInstance: {self.first_subject.name} and {self.second_subject.name}, score: {self.score}"

    def __dict__(self):
        return {
            "first_subject_name": self.first_subject.name,
            "second_subject_name": self.second_subject.name,
            "score": self.score,
            "relevant_aspects": self.relevant_aspects,
            "relevant_default_aspects": self.relevant_default_aspects,
            "is_destiny_sign": self.is_destiny_sign,
        }

    def _log_aspect(self, aspect: dict, points: int) -> None:
        logging.debug(
            f"{points} Points: {aspect['p1_name']} {aspect['aspect']} {aspect['p2_name']}, rounded orbit: {int(aspect['orbit'])}"
        )

    def _evaluate_destiny_sign(self) -> int:
        """
        5 points if is a destiny sign:
        """
        if self.first_subject.sun["quality"] == self.second_subject.sun["quality"]:
            logging.debug(
                f'5 points: Destiny sign, {self.first_subject.sun["sign"]} and {self.second_subject.sun["sign"]}'
            )
            self.is_destiny_sign = True
            return 5

        return 0

    def _check_if_sun_sun_aspect(self, aspect: dict, log: bool = True) -> int:
        """
        8 points if Sun conjunction/opposition/square to Sun,
        11 if diff <= 2 degrees:
        """
        aspect_types = ["conjunction", "opposition", "square"]

        if (aspect["p1_name"] == "Sun" and aspect["p2_name"] == "Sun") and (aspect["aspect"] in aspect_types):
            self.relevant_default_aspects.append(aspect)

            if aspect["orbit"] <= 2:
                score = 11

                self._log_aspect(aspect, score)
                self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

                return score
            else:
                score = 8

                self._log_aspect(aspect, score)
                self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

                return score

        return 0

    def _check_if_sun_moon_conjunction(self, aspect: dict) -> int:
        """
        8 points if Moon conjunction/opposition/square to Moon,
        11 if diff <= 2 degrees:
        """
        planets = set(["Moon", "Sun"])

        if set([aspect["p1_name"], aspect["p2_name"]]) == planets and aspect["aspect"] == "conjunction":
            self.relevant_default_aspects.append(aspect)

            if aspect["orbit"] <= 2:
                score = 11

                self._log_aspect(aspect, score)
                self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

                return score

            else:
                score = 8

                self._log_aspect(aspect, score)
                self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

                return score

        return 0

    def _check_if_sun_moon_asc_aspect(self, aspect: dict) -> int:
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
        planets = set(["Venus", "Mars"])
        if set([aspect["p1_name"], aspect["p2_name"]]) == planets:
            score = 4
            self.relevant_default_aspects.append(aspect)

            self._log_aspect(aspect, score)
            self.relevant_aspects.append(self._create_aspects_dictionary(aspect, score))

            return score

        return 0

    def _create_aspects_dictionary(self, aspect: dict, score: int) -> dict:
        return {
            "points": score,
            "p1_name": aspect["p1_name"],
            "p2_name": aspect["p2_name"],
            "aspect": aspect["aspect"],
            "orbit": aspect["orbit"],
        }

    def _get_all(self) -> None:
        self.score += self._evaluate_destiny_sign()

        for a in self.__all_synastry_aspects:
            self.score += self._check_if_sun_sun_aspect(a)
            self.score += self._check_if_sun_moon_conjunction(a)
            self.score += self._check_if_sun_moon_asc_aspect(a)
            self.score += self._check_if_venus_mars_aspect(a)


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    setup_logging(level="debug")

    lui = AstrologicalSubject("John", 1975, 10, 10, 21, 15, "Roma", "IT")
    lei = AstrologicalSubject("Sarah", 1978, 2, 9, 15, 50, "Roma", "IT")

    score = RelationshipScore(lui, lei)
    print(score.__dict__()["score"])
    print(score.__dict__()["is_destiny_sign"])
    print(score.__dict__()["relevant_aspects"][0])
