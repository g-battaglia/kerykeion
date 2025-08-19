# Charts Module - ChartDrawer

## Overview

The `ChartDrawer` class is the pure visualization engine of Kerykeion, responsible for generating professional-quality SVG astrological charts from pre-computed chart data. This class focuses exclusively on rendering and does not perform any astronomical calculations - it requires chart data to be prepared beforehand using `ChartDataFactory`.

This clean separation ensures that `ChartDataFactory` handles all calculations (planetary positions, aspects, element/quality distributions) while `ChartDrawer` focuses solely on creating beautiful, customizable visual representations. The module supports the complete spectrum of astrological chart types used in both Western and Vedic traditions, with extensive customization options for themes, languages, and visual settings.

The SVG output ensures scalable, high-quality graphics that maintain clarity at any size while remaining lightweight for web applications.

## Core Features

- **Chart Types**: Natal, ExternalNatal, Transit, Synastry, Composite
- **Pre-computed Data**: Requires `ChartDataModel` from `ChartDataFactory`
- **Output Methods**: Full chart, wheel-only, aspect grid-only
- **Themes**: classic, dark, light, strawberry, dark-high-contrast
- **Languages**: EN, IT, FR, ES, PT, CN, RU, TR, DE, HI
- **Customization**: Themes, languages, transparency, minification
- **Output Formats**: Standard SVG, minified SVG, template strings

## Basic Usage

Chart creation with `ChartDrawer` follows a two-step process: first generate chart data using `ChartDataFactory`, then create visualizations with `ChartDrawer`. This separation ensures clean architecture and efficient data processing.

### Simple Natal Chart

A natal chart represents the sky at the moment of birth, showing planetary positions, house divisions, and aspects. Here's how to create one with the new architecture:

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Create an astrological subject with birth data
subject = AstrologicalSubjectFactory.from_birth_data(
    name="John", 
    year=1990, month=7, day=15, 
    hour=10, minute=30, 
    city="Rome", country="IT"
)

# Step 2: Pre-compute chart data (this does all the calculations)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Step 3: Create visualization (this only renders the SVG)
chart_drawer = ChartDrawer(chart_data=chart_data)

# METHOD 1: Generate and save SVG file to disk
chart_drawer.makeSVG()  # Saves file to default location

# METHOD 2: Get SVG content as string (recommended for web apps)
svg_content = chart_drawer.makeTemplate()  # Returns SVG as string

# If you want to save the string content manually:
with open("natal_chart.svg", "w") as f:
    f.write(svg_content)
```

### Synastry Chart

Synastry charts are used for relationship analysis, comparing two people's birth charts to understand compatibility and interaction patterns. The chart displays both individuals' planetary positions simultaneously, with aspects drawn between them.

```python
# Step 1: Create two subjects for relationship compatibility analysis
subject1 = AstrologicalSubjectFactory.from_birth_data(
    "Person1", 1990, 7, 15, 10, 30, "Rome", "IT"
)
subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Person2", 1985, 3, 20, 14, 15, "London", "GB"
)

# Step 2: Pre-compute synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(
    first_subject=subject1,   # Person1's planets in inner circle
    second_subject=subject2   # Person2's planets in outer circle
)

# Step 3: Create visualization
chart_drawer = ChartDrawer(chart_data=chart_data)

# Get SVG content as string (recommended)
svg_content = chart_drawer.makeTemplate()

# OR save directly to file
chart_drawer.makeSVG()  # Saves to default location
```

### Composite Chart

Composite charts represent the mathematical midpoint between two people's planetary positions, creating a theoretical "relationship chart" that describes the combined energy and purpose of a partnership.

```python
# Step 1: Create subjects
subject1 = AstrologicalSubjectFactory.from_birth_data(
    "Person1", 1990, 7, 15, 10, 30, "Rome", "IT"
)
subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Person2", 1985, 3, 20, 14, 15, "London", "GB"
)

# Step 2: Pre-compute composite chart data (calculates midpoints)
chart_data = ChartDataFactory.create_composite_chart_data(
    first_subject=subject1,
    second_subject=subject2
)

# Step 3: Create visualization
chart_drawer = ChartDrawer(chart_data=chart_data)

# Get the relationship chart as string
svg_content = chart_drawer.makeTemplate()
```

### Transit Chart

Transit charts show how current planetary movements affect an individual's natal chart. This is essential for timing analysis and understanding current astrological influences.

```python
# Step 1: Create subjects
natal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT"
)

# Create a transit subject for current planetary positions
transit_subject = AstrologicalSubjectFactory.from_birth_data(
    "Transit", 2024, 1, 15, 12, 0, "Rome", "IT"
)

# Step 2: Pre-compute transit chart data
chart_data = ChartDataFactory.create_transit_chart_data(
    first_subject=natal_subject,     # Natal chart (inner wheel)
    second_subject=transit_subject   # Current planetary positions (outer wheel)
)

# Step 3: Create visualization
chart_drawer = ChartDrawer(chart_data=chart_data)

# Get the transit chart content
svg_content = chart_drawer.makeTemplate()
```

## Output Methods

⚠️ **IMPORTANT DISTINCTION**: 
- `makeSVG()` methods **save files** to the location specified in the constructor
- `makeTemplate()` methods **return string content** without saving files

The ChartDrawer class offers two categories of output methods: file generation and template string generation.

### Full Chart with Aspects

```python
# Step 1: Create chart data
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Step 2: Create chart drawer
chart_drawer = ChartDrawer(chart_data=chart_data)

# makeSVG() SAVES the complete chart file to disk
# Does NOT return content - saves to default output directory
chart_drawer.makeSVG()  # File saved, no return value

# makeTemplate() RETURNS the complete chart as string
# Does NOT save file - returns SVG content for further processing
svg_string = chart_drawer.makeTemplate()  # Returns SVG content as string
```

### Wheel Only

```python
chart_drawer = ChartDrawer(chart_data=chart_data)

# makeWheelOnlySVG() SAVES wheel-only file to disk
chart_drawer.makeWheelOnlySVG()  # File saved, no return value

# makeWheelOnlyTemplate() RETURNS wheel-only content as string
wheel_string = chart_drawer.makeWheelOnlyTemplate()  # Returns SVG string
```

### Aspect Grid Only

```python
chart_drawer = ChartDrawer(chart_data=chart_data)

# makeAspectGridOnlySVG() SAVES aspect grid file to disk
chart_drawer.makeAspectGridOnlySVG()  # File saved, no return value

# makeAspectGridOnlyTemplate() RETURNS aspect grid as string
aspects_string = chart_drawer.makeAspectGridOnlyTemplate()  # Returns SVG string
```

## Themes

Visual presentation is crucial for astrological charts, and ChartDrawer offers carefully designed themes to suit different contexts, from traditional printed materials to modern digital interfaces.

### Available Themes

```python
# Classic theme (default) - traditional colors and styling
# White background, black text, traditional planet colors
# Best for: Printed materials, traditional presentations, educational content
chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(chart_data=chart_data, theme="classic")

# Dark theme - modern dark interface
# Dark background, light text, optimized for night viewing
# Best for: Digital applications, reduced eye strain, modern aesthetics
chart_drawer = ChartDrawer(chart_data=chart_data, theme="dark")

# Light theme - clean minimalist appearance
# Light background, subtle colors, modern aesthetic
# Best for: Clean presentations, web applications, minimalist design
chart_drawer = ChartDrawer(chart_data=chart_data, theme="light")

# Strawberry theme - elegant pink and red tones
# Beautiful color palette with warm, inviting aesthetics
# Best for: Modern presentations, romantic contexts, unique visual appeal
chart_drawer = ChartDrawer(chart_data=chart_data, theme="strawberry")

# High contrast dark - accessibility focused
# Maximum contrast for visual impairments, dark background
# Best for: Accessibility compliance, visually impaired users, high contrast needs
chart_drawer = ChartDrawer(chart_data=chart_data, theme="dark-high-contrast")
```

## Language Support

Kerykeion provides comprehensive internationalization support, making charts accessible to astrologers and users worldwide. Each language includes localized planet names, zodiac signs, house labels, and aspect terminology.

```python
# Italian - all text labels, planet names, and signs in Italian
# Includes traditional Italian astrological terminology
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="IT")

# English (default) - standard international astrological terms
# Uses conventional Western astrological terminology
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="EN")

# French - labels and terms translated to French
# Follows French astrological tradition and terminology
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="FR")

# Spanish - full Spanish localization of chart text
# Suitable for both European and Latin American contexts
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="ES")

# Portuguese - Brazilian/Portuguese language support
# Appropriate for both European and Brazilian Portuguese
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="PT")

# Chinese - planet names and signs in Chinese characters
# Traditional Chinese astrological terminology
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="CN")

# Russian - Cyrillic text for all chart labels
# Complete Russian localization for Cyrillic readers
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="RU")

# Turkish - Turkish language localization
# Modern Turkish astrological terminology
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="TR")

# German - German astrological terminology
# Traditional German astrological terms and conventions
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="DE")

# Hindi - Devanagari script for Indian astrology contexts
# Supports Vedic astrology terminology in Hindi
chart_drawer = ChartDrawer(chart_data=chart_data, chart_language="HI")
```

## Zodiac Systems

Zodiac system configuration is handled by `ChartDataFactory` during chart data creation, not by `ChartDrawer`. The choice between tropical and sidereal affects all planetary positions and interpretations before visualization.

### Tropical Zodiac (Default)

The tropical zodiac is based on the seasons and is standard in Western astrology. It uses the vernal equinox as 0° Aries.

```python
from kerykeion.settings import KerykeionSettingsModel

# Tropical zodiac (default) - seasonal based, used in Western astrology
# 0° Aries = vernal equinox, signs aligned with seasons
settings = KerykeionSettingsModel(
    zodiac_type="Tropical"  # Default setting, can be omitted
)

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT",
    ks=settings
)

# Chart data will use tropical positions
chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(chart_data=chart_data)
```

### Sidereal Zodiac

The sidereal zodiac is based on the actual position of constellations and is primarily used in Vedic (Indian) astrology. Different ayanamsas (correction factors) account for the precession of equinoxes.

```python
# Lahiri Ayanamsa - most popular in Indian astrology
# Official ayanamsa of the Government of India
settings = KerykeionSettingsModel(
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI"  # Government of India standard
)

# Raman Ayanamsa - traditional Indian calculation
# Based on B.V. Raman's calculations
settings = KerykeionSettingsModel(
    zodiac_type="Sidereal",
    sidereal_mode="RAMAN"  # Traditional Raman method
)

# Krishnamurti Ayanamsa - used in KP system
# Specific to Krishnamurti Paddhati astrology
settings = KerykeionSettingsModel(
    zodiac_type="Sidereal",
    sidereal_mode="KRISHNAMURTI"  # KP system standard
)

# Apply sidereal settings to subject
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT",
    ks=settings  # Sidereal positions typically ~24° different from tropical
)

# Chart data will show sidereal positions (star-based)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(chart_data=chart_data)
svg_content = chart_drawer.makeTemplate()  # Get as string, don't save file
```

### Comparison Example

```python
# Generate both tropical and sidereal charts for comparison
tropical_settings = KerykeionSettingsModel(zodiac_type="Tropical")
sidereal_settings = KerykeionSettingsModel(
    zodiac_type="Sidereal", 
    sidereal_mode="LAHIRI"
)

# Same birth data, different zodiac systems
tropical_subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT", 
    ks=tropical_settings
)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT", 
    ks=sidereal_settings
)

# Generate chart data for comparison
tropical_chart_data = ChartDataFactory.create_natal_chart_data(tropical_subject)
sidereal_chart_data = ChartDataFactory.create_natal_chart_data(sidereal_subject)

# Create visualizations
tropical_chart_drawer = ChartDrawer(chart_data=tropical_chart_data)
sidereal_chart_drawer = ChartDrawer(chart_data=sidereal_chart_data)

tropical_svg = tropical_chart_drawer.makeTemplate()  # Get string content
sidereal_svg = sidereal_chart_drawer.makeTemplate()  # Get string content
```

## Custom Points and Aspects

Active points and aspects configuration is handled by `ChartDataFactory` during chart data creation. This allows for focused analysis and cleaner presentations by controlling which celestial bodies and aspects appear on charts.

### Active Points Configuration

```python
# Limit chart to specific celestial bodies for cleaner display
# Useful for focusing on personal planets or specific analysis

# Personal planets only - for personality analysis
personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]

# Classical planets - traditional astrology (pre-Uranus discovery)
classical_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]

# Modern planets - full contemporary set
modern_planets = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",    # Personal planets
    "Jupiter", "Saturn",                          # Social planets
    "Uranus", "Neptune", "Pluto"                  # Outer/generational planets
]

# Asteroids and additional points
extended_points = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "Chiron", "Node", "Lilith"
]

# Create chart data with custom active points
chart_data = ChartDataFactory.create_natal_chart_data(
    subject, 
    active_points=personal_planets  # Only these planets will appear on chart
)

chart_drawer = ChartDrawer(chart_data=chart_data)
```

### Active Aspects Configuration

```python
# Control which aspect types are displayed for cleaner charts

# Major aspects only - traditional five aspects
major_aspects = [
    "conjunction",  # 0° - planets in same position, unified energy
    "opposition",   # 180° - planets opposite, tension and awareness
    "trine",        # 120° - harmonious flow, natural talents
    "square",       # 90° - dynamic tension, challenges and growth
    "sextile"       # 60° - opportunities, cooperative energy
]

# Minor aspects - additional subtle influences
minor_aspects = [
    "semisextile",    # 30° - subtle adjustment
    "semisquare",     # 45° - minor friction
    "quintile",       # 72° - creative expression
    "sesquisquare",   # 135° - persistent irritation
    "quincunx"        # 150° - adjustment and adaptation
]

# Combine for comprehensive analysis
all_aspects = major_aspects + minor_aspects

# Create chart data with custom active aspects
chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_aspects=major_aspects  # List of strings: aspect type names
)

chart_drawer = ChartDrawer(chart_data=chart_data)
```

### Combined Configuration Example

```python
# Create a focused chart for relationship counseling
relationship_points = ["Sun", "Moon", "Venus", "Mars", "Jupiter"]
relationship_aspects = ["conjunction", "opposition", "trine", "square"]  # List of aspect type strings

# Create subjects
subject1 = AstrologicalSubjectFactory.from_birth_data(
    "Person1", 1990, 7, 15, 10, 30, "Rome", "IT"
)
subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Person2", 1985, 3, 20, 14, 15, "London", "GB"
)

# Create synastry chart data with custom points and aspects
synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
    first_subject=subject1,
    second_subject=subject2,
    active_points=relationship_points,
    active_aspects=relationship_aspects  # Pass list of aspect type names as strings
)

# Create visualization with theme and language
synastry_chart_drawer = ChartDrawer(
    chart_data=synastry_chart_data,
    theme="light",
    chart_language="EN"
)
```

## Advanced Customization

### Complete Configuration Example

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.settings import KerykeionSettingsModel

# Advanced settings
settings = KerykeionSettingsModel(
    house_system="W",  # Whole Signs
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    perspective_type="Traditional"
)

# Create subjects with custom settings
subject1 = AstrologicalSubjectFactory.from_birth_data(
    "Person1", 1990, 7, 15, 10, 30, "Rome", "IT", 
    ks=settings
)
subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Person2", 1985, 3, 20, 14, 15, "London", "GB", 
    ks=settings
)

# Custom points and aspects
active_points = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
active_aspects = ["conjunction", "opposition", "trine", "square"]  # List of aspect type strings

# Create synastry chart data
chart_data = ChartDataFactory.create_synastry_chart_data(
    first_subject=subject1,
    second_subject=subject2,
    active_points=active_points,
    active_aspects=active_aspects  # Pass aspect type names as strings
)

# Create chart drawer with visual settings
chart_drawer = ChartDrawer(
    chart_data=chart_data,
    theme="dark",
    chart_language="IT",
    transparent_background=True
)

# Generate different outputs
full_chart = chart_drawer.makeTemplate(minify=True)  # String content, minified
wheel_only = chart_drawer.makeWheelOnlyTemplate()   # String content, wheel only
aspects_only = chart_drawer.makeAspectGridOnlyTemplate()  # String content, aspects only

# Or save directly to files
chart_drawer.makeSVG(minify=True)              # Save full chart
chart_drawer.makeWheelOnlySVG()                # Save wheel only
chart_drawer.makeAspectGridOnlySVG()           # Save aspects only
```

## House Systems

House system configuration is handled by `ChartDataFactory` during subject creation, not by `ChartDrawer`. House systems determine how the ecliptic is divided into twelve segments, each representing different life areas. The choice of house system can significantly affect chart interpretation, especially for planets near house cusps.

### Popular House Systems

```python
# Placidus (default) - most common in Western astrology
# Time-based system creating unequal houses, excellent for psychological analysis
# Houses vary in size based on geographic latitude
settings = KerykeionSettingsModel(house_system="P")

# Whole Signs - each sign = one house (30° each)
# Ancient system, simple and clear, popular in Hellenistic astrology
# Each zodiac sign occupies exactly one house
settings = KerykeionSettingsModel(house_system="W")

# Equal House - 30° houses starting from Ascendant
# Keeps Ascendant as 1st house cusp, creates equal 30° divisions
# Good compromise between simplicity and Ascendant importance
settings = KerykeionSettingsModel(house_system="E")

# Koch - similar to Placidus but different calculation
# Time-based system popular in some European traditions
# Creates unequal houses with different mathematical approach
settings = KerykeionSettingsModel(house_system="K")

# Campanus - space-based system
# Divides the prime vertical into equal parts
# Popular in medieval astrology, creates unique house shapes
settings = KerykeionSettingsModel(house_system="C")

# Regiomontanus - another space-based system
# Divides the celestial equator into equal parts
# Renaissance-era system, still used by some modern astrologers
settings = KerykeionSettingsModel(house_system="R")
```

### House System Comparison

```python
# Compare different house systems for the same birth data
birth_data = ("John", 1990, 7, 15, 10, 30, "Rome", "IT")

house_systems = {
    "Placidus": "P",
    "Whole Signs": "W", 
    "Equal House": "E",
    "Koch": "K",
    "Campanus": "C",
    "Regiomontanus": "R"
}

charts = {}
for name, system in house_systems.items():
    settings = KerykeionSettingsModel(house_system=system)
    subject = AstrologicalSubjectFactory.from_birth_data(*birth_data, ks=settings)
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    chart_drawer = ChartDrawer(chart_data=chart_data)
    charts[name] = chart_drawer.makeTemplate()  # Get as string
    
    # Save string content to file
    with open(f"house_comparison_{name.lower().replace(' ', '_')}.svg", "w") as f:
        f.write(charts[name])
```

### Geographic Considerations

```python
# House systems affect different latitudes differently
# Extreme latitudes show more dramatic differences

# High latitude location (Norway)
high_lat_settings = KerykeionSettingsModel(house_system="P")
high_lat_subject = AstrologicalSubjectFactory.from_birth_data(
    "Arctic", 1990, 7, 15, 12, 0, "Tromsø", "NO", 
    ks=high_lat_settings
)

# Equatorial location
equatorial_settings = KerykeionSettingsModel(house_system="P")
equatorial_subject = AstrologicalSubjectFactory.from_birth_data(
    "Equator", 1990, 7, 15, 12, 0, "Quito", "EC", 
    ks=equatorial_settings
)

# Generate chart data to see latitude effects
high_lat_chart_data = ChartDataFactory.create_natal_chart_data(high_lat_subject)
equatorial_chart_data = ChartDataFactory.create_natal_chart_data(equatorial_subject)

# Create visualizations
high_lat_chart_drawer = ChartDrawer(chart_data=high_lat_chart_data)
equatorial_chart_drawer = ChartDrawer(chart_data=equatorial_chart_data)
```

## Chart Perspectives

Chart perspectives are handled by `ChartDataFactory` during subject creation and control the overall approach to chart calculation and presentation, affecting how data is processed before visualization.

### Perspective Configuration

```python
# Traditional perspective (default) - comprehensive astrological approach
# Includes all standard astrological elements and calculations
# Best for: Complete analysis, traditional astrology, educational purposes
settings = KerykeionSettingsModel(perspective_type="Traditional")

# Minified perspective - streamlined approach with essential elements
# Focuses on core planets and aspects, reduces complexity
# Best for: Quick analysis, simplified presentations, beginner-friendly charts
settings = KerykeionSettingsModel(perspective_type="Minified")

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT",
    ks=settings  # Perspective affects calculation depth and display elements
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(chart_data=chart_data)
```

### Perspective Comparison

```python
# Compare traditional vs minified perspectives
traditional_settings = KerykeionSettingsModel(perspective_type="Traditional")
minified_settings = KerykeionSettingsModel(perspective_type="Minified")

# Same person, different perspectives
birth_data = ("John", 1990, 7, 15, 10, 30, "Rome", "IT")

traditional_subject = AstrologicalSubjectFactory.from_birth_data(*birth_data, ks=traditional_settings)
minified_subject = AstrologicalSubjectFactory.from_birth_data(*birth_data, ks=minified_settings)

# Generate chart data for both perspectives
traditional_chart_data = ChartDataFactory.create_natal_chart_data(traditional_subject)
minified_chart_data = ChartDataFactory.create_natal_chart_data(minified_subject)

# Generate both chart types
traditional_chart_drawer = ChartDrawer(chart_data=traditional_chart_data)
minified_chart_drawer = ChartDrawer(chart_data=minified_chart_data)

traditional_svg = traditional_chart_drawer.makeTemplate()  # Get string content
minified_svg = minified_chart_drawer.makeTemplate()  # Get string content
```

## Output Options

These options control the technical aspects of SVG generation, affecting file size, compatibility, and visual presentation.

### Minification

Minification reduces file size by removing unnecessary whitespace and optimizing code structure, crucial for web applications and storage efficiency.

```python
chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(chart_data=chart_data)

# Get template strings with different options
standard_svg = chart_drawer.makeTemplate(minify=False)  # Human-readable
minified_svg = chart_drawer.makeTemplate(minify=True)   # Compressed (30-50% smaller)
compatible_svg = chart_drawer.makeTemplate(remove_css_variables=True)  # Legacy browsers
optimized_svg = chart_drawer.makeTemplate(minify=True, remove_css_variables=True)  # Maximum optimization

# Or save directly to files
chart_drawer.makeSVG(minify=True)  # Saves minified file to disk
```

### Transparency and Background

Background transparency enables flexible integration with different design contexts and overlay applications.

```python
# Transparent background useful for web integration and overlays
# Chart can be placed over other content or different backgrounds
# Perfect for: Web applications, design compositions, layered graphics
chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(
    chart_data=chart_data,
    transparent_background=True  # Removes default white background
)
svg_content = chart_drawer.makeTemplate()  # Get as string

# Combine with themes for different effects
dark_transparent = ChartDrawer(
    chart_data=chart_data,
    theme="dark",
    transparent_background=True
)

light_transparent = ChartDrawer(
    chart_data=chart_data, 
    theme="light",
    transparent_background=True
)

# Get string content for web integration
dark_svg = dark_transparent.makeTemplate()
light_svg = light_transparent.makeTemplate()
```

## ExternalNatal Charts

```python
# ExternalNatal shows how external planets affect a natal chart
# Different from Transit - shows current sky positions relative to birth chart
# Useful for timing analysis and progressions
natal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT"
)
external_subject = AstrologicalSubjectFactory.from_birth_data(
    "External", 2024, 1, 15, 12, 0, "Rome", "IT"
)

chart_data = ChartDataFactory.create_external_natal_chart_data(
    first_subject=natal_subject,    # Birth chart as reference (inner wheel)
    second_subject=external_subject # External planetary positions (outer wheel)
)

chart_drawer = ChartDrawer(chart_data=chart_data)

# Get chart content showing activated natal planets
svg_content = chart_drawer.makeTemplate()
```

## Advanced Customization

### Complete Configuration Example

```python
from kerykeion import AstrologicalSubject, ChartDrawer
from kerykeion.settings import KerykeionSettingsModel

# Advanced settings
settings = KerykeionSettingsModel(
    house_system="W",  # Whole Signs
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    perspective_type="Traditional"
)

# Create subjects with custom settings
subject1 = AstrologicalSubject(
    "Person1", 1990, 7, 15, 10, 30, "Rome", "IT", 
    ks=settings
)
subject2 = AstrologicalSubject(
    "Person2", 1985, 3, 20, 14, 15, "London", "GB", 
    ks=settings
)

# Custom points and aspects
active_points = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
active_aspects = ["conjunction", "opposition", "trine", "square"]  # List of aspect type strings

# Create synastry chart
chart = ChartDrawer(
    first_obj=subject1,
    second_obj=subject2,
    chart_type="Synastry",
    theme="dark",
    language="IT",
    active_points=active_points,
    active_aspects=active_aspects,  # Pass aspect type names as strings
    transparent_background=True
)

# Generate different outputs
full_chart = chart.makeTemplate(minify=True)  # String content, minified
wheel_only = chart.makeWheelOnlyTemplate()   # String content, wheel only
aspects_only = chart.makeAspectGridOnlyTemplate()  # String content, aspects only

# Or save directly to files
chart.makeSVG(minify=True)              # Save full chart
chart.makeWheelOnlySVG()                # Save wheel only
chart.makeAspectGridOnlySVG()           # Save aspects only
```

## Error Handling

```python
try:
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    chart_drawer = ChartDrawer(chart_data=chart_data)
    svg_content = chart_drawer.makeTemplate()  # Get string content
    # Process svg_content as needed
except Exception as e:
    print(f"Chart generation failed: {e}")
```

## File Operations

```python
import os

# Ensure output directory exists before saving charts
# Prevents file system errors when saving to subdirectories
os.makedirs("charts", exist_ok=True)

# METHOD 1: Get content as string and save manually (recommended)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(chart_data=chart_data, theme="dark")
svg_content = chart_drawer.makeTemplate()  # Get SVG as string

# Save with UTF-8 encoding to handle international characters
# Important for charts with non-Latin language settings
with open("charts/natal_chart.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

# METHOD 2: Direct file saving (saves to default output directory)
chart_drawer.makeSVG()  # Saves to path specified in constructor

print("Chart saved successfully")

# Example: Generate multiple chart versions as strings
chart_data_items = [
    ("full", chart_drawer.makeTemplate()),
    ("wheel", chart_drawer.makeWheelOnlyTemplate()),
    ("aspects", chart_drawer.makeAspectGridOnlyTemplate())
]

for chart_type, content in chart_data_items:
    filename = f"charts/{subject.name}_{chart_type}.svg"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filename}")
```

## Performance Considerations

- Use `minify=True` for smaller file sizes
- Cache chart data objects when generating multiple output formats
- Consider `transparent_background=True` for web integration
- Pre-compute chart data once with `ChartDataFactory`, then create multiple visualizations
- Use specific `active_points` and `active_aspects` in `ChartDataFactory` to reduce complexity

## Template Access

⚠️ **KEY DIFFERENCE**: Template methods return SVG strings, while SVG methods save files to disk.

The class provides template methods for getting SVG content as strings, perfect for web applications and custom processing:

```python
chart_data = ChartDataFactory.create_natal_chart_data(subject)
chart_drawer = ChartDrawer(chart_data=chart_data)

# Get template strings for further processing (RECOMMENDED for web apps)
full_template = chart_drawer.makeTemplate()          # Full chart as string
wheel_template = chart_drawer.makeWheelOnlyTemplate() # Wheel only as string
aspects_template = chart_drawer.makeAspectGridOnlyTemplate() # Aspects only as string

# Save files directly to disk (uses default output directory)
chart_drawer.makeSVG()                    # Saves full chart file
chart_drawer.makeWheelOnlySVG()          # Saves wheel only file
chart_drawer.makeAspectGridOnlySVG()     # Saves aspects only file

# Template methods support minification and CSS options
minified_template = chart_drawer.makeTemplate(minify=True, remove_css_variables=True)
```
