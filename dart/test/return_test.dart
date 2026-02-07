import 'package:flutter_test/flutter_test.dart';
import 'package:kerykeion_dart/src/astrological_subject_factory.dart';
import 'package:kerykeion_dart/src/return_factory.dart';

void main() {
  setUpAll(() async {
    await AstrologicalSubjectFactory.initialize();
  });

  group('Return Charts', () {
    test('Calculate Solar Return', () async {
      // Create natal chart
      final natal = await AstrologicalSubjectFactory.createSubject(
        name: "Test Subject",
        year: 1990,
        month: 6,
        day: 15,
        hour: 12,
        minute: 0,
        city: "London",
        nation: "GB",
        lng: 0,
        lat: 51.5,
        tzStr: "Europe/London",
      );

      // Calculate solar return for 2020
      final solarReturn = await ReturnFactory.calculateSolarReturn(natalSubject: natal, returnYear: 2020);

      // Verify the Sun position matches natal Sun
      expect(solarReturn.sun, isNotNull);
      expect(natal.sun, isNotNull);

      final natalSunPos = natal.sun!.absPos;
      final returnSunPos = solarReturn.sun!.absPos;

      // Should be within 0.01 degrees (about 36 seconds of arc)
      expect((returnSunPos - natalSunPos).abs(), lessThan(0.01));

      // Verify it's in the correct year
      expect(solarReturn.year, 2020);

      // Should be close to birthday (within a few days)
      expect((solarReturn.month! - natal.month!).abs(), lessThanOrEqualTo(1));
    });

    test('Calculate Lunar Return', () async {
      // Create natal chart
      final natal = await AstrologicalSubjectFactory.createSubject(
        name: "Test Subject",
        year: 1990,
        month: 6,
        day: 15,
        hour: 12,
        minute: 0,
        city: "London",
        nation: "GB",
        lng: 0,
        lat: 51.5,
        tzStr: "Europe/London",
      );

      // Calculate lunar return for June 2020
      final lunarReturn = await ReturnFactory.calculateLunarReturn(natalSubject: natal, returnYear: 2020, returnMonth: 6);

      // Verify the Moon position matches natal Moon
      expect(lunarReturn.moon, isNotNull);
      expect(natal.moon, isNotNull);

      final natalMoonPos = natal.moon!.absPos;
      final returnMoonPos = lunarReturn.moon!.absPos;

      // Should be within 0.1 degrees (Moon moves faster, less precision needed)
      expect((returnMoonPos - natalMoonPos).abs(), lessThan(0.1));

      // Verify it's in the correct month/year
      expect(lunarReturn.year, 2020);
      expect(lunarReturn.month, 6);
    });
  });
}
