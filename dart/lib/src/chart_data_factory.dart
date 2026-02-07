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

  static ElementDistributionModel _calculateElementDistribution(AstrologicalSubjectModel subject, List<AstrologicalPoint> activePoints) {
    int fire = 0;
    int earth = 0;
    int air = 0;
    int water = 0;
    int total = 0;

    void processPoint(KerykeionPointModel? point) {
      if (point != null) {
        if (point.element == Element.Fire) fire++;
        if (point.element == Element.Earth) earth++;
        if (point.element == Element.Air) air++;
        if (point.element == Element.Water) water++;
        total++;
      }
    }

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
      AstrologicalPoint.Ascendant: subject.ascendant,
      AstrologicalPoint.Medium_Coeli: subject.mediumCoeli,
    };

    for (var entry in map.entries) {
      if (activePoints.contains(entry.key)) {
        processPoint(entry.value);
      }
    }

    Element? dominant;
    int max = 0;
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

    // Calculate percentages
    int totalPoints = total == 0 ? 1 : total; // Avoid division by zero
    int firePercentage = ((fire / totalPoints) * 100).round();
    int earthPercentage = ((earth / totalPoints) * 100).round();
    int airPercentage = ((air / totalPoints) * 100).round();
    int waterPercentage = ((water / totalPoints) * 100).round();

    return ElementDistributionModel(
      fire: fire.toDouble(),
      earth: earth.toDouble(),
      air: air.toDouble(),
      water: water.toDouble(),
      firePercentage: firePercentage,
      earthPercentage: earthPercentage,
      airPercentage: airPercentage,
      waterPercentage: waterPercentage,
      dominant: dominant,
    );
  }

  static QualityDistributionModel _calculateQualityDistribution(AstrologicalSubjectModel subject, List<AstrologicalPoint> activePoints) {
    int cardinal = 0;
    int fixed = 0;
    int mutable = 0;
    int total = 0;

    void processPoint(KerykeionPointModel? point) {
      if (point != null) {
        if (point.quality == Quality.Cardinal) cardinal++;
        if (point.quality == Quality.Fixed) fixed++;
        if (point.quality == Quality.Mutable) mutable++;
        total++;
      }
    }

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
      AstrologicalPoint.Ascendant: subject.ascendant,
      AstrologicalPoint.Medium_Coeli: subject.mediumCoeli,
    };

    for (var entry in map.entries) {
      if (activePoints.contains(entry.key)) {
        processPoint(entry.value);
      }
    }

    Quality? dominant;
    int max = 0;
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

    int totalPoints = total == 0 ? 1 : total;
    int cardinalPercentage = ((cardinal / totalPoints) * 100).round();
    int fixedPercentage = ((fixed / totalPoints) * 100).round();
    int mutablePercentage = ((mutable / totalPoints) * 100).round();

    return QualityDistributionModel(
      cardinal: cardinal.toDouble(),
      fixed: fixed.toDouble(),
      mutable: mutable.toDouble(),
      cardinalPercentage: cardinalPercentage,
      fixedPercentage: fixedPercentage,
      mutablePercentage: mutablePercentage,
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
