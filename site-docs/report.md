# Report Module

## Overview

The `Report` class provides comprehensive, human-readable text reports for astrological charts. It generates well-formatted ASCII tables containing all essential astrological data including planetary positions, **speed (daily motion)**, **declination**, houses, lunar phases, element/quality distributions, and aspects.

This module is ideal for:
- Quick data inspection and debugging
- Console-based astrological analysis
- Text-based reports for applications
- Data export in human-readable format
- Integration with command-line tools
- Educational purposes and learning astrology

## Key Features

- **Comprehensive Data Coverage**: All astrological data in organized sections
- **Speed & Declination**: Shows daily motion and celestial declination for all points
- **Element & Quality Distributions**: Visual representation with percentages (when available)
- **Aspect Analysis**: Complete aspect listings with orbs and applying/separating information
- **Flexible Input**: Works with both subject models and chart data models
- **Modular Reports**: Generate individual sections or complete reports
- **Professional Formatting**: Clean ASCII tables with proper alignment and emoji support
- **Type-Safe**: Full type hints and Pydantic model integration

## Installation & Import

```python
from kerykeion import Report, AstrologicalSubjectFactory, ChartDataFactory
```

## Basic Usage

### Simple Subject Report

For basic astrological subject data without elements/qualities:

```python
from kerykeion import AstrologicalSubjectFactory, Report

# Create subject
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
)

# Create report
report = Report(john)

# Print complete report
report.print_report()
```

### Complete Chart Report with Elements & Qualities

For full chart data including elements, qualities, and aspects:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, Report

# Create subject
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
)

# Create chart data (calculates elements, qualities, aspects)
chart = ChartDataFactory.create_chart_data("Natal", first_subject=john)

# Create report with chart data
report = Report(chart)

# Print complete report with all features
report.print_report()
```

## Report Sections

The `Report` class provides multiple methods to generate different sections independently:

### 1. Report Title

```python
title = report.get_report_title()
print(title)
```

Output:
```
=============================================
Kerykeion Astrological Report for John Lennon
=============================================
```

### 2. Subject Data Report

Birth information and astrological settings:

```python
subject_data = report.get_subject_data_report()
print(subject_data)
```

Output:
```
+Birth Data---------+---------------+
| Birth Information | Value         |
+-------------------+---------------+
| Name              | John Lennon   |
| Date              | 09/10/1940    |
| Time              | 18:30         |
| City              | Liverpool     |
| Nation            | GB            |
| Latitude          | 53.4106°      |
| Longitude         | -2.9779°      |
| Timezone          | Europe/London |
| Day of Week       | Wednesday     |
+-------------------+---------------+

+Settings---------------+---------------------+
| Astrological Settings | Value               |
+-----------------------+---------------------+
| Zodiac Type           | Tropic              |
| Houses System         | Placidus            |
| Perspective Type      | Apparent Geocentric |
| Julian Day            | 2429912.229167      |
+-----------------------+---------------------+
```

### 3. Celestial Points Report

Complete planetary data including **speed** and **declination**:

```python
celestial = report.get_celestial_points_report()
print(celestial)
```

Output:
```
+Celestial Points-+---------+----------+-------------+---------+------+----------------+
| Point           | Sign    | Position | Speed       | Decl.   | Ret. | House          |
+-----------------+---------+----------+-------------+---------+------+----------------+
| Ascendant       | Ari ♈️ | 19.75°   | N/A         | N/A     | -    | First House    |
| Medium Coeli    | Cap ♑️ | 7.07°    | N/A         | N/A     | -    | Tenth House    |
| Sun             | Lib ♎️ | 16.27°   | +0.9885°/d  | -6.40°  | -    | Sixth House    |
| Moon            | Aqu ♒️ | 3.55°    | +12.5292°/d | -14.60° | -    | Eleventh House |
| Mercury         | Sco ♏️ | 8.56°    | +1.3195°/d  | -16.23° | -    | Seventh House  |
| Venus           | Vir ♍️ | 3.22°    | +1.1337°/d  | +10.57° | -    | Sixth House    |
| Mars            | Lib ♎️ | 2.66°    | +0.6449°/d  | -0.18°  | -    | Sixth House    |
| Jupiter         | Tau ♉️ | 13.69°   | -0.1069°/d  | +14.61° | R    | First House    |
| Saturn          | Tau ♉️ | 13.22°   | -0.0669°/d  | +13.30° | R    | First House    |
| Uranus          | Tau ♉️ | 25.55°   | -0.0294°/d  | +18.88° | R    | First House    |
| Neptune         | Vir ♍️ | 26.03°   | +0.0353°/d  | +2.68°  | -    | Sixth House    |
| Pluto           | Leo ♌️ | 4.19°    | +0.0114°/d  | +23.12° | -    | Fifth House    |
| True Node       | Lib ♎️ | 11.03°   | +0.0001°/d  | -4.36°  | -    | Sixth House    |
| Mean Lilith     | Ari ♈️ | 13.37°   | +0.1107°/d  | +5.05°  | -    | Twelfth House  |
| Chiron          | Leo ♌️ | 0.57°    | +0.0529°/d  | +13.41° | -    | Fifth House    |
+-----------------+---------+----------+-------------+---------+------+----------------+
```

**Understanding the Columns:**
- **Point**: Name of the celestial body or point
- **Sign**: Zodiac sign with emoji
- **Position**: Degrees within the sign (0-30°)
- **Speed**: Daily motion in degrees per day (°/d)
  - Positive values: Direct motion
  - Negative values: Retrograde motion
  - Higher absolute values indicate faster movement
- **Decl.**: Declination (celestial latitude, -90° to +90°)
- **Ret.**: Retrograde status (R = retrograde, - = direct)
- **House**: House placement

### 4. Houses Report

Complete house system information:

```python
houses = report.get_houses_report()
print(houses)
```

Output:
```
+Houses (Placidus)---------+----------+-------------------+
| House          | Sign    | Position | Absolute Position |
+----------------+---------+----------+-------------------+
| First House    | Ari ♈️ | 19.75°   | 19.75°            |
| Second House   | Tau ♉️ | 29.54°   | 59.54°            |
| Third House    | Gem ♊️ | 20.24°   | 80.24°            |
| Fourth House   | Can ♋️ | 7.07°    | 97.07°            |
| Fifth House    | Can ♋️ | 25.31°   | 115.31°           |
| Sixth House    | Leo ♌️ | 22.11°   | 142.11°           |
| Seventh House  | Lib ♎️ | 19.75°   | 199.75°           |
| Eighth House   | Sco ♏️ | 29.54°   | 239.54°           |
| Ninth House    | Sag ♐️ | 20.24°   | 260.24°           |
| Tenth House    | Cap ♑️ | 7.07°    | 277.07°           |
| Eleventh House | Cap ♑️ | 25.31°   | 295.31°           |
| Twelfth House  | Aqu ♒️ | 22.11°   | 322.11°           |
+----------------+---------+----------+-------------------+
```

### 5. Lunar Phase Report

Current moon phase information:

```python
lunar = report.get_lunar_phase_report()
print(lunar)
```

Output:
```
+Lunar Phase--------------+------------------+
| Lunar Phase Information | Value            |
+-------------------------+------------------+
| Phase Name              | First Quarter 🌓 |
| Sun-Moon Angle          | 107.28°          |
| Moon Phase              | 9                |
| Sun Phase               | 8                |
+-------------------------+------------------+
```

### 6. Elements Distribution Report

**Note**: Only available with `ChartDataFactory` chart data models.

```python
elements = report.get_elements_report()
print(elements)
```

Output:
```
+Element Distribution-----------+
| Element  | Count | Percentage |
+----------+-------+------------+
| Fire 🔥  | 50.0  | 21.3%      |
| Earth 🌍 | 75.0  | 31.9%      |
| Air 💨   | 95.0  | 40.4%      |
| Water 💧 | 15.0  | 6.4%       |
| Total    | 235.0 | 100%       |
+----------+-------+------------+
```

**Understanding Element Distribution:**
- Shows the distribution of planetary energies across the four elements
- Count represents the weighted strength of planets in each element
- Percentages provide proportional representation
- Useful for understanding temperament and energy balance

### 7. Qualities Distribution Report

**Note**: Only available with `ChartDataFactory` chart data models.

```python
qualities = report.get_qualities_report()
print(qualities)
```

Output:
```
+Quality Distribution-----------+
| Quality  | Count | Percentage |
+----------+-------+------------+
| Cardinal | 115.0 | 48.9%      |
| Fixed    | 95.0  | 40.4%      |
| Mutable  | 25.0  | 10.6%      |
| Total    | 235.0 | 100%       |
+----------+-------+------------+
```

**Understanding Quality Distribution:**
- **Cardinal**: Initiative, action, leadership
- **Fixed**: Stability, determination, persistence  
- **Mutable**: Adaptability, flexibility, communication
- Shows the distribution of planetary energies across the three modalities

### 8. Aspects Report

**Note**: Only available with `ChartDataFactory` chart data models.

```python
aspects = report.get_aspects_report(max_aspects=10)
print(aspects)
```

Output:
```
+Aspects (showing 10 of 29)-----------------+--------+------------+
| Point 1 | Aspect        | Point 2         | Orb    | Type       |
+---------+---------------+-----------------+--------+------------+
| Sun     | quintile Q    | Pluto           | 0.08°  | Separating |
| Sun     | conjunction ☌ | True Node       | 5.24°  | Separating |
| Sun     | opposition ☍  | Mean Lilith     | -2.90° | Applying   |
| Moon    | trine △       | Mars            | 0.88°  | Separating |
| Moon    | trine △       | Uranus          | -7.99° | Applying   |
| Moon    | opposition ☍  | Pluto           | -0.64° | Applying   |
| Mercury | sextile ⚹     | Venus           | 5.34°  | Separating |
| Mercury | opposition ☍  | Jupiter         | -5.13° | Applying   |
| Mercury | square □      | Pluto           | 4.37°  | Separating |
| Mars    | trine △       | Uranus          | 7.11°  | Separating |
+---------+---------------+-----------------+--------+------------+
```

**Understanding Aspects:**
- **Orb**: Exact difference from perfect aspect (smaller = stronger)
- **Type**:
  - **Applying**: Aspect is becoming more exact (negative orb)
  - **Separating**: Aspect is becoming less exact (positive orb)
- **Aspect Symbols**:
  - ☌ Conjunction (0°)
  - ☍ Opposition (180°)
  - △ Trine (120°)
  - □ Square (90°)
  - ⚹ Sextile (60°)
  - Q Quintile (72°)

## Complete Report

Generate all sections at once:

```python
# Without aspects
report.print_report(include_aspects=False)

# With aspects (limited to 20)
report.print_report(include_aspects=True, max_aspects=20)

# Get as string instead of printing
full_report_string = report.get_full_report(include_aspects=True, max_aspects=15)
```

## Important Distinctions

### Subject vs Chart Data

The `Report` class accepts two types of input:

#### 1. AstrologicalSubjectModel (Basic)

Created with `AstrologicalSubjectFactory.from_birth_data()`:

**Available Sections:**
- ✅ Report Title
- ✅ Subject Data
- ✅ Celestial Points (with speed & declination)
- ✅ Houses
- ✅ Lunar Phase
- ❌ Elements Distribution (not available)
- ❌ Qualities Distribution (not available)
- ❌ Aspects (not available)

```python
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
)
report = Report(john)
# Elements and qualities will show "No data available"
```

#### 2. ChartDataModel (Complete)

Created with `ChartDataFactory.create_chart_data()`:

**Available Sections:**
- ✅ Report Title
- ✅ Subject Data
- ✅ Celestial Points (with speed & declination)
- ✅ Houses
- ✅ Lunar Phase
- ✅ Elements Distribution
- ✅ Qualities Distribution
- ✅ Aspects

```python
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
)
chart = ChartDataFactory.create_chart_data("Natal", first_subject=john)
report = Report(chart)
# All sections available including elements, qualities, and aspects
```

## Advanced Usage

### Custom Report Sections

Build custom reports by combining individual sections:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, Report

# Create subject and chart
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
)
chart = ChartDataFactory.create_chart_data("Natal", first_subject=john)
report = Report(chart)

# Build custom report
custom_report = f"""
{report.get_report_title()}

=== BIRTH DATA ===
{report.get_subject_data_report()}

=== PLANETS WITH SPEED & DECLINATION ===
{report.get_celestial_points_report()}

=== ELEMENTAL ANALYSIS ===
{report.get_elements_report()}

=== MODAL ANALYSIS ===
{report.get_qualities_report()}
"""

print(custom_report)
```

### Filtering Aspects

Control the number of aspects displayed:

```python
# Show only the 5 strongest aspects
aspects = report.get_aspects_report(max_aspects=5)

# Show all aspects
aspects = report.get_aspects_report(max_aspects=None)
```

### Export to File

Save reports to text files:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, Report

john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
)
chart = ChartDataFactory.create_chart_data("Natal", first_subject=john)
report = Report(chart)

# Get complete report as string
full_report = report.get_full_report(include_aspects=True, max_aspects=30)

# Save to file
with open("john_lennon_report.txt", "w", encoding="utf-8") as f:
    f.write(full_report)
```

## Speed and Declination

### Speed (Daily Motion)

The **speed** field shows the daily motion of celestial bodies in degrees per day:

**Typical Speed Values:**
- **Moon**: ~12-14°/day (fastest)
- **Sun**: ~0.96-1.02°/day
- **Mercury**: 0-2.2°/day (varies greatly)
- **Venus**: 0-1.3°/day
- **Mars**: 0-0.8°/day
- **Jupiter**: 0-0.25°/day
- **Saturn**: 0-0.13°/day
- **Uranus, Neptune, Pluto**: <0.05°/day (slowest)

**Retrograde Motion:**
- Negative speed values indicate retrograde (backward) motion
- Example: Jupiter at -0.11°/day is moving retrograde

**Interpretation:**
- Higher speed = more activity, quicker changes
- Retrograde = internalization, review, delays
- Stationary (near 0°/day) = concentrated energy, pivotal moments

### Declination (Celestial Latitude)

The **declination** field shows the celestial latitude of planets:

**Range**: -90° to +90° (relative to celestial equator)

**Typical Ranges:**
- **Sun**: -23.44° to +23.44° (seasonal variation)
- **Moon**: ~±28° (varies monthly)
- **Planets**: Generally stay within ±28° of celestial equator
- **Lunar Nodes**: ~±18-22° (shows ecliptic-equator intersection)

**Interpretation:**
- Positive declination: Northern celestial hemisphere (more visible in northern latitudes)
- Negative declination: Southern celestial hemisphere (more visible in southern latitudes)
- High absolute declination: Extreme energies, out-of-bounds behavior
- Zero declination: Crossing celestial equator, balanced energy
- Planets at same declination: Parallel aspects (similar influence)

**Out of Bounds:**
When declination exceeds ±23.44° (Sun's maximum), the planet is "out of bounds":
- Unusual, unconventional energy expression
- Operating outside normal parameters
- Heightened intensity and independence

## API Reference

### Report Class

```python
class Report:
    """
    Create comprehensive astrological reports.
    
    Args:
        instance: AstrologicalSubjectModel, SingleChartDataModel, or DualChartDataModel
    """
    
    def __init__(
        self, 
        instance: Union[AstrologicalSubjectModel, SingleChartDataModel, DualChartDataModel]
    ) -> None:
        """Initialize report with subject or chart data."""
    
    def get_report_title(self) -> str:
        """Generate the report title."""
    
    def get_subject_data_report(self) -> str:
        """Get birth data and settings report."""
    
    def get_celestial_points_report(self) -> str:
        """Get celestial points with speed and declination."""
    
    def get_houses_report(self) -> str:
        """Get houses system report."""
    
    def get_lunar_phase_report(self) -> str:
        """Get lunar phase information."""
    
    def get_elements_report(self) -> str:
        """
        Get element distribution report.
        Only available with ChartDataFactory chart models.
        """
    
    def get_qualities_report(self) -> str:
        """
        Get quality distribution report.
        Only available with ChartDataFactory chart models.
        """
    
    def get_aspects_report(self, max_aspects: Optional[int] = None) -> str:
        """
        Get aspects report.
        Only available with ChartDataFactory chart models.
        
        Args:
            max_aspects: Maximum aspects to display (None = all)
        """
    
    def get_full_report(
        self, 
        include_aspects: bool = True, 
        max_aspects: Optional[int] = 20
    ) -> str:
        """
        Get complete report with all sections.
        
        Args:
            include_aspects: Whether to include aspects
            max_aspects: Maximum aspects to display
        """
    
    def print_report(
        self, 
        include_aspects: bool = True, 
        max_aspects: Optional[int] = 20
    ) -> None:
        """
        Print complete report to console.
        
        Args:
            include_aspects: Whether to include aspects
            max_aspects: Maximum aspects to display
        """
```

## Examples

### Example 1: Quick Console Inspection

```python
from kerykeion import AstrologicalSubjectFactory, Report

# Quick subject inspection
subject = AstrologicalSubjectFactory.from_birth_data(
    "Test Subject", 1990, 5, 15, 12, 0, "London", "GB"
)
Report(subject).print_report(include_aspects=False)
```

### Example 2: Complete Analysis

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, Report

# Full chart analysis
subject = AstrologicalSubjectFactory.from_birth_data(
    "Jane Doe", 1985, 8, 20, 14, 30, "New York", "US"
)
chart = ChartDataFactory.create_chart_data("Natal", first_subject=subject)
report = Report(chart)

# Individual sections for specific analysis
print("=== SPEED ANALYSIS ===")
print(report.get_celestial_points_report())

print("\n=== TEMPERAMENT ANALYSIS ===")
print(report.get_elements_report())

print("\n=== MODALITY ANALYSIS ===")
print(report.get_qualities_report())

print("\n=== STRONGEST ASPECTS ===")
print(report.get_aspects_report(max_aspects=5))
```

### Example 3: Batch Processing

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, Report
import os

# Batch generate reports
subjects_data = [
    ("Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE"),
    ("Marie Curie", 1867, 11, 7, 0, 0, "Warsaw", "PL"),
    ("Isaac Newton", 1643, 1, 4, 1, 30, "Woolsthorpe", "GB"),
]

output_dir = "astrological_reports"
os.makedirs(output_dir, exist_ok=True)

for name, year, month, day, hour, minute, city, nation in subjects_data:
    subject = AstrologicalSubjectFactory.from_birth_data(
        name, year, month, day, hour, minute, city, nation
    )
    chart = ChartDataFactory.create_chart_data("Natal", first_subject=subject)
    report = Report(chart)
    
    # Save report
    filename = f"{output_dir}/{name.replace(' ', '_')}_report.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report.get_full_report(include_aspects=True, max_aspects=20))
    
    print(f"✓ Generated report for {name}")
```

### Example 4: Comparing Two Charts

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, Report

# Create two subjects
john = AstrologicalSubjectFactory.from_birth_data(
    "John", 1980, 5, 10, 12, 0, "London", "GB"
)
jane = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1982, 8, 15, 18, 30, "Paris", "FR"
)

# Generate individual reports
john_chart = ChartDataFactory.create_chart_data("Natal", first_subject=john)
jane_chart = ChartDataFactory.create_chart_data("Natal", first_subject=jane)

print("=== JOHN'S ELEMENTAL BALANCE ===")
print(Report(john_chart).get_elements_report())

print("\n=== JANE'S ELEMENTAL BALANCE ===")
print(Report(jane_chart).get_elements_report())

# Generate synastry report
synastry = ChartDataFactory.create_chart_data("Synastry", first_subject=john, second_subject=jane)
synastry_report = Report(synastry)

print("\n=== SYNASTRY ASPECTS ===")
print(synastry_report.get_aspects_report(max_aspects=15))
```

## Best Practices

1. **Use Chart Data for Complete Analysis**: Always use `ChartDataFactory` when you need elements, qualities, or aspects
2. **Limit Aspect Display**: Use `max_aspects` parameter to show only the most relevant aspects
3. **Custom Section Order**: Build custom reports by calling individual section methods
4. **File Export**: Save reports to files for record-keeping or batch processing
5. **Error Handling**: Check for "No data available" messages when using basic subjects
6. **Encoding**: Use UTF-8 encoding when saving reports to preserve emoji characters

## Troubleshooting

### "No element distribution data available"

**Cause**: Using `AstrologicalSubjectModel` instead of chart data.

**Solution**: Use `ChartDataFactory` to create chart data:
```python
chart = ChartDataFactory.create_chart_data("Natal", first_subject=subject)
report = Report(chart)
```

### Missing Emoji Characters

**Cause**: Terminal or file encoding doesn't support Unicode.

**Solution**: 
- Ensure terminal supports UTF-8
- Use UTF-8 encoding when saving to files:
  ```python
  with open("report.txt", "w", encoding="utf-8") as f:
      f.write(report.get_full_report())
  ```

### Aspect Section Empty

**Cause**: No aspects within configured orbs.

**Solution**: This is normal for some charts. Check the chart's aspect settings or increase orb values in chart creation.

## Performance Considerations

- Report generation is very fast (<0.1s for typical charts)
- The main computation time is in creating the chart data, not the report
- Individual section methods are more efficient when you need specific data
- Use `max_aspects` to limit aspect processing for large charts

## See Also

- [Chart Data Factory](chart_data_factory.md) - Generate chart data with elements and qualities
- [Astrological Subject Factory](astrological_subject_factory.md) - Create basic subjects
- [Aspects](aspects.md) - Understanding aspect calculations
- [Utilities](utilities.md) - Helper functions for astrological calculations
