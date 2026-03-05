---
title: 'Transits Time Range'
tags: ['examples', 'transits', 'forecasting', 'time-range', 'kerykeion']
order: 18
---

# Transits Time Range

The `TransitsTimeRangeFactory` calculates all transit aspects formed between a natal chart and a series of ephemeris data points over a time period. It answers the question: "What transits happen to my chart between date A and date B?"

## Basic 3-Step Workflow

1. Create a natal subject
2. Generate ephemeris data for the transit period
3. Feed both to `TransitsTimeRangeFactory`

```python
from datetime import datetime
from kerykeion import (
    AstrologicalSubjectFactory,
    EphemerisDataFactory,
    TransitsTimeRangeFactory,
)

# Step 1: Natal chart
natal = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

# Step 2: Ephemeris data for the transit window
ephemeris_factory = EphemerisDataFactory(
    start_datetime=datetime(2025, 3, 1),
    end_datetime=datetime(2025, 3, 31),
    step_type="days",
    step=1,
    lat=41.9028,
    lng=12.4964,
    tz_str="Europe/Rome",
)
ephemeris_points = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

# Step 3: Calculate transits
transit_factory = TransitsTimeRangeFactory(
    natal_chart=natal,
    ephemeris_data_points=ephemeris_points,
)
result = transit_factory.get_transit_moments()

# Explore the results
print(f"Transit period: {len(result.dates)} days analyzed")
for moment in result.transits[:5]:
    if moment.aspects:
        print(f"\n{moment.date}:")
        for aspect in moment.aspects[:3]:
            print(f"  {aspect.p1_name} {aspect.aspect} {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
```

## Analyzing Results

The `get_transit_moments()` method returns a `TransitsTimeRangeModel` with:

- `dates`: List of ISO-formatted datetime strings for all analyzed points.
- `subject`: The natal chart used as reference.
- `transits`: List of `TransitMomentModel`, each containing:
  - `date`: ISO-formatted timestamp.
  - `aspects`: List of all aspects formed at that moment.

### Finding Specific Transits

```python
# Find all days when transiting Saturn aspects natal Sun
for moment in result.transits:
    for aspect in moment.aspects:
        if aspect.p1_name == "Saturn" and aspect.p2_name == "Sun":
            print(f"{moment.date}: Saturn {aspect.aspect} Sun (orb: {aspect.orbit:.2f}°)")
```

### Counting Aspect Activity

```python
# Count total aspects per day
for moment in result.transits:
    count = len(moment.aspects)
    if count > 5:
        print(f"{moment.date}: {count} aspects (busy day!)")
```

## Constructor Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `natal_chart` | `AstrologicalSubjectModel` | **Required** | The natal chart to transit against |
| `ephemeris_data_points` | `list[AstrologicalSubjectModel]` | **Required** | Time-series data from `EphemerisDataFactory` |
| `active_points` | `list[AstrologicalPoint]` | `DEFAULT_ACTIVE_POINTS` | Which points to consider |
| `active_aspects` | `list[ActiveAspect]` | `DEFAULT_ACTIVE_ASPECTS` | Which aspects to detect (with orbs) |
| `axis_orb_limit` | `float` | `None` | Stricter orb for angles (Asc, MC) *(keyword-only)* |

## Tips

- **Use daily steps** for outer planet transits (Jupiter through Pluto) — they move slowly.
- **Use hourly steps** for Moon transits — the Moon moves ~13°/day.
- **Limit the date range** to what you need. The `max_days` safety limit on `EphemerisDataFactory` defaults to 730 days (2 years).
- **Custom active_points**: Pass a reduced list to focus only on specific transiting planets.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
