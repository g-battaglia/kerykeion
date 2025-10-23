# Report Module

## Overview

The report subsystem turns any Kerykeion data model into a concise, console‑friendly document.
The new `ReportGenerator` class mirrors the chart dispatching logic of `ChartDrawer`: it inspects
the supplied model, detects its chart type, and assembles the relevant sections automatically.

Reports are designed for:
- human-readable exports (terminal, log files, chatbots)
- quick inspection during development
- debugging pipelines that produce chart data models
- educational walkthroughs of chart contents

Each report is made up of ASCII tables and prose headers, making it easy to read or redirect
into text files without additional formatting libraries.

## Supported Inputs

`ReportGenerator` accepts:
- `AstrologicalSubjectModel` — raw subject data (natal event, return subject, transit moment, …)
- `SingleChartDataModel` — natal, composite, or single return data produced by `ChartDataFactory`
- `DualChartDataModel` — synastry, transit, or dual return data produced by `ChartDataFactory`

Every model comes with its own context and optional sections:

| Input model | Detected chart types | Secondary subject | Chart-specific sections |
|-------------|----------------------|-------------------|-------------------------|
| `AstrologicalSubjectModel` | `"Subject"` | – | Birth/event data, celestial points, houses, lunar phase |
| `SingleChartDataModel` | `"Natal"`, `"Composite"`, `"SingleReturnChart"` | Optional composite members | Elements, qualities, active configuration, aspects |
| `DualChartDataModel` | `"Transit"`, `"Synastry"`, `"DualReturnChart"` | Required | House comparison, relationship score, dual-aspect layout |

## Quickstart

```python
from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

# Base subject
subject = AstrologicalSubjectFactory.from_birth_data(
    "Sample Natal", 1990, 7, 21, 14, 45,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

# Subject-only report
ReportGenerator(subject).print_report(include_aspects=False)

# Natal chart data (elements, qualities, aspects included)
natal = ChartDataFactory.create_natal_chart_data(subject)
ReportGenerator(natal).print_report(max_aspects=10)

# Synastry chart between two subjects
partner = AstrologicalSubjectFactory.from_birth_data(
    "Sample Partner", 1992, 11, 5, 9, 30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
synastry = ChartDataFactory.create_synastry_chart_data(subject, partner)
ReportGenerator(synastry).print_report(max_aspects=12)
```

Use `generate_report()` when you need the string instead of printing directly:

```python
from pathlib import Path
from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Sample Natal", 1990, 7, 21, 14, 45,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
natal = ChartDataFactory.create_natal_chart_data(subject)

text_report = ReportGenerator(natal).generate_report(include_aspects=True, max_aspects=6)
Path("natal_report.txt").write_text(text_report, encoding="utf-8")
```

## Chart-specific Examples

### AstrologicalSubjectModel reports

Subject reports focus on a single `AstrologicalSubjectModel` and omit derived analytics that
require chart data factories.

```python
from kerykeion import AstrologicalSubjectFactory, ReportGenerator

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1988, 3, 12, 8, 10,
    lng=2.3522,
    lat=48.8566,
    tz_str="Europe/Paris",
    online=False,
)
ReportGenerator(subject, include_aspects=False).print_report()
```

Sections produced:
- subject metadata (birth data, location, configuration)
- celestial points with sign, position, daily motion, declination, retrograde flag, and house
- house cusps for the subject’s house system
- lunar phase summary if available

### SingleChartDataModel reports

Single-chart data models add aggregated analytics. The dispatcher automatically recognises
the specific chart type:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ReportGenerator

subject = AstrologicalSubjectFactory.from_birth_data(
    "Report Subject", 1990, 5, 10, 13, 20,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
ReportGenerator(chart_data).print_report(max_aspects=8)
```

Composite subjects include additional member summaries:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ReportGenerator
from kerykeion.composite_subject_factory import CompositeSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Partner A", 1985, 4, 18, 9, 45,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
partner = AstrologicalSubjectFactory.from_birth_data(
    "Partner B", 1987, 9, 2, 19, 10,
    lng=2.3522,
    lat=48.8566,
    tz_str="Europe/Paris",
    online=False,
)

composite_subject = CompositeSubjectFactory(subject, partner).get_midpoint_composite_subject_model()
composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)
ReportGenerator(composite_data).print_report(max_aspects=5)
```

Single planetary returns (solar or lunar) are equally supported:

```python
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ReportGenerator
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Return Subject", 1990, 7, 21, 14, 45,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

factory = PlanetaryReturnFactory(
    subject,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False
)
return_subject = factory.next_return_from_year(2024, "Solar")
return_data = ChartDataFactory.create_single_wheel_return_chart_data(return_subject)
ReportGenerator(return_data).print_report(max_aspects=4)
```

### DualChartDataModel reports

Dual chart data includes both subjects and the comparisons between them.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ReportGenerator
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Natal Subject", 1990, 7, 21, 14, 45,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
partner = AstrologicalSubjectFactory.from_birth_data(
    "Transit Snapshot", 2024, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "Transit Chart", 2024, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

factory = PlanetaryReturnFactory(
    subject,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
return_subject = factory.next_return_from_year(2024, "Solar")

# Transit chart (natal subject vs snapshot of current sky)
transit = ChartDataFactory.create_transit_chart_data(subject, transit_subject)
ReportGenerator(transit).print_report(max_aspects=10)

# Synastry with full house comparison and relationship score
synastry = ChartDataFactory.create_synastry_chart_data(subject, partner)
ReportGenerator(synastry).print_report(max_aspects=12)

# Dual return (natal vs solar return subject)
dual_return = ChartDataFactory.create_return_chart_data(subject, return_subject)
ReportGenerator(dual_return).print_report(max_aspects=6)
```

Dual reports add:
- duplicated subject data (one table per participant)
- two celestial-points tables (one per subject)
- house lists for both subjects
- optional house comparison grids (points projected into partner houses)
- optional relationship score summary with supporting aspects
- aspect tables showing point owners for each side

## Section reference

All helper methods remain accessible so you can assemble custom outputs.

| Method | Description |
|--------|-------------|
| `get_report_title()` | Returns the chart-aware heading (with separators). |
| `get_subject_data_report()` | Core metadata table(s) for the relevant subject. |
| `get_celestial_points_report()` | ASCII table of active celestial points. |
| `get_houses_report()` | House cusp table for the supplied subject. |
| `get_lunar_phase_report()` | Lunar phase table when data is present. Empty string otherwise. |
| `get_elements_report()` | Element distribution table (single/dual chart data only). |
| `get_qualities_report()` | Quality distribution table (single/dual chart data only). |
| `get_aspects_report(max_aspects=None)` | Aspect table with symbols for type and movement. |
| `generate_report()` | Constructs the full report as a string. |
| `print_report()` | Prints the report to stdout. |

Additional helpers invoked internally:
- `ReportGenerator._active_configuration_report()` — active points and aspect settings
- `ReportGenerator._house_comparison_report()` — dual-chart house overlays
- `ReportGenerator._relationship_score_report()` — synastry scoring details

## Working with aspects

- `include_aspects=False` suppresses the aspect section entirely.
- `max_aspects=<int>` limits the number of rows (handy for dense transit charts).
- Dual chart tables include owner columns so you can distinguish which subject each point belongs to.
- Aspect names map to unicode symbols (`☌`, `☍`, `△`, `□`, `⚹`, …) and movement arrows (`→`, `←`, `✓`).

Example:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ReportGenerator

subject = AstrologicalSubjectFactory.from_birth_data(
    "Person A", 1990, 7, 21, 14, 45,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
partner = AstrologicalSubjectFactory.from_birth_data(
    "Person B", 1992, 5, 10, 9, 30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

synastry = ChartDataFactory.create_synastry_chart_data(subject, partner)
report = ReportGenerator(synastry)
print(report.generate_report(max_aspects=5))
```

```
+Point 1+Owner 1+Aspect+Point 2+Owner 2+Orb+Movement+
| Sun   | Alice | ☌    | Moon   | Partner | 1.24° | Applying →
...
```

## Understanding motion and declination columns

- **Speed (daily motion)** expresses the rate of change in degrees per day. Negative values indicate retrograde motion.
- **Declination** is the angular distance north/south of the celestial equator. Values beyond ±23.44° highlight out‑of‑bounds behaviour.
- **Ret.** is a shorthand retrograde flag (`R` or `-`).

These metrics are already calculated by the factories; the report simply formats them.

## Writing to files

Reports are plain text, so standard Python I/O works:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ReportGenerator

subject = AstrologicalSubjectFactory.from_birth_data(
    "Export Natal", 1990, 7, 21, 14, 45,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
natal = ChartDataFactory.create_natal_chart_data(subject)
report = ReportGenerator(natal)
Path("natal_report.txt").write_text(report.generate_report(), encoding="utf-8")
```

Redirecting stdout also works:

```bash
python make_report.py > synastry_report.txt
```

## Inline examples (`python -m kerykeion.report`)

Running the module directly executes a suite of full examples that cover each supported model:

```bash
python -m kerykeion.report
```

The script prints complete reports (one per model type) using offline birth data for Rome to guarantee deterministic results.

## Migrating from older versions

- Update imports to `from kerykeion import ReportGenerator`.
- Ensure your code now instantiates `ReportGenerator(...)` everywhere.
- New keyword arguments (`include_aspects`, `max_aspects`) behave exactly as before.
- To access the raw string, prefer `generate_report()` rather than capturing stdout.

With these updates the report system stays fully compatible with earlier code while gaining support for every chart type that Kerykeion can produce.
