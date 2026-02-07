import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/models/astrological_subject.dart';
import 'package:kerykeion_dart/src/models/kerykeion_point.dart';
import 'package:kerykeion_dart/src/utilities.dart';

class CompositeSubjectFactory {
  /// Creates a composite chart (Midpoint method) from two subjects.
  /// The composite chart is represented as an [AstrologicalSubjectModel].
  ///
  /// The coordinates (lat/lng) are midpoints (though strictly not used for planetary calc in this method,
  /// as we average the positions directly).
  static AstrologicalSubjectModel createCompositeSubject({required AstrologicalSubjectModel subject1, required AstrologicalSubjectModel subject2}) {
    // 1. Base Metadata
    final name = "Composite (${subject1.name} & ${subject2.name})";
    final lat = (subject1.lat! + subject2.lat!) / 2;
    final lng = (subject1.lng! + subject2.lng!) / 2;

    // 2. Planets Calculation (Midpoints)
    final pointsMap = <AstrologicalPoint, KerykeionPointModel>{};

    // Map of points to process
    final s1Map = _getPointMap(subject1);
    final s2Map = _getPointMap(subject2);

    // Union of points
    final allPoints = {...s1Map.keys, ...s2Map.keys};

    for (var point in allPoints) {
      if (s1Map.containsKey(point) && s2Map.containsKey(point)) {
        final p1 = s1Map[point]!;
        final p2 = s2Map[point]!;

        final midpointDeg = getMidpoint(p1.absPos, p2.absPos);

        pointsMap[point] = getKerykeionPointFromDegree(
          midpointDeg,
          point.name, // Enum name
          PointType.AstrologicalPoint,
        );
      }
    }

    // 3. Houses Calculation
    // For Composite Houses, there are two main methods:
    // a) Midpoint of Cusps (Simple, commonly used with Midpoint method)
    // b) Calculate derived latitude/longitude and time, then re-calculate houses (Davison mostly, but sometimes applied to Composite)
    // Kerykeion Python (v2.1.18) seems to use midpoints of planets.
    // For houses, let's verify Python implementation behavior or standard practice.
    // Usually "Midpoint Composite" uses midpoints of cusps as well.

    final housesMap = <House, KerykeionPointModel>{};
    final houseS1 = _getHouseMap(subject1);
    final houseS2 = _getHouseMap(subject2);

    for (var house in House.values) {
      final h1 = houseS1[house]!;
      final h2 = houseS2[house]!;

      final midpointDeg = getMidpoint(h1.absPos, h2.absPos);

      housesMap[house] = getKerykeionPointFromDegree(midpointDeg, house.toString().split('.').last, PointType.House);
    }

    // 4. Construct Axes (Midpoints)
    KerykeionPointModel? asc, mc, dsc, ic;

    if (subject1.ascendant != null && subject2.ascendant != null) {
      asc = getKerykeionPointFromDegree(getMidpoint(subject1.ascendant!.absPos, subject2.ascendant!.absPos), "Ascendant", PointType.AstrologicalPoint);
    }

    if (subject1.mediumCoeli != null && subject2.mediumCoeli != null) {
      mc = getKerykeionPointFromDegree(getMidpoint(subject1.mediumCoeli!.absPos, subject2.mediumCoeli!.absPos), "Medium_Coeli", PointType.AstrologicalPoint);
    }

    // Derived descending/IC
    if (asc != null) {
      dsc = getKerykeionPointFromDegree((asc.absPos + 180) % 360, "Descendant", PointType.AstrologicalPoint);
    }

    if (mc != null) {
      ic = getKerykeionPointFromDegree((mc.absPos + 180) % 360, "Imum_Coeli", PointType.AstrologicalPoint);
    }

    // 5. Lunar Phase (Derived from composite Sun/Moon)
    final sun = pointsMap[AstrologicalPoint.Sun];
    final moon = pointsMap[AstrologicalPoint.Moon];
    final lunarPhase = (sun != null && moon != null) ? calculateMoonPhase(moon.absPos, sun.absPos) : null;

    return AstrologicalSubjectModel(
      name: name,
      lat: lat,
      lng: lng,
      city: "Composite",
      nation: "Composite",
      tzStr: "UTC", // Not relevant for composite
      housesSystemIdentifier: subject1.housesSystemIdentifier, // Inherit
      perspectiveType: subject1.perspectiveType, // Inherit
      housesNamesList: House.values,
      activePoints: pointsMap.keys.toList(),

      // Planets
      sun: pointsMap[AstrologicalPoint.Sun],
      moon: pointsMap[AstrologicalPoint.Moon],
      mercury: pointsMap[AstrologicalPoint.Mercury],
      venus: pointsMap[AstrologicalPoint.Venus],
      mars: pointsMap[AstrologicalPoint.Mars],
      jupiter: pointsMap[AstrologicalPoint.Jupiter],
      saturn: pointsMap[AstrologicalPoint.Saturn],
      uranus: pointsMap[AstrologicalPoint.Uranus],
      neptune: pointsMap[AstrologicalPoint.Neptune],
      pluto: pointsMap[AstrologicalPoint.Pluto],

      // Nodes
      meanNorthLunarNode: pointsMap[AstrologicalPoint.Mean_North_Lunar_Node],
      trueNorthLunarNode: pointsMap[AstrologicalPoint.True_North_Lunar_Node],
      meanSouthLunarNode: pointsMap[AstrologicalPoint.Mean_South_Lunar_Node],
      trueSouthLunarNode: pointsMap[AstrologicalPoint.True_South_Lunar_Node],

      // Other
      chiron: pointsMap[AstrologicalPoint.Chiron],
      meanLilith: pointsMap[AstrologicalPoint.Mean_Lilith],
      trueLilith: pointsMap[AstrologicalPoint.True_Lilith],

      // Axes
      ascendant: asc,
      descendant: dsc,
      mediumCoeli: mc,
      imumCoeli: ic,

      // Houses
      firstHouse: housesMap[House.First_House]!,
      secondHouse: housesMap[House.Second_House]!,
      thirdHouse: housesMap[House.Third_House]!,
      fourthHouse: housesMap[House.Fourth_House]!,
      fifthHouse: housesMap[House.Fifth_House]!,
      sixthHouse: housesMap[House.Sixth_House]!,
      seventhHouse: housesMap[House.Seventh_House]!,
      eighthHouse: housesMap[House.Eighth_House]!,
      ninthHouse: housesMap[House.Ninth_House]!,
      tenthHouse: housesMap[House.Tenth_House]!,
      eleventhHouse: housesMap[House.Eleventh_House]!,
      twelfthHouse: housesMap[House.Twelfth_House]!,

      lunarPhase: lunarPhase,

      // Just filling required fields with dummy data
      year: 0,
      month: 1,
      day: 1,
      hour: 0,
      minute: 0,
    );
  }

  static Map<AstrologicalPoint, KerykeionPointModel> _getPointMap(AstrologicalSubjectModel subject) {
    final map = <AstrologicalPoint, KerykeionPointModel?>{
      AstrologicalPoint.Sun: subject.sun,
      AstrologicalPoint.Moon: subject.moon,
      AstrologicalPoint.Mercury: subject.mercury,
      AstrologicalPoint.Venus: subject.venus,
      AstrologicalPoint.Mars: subject.mars,
      AstrologicalPoint.Jupiter: subject.jupiter,
      AstrologicalPoint.Saturn: subject.saturn,
      AstrologicalPoint.Uranus: subject.uranus,
      AstrologicalPoint.Neptune: subject.neptune,
      AstrologicalPoint.Pluto: subject.pluto,
      AstrologicalPoint.Mean_North_Lunar_Node: subject.meanNorthLunarNode,
      AstrologicalPoint.True_North_Lunar_Node: subject.trueNorthLunarNode,
      AstrologicalPoint.Mean_South_Lunar_Node: subject.meanSouthLunarNode,
      AstrologicalPoint.True_South_Lunar_Node: subject.trueSouthLunarNode,
      AstrologicalPoint.Chiron: subject.chiron,
      AstrologicalPoint.Mean_Lilith: subject.meanLilith,
      AstrologicalPoint.True_Lilith: subject.trueLilith,
    };
    // remove null values
    return Map.fromEntries(map.entries.where((e) => e.value != null).map((e) => MapEntry(e.key, e.value!)));
  }

  static Map<House, KerykeionPointModel> _getHouseMap(AstrologicalSubjectModel subject) {
    return {
      House.First_House: subject.firstHouse,
      House.Second_House: subject.secondHouse,
      House.Third_House: subject.thirdHouse,
      House.Fourth_House: subject.fourthHouse,
      House.Fifth_House: subject.fifthHouse,
      House.Sixth_House: subject.sixthHouse,
      House.Seventh_House: subject.seventhHouse,
      House.Eighth_House: subject.eighthHouse,
      House.Ninth_House: subject.ninthHouse,
      House.Tenth_House: subject.tenthHouse,
      House.Eleventh_House: subject.eleventhHouse,
      House.Twelfth_House: subject.twelfthHouse,
    };
  }
}
