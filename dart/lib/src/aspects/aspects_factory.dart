import 'package:kerykeion_dart/src/models/astrological_subject.dart';
import 'package:kerykeion_dart/src/models/aspect_model.dart';
import 'package:kerykeion_dart/src/models/chart_aspects.dart';

import 'package:kerykeion_dart/src/settings/chart_defaults.dart';
import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/aspects/aspects_utils.dart';

// Axes constants for orb filtering
const List<String> axesList = ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"];

class AspectsFactory {
  /// Create aspects analysis for a single astrological chart.
  static SingleChartAspectsModel singleChartAspects(
    AstrologicalSubjectModel subject, {
    List<AstrologicalPoint>? activePoints,
    List<ActiveAspect>? activeAspects,
    double? axisOrbLimit,
  }) {
    // Initialize settings
    // In Dart we use constants directly, avoiding copy if strict immutability isn't required.
    // But _updateAspectSettings returns new list anyway.

    final activeAspectsResolved = activeAspects ?? defaultActiveAspects;

    // Determine active points
    List<AstrologicalPoint> activePointsResolved;
    if (activePoints == null) {
      activePointsResolved = subject.activePoints;
    } else {
      // Intersection of subject's active points and requested active points
      activePointsResolved = subject.activePoints.where((p) => activePoints.contains(p)).toList();
    }

    final allAspects = _calculateSingleChartAspects(subject, activePointsResolved, activeAspectsResolved, defaultChartAspectsSettings);

    final filteredAspects = _filterRelevantAspects(allAspects, axisOrbLimit: axisOrbLimit, applyAxisOrbFilter: axisOrbLimit != null);

    return SingleChartAspectsModel(subject: subject, aspects: filteredAspects, activePoints: activePointsResolved, activeAspects: activeAspectsResolved);
  }

  /// Create aspects analysis between two astrological charts.
  static DualChartAspectsModel dualChartAspects(
    AstrologicalSubjectModel firstSubject,
    AstrologicalSubjectModel secondSubject, {
    List<AstrologicalPoint>? activePoints,
    List<ActiveAspect>? activeAspects,
    double? axisOrbLimit,
    bool firstSubjectIsFixed = false,
    bool secondSubjectIsFixed = false,
  }) {
    final activeAspectsResolved = activeAspects ?? defaultActiveAspects;

    List<AstrologicalPoint> activePointsResolved;
    if (activePoints == null) {
      activePointsResolved = firstSubject.activePoints;
    } else {
      activePointsResolved = firstSubject.activePoints.where((p) => activePoints.contains(p)).toList();
    }

    // Further filter with second subject's active points
    activePointsResolved = secondSubject.activePoints.where((p) => activePointsResolved.contains(p)).toList();

    final allAspects = _calculateDualChartAspects(
      firstSubject,
      secondSubject,
      activePointsResolved,
      activeAspectsResolved,
      defaultChartAspectsSettings,
      firstSubjectIsFixed: firstSubjectIsFixed,
      secondSubjectIsFixed: secondSubjectIsFixed,
    );

    final filteredAspects = _filterRelevantAspects(allAspects, axisOrbLimit: axisOrbLimit, applyAxisOrbFilter: false);

    return DualChartAspectsModel(
      firstSubject: firstSubject,
      secondSubject: secondSubject,
      aspects: filteredAspects,
      activePoints: activePointsResolved,
      activeAspects: activeAspectsResolved,
    );
  }

  static List<AspectModel> _calculateSingleChartAspects(
    AstrologicalSubjectModel subject,
    List<AstrologicalPoint> activePoints,
    List<ActiveAspect> activeAspects,
    List<ChartAspectSetting> aspectsSettings,
  ) {
    final activePointsList = AspectsUtils.getActivePointsList(subject, activePoints);
    final filteredSettings = _updateAspectSettings(aspectsSettings, activeAspects);

    // Define opposite pairs to skip
    const oppositePairs = {
      "Ascendant": "Descendant",
      "Descendant": "Ascendant",
      "Medium_Coeli": "Imum_Coeli",
      "Imum_Coeli": "Medium_Coeli",
      "True_North_Lunar_Node": "True_South_Lunar_Node",
      "Mean_North_Lunar_Node": "Mean_South_Lunar_Node",
      "True_South_Lunar_Node": "True_North_Lunar_Node",
      "Mean_South_Lunar_Node": "Mean_North_Lunar_Node",
    };

    final List<AspectModel> allAspectsList = [];

    for (int i = 0; i < activePointsList.length; i++) {
      for (int j = i + 1; j < activePointsList.length; j++) {
        final p1 = activePointsList[i];
        final p2 = activePointsList[j];

        if (oppositePairs[p1.name] == p2.name) continue;

        final aspectResult = AspectsUtils.getAspectFromTwoPoints(filteredSettings, p1.absPos, p2.absPos);

        if (aspectResult["verdict"] == true) {
          final p1Speed = p1.speed ?? 0.0;
          final p2Speed = p2.speed ?? 0.0;

          AspectMovementType aspectMovement;
          if (axesList.contains(p1.name) && axesList.contains(p2.name)) {
            aspectMovement = AspectMovementType.Static;
          } else {
            aspectMovement = AspectsUtils.calculateAspectMovement(p1.absPos, p2.absPos, aspectResult["aspect_degrees"], p1Speed, p2Speed);
          }

          allAspectsList.add(
            AspectModel(
              p1Name: p1.name,
              p1Owner: subject.name,
              p1AbsPos: p1.absPos,
              p2Name: p2.name,
              p2Owner: subject.name,
              p2AbsPos: p2.absPos,
              aspect: aspectResult["name"],
              orbit: aspectResult["orbit"],
              aspectDegrees: (aspectResult["aspect_degrees"] as num).toInt(),
              diff: aspectResult["diff"],
              p1: AspectsUtils.getPlanetId(p1.name),
              p2: AspectsUtils.getPlanetId(p2.name),
              p1Speed: p1Speed,
              p2Speed: p2Speed,
              aspectMovement: aspectMovement,
            ),
          );
        }
      }
    }

    return allAspectsList;
  }

  static List<AspectModel> _calculateDualChartAspects(
    AstrologicalSubjectModel firstSubject,
    AstrologicalSubjectModel secondSubject,
    List<AstrologicalPoint> activePoints,
    List<ActiveAspect> activeAspects,
    List<ChartAspectSetting> aspectsSettings, {
    required bool firstSubjectIsFixed,
    required bool secondSubjectIsFixed,
  }) {
    // Get points for both subjects filtering by the SAME activePoints list intersection
    // Python code calls `get_active_points_list` separately for each subject using the passed `active_points`.

    final firstActivePointsList = AspectsUtils.getActivePointsList(firstSubject, activePoints);
    final secondActivePointsList = AspectsUtils.getActivePointsList(secondSubject, activePoints);

    final filteredSettings = _updateAspectSettings(aspectsSettings, activeAspects);

    final List<AspectModel> allAspectsList = [];

    for (int i = 0; i < firstActivePointsList.length; i++) {
      for (int j = 0; j < secondActivePointsList.length; j++) {
        final p1 = firstActivePointsList[i];
        final p2 = secondActivePointsList[j];

        final aspectResult = AspectsUtils.getAspectFromTwoPoints(filteredSettings, p1.absPos, p2.absPos);

        if (aspectResult["verdict"] == true) {
          var p1Speed = p1.speed ?? 0.0;
          var p2Speed = p2.speed ?? 0.0;

          if (firstSubjectIsFixed) p1Speed = 0.0;
          if (secondSubjectIsFixed) p2Speed = 0.0;

          AspectMovementType aspectMovement;
          if (axesList.contains(p1.name) && axesList.contains(p2.name)) {
            aspectMovement = AspectMovementType.Static;
          } else {
            aspectMovement = AspectsUtils.calculateAspectMovement(p1.absPos, p2.absPos, aspectResult["aspect_degrees"], p1Speed, p2Speed);
          }

          allAspectsList.add(
            AspectModel(
              p1Name: p1.name,
              p1Owner: firstSubject.name,
              p1AbsPos: p1.absPos,
              p2Name: p2.name,
              p2Owner: secondSubject.name,
              p2AbsPos: p2.absPos,
              aspect: aspectResult["name"],
              orbit: aspectResult["orbit"],
              aspectDegrees: (aspectResult["aspect_degrees"] as num).toInt(),
              diff: aspectResult["diff"],
              p1: AspectsUtils.getPlanetId(p1.name),
              p2: AspectsUtils.getPlanetId(p2.name),
              p1Speed: p1Speed,
              p2Speed: p2Speed,
              aspectMovement: aspectMovement,
            ),
          );
        }
      }
    }

    return allAspectsList;
  }

  static List<ChartAspectSetting> _updateAspectSettings(List<ChartAspectSetting> aspectsSettings, List<ActiveAspect> activeAspects) {
    final List<ChartAspectSetting> result = [];

    for (var setting in aspectsSettings) {
      for (var active in activeAspects) {
        if (setting.name == active.name) {
          result.add(
            ChartAspectSetting(
              degree: setting.degree,
              name: setting.name,
              isMajor: setting.isMajor,
              color: setting.color,
              orb: active.orb, // Use active aspect's orb
            ),
          );
          break;
        }
      }
    }
    return result;
  }

  static List<AspectModel> _filterRelevantAspects(List<AspectModel> allAspects, {double? axisOrbLimit, required bool applyAxisOrbFilter}) {
    if (!applyAxisOrbFilter || axisOrbLimit == null) {
      return List.from(allAspects);
    }

    final List<AspectModel> relevantAspects = [];

    for (var aspect in allAspects) {
      final aspectInvolvesAxes = axesList.contains(aspect.p1Name) || axesList.contains(aspect.p2Name);

      if (aspectInvolvesAxes && aspect.orbit.abs() >= axisOrbLimit) {
        continue;
      }
      relevantAspects.add(aspect);
    }

    return relevantAspects;
  }

  // Legacy Aliases
  @Deprecated('Use singleChartAspects instead')
  static NatalAspectsModel natalAspects(
    AstrologicalSubjectModel subject, {
    List<AstrologicalPoint>? activePoints,
    List<ActiveAspect>? activeAspects,
    double? axisOrbLimit,
  }) {
    return singleChartAspects(subject, activePoints: activePoints, activeAspects: activeAspects, axisOrbLimit: axisOrbLimit);
  }

  @Deprecated('Use dualChartAspects instead')
  static SynastryAspectsModel synastryAspects(
    AstrologicalSubjectModel firstSubject,
    AstrologicalSubjectModel secondSubject, {
    List<AstrologicalPoint>? activePoints,
    List<ActiveAspect>? activeAspects,
    double? axisOrbLimit,
  }) {
    return dualChartAspects(firstSubject, secondSubject, activePoints: activePoints, activeAspects: activeAspects, axisOrbLimit: axisOrbLimit);
  }
}
