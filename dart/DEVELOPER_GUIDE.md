# Kerykeion Dart - Developer Guide

**Version:** 1.0  
**Last Updated:** 2026-02-07  
**Python Reference:** Kerykeion v2.1.18+

## Table of Contents

1. [Overview](#overview)
2. [Conversion Process from Python](#conversion-process-from-python)
3. [Architecture & Design Patterns](#architecture--design-patterns)
4. [Testing Strategy](#testing-strategy)
5. [Debugging Guide](#debugging-guide)
6. [Known Issues & Limitations](#known-issues--limitations)
7. [Future Development](#future-development)

---

## Overview

This is a Dart port of the Python Kerykeion library, providing comprehensive astrological calculations using the Swiss Ephemeris. The implementation maintains functional parity with Python Kerykeion while leveraging Dart's type safety and async capabilities.

### Key Features Implemented

- ✅ **Core Calculations**: Natal charts with all major/minor bodies, asteroids, fixed stars
- ✅ **Aspects**: Single and dual chart aspect calculations with configurable orbs
- ✅ **Chart Data**: Element/quality distributions, lunar phases, house comparisons
- ✅ **Composite Charts**: Midpoint method for relationship analysis
- ✅ **Return Charts**: Solar and lunar returns with high precision (< 0.01° for Sun)
- ✅ **Synastry**: Inter-chart aspects and house overlays

### Dependencies

```yaml
dependencies:
  sweph: ^2.10.3+3  # Swiss Ephemeris bindings
  timezone: ^0.9.0   # Timezone calculations
```

---

## Conversion Process from Python

### Phase-by-Phase Conversion

#### Phase 1: Foundation (Completed)
**Python Files → Dart Files:**
- `kr_types/kr_types.py` → `lib/src/types.dart`
- `kr_types/kr_models.py` → `lib/src/models/*.dart`
- `settings/kerykeion_settings.py` → `lib/src/settings/*.dart`

**Key Conversions:**
```python
# Python
class KerykeionPointModel:
    def __init__(self, name: str, quality: str, ...):
        self.name = name
        self.quality = quality
```

```dart
// Dart
class KerykeionPointModel {
  final String name;
  final String quality;
  
  const KerykeionPointModel({
    required this.name,
    required this.quality,
  });
}
```

**Challenges:**
- Python's dynamic typing → Dart's strict null safety
- Python's `@dataclass` → Dart's `const` constructors
- Python's `Literal` types → Dart enums

#### Phase 2: Core Calculations (Completed)
**Python Files → Dart Files:**
- `astrological_subject.py` → `lib/src/astrological_subject_factory.dart`
- `utilities.py` → `lib/src/utilities.dart`

**Key Conversions:**

1. **Julian Day Calculation:**
```python
# Python (using swisseph directly)
import swisseph as swe
jd = swe.julday(year, month, day, hour)
```

```dart
// Dart (using sweph package)
import 'package:sweph/sweph.dart' as swe;

double datetimeToJulian(DateTime dt) {
  double hourDecimal = dt.hour + (dt.minute / 60.0) + 
                       (dt.second / 3600.0);
  return swe.Sweph.swe_julday(
    dt.year, dt.month, dt.day, 
    hourDecimal, 
    swe.CalendarType.SE_GREG_CAL
  );
}
```

2. **Planetary Calculations:**
```python
# Python
result = swe.calc_ut(jd, planet_id, flags)
longitude = result[0]
```

```dart
// Dart
final result = swe.Sweph.swe_calc_ut(
  julianDay, 
  swe.HeavenlyBody(planetId), 
  iflag
);
final longitude = result.longitude;
```

**Challenges:**
- Async initialization required for sweph in Dart
- Different API structure in sweph package vs Python swisseph
- Timezone handling (Python's `pytz` → Dart's `timezone` package)

#### Phase 3: Aspects (Completed)
**Python Files → Dart Files:**
- `aspects/aspects_utils.py` → `lib/src/aspects/aspects_utils.dart`
- `aspects/synastry_aspects.py` → `lib/src/aspects/aspects_factory.dart`

**Key Conversions:**

1. **Aspect Detection:**
```python
# Python
def is_aspect(angle: float, aspect_degrees: float, orb: float) -> bool:
    return abs(angle - aspect_degrees) <= orb
```

```dart
// Dart
bool isAspect(double angle, double aspectDegrees, double orb) {
  return (angle - aspectDegrees).abs() <= orb;
}
```

2. **Movement Detection:**
```python
# Python - using speed directly
if point1.speed > 0 and point2.speed > 0:
    movement = "Applying"
```

```dart
// Dart - null-safe speed handling
String? detectMovement(KerykeionPointModel p1, KerykeionPointModel p2) {
  if (p1.speed == null || p2.speed == null) return null;
  
  if (p1.speed! > 0 && p2.speed! > 0) {
    return "Applying";
  }
  // ...
}
```

**Challenges:**
- Null safety for optional speed/declination values
- Generic type handling for aspect lists
- Enum serialization for aspect types

#### Phase 4: Chart Data (Completed)
**Python Files → Dart Files:**
- `chart_data_factory.py` → `lib/src/chart_data_factory.dart`

**Key Conversions:**

1. **Distribution Calculations:**
```python
# Python - using Counter
from collections import Counter
element_counts = Counter(point.element for point in points)
dominant = element_counts.most_common(1)[0][0]
```

```dart
// Dart - manual counting
Map<String, int> elementCounts = {};
for (var point in points) {
  elementCounts[point.element] = 
    (elementCounts[point.element] ?? 0) + 1;
}
String dominant = elementCounts.entries
  .reduce((a, b) => a.value > b.value ? a : b)
  .key;
```

2. **House Comparisons:**
```python
# Python
def get_planet_house(planet_degree, houses):
    for i, house in enumerate(houses):
        if is_between(house, houses[i+1], planet_degree):
            return i + 1
```

```dart
// Dart - using enums
House getPlanetHouse(double planetDegree, List<double> houses) {
  List<House> houseNames = House.values;
  
  for (int i = 0; i < houseNames.length; i++) {
    if (isPointBetween(houses[i], houses[i+1], planetDegree)) {
      return houseNames[i];
    }
  }
  throw Exception("Error in house calculation");
}
```

**Challenges:**
- Python's `Counter` → Manual map operations in Dart
- Dynamic property access → Explicit field mapping
- Optional parameters with defaults

#### Phase 5: Composite & Returns (Completed)
**Python Files → Dart Files:**
- `composite.py` → `lib/src/composite_factory.dart`
- `return_charts.py` → `lib/src/return_factory.dart`

**Key Conversions:**

1. **Midpoint Calculation:**
```python
# Python
def get_midpoint(p1: float, p2: float) -> float:
    diff = (p2 - p1) % 360
    if diff > 180:
        diff -= 360
    return (p1 + diff / 2) % 360
```

```dart
// Dart
double getMidpoint(double p1, double p2) {
  double distance = getShortestDistance(p1, p2);
  double midpoint = (p1 + distance / 2) % 360;
  if (midpoint < 0) midpoint += 360;
  return midpoint;
}
```

2. **Binary Search for Returns:**
```python
# Python - using scipy or custom search
from scipy.optimize import brentq

def find_return(target_longitude, start_jd):
    def f(jd):
        pos = swe.calc_ut(jd, planet)[0]
        return (pos - target_longitude) % 360
    
    return brentq(f, start_jd, start_jd + max_days)
```

```dart
// Dart - custom binary search
Future<DateTime> _findPlanetReturn({
  required double targetLongitude,
  required swe.HeavenlyBody planetId,
  required DateTime searchStart,
  required int maxDaysSearch,
}) async {
  double startJd = datetimeToJulian(searchStart);
  double endJd = startJd + maxDaysSearch;
  
  const double tolerance = 0.0001; // ~8.6 seconds
  
  for (int i = 0; i < 50; i++) {
    double midJd = (startJd + endJd) / 2;
    final result = swe.Sweph.swe_calc_ut(midJd, planetId, flags);
    double currentLong = result.longitude % 360;
    
    double distance = (currentLong - targetLongitude) % 360;
    if (distance > 180) distance -= 360;
    if (distance < -180) distance += 360;
    
    if (distance.abs() < tolerance) {
      return julianToDatetime(midJd);
    }
    
    if (distance < 0) {
      startJd = midJd;
    } else {
      endJd = midJd;
    }
  }
  
  return julianToDatetime((startJd + endJd) / 2);
}
```

**Challenges:**
- No scipy in Dart → Custom binary search implementation
- Async/await for all sweph operations
- Precision requirements (< 0.01° for Sun, < 0.1° for Moon)

---

## Architecture & Design Patterns

### Factory Pattern

All chart creation uses factory methods:

```dart
// Natal Chart
final natal = await AstrologicalSubjectFactory.createSubject(
  name: "John Doe",
  year: 1990,
  month: 6,
  day: 15,
  // ...
);

// Composite Chart
final composite = CompositeSubjectFactory.createCompositeSubject(
  subject1: person1,
  subject2: person2,
);

// Return Chart
final solarReturn = await ReturnFactory.calculateSolarReturn(
  natalSubject: natal,
  returnYear: 2023,
);

// Chart Data
final chartData = ChartDataFactory.createChartData(
  ChartType.Natal,
  natal,
);
```

### Immutable Models

All data models are immutable with `const` constructors:

```dart
class KerykeionPointModel {
  final String name;
  final double absPos;
  final Sign sign;
  // ...
  
  const KerykeionPointModel({
    required this.name,
    required this.absPos,
    required this.sign,
    // ...
  });
}
```

### Null Safety

Dart's null safety is strictly enforced:

```dart
// Optional fields
final double? speed;  // Can be null
final double? declination;  // Can be null

// Required fields
final String name;  // Never null
final double absPos;  // Never null

// Usage
if (point.speed != null) {
  print('Speed: ${point.speed!}');
}
```

### Async Initialization

Swiss Ephemeris requires async initialization:

```dart
void main() async {
  // MUST call before any calculations
  await AstrologicalSubjectFactory.initialize();
  
  // Now safe to create charts
  final chart = await AstrologicalSubjectFactory.createSubject(/*...*/);
}
```

---

## Testing Strategy

### Test Structure

```
test/
├── sweph_test_v2.dart          # Swiss Ephemeris integration
├── astrological_subject_test.dart  # Core calculations
├── extended_points_test.dart   # Asteroids, fixed stars
├── aspects_test.dart           # Aspect calculations
├── chart_data_test.dart        # Chart data generation
├── return_test.dart            # Return charts
└── api_integration_test.dart   # Full API integration
```

### Running Tests

```bash
# All tests
dart test

# Specific test file
dart test test/chart_data_test.dart

# With coverage
dart test --coverage=coverage
dart pub global activate coverage
dart pub global run coverage:format_coverage \
  --lcov --in=coverage --out=coverage/lcov.info
```

### Test Patterns

#### 1. Setup with Initialization

```dart
void main() {
  setUpAll(() async {
    await AstrologicalSubjectFactory.initialize();
  });
  
  test('Calculate natal chart', () async {
    final chart = await AstrologicalSubjectFactory.createSubject(/*...*/);
    expect(chart.sun, isNotNull);
  });
}
```

#### 2. Precision Testing

```dart
test('Solar return precision', () async {
  final natal = await createNatalChart();
  final solarReturn = await ReturnFactory.calculateSolarReturn(
    natalSubject: natal,
    returnYear: 2023,
  );
  
  final difference = (solarReturn.sun!.absPos - natal.sun!.absPos).abs();
  expect(difference, lessThan(0.01), 
    reason: 'Sun position should match within 0.01°');
});
```

#### 3. Comparison with Python

```dart
test('Match Python Kerykeion output', () async {
  // Python reference values (from Kerykeion v2.1.18)
  const pythonSunPos = 83.7234;  // Gemini 23.72°
  
  final chart = await AstrologicalSubjectFactory.createSubject(
    year: 1990, month: 6, day: 15,
    hour: 14, minute: 30,
    lat: 40.7128, lng: -74.0060,
    tzStr: "America/New_York",
  );
  
  expect(chart.sun!.absPos, closeTo(pythonSunPos, 0.01));
});
```

### Known Test Issues

1. **Flutter SDK Compilation Errors**: Tests using `flutter_test` may fail with Flutter SDK errors unrelated to our code. Use pure Dart tests when possible.

2. **Sweph Library Loading**: `dart run` fails to load `libsweph.so`. Always use `dart test` for proper library access.

3. **Timezone Data**: Ensure timezone database is initialized before creating charts with non-UTC timezones.

---

## Debugging Guide

### Common Issues

#### 1. "Failed to load dynamic library 'libsweph.so'"

**Cause:** Running with `dart run` instead of `dart test`, or sweph not initialized.

**Solution:**
```dart
// Always initialize first
await AstrologicalSubjectFactory.initialize();

// Use dart test, not dart run
dart test test/my_test.dart
```

#### 2. "Timezone not found"

**Cause:** Timezone database not initialized or invalid timezone string.

**Solution:**
```dart
import 'package:timezone/data/latest.dart' as tz_data;

void main() async {
  tz_data.initializeTimeZones();  // Initialize timezone DB
  
  // Use IANA timezone names
  final chart = await createSubject(
    tzStr: "America/New_York",  // ✓ Correct
    // tzStr: "EST",  // ✗ Wrong
  );
}
```

#### 3. Null Safety Errors

**Cause:** Accessing nullable fields without null checks.

**Solution:**
```dart
// Wrong
print(point.speed);  // Error if speed is null

// Correct
if (point.speed != null) {
  print(point.speed!);
}

// Or use null-aware operator
print(point.speed ?? 0.0);
```

#### 4. Aspect Calculation Discrepancies

**Cause:** Different orb settings or aspect types between Python and Dart.

**Solution:**
```dart
// Match Python default settings
final aspects = AspectsFactory.singleChartAspects(
  subject,
  activeAspects: defaultActiveAspects,  // Use library defaults
  axisOrbLimit: 1.0,  // Match Python default
);
```

### Debugging Tools

#### 1. Print Detailed Chart Info

```dart
void printChartDebug(AstrologicalSubjectModel chart) {
  print('=== CHART DEBUG ===');
  print('Name: ${chart.name}');
  print('JD: ${chart.julianDay}');
  print('Sun: ${chart.sun!.sign} ${chart.sun!.position}° (${chart.sun!.absPos}°)');
  print('Moon: ${chart.moon!.sign} ${chart.moon!.position}° (${chart.moon!.absPos}°)');
  print('Asc: ${chart.ascendant!.sign} ${chart.ascendant!.position}° (${chart.ascendant!.absPos}°)');
  print('MC: ${chart.mediumCoeli!.sign} ${chart.mediumCoeli!.position}° (${chart.mediumCoeli!.absPos}°)');
}
```

#### 2. Compare with Python

```python
# Python Kerykeion
from kerykeion import AstrologicalSubject

subject = AstrologicalSubject(
    "John Doe", 1990, 6, 15, 14, 30,
    "New York", "US", lat=40.7128, lng=-74.0060
)

print(f"Sun: {subject.sun.sign} {subject.sun.position}° ({subject.sun.abs_pos}°)")
```

```dart
// Dart Kerykeion
final subject = await AstrologicalSubjectFactory.createSubject(
  name: "John Doe",
  year: 1990, month: 6, day: 15,
  hour: 14, minute: 30,
  city: "New York", nation: "US",
  lat: 40.7128, lng: -74.0060,
  tzStr: "America/New_York",
);

print('Sun: ${subject.sun!.sign} ${subject.sun!.position}° (${subject.sun!.absPos}°)');
```

#### 3. Validate Julian Day

```dart
void validateJulianDay(DateTime dt) {
  final jd = datetimeToJulian(dt);
  final reversed = julianToDatetime(jd);
  
  print('Original: $dt');
  print('JD: $jd');
  print('Reversed: $reversed');
  print('Match: ${dt.difference(reversed).inSeconds < 60}');
}
```

---

## Known Issues & Limitations

### Current Limitations

1. **No Progressed Charts**: Not yet implemented (Python has this).

2. **Limited Return Types**: Only Solar and Lunar returns. Python supports Mercury, Venus, Mars returns.

3. **No Davison Composite**: Only Midpoint composite implemented.

4. **Linting Warnings**: 150 info-level warnings (mostly enum naming conventions). Non-critical.

### Differences from Python

| Feature | Python Kerykeion | Dart Kerykeion | Notes |
|---------|-----------------|----------------|-------|
| Return Search | `scipy.optimize.brentq` | Custom binary search | Same precision achieved |
| Timezone | `pytz` | `timezone` package | Different API, same results |
| Initialization | Automatic | Explicit `await init()` | Dart async requirement |
| Null Handling | Optional types | Strict null safety | More type-safe in Dart |

### Performance Notes

- **Initialization**: ~100-500ms (one-time cost)
- **Natal Chart**: ~50-100ms
- **Composite Chart**: ~100-200ms (2x natal + midpoint calc)
- **Solar Return**: ~500-1000ms (binary search iterations)
- **Lunar Return**: ~500-1000ms (binary search iterations)

---

## Future Development

### Planned Features

1. **Progressed Charts**
   - Secondary progressions
   - Solar arc directions
   - Tertiary progressions

2. **Additional Return Types**
   - Mercury returns
   - Venus returns
   - Mars returns

3. **Davison Composite**
   - Alternative to midpoint composite
   - Time/space midpoint method

4. **Report Generation**
   - Text-based interpretations
   - PDF export
   - Customizable templates

5. **Harmonics**
   - Harmonic charts (4th, 5th, 7th, 9th)
   - Harmonic aspects

### Code Quality Improvements

1. **Fix Linting Warnings**
   - Rename enums to lowerCamelCase
   - Use string interpolation
   - Add curly braces to control structures

2. **Enhanced Testing**
   - Integration tests with Python comparison
   - Performance benchmarks
   - Edge case coverage

3. **Documentation**
   - API documentation (dartdoc)
   - Usage examples
   - Tutorial series

### Contributing Guidelines

1. **Code Style**: Follow Dart style guide
2. **Testing**: All new features must have tests
3. **Python Parity**: Verify against Python Kerykeion
4. **Documentation**: Update this guide with changes

---

## Quick Reference

### Essential Commands

```bash
# Initialize project
dart pub get

# Run tests
dart test

# Analyze code
dart analyze

# Format code
dart format lib test

# Generate documentation
dart doc
```

### Key Files

| File | Purpose |
|------|---------|
| `lib/src/astrological_subject_factory.dart` | Core chart calculations |
| `lib/src/composite_factory.dart` | Composite charts |
| `lib/src/return_factory.dart` | Return charts |
| `lib/src/chart_data_factory.dart` | Chart data generation |
| `lib/src/aspects/aspects_factory.dart` | Aspect calculations |
| `lib/src/utilities.dart` | Helper functions |
| `lib/src/types.dart` | Type definitions |
| `lib/src/constants.dart` | Constants and mappings |

### Support

- **Python Reference**: [Kerykeion GitHub](https://github.com/g-battaglia/kerykeion)
- **Swiss Ephemeris**: [Astrodienst Documentation](https://www.astro.com/swisseph/)
- **Dart Package**: `sweph` on pub.dev

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-07  
**Maintainer:** Development Team
