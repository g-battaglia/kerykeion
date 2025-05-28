from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, PlanetReturnModel
from kerykeion.kr_types.kr_literals import AstrologicalPoint
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS
from kerykeion.utilities import get_planet_house, get_house_number
from kerykeion.house_comparison.house_comparison_models import PointInHouseModel
from typing import Union


def calculate_points_in_reciprocal_houses(
    point_subject: Union[AstrologicalSubjectModel, PlanetReturnModel],
    house_subject: Union[AstrologicalSubjectModel, PlanetReturnModel],
    active_points: list[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS,
) -> list[PointInHouseModel]:
    """
    Calculates which houses of the house_subject the points of point_subject fall into.

    Args:
        point_subject: Subject whose points are being analyzed
        house_subject: Subject whose houses are being considered
        active_points: Optional list of point names to process. If None, all points are processed.

    Returns:
        List of PointInHouseModel objects
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
