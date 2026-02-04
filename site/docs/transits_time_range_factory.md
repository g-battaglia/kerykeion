---
title: 'Transits Time Range Factory'
description: 'Forecast upcoming astrological influences with transits. Learn how to calculate planetary movements over time against a fixed natal chart.'
category: 'Forecasting'
tags: ['docs', 'transits', 'forecasting', 'kerykeion']
order: 12
---

# Transits Time Range Factory

The `TransitsTimeRangeFactory` calculates transits over a period of time (days, weeks, or months) by comparing a fixed Natal chart against a series of Ephemeris data points.

## What Are Transits?

**Transits** are the current positions of planets in the sky as they form aspects to the planets in your natal chart. They represent the dynamic, ever-changing celestial influences affecting your birth chart at any given moment.

In predictive astrology, transits are used to:

- **Forecast** upcoming periods of opportunity or challenge
- **Understand timing** for major life events (career changes, relationships, relocations)
- **Track cycles** of outer planets (Jupiter, Saturn, Uranus, Neptune, Pluto) that mark significant developmental phases

For example, when transiting Jupiter (the planet of expansion) forms a trine (harmonious 120° aspect) to your natal Sun, it's traditionally considered a favorable period for growth and new opportunities.

## Usage Workflow

The process involves three steps:

1.  Define the **Natal Subject**.
2.  Generate **Ephemeris Data** for the desired time range.
3.  Calculate **Transits** by comparing the two.

```python
from datetime import datetime, timedelta
from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory

# 1. Create Natal Subject
natal_subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0, "London", "GB"
)

# 2. Generate Ephemeris Data (e.g., for 30 days starting now)
start_date = datetime.now()
end_date = start_date + timedelta(days=30)

ephemeris_factory = EphemerisDataFactory(
    start_datetime=start_date,
    end_datetime=end_date,
    step_type="days",  # "days", "hours", "months"
    step=1,            # Interval size
    lat=natal_subject.lat,
    lng=natal_subject.lng,
    tz_str=natal_subject.tz_str
)

# Get ephemeris as a list of AstrologicalSubject objects
ephemeris_data = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

# 3. Calculate Transits
transit_factory = TransitsTimeRangeFactory(
    natal_chart=natal_subject,
    ephemeris_data_points=ephemeris_data,
    # Optional: limit calculation to specific planets
    active_points=["Sun", "Mars", "Jupiter"]
)

results = transit_factory.get_transit_moments()
```

## Analyzing Results

The results contain a list of `transit_moments`, each representing a point in time where valid aspects were found.

```python
print(f"Total time points analyzed: {len(results.transits)}")

for moment in results.transits:
    if moment.aspects:
        date_str = moment.date[:10] # ISO string YYYY-MM-DD
        print(f"\nDate: {date_str}")
        for aspect in moment.aspects:
            print(f"  {aspect.p1_name} {aspect.aspect} natal {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
```

### Result Data Structure

The `get_transit_moments()` method returns a specialized object simplifying access to the data.

- `results.dates`: List of all ISO timestamps checked.
- `results.transits`: List of objects containing:
  - `date`: The specific timestamp.
  - `aspects`: List of `AspectModel` objects (Transiting Planet -> Natal Planet).

## Constructor Parameters

| Parameter               | Type                             | Default     | Description                        |
| :---------------------- | :------------------------------- | :---------- | :--------------------------------- | ------ | -------------------------------- |
| `natal_chart`           | `AstrologicalSubjectModel`       | Required    | Reference natal chart.             |
| `ephemeris_data_points` | `List[AstrologicalSubjectModel]` | Required    | Time-series planetary positions.   |
| `active_points`         | `List[AstrologicalPoint]`        | All planets | Points to include in calculation.  |
| `active_aspects`        | `List[ActiveAspect]`             | All aspects | Aspect types and orbs to use.      |
| `settings_file`         | `Path                            | dict        | None`                              | `None` | Custom orb/calculation settings. |
| `axis_orb_limit`        | `float`                          | `None`      | Stricter orb for angles (Asc, MC). |

## Configuration Tips

- **Step Size**: Use larger steps (e.g., `step=7` days) for long-term outer planet transit searches (Jupiter/Saturn) to save performance.
- **Orb**: Use standard `active_aspects` configuration to define orb tightness.
- **Ephemeris Location**: Ideally should match the natal subject's current location, as transits are technically location-dependent for exact timing (especially angles), though global planetary positions are roughly the same.
