---
title: 'Glossary'
description: 'Astrological terms and concepts explained for developers'
category: 'Getting Started'
tags: ['docs', 'glossary', 'terms', 'astrology', 'reference']
order: 4
---

# Glossary of Astrological Terms

This glossary explains astrological concepts used in Kerykeion, designed for developers who may be new to astrology.

## Chart Components

### Natal Chart (Birth Chart)
A map of the sky at the exact moment and location of birth. Shows the positions of celestial bodies in the zodiac signs and houses.

**In Kerykeion:**
```python
chart_data = ChartDataFactory.create_natal_chart_data(subject)
```

### Zodiac
The 12-sign system used to divide the ecliptic (the Sun's apparent path). Each sign spans 30°.

**Types:**
- **Tropical** (default): Based on the seasons. 0° Aries = spring equinox.
- **Sidereal**: Based on fixed stars. Used in Vedic astrology.

### Houses
The 12 divisions of the chart representing different life areas. Unlike signs (which are celestial), houses are based on the observer's location on Earth.

| House | Life Area |
|:------|:----------|
| 1st | Self, identity, appearance |
| 2nd | Money, possessions, values |
| 3rd | Communication, siblings, local travel |
| 4th | Home, family, roots |
| 5th | Creativity, romance, children |
| 6th | Health, daily work, service |
| 7th | Partnerships, marriage |
| 8th | Transformation, shared resources |
| 9th | Philosophy, travel, higher education |
| 10th | Career, public image |
| 11th | Friends, groups, hopes |
| 12th | Subconscious, secrets, spirituality |

### Ascendant (Rising Sign)
The zodiac sign rising on the eastern horizon at the time of birth. Determines the 1st house cusp and is one of the most important chart points.

**In Kerykeion:**
```python
print(subject.first_house.sign)  # The Ascendant sign
print(subject.ascendant.position)  # Exact degree
```

### Midheaven (MC - Medium Coeli)
The highest point in the chart, representing career and public image. The cusp of the 10th house in most house systems.

**In Kerykeion:**
```python
print(subject.tenth_house.sign)
print(subject.medium_coeli.position)
```

### Descendant (DC)
The point opposite the Ascendant, representing partnerships. The cusp of the 7th house.

### Imum Coeli (IC)
The lowest point in the chart, opposite the MC. Represents home and roots. The cusp of the 4th house.

---

## Celestial Bodies

### Planets
In astrology, "planets" includes the Sun and Moon (called "luminaries"), plus Mercury through Pluto.

| Planet | Represents | Orbit |
|:-------|:-----------|:------|
| **Sun** | Core identity, ego, vitality | 1 year |
| **Moon** | Emotions, instincts, habits | 28 days |
| **Mercury** | Communication, thinking | 88 days |
| **Venus** | Love, beauty, values | 225 days |
| **Mars** | Action, energy, desire | 2 years |
| **Jupiter** | Expansion, luck, wisdom | 12 years |
| **Saturn** | Structure, discipline, limits | 29 years |
| **Uranus** | Innovation, rebellion | 84 years |
| **Neptune** | Dreams, spirituality, illusion | 165 years |
| **Pluto** | Transformation, power | 248 years |

### Lunar Nodes
The points where the Moon's orbit crosses the ecliptic. Related to karmic themes.

- **North Node (Rahu)**: Future direction, growth
- **South Node (Ketu)**: Past patterns, comfort zone

**In Kerykeion:**
```python
# True nodes (oscillating)
print(subject.true_north_lunar_node)
print(subject.true_south_lunar_node)

# Mean nodes (averaged)
print(subject.mean_north_lunar_node)
print(subject.mean_south_lunar_node)
```

### Chiron
A "centaur" asteroid representing wounds and healing.

### Lilith (Black Moon)
The lunar apogee, associated with shadow self and repressed desires.

- **Mean Lilith**: Averaged position
- **True Lilith**: Oscillating position

### Asteroids
Minor bodies in the asteroid belt:
- **Ceres**: Nurturing, agriculture
- **Pallas**: Wisdom, strategy
- **Juno**: Partnerships, commitment
- **Vesta**: Focus, dedication

### Arabic Parts (Lots)
Calculated points based on formulas involving other chart positions:
- **Part of Fortune (Pars Fortunae)**: Luck, prosperity
- **Part of Spirit (Pars Spiritus)**: Soul purpose

---

## Aspects

Angular relationships between planets that create energetic connections.

### Major Aspects

| Aspect | Degrees | Symbol | Nature |
|:-------|:--------|:-------|:-------|
| **Conjunction** | 0° | ☌ | Fusion, intensity |
| **Opposition** | 180° | ☍ | Polarity, awareness |
| **Trine** | 120° | △ | Harmony, ease |
| **Square** | 90° | □ | Tension, growth |
| **Sextile** | 60° | ⚹ | Opportunity |

### Minor Aspects

| Aspect | Degrees | Nature |
|:-------|:--------|:-------|
| **Semi-sextile** | 30° | Slight adjustment |
| **Semi-square** | 45° | Minor friction |
| **Quintile** | 72° | Creative talent |
| **Sesquiquadrate** | 135° | Agitation |
| **Quincunx** | 150° | Adjustment needed |
| **Biquintile** | 144° | Creative expression |

### Orb
The tolerance in degrees for an aspect to be considered active. A conjunction with 8° orb means planets within 8° of each other are "in conjunction."

**In Kerykeion:**
```python
# Aspect data includes orb
aspect.orbit  # The actual deviation from exact
```

### Applying vs Separating
- **Applying**: Planets moving toward exact aspect (considered stronger)
- **Separating**: Planets moving away from exact aspect

---

## Technical Terms

### Ayanamsa
The angular difference between tropical and sidereal zodiacs. Different ayanamsas (like Lahiri or Fagan-Bradley) define different starting points.

### Retrograde
When a planet appears to move backward through the zodiac due to relative orbital positions. Significant in interpretation.

**In Kerykeion:**
```python
if subject.mercury.retrograde:
    print("Mercury is retrograde")
```

### Declination
A planet's angular distance north or south of the celestial equator. Planets with the same declination are "in parallel."

### Ephemeris
Tables showing planetary positions for each day. Kerykeion uses the Swiss Ephemeris for high-precision calculations.

### Julian Day
A continuous count of days since January 1, 4713 BCE. Used internally for astronomical calculations.

**In Kerykeion:**
```python
print(subject.julian_day)
```

---

## Chart Types

### Synastry Chart
Overlays two natal charts to analyze relationship compatibility. Shows how one person's planets aspect the other's.

```python
synastry_data = ChartDataFactory.create_synastry_chart_data(person1, person2)
```

### Composite Chart
Creates a single chart from the midpoints of two people's charts. Represents the relationship itself as an entity.

```python
composite = CompositeSubjectFactory(person1, person2).get_midpoint_composite_subject_model()
```

### Transit Chart
Compares current planetary positions to a natal chart. Used for timing and prediction.

```python
transit_data = ChartDataFactory.create_transit_chart_data(natal_subject, transit_subject)
```

### Solar Return Chart
The chart for the moment the Sun returns to its exact natal position each year. Used for annual forecasts.

```python
return_subject = PlanetaryReturnFactory(natal, ...).next_return_from_date(2024, 1, 1, return_type="Solar")
```

### Lunar Return Chart
The chart for the Moon returning to its natal position (approximately monthly).

---

## Elements & Qualities

### Elements (Triplicities)
The four classical elements each ruling three signs:

| Element | Signs | Traits |
|:--------|:------|:-------|
| **Fire** | Aries, Leo, Sagittarius | Action, enthusiasm |
| **Earth** | Taurus, Virgo, Capricorn | Practicality, stability |
| **Air** | Gemini, Libra, Aquarius | Intellect, communication |
| **Water** | Cancer, Scorpio, Pisces | Emotion, intuition |

### Qualities (Modalities)
Three modes describing how signs express energy:

| Quality | Signs | Traits |
|:--------|:------|:-------|
| **Cardinal** | Aries, Cancer, Libra, Capricorn | Initiating, leading |
| **Fixed** | Taurus, Leo, Scorpio, Aquarius | Stable, persistent |
| **Mutable** | Gemini, Virgo, Sagittarius, Pisces | Adaptable, flexible |

**In Kerykeion:**
```python
print(chart_data.element_distribution.fire_percentage)
print(chart_data.quality_distribution.cardinal_percentage)
```

---

## Lunar Phases

| Phase | Description |
|:------|:------------|
| **New Moon** | Moon conjunct Sun. New beginnings. |
| **Waxing Crescent** | Building intention. |
| **First Quarter** | Action, challenges. |
| **Waxing Gibbous** | Refinement. |
| **Full Moon** | Culmination, illumination. |
| **Waning Gibbous** | Sharing, gratitude. |
| **Last Quarter** | Letting go. |
| **Waning Crescent** | Rest, surrender. |

**In Kerykeion:**
```python
print(subject.lunar_phase.moon_phase_name)
print(subject.lunar_phase.moon_emoji)
```

---

## House Systems

Different methods for calculating house cusps:

| System | Description | Best For |
|:-------|:------------|:---------|
| **Placidus** | Time-based, most popular | General use |
| **Whole Sign** | Each house = one sign | Traditional, Vedic |
| **Koch** | Similar to Placidus | Natal charts |
| **Regiomontanus** | Space-based | Horary astrology |
| **Equal** | 30° each from Asc | Simplicity |
| **Campanus** | Prime vertical | Traditional |

See [House Systems](/content/examples/houses-systems) for the complete list.
