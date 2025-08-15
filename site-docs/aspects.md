# Aspects Module

Calculates astrological aspects (angular relationships) between celestial points in natal charts and between two charts for synastry analysis. Essential for understanding planetary interactions and compatibility in astrological analysis.

The module provides two core factory classes: **NatalAspectsFactory** for single chart analysis and **SynastryAspectsFactory** for relationship compatibility analysis between two charts.

## How It Works

Aspects are geometric relationships between planets and points in astrological charts, measured in degrees. The module calculates these angular distances and determines which aspects are formed based on traditional astrological orb tolerances.

**Major Aspects Calculated:**
- Conjunction (0°)
- Opposition (180°)
- Trine (120°)
- Square (90°)
- Sextile (60°)

**Minor Aspects Available:**
- Semi-sextile (30°)
- Semi-square (45°)
- Quintile (72°)
- Sesquiquadrate (135°)
- Biquintile (144°)
- Quincunx/Inconjunct (150°)

Each aspect includes orb analysis (how close to exact the aspect is) and applies stricter orb limits for chart axes (Ascendant, Midheaven, Descendant, IC).

## Natal Aspects Analysis

Analyzes aspects within a single birth chart to understand internal planetary dynamics and personality patterns.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import NatalAspectsFactory

# Create natal chart
person = AstrologicalSubjectFactory.from_birth_data("John", 1990, 6, 15, 12, 0, "London", "GB")

# Generate natal aspects analysis
natal_aspects = NatalAspectsFactory.from_subject(person)

# Access all aspects
print(f"Total aspects found: {len(natal_aspects.all_aspects)}")
print(f"Relevant aspects: {len(natal_aspects.relevant_aspects)}")

# Examine specific aspects
for aspect in natal_aspects.relevant_aspects[:5]:
    print(f"{aspect.p1_name} {aspect.aspect} {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
```

**Output example:**
```
Total aspects found: 38
Relevant aspects: 38
Sun quintile Mars (orb: 1.08°)
Moon sextile Venus (orb: 3.93°)
Moon trine Jupiter (orb: 1.08°)
Moon sextile Uranus (orb: 6.63°)
Moon sextile Neptune (orb: 1.08°)
```

## Synastry Aspects Analysis

Analyzes aspects between two charts for relationship compatibility and planetary interactions between partners.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import SynastryAspectsFactory

# Create two charts for comparison
person_a = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 5, 15, 10, 30, "Rome", "IT")
person_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 23, 14, 45, "Milan", "IT")

# Generate synastry analysis
synastry = SynastryAspectsFactory.from_subjects(person_a, person_b)

# Access synastry aspects
print(f"Total synastry aspects: {len(synastry.all_aspects)}")
print(f"Relevant synastry aspects: {len(synastry.relevant_aspects)}")

# Examine relationship aspects
for aspect in synastry.relevant_aspects[:5]:
    print(f"{aspect.p1_owner}'s {aspect.p1_name} {aspect.aspect} {aspect.p2_owner}'s {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
```

**Output example:**
```
Total synastry aspects: 68
Relevant synastry aspects: 68
Alice's Sun trine Bob's Venus (orb: -4.26°)
Alice's Sun trine Bob's Jupiter (orb: -4.56°)
Alice's Sun trine Bob's Neptune (orb: 7.75°)
Alice's Sun opposition Bob's Pluto (orb: -3.95°)
Alice's Sun square Bob's Mean_Lilith (orb: 0.34°)
```

## Custom Point Selection

Specify which astrological points to include in aspect calculations for focused analysis or performance optimization.

```python
# Focus on personal planets only
personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
natal_aspects = NatalAspectsFactory.from_subject(person, active_points=personal_planets)

# Traditional planets for relationship analysis
traditional_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
synastry = SynastryAspectsFactory.from_subjects(person_a, person_b, active_points=traditional_planets)

# Check specific planet interactions
venus_aspects = []
for aspect in synastry.relevant_aspects:
    if "Venus" in [aspect.p1_name, aspect.p2_name]:
        venus_aspects.append(aspect)
        print(f"Venus aspect: {aspect.p1_owner}'s {aspect.p1_name} {aspect.aspect} {aspect.p2_owner}'s {aspect.p2_name}")
```

## Custom Aspect Configuration

Configure which aspect types to calculate and their orb tolerances, including minor aspects for detailed analysis.

```python
from kerykeion.kr_types.kr_models import ActiveAspect

# Define custom aspects with specific orbs
custom_aspects = [
    ActiveAspect(name="conjunction", orb=8.0),
    ActiveAspect(name="opposition", orb=8.0),
    ActiveAspect(name="trine", orb=6.0),
    ActiveAspect(name="square", orb=6.0),
    ActiveAspect(name="sextile", orb=4.0)
]

# Include all available aspects (major and minor) for comprehensive analysis
all_aspects = [
    ActiveAspect(name="conjunction", orb=10),
    ActiveAspect(name="opposition", orb=10),
    ActiveAspect(name="trine", orb=8),
    ActiveAspect(name="sextile", orb=6),
    ActiveAspect(name="square", orb=5),
    ActiveAspect(name="quintile", orb=1),
    ActiveAspect(name="semi-sextile", orb=1),
    ActiveAspect(name="semi-square", orb=1),
    ActiveAspect(name="sesquiquadrate", orb=1),
    ActiveAspect(name="biquintile", orb=1),
    ActiveAspect(name="quincunx", orb=1),
]

# Use custom aspects configuration
natal_aspects = NatalAspectsFactory.from_subject(person, active_aspects=all_aspects)
synastry = SynastryAspectsFactory.from_subjects(person_a, person_b, active_aspects=custom_aspects)
```

## Data Access and Analysis

The aspect models provide detailed information for comprehensive analysis.

```python
# Access comprehensive aspect data
aspect = natal_aspects.relevant_aspects[0]
print(f"Aspect details:")
print(f"  Planets: {aspect.p1_name} {aspect.aspect} {aspect.p2_name}")
print(f"  Orb: {aspect.orbit:.2f}°")
print(f"  Aspect degrees: {aspect.aspect_degrees}°")
print(f"  Planet positions: {aspect.p1_abs_pos:.2f}° - {aspect.p2_abs_pos:.2f}°")

# Group aspects by type for analysis
aspect_types = {}
for aspect in natal_aspects.relevant_aspects:
    aspect_type = aspect.aspect
    if aspect_type not in aspect_types:
        aspect_types[aspect_type] = []
    aspect_types[aspect_type].append(aspect)

print("Aspects by type:")
for aspect_type, aspects in aspect_types.items():
    print(f"{aspect_type}: {len(aspects)} aspects")

# Export data for further analysis
import json
aspects_data = [aspect.model_dump() for aspect in natal_aspects.relevant_aspects]
with open("natal_aspects.json", "w") as f:
    json.dump(aspects_data, f, indent=2)
```

Each aspect result includes detailed information:
- `p1_name` / `p2_name`: Names of the aspected points
- `p1_owner` / `p2_owner`: Chart owners (same for natal, different for synastry)
- `aspect`: Type of aspect (Conjunction, Trine, etc.)
- `orbit`: Orb difference from exact aspect
- `aspect_degrees`: Exact degrees of the aspect type
- `p1_abs_pos` / `p2_abs_pos`: Absolute positions of the points

---

*This module is part of the Kerykeion astrological framework.*

## Use Cases

- **Natal Chart Analysis**: Understand personality patterns and internal dynamics
- **Relationship Compatibility**: Analyze planetary interactions between partners
- **Transit Analysis**: Compare current planetary positions with natal chart
- **Psychological Astrology**: Explore psychological patterns through aspect analysis
- **Predictive Astrology**: Assess timing and influence of planetary cycles

## Integration with Other Modules

This module works complementary with other Kerykeion modules:

- **House Comparison**: Use together for complete synastry analysis - aspects show how planets interact, house comparison shows where energies are activated
- **Charts Module**: Aspects can be visualized in chart drawings with aspect lines and orb indicators
- **Transits**: Calculate current planetary aspects to natal positions for timing analysis

For house overlays and life area activations, refer to the `HouseComparisonFactory` module documentation.
