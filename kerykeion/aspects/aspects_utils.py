# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""
# TODO: Better documentation and unit tests

from swisseph import difdeg2n
from typing import Union
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel
from kerykeion.schemas.kr_literals import AspectMovementType
from kerykeion.schemas.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS


def get_aspect_from_two_points(
    aspects_settings: Union[list[dict], list[dict]],
    point_one: Union[float, int],
    point_two: Union[float, int],
):
    """
    Utility function to calculate the aspects between two points.

    Args:
        aspects_settings (dict): Dictionary containing aspect settings.
        point_one (Union[float, int]): First point.
        point_two (Union[float, int]): Second point.

    Returns:
        dict: Dictionary containing the aspect details.
    """
    distance = abs(difdeg2n(point_one, point_two))
    diff = abs(point_one - point_two)

    for aid, aspect in enumerate(aspects_settings):
        # TODO: Remove the "degree" element EVERYWHERE!
        aspect_degree = aspect["degree"] # type: ignore
        aspect_orb = aspect["orb"] # type: ignore

        if (aspect_degree - aspect_orb) <= int(distance) <= (aspect_degree + aspect_orb):
            name = aspect["name"] # type: ignore
            aspect_degrees = aspect_degree
            verdict = True
            break
    else:
        verdict = False
        name = None
        aspect_degrees = 0

    return {
        "verdict": verdict,
        "name": name,
        "orbit": abs(distance - aspect_degrees),
        "distance": abs(distance - aspect_degrees),
        "aspect_degrees": aspect_degrees,
        "diff": diff,
    }


def _sign(x: float) -> int:
    """
    Return the sign of ``x``.

    Returns +1 if ``x`` > 0, -1 if ``x`` < 0, and 0 if ``x`` == 0.
    """
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


def calculate_aspect_movement(
    point_one_abs_pos: float,
    point_two_abs_pos: float,
    aspect_degrees: float,
    point_one_speed: float,
    point_two_speed: float,
) -> AspectMovementType:
    """
        Determine whether an aspect is applying, separating, or fixed.

        This implementation uses a dynamic definition based on the time evolution
        of the orb:

        - "Applying": the orb is decreasing with time (the aspect is moving toward
            exactness).
        - "Separating": the orb is increasing with time (the aspect has already
            perfected in the past, or will not perfect given the current motion).
        - "Fixed": both points are effectively fixed so the orb does not change.

        Motion direction (direct or retrograde) is taken from the sign of the
        speed values:

        - speed > 0: direct motion (increasing longitude)
        - speed < 0: retrograde motion (decreasing longitude)

        The algorithm does not assume which point is "faster" in absolute terms;
        it uses the relative motion to determine whether the orb is growing or
        shrinking.

        Definitions:

        - Longitudes are in degrees, 0 <= λ < 360 (normalized internally).
        - ``aspect_degrees`` is the nominal angle of the aspect; values > 180
            are made symmetric (e.g. 240° becomes 120°).
        - The orb is defined as::

                orb = abs(abs(separation) - aspect)

            where ``separation`` is the minimal angular distance between the two
            points in [-180, 180).

        Logical steps:

        1. Normalize longitudes to [0, 360) and the aspect to [0, 180].
        2. Compute the signed separation ``sep`` between the two points using
             ``difdeg2n``.
        3. Compute the current orb::

                     sep_abs = abs(sep)
                     orb = abs(sep_abs - aspect)

        4. Compute the relevant speed:
             - if both points move: ``moving_speed = point_two_speed - point_one_speed``
             - if one point is fixed (speed == 0): use the moving point speed
                 against the fixed point.
        5. The qualitative sign of the orb derivative is::

                     sign_d_orb = sign(sep_abs - aspect) * sign(sep) * sign(moving_speed)

             If ``sign_d_orb < 0`` the orb decreases (applying), if
             ``sign_d_orb > 0`` the orb increases (separating).
        6. If the relevant speed is exactly zero, the orb does not change over
             time; if it is not exact, it is considered separating by convention.

        Args:
                point_one_abs_pos: Absolute longitude of the first point in degrees.
                point_two_abs_pos: Absolute longitude of the second point in degrees.
                aspect_degrees: Nominal aspect angle (e.g. 0, 60, 90, 120, 180).
                point_one_speed: Speed of the first point in degrees/day (signed).
                point_two_speed: Speed of the second point in degrees/day (signed).

        Returns:
                AspectMovementType: ``"Applying"``, ``"Separating"`` or ``"Fixed"``.

        Raises:
                ValueError: If any of the speeds is ``None``.

        Examples:
                >>> # Fast Moon at 45° approaching Sun at 50° (conjunction)
                >>> calculate_aspect_movement(45, 50, 0, 12.5, 1.0)
                'Applying'

                >>> # Moon at 55° moving away from Sun at 50° (conjunction)
                >>> calculate_aspect_movement(55, 50, 0, 12.5, 1.0)
                'Separating'

                >>> # Mercury (fast) square Mars
                >>> calculate_aspect_movement(5, 100, 90, 1.5, 0.5)
                'Applying'

                >>> # Venus separating from a trine to Jupiter
                >>> calculate_aspect_movement(5, 127, 120, 0.1, 1.2)
                'Separating'

                >>> # Retrograde Mars applying to a conjunction with direct Jupiter
                >>> calculate_aspect_movement(110, 100, 0, -0.8, 0.1)
                'Applying'
    """

    if point_one_speed is None or point_two_speed is None:
        raise ValueError(
            "Speed values for both points are required to compute aspect "
            "movement correctly. point_one_speed and point_two_speed "
            "cannot be None."
        )

    # Normalize longitudes to [0, 360)
    p1 = point_one_abs_pos % 360.0
    p2 = point_two_abs_pos % 360.0

    # Normalize aspect to [0, 360) and then to [0, 180]
    aspect = aspect_degrees % 360.0
    if aspect > 180.0:
        aspect = 360.0 - aspect  # es. 240 -> 120

    # Special case: if one of the two points is effectively fixed (speed = 0),
    # such as chart angles, we consider only the motion of the moving point
    # relative to the fixed one. The order of the points must not affect
    # the result.
    if point_one_speed == 0 and point_two_speed == 0:
        # Both points are fixed, the aspect never changes dynamically
        return "Fixed"

    # Identify which point is moving and which one is fixed/slower.
    # To correctly handle axes we always compute with respect to the
    # moving point.
    if point_one_speed == 0:
        # point_one is fixed (e.g. axis), point_two moves
        moving_pos = p2
        fixed_pos = p1
        moving_speed = point_two_speed
        sep = difdeg2n(moving_pos, fixed_pos)

    elif point_two_speed == 0:
        # point_two is fixed (e.g. axis), point_one moves
        moving_pos = p1
        fixed_pos = p2
        moving_speed = point_one_speed
        sep = difdeg2n(moving_pos, fixed_pos)

    else:
        # Both points move: use relative speed and standard separation
        sep = difdeg2n(p2, p1)
        moving_speed = point_two_speed - point_one_speed

    sep_abs = abs(sep)

    # If the (relative or absolute) speed is zero, the orb does not change
    if moving_speed == 0:
        return "Separating"

    # Signs used to determine whether the orb grows or shrinks
    sign_sep = _sign(sep)                 # sign of the separation
    sign_delta = _sign(sep_abs - aspect)  # whether we are "before" or "beyond" the exact aspect
    sign_rel = _sign(moving_speed)        # direction in which the separation evolves

    # Qualitative sign of the orb derivative (d(orb)/dt):
    # < 0  -> orb decreases -> Applying
    # > 0  -> orb increases -> Separating
    orb_derivative_sign = sign_delta * sign_sep * sign_rel

    return "Applying" if orb_derivative_sign < 0 else "Separating"


def planet_id_decoder(planets_settings: list[KerykeionSettingsCelestialPointModel], name: str) -> int:
    """
    Check if the name of the planet is the same in the settings and return
    the correct id for the planet.
    """
    str_name = str(name)
    for planet in planets_settings:
        if planet["name"] == str_name:
            result = planet["id"]
            return result

    raise ValueError(f"Planet {name} not found in the settings")


def get_active_points_list(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    active_points: list = [],
    *,
    celestial_points: list[dict] = DEFAULT_CELESTIAL_POINTS_SETTINGS,
) -> list:
    """
    Given an astrological subject and the settings, return a list of the active points.
    Args:
        subject (AstrologicalSubject): The astrological subject to get the active points from.
        settings (Union[KerykeionSettingsModel, dict]): Settings model o dictionary.

    Returns:
        list: List of the active points.
    """
    point_list = []
    for planet in celestial_points:
        if planet["name"] in active_points:
            point_list.append(subject[planet["name"].lower()])

    return point_list
