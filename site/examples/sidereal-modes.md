---
title: 'Sidereal Modes'
tags: ['examples', 'sidereal', 'charts', 'zodiac', 'kerykeion']
order: 9
---

# Sidereal Modes (Ayanamsas)

Kerykeion supports both **Tropical** (default) and **Sidereal** zodiac systems. When using the Sidereal zodiac, you must specify an **ayanamsa** (sidereal mode) that defines the starting point of the zodiac relative to the fixed stars.

## Tropical vs Sidereal

| System | Reference Point | Zodiac Drift | Primary Use |
|:-------|:----------------|:-------------|:------------|
| **Tropical** | Vernal equinox (0° Aries = spring equinox) | Aligned with seasons | Western astrology |
| **Sidereal** | Fixed stars (constellation-based) | ~24° behind tropical | Vedic/Jyotish, some Western sidereal |

Due to the precession of the equinoxes, the tropical and sidereal zodiacs differ by approximately **24°** (as of 2024). This difference grows by about 1° every 72 years.

## Available Sidereal Modes

| Mode | Description | Origin |
|:-----|:------------|:-------|
| `LAHIRI` | **Most common.** Official ayanamsa of the Indian government. Standard for Vedic/Jyotish astrology. | India |
| `FAGAN_BRADLEY` | Standard Western sidereal ayanamsa. Used by Cyril Fagan and Donald Bradley. | Western |
| `KRISHNAMURTI` | Used in the Krishnamurti Paddhati (KP) system. Slightly different from Lahiri. | India |
| `RAMAN` | B.V. Raman's ayanamsa, popular in South India. | India |
| `YUKTESHWAR` | Based on Sri Yukteshwar's calculations from "The Holy Science". | India |
| `DELUCE` | DeLuce ayanamsa. | Western |
| `JN_BHASIN` | J.N. Bhasin's ayanamsa. | India |
| `DJWHAL_KHUL` | Theosophical ayanamsa. | Esoteric |
| `HIPPARCHOS` | Based on ancient Greek astronomer Hipparchos. | Historical |
| `SASSANIAN` | Persian/Sassanian ayanamsa. | Historical |
| `ALDEBARAN_15TAU` | Sets Aldebaran at 15° Taurus. Ancient reference point. | Historical |
| `J2000` | Reference frame at Julian epoch J2000.0 (Jan 1, 2000). | Scientific |
| `J1900` | Reference frame at Julian epoch J1900.0. | Scientific |
| `B1950` | Reference frame at Besselian epoch B1950.0. | Scientific |
| `BABYL_KUGLER1` | Babylonian (Kugler 1). | Historical |
| `BABYL_KUGLER2` | Babylonian (Kugler 2). | Historical |
| `BABYL_KUGLER3` | Babylonian (Kugler 3). | Historical |
| `BABYL_HUBER` | Babylonian (Huber). | Historical |
| `BABYL_ETPSC` | Babylonian (ETPSC). | Historical |
| `USHASHASHI` | Ushashashi ayanamsa. | India |

## Examples

### Lahiri (Vedic Standard)

The most widely used ayanamsa for Vedic astrology:

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon Lahiri", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
)

print(f"Sun (Lahiri): {sidereal_subject.sun.sign} {sidereal_subject.sun.position:.2f}°")
# Compare: Tropical Sun would be Libra 16.27°

data = ChartDataFactory.create_natal_chart_data(sidereal_subject)
chart = ChartDrawer(data)

out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=out_dir, filename="lennon-lahiri")
```

**Output:**
```
Sun (Lahiri): Vir 23.08°
```

The chart output:

![John Lennon Lahiri](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/charts/svg/John%20Lennon%20Lahiri%20-%20Natal%20Chart.svg)

### Fagan-Bradley (Western Sidereal)

The standard ayanamsa for Western sidereal astrologers:

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Fagan-Bradley", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="FAGAN_BRADLEY",
)

print(f"Sun (Fagan-Bradley): {subject.sun.sign} {subject.sun.position:.2f}°")
```

### Krishnamurti (KP System)

Used for the popular Krishnamurti Paddhati system:

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - KP", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="KRISHNAMURTI",
)

print(f"Sun (KP): {subject.sun.sign} {subject.sun.position:.2f}°")
```

### Comparing Ayanamsas

See how different ayanamsas affect planetary positions:

```python
from kerykeion import AstrologicalSubjectFactory

modes = ["LAHIRI", "FAGAN_BRADLEY", "KRISHNAMURTI", "RAMAN"]

for mode in modes:
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Test", 1990, 6, 15, 12, 0,
        lng=-0.1276, lat=51.5074, tz_str="Europe/London",
        online=False,
        zodiac_type="Sidereal",
        sidereal_mode=mode,
    )
    print(f"{mode}: Sun at {subject.sun.sign} {subject.sun.position:.2f}°")
```

**Output:**
```
LAHIRI: Sun at Tau 29.85°
FAGAN_BRADLEY: Sun at Gem 0.62°
KRISHNAMURTI: Sun at Tau 29.78°
RAMAN: Sun at Tau 28.25°
```

> **Note:** The differences between ayanamsas can be significant (up to a few degrees), which may change the sign a planet falls in, especially for planets near sign boundaries.

### Tropical vs Sidereal Comparison

```python
from kerykeion import AstrologicalSubjectFactory

# Same birth data, different zodiac types
tropical = AstrologicalSubjectFactory.from_birth_data(
    "Tropical", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    zodiac_type="Tropical",
)

sidereal = AstrologicalSubjectFactory.from_birth_data(
    "Sidereal", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
)

print("Tropical positions:")
print(f"  Sun: {tropical.sun.sign} {tropical.sun.position:.2f}°")
print(f"  Moon: {tropical.moon.sign} {tropical.moon.position:.2f}°")
print(f"  Ascendant: {tropical.first_house.sign} {tropical.first_house.position:.2f}°")

print("\nSidereal (Lahiri) positions:")
print(f"  Sun: {sidereal.sun.sign} {sidereal.sun.position:.2f}°")
print(f"  Moon: {sidereal.moon.sign} {sidereal.moon.position:.2f}°")
print(f"  Ascendant: {sidereal.first_house.sign} {sidereal.first_house.position:.2f}°")
```

**Output:**
```
Tropical positions:
  Sun: Gem 24.05°
  Moon: Sco 15.23°
  Ascendant: Vir 24.52°

Sidereal (Lahiri) positions:
  Sun: Tau 29.85°
  Moon: Lib 21.03°
  Ascendant: Leo 0.32°
```

> **Important:** You cannot set a `sidereal_mode` when using `zodiac_type="Tropical"`. Attempting to do so will raise a `KerykeionException`.
