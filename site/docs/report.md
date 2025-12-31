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

The simplest way to use the generator is to print the report directly to `stdout`. This is useful for CLI applications or debugging.

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

## Configuration

| Parameter         | Type                                           | Default      | Description                                                |
| :---------------- | :--------------------------------------------- | :----------- | :--------------------------------------------------------- |
| `model`           | `ChartDataModel` or `AstrologicalSubjectModel` | **Required** | The data model to generate the report for.                 |
| `include_aspects` | `bool`                                         | `True`       | Include the Aspect table (default: `True`).                |
| `max_aspects`     | `int`                                          | `None`       | Limit the number of aspects shown (default: `None` = all). |

## Public API

| Method                                                           | Description                             |
| :--------------------------------------------------------------- | :-------------------------------------- |
| `generate_report(include_aspects=None, max_aspects=None) -> str` | Build the report content as a string.   |
| `print_report(include_aspects=None, max_aspects=None) -> None`   | Print the generated report to `stdout`. |
