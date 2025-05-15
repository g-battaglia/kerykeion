from kerykeion.kr_types import SubscriptableBaseModel
from typing import Optional


class PointInHouseModel(SubscriptableBaseModel):
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


class HouseComparisonModel(SubscriptableBaseModel):
    """Pydantic model for comparing points in houses between two astrological subjects"""

    first_subject_name: str
    """Name of the first subject"""
    second_subject_name: str
    """Name of the second subject"""
    first_points_in_second_houses: list[PointInHouseModel]
    """List of points from the first subject in the houses of the second subject"""
    second_points_in_first_houses: list[PointInHouseModel]
    """List of points from the second subject in the houses of the first subject"""

    def __str__(self) -> str:
        return f"House Comparison between {self.first_subject_name} and {self.second_subject_name}"
