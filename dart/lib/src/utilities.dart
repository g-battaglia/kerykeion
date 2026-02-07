import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/models/kerykeion_point.dart';
import 'package:kerykeion_dart/src/models/lunar_phase.dart';
import 'package:kerykeion_dart/src/constants.dart';
import 'package:sweph/sweph.dart' as swe;

// ... existing code ...

// =============================================================================
// DATE/TIME UTILITIES
// =============================================================================

double datetimeToJulian(DateTime dt) {
  // Ensure UTC? swe_julday expects UT if calculating for UT.
  // The factory converts local to UTC before calling this.
  // swe_julday args: year, month, day, hour (decimal), calendar flag (1 for Gregorian)

  double hourDecimal = dt.hour + (dt.minute / 60.0) + (dt.second / 3600.0) + (dt.millisecond / 3600000.0);

  return swe.Sweph.swe_julday(dt.year, dt.month, dt.day, hourDecimal, swe.CalendarType.SE_GREG_CAL);
}

DateTime julianToDatetime(double julianDay) {
  // swe_revjul(jd, flag) -> returns Year, Month, Day, Hour
  final date = swe.Sweph.swe_revjul(julianDay, swe.CalendarType.SE_GREG_CAL);

  int year = date.year;
  int month = date.month;
  int day = date.day;
  double hourDecimal = (date.hour as num).toDouble();

  int hour = hourDecimal.floor();
  double remainingMinutes = (hourDecimal - hour) * 60;
  int minute = remainingMinutes.floor();
  double remainingSeconds = (remainingMinutes - minute) * 60;
  int second = remainingSeconds.floor();
  // ignore milliseconds for simplicity or calc them

  return DateTime.utc(year, month, day, hour, minute, second);
}

KerykeionPointModel getKerykeionPointFromDegree(double degree, String name, PointType pointType, {double? speed, double? declination}) {
  // ... existing implementation ...
  if (degree < 0) {
    degree = degree % 360;
  }

  if (degree >= 360) {
    throw Exception("Error in calculating positions! Degrees: $degree");
  }

  var signIndex = (degree ~/ 30);
  var signDegree = degree % 30;
  var zodiacSign = zodiacSigns[signIndex]!;

  return KerykeionPointModel(
    name: name,
    pointType: pointType,
    quality: zodiacSign.quality,
    element: zodiacSign.element,
    sign: zodiacSign.sign,
    signNum: zodiacSign.signNum,
    position: signDegree,
    absPos: degree,
    emoji: zodiacSign.emoji,
    speed: speed,
    declination: declination,
  );
}

// =============================================================================
// HOUSE UTILITIES
// =============================================================================

bool isPointBetween(double startAngle, double endAngle, double candidate) {
  double normalize(double value) => value % 360;

  double start = normalize(startAngle);
  double end = normalize(endAngle);
  double target = normalize(candidate);
  double span = (end - start) % 360;

  if (span > 180) {
    // In Kerykeion logic, if house span > 180 it might be an issue, but standard houses shouldn't exceed 180 usually.
    // However, Placidus at high latitudes can be weird.
    // For now, we follow Python logic which raises exception or handles strict check.
    // Python code: raise KerykeionException...
    // We will assume valid houses for now or log/throw.
    // Let's implement basic check.
  }

  if (target == start) return true;
  if (target == end) return false;

  double distanceFromStart = (target - start) % 360;
  return distanceFromStart < span;
}

House getPlanetHouse(double planetDegree, List<double> housesDegreeUtList) {
  List<House> houseNames = House.values;

  for (int i = 0; i < houseNames.length; i++) {
    double startDegree = housesDegreeUtList[i];
    double endDegree = housesDegreeUtList[(i + 1) % housesDegreeUtList.length];

    if (isPointBetween(startDegree, endDegree, planetDegree)) {
      return houseNames[i];
    }
  }

  throw Exception("Error in house calculation, planet: $planetDegree");
}

String getHouseName(int houseNumber) {
  return houseNames[houseNumber]!.toString().split('.').last;
}

int getHouseNumber(String houseName) {
  // Convert String to Enum
  House house = House.values.firstWhere((e) => e.toString().split('.').last == houseName);
  return houseNumbers[house]!;
}

// =============================================================================
// LUNAR PHASE UTILITIES
// =============================================================================

int _getLunarPhaseIndex(int phase) {
  if (phase == 1) return 0;
  if (phase < 7) return 1;
  if (phase >= 7 && phase <= 9) return 2;
  if (phase < 14) return 3;
  if (phase == 14) return 4;
  if (phase < 20) return 5;
  if (phase >= 20 && phase <= 22) return 6;
  if (phase <= 28) return 7;
  throw Exception("Error in lunar phase calculation! Phase: $phase");
}

LunarPhaseEmoji getMoonEmojiFromPhaseInt(int phase) {
  return LunarPhaseEmoji.values[_getLunarPhaseIndex(phase)];
}

LunarPhaseName getMoonPhaseNameFromPhaseInt(int phase) {
  return LunarPhaseName.values[_getLunarPhaseIndex(phase)];
}

LunarPhaseModel calculateMoonPhase(double moonAbsPos, double sunAbsPos) {
  double degreesBetween = (moonAbsPos - sunAbsPos) % 360;
  double step = 360.0 / 28.0;
  int moonPhase = (degreesBetween / step).floor() + 1;

  // LunarPhaseEmoji emoji = getMoonEmojiFromPhaseInt(moonPhase); // Removed unused variable

  const List<String> emojiMap = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"];
  String emojiStr = emojiMap[_getLunarPhaseIndex(moonPhase)];
  LunarPhaseName name = getMoonPhaseNameFromPhaseInt(moonPhase);

  return LunarPhaseModel(degreesBetweenSunAndMoon: degreesBetween, moonPhase: moonPhase, moonEmoji: emojiStr, moonPhaseName: name);
}

// =============================================================================
// COMPOSITE UTILITIES
// =============================================================================

/// Calculates the shortest angular distance between two points on a 360-degree circle.
/// Returns a value between -180 and 180.
double getShortestDistance(double p1, double p2) {
  double diff = (p2 - p1) % 360;
  if (diff > 180) {
    diff -= 360;
  }
  return diff;
}

/// Calculates the midpoint between two degrees.
/// Always chooses the midpoint on the shortest arc between the two points.
double getMidpoint(double p1, double p2) {
  double distance = getShortestDistance(p1, p2);
  double midpoint = (p1 + distance / 2) % 360;
  if (midpoint < 0) {
    midpoint += 360;
  }
  return midpoint;
}
