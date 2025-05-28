from kerykeion.house_comparison.house_comparison_utils import calculate_points_in_reciprocal_houses
from typing import Union
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS
from kerykeion.house_comparison.house_comparison_models import HouseComparisonModel
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.kr_types import AstrologicalSubjectModel, PlanetReturnModel
from kerykeion.kr_types.kr_literals import AstrologicalPoint


class HouseComparisonFactory:
    """
    Factory class for creating house comparison analyses between two astrological charts.

    This class handles the generation of house comparison data, calculating how planets
    from one chart interact with the house system of another chart (and vice versa).
    This is useful for synastry analysis and other forms of relationship astrology.

    Attributes:
        first_subject (AstrologicalSubject): The first person's astrological chart
        second_subject (AstrologicalSubject): The second person's astrological chart

    Example:
        >>> natal_chart = AstrologicalSubjectFactory.from_birth_data("Person A", 1990, 5, 15, 10, 30, "Rome", "IT")
        >>> partner_chart = AstrologicalSubjectFactory.from_birth_data("Person B", 1992, 8, 23, 14, 45, "Milan", "IT")
        >>> factory = HouseComparisonFactory(natal_chart, partner_chart)
        >>> comparison = factory.get_house_comparison()
        >>> print(comparison.model_dump_json(indent=4))

    """
    def __init__(self,
                 first_subject: Union["AstrologicalSubjectModel", "PlanetReturnModel"],
                 second_subject: Union["AstrologicalSubjectModel", "PlanetReturnModel"],
                active_points: list[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,

        ):
        self.first_subject = first_subject
        self.second_subject = second_subject
        self.active_points = active_points

    def get_house_comparison(self) -> "HouseComparisonModel":
        """
        Creates a house comparison model for two astrological subjects.

        Args:
            chart1: First astrological subject
            chart2: Second astrological subject
            description: Description of the comparison

        Returns:
            "HouseComparisonModel": Model containing the comparison data.
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
