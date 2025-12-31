---
title: 'Report Module'
category: 'Core'
tags: ['docs', 'reports', 'cli', 'kerykeion']
order: 5
---

# Report Module

The `ReportGenerator` class generates concise, human-readable text reports (tables) from any Kerykeion data model. It is ideal for CLI output, debugging, or log files.

## Supported Inputs

-   **`AstrologicalSubjectModel`**: Basic birth/event data, celestial points, houses.
-   **`SingleChartDataModel`**: Natal, Composite, Returns (includes elements, aspects).
-   **`DualChartDataModel`**: Synastry, Transits (includes comparison tables).

## Usage

### Printing to Console

```python
from kerykeion import ReportGenerator, AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 6, 15, 12, 0, "London", "GB")
ReportGenerator(subject).print_report()
```

### Generating a String

Use `generate_report()` to return the string instead of printing it.

```python
from kerykeion import ChartDataFactory

natal_data = ChartDataFactory.create_natal_chart_data(subject)
report_text = ReportGenerator(natal_data).generate_report(include_aspects=True)

with open("report.txt", "w") as f:
    f.write(report_text)
```

## Configuration

| Parameter         | Type   | Description                                                  |
| :---------------- | :----- | :----------------------------------------------------------- |
| `include_aspects` | `bool` | Include the Aspect table (default: `True` for Chart models). |
| `max_aspects`     | `int`  | Limit the number of aspects shown (default: `None` = all).   |

## Helper Methods

You can also retrieve specific sections of the report individually:

| Method                            | Description                                  |
| :-------------------------------- | :------------------------------------------- |
| `get_subject_data_report()`       | Subject metadata (name, date, location).     |
| `get_celestial_points_report()`   | Table of planets, signs, houses, and speeds. |
| `get_houses_report()`             | Table of house cusps.                        |
| `get_elements_report()`           | Element distribution table.                  |
| `get_qualities_report()`          | Quality distribution table.                  |
| `get_aspects_report()`            | Aspect table with symbols (`☌`, `△`, etc.).  |
| `get_relationship_score_report()` | Synastry score details (Dual charts only).   |
