---
title: 'Composite Subject Factory'
description: 'Understand the dynamics of relationships with composite charts. Learn how to calculate midpoints and generate unified relationship charts using Kerykeion.'
category: 'Analysis'
tags: ['docs', 'composite', 'relationships', 'kerykeion']
order: 7
---

# Composite Subject Factory

The `CompositeSubjectFactory` creates a new astrological subject representing the relationship between two people, using either the **Midpoint Method** (averaging the two charts' positions) or the **Davison Method** (the time-space midpoint, cast as a real chart). The resulting chart represents the relationship itself as a third entity.

## What Is a Composite Chart?

Unlike **Synastry** (which compares two separate charts), a **Composite Chart** creates a single unified chart that symbolizes the relationship itself. Think of it as the "birth chart" of the relationship.

**How It Works:**

- Every planetary position is calculated as the midpoint between the two natal charts
- The Composite Sun shows the relationship's core identity and purpose
- The Composite Moon reveals the emotional dynamics between partners
- House placements show which life areas the relationship emphasizes

Composite charts are especially useful for understanding:

- **Romantic partnerships**: What does this relationship want to become?
- **Business partnerships**: What are the shared goals and challenges?
- **Friendships**: What unique dynamic emerges when these two people interact?

## Basic Usage

The process involves creating two individual subjects first, then generating a composite from them.

```python
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory

# 1. Create Individual Subjects
person_a = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 6, 15, 14, 30, "London", "GB")
person_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 9, 22, 18, 45, "Los Angeles", "US")

# 2. Create Composite Factory
composite_factory = CompositeSubjectFactory(
    person_a,
    person_b,
    chart_name="Alice & Bob Composite" # Optional custom name
)

# 3. Get the Composite Subject Model
composite_subject = composite_factory.get_midpoint_composite_subject_model()

print(f"Composite Sun: {composite_subject.sun.sign} {composite_subject.sun.abs_pos:.2f}°")
```

**Expected Output:**

```text
Composite Sun: Leo 132.24°
```

> **Note:** The position is the midpoint between Alice's Sun (Gemini ~84°) and Bob's Sun (Libra ~180°), yielding ~132° (Leo).

## Chart Generation

The returned `composite_subject` is a `CompositeSubjectModel` (which inherits from `AstrologicalBaseModel`, not `AstrologicalSubjectModel`). You can use it with `ChartDataFactory` to generate chart data or SVG visualizations.

```python
from kerykeion import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer

# Generate Data
composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)

# Draw Chart
drawer = ChartDrawer(composite_data)
svg = drawer.generate_svg_string()
```

## Constructor Parameters

| Parameter        | Type                       | Default     | Description                                                                        |
| :--------------- | :------------------------- | :---------- | :--------------------------------------------------------------------------------- |
| `first_subject`  | `AstrologicalSubjectModel` | **Required** | First person's natal subject.                                                     |
| `second_subject` | `AstrologicalSubjectModel` | **Required** | Second person's natal subject.                                                    |
| `chart_name`     | `Optional[str]`            | `None`       | Custom name for the composite chart. If `None`, auto-generates as `"{name1} and {name2} Composite Chart"`. |

**Method:** Call `get_midpoint_composite_subject_model()` on the factory instance to get the `CompositeSubjectModel`.

## Requirements

To calculate a valid midpoint composite, both subjects must agree on:

- **Zodiac System**: Both Tropical OR Both Sidereal (with same Ayanamsa).
- **House System**: the division their cusps were **actually computed with** — see below.
- **Perspective**: Both Apparent Geocentric, etc.

If these settings do not match, the factory raises a `KerykeionException`. The messages, which are not an exhaustive list, read:

```text
KerykeionException: Both subjects must have the same zodiac type
KerykeionException: Both subjects must have the same sidereal mode
KerykeionException: Both subjects must have the same houses system
KerykeionException: Both subjects must have the same houses system name
KerykeionException: Both subjects must have the same perspective type
```

### The house-system requirement is about the cusps, not the request

Each composite cusp is the circular mean of the two subjects' same-numbered cusps, so the result inherits whatever division produced them. Averaging a Porphyry third house with a Placidus third house yields a boundary belonging to neither system, and no label on the output could turn it into one.

That matters because a subject's requested and actual divisions can differ. Inside the polar circle a quadrant system is undefined, so the cusps are recomputed with Porphyry at the real latitude and the substitution is recorded — see [Polar Latitudes](/content/docs/faq). Two subjects can therefore both request Placidus and still have incompatible cusps. The factory compares `effective_houses_system_identifier`, and says why when it refuses:

```text
KerykeionException: Both subjects must have the same houses system: Polar's cusps were
computed with 'Porphyry' and Temp's with 'Placidus'. A house system undefined at one
subject's latitude was substituted there; see polar_house_fallbacks on that subject.
```

To compose such a pair, cast both subjects with a system defined at every latitude (Whole Sign, Equal, Porphyry) so neither needs a substitute.

### What the composite reports when both parents were substituted

When both parents' cusps came from the same substitute, the composite is valid and keeps both facts, in separate fields:

```python
# Two subjects far inside the Arctic circle, both cast with houses_system_identifier="P"
composite = CompositeSubjectFactory(polar_a, polar_b).get_midpoint_composite_subject_model()

print(composite.houses_system_identifier)            # "P" — the REQUESTED system
print(composite.houses_system_name)                  # "Placidus"
print(composite.effective_houses_system_identifier)  # "O" — where the cusps came from
print(composite.effective_houses_system_name)        # "Porphyry"

for record in composite.polar_house_fallbacks:
    print(record.latitude, record.requested_house_system_identifier,
          record.used_house_system_identifier)
# 78.2232 P O
# 79.0    P O
```

The requested pair is deliberately left untouched. A substitution forced by one parent's latitude is a fact about that parent, not a preference the relationship adopted, and the requested value is what a relocation or a re-cast has to start from. The substitution stays visible because the parents' own records travel with the composite, and the `effective_houses_system_*` view is derived from them.

A midpoint composite has no latitude of its own — `composite.lat` is `None`, since its cusps are means of cusps computed in two different places — so it can never author a substitution record, only inherit one. Each parent contributes the record that explains its house cusps; an ancillary Gauquelin clamp does not travel, because the midpoint technique averages no sectors and the composite has none to claim.

A **Davison** composite is not affected by any of this. It recasts a whole new chart at the midpoint moment and place rather than averaging cusps, so it accepts parents whose effective systems differ, retains the requested system, and lets that fresh cast decide for itself whether a substitution is needed at the derived latitude.

## Davison Composite (Time-Space Midpoint)

The **Davison** method is fundamentally different from the midpoint composite: instead of averaging the two charts' planetary positions, it averages the two birth **moments** (in time) and the two **locations** (in space), then casts a *real* natal chart for that derived date and place. The result therefore has valid astronomical positions that actually occurred — it is a real chart, not an averaged abstraction.

```python
# Using the `composite_factory` from the Basic Usage example above:
davison = composite_factory.get_davison_composite_subject_model()

print(davison.composite_chart_type)               # "Davison"
print(davison.sun.sign, f"{davison.sun.abs_pos:.2f}°")
```

When the input subjects use `sidereal_mode="USER"`, pass `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0` to `get_davison_composite_subject_model()` so the Davison chart is built with the same ayanamsa. The return value is a `CompositeSubjectModel` with `composite_chart_type="Davison"`.

## Methodology

- **Midpoint method**: Positions are calculated as the shortest-arc mean between the two input points (e.g., Aries 0° and Aries 20° = Aries 10°); house cusps are also taken by midpoint, which is why both parents' cusps have to come from the same division. Only points present in _both_ input subjects are included.
- **Davison method**: The two birth moments (Julian Day) and the two locations (lat/lng) are averaged, then a standard natal chart is cast for that derived moment and place.
- **Active Points**: For the midpoint composite, only points present in _both_ input subjects are included.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
