# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia

Context Serializer Module

This module provides functionality to transform Kerykeion Pydantic models
into textual English descriptions suitable for AI consumption. The output
is strictly non-qualitative and non-interpretive, providing factual
representations of astrological data.
"""

from typing import Union
from kerykeion.schemas.kr_models import (
    KerykeionPointModel,
    LunarPhaseModel,
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    PlanetReturnModel,
    AspectModel,
    SingleChartDataModel,
    DualChartDataModel,
    ElementDistributionModel,
    QualityDistributionModel,
    TransitMomentModel,
    TransitsTimeRangeModel,
    PointInHouseModel,
    HouseComparisonModel,
)


# Mapping from abbreviated sign names to full names
SIGN_FULL_NAMES = {
    "Ari": "Aries",
    "Tau": "Taurus",
    "Gem": "Gemini",
    "Can": "Cancer",
    "Leo": "Leo",
    "Vir": "Virgo",
    "Lib": "Libra",
    "Sco": "Scorpio",
    "Sag": "Sagittarius",
    "Cap": "Capricorn",
    "Aqu": "Aquarius",
    "Pis": "Pisces",
}


def kerykeion_point_to_context(point: KerykeionPointModel) -> str:
    """
    Transform a KerykeionPointModel into textual context.

    Provides a non-qualitative description of an astrological point including
    its position, sign, element, quality, house placement, and motion status.

    Args:
        point: A KerykeionPointModel representing a planet, axis, or house cusp.

    Returns:
        A string describing the point in factual terms.

    Example:
        >>> point = subject.sun
        >>> kerykeion_point_to_context(point)
        'Sun at 10.81° in Capricorn in First House, quality: Cardinal, element: Earth, direct motion, speed 1.0195°/day, declination -23.00°'
    """
    # Build the position string (sign + house together, no comma between them)
    full_sign_name = SIGN_FULL_NAMES.get(point.sign, point.sign)
    position_str = f"{point.name} at {point.position:.2f}° in {full_sign_name}"

    # Add house placement directly to position string (no comma)
    if point.house is not None:
        house_name = str(point.house).replace("_", " ")
        position_str += f" in {house_name}"

    # Now build the parts list starting with the complete position string
    parts = [position_str]

    # Absolute position in the zodiac
    parts.append(f"absolute position {point.abs_pos:.2f}°")

    # Element and quality with explicit labels
    parts.append(f"quality: {point.quality}, element: {point.element}")

    # Retrograde status (for planets)
    if point.retrograde is not None:
        motion = "retrograde" if point.retrograde else "direct motion"
        parts.append(motion)

    # Speed (if available)
    if point.speed is not None:
        parts.append(f"speed {point.speed:.4f}°/day")

    # Declination (if available)
    if point.declination is not None:
        parts.append(f"declination {point.declination:.2f}°")

    return ", ".join(parts)


def lunar_phase_to_context(lunar_phase: LunarPhaseModel) -> str:
    """
    Transform a LunarPhaseModel into textual context.

    Args:
        lunar_phase: A LunarPhaseModel containing lunar phase information.

    Returns:
        A string describing the lunar phase.

    Example:
        >>> lunar_phase_to_context(subject.lunar_phase)
        'Lunar phase: Waning Gibbous (phase 20), 254.32° separation between Sun and Moon, emoji: 🌖'
    """
    return (
        f"Lunar phase: {lunar_phase.moon_phase_name} (phase {lunar_phase.moon_phase}), "
        f"{lunar_phase.degrees_between_s_m:.2f}° separation between Sun and Moon, "
        f"emoji: {lunar_phase.moon_emoji}"
    )


def aspect_to_context(aspect: AspectModel, is_synastry: bool = False, is_transit: bool = False) -> str:
    """
    Transform an AspectModel into textual context.

    Describes the relationship between two astrological points including
    the aspect type, orb, and movement status.

    Args:
        aspect: An AspectModel representing an aspect between two points.
        is_synastry: True for synastry/dual charts, False for natal/single charts.
        is_transit: True for transit charts to use 'Transit's' instead of subject name.

    Returns:
        A string describing the aspect.

    Examples:
        Natal chart:
        >>> aspect_to_context(aspect, is_synastry=False)
        'conjunction between Mercury and Saturn, orb 10.02°, movement: applying'

        Synastry chart:
        >>> aspect_to_context(aspect, is_synastry=True)
        "opposition between \"Test Subject\"'s Sun and \"Second Subject\"'s Mercury, orb 6.42°"

        Transit chart:
        >>> aspect_to_context(aspect, is_synastry=True, is_transit=True)
        "opposition between \"John Lennon\"'s Sun and Transit's Jupiter, orb 6.42°"
    """
    parts = []

    if is_synastry:
        # For transit charts, second subject is always "Transit"
        if is_transit:
            p2_owner = "Transit"
        else:
            p2_owner = f'"{aspect.p2_owner}"'

        # Synastry/Transit format: show clear ownership, with orb and aspect angle, no movement
        parts.append(
            f"{aspect.aspect} between \"{aspect.p1_owner}\"'s {aspect.p1_name} and {p2_owner}'s {aspect.p2_name}"
        )
        # Orb and aspect angle
        parts.append(f"orb {aspect.orbit:.2f}°, aspect angle {aspect.aspect_degrees}°")
    else:
        # Natal format: no owner (same subject), with orb, aspect angle and movement
        parts.append(f"{aspect.aspect} between {aspect.p1_name} and {aspect.p2_name}")
        # Orb and aspect angle
        parts.append(f"orb {aspect.orbit:.2f}°, aspect angle {aspect.aspect_degrees}°")
        # Movement (only for natal charts)
        parts.append(f"movement: {aspect.aspect_movement.lower()}")

    return ", ".join(parts)


def point_in_house_to_context(point_in_house: PointInHouseModel) -> str:
    """
    Transform a PointInHouseModel into textual context.

    Describes where an astrological point from one subject falls within
    another subject's house system.

    Args:
        point_in_house: A PointInHouseModel representing a point's house placement.

    Returns:
        A string describing the point's house placement.

    Example:
        >>> point_in_house_to_context(point_data)
        '"John"\'s Sun at 15.32° Aries (in John\'s First House) falls in "Jane"\'s Seventh House'
    """
    parts = []

    # Point owner and point information
    parts.append(f'"{point_in_house.point_owner_name}"\'s {point_in_house.point_name}')
    parts.append(f"at {point_in_house.point_degree:.2f}° {point_in_house.point_sign}")

    # Original house position (if available)
    if point_in_house.point_owner_house_name:
        parts.append(f"(in {point_in_house.point_owner_name}'s {point_in_house.point_owner_house_name})")

    # Projected house position
    parts.append(f'falls in "{point_in_house.projected_house_owner_name}"\'s {point_in_house.projected_house_name}')

    return " ".join(parts)


def house_comparison_to_context(house_comparison: HouseComparisonModel, is_transit: bool = False) -> str:
    """
    Transform a HouseComparisonModel into textual context.

    Provides bidirectional house overlay analysis between two subjects,
    showing how each subject's planets fall within the other's house system.

    Args:
        house_comparison: A HouseComparisonModel with bidirectional house placements.
        is_transit: If True, handles transit chart logic (transit subject has no houses).

    Returns:
        A multi-line string describing the house comparison.

    Example:
        >>> house_comparison_to_context(comparison, is_transit=False)
        'House Overlay Analysis:\\n\\n"John"\'s points in "Jane"\'s houses:\\n  - ...'
    """
    lines = []

    lines.append("House Overlay Analysis:")

    # First subject's points in second subject's houses
    if house_comparison.first_points_in_second_houses:
        lines.append(
            f'\n"{house_comparison.first_subject_name}"\'s points in "{house_comparison.second_subject_name}"\'s houses:'
        )
        for point in house_comparison.first_points_in_second_houses:
            lines.append(f"  - {point_in_house_to_context(point)}")

    # Second subject's points in first subject's houses
    # For transit charts, the transit subject has no houses, so we handle this differently
    if house_comparison.second_points_in_first_houses:
        if is_transit:
            # Transit case: "Transit's planets in John's houses"
            lines.append(f'\nTransit planets in "{house_comparison.first_subject_name}"\'s houses:')
        else:
            # Normal synastry case: bidirectional
            lines.append(
                f'\n"{house_comparison.second_subject_name}"\'s points in "{house_comparison.first_subject_name}"\'s houses:'
            )

        for point in house_comparison.second_points_in_first_houses:
            lines.append(f"  - {point_in_house_to_context(point)}")

    # First subject's cusps in second subject's houses
    if house_comparison.first_cusps_in_second_houses:
        if is_transit:
            # Transit case: "John's cusps in Transit's houses" (less common but included)
            lines.append(f"\n\"{house_comparison.first_subject_name}\"'s cusps in Transit's houses:")
        else:
            # Normal synastry case: bidirectional
            lines.append(
                f'\n"{house_comparison.first_subject_name}"\'s cusps in "{house_comparison.second_subject_name}"\'s houses:'
            )

        for cusp in house_comparison.first_cusps_in_second_houses:
            lines.append(f"  - {point_in_house_to_context(cusp)}")

    # Second subject's cusps in first subject's houses
    # For transit charts, the transit subject has no houses, so we handle this differently
    if house_comparison.second_cusps_in_first_houses:
        if is_transit:
            # Transit case: "Transit's cusps in John's houses"
            lines.append(f'\nTransit cusps in "{house_comparison.first_subject_name}"\'s houses:')
        else:
            # Normal synastry case: bidirectional
            lines.append(
                f'\n"{house_comparison.second_subject_name}"\'s cusps in "{house_comparison.first_subject_name}"\'s houses:'
            )

        for cusp in house_comparison.second_cusps_in_first_houses:
            lines.append(f"  - {point_in_house_to_context(cusp)}")

    return "\n".join(lines)


def element_distribution_to_context(distribution: ElementDistributionModel) -> str:
    """
    Transform an ElementDistributionModel into textual context.

    Args:
        distribution: An ElementDistributionModel with element percentages.

    Returns:
        A string describing the element distribution.

    Example:
        >>> element_distribution_to_context(chart_data.element_distribution)
        'Element distribution: Fire 25%, Earth 20%, Air 30%, Water 25%'
    """
    return (
        f"Element distribution: "
        f"Fire {distribution.fire_percentage}%, "
        f"Earth {distribution.earth_percentage}%, "
        f"Air {distribution.air_percentage}%, "
        f"Water {distribution.water_percentage}%"
    )


def quality_distribution_to_context(distribution: QualityDistributionModel) -> str:
    """
    Transform a QualityDistributionModel into textual context.

    Args:
        distribution: A QualityDistributionModel with quality percentages.

    Returns:
        A string describing the quality distribution.

    Example:
        >>> quality_distribution_to_context(chart_data.quality_distribution)
        'Quality distribution: Cardinal 33%, Fixed 40%, Mutable 27%'
    """
    return (
        f"Quality distribution: "
        f"Cardinal {distribution.cardinal_percentage}%, "
        f"Fixed {distribution.fixed_percentage}%, "
        f"Mutable {distribution.mutable_percentage}%"
    )


def astrological_subject_to_context(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel], is_transit_subject: bool = False
) -> str:
    """
    Transform an AstrologicalSubjectModel into comprehensive textual context.

    Provides a complete description of an astrological chart including metadata,
    planetary positions, house cusps, and lunar phase.

    Args:
        subject: An AstrologicalSubjectModel, CompositeSubjectModel, or PlanetReturnModel.
        is_transit_subject: If True, formats output for a transit moment (omits 'Chart for' and uses 'Transit moment').

    Returns:
        A multi-line string describing the complete chart.

    Example:
        >>> context = astrological_subject_to_context(natal_chart)
        >>> print(context)
        Chart for Johnny Depp
        Birth data: 1963-06-09 00:00:00, Owensboro, US
        ...
    """
    lines = []

    # Header (omit for transit subjects as it's already indicated by 'Transit Subject:')
    if not is_transit_subject:
        lines.append(f'Chart for "{subject.name}"')

    # Birth/Event data (for regular subjects)
    if isinstance(subject, AstrologicalSubjectModel):
        # Use 'Transit moment:' for transits, 'Birth data:' for natal charts
        data_label = "Transit moment:" if is_transit_subject else "Birth data:"
        lines.append(
            f"{data_label} {subject.year}-{subject.month:02d}-{subject.day:02d} "
            f"{subject.hour:02d}:{subject.minute:02d}, {subject.city}, {subject.nation}"
        )
        lines.append(
            f"Coordinates: {subject.lat:.2f}°N, {subject.lng:.2f}°W"
            if subject.lng < 0
            else f"Coordinates: {subject.lat:.2f}°N, {subject.lng:.2f}°E"
        )
        lines.append(f"Timezone: {subject.tz_str}")

    # Chart configuration
    lines.append(f"Zodiac system: {subject.zodiac_type}")
    if subject.sidereal_mode:
        lines.append(f"Sidereal mode: {subject.sidereal_mode}")
    lines.append(f"House system: {subject.houses_system_name}")
    lines.append(f"Perspective: {subject.perspective_type}")

    # Composite chart specific info
    if isinstance(subject, CompositeSubjectModel):
        lines.append(f"Composite type: {subject.composite_chart_type}")
        lines.append(f'First subject: "{subject.first_subject.name}"')
        lines.append(f'Second subject: "{subject.second_subject.name}"')

    # Planet Return specific info
    if isinstance(subject, PlanetReturnModel):
        lines.append(f"Return type: {subject.return_type}")

    # Celestial Points (unified section for planets)
    lines.append("\nPlanetary positions:")
    # All celestial points in one list
    celestial_point_names = [
        "sun",
        "moon",
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
        "chiron",
        "mean_lilith",
        "true_lilith",
        "ceres",
        "pallas",
        "juno",
        "vesta",
    ]
    for point_name in celestial_point_names:
        point = getattr(subject, point_name, None)
        if point is not None:
            lines.append(f"  - {kerykeion_point_to_context(point)}")

    # Important points (axes and lunar nodes)
    axes = ["ascendant", "descendant", "medium_coeli", "imum_coeli", "vertex", "anti_vertex"]
    axes_present = [getattr(subject, axis, None) for axis in axes if getattr(subject, axis, None) is not None]
    lunar_nodes_present = (
        subject.true_north_lunar_node is not None
        or subject.mean_north_lunar_node is not None
        or subject.true_south_lunar_node is not None
        or subject.mean_south_lunar_node is not None
    )

    if axes_present or lunar_nodes_present:
        lines.append("\nImportant points:")
        for axis_name in axes:
            axis = getattr(subject, axis_name, None)
            if axis is not None:
                lines.append(f"  - {kerykeion_point_to_context(axis)}")

        if subject.true_north_lunar_node is not None:
            lines.append(f"  - {kerykeion_point_to_context(subject.true_north_lunar_node)}")
        if subject.true_south_lunar_node is not None:
            lines.append(f"  - {kerykeion_point_to_context(subject.true_south_lunar_node)}")

    # House cusps
    lines.append("\nHouse cusps:")
    house_names = [
        "first_house",
        "second_house",
        "third_house",
        "fourth_house",
        "fifth_house",
        "sixth_house",
        "seventh_house",
        "eighth_house",
        "ninth_house",
        "tenth_house",
        "eleventh_house",
        "twelfth_house",
    ]
    for house_name in house_names:
        house = getattr(subject, house_name, None)
        if house is not None:
            lines.append(f"  - {house.name} cusp at {house.position:.2f}° in {house.sign}")

    # Lunar phase (if present)
    if subject.lunar_phase is not None:
        lines.append(f"\n{lunar_phase_to_context(subject.lunar_phase)}")

    return "\n".join(lines)


def single_chart_data_to_context(chart_data: SingleChartDataModel) -> str:
    """
    Transform a SingleChartDataModel into textual context.

    Provides complete chart information including subject data, aspects,
    and element/quality distributions.

    Args:
        chart_data: A SingleChartDataModel containing complete chart data.

    Returns:
        A multi-line string describing the chart data.
    """
    lines = []

    # Chart type
    lines.append(f"{chart_data.chart_type} Chart Analysis")
    lines.append("=" * 50)

    # Subject information
    lines.append("\n" + astrological_subject_to_context(chart_data.subject))

    # Element and quality distributions
    lines.append("\n" + element_distribution_to_context(chart_data.element_distribution))
    lines.append(quality_distribution_to_context(chart_data.quality_distribution))

    # Aspects (natal format: no owner, with movement)
    if chart_data.aspects:
        lines.append(f"\nAspects ({len(chart_data.aspects)} total):")
        for aspect in chart_data.aspects:
            lines.append(f"  - {aspect_to_context(aspect, is_synastry=False)}")

    # Active configuration
    lines.append(f"\nActive points: {', '.join(chart_data.active_points)}")
    lines.append(
        f"Active aspects: {', '.join([a['name'] + ' (' + str(a['orb']) + '°)' for a in chart_data.active_aspects])}"
    )

    return "\n".join(lines)


def dual_chart_data_to_context(chart_data: DualChartDataModel) -> str:
    """
    Transform a DualChartDataModel into textual context.

    Provides complete dual chart information including both subjects,
    inter-chart aspects, and relationship analysis.

    Args:
        chart_data: A DualChartDataModel containing dual chart data.

    Returns:
        A multi-line string describing the dual chart data.
    """
    lines = []

    # Chart type
    lines.append(f"{chart_data.chart_type} Chart Analysis")
    lines.append("=" * 50)

    # First subject
    lines.append("\nFirst Subject:")
    lines.append(astrological_subject_to_context(chart_data.first_subject))

    # Second subject (or Transit subject for transit charts)
    # Detect if this is a transit chart by checking chart_type
    is_transit = chart_data.chart_type == "Transit"

    lines.append("\n" + "=" * 50)
    if is_transit:
        lines.append("Transit Subject:")
    else:
        lines.append("Second Subject:")
    lines.append(astrological_subject_to_context(chart_data.second_subject, is_transit_subject=is_transit))

    # Inter-chart aspects (synastry format: clear ownership, no movement)

    if chart_data.aspects:
        lines.append("\n" + "=" * 50)
        lines.append(f"Inter-chart aspects ({len(chart_data.aspects)} total):")
        for aspect in chart_data.aspects:
            lines.append(f"  - {aspect_to_context(aspect, is_synastry=True, is_transit=is_transit)}")

    # House comparison analysis
    if chart_data.house_comparison is not None:
        lines.append("\n" + "=" * 50)
        lines.append(house_comparison_to_context(chart_data.house_comparison, is_transit=is_transit))

    # Relationship score (for synastry)
    if chart_data.relationship_score is not None:
        score = chart_data.relationship_score
        lines.append("\n" + "=" * 50)
        lines.append("Relationship Analysis:")
        lines.append(f"Score: {score.score_value}/44 ({score.score_description})")
        lines.append(f"Destiny sign connection: {score.is_destiny_sign}")

    # Element and quality distributions
    lines.append("\n" + "=" * 50)
    lines.append("Combined " + element_distribution_to_context(chart_data.element_distribution))
    lines.append("Combined " + quality_distribution_to_context(chart_data.quality_distribution))

    # Active configuration
    lines.append(f"\nActive points: {', '.join(chart_data.active_points)}")
    lines.append(
        f"Active aspects: {', '.join([a['name'] + ' (' + str(a['orb']) + '°)' for a in chart_data.active_aspects])}"
    )

    return "\n".join(lines)


def transit_moment_to_context(transit: TransitMomentModel) -> str:
    """
    Transform a TransitMomentModel into textual context.

    Args:
        transit: A TransitMomentModel representing a transit snapshot.

    Returns:
        A string describing the transit moment.
    """
    lines = []
    lines.append(f"Transit moment: {transit.date}")

    if transit.aspects:
        lines.append(f"Active transits ({len(transit.aspects)} aspects):")
        for aspect in transit.aspects:
            lines.append(f"  - {aspect_to_context(aspect, is_synastry=True, is_transit=True)}")
    else:
        lines.append("No active transits at this moment")

    return "\n".join(lines)


def transits_time_range_to_context(transits: TransitsTimeRangeModel) -> str:
    """
    Transform a TransitsTimeRangeModel into textual context.

    Args:
        transits: A TransitsTimeRangeModel containing multiple transit moments.

    Returns:
        A string describing the transit time range.
    """
    lines = []

    # Header
    if transits.subject:
        lines.append(f'Transit analysis for "{transits.subject.name}"')
    else:
        lines.append("Transit analysis")

    lines.append(f"Time range: {len(transits.transits)} moments analyzed")

    if transits.dates:
        lines.append(f"From {transits.dates[0]} to {transits.dates[-1]}")

    # Transit moments
    lines.append("\nTransit moments:")
    for transit in transits.transits:
        lines.append("\n" + transit_moment_to_context(transit))

    return "\n".join(lines)


def to_context(
    model: Union[
        KerykeionPointModel,
        LunarPhaseModel,
        AstrologicalSubjectModel,
        CompositeSubjectModel,
        PlanetReturnModel,
        AspectModel,
        SingleChartDataModel,
        DualChartDataModel,
        ElementDistributionModel,
        QualityDistributionModel,
        TransitMomentModel,
        TransitsTimeRangeModel,
        PointInHouseModel,
        HouseComparisonModel,
    ],
) -> str:
    """
    Main dispatcher function to convert any Kerykeion model to textual context.

    This function automatically detects the model type and routes to the
    appropriate transformer function.

    Args:
        model: Any supported Kerykeion Pydantic model.

    Returns:
        A string containing the textual representation of the model.

    Raises:
        TypeError: If the model type is not supported.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, to_context
        >>> subject = AstrologicalSubjectFactory.from_birth_data(...)
        >>> context = to_context(subject)
        >>> print(context)
    """
    if isinstance(model, SingleChartDataModel):
        return single_chart_data_to_context(model)
    elif isinstance(model, DualChartDataModel):
        return dual_chart_data_to_context(model)
    elif isinstance(model, TransitsTimeRangeModel):
        return transits_time_range_to_context(model)
    elif isinstance(model, TransitMomentModel):
        return transit_moment_to_context(model)
    elif isinstance(model, (AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel)):
        return astrological_subject_to_context(model)
    elif isinstance(model, KerykeionPointModel):
        return kerykeion_point_to_context(model)
    elif isinstance(model, LunarPhaseModel):
        return lunar_phase_to_context(model)
    elif isinstance(model, AspectModel):
        return aspect_to_context(model)
    elif isinstance(model, ElementDistributionModel):
        return element_distribution_to_context(model)
    elif isinstance(model, QualityDistributionModel):
        return quality_distribution_to_context(model)
    elif isinstance(model, PointInHouseModel):
        return point_in_house_to_context(model)
    elif isinstance(model, HouseComparisonModel):
        return house_comparison_to_context(model)
    else:
        raise TypeError(
            f"Unsupported model type: {type(model).__name__}. "
            f"Supported types are: KerykeionPointModel, LunarPhaseModel, "
            f"AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel, "
            f"AspectModel, SingleChartDataModel, DualChartDataModel, "
            f"ElementDistributionModel, QualityDistributionModel, "
            f"TransitMomentModel, TransitsTimeRangeModel, "
            f"PointInHouseModel, HouseComparisonModel"
        )


__all__ = [
    "to_context",
    "kerykeion_point_to_context",
    "lunar_phase_to_context",
    "aspect_to_context",
    "point_in_house_to_context",
    "house_comparison_to_context",
    "element_distribution_to_context",
    "quality_distribution_to_context",
    "astrological_subject_to_context",
    "single_chart_data_to_context",
    "dual_chart_data_to_context",
    "transit_moment_to_context",
    "transits_time_range_to_context",
]


if __name__ == "__main__":
    from kerykeion import astrological_subject_factory
    from kerykeion.chart_data_factory import ChartDataFactory

    natal_model = astrological_subject_factory.AstrologicalSubjectFactory.from_iso_utc_time(
        name="Test Subject",
        iso_utc_time="1990-01-01T12:00:00Z",
        city="New York",
        nation="US",
        lat=40.7128,
        lng=-74.0060,
    )

    chart_data = ChartDataFactory.create_natal_chart_data(subject=natal_model)

    context = to_context(chart_data)

    print(context)
