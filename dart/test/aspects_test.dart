import 'package:kerykeion_dart/kerykeion_dart.dart';
import 'package:sweph/sweph.dart';
import 'package:test/test.dart';

void main() {
  setUpAll(() async {
    print("Initializing Sweph...");
    await Sweph.init();
    print("Sweph initialized. Initializing Factory...");
    AstrologicalSubjectFactory.initialize();
    print("Factory initialized.");
  });

  group('Aspect Calculations', () {
    test('calculateAspectMovement', () {
      // Case 1: Applying Conjunction
      // P1 at 10, moving 1 deg/day
      // P2 at 20, moving 0.5 deg/day
      // Aspect: 0 (Conjunction)
      // Current Orb: |10-20| = 10
      // Next Day: P1=11, P2=20.5. Orb: |11-20.5| = 9.5
      // Orb is decreasing -> Applying

      var movement = AspectsUtils.calculateAspectMovement(10.0, 20.0, 0.0, 1.0, 0.5);
      expect(movement, AspectMovementType.Applying);

      // Case 2: Separating Conjunction
      // P1 at 20, moving 1 deg/day
      // P2 at 10, moving 0.5 deg/day
      // Aspect: 0
      // Current Orb: 10
      // Next day: P1=21, P2=10.5. Orb: 10.5
      // Orb increasing -> Separating
      movement = AspectsUtils.calculateAspectMovement(20.0, 10.0, 0.0, 1.0, 0.5);
      expect(movement, AspectMovementType.Separating);

      // Case 3: Converting to Static if speed difference is tiny?
      // Not tested here as speeds are significant.
    });

    test('Single Chart Aspects - Simple', () async {
      // Mock subject data or create a subject with known positions
      // Since we can't easily mock AstrologicalSubjectModel without internal factory or heavy setup,
      // we'll create one "officially" but trust the positions calc (tested elsewhere).
      // Or we can rely on `_calculateSingleChartAspects` logic if we exposed it,
      // but we only exposed `AspectsFactory.singleChartAspects`.

      // Let's use a known date: 2000-01-01 12:00 UTC London
      final subject = await AstrologicalSubjectFactory.createSubject(
        name: "Test Subject",
        year: 2000,
        month: 1,
        day: 1,
        hour: 12,
        minute: 0,
        city: "London",
        nation: "GB",
        lng: 0.0,
        lat: 51.5,
        tzStr: "Europe/London",
      );

      final aspectsModel = AspectsFactory.singleChartAspects(subject);

      expect(aspectsModel.aspects, isNotEmpty);

      // Check for a specific aspect if possible, or just structure.
      // Sun approx 280 (Capricorn)
      // Moon approx 215 (Scorpio)
      // Diff approx 65 degrees -> Sextile (60) with 5 orb?

      // Find aspect between Sun and Moon
      try {
        final sunMoonAspect = aspectsModel.aspects.firstWhere((a) => (a.p1Name == "Sun" && a.p2Name == "Moon") || (a.p1Name == "Moon" && a.p2Name == "Sun"));
        print("Sun-Moon Aspect: ${sunMoonAspect.aspect} orb: ${sunMoonAspect.orbit}");
      } catch (e) {
        print("No Sun-Moon aspect found");
      }

      // Basic validation
      for (var aspect in aspectsModel.aspects) {
        expect(aspect.p1Name, isNotNull);
        expect(aspect.p2Name, isNotNull);
        expect(aspect.aspect, isNotNull);
        // Verify orb limits based on default settings
        // e.g. Sextile default orb is 6.
        if (aspect.aspect == "sextile") {
          expect(aspect.orbit, lessThanOrEqualTo(6.0001)); // epsilon
        }
      }
    });

    test('Dual Chart Aspects - Simple', () async {
      final subject1 = await AstrologicalSubjectFactory.createSubject(
        name: "S1",
        year: 2000,
        month: 1,
        day: 1,
        hour: 12,
        minute: 0,
        city: "A",
        nation: "GB",
        lng: 0,
        lat: 51,
        tzStr: "Europe/London",
      );
      // Subject 2 same time -> Exact conjunctions expected (orb 0)
      final subject2 = await AstrologicalSubjectFactory.createSubject(
        name: "S2",
        year: 2000,
        month: 1,
        day: 1,
        hour: 12,
        minute: 0,
        city: "B",
        nation: "GB",
        lng: 0,
        lat: 51,
        tzStr: "Europe/London",
      );

      final aspectsModel = AspectsFactory.dualChartAspects(subject1, subject2);

      // Should find conjunctions for every planet with orb ~0
      final sunConjunction = aspectsModel.aspects.firstWhere((a) => a.p1Name == "Sun" && a.p2Name == "Sun" && a.aspect == "conjunction");
      expect(sunConjunction.orbit, lessThan(0.001));

      // Check movement. p1 and p2 speeds are same?
      // If same subject time/loc, speeds are identical.
      // Movement should be Static?
      // Logic: relSpeed < epsilon -> Static.
      expect(sunConjunction.aspectMovement, AspectMovementType.Static);
    });
  });
}
