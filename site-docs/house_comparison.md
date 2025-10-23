# House Comparison Module

Analyzes placement of astrological points from one subject within another subject's house system. Essential for synastry analysis and chart comparisons.

The module performs **bidirectional analysis**: it calculates where each subject's planets fall in the other subject's houses, providing insights into how planetary energies interact with different life areas between two people.

## How It Works

The house comparison takes the planetary positions of one subject and projects them onto the house system of another subject. This reveals which areas of life (houses) are activated by each person's planetary influences in a relationship or comparison.

For example, if Person A's Venus falls in Person B's 7th house, it suggests that Person A's love nature activates Person B's partnership sector.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.house_comparison import HouseComparisonFactory

# Create two subjects for comparison
person_a = AstrologicalSubjectFactory.from_birth_data(
    "Person A", 1990, 5, 15, 10, 30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
person_b = AstrologicalSubjectFactory.from_birth_data(
    "Person B", 1992, 8, 23, 14, 45,
    lng=9.19,
    lat=45.4642,
    tz_str="Europe/Rome",
    online=False,
)

# Generate bidirectional house comparison
factory = HouseComparisonFactory(person_a, person_b)
comparison = factory.get_house_comparison()

# Show Person A points in Person B houses
print("Person A planets in Person B houses:")
for point in comparison.first_points_in_second_houses:
    print(f"Person A {point.point_name} in Person B {point.projected_house_name}")

print("\nPerson B planets in Person A houses:")
for point in comparison.second_points_in_first_houses:
    print(f"Person B {point.point_name} in Person A {point.projected_house_name}")
```

**Output example (Person A points in Person B houses):**
```
Person A Sun in Person B Sixth_House
Person A Moon in Person B Second_House
Person A Mercury in Person B Fifth_House
Person A Venus in Person B Fourth_House
Person A Mars in Person B Third_House
```

## Custom Points

You can specify which astrological points to analyze instead of using all available points. This is useful for focused analysis or performance optimization.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.house_comparison import HouseComparisonFactory

person_a = AstrologicalSubjectFactory.from_birth_data(
    "Person A", 1990, 5, 15, 10, 30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
person_b = AstrologicalSubjectFactory.from_birth_data(
    "Person B", 1992, 8, 23, 14, 45,
    lng=9.19,
    lat=45.4642,
    tz_str="Europe/Rome",
    online=False,
)

# Use specific points only - traditional planets
traditional_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
factory = HouseComparisonFactory(person_a, person_b, active_points=traditional_planets)
comparison = factory.get_house_comparison()

# Focus on personal planets for relationship analysis
personal_planets = ["Sun", "Moon", "Venus", "Mars"]
factory_personal = HouseComparisonFactory(person_a, person_b, active_points=personal_planets)
comparison_personal = factory_personal.get_house_comparison()

# Check specific planet placements
for point in comparison_personal.first_points_in_second_houses:
    if point.point_name == "Venus":
        print(f"Person A's Venus activates Person B's {point.projected_house_name}")
        print(f"Located at {point.point_degree}° {point.point_sign}")
```

## Data Access

The comparison results are organized in two directions, allowing you to see both perspectives of the relationship.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.house_comparison import HouseComparisonFactory

person_a = AstrologicalSubjectFactory.from_birth_data(
    "Person A", 1990, 5, 15, 10, 30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)
person_b = AstrologicalSubjectFactory.from_birth_data(
    "Person B", 1992, 8, 23, 14, 45,
    lng=9.19,
    lat=45.4642,
    tz_str="Europe/Rome",
    online=False,
)
comparison = HouseComparisonFactory(person_a, person_b).get_house_comparison()

# Access both directions of the analysis
person_a_in_b = comparison.first_points_in_second_houses  # Person A points in Person B houses
person_b_in_a = comparison.second_points_in_first_houses  # Person B points in Person A houses

# Group planets by house for easier analysis
house_activations = {}
for point in person_a_in_b:
    house = point.projected_house_name
    if house not in house_activations:
        house_activations[house] = []
    house_activations[house].append(point.point_name)

print("Person A planets grouped by Person B houses:")
for house, planets in house_activations.items():
    print(f"{house}: {', '.join(planets)}")

# Export all data to JSON for further analysis
json_data = comparison.model_dump_json(indent=2)
with open("house_comparison_results.json", "w") as f:
    f.write(json_data)
```

**Example output:**
```
Person A planets grouped by Person B houses:
Second_House: Moon, Jupiter
Third_House: Mars
Fourth_House: Venus
Fifth_House: Mercury
Sixth_House: Sun
Seventh_House: Saturn
```

Each point result includes detailed information:
- `point_name`: The astrological point (e.g., "Sun", "Moon")
- `projected_house_name`: The house where the point falls
- `point_degree`: Exact degree position
- `point_sign`: Zodiac sign of the point

---

*This module is part of the Kerykeion astrological framework.*

## Use Cases

- **Synastry Analysis**: Understand how partners influence each other's life areas
- **Composite Charts**: Analyze blended relationship dynamics  
- **Transit Analysis**: See how current planetary positions affect personal houses
- **Compatibility Studies**: Evaluate relationship potential through house overlays

## Synastry Integration

This module is complementary to `AspectsFactory` for complete synastry analysis. While house comparison reveals where planetary energies are activated in each person's life areas, dual chart aspects show how the planets interact with each other through geometric relationships.

For a comprehensive relationship analysis, use both modules together:
- **House Comparison**: Shows planetary placements and life area activations
- **Dual Chart Aspects**: Reveals planetary interactions and compatibility patterns

Refer to the `AspectsFactory` module documentation for details on aspect analysis.
