from typing import Optional
from pydantic import BaseModel
from kerykeion import AstrologicalSubject
from kerykeion.utilities import get_planet_house, get_house_number


class PointInHouseModel(BaseModel):
    """Represents a point from one chart positioned in a house from another chart"""

    point_name: str
    """Name of the celestial point"""
    point_degree: float
    """Degree of the celestial point"""
    point_sign: str
    """Sign of the celestial point"""
    point_owner_name: str
    """Name of the owner of the celestial point"""
    house_number: int
    """Number of the house"""
    house_name: str
    """Name of the house"""
    house_owner_name: str
    """Name of the owner of the house"""

    def __str__(self) -> str:
        return f"{self.point_name} of {self.point_owner_name} at {self.point_degree}° {self.point_sign} in {self.house_owner_name}'s {self.house_number} house"


class HouseComparisonModel(BaseModel):
    """Pydantic model for any two-chart comparison analysis"""

    first_subject_name: str
    """Name of the first subject"""
    second_subject_name: str
    """Name of the second subject"""
    first_points_in_second_houses: list[PointInHouseModel]
    """List of points from the first subject in the houses of the second subject"""
    second_points_in_first_houses: Optional[list[PointInHouseModel]] = None
    """List of points from the second subject in the houses of the first subject"""


def calculate_points_in_houses(
    point_subject: AstrologicalSubject, house_subject: AstrologicalSubject
) -> list[PointInHouseModel]:
    """
    Calculates which houses of the house_subject the points of point_subject fall into.

    Args:
        point_subject: Subject whose points are being analyzed
        house_subject: Subject whose houses are being considered

    Returns:
        List of PointInHouseModel objects
    """
    points_in_houses: list[PointInHouseModel] = []

    # List of points to consider
    celestial_points = []

    for point in point_subject.planets_names_list:
        point_obj = getattr(point_subject, point.lower())
        if point_obj is not None:
            celestial_points.append(point_obj)

    for axis in point_subject.axial_cusps_names_list:
        axis_obj = getattr(point_subject, axis.lower())
        if axis_obj is not None:
            celestial_points.append(axis_obj)

    # Ordered list of house cusps degrees
    house_cusps = [
        house_subject.first_house.abs_pos,
        house_subject.second_house.abs_pos,
        house_subject.third_house.abs_pos,
        house_subject.fourth_house.abs_pos,
        house_subject.fifth_house.abs_pos,
        house_subject.sixth_house.abs_pos,
        house_subject.seventh_house.abs_pos,
        house_subject.eighth_house.abs_pos,
        house_subject.ninth_house.abs_pos,
        house_subject.tenth_house.abs_pos,
        house_subject.eleventh_house.abs_pos,
        house_subject.twelfth_house.abs_pos,
    ]

    # For each point, determine which house it falls in
    for point in celestial_points:
        if point is None:
            continue

        point_degree = point.abs_pos
        house_name = get_planet_house(point_degree, house_cusps)
        house_number = get_house_number(house_name)

        point_in_house = PointInHouseModel(
            point_name=point.name,
            point_degree=point.position,
            point_sign=point.sign,
            point_owner_name=point_subject.name,
            house_number=house_number,
            house_name=house_name,
            house_owner_name=house_subject.name,
        )

        points_in_houses.append(point_in_house)

    return points_in_houses


class HouseComparisonFactory:

    def __init__(self, first_subject: AstrologicalSubject, second_subject: AstrologicalSubject):
        self.first_subject = first_subject
        self.second_subject = second_subject

    def get_house_comparison(self) -> HouseComparisonModel:
        """
        Creates a house comparison model for two astrological subjects.

        Args:
            chart1: First astrological subject
            chart2: Second astrological subject
            description: Description of the comparison

        Returns:
            HouseComparisonModel object
        """
        first_points_in_second_houses = calculate_points_in_houses(self.first_subject, self.second_subject)
        second_points_in_first_houses = calculate_points_in_houses(self.second_subject, self.first_subject)

        return HouseComparisonModel(
            first_subject_name=self.first_subject.name,
            second_subject_name=self.second_subject.name,
            first_points_in_second_houses=first_points_in_second_houses,
            second_points_in_first_houses=second_points_in_first_houses,
        )


if __name__ == "__main__":
    natal_chart = AstrologicalSubject("Person A", 1990, 5, 15, 10, 30, "Rome", "IT")
    partner_chart = AstrologicalSubject("Person B", 1992, 8, 23, 14, 45, "Milan", "IT")

    factory = HouseComparisonFactory(natal_chart, partner_chart)
    comparison = factory.get_house_comparison()

    print(comparison.model_dump_json(indent=4))
