# Aspects Module

Calculates astrological aspects (angular relationships) between celestial points in natal charts and between two charts for synastry analysis. Essential for understanding planetary interactions and compatibility in astrological analysis.

The module provides a unified **AspectsFactory** class with two main methods: **single_chart_aspects()** for individual chart analysis and **dual_chart_aspects()** for relationship compatibility analysis between two charts.

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

## Single Chart Aspects Analysis

Analyzes aspects within a single birth chart to understand internal planetary dynamics and personality patterns.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory

# Create natal chart
person = AstrologicalSubjectFactory.from_birth_data("John", 1990, 6, 15, 12, 0, "London", "GB")

# Generate single chart aspects analysis
chart_aspects = AspectsFactory.single_chart_aspects(person)

# Access all aspects
print(f"Total aspects found: {len(chart_aspects.all_aspects)}")
print(f"Relevant aspects: {len(chart_aspects.relevant_aspects)}")

# Examine specific aspects
for aspect in chart_aspects.relevant_aspects[:5]:
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

## Dual Chart Aspects Analysis

Analyzes aspects between two charts for relationship compatibility and planetary interactions between partners.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory

# Create two charts for comparison
person_a = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 5, 15, 10, 30, "Rome", "IT")
person_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 23, 14, 45, "Milan", "IT")

# Generate dual chart analysis
dual_aspects = AspectsFactory.dual_chart_aspects(person_a, person_b)

# Access synastry aspects
print(f"Total synastry aspects: {len(dual_aspects.all_aspects)}")
print(f"Relevant synastry aspects: {len(dual_aspects.relevant_aspects)}")

# Examine relationship aspects
for aspect in dual_aspects.relevant_aspects[:5]:
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
from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory

person = AstrologicalSubjectFactory.from_birth_data("John", 1990, 6, 15, 12, 0, "London", "GB")
person_a = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 5, 15, 10, 30, "Rome", "IT")
person_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 23, 14, 45, "Milan", "IT")

personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]

# Focus on personal planets only
personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
chart_aspects = AspectsFactory.single_chart_aspects(person, active_points=personal_planets)

# Traditional planets for relationship analysis
traditional_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
dual_aspects = AspectsFactory.dual_chart_aspects(person_a, person_b, active_points=traditional_planets)

# Check specific planet interactions
venus_aspects = []
for aspect in dual_aspects.relevant_aspects:
    if "Venus" in [aspect.p1_name, aspect.p2_name]:
        venus_aspects.append(aspect)

print(f"Venus aspects in synastry: {len(venus_aspects)}")
for aspect in venus_aspects:
    print(f"{aspect.p1_owner}'s {aspect.p1_name} {aspect.aspect} {aspect.p2_owner}'s {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
```

## Custom Aspect Configuration

Configure which aspect types to calculate and their orb tolerances, including minor aspects for detailed analysis.

```python
from kerykeion.kr_types.kr_models import ActiveAspect
from kerykeion.aspects import AspectsFactory
from kerykeion import AstrologicalSubjectFactory

# Define custom aspects with specific orbs
custom_aspects = [
    ActiveAspect(name="conjunction", orb=8),
    ActiveAspect(name="opposition", orb=8),
    ActiveAspect(name="trine", orb=6),
    ActiveAspect(name="square", orb=6),
    ActiveAspect(name="sextile", orb=4)
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
a_person = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 5, 15, 10, 30, "Rome", "IT")
b_person = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 23, 14, 45, "Milan", "IT")

chart_aspects = AspectsFactory.single_chart_aspects(a_person, active_aspects=all_aspects)
dual_aspects = AspectsFactory.dual_chart_aspects(b_person, a_person, active_aspects=custom_aspects)

print("Single Chart Aspects for Alice:")
print(chart_aspects)

print("\nDual Chart Aspects between Alice and Bob:")
print(dual_aspects)
```

## Data Access and Analysis

The aspect models provide detailed information for comprehensive analysis.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory

chart_aspects = AspectsFactory.single_chart_aspects(
    AstrologicalSubjectFactory.from_birth_data("John", 1990, 6, 15, 12, 0, "London", "GB")
)

# Access comprehensive aspect data
aspect = chart_aspects.relevant_aspects[0]
print(f"Aspect details:")
print(f"  Planets: {aspect.p1_name} {aspect.aspect} {aspect.p2_name}")
print(f"  Orb: {aspect.orbit:.2f}°")
print(f"  Aspect degrees: {aspect.aspect_degrees}°")
print(f"  Planet positions: {aspect.p1_abs_pos:.2f}° - {aspect.p2_abs_pos:.2f}°")

# Group aspects by type for analysis
aspect_types = {}
for aspect in chart_aspects.relevant_aspects:
    aspect_type = aspect.aspect
    if aspect_type not in aspect_types:
        aspect_types[aspect_type] = []
    aspect_types[aspect_type].append(aspect)

print("Aspects by type:")
for aspect_type, aspects in aspect_types.items():
    print(f"{aspect_type}: {len(aspects)} aspects")

# Export data for further analysis
import json
aspects_data = [aspect.model_dump() for aspect in chart_aspects.relevant_aspects]
with open("chart_aspects.json", "w") as f:
    json.dump(aspects_data, f, indent=2)
```

Each aspect result includes detailed information:
- `p1_name` / `p2_name`: Names of the aspected points
- `p1_owner` / `p2_owner`: Chart owners (same for single chart, different for dual chart)
- `aspect`: Type of aspect (Conjunction, Trine, etc.)
- `orbit`: Orb difference from exact aspect
- `aspect_degrees`: Exact degrees of the aspect type
- `p1_abs_pos` / `p2_abs_pos`: Absolute positions of the points

Example JSON output for a dual chart aspect:
```json
[
  {
    "p1_name": "Sun",
    "p1_owner": "John",
    "p1_abs_pos": 84.08977083584041,
    "p2_name": "Mars",
    "p2_owner": "John",
    "p2_abs_pos": 11.011355780195629,
    "aspect": "quintile",
    "orbit": 1.0784150556447827,
    "aspect_degrees": 72,
    "diff": 73.07841505564478,
    "p1": 0,
    "p2": 4
  },
  [...]
]
```

---

*This module is part of the Kerykeion astrological framework.*

## Use Cases

- **Single Chart Analysis**: Understand personality patterns and internal dynamics in natal, return, and composite charts
- **Relationship Compatibility**: Analyze planetary interactions between partners using dual chart analysis
- **Transit Analysis**: Compare current planetary positions with natal chart using dual chart methods
- **Psychological Astrology**: Explore psychological patterns through aspect analysis
- **Predictive Astrology**: Assess timing and influence of planetary cycles

## Integration with Other Modules

This module works complementary with other Kerykeion modules:

- **House Comparison**: Use together for complete synastry analysis - aspects show how planets interact, house comparison shows where energies are activated
- **Charts Module**: Aspects can be visualized in chart drawings with aspect lines and orb indicators
- **Transits**: Calculate current planetary aspects to natal positions for timing analysis

For house overlays and life area activations, refer to the `HouseComparisonFactory` module documentation.
