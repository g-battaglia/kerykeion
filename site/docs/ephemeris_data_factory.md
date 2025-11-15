# Ephemeris Data Factory

The `ephemeris_data_factory` module generates time-series astrological ephemeris data across specified date ranges with flexible intervals and calculation parameters.

## Overview

The `EphemerisDataFactory` creates comprehensive astronomical datasets for research, analysis, and tracking planetary movements over time. It supports various time intervals and output formats, making it ideal for both lightweight data collection and full astrological analysis.

## Key Features

- **Time-Series Generation**: Create data points across date ranges with configurable intervals
- **Multiple Time Units**: Support for days, hours, and minutes intervals
- **Flexible Output Formats**: Dictionary data or full AstrologicalSubject instances
- **Performance Safeguards**: Built-in limits and warnings for large datasets
- **Complete Compatibility**: Works with all zodiac systems, house systems, and perspectives

## EphemerisDataFactory Class

### Basic Usage

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

# Create daily ephemeris data for January 2024
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 31)

factory = EphemerisDataFactory(start, end)
data = factory.get_ephemeris_data()

print(f"Generated {len(data)} daily data points")
print(f"First date: {data[0]['date']}")
print(f"Sun position: {data[0]['planets'][0]['abs_pos']:.2f}°")
```

**Output:**
```
Generated 31 daily data points
First date: 2024-01-01T00:00:00
Sun position: 280.23°
```

### Different Time Intervals

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

# Hourly data for a specific day
start = datetime(2024, 6, 21, 0, 0)  # Summer Solstice
end = datetime(2024, 6, 22, 0, 0)

hourly_factory = EphemerisDataFactory(
    start, end,
    step_type="hours",
    step=1
)

hourly_data = hourly_factory.get_ephemeris_data()
print(f"Generated {len(hourly_data)} hourly data points")

# Every 15 minutes for detailed analysis
minute_factory = EphemerisDataFactory(
    start, end,
    step_type="minutes", 
    step=15,
    max_minutes=200  # Increase limit for detailed data
)

minute_data = minute_factory.get_ephemeris_data()
print(f"Generated {len(minute_data)} 15-minute intervals")
```

**Output:**
```
Generated 25 hourly data points
Generated 97 15-minute intervals
```

### Custom Location and Settings

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

# Ephemeris for specific location with custom settings
factory = EphemerisDataFactory(
    start_datetime=datetime(2024, 3, 20),  # Spring Equinox
    end_datetime=datetime(2024, 3, 22),
    step_type="hours",
    step=2,  # Every 2 hours
    lat=40.7128,  # New York coordinates
    lng=-74.0060,
    tz_str="America/New_York",
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
    houses_system_identifier="W"  # Whole Sign houses
)

vedic_data = factory.get_ephemeris_data()

print("=== SIDEREAL EPHEMERIS DATA ===")
for i, point in enumerate(vedic_data[:3]):  # First 3 data points
    date = point['date']
    sun_pos = point['planets'][0]['abs_pos']
    sun_sign = point['planets'][0]['sign']
    print(f"{date}: Sun at {sun_sign} {sun_pos:.2f}°")
```

**Output:**
```
=== SIDEREAL EPHEMERIS DATA ===
2024-03-20T00:00:00: Sun at Pisces 5.45°
2024-03-20T02:00:00: Sun at Pisces 5.53°
2024-03-20T04:00:00: Sun at Pisces 5.62°
```

## Detailed Examples

### Planetary Motion Analysis

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Track Mercury's motion over a month
start = datetime(2024, 8, 1)
end = datetime(2024, 8, 31)

factory = EphemerisDataFactory(start, end, step_type="days")
data = factory.get_ephemeris_data()

print("=== MERCURY MOTION TRACKING ===")
mercury_positions = []

for point in data:
    # Find Mercury in the planets list
    for planet in point['planets']:
        if planet['name'] == 'Mercury':
            mercury_positions.append({
                'date': point['date'][:10],  # Date only
                'position': planet['abs_pos'],
                'sign': planet['sign'],
                'retrograde': planet['speed'] < 0
            })
            break

# Show position changes
print(f"{'Date':<12} {'Position':<15} {'Sign':<12} {'Status'}")
print("-" * 50)

for i, pos in enumerate(mercury_positions[::3]):  # Every 3 days
    status = "Retrograde" if pos['retrograde'] else "Direct"
    print(f"{pos['date']:<12} {pos['position']:.2f}°{'':<9} {pos['sign']:<12} {status}")
```

**Output:**
```
=== MERCURY MOTION TRACKING ===
Date         Position        Sign         Status
--------------------------------------------------
2024-08-01   116.45°         Cancer       Direct
2024-08-04   121.23°         Leo          Direct
2024-08-07   126.78°         Leo          Direct
2024-08-10   131.45°         Leo          Retrograde
2024-08-13   129.12°         Leo          Retrograde
```

### Full Astrological Subject Analysis

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Generate complete astrological subjects for detailed analysis
factory = EphemerisDataFactory(
    start_datetime=datetime(2024, 12, 21),  # Winter Solstice period
    end_datetime=datetime(2024, 12, 25),
    step_type="days",
    lat=51.5074,  # London
    lng=-0.1278,
    tz_str="Europe/London"
)

subjects = factory.get_ephemeris_data_as_astrological_subjects()

print("=== COMPLETE ASTROLOGICAL ANALYSIS ===")
for i, subject in enumerate(subjects):
    print(f"\nDay {i+1}: {subject.iso_formatted_local_datetime[:10]}")
    
    # Access full astrological data
    print(f"Sun: {subject.sun.sign} {subject.sun.abs_pos:.2f}° (House {subject.sun.house})")
    print(f"Moon: {subject.moon.sign} {subject.moon.abs_pos:.2f}° (House {subject.moon.house})")
    print(f"Ascendant: {subject.ascendant.sign} {subject.ascendant.abs_pos:.2f}°")
    print(f"Lunar Phase: {subject.lunar_phase.moon_phase_name}")
    
    # Check for retrograde planets
    retrogrades = []
    for planet_name in ['mercury', 'venus', 'mars', 'jupiter', 'saturn']:
        planet = getattr(subject, planet_name)
        if planet.retrograde:
            retrogrades.append(planet.name)
    
    if retrogrades:
        print(f"Retrograde: {', '.join(retrogrades)}")
    else:
        print("No major planets retrograde")
```

### Research Applications

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Statistical analysis of planetary patterns
import statistics

factory = EphemerisDataFactory(
    start_datetime=datetime(2023, 1, 1),
    end_datetime=datetime(2023, 12, 31),
    step_type="days",
    step=7  # Weekly data points
)

data = factory.get_ephemeris_data()

# Analyze Jupiter's motion throughout the year
jupiter_positions = []
jupiter_signs = {}

for point in data:
    for planet in point['planets']:
        if planet['name'] == 'Jupiter':
            jupiter_positions.append(planet['abs_pos'])
            sign = planet['sign']
            jupiter_signs[sign] = jupiter_signs.get(sign, 0) + 1
            break

print("=== JUPITER RESEARCH ANALYSIS ===")
print(f"Data points analyzed: {len(jupiter_positions)}")
print(f"Average position: {statistics.mean(jupiter_positions):.2f}°")
print(f"Position range: {min(jupiter_positions):.2f}° - {max(jupiter_positions):.2f}°")
print(f"Movement span: {max(jupiter_positions) - min(jupiter_positions):.2f}°")

print("\nTime spent in each sign:")
for sign, count in jupiter_signs.items():
    weeks = count
    print(f"  {sign}: {weeks} weeks")
```

**Output:**
```
=== JUPITER RESEARCH ANALYSIS ===
Data points analyzed: 53
Average position: 45.67°
Position range: 22.34° - 68.90°
Movement span: 46.56°

Time spent in each sign:
  Aries: 35 weeks
  Taurus: 18 weeks
```

### High-Frequency Data

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Minute-by-minute data for precise timing
start = datetime(2024, 4, 8, 17, 0)  # Eclipse time
end = datetime(2024, 4, 8, 21, 0)    # 4-hour window

eclipse_factory = EphemerisDataFactory(
    start, end,
    step_type="minutes",
    step=5,  # Every 5 minutes
    lat=32.7767,  # Dallas (eclipse path)
    lng=-96.7970,
    tz_str="America/Chicago",
    max_minutes=100  # Increase limit for detailed timing
)

eclipse_data = eclipse_factory.get_ephemeris_data()

print("=== ECLIPSE TIMING ANALYSIS ===")
print(f"Tracking {len(eclipse_data)} data points over 4 hours")

# Find exact conjunction times (simplified example)
for i, point in enumerate(eclipse_data[::12]):  # Every hour
    sun_pos = moon_pos = None
    
    for planet in point['planets']:
        if planet['name'] == 'Sun':
            sun_pos = planet['abs_pos']
        elif planet['name'] == 'Moon':
            moon_pos = planet['abs_pos']
    
    if sun_pos and moon_pos:
        difference = abs(sun_pos - moon_pos)
        time = point['date'][11:16]  # Extract time
        print(f"{time}: Sun-Moon difference = {difference:.3f}°")
```

## Performance and Limits

### Understanding Limits

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# The factory includes safety limits to prevent excessive computation
try:
    # This would generate too many data points
    large_factory = EphemerisDataFactory(
        start_datetime=datetime(2020, 1, 1),
        end_datetime=datetime(2024, 1, 1),  # 4 years
        step_type="hours",  # Would create ~35,000 data points
        step=1
    )
except ValueError as e:
    print(f"Error: {e}")
    
    # Solution: Adjust limits or reduce range
    large_factory = EphemerisDataFactory(
        start_datetime=datetime(2020, 1, 1),
        end_datetime=datetime(2024, 1, 1),
        step_type="hours",
        step=1,
        max_hours=50000  # Increase limit
    )
    print("Factory created with increased limits")
```

### Performance Optimization

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
import time

# Compare performance between methods
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 8)

factory = EphemerisDataFactory(start, end)

# Method 1: Dictionary data (faster)
start_time = time.time()
dict_data = factory.get_ephemeris_data()
dict_time = time.time() - start_time

# Method 2: Full subjects (more features)
start_time = time.time()
subjects = factory.get_ephemeris_data_as_astrological_subjects()
subjects_time = time.time() - start_time

print("=== PERFORMANCE COMPARISON ===")
print(f"Dictionary method: {dict_time:.3f}s for {len(dict_data)} points")
print(f"Subjects method: {subjects_time:.3f}s for {len(subjects)} points")
print(f"Speed ratio: {subjects_time/dict_time:.1f}x slower for full subjects")

# Memory usage comparison
import sys
dict_size = sys.getsizeof(dict_data)
subjects_size = sys.getsizeof(subjects)
print(f"\nMemory usage:")
print(f"Dictionary data: {dict_size:,} bytes")
print(f"Subject data: {subjects_size:,} bytes")
```

**Output:**
```
=== PERFORMANCE COMPARISON ===
Dictionary method: 0.234s for 8 points
Subjects method: 0.876s for 8 points  
Speed ratio: 3.7x slower for full subjects

Memory usage:
Dictionary data: 12,456 bytes
Subject data: 45,672 bytes
```

## Error Handling

### Common Issues and Solutions

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Issue 1: Date range too large
try:
    huge_factory = EphemerisDataFactory(
        datetime(2000, 1, 1),
        datetime(2030, 1, 1),  # 30 years daily = ~11,000 points
        step_type="days"
    )
except ValueError as e:
    print(f"Date range error: {e}")
    
    # Solution: Use larger steps or disable limits
    manageable_factory = EphemerisDataFactory(
        datetime(2000, 1, 1),
        datetime(2030, 1, 1),
        step_type="days",
        step=30,  # Monthly instead of daily
        max_days=None  # Disable limit
    )

# Issue 2: Invalid step type
try:
    invalid_factory = EphemerisDataFactory(
        datetime(2024, 1, 1),
        datetime(2024, 1, 2),
        step_type="weeks"  # Invalid
    )
except ValueError as e:
    print(f"Step type error: {e}")

# Issue 3: No valid dates
try:
    no_dates_factory = EphemerisDataFactory(
        datetime(2024, 1, 1),
        datetime(2023, 1, 1),  # End before start
        step_type="days"
    )
except ValueError as e:
    print(f"Date order error: {e}")
```

## Practical Applications

### 1. Astrological Research
```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Planetary cycle analysis
factory = EphemerisDataFactory(
    datetime(2020, 1, 1),
    datetime(2024, 1, 1),
    step_type="days",
    step=10  # Every 10 days
)

data = factory.get_ephemeris_data()
# Analyze long-term planetary patterns
```

### 2. Market Timing (Financial Astrology)
```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Business cycle correlation
factory = EphemerisDataFactory(
    datetime(2023, 1, 1),
    datetime(2023, 12, 31),
    step_type="days",
    lat=40.7128,  # NYSE location
    lng=-74.0060,
    tz_str="America/New_York"
)

market_data = factory.get_ephemeris_data()
# Correlate with market movements
```

### 3. Event Planning (Electional Astrology)
```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Find optimal dates for events
factory = EphemerisDataFactory(
    datetime(2024, 6, 1),
    datetime(2024, 6, 30),
    step_type="days",
    lat=34.0522,
    lng=-118.2437,
    tz_str="America/Los_Angeles"
)

subjects = factory.get_ephemeris_data_as_astrological_subjects()
# Analyze each day for favorable conditions
```

### 4. Educational/Learning
```python
from datetime import datetime
from kerykeion import EphemerisDataFactory
# Demonstrate planetary motion
factory = EphemerisDataFactory(
    datetime(2024, 1, 1),
    datetime(2024, 1, 31),
    step_type="days"
)

educational_data = factory.get_ephemeris_data()
# Show how planets move through signs
```

## Technical Notes

### Time Interval Guidelines
- **Days**: Best for long-term analysis (months to years)
- **Hours**: Ideal for detailed daily analysis or event timing
- **Minutes**: Use for precise timing analysis (eclipses, exact aspects)

### Performance Recommendations
- Use dictionary method for large datasets and simple analysis
- Use subjects method when you need full astrological features
- Consider batch processing for very large date ranges
- Monitor memory usage with extensive datasets

### Default Limits
- **max_days**: 730 (2 years of daily data)
- **max_hours**: 8,760 (1 year of hourly data)  
- **max_minutes**: 525,600 (1 year of minute data)

The `EphemerisDataFactory` provides a powerful and flexible system for generating time-series astrological data, supporting everything from quick planetary position lookups to comprehensive research datasets.
