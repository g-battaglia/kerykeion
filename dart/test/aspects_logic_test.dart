import 'package:kerykeion_dart/kerykeion_dart.dart';
import 'package:test/test.dart';

void main() {
  group('Aspect Logic Tests (No Sweph)', () {
    test('calculateAspectMovement Logic', () {
      // P1 at 10, speed 1. P2 at 20, speed 0.5.
      // Aspect 0 (Conj). Orb = 10.
      // Next day: P1=11, P2=20.5. Orb=9.5 (Applying)
      expect(AspectsUtils.calculateAspectMovement(10, 20, 0, 1, 0.5), AspectMovementType.Applying);

      // P1 at 20, speed 1. P2 at 10, speed 0.5.
      // Aspect 0 (Conj). Orb = 10.
      // Next day: P1=21, P2=10.5. Orb=10.5 (Separating)
      expect(AspectsUtils.calculateAspectMovement(20, 10, 0, 1, 0.5), AspectMovementType.Separating);
    });

    test('Single Chart Aspects - Mock Data', () {
      // Create disjoint points (Sun at 0, Moon at 60) -> Sextile
      final sun = KerykeionPointModel(
        name: "Sun",
        pointType: PointType.AstrologicalPoint,
        quality: Quality.Cardinal,
        element: Element.Fire,
        sign: Sign.Ari,
        signNum: 0,
        position: 0,
        absPos: 0,
        emoji: "S",
        speed: 1.0,
      );
      final moon = KerykeionPointModel(
        name: "Moon",
        pointType: PointType.AstrologicalPoint,
        quality: Quality.Mutable,
        element: Element.Air,
        sign: Sign.Gem,
        signNum: 2,
        position: 0,
        absPos: 60,
        emoji: "M",
        speed: 13.0,
      );

      // Minimal subject
      final subject = AstrologicalSubjectModel(
        name: "MockSub",
        housesSystemIdentifier: HousesSystemIdentifier.P,
        perspectiveType: PerspectiveType.Apparent_Geocentric,
        sun: sun,
        moon: moon,
        // Mock required houses with dummy data
        firstHouse: _dummyPoint("H1"),
        secondHouse: _dummyPoint("H2"),
        thirdHouse: _dummyPoint("H3"),
        fourthHouse: _dummyPoint("H4"),
        fifthHouse: _dummyPoint("H5"),
        sixthHouse: _dummyPoint("H6"),
        seventhHouse: _dummyPoint("H7"),
        eighthHouse: _dummyPoint("H8"),
        ninthHouse: _dummyPoint("H9"),
        tenthHouse: _dummyPoint("H10"),
        eleventhHouse: _dummyPoint("H11"),
        twelfthHouse: _dummyPoint("H12"),
        housesNamesList: const <House>[],
        activePoints: const [AstrologicalPoint.Sun, AstrologicalPoint.Moon],
      );

      final result = AspectsFactory.singleChartAspects(subject);

      expect(result.aspects, isNotEmpty);
      final aspect = result.aspects.first;
      print("Found aspect: ${aspect.p1Name}-${aspect.p2Name} ${aspect.aspect}");

      expect(aspect.p1Name, anyOf("Sun", "Moon"));
      expect(aspect.p2Name, anyOf("Sun", "Moon"));
      expect(aspect.aspect, "sextile");
      expect(aspect.orbit, 0.0);
    });

    test('Dual Chart Aspects - Mock Data', () {
      // Subject 1: Sun at 0
      final s1 = _createMockSubject("S1", 0);
      // Subject 2: Sun at 180 (Opposition)
      final s2 = _createMockSubject("S2", 180);

      final result = AspectsFactory.dualChartAspects(s1, s2);

      final opposition = result.aspects.firstWhere((a) => a.p1Name == "Sun" && a.p2Name == "Sun" && a.aspect == "opposition");
      expect(opposition, isNotNull);
      expect(opposition.orbit, 0.0);
    });
  });
}

KerykeionPointModel _dummyPoint(String name) {
  return KerykeionPointModel(
    name: name,
    pointType: PointType.House,
    quality: Quality.Cardinal,
    element: Element.Fire,
    sign: Sign.Ari,
    signNum: 0,
    position: 0,
    absPos: 0,
    emoji: "",
  );
}

AstrologicalSubjectModel _createMockSubject(String name, double sunPos) {
  final sun = KerykeionPointModel(
    name: "Sun",
    pointType: PointType.AstrologicalPoint,
    quality: Quality.Cardinal,
    element: Element.Fire,
    sign: Sign.Ari,
    signNum: 0,
    position: 0,
    absPos: sunPos,
    emoji: "S",
    speed: 1.0,
  );

  return AstrologicalSubjectModel(
    name: name,
    housesSystemIdentifier: HousesSystemIdentifier.P,
    perspectiveType: PerspectiveType.Apparent_Geocentric,
    sun: sun,
    firstHouse: _dummyPoint("H1"),
    secondHouse: _dummyPoint("H2"),
    thirdHouse: _dummyPoint("H3"),
    fourthHouse: _dummyPoint("H4"),
    fifthHouse: _dummyPoint("H5"),
    sixthHouse: _dummyPoint("H6"),
    seventhHouse: _dummyPoint("H7"),
    eighthHouse: _dummyPoint("H8"),
    ninthHouse: _dummyPoint("H9"),
    tenthHouse: _dummyPoint("H10"),
    eleventhHouse: _dummyPoint("H11"),
    twelfthHouse: _dummyPoint("H12"),
    housesNamesList: [],
    activePoints: [AstrologicalPoint.Sun],
  );
}
