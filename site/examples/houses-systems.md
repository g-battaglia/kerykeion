---
title: 'Houses Systems'
tags: ['examples', 'houses', 'systems', 'charts', 'kerykeion']
order: 7
---

# House Systems

Kerykeion supports **23 different house systems** (Swiss Ephemeris letter codes, honoured by both backends). Each system divides the celestial sphere differently, affecting house cusp positions (though planetary positions remain the same).

## Choosing a House System

The choice of house system depends on your astrological tradition and preferences:

- **Modern Western**: Placidus (default) or Koch
- **Traditional/Hellenistic**: Whole Sign or Porphyry
- **Medieval**: Regiomontanus or Alcabitius
- **Vedic/Jyotish**: Whole Sign or Sripati
- **Horary**: Regiomontanus
- **Inside the polar circle**: Whole Sign, Equal or Porphyry — the quadrant
  systems are undefined there and Kerykeion substitutes one for them (see below)

## Complete House Systems Reference

| ID  | Name                        | Description |
|:---:|:---------------------------|:------------|
| `P` | **Placidus** | **Default.** Most popular in modern Western astrology. Time-based system that divides the diurnal arc into equal time segments. Undefined inside the polar circle. |
| `K` | **Koch** | Popular in Germany and for natal work. Similar to Placidus but uses birthplace latitude differently. Also undefined inside the polar circle. |
| `W` | **Whole Sign** | Ancient system where each house equals one entire zodiac sign. The Ascendant's sign becomes the 1st house. Works at all latitudes. Preferred in Hellenistic and Vedic astrology. |
| `A` | Equal (from Asc) | Houses are exactly 30° each, starting from the Ascendant degree. Simple and works at all latitudes. |
| `D` | Equal (from MC) | Equal 30° houses with the MC on the 10th house cusp. |
| `V` | Equal/Vehlow | Equal houses with the Ascendant in the *middle* of the 1st house rather than at its cusp. |
| `N` | Equal/1=Aries | Fixed houses where 0° Aries is always the 1st house cusp. |
| `O` | Porphyry | Simple quadrant-based system. Divides each quadrant into three equal parts. Ancient and reliable. |
| `R` | **Regiomontanus** | Medieval space-based system. Standard for horary astrology. Divides the celestial equator. |
| `C` | Campanus | Space-based system using the prime vertical. Popular among some traditional astrologers. |
| `B` | Alcabitius | Medieval semi-arc system. Was standard in Arabic and medieval European astrology. |
| `M` | Morinus | Equator-based system. Unique in that the Ascendant is not necessarily on the 1st house cusp. |
| `T` | Polich/Page (Topocentric) | Similar to Placidus but accounts for the observer's exact position on Earth. Very accurate for the Moon. |
| `S` | Sripati | Vedic-influenced system. Midpoint-based similar to Porphyry. |
| `H` | Horizon/Azimuth | Based on the local horizon and azimuth circle. |
| `I` | Sunshine | Modern system based on solar position. |
| `i` | Sunshine/Alternate | Alternate calculation of the Sunshine system. |
| `L` | Pullen SD | Modern Sinusoidal Delta system. |
| `Q` | Pullen SR | Modern Sinusoidal Ratio system. |
| `U` | Krusinski-Pisa-Goelzer | Modern house system. |
| `X` | Axial Rotation/Meridian | Based on the meridian circle. |
| `Y` | APC Houses | Astrological PC houses system. |
| `F` | Carter Poli-Equatorial | Rarely used system developed by Charles Carter. |

## Examples

### Birth Chart with Morinus House System

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer

morinus_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - House System Morinus", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    houses_system_identifier="M",
)
data = ChartDataFactory.create_natal_chart_data(morinus_subject)
chart = ChartDrawer(data)

out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=out_dir, filename="john-lennon-morinus", style="classic")
```

The output will be:

![John Lennon - House System Morinus](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/alpha/v6/tests/data/svg/John%20Lennon%20-%20House%20System%20Morinus%20-%20Natal%20Chart%20-%20Classic.svg)

### Birth Chart with Whole Sign Houses

```python
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer

whole_sign_subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon - Whole Sign", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London",
    online=False,
    houses_system_identifier="W",
)
data = ChartDataFactory.create_natal_chart_data(whole_sign_subject)
chart = ChartDrawer(data)

out_dir = Path("charts_output")
out_dir.mkdir(exist_ok=True)
chart.save_svg(output_path=out_dir, filename="john-lennon-whole-sign")
```

### Check House System Name on a Subject

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Johnny Depp", 1963, 6, 9, 0, 0,
    lng=-87.1112,
    lat=37.7719,
    tz_str="America/Chicago",
    online=False,
    houses_system_identifier="P",  # Placidus
)

print(subject.houses_system_name)
# Output: Placidus
```

### Comparing House Systems

```python
from kerykeion import AstrologicalSubjectFactory

# Same birth data, different house systems
systems = {"P": "Placidus", "K": "Koch", "W": "Whole Sign", "R": "Regiomontanus"}

for system_id, label in systems.items():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Test", 1990, 6, 15, 12, 0,
        lng=-0.1276, lat=51.5074, tz_str="Europe/London",
        online=False,
        houses_system_identifier=system_id,
    )
    print(f"{label}:")
    print(f"  1st House: {subject.first_house.sign} {subject.first_house.position:.1f}°")
    print(f"  10th House (MC): {subject.tenth_house.sign} {subject.tenth_house.position:.1f}°")
```

**Output:**
```
Placidus:
  1st House: Vir 14.7°
  10th House (MC): Gem 10.0°
Koch:
  1st House: Vir 14.7°
  10th House (MC): Gem 10.0°
Whole Sign:
  1st House: Vir 0.0°
  10th House (MC): Gem 0.0°
Regiomontanus:
  1st House: Vir 14.7°
  10th House (MC): Gem 10.0°
```

> **Note:** The Ascendant and MC remain the same across most systems - only the intermediate house cusps differ.

## Inside the Polar Circle

A quadrant system divides the semi-diurnal arc of a degree of the ecliptic.
Inside the polar circle some degrees never rise or set, so that arc does not
exist and there is nothing to divide. Kerykeion does not fail there, and does not
move the observer either: it recomputes the cusps with **Porphyry** (`"O"`) at
the real latitude, logs a warning naming both systems, and records the
substitution.

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Arctic Explorer", 1990, 6, 21, 12, 0,
    lng=25.0, lat=70.0, tz_str="Europe/Helsinki", online=False,
    houses_system_identifier="P",
)

print(subject.lat)                                 # 70.0  — never clamped
print(subject.houses_system_identifier)            # "P"   — what you asked for
print(subject.effective_houses_system_identifier)  # "O"   — what the cusps used
print(subject.polar_house_fallbacks[0].affects)    # ["house_cusps"]
```

The angles are untouched: the Ascendant, MC, Descendant, IC and Vertex are
intersections of the ecliptic with the horizon and the meridian, so they do not
depend on a house system and stay exact at any latitude. Pick `"W"` or `"A"` if
you would rather choose the division yourself than accept a substitute.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
