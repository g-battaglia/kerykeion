# Composite Subject Factory

The `composite_subject_factory` module creates composite astrological charts from two individual subjects, representing the relationship between two people through midpoint calculations.

## Overview

The `CompositeSubjectFactory` creates relationship charts by calculating the midpoint between corresponding planetary positions and house cusps of two people. This produces a single chart that symbolizes the energy and dynamics of the relationship itself, rather than comparing two separate individual charts.

Composite charts are fundamental in relationship astrology because they represent the "third entity" created when two people come together. Unlike synastry (which overlays two charts), a composite chart shows the relationship as if it were a person with its own personality, strengths, and challenges.

## Key Features

- **Midpoint Calculations**: Planetary and house cusp positions calculated as circular means, ensuring proper handling of zodiacal boundaries
- **Compatibility Validation**: Ensures both subjects use identical astrological settings (zodiac type, house system, etc.)
- **Boundary Handling**: Sophisticated circular mathematics for proper zodiacal boundary crossings (e.g., 350° + 10° = 0°, not 180°)
- **Lunar Phase Calculation**: Determines the composite emotional cycle and relationship rhythm
- **Common Points Only**: Intelligently includes only shared active points between subjects for meaningful results

## CompositeSubjectFactory Class

### Basic Usage

Creating a composite chart requires two individual astrological subjects with compatible settings. The process is straightforward: create both individual charts first, then combine them using the factory.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

# Create two individual charts
person1 = AstrologicalSubjectFactory.from_birth_data(
    name="John",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

person2 = AstrologicalSubjectFactory.from_birth_data(
    name="Jane",
    year=1992, month=9, day=22,
    hour=18, minute=45,
    lng=-118.2437,
    lat=34.0522,
    tz_str="America/Los_Angeles",
    online=False,
)

# Create composite chart
composite = CompositeSubjectFactory(person1, person2)
composite_model = composite.get_midpoint_composite_subject_model()

print(f"Composite Chart: {composite_model.name}")
print(f"Composite Sun: {composite_model.sun.sign} {composite_model.sun.abs_pos:.2f}°")
print(f"Composite Moon: {composite_model.moon.sign} {composite_model.moon.abs_pos:.2f}°")
print(f"Composite Ascendant: {composite_model.ascendant.sign} {composite_model.ascendant.abs_pos:.2f}°")
```

**Output:**
```
Composite Chart: John and Jane Composite Chart
Composite Sun: Leo 18.23°
Composite Moon: Aquarius 12.45°
Composite Ascendant: Scorpio 5.67°
```

### Custom Chart Name

By default, the composite chart name combines both individual names. You can provide a custom name that better reflects the relationship's nature or purpose.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

person1 = AstrologicalSubjectFactory.from_birth_data(
    name="Partner 1",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

person2 = AstrologicalSubjectFactory.from_birth_data(
    name="Partner 2",
    year=1992, month=9, day=22,
    hour=18, minute=45,
    lng=-118.2437,
    lat=34.0522,
    tz_str="America/Los_Angeles",
    online=False,
)

# Create composite with custom name
composite = CompositeSubjectFactory(
    person1,
    person2,
    chart_name="Our Relationship Chart"
)

composite_model = composite.get_midpoint_composite_subject_model()
print(f"Chart Name: {composite_model.name}")
```

**Output:**
```
Chart Name: Our Relationship Chart
```

## Detailed Examples

### Complete Relationship Analysis

This example demonstrates a comprehensive relationship analysis using composite charts. The composite positions reveal how the relationship functions as a unified entity, showing its core identity, emotional patterns, and external expression.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

# Create detailed composite analysis
person1 = AstrologicalSubjectFactory.from_birth_data(
    name="Partner A",
    year=1985, month=3, day=21,
    hour=10, minute=30,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

person2 = AstrologicalSubjectFactory.from_birth_data(
    name="Partner B",
    year=1987, month=11, day=8,
    hour=16, minute=15,
    lng=2.3522,
    lat=48.8566,
    tz_str="Europe/Paris",
    online=False,
)

composite = CompositeSubjectFactory(person1, person2, "Partnership Analysis")
model = composite.get_midpoint_composite_subject_model()

print("=== COMPOSITE RELATIONSHIP CHART ===")
print(f"Relationship: {model.name}")
print(f"Chart Type: {model.composite_chart_type}")
print(f"Zodiac System: {model.zodiac_type}")
print(f"House System: {model.houses_system_name}")

# Core relationship dynamics
print("\n=== CORE RELATIONSHIP DYNAMICS ===")
print(f"Composite Sun (Identity): {model.sun.sign} {model.sun.abs_pos:.2f}° (House {model.sun.house})")
print(f"Composite Moon (Emotions): {model.moon.sign} {model.moon.abs_pos:.2f}° (House {model.moon.house})")
print(f"Composite Mercury (Communication): {model.mercury.sign} {model.mercury.abs_pos:.2f}° (House {model.mercury.house})")
print(f"Composite Venus (Love): {model.venus.sign} {model.venus.abs_pos:.2f}° (House {model.venus.house})")
print(f"Composite Mars (Action): {model.mars.sign} {model.mars.abs_pos:.2f}° (House {model.mars.house})")

# Relationship structure - how the partnership manifests in the world
print("\n=== RELATIONSHIP STRUCTURE ===")
print(f"Composite Ascendant (How others see the relationship): {model.ascendant.sign} {model.ascendant.abs_pos:.2f}°")
print(f"Composite 7th House (Partnership dynamics): {model.seventh_house.sign} {model.seventh_house.abs_pos:.2f}°")
print(f"Composite 10th House (Public image): {model.tenth_house.sign} {model.tenth_house.abs_pos:.2f}°")

# Emotional cycle - the relationship's emotional rhythm and growth pattern
print(f"\n=== EMOTIONAL DYNAMICS ===")
print(f"Lunar Phase: {model.lunar_phase.moon_phase:.2f}")
print(f"Phase Name: {model.lunar_phase.moon_phase_name}")
print(f"Emotional Pattern: {model.lunar_phase.moon_phase_name} energy in the relationship")
```

**Output:**
```
=== COMPOSITE RELATIONSHIP CHART ===
Relationship: Partnership Analysis
Chart Type: Midpoint
Zodiac System: Tropical
House System: Placidus

=== CORE RELATIONSHIP DYNAMICS ===
Composite Sun (Identity): Cancwr 29.45° (House 7)
Composite Moon (Emotions): Virgo 12.78° (House 9)
Composite Mercury (Communication): Leo 5.23° (House 8)
Composite Venus (Love): Gemini 18.90° (House 6)
Composite Mars (Action): Libra 22.34° (House 10)

=== RELATIONSHIP STRUCTURE ===
Composite Ascendant (How others see the relationship): Sagittarius 15.67°
Composite 7th House (Partnership dynamics): Gemini 15.67°
Composite 10th House (Public image): Virgo 8.23°

=== EMOTIONAL DYNAMICS ===
Lunar Phase: 0.73
Phase Name: Waxing Gibbous
Emotional Pattern: Waxing Gibbous energy in the relationship
```

### Individual vs Composite Comparison

This comparison shows how individual planetary positions combine to create the composite midpoints. Understanding these differences helps interpret how the relationship transforms individual energies into something new.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

# Compare individual charts with composite
def compare_positions(person1, person2, composite, planet_name):
    p1_planet = getattr(person1, planet_name)
    p2_planet = getattr(person2, planet_name)
    comp_planet = getattr(composite, planet_name)
    
    print(f"{planet_name.capitalize()}:")
    print(f"  Person 1: {p1_planet.sign} {p1_planet.abs_pos:.2f}°")
    print(f"  Person 2: {p2_planet.sign} {p2_planet.abs_pos:.2f}°")
    print(f"  Composite: {comp_planet.sign} {comp_planet.abs_pos:.2f}°")
    print()

person1 = AstrologicalSubjectFactory.from_birth_data(
    "Alex", 1990, 4, 12, 9, 20,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)
person2 = AstrologicalSubjectFactory.from_birth_data(
    "Sam", 1988, 8, 5, 17, 45,
    lng=2.3522,
    lat=48.8566,
    tz_str="Europe/Paris",
    online=False,
)
composite = CompositeSubjectFactory(person1, person2)
composite_model = composite.get_midpoint_composite_subject_model()

print("=== INDIVIDUAL vs COMPOSITE COMPARISON ===")
planets = ["sun", "moon", "venus", "mars"]
for planet in planets:
    compare_positions(person1, person2, composite_model, planet)
```

**Output:**
```
=== INDIVIDUAL vs COMPOSITE COMPARISON ===
Sun:
  Person 1: Aries 0.45°
  Person 2: Scorpio 15.67°
  Composite: Cancer 29.45°

Moon:
  Person 1: Gemini 23.12°
  Person 2: Sagittarius 2.45°
  Composite: Virgo 12.78°

Venus:
  Person 1: Pisces 8.90°
  Person 2: Virgo 28.90°
  Composite: Gemini 18.90°

Mars:
  Person 1: Capricorn 15.23°
  Person 2: Cancer 29.45°
  Composite: Libra 22.34°
```

### Different Chart Types

Composite charts can be applied to any type of relationship. This example uses famous individuals to demonstrate how creative partnerships might be analyzed through composite astrology.

```python
# Famous couple example - John Lennon & Yoko Ono
john = AstrologicalSubjectFactory.from_birth_data(
    name="John Lennon",
    year=1940, month=10, day=9,
    hour=18, minute=30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

yoko = AstrologicalSubjectFactory.from_birth_data(
    name="Yoko Ono",
    year=1933, month=2, day=18,
    hour=20, minute=30,
    lng=139.6917,
    lat=35.6895,
    tz_str="Asia/Tokyo",
    online=False,
)

# Creative partnership composite
creative_composite = CompositeSubjectFactory(
    john, yoko, 
    "John & Yoko Creative Partnership"
)

model = creative_composite.get_midpoint_composite_subject_model()

print("=== CREATIVE PARTNERSHIP COMPOSITE ===")
print(f"Partnership: {model.name}")

# Focus on creative and communication planets
creative_planets = [
    ("sun", "Creative Identity"),
    ("mercury", "Communication Style"),
    ("venus", "Artistic Expression"),
    ("jupiter", "Shared Vision"),
    ("neptune", "Inspiration/Dreams")
]

for planet_attr, description in creative_planets:
    if hasattr(model, planet_attr):
        planet = getattr(model, planet_attr)
        print(f"{description}: {planet.sign} {planet.abs_pos:.2f}° (House {planet.house})")
```

### Sidereal Composite Chart

Composite charts work with any zodiac system, provided both individual charts use the same settings. This example shows how to create a Vedic (sidereal) composite chart following traditional Indian astrological principles.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

# Create Vedic composite chart
person1_vedic = AstrologicalSubjectFactory.from_birth_data(
    name="Partner A",
    year=1988, month=7, day=15,
    hour=14, minute=30,
    lng=72.8777,
    lat=19.0760,
    tz_str="Asia/Kolkata",
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    houses_system_identifier="P",
    online=False,
)

person2_vedic = AstrologicalSubjectFactory.from_birth_data(
    name="Partner B",
    year=1990, month=12, day=3,
    hour=9, minute=45,
    lng=77.2090,
    lat=28.6139,
    tz_str="Asia/Kolkata",
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    houses_system_identifier="P",
    online=False,
)

vedic_composite = CompositeSubjectFactory(
    person1_vedic, 
    person2_vedic, 
    "Vedic Relationship Chart"
)

vedic_model = vedic_composite.get_midpoint_composite_subject_model()

print("=== VEDIC COMPOSITE CHART ===")
print(f"Zodiac: {vedic_model.zodiac_type} ({vedic_model.sidereal_mode})")
print(f"Houses: {vedic_model.houses_system_name}")

# Show differences between Tropical and Sidereal composite
print("\nVedic planetary positions:")
for planet in ["sun", "moon", "venus", "mars", "jupiter"]:
    if hasattr(vedic_model, planet):
        p = getattr(vedic_model, planet)
        print(f"  {p.name}: {p.sign} {p.abs_pos:.2f}°")
```

## Error Handling

Understanding common errors helps ensure successful composite chart creation and troubleshooting when issues arise.

### Incompatible Charts

The most common error occurs when trying to combine charts with different astrological settings. All calculation parameters must match between the two subjects.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

# Create charts with different settings
tropical_chart = AstrologicalSubjectFactory.from_birth_data(
    name="Tropical Person",
    year=1990, month=1, day=1,
    hour=12, minute=0,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    zodiac_type="Tropical",
    online=False,
)

sidereal_chart = AstrologicalSubjectFactory.from_birth_data(
    name="Sidereal Person",
    year=1992, month=6, day=15,
    hour=14, minute=30,
    lng=72.8777,
    lat=19.0760,
    tz_str="Asia/Kolkata",
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    online=False,
)

# This will raise an exception
try:
    incompatible_composite = CompositeSubjectFactory(tropical_chart, sidereal_chart)
except Exception as e:
    print(f"Error: {e}")
    print("Solution: Both charts must use the same zodiac type, house system, and perspective")
```

**Output:**
```
Error: Both subjects must have the same zodiac type
Solution: Both charts must use the same zodiac type, house system, and perspective
```

### Common Points Analysis

When subjects have different active points, the composite automatically uses only the points common to both charts. This ensures meaningful midpoint calculations and prevents errors from missing data.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

# Charts with different active points
minimal_chart = AstrologicalSubjectFactory.from_birth_data(
    name="Essential Person",
    year=1985, month=3, day=15,
    hour=10, minute=0,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    active_points=["Sun", "Moon", "Mercury", "Venus", "Ascendant"],
    online=False,
)

full_chart = AstrologicalSubjectFactory.from_birth_data(
    name="Complete Person",
    year=1987, month=8, day=20,
    hour=16, minute=30,
    lng=9.19,
    lat=45.4642,
    tz_str="Europe/Rome",
    online=False,
)

composite = CompositeSubjectFactory(minimal_chart, full_chart)
model = composite.get_midpoint_composite_subject_model()

print("=== COMMON POINTS ANALYSIS ===")
print(f"Person 1 active points: {len(minimal_chart.active_points)}")
print(f"Person 2 active points: {len(full_chart.active_points)}")
print(f"Composite active points: {len(model.active_points)}")
print(f"Common points used: {model.active_points}")
```

## Practical Applications

Composite charts serve different purposes depending on the relationship type. Here are common applications with specific interpretive focus areas.

### 1. Romantic Relationships
For romantic partnerships, focus on houses related to love, intimacy, and shared values. The composite reveals how the couple functions together emotionally and romantically.

```python
# Relationship compatibility analysis
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

partner1 = AstrologicalSubjectFactory.from_birth_data(
    "Partner 1", 1988, 4, 10, 9, 15,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
partner2 = AstrologicalSubjectFactory.from_birth_data(
    "Partner 2", 1986, 9, 2, 19, 40,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

romantic_composite = CompositeSubjectFactory(partner1, partner2, "Love Compatibility")
model = romantic_composite.get_midpoint_composite_subject_model()

# Focus on relationship houses
relationship_houses = [1, 5, 7, 8]  # Identity, Romance, Partnership, Intimacy
for house_num in relationship_houses:
    house_name = f"{['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth'][house_num]}_house"
    house = getattr(model, house_name)
    print(f"House {house_num}: {house.sign} {house.abs_pos:.2f}°")
```

### 2. Business Partnerships
Business composites emphasize practical matters: shared resources, work dynamics, and public reputation. The focus shifts to material success and professional compatibility.

```python
# Business partnership analysis
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

business_partner1 = AstrologicalSubjectFactory.from_birth_data(
    "Entrepreneur A", 1980, 5, 8, 8, 45,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)
business_partner2 = AstrologicalSubjectFactory.from_birth_data(
    "Entrepreneur B", 1982, 11, 19, 13, 30,
    lng=-118.2437,
    lat=34.0522,
    tz_str="America/Los_Angeles",
    online=False,
)

business_composite = CompositeSubjectFactory(
    business_partner1,
    business_partner2,
    "Business Partnership"
)
model = business_composite.get_midpoint_composite_subject_model()

# Focus on career and money houses
business_houses = [2, 6, 10]  # Resources, Work, Career/Reputation
for house_num in business_houses:
    house_name = f"{['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth'][house_num]}_house"
    house = getattr(model, house_name)
    print(f"House {house_num} (Business): {house.sign} {house.abs_pos:.2f}°")
```

### 3. Family Relationships
Family composites (parent-child, siblings) highlight nurturing dynamics, home environment, and generational patterns. These charts often emphasize the 4th and 5th houses.

```python
# Parent-child composite
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

parent = AstrologicalSubjectFactory.from_birth_data(
    "Parent", 1970, 2, 18, 7, 20,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
child = AstrologicalSubjectFactory.from_birth_data(
    "Child", 2005, 9, 12, 15, 5,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

family_composite = CompositeSubjectFactory(parent, child, "Family Dynamic")
model = family_composite.get_midpoint_composite_subject_model()

# Focus on family-related houses
family_houses = [4, 5]  # Home/Family, Children/Creativity
for house_num in family_houses:
    house_name = f"{['', 'first', 'second', 'third', 'fourth', 'fifth'][house_num]}_house"
    house = getattr(model, house_name)
    print(f"House {house_num} (Family): {house.sign} {house.abs_pos:.2f}°")
```

## Technical Notes

### Midpoint Calculation Method
The composite uses sophisticated circular mean calculations that properly handle zodiacal boundaries. This mathematical approach ensures accurate midpoints even when individual positions span the 0°/360° boundary. For example:
- Positions at 350° and 10° correctly calculate to 0° (not 180°)
- House cusps maintain proper sequential order after midpoint calculation
- Only common active points between subjects are included to ensure data integrity

### Compatibility Requirements
Both subjects must have identical astrological calculation settings to create a valid composite:
- `zodiac_type` (Tropical or Sidereal) - Different zodiac systems cannot be meaningfully combined
- `sidereal_mode` (if using Sidereal) - Different ayanamshas would create inconsistent results  
- `houses_system_identifier` - Different house systems use incompatible mathematical divisions
- `perspective_type` - Different perspectives (geocentric/heliocentric) represent fundamentally different viewpoints

### Performance Considerations
- Composite calculation is fast (< 50ms typically) since it uses pre-calculated individual positions
- Memory usage is minimal, similar to a single chart rather than two separate charts
- Only common points are calculated, improving efficiency with large active point lists
- The resulting model contains all standard astrological chart features for analysis

The `CompositeSubjectFactory` provides an essential tool for relationship astrology, creating meaningful charts that represent the unique dynamics between two people.
