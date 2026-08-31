---
title: 'Report Module'
description: 'Generate human-readable text reports and tables from your astrological data. Ideal for CLI applications, debugging, and consolidated chart summaries.'
category: 'Core'
tags: ['docs', 'reports', 'kerykeion']
order: 5
---

# Report Module

The `ReportGenerator` class generates concise, human-readable text reports (tables) from any Kerykeion data model. It is ideal for CLI output, debugging, or log files.

## Supported Inputs

- **`AstrologicalSubjectModel`**: Basic birth/event data, celestial points, houses.
- **`SingleChartDataModel`**: Natal, Composite, Returns (includes elements, aspects, angularities, stelliums).
- **`DualChartDataModel`**: Synastry, Transits (includes comparison tables, per-subject angularities and stelliums).
- **`MoonPhaseOverviewModel`**: Detailed lunar phase context produced by [`MoonPhaseDetailsFactory`](/content/docs/moon_phase_details_factory) (includes moon summary, illumination, upcoming phases, eclipses, sun info, and location).
- **`ProfectionsModel`**: Annual profections from [`ProfectionsFactory`](/content/docs/profections_factory) — current year plus the surrounding window.
- **`FirdariaModel`**: Firdaria periods from [`FirdariaFactory`](/content/docs/firdaria_factory) — sect summary, the timeline, and the running period's sub-lords.
- **`HoraryIndicatorsModel`**: Significators, considerations and receptions from [`HoraryIndicatorsFactory`](/content/docs/horary_factory).
- **`MutualReceptionsModel`**: Domicile and exaltation receptions from [`MutualReceptionsFactory`](/content/docs/receptions_factory).
- **`DominantsModel`**: Ranked dominants from [`DominantsFactory`](/content/docs/dominants_factory) — one table per scored category.
- **`ZodiacalReleasingModel`**: Periods from [`ZodiacalReleasingFactory`](/content/docs/zodiacal_releasing_factory) — L1 timeline plus the current period chain.

The generator is **pure rendering**: it never calls a factory. Compute the
technique first, then hand the result over.

```python
from kerykeion import AstrologicalSubjectFactory, ProfectionsFactory, ReportGenerator

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False,
)
profections = ProfectionsFactory.from_subject(subject, target_date="2026-06-04")
ReportGenerator(profections).print_report()
```

## Optional Columns and Sections

Nothing renders on speculation: every optional column and section appears only
when the chart actually carries the data, so a report never widens into columns
of `-`.

| Column / section | Appears when |
| :--------------- | :----------- |
| `Motion` | A point has a `motion_state` (the ten planets, Earth-centred perspectives) |
| `OOB` | A point **is** out of bounds |
| `Mag.` | A point has a magnitude (fixed stars) |
| `Constellation` | The star is found in the catalog (Fixed Stars table only) |
| Arabic Parts | A lot is among the active points |
| Essential Dignities | The subject was built with `calculate_dignities=True` |
| Nakshatras | The subject was built with `calculate_nakshatra=True` |
| Gauquelin Sectors | The subject was built with `calculate_gauquelin=True` |
| Angularities / Stelliums | Chart data reports at least one |

## Usage

### Printing to Console

The simplest way to use the generator is to print the report directly to `stdout`. This is useful for CLI applications or debugging.

```python
from kerykeion import ReportGenerator, AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    city="London", nation="GB",
    lng=-0.1257, lat=51.5085, tz_str="Europe/London",
    online=False,
)
ReportGenerator(subject).print_report()
```

**Example Output:**

```text
======================
Alice — Subject Report
======================

+Astrological Subject — Birth Data---------------+
| Field              | Value                     |
+--------------------+---------------------------+
| Name               | Alice                     |
| Date               | 15/06/1990                |
| Time               | 12:00                     |
| City               | London                    |
| Nation             | GB                        |
| Latitude           | 51.5085°                  |
| Longitude          | -0.1257°                  |
| Timezone           | Europe/London             |
| Day of Week        | Friday                    |
| ISO Local Datetime | 1990-06-15T12:00:00+01:00 |
| Diurnality         | Diurnal                   |
+--------------------+---------------------------+

+Astrological Subject — Settings------------+
| Setting             | Value               |
+---------------------+---------------------+
| Zodiac Type         | Tropical            |
| Houses System       | Placidus            |
| Perspective Type    | Apparent Geocentric |
| Julian Day          | 2448057.958333      |
| Active Points Count | 14                  |
+---------------------+---------------------+

+Celestial Points-------+--------+----------+--------------+------------+---------+-----+------+---------------+
| Point                 | Sign   | Position | Speed        | Motion     | Decl.   | OOB | Ret. | House         |
+-----------------------+--------+----------+--------------+------------+---------+-----+------+---------------+
| Ascendant             | Vir ♍ | 14.74°   | +253.7365°/d | -          | N/A     | -   | -    | First House   |
| Medium Coeli          | Gem ♊ | 9.98°    | +338.4858°/d | -          | N/A     | -   | -    | Tenth House   |
| Sun                   | Gem ♊ | 24.09°   | +0.9551°/d   | Average    | +23.31° | -   | -    | Tenth House   |
| Moon                  | Pis ♓ | 14.80°   | +13.3469°/d  | Average    | -3.13°  | -   | -    | Seventh House |
| Mercury               | Gem ♊ | 5.62°    | +1.7140°/d   | Fast       | +19.60° | -   | -    | Ninth House   |
| Uranus                | Cap ♑ | 8.17°    | -0.0389°/d   | Retrograde | -23.51° | Y   | R    | Fourth House  |
| ...                                                                                                             |
+-----------------------+--------+----------+--------------+------------+---------+-----+------+---------------+

...

+Lunar Phase--------------+-----------------+
| Lunar Phase Information | Value           |
+-------------------------+-----------------+
| Phase Name              | Last Quarter 🌗 |
| Sun-Moon Angle          | 260.71°         |
| Lunation Day            | 21              |
+-------------------------+-----------------+
```

### Generating a String

Use `generate_report()` to return the string instead of printing it.

```python
from kerykeion import ChartDataFactory

from pathlib import Path

natal_data = ChartDataFactory.create_natal_chart_data(subject)
report_text = ReportGenerator(natal_data).generate_report(include_aspects=True)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
(output_dir / "report.txt").write_text(report_text, encoding="utf-8")
```

### Synastry / Transit Report

You can also generate reports from dual-chart data models:

```python
subject_b = AstrologicalSubjectFactory.from_birth_data(
    "Bob", 1992, 8, 20, 14, 30,
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False
)

synastry_data = ChartDataFactory.create_synastry_chart_data(subject, subject_b)
ReportGenerator(synastry_data).print_report(max_aspects=10)
```

The dual-chart report includes both subjects' birth data, inter-chart aspects, and house comparison tables (if available).

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

`ReportGenerator(model, *, include_aspects=True, max_aspects=None)` — everything
after `model` is keyword-only.

| Parameter         | Type   | Default      | Description                                                                                          |
| :---------------- | :----- | :----------- | :--------------------------------------------------------------------------------------------------- |
| `model`           | One of the nine models listed under [Supported Inputs](#supported-inputs): `ChartDataModel` (`SingleChartDataModel` / `DualChartDataModel`), `AstrologicalSubjectModel`, `MoonPhaseOverviewModel`, `ProfectionsModel`, `FirdariaModel`, `HoraryIndicatorsModel`, `MutualReceptionsModel`, `DominantsModel`, `ZodiacalReleasingModel` | **Required** | The data model to generate the report for. |
| `include_aspects` | `bool` | `True`       | Include the Aspect table. Ignored by the report layouts that have none.                              |
| `max_aspects`     | `int \| None` | `None` | Limit the number of aspects shown (`None` = all). Ignored by the report layouts that have none.      |

## Public API

| Method                                                           | Description                             |
| :--------------------------------------------------------------- | :-------------------------------------- |
| `generate_report(*, include_aspects=None, max_aspects=None) -> str` | Build the report content as a string. Both arguments are keyword-only; `None` keeps the constructor's value. |
| `print_report(*, include_aspects=None, max_aspects=None) -> None`   | Print the generated report to `stdout`, same arguments. |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
