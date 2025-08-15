"""
House Comparison Data Models

Pydantic models for house comparison analysis results between astrological subjects.
Structures data output from house comparison calculations.

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from kerykeion.kr_types import SubscriptableBaseModel
from typing import Optional


class PointInHouseModel(SubscriptableBaseModel):
    """
    Represents an astrological point from one subject positioned within another subject's house.

    Captures point characteristics and its placement within the target subject's house system
    for house comparison analysis.

    Attributes:
        point_name: Name of the astrological point
        point_degree: Degree position within its sign
        point_sign: Zodiacal sign containing the point
        point_owner_name: Name of the subject who owns this point
        point_owner_house_number: House number in owner's chart
        point_owner_house_name: House name in owner's chart
        projected_house_number: House number in target subject's chart
        projected_house_name: House name in target subject's chart
        projected_house_owner_name: Name of the target subject
    """

    point_name: str
    """Name of the astrological point"""
    point_degree: float
    """Degree position of the point within its zodiacal sign"""
    point_sign: str
    """Zodiacal sign containing the point"""
    point_owner_name: str
    """Name of the subject who owns this point"""
    point_owner_house_number: Optional[int]
    """House number in owner's chart"""
    point_owner_house_name: Optional[str]
    """House name in owner's chart"""
    projected_house_number: int
    """House number in target subject's chart"""
    projected_house_name: str
    """House name in target subject's chart"""
    projected_house_owner_name: str
    """Name of the target subject"""


class HouseComparisonModel(SubscriptableBaseModel):
    """
    Bidirectional house comparison analysis between two astrological subjects.

    Contains results of how astrological points from each subject interact with
    the house system of the other subject.

    Attributes:
        first_subject_name: Name of the first subject
        second_subject_name: Name of the second subject
        first_points_in_second_houses: First subject's points in second subject's houses
        second_points_in_first_houses: Second subject's points in first subject's houses
    """

    first_subject_name: str
    """Name of the first subject"""
    second_subject_name: str
    """Name of the second subject"""
    first_points_in_second_houses: list[PointInHouseModel]
    """First subject's points positioned in second subject's houses"""
    second_points_in_first_houses: list[PointInHouseModel]
    """Second subject's points positioned in first subject's houses"""
