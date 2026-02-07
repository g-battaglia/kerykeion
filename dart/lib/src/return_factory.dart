import 'package:kerykeion_dart/src/models/astrological_subject.dart';
import 'package:kerykeion_dart/src/astrological_subject_factory.dart';
import 'package:kerykeion_dart/src/utilities.dart';
import 'package:sweph/sweph.dart' as swe;
import 'package:timezone/timezone.dart' as tz;

class ReturnFactory {
  /// Calculates the Solar Return chart for a given year.
  /// Finds the exact moment when the Sun returns to its natal position.
  static Future<AstrologicalSubjectModel> calculateSolarReturn({required AstrologicalSubjectModel natalSubject, required int returnYear}) async {
    if (natalSubject.sun == null) {
      throw Exception("Natal subject must have Sun position calculated");
    }

    final natalSunLongitude = natalSubject.sun!.absPos;

    // Start search from birthday in return year
    final searchStart = DateTime.utc(returnYear, natalSubject.month!, natalSubject.day!, natalSubject.hour!, natalSubject.minute!);

    // Find exact return time using iterative search
    final returnTime = await _findPlanetReturn(
      targetLongitude: natalSunLongitude,
      planetId: swe.HeavenlyBody.SE_SUN,
      searchStart: searchStart,
      maxDaysSearch: 3, // Sun returns are within ~2 days of birthday
    );

    // Convert back to local time for the natal location
    final location = natalSubject.tzStr == 'UTC' ? tz.UTC : tz.getLocation(natalSubject.tzStr!);
    final localReturnTime = tz.TZDateTime.from(returnTime, location);

    // Create return chart
    return await AstrologicalSubjectFactory.createSubject(
      name: "${natalSubject.name} - Solar Return $returnYear",
      year: localReturnTime.year,
      month: localReturnTime.month,
      day: localReturnTime.day,
      hour: localReturnTime.hour,
      minute: localReturnTime.minute,
      city: natalSubject.city ?? "Return Location",
      nation: natalSubject.nation ?? "Return Nation",
      lng: natalSubject.lng!,
      lat: natalSubject.lat!,
      tzStr: natalSubject.tzStr!,
      housesSystemIdentifier: natalSubject.housesSystemIdentifier,
      perspectiveType: natalSubject.perspectiveType,
    );
  }

  /// Calculates the Lunar Return chart for a given month/year.
  /// Finds the exact moment when the Moon returns to its natal position.
  static Future<AstrologicalSubjectModel> calculateLunarReturn({
    required AstrologicalSubjectModel natalSubject,
    required int returnYear,
    required int returnMonth,
  }) async {
    if (natalSubject.moon == null) {
      throw Exception("Natal subject must have Moon position calculated");
    }

    final natalMoonLongitude = natalSubject.moon!.absPos;

    // Start search from first day of return month
    final searchStart = DateTime.utc(returnYear, returnMonth, 1, 0, 0);

    // Find exact return time
    final returnTime = await _findPlanetReturn(
      targetLongitude: natalMoonLongitude,
      planetId: swe.HeavenlyBody.SE_MOON,
      searchStart: searchStart,
      maxDaysSearch: 31, // Moon returns happen monthly
    );

    // Convert to local time
    final location = natalSubject.tzStr == 'UTC' ? tz.UTC : tz.getLocation(natalSubject.tzStr!);
    final localReturnTime = tz.TZDateTime.from(returnTime, location);

    // Create return chart
    return await AstrologicalSubjectFactory.createSubject(
      name: "${natalSubject.name} - Lunar Return $returnYear-$returnMonth",
      year: localReturnTime.year,
      month: localReturnTime.month,
      day: localReturnTime.day,
      hour: localReturnTime.hour,
      minute: localReturnTime.minute,
      city: natalSubject.city ?? "Return Location",
      nation: natalSubject.nation ?? "Return Nation",
      lng: natalSubject.lng!,
      lat: natalSubject.lat!,
      tzStr: natalSubject.tzStr!,
      housesSystemIdentifier: natalSubject.housesSystemIdentifier,
      perspectiveType: natalSubject.perspectiveType,
    );
  }

  /// Internal helper to find exact planetary return time using binary search.
  static Future<DateTime> _findPlanetReturn({
    required double targetLongitude,
    required swe.HeavenlyBody planetId,
    required DateTime searchStart,
    required int maxDaysSearch,
  }) async {
    // Normalize target longitude
    final target = targetLongitude % 360;

    // Binary search parameters
    double startJd = datetimeToJulian(searchStart);
    double endJd = startJd + maxDaysSearch;

    const double tolerance = 0.0001; // ~8.6 seconds precision
    const int maxIterations = 50;

    for (int i = 0; i < maxIterations; i++) {
      double midJd = (startJd + endJd) / 2;

      // Calculate planet position at midpoint
      final result = swe.Sweph.swe_calc_ut(midJd, planetId, swe.SwephFlag.SEFLG_SWIEPH | swe.SwephFlag.SEFLG_SPEED);

      final currentLongitude = result.longitude % 360;

      // Calculate angular distance (accounting for 0/360 boundary)
      double distance = (currentLongitude - target) % 360;
      if (distance > 180) distance -= 360;
      if (distance < -180) distance += 360;

      // Check if we're close enough
      if (distance.abs() < tolerance) {
        return julianToDatetime(midJd);
      }

      // Determine which half to search
      // If planet hasn't reached target yet, search later half
      // This assumes forward motion (works for Sun, needs refinement for Moon retrograde)
      if (distance < 0) {
        startJd = midJd;
      } else {
        endJd = midJd;
      }

      // Safety check: if range is too small, we're done
      if ((endJd - startJd) < tolerance) {
        return julianToDatetime(midJd);
      }
    }

    // If we didn't converge, return best estimate
    return julianToDatetime((startJd + endJd) / 2);
  }
}
