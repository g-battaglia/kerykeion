<h1 align="center">Kerykeion</h1>

<div align="center">
    <img src="https://img.shields.io/github/stars/g-battaglia/kerykeion.svg?logo=github" alt="stars">
    <img src="https://img.shields.io/github/forks/g-battaglia/kerykeion.svg?logo=github" alt="forks">
</div>
<div align="center">
    <img src="https://static.pepy.tech/badge/kerykeion/month" alt="PyPI Downloads">
    <img src="https://static.pepy.tech/badge/kerykeion/week" alt="PyPI Downloads">
    <img src="https://static.pepy.tech/personalized-badge/kerykeion?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads/total" alt="PyPI Downloads">
</div>
<div align="center">
    <img src="https://img.shields.io/pypi/v/kerykeion?label=pypi%20package" alt="Package version">
    <img src="https://img.shields.io/pypi/pyversions/kerykeion.svg" alt="Supported Python versions">
</div>
<p align="center">⭐ Like this project? Star it on GitHub and help it grow! ⭐</p>
&nbsp;

Kerykeion is a Python library for astrology. It computes planetary and house positions, detects aspects, and generates SVG charts—including birth, synastry, transit, and composite charts. You can also customize which planets to include in your calculations.

The main goal of this project is to offer a clean, data-driven approach to astrology, making it accessible and programmable.

Kerykeion also integrates seamlessly with LLM and AI applications.

Here is an example of a birthchart:

![John Lenon Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Dark%20Theme%20-%20Natal%20Chart.svg)

## **Web API**

If you want to use Kerykeion in a web application or for commercial or *closed-source* purposes, you can try the dedicated web API:

**[AstrologerAPI](https://rapidapi.com/gbattaglia/api/astrologer/pricing)**

It is [open source](https://github.com/g-battaglia/Astrologer-API) and directly supports this project.

## **Donate**

Maintaining this project requires substantial time and effort. The Astrologer API alone cannot cover the costs of full-time development. If you find Kerykeion valuable and would like to support further development, please consider donating:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kerykeion)

## Table of Contents

- [**Web API**](#web-api)
- [**Donate**](#donate)
- [Table of Contents](#table-of-contents)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation Map](#documentation-map)
- [Basic Usage](#basic-usage)
- [Generate a SVG Chart](#generate-a-svg-chart)
  - [Birth Chart](#birth-chart)
  - [External Birth Chart](#external-birth-chart)
  - [Synastry Chart](#synastry-chart)
  - [Transit Chart](#transit-chart)
  - [Solar Return Chart (Dual Wheel)](#solar-return-chart-dual-wheel)
  - [Solar Return Chart (Single Wheel)](#solar-return-chart-single-wheel)
  - [Lunar Return Chart](#lunar-return-chart)
  - [Composite Chart](#composite-chart)
- [Wheel Only Charts](#wheel-only-charts)
  - [Birth Chart](#birth-chart-1)
  - [Wheel Only Birth Chart (External)](#wheel-only-birth-chart-external)
  - [Synastry Chart](#synastry-chart-1)
  - [Change the Output Directory](#change-the-output-directory)
  - [Change Language](#change-language)
  - [Minified SVG](#minified-svg)
  - [SVG without CSS Variables](#svg-without-css-variables)
  - [Grid Only SVG](#grid-only-svg)
- [Report Generator](#report-generator)
  - [Quick Examples](#quick-examples)
  - [Section Access](#section-access)
- [Example: Retrieving Aspects](#example-retrieving-aspects)
- [Element \& Quality Distribution Strategies](#element--quality-distribution-strategies)
- [Ayanamsa (Sidereal Modes)](#ayanamsa-sidereal-modes)
- [House Systems](#house-systems)
- [Perspective Type](#perspective-type)
- [Themes](#themes)
- [Alternative Initialization](#alternative-initialization)
- [Lunar Nodes (Rahu \& Ketu)](#lunar-nodes-rahu--ketu)
- [JSON Support](#json-support)
- [Auto Generated Documentation](#auto-generated-documentation)
- [Development](#development)
- [Kerykeion v5.0 – What's New](#kerykeion-v50--whats-new)
  - [🎯 Key Highlights](#-key-highlights)
    - [Factory-Centered Architecture](#factory-centered-architecture)
    - [Pydantic 2 Models \& Type Safety](#pydantic-2-models--type-safety)
    - [Enhanced Features](#enhanced-features)
  - [📦 Other Notable Changes](#-other-notable-changes)
  - [🎨 New Themes](#-new-themes)
  - [📚 Resources](#-resources)
- [Integrating Kerykeion into Your Project](#integrating-kerykeion-into-your-project)
- [License](#license)
- [Contributing](#contributing)
- [Citations](#citations)

## Installation

Kerykeion requires **Python 3.9** or higher.

```bash
pip3 install kerykeion
```

## Quick Start

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person",
    year=1990, month=7, day=15,
    hour=10, minute=30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

chart_drawer.save_svg(output_path=output_dir, filename="example-natal")
print("Chart saved to", (output_dir / "example-natal.svg").resolve())
```

This script shows the recommended workflow:
1. Create an `AstrologicalSubject` with explicit coordinates and timezone (offline mode).
2. Build a `ChartDataModel` through `ChartDataFactory`.
3. Render the SVG via `ChartDrawer`, saving it to a controlled folder (`charts_output`).

Use the same pattern for synastry, composite, transit, or return charts by swapping the factory method.

## Documentation Map

- **README (this file):** Quick start, common recipes, and v5 overview. Full migration guide: [MIGRATION_V4_TO_V5.md](MIGRATION_V4_TO_V5.md).
- **`site-docs/` (offline Markdown guides):** Deep dives for each factory (`chart_data_factory.md`, `charts.md`, `planetary_return_factory.md`, etc.) with runnable snippets. Run `python scripts/test_markdown_snippets.py site-docs` to validate them locally.
- **[Auto-generated API Reference](https://www.kerykeion.net/pydocs/kerykeion.html):** Detailed model and function signatures straight from the codebase.
- **[Kerykeion website](https://www.kerykeion.net/docs/):** Rendered documentation with additional context, tutorials, and showcase material.

## Basic Usage

Below is a simple example illustrating the creation of an astrological subject and retrieving astrological details:

```python
from kerykeion import AstrologicalSubjectFactory

# Create an instance of the AstrologicalSubjectFactory class.
# Arguments: Name, year, month, day, hour, minutes, city, nation
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Retrieve information about the Sun:
print(john.sun.model_dump_json())
# > {"name":"Sun","quality":"Cardinal","element":"Air","sign":"Lib","sign_num":6,"position":16.26789199474399,"abs_pos":196.267891994744,"emoji":"♎️","point_type":"AstrologicalPoint","house":"Sixth_House","retrograde":false}

# Retrieve information about the first house:
print(john.first_house.model_dump_json())
# > {"name":"First_House","quality":"Cardinal","element":"Fire","sign":"Ari","sign_num":0,"position":19.74676624176799,"abs_pos":19.74676624176799,"emoji":"♈️","point_type":"House","house":null,"retrograde":null}

# Retrieve the element of the Moon sign:
print(john.moon.element)
# > 'Air'
```

> **Working offline:** pass `online=False` and specify `lng`, `lat`, and `tz_str` as shown above.  
> **Working online:** set `online=True` and provide `city`, `nation`, and a valid GeoNames username (see `AstrologicalSubjectFactory.from_birth_data()` for details).

**To avoid using GeoNames online, specify longitude, latitude, and timezone instead of city and nation:**

```python
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,  # Longitude for Liverpool
    lat=53.4000,  # Latitude for Liverpool
    tz_str="Europe/London",  # Timezone for Liverpool
    city="Liverpool",
)
```

## Generate a SVG Chart

All chart-rendering examples below create a local `charts_output/` folder so the tests can write without touching your home directory. Feel free to change the path when integrating into your own projects.

To generate a chart, use the `ChartDataFactory` to pre-compute chart data, then `ChartDrawer` to create the visualization. This two-step process ensures clean separation between astrological calculations and chart rendering.

**Tip:**
The optimized way to open the generated SVG files is with a web browser (e.g., Chrome, Firefox).
To improve compatibility across different applications, you can use the `remove_css_variables` parameter when generating the SVG. This will inline all styles and eliminate CSS variables, resulting in an SVG that is more broadly supported.

### Birth Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(john)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
birth_chart_svg.save_svg(output_path=output_dir, filename="john-lennon-natal")
```

The SVG file is saved under `charts_output/john-lennon-natal.svg`.
![John Lennon Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Natal%20Chart.svg)

### External Birth Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute chart data for external natal chart
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
birth_chart_svg.save_svg(output_path=output_dir, filename="john-lennon-natal-external")
```

![John Lennon External Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20ExternalNatal%20-%20Natal%20Chart.svg)

### Synastry Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)
second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney", 1942, 6, 18, 15, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(first, second)

# Step 3: Create visualization
synastry_chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
synastry_chart.save_svg(output_path=output_dir, filename="lennon-mccartney-synastry")
```

![John Lennon and Paul McCartney Synastry](https://www.kerykeion.net/img/examples/synastry-chart.svg)

### Transit Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
transit = AstrologicalSubjectFactory.from_birth_data(
    "Transit", 2025, 6, 8, 8, 45,
    lng=-84.3880,
    lat=33.7490,
    tz_str="America/New_York",
    online=False,
)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute transit chart data
chart_data = ChartDataFactory.create_transit_chart_data(subject, transit)

# Step 3: Create visualization
transit_chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
transit_chart.save_svg(output_path=output_dir, filename="john-lennon-transit")
```

![John Lennon Transit Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Transit%20Chart.svg)

### Solar Return Chart (Dual Wheel)

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create natal subject
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Calculate Solar Return subject (offline example with manual coordinates)
return_factory = PlanetaryReturnFactory(
    john,
    lng=-2.9833,
    lat=53.4000,
    tz_str="Europe/London",
    online=False
)
solar_return_subject = return_factory.next_return_from_year(1964, "Solar")

# Step 3: Pre-compute return chart data (dual wheel: natal + solar return)
chart_data = ChartDataFactory.create_return_chart_data(john, solar_return_subject)

# Step 4: Create visualization
solar_return_chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
solar_return_chart.save_svg(output_path=output_dir, filename="john-lennon-solar-return-dual")
```

![John Lennon Solar Return Chart (Dual Wheel)](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20DualReturnChart%20Chart%20-%20Solar%20Return.svg)

### Solar Return Chart (Single Wheel)

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create natal subject
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Calculate Solar Return subject (offline example with manual coordinates)
return_factory = PlanetaryReturnFactory(
    john,
    lng=-2.9833,
    lat=53.4000,
    tz_str="Europe/London",
    online=False
)
solar_return_subject = return_factory.next_return_from_year(1964, "Solar")

# Step 3: Build a single-wheel return chart
chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return_subject)

# Step 4: Create visualization
single_wheel_chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
single_wheel_chart.save_svg(output_path=output_dir, filename="john-lennon-solar-return-single")
```

![John Lennon Solar Return Chart (Single Wheel)](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20Solar%20Return%20-%20SingleReturnChart%20Chart.svg)

### Lunar Return Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create natal subject
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Calculate Lunar Return subject
return_factory = PlanetaryReturnFactory(
    john,
    lng=-2.9833,
    lat=53.4000,
    tz_str="Europe/London",
    online=False
)
lunar_return_subject = return_factory.next_return_from_year(1964, "Lunar")

# Step 3: Build a dual wheel (natal + lunar return)
lunar_return_chart_data = ChartDataFactory.create_return_chart_data(john, lunar_return_subject)
dual_wheel_chart = ChartDrawer(chart_data=lunar_return_chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
dual_wheel_chart.save_svg(output_path=output_dir, filename="john-lennon-lunar-return-dual")

# Optional: create a single-wheel lunar return
single_wheel_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return_subject)
single_wheel_chart = ChartDrawer(chart_data=single_wheel_data)
single_wheel_chart.save_svg(output_path=output_dir, filename="john-lennon-lunar-return-single")
```

![John Lennon Lunar Return Chart (Dual Wheel)](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20DualReturnChart%20Chart%20-%20Lunar%20Return.svg)

![John Lennon Lunar Return Chart (Single Wheel)](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20Lunar%20Return%20-%20SingleReturnChart%20Chart.svg)

### Composite Chart

```python
from pathlib import Path
from kerykeion import CompositeSubjectFactory, AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects (offline configuration)
angelina = AstrologicalSubjectFactory.from_birth_data(
    "Angelina Jolie", 1975, 6, 4, 9, 9,
    lng=-118.2437,
    lat=34.0522,
    tz_str="America/Los_Angeles",
    online=False,
)

brad = AstrologicalSubjectFactory.from_birth_data(
    "Brad Pitt", 1963, 12, 18, 6, 31,
    lng=-96.7069,
    lat=35.3273,
    tz_str="America/Chicago",
    online=False,
)

# Step 2: Create composite subject
factory = CompositeSubjectFactory(angelina, brad)
composite_model = factory.get_midpoint_composite_subject_model()

# Step 3: Pre-compute composite chart data
chart_data = ChartDataFactory.create_composite_chart_data(composite_model)

# Step 4: Create visualization
composite_chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
composite_chart.save_svg(output_path=output_dir, filename="jolie-pitt-composite")
```

![Angelina Jolie and Brad Pitt Composite Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/Angelina%20Jolie%20and%20Brad%20Pitt%20Composite%20Chart%20-%20Composite%20Chart.svg)

## Wheel Only Charts

For _all_ the charts, you can generate a wheel-only chart by using the method `makeWheelOnlySVG()`:

### Birth Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
birth_chart_svg.save_wheel_only_svg_file(output_path=output_dir, filename="john-lennon-natal-wheel")
```

![John Lennon Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Wheel%20Only%20-%20Natal%20Chart%20-%20Wheel%20Only.svg)

### Wheel Only Birth Chart (External)

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute external natal chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization (external wheel view)
birth_chart_svg = ChartDrawer(chart_data=chart_data, external_view=True)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
birth_chart_svg.save_wheel_only_svg_file(output_path=output_dir, filename="john-lennon-natal-wheel-external")
```

![John Lennon Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Wheel%20External%20Only%20-%20ExternalNatal%20Chart%20-%20Wheel%20Only.svg)

### Synastry Chart

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)
second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney", 1942, 6, 18, 15, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(first, second)

# Step 3: Create visualization
synastry_chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
synastry_chart.save_wheel_only_svg_file(output_path=output_dir, filename="lennon-mccartney-synastry-wheel")
```

![John Lennon and Paul McCartney Synastry](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Wheel%20Synastry%20Only%20-%20Synastry%20Chart%20-%20Wheel%20Only.svg)

### Change the Output Directory

To save the SVG file in a custom location, specify the `output_path` parameter in `save_svg()`:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
first = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)
second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney", 1942, 6, 18, 15, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(first, second)

# Step 3: Create visualization with custom output directory
synastry_chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
synastry_chart.save_svg(output_path=output_dir)
print("Saved to", (output_dir / f"{synastry_chart.first_obj.name} - Synastry Chart.svg").resolve())
```

### Change Language

You can switch chart language by passing `chart_language` to the `ChartDrawer` class:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization with Italian language
birth_chart_svg = ChartDrawer(
    chart_data=chart_data,
    chart_language="IT"  # Change to Italian
)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
birth_chart_svg.save_svg(output_path=output_dir, filename="john-lennon-natal-it")
```

You can also provide custom labels (or introduce a brand-new language) by passing
a dictionary to `language_pack`. Only the keys you supply are merged on top of the
built-in strings:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

birth_chart = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

custom_labels = {
    "PT": {
        "info": "Informações",
        "celestial_points": {"Sun": "Sol", "Moon": "Lua"},
    }
}

custom_chart = ChartDrawer(
    chart_data=chart_data,
    chart_language="PT",
    language_pack=custom_labels["PT"],
)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
custom_chart.save_svg(output_path=output_dir, filename="john-lennon-natal-pt")
```

More details [here](https://www.kerykeion.net/docs/chart-language).

The available languages are:

-   EN (English)
-   FR (French)
-   PT (Portuguese)
-   ES (Spanish)
-   TR (Turkish)
-   RU (Russian)
-   IT (Italian)
-   CN (Chinese)
-   DE (German)

### Minified SVG

To generate a minified SVG, set `minify_svg=True` in the `makeSVG()` method:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
birth_chart_svg.save_svg(
    output_path=output_dir,
    filename="john-lennon-natal-minified",
    minify=True,
)
```

### SVG without CSS Variables

To generate an SVG without CSS variables, set `remove_css_variables=True` in the `makeSVG()` method:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
birth_chart_svg.save_svg(
    output_path=output_dir,
    filename="john-lennon-natal-no-css-variables",
    remove_css_variables=True,
)
```

This will inline all styles and eliminate CSS variables, resulting in an SVG that is more broadly supported.

### Grid Only SVG

It's possible to generate a grid-only SVG, useful for creating a custom layout. To do this, use the `save_aspect_grid_only_svg_file()` method:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
birth_chart = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)
second = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney", 1942, 6, 18, 15, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(birth_chart, second)

# Step 3: Create visualization with dark theme
aspect_grid_chart = ChartDrawer(chart_data=chart_data, theme="dark")

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
aspect_grid_chart.save_aspect_grid_only_svg_file(output_path=output_dir, filename="lennon-mccartney-aspect-grid")
```

![John Lennon Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Aspect%20Grid%20Only%20-%20Natal%20Chart%20-%20Aspect%20Grid%20Only.svg)

## Report Generator

`ReportGenerator` mirrors the chart-type dispatch of `ChartDrawer`. It accepts raw `AstrologicalSubjectModel` instances as well as any `ChartDataModel` produced by `ChartDataFactory`—including natal, composite, synastry, transit, and planetary return charts—and renders the appropriate textual report automatically.

### Quick Examples

```python
from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

# Subject-only report
subject = AstrologicalSubjectFactory.from_birth_data(
    "Sample Natal", 1990, 7, 21, 14, 45,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
ReportGenerator(subject).print_report(include_aspects=False)

# Single-chart data (elements, qualities, aspects enabled)
natal_data = ChartDataFactory.create_natal_chart_data(subject)
ReportGenerator(natal_data).print_report(max_aspects=10)

# Dual-chart data (synastry, transit, dual return, …)
partner = AstrologicalSubjectFactory.from_birth_data(
    "Sample Partner", 1992, 11, 5, 9, 30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
synastry_data = ChartDataFactory.create_synastry_chart_data(subject, partner)
ReportGenerator(synastry_data).print_report(max_aspects=12)
```

Each report contains:

-   A chart-aware title summarising the subject(s) and chart type
-   Birth/event metadata and configuration settings
-   Celestial points with sign, position, **daily motion**, **declination**, retrograde flag, and house
-   House cusp tables for every subject involved
-   Lunar phase details when available
-   Element/quality distributions and active configuration summaries (for chart data)
-   Aspect listings tailored for single or dual charts, with symbols for type and movement
-   Dual-chart extras such as house comparisons and relationship scores (when provided by the data)

### Section Access

All section helpers remain available for targeted output:

```python
from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Sample Natal", 1990, 7, 21, 14, 45,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
natal_data = ChartDataFactory.create_natal_chart_data(subject)

report = ReportGenerator(natal_data)
sections = report.generate_report(max_aspects=5).split("\n\n")
for section in sections[:3]:
    print(section)
```

Refer to the refreshed [Report Documentation](https://www.kerykeion.net/report/) for end-to-end examples covering every supported chart model.

## Example: Retrieving Aspects

Kerykeion provides a unified `AspectsFactory` class for calculating astrological aspects within single charts or between two charts:

```python
from kerykeion import AspectsFactory, AstrologicalSubjectFactory

# Create astrological subjects
jack = AstrologicalSubjectFactory.from_birth_data(
    "Jack", 1990, 6, 15, 15, 15,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
jane = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1991, 10, 25, 21, 0,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

# For single chart aspects (natal, return, composite, etc.)
single_chart_result = AspectsFactory.single_chart_aspects(jack)
print(f"Found {len(single_chart_result.aspects)} aspects in Jack's chart")
print(single_chart_result.aspects[0])

# For dual chart aspects (synastry, transits, comparisons, etc.)
dual_chart_result = AspectsFactory.dual_chart_aspects(jack, jane)
print(f"Found {len(dual_chart_result.aspects)} aspects between Jack and Jane's charts")
print(dual_chart_result.aspects[0])

# Each AspectModel includes:
# - p1_name, p2_name: Planet/point names
# - aspect: Aspect type (conjunction, trine, square, etc.)
# - orbit: Orb tolerance in degrees
# - aspect_degrees: Exact degrees for the aspect (0, 60, 90, 120, 180, etc.)
# - color: Hex color code for visualization
```

**Advanced Usage with Custom Settings:**

```python
# You can also customize aspect calculations with custom orb settings
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_ASPECTS

# Modify aspect settings if needed
custom_aspects = DEFAULT_ACTIVE_ASPECTS.copy()
# ... modify as needed

# The factory automatically uses the configured settings for orb calculations
# and filters aspects based on relevance and orb thresholds
```

## Element & Quality Distribution Strategies

`ChartDataFactory` now offers two strategies for calculating element and modality totals. The default `"weighted"` mode leans on a curated map that emphasises core factors (for example `sun`, `moon`, and `ascendant` weight 2.0, angles such as `medium_coeli` 1.5, personal planets 1.5, social planets 1.0, outers 0.5, and minor bodies 0.3–0.8). Provide `distribution_method="pure_count"` when you want every active point to contribute equally.

You can refine the weighting without rebuilding the dictionary: pass lowercase point names to `custom_distribution_weights` and use `"__default__"` to override the fallback value applied to entries that are not listed explicitly.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Sample", 1986, 4, 12, 8, 45,
    lng=11.3426,
    lat=44.4949,
    tz_str="Europe/Rome",
    online=False,
)

# Equal weighting: every active point counts once
pure_data = ChartDataFactory.create_natal_chart_data(
    subject,
    distribution_method="pure_count",
)

# Custom emphasis: boost the Sun, soften everything else
weighted_data = ChartDataFactory.create_natal_chart_data(
    subject,
    distribution_method="weighted",
    custom_distribution_weights={
        "sun": 3.0,
        "__default__": 0.75,
    },
)

print(pure_data.element_distribution.fire)
print(weighted_data.element_distribution.fire)
```

All convenience helpers (`create_synastry_chart_data`, `create_transit_chart_data`, returns, and composites) forward the same keyword-only parameters, so you can keep a consistent weighting scheme across every chart type.

For an extended walkthrough (including category breakdowns of the default map), see `site-docs/element_quality_distribution.md`.

## Ayanamsa (Sidereal Modes)

By default, the zodiac type is **Tropical**. To use **Sidereal**, specify the sidereal mode:

```python
johnny = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI"
)
```

More examples [here](https://www.kerykeion.net/docs//sidereal-modes/).

Full list of supported sidereal modes [here](https://www.kerykeion.net/pydocs/kerykeion/schemas/kr_literals.html#SiderealMode).

## House Systems

By default, houses are calculated using **Placidus**. Configure a different house system as follows:

```python
johnny = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
    houses_system_identifier="M"
)
```

More examples [here](https://www.kerykeion.net/docs//houses-systems/).

Full list of supported house systems [here](https://www.kerykeion.net/pydocs/kerykeion/schemas/kr_literals.html#HousesSystem).

So far all the available houses system in the Swiss Ephemeris are supported but the Gauquelin Sectors.

## Perspective Type

By default, Kerykeion uses the **Apparent Geocentric** perspective (the most standard in astrology). Other perspectives (e.g., **Heliocentric**) can be set this way:

```python
johnny = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
    perspective_type="Heliocentric"
)
```

More examples [here](https://www.kerykeion.net/docs//perspective-type/).

Full list of supported perspective types [here](https://www.kerykeion.net/pydocs/kerykeion/schemas/kr_literals.html#PerspectiveType).

## Themes

Kerykeion provides several chart themes:

-   **Classic** (default)
-   **Dark**
-   **Dark High Contrast**
-   **Light**
-   **Strawberry**
-   **Black & White** (optimized for monochrome printing)

Each theme offers a distinct visual style, allowing you to choose the one that best suits your preferences or presentation needs. If you prefer more control over the appearance, you can opt not to set any theme, making it easier to customize the chart by overriding the default CSS variables. For more detailed instructions on how to apply themes, check the [documentation](https://www.kerykeion.net/docs/theming)

The Black & White theme renders glyphs, rings, and aspects in solid black on light backgrounds, designed for crisp B/W prints (PDF or paper) without sacrificing legibility.

Here's an example of how to set the theme:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
dark_theme_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Dark Theme", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(dark_theme_subject)

# Step 3: Create visualization with dark high contrast theme
dark_theme_natal_chart = ChartDrawer(chart_data=chart_data, theme="dark-high-contrast")

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
dark_theme_natal_chart.save_svg(output_path=output_dir, filename="john-lennon-natal-dark-high-contrast")
```

![John Lennon](https://www.kerykeion.net/img/showcase/John%20Lennon%20-%20Dark%20-%20Natal%20Chart.svg)

## Alternative Initialization

Create an `AstrologicalSubjectModel` from a UTC ISO 8601 string:

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_iso_utc_time(
    name="Johnny Depp",
    iso_utc_time="1963-06-09T05:00:00Z",
    city="Owensboro",
    nation="US",
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
)

print(subject.iso_formatted_local_datetime)
```

If you prefer automatic geocoding, set `online=True` and provide your GeoNames credentials via `geonames_username`.

## Lunar Nodes (Rahu & Ketu)

Kerykeion supports both **True** and **Mean** Lunar Nodes:

-   **True North Lunar Node**: `"true_node"` (name kept without "north" for backward compatibility).
-   **True South Lunar Node**: `"true_south_node"`.
-   **Mean North Lunar Node**: `"mean_node"` (name kept without "north" for backward compatibility).
-   **Mean South Lunar Node**: `"mean_south_node"`.

In instances of the classes used to generate aspects and SVG charts, only the mean nodes are active. To activate the true nodes, you need to pass the `active_points` parameter to the `ChartDataFactory` methods.

Example:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

# Step 2: Pre-compute chart data with custom active points including true nodes
chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=[
        "Sun",
        "Moon",
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
        "Mean_Node",
        "Mean_South_Node",
        "True_Node",       # Activates True North Node
        "True_South_Node", # Activates True South Node
        "Ascendant",
        "Medium_Coeli",
        "Descendant",
        "Imum_Coeli"
    ]
)

# Step 3: Create visualization
chart = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=output_dir, filename="johnny-depp-custom-points")
```

## JSON Support

You can serialize the astrological subject (the base data used throughout the library) to JSON:

```python
from kerykeion import AstrologicalSubjectFactory

johnny = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
)

print(johnny.model_dump_json(indent=2))
```

## Auto Generated Documentation

You can find auto-generated documentation [here](https://www.kerykeion.net/pydocs/kerykeion.html). Most classes and functions include docstrings.

## Development

Clone the repository or download the ZIP via the GitHub interface.

## Kerykeion v5.0 – What's New

Kerykeion v5 is a **complete redesign** that modernizes the library with a data-first approach, factory-based architecture, and Pydantic 2 models. This version brings significant improvements in API design, type safety, and extensibility.

Looking to upgrade from v4? See the dedicated migration guide: [MIGRATION_V4_TO_V5.md](MIGRATION_V4_TO_V5.md).

### 🎯 Key Highlights

#### Factory-Centered Architecture

The old class-based approach has been replaced with a modern factory pattern:

-   **`AstrologicalSubjectFactory`**: Replaces the old `AstrologicalSubject` class
-   **`ChartDataFactory`**: Pre-computes enriched chart data (elements, qualities, aspects)
-   **`ChartDrawer`**: Pure SVG rendering separated from calculations
-   **`AspectsFactory`**: Unified aspects calculation for natal and synastry charts
-   **`PlanetaryReturnFactory`**: Solar and Lunar returns computation
-   **`HouseComparisonFactory`**: House overlay analysis for synastry
-   **`RelationshipScoreFactory`**: Compatibility scoring between charts

**Old v4 API:**

```python
from pathlib import Path
from kerykeion import AstrologicalSubject, KerykeionChartSVG

# v4 - Class-based approach
output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

subject = AstrologicalSubject(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
chart = KerykeionChartSVG(subject, new_output_directory=output_dir)
chart.makeSVG()
```

**New v5 API:**

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

# v5 - Factory-based approach with separation of concerns
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=output_dir, filename="john-factory-demo")
```

#### Pydantic 2 Models & Type Safety

All data structures are now strongly typed Pydantic models:

-   **`AstrologicalSubjectModel`**: Subject data with full validation
-   **`ChartDataModel`**: Enriched chart data with elements, qualities, aspects
-   **`AspectModel` list**: Raw aspect entries directly on `ChartDataModel.aspects`
-   **`PlanetReturnModel`**: Planetary return data
-   **`ElementDistributionModel`**: Element statistics (fire, earth, air, water)
-   **`QualityDistributionModel`**: Quality statistics (cardinal, fixed, mutable)

All models support:

-   JSON serialization/deserialization
-   Dictionary export
-   Subscript access
-   Full IDE autocomplete and type checking

#### Enhanced Features

-   **Speed & Declination**: All celestial points now include daily motion speed and declination
-   **Element & Quality Analysis**: Automatic calculation of element/quality distributions
-   **Relationship Scoring**: Built-in compatibility analysis for synastry
-   **House Comparison**: Detailed house overlay analysis
-   **Transit Time Ranges**: Advanced transit tracking over time periods
-   **Report Module**: Comprehensive text reports with ASCII tables
-   **Axis Orb Control**: Chart axes now share the same orb as planets by default; pass the keyword-only `axis_orb_limit` to return to a traditional, tighter axis filtering when you need it.
-   **Element Weight Strategies**: Element and quality stats now default to a curated weighted balance; pass `distribution_method` or `custom_distribution_weights` when you need equal counts or bespoke weightings (including a `__default__` fallback) across any chart factory helper.

<!-- Migration details moved to MIGRATION_V4_TO_V5.md -->

### 📦 Other Notable Changes

-   **Packaging**: Migrated from Poetry to PEP 621 + Hatchling with `uv.lock`
-   **Settings**: Centralized in `kerykeion.schemas` and `kerykeion.settings`
-   **Configuration**: Default chart presets consolidated in `kerykeion/settings/chart_defaults.py`
-   **Type System**: All literals consolidated in `kr_literals.py`
-   **Performance**: Caching improvements with `functools.lru_cache`
-   **Testing**: 376 tests with 87% coverage, regenerated fixtures for v5

### 🎨 New Themes

Additional chart themes added:

-   `classic` (default)
-   `dark`
-   `dark-high-contrast`
-   `light`
-   `strawberry`
-   `black-and-white`

### 📚 Resources

-   **Full Release Notes**: [v5.0.0.md](release_notes/v5.0.0b1.md)
-   **Migration Guide (v4 → v5)**: [MIGRATION_V4_TO_V5.md](MIGRATION_V4_TO_V5.md)
-   **Documentation**: [kerykeion.readthedocs.io](https://kerykeion.readthedocs.io)
-   **API Reference**: [kerykeion.net/pydocs](https://www.kerykeion.net/pydocs/kerykeion.html)
-   **Examples**: See the `examples/` folder for runnable code
-   **Support**: [GitHub Discussions](https://github.com/g-battaglia/kerykeion/discussions)
-   

## Integrating Kerykeion into Your Project

If you would like to incorporate Kerykeion's astrological features into your application, please reach out via [email](mailto:kerykeion.astrology@gmail.com?subject=Integration%20Request). Whether you need custom features, support, or specialized consulting, I am happy to discuss potential collaborations.

## License

This project is covered under the AGPL-3.0 License. For detailed information, please see the [LICENSE](LICENSE) file. If you have questions, feel free to contact me at [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com?subject=Kerykeion).

As a rule of thumb, if you use this library in a project, you should open-source that project under a compatible license. Alternatively, if you wish to keep your source closed, consider using the [AstrologerAPI](https://rapidapi.com/gbattaglia/api/astrologer/), which is AGPL-3.0 compliant and also helps support the project.

Since the AstrologerAPI is an external third-party service, using it does _not_ require your code to be open-source.

## Contributing

Contributions are welcome! Feel free to submit pull requests or report issues.

By submitting a contribution, you agree to assign the copyright of that contribution to the maintainer. The project stays openly available under the AGPL for everyone, while the re-licensing option helps sustain future development. Your authorship remains acknowledged in the commit history and release notes.

## Citations

If using Kerykeion in published or academic work, please cite as follows:

```
Battaglia, G. (2025). Kerykeion: A Python Library for Astrological Calculations and Chart Generation.
https://github.com/g-battaglia/kerykeion
```
