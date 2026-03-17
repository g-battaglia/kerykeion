---
title: 'Sidereal Modes'
tags: ['examples', 'sidereal', 'charts', 'zodiac', 'kerykeion']
order: 9
---

# Sidereal Modes (Ayanamsas)

Kerykeion supports both **Tropical** (default) and **Sidereal** zodiac systems. When using the Sidereal zodiac, you must specify an **ayanamsa** (sidereal mode) that defines the starting point of the zodiac relative to the fixed stars.

As of v5.12, Kerykeion supports **48 sidereal modes** (47 named + USER for custom definitions).

## Tropical vs Sidereal

| System | Reference Point | Zodiac Drift | Primary Use |
|:-------|:----------------|:-------------|:------------|
| **Tropical** | Vernal equinox (0° Aries = spring equinox) | Aligned with seasons | Western astrology |
| **Sidereal** | Fixed stars (constellation-based) | ~24° behind tropical | Vedic/Jyotish, some Western sidereal |

Due to the precession of the equinoxes, the tropical and sidereal zodiacs differ by approximately **24°** (as of 2024). This difference grows by about 1° every 72 years.

## Available Sidereal Modes

### Classic Modes

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

### New in v5.12

| Mode | Description | Category |
|:-----|:------------|:---------|
| `ARYABHATA` | Aryabhata ayanamsa. | Indian/Vedic |
| `ARYABHATA_522` | Aryabhata (522 CE epoch). | Indian/Vedic |
| `ARYABHATA_MSUN` | Aryabhata (mean Sun). | Indian/Vedic |
| `SURYASIDDHANTA` | Suryasiddhanta ayanamsa. | Indian/Vedic |
| `SURYASIDDHANTA_MSUN` | Suryasiddhanta (mean Sun). | Indian/Vedic |
| `SS_CITRA` | Suryasiddhanta (Citra/Spica reference). | Indian/Vedic |
| `SS_REVATI` | Suryasiddhanta (Revati/zeta Piscium). | Indian/Vedic |
| `TRUE_CITRA` | True Citra (Spica at 0° Libra). | True star-based |
| `TRUE_MULA` | True Mula (lambda Scorpii at 0° Sagittarius). | True star-based |
| `TRUE_PUSHYA` | True Pushya (delta Cancri reference). | True star-based |
| `TRUE_REVATI` | True Revati (zeta Piscium at 0° Aries). | True star-based |
| `TRUE_SHEORAN` | True Sheoran ayanamsa. | True star-based |
| `LAHIRI_1940` | Lahiri (1940 epoch). | Lahiri variants |
| `LAHIRI_ICRC` | Lahiri (ICRC standard). | Lahiri variants |
| `LAHIRI_VP285` | Lahiri (VP285 variant). | Lahiri variants |
| `KRISHNAMURTI_VP291` | Krishnamurti (VP291 variant). | Lahiri variants |
| `GALCENT_0SAG` | Galactic Center at 0° Sagittarius. | Galactic alignment |
| `GALCENT_COCHRANE` | Galactic Center (Cochrane). | Galactic alignment |
| `GALCENT_MULA_WILHELM` | Galactic Center (Mula/Wilhelm). | Galactic alignment |
| `GALCENT_RGILBRAND` | Galactic Center (Rgilbrand). | Galactic alignment |
| `GALEQU_FIORENZA` | Galactic Equator (Fiorenza). | Galactic alignment |
| `GALEQU_IAU1958` | Galactic Equator (IAU 1958). | Galactic alignment |
| `GALEQU_MULA` | Galactic Equator (Mula). | Galactic alignment |
| `GALEQU_TRUE` | Galactic Equator (true). | Galactic alignment |
| `GALALIGN_MARDYKS` | Galactic alignment (Mardyks). | Galactic alignment |
| `BABYL_BRITTON` | Babylonian (Britton). | Historical |
| `VALENS_MOON` | Vettius Valens Moon ayanamsa. | Historical |
| `USER` | Custom ayanamsa -- see below. | User-defined |

## Custom Ayanamsa (USER Mode)

The `USER` sidereal mode lets you define a custom ayanamsa by providing a reference epoch and offset:

```python
from kerykeion import AstrologicalSubjectFactory

custom = AstrologicalSubjectFactory.from_birth_data(
    "Custom Ayanamsa", 2000, 1, 1, 0, 0,
    lng=0.0, lat=51.5, tz_str="Etc/GMT", online=False,
    zodiac_type="Sidereal",
    sidereal_mode="USER",
    custom_ayanamsa_t0=2451545.0,      # J2000.0 reference epoch (Julian Day)
    custom_ayanamsa_ayan_t0=23.5,       # Ayanamsa offset at epoch (degrees)
)

print(f"Sun (Custom): {custom.sun.sign} {custom.sun.position:.2f}")
print(f"Ayanamsa value: {custom.ayanamsa_value:.4f}")
```

> Both `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0` are required when using `sidereal_mode="USER"`. Omitting either will raise a `KerykeionException`.

## Accessing the Ayanamsa Value

For any sidereal chart, the computed ayanamsa offset (in degrees) is available via `ayanamsa_value`:

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Ayanamsa Check", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
)

print(f"Ayanamsa value: {subject.ayanamsa_value:.4f}°")
# e.g. 23.7234° -- the tropical-sidereal offset for this date
```

> `ayanamsa_value` is `None` for tropical charts.

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

![John Lennon Lahiri](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/tests/data/svg/John%20Lennon%20Lahiri%20-%20Natal%20Chart.svg)

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

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
