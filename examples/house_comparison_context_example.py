#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example demonstrating house comparison serialization in context_serializer.

This example shows how the new house comparison serialization works
for different dual chart types.
"""

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, to_context

# Create two subjects for synastry
john = AstrologicalSubjectFactory.from_birth_data(
    name="John", year=1990, month=5, day=15, hour=10, minute=30, city="London", nation="GB"
)

jane = AstrologicalSubjectFactory.from_birth_data(
    name="Jane", year=1992, month=8, day=23, hour=14, minute=45, city="Paris", nation="FR"
)

# Create synastry chart data with house comparison
synastry_data = ChartDataFactory.create_synastry_chart_data(
    first_subject=john,
    second_subject=jane,
    include_house_comparison=True,  # This is the default
)

# Serialize to AI-friendly text context
context = to_context(synastry_data)

print("SYNASTRY CHART WITH HOUSE COMPARISON:")
print("=" * 80)
print(context)

# The output will include a "House Overlay Analysis" section showing:
# - John's planets in Jane's houses
# - Jane's planets in John's houses

# For transit charts, the same works but with special handling:
transit = AstrologicalSubjectFactory.from_current_time(name="Current Transit", city="London", nation="GB")

transit_data = ChartDataFactory.create_transit_chart_data(
    natal_subject=john, transit_subject=transit, include_house_comparison=True
)

print("\n\nTRANSIT CHART WITH HOUSE COMPARISON:")
print("=" * 80)
print(to_context(transit_data))

# The transit output will show:
# - John's planets in Transit's houses
# - "Transit planets in John's houses" (note the special wording)
# - Transit planets won't show their original house positions
