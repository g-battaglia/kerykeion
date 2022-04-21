"""
    This is part of Kerykeion (C) 2022 Giacomo Battaglia
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kerykeion import KrInstance
from kerykeion.aspects import CompositeAspects
from logging import basicConfig, Logger, getLogger
from pathlib import Path
from typing import Union

basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=20
)


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
        first_subject (KrInstance): First subject kerykeion instance
        second_subject (KrInstance): Second subject kerykeion instance
        logger (Union[Logger, None], optional): Instance of Logger if None creates new one. Defaults to None.

    """
    first_subject: KrInstance
    second_subject: KrInstance
    score: int
    is_destiny_sign: bool
    relevant_default_aspects: list
    relevant_default_aspects: list

    def __init__(self, first_subject: KrInstance, second_subject: KrInstance, logger: Union[Logger, None] = None, new_settings_file: Union[str, Path, None] = None):

        self.first_subject = first_subject
        self.second_subject = second_subject
        self.score = 0
        self.is_destiny_sign = False
        self.relevant_aspects = []
        self.relevant_default_aspects = []
        self.__logger: Logger = logger or getLogger(self.__class__.__name__)
        self.__all_composite_aspects = CompositeAspects(
            first_subject,
            second_subject,
            new_settings_file=new_settings_file
        ).get_all_aspects()

        # Calculates all at initialization
        self.__get_all()

    def __str__(self) -> str:
        return f'CuppleScoreInstance: {self.first_subject.name} and {self.second_subject.name}, score: {self.score}'

    def __dict__(self):
        return {
            'first_subject_name': self.first_subject.name,
            'second_subject_name': self.second_subject.name,
            'score': self.score,
            'relevant_aspects': self.relevant_aspects,
            'relevant_default_aspects': self.relevant_default_aspects,
            'is_destiny_sign': self.is_destiny_sign
        }

    def __log_aspect(self, aspect: dict, points: int) -> None:
        self.__logger.debug(
            f"{points} Points: {aspect['p1_name']} {aspect['aspect']} {aspect['p2_name']}, rounded orbit: {int(aspect['orbit'])}"
        )

    def __evaluate_destiny_sign(self) -> int:
        """5 points if is a destiny sign:"""
        if self.first_subject.sun['quality'] == self.second_subject.sun['quality']:
            self.__logger.debug(
                f'5 points: Destiny sign, {self.first_subject.sun["sign"]} and {self.second_subject.sun["sign"]}')
            self.is_destiny_sign = True
            return 5

        return 0

    def __check_if_sun_sun_aspect(self, aspect: dict, log: bool = True) -> int:
        """8 points if Sun conjunction/opposition/square to Sun,
         11 if diff <= 2 degrees:"""
        aspect_types = ['conjunction', 'opposition', 'square']

        if (aspect['p1_name'] == 'Sun' and aspect['p2_name'] == 'Sun') and (aspect['aspect'] in aspect_types):
            self.relevant_default_aspects.append(aspect)

            if aspect['orbit'] <= 2:
                score = 11

                if log:
                    self.__log_aspect(aspect, score)
                    self.relevant_aspects.append(
                        self.__create_aspects_dictionary(aspect, score))

                return score
            else:
                score = 8

                if log:
                    self.__log_aspect(aspect, score)
                    self.relevant_aspects.append(
                        self.__create_aspects_dictionary(aspect, score))

                return score

        return 0

    def __check_if_sun_moon_conjunction(self, aspect: dict, log: bool = True) -> int:
        """ 8 points if Moon conjunction/opposition/square to Moon,
        11 if diff <= 2 degrees: """
        planets = set(['Moon', 'Sun'])

        if (
            set([aspect['p1_name'], aspect['p2_name']]) == planets
            and aspect['aspect'] == 'conjunction'
        ):
            self.relevant_default_aspects.append(aspect)

            if aspect['orbit'] <= 2:
                score = 11

                if log:
                    self.__log_aspect(aspect, score)
                    self.relevant_aspects.append(
                        self.__create_aspects_dictionary(aspect, score))

                return score

            else:
                score = 8
                if log:
                    self.__log_aspect(aspect, score)
                    self.relevant_aspects.append(
                        self.__create_aspects_dictionary(aspect, score))

                return score

        return 0

    def __check_if_sun_moon_asc_aspect(self, aspect: dict, log: bool = True) -> int:
        planets = ["Sun", "Moon", "First House"]

        if self.__check_if_sun_sun_aspect(aspect, log=False) or self.__check_if_sun_moon_conjunction(aspect, log=False):
            return 0

        if (aspect['p1_name'] in planets and aspect['p2_name'] in planets):
            self.relevant_default_aspects.append(aspect)
            score = 4

            if log:
                self.__log_aspect(aspect, score)
                self.relevant_aspects.append(
                    self.__create_aspects_dictionary(aspect, score))

            return score

        return 0

    def __check_if_venus_mars_aspect(self, aspect: dict, log: bool = True) -> int:
        planets = set(['Venus', 'Mars'])
        if set([aspect['p1_name'], aspect['p2_name']]) == planets:
            score = 4
            self.relevant_default_aspects.append(aspect)

            if log:
                self.__log_aspect(aspect, score)
                self.relevant_aspects.append(
                    self.__create_aspects_dictionary(aspect, score))
                    
            return score

        return 0

    def __create_aspects_dictionary(self, aspect: dict, score: int) -> dict:
        return {
            'points': score,
            'p1_name': aspect['p1_name'],
            'p2_name': aspect['p2_name'],
            'aspect': 'conjunction',
            'orbit': aspect['orbit']
        }

    def __get_all(self) -> None:
        self.score += self.__evaluate_destiny_sign()

        for a in self.__all_composite_aspects:
            self.score += self.__check_if_sun_sun_aspect(a)
            self.score += self.__check_if_sun_moon_conjunction(a)
            self.score += self.__check_if_sun_moon_asc_aspect(a)
            self.score += self.__check_if_venus_mars_aspect(a)


if __name__ == '__main__':
    basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=10,
        force=True
    )
    lui = KrInstance("John", 1975, 10, 10, 21, 15, 'Roma', 'IT')
    lei = KrInstance("Sarah", 1978, 2, 9, 15, 50, 'Roma', 'IT')

    score = RelationshipScore(lui, lei)
    print(score.__dict__()['score'])
    print(score.__dict__()['is_destiny_sign'])
    print(score.__dict__()['relevant_aspects'][0])
