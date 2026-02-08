import 'dart:math' as math;
import 'charts_utils.dart';

/// Planet drawing module for astrological chart SVG rendering.
/// Ported from Python kerykeion draw_planets.py.

// =============================================================================
// CONSTANTS
// =============================================================================

const double planetGroupingThreshold = 3.4;
const double indicatorGroupingThreshold = 2.5;
const int chartAngleMinIndex = 22;
const int chartAngleMaxIndex = 27;
const int natalIndicatorOffset = 72;
const int dualChartAngleRadius = 76;
const int dualChartPlanetRadiusA = 110;
const int dualChartPlanetRadiusB = 130;
const List<String> dualChartTypes = ['Transit', 'Synastry', 'DualReturnChart'];

// =============================================================================
// MAIN FUNCTION
// =============================================================================

/// Draw celestial points on an astrological chart.
///
/// Handles position calculations, overlap prevention, and SVG generation.
String drawPlanets({
  required double radius,
  required List<Map<String, dynamic>> availableCelestialPoints,
  required List<Map<String, dynamic>> availablePlanetsSettings,
  required double thirdCircleRadius,
  required double firstHouseDegreeUt,
  required double seventhHouseDegreeUt,
  required String chartType,
  List<Map<String, dynamic>>? secondSubjectCelestialPoints,
  bool externalView = false,
  double? firstCircleRadius,
  double? secondCircleRadius,
  bool showDegreeIndicators = true,
}) {
  // Points to exclude from transit ring (house cusps)
  final transitRingExcludePoints = [
    'First_House',
    'Second_House',
    'Third_House',
    'Fourth_House',
    'Fifth_House',
    'Sixth_House',
    'Seventh_House',
    'Eighth_House',
    'Ninth_House',
    'Tenth_House',
    'Eleventh_House',
    'Twelfth_House',
  ];

  final sb = StringBuffer();

  // Extract positions
  final mainAbsPositions = availableCelestialPoints.map((p) => (p['abs_pos'] as num).toDouble()).toList();

  List<double> secondaryAbsPositions = [];
  List<double> secondaryRelPositions = [];
  if (dualChartTypes.contains(chartType) && secondSubjectCelestialPoints != null) {
    secondaryAbsPositions = secondSubjectCelestialPoints.map((p) => (p['abs_pos'] as num).toDouble()).toList();
    secondaryRelPositions = secondSubjectCelestialPoints.map((p) => (p['position'] as num).toDouble()).toList();
  }

  // Build position-to-index mapping and sort
  final positionIndexMap = <double, int>{};
  for (int i = 0; i < availablePlanetsSettings.length && i < mainAbsPositions.length; i++) {
    positionIndexMap[mainAbsPositions[i]] = i;
  }
  final sortedPositions = positionIndexMap.keys.toList()..sort();

  // Calculate adjustments to prevent overlapping
  final positionAdjustments = _calculatePlanetAdjustments(mainAbsPositions, availablePlanetsSettings, positionIndexMap, sortedPositions);

  // Draw main celestial points
  double adjustedOffset = 0.0;
  for (int posIdx = 0; posIdx < sortedPositions.length; posIdx++) {
    final absPosition = sortedPositions[posIdx];
    final pointIdx = positionIndexMap[absPosition]!;

    final pointRadius = _determinePointRadius(pointIdx, chartType, posIdx % 2 == 1, externalView);

    adjustedOffset = _calculatePointOffset(seventhHouseDegreeUt, mainAbsPositions[pointIdx], positionAdjustments[posIdx]);
    final trueOffset = _calculatePointOffset(seventhHouseDegreeUt, mainAbsPositions[pointIdx], 0);

    final pointX = sliceToX(0, radius - pointRadius, adjustedOffset) + pointRadius;
    final pointY = sliceToY(0, radius - pointRadius, adjustedOffset) + pointRadius;

    final scaleFactor = (dualChartTypes.contains(chartType) || externalView) ? 0.8 : 1.0;

    // External view connecting lines
    if (externalView) {
      sb.write(
        _drawExternalNatalLines(
          radius,
          thirdCircleRadius,
          pointRadius.toDouble(),
          trueOffset,
          adjustedOffset,
          availablePlanetsSettings[pointIdx]['color'] as String,
        ),
      );
    }

    // Draw the celestial point
    final point = availableCelestialPoints[pointIdx];
    sb.write(_generatePointSvg(point, pointX, pointY, scaleFactor, availablePlanetsSettings[pointIdx]['name'] as String));
  }

  // Draw degree indicators
  if (chartType == 'Natal' || chartType == 'Composite' || chartType == 'SingleReturnChart') {
    if (showDegreeIndicators && firstCircleRadius != null && !externalView) {
      sb.write(
        _drawPrimaryPointIndicators(
          radius: radius,
          firstCircleRadius: firstCircleRadius,
          thirdCircleRadius: thirdCircleRadius,
          firstHouseDegree: firstHouseDegreeUt,
          seventhHouseDegree: seventhHouseDegreeUt,
          pointsAbsPositions: mainAbsPositions,
          pointsRelPositions: availableCelestialPoints.map((p) => (p['position'] as num).toDouble()).toList(),
          pointsSettings: availablePlanetsSettings,
        ),
      );
    }
  } else if (dualChartTypes.contains(chartType)) {
    if (showDegreeIndicators) {
      // Secondary/outer points
      if (secondaryAbsPositions.isNotEmpty && secondaryRelPositions.isNotEmpty) {
        sb.write(
          _drawSecondaryPoints(
            radius: radius,
            firstHouseDegree: firstHouseDegreeUt,
            seventhHouseDegree: seventhHouseDegreeUt,
            pointsAbsPositions: secondaryAbsPositions,
            pointsRelPositions: secondaryRelPositions,
            pointsSettings: availablePlanetsSettings,
            chartType: chartType,
            excludePoints: transitRingExcludePoints,
            mainOffset: adjustedOffset,
          ),
        );
      }
      // Primary/inner points
      sb.write(
        _drawInnerPointIndicators(
          radius: radius,
          thirdCircleRadius: thirdCircleRadius,
          firstHouseDegree: firstHouseDegreeUt,
          seventhHouseDegree: seventhHouseDegreeUt,
          pointsAbsPositions: mainAbsPositions,
          pointsRelPositions: availableCelestialPoints.map((p) => (p['position'] as num).toDouble()).toList(),
          pointsSettings: availablePlanetsSettings,
        ),
      );
    }
  }

  return sb.toString();
}

// =============================================================================
// POSITION CALCULATION
// =============================================================================

List<double> _calculatePlanetAdjustments(
  List<double> pointsAbsPositions,
  List<Map<String, dynamic>> pointsSettings,
  Map<double, int> positionIndexMap,
  List<double> sortedPositions,
) {
  final int n = pointsSettings.length;
  final planetsByPosition = List<List<double>?>.filled(n, null);
  final pointGroups = <List<List<dynamic>>>[];
  final positionAdjustments = List<double>.filled(sortedPositions.length, 0.0);
  bool isGroupOpen = false;

  for (int posIdx = 0; posIdx < sortedPositions.length; posIdx++) {
    final absPos = sortedPositions[posIdx];
    final pointIdx = positionIndexMap[absPos]!;

    double distToPrev, distToNext;
    if (sortedPositions.length == 1) {
      distToPrev = 360.0;
      distToNext = 360.0;
    } else {
      final adj = _getAdjacentPositions(posIdx, sortedPositions, positionIndexMap, pointsAbsPositions);
      distToPrev = degreeDiff(adj[0], pointsAbsPositions[pointIdx]);
      distToNext = degreeDiff(adj[1], pointsAbsPositions[pointIdx]);
    }

    planetsByPosition[posIdx] = [pointIdx.toDouble(), distToPrev, distToNext];
    final label = pointsSettings[pointIdx]['label'] ?? pointsSettings[pointIdx]['name'];

    if (distToNext < planetGroupingThreshold) {
      final pointData = [posIdx, distToPrev, distToNext, label];
      if (isGroupOpen) {
        pointGroups.last.add(pointData);
      } else {
        isGroupOpen = true;
        pointGroups.add([pointData]);
      }
    } else {
      if (isGroupOpen) {
        final pointData = [posIdx, distToPrev, distToNext, label];
        pointGroups.last.add(pointData);
      }
      isGroupOpen = false;
    }
  }

  // Apply adjustments per group
  for (final group in pointGroups) {
    if (group.length == 2) {
      _handleTwoPointGroup(group, planetsByPosition, positionAdjustments, planetGroupingThreshold);
    } else if (group.length >= 3) {
      _handleMultiPointGroup(group, positionAdjustments, planetGroupingThreshold);
    }
  }

  return positionAdjustments;
}

List<double> _getAdjacentPositions(int posIdx, List<double> sortedPositions, Map<double, int> positionIndexMap, List<double> pointsAbsPositions) {
  final total = sortedPositions.length;
  int prevIdx, nextIdx;
  if (posIdx == 0) {
    prevIdx = positionIndexMap[sortedPositions.last]!;
    nextIdx = positionIndexMap[sortedPositions[1]]!;
  } else if (posIdx == total - 1) {
    prevIdx = positionIndexMap[sortedPositions[posIdx - 1]]!;
    nextIdx = positionIndexMap[sortedPositions[0]]!;
  } else {
    prevIdx = positionIndexMap[sortedPositions[posIdx - 1]]!;
    nextIdx = positionIndexMap[sortedPositions[posIdx + 1]]!;
  }
  return [pointsAbsPositions[prevIdx], pointsAbsPositions[nextIdx]];
}

void _handleTwoPointGroup(List<List<dynamic>> group, List<List<double>?> planetsByPosition, List<double> positionAdjustments, double threshold) {
  final int idxA = group[0][0] as int;
  final int idxB = group[1][0] as int;
  final double distPrevA = (group[0][1] as num).toDouble();
  final double distNextA = (group[0][2] as num).toDouble();
  final double distNextB = (group[1][2] as num).toDouble();

  final nextToA = idxA - 1;
  final nextToB = (idxB == planetsByPosition.length - 1) ? 0 : idxB + 1;

  if (distPrevA > (2 * threshold) && distNextB > (2 * threshold)) {
    positionAdjustments[idxA] = -(threshold - distNextA) / 2;
    positionAdjustments[idxB] = (threshold - distNextA) / 2;
  } else if (distPrevA > (2 * threshold)) {
    positionAdjustments[idxA] = -threshold;
  } else if (distNextB > (2 * threshold)) {
    positionAdjustments[idxB] = threshold;
  } else if (nextToA >= 0 &&
      nextToB < planetsByPosition.length &&
      planetsByPosition[nextToA] != null &&
      planetsByPosition[nextToB] != null &&
      planetsByPosition[nextToA]![1] > (2.4 * threshold) &&
      planetsByPosition[nextToB]![2] > (2.4 * threshold)) {
    positionAdjustments[nextToA] = distPrevA - threshold * 2;
    positionAdjustments[idxA] = -threshold * 0.5;
    positionAdjustments[nextToB] = -(distNextB - threshold * 2);
    positionAdjustments[idxB] = threshold * 0.5;
  } else if (nextToA >= 0 && planetsByPosition[nextToA] != null && planetsByPosition[nextToA]![1] > (2 * threshold)) {
    positionAdjustments[nextToA] = distPrevA - threshold * 2.5;
    positionAdjustments[idxA] = -threshold * 1.2;
  } else if (nextToB < planetsByPosition.length && planetsByPosition[nextToB] != null && planetsByPosition[nextToB]![2] > (2 * threshold)) {
    positionAdjustments[nextToB] = -(distNextB - threshold * 2.5);
    positionAdjustments[idxB] = threshold * 1.2;
  }
}

void _handleMultiPointGroup(List<List<dynamic>> group, List<double> positionAdjustments, double threshold) {
  final groupSize = group.length;
  double availableSpace = (group[0][1] as num).toDouble();
  for (int i = 0; i < groupSize; i++) {
    availableSpace += (group[i][2] as num).toDouble();
  }

  final neededSpace = (3 * threshold) + (1.2 * (groupSize - 1) * threshold);
  final leftoverSpace = availableSpace - neededSpace;

  final spaceBeforeFirst = (group[0][1] as num).toDouble();
  final spaceAfterLast = (group[groupSize - 1][2] as num).toDouble();

  double startPosition;
  if (spaceBeforeFirst > (neededSpace * 0.5) && spaceAfterLast > (neededSpace * 0.5)) {
    startPosition = spaceBeforeFirst - (neededSpace * 0.5);
  } else {
    startPosition = (leftoverSpace / (spaceBeforeFirst + spaceAfterLast)) * spaceBeforeFirst;
  }

  if (availableSpace > neededSpace) {
    final idx0 = group[0][0] as int;
    positionAdjustments[idx0] = startPosition - (group[0][1] as num).toDouble() + (1.5 * threshold);
    for (int i = 0; i < groupSize - 1; i++) {
      final idxI = group[i][0] as int;
      final idxNext = group[i + 1][0] as int;
      positionAdjustments[idxNext] = 1.2 * threshold + positionAdjustments[idxI] - (group[i][2] as num).toDouble();
    }
  }
}

double _calculatePointOffset(double seventhHouseDeg, double pointDeg, double adjustment) {
  // Match Python: (int(seventh_house_degree) / -1) + int(point_degree + adjustment)
  return (seventhHouseDeg.truncateToDouble() / -1) + (pointDeg + adjustment).truncateToDouble();
}

int _determinePointRadius(int pointIdx, String chartType, bool isAlternate, bool externalView) {
  final isChartAngle = chartAngleMinIndex < pointIdx && pointIdx < chartAngleMaxIndex;

  if (dualChartTypes.contains(chartType)) {
    if (isChartAngle) return dualChartAngleRadius;
    return isAlternate ? dualChartPlanetRadiusA : dualChartPlanetRadiusB;
  }

  if (externalView) return 10;

  if (isChartAngle) return 40;
  return isAlternate ? 74 : 94;
}

// =============================================================================
// SVG RENDERING
// =============================================================================

String _generatePointSvg(Map<String, dynamic> pointDetails, double x, double y, double scale, String pointName) {
  final house = pointDetails['house'] ?? '';
  final sign = pointDetails['sign'] ?? '';
  final absPos = pointDetails['abs_pos'] ?? 0;
  final position = pointDetails['position'] ?? 0;
  final name = pointDetails['name'] ?? '';

  return '<g kr:node="ChartPoint" kr:house="$house" '
      'kr:sign="$sign" kr:absoluteposition="$absPos" '
      'kr:signposition="$position" kr:slug="$name" '
      'transform="translate(-${12 * scale},-${12 * scale}) scale($scale)">'
      '<use x="${x * (1 / scale)}" y="${y * (1 / scale)}" xlink:href="#$pointName"/>'
      '</g>';
}

String _drawExternalNatalLines(double radius, double thirdCircleRadius, double pointRadius, double trueOffset, double adjustedOffset, String color) {
  final sb = StringBuffer();
  final x1a = sliceToX(0, radius - thirdCircleRadius, trueOffset) + thirdCircleRadius;
  final y1a = sliceToY(0, radius - thirdCircleRadius, trueOffset) + thirdCircleRadius;
  final x2a = sliceToX(0, radius - pointRadius - 30, trueOffset) + pointRadius + 30;
  final y2a = sliceToY(0, radius - pointRadius - 30, trueOffset) + pointRadius + 30;
  sb.write(
    '<line x1="$x1a" y1="$y1a" x2="$x2a" y2="$y2a" '
    'style="stroke-width:1px;stroke:$color;stroke-opacity:.3;"/>\n',
  );

  final x2b = sliceToX(0, radius - pointRadius - 10, adjustedOffset) + pointRadius + 10;
  final y2b = sliceToY(0, radius - pointRadius - 10, adjustedOffset) + pointRadius + 10;
  sb.write(
    '<line x1="$x2a" y1="$y2a" x2="$x2b" y2="$y2b" '
    'style="stroke-width:1px;stroke:$color;stroke-opacity:.5;"/>\n',
  );

  return sb.toString();
}

/// Convert decimal to degree string with format type.
/// format "1" = "a°", "2" = "a°b'", "3" = "a°b'c\""
String convertDecimalToDegreeStringFormatted(double dec, {String formatType = '3'}) {
  final d = dec.truncate();
  final mf = (dec - d).abs() * 60.0;
  final m = mf.truncate();
  final s = ((mf - m) * 60.0).round();

  if (formatType == '1') return '$d°';
  if (formatType == '2') return '$d°${m.toString().padLeft(2, '0')}\'';
  return '$d°${m.toString().padLeft(2, '0')}\'${s.toString().padLeft(2, '0')}"';
}

(double, String) _calculateTextRotation(double firstHouseDegree, double pointAbsPosition) {
  double rotation = firstHouseDegree - pointAbsPosition;
  String textAnchor = 'end';

  while (rotation > 180) rotation -= 360;
  while (rotation < -180) rotation += 360;

  if (rotation < -90 || rotation > 90) {
    rotation += rotation < 0 ? 180 : -180;
    textAnchor = 'start';
  }

  return (rotation, textAnchor);
}

// =============================================================================
// INDICATOR CALCULATION
// =============================================================================

Map<int, double> _calculateIndicatorAdjustments(
  List<double> pointsAbsPositions,
  List<Map<String, dynamic>> pointsSettings, {
  String chartType = '',
  List<String>? excludePoints,
}) {
  final adjustments = <int, double>{for (int i = 0; i < pointsSettings.length; i++) i: 0.0};
  excludePoints ??= [];

  final positionIndexMap = <double, int>{};
  for (int i = 0; i < pointsSettings.length; i++) {
    if (chartType == 'Transit' && excludePoints.contains(pointsSettings[i]['name'])) continue;
    positionIndexMap[pointsAbsPositions[i]] = i;
  }

  final sortedPositions = positionIndexMap.keys.toList()..sort();
  final pointGroups = <List<int>>[];
  bool inGroup = false;

  for (int posIdx = 0; posIdx < sortedPositions.length; posIdx++) {
    final idxA = positionIndexMap[sortedPositions[posIdx]]!;
    final nextPosIdx = posIdx == sortedPositions.length - 1 ? 0 : posIdx + 1;
    final idxB = positionIndexMap[sortedPositions[nextPosIdx]]!;

    final distance = degreeDiff(pointsAbsPositions[idxA], pointsAbsPositions[idxB]);

    if (distance <= indicatorGroupingThreshold) {
      if (inGroup) {
        pointGroups.last.add(idxB);
      } else {
        pointGroups.add([idxA, idxB]);
        inGroup = true;
      }
    } else {
      inGroup = false;
    }
  }

  for (final group in pointGroups) {
    _applyGroupAdjustments(group, adjustments);
  }

  return adjustments;
}

void _applyGroupAdjustments(List<int> group, Map<int, double> adjustments) {
  final size = group.length;
  if (size == 2) {
    adjustments[group[0]] = -1.5;
    adjustments[group[1]] = 1.5;
  } else if (size == 3) {
    adjustments[group[0]] = -2.0;
    adjustments[group[1]] = 0.0;
    adjustments[group[2]] = 2.0;
  } else if (size == 4) {
    adjustments[group[0]] = -3.0;
    adjustments[group[1]] = -1.0;
    adjustments[group[2]] = 1.0;
    adjustments[group[3]] = 3.0;
  } else if (size >= 5) {
    const spread = 1.5;
    final mid = (size - 1) / 2.0;
    for (int i = 0; i < group.length; i++) {
      adjustments[group[i]] = (i - mid) * spread;
    }
  }
}

void _applySecondaryGroupAdjustments(List<int> group, Map<int, double> adjustments) {
  final size = group.length;
  if (size == 2) {
    adjustments[group[0]] = -1.0;
    adjustments[group[1]] = 1.0;
  } else if (size == 3) {
    adjustments[group[0]] = -1.5;
    adjustments[group[1]] = 0.0;
    adjustments[group[2]] = 1.5;
  } else if (size == 4) {
    adjustments[group[0]] = -2.0;
    adjustments[group[1]] = -1.0;
    adjustments[group[2]] = 1.0;
    adjustments[group[3]] = 2.0;
  }
}

Map<int, double> _calculateSecondaryIndicatorAdjustments(
  List<double> pointsAbsPositions,
  List<Map<String, dynamic>> pointsSettings, {
  String chartType = '',
  List<String>? excludePoints,
}) {
  final adjustments = <int, double>{for (int i = 0; i < pointsSettings.length; i++) i: 0.0};
  excludePoints ??= [];

  final positionIndexMap = <double, int>{};
  for (int i = 0; i < pointsSettings.length; i++) {
    if (chartType == 'Transit' && excludePoints.contains(pointsSettings[i]['name'])) continue;
    positionIndexMap[pointsAbsPositions[i]] = i;
  }

  final sortedPositions = positionIndexMap.keys.toList()..sort();
  final pointGroups = <List<int>>[];
  bool inGroup = false;

  for (int posIdx = 0; posIdx < sortedPositions.length; posIdx++) {
    final idxA = positionIndexMap[sortedPositions[posIdx]]!;
    final nextPosIdx = posIdx == sortedPositions.length - 1 ? 0 : posIdx + 1;
    final idxB = positionIndexMap[sortedPositions[nextPosIdx]]!;

    final distance = degreeDiff(pointsAbsPositions[idxA], pointsAbsPositions[idxB]);

    if (distance <= indicatorGroupingThreshold) {
      if (inGroup) {
        pointGroups.last.add(idxB);
      } else {
        pointGroups.add([idxA, idxB]);
        inGroup = true;
      }
    } else {
      inGroup = false;
    }
  }

  for (final group in pointGroups) {
    _applySecondaryGroupAdjustments(group, adjustments);
  }

  return adjustments;
}

// =============================================================================
// DEGREE INDICATOR DRAWING
// =============================================================================

String _drawPrimaryPointIndicators({
  required double radius,
  required double firstCircleRadius,
  required double thirdCircleRadius,
  required double firstHouseDegree,
  required double seventhHouseDegree,
  required List<double> pointsAbsPositions,
  required List<double> pointsRelPositions,
  required List<Map<String, dynamic>> pointsSettings,
}) {
  final sb = StringBuffer();
  final adjustments = _calculateIndicatorAdjustments(pointsAbsPositions, pointsSettings);
  final zeroPoint = 360.0 - seventhHouseDegree;

  for (int i = 0; i < pointsSettings.length; i++) {
    double pointOffset = zeroPoint + pointsAbsPositions[i];
    if (pointOffset > 360) pointOffset -= 360;

    // Radial indicator line
    final x1 = sliceToX(0, radius - firstCircleRadius + 4, pointOffset) + firstCircleRadius - 4;
    final y1 = sliceToY(0, radius - firstCircleRadius + 4, pointOffset) + firstCircleRadius - 4;
    final x2 = sliceToX(0, radius - firstCircleRadius - 4, pointOffset) + firstCircleRadius + 4;
    final y2 = sliceToY(0, radius - firstCircleRadius - 4, pointOffset) + firstCircleRadius + 4;

    final color = pointsSettings[i]['color'] as String;
    sb.write(
      '<line class="planet-degree-line" x1="$x1" y1="$y1" '
      'x2="$x2" y2="$y2" '
      'style="stroke: $color; stroke-width: 1px; stroke-opacity:.8;"/>',
    );

    // Rotated degree text
    final (rotation, textAnchor) = _calculateTextRotation(firstHouseDegree, pointsAbsPositions[i]);
    final xOffset = textAnchor == 'end' ? 1.0 : -1.0;
    final adjPointOffset = pointOffset + (adjustments[i] ?? 0.0);
    const textRadius = 5.0; // firstCircleRadius - 5.0 simplified for natal

    final degX = sliceToX(0, radius - (firstCircleRadius - textRadius), adjPointOffset + xOffset) + (firstCircleRadius - textRadius);
    final degY = sliceToY(0, radius - (firstCircleRadius - textRadius), adjPointOffset + xOffset) + (firstCircleRadius - textRadius);

    final degText = convertDecimalToDegreeStringFormatted(pointsRelPositions[i], formatType: '1');
    sb.write('<g transform="translate($degX,$degY)">');
    sb.write(
      '<text transform="rotate($rotation)" text-anchor="$textAnchor" '
      'style="fill: $color; font-size: 10px;">$degText</text></g>',
    );
  }

  return sb.toString();
}

String _drawInnerPointIndicators({
  required double radius,
  required double thirdCircleRadius,
  required double firstHouseDegree,
  required double seventhHouseDegree,
  required List<double> pointsAbsPositions,
  required List<double> pointsRelPositions,
  required List<Map<String, dynamic>> pointsSettings,
}) {
  final sb = StringBuffer();
  final adjustments = _calculateIndicatorAdjustments(pointsAbsPositions, pointsSettings);
  final zeroPoint = 360.0 - seventhHouseDegree;

  for (int i = 0; i < pointsSettings.length; i++) {
    double pointOffset = zeroPoint + pointsAbsPositions[i];
    if (pointOffset > 360) pointOffset -= 360;

    final x1 = sliceToX(0, radius - natalIndicatorOffset + 4, pointOffset) + natalIndicatorOffset - 4;
    final y1 = sliceToY(0, radius - natalIndicatorOffset + 4, pointOffset) + natalIndicatorOffset - 4;
    final x2 = sliceToX(0, radius - natalIndicatorOffset - 4, pointOffset) + natalIndicatorOffset + 4;
    final y2 = sliceToY(0, radius - natalIndicatorOffset - 4, pointOffset) + natalIndicatorOffset + 4;

    final color = pointsSettings[i]['color'] as String;
    sb.write(
      '<line class="planet-degree-line-inner" x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
      'style="stroke: $color; stroke-width: 1px; stroke-opacity:.8;"/>',
    );

    final (rotation, rawAnchor) = _calculateTextRotation(firstHouseDegree, pointsAbsPositions[i]);
    final textAnchor = rawAnchor == 'end' ? 'start' : 'end';

    final adjPointOffset = pointOffset + (adjustments[i] ?? 0.0);
    const textRadius = natalIndicatorOffset + 5.0;

    final degX = sliceToX(0, radius - textRadius, adjPointOffset) + textRadius;
    final degY = sliceToY(0, radius - textRadius, adjPointOffset) + textRadius;

    final degText = convertDecimalToDegreeStringFormatted(pointsRelPositions[i], formatType: '1');
    sb.write('<g transform="translate($degX,$degY)">');
    sb.write(
      '<text transform="rotate($rotation)" text-anchor="$textAnchor" '
      'style="fill: $color; font-size: 8px; dominant-baseline: middle;">$degText</text></g>',
    );
  }

  return sb.toString();
}

String _drawSecondaryPoints({
  required double radius,
  required double firstHouseDegree,
  required double seventhHouseDegree,
  required List<double> pointsAbsPositions,
  required List<double> pointsRelPositions,
  required List<Map<String, dynamic>> pointsSettings,
  required String chartType,
  required List<String> excludePoints,
  required double mainOffset,
}) {
  final sb = StringBuffer();
  final adjustments = _calculateSecondaryIndicatorAdjustments(pointsAbsPositions, pointsSettings, chartType: chartType, excludePoints: excludePoints);

  final positionIndexMap = <double, int>{};
  for (int i = 0; i < pointsSettings.length; i++) {
    if (chartType == 'Transit' && excludePoints.contains(pointsSettings[i]['name'])) continue;
    positionIndexMap[pointsAbsPositions[i]] = i;
  }

  final sortedPositions = positionIndexMap.keys.toList()..sort();
  final zeroPoint = 360.0 - seventhHouseDegree;
  bool alternatePosition = false;
  int pointIdx = 0;

  for (final absPos in sortedPositions) {
    pointIdx = positionIndexMap[absPos]!;

    if (chartType == 'Transit' && excludePoints.contains(pointsSettings[pointIdx]['name'])) continue;

    final isChartAngle = chartAngleMinIndex < pointIdx && pointIdx < chartAngleMaxIndex;
    int pointRadius;
    if (isChartAngle) {
      pointRadius = 9;
    } else if (alternatePosition) {
      pointRadius = 18;
      alternatePosition = false;
    } else {
      pointRadius = 26;
      alternatePosition = true;
    }

    double pointOffset = zeroPoint + pointsAbsPositions[pointIdx];
    if (pointOffset > 360) pointOffset -= 360;

    // Point symbol
    final px = sliceToX(0, radius - pointRadius, pointOffset) + pointRadius;
    final py = sliceToY(0, radius - pointRadius, pointOffset) + pointRadius;
    sb.write('<g class="transit-planet-name" transform="translate(-6,-6)"><g transform="scale(0.5)">');
    sb.write('<use x="${px * 2}" y="${py * 2}" xlink:href="#${pointsSettings[pointIdx]['name']}"/></g></g>');

    // Indicator line
    final x1 = sliceToX(0, radius + 3, pointOffset) - 3;
    final y1 = sliceToY(0, radius + 3, pointOffset) - 3;
    final x2 = sliceToX(0, radius - 3, pointOffset) + 3;
    final y2 = sliceToY(0, radius - 3, pointOffset) + 3;
    final color = pointsSettings[pointIdx]['color'] as String;
    sb.write(
      '<line class="transit-planet-line" x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
      'style="stroke: $color; stroke-width: 1px; stroke-opacity:.8;"/>',
    );

    // Degree text
    final (rotation, textAnchor) = _calculateTextRotation(firstHouseDegree, pointsAbsPositions[pointIdx]);
    final xOff = textAnchor == 'end' ? 1.0 : -1.0;
    final adjOffset = pointOffset + (adjustments[pointIdx] ?? 0.0);
    const textRadius = -3.0;

    final degX = sliceToX(0, radius - textRadius, adjOffset + xOff) + textRadius;
    final degY = sliceToY(0, radius - textRadius, adjOffset + xOff) + textRadius;

    final degText = convertDecimalToDegreeStringFormatted(pointsRelPositions[pointIdx], formatType: '1');
    sb.write('<g transform="translate($degX,$degY)">');
    sb.write(
      '<text transform="rotate($rotation)" text-anchor="$textAnchor" '
      'style="fill: $color; font-size: 10px;">$degText</text></g>',
    );
  }

  // Connecting lines
  final dropin1 = dualChartTypes.contains(chartType) ? 36.0 : 0.0;
  final cx1 = sliceToX(0, radius - (dropin1 + 3), mainOffset) + (dropin1 + 3);
  final cy1 = sliceToY(0, radius - (dropin1 + 3), mainOffset) + (dropin1 + 3);
  final cx2 = sliceToX(0, radius - (dropin1 - 3), mainOffset) + (dropin1 - 3);
  final cy2 = sliceToY(0, radius - (dropin1 - 3), mainOffset) + (dropin1 - 3);
  final lastColor = pointsSettings[pointIdx]['color'] as String;
  sb.write(
    '<line x1="$cx1" y1="$cy1" x2="$cx2" y2="$cy2" '
    'style="stroke: $lastColor; stroke-width: 2px; stroke-opacity:.6;"/>',
  );

  final dropin2 = dualChartTypes.contains(chartType) ? 160.0 : 120.0;
  final dx1 = sliceToX(0, radius - dropin2, mainOffset) + dropin2;
  final dy1 = sliceToY(0, radius - dropin2, mainOffset) + dropin2;
  final dx2 = sliceToX(0, radius - (dropin2 - 3), mainOffset) + (dropin2 - 3);
  final dy2 = sliceToY(0, radius - (dropin2 - 3), mainOffset) + (dropin2 - 3);
  sb.write(
    '<line x1="$dx1" y1="$dy1" x2="$dx2" y2="$dy2" '
    'style="stroke: $lastColor; stroke-width: 2px; stroke-opacity:.6;"/>',
  );

  return sb.toString();
}
