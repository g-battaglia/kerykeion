---
title: 'Composite Subject Factory'
description: 'Understand the dynamics of relationships with composite charts. Learn how to calculate midpoints and generate unified relationship charts using Kerykeion.'
category: 'Analysis'
tags: ['docs', 'composite', 'relationships', 'kerykeion']
order: 7
---

# Composite Subject Factory

The `CompositeSubjectFactory` creates a new astrological subject representing the relationship between two people using the **Midpoint Method**. The resulting chart represents the relationship itself as a third entity.

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
Composite Sun: Leo 124.36°
```

> **Note:** The position is the midpoint between Alice's Sun (Gemini ~84°) and Bob's Sun (Virgo ~170°), yielding ~127° (Leo).

## Chart Generation

The returned `composite_subject` is a standard `AstrologicalSubjectModel`. You can use it just like a natal subject to generate chart data or SVG visualizations.

```python
from kerykeion import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Generate Data
composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)

# Draw Chart
drawer = ChartDrawer(composite_data)
svg = drawer.generate_svg_string()
```

## Requirements

To calculate a valid composite chart, both subjects **MUST** have matching configuration:

- **Zodiac System**: Both Tropical OR Both Sidereal (with same Ayanamsa).
- **House System**: Both Placidus, Whole Sign, etc.
- **Perspective**: Both Apparent Geocentric, etc.

If these settings do not match, the factory will raise an error, as you cannot mathematically combine disparate coordinate systems.

## Methodology

- **Midpoints**: Positions are calculated as the shortest arc mean between the two input points (e.g., Aries 0° and Aries 20° = Aries 10°).
- **House Cusps**: House cusps are also calculated by midpoint.
- **Active Points**: Only points present in _both_ input subjects are included in the composite.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
