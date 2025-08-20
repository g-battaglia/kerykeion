"""
House Comparison Factory Module

Provides factory class for house comparison analysis between astrological subjects.
Enables bidirectional analysis of astrological point placements in house systems.

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from kerykeion.house_comparison.house_comparison_utils import calculate_points_in_reciprocal_houses
from typing import Union
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS
from kerykeion.schemas.kr_models import HouseComparisonModel
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.schemas import AstrologicalSubjectModel, PlanetReturnModel
from kerykeion.schemas.kr_literals import AstrologicalPoint


class HouseComparisonFactory:
    """
    Factory for creating house comparison analyses between two astrological subjects.

    Analyzes placement of astrological points from one subject within the house system
    of another subject, performing bidirectional analysis for synastry studies and
    subject comparisons. Supports both natal subjects and planetary return subjects.

    Attributes:
        first_subject: First astrological subject (natal or return subject)
        second_subject: Second astrological subject (natal or return subject)
        active_points: List of astrological points to include in analysis

    Example:
        >>> natal_chart = AstrologicalSubjectFactory.from_birth_data(
        ...     "Person A", 1990, 5, 15, 10, 30, "Rome", "IT"
        ... )
        >>> partner_chart = AstrologicalSubjectFactory.from_birth_data(
        ...     "Person B", 1992, 8, 23, 14, 45, "Milan", "IT"
        ... )
        >>> factory = HouseComparisonFactory(natal_chart, partner_chart)
        >>> comparison = factory.get_house_comparison()

    """
    def __init__(self,
                 first_subject: Union["AstrologicalSubjectModel", "PlanetReturnModel"],
                 second_subject: Union["AstrologicalSubjectModel", "PlanetReturnModel"],
                active_points: list[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,

        ):
        """
        Initialize the house comparison factory.

        Args:
            first_subject: First astrological subject for comparison
            second_subject: Second astrological subject for comparison
            active_points: List of astrological points to include in analysis.
                          Defaults to standard active points.

        Note:
            Both subjects must have valid house system data for accurate analysis.
        """
        self.first_subject = first_subject
        self.second_subject = second_subject
        self.active_points = active_points

    def get_house_comparison(self) -> "HouseComparisonModel":
        """
        Generate bidirectional house comparison analysis between the two subjects.

        Calculates where each active astrological point from one subject falls within
        the house system of the other subject, and vice versa.

        Returns:
            HouseComparisonModel: Model containing:
                - first_subject_name: Name of the first subject
                - second_subject_name: Name of the second subject
                - first_points_in_second_houses: First subject's points in second subject's houses
                - second_points_in_first_houses: Second subject's points in first subject's houses

        Note:
            Analysis scope is determined by the active_points list. Only specified
            points will be included in the results.
        """
        first_points_in_second_houses = calculate_points_in_reciprocal_houses(self.first_subject, self.second_subject, self.active_points)
        second_points_in_first_houses = calculate_points_in_reciprocal_houses(self.second_subject, self.first_subject, self.active_points)

        return HouseComparisonModel(
            first_subject_name=self.first_subject.name,
            second_subject_name=self.second_subject.name,
            first_points_in_second_houses=first_points_in_second_houses,
            second_points_in_first_houses=second_points_in_first_houses,
        )


if __name__ == "__main__":
    natal_chart = AstrologicalSubjectFactory.from_birth_data("Person A", 1990, 5, 15, 10, 30, "Rome", "IT")
    partner_chart = AstrologicalSubjectFactory.from_birth_data("Person B", 1992, 8, 23, 14, 45, "Milan", "IT")

    factory = HouseComparisonFactory(natal_chart, partner_chart)
    comparison = factory.get_house_comparison()

    print(comparison.model_dump_json(indent=4))
