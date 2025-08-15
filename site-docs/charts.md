# Charts Module - KerykeionChartSVG

## Overview

The `KerykeionChartSVG` class is the core visualization engine of Kerykeion, responsible for generating professional-quality SVG astrological charts. As the primary interface for chart creation, this module transforms astronomical calculations into beautiful, customizable visual representations that can be used in web applications, printed materials, or standalone analysis tools.

This module supports the complete spectrum of astrological chart types used in both Western and Vedic traditions, with extensive customization options for themes, languages, house systems, and zodiac types. The SVG output ensures scalable, high-quality graphics that maintain clarity at any size while remaining lightweight for web applications.

## Core Features

- **Chart Types**: Natal, ExternalNatal, Transit, Synastry, Composite
- **Output Methods**: Full chart, wheel-only, aspect grid-only
- **Themes**: classic, dark, light, strawberry, dark-high-contrast
- **Languages**: EN, IT, FR, ES, PT, CN, RU, TR, DE, HI
- **Zodiac Systems**: Tropical, Sidereal (multiple ayanamsas)
- **House Systems**: Placidus, Whole Signs, Equal House, Koch, Campanus, Regiomontanus, and more
- **Customization**: Active points, aspects, house systems, perspectives, transparency
- **Output Formats**: Standard SVG, minified SVG, template strings

## Basic Usage

The foundation of chart creation starts with defining astrological subjects and selecting appropriate chart types. The `KerykeionChartSVG` class handles all the complex calculations internally, transforming astronomical data into professional visual representations.

### Simple Natal Chart

A natal chart represents the sky at the moment of birth, showing planetary positions, house divisions, and aspects. This is the most fundamental chart type in astrology.

```python
from kerykeion import AstrologicalSubject, KerykeionChartSVG

# Create an astrological subject with birth data
# Parameters: name, year, month, day, hour, minute, city, country
subject = AstrologicalSubject("John", 1990, 7, 15, 10, 30, "Rome", "IT")

# Create a chart object - this calculates all planetary positions and aspects
chart = KerykeionChartSVG(subject)

# METHOD 1: Generate and save SVG file to disk
chart.makeSVG()  # Saves file to location specified in constructor

# METHOD 2: Get SVG content as string (recommended for web apps)
svg_content = chart.makeTemplate()  # Returns SVG as string

# If you want to save the string content manually:
with open("natal_chart.svg", "w") as f:
    f.write(svg_content)
```

### Synastry Chart

Synastry charts are used for relationship analysis, comparing two people's birth charts to understand compatibility and interaction patterns. The chart displays both individuals' planetary positions simultaneously, with aspects drawn between them.

```python
# Create two subjects for relationship compatibility analysis
subject1 = AstrologicalSubject("Person1", 1990, 7, 15, 10, 30, "Rome", "IT")
subject2 = AstrologicalSubject("Person2", 1985, 3, 20, 14, 15, "London", "GB")

# Synastry chart shows aspects between two people's planets
# first_obj = inner wheel, second_obj = outer wheel
chart = KerykeionChartSVG(
    first_obj=subject1,      # Person1's planets in inner circle
    second_obj=subject2,     # Person2's planets in outer circle
    chart_type="Synastry"    # Chart type for relationship analysis
)

# Get SVG content as string (recommended)
svg_content = chart.makeTemplate()

# OR save directly to file
chart.makeSVG()  # Saves to constructor location
```

### Composite Chart

Composite charts represent the mathematical midpoint between two people's planetary positions, creating a theoretical "relationship chart" that describes the combined energy and purpose of a partnership.

```python
# Composite chart calculates the midpoint between two people's planets
# Creates a theoretical "relationship chart" representing the union
chart = KerykeionChartSVG(
    first_obj=subject1,      # First person's birth data
    second_obj=subject2,     # Second person's birth data  
    chart_type="Composite"   # Midpoint calculation method
)

# Get the relationship chart as string
svg_content = chart.makeTemplate()
```

### Transit Chart

Transit charts show how current planetary movements affect an individual's natal chart. This is essential for timing analysis and understanding current astrological influences.

```python
# Create a transit subject for current planetary positions
# Transits show how current planets aspect natal positions
transit_subject = AstrologicalSubject("Transit", 2024, 1, 15, 12, 0, "Rome", "IT")

chart = KerykeionChartSVG(
    first_obj=subject1,         # Natal chart (inner wheel)
    second_obj=transit_subject, # Current planetary positions (outer wheel)
    chart_type="Transit"        # Shows transiting planet aspects to natal
)

# Get the transit chart content
svg_content = chart.makeTemplate()
```

## Output Methods

⚠️ **IMPORTANT DISTINCTION**: 
- `makeSVG()` methods **save files** to the location specified in the constructor
- `makeTemplate()` methods **return string content** without saving files

The KerykeionChartSVG class offers two categories of output methods: file generation and template string generation.

### Full Chart with Aspects

```python
chart = KerykeionChartSVG(subject)

# makeSVG() SAVES the complete chart file to disk
# Does NOT return content - saves to constructor's specified location
chart.makeSVG()  # File saved, no return value

# makeTemplate() RETURNS the complete chart as string
# Does NOT save file - returns SVG content for further processing
svg_string = chart.makeTemplate()  # Returns SVG content as string
```

### Wheel Only

```python
chart = KerykeionChartSVG(subject)

# makeWheelOnlySVG() SAVES wheel-only file to disk
chart.makeWheelOnlySVG()  # File saved, no return value

# makeWheelOnlyTemplate() RETURNS wheel-only content as string
wheel_string = chart.makeWheelOnlyTemplate()  # Returns SVG string
```

### Aspect Grid Only

```python
chart = KerykeionChartSVG(subject)

# makeAspectGridOnlySVG() SAVES aspect grid file to disk
chart.makeAspectGridOnlySVG()  # File saved, no return value

# makeAspectGridOnlyTemplate() RETURNS aspect grid as string
aspects_string = chart.makeAspectGridOnlyTemplate()  # Returns SVG string
```

## Themes

Visual presentation is crucial for astrological charts, and KerykeionChartSVG offers carefully designed themes to suit different contexts, from traditional printed materials to modern digital interfaces.

### Available Themes

```python
# Classic theme (default) - traditional colors and styling
# White background, black text, traditional planet colors
# Best for: Printed materials, traditional presentations, educational content
chart = KerykeionChartSVG(subject, theme="classic")

# Dark theme - modern dark interface
# Dark background, light text, optimized for night viewing
# Best for: Digital applications, reduced eye strain, modern aesthetics
chart = KerykeionChartSVG(subject, theme="dark")

# Light theme - clean minimalist appearance
# Light background, subtle colors, modern aesthetic
# Best for: Clean presentations, web applications, minimalist design
chart = KerykeionChartSVG(subject, theme="light")

# Strawberry theme - elegant pink and red tones
# Beautiful color palette with warm, inviting aesthetics
# Best for: Modern presentations, romantic contexts, unique visual appeal
chart = KerykeionChartSVG(subject, theme="strawberry")

# High contrast dark - accessibility focused
# Maximum contrast for visual impairments, dark background
# Best for: Accessibility compliance, visually impaired users, high contrast needs
chart = KerykeionChartSVG(subject, theme="dark-high-contrast")
```

## Language Support

Kerykeion provides comprehensive internationalization support, making charts accessible to astrologers and users worldwide. Each language includes localized planet names, zodiac signs, house labels, and aspect terminology.

```python
# Italian - all text labels, planet names, and signs in Italian
# Includes traditional Italian astrological terminology
chart = KerykeionChartSVG(subject, language="IT")

# English (default) - standard international astrological terms
# Uses conventional Western astrological terminology
chart = KerykeionChartSVG(subject, language="EN")

# French - labels and terms translated to French
# Follows French astrological tradition and terminology
chart = KerykeionChartSVG(subject, language="FR")

# Spanish - full Spanish localization of chart text
# Suitable for both European and Latin American contexts
chart = KerykeionChartSVG(subject, language="ES")

# Portuguese - Brazilian/Portuguese language support
# Appropriate for both European and Brazilian Portuguese
chart = KerykeionChartSVG(subject, language="PT")

# Chinese - planet names and signs in Chinese characters
# Traditional Chinese astrological terminology
chart = KerykeionChartSVG(subject, language="CN")

# Russian - Cyrillic text for all chart labels
# Complete Russian localization for Cyrillic readers
chart = KerykeionChartSVG(subject, language="RU")

# Turkish - Turkish language localization
# Modern Turkish astrological terminology
chart = KerykeionChartSVG(subject, language="TR")

# German - German astrological terminology
# Traditional German astrological terms and conventions
chart = KerykeionChartSVG(subject, language="DE")

# Hindi - Devanagari script for Indian astrology contexts
# Supports Vedic astrology terminology in Hindi
chart = KerykeionChartSVG(subject, language="HI")
```

## Zodiac Systems

Kerykeion supports both major zodiac systems used in astrology worldwide. The choice between tropical and sidereal affects all planetary positions and interpretations.

### Tropical Zodiac (Default)

The tropical zodiac is based on the seasons and is standard in Western astrology. It uses the vernal equinox as 0° Aries.

```python
from kerykeion.settings import KerykeionSettingsModel

# Tropical zodiac (default) - seasonal based, used in Western astrology
# 0° Aries = vernal equinox, signs aligned with seasons
settings = KerykeionSettingsModel(
    zodiac_type="Tropical"  # Default setting, can be omitted
)

subject = AstrologicalSubject(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT",
    ks=settings
)

chart = KerykeionChartSVG(subject)
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
subject = AstrologicalSubject(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT",
    ks=settings  # Sidereal positions typically ~24° different from tropical
)

# Chart will show sidereal positions (star-based)
chart = KerykeionChartSVG(subject)
svg_content = chart.makeTemplate()  # Get as string, don't save file
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
tropical_subject = AstrologicalSubject(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT", 
    ks=tropical_settings
)
sidereal_subject = AstrologicalSubject(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT", 
    ks=sidereal_settings
)

# Generate charts for comparison
tropical_chart = KerykeionChartSVG(tropical_subject)
sidereal_chart = KerykeionChartSVG(sidereal_subject)

tropical_svg = tropical_chart.makeTemplate()  # Get string content
sidereal_svg = sidereal_chart.makeTemplate()  # Get string content
```

## Custom Points and Aspects

Fine-tuning which celestial bodies and aspects appear on your charts allows for focused analysis and cleaner presentations. This is particularly useful for educational materials or specific astrological techniques.

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

chart = KerykeionChartSVG(
    subject, 
    active_points=personal_planets  # Only these planets will appear on chart
)
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

chart = KerykeionChartSVG(
    subject,
    active_aspects=major_aspects  # List of strings: aspect type names
)
```

### Combined Configuration Example

```python
# Create a focused chart for relationship counseling
relationship_points = ["Sun", "Moon", "Venus", "Mars", "Jupiter"]
relationship_aspects = ["conjunction", "opposition", "trine", "square"]  # List of aspect type strings

synastry_chart = KerykeionChartSVG(
    first_obj=subject1,
    second_obj=subject2,
    chart_type="Synastry",
    active_points=relationship_points,
    active_aspects=relationship_aspects,  # Pass list of aspect type names as strings
    theme="light",
    language="EN"
)
```

## Sidereal Charts

```python
from kerykeion.settings import KerykeionSettingsModel

# Configure sidereal zodiac system (used in Vedic/Indian astrology)
# Accounts for precession of equinoxes, different from tropical zodiac
settings = KerykeionSettingsModel(
    zodiac_type="Sidereal",    # Use sidereal instead of tropical
    sidereal_mode="LAHIRI"     # Lahiri ayanamsa (most common in Vedic)
)

# Create subject with sidereal settings applied
subject = AstrologicalSubject(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT",
    ks=settings  # Apply custom settings to calculation
)

# Chart will now show sidereal positions (typically ~24° different)
chart = KerykeionChartSVG(subject)
svg_content = chart.makeSVG()
```

## House Systems

House systems determine how the ecliptic is divided into twelve segments, each representing different life areas. The choice of house system can significantly affect chart interpretation, especially for planets near house cusps.

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
    subject = AstrologicalSubject(*birth_data, ks=settings)
    chart = KerykeionChartSVG(subject)
    charts[name] = chart.makeTemplate()  # Get as string
    
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
high_lat_subject = AstrologicalSubject(
    "Arctic", 1990, 7, 15, 12, 0, "Tromsø", "NO", 
    ks=high_lat_settings
)

# Equatorial location
equatorial_settings = KerykeionSettingsModel(house_system="P")
equatorial_subject = AstrologicalSubject(
    "Equator", 1990, 7, 15, 12, 0, "Quito", "EC", 
    ks=equatorial_settings
)

# Generate charts to see latitude effects
high_lat_chart = KerykeionChartSVG(high_lat_subject)
equatorial_chart = KerykeionChartSVG(equatorial_subject)
```

## Chart Perspectives

Chart perspectives control the overall approach to chart calculation and presentation, affecting how data is processed and displayed.

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

subject = AstrologicalSubject(
    "John", 1990, 7, 15, 10, 30, "Rome", "IT",
    ks=settings  # Perspective affects calculation depth and display elements
)

chart = KerykeionChartSVG(subject)
```

### Perspective Comparison

```python
# Compare traditional vs minified perspectives
traditional_settings = KerykeionSettingsModel(perspective_type="Traditional")
minified_settings = KerykeionSettingsModel(perspective_type="Minified")

# Same person, different perspectives
birth_data = ("John", 1990, 7, 15, 10, 30, "Rome", "IT")

traditional_subject = AstrologicalSubject(*birth_data, ks=traditional_settings)
minified_subject = AstrologicalSubject(*birth_data, ks=minified_settings)

# Generate both chart types
traditional_chart = KerykeionChartSVG(traditional_subject)
minified_chart = KerykeionChartSVG(minified_subject)

traditional_svg = traditional_chart.makeTemplate()  # Get string content
minified_svg = minified_chart.makeTemplate()  # Get string content
```

## Output Options

These options control the technical aspects of SVG generation, affecting file size, compatibility, and visual presentation.

### Minification

Minification reduces file size by removing unnecessary whitespace and optimizing code structure, crucial for web applications and storage efficiency.

```python
chart = KerykeionChartSVG(subject)

# Get template strings with different options
standard_svg = chart.makeTemplate(minify=False)  # Human-readable
minified_svg = chart.makeTemplate(minify=True)   # Compressed (30-50% smaller)
compatible_svg = chart.makeTemplate(remove_css_variables=True)  # Legacy browsers
optimized_svg = chart.makeTemplate(minify=True, remove_css_variables=True)  # Maximum optimization

# Or save directly to files
chart.makeSVG(minify=True)  # Saves minified file to disk
```

### Transparency and Background

Background transparency enables flexible integration with different design contexts and overlay applications.

```python
# Transparent background useful for web integration and overlays
# Chart can be placed over other content or different backgrounds
# Perfect for: Web applications, design compositions, layered graphics
chart = KerykeionChartSVG(
    subject,
    transparent_background=True  # Removes default white background
)
svg_content = chart.makeTemplate()  # Get as string

# Combine with themes for different effects
dark_transparent = KerykeionChartSVG(
    subject,
    theme="dark",
    transparent_background=True
)

light_transparent = KerykeionChartSVG(
    subject, 
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
chart = KerykeionChartSVG(
    first_obj=natal_subject,    # Birth chart as reference (inner wheel)
    second_obj=transit_subject, # Current planetary positions (outer wheel)
    chart_type="ExternalNatal"  # External influences on natal positions
)

# Get chart content showing activated natal planets
svg_content = chart.makeTemplate()
```

## Advanced Customization

### Complete Configuration Example

```python
from kerykeion import AstrologicalSubject, KerykeionChartSVG
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
chart = KerykeionChartSVG(
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
    chart = KerykeionChartSVG(subject)
    svg_content = chart.makeTemplate()  # Get string content
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
chart = KerykeionChartSVG(subject, theme="dark")
svg_content = chart.makeTemplate()  # Get SVG as string

# Save with UTF-8 encoding to handle international characters
# Important for charts with non-Latin language settings
with open("charts/natal_chart.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

# METHOD 2: Direct file saving (saves to constructor location)
chart.makeSVG()  # Saves to path specified in constructor

print("Chart saved successfully")

# Example: Generate multiple chart versions as strings
chart_data = [
    ("full", chart.makeTemplate()),
    ("wheel", chart.makeWheelOnlyTemplate()),
    ("aspects", chart.makeAspectGridOnlyTemplate())
]

for chart_type, content in chart_data:
    filename = f"charts/{subject.name}_{chart_type}.svg"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filename}")
```

## Performance Considerations

- Use `minify=True` for smaller file sizes
- Cache chart objects when generating multiple outputs
- Consider `transparent_background=True` for web integration
- Use specific `active_points` and `active_aspects` (lists of strings) to reduce complexity

## Template Access

⚠️ **KEY DIFFERENCE**: Template methods return SVG strings, while SVG methods save files to disk.

The class provides template methods for getting SVG content as strings, perfect for web applications and custom processing:

```python
chart = KerykeionChartSVG(subject)

# Get template strings for further processing (RECOMMENDED for web apps)
full_template = chart.makeTemplate()          # Full chart as string
wheel_template = chart.makeWheelOnlyTemplate() # Wheel only as string
aspects_template = chart.makeAspectGridOnlyTemplate() # Aspects only as string

# Save files directly to disk (uses constructor path)
chart.makeSVG()                    # Saves full chart file
chart.makeWheelOnlySVG()          # Saves wheel only file
chart.makeAspectGridOnlySVG()     # Saves aspects only file

# Template methods support minification and CSS options
minified_template = chart.makeTemplate(minify=True, remove_css_variables=True)
```
