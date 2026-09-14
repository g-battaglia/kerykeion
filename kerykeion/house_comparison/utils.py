"""
House Comparison Utilities

Utility functions for calculating house placement relationships between astrological subjects.
Provides core calculation logic for determining where points from one subject fall within
another subject's house system.

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from kerykeion.schemas.models import AstrologicalSubjectModel, PlanetReturnModel, PointInHouseModel
from kerykeion.schemas.literals import AstrologicalPoint
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS
from kerykeion.utilities.core import get_planet_house, get_house_number, get_houses_list
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
    house_cusps = [h.abs_pos for h in get_houses_list(house_subject)]

    # Ordered list of house cusps degrees for point_subject
    point_subject_house_cusps = [h.abs_pos for h in get_houses_list(point_subject)]

    # For each point, determine which house it falls in
    for point in celestial_points:
        point_degree = point.abs_pos
        house_name = get_planet_house(point_degree, house_cusps)
        house_number = get_house_number(house_name)

        # Which house the point is in its own chart: the model already says, and
        # says it right where the reader cannot — an angle that IS one of several
        # coincident cusps opens its own house, which the twelve numbers alone do
        # not tell. The reader is only for a point that carries no house.
        point_owner_house_name = point.house or get_planet_house(point_degree, point_subject_house_cusps)
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

    # Iterate through each house cusp of the cusp_subject.
    # get_houses_list returns the cusps in order (First_House .. Twelfth_House),
    # so the cusp's own house number is its position in that list. Parsing the
    # number out of the cusp name is unreliable: the canonical names carry no
    # digits ("First_House", not "House 1").
    for cusp_index, cusp in enumerate(cusp_subject_houses, start=1):
        # Get the cusp's absolute position
        point_degree = cusp.abs_pos

        # Determine which house this cusp falls into in the house_subject's system
        try:
            projected_house_name = get_planet_house(point_degree, house_subject_cusps)
            projected_house_number = get_house_number(projected_house_name)
        except ValueError:
            # Skip if cusp doesn't fall within any house (shouldn't happen with valid data)
            continue

        # The cusp's original house number is simply its ordinal position
        cusp_house_number = cusp_index

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
