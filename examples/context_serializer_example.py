# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia

    Context Serializer Examples

    This example demonstrates how to use the context_serializer module
    to transform ALL types of astrological data into AI-readable textual context.
"""

from kerykeion import (
    AstrologicalSubjectFactory, 
    ChartDataFactory,
    CompositeSubjectFactory,
    PlanetaryReturnFactory,
    to_context
)

print("=" * 80)
print("CONTEXT SERIALIZER - COMPLETE EXAMPLES FOR ALL CHART TYPES")
print("=" * 80)

# Example 1: Natal Chart
print("\n" + "=" * 80)
print("EXAMPLE 1: NATAL CHART")
print("=" * 80)

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB",
    suppress_geonames_warning=True
)

natal_context = to_context(subject)
print(natal_context)

# Example 2: Natal Chart with Aspects
print("\n" + "=" * 80)
print("EXAMPLE 2: NATAL CHART WITH ASPECTS")
print("=" * 80)

natal_chart_data = ChartDataFactory.create_natal_chart_data(subject)
natal_chart_context = to_context(natal_chart_data)
print(natal_chart_context)

# Example 3: Synastry Chart
print("\n" + "=" * 80)
print("EXAMPLE 3: SYNASTRY CHART")
print("=" * 80)

subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Yoko Ono", 1933, 2, 18, 20, 30, "Tokyo", "JP",
    suppress_geonames_warning=True
)

synastry_data = ChartDataFactory.create_synastry_chart_data(
    first_subject=subject,
    second_subject=subject2
)

synastry_context = to_context(synastry_data)
print(synastry_context)

# Example 4: Composite Chart
print("\n" + "=" * 80)
print("EXAMPLE 4: COMPOSITE CHART")
print("=" * 80)

composite_factory = CompositeSubjectFactory(
    first_subject=subject,
    second_subject=subject2
)
composite_subject = composite_factory.get_midpoint_composite_subject_model()

composite_context = to_context(composite_subject)
print(composite_context)

# Example  5: Solar Return
print("\n" + "=" * 80)
print("EXAMPLE 5: SOLAR RETURN")
print("=" * 80)

solar_return_factory = PlanetaryReturnFactory(
    subject=subject,
    online=False,
    lng=subject.lng,
    lat=subject.lat,
    tz_str=subject.tz_str
)
solar_return = solar_return_factory.next_return_from_year(2024, "Solar")

solar_return_context = to_context(solar_return)
print(solar_return_context)

# Example 6: Lunar Return
print("\n" + "=" * 80)
print("EXAMPLE 6: LUNAR RETURN")
print("=" * 80)

lunar_return_factory = PlanetaryReturnFactory(
    subject=subject,
    online=False,
    lng=subject.lng,
    lat=subject.lat,
    tz_str=subject.tz_str
)
lunar_return = lunar_return_factory.next_return_from_month_and_year(2024, 1, "Lunar")

lunar_return_context = to_context(lunar_return)
print(lunar_return_context)

# Example 7: Transit Chart
print("\n" + "=" * 80)
print("EXAMPLE 7: TRANSIT CHART")
print("=" * 80)
print("(Using the historic date when John Lennon met Paul McCartney: July 6, 1957)\n")

# Create a transit moment for when John Lennon met Paul McCartney
transit_moment = AstrologicalSubjectFactory.from_birth_data(
    "Transit - Lennon meets McCartney", 1957, 7, 6, 18, 0, "Liverpool", "GB",
    suppress_geonames_warning=True
)

transit_data = ChartDataFactory.create_transit_chart_data(
    natal_subject=subject,
    transit_subject=transit_moment
)

transit_context = to_context(transit_data)
print(transit_context)

# Example 8: Individual Point (Planet)
print("\n" + "=" * 80)
print("EXAMPLE 8: INDIVIDUAL PLANET")
print("=" * 80)

sun_context = to_context(subject.sun)
print(sun_context)

# Example 9: Lunar Phase
print("\n" + "=" * 80)
print("EXAMPLE 9: LUNAR PHASE")
print("=" * 80)

if subject.lunar_phase:
    lunar_phase_context = to_context(subject.lunar_phase)
    print(lunar_phase_context)

# Example 10: Individual Aspect
print("\n" + "=" * 80)
print("EXAMPLE 10: INDIVIDUAL ASPECT")
print("=" * 80)

if natal_chart_data.aspects:
    first_aspect_context = to_context(natal_chart_data.aspects[0])
    print(first_aspect_context)

# Summary
print("\n" + "=" * 80)
print("SUMMARY - ALL MAJOR CHART TYPES DEMONSTRATED")
print("=" * 80)
print("""
The to_context() function supports all major chart types:

1. Natal Charts (AstrologicalSubjectModel)
2. Natal Charts with Aspects (SingleChartDataModel)
3. Synastry Charts (DualChartDataModel)
4. Composite Charts (CompositeSubjectModel)
5. Solar Returns (PlanetReturnModel)
6. Lunar Returns (PlanetReturnModel)
7. Transit Charts (DualChartDataModel)
8. Individual Points (KerykeionPointModel)
9. Lunar Phase (LunarPhaseModel)
10. Individual Aspects (AspectModel)
11. Element Distribution (ElementDistributionModel)
12. Quality Distribution (QualityDistributionModel)

Usage:
  from kerykeion import to_context
  context = to_context(any_model)
  print(context)
""")
