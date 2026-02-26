---
title: 'Perspective Type'
tags: ['examples', 'charts', 'perspective', 'heliocentric', 'kerykeion']
order: 8
---

# Perspective Type

The `perspective_type` parameter defines the viewpoint from which planetary positions are calculated. Kerykeion supports four different perspectives.

## Available Perspective Types

| Perspective | Description | Use Case |
|:------------|:------------|:---------|
| `Apparent Geocentric` | Earth-centered, accounting for light-time and aberration. **Default and standard for most astrology.** | Traditional natal, synastry, transit charts |
| `True Geocentric` | Earth-centered, without light-time correction. Positions as they "truly" are at that moment. | Research, comparison with astronomical data |
| `Heliocentric` | Sun-centered. Shows planetary positions as seen from the Sun. Earth replaces Sun in the chart. | Esoteric/cosmobiological techniques, solar system studies |
| `Topocentric` | Observer's exact location on Earth's surface. Most accurate for Moon position. | Precise lunar work, electional astrology |

## Apparent Geocentric (Default)

This is the standard perspective for almost all astrological work. It accounts for the time light takes to travel from celestial bodies to Earth.

```python
from kerykeion import AstrologicalSubjectFactory

# Default perspective - no need to specify
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    # perspective_type="Apparent Geocentric"  # This is the default
)

print(f"Sun: {subject.sun.sign} {subject.sun.position:.2f}°")
print(f"Moon: {subject.moon.sign} {subject.moon.position:.2f}°")
```

**Output:**
```
Sun: Lib 16.27°
Moon: Aqu 3.50°
```

## Heliocentric

In heliocentric charts, we view the solar system from the Sun's perspective. The Earth appears in the chart instead of the Sun.

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Heliocentric", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    perspective_type="Heliocentric",
)

# Note: In heliocentric, Earth replaces Sun
print(f"Earth: {subject.earth.sign} {subject.earth.position:.2f}°")
print(f"Mars: {subject.mars.sign} {subject.mars.position:.2f}°")

data = ChartDataFactory.create_natal_chart_data(subject)
chart = ChartDrawer(data)

out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=out_dir, filename="lennon-heliocentric")
```

The output will be:

![John Lennon Heliocentric](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20-%20Heliocentric%20-%20Natal%20Chart.svg)

> **Note:** Heliocentric charts have no houses or Ascendant since there is no observer on Earth. The house system is ignored.

## True Geocentric

Shows positions without light-time correction. The difference from Apparent Geocentric is typically very small (a few arcseconds for most planets).

```python
from kerykeion import AstrologicalSubjectFactory

# True geocentric perspective
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - True Geocentric", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    perspective_type="True Geocentric",
)

print(f"Sun: {subject.sun.sign} {subject.sun.position:.4f}°")
```

## Topocentric

The most precise perspective for the Moon and fast-moving points. Accounts for the observer's exact location on Earth's surface (parallax correction).

```python
from kerykeion import AstrologicalSubjectFactory

# Topocentric for precise Moon position
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Topocentric", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    perspective_type="Topocentric",
)

print(f"Moon: {subject.moon.sign} {subject.moon.position:.4f}°")
print(f"Ascendant: {subject.first_house.sign} {subject.first_house.position:.4f}°")
```

## Comparing Perspectives

```python
from kerykeion import AstrologicalSubjectFactory

perspectives = ["Apparent Geocentric", "True Geocentric", "Topocentric"]

for perspective in perspectives:
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Test", 1990, 6, 15, 12, 0,
        lng=-0.1276, lat=51.5074, tz_str="Europe/London",
        online=False,
        perspective_type=perspective,
    )
    print(f"{perspective}:")
    print(f"  Moon: {subject.moon.position:.4f}°")
```

**Output:**
```
Apparent Geocentric:
  Moon: 15.2347°
True Geocentric:
  Moon: 15.2348°
Topocentric:
  Moon: 15.1892°  # Note the larger difference due to parallax
```

> **Tip:** For most astrological work, stick with the default `Apparent Geocentric`. Use `Topocentric` only when precise Moon timing is critical (e.g., for electional astrology or void-of-course Moon calculations).

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
