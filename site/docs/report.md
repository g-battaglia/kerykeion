---
title: 'Report Module'
description: 'Generate human-readable text reports and tables from your astrological data. Ideal for CLI applications, debugging, and consolidated chart summaries.'
category: 'Core'
tags: ['docs', 'reports', 'cli', 'kerykeion']
order: 5
---

# Report Module

The `ReportGenerator` class generates concise, human-readable text reports (tables) from any Kerykeion data model. It is ideal for CLI output, debugging, or log files.

## Supported Inputs

- **`AstrologicalSubjectModel`**: Basic birth/event data, celestial points, houses.
- **`SingleChartDataModel`**: Natal, Composite, Returns (includes elements, aspects).
- **`DualChartDataModel`**: Synastry, Transits (includes comparison tables).
- **`MoonPhaseOverviewModel`**: Detailed lunar phase context produced by [`MoonPhaseDetailsFactory`](/content/docs/moon_phase_details_factory) (includes moon summary, illumination, upcoming phases, eclipses, sun info, and location).

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

### Moon Phase Overview Report

You can also generate a report from a `MoonPhaseOverviewModel` produced by the `MoonPhaseDetailsFactory`:

```python
from kerykeion import (
    AstrologicalSubjectFactory,
    MoonPhaseDetailsFactory,
    ReportGenerator,
)

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False,
)

overview = MoonPhaseDetailsFactory.from_subject(subject)
ReportGenerator(overview).print_report()
```

The moon phase overview report includes dedicated sections for Moon Summary, Illumination Details, Upcoming Phases, Next Lunar Eclipse, Sun Info, Next Solar Eclipse, and Location.

See the [Moon Phase Details Factory](/content/docs/moon_phase_details_factory) documentation for full details on the data model.

## Configuration

| Parameter         | Type                                                                    | Default      | Description                                                                                          |
| :---------------- | :---------------------------------------------------------------------- | :----------- | :--------------------------------------------------------------------------------------------------- |
| `model`           | `ChartDataModel`, `AstrologicalSubjectModel`, or `MoonPhaseOverviewModel` | **Required** | The data model to generate the report for.                                                           |
| `include_aspects` | `bool`                                                                  | `True`       | Include the Aspect table (default: `True`). Ignored for moon phase overview reports.                 |
| `max_aspects`     | `int`                                                                   | `None`       | Limit the number of aspects shown (default: `None` = all). Ignored for moon phase overview reports.  |

## Public API

| Method                                                           | Description                             |
| :--------------------------------------------------------------- | :-------------------------------------- |
| `generate_report(include_aspects=None, max_aspects=None) -> str` | Build the report content as a string.   |
| `print_report(include_aspects=None, max_aspects=None) -> None`   | Print the generated report to `stdout`. |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
