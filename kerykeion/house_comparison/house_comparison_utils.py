"""
House Comparison Utilities

Utility functions for calculating house placement relationships between astrological subjects.
Provides core calculation logic for determining where points from one subject fall within
another subject's house system.

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from kerykeion.schemas.kr_models import AstrologicalSubjectModel, PlanetReturnModel, PointInHouseModel
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS
from kerykeion.utilities import get_planet_house, get_house_number, get_houses_list
from typing import Union


def calculate_points_in_reciprocal_houses(
    point_subject: Union[AstrologicalSubjectModel, PlanetReturnModel],
    house_subject: Union[AstrologicalSubjectModel, PlanetReturnModel],
    active_points: list[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,
) -> list[PointInHouseModel]:
    """
    Calculate house placements of one subject's points within another subject's house system.

    Analyzes where each astrological point from the point_subject falls within the
    house structure of the house_subject. Creates detailed mapping including both
    the point's original house position and its projected house placement.

    Args:
        point_subject: Subject whose astrological points are being analyzed
        house_subject: Subject whose house system provides the projection framework
        active_points: List of astrological points to include in the analysis.
                      Defaults to standard active points configuration.

    Returns:
        list[PointInHouseModel]: List of point placement models containing detailed
                                information about each point's house relationships,
                                including original and projected house positions.

    Note:
        Only processes points that exist in both the point_subject's active_points
        and the provided active_points list. Points with None values are skipped.

    Example:
        >>> points_in_houses = calculate_points_in_reciprocal_houses(
        ...     natal_chart, partner_chart, ["Sun", "Moon"]
        ... )
        >>> sun_placement = points_in_houses[0]  # Assuming Sun is first
        >>> print(f"Sun falls in house: {sun_placement.projected_house_name}")
    """
    points_in_houses: list[PointInHouseModel] = []

    # List of points to consider
    celestial_points = []

    for point in point_subject.active_points:
        if point not in active_points:
            continue

        point_obj = getattr(point_subject, point.lower())
        if point_obj is not None:
            celestial_points.append(point_obj)

    # Ordered list of house cusps degrees for house_subject
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

    # Ordered list of house cusps degrees for point_subject
    point_subject_house_cusps = [
        point_subject.first_house.abs_pos,
        point_subject.second_house.abs_pos,
        point_subject.third_house.abs_pos,
        point_subject.fourth_house.abs_pos,
        point_subject.fifth_house.abs_pos,
        point_subject.sixth_house.abs_pos,
        point_subject.seventh_house.abs_pos,
        point_subject.eighth_house.abs_pos,
        point_subject.ninth_house.abs_pos,
        point_subject.tenth_house.abs_pos,
        point_subject.eleventh_house.abs_pos,
        point_subject.twelfth_house.abs_pos,
    ]

    # For each point, determine which house it falls in
    for point in celestial_points:
        if point is None:
            continue

        point_degree = point.abs_pos
        house_name = get_planet_house(point_degree, house_cusps)
        house_number = get_house_number(house_name)

        # Find which house the point is in its own chart (point_subject)
        point_owner_house_name = get_planet_house(point_degree, point_subject_house_cusps)
        point_owner_house_number = get_house_number(point_owner_house_name)

        point_in_house = PointInHouseModel(
            point_name=point.name,
            point_degree=point.position,
            point_sign=point.sign,
            point_owner_name=point_subject.name,
            point_owner_house_name=point_owner_house_name,
            point_owner_house_number=point_owner_house_number,
            projected_house_number=house_number,
            projected_house_name=house_name,
            projected_house_owner_name=house_subject.name,
        )

        points_in_houses.append(point_in_house)

    return points_in_houses


def calculate_cusps_in_reciprocal_houses(
    cusp_subject: Union[AstrologicalSubjectModel, PlanetReturnModel],
    house_subject: Union[AstrologicalSubjectModel, PlanetReturnModel],
) -> list[PointInHouseModel]:
    """
    Calculate house placements of one subject's house cusps within another subject's house system.

    Analyzes where each house cusp from the cusp_subject falls within the
    house structure of the house_subject. Creates detailed mapping including both
    the cusp's original house position and its projected house placement.

    Args:
        cusp_subject: Subject whose house cusps are being analyzed
        house_subject: Subject whose house system is used for projection

    Returns:
        List of PointInHouseModel objects representing cusp placements
    """
    cusps_in_houses = []

    # Get house cusps for both subjects
    cusp_subject_houses = get_houses_list(cusp_subject)
    house_subject_houses = get_houses_list(house_subject)

    # Extract house cusp degrees for projection calculation
    house_subject_cusps = [house.abs_pos for house in house_subject_houses]

    # Iterate through each house cusp of the cusp_subject
    for cusp in cusp_subject_houses:
        # Get the cusp's absolute position
        point_degree = cusp.abs_pos

        # Determine which house this cusp falls into in the house_subject's system
        try:
            projected_house_name = get_planet_house(point_degree, house_subject_cusps)
            projected_house_number = get_house_number(projected_house_name)
        except ValueError:
            # Skip if cusp doesn't fall within any house (shouldn't happen with valid data)
            continue

        # Get the cusp's original house information
        try:
            # Extract house number from cusp name (e.g., "House 1" -> 1)
            if " " in cusp.name:
                cusp_house_number = int(cusp.name.split()[1])
            else:
                # Fallback: try to extract digits from the name
                import re

                numbers = re.findall(r"\d+", cusp.name)
                cusp_house_number = int(numbers[0]) if numbers else 1
        except (IndexError, ValueError):
            # Fallback to sequential numbering if parsing fails
            cusp_house_number = cusp_subject_houses.index(cusp) + 1

        # Create PointInHouseModel for this cusp
        cusp_in_house = PointInHouseModel(
            point_name=cusp.name,
            point_degree=cusp.position,
            point_sign=cusp.sign,
            point_owner_name=cusp_subject.name,
            point_owner_house_number=cusp_house_number,
            point_owner_house_name=cusp.name,
            projected_house_number=projected_house_number,
            projected_house_name=projected_house_name,
            projected_house_owner_name=house_subject.name,
        )

        cusps_in_houses.append(cusp_in_house)

    return cusps_in_houses
