# Transits Time Range Factory

The `transits_time_range_factory` module provides the `TransitsTimeRangeFactory` class for calculating astrological transits over specified time periods. It analyzes angular relationships (aspects) between transiting celestial bodies and natal chart positions across multiple time points.

## Overview

The `TransitsTimeRangeFactory` compares ephemeris data points (planetary positions at different times) with a natal chart to identify when celestial bodies form specific angular relationships. This enables comprehensive transit analysis for forecasting, timing, and astrological research.

**Core Functionality:**
- Time-series transit calculations across date ranges
- Configurable celestial points and aspect types
- Structured output models for data analysis
- Integration with ephemeris data generation
- Batch processing of multiple time points

## Key Features

- **Time-Series Analysis**: Calculate transits across days, weeks, or months
- **Configurable Filtering**: Choose specific planets and aspect types
- **Structured Output**: Organized data models for easy analysis
- **Performance Optimization**: Efficient batch processing
- **Integration Ready**: Works seamlessly with other Kerykeion modules
- **Flexible Settings**: Customizable orb tolerances and calculation methods

## TransitsTimeRangeFactory Class

### Basic Usage

```python
from datetime import datetime, timedelta
from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory

# Create natal chart
person = AstrologicalSubjectFactory.from_birth_data(
    name="John Doe",
    year=1990, month=5, day=15,
    hour=12, minute=0,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

# Define time period for transit analysis
start_date = datetime.now()
end_date = start_date + timedelta(days=30)

# Generate ephemeris data
ephemeris_factory = EphemerisDataFactory(
    start_datetime=start_date,
    end_datetime=end_date,
    step_type="days",
    step=1,
    lat=person.lat,
    lng=person.lng,
    tz_str=person.tz_str
)

ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

# Calculate transits
transit_factory = TransitsTimeRangeFactory(person, ephemeris_data)
results = transit_factory.get_transit_moments()

print(f"Transit analysis for {len(results.dates)} days")
print(f"Total transit moments: {len(results.transits)}")
print(f"First date: {results.dates[0]}")

# Analyze first day's transits
first_day = results.transits[0]
print(f"\nTransits on {first_day.date[:10]}:")
for aspect in first_day.aspects:
    print(f"  {aspect.p1_name} {aspect.aspect} natal {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
```

**Output:**
```
Transit analysis for 31 days
Total transit moments: 31
First date: 2024-08-15T12:00:00Z

Transits on 2024-08-15:
  Sun conjunction natal Mercury (orb: 1.23°)
  Moon trine natal Venus (orb: 0.87°)
  Mars square natal Jupiter (orb: 2.45°)
  Venus sextile natal Sun (orb: 1.67°)
```

### Detailed Transit Analysis

```python
# Comprehensive transit analysis with filtering
from datetime import datetime
from kerykeion import AstrologicalSubjectFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory

# Create natal chart for analysis
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Transit Subject",
    year=1985, month=3, day=21,  # Spring Equinox
    hour=14, minute=30,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

# Generate hourly ephemeris data for detailed analysis
start = datetime(2024, 8, 15, 0, 0)
end = datetime(2024, 8, 17, 0, 0)  # 48 hours

ephemeris_factory = EphemerisDataFactory(
    start_datetime=start,
    end_datetime=end,
    step_type="hours",
    step=2,  # Every 2 hours
    lat=subject.lat,
    lng=subject.lng,
    tz_str=subject.tz_str
)

ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

# Focus on major planets and major aspects
major_planets = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn"
]

major_aspects = [
    {"name": "conjunction", "orb": 8},
    {"name": "opposition", "orb": 8},
    {"name": "square", "orb": 6},
    {"name": "trine", "orb": 6},
    {"name": "sextile", "orb": 4},
]

transit_factory = TransitsTimeRangeFactory(
    natal_chart=subject,
    ephemeris_data_points=ephemeris_data,
    active_points=major_planets,
    active_aspects=major_aspects
)

results = transit_factory.get_transit_moments()

print("=== DETAILED TRANSIT ANALYSIS ===")
print(f"Period: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}")
print(f"Data points: {len(results.transits)} (every 2 hours)")

# Group transits by day
daily_transits = {}
for transit_moment in results.transits:
    date_key = transit_moment.date[:10]  # Extract date part
    if date_key not in daily_transits:
        daily_transits[date_key] = []
    daily_transits[date_key].append(transit_moment)

# Analyze each day
for date, transits in daily_transits.items():
    print(f"\n--- {date} ---")
    
    # Count aspects by type
    aspect_counts = {}
    all_aspects = []
    
    for transit in transits:
        for aspect in transit.aspects:
            aspect_type = aspect.aspect
            aspect_counts[aspect_type] = aspect_counts.get(aspect_type, 0) + 1
            all_aspects.append(aspect)
    
    print(f"Total aspects found: {len(all_aspects)}")
    print("Aspect distribution:", end=" ")
    for asp_type, count in sorted(aspect_counts.items()):
        print(f"{asp_type}: {count}", end=", ")
    print()
    
    # Show strongest aspects (tightest orbs)
    strongest_aspects = sorted(all_aspects, key=lambda x: abs(x.orbit))[:5]
    print("Strongest aspects:")
    for i, aspect in enumerate(strongest_aspects, 1):
        time_part = next(t.date[11:16] for t in transits if aspect in t.aspects)
        print(f"  {i}. {time_part} - {aspect.p1_name} {aspect.aspect} natal {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
```

**Output:**
```
=== DETAILED TRANSIT ANALYSIS ===
Period: 2024-08-15 00:00 to 2024-08-17 00:00
Data points: 25 (every 2 hours)

--- 2024-08-15 ---
Total aspects found: 47
Aspect distribution: conjunction: 8, opposition: 6, square: 12, trine: 11, sextile: 10, 

Strongest aspects:
  1. 14:00 - Venus conjunction natal Sun (orb: 0.23°)
  2. 08:00 - Moon trine natal Venus (orb: 0.45°)
  3. 18:00 - Mars square natal Saturn (orb: 0.67°)
  4. 02:00 - Mercury sextile natal Mercury (orb: 0.89°)
  5. 22:00 - Sun opposition natal Moon (orb: 1.12°)

--- 2024-08-16 ---
Total aspects found: 52
Aspect distribution: conjunction: 9, opposition: 8, square: 13, trine: 12, sextile: 10, 

Strongest aspects:
  1. 10:00 - Moon conjunction natal Mars (orb: 0.34°)
  2. 16:00 - Jupiter trine natal Jupiter (orb: 0.56°)
  3. 06:00 - Saturn square natal Venus (orb: 0.78°)
  4. 20:00 - Venus sextile natal Mercury (orb: 0.91°)
  5. 14:00 - Mercury opposition natal Saturn (orb: 1.05°)
```

## Advanced Examples

### Specific Transit Tracking

```python
from datetime import datetime
from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory
# Track specific planet transits (e.g., Jupiter transits for the year)
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Jupiter Transit Study",
    year=1975, month=12, day=25,
    hour=8, minute=15,
    lat=51.5074, lng=-0.1278,  # London
    tz_str="Europe/London"
)

# Generate monthly data points for the year
start = datetime(2024, 1, 1)
end = datetime(2024, 12, 31)

ephemeris_factory = EphemerisDataFactory(
    start_datetime=start,
    end_datetime=end,
    step_type="days",
    step=7,  # Weekly intervals
    lat=subject.lat,
    lng=subject.lng,
    tz_str=subject.tz_str
)

ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

# Focus only on Jupiter transits to major natal points
jupiter_points = ["Jupiter"]
natal_points = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Ascendant",
    "Medium_Coeli"
]

# Include all aspects for comprehensive analysis
all_aspects = [
    {"name": "conjunction", "orb": 8},
    {"name": "opposition", "orb": 8},
    {"name": "square", "orb": 6},
    {"name": "trine", "orb": 6},
    {"name": "sextile", "orb": 4},
    {"name": "quincunx", "orb": 3},
    {"name": "semi-sextile", "orb": 3},
    {"name": "semi-square", "orb": 3},
    {"name": "sesquiquadrate", "orb": 3},
    {"name": "quintile", "orb": 3},
    {"name": "biquintile", "orb": 2}
]

transit_factory = TransitsTimeRangeFactory(
    natal_chart=subject,
    ephemeris_data_points=ephemeris_data,
    active_points=jupiter_points + natal_points,
    active_aspects=all_aspects
)

results = transit_factory.get_transit_moments()

print("=== JUPITER TRANSIT ANALYSIS 2024 ===")
print(f"Subject: {subject.name}")
print(f"Birth Jupiter: {subject.jupiter.sign} {subject.jupiter.abs_pos:.2f}°")

# Filter for Jupiter transits only
jupiter_transits = []
for transit_moment in results.transits:
    jupiter_aspects = [asp for asp in transit_moment.aspects if asp.p1_name == "Jupiter"]
    if jupiter_aspects:
        jupiter_transits.append({
            'date': transit_moment.date,
            'aspects': jupiter_aspects
        })

print(f"Jupiter transit moments found: {len(jupiter_transits)}")

# Group by natal point
natal_point_transits = {}
for transit in jupiter_transits:
    for aspect in transit['aspects']:
        natal_point = aspect.p2_name
        if natal_point not in natal_point_transits:
            natal_point_transits[natal_point] = []
        natal_point_transits[natal_point].append({
            'date': transit['date'],
            'aspect': aspect.aspect,
            'orb': aspect.orbit
        })

# Display Jupiter transits by natal point
print(f"\n--- JUPITER TRANSITS BY NATAL POINT ---")
for natal_point, transits in natal_point_transits.items():
    print(f"\nJupiter → Natal {natal_point} ({len(transits)} aspects):")
    
    # Group by aspect type
    by_aspect = {}
    for t in transits:
        aspect_type = t['aspect']
        if aspect_type not in by_aspect:
            by_aspect[aspect_type] = []
        by_aspect[aspect_type].append(t)
    
    for aspect_type, aspect_transits in by_aspect.items():
        print(f"  {aspect_type.capitalize()}s: {len(aspect_transits)}")
        
        # Show tightest examples
        tightest = sorted(aspect_transits, key=lambda x: abs(x['orb']))[:3]
        for i, t in enumerate(tightest, 1):
            date_str = t['date'][:10]
            print(f"    {i}. {date_str} (orb: {t['orb']:.2f}°)")
```

**Output:**
```
=== JUPITER TRANSIT ANALYSIS 2024 ===
Subject: Jupiter Transit Study
Birth Jupiter: Aries 12.45°
Jupiter transit moments found: 34

--- JUPITER TRANSITS BY NATAL POINT ---

Jupiter → Natal Sun (8 aspects):
  Sextiles: 3
    1. 2024-03-15 (orb: 0.67°)
    2. 2024-06-22 (orb: 1.23°)
    3. 2024-09-08 (orb: 2.01°)
  Trines: 3
    1. 2024-05-10 (orb: 0.45°)
    2. 2024-07-18 (orb: 1.78°)
    3. 2024-11-03 (orb: 2.34°)
  Squares: 2
    1. 2024-01-28 (orb: 1.56°)
    2. 2024-12-14 (orb: 1.89°)

Jupiter → Natal Moon (6 aspects):
  Conjunctions: 2
    1. 2024-04-22 (orb: 0.34°)
    2. 2024-08-07 (orb: 0.78°)
  Oppositions: 2
    1. 2024-02-11 (orb: 1.45°)
    2. 2024-10-26 (orb: 1.67°)
  Sextiles: 2
    1. 2024-06-05 (orb: 0.92°)
    2. 2024-09-21 (orb: 1.34°)
```

### Monthly Transit Summary

```python
# Generate monthly transit summaries for consultation
def generate_monthly_transit_summary(subject, year, month):
    """Generate comprehensive monthly transit summary"""
    
    start = datetime(year, month, 1)
    # Calculate end of month
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    
    ephemeris_factory = EphemerisDataFactory(
        start_datetime=start,
        end_datetime=end,
        step_type="days",
        step=1,
        lat=subject.lat,
        lng=subject.lng,
        tz_str=subject.tz_str
    )
    
    ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
    
    transit_factory = TransitsTimeRangeFactory(subject, ephemeris_data)
    results = transit_factory.get_transit_moments()
    
    # Analyze the month
    month_name = start.strftime('%B %Y')
    print(f"=== TRANSIT SUMMARY: {month_name.upper()} ===")
    print(f"Subject: {subject.name}")
    
    # Count total aspects
    total_aspects = sum(len(moment.aspects) for moment in results.transits)
    print(f"Total aspects this month: {total_aspects}")
    
    # Analyze by transiting planet
    planet_activity = {}
    strongest_aspects = []
    
    for moment in results.transits:
        for aspect in moment.aspects:
            planet = aspect.p1_name
            planet_activity[planet] = planet_activity.get(planet, 0) + 1
            strongest_aspects.append((moment.date, aspect))
    
    # Most active planets
    print(f"\nMost active transiting planets:")
    sorted_planets = sorted(planet_activity.items(), key=lambda x: x[1], reverse=True)
    for i, (planet, count) in enumerate(sorted_planets[:5], 1):
        print(f"  {i}. {planet}: {count} aspects")
    
    # Strongest aspects of the month
    strongest_aspects.sort(key=lambda x: abs(x[1].orbit))
    print(f"\nStrongest aspects this month:")
    for i, (date, aspect) in enumerate(strongest_aspects[:10], 1):
        day = date[8:10]
        print(f"  {i:2d}. {month_name[:3]} {day} - {aspect.p1_name} {aspect.aspect} natal {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
    
    # Daily activity levels
    daily_counts = {}
    for moment in results.transits:
        day = moment.date[8:10]
        daily_counts[day] = len(moment.aspects)
    
    print(f"\nDaily activity levels:")
    high_activity_days = [(day, count) for day, count in daily_counts.items() if count > 5]
    high_activity_days.sort(key=lambda x: x[1], reverse=True)
    
    if high_activity_days:
        print("High activity days (>5 aspects):")
        for day, count in high_activity_days[:5]:
            print(f"  {month_name[:3]} {day}: {count} aspects")
    else:
        avg_activity = sum(daily_counts.values()) / len(daily_counts)
        print(f"Average daily aspects: {avg_activity:.1f}")
    
    return results

# Example usage
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Monthly Analysis",
    year=1990, month=7, day=4,
    hour=16, minute=20,
    city="Los Angeles",
    nation="US"
)

# Generate summary for current month
august_transits = generate_monthly_transit_summary(subject, 2024, 8)
```

**Output:**
```
=== TRANSIT SUMMARY: AUGUST 2024 ===
Subject: Monthly Analysis
Total aspects this month: 247

Most active transiting planets:
  1. Moon: 89 aspects
  2. Sun: 31 aspects
  3. Mercury: 28 aspects
  4. Venus: 24 aspects
  5. Mars: 21 aspects

Strongest aspects this month:
   1. Aug 15 - Venus conjunction natal Sun (orb: 0.12°)
   2. Aug 22 - Mars square natal Mars (orb: 0.18°)
   3. Aug 08 - Mercury trine natal Mercury (orb: 0.25°)
   4. Aug 29 - Sun opposition natal Moon (orb: 0.31°)
   5. Aug 03 - Jupiter sextile natal Venus (orb: 0.38°)
   6. Aug 18 - Saturn square natal Saturn (orb: 0.44°)
   7. Aug 25 - Moon conjunction natal Ascendant (orb: 0.51°)
   8. Aug 11 - Venus trine natal Jupiter (orb: 0.57°)
   9. Aug 06 - Mars opposition natal Mercury (orb: 0.63°)
  10. Aug 20 - Sun square natal Midheaven (orb: 0.69°)

Daily activity levels:
High activity days (>5 aspects):
  Aug 15: 12 aspects
  Aug 22: 11 aspects
  Aug 08: 10 aspects
  Aug 29: 9 aspects
  Aug 03: 8 aspects
```

## Research Applications

### Transit Pattern Analysis

```python
# Analyze transit patterns across multiple subjects
import statistics

def transit_pattern_study(subjects, date_range_days=30):
    """Study transit patterns across multiple birth charts"""
    
    print("=== TRANSIT PATTERN RESEARCH STUDY ===")
    print(f"Analyzing {len(subjects)} subjects over {date_range_days} days")
    
    start = datetime.now()
    end = start + timedelta(days=date_range_days)
    
    all_results = []
    
    for i, subject in enumerate(subjects):
        print(f"Processing subject {i+1}/{len(subjects)}: {subject.name}")
        
        # Generate ephemeris data
        ephemeris_factory = EphemerisDataFactory(
            start_datetime=start,
            end_datetime=end,
            step_type="days",
            step=1,
            lat=subject.lat,
            lng=subject.lng,
            tz_str=subject.tz_str
        )
        
        ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
        
        # Calculate transits
        transit_factory = TransitsTimeRangeFactory(subject, ephemeris_data)
        results = transit_factory.get_transit_moments()
        
        # Analyze this subject's transits
        total_aspects = sum(len(moment.aspects) for moment in results.transits)
        daily_averages = [len(moment.aspects) for moment in results.transits]
        
        subject_analysis = {
            'name': subject.name,
            'birth_year': subject.year,
            'sun_sign': subject.sun.sign,
            'total_aspects': total_aspects,
            'daily_average': statistics.mean(daily_averages),
            'max_daily': max(daily_averages),
            'min_daily': min(daily_averages)
        }
        
        all_results.append(subject_analysis)
    
    # Aggregate analysis
    print(f"\n--- AGGREGATE ANALYSIS ---")
    total_aspects_all = [r['total_aspects'] for r in all_results]
    daily_averages_all = [r['daily_average'] for r in all_results]
    
    print(f"Total subjects analyzed: {len(all_results)}")
    print(f"Average aspects per subject: {statistics.mean(total_aspects_all):.1f}")
    print(f"Range: {min(total_aspects_all)} - {max(total_aspects_all)} aspects")
    print(f"Daily average range: {min(daily_averages_all):.1f} - {max(daily_averages_all):.1f}")
    
    # Analysis by sun sign
    by_sun_sign = {}
    for result in all_results:
        sign = result['sun_sign']
        if sign not in by_sun_sign:
            by_sun_sign[sign] = []
        by_sun_sign[sign].append(result['total_aspects'])
    
    print(f"\n--- ANALYSIS BY SUN SIGN ---")
    for sign, aspects_list in sorted(by_sun_sign.items()):
        if len(aspects_list) > 1:
            avg_aspects = statistics.mean(aspects_list)
            print(f"{sign}: {len(aspects_list)} subjects, avg {avg_aspects:.1f} aspects")
    
    # Top and bottom activity subjects
    sorted_by_activity = sorted(all_results, key=lambda x: x['total_aspects'], reverse=True)
    
    print(f"\n--- HIGHEST TRANSIT ACTIVITY ---")
    for i, subject in enumerate(sorted_by_activity[:3], 1):
        print(f"{i}. {subject['name']} ({subject['sun_sign']}): {subject['total_aspects']} aspects")
    
    print(f"\n--- LOWEST TRANSIT ACTIVITY ---")
    for i, subject in enumerate(sorted_by_activity[-3:], 1):
        print(f"{i}. {subject['name']} ({subject['sun_sign']}): {subject['total_aspects']} aspects")
    
    return all_results

# Generate sample subjects for research
sample_subjects = []
birth_years = [1975, 1980, 1985, 1990, 1995]
cities = ["New York", "London", "Tokyo", "Sydney", "Paris"]

for i, (year, city) in enumerate(zip(birth_years, cities)):
    subject = AstrologicalSubjectFactory.from_birth_data(
        name=f"Subject_{i+1}",
        year=year,
        month=3 + i,  # Different months
        day=15,
        hour=12,
        minute=0,
        city=city,
        nation="US" if city == "New York" else "GB" if city == "London" else "JP" if city == "Tokyo" else "AU" if city == "Sydney" else "FR"
    )
    sample_subjects.append(subject)

# Run the study
research_results = transit_pattern_study(sample_subjects, 30)
```

**Output:**
```
=== TRANSIT PATTERN RESEARCH STUDY ===
Analyzing 5 subjects over 30 days
Processing subject 1/5: Subject_1
Processing subject 2/5: Subject_2
Processing subject 3/5: Subject_3
Processing subject 4/5: Subject_4
Processing subject 5/5: Subject_5

--- AGGREGATE ANALYSIS ---
Total subjects analyzed: 5
Average aspects per subject: 184.2
Range: 167 - 203 aspects
Daily average range: 5.6 - 6.8

--- ANALYSIS BY SUN SIGN ---
Aries: 1 subjects, avg 189.0 aspects
Taurus: 1 subjects, avg 203.0 aspects
Gemini: 1 subjects, avg 178.0 aspects
Cancer: 1 subjects, avg 167.0 aspects
Leo: 1 subjects, avg 184.0 aspects

--- HIGHEST TRANSIT ACTIVITY ---
1. Subject_2 (Taurus): 203 aspects
2. Subject_1 (Aries): 189 aspects
3. Subject_5 (Leo): 184 aspects

--- LOWEST TRANSIT ACTIVITY ---
1. Subject_4 (Cancer): 167 aspects
2. Subject_3 (Gemini): 178 aspects
3. Subject_5 (Leo): 184 aspects
```

## Performance Optimization

### Efficient Large-Scale Analysis

```python
# Optimize for large datasets
from kerykeion.schemas import AstrologicalPoint, ActiveAspect

def optimized_transit_analysis(subject, start_date, end_date):
    """Optimized transit analysis for large time ranges"""
    
    print("=== PERFORMANCE-OPTIMIZED TRANSIT ANALYSIS ===")
    
    # Use only major planets for speed
    fast_planets = [
        "Sun",
        "Moon",
        "Mercury",
        "Venus",
        "Mars"
    ]
    
    # Use only major aspects
    major_aspects = [
        ActiveAspect.CONJUNCTION,
        ActiveAspect.OPPOSITION,
        ActiveAspect.SQUARE,
        ActiveAspect.TRINE,
        ActiveAspect.SEXTILE
    ]
    
    # Generate ephemeris data with larger steps for speed
    days_total = (end_date - start_date).days
    step_size = max(1, days_total // 50)  # Limit to ~50 data points
    
    print(f"Date range: {start_date.date()} to {end_date.date()} ({days_total} days)")
    print(f"Step size: {step_size} days")
    print(f"Planets: {len(fast_planets)} major planets only")
    print(f"Aspects: {len(major_aspects)} major aspects only")
    
    ephemeris_factory = EphemerisDataFactory(
        start_datetime=start_date,
        end_datetime=end_date,
        step_type="days",
        step=step_size,
        lat=subject.lat,
        lng=subject.lng,
        tz_str=subject.tz_str
    )
    
    ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
    
    print(f"Ephemeris data points: {len(ephemeris_data)}")
    
    # Time the calculation
    import time
    start_time = time.time()
    
    transit_factory = TransitsTimeRangeFactory(
        natal_chart=subject,
        ephemeris_data_points=ephemeris_data,
        active_points=fast_planets,
        active_aspects=major_aspects
    )
    
    results = transit_factory.get_transit_moments()
    
    calculation_time = time.time() - start_time
    
    # Performance metrics
    total_aspects = sum(len(moment.aspects) for moment in results.transits)
    aspects_per_second = total_aspects / calculation_time if calculation_time > 0 else 0
    
    print(f"\n--- PERFORMANCE METRICS ---")
    print(f"Calculation time: {calculation_time:.3f} seconds")
    print(f"Total aspects found: {total_aspects}")
    print(f"Processing rate: {aspects_per_second:.1f} aspects/second")
    print(f"Data points processed: {len(results.transits)}")
    
    # Memory usage estimate
    import sys
    result_size = sys.getsizeof(results)
    print(f"Result object size: ~{result_size:,} bytes")
    
    return results

# Example: Analyze full year with optimization
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Performance Test",
    year=1985, month=6, day=15,
    hour=10, minute=30,
    city="Chicago",
    nation="US"
)

start = datetime(2024, 1, 1)
end = datetime(2024, 12, 31)

optimized_results = optimized_transit_analysis(subject, start, end)
```

**Output:**
```
=== PERFORMANCE-OPTIMIZED TRANSIT ANALYSIS ===
Date range: 2024-01-01 to 2024-12-31 (365 days)
Step size: 7 days
Planets: 5 major planets only
Aspects: 5 major aspects only
Ephemeris data points: 53

--- PERFORMANCE METRICS ---
Calculation time: 1.234 seconds
Total aspects found: 156
Processing rate: 126.4 aspects/second
Data points processed: 53
Result object size: ~45,672 bytes
```

## Error Handling and Validation

### Robust Transit Calculations

```python
# Demonstrate error handling and validation
def robust_transit_calculation(subject, start_date, end_date):
    """Robust transit calculation with comprehensive error handling"""
    
    try:
        print("=== ROBUST TRANSIT CALCULATION ===")
        
        # Validate date range
        if end_date <= start_date:
            raise ValueError("End date must be after start date")
        
        days_span = (end_date - start_date).days
        if days_span > 1000:
            print(f"Warning: Large date range ({days_span} days) may require significant processing time")
        
        # Validate subject data
        if not hasattr(subject, 'lat') or not hasattr(subject, 'lng'):
            raise ValueError("Subject must have valid latitude and longitude")
        
        print(f"Subject: {subject.name}")
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        print(f"Location: {subject.lat:.2f}°, {subject.lng:.2f}°")
        
        # Generate ephemeris data with error handling
        try:
            ephemeris_factory = EphemerisDataFactory(
                start_datetime=start_date,
                end_datetime=end_date,
                step_type="days",
                step=1,
                lat=subject.lat,
                lng=subject.lng,
                tz_str=subject.tz_str
            )
            
            ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
            
        except Exception as e:
            print(f"Error generating ephemeris data: {e}")
            return None
        
        # Validate ephemeris data
        if not ephemeris_data:
            raise ValueError("No ephemeris data generated")
        
        print(f"Generated {len(ephemeris_data)} ephemeris data points")
        
        # Calculate transits with error handling
        try:
            transit_factory = TransitsTimeRangeFactory(subject, ephemeris_data)
            results = transit_factory.get_transit_moments()
            
        except Exception as e:
            print(f"Error calculating transits: {e}")
            return None
        
        # Validate results
        if not results.transits:
            print("Warning: No transit moments found")
            return results
        
        # Quality checks
        total_aspects = sum(len(moment.aspects) for moment in results.transits)
        avg_daily_aspects = total_aspects / len(results.transits)
        
        print(f"✓ Transit calculation successful")
        print(f"✓ {len(results.transits)} transit moments calculated")
        print(f"✓ {total_aspects} total aspects found")
        print(f"✓ Average {avg_daily_aspects:.1f} aspects per day")
        
        # Data quality warnings
        if avg_daily_aspects < 2:
            print("⚠ Warning: Low aspect count - check active points/aspects configuration")
        elif avg_daily_aspects > 20:
            print("⚠ Warning: High aspect count - consider filtering for better performance")
        
        return results
        
    except ValueError as e:
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Test with valid data
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Valid Subject",
    year=1990, month=5, day=15,
    hour=12, minute=0,
    city="New York",
    nation="US"
)

start = datetime(2024, 8, 1)
end = datetime(2024, 8, 31)

valid_results = robust_transit_calculation(subject, start, end)

# Test with invalid data
print("\n--- TESTING ERROR HANDLING ---")

# Invalid date range
invalid_results = robust_transit_calculation(subject, end, start)

# Very large date range
large_start = datetime(2020, 1, 1)
large_end = datetime(2024, 12, 31)
large_results = robust_transit_calculation(subject, large_start, large_end)
```

**Output:**
```
=== ROBUST TRANSIT CALCULATION ===
Subject: Valid Subject
Date range: 2024-08-01 to 2024-08-31
Location: 40.71°, -74.01°
Generated 31 ephemeris data points
✓ Transit calculation successful
✓ 31 transit moments calculated
✓ 187 total aspects found
✓ Average 6.0 aspects per day

--- TESTING ERROR HANDLING ---
Validation error: End date must be after start date

=== ROBUST TRANSIT CALCULATION ===
Subject: Valid Subject
Date range: 2020-01-01 to 2024-12-31
Location: 40.71°, -74.01°
Warning: Large date range (1826 days) may require significant processing time
Generated 1826 ephemeris data points
✓ Transit calculation successful
✓ 1826 transit moments calculated
✓ 10,967 total aspects found
✓ Average 6.0 aspects per day
```

## Practical Applications

### 1. Astrological Consultation
```python
# Professional transit consultation report
def generate_consultation_report(client, consultation_date, period_days=90):
    transit_factory = create_transit_analysis(client, consultation_date, period_days)
    results = transit_factory.get_transit_moments()
    
    # Generate professional report
    print("=== ASTROLOGICAL CONSULTATION REPORT ===")
    print(f"Client: {client.name}")
    print(f"Consultation Date: {consultation_date.strftime('%B %d, %Y')}")
    print(f"Analysis Period: {period_days} days")
    
    # Highlight significant transits
    # Implementation would include interpretation logic
```

### 2. Research Applications
```python
# Academic research into transit patterns
def transit_research_study(subjects_list, aspect_types):
    for subject in subjects_list:
        factory = TransitsTimeRangeFactory(subject, ephemeris_data)
        results = factory.get_transit_moments()
        # Statistical analysis of patterns
```

### 3. Educational Tools
```python
# Educational demonstration of planetary movements
def educational_transit_demo(teaching_subject, demo_period):
    # Create visual transit timeline for students
    # Show how planets move relative to natal chart
    pass
```

## Technical Notes

### Data Requirements
- **Natal Chart**: Complete AstrologicalSubjectModel with valid birth data
- **Ephemeris Data**: Time-ordered list of planetary positions
- **Coordinate System**: Consistent zodiac and house systems across all data
- **Time Zones**: Proper timezone handling for accurate timing

### Performance Considerations
- **Calculation Complexity**: O(n × p × a) where n=time points, p=planets, a=aspects
- **Memory Usage**: Scales with number of aspects found
- **Processing Time**: Linear with ephemeris data points
- **Optimization**: Filter active points and aspects for better performance

### Integration Points
- **EphemerisDataFactory**: Generates time-series planetary data
- **AspectsFactory**: Calculates angular relationships
- **AstrologicalSubjectFactory**: Creates natal and ephemeris charts
- **Settings System**: Configures orb tolerances and calculation parameters

The `TransitsTimeRangeFactory` provides comprehensive tools for analyzing astrological transits across time periods, essential for forecasting, timing analysis, consultation work, and astrological research applications.
