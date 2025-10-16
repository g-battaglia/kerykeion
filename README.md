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

![John Lenon Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Dark%20Theme%20-%20Natal%20Chart.svg)

## **Web API**

If you want to use Kerykeion in a web application, you can try the dedicated web API:

**[AstrologerAPI](https://rapidapi.com/gbattaglia/api/astrologer/pricing)**

It is [open source](https://github.com/g-battaglia/Astrologer-API) and directly supports this project.

## **Donate**

Maintaining this project requires substantial time and effort. The Astrologer API alone cannot cover the costs of full-time development. If you find Kerykeion valuable and would like to support further development, please consider donating:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kerykeion)

## ⚠️ Development Branch Notice

This branch (`next`) is **not the stable version** of Kerykeion. It is the **development branch for the upcoming V5 release**.

If you're looking for the latest stable version, please check out the [`master`](https://github.com/g-battaglia/kerykeion/tree/master) branch instead.

## Table of Contents

-   [**Web API**](#web-api)
-   [**Donate**](#donate)
-   [⚠️ Development Branch Notice](#️-development-branch-notice)
-   [Table of Contents](#table-of-contents)
-   [Installation](#installation)
-   [Basic Usage](#basic-usage)
-   [Generate a SVG Chart](#generate-a-svg-chart)
    -   [Birth Chart](#birth-chart)
    -   [External Birth Chart](#external-birth-chart)
    -   [Synastry Chart](#synastry-chart)
    -   [Transit Chart](#transit-chart)
    -   [Composite Chart](#composite-chart)
-   [Wheel Only Charts](#wheel-only-charts)
    -   [Birth Chart](#birth-chart-1)
    -   [Wheel Only Birth Chart (External)](#wheel-only-birth-chart-external)
    -   [Synastry Chart](#synastry-chart-1)
    -   [Change the Output Directory](#change-the-output-directory)
    -   [Change Language](#change-language)
    -   [Minified SVG](#minified-svg)
    -   [SVG without CSS Variables](#svg-without-css-variables)
    -   [Grid Only SVG](#grid-only-svg)
-   [Report Generator](#report-generator)
    -   [Quick Examples](#quick-examples)
    -   [Section Access](#section-access)
-   [Example: Retrieving Aspects](#example-retrieving-aspects)
-   [Ayanamsa (Sidereal Modes)](#ayanamsa-sidereal-modes)
-   [House Systems](#house-systems)
-   [Perspective Type](#perspective-type)
-   [Themes](#themes)
-   [Alternative Initialization](#alternative-initialization)
-   [Lunar Nodes (Rahu \& Ketu)](#lunar-nodes-rahu--ketu)
-   [JSON Support](#json-support)
-   [Auto Generated Documentation](#auto-generated-documentation)
-   [Development](#development)
-   [Kerykeion v5.0 – What's New](#kerykeion-v50--whats-new)
    -   [🎯 Key Highlights](#-key-highlights)
        -   [Factory-Centered Architecture](#factory-centered-architecture)
        -   [Pydantic 2 Models \& Type Safety](#pydantic-2-models--type-safety)
        -   [Enhanced Features](#enhanced-features)
    -   [🚨 Breaking Changes](#-breaking-changes)
        -   [1. Removed Legacy Classes](#1-removed-legacy-classes)
        -   [2. Import Changes](#2-import-changes)
        -   [3. Lunar Nodes Naming](#3-lunar-nodes-naming)
        -   [4. Chart Generation Changes](#4-chart-generation-changes)
        -   [5. Aspects API Changes](#5-aspects-api-changes)
    -   [🔄 Migration Guide](#-migration-guide)
        -   [Using the Backward Compatibility Layer](#using-the-backward-compatibility-layer)
        -   [Step-by-Step Migration](#step-by-step-migration)
        -   [Automated Migration Script](#automated-migration-script)
    -   [📦 Other Notable Changes](#-other-notable-changes)
    -   [🎨 New Themes](#-new-themes)
    -   [📚 Resources](#-resources)
-   [Integrating Kerykeion into Your Project](#integrating-kerykeion-into-your-project)
-   [License](#license)
-   [Contributing](#contributing)
-   [Citations](#citations)

## Installation

Kerykeion requires **Python 3.9** or higher.

```bash
pip3 install kerykeion
```

## Basic Usage

Below is a simple example illustrating the creation of an astrological subject and retrieving astrological details:

```python
from kerykeion import AstrologicalSubjectFactory

# Create an instance of the AstrologicalSubjectFactory class.
# Arguments: Name, year, month, day, hour, minutes, city, nation
john = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

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

To generate a chart, use the `ChartDataFactory` to pre-compute chart data, then `ChartDrawer` to create the visualization. This two-step process ensures clean separation between astrological calculations and chart rendering.

**Tip:**
The optimized way to open the generated SVG files is with a web browser (e.g., Chrome, Firefox).
To improve compatibility across different applications, you can use the `remove_css_variables` parameter when generating the SVG. This will inline all styles and eliminate CSS variables, resulting in an SVG that is more broadly supported.

### Birth Chart

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
john = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(john)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)
birth_chart_svg.save_svg()
```

The SVG file will be saved in the home directory.
![John Lennon Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Natal%20Chart.svg)

### External Birth Chart

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute chart data for external natal chart
chart_data = ChartDataFactory.create_external_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)
birth_chart_svg.save_svg()
```

![John Lennon External Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20ExternalNatal%20Chart.svg)

### Synastry Chart

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(first, second)

# Step 3: Create visualization
synastry_chart = ChartDrawer(chart_data=chart_data)
synastry_chart.save_svg()
```

![John Lennon and Paul McCartney Synastry](https://www.kerykeion.net/img/examples/synastry-chart.svg)

### Transit Chart

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
transit = AstrologicalSubjectFactory.from_birth_data("Transit", 2025, 6, 8, 8, 45, "Atlanta", "US")
subject = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute transit chart data
chart_data = ChartDataFactory.create_transit_chart_data(subject, transit)

# Step 3: Create visualization
transit_chart = ChartDrawer(chart_data=chart_data)
transit_chart.save_svg()
```

![John Lennon Transit Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Transit%20Chart.svg)

### Composite Chart

```python
from kerykeion import CompositeSubjectFactory, AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
angelina = AstrologicalSubjectFactory.from_birth_data("Angelina Jolie", 1975, 6, 4, 9, 9, "Los Angeles", "US", lng=-118.15, lat=34.03, tz_str="America/Los_Angeles")

brad = AstrologicalSubjectFactory.from_birth_data("Brad Pitt", 1963, 12, 18, 6, 31, "Shawnee", "US", lng=-96.56, lat=35.20, tz_str="America/Chicago")

# Step 2: Create composite subject
factory = CompositeSubjectFactory(angelina, brad)
composite_model = factory.get_midpoint_composite_subject_model()

# Step 3: Pre-compute composite chart data
chart_data = ChartDataFactory.create_composite_chart_data(composite_model)

# Step 4: Create visualization
composite_chart = ChartDrawer(chart_data=chart_data)
composite_chart.save_svg()
```

![Angelina Jolie and Brad Pitt Composite Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/Angelina%20Jolie%20and%20Brad%20Pitt%20Composite%20Chart%20-%20Composite%20Chart.svg)

## Wheel Only Charts

For _all_ the charts, you can generate a wheel-only chart by using the method `makeWheelOnlySVG()`:

### Birth Chart

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)
birth_chart_svg.save_wheel_only_svg_file()
```

![John Lennon Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Wheel%20Only%20-%20Natal%20Chart%20-%20Wheel%20Only.svg)

### Wheel Only Birth Chart (External)

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute external natal chart data
chart_data = ChartDataFactory.create_external_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)
birth_chart_svg.save_wheel_only_svg_file(
    wheel_only=True,
    wheel_only_external=True
)
```

![John Lennon Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Wheel%20External%20Only%20-%20ExternalNatal%20Chart%20-%20Wheel%20Only.svg)

### Synastry Chart

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(first, second)

# Step 3: Create visualization
synastry_chart = ChartDrawer(chart_data=chart_data)
synastry_chart.save_wheel_only_svg_file()
```

![John Lennon and Paul McCartney Synastry](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Wheel%20Synastry%20Only%20-%20Synastry%20Chart%20-%20Wheel%20Only.svg)

### Change the Output Directory

To save the SVG file in a custom location, specify the `output_path` parameter in `save_svg()`:

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(first, second)

# Step 3: Create visualization with custom output directory
synastry_chart = ChartDrawer(chart_data=chart_data)
synastry_chart.save_svg(output_path=".")
```

### Change Language

You can switch chart language by passing `chart_language` to the `ChartDrawer` class:

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization with Italian language
birth_chart_svg = ChartDrawer(
    chart_data=chart_data,
    chart_language="IT"  # Change to Italian
)
birth_chart_svg.save_svg()
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
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)
birth_chart_svg.save_svg(
    minify=True
)
```

### SVG without CSS Variables

To generate an SVG without CSS variables, set `remove_css_variables=True` in the `makeSVG()` method:

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
birth_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(birth_chart)

# Step 3: Create visualization
birth_chart_svg = ChartDrawer(chart_data=chart_data)
birth_chart_svg.save_svg(
    remove_css_variables=True
)
```

This will inline all styles and eliminate CSS variables, resulting in an SVG that is more broadly supported.

### Grid Only SVG

It's possible to generate a grid-only SVG, useful for creating a custom layout. To do this, use the `save_aspect_grid_only_svg_file()` method:

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subjects
birth_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(birth_chart, second)

# Step 3: Create visualization with dark theme
aspect_grid_chart = ChartDrawer(chart_data=chart_data, theme="dark")
aspect_grid_chart.save_aspect_grid_only_svg_file()
```

![John Lennon Birth Chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/master/tests/charts/svg/John%20Lennon%20-%20Aspect%20Grid%20Only%20-%20Natal%20Chart%20-%20Aspect%20Grid%20Only.svg)

## Report Generator

`ReportGenerator` mirrors the chart-type dispatch of `ChartDrawer`. It accepts raw `AstrologicalSubjectModel` instances as well as any `ChartDataModel` produced by `ChartDataFactory`—including natal, composite, synastry, transit, and planetary return charts—and renders the appropriate textual report automatically.

### Quick Examples

```python
from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

# Subject-only report
subject = AstrologicalSubjectFactory.from_birth_data(
    "Sample Natal", 1990, 7, 21, 14, 45, "Rome", "IT"
)
ReportGenerator(subject).print_report(include_aspects=False)

# Single-chart data (elements, qualities, aspects enabled)
natal_data = ChartDataFactory.create_natal_chart_data(subject)
ReportGenerator(natal_data).print_report(max_aspects=10)

# Dual-chart data (synastry, transit, dual return, …)
partner = AstrologicalSubjectFactory.from_birth_data(
    "Sample Partner", 1992, 11, 5, 9, 30, "Rome", "IT"
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
report = ReportGenerator(natal_data)
print(report.get_subject_data_report())
print(report.get_celestial_points_report())
print(report.get_elements_report())
print(report.get_aspects_report(max_aspects=5))
```

Refer to the refreshed [Report Documentation](https://www.kerykeion.net/report/) for end-to-end examples covering every supported chart model.

## Example: Retrieving Aspects

Kerykeion provides a unified `AspectsFactory` class for calculating astrological aspects within single charts or between two charts:

```python
from kerykeion import AspectsFactory, AstrologicalSubjectFactory

# Create astrological subjects
jack = AstrologicalSubjectFactory.from_birth_data("Jack", 1990, 6, 15, 15, 15, "Roma", "IT")
jane = AstrologicalSubjectFactory.from_birth_data("Jane", 1991, 10, 25, 21, 0, "Roma", "IT")

# For single chart aspects (natal, return, composite, etc.)
single_chart_aspects = AspectsFactory.single_chart_aspects(jack)
print(f"Found {len(single_chart_aspects)} aspects in Jack's chart")
print(single_chart_aspects[0])
# Output: AspectModel with details like aspect type, orb, planets involved, etc.

# For dual chart aspects (synastry, transits, comparisons, etc.)
dual_chart_aspects = AspectsFactory.dual_chart_aspects(jack, jane)
print(f"Found {len(dual_chart_aspects)} aspects between Jack and Jane's charts")
print(dual_chart_aspects[0])
# Output: AspectModel with cross-chart aspect details

# The factory returns structured AspectModel objects with properties like:
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

## Ayanamsa (Sidereal Modes)

By default, the zodiac type is **Tropical**. To use **Sidereal**, specify the sidereal mode:

```python
johnny = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    "Owensboro", "US",
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
    "Owensboro", "US",
    houses_system="M"
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
    "Owensboro", "US",
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

Each theme offers a distinct visual style, allowing you to choose the one that best suits your preferences or presentation needs. If you prefer more control over the appearance, you can opt not to set any theme, making it easier to customize the chart by overriding the default CSS variables. For more detailed instructions on how to apply themes, check the [documentation](https://www.kerykeion.net/docs/theming)

Here's an example of how to set the theme:

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
dark_theme_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")

# Step 2: Pre-compute chart data
chart_data = ChartDataFactory.create_natal_chart_data(dark_theme_subject)

# Step 3: Create visualization with dark high contrast theme
dark_theme_natal_chart = ChartDrawer(chart_data=chart_data, theme="dark_high_contrast")
dark_theme_natal_chart.save_svg()
```

![John Lennon](https://www.kerykeion.net/img/showcase/John%20Lennon%20-%20Dark%20-%20Natal%20Chart.svg)

## Alternative Initialization

Create an `AstrologicalSubject` from a UTC ISO 8601 string:

```python
subject = AstrologicalSubject.get_from_iso_utc_time(
    "Johnny Depp", "1963-06-09T05:00:00Z", "Owensboro", "US"
)
```

If you set `online=True`, provide a `geonames_username` to allow city-based geolocation:

```python
from kerykeion.astrological_subject import AstrologicalSubjectFactory

subject = AstrologicalSubject.get_from_iso_utc_time(
    "Johnny Depp", "1963-06-09T05:00:00Z", "Owensboro", "US", online=True
)
```

## Lunar Nodes (Rahu & Ketu)

Kerykeion supports both **True** and **Mean** Lunar Nodes:

-   **True North Lunar Node**: `"true_node"` (name kept without "north" for backward compatibility).
-   **True South Lunar Node**: `"true_south_node"`.
-   **Mean North Lunar Node**: `"mean_node"` (name kept without "north" for backward compatibility).
-   **Mean South Lunar Node**: `"mean_south_node"`.

In instances of the classes used to generate aspects and SVG charts, only the mean nodes are active. To activate the true nodes, you need to pass the `active_points` parameter to the `ChartDataFactory` methods.

Example:

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create subject
subject = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

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
chart.save_svg()
```

## JSON Support

You can serialize the astrological subject (the base data used throughout the library) to JSON:

```python
from kerykeion import AstrologicalSubjectFactory

johnny = AstrologicalSubjectFactory.from_birth_data("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US")

print(johnny.json(dump=False, indent=2))
```

## Auto Generated Documentation

You can find auto-generated documentation [here](https://www.kerykeion.net/pydocs/kerykeion.html). Most classes and functions include docstrings.

## Development

Clone the repository or download the ZIP via the GitHub interface.

## Kerykeion v5.0 – What's New

Kerykeion v5 is a **complete redesign** that modernizes the library with a data-first approach, factory-based architecture, and Pydantic 2 models. This version brings significant improvements in API design, type safety, and extensibility.

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
from kerykeion import AstrologicalSubject, KerykeionChartSVG

# v4 - Class-based approach
subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "London", "GB")
chart = KerykeionChartSVG(subject)
chart.makeSVG()
```

**New v5 API:**

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

# v5 - Factory-based approach with separation of concerns
subject = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)
drawer.save_svg()
```

#### Pydantic 2 Models & Type Safety

All data structures are now strongly typed Pydantic models:

-   **`AstrologicalSubjectModel`**: Subject data with full validation
-   **`ChartDataModel`**: Enriched chart data with elements, qualities, aspects
-   **`SingleChartAspectsModel` / `DualChartAspectsModel`**: Typed aspect collections
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

### 🚨 Breaking Changes

#### 1. Removed Legacy Classes

The following classes have been **completely removed** and must be replaced:

| Removed (v4)           | Replacement (v5)                               |
| ---------------------- | ---------------------------------------------- |
| `AstrologicalSubject`  | `AstrologicalSubjectFactory.from_birth_data()` |
| `KerykeionChartSVG`    | `ChartDrawer` + `ChartDataFactory`             |
| `NatalAspects`         | `AspectsFactory.single_chart_aspects()`        |
| `SynastryAspects`      | `AspectsFactory.dual_chart_aspects()`          |
| `relationship_score()` | `RelationshipScoreFactory`                     |

**Note**: The `kerykeion.backword` module provides temporary wrappers for `AstrologicalSubject` and `KerykeionChartSVG` with deprecation warnings. These will be **removed in v6.0**.

#### 2. Import Changes

Module structure has been completely reorganized:

**Old imports (v4):**

```python
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from kerykeion.kr_types import KerykeionException
```

**New imports (v5):**

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.schemas.kerykeion_exception import KerykeionException
```

#### 3. Lunar Nodes Naming

All lunar node fields have been renamed for clarity:

| Old Name (v4)     | New Name (v5)           |
| ----------------- | ----------------------- |
| `Mean_Node`       | `Mean_North_Lunar_Node` |
| `True_Node`       | `True_North_Lunar_Node` |
| `Mean_South_Node` | `Mean_South_Lunar_Node` |
| `True_South_Node` | `True_South_Lunar_Node` |

**Migration example:**

```python
# v4
print(subject.mean_node)

# v5
print(subject.mean_north_lunar_node)
```

#### 4. Axis Orb Filtering

Modern default orbs now treat chart axes (ASC, MC, DSC, IC) exactly like planets. If you prefer a traditional, constrained approach, every public aspect factory exposes the keyword-only `axis_orb_limit` parameter so you can set a dedicated threshold when needed.

#### 5. Chart Generation Changes

The two-step process (data + rendering) is now required:

**Old v4:**

```python
chart = KerykeionChartSVG(subject)
chart.makeSVG()
```

**New v5:**

```python
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)
drawer.save_svg()
```

#### 5. Aspects API Changes

Aspects are now calculated through the factory:

**Old v4:**

```python
from kerykeion import NatalAspects, SynastryAspects

natal_aspects = NatalAspects(subject)
synastry_aspects = SynastryAspects(subject1, subject2)
```

**New v5:**

```python
from kerykeion import AspectsFactory

natal_aspects = AspectsFactory.single_chart_aspects(subject)
synastry_aspects = AspectsFactory.dual_chart_aspects(subject1, subject2)
```

### 🔄 Migration Guide

#### Using the Backward Compatibility Layer

For a gradual migration, use the `kerykeion.backword` module:

```python
from kerykeion import AstrologicalSubject  # Legacy wrapper

subject = AstrologicalSubject("John Doe", 1990, 1, 1, 12, 0, "London", "GB")

# These still work but show DeprecationWarnings
print(subject.mean_node)  # Maps to mean_north_lunar_node
print(subject.true_node)  # Maps to true_north_lunar_node
```

**⚠️ Warning**: This compatibility layer will be **removed in v6.0**.

#### Step-by-Step Migration

1. **Update imports**

    ```python
    # Old
    from kerykeion import AstrologicalSubject, KerykeionChartSVG

    # New
    from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
    ```

2. **Update subject creation**

    ```python
    # Old
    subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "London", "GB")

    # New
    subject = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
    ```

3. **Update chart generation**

    ```python
    # Old
    chart = KerykeionChartSVG(subject)
    chart.makeSVG()

    # New
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    drawer = ChartDrawer(chart_data=chart_data)
    drawer.save_svg()
    ```

4. **Update field access** (lunar nodes)

    ```python
    # Old
    print(subject.mean_node.position)

    # New
    print(subject.mean_north_lunar_node.position)
    ```

5. **Update aspects**

    ```python
    # Old
    from kerykeion import NatalAspects
    aspects = NatalAspects(subject)

    # New
    from kerykeion import AspectsFactory
    aspects = AspectsFactory.single_chart_aspects(subject)
    ```

#### Automated Migration Script

Use this sed script to update Python files automatically:

```bash
# Update lunar node references
find . -name "*.py" -type f -exec sed -i.bak \
    -e 's/\.mean_node/.mean_north_lunar_node/g' \
    -e 's/\.true_node/.true_north_lunar_node/g' \
    -e 's/\.mean_south_node/.mean_south_lunar_node/g' \
    -e 's/\.true_south_node/.true_south_lunar_node/g' \
    -e 's/"Mean_Node"/"Mean_North_Lunar_Node"/g' \
    -e 's/"True_Node"/"True_North_Lunar_Node"/g' \
    -e 's/"Mean_South_Node"/"Mean_South_Lunar_Node"/g' \
    -e 's/"True_South_Node"/"True_South_Lunar_Node"/g' \
    {} \;
```

**Note**: Always review automated changes and test thoroughly before committing.

### 📦 Other Notable Changes

-   **Packaging**: Migrated from Poetry to PEP 621 + Hatchling with `uv.lock`
-   **Settings**: Centralized in `kerykeion.schemas` and `kerykeion.settings`
-   **Configuration**: Legacy presets available in `settings/legacy/`
-   **Type System**: All literals consolidated in `kr_literals.py`
-   **Performance**: Caching improvements with `functools.lru_cache`
-   **Testing**: 376 tests with 87% coverage, regenerated fixtures for v5

### 🎨 New Themes

Additional chart themes added:

-   `classic` (default)
-   `dark`
-   `dark_high_contrast`
-   `light`
-   `strawberry`

### 📚 Resources

-   **Full Release Notes**: [v5.0.0.md](release_notes/v5.0.0b1.md)
-   **Documentation**: [kerykeion.readthedocs.io](https://kerykeion.readthedocs.io)
-   **API Reference**: [kerykeion.net/pydocs](https://www.kerykeion.net/pydocs/kerykeion.html)
-   **Examples**: See the `examples/` folder for runnable code
-   **Support**: [GitHub Discussions](https://github.com/g-battaglia/kerykeion/discussions)

**Migration Timeline:**

-   **v5.0**: Current - Backward compatibility layer available
-   **v6.0**: Future - Compatibility layer will be removed

## Integrating Kerykeion into Your Project

If you would like to incorporate Kerykeion's astrological features into your application, please reach out via [email](mailto:kerykeion.astrology@gmail.com?subject=Integration%20Request). Whether you need custom features, support, or specialized consulting, I am happy to discuss potential collaborations.

## License

This project is covered under the AGPL-3.0 License. For detailed information, please see the [LICENSE](LICENSE) file. If you have questions, feel free to contact me at [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com?subject=Kerykeion).

As a rule of thumb, if you use this library in a project, you should open-source that project under a compatible license. Alternatively, if you wish to keep your source closed, consider using the [AstrologerAPI](https://rapidapi.com/gbattaglia/api/astrologer/), which is AGPL-3.0 compliant and also helps support the project.

Since the AstrologerAPI is an external third-party service, using it does _not_ require your code to be open-source.

## Contributing

Contributions are welcome! Feel free to submit pull requests or report issues.

## Citations

If using Kerykeion in published or academic work, please cite as follows:

```
Battaglia, G. (2025). Kerykeion: A Python Library for Astrological Calculations and Chart Generation.
https://github.com/g-battaglia/kerykeion
```
