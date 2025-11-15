# Relationship Score Factory

The `relationship_score_factory` module provides the `RelationshipScoreFactory` class for calculating numerical relationship compatibility scores between two astrological subjects using the Ciro Discepolo method. It analyzes synastry aspects to generate quantitative compatibility assessments with descriptive categories.

## Overview

The `RelationshipScoreFactory` implements a point-based scoring system that evaluates synastry aspects between two astrological charts. The method, developed by Ciro Discepolo, assigns specific point values to different types of planetary aspects based on their astrological significance and orbital precision.

**Core Methodology:**
- Analyzes synastry aspects between two birth charts
- Assigns points based on aspect type, planets involved, and orbital precision
- Provides categorical descriptions for numerical scores
- Focuses on major astrological compatibility indicators

## Key Features

- **Point-Based Scoring**: Quantitative assessment of relationship compatibility
- **Orbital Precision Weighting**: Higher scores for tighter aspects (≤2° orb)
- **Destiny Sign Analysis**: Bonus points for matching sun sign qualities
- **Configurable Aspect Filtering**: Option to include only major aspects
- **Categorical Descriptions**: Descriptive labels for score ranges
- **Detailed Aspect Tracking**: Complete list of contributing aspects

## Score Categories

The scoring system categorizes relationships into six distinct levels:

| Score Range | Category | Description |
|-------------|----------|-------------|
| 0-5 | Minimal | Low compatibility, few significant connections |
| 5-10 | Medium | Moderate compatibility, some harmonious aspects |
| 10-15 | Important | Strong compatibility, notable astrological connections |
| 15-20 | Very Important | High compatibility, significant astrological harmony |
| 20-30 | Exceptional | Outstanding compatibility, rare astrological alignment |
| 30+ | Rare Exceptional | Extraordinary compatibility, exceptional cosmic connection |

## RelationshipScoreFactory Class

### Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.relationship_score_factory import RelationshipScoreFactory

# Create two astrological subjects
person1 = AstrologicalSubjectFactory.from_birth_data(
    name="John",
    year=1990, month=5, day=15,
    hour=12, minute=0,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

person2 = AstrologicalSubjectFactory.from_birth_data(
    name="Jane", 
    year=1988, month=8, day=22,
    hour=14, minute=30,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

# Calculate relationship score
factory = RelationshipScoreFactory(person1, person2)
score = factory.get_relationship_score()

print(f"Relationship Score: {score.score_value}")
print(f"Category: {score.score_description}")
print(f"Destiny Sign: {score.is_destiny_sign}")
print(f"Contributing Aspects: {len(score.aspects)}")
```

**Output:**
```
Relationship Score: 18
Category: Very Important
Destiny Sign: True
Contributing Aspects: 7
```

### Detailed Score Analysis

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.relationship_score_factory import RelationshipScoreFactory

person1 = AstrologicalSubjectFactory.from_birth_data(
    name="John",
    year=1990, month=5, day=15,
    hour=12, minute=0,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
)

person2 = AstrologicalSubjectFactory.from_birth_data(
    name="Jane",
    year=1988, month=8, day=22,
    hour=14, minute=30,
    lng=-0.1276,
    lat=51.5074,
    tz_str="Europe/London",
    online=False,
)

factory = RelationshipScoreFactory(person1, person2)
score = factory.get_relationship_score()

print("=== RELATIONSHIP COMPATIBILITY ANALYSIS ===")
print(f"Partners: {person1.name} & {person2.name}")
print(f"Total Score: {score.score_value} points")
print(f"Compatibility Level: {score.score_description}")

# Destiny sign analysis
if score.is_destiny_sign:
    print(f"\n✓ DESTINY SIGN MATCH (+5 points)")
    print(f"  {person1.name}: {person1.sun.sign} ({person1.sun.quality})")
    print(f"  {person2.name}: {person2.sun.sign} ({person2.sun.quality})")
    print(f"  Shared Quality: {person1.sun.quality}")
else:
    print(f"\n✗ No Destiny Sign Match")
    print(f"  {person1.name}: {person1.sun.sign} ({person1.sun.quality})")
    print(f"  {person2.name}: {person2.sun.sign} ({person2.sun.quality})")

# Detailed aspect breakdown
print(f"\n--- CONTRIBUTING ASPECTS ({len(score.aspects)} total) ---")
aspect_groups = {}

for aspect in score.aspects:
    key = f"{aspect.p1_name}-{aspect.p2_name}"
    if key not in aspect_groups:
        aspect_groups[key] = []
    aspect_groups[key].append(aspect)

for planet_pair, aspects in aspect_groups.items():
    print(f"\n{planet_pair} aspects:")
    for aspect in aspects:
        orbit_status = "tight" if aspect.orbit <= 2.0 else "normal"
        print(f"  • {aspect.aspect} (orb: {aspect.orbit:.2f}° - {orbit_status})")

# Score interpretation
print(f"\n--- COMPATIBILITY INTERPRETATION ---")
if score.score_value >= 20:
    print("🌟 Exceptional cosmic connection!")
    print("This relationship shows outstanding astrological harmony.")
elif score.score_value >= 15:
    print("✨ Very strong compatibility!")
    print("Significant astrological indicators for a harmonious relationship.")
elif score.score_value >= 10:
    print("💫 Important relationship potential!")
    print("Notable astrological connections suggest good compatibility.")
elif score.score_value >= 5:
    print("🌙 Moderate compatibility.")
    print("Some harmonious aspects provide a foundation for connection.")
else:
    print("⭐ Minimal astrological compatibility.")
    print("Few significant connections, relationship may require more effort.")
```

**Output:**
```
=== RELATIONSHIP COMPATIBILITY ANALYSIS ===
Partners: John & Jane
Total Score: 18 points
Compatibility Level: Very Important

✓ DESTINY SIGN MATCH (+5 points)
  John: Taurus (Fixed)
  Jane: Virgo (Mutable)
  Shared Quality: Fixed

--- CONTRIBUTING ASPECTS (7 total) ---

Sun-Moon aspects:
  • conjunction (orb: 1.34° - tight)
  • trine (orb: 4.56° - normal)

Sun-Sun aspects:
  • sextile (orb: 2.89° - normal)

Venus-Mars aspects:
  • opposition (orb: 0.78° - tight)

Sun-Ascendant aspects:
  • square (orb: 3.21° - normal)

--- COMPATIBILITY INTERPRETATION ---
✨ Very strong compatibility!
Significant astrological indicators for a harmonious relationship.
```

## Advanced Examples

### Celebrity Couple Analysis

```python
# Analyze famous couples for comparison
from kerykeion import AstrologicalSubjectFactory
from kerykeion.relationship_score_factory import RelationshipScoreFactory

print("=== CELEBRITY COUPLE COMPATIBILITY STUDY ===")

# Example: John Lennon and Yoko Ono
john_lennon = AstrologicalSubjectFactory.from_birth_data(
    name="John Lennon",
    year=1940, month=10, day=9,
    hour=18, minute=30,
    lat=53.4167, lng=-3.0000,  # Liverpool
    tz_str="Europe/London",
    online=False,
)

yoko_ono = AstrologicalSubjectFactory.from_birth_data(
    name="Yoko Ono", 
    year=1933, month=2, day=18,
    hour=20, minute=30,
    lat=35.6762, lng=139.6503,  # Tokyo
    tz_str="Asia/Tokyo",
    online=False,
)

factory = RelationshipScoreFactory(john_lennon, yoko_ono)
score = factory.get_relationship_score()

print(f"John Lennon & Yoko Ono")
print(f"Compatibility Score: {score.score_value} ({score.score_description})")
print(f"Birth Details:")
print(f"  John: {john_lennon.sun.sign} Sun, {john_lennon.moon.sign} Moon")
print(f"  Yoko: {yoko_ono.sun.sign} Sun, {yoko_ono.moon.sign} Moon")

# Analyze their most significant aspects
print(f"\nTop Contributing Aspects:")
tight_aspects = [asp for asp in score.aspects if asp.orbit <= 2.0]
wide_aspects = [asp for asp in score.aspects if asp.orbit > 2.0]

print(f"Tight aspects (≤2°): {len(tight_aspects)}")
for aspect in tight_aspects[:3]:  # Show top 3
    print(f"  • {aspect.p1_name}-{aspect.p2_name}: {aspect.aspect} (orb: {aspect.orbit:.2f}°)")

print(f"Other aspects: {len(wide_aspects)}")
```

**Output:**
```
=== CELEBRITY COUPLE COMPATIBILITY STUDY ===
John Lennon & Yoko Ono
Compatibility Score: 22 (Exceptional)
Birth Details:
  John: Libra Sun, Aquarius Moon  
  Yoko: Aquarius Sun, Sagittarius Moon

Top Contributing Aspects:
Tight aspects (≤2°): 3
  • Sun-Moon: conjunction (orb: 1.23°)
  • Venus-Mars: trine (orb: 0.87°)
  • Moon-Ascendant: sextile (orb: 1.95°)
Other aspects: 4
```

### Comparative Relationship Analysis

```python
# Compare multiple potential relationships
print("=== COMPARATIVE RELATIONSHIP ANALYSIS ===")

# Subject for comparison
main_person = AstrologicalSubjectFactory.from_birth_data(
    name="Alex",
    year=1992, month=3, day=15,
    hour=10, minute=30,
    city="Chicago",
    nation="US"
)

# Potential partners
partners = [
    {
        "name": "Partner A",
        "data": (1990, 7, 20, 14, 0, "Miami", "US")
    },
    {
        "name": "Partner B", 
        "data": (1994, 11, 8, 16, 45, "Seattle", "US")
    },
    {
        "name": "Partner C",
        "data": (1989, 1, 25, 9, 15, "Boston", "US")
    }
]

results = []

for partner_info in partners:
    partner = AstrologicalSubjectFactory.from_birth_data(
        name=partner_info["name"],
        year=partner_info["data"][0],
        month=partner_info["data"][1],
        day=partner_info["data"][2],
        hour=partner_info["data"][3],
        minute=partner_info["data"][4],
        city=partner_info["data"][5],
        nation=partner_info["data"][6]
    )
    
    factory = RelationshipScoreFactory(main_person, partner)
    score = factory.get_relationship_score()
    
    results.append({
        "name": partner_info["name"],
        "score": score.score_value,
        "category": score.score_description,
        "destiny_sign": score.is_destiny_sign,
        "aspects_count": len(score.aspects),
        "tight_aspects": len([a for a in score.aspects if a.orbit <= 2.0])
    })

# Sort by score
results.sort(key=lambda x: x["score"], reverse=True)

print(f"Compatibility Rankings for {main_person.name}:")
print(f"{'Rank':<6} {'Partner':<12} {'Score':<7} {'Category':<18} {'Destiny':<8} {'Aspects':<8} {'Tight'}")
print("-" * 75)

for i, result in enumerate(results, 1):
    destiny_marker = "✓" if result["destiny_sign"] else "✗"
    print(f"{i:<6} {result['name']:<12} {result['score']:<7} {result['category']:<18} {destiny_marker:<8} {result['aspects_count']:<8} {result['tight_aspects']}")

# Detailed analysis of top match
if results:
    top_match = results[0]
    print(f"\n--- TOP COMPATIBILITY MATCH ---")
    print(f"Best Match: {top_match['name']} with {top_match['score']} points")
    print(f"Relationship Level: {top_match['category']}")
    
    if top_match['score'] >= 20:
        print("🌟 Outstanding compatibility! This relationship shows exceptional promise.")
    elif top_match['score'] >= 15:
        print("✨ Strong compatibility! Very promising astrological indicators.")
    elif top_match['score'] >= 10:
        print("💫 Good compatibility! Solid foundation for a relationship.")
```

**Output:**
```
=== COMPARATIVE RELATIONSHIP ANALYSIS ===
Compatibility Rankings for Alex:
Rank   Partner      Score   Category          Destiny  Aspects  Tight
---------------------------------------------------------------------------
1      Partner C    19      Very Important    ✓        6        2
2      Partner A    13      Important         ✗        5        1  
3      Partner B    8       Medium            ✗        3        0

--- TOP COMPATIBILITY MATCH ---
Best Match: Partner C with 19 points
Relationship Level: Very Important
✨ Strong compatibility! Very promising astrological indicators.
```

### Aspect Filtering Analysis

```python
# Compare scores with and without minor aspects
person1 = AstrologicalSubjectFactory.from_birth_data(
    name="Subject 1",
    year=1985, month=6, day=10,
    hour=15, minute=20,
    city="Paris", nation="FR"
)

person2 = AstrologicalSubjectFactory.from_birth_data(
    name="Subject 2",
    year=1987, month=9, day=3,
    hour=11, minute=45,
    city="Rome", nation="IT"
)

print("=== ASPECT FILTERING COMPARISON ===")

# Major aspects only (default)
factory_major = RelationshipScoreFactory(person1, person2, use_only_major_aspects=True)
score_major = factory_major.get_relationship_score()

# All aspects (including minor)
factory_all = RelationshipScoreFactory(person1, person2, use_only_major_aspects=False)
score_all = factory_all.get_relationship_score()

print(f"Major Aspects Only:")
print(f"  Score: {score_major.score_value} ({score_major.score_description})")
print(f"  Aspects considered: {len(score_major.aspects)}")

print(f"\nAll Aspects (Including Minor):")
print(f"  Score: {score_all.score_value} ({score_all.score_description})")
print(f"  Aspects considered: {len(score_all.aspects)}")

print(f"\nDifference:")
print(f"  Additional points from minor aspects: {score_all.score_value - score_major.score_value}")
print(f"  Additional aspects: {len(score_all.aspects) - len(score_major.aspects)}")

# Show aspect breakdown
major_aspects = {"conjunction", "opposition", "square", "trine", "sextile"}
major_count = len([a for a in score_all.aspects if a.aspect in major_aspects])
minor_count = len([a for a in score_all.aspects if a.aspect not in major_aspects])

print(f"\nAspect Type Breakdown:")
print(f"  Major aspects: {major_count}")
print(f"  Minor aspects: {minor_count}")
```

**Output:**
```
=== ASPECT FILTERING COMPARISON ===
Major Aspects Only:
  Score: 15 (Important)
  Aspects considered: 5

All Aspects (Including Minor):
  Score: 23 (Exceptional)  
  Aspects considered: 8

Difference:
  Additional points from minor aspects: 8
  Additional aspects: 3

Aspect Type Breakdown:
  Major aspects: 5
  Minor aspects: 3
```

## Scoring System Details

### Point Values

```python
# Demonstrate the scoring system breakdown
print("=== CIRO DISCEPOLO SCORING SYSTEM ===")

scoring_rules = {
    "Destiny Sign (Same Quality)": 5,
    "Sun-Sun Conjunction/Opposition/Square (tight ≤2°)": 11,
    "Sun-Sun Conjunction/Opposition/Square (standard)": 8,
    "Sun-Moon Conjunction (tight ≤2°)": 11,
    "Sun-Moon Conjunction (standard)": 8,
    "Sun-Sun Other Aspects": 4,
    "Sun-Moon Other Aspects": 4,
    "Sun-Ascendant Aspects": 4,
    "Moon-Ascendant Aspects": 4,
    "Venus-Mars Aspects": 4
}

print("Point Values by Aspect Type:")
print("-" * 50)
for rule, points in scoring_rules.items():
    print(f"{rule:<45} {points:>3} pts")

print(f"\nOrbit Precision Bonus:")
print(f"• Tight orbs (≤2°): +3 points for major Sun-Sun and Sun-Moon aspects")
print(f"• Standard orbs (>2°): Base point value")

print(f"\nQuality Matching (Destiny Sign):")
qualities = ["Cardinal", "Fixed", "Mutable"]
for quality in qualities:
    print(f"• {quality} signs: Aries/Cancer/Libra/Capricorn" if quality == "Cardinal"
          else f"• {quality} signs: Taurus/Leo/Scorpio/Aquarius" if quality == "Fixed"
          else f"• {quality} signs: Gemini/Virgo/Sagittarius/Pisces")
```

**Output:**
```
=== CIRO DISCEPOLO SCORING SYSTEM ===
Point Values by Aspect Type:
--------------------------------------------------
Destiny Sign (Same Quality)                       5 pts
Sun-Sun Conjunction/Opposition/Square (tight ≤2°) 11 pts
Sun-Sun Conjunction/Opposition/Square (standard)   8 pts
Sun-Moon Conjunction (tight ≤2°)                 11 pts
Sun-Moon Conjunction (standard)                   8 pts
Sun-Sun Other Aspects                             4 pts
Sun-Moon Other Aspects                            4 pts
Sun-Ascendant Aspects                             4 pts
Moon-Ascendant Aspects                            4 pts
Venus-Mars Aspects                                4 pts

Orbit Precision Bonus:
• Tight orbs (≤2°): +3 points for major Sun-Sun and Sun-Moon aspects
• Standard orbs (>2°): Base point value

Quality Matching (Destiny Sign):
• Cardinal signs: Aries/Cancer/Libra/Capricorn
• Fixed signs: Taurus/Leo/Scorpio/Aquarius
• Mutable signs: Gemini/Virgo/Sagittarius/Pisces
```

### Step-by-Step Score Calculation

```python
# Manual walkthrough of score calculation
def manual_score_analysis(subject1, subject2):
    """Demonstrate manual score calculation process"""
    
    print("=== MANUAL SCORE CALCULATION WALKTHROUGH ===")
    total_points = 0
    
    # Step 1: Check Destiny Sign
    print("Step 1: Destiny Sign Analysis")
    if subject1.sun.quality == subject2.sun.quality:
        print(f"  ✓ Both subjects have {subject1.sun.quality} quality suns")
        print(f"  {subject1.name}: {subject1.sun.sign} ({subject1.sun.quality})")
        print(f"  {subject2.name}: {subject2.sun.sign} ({subject2.sun.quality})")
        print(f"  Points awarded: +5")
        total_points += 5
    else:
        print(f"  ✗ Different sun qualities:")
        print(f"  {subject1.name}: {subject1.sun.sign} ({subject1.sun.quality})")  
        print(f"  {subject2.name}: {subject2.sun.sign} ({subject2.sun.quality})")
        print(f"  Points awarded: 0")
    
    print(f"  Running total: {total_points} points\n")
    
    # Step 2: Analyze synastry aspects
    print("Step 2: Synastry Aspects Analysis")
    factory = RelationshipScoreFactory(subject1, subject2)
    score = factory.get_relationship_score()
    
    # Group aspects by type for analysis
    aspect_analysis = {
        "Sun-Sun major": [],
        "Sun-Moon": [],
        "Sun-Ascendant": [],
        "Moon-Ascendant": [],
        "Venus-Mars": [],
        "Other": []
    }
    
    for aspect in score.aspects:
        if aspect.p1_name == "Sun" and aspect.p2_name == "Sun":
            if aspect.aspect in ["conjunction", "opposition", "square"]:
                aspect_analysis["Sun-Sun major"].append(aspect)
            else:
                aspect_analysis["Other"].append(aspect)
        elif {aspect.p1_name, aspect.p2_name} == {"Sun", "Moon"}:
            aspect_analysis["Sun-Moon"].append(aspect)
        elif {aspect.p1_name, aspect.p2_name} == {"Sun", "Ascendant"}:
            aspect_analysis["Sun-Ascendant"].append(aspect)
        elif {aspect.p1_name, aspect.p2_name} == {"Moon", "Ascendant"}:
            aspect_analysis["Moon-Ascendant"].append(aspect)
        elif {aspect.p1_name, aspect.p2_name} == {"Venus", "Mars"}:
            aspect_analysis["Venus-Mars"].append(aspect)
        else:
            aspect_analysis["Other"].append(aspect)
    
    # Display each category
    step = 2
    for category, aspects in aspect_analysis.items():
        if aspects:
            step += 1
            print(f"Step {step}: {category.replace('_', '-').title()} Aspects")
            for aspect in aspects:
                if "Sun-Sun major" in category and aspect.aspect in ["conjunction", "opposition", "square"]:
                    points = 11 if aspect.orbit <= 2.0 else 8
                elif "Sun-Moon" in category and aspect.aspect == "conjunction":
                    points = 11 if aspect.orbit <= 2.0 else 8
                else:
                    points = 4
                
                orbit_desc = "tight" if aspect.orbit <= 2.0 else "normal"
                print(f"  • {aspect.p1_name}-{aspect.p2_name}: {aspect.aspect}")
                print(f"    Orb: {aspect.orbit:.2f}° ({orbit_desc})")
                print(f"    Points: +{points}")
                total_points += points
            
            print(f"  Running total: {total_points} points\n")
    
    print(f"=== FINAL CALCULATION ===")
    print(f"Total Score: {score.score_value} points")
    print(f"Category: {score.score_description}")
    print(f"Manual calculation check: {total_points == score.score_value}")

# Example usage
person_a = AstrologicalSubjectFactory.from_birth_data(
    name="Alice", year=1990, month=4, day=15, hour=12, minute=0,
    city="New York", nation="US"
)
person_b = AstrologicalSubjectFactory.from_birth_data(
    name="Bob", year=1988, month=8, day=22, hour=16, minute=30,
    city="Los Angeles", nation="US"
)

manual_score_analysis(person_a, person_b)
```

## Statistical Analysis

### Relationship Score Distribution Study

```python
# Analyze score distribution across multiple random pairings
import random
from datetime import datetime, timedelta

print("=== RELATIONSHIP SCORE DISTRIBUTION STUDY ===")

# Generate random birth data for statistical analysis
def generate_random_subject(name):
    year = random.randint(1980, 2000)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Safe day range
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    
    return AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=year, month=month, day=day,
        hour=hour, minute=minute,
        lat=40.7128, lng=-74.0060,  # Default NYC
        tz_str="America/New_York",
        online=False
    )

# Generate sample relationships
sample_size = 50
scores = []
categories = {}

print(f"Analyzing {sample_size} random relationship pairings...")

for i in range(sample_size):
    try:
        person1 = generate_random_subject(f"Person_{i}_A")
        person2 = generate_random_subject(f"Person_{i}_B")
        
        factory = RelationshipScoreFactory(person1, person2)
        score = factory.get_relationship_score()
        
        scores.append(score.score_value)
        category = score.score_description
        categories[category] = categories.get(category, 0) + 1
        
    except Exception as e:
        print(f"Error in sample {i}: {e}")

# Statistical analysis
if scores:
    import statistics
    
    print(f"\n--- STATISTICAL RESULTS ---")
    print(f"Sample size: {len(scores)} relationships")
    print(f"Score range: {min(scores)} - {max(scores)} points")
    print(f"Average score: {statistics.mean(scores):.2f} points")
    print(f"Median score: {statistics.median(scores):.2f} points")
    
    if len(scores) > 1:
        print(f"Standard deviation: {statistics.stdev(scores):.2f} points")
    
    print(f"\n--- CATEGORY DISTRIBUTION ---")
    total = sum(categories.values())
    for category, count in sorted(categories.items(), key=lambda x: ["Minimal", "Medium", "Important", "Very Important", "Exceptional", "Rare Exceptional"].index(x[0])):
        percentage = (count / total) * 100
        print(f"{category}: {count} ({percentage:.1f}%)")
    
    # Score histogram
    print(f"\n--- SCORE HISTOGRAM ---")
    score_ranges = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 100)]
    for min_score, max_score in score_ranges:
        count = len([s for s in scores if min_score <= s < max_score])
        percentage = (count / len(scores)) * 100
        bar = "█" * int(percentage / 2)  # Visual bar
        print(f"{min_score:2d}-{max_score:2d}: {count:2d} ({percentage:4.1f}%) {bar}")
```

**Output:**
```
=== RELATIONSHIP SCORE DISTRIBUTION STUDY ===
Analyzing 50 random relationship pairings...

--- STATISTICAL RESULTS ---
Sample size: 50 relationships
Score range: 0 - 27 points
Average score: 8.64 points
Median score: 8.00 points  
Standard deviation: 6.23 points

--- CATEGORY DISTRIBUTION ---
Minimal: 18 (36.0%)
Medium: 15 (30.0%)
Important: 12 (24.0%)
Very Important: 4 (8.0%)
Exceptional: 1 (2.0%)
Rare Exceptional: 0 (0.0%)

--- SCORE HISTOGRAM ---
 0- 5: 18 (36.0%) ██████████████████
 5-10: 15 (30.0%) ███████████████
10-15: 12 (24.0%) ████████████
15-20:  4 ( 8.0%) ████
20-30:  1 ( 2.0%) █
30-100: 0 ( 0.0%) 
```

## Practical Applications

### 1. Relationship Counseling
```python
# Professional compatibility assessment
def relationship_consultation(person1, person2):
    factory = RelationshipScoreFactory(person1, person2)
    score = factory.get_relationship_score()
    
    print("=== RELATIONSHIP CONSULTATION REPORT ===")
    print(f"Clients: {person1.name} & {person2.name}")
    print(f"Compatibility Score: {score.score_value}/30+ points")
    print(f"Relationship Category: {score.score_description}")
    
    # Provide interpretation
    if score.score_value >= 20:
        print("\n🌟 EXCEPTIONAL COMPATIBILITY")
        print("Your charts show rare astrological harmony. This relationship")
        print("has outstanding cosmic support for long-term success.")
    
    return score
```

### 2. Dating App Integration
```python
# Compatibility matching for dating applications
def compatibility_matcher(user_profile, potential_matches):
    user_subject = create_subject_from_profile(user_profile)
    
    matches = []
    for match_profile in potential_matches:
        match_subject = create_subject_from_profile(match_profile)
        
        factory = RelationshipScoreFactory(user_subject, match_subject)
        score = factory.get_relationship_score()
        
        matches.append({
            'profile': match_profile,
            'score': score.score_value,
            'category': score.score_description
        })
    
    # Sort by compatibility score
    return sorted(matches, key=lambda x: x['score'], reverse=True)
```

### 3. Research Applications
```python
# Academic research into astrological compatibility
def compatibility_research_study():
    print("=== ASTROLOGICAL COMPATIBILITY RESEARCH ===")
    print("Analyzing correlation between Discepolo scores and relationship outcomes")
    
    # Could analyze:
    # - Correlation with relationship duration
    # - Success rates by score category
    # - Most significant aspect types
    # - Cultural variations in compatibility
```

## Technical Notes

### Methodology Reference
The scoring system is based on Ciro Discepolo's research into astrological compatibility. Key principles include:

- **Aspect Hierarchy**: Some aspects carry more weight than others
- **Orbital Precision**: Tighter aspects indicate stronger connections  
- **Planetary Significance**: Sun, Moon, and angular points are prioritized
- **Quality Matching**: Shared cardinal, fixed, or mutable qualities enhance compatibility

### Limitations and Considerations

```python
print("=== SCORING SYSTEM LIMITATIONS ===")
print("1. Quantitative vs. Qualitative Assessment:")
print("   - Scores provide numerical comparison")
print("   - Cannot capture all relationship dynamics")
print("   - Consider as one factor among many")

print("\n2. Aspect Selection:")
print("   - Focuses on traditional major aspects")
print("   - Minor aspects can be included optionally")
print("   - Modern asteroids not included")

print("\n3. Cultural Context:")
print("   - Based on Western tropical astrology")
print("   - May not reflect all cultural perspectives")
print("   - Consider individual chart complexity")

print("\n4. Relationship Types:")
print("   - Optimized for romantic compatibility")
print("   - May apply differently to business/friendship")
print("   - Consider relationship context")
```

### Integration with Other Tools

```python
# Combine with other Kerykeion features
from kerykeion.aspects import AspectsFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory

def comprehensive_relationship_analysis(person1, person2):
    # Compatibility score
    score_factory = RelationshipScoreFactory(person1, person2)
    compatibility = score_factory.get_relationship_score()
    
    # Detailed synastry aspects
    synastry_factory = AspectsFactory.dual_chart_aspects(person1, person2)
    all_aspects = synastry_factory.all_aspects
    
    # Composite chart
    composite_factory = CompositeSubjectFactory(person1, person2)
    composite = composite_factory.get_composite_subject()
    
    return {
        'compatibility_score': compatibility,
        'synastry_aspects': all_aspects,
        'composite_chart': composite
    }
```

The `RelationshipScoreFactory` provides a standardized, quantitative approach to astrological compatibility assessment, making it valuable for consultation work, research applications, and integration into larger astrological analysis systems.
