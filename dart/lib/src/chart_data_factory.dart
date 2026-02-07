import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/models/astrological_subject.dart';
import 'package:kerykeion_dart/src/models/chart_data.dart';
import 'package:kerykeion_dart/src/models/distribution.dart';
import 'package:kerykeion_dart/src/models/house_comparison.dart';
import 'package:kerykeion_dart/src/models/aspect_model.dart';
import 'package:kerykeion_dart/src/models/kerykeion_point.dart';

import 'package:kerykeion_dart/src/aspects/aspects_factory.dart';
import 'package:kerykeion_dart/src/utilities.dart';
import 'package:kerykeion_dart/src/settings/chart_defaults.dart';
import 'package:kerykeion_dart/src/composite_factory.dart';

class ChartDataFactory {
  /// Creates a [ChartDataModel] which can be either [SingleChartDataModel] or [DualChartDataModel].
  static ChartDataModel createChartData(
    ChartType chartType,
    AstrologicalSubjectModel firstSubject, {
    AstrologicalSubjectModel? secondSubject,
    List<AstrologicalPoint>? activePoints,
    List<ActiveAspect>? activeAspects,
    bool includeHouseComparison = true,
    double? axisOrbLimit,
  }) {
    final activePointsResolved = activePoints ?? firstSubject.activePoints;
    final activeAspectsResolved = activeAspects ?? defaultActiveAspects;

    // Handle Composite Chart
    AstrologicalSubjectModel? effectiveSubject = firstSubject;

    if (chartType == ChartType.Composite && secondSubject != null) {
      effectiveSubject = CompositeSubjectFactory.createCompositeSubject(subject1: firstSubject, subject2: secondSubject);
    }

    // Calculate Aspects
    List<AspectModel> aspects = [];
    if (chartType == ChartType.Natal || chartType == ChartType.Composite || chartType == ChartType.SingleReturnChart) {
      final aspectsModel = AspectsFactory.singleChartAspects(
        effectiveSubject,
        activePoints: activePointsResolved,
        activeAspects: activeAspectsResolved,
        axisOrbLimit: axisOrbLimit,
      );
      aspects = aspectsModel.aspects;
    } else if (secondSubject != null) {
      if (chartType == ChartType.Synastry || chartType == ChartType.Transits) {
        final aspectsModel = AspectsFactory.dualChartAspects(
          firstSubject,
          secondSubject,
          activePoints: activePointsResolved,
          activeAspects: activeAspectsResolved,
          axisOrbLimit: axisOrbLimit,
          firstSubjectIsFixed: chartType == ChartType.Transits,
        );
        aspects = aspectsModel.aspects;
      }
    }

    // Calculate Distributions
    final elementDistribution = _calculateElementDistribution(effectiveSubject, activePointsResolved);
    final qualityDistribution = _calculateQualityDistribution(effectiveSubject, activePointsResolved);

    if (chartType == ChartType.Natal || chartType == ChartType.Composite || chartType == ChartType.SingleReturnChart) {
      return SingleChartDataModel(
        chartType: chartType.name,
        subject: effectiveSubject,
        aspects: aspects,
        elementDistribution: elementDistribution,
        qualityDistribution: qualityDistribution,
        activePoints: activePointsResolved,
      );
    } else {
      if (secondSubject == null) {
        throw Exception("Second subject is required for Dual Chart types.");
      }

      HouseComparisonModel? houseComparison;
      if (includeHouseComparison) {
        if (chartType == ChartType.Synastry || chartType == ChartType.Transits) {
          houseComparison = _calculateHouseComparison(firstSubject, secondSubject, activePointsResolved);
        }
      }

      return DualChartDataModel(
        chartType: chartType.name,
        firstSubject: firstSubject,
        secondSubject: secondSubject,
        aspects: aspects,
        elementDistribution: elementDistribution,
        qualityDistribution: qualityDistribution,
        activePoints: activePointsResolved,
        houseComparison: houseComparison,
      );
    }
  }

  // =========================================================================
  // Weighted point configuration — matches Python kerykeion's
  // DEFAULT_WEIGHTED_POINT_WEIGHTS in charts/charts_utils.py
  // =========================================================================
  static const Map<AstrologicalPoint, double> _defaultWeights = {
    // Core luminaries & angles
    AstrologicalPoint.Sun: 2.0,
    AstrologicalPoint.Moon: 2.0,
    AstrologicalPoint.Ascendant: 2.0,
    AstrologicalPoint.Medium_Coeli: 1.5,
    AstrologicalPoint.Descendant: 1.5,
    AstrologicalPoint.Imum_Coeli: 1.5,
    // Personal planets
    AstrologicalPoint.Mercury: 1.5,
    AstrologicalPoint.Venus: 1.5,
    AstrologicalPoint.Mars: 1.5,
    // Social planets
    AstrologicalPoint.Jupiter: 1.0,
    AstrologicalPoint.Saturn: 1.0,
    // Outer / transpersonal
    AstrologicalPoint.Uranus: 0.5,
    AstrologicalPoint.Neptune: 0.5,
    AstrologicalPoint.Pluto: 0.5,
    // Lunar nodes
    AstrologicalPoint.Mean_North_Lunar_Node: 0.5,
    AstrologicalPoint.True_North_Lunar_Node: 0.5,
    AstrologicalPoint.Mean_South_Lunar_Node: 0.5,
    AstrologicalPoint.True_South_Lunar_Node: 0.5,
    // Chiron & Lilith
    AstrologicalPoint.Chiron: 0.6,
    AstrologicalPoint.Mean_Lilith: 0.5,
    AstrologicalPoint.True_Lilith: 0.5,
  };

  /// Fallback weight for any point not in [_defaultWeights].
  static const double _fallbackWeight = 1.0;

  /// Largest-remainder method so percentages always sum to exactly 100.
  /// Matches Python kerykeion's `distribute_percentages_to_100`.
  static Map<String, int> _distributePercentagesTo100(Map<String, double> values) {
    final total = values.values.fold(0.0, (a, b) => a + b);
    if (total == 0) return {for (var k in values.keys) k: 0};

    final percentages = {for (var e in values.entries) e.key: e.value * 100.0 / total};
    final intParts = {for (var e in percentages.entries) e.key: e.value.floor()};
    final remainders = {for (var e in percentages.entries) e.key: e.value - intParts[e.key]!};

    final currentSum = intParts.values.fold(0, (a, b) => a + b);
    final needed = 100 - currentSum;

    final sorted = remainders.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    final result = Map<String, int>.from(intParts);
    for (var i = 0; i < needed && i < sorted.length; i++) {
      result[sorted[i].key] = result[sorted[i].key]! + 1;
    }
    return result;
  }

  static ElementDistributionModel _calculateElementDistribution(AstrologicalSubjectModel subject, List<AstrologicalPoint> activePoints) {
    double fire = 0;
    double earth = 0;
    double air = 0;
    double water = 0;

    final map = {
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
      AstrologicalPoint.Chiron: subject.chiron,
      AstrologicalPoint.Mean_North_Lunar_Node: subject.meanNorthLunarNode,
      AstrologicalPoint.True_North_Lunar_Node: subject.trueNorthLunarNode,
      AstrologicalPoint.Mean_South_Lunar_Node: subject.meanSouthLunarNode,
      AstrologicalPoint.True_South_Lunar_Node: subject.trueSouthLunarNode,
      AstrologicalPoint.Mean_Lilith: subject.meanLilith,
      AstrologicalPoint.True_Lilith: subject.trueLilith,
      AstrologicalPoint.Ascendant: subject.ascendant,
      AstrologicalPoint.Medium_Coeli: subject.mediumCoeli,
      AstrologicalPoint.Descendant: subject.descendant,
      AstrologicalPoint.Imum_Coeli: subject.imumCoeli,
    };

    for (var entry in map.entries) {
      if (!activePoints.contains(entry.key)) continue;
      final point = entry.value;
      if (point == null) continue;
      final weight = _defaultWeights[entry.key] ?? _fallbackWeight;
      switch (point.element) {
        case Element.Fire:
          fire += weight;
          break;
        case Element.Earth:
          earth += weight;
          break;
        case Element.Air:
          air += weight;
          break;
        case Element.Water:
          water += weight;
          break;
      }
    }

    // Determine dominant
    Element? dominant;
    double max = 0;
    if (fire > max) {
      max = fire;
      dominant = Element.Fire;
    }
    if (earth > max) {
      max = earth;
      dominant = Element.Earth;
    }
    if (air > max) {
      max = air;
      dominant = Element.Air;
    }
    if (water > max) {
      max = water;
      dominant = Element.Water;
    }

    // Largest-remainder percentages (sum = 100)
    final pct = _distributePercentagesTo100({'fire': fire, 'earth': earth, 'air': air, 'water': water});

    return ElementDistributionModel(
      fire: fire,
      earth: earth,
      air: air,
      water: water,
      firePercentage: pct['fire']!,
      earthPercentage: pct['earth']!,
      airPercentage: pct['air']!,
      waterPercentage: pct['water']!,
      dominant: dominant,
    );
  }

  static QualityDistributionModel _calculateQualityDistribution(AstrologicalSubjectModel subject, List<AstrologicalPoint> activePoints) {
    double cardinal = 0;
    double fixed = 0;
    double mutable = 0;

    final map = {
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
      AstrologicalPoint.Chiron: subject.chiron,
      AstrologicalPoint.Mean_North_Lunar_Node: subject.meanNorthLunarNode,
      AstrologicalPoint.True_North_Lunar_Node: subject.trueNorthLunarNode,
      AstrologicalPoint.Mean_South_Lunar_Node: subject.meanSouthLunarNode,
      AstrologicalPoint.True_South_Lunar_Node: subject.trueSouthLunarNode,
      AstrologicalPoint.Mean_Lilith: subject.meanLilith,
      AstrologicalPoint.True_Lilith: subject.trueLilith,
      AstrologicalPoint.Ascendant: subject.ascendant,
      AstrologicalPoint.Medium_Coeli: subject.mediumCoeli,
      AstrologicalPoint.Descendant: subject.descendant,
      AstrologicalPoint.Imum_Coeli: subject.imumCoeli,
    };

    for (var entry in map.entries) {
      if (!activePoints.contains(entry.key)) continue;
      final point = entry.value;
      if (point == null) continue;
      final weight = _defaultWeights[entry.key] ?? _fallbackWeight;
      switch (point.quality) {
        case Quality.Cardinal:
          cardinal += weight;
          break;
        case Quality.Fixed:
          fixed += weight;
          break;
        case Quality.Mutable:
          mutable += weight;
          break;
      }
    }

    // Determine dominant
    Quality? dominant;
    double max = 0;
    if (cardinal > max) {
      max = cardinal;
      dominant = Quality.Cardinal;
    }
    if (fixed > max) {
      max = fixed;
      dominant = Quality.Fixed;
    }
    if (mutable > max) {
      max = mutable;
      dominant = Quality.Mutable;
    }

    // Largest-remainder percentages (sum = 100)
    final pct = _distributePercentagesTo100({'cardinal': cardinal, 'fixed': fixed, 'mutable': mutable});

    return QualityDistributionModel(
      cardinal: cardinal,
      fixed: fixed,
      mutable: mutable,
      cardinalPercentage: pct['cardinal']!,
      fixedPercentage: pct['fixed']!,
      mutablePercentage: pct['mutable']!,
      dominant: dominant,
    );
  }

  static HouseComparisonModel _calculateHouseComparison(
    AstrologicalSubjectModel subjectA,
    AstrologicalSubjectModel subjectB,
    List<AstrologicalPoint> activePoints,
  ) {
    // A in B
    final List<PointInHouseModel> aInB = [];

    final housesDegreeUtListB = [
      subjectB.firstHouse.absPos,
      subjectB.secondHouse.absPos,
      subjectB.thirdHouse.absPos,
      subjectB.fourthHouse.absPos,
      subjectB.fifthHouse.absPos,
      subjectB.sixthHouse.absPos,
      subjectB.seventhHouse.absPos,
      subjectB.eighthHouse.absPos,
      subjectB.ninthHouse.absPos,
      subjectB.tenthHouse.absPos,
      subjectB.eleventhHouse.absPos,
      subjectB.twelfthHouse.absPos,
    ];

    final mapDefault = {
      AstrologicalPoint.Sun: subjectA.sun,
      AstrologicalPoint.Moon: subjectA.moon,
      AstrologicalPoint.Mercury: subjectA.mercury,
      AstrologicalPoint.Venus: subjectA.venus,
      AstrologicalPoint.Mars: subjectA.mars,
      AstrologicalPoint.Jupiter: subjectA.jupiter,
      AstrologicalPoint.Saturn: subjectA.saturn,
      AstrologicalPoint.Uranus: subjectA.uranus,
      AstrologicalPoint.Neptune: subjectA.neptune,
      AstrologicalPoint.Pluto: subjectA.pluto,
    };

    for (var pointId in activePoints) {
      KerykeionPointModel? planet;
      if (mapDefault.containsKey(pointId)) {
        planet = mapDefault[pointId];
      }

      if (planet != null) {
        final house = getPlanetHouse(planet.absPos, housesDegreeUtListB);
        final houseNum = getHouseNumber(house.toString().split('.').last);
        final houseNameStr = getHouseName(houseNum);

        aInB.add(
          PointInHouseModel(
            pointName: planet.name,
            pointDegree: planet.absPos,
            pointSign: planet.sign.name,
            pointOwnerName: subjectA.name,
            projectedHouseNumber: houseNum,
            projectedHouseName: houseNameStr,
            projectedHouseOwnerName: subjectB.name,
          ),
        );
      }
    }

    // B in A
    final List<PointInHouseModel> bInA = [];
    final housesDegreeUtListA = [
      subjectA.firstHouse.absPos,
      subjectA.secondHouse.absPos,
      subjectA.thirdHouse.absPos,
      subjectA.fourthHouse.absPos,
      subjectA.fifthHouse.absPos,
      subjectA.sixthHouse.absPos,
      subjectA.seventhHouse.absPos,
      subjectA.eighthHouse.absPos,
      subjectA.ninthHouse.absPos,
      subjectA.tenthHouse.absPos,
      subjectA.eleventhHouse.absPos,
      subjectA.twelfthHouse.absPos,
    ];

    final mapDefaultB = {
      AstrologicalPoint.Sun: subjectB.sun,
      AstrologicalPoint.Moon: subjectB.moon,
      AstrologicalPoint.Mercury: subjectB.mercury,
      AstrologicalPoint.Venus: subjectB.venus,
      AstrologicalPoint.Mars: subjectB.mars,
      AstrologicalPoint.Jupiter: subjectB.jupiter,
      AstrologicalPoint.Saturn: subjectB.saturn,
      AstrologicalPoint.Uranus: subjectB.uranus,
      AstrologicalPoint.Neptune: subjectB.neptune,
      AstrologicalPoint.Pluto: subjectB.pluto,
    };

    for (var pointId in activePoints) {
      KerykeionPointModel? planet;
      if (mapDefaultB.containsKey(pointId)) {
        planet = mapDefaultB[pointId];
      }
      if (planet != null) {
        final house = getPlanetHouse(planet.absPos, housesDegreeUtListA);
        final houseNum = getHouseNumber(house.toString().split('.').last);
        final houseNameStr = getHouseName(houseNum);

        bInA.add(
          PointInHouseModel(
            pointName: planet.name,
            pointDegree: planet.absPos,
            pointSign: planet.sign.name,
            pointOwnerName: subjectB.name,
            projectedHouseNumber: houseNum,
            projectedHouseName: houseNameStr,
            projectedHouseOwnerName: subjectA.name,
          ),
        );
      }
    }

    return HouseComparisonModel(
      firstSubjectName: subjectA.name,
      secondSubjectName: subjectB.name,
      firstPointsInSecondHouses: aInB,
      secondPointsInFirstHouses: bInA,
    );
  }
}
