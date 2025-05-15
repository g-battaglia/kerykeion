from kerykeion import AstrologicalSubject
from kerykeion.utilities import get_planet_house, get_house_number
from kerykeion.house_comparison.house_comparison_models import PointInHouseModel


def calculate_points_in_reciprocal_houses(
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

