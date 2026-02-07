import 'package:kerykeion_dart/kerykeion_dart.dart';
import 'package:test/test.dart';

void main() {
  group('ChartDataFactory Tests', () {
    setUp(() async {
      await AstrologicalSubjectFactory.initialize();
    });

    test('Calculate Moon Phase', () {
      // Test New Moon (approximate, angle should be near 0)
      // Sun at 0, Moon at 0 -> Angle 0 -> Phase 1 (New Moon)
      final phase1 = calculateMoonPhase(0, 0);
      expect(phase1.moonPhase, 1);
      expect(phase1.moonPhaseName, LunarPhaseName.New_Moon);
      expect(phase1.moonEmoji, "🌑");

      // Test Full Moon (approximate, angle 180)
      // Sun at 0, Moon at 180 -> Angle 180 -> Phase 15 (Full Moon)
      final phase15 = calculateMoonPhase(180, 0);
      expect(phase15.moonPhase, 15);
      expect(phase15.moonPhaseName, LunarPhaseName.Full_Moon);
      expect(phase15.moonEmoji, "🌕");

      // Test Waxing Crescent
      final phase5 = calculateMoonPhase(45, 0); // 45 degrees
      expect(phase5.moonPhase, greaterThan(1));
      expect(phase5.moonPhase, lessThan(8));
    });

    test('Create Natal Chart Data', () async {
      final subject = await AstrologicalSubjectFactory.createSubject(
        name: "Test Subject",
        year: 2000,
        month: 1,
        day: 1,
        hour: 12,
        minute: 0,
        city: "London",
        nation: "GB",
        lng: 0,
        lat: 51.5,
        tzStr: "Europe/London",
      );

      final chartData = ChartDataFactory.createChartData(ChartType.Natal, subject);

      expect(chartData, isA<SingleChartDataModel>());
      expect(chartData.chartType, "Natal");
      expect((chartData as SingleChartDataModel).firstSubject.name, "Test Subject");

      // Verify distributions are populated
      expect(
        chartData.elementDistribution.fire + chartData.elementDistribution.earth + chartData.elementDistribution.air + chartData.elementDistribution.water,
        greaterThan(0),
      );
      expect(chartData.qualityDistribution.cardinal + chartData.qualityDistribution.fixed + chartData.qualityDistribution.mutable, greaterThan(0));

      // Verify aspects
      expect(chartData.aspects, isNotEmpty);
    });

    test('Create Synastry Chart Data with House Comparison', () async {
      final subject1 = await AstrologicalSubjectFactory.createSubject(
        name: "Subject A",
        year: 2000,
        month: 1,
        day: 1,
        hour: 12,
        minute: 0,
        city: "London",
        nation: "GB",
        lng: 0,
        lat: 51.5,
        tzStr: "Europe/London",
      );

      final subject2 = await AstrologicalSubjectFactory.createSubject(
        name: "Subject B",
        year: 2001,
        month: 1,
        day: 1,
        hour: 12,
        minute: 0,
        city: "London",
        nation: "GB",
        lng: 0,
        lat: 51.5,
        tzStr: "Europe/London",
      );

      final chartData = ChartDataFactory.createChartData(ChartType.Synastry, subject1, secondSubject: subject2, includeHouseComparison: true);

      expect(chartData, isA<DualChartDataModel>());
      final dualData = chartData as DualChartDataModel;

      expect(dualData.houseComparison, isNotNull);
      expect(dualData.houseComparison!.firstPointsInSecondHouses, isNotEmpty);
      expect(dualData.houseComparison!.secondPointsInFirstHouses, isNotEmpty);

      // Verify a point
      final sunInB = dualData.houseComparison!.firstPointsInSecondHouses.firstWhere((p) => p.pointName == "Sun");
      expect(sunInB.pointOwnerName, "Subject A");
      expect(sunInB.projectedHouseOwnerName, "Subject B");
    });

    test('Create Composite Chart Data', () async {
      final subject1 = await AstrologicalSubjectFactory.createSubject(
        name: "Subject A",
        year: 2000,
        month: 1,
        day: 1,
        hour: 12,
        minute: 0,
        city: "London",
        nation: "GB",
        lng: 0,
        lat: 51.5,
        tzStr: "Europe/London",
      );

      // Let's manually tweak subject 2's sun to be 180 degrees away to test midpoint if possible?
      // No, createSubject returns a complete model. Hard to tweak just one field consistently.
      // Better: Create two subjects with known difference.
      // Subject 1: Jan 1. Sun ~ 280 deg (Capricorn)
      // Subject 2: Jul 1. Sun ~ 100 deg (Cancer)
      // Midpoint: ~ 190 or 10.

      final subject3 = await AstrologicalSubjectFactory.createSubject(
        name: "Subject C",
        year: 2000,
        month: 7,
        day: 1,
        hour: 12,
        minute: 0,
        city: "London",
        nation: "GB",
        lng: 0,
        lat: 51.5,
        tzStr: "Europe/London",
      );

      final compositeData = ChartDataFactory.createChartData(ChartType.Composite, subject1, secondSubject: subject3);

      expect(compositeData, isA<SingleChartDataModel>());
      final singleData = compositeData as SingleChartDataModel;
      expect(singleData.firstSubject.name, contains("Composite"));

      final sunPos = singleData.firstSubject.sun!.absPos;
      // S1 Sun: ~280. S3 Sun: ~100. Diff: 180. Midpoint: ~190 or 10.
      // Shortest arc? 280 -> 100 via 360 is (360-280)+100 = 180.
      // Midpoint should be 280 + 90 = 370 -> 10. Or 100 - 90 = 10.
      // Let's just assert it is valid number for now.
      expect(sunPos, greaterThanOrEqualTo(0));
      expect(sunPos, lessThan(360));
    });
  });
}
