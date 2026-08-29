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
# doc-snippet: no-run — illustrative fragment
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
# doc-snippet: no-run — illustrative fragment
print(subject.first_house.sign)  # The Ascendant sign
print(subject.ascendant.position)  # Exact degree
```

### Midheaven (MC - Medium Coeli)
The highest point in the chart, representing career and public image. The cusp of the 10th house in most house systems.

**In Kerykeion:**
```python
# doc-snippet: no-run — illustrative fragment
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
# doc-snippet: no-run — illustrative fragment
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

### Perigee / Apogee
The two ends of the Moon's orbit around the Earth: the perigee is the point nearest the Earth, the apogee the point farthest from it. They are the Moon's **apsides**. The names *perihelion* and *aphelion* mean the same two ends of an orbit around the **Sun**, which is what the eight planets go round — so they are wrong for the Moon, and the apogee is precisely the point the tradition calls the Black Moon Lilith.

> **In Kerykeion:** `PlanetaryNodesFactory` reports both ends of every orbit as `periapsis` / `apoapsis`, with `apsis_kind` saying which body they are measured against (`"geocentric"` for the Moon alone). The Moon's `apoapsis` equals `mean_lilith` with `method="mean"` and `true_lilith` with `method="osculating"`. The older `perihelion` / `aphelion` fields are deprecated but still populated.

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
# doc-snippet: no-run — illustrative fragment
# Aspect data includes orb
aspect.orbit  # The actual deviation from exact
```

### Applying vs Separating
- **Applying**: Planets moving toward exact aspect (considered stronger)
- **Separating**: Planets moving away from exact aspect

---

## Dignities & Debilities

### Domicile (Rulership)
A planet in the sign it rules. The planet operates at full strength. For example, Mars in Aries or Venus in Taurus.

### Exaltation
A planet in the sign where it is considered especially powerful (though not its ruler). For example, the Sun is exalted in Aries, the Moon in Taurus.

### Detriment
A planet in the sign opposite its domicile. Considered weakened or challenged. For example, Mars in Libra (opposite Aries).

### Fall
A planet in the sign opposite its exaltation. Considered at its weakest dignity. For example, the Sun in fall in Libra (opposite Aries).

### Peregrine
A planet with no essential dignity in its current sign — not in domicile, exaltation, triplicity, term, or face. Sometimes described as "wandering."

### Decanate (Decan)
Each zodiac sign is divided into three 10° segments called decanates (or decans). The first decan spans 0°-10°, the second 10°-20°, the third 20°-30°. Each decan has its own sub-ruler, adding nuance to interpretation.

---

## Technical Terms

### Ayanamsa
The angular difference between tropical and sidereal zodiacs. Different ayanamsas (like Lahiri or Fagan-Bradley) define different starting points.

### Retrograde
When a planet appears to move backward through the zodiac due to relative orbital positions. Significant in interpretation.

**In Kerykeion:**
```python
# doc-snippet: no-run — illustrative fragment
if subject.mercury.retrograde:
    print("Mercury is retrograde")
```

### Declination
A planet's angular distance north or south of the celestial equator. Planets with the same declination are "in parallel."

### Ephemeris
Tables showing planetary positions for each day. Kerykeion uses libephemeris (based on NASA JPL ephemerides) for high-precision calculations by default, with the Swiss Ephemeris available as an opt-in backend.

### Julian Day
A continuous count of days since January 1, 4713 BCE. Used internally for astronomical calculations.

**In Kerykeion:**
```python
# doc-snippet: no-run — illustrative fragment
print(subject.julian_day)
```

### Void-of-Course Moon
The period after the Moon makes its last major aspect in a sign and before it enters the next sign. Traditionally considered an unfavorable time for initiating new actions. Duration varies from minutes to over a day.

> **In Kerykeion:** Use `VoidOfCourseMoonFactory` to compute the void-of-course state for any moment — it returns the void window, the current/next sign, and the framing last/next aspects:

```python
from kerykeion import VoidOfCourseMoonFactory

voc = VoidOfCourseMoonFactory.from_datetime(2026, 6, 1, 9, 0, tz_str="Europe/Rome")
print(voc.is_void_of_course, voc.moon_sign, voc.next_sign)  # True Sag Cap
```

### Progressed Chart
A forecasting technique where each day after birth corresponds to one year of life (secondary progressions). For example, the planetary positions 30 days after birth represent the progressed chart for age 30.

> **Note:** Kerykeion implements secondary progressions via `SecondaryProgressionFactory` and solar arc directions via `SolarArcFactory`. Both are available from `from kerykeion import SecondaryProgressionFactory, SolarArcFactory`.

### Midpoint
The zodiacal longitude exactly halfway between two planets on the shorter arc. Central to cosmobiology (Ebertin) and Uranian/Hamburg-school astrology. When a third planet sits on a midpoint, it "activates" the pair.

> **In Kerykeion:** Use `MidpointFactory.compute(subject)` to calculate all pairwise midpoints with aspect activations.

### Primary Directions
The oldest predictive technique in Western astrology. Measures the arc a promissor planet travels along the equator to reach the position of a significator. Each degree of arc equals approximately one year of life (Ptolemy's key).

> **In Kerykeion:** Use `PrimaryDirectionsFactory.compute(subject, max_years=80)`.

### Heliacal Rising
The first morning a celestial body becomes visible above the eastern horizon just before sunrise after a period of invisibility (hidden by the Sun's glare). Heliacal settings are the opposite: the last evening visibility before the body disappears into the Sun's glare.

> **In Kerykeion:** Use `HeliacalFactory().next_heliacal_rising(jd, planet, geopos)`.

### Cazimi, Combust, Under the Beams
Three classical names for how near the Sun a body stands, read as a condition of visibility rather than as a number of degrees. From the closest outwards:

| Term | Meaning | Default cut-off |
|:-----|:--------|:----------------|
| **Cazimi** | In the heart of the Sun | within 0.2833° (17 arcminutes) |
| **Combust** | Burnt; invisible in the glare | within 8.5° |
| **Under the Beams** | Still inside the Sun's rays | within 17° |
| **Free** | Far enough to be seen in a dark sky | 17° or more |

The cut-offs are conventions, not measurements, and the schools disagree on all three — some read the beams at 15°, some scale combustion by planet.

> **In Kerykeion:** every `PlanetaryPhenomenaModel` carries `solar_phase` (`"cazimi"` / `"combust"` / `"under_the_beams"` / `"free"`), read against the collection's `solar_phase_thresholds`, which you may replace. Note that `is_morning_star` / `is_evening_star` are purely geometric — which side of the Sun the planet stands on — and say nothing about visibility.

### Major Phase (Moon)
The nearest of the Moon's four syzygy/quadrature events — New Moon, First Quarter, Full Moon, Last Quarter — to a given moment. The eight-name phase (`Waxing Crescent`, `Waning Gibbous`, …) says where in the cycle the Moon is; the major phase says which of the four turning points it is closest to, and `stage` says whether it is `"waxing"` or `"waning"`.

> **In Kerykeion:** `subject.lunar_phase.major_phase` / `.stage`, and the same two fields on `MoonPhaseDetailsFactory`'s `overview.moon`.

### Occultation
An event where the Moon passes in front of a planet or star as seen from Earth, temporarily hiding it from view. Similar to an eclipse, but involving a body other than the Sun.

> **In Kerykeion:** Use `OccultationFactory().search_global(jd, planet_id)`.

### Astro-Cartography (ACG)
A mapping technique showing where each planet's angular lines (ASC, DSC, MC, IC) fall across the globe. Used for relocation astrology: living near a planet's line activates its themes.

> **In Kerykeion:** Use `AstroCartographyFactory.compute(subject)`.

### Eclipse
The alignment of Sun, Moon, and Earth. Solar eclipses occur at New Moon (Moon between Sun and Earth); lunar eclipses at Full Moon (Earth between Sun and Moon). Eclipses near natal points are considered powerful triggers.

> **In Kerykeion:** Use `EclipseFactory.search_global()` or `EclipseFactory.search_from_location()`.

### Parallel / Contra-Parallel
Declination-based aspects. A parallel is when two planets have the same declination (both north or both south of the equator); a contra-parallel is when they have equal declination but opposite signs (one north, one south). Parallels act like conjunctions, contra-parallels like oppositions.

> **In Kerykeion:** Use `AspectsFactory.single_chart_declination_aspects(subject)`.

---

## Chart Types

### Synastry Chart
Overlays two natal charts to analyze relationship compatibility. Shows how one person's planets aspect the other's.

```python
# doc-snippet: no-run — illustrative fragment
synastry_data = ChartDataFactory.create_synastry_chart_data(person1, person2)
```

### Composite Chart
Creates a single chart from the midpoints of two people's charts. Represents the relationship itself as an entity.

```python
# doc-snippet: no-run — illustrative fragment
composite = CompositeSubjectFactory(person1, person2).get_midpoint_composite_subject_model()
```

### Transit Chart
Compares current planetary positions to a natal chart. Used for timing and prediction.

```python
# doc-snippet: no-run — illustrative fragment
transit_data = ChartDataFactory.create_transit_chart_data(natal_subject, transit_subject)
```

### Solar Return Chart
The chart for the moment the Sun returns to its exact natal position each year. Used for annual forecasts.

```python
# doc-snippet: no-run — illustrative fragment
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
# doc-snippet: no-run — illustrative fragment
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
# doc-snippet: no-run — illustrative fragment
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

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
