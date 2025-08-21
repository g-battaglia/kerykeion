# Aspects Module

The Aspects module provides comprehensive astrological aspect analysis through a unified `AspectsFactory` class. It calculates angular relationships between celestial points within individual charts or between multiple charts, making it essential for understanding planetary interactions, compatibility analysis, and timing in astrological practice.

## Overview

Astrological aspects are geometric relationships between planets and points measured in degrees along the zodiac. These angular relationships reveal how planetary energies interact, creating harmonious or challenging dynamics that influence personality traits, life events, and relationships.

The `AspectsFactory` provides a unified approach to aspect calculation with two primary methods:
- **`single_chart_aspects()`**: Analyzes aspects within one chart (natal, return, composite, etc.)
- **`dual_chart_aspects()`**: Analyzes aspects between two charts (synastry, transits, comparisons, etc.)

This unified design eliminates the complexity of managing separate classes while providing specialized functionality for different types of astrological analysis.

## Fundamental Concepts

### Aspect Types

The module calculates both major and minor aspects with customizable orb tolerances:

**Major Aspects** (Traditional):
- **Conjunction (0°)**: Planetary energies blend and intensify
- **Opposition (180°)**: Polarized energies creating tension or balance
- **Trine (120°)**: Harmonious flow of energies
- **Square (90°)**: Dynamic tension and challenge
- **Sextile (60°)**: Cooperative and supportive energies

**Minor Aspects** (Extended Analysis):
- **Semi-sextile (30°)**: Subtle supportive connection
- **Semi-square (45°)**: Minor friction requiring adjustment
- **Quintile (72°)**: Creative and spiritual talents
- **Sesquiquadrate (135°)**: Persistent challenge requiring resolution
- **Biquintile (144°)**: Enhanced creative expression
- **Quincunx/Inconjunct (150°)**: Adjustment and integration needed

### Orb Tolerances

Orbs determine how close to exact an aspect needs to be to be considered valid:

- **Standard Orbs**: Vary by aspect type (typically 6-10° for major aspects, 1-3° for minor)
- **Axes Orbs**: Stricter limits for chart angles (Ascendant, Midheaven, Descendant, IC)
- **Tight Aspects**: Aspects within 1-2° are considered particularly significant
- **Custom Orbs**: Configurable for specialized analysis needs

### Chart Types Supported

The unified factory works with all chart types:
- **Natal Charts**: Birth chart aspects revealing personality dynamics
- **Planetary Returns**: Solar, lunar, and other planetary return charts
- **Composite Charts**: Blended relationship charts
- **Transit Charts**: Current planetary positions
- **Progressed Charts**: Evolved natal positions over time

## Single Chart Aspects Analysis

Single chart analysis examines aspects within one astrological chart, revealing internal planetary dynamics and personality patterns.

### Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects import AspectsFactory

# Create a natal chart
person = AstrologicalSubjectFactory.from_birth_data(
    name="Maria Garcia",
    year=1985, month=7, day=22,
    hour=14, minute=30,
    city="Barcelona", 
    nation="ES"
)

# Calculate single chart aspects
chart_aspects = AspectsFactory.single_chart_aspects(person)

print(f"Analyzing {person.name}'s natal chart:")
print(f"Total aspects found: {len(chart_aspects.all_aspects)}")
print(f"Relevant aspects: {len(chart_aspects.relevant_aspects)}")

# Examine the strongest aspects (tightest orbs)
print("\nStrongest aspects:")
sorted_aspects = sorted(chart_aspects.relevant_aspects, key=lambda x: abs(x.orbit))
for i, aspect in enumerate(sorted_aspects[:5], 1):
    print(f"{i}. {aspect.p1_name} {aspect.aspect} {aspect.p2_name} (orb: {aspect.orbit:+.2f}°)")
```

**Output example:**
```
Analyzing Maria Garcia's natal chart:
Total aspects found: 45
Relevant aspects: 42

Strongest aspects:
1. Sun conjunction Mercury (orb: +0.23°)
2. Moon trine Jupiter (orb: -0.45°)
3. Venus sextile Mars (orb: +0.67°)
4. Saturn square Ascendant (orb: -0.89°)
5. Jupiter trine Midheaven (orb: +1.12°)
```

### Aspect Pattern Analysis

```python
# Analyze aspect patterns and distributions
def analyze_aspect_patterns(chart_aspects):
    """Comprehensive aspect pattern analysis"""
    
    # Group aspects by type
    aspect_types = {}
    for aspect in chart_aspects.relevant_aspects:
        aspect_type = aspect.aspect
        if aspect_type not in aspect_types:
            aspect_types[aspect_type] = []
        aspect_types[aspect_type].append(aspect)
    
    print("=== ASPECT PATTERN ANALYSIS ===")
    
    # Count by aspect type
    print("\nAspect Distribution:")
    for aspect_type, aspects in sorted(aspect_types.items()):
        avg_orb = sum(abs(a.orbit) for a in aspects) / len(aspects)
        print(f"  {aspect_type}: {len(aspects)} aspects (avg orb: {avg_orb:.2f}°)")
    
    # Analyze planetary involvement
    planet_involvement = {}
    for aspect in chart_aspects.relevant_aspects:
        for planet in [aspect.p1_name, aspect.p2_name]:
            planet_involvement[planet] = planet_involvement.get(planet, 0) + 1
    
    print("\nMost Aspected Planets:")
    sorted_planets = sorted(planet_involvement.items(), key=lambda x: x[1], reverse=True)
    for planet, count in sorted_planets[:5]:
        print(f"  {planet}: {count} aspects")
    
    # Identify tight aspects (within 1 degree)
    tight_aspects = [a for a in chart_aspects.relevant_aspects if abs(a.orbit) <= 1.0]
    print(f"\nTight Aspects (≤1°): {len(tight_aspects)}")
    for aspect in sorted(tight_aspects, key=lambda x: abs(x.orbit)):
        print(f"  {aspect.p1_name} {aspect.aspect} {aspect.p2_name} (orb: {aspect.orbit:+.2f}°)")
    
    return aspect_types, planet_involvement, tight_aspects

# Example usage
patterns, involvement, tight = analyze_aspect_patterns(chart_aspects)
```

**Output example:**
```
=== ASPECT PATTERN ANALYSIS ===

Aspect Distribution:
  conjunction: 8 aspects (avg orb: 2.34°)
  opposition: 6 aspects (avg orb: 3.45°)
  square: 9 aspects (avg orb: 2.78°)
  trine: 11 aspects (avg orb: 3.12°)
  sextile: 8 aspects (avg orb: 2.89°)

Most Aspected Planets:
  Sun: 9 aspects
  Moon: 8 aspects
  Venus: 7 aspects
  Mars: 6 aspects
  Jupiter: 6 aspects

Tight Aspects (≤1°): 4
  Sun conjunction Mercury (orb: +0.23°)
  Moon trine Jupiter (orb: -0.45°)
  Venus sextile Mars (orb: +0.67°)
  Saturn square Ascendant (orb: -0.89°)
```

## Dual Chart Aspects Analysis

Dual chart analysis compares aspects between two different charts, essential for relationship compatibility, transit analysis, and comparative astrology.

### Synastry Analysis

```python
# Comprehensive relationship compatibility analysis
def synastry_compatibility_analysis(person1, person2):
    """Complete synastry analysis with multiple perspectives"""
    
    # Calculate dual chart aspects
    synastry = AspectsFactory.dual_chart_aspects(person1, person2)
    
    print(f"=== SYNASTRY ANALYSIS ===")
    print(f"{person1.name} & {person2.name}")
    print(f"Total aspects: {len(synastry.all_aspects)}")
    print(f"Relevant aspects: {len(synastry.relevant_aspects)}")
    
    # Categorize aspects by harmony
    harmonious = []
    challenging = []
    neutral = []
    
    harmonious_aspects = ["conjunction", "trine", "sextile"]
    challenging_aspects = ["opposition", "square"]
    
    for aspect in synastry.relevant_aspects:
        if aspect.aspect in harmonious_aspects:
            harmonious.append(aspect)
        elif aspect.aspect in challenging_aspects:
            challenging.append(aspect)
        else:
            neutral.append(aspect)
    
    print(f"\nAspect Quality Distribution:")
    print(f"  Harmonious: {len(harmonious)} aspects")
    print(f"  Challenging: {len(challenging)} aspects")
    print(f"  Neutral/Mixed: {len(neutral)} aspects")
    
    # Compatibility ratio
    if len(challenging) > 0:
        harmony_ratio = len(harmonious) / len(challenging)
        print(f"  Harmony Ratio: {harmony_ratio:.2f}")
    else:
        print(f"  Harmony Ratio: Perfect (no challenging aspects)")
    
    # Analyze by planetary combinations
    love_aspects = []
    passion_aspects = []
    communication_aspects = []
    
    for aspect in synastry.relevant_aspects:
        planets = {aspect.p1_name, aspect.p2_name}
        
        if "Venus" in planets or "Moon" in planets:
            love_aspects.append(aspect)
        if "Mars" in planets or "Pluto" in planets:
            passion_aspects.append(aspect)
        if "Mercury" in planets:
            communication_aspects.append(aspect)
    
    print(f"\nRelationship Themes:")
    print(f"  Love & Emotional Connection: {len(love_aspects)} aspects")
    print(f"  Passion & Energy: {len(passion_aspects)} aspects")
    print(f"  Communication: {len(communication_aspects)} aspects")
    
    # Show strongest connections
    print(f"\nStrongest Connections:")
    strongest = sorted(synastry.relevant_aspects, key=lambda x: abs(x.orbit))[:5]
    for i, aspect in enumerate(strongest, 1):
        print(f"  {i}. {aspect.p1_owner}'s {aspect.p1_name} {aspect.aspect} {aspect.p2_owner}'s {aspect.p2_name} (orb: {aspect.orbit:+.2f}°)")
    
    return synastry

# Example relationship analysis
person1 = AstrologicalSubjectFactory.from_birth_data(
    name="Alessandro", year=1988, month=3, day=15, hour=10, minute=45,
    city="Rome", nation="IT"
)

person2 = AstrologicalSubjectFactory.from_birth_data(
    name="Sofia", year=1990, month=9, day=23, hour=16, minute=20,
    city="Milan", nation="IT"
)

relationship_analysis = synastry_compatibility_analysis(person1, person2)
```

**Output example:**
```
=== SYNASTRY ANALYSIS ===
Alessandro & Sofia
Total aspects: 78
Relevant aspects: 73

Aspect Quality Distribution:
  Harmonious: 32 aspects
  Challenging: 18 aspects
  Neutral/Mixed: 23 aspects
  Harmony Ratio: 1.78

Relationship Themes:
  Love & Emotional Connection: 15 aspects
  Passion & Energy: 12 aspects
  Communication: 8 aspects

Strongest Connections:
  1. Alessandro's Venus conjunction Sofia's Sun (orb: +0.34°)
  2. Sofia's Moon trine Alessandro's Jupiter (orb: -0.67°)
  3. Alessandro's Mars sextile Sofia's Venus (orb: +0.89°)
  4. Sofia's Mercury conjunction Alessandro's Mercury (orb: +1.12°)
  5. Alessandro's Sun opposition Sofia's Saturn (orb: -1.45°)
```

### Transit Analysis

```python
# Analyze current transits to natal chart
from datetime import datetime

def current_transits_analysis(natal_person, transit_date=None):
    """Analyze current planetary transits to natal chart"""
    
    if transit_date is None:
        transit_date = datetime.now()
    
    # Create transit chart for current moment
    transit_chart = AstrologicalSubjectFactory.from_birth_data(
        name=f"Transits_{transit_date.strftime('%Y%m%d')}",
        year=transit_date.year,
        month=transit_date.month,
        day=transit_date.day,
        hour=transit_date.hour,
        minute=transit_date.minute,
        lat=natal_person.lat,
        lng=natal_person.lng,
        tz_str=natal_person.tz_str
    )
    
    # Calculate transits (dual chart aspects)
    transits = AspectsFactory.dual_chart_aspects(transit_chart, natal_person)
    
    print(f"=== CURRENT TRANSITS ANALYSIS ===")
    print(f"For: {natal_person.name}")
    print(f"Date: {transit_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"Active transits: {len(transits.relevant_aspects)}")
    
    # Group by transiting planet
    transit_planets = {}
    for aspect in transits.relevant_aspects:
        transiting_planet = aspect.p1_name  # Transit chart is first
        if transiting_planet not in transit_planets:
            transit_planets[transiting_planet] = []
        transit_planets[transiting_planet].append(aspect)
    
    print("\nTransits by Planet:")
    for planet, aspects in sorted(transit_planets.items()):
        if len(aspects) > 0:
            print(f"\n  {planet} transits:")
            for aspect in sorted(aspects, key=lambda x: abs(x.orbit)):
                natal_planet = aspect.p2_name
                print(f"    {aspect.aspect} natal {natal_planet} (orb: {aspect.orbit:+.2f}°)")
    
    # Highlight significant transits
    significant_transits = []
    significant_planets = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    
    for aspect in transits.relevant_aspects:
        if aspect.p1_name in significant_planets and abs(aspect.orbit) <= 2.0:
            significant_transits.append(aspect)
    
    if significant_transits:
        print(f"\nSignificant Outer Planet Transits (≤2° orb):")
        for aspect in sorted(significant_transits, key=lambda x: abs(x.orbit)):
            print(f"  {aspect.p1_name} {aspect.aspect} natal {aspect.p2_name} (orb: {aspect.orbit:+.2f}°)")
    
    return transits

# Example transit analysis
transit_analysis = current_transits_analysis(person)
```

## Customization and Configuration

### Custom Planetary Selection

```python
# Focus analysis on specific planetary combinations
from kerykeion.schemas.kr_literals import AstrologicalPoint

# Personal planets for core personality analysis
personal_planets = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars"
]

# Traditional seven planets
traditional_planets = personal_planets + [
    "Jupiter",
    "Saturn"
]

# Modern planets including outer planets
modern_planets = traditional_planets + [
    "Uranus",
    "Neptune",
    "Pluto"
]

# Chart angles and nodes
angles_and_nodes = [
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
    "True_Node",
    "True_South_Node"
]

# Example: Personal planets only analysis
personal_aspects = AspectsFactory.single_chart_aspects(
    person, 
    active_points=personal_planets
)

print(f"Personal planets aspects: {len(personal_aspects.relevant_aspects)}")

# Example: Synastry with traditional planets only
traditional_synastry = AspectsFactory.dual_chart_aspects(
    person1, person2,
    active_points=traditional_planets
)

print(f"Traditional synastry aspects: {len(traditional_synastry.relevant_aspects)}")
```

### Custom Aspect Configuration

```python
# Configure specific aspects and orb tolerances
from kerykeion.schemas.kr_models import ActiveAspect

# Tight orb configuration for precise analysis
tight_aspects = [
    ActiveAspect(name="conjunction", orb=6),
    ActiveAspect(name="opposition", orb=6),
    ActiveAspect(name="square", orb=4),
    ActiveAspect(name="trine", orb=4),
    ActiveAspect(name="sextile", orb=3)
]

# Wide orb configuration for comprehensive analysis
wide_aspects = [
    ActiveAspect(name="conjunction", orb=12),
    ActiveAspect(name="opposition", orb=12),
    ActiveAspect(name="square", orb=8),
    ActiveAspect(name="trine", orb=8),
    ActiveAspect(name="sextile", orb=6)
]

# Include minor aspects for detailed analysis
comprehensive_aspects = tight_aspects + [
    ActiveAspect(name="quintile", orb=2),
    ActiveAspect(name="semi-sextile", orb=2),
    ActiveAspect(name="semi-square", orb=2),
    ActiveAspect(name="sesquiquadrate", orb=2),
    ActiveAspect(name="biquintile", orb=2),
    ActiveAspect(name="quincunx", orb=3)
]

# Example: Tight orb natal analysis
precise_natal = AspectsFactory.single_chart_aspects(
    person,
    active_aspects=tight_aspects
)

# Example: Comprehensive synastry with minor aspects
detailed_synastry = AspectsFactory.dual_chart_aspects(
    person1, person2,
    active_aspects=comprehensive_aspects
)

print(f"Precise natal aspects: {len(precise_natal.relevant_aspects)}")
print(f"Detailed synastry aspects: {len(detailed_synastry.relevant_aspects)}")
```

## Advanced Analysis Techniques

### Aspect Quality Assessment

```python
def aspect_quality_analysis(aspects_result):
    """Analyze the overall quality and distribution of aspects"""
    
    aspect_qualities = {
        "conjunction": "neutral",  # Depends on planets involved
        "trine": "harmonious",
        "sextile": "harmonious", 
        "square": "challenging",
        "opposition": "challenging",
        "quintile": "creative",
        "semi-sextile": "mild_harmonious",
        "semi-square": "mild_challenging",
        "sesquiquadrate": "mild_challenging",
        "biquintile": "creative",
        "quincunx": "adjustment"
    }
    
    quality_counts = {
        "harmonious": 0,
        "challenging": 0,
        "neutral": 0,
        "creative": 0,
        "mild_harmonious": 0,
        "mild_challenging": 0,
        "adjustment": 0
    }
    
    orb_statistics = {
        "very_tight": 0,  # ≤ 1°
        "tight": 0,       # 1-2°
        "moderate": 0,    # 2-4°
        "wide": 0         # > 4°
    }
    
    for aspect in aspects_result.relevant_aspects:
        # Count by quality
        quality = aspect_qualities.get(aspect.aspect, "neutral")
        quality_counts[quality] += 1
        
        # Count by orb tightness
        orb = abs(aspect.orbit)
        if orb <= 1.0:
            orb_statistics["very_tight"] += 1
        elif orb <= 2.0:
            orb_statistics["tight"] += 1
        elif orb <= 4.0:
            orb_statistics["moderate"] += 1
        else:
            orb_statistics["wide"] += 1
    
    total_aspects = len(aspects_result.relevant_aspects)
    
    print(f"=== ASPECT QUALITY ANALYSIS ===")
    print(f"Total aspects analyzed: {total_aspects}")
    
    print(f"\nQuality Distribution:")
    for quality, count in quality_counts.items():
        if count > 0:
            percentage = (count / total_aspects) * 100
            print(f"  {quality.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    print(f"\nOrb Distribution:")
    for orb_range, count in orb_statistics.items():
        if count > 0:
            percentage = (count / total_aspects) * 100
            print(f"  {orb_range.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    # Calculate harmony index
    harmonious_total = quality_counts["harmonious"] + quality_counts["mild_harmonious"]
    challenging_total = quality_counts["challenging"] + quality_counts["mild_challenging"]
    
    if challenging_total > 0:
        harmony_index = harmonious_total / challenging_total
        print(f"\nHarmony Index: {harmony_index:.2f}")
        if harmony_index > 1.5:
            print("  Assessment: Predominantly harmonious")
        elif harmony_index > 0.7:
            print("  Assessment: Balanced")
        else:
            print("  Assessment: Predominantly challenging")
    else:
        print(f"\nHarmony Index: Perfect (no challenging aspects)")
    
    return quality_counts, orb_statistics

# Example quality analysis
natal_quality = aspect_quality_analysis(chart_aspects)
synastry_quality = aspect_quality_analysis(relationship_analysis)
```

### Aspect Pattern Recognition

```python
def identify_aspect_patterns(aspects_result):
    """Identify significant aspect patterns and configurations"""
    
    # Group aspects by planets
    planet_aspects = {}
    for aspect in aspects_result.relevant_aspects:
        for planet_name in [aspect.p1_name, aspect.p2_name]:
            if planet_name not in planet_aspects:
                planet_aspects[planet_name] = []
            planet_aspects[planet_name].append(aspect)
    
    print(f"=== ASPECT PATTERN RECOGNITION ===")
    
    # Identify heavily aspected planets (potential focal points)
    heavily_aspected = []
    for planet, aspects in planet_aspects.items():
        if len(aspects) >= 6:  # Threshold for "heavily aspected"
            heavily_aspected.append((planet, len(aspects)))
    
    if heavily_aspected:
        print(f"\nHeavily Aspected Planets (Focal Points):")
        for planet, count in sorted(heavily_aspected, key=lambda x: x[1], reverse=True):
            print(f"  {planet}: {count} aspects")
    
    # Look for stelliums (multiple planets in tight conjunction)
    conjunctions = [a for a in aspects_result.relevant_aspects if a.aspect == "conjunction"]
    if len(conjunctions) >= 2:
        print(f"\nConjunction Patterns:")
        print(f"  Found {len(conjunctions)} conjunctions")
        for conj in sorted(conjunctions, key=lambda x: abs(x.orbit)):
            print(f"    {conj.p1_name} ☌ {conj.p2_name} (orb: {conj.orbit:+.2f}°)")
    
    # Identify T-squares and Grand Trines (simplified detection)
    squares = [a for a in aspects_result.relevant_aspects if a.aspect == "square"]
    trines = [a for a in aspects_result.relevant_aspects if a.aspect == "trine"]
    oppositions = [a for a in aspects_result.relevant_aspects if a.aspect == "opposition"]
    
    if len(squares) >= 2 and len(oppositions) >= 1:
        print(f"\nPotential T-Square Configuration detected")
        print(f"  Squares: {len(squares)}, Oppositions: {len(oppositions)}")
    
    if len(trines) >= 3:
        print(f"\nPotential Grand Trine Configuration detected")
        print(f"  Trines: {len(trines)}")
    
    return planet_aspects, heavily_aspected

# Example pattern recognition
patterns = identify_aspect_patterns(chart_aspects)
```

## Data Export and Integration

### JSON Export for Analysis

```python
import json
from datetime import datetime

def export_aspects_analysis(aspects_result, filename_prefix="aspects"):
    """Export comprehensive aspects analysis to JSON"""
    
    # Prepare export data
    export_data = {
        "analysis_info": {
            "generated_date": datetime.now().isoformat(),
            "chart_owner": aspects_result.subject.name if hasattr(aspects_result, 'subject') else "Synastry",
            "total_aspects": len(aspects_result.all_aspects),
            "relevant_aspects": len(aspects_result.relevant_aspects),
            "active_points": [str(point) for point in aspects_result.active_points],
            "active_aspects": [aspect.model_dump() for aspect in aspects_result.active_aspects]
        },
        "aspects_data": {
            "all_aspects": [aspect.model_dump() for aspect in aspects_result.all_aspects],
            "relevant_aspects": [aspect.model_dump() for aspect in aspects_result.relevant_aspects]
        }
    }
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    
    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"Aspects analysis exported to: {filename}")
    return filename

# Export examples
natal_export = export_aspects_analysis(chart_aspects, "natal_aspects")
synastry_export = export_aspects_analysis(relationship_analysis, "synastry_aspects")
```

### Statistical Analysis

```python
import statistics

def statistical_aspects_analysis(aspects_list):
    """Perform statistical analysis on aspects data"""
    
    if not aspects_list:
        print("No aspects to analyze")
        return
    
    # Orb statistics
    orbs = [abs(aspect.orbit) for aspect in aspects_list]
    
    print(f"=== STATISTICAL ANALYSIS ===")
    print(f"Sample size: {len(aspects_list)} aspects")
    
    print(f"\nOrb Statistics:")
    print(f"  Mean orb: {statistics.mean(orbs):.2f}°")
    print(f"  Median orb: {statistics.median(orbs):.2f}°")
    print(f"  Standard deviation: {statistics.stdev(orbs):.2f}°")
    print(f"  Min orb: {min(orbs):.2f}°")
    print(f"  Max orb: {max(orbs):.2f}°")
    
    # Aspect type frequency
    aspect_types = {}
    for aspect in aspects_list:
        aspect_type = aspect.aspect
        aspect_types[aspect_type] = aspect_types.get(aspect_type, 0) + 1
    
    print(f"\nAspect Type Frequency:")
    total = len(aspects_list)
    for aspect_type, count in sorted(aspect_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        print(f"  {aspect_type}: {count} ({percentage:.1f}%)")
    
    return {
        "orb_stats": {
            "mean": statistics.mean(orbs),
            "median": statistics.median(orbs),
            "stdev": statistics.stdev(orbs) if len(orbs) > 1 else 0,
            "min": min(orbs),
            "max": max(orbs)
        },
        "type_frequency": aspect_types
    }

# Example statistical analysis
natal_stats = statistical_aspects_analysis(chart_aspects.relevant_aspects)
synastry_stats = statistical_aspects_analysis(relationship_analysis.relevant_aspects)
```

## Practical Applications

### Professional Consultation

```python
def generate_consultation_report(person, report_type="comprehensive"):
    """Generate professional astrological consultation report"""
    
    print(f"=== ASTROLOGICAL CONSULTATION REPORT ===")
    print(f"Client: {person.name}")
    print(f"Birth Data: {person.year}-{person.month:02d}-{person.day:02d} at {person.hour:02d}:{person.minute:02d}")
    print(f"Location: {person.city}, {person.nation}")
    print(f"Report Type: {report_type.title()}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # Single chart analysis
    chart_aspects = AspectsFactory.single_chart_aspects(person)
    
    print(f"\n1. NATAL CHART ASPECTS OVERVIEW")
    print(f"   Total aspects calculated: {len(chart_aspects.all_aspects)}")
    print(f"   Significant aspects: {len(chart_aspects.relevant_aspects)}")
    
    # Quality analysis
    quality_analysis = aspect_quality_analysis(chart_aspects)
    
    # Pattern recognition
    pattern_analysis = identify_aspect_patterns(chart_aspects)
    
    # Key aspects interpretation
    print(f"\n2. KEY ASPECTS FOR INTERPRETATION")
    strongest_aspects = sorted(chart_aspects.relevant_aspects, key=lambda x: abs(x.orbit))[:10]
    
    for i, aspect in enumerate(strongest_aspects, 1):
        print(f"   {i:2d}. {aspect.p1_name} {aspect.aspect} {aspect.p2_name} (orb: {aspect.orbit:+.2f}°)")
    
    if report_type == "comprehensive":
        # Additional detailed analysis for comprehensive reports
        print(f"\n3. DETAILED PLANETARY ANALYSIS")
        
        # Analyze each personal planet's aspects
        personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
        for planet in personal_planets:
            planet_aspects = [a for a in chart_aspects.relevant_aspects 
                            if planet in [a.p1_name, a.p2_name]]
            if planet_aspects:
                print(f"\n   {planet} Aspects ({len(planet_aspects)} total):")
                for aspect in planet_aspects[:3]:  # Show top 3 for each planet
                    other_planet = aspect.p2_name if aspect.p1_name == planet else aspect.p1_name
                    print(f"     • {aspect.aspect} {other_planet} (orb: {aspect.orbit:+.2f}°)")
    
    return chart_aspects

# Example consultation report
consultation = generate_consultation_report(person, "comprehensive")
```

### Research Applications

```python
def comparative_study(subjects_list, study_focus="general"):
    """Conduct comparative astrological research across multiple subjects"""
    
    print(f"=== COMPARATIVE ASTROLOGICAL STUDY ===")
    print(f"Study Focus: {study_focus.title()}")
    print(f"Sample Size: {len(subjects_list)} subjects")
    print("=" * 50)
    
    all_results = []
    
    for i, subject in enumerate(subjects_list, 1):
        print(f"\nProcessing subject {i}/{len(subjects_list)}: {subject.name}")
        
        # Calculate aspects for each subject
        chart_aspects = AspectsFactory.single_chart_aspects(subject)
        stats = statistical_aspects_analysis(chart_aspects.relevant_aspects)
        
        result = {
            "name": subject.name,
            "birth_year": subject.year,
            "sun_sign": subject.sun.sign,
            "total_aspects": len(chart_aspects.all_aspects),
            "relevant_aspects": len(chart_aspects.relevant_aspects),
            "stats": stats
        }
        all_results.append(result)
    
    # Aggregate analysis
    print(f"\n=== AGGREGATE ANALYSIS ===")
    
    total_aspects = [r["relevant_aspects"] for r in all_results]
    avg_aspects = statistics.mean(total_aspects)
    
    print(f"Average aspects per chart: {avg_aspects:.1f}")
    print(f"Range: {min(total_aspects)} - {max(total_aspects)} aspects")
    
    # Analysis by sun sign
    if study_focus == "sun_sign":
        sun_sign_data = {}
        for result in all_results:
            sign = result["sun_sign"]
            if sign not in sun_sign_data:
                sun_sign_data[sign] = []
            sun_sign_data[sign].append(result["relevant_aspects"])
        
        print(f"\nAspects by Sun Sign:")
        for sign, aspects_counts in sun_sign_data.items():
            if len(aspects_counts) > 1:
                avg = statistics.mean(aspects_counts)
                print(f"  {sign}: {len(aspects_counts)} subjects, avg {avg:.1f} aspects")
    
    return all_results

# Example research study
sample_subjects = [person1, person2, person]  # Add more subjects for real research
research_results = comparative_study(sample_subjects, "sun_sign")
```

## Integration with Other Modules

The Aspects module works seamlessly with other Kerykeion components:

### Chart Visualization
```python
from kerykeion.charts import ChartDrawer

# Create chart with aspect lines
chart = ChartDrawer(person)
chart_svg = chart.generate_svg_string()
# Aspects are automatically calculated and displayed as lines
```

### House Comparison
```python
from kerykeion.house_comparison import HouseComparisonFactory

# Combine aspects and house overlays for complete synastry
aspects = AspectsFactory.dual_chart_aspects(person1, person2)
houses = HouseComparisonFactory(person1, person2).get_house_comparison()

print("Complete relationship analysis:")
print(f"  Aspects: {len(aspects.relevant_aspects)}")
print(f"  House overlays: {len(houses.first_points_in_second_houses)}")
```

### Transits and Returns
```python
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

# Analyze return chart aspects
solar_return = PlanetaryReturnFactory.solar_return(person, 2024)
return_aspects = AspectsFactory.single_chart_aspects(solar_return)

print(f"Solar return aspects: {len(return_aspects.relevant_aspects)}")
```

This comprehensive aspects module provides the foundation for all astrological analysis within the Kerykeion framework, offering both simple usage for beginners and advanced features for professional astrologers and researchers.
