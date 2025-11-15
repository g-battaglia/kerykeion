# Chart Data Factory

## Overview

The `ChartDataFactory` class is the **data-centric counterpart** to `ChartDrawer`, providing structured access to pure astrological chart data without visual rendering components. While `ChartDrawer` creates beautiful SVG visualizations, `ChartDataFactory` extracts and organizes all the underlying astronomical calculations, aspects, and analytical data into Pydantic models perfect for data analysis, and programmatic processing.

This factory creates comprehensive `ChartDataModel` instances containing subjects, aspects, house comparisons, element/quality distributions, relationship analysis, and location information. The structured output is ideal for mobile app backends, and any application requiring astrological data in a machine-readable format.

## Core Features

- **Comprehensive Data Extraction**: All chart data including subjects, aspects, house analysis
- **Element & Quality Analysis**: Automatic calculation of elemental and modal distributions with percentages
- **Relationship Analysis**: Synastry compatibility scoring and house overlay analysis
- **Flexible Chart Support**: All chart types supported by Kerykeion (Natal, Transit, Synastry, Composite, DualReturnChart)
- **Data-Ready Format**: Pydantic models with JSON serialization and type validation
- **Performance Optimized**: Calculates only requested data points and aspects
- **Customizable Filtering**: Support for custom active points and aspect configurations

## Supported Chart Types

The `ChartDataFactory` supports all chart types available in Kerykeion, automatically including relevant analyses based on chart type:

- **Natal**: Single subject with internal aspects and element/quality analysis
- **Transit**: Natal subject with current transits, includes house comparison analysis  
- **Synastry**: Two subjects with inter-chart aspects, relationship scoring, and house overlays
- **Composite**: Composite subject with internal aspects and averaged location data
- **DualReturnChart**: Natal subject with planetary return, includes comparative analysis
- **SingleReturnChart**: Single planetary return with internal aspects

## Data Models

The `ChartDataFactory` now uses **two specialized data models** for better separation of concerns:

### SingleChartDataModel

Used for charts analyzing a single astrological subject:

```python
from kerykeion.schemas.kr_models import SingleChartDataModel

print("SingleChartDataModel fields:")
for name, field in SingleChartDataModel.model_fields.items():
    print(f"  {name:<22} {field.annotation}")
```

**Supported Chart Types:**
- **Natal**: Birth chart with internal aspects
- **Composite**: Midpoint-based composite chart with internal aspects  
- **SingleReturnChart**: Planetary return chart with internal aspects

### DualChartDataModel

Used for charts comparing or overlaying two astrological subjects:

```python
from kerykeion.schemas.kr_models import DualChartDataModel

print("DualChartDataModel fields:")
for name, field in DualChartDataModel.model_fields.items():
    print(f"  {name:<22} {field.annotation}")
```

**Supported Chart Types:**
- **Transit**: Natal chart with current planetary transits
- **Synastry**: Relationship compatibility between two people
- **DualReturnChart**: Natal chart with planetary return comparison

### Union Type

```python
from typing import Union
from kerykeion.schemas.kr_models import SingleChartDataModel, DualChartDataModel

ChartDataModel = Union[SingleChartDataModel, DualChartDataModel]
print(ChartDataModel.__args__)
```

The factory method returns the appropriate model type based on the chart type requested.
    longitude: float                                        # Geographic longitude
```

### ElementDistributionModel

Elemental analysis with raw points and calculated percentages:

```python
class ElementDistributionModel:
    fire: float              # Fire element points total
    earth: float             # Earth element points total
    air: float               # Air element points total
    water: float             # Water element points total
    fire_percentage: int     # Fire element percentage (0-100)
    earth_percentage: int    # Earth element percentage (0-100)
    air_percentage: int      # Air element percentage (0-100)
    water_percentage: int    # Water element percentage (0-100)
```

### QualityDistributionModel

Modal (quality) analysis with raw points and calculated percentages:

```python
class QualityDistributionModel:
    cardinal: float             # Cardinal quality points total
    fixed: float                # Fixed quality points total
    mutable: float              # Mutable quality points total
    cardinal_percentage: int    # Cardinal quality percentage (0-100)
    fixed_percentage: int       # Fixed quality percentage (0-100)
    mutable_percentage: int     # Mutable quality percentage (0-100)
```

## Basic Usage

### Import the Factory

```python
from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    SingleChartDataModel,
    DualChartDataModel,
    ElementDistributionModel,
    QualityDistributionModel
)
```

### Simple Natal Chart Data (SingleChartDataModel)

Extract comprehensive data from a natal chart for analysis use:

```python
# Create astrological subject
subject = AstrologicalSubjectFactory.from_birth_data(
    name="John Doe",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False
)

# Generate structured chart data
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Returns SingleChartDataModel
print(f"Model Type: {type(chart_data).__name__}")  # SingleChartDataModel
print(f"Chart Type: {chart_data.chart_type}")      # Natal
print(f"Subject: {chart_data.subject.name}")       # John Doe
print(f"Active Points: {len(chart_data.active_points)}")
print(f"Aspects: {len(chart_data.aspects)}")

# Element distribution analysis
elements = chart_data.element_distribution
print(f"Fire: {elements.fire_percentage}% ({elements.fire} points)")
print(f"Earth: {elements.earth_percentage}% ({elements.earth} points)")
print(f"Air: {elements.air_percentage}% ({elements.air} points)")
print(f"Water: {elements.water_percentage}% ({elements.water} points)")

# Quality distribution analysis  
qualities = chart_data.quality_distribution
print(f"Cardinal: {qualities.cardinal_percentage}%")
print(f"Fixed: {qualities.fixed_percentage}%")
print(f"Mutable: {qualities.mutable_percentage}%")

# Location information
print(f"Location: {subject.city}, {subject.nation}")
print(f"Coordinates: {subject.lat:.2f}, {subject.lng:.2f}")
```

### Synastry Chart Data (DualChartDataModel)

Create comprehensive relationship analysis data including compatibility scoring and house overlays:

```python
# Create two subjects for relationship analysis
person1 = AstrologicalSubjectFactory.from_birth_data(
    name="Person 1", year=1990, month=6, day=15,
    hour=14, minute=30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

person2 = AstrologicalSubjectFactory.from_birth_data(
    name="Person 2", year=1992, month=12, day=25,
    hour=16, minute=45,
    lng=9.19,
    lat=45.4642,
    tz_str="Europe/Rome",
    online=False,
)

# Generate synastry chart data with relationship analysis
synastry_data = ChartDataFactory.create_synastry_chart_data(
    person1, person2,
    include_house_comparison=True,
    include_relationship_score=True
)

# Returns DualChartDataModel  
print(f"Model Type: {type(synastry_data).__name__}")  # DualChartDataModel
print(f"Chart Type: {synastry_data.chart_type}")      # Synastry
print(f"First Subject: {synastry_data.first_subject.name}")   # Person 1
print(f"Second Subject: {synastry_data.second_subject.name}") # Person 2
print(f"Inter-chart Aspects: {len(synastry_data.aspects)}")

# Relationship compatibility analysis
if synastry_data.relationship_score:
    score = synastry_data.relationship_score
    print(f"Compatibility Score: {score.score_value}")
    print(f"Description: {score.score_description}")
    print(f"Destiny Connection: {score.is_destiny_sign}")
    print(f"Key Aspects: {len(score.aspects)}")

# House overlay analysis
if synastry_data.house_comparison:
    house_data = synastry_data.house_comparison
    print(f"Person 1 in Person 2's Houses: {len(house_data.first_points_in_second_houses)}")
    print(f"Person 2 in Person 1's Houses: {len(house_data.second_points_in_first_houses)}")

# Combined elemental emphasis
elements = synastry_data.element_distribution
print(f"Combined Elements - Fire: {elements.fire_percentage}%, Earth: {elements.earth_percentage}%")
```

### Transit Chart Data (DualChartDataModel)

Analyze current planetary transits affecting a natal chart:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

natal_person = AstrologicalSubjectFactory.from_birth_data(
    name="Transit Natal", year=1990, month=6, day=15,
    hour=14, minute=30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

current_transits = AstrologicalSubjectFactory.from_current_time(
    name="Current Transits",
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

transit_data = ChartDataFactory.create_transit_chart_data(
    natal_person,
    current_transits,
    include_house_comparison=True,
)

print(f"Transit Time: {transit_data.second_subject.iso_formatted_local_datetime}")
print(f"Active Transits: {len(transit_data.aspects)}")

# Analyze major transits
major_aspects = ["conjunction", "opposition", "trine", "square", "sextile"]
major_transits = [
    aspect for aspect in transit_data.aspects
    if aspect.aspect in major_aspects
]

print(f"Major Transits: {len(major_transits)}")
for transit in major_transits[:5]:  # Show first 5
    print(f"  {transit.p2_name} {transit.aspect} {transit.p1_name} (orb: {transit.orbit:.1f}°)")

# House activations
if transit_data.house_comparison:
    house_activations = transit_data.house_comparison.second_points_in_first_houses
    print(f"Activated Houses: {len(house_activations)}")
```

### Composite Chart Data

Extract data from composite relationships representing the partnership itself:

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory, ChartDataFactory

person1 = AstrologicalSubjectFactory.from_birth_data(
    "Composite Person A", 1990, 6, 15, 14, 30,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)
person2 = AstrologicalSubjectFactory.from_birth_data(
    "Composite Person B", 1992, 12, 25, 16, 45,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

composite_factory = CompositeSubjectFactory(person1, person2)
composite_subject = composite_factory.get_midpoint_composite_subject_model()
composite_chart = ChartDataFactory.create_composite_chart_data(composite_subject)

composite_subject_model = composite_chart.subject
first_subject = composite_subject_model.first_subject
second_subject = composite_subject_model.second_subject

print(f"Composite Chart Name: {composite_subject_model.name}")
print(f"Members: {first_subject.name} & {second_subject.name}")
print(f"Chart Type: {composite_chart.chart_type}")
print(f"Aspects: {len(composite_chart.aspects)}")

average_latitude = (first_subject.lat + second_subject.lat) / 2
average_longitude = (first_subject.lng + second_subject.lng) / 2
print(f"Approximate midpoint coordinates: {average_latitude:.2f}, {average_longitude:.2f}")

elements = composite_chart.element_distribution
print("Relationship Elements:")
print(f"  Fire: {elements.fire_percentage}% (passion, initiative)")
print(f"  Earth: {elements.earth_percentage}% (stability, practical)")
print(f"  Air: {elements.air_percentage}% (communication, mental)")
print(f"  Water: {elements.water_percentage}% (emotional, intuitive)")

qualities = composite_chart.quality_distribution
print("Modalities:")
print(f"  Cardinal: {qualities.cardinal_percentage}%")
print(f"  Fixed: {qualities.fixed_percentage}%")
print(f"  Mutable: {qualities.mutable_percentage}%")
```

## Advanced Usage

### Custom Active Points

Filter calculations to specific celestial points for performance or specialized analysis:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

custom_subject = AstrologicalSubjectFactory.from_birth_data(
    "Focused Points", 1991, 3, 5, 9, 10,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

custom_points = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Ascendant", "Medium_Coeli",
]

chart_data = ChartDataFactory.create_natal_chart_data(
    custom_subject,
    active_points=custom_points,
)

print(f"Active Points: {len(chart_data.active_points)}")
print(f"Calculated Aspects: {len(chart_data.aspects)}")
```

### Custom Aspect Configuration

Configure which aspects to calculate and their orb tolerances:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

custom_subject = AstrologicalSubjectFactory.from_birth_data(
    "Custom Aspects", 1992, 10, 28, 18, 15,
    lng=2.3522,
    lat=48.8566,
    tz_str="Europe/Paris",
    online=False,
)

custom_aspects = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "square", "orb": 8},
    {"name": "sextile", "orb": 6},
    {"name": "quintile", "orb": 2},
    {"name": "biquintile", "orb": 2},
]

chart_data = ChartDataFactory.create_natal_chart_data(
    custom_subject,
    active_aspects=custom_aspects,
)

print(f"Configured Aspects: {len(chart_data.active_aspects)}")
print(f"Found Aspects: {len(chart_data.aspects)}")
```

### Selective Analysis Features

Control which analytical features to include for performance optimization:

```python
# Create synastry data with selective features
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

person1 = AstrologicalSubjectFactory.from_birth_data(
    "Love Focus A", 1989, 1, 17, 8, 30,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)
person2 = AstrologicalSubjectFactory.from_birth_data(
    "Love Focus B", 1990, 3, 4, 21, 55,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

synastry_data = ChartDataFactory.create_synastry_chart_data(
    person1, person2,
    include_house_comparison=False,
    include_relationship_score=True,
    active_points=["Sun", "Moon", "Venus", "Mars"],
)

print(f"Love-focused aspects: {len(synastry_data.aspects)}")
```

## Programming Integration Examples

### Data Processing Example

Create comprehensive data processing pipeline for astrological analysis:

```python
from dataclasses import dataclass
from typing import Dict, Any, List
import json

@dataclass
class BirthData:
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    nation: str

def process_natal_chart(birth_data: BirthData) -> Dict[str, Any]:
    """Process natal chart data for analysis."""
    
    # Create astrological subject
    subject_factory = AstrologicalSubjectFactory()
    subject = subject_factory.from_birth_data(
        birth_data.name, birth_data.year, birth_data.month, birth_data.day,
        birth_data.hour, birth_data.minute, birth_data.city, birth_data.nation
    )
    
    # Generate chart data - returns SingleChartDataModel
    chart_data = ChartDataFactory().create_chart_data("Natal", subject)
    
    # Structure response data
    return {
        "chart_info": {
            "type": chart_data.chart_type,
            "subject": chart_data.subject.name,
            "birth_time": chart_data.subject.iso_formatted_local_datetime,
            "location": {
                "name": chart_data.location_name,
                "latitude": chart_data.latitude,
                "longitude": chart_data.longitude
            }
        },
        "planetary_positions": {
            point.name.lower(): {
                "sign": point.sign,
                "house": point.house,
                "position": point.position,
                "retrograde": point.retrograde
            }
            for point in [
                chart_data.subject.sun,
                chart_data.subject.moon,
                chart_data.subject.mercury,
                chart_data.subject.venus,
                chart_data.subject.mars,
                chart_data.subject.jupiter,
                chart_data.subject.saturn,
            ] if point is not None
        },
        "analysis": {
            "aspects": {
                "total": len(chart_data.aspects),
                "relevant": len(chart_data.aspects),
                "list": [
                    {
                        "from": aspect.p1_name,
                        "to": aspect.p2_name,
                        "type": aspect.aspect,
                        "orb": round(aspect.orbit, 2),
                        "exact_degrees": aspect.aspect_degrees
                    }
                    for aspect in chart_data.aspects
                ]
            },
            "elements": {
                "fire": chart_data.element_distribution.fire_percentage,
                "earth": chart_data.element_distribution.earth_percentage,
                "air": chart_data.element_distribution.air_percentage,
                "water": chart_data.element_distribution.water_percentage
            },
            "qualities": {
                "cardinal": chart_data.quality_distribution.cardinal_percentage,
                "fixed": chart_data.quality_distribution.fixed_percentage,
                "mutable": chart_data.quality_distribution.mutable_percentage
            }
        }
    }

def analyze_relationship_compatibility(person1: BirthData, person2: BirthData) -> Dict[str, Any]:
    """Analyze relationship compatibility between two people."""
    
    # Create subjects
    subject_factory = AstrologicalSubjectFactory()
    subject1 = subject_factory.from_birth_data(
        person1.name, person1.year, person1.month, person1.day,
        person1.hour, person1.minute, person1.city, person1.nation
    )
    subject2 = subject_factory.from_birth_data(
        person2.name, person2.year, person2.month, person2.day,
        person2.hour, person2.minute, person2.city, person2.nation
    )
    
    # Generate synastry data
    synastry_data = ChartDataFactory().create_chart_data("Synastry", subject1, subject2)
    
    return {
        "subjects": {
            "person1": {"name": person1.name},
            "person2": {"name": person2.name}
        },
        "compatibility": {
            "score": synastry_data.relationship_score.score_value if synastry_data.relationship_score else None,
            "description": synastry_data.relationship_score.score_description if synastry_data.relationship_score else None,
            "aspects_count": len(synastry_data.aspects)
        },
        "key_aspects": [
            {
                "person1_planet": aspect.p1_name,
                "person2_planet": aspect.p2_name,
                "aspect_type": aspect.aspect,
                "orb": round(aspect.orbit, 2),
                "strength": "strong" if aspect.orbit < 3 else "moderate" if aspect.orbit < 6 else "weak"
            }
            for aspect in synastry_data.aspects[:10]
        ],
        "house_overlays": {
            "person1_in_person2": len(synastry_data.house_comparison.first_points_in_second_houses) if synastry_data.house_comparison else 0,
            "person2_in_person1": len(synastry_data.house_comparison.second_points_in_first_houses) if synastry_data.house_comparison else 0
        }
    }

# Example usage
if __name__ == "__main__":
    # Process a natal chart
    birth_info = BirthData("John Doe", 1990, 6, 15, 14, 30, "Rome", "IT")
    natal_analysis = process_natal_chart(birth_info)
    
    # Save to JSON file
    with open("natal_analysis.json", "w") as f:
        json.dump(natal_analysis, f, indent=2)
    
    print("Natal chart analysis saved to natal_analysis.json")
```

### Batch Processing Example

Process multiple charts for statistical analysis:

```python
import csv
from dataclasses import dataclass
from typing import List, Dict, Any
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

@dataclass
class BirthData:
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    nation: str


def process_multiple_charts(birth_data_list: List[BirthData]) -> List[Dict[str, Any]]:
    """Process multiple natal charts for batch analysis."""

    results = []
    for birth_data in birth_data_list:
        try:
            subject = AstrologicalSubjectFactory.from_birth_data(
                birth_data.name,
                birth_data.year,
                birth_data.month,
                birth_data.day,
                birth_data.hour,
                birth_data.minute,
                city=birth_data.city,
                nation=birth_data.nation,
                online=True,
            )

            chart_data = ChartDataFactory.create_natal_chart_data(subject)

            result = {
                "name": birth_data.name,
                "fire_percentage": chart_data.element_distribution.fire_percentage,
                "earth_percentage": chart_data.element_distribution.earth_percentage,
                "air_percentage": chart_data.element_distribution.air_percentage,
                "water_percentage": chart_data.element_distribution.water_percentage,
                "cardinal_percentage": chart_data.quality_distribution.cardinal_percentage,
                "fixed_percentage": chart_data.quality_distribution.fixed_percentage,
                "mutable_percentage": chart_data.quality_distribution.mutable_percentage,
                "aspect_count": len(chart_data.aspects),
            }

            results.append(result)

        except Exception as e:
            print(f"Error processing {birth_data.name}: {e}")
            continue

    return results


def save_to_csv(data: List[Dict[str, Any]], filename: str):
    """Save processed data to CSV file."""
    if not data:
        return

    fieldnames = data[0].keys()

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


birth_data_samples = [
    BirthData("Person 1", 1990, 3, 15, 10, 30, "Rome", "IT"),
    BirthData("Person 2", 1985, 7, 22, 16, 45, "Milan", "IT"),
    BirthData("Person 3", 1992, 11, 8, 8, 15, "Naples", "IT"),
]

results = process_multiple_charts(birth_data_samples)
save_to_csv(results, "astrological_analysis.csv")
print(f"Processed {len(results)} charts and saved to CSV")
```

## Factory Methods Reference

### Main Factory Method

The unified factory method with automatic model selection:

```python
from inspect import signature
from kerykeion import ChartDataFactory

factory = ChartDataFactory()
print(signature(factory.create_chart_data))
```

**Return Types:**
- **SingleChartDataModel**: For "Natal", "Composite", "SingleReturnChart"
- **DualChartDataModel**: For "Transit", "Synastry", "DualReturnChart"

#### Natal Chart Data
```python
from inspect import signature
from kerykeion import ChartDataFactory

print(signature(ChartDataFactory.create_natal_chart_data))
```

#### Synastry Chart Data
```python
from inspect import signature
from kerykeion import ChartDataFactory

print(signature(ChartDataFactory.create_synastry_chart_data))
```

#### Transit Chart Data
```python
from inspect import signature
from kerykeion import ChartDataFactory

print(signature(ChartDataFactory.create_transit_chart_data))
```

#### Composite Chart Data
```python
from inspect import signature
from kerykeion import ChartDataFactory

print(signature(ChartDataFactory.create_composite_chart_data))
```

## Data Analysis Capabilities

### Element Analysis

The element distribution provides insights into temperament and life approach:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Element Analysis", 1994, 5, 2, 11, 20,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

elements = chart_data.element_distribution

# Temperament analysis
if elements.fire_percentage > 30:
    print("Strong fire influence: enthusiastic, energetic, pioneering")
if elements.earth_percentage > 30:
    print("Strong earth influence: practical, stable, materialistic")
if elements.air_percentage > 30:
    print("Strong air influence: intellectual, social, communicative")
if elements.water_percentage > 30:
    print("Strong water influence: emotional, intuitive, empathetic")

# Lacking elements (potential growth areas)
lacking_elements = []
if elements.fire_percentage < 15:
    lacking_elements.append("fire (initiative, enthusiasm)")
if elements.earth_percentage < 15:
    lacking_elements.append("earth (practicality, grounding)")
# Continue for air and water...

if lacking_elements:
    print(f"Areas for development: {', '.join(lacking_elements)}")
```

### Quality Analysis

The quality distribution reveals life approach and change patterns:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Quality Analysis", 1992, 3, 18, 6, 55,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

qualities = chart_data.quality_distribution

# Life approach analysis
if qualities.cardinal_percentage > 35:
    print("Cardinal emphasis: leadership, initiative, new beginnings")
if qualities.fixed_percentage > 35:
    print("Fixed emphasis: stability, persistence, determination")
if qualities.mutable_percentage > 35:
    print("Mutable emphasis: adaptability, flexibility, versatility")

# Balance assessment
total = qualities.cardinal_percentage + qualities.fixed_percentage + qualities.mutable_percentage
if total == 100:  # Sanity check
    most_prominent = max(
        ("Cardinal", qualities.cardinal_percentage),
        ("Fixed", qualities.fixed_percentage),
        ("Mutable", qualities.mutable_percentage),
        key=lambda x: x[1]
    )
    print(f"Most prominent quality: {most_prominent[0]} ({most_prominent[1]}%)")
```

### Aspect Pattern Analysis

Identify significant aspect patterns in the data:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Aspect Distribution", 1990, 8, 9, 4, 35,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

aspects = chart_data.aspects

# Count aspect types
aspect_counts = {}
for aspect in aspects:
    aspect_type = aspect.aspect
    aspect_counts[aspect_type] = aspect_counts.get(aspect_type, 0) + 1

# Analyze aspect emphasis
print("Aspect distribution:")
for aspect_type, count in sorted(aspect_counts.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / len(aspects)) * 100
    print(f"  {aspect_type}: {count} ({percentage:.1f}%)")

# Identify tight aspects (strong influences)
tight_aspects = [aspect for aspect in aspects if aspect.orbit < 2.0]
print(f"\nTight aspects (< 2° orb): {len(tight_aspects)}")

# Find exact aspects (very strong influences)
exact_aspects = [aspect for aspect in aspects if aspect.orbit < 0.5]
print(f"Nearly exact aspects (< 0.5° orb): {len(exact_aspects)}")
```

## Performance Considerations

### Optimizing Active Points

For high-performance applications, limit active points to only what's needed:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Point Sets", 1993, 5, 8, 7, 30,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

basic_points = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Ascendant"]
traditional_points = basic_points + ["Jupiter", "Saturn", "Medium_Coeli"]
modern_points = traditional_points + [
    "Uranus", "Neptune", "Pluto", "Chiron", "Mean_North_Lunar_Node", "Vertex"
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=basic_points,
)

print(f"Active Points: {len(chart_data.active_points)}")
print(f"Calculated Aspects: {len(chart_data.aspects)}")
```

### Aspect Configuration Optimization

Reduce aspect calculations for better performance:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Aspect Optimization", 1993, 5, 8, 7, 30,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

# Major aspects only (fastest)
major_aspects = [
    {"name": "conjunction", "orb": 8},
    {"name": "opposition", "orb": 8},
    {"name": "trine", "orb": 6},
    {"name": "square", "orb": 6},
    {"name": "sextile", "orb": 4},
]

# Traditional aspects (moderate)
traditional_aspects = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "square", "orb": 8},
    {"name": "sextile", "orb": 6},
    {"name": "semi-sextile", "orb": 3},
    {"name": "quincunx", "orb": 3},
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_aspects=major_aspects,  # Use for speed
)

print(f"Configured {len(chart_data.active_aspects)} active aspect types")
print(f"Resulting aspects: {len(chart_data.aspects)}")
```

### Selective Feature Loading

Disable expensive calculations when not needed:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

person1 = AstrologicalSubjectFactory.from_birth_data(
    "Quick A", 1989, 5, 9, 9, 45,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)
person2 = AstrologicalSubjectFactory.from_birth_data(
    "Quick B", 1991, 12, 19, 20, 15,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

quick_synastry = ChartDataFactory.create_synastry_chart_data(
    person1, person2,
    include_house_comparison=False,
    include_relationship_score=False,
    active_points=["Sun", "Moon", "Venus", "Mars"],
)

print(f"Quick analysis: {len(quick_synastry.aspects)} aspects")
```

## Error Handling

### Validation and Error Cases

The factory includes comprehensive validation and error handling:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.schemas import KerykeionException

natal_subject = AstrologicalSubjectFactory.from_birth_data(
    "Validation Example", 1990, 4, 3, 12, 0,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

try:
    # This will raise an error - missing second subject for synastry
    invalid_data = ChartDataFactory.create_chart_data(
        chart_type="Synastry",  # Requires second_subject
        first_subject=natal_subject,
    )
except KerykeionException as e:
    print(f"Chart creation error: {e}")

try:
    # This will raise an error - wrong subject type for composite
    invalid_composite = ChartDataFactory.create_chart_data(
        chart_type="Composite",
        first_subject=natal_subject,  # Should be CompositeSubjectModel
    )
except KerykeionException as e:
    print(f"Type validation error: {e}")


# Proper error handling in production code
def safe_chart_creation(subject_data, chart_type="Natal"):
    try:
        subject = AstrologicalSubjectFactory.from_birth_data(**subject_data)
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        return {"success": True, "data": chart_data}
    except KerykeionException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}
```

## Comparison with ChartDrawer

| Feature | ChartDrawer | ChartDataFactory |
|---------|-------------|------------------|
| **Purpose** | Visual chart rendering | Structured data extraction |
| **Output** | SVG files/strings | Pydantic models |
| **Use Cases** | Charts, reports, printing | Data analysis, databases |
| **Data Format** | Visual/graphical | JSON-serializable |
| **Performance** | Complex rendering | Data-only calculations |
| **Customization** | Themes, colors, fonts | Points, aspects, features |
| **Web Integration** | SVG display | Data processing |
| **Analysis Depth** | Visual patterns | Quantified data |

## Use Cases and Applications

### Application Development
Perfect for desktop applications, mobile backends, and data processing services providing astrological analysis.

### Mobile App Backends
Structured data ideal for mobile applications requiring astrological information.

### Data Analysis
Quantified astrological data for statistical analysis, research, and pattern recognition.

### Database Integration
Pydantic models can be easily stored in databases or converted to other formats.

### Machine Learning
Structured numerical data suitable for ML training and astrological pattern analysis.

### Third-Party Integration
Clean data format for integration with other systems and services.

### Batch Processing
Efficient for processing multiple charts without visual rendering overhead.

The `ChartDataFactory` represents the evolution of astrological software towards data-first design, providing the same comprehensive calculations as traditional chart software but in a format optimized for modern application development and data science workflows.
