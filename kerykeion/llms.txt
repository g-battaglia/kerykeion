# Kerykeion AI Agent Guide

**Comprehensive reference for AI agents using the Kerykeion Astrological Library**

## Quick Overview

Kerykeion is a Python library for astrological calculations using Swiss Ephemeris. It provides:

-   Planetary position calculations (tropical/sidereal)
-   Chart generation (Natal, Synastry, Transit, Composite, Returns)
-   Aspect analysis and element/quality distributions
-   SVG chart visualization
-   Multiple house systems and coordinate perspectives

## Core Architecture

```
AstrologicalSubjectFactory → Creates subjects with planetary positions
         ↓
ChartDataFactory → Organizes data, calculates aspects/distributions
         ↓
ChartDrawer → Generates SVG visualizations
```

## Essential Imports

```python
from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
    PlanetaryReturnFactory,
    to_context  # AI-readable text serializer
)
```

## 1. Creating Astrological Subjects

### Basic Natal Chart (Offline - Recommended)

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    name="John Doe",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    lng=12.4964,  # Longitude (E+, W-)
    lat=41.9028,   # Latitude (N+, S-)
    tz_str="Europe/Rome",  # IANA timezone
    online=False
)
```

### Online Mode (Requires GeoNames)

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Jane Doe",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    city="Rome",
    nation="IT",
    geonames_username="your_username",
    online=True
)
```

### Current Time / Horary

```python
now = AstrologicalSubjectFactory.from_current_time(
    name="Current Transits",
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False
)
```

## 2. Configuration Options

### Zodiac Systems

```python
# Tropical (default - Western astrology)
zodiac_type="Tropical"

# Sidereal (Vedic astrology)
zodiac_type="Sidereal",
sidereal_mode="LAHIRI"  # or RAMAN, FAGAN_BRADLEY, KRISHNAMURTI
```

### House Systems

```python
houses_system_identifier="P"  # Placidus (default)
# "W" = Whole Sign, "K" = Koch, "A" = Equal, "C" = Campanus, "R" = Regiomontanus
```

### Active Points (Performance Optimization)

```python
active_points=["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Ascendant"]
```

### Perspective Types

```python
perspective_type="Apparent Geocentric"  # Default, standard astrology
# "True Geocentric", "Heliocentric", "Topocentric"
```

## 3. Accessing Data

### Planetary Positions

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
sun = subject.sun
print(f"{sun.name}: {sun.sign} {sun.abs_pos:.2f}° (House {sun.house})")
print(f"Retrograde: {sun.retrograde}")
```

### House Cusps

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
asc = subject.first_house  # Ascendant
mc = subject.tenth_house   # Midheaven
print(f"Ascendant: {asc.sign} {asc.abs_pos:.2f}°")
```

### Lunar Phase

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
if subject.lunar_phase:
    phase = subject.lunar_phase
    print(f"Phase: {phase.moon_phase_name}")
    print(f"Emoji: {phase.moon_emoji}")
```

## 4. Chart Data Factory

### Natal Chart Data

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Access structured data
print(f"Chart Type: {chart_data.chart_type}")
print(f"Aspects: {len(chart_data.aspects)}")
print(f"Fire: {chart_data.element_distribution.fire_percentage}%")
```

### Synastry (Relationship Analysis)

```python
person1 = AstrologicalSubjectFactory.from_birth_data(
    "Person1", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
person2 = AstrologicalSubjectFactory.from_birth_data(
    "Person2", 1992, 12, 25, 16, 45,
    lng=9.19, lat=45.4642, tz_str="Europe/Rome", online=False
)
synastry = ChartDataFactory.create_synastry_chart_data(
    first_subject=person1,
    second_subject=person2,
    include_house_comparison=True,
    include_relationship_score=True
)

if synastry.relationship_score:
    print(f"Compatibility: {synastry.relationship_score.score_value}")
```

### Transits

```python
natal = AstrologicalSubjectFactory.from_birth_data(
    "Natal", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
now = AstrologicalSubjectFactory.from_current_time(
    "Now", lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
transits = ChartDataFactory.create_transit_chart_data(
    natal_subject=natal,
    transit_subject=now
)
```

### Composite

```python
person1 = AstrologicalSubjectFactory.from_birth_data(
    "Person1", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
person2 = AstrologicalSubjectFactory.from_birth_data(
    "Person2", 1992, 12, 25, 16, 45,
    lng=9.19, lat=45.4642, tz_str="Europe/Rome", online=False
)
composite_factory = CompositeSubjectFactory(person1, person2)
composite_subject = composite_factory.get_midpoint_composite_subject_model()
composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)
```

### Custom Aspects

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
custom_aspects = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "square", "orb": 6},
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_aspects=custom_aspects
)
```

## 5. SVG Chart Generation

### Basic Chart

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)

# Get SVG as string (recommended for web apps)
svg_string = drawer.generate_svg_string()

# Or save to file
from pathlib import Path
output_dir = Path("charts")
output_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=output_dir)
```

### Themes & Languages

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(
    chart_data=chart_data,
    theme="dark",  # "classic", "light", "strawberry", "dark-high-contrast"
    chart_language="IT",  # "EN", "FR", "ES", "PT", "CN", "RU", "TR", "DE", "HI"
    transparent_background=True
)
```

### Output Variants

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)
full_chart = drawer.generate_svg_string()  # Complete chart
wheel_only = drawer.generate_wheel_only_svg_string()  # Just the wheel
aspects_only = drawer.generate_aspect_grid_only_svg_string()  # Just aspects
```

## 6. AI Context Serialization

Convert any Kerykeion model to AI-readable text:

```python
from kerykeion import to_context

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Serialize subject
text = to_context(subject)

# Serialize chart data
text = to_context(chart_data)

# Serialize specific components
text = to_context(subject.sun)
if subject.lunar_phase:
    text = to_context(subject.lunar_phase)
```

**Output format:** Factual, non-qualitative text descriptions optimized for AI interpretation.

## 7. Complete Workflow Examples

### Simple Natal Chart

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data)
svg = drawer.generate_svg_string()
```

### Relationship Compatibility

```python
person1 = AstrologicalSubjectFactory.from_birth_data(
    "Person1", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
person2 = AstrologicalSubjectFactory.from_birth_data(
    "Person2", 1992, 12, 25, 16, 45,
    lng=9.19, lat=45.4642, tz_str="Europe/Rome", online=False
)

synastry = ChartDataFactory.create_synastry_chart_data(person1, person2)
score = synastry.relationship_score.score_value if synastry.relationship_score else None
```

### Current Transits

```python
natal = AstrologicalSubjectFactory.from_birth_data(
    "Natal", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)

now = AstrologicalSubjectFactory.from_current_time(
    "Now", lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)

transits = ChartDataFactory.create_transit_chart_data(natal, now)
```

## 8. Data Models Reference

### Key Pydantic Models

-   `AstrologicalSubjectModel`: Complete subject with all positions
-   `KerykeionPointModel`: Individual planetary/point data
-   `AspectModel`: Aspect between two points
-   `LunarPhaseModel`: Lunar phase information
-   `SingleChartDataModel`: Natal/Composite/Return chart data
-   `DualChartDataModel`: Synastry/Transit chart data
-   `ElementDistributionModel`: Element percentages
-   `QualityDistributionModel`: Quality/mode percentages

### Available Points

Planets: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto
Nodes: Mean_Node, True_Node, Mean_South_Node, True_South_Node
Asteroids: Ceres, Pallas, Juno, Vesta, Chiron
Angles: Ascendant, Medium_Coeli, Descendant, Imum_Coeli
Arabic Parts: Pars_Fortunae, Pars_Spiritus, Pars_Amoris, Pars_Fidei
Fixed Stars: Regulus, Spica
Others: Mean_Lilith, True_Lilith, Earth, Vertex, Anti_Vertex

### Aspect Types

Major: conjunction (0°), opposition (180°), trine (120°), square (90°), sextile (60°)
Minor: semi-sextile (30°), semi-square (45°), sesquiquadrate (135°), quincunx (150°)
Special: quintile (72°), biquintile (144°)

## 9. Error Handling

```python
try:
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Subject", 1990, 6, 15, 14, 30,
        city="Rome", nation="IT",
        geonames_username="your_username"
    )
except Exception as e:
    print(f"Error: {e}")
    # Fallback to offline mode
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Subject", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
    )
```

## 10. Performance Tips

1. **Use offline mode** when coordinates are known (faster, more reliable)
2. **Limit active_points** for batch processing
3. **Disable optional features** when not needed:
    ```python
    calculate_lunar_phase=False
    include_house_comparison=False
    include_relationship_score=False
    ```
4. **Reuse chart_data objects** for multiple output formats

## 11. Common Patterns

### Vedic Chart

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Vedic", 1990, 6, 15, 14, 30,
    lng=82.9739, lat=25.3176, tz_str="Asia/Kolkata",
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    houses_system_identifier="W",  # Whole Sign
    online=False
)
```

### Horary Question

```python
horary = AstrologicalSubjectFactory.from_current_time(
    name="Will I get the job?",
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
```

### Batch Processing

```python
subjects = []
for year in range(1980, 1990):
    s = AstrologicalSubjectFactory.from_birth_data(
        f"Person_{year}", year, 1, 1, 12, 0,
        lng=0, lat=51.5, tz_str="UTC",
        active_points=["Sun", "Moon", "Ascendant"],
        calculate_lunar_phase=False,
        online=False
    )
    subjects.append(s)
```

## 12. Data Export

### JSON Export

```python
import json

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Pydantic models have .model_dump()
data_dict = chart_data.model_dump()
json_str = json.dumps(data_dict, indent=2, default=str)
```

### AI-Readable Text

```python
from kerykeion import to_context

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 6, 15, 14, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

ai_text = to_context(chart_data)
# Non-qualitative, factual description for LLM processing
```

## Dependencies

-   **Swiss Ephemeris**: Core astronomical calculations
-   **pytz**: Timezone handling
-   **GeoNames API**: Optional online location lookup (requires username)
-   **Python 3.8+**: Minimum version

## Environment Variables

```bash
export KERYKEION_GEONAMES_USERNAME="your_username"  # For online mode
```

## Quick Reference Table

| Task             | Factory                        | Key Parameter    |
| ---------------- | ------------------------------ | ---------------- |
| Natal Chart      | `from_birth_data()`            | Basic birth data |
| Current Transits | `from_current_time()`          | Location only    |
| Event Chart      | `from_iso_utc_time()`          | ISO timestamp    |
| Synastry         | `create_synastry_chart_data()` | Two subjects     |
| Composite        | `CompositeSubjectFactory`      | Two subjects     |
| Returns          | `PlanetaryReturnFactory`       | Planet type      |
| SVG Chart        | `ChartDrawer`                  | chart_data       |
| AI Text          | `to_context()`                 | Any model        |

---

**Version**: Kerykeion 5.x+  
**Documentation**: https://github.com/g-battaglia/kerykeion  
**License**: AGPL-3.0
