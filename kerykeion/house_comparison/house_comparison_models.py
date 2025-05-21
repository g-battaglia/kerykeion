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
    point_owner_house_number: Optional[int]
    """House number of the point of the owner of the celestial point"""
    point_owner_house_name: Optional[str]
    """House name of the point of the owner of the celestial point"""
    projected_house_number: int
    """Number of the house where the point is projected"""
    projected_house_name: str
    """Name of the house where the point is projected"""
    projected_house_owner_name: str
    """Name of the owner of the house where the point is projected"""


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
