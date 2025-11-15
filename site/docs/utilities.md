# Utilities Module

The `utilities` module provides a comprehensive set of utility functions for astrological calculations, coordinate conversions, data management, and astronomical information processing. These functions support the fundamental operations of the entire Kerykeion framework.

## Overview

The utilities module contains essential functions for:
- **Coordinate conversions**: Between different coordinate systems
- **Circular calculations**: For handling astronomical angular positions
- **House management**: Determination of astrological houses
- **Lunar phases**: Calculation and representation of lunar phases
- **Temporal conversions**: Between different date systems
- **SVG processing**: For astrological chart manipulation

## Main Functions

### 1. Coordinate and Position Conversions

#### `get_number_from_name()`
Converts the name of an astrological point to its numerical identifier for Swiss Ephemeris calculations.

```python
from kerykeion.utilities import get_number_from_name

# Get identifier numbers for planets
sun_id = get_number_from_name("Sun")
moon_id = get_number_from_name("Moon")
mercury_id = get_number_from_name("Mercury")

print(f"Sun: {sun_id}")        # Output: Sun: 0
print(f"Moon: {moon_id}")       # Output: Moon: 1
print(f"Mercury: {mercury_id}") # Output: Mercury: 2

# Special points
mean_node_id = get_number_from_name("Mean_North_Lunar_Node")
chiron_id = get_number_from_name("Chiron")
lilith_id = get_number_from_name("Mean_Lilith")

print(f"Mean Node: {mean_node_id}")    # Output: Mean Node: 10
print(f"Chiron: {chiron_id}")          # Output: Chiron: 15
print(f"Mean Lilith: {lilith_id}")     # Output: Mean Lilith: 12

# Angles (for internal reference)
asc_id = get_number_from_name("Ascendant")
mc_id = get_number_from_name("Medium_Coeli")

print(f"Ascendant: {asc_id}")          # Output: Ascendant: 9900
print(f"Medium Coeli: {mc_id}")        # Output: Medium Coeli: 9902
```

#### `get_kerykeion_point_from_degree()`
Creates a KerykeionPointModel object from a degree position, automatically calculating zodiac sign, element, quality, and other properties.

```python
from kerykeion.utilities import get_kerykeion_point_from_degree

# Create an astrological point from degrees
sun_position = get_kerykeion_point_from_degree(
    degree=120.5,  # 0° Leo + 30.5°
    name="Sun",
    point_type="AstrologicalPoint"
)

print(f"=== SUN POSITION ===")
print(f"Name: {sun_position.name}")
print(f"Sign: {sun_position.sign}")
print(f"Position in sign: {sun_position.position:.2f}°")
print(f"Absolute position: {sun_position.abs_pos:.2f}°")
print(f"Element: {sun_position.element}")
print(f"Quality: {sun_position.quality}")
print(f"Emoji: {sun_position.emoji}")

# Examples with different degrees
examples = [
    (0, "Aries 0°"),
    (30, "Taurus 0°"),
    (90, "Cancer 0°"),
    (180, "Libra 0°"),
    (270, "Capricorn 0°"),
    (359.9, "Pisces 29.9°")
]

print(f"\n=== CONVERSION EXAMPLES ===")
for degree, description in examples:
    point = get_kerykeion_point_from_degree(degree, "Sun", "AstrologicalPoint")
    print(f"{degree:6.1f}° → {point.sign} {point.position:5.1f}° ({description})")
```

**Output:**
```
=== SUN POSITION ===
Name: Sun
Sign: Leo
Position in sign: 0.50°
Absolute position: 120.50°
Element: Fire
Quality: Fixed
Emoji: ♌️

=== CONVERSION EXAMPLES ===
   0.0° → Ari   0.0° (Aries 0°)
  30.0° → Tau   0.0° (Taurus 0°)
  90.0° → Can   0.0° (Cancer 0°)
 180.0° → Lib   0.0° (Libra 0°)
 270.0° → Cap   0.0° (Capricorn 0°)
 359.9° → Pis  29.9° (Pisces 29.9°)
```

### 2. Circular Calculations

#### `circular_mean()`
Calculates the circular mean of two angular positions, correctly handling the 0°/360° boundary.

```python
from kerykeion.utilities import circular_mean

# Examples of circular mean
print("=== CIRCULAR MEAN CALCULATIONS ===")

# Normal case (doesn't cross 0°)
pos1, pos2 = 10, 20
mean1 = circular_mean(pos1, pos2)
print(f"Mean of {pos1}° and {pos2}°: {mean1:.2f}°")

# Case that crosses 0° (problematic for arithmetic mean)
pos3, pos4 = 350, 10  # 350° and 10°
mean2 = circular_mean(pos3, pos4)
arithmetic_mean = (pos3 + pos4) / 2  # Wrong arithmetic mean
print(f"Mean of {pos3}° and {pos4}°:")
print(f"  Circular (correct): {mean2:.2f}°")
print(f"  Arithmetic (wrong): {arithmetic_mean:.2f}°")

# Other examples
test_cases = [
    (0, 180),      # Opposites
    (90, 270),     # Opposites
    (359, 1),      # Crosses boundary
    (340, 20),     # Crosses boundary
    (180, 180),    # Identical
]

print(f"\n--- TEST CASES ---")
for a, b in test_cases:
    result = circular_mean(a, b)
    print(f"Mean of {a:3d}° and {b:3d}°: {result:6.2f}°")
```

**Output:**
```
=== CIRCULAR MEAN CALCULATIONS ===
Mean of 10° and 20°: 15.00°
Mean of 350° and 10°:
  Circular (correct): 0.00°
  Arithmetic (wrong): 180.00°

--- TEST CASES ---
Mean of   0° and 180°: 270.00°
Mean of  90° and 270°:   0.00°
Mean of 359° and   1°:   0.00°
Mean of 340° and  20°:   0.00°
Mean of 180° and 180°: 180.00°
```

#### `is_point_between()`
Determines if a point lies between two other points on a circle, with special rules for boundaries.

```python
from kerykeion.utilities import is_point_between

print("=== POINT POSITION VERIFICATION ===")

# Basic test
start, end = 10, 50
test_points = [5, 10, 25, 50, 75]

print(f"Range: {start}° - {end}°")
for point in test_points:
    result = is_point_between(start, end, point)
    status = "YES" if result else "NO"
    print(f"  {point:2d}° is in range? {status}")

# Test crossing 0°
print(f"\nRange crossing 0°: 340° - 20°")
start2, end2 = 340, 20
test_points2 = [330, 340, 350, 0, 10, 20, 30]

for point in test_points2:
    try:
        result = is_point_between(start2, end2, point)
        status = "YES" if result else "NO"
        print(f"  {point:3d}° is in range? {status}")
    except Exception as e:
        print(f"  {point:3d}° → Error: {e}")

# Special rules
print(f"\n--- SPECIAL RULES ---")
print(f"Point equal to start point (340°): {is_point_between(340, 20, 340)}")  # True
print(f"Point equal to end point (20°): {is_point_between(340, 20, 20)}")      # False
```

**Output:**
```
=== POINT POSITION VERIFICATION ===
Range: 10° - 50°
   5° is in range? NO
  10° is in range? YES
  25° is in range? YES
  50° is in range? NO
  75° is in range? NO

Range crossing 0°: 340° - 20°
  330° is in range? NO
  340° is in range? YES
  350° is in range? YES
    0° is in range? YES
   10° is in range? YES
   20° is in range? NO
   30° is in range? NO

--- SPECIAL RULES ---
Point equal to start point (340°): True
Point equal to end point (20°): False
```

#### `circular_sort()`
Sorts degrees in clockwise circular progression starting from the first element.

```python
from kerykeion.utilities import circular_sort

print("=== CIRCULAR SORTING ===")

# List of degrees to sort
degrees = [100, 350, 50, 200, 10, 300]
print(f"Original degrees: {degrees}")

sorted_degrees = circular_sort(degrees)
print(f"Circularly sorted: {sorted_degrees}")

# Explanation of sorting
print(f"\nReference: {degrees[0]}° (first element)")
print("Clockwise distances from reference:")
for deg in sorted_degrees[1:]:  # Exclude reference
    distance = (deg - degrees[0]) % 360
    print(f"  {deg:3d}° → distance {distance:3.0f}°")

# Other examples
test_cases = [
    [0, 90, 180, 270],
    [180, 0, 270, 90],
    [359, 1, 180],
    [45, 315, 135, 225]
]

print(f"\n--- OTHER EXAMPLES ---")
for i, case in enumerate(test_cases, 1):
    result = circular_sort(case)
    print(f"Case {i}: {case} → {result}")
```

**Output:**
```
=== CIRCULAR SORTING ===
Original degrees: [100, 350, 50, 200, 10, 300]
Circularly sorted: [100, 200, 300, 350, 10, 50]

Reference: 100° (first element)
Clockwise distances from reference:
  200° → distance 100°
  300° → distance 200°
  350° → distance 250°
   10° → distance 270°
   50° → distance 310°

--- OTHER EXAMPLES ---
Case 1: [0, 90, 180, 270] → [0, 90, 180, 270]
Case 2: [180, 0, 270, 90] → [180, 270, 0, 90]
Case 3: [359, 1, 180] → [359, 1, 180]
Case 4: [45, 315, 135, 225] → [45, 135, 225, 315]
```

### 3. Astrological House Management

#### `get_planet_house()`
Determines which house a planet is in based on its position in degrees.

```python
from kerykeion.utilities import get_planet_house

# Example house cusps (in degrees)
house_cusps = [
    0,    # House 1 (Ascendant)
    30,   # House 2
    60,   # House 3
    90,   # House 4 (IC)
    120,  # House 5
    150,  # House 6
    180,  # House 7 (Descendant)
    210,  # House 8
    240,  # House 9
    270,  # House 10 (MC)
    300,  # House 11
    330   # House 12
]

print("=== HOUSE DETERMINATION ===")
print("House cusps:", house_cusps)

# Test planetary positions
planet_positions = [
    (15, "Sun at 15°"),
    (45, "Moon at 45°"),
    (95, "Mercury at 95°"),
    (165, "Venus at 165°"),
    (195, "Mars at 195°"),
    (285, "Jupiter at 285°"),
    (345, "Saturn at 345°"),
    (0, "Point exactly on Ascendant"),
    (359, "Point near Ascendant")
]

print(f"\n--- PLANETARY POSITIONS ---")
for position, description in planet_positions:
    try:
        house = get_planet_house(position, house_cusps)
        print(f"{description}: {house}")
    except Exception as e:
        print(f"{description}: Error - {e}")

# Example with a real astrological subject
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Test Subject",
    year=1990, month=6, day=15,
    hour=12, minute=0,
    city="Rome",
    nation="IT"
)

print(f"\n=== REAL HOUSES ===")
print(f"Subject: {subject.name}")
print(f"Real cusps: {[round(house.abs_pos, 1) for house in subject.houses_names_list]}")

# Determine house for each planet
planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn']
house_cusps_real = [house.abs_pos for house in subject.houses_names_list]

print(f"\n--- PLANETARY HOUSES ---")
for planet_name in planets:
    planet = getattr(subject, planet_name)
    house = get_planet_house(planet.abs_pos, house_cusps_real)
    print(f"{planet.name}: {planet.abs_pos:.1f}° → {house}")
```

#### `get_house_name()` and `get_house_number()`
Conversions between house numbers and names.

```python
from kerykeion.utilities import get_house_name, get_house_number

print("=== HOUSE CONVERSIONS ===")

# From number to name
print("Numbers → Names:")
for i in range(1, 13):
    name = get_house_name(i)
    print(f"  House {i:2d}: {name}")

print(f"\nNames → Numbers:")
house_names = [
    "First_House", "Second_House", "Third_House", "Fourth_House",
    "Fifth_House", "Sixth_House", "Seventh_House", "Eighth_House",
    "Ninth_House", "Tenth_House", "Eleventh_House", "Twelfth_House"
]

for name in house_names:
    number = get_house_number(name)
    print(f"  {name}: House {number}")

# Error testing
print(f"\n--- VALIDATION TESTS ---")
try:
    invalid_house = get_house_name(13)
except ValueError as e:
    print(f"House 13: {e}")

try:
    invalid_name = get_house_number("Invalid_House")
except ValueError as e:
    print(f"Invalid name: {e}")
```

### 4. Lunar Phase Calculations

#### `calculate_moon_phase()`
Calculates complete lunar phase information from Sun and Moon positions.

```python
from kerykeion.utilities import calculate_moon_phase

print("=== LUNAR PHASE CALCULATIONS ===")

# Examples of different lunar phases
lunar_examples = [
    (0, 0, "New Moon"),
    (90, 0, "First Quarter"),
    (180, 0, "Full Moon"),
    (270, 0, "Last Quarter"),
    (45, 0, "Waxing Crescent"),
    (135, 0, "Waxing Gibbous"),
    (225, 0, "Waning Gibbous"),
    (315, 0, "Waning Crescent")
]

for moon_pos, sun_pos, description in lunar_examples:
    phase_info = calculate_moon_phase(moon_pos, sun_pos)
    
    print(f"\n{description}:")
    print(f"  Moon: {moon_pos}°, Sun: {sun_pos}°")
    print(f"  Degrees of separation: {phase_info.degrees_between_s_m:.1f}°")
    print(f"  Moon phase: {phase_info.moon_phase}/28")
    print(f"  Phase name: {phase_info.moon_phase_name}")
    print(f"  Emoji: {phase_info.moon_emoji}")

# Calculation with real subject data
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Lunar Example",
    year=1990, month=6, day=15,
    hour=12, minute=0,
    city="Rome",
    nation="IT"
)

real_phase = calculate_moon_phase(subject.moon.abs_pos, subject.sun.abs_pos)

print(f"\n=== REAL LUNAR PHASE ===")
print(f"Subject: {subject.name}")
print(f"Date: {subject.iso_formatted_local_datetime}")
print(f"Sun: {subject.sun.abs_pos:.2f}° in {subject.sun.sign}")
print(f"Moon: {subject.moon.abs_pos:.2f}° in {subject.moon.sign}")
print(f"Separation: {real_phase.degrees_between_s_m:.2f}°")
print(f"Phase: {real_phase.moon_phase_name} {real_phase.moon_emoji}")
```

**Output:**
```
=== LUNAR PHASE CALCULATIONS ===

New Moon:
  Moon: 0°, Sun: 0°
  Degrees of separation: 0.0°
  Moon phase: 1/28
  Sun phase: 1/28
  Phase name: New Moon
  Emoji: 🌑

First Quarter:
  Moon: 90°, Sun: 0°
  Degrees of separation: 90.0°
  Moon phase: 8/28
  Sun phase: 8/28
  Phase name: First Quarter
  Emoji: 🌓

Full Moon:
  Moon: 180°, Sun: 0°
  Degrees of separation: 180.0°
  Moon phase: 15/28
  Sun phase: 15/28
  Phase name: Full Moon
  Emoji: 🌕

=== REAL LUNAR PHASE ===
Subject: Lunar Example
Date: 1990-06-15T12:00:00+02:00
Sun: 84.23° in Gem
Moon: 127.45° in Leo
Separation: 43.22°
Phase: Waxing Crescent 🌒
```

### 5. Temporal Conversions

#### `datetime_to_julian()` and `julian_to_datetime()`
Conversions between Python datetime objects and Julian Days for astronomical calculations.

```python
from kerykeion.utilities import datetime_to_julian, julian_to_datetime
from datetime import datetime

print("=== TEMPORAL CONVERSIONS ===")

# Significant dates
important_dates = [
    datetime(2000, 1, 1, 12, 0, 0),  # J2000.0
    datetime(1900, 1, 1, 0, 0, 0),   # Start of 20th century
    datetime(2024, 8, 15, 15, 30, 0), # Current date
    datetime(1990, 6, 15, 12, 0, 0),  # Example date
]

print("DateTime → Julian Day conversions:")
for dt in important_dates:
    jd = datetime_to_julian(dt)
    print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')} → JD {jd:.6f}")

# Reverse conversion test
print(f"\nReverse conversion test:")
test_date = datetime(2024, 8, 15, 18, 30, 45)
jd = datetime_to_julian(test_date)
converted_back = julian_to_datetime(jd)

print(f"Original:      {test_date}")
print(f"Julian Day:    {jd:.8f}")
print(f"Converted back: {converted_back}")
print(f"Difference:    {abs((test_date - converted_back).total_seconds()):.3f} seconds")

# Calculate age in Julian days
birth_date = datetime(1990, 6, 15, 12, 0, 0)
current_date = datetime.now()

birth_jd = datetime_to_julian(birth_date)
current_jd = datetime_to_julian(current_date)
age_days = current_jd - birth_jd

print(f"\n=== AGE CALCULATION ===")
print(f"Birth date: {birth_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Current date: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Age in Julian days: {age_days:.2f}")
print(f"Age in years: {age_days / 365.25:.2f}")
```

### 6. Astrological Data Utilities

#### `get_houses_list()` and `get_available_astrological_points_list()`
Extract ordered lists of houses and astrological points from a subject.

```python
from kerykeion.utilities import get_houses_list, get_available_astrological_points_list
from kerykeion import AstrologicalSubjectFactory

# Create a subject for the example
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Data Example",
    year=1990, month=6, day=15,
    hour=12, minute=0,
    city="Rome",
    nation="IT"
)

print("=== ASTROLOGICAL DATA EXTRACTION ===")

# Get houses list
houses = get_houses_list(subject)
print(f"Astrological houses ({len(houses)} total):")
for i, house in enumerate(houses, 1):
    print(f"  House {i:2d}: {house.abs_pos:6.2f}° in {house.sign}")

# Get active astrological points list
points = get_available_astrological_points_list(subject)
print(f"\nActive astrological points ({len(points)} total):")
for point in points:
    print(f"  {point.name:12s}: {point.abs_pos:6.2f}° in {point.sign}")

# Statistical analysis of positions
print(f"\n=== STATISTICAL ANALYSIS ===")
house_positions = [house.abs_pos for house in houses]
point_positions = [point.abs_pos for point in points]

print(f"Houses range: {min(house_positions):.2f}° - {max(house_positions):.2f}°")
print(f"Points range: {min(point_positions):.2f}° - {max(point_positions):.2f}°")

# Distribution by sign
from collections import Counter
point_signs = [point.sign for point in points]
sign_distribution = Counter(point_signs)

print(f"\nDistribution by sign:")
for sign, count in sorted(sign_distribution.items()):
    print(f"  {sign}: {count} point{'s' if count != 1 else ''}")
```

#### `find_common_active_points()`
Finds common astrological points between two lists.

```python
from kerykeion.utilities import find_common_active_points
from kerykeion.schemas import AstrologicalPoint

print("=== COMMON ASTROLOGICAL POINTS ===")

# Example lists
list1 = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter"
]

list2 = [
    "Moon",
    "Venus",
    "Mars",
    "Saturn",
    "Uranus",
    "Neptune"
]

print(f"List 1: {list1}")
print(f"List 2: {list2}")

common_points = find_common_active_points(list1, list2)
print(f"Common points: {common_points}")

# Practical example: compare configurations of two subjects
subject1 = AstrologicalSubjectFactory.from_birth_data(
    name="Subject 1", year=1990, month=6, day=15,
    hour=12, minute=0, city="Rome", nation="IT"
)

subject2 = AstrologicalSubjectFactory.from_birth_data(
    name="Subject 2", year=1985, month=3, day=21,
    hour=16, minute=30, city="Milan", nation="IT"
)

common_active = find_common_active_points(subject1.active_points, subject2.active_points)

print(f"\n--- SUBJECT COMPARISON ---")
print(f"{subject1.name} - Active points: {len(subject1.active_points)}")
print(f"{subject2.name} - Active points: {len(subject2.active_points)}")
print(f"Common points: {len(common_active)}")
print(f"Shared points: {[point.value for point in common_active]}")
```

### 7. System Utilities

#### `setup_logging()`
Configures the logging system for the application.

```python
from kerykeion.utilities import setup_logging
import logging

print("=== LOGGING CONFIGURATION ===")

# Configure different logging levels
log_levels = ["debug", "info", "warning", "error", "critical"]

for level in log_levels:
    print(f"\nConfiguration level: {level.upper()}")
    setup_logging(level)
    
    # Test each level
    logging.debug(f"Debug message - level {level}")
    logging.info(f"Info message - level {level}")
    logging.warning(f"Warning message - level {level}")
    logging.error(f"Error message - level {level}")
    logging.critical(f"Critical message - level {level}")

# Practical usage
print(f"\n=== PRACTICAL USAGE ===")
setup_logging("info")
logging.info("Logging system configured for INFO level")
logging.debug("This debug message will not appear")
logging.warning("This warning message will appear")
```

#### `check_and_adjust_polar_latitude()`
Adjusts latitude values for polar regions to prevent calculation errors.

```python
from kerykeion.utilities import check_and_adjust_polar_latitude

print("=== POLAR LATITUDE ADJUSTMENT ===")

# Test different latitudes
test_latitudes = [
    (90, "North Pole"),
    (70, "Beyond Arctic Circle"),
    (66, "Arctic Circle"),
    (60, "Normal northern latitude"),
    (0, "Equator"),
    (-60, "Normal southern latitude"),
    (-66, "Antarctic Circle"),
    (-70, "Beyond Antarctic Circle"),
    (-90, "South Pole")
]

print("Adjustments for house calculations:")
for lat, description in test_latitudes:
    adjusted = check_and_adjust_polar_latitude(lat)
    status = "ADJUSTED" if adjusted != lat else "OK"
    print(f"  {lat:4.0f}° ({description:32s}) → {adjusted:4.0f}° [{status}]")

# Example with real data
print(f"\n=== REAL EXAMPLES ===")
extreme_locations = [
    (78.2232, "Svalbard, Norway"),
    (-77.8419, "McMurdo Base, Antarctica"),
    (71.0486, "Barrow, Alaska"),
    (-54.8019, "Ushuaia, Argentina")
]

for lat, location in extreme_locations:
    adjusted = check_and_adjust_polar_latitude(lat)
    print(f"{location}:")
    print(f"  Original latitude: {lat:.4f}°")
    print(f"  Adjusted latitude: {adjusted:.4f}°")
    if adjusted != lat:
        print(f"  ⚠️  Adjusted to prevent house calculation errors")
    else:
        print(f"  ✓  No adjustment necessary")
```

### 8. SVG Processing

#### `inline_css_variables_in_svg()`
Replaces custom CSS variables with their values in SVG content.

```python
from kerykeion.utilities import inline_css_variables_in_svg

print("=== SVG PROCESSING ===")

# Example SVG with CSS variables
svg_content = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <style>
        :root {
            --primary-color: #ff6b6b;
            --secondary-color: #4ecdc4;
            --border-width: 2px;
            --font-size: 14px;
        }
        .circle {
            fill: var(--primary-color);
            stroke: var(--secondary-color);
            stroke-width: var(--border-width);
        }
        .text {
            font-size: var(--font-size);
            fill: var(--secondary-color, #000);
        }
    </style>
    <circle class="circle" cx="50" cy="50" r="30"/>
    <text class="text" x="50" y="55">Test</text>
    <rect fill="var(--primary-color)" stroke="var(--secondary-color)" 
          stroke-width="var(--border-width)" x="10" y="10" width="20" height="20"/>
</svg>
"""

print("Original SVG (first fragment):")
print(svg_content[:200] + "...")

# Process the SVG
processed_svg = inline_css_variables_in_svg(svg_content)

print(f"\nProcessed SVG (first fragment):")
print(processed_svg[:200] + "...")

# Verify that variables were replaced
print(f"\n=== SUBSTITUTION ANALYSIS ===")
original_vars = svg_content.count("var(")
processed_vars = processed_svg.count("var(")

print(f"CSS variables in original: {original_vars}")
print(f"CSS variables in processed: {processed_vars}")
print(f"Variables replaced: {original_vars - processed_vars}")

# Verify specific substitutions
substitutions = [
    ("var(--primary-color)", "#ff6b6b"),
    ("var(--secondary-color)", "#4ecdc4"),
    ("var(--border-width)", "2px"),
    ("var(--font-size)", "14px")
]

print(f"\n--- SPECIFIC SUBSTITUTIONS ---")
for original, expected in substitutions:
    found = original in processed_svg
    replaced = expected in processed_svg
    print(f"{original:25s} → {expected:10s} [{'❌' if found else '✅'}]")

# Verify removal of style blocks
style_blocks_original = svg_content.count("<style")
style_blocks_processed = processed_svg.count("<style")

print(f"\nOriginal <style> blocks: {style_blocks_original}")
print(f"Processed <style> blocks: {style_blocks_processed}")
print(f"Result: {'Style blocks removed ✅' if style_blocks_processed == 0 else 'Style blocks still present ❌'}")
```

## Integrated Usage Examples

### Complete Subject Analysis

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.utilities import *
from datetime import datetime

# Create a complete subject
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Complete Analysis",
    year=1990, month=6, day=15,
    hour=12, minute=0,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

print("=== COMPLETE ANALYSIS WITH UTILITIES ===")
print(f"Subject: {subject.name}")
print(f"Date: {subject.iso_formatted_local_datetime}")

# 1. House analysis
print(f"\n--- HOUSE ANALYSIS ---")
houses = get_houses_list(subject)
for i, house in enumerate(houses, 1):
    print(f"House {i:2d}: {house.abs_pos:6.2f}° in {house.sign}")

# 2. Astrological points analysis
print(f"\n--- ASTROLOGICAL POINTS ---")
points = get_available_astrological_points_list(subject)
for point in points:
    house_num = None
    house_cusps = [h.abs_pos for h in houses]
    try:
        house_name = get_planet_house(point.abs_pos, house_cusps)
        house_num = get_house_number(house_name)
    except:
        house_num = "?"
    
    print(f"{point.name:12s}: {point.abs_pos:6.2f}° {point.sign} (House {house_num})")

# 3. Lunar phase
print(f"\n--- LUNAR PHASE ---")
lunar_phase = calculate_moon_phase(subject.moon.abs_pos, subject.sun.abs_pos)
print(f"Sun-Moon separation: {lunar_phase.degrees_between_s_m:.2f}°")
print(f"Phase: {lunar_phase.moon_phase_name} {lunar_phase.moon_emoji}")
print(f"Phase number: {lunar_phase.moon_phase}/28")

# 4. Temporal conversions
print(f"\n--- TEMPORAL INFORMATION ---")
birth_jd = datetime_to_julian(datetime.fromisoformat(subject.iso_formatted_utc_datetime.replace('Z', '+00:00')))
current_jd = datetime_to_julian(datetime.now())
age_days = current_jd - birth_jd

print(f"Birth Julian Day: {birth_jd:.6f}")
print(f"Age in days: {age_days:.2f}")
print(f"Age in years: {age_days / 365.25:.2f}")

# 5. Circular calculations
print(f"\n--- CIRCULAR CALCULATIONS ---")
sun_moon_midpoint = circular_mean(subject.sun.abs_pos, subject.moon.abs_pos)
print(f"Sun-Moon midpoint: {sun_moon_midpoint:.2f}°")

# Convert to zodiac sign
midpoint_data = get_kerykeion_point_from_degree(
    sun_moon_midpoint, "Sun", "AstrologicalPoint"
)
print(f"Midpoint in sign: {midpoint_data.sign} {midpoint_data.position:.2f}°")

# 6. Distribution analysis
print(f"\n--- ELEMENTAL DISTRIBUTION ---")
elements = {}
for point in points:
    element = point.element
    elements[element] = elements.get(element, 0) + 1

for element, count in sorted(elements.items()):
    print(f"{element:5s}: {count} point{'s' if count != 1 else ''}")

print(f"\n--- QUALITY DISTRIBUTION ---")
qualities = {}
for point in points:
    quality = point.quality
    qualities[quality] = qualities.get(quality, 0) + 1

for quality, count in sorted(qualities.items()):
    print(f"{quality:8s}: {count} point{'s' if count != 1 else ''}")
```

## Technical Notes

### Circular Calculation Considerations
- All angular calculations correctly handle the 0°/360° boundary
- Circular functions use trigonometry to avoid wraparound errors
- Polar tolerances prevent errors in house calculations

### Precision and Validation
- Temporal conversions maintain microsecond precision
- Parameter validation prevents common errors
- Astronomical calculations use proven algorithms

### Framework Integration
- Utilities are designed to work with Kerykeion models
- Support all coordinate and zodiacal systems
- Optimized for performance in batch operations

The utilities module provides the mathematical and data management foundations for the entire Kerykeion framework, ensuring accurate calculations and robust handling of astrological data.
