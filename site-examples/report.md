---
layout: ../../layouts/DocLayout.astro
title: 'Report'
---

# Generate a text Report

This is a simple example of how to generate a report using the `ReportGenerator` class.

```python
from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Kanye", 1977, 6, 8, 8, 45,
    lng=-84.38798, lat=33.7490, tz_str="America/New_York", online=False,
)

# Subject-only report
ReportGenerator(subject).print_report(include_aspects=False)

# Or generate from chart data with aspects
natal = ChartDataFactory.create_natal_chart_data(subject)
ReportGenerator(natal).print_report(max_aspects=10)
```

The output in the terminal will be:

```plaintext
+- Kerykeion report for Kanye -+
... (tables for metadata, celestial points, houses, and aspects)

```
