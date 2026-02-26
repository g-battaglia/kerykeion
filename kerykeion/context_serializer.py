# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia

Context Serializer Module

This module provides functionality to transform Kerykeion Pydantic models
into XML representations suitable for AI consumption. The output is strictly
non-qualitative and non-interpretive, providing factual representations
of astrological data in semantic XML format.

Optional/None fields are omitted from the output rather than rendered as empty.
"""

from typing import Union
from xml.sax.saxutils import escape, quoteattr
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
    MoonPhaseOverviewModel,
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


# ============================================================================
# XML Helper Functions
# ============================================================================


def _xe(value) -> str:
    """Escape a value for use as XML text content."""
    return escape(str(value))


def _attrs(**kwargs) -> str:
    """Format keyword arguments as XML attributes, omitting None values.

    Returns a string with a leading space if any attributes are present,
    or an empty string if all values are None.
    """
    parts = []
    for key, value in kwargs.items():
        if value is not None:
            parts.append(f"{key}={quoteattr(str(value))}")
    if not parts:
        return ""
    return " " + " ".join(parts)


def _sc(tag: str, **kwargs) -> str:
    """Create a self-closing XML tag: ``<tag key="value" />``."""
    return f"<{tag}{_attrs(**kwargs)} />"


def _o(tag: str, **kwargs) -> str:
    """Create an opening XML tag: ``<tag key="value">``."""
    return f"<{tag}{_attrs(**kwargs)}>"


def _c(tag: str) -> str:
    """Create a closing XML tag: ``</tag>``."""
    return f"</{tag}>"


def _el(tag: str, text, **kwargs) -> str:
    """Create an XML element with text content: ``<tag>text</tag>``.

    Returns empty string if *text* is None.
    """
    if text is None:
        return ""
    return f"{_o(tag, **kwargs)}{_xe(text)}{_c(tag)}"


# ============================================================================
# Individual Model Converters
# ============================================================================


def kerykeion_point_to_context(point: KerykeionPointModel) -> str:
    """
    Transform a KerykeionPointModel into an XML ``<point />`` element.

    Provides a non-qualitative description of an astrological point including
    its position, sign, element, quality, house placement, and motion status.

    Args:
        point: A KerykeionPointModel representing a planet, axis, or house cusp.

    Returns:
        A self-closing XML string describing the point.

    Example:
        >>> point = subject.sun
        >>> kerykeion_point_to_context(point)
        '<point name="Sun" position="10.81" sign="Capricorn" abs_pos="280.81" quality="Cardinal" element="Earth" house="First House" motion="direct" speed="1.0195" declination="-23.00" />'
    """
    full_sign_name = SIGN_FULL_NAMES.get(point.sign, point.sign)

    attrs: dict = {
        "name": point.name,
        "position": f"{point.position:.2f}",
        "sign": full_sign_name,
        "abs_pos": f"{point.abs_pos:.2f}",
        "quality": point.quality,
        "element": point.element,
    }

    if point.house is not None:
        attrs["house"] = str(point.house).replace("_", " ")

    if point.retrograde is not None:
        attrs["motion"] = "retrograde" if point.retrograde else "direct"

    if point.speed is not None:
        attrs["speed"] = f"{point.speed:.4f}"

    if point.declination is not None:
        attrs["declination"] = f"{point.declination:.2f}"

    return _sc("point", **attrs)


def lunar_phase_to_context(lunar_phase: LunarPhaseModel) -> str:
    """
    Transform a LunarPhaseModel into an XML ``<lunar_phase />`` element.

    Args:
        lunar_phase: A LunarPhaseModel containing lunar phase information.

    Returns:
        A self-closing XML string describing the lunar phase.

    Example:
        >>> lunar_phase_to_context(subject.lunar_phase)
        '<lunar_phase name="Waning Gibbous" phase="20" degrees_between="254.32" emoji="\\U0001f316" />'
    """
    return _sc(
        "lunar_phase",
        name=lunar_phase.moon_phase_name,
        phase=str(lunar_phase.moon_phase),
        degrees_between=f"{lunar_phase.degrees_between_s_m:.2f}",
        emoji=lunar_phase.moon_emoji,
    )


def aspect_to_context(aspect: AspectModel, is_synastry: bool = False, is_transit: bool = False) -> str:
    """
    Transform an AspectModel into an XML ``<aspect />`` element.

    Args:
        aspect: An AspectModel representing an aspect between two points.
        is_synastry: True for synastry/dual charts (adds ownership attributes).
        is_transit: True for transit charts (uses "Transit" as second owner).

    Returns:
        A self-closing XML string describing the aspect.

    Examples:
        Natal chart::

            <aspect type="conjunction" p1="Mercury" p2="Saturn" orb="10.02" angle="0" movement="applying" />

        Synastry chart::

            <aspect type="opposition" p1_name="Sun" p1_owner="John" p2_name="Mercury" p2_owner="Jane" orb="6.42" angle="180" />

        Transit chart::

            <aspect type="opposition" p1_name="Sun" p1_owner="John" p2_name="Jupiter" p2_owner="Transit" orb="6.42" angle="180" />
    """
    if is_synastry:
        p2_owner = "Transit" if is_transit else aspect.p2_owner
        return _sc(
            "aspect",
            type=aspect.aspect,
            p1_name=aspect.p1_name,
            p1_owner=aspect.p1_owner,
            p2_name=aspect.p2_name,
            p2_owner=p2_owner,
            orb=f"{aspect.orbit:.2f}",
            angle=str(aspect.aspect_degrees),
        )
    else:
        return _sc(
            "aspect",
            type=aspect.aspect,
            p1=aspect.p1_name,
            p2=aspect.p2_name,
            orb=f"{aspect.orbit:.2f}",
            angle=str(aspect.aspect_degrees),
            movement=aspect.aspect_movement.lower(),
        )


def point_in_house_to_context(point_in_house: PointInHouseModel) -> str:
    """
    Transform a PointInHouseModel into an XML ``<point_in_house />`` element.

    Args:
        point_in_house: A PointInHouseModel representing a point's house placement.

    Returns:
        A self-closing XML string describing the point's house placement.

    Example::

        <point_in_house point_name="Sun" point_owner="John" degree="15.32"
            sign="Aries" owner_house="First House" projected_house="Seventh House"
            projected_house_owner="Jane" />
    """
    attrs: dict = {
        "point_name": point_in_house.point_name,
        "point_owner": point_in_house.point_owner_name,
        "degree": f"{point_in_house.point_degree:.2f}",
        "sign": point_in_house.point_sign,
    }

    if point_in_house.point_owner_house_name:
        attrs["owner_house"] = point_in_house.point_owner_house_name

    attrs["projected_house"] = point_in_house.projected_house_name
    attrs["projected_house_owner"] = point_in_house.projected_house_owner_name

    return _sc("point_in_house", **attrs)


def house_comparison_to_context(house_comparison: HouseComparisonModel, is_transit: bool = False) -> str:
    """
    Transform a HouseComparisonModel into an XML ``<house_overlay>`` element.

    Provides bidirectional house overlay analysis between two subjects.

    Args:
        house_comparison: A HouseComparisonModel with bidirectional house placements.
        is_transit: If True, handles transit chart logic.

    Returns:
        A multi-line XML string describing the house comparison.
    """
    lines = [_o("house_overlay")]

    # First subject's points in second subject's houses
    if house_comparison.first_points_in_second_houses:
        lines.append(
            f"  {_o('first_points_in_second', subject=house_comparison.first_subject_name, target=house_comparison.second_subject_name)}"
        )
        for point in house_comparison.first_points_in_second_houses:
            lines.append(f"    {point_in_house_to_context(point)}")
        lines.append(f"  {_c('first_points_in_second')}")

    # Second subject's points in first subject's houses
    if house_comparison.second_points_in_first_houses:
        if is_transit:
            subj, tgt = "Transit", house_comparison.first_subject_name
        else:
            subj, tgt = house_comparison.second_subject_name, house_comparison.first_subject_name
        lines.append(f"  {_o('second_points_in_first', subject=subj, target=tgt)}")
        for point in house_comparison.second_points_in_first_houses:
            lines.append(f"    {point_in_house_to_context(point)}")
        lines.append(f"  {_c('second_points_in_first')}")

    # First subject's cusps in second subject's houses
    if house_comparison.first_cusps_in_second_houses:
        if is_transit:
            subj, tgt = house_comparison.first_subject_name, "Transit"
        else:
            subj, tgt = house_comparison.first_subject_name, house_comparison.second_subject_name
        lines.append(f"  {_o('first_cusps_in_second', subject=subj, target=tgt)}")
        for cusp in house_comparison.first_cusps_in_second_houses:
            lines.append(f"    {point_in_house_to_context(cusp)}")
        lines.append(f"  {_c('first_cusps_in_second')}")

    # Second subject's cusps in first subject's houses
    if house_comparison.second_cusps_in_first_houses:
        if is_transit:
            subj, tgt = "Transit", house_comparison.first_subject_name
        else:
            subj, tgt = house_comparison.second_subject_name, house_comparison.first_subject_name
        lines.append(f"  {_o('second_cusps_in_first', subject=subj, target=tgt)}")
        for cusp in house_comparison.second_cusps_in_first_houses:
            lines.append(f"    {point_in_house_to_context(cusp)}")
        lines.append(f"  {_c('second_cusps_in_first')}")

    lines.append(_c("house_overlay"))
    return "\n".join(lines)


def element_distribution_to_context(distribution: ElementDistributionModel) -> str:
    """
    Transform an ElementDistributionModel into an XML ``<element_distribution />`` element.

    Args:
        distribution: An ElementDistributionModel with element percentages.

    Returns:
        A self-closing XML string describing the element distribution.

    Example::

        <element_distribution fire="25%" earth="20%" air="30%" water="25%" />
    """
    return _sc(
        "element_distribution",
        fire=f"{distribution.fire_percentage}%",
        earth=f"{distribution.earth_percentage}%",
        air=f"{distribution.air_percentage}%",
        water=f"{distribution.water_percentage}%",
    )


def quality_distribution_to_context(distribution: QualityDistributionModel) -> str:
    """
    Transform a QualityDistributionModel into an XML ``<quality_distribution />`` element.

    Args:
        distribution: A QualityDistributionModel with quality percentages.

    Returns:
        A self-closing XML string describing the quality distribution.

    Example::

        <quality_distribution cardinal="33%" fixed="40%" mutable="27%" />
    """
    return _sc(
        "quality_distribution",
        cardinal=f"{distribution.cardinal_percentage}%",
        fixed=f"{distribution.fixed_percentage}%",
        mutable=f"{distribution.mutable_percentage}%",
    )


def astrological_subject_to_context(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel], is_transit_subject: bool = False
) -> str:
    """
    Transform an AstrologicalSubjectModel into a comprehensive XML ``<chart>`` element.

    Provides a complete description of an astrological chart including metadata,
    planetary positions, house cusps, and lunar phase.

    Args:
        subject: An AstrologicalSubjectModel, CompositeSubjectModel, or PlanetReturnModel.
        is_transit_subject: If True, uses ``<transit_data>`` instead of ``<birth_data>``.

    Returns:
        A multi-line XML string describing the complete chart.
    """
    lines = [_o("chart", name=subject.name)]

    # Birth/Event data (for regular subjects)
    if isinstance(subject, AstrologicalSubjectModel):
        data_tag = "transit_data" if is_transit_subject else "birth_data"
        lng_dir = "W" if subject.lng < 0 else "E"
        lines.append(
            f"  {_sc(data_tag, date=f'{subject.year}-{subject.month:02d}-{subject.day:02d} {subject.hour:02d}:{subject.minute:02d}', city=subject.city, nation=subject.nation, lat=f'{subject.lat:.2f}', lng=f'{subject.lng:.2f}', lng_dir=lng_dir, tz=subject.tz_str)}"
        )

    # Chart configuration
    config_attrs: dict = {
        "zodiac": subject.zodiac_type,
        "house_system": subject.houses_system_name,
        "perspective": subject.perspective_type,
    }
    if subject.sidereal_mode:
        config_attrs["sidereal_mode"] = subject.sidereal_mode
    lines.append(f"  {_sc('config', **config_attrs)}")

    # Composite chart specific info
    if isinstance(subject, CompositeSubjectModel):
        lines.append(
            f"  {_sc('composite_info', type=subject.composite_chart_type, first_subject=subject.first_subject.name, second_subject=subject.second_subject.name)}"
        )

    # Planet Return specific info
    if isinstance(subject, PlanetReturnModel):
        lines.append(f"  {_sc('return_info', type=subject.return_type)}")

    # Celestial Points (planets)
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
    planet_lines = []
    for point_name in celestial_point_names:
        point = getattr(subject, point_name, None)
        if point is not None:
            planet_lines.append(f"    {kerykeion_point_to_context(point)}")

    if planet_lines:
        lines.append(f"  {_o('planets')}")
        lines.extend(planet_lines)
        lines.append(f"  {_c('planets')}")

    # Important points (axes and lunar nodes)
    axes = ["ascendant", "descendant", "medium_coeli", "imum_coeli", "vertex", "anti_vertex"]
    axes_lines = []
    for axis_name in axes:
        axis = getattr(subject, axis_name, None)
        if axis is not None:
            axes_lines.append(f"    {kerykeion_point_to_context(axis)}")

    for node_name in ["true_north_lunar_node", "true_south_lunar_node"]:
        node = getattr(subject, node_name, None)
        if node is not None:
            axes_lines.append(f"    {kerykeion_point_to_context(node)}")

    if axes_lines:
        lines.append(f"  {_o('axes')}")
        lines.extend(axes_lines)
        lines.append(f"  {_c('axes')}")

    # House cusps
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
    lines.append(f"  {_o('houses')}")
    for house_name in house_names:
        house = getattr(subject, house_name, None)
        if house is not None:
            lines.append(
                f"    {_sc('house', name=house.name, cusp=f'{house.position:.2f}', sign=SIGN_FULL_NAMES.get(house.sign, house.sign))}"
            )
    lines.append(f"  {_c('houses')}")

    # Lunar phase (if present)
    if subject.lunar_phase is not None:
        lines.append(f"  {lunar_phase_to_context(subject.lunar_phase)}")

    lines.append(_c("chart"))
    return "\n".join(lines)


def single_chart_data_to_context(chart_data: SingleChartDataModel) -> str:
    """
    Transform a SingleChartDataModel into an XML ``<chart_analysis>`` element.

    Args:
        chart_data: A SingleChartDataModel containing complete chart data.

    Returns:
        A multi-line XML string describing the chart data.
    """
    lines = [_o("chart_analysis", type=chart_data.chart_type)]

    # Subject information
    subject_xml = astrological_subject_to_context(chart_data.subject)
    for line in subject_xml.split("\n"):
        lines.append(f"  {line}")

    # Element and quality distributions
    lines.append(f"  {element_distribution_to_context(chart_data.element_distribution)}")
    lines.append(f"  {quality_distribution_to_context(chart_data.quality_distribution)}")

    # Aspects (natal format)
    if chart_data.aspects:
        lines.append(f"  {_o('aspects', count=str(len(chart_data.aspects)))}")
        for aspect in chart_data.aspects:
            lines.append(f"    {aspect_to_context(aspect, is_synastry=False)}")
        lines.append(f"  {_c('aspects')}")

    # Active configuration
    lines.append(f"  {_el('active_points', ', '.join(chart_data.active_points))}")
    active_aspects_str = ", ".join([f"{a['name']} ({a['orb']})" for a in chart_data.active_aspects])
    lines.append(f"  {_el('active_aspects', active_aspects_str)}")

    lines.append(_c("chart_analysis"))
    return "\n".join(lines)


def dual_chart_data_to_context(chart_data: DualChartDataModel) -> str:
    """
    Transform a DualChartDataModel into an XML ``<chart_analysis>`` element.

    Args:
        chart_data: A DualChartDataModel containing dual chart data.

    Returns:
        A multi-line XML string describing the dual chart data.
    """
    lines = []
    is_transit = chart_data.chart_type == "Transit"

    lines.append(_o("chart_analysis", type=chart_data.chart_type))

    # First subject
    lines.append(f"  {_o('first_subject')}")
    first_xml = astrological_subject_to_context(chart_data.first_subject)
    for line in first_xml.split("\n"):
        lines.append(f"    {line}")
    lines.append(f"  {_c('first_subject')}")

    # Second subject (or transit subject)
    wrapper_tag = "transit_subject" if is_transit else "second_subject"
    lines.append(f"  {_o(wrapper_tag)}")
    second_xml = astrological_subject_to_context(chart_data.second_subject, is_transit_subject=is_transit)
    for line in second_xml.split("\n"):
        lines.append(f"    {line}")
    lines.append(f"  {_c(wrapper_tag)}")

    # Inter-chart aspects (synastry format)
    if chart_data.aspects:
        lines.append(f"  {_o('aspects', count=str(len(chart_data.aspects)))}")
        for aspect in chart_data.aspects:
            lines.append(f"    {aspect_to_context(aspect, is_synastry=True, is_transit=is_transit)}")
        lines.append(f"  {_c('aspects')}")

    # House comparison analysis
    if chart_data.house_comparison is not None:
        hc_xml = house_comparison_to_context(chart_data.house_comparison, is_transit=is_transit)
        for line in hc_xml.split("\n"):
            lines.append(f"  {line}")

    # Relationship score (for synastry)
    if chart_data.relationship_score is not None:
        score = chart_data.relationship_score
        lines.append(
            f"  {_sc('relationship_score', value=str(score.score_value), max='44', description=score.score_description, destiny_sign=str(score.is_destiny_sign).lower())}"
        )

    # Element and quality distributions
    lines.append(f"  {element_distribution_to_context(chart_data.element_distribution)}")
    lines.append(f"  {quality_distribution_to_context(chart_data.quality_distribution)}")

    # Active configuration
    lines.append(f"  {_el('active_points', ', '.join(chart_data.active_points))}")
    active_aspects_str = ", ".join([f"{a['name']} ({a['orb']})" for a in chart_data.active_aspects])
    lines.append(f"  {_el('active_aspects', active_aspects_str)}")

    lines.append(_c("chart_analysis"))
    return "\n".join(lines)


def transit_moment_to_context(transit: TransitMomentModel) -> str:
    """
    Transform a TransitMomentModel into an XML ``<transit_moment>`` element.

    Args:
        transit: A TransitMomentModel representing a transit snapshot.

    Returns:
        An XML string describing the transit moment.
    """
    if transit.aspects:
        lines = [_o("transit_moment", date=transit.date)]
        lines.append(f"  {_o('aspects', count=str(len(transit.aspects)))}")
        for aspect in transit.aspects:
            lines.append(f"    {aspect_to_context(aspect, is_synastry=True, is_transit=True)}")
        lines.append(f"  {_c('aspects')}")
        lines.append(_c("transit_moment"))
        return "\n".join(lines)
    else:
        return _sc("transit_moment", date=transit.date, aspects="0")


def transits_time_range_to_context(transits: TransitsTimeRangeModel) -> str:
    """
    Transform a TransitsTimeRangeModel into an XML ``<transit_analysis>`` element.

    Args:
        transits: A TransitsTimeRangeModel containing multiple transit moments.

    Returns:
        A multi-line XML string describing the transit time range.
    """
    lines = []

    attrs: dict = {"moments": str(len(transits.transits))}
    if transits.subject:
        attrs["subject"] = transits.subject.name
    if transits.dates:
        attrs["from_date"] = transits.dates[0]
        attrs["to_date"] = transits.dates[-1]

    lines.append(_o("transit_analysis", **attrs))

    for transit in transits.transits:
        transit_xml = transit_moment_to_context(transit)
        for line in transit_xml.split("\n"):
            lines.append(f"  {line}")

    lines.append(_c("transit_analysis"))
    return "\n".join(lines)


def moon_phase_overview_to_context(overview: MoonPhaseOverviewModel) -> str:
    """
    Transform a MoonPhaseOverviewModel into an XML ``<moon_phase_overview>`` element.

    Provides a comprehensive description of the current lunar phase, sun info,
    and location context. All optional/None fields are omitted.

    Args:
        overview: A MoonPhaseOverviewModel containing moon phase details.

    Returns:
        A multi-line XML string describing the moon phase overview.
    """
    lines = [_o("moon_phase_overview", timestamp=str(overview.timestamp), datestamp=overview.datestamp)]

    # ---- Moon section ----
    moon = overview.moon
    lines.append(f"  {_o('moon')}")

    # Simple scalar fields
    if moon.phase is not None:
        lines.append(f"    {_el('phase', f'{moon.phase:.3f}')}")
    if moon.phase_name is not None:
        lines.append(f"    {_el('phase_name', moon.phase_name)}")
    if moon.major_phase is not None:
        lines.append(f"    {_el('major_phase', moon.major_phase)}")
    if moon.stage is not None:
        lines.append(f"    {_el('stage', moon.stage)}")
    if moon.illumination is not None:
        lines.append(f"    {_el('illumination', moon.illumination)}")
    if moon.age_days is not None:
        lines.append(f"    {_el('age_days', str(moon.age_days))}")
    if moon.lunar_cycle is not None:
        lines.append(f"    {_el('lunar_cycle', moon.lunar_cycle)}")
    if moon.emoji is not None:
        lines.append(f"    {_el('emoji', moon.emoji)}")

    # Zodiac
    if moon.zodiac is not None:
        lines.append(f"    {_sc('zodiac', sun_sign=moon.zodiac.sun_sign, moon_sign=moon.zodiac.moon_sign)}")

    # Moonrise / moonset
    if moon.moonrise is not None:
        lines.append(f"    {_el('moonrise', moon.moonrise)}")
    if moon.moonrise_timestamp is not None:
        lines.append(f"    {_el('moonrise_timestamp', str(moon.moonrise_timestamp))}")
    if moon.moonset is not None:
        lines.append(f"    {_el('moonset', moon.moonset)}")
    if moon.moonset_timestamp is not None:
        lines.append(f"    {_el('moonset_timestamp', str(moon.moonset_timestamp))}")

    # Next lunar eclipse
    if moon.next_lunar_eclipse is not None:
        ecl = moon.next_lunar_eclipse
        ecl_attrs: dict = {}
        if ecl.timestamp is not None:
            ecl_attrs["timestamp"] = str(ecl.timestamp)
        if ecl.datestamp is not None:
            ecl_attrs["datestamp"] = ecl.datestamp
        if ecl.type is not None:
            ecl_attrs["type"] = ecl.type
        if ecl.visibility_regions is not None:
            ecl_attrs["visibility_regions"] = ecl.visibility_regions
        lines.append(f"    {_sc('next_lunar_eclipse', **ecl_attrs)}")

    # Detailed section
    if moon.detailed is not None:
        detailed = moon.detailed
        lines.append(f"    {_o('detailed')}")

        # Position
        if detailed.position is not None:
            pos = detailed.position
            pos_attrs: dict = {}
            if pos.altitude is not None:
                pos_attrs["altitude"] = f"{pos.altitude:.2f}"
            if pos.azimuth is not None:
                pos_attrs["azimuth"] = f"{pos.azimuth:.2f}"
            if pos.distance is not None:
                pos_attrs["distance"] = f"{pos.distance:.2f}"
            if pos.parallactic_angle is not None:
                pos_attrs["parallactic_angle"] = f"{pos.parallactic_angle:.2f}"
            if pos.phase_angle is not None:
                pos_attrs["phase_angle"] = f"{pos.phase_angle:.2f}"
            lines.append(f"      {_sc('position', **pos_attrs)}")

        # Visibility
        if detailed.visibility is not None:
            vis = detailed.visibility
            vis_attrs: dict = {}
            if vis.visible_hours is not None:
                vis_attrs["visible_hours"] = f"{vis.visible_hours:.1f}"
            if vis.best_viewing_time is not None:
                vis_attrs["best_viewing_time"] = vis.best_viewing_time
            if vis.visibility_rating is not None:
                vis_attrs["visibility_rating"] = vis.visibility_rating
            if vis.illumination is not None:
                vis_attrs["illumination"] = vis.illumination

            if vis.viewing_conditions is not None:
                lines.append(f"      {_o('visibility', **vis_attrs)}")
                vc = vis.viewing_conditions
                vc_attrs: dict = {}
                if vc.phase_quality is not None:
                    vc_attrs["phase_quality"] = vc.phase_quality

                if vc.recommended_equipment is not None:
                    lines.append(f"        {_o('viewing_conditions', **vc_attrs)}")
                    eq = vc.recommended_equipment
                    eq_attrs: dict = {}
                    if eq.filters is not None:
                        eq_attrs["filters"] = eq.filters
                    if eq.telescope is not None:
                        eq_attrs["telescope"] = eq.telescope
                    if eq.best_magnification is not None:
                        eq_attrs["best_magnification"] = eq.best_magnification
                    lines.append(f"          {_sc('recommended_equipment', **eq_attrs)}")
                    lines.append(f"        {_c('viewing_conditions')}")
                else:
                    lines.append(f"        {_sc('viewing_conditions', **vc_attrs)}")
                lines.append(f"      {_c('visibility')}")
            else:
                lines.append(f"      {_sc('visibility', **vis_attrs)}")

        # Upcoming phases
        if detailed.upcoming_phases is not None:
            up = detailed.upcoming_phases
            lines.append(f"      {_o('upcoming_phases')}")
            for phase_tag, phase_window in [
                ("new_moon", up.new_moon),
                ("first_quarter", up.first_quarter),
                ("full_moon", up.full_moon),
                ("last_quarter", up.last_quarter),
            ]:
                if phase_window is not None:
                    lines.append(f"        {_o(phase_tag)}")
                    for moment_tag, moment in [("last", phase_window.last), ("next", phase_window.next)]:
                        if moment is not None:
                            m_attrs: dict = {}
                            if moment.timestamp is not None:
                                m_attrs["timestamp"] = str(moment.timestamp)
                            if moment.datestamp is not None:
                                m_attrs["datestamp"] = moment.datestamp
                            if moment.days_ago is not None:
                                m_attrs["days_ago"] = str(moment.days_ago)
                            if moment.days_ahead is not None:
                                m_attrs["days_ahead"] = str(moment.days_ahead)
                            if moment.name is not None:
                                m_attrs["name"] = moment.name
                            if moment.description is not None:
                                m_attrs["description"] = moment.description
                            lines.append(f"          {_sc(moment_tag, **m_attrs)}")
                    lines.append(f"        {_c(phase_tag)}")
            lines.append(f"      {_c('upcoming_phases')}")

        # Illumination details
        if detailed.illumination_details is not None:
            ill = detailed.illumination_details
            ill_attrs: dict = {}
            if ill.percentage is not None:
                ill_attrs["percentage"] = f"{ill.percentage:.1f}"
            if ill.visible_fraction is not None:
                ill_attrs["visible_fraction"] = f"{ill.visible_fraction:.4f}"
            if ill.phase_angle is not None:
                ill_attrs["phase_angle"] = f"{ill.phase_angle:.2f}"
            lines.append(f"      {_sc('illumination_details', **ill_attrs)}")

        lines.append(f"    {_c('detailed')}")

    # Events
    if moon.events is not None:
        ev = moon.events
        ev_attrs: dict = {}
        if ev.moonrise_visible is not None:
            ev_attrs["moonrise_visible"] = str(ev.moonrise_visible).lower()
        if ev.moonset_visible is not None:
            ev_attrs["moonset_visible"] = str(ev.moonset_visible).lower()

        if ev.optimal_viewing_period is not None:
            lines.append(f"    {_o('events', **ev_attrs)}")
            ovp = ev.optimal_viewing_period
            ovp_attrs: dict = {}
            if ovp.start_time is not None:
                ovp_attrs["start_time"] = ovp.start_time
            if ovp.end_time is not None:
                ovp_attrs["end_time"] = ovp.end_time
            if ovp.duration_hours is not None:
                ovp_attrs["duration_hours"] = f"{ovp.duration_hours:.1f}"
            if ovp.viewing_quality is not None:
                ovp_attrs["viewing_quality"] = ovp.viewing_quality

            if ovp.recommendations and len(ovp.recommendations) > 0:
                lines.append(f"      {_o('optimal_viewing_period', **ovp_attrs)}")
                for rec in ovp.recommendations:
                    lines.append(f"        {_el('recommendation', rec)}")
                lines.append(f"      {_c('optimal_viewing_period')}")
            else:
                lines.append(f"      {_sc('optimal_viewing_period', **ovp_attrs)}")
            lines.append(f"    {_c('events')}")
        else:
            lines.append(f"    {_sc('events', **ev_attrs)}")

    lines.append(f"  {_c('moon')}")

    # ---- Sun section ----
    if overview.sun is not None:
        sun = overview.sun
        lines.append(f"  {_o('sun')}")

        if sun.sunrise is not None:
            lines.append(f"    {_el('sunrise', str(sun.sunrise))}")
        if sun.sunrise_timestamp is not None:
            lines.append(f"    {_el('sunrise_timestamp', sun.sunrise_timestamp)}")
        if sun.sunset is not None:
            lines.append(f"    {_el('sunset', str(sun.sunset))}")
        if sun.sunset_timestamp is not None:
            lines.append(f"    {_el('sunset_timestamp', sun.sunset_timestamp)}")
        if sun.solar_noon is not None:
            lines.append(f"    {_el('solar_noon', sun.solar_noon)}")
        if sun.day_length is not None:
            lines.append(f"    {_el('day_length', sun.day_length)}")

        if sun.position is not None:
            pos = sun.position
            sp_attrs: dict = {}
            if pos.altitude is not None:
                sp_attrs["altitude"] = f"{pos.altitude:.2f}"
            if pos.azimuth is not None:
                sp_attrs["azimuth"] = f"{pos.azimuth:.2f}"
            if pos.distance is not None:
                sp_attrs["distance"] = f"{pos.distance:.2f}"
            lines.append(f"    {_sc('position', **sp_attrs)}")

        if sun.next_solar_eclipse is not None:
            ecl = sun.next_solar_eclipse
            se_attrs: dict = {}
            if ecl.timestamp is not None:
                se_attrs["timestamp"] = str(ecl.timestamp)
            if ecl.datestamp is not None:
                se_attrs["datestamp"] = ecl.datestamp
            if ecl.type is not None:
                se_attrs["type"] = ecl.type
            if ecl.visibility_regions is not None:
                se_attrs["visibility_regions"] = ecl.visibility_regions
            lines.append(f"    {_sc('next_solar_eclipse', **se_attrs)}")

        lines.append(f"  {_c('sun')}")

    # ---- Location section ----
    if overview.location is not None:
        loc = overview.location
        loc_attrs: dict = {}
        if loc.latitude is not None:
            loc_attrs["latitude"] = loc.latitude
        if loc.longitude is not None:
            loc_attrs["longitude"] = loc.longitude
        if loc.precision is not None:
            loc_attrs["precision"] = str(loc.precision)
        if loc.using_default_location is not None:
            loc_attrs["using_default_location"] = str(loc.using_default_location).lower()
        if loc.note is not None:
            loc_attrs["note"] = loc.note
        lines.append(f"  {_sc('location', **loc_attrs)}")

    lines.append(_c("moon_phase_overview"))
    return "\n".join(lines)


# ============================================================================
# Main Dispatcher
# ============================================================================


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
        MoonPhaseOverviewModel,
    ],
) -> str:
    """
    Main dispatcher function to convert any Kerykeion model to XML context.

    This function automatically detects the model type and routes to the
    appropriate transformer function.

    Args:
        model: Any supported Kerykeion Pydantic model.

    Returns:
        A string containing the XML representation of the model.

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
    elif isinstance(model, MoonPhaseOverviewModel):
        return moon_phase_overview_to_context(model)
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
            f"PointInHouseModel, HouseComparisonModel, MoonPhaseOverviewModel"
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
    "moon_phase_overview_to_context",
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
