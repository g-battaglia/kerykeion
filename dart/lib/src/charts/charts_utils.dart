import 'dart:math' as math;

/// Mathematical and SVG drawing utilities for astrological chart rendering.
/// Ported from Python kerykeion charts_utils.py.

// ============================================================================
// MATH UTILITIES
// ============================================================================

/// Normalize a degree value to 0–360 range.
double normalizeDegree(double degree) {
  double d = degree % 360.0;
  if (d < 0) d += 360.0;
  return d;
}

/// Calculate the shortest difference between two degree values.
double degreeDiff(double a, double b) {
  double diff = ((a - b) % 360.0).abs();
  if (diff > 180.0) diff = 360.0 - diff;
  return diff;
}

/// Sum two degree values, normalizing to 0–360.
double degreeSum(double a, double b) => normalizeDegree(a + b);

/// Join hours and minutes into a decimal hour.
double decHourJoin(int hour, int minute, [int second = 0]) => hour + minute / 60.0 + second / 3600.0;

/// Convert degree position to X coordinate on the chart circle.
///
/// The zodiac wheel is rotated so that the 7th house cusp (Descendant)
/// is at the left (180° in SVG coordinates). All positions are relative
/// to this anchor.
double sliceToX(double r, double degree, double offsetDegree) {
  final adjustedDegree = degree + offsetDegree;
  return r * math.cos(adjustedDegree * math.pi / 180.0);
}

/// Convert degree position to Y coordinate on the chart circle.
double sliceToY(double r, double degree, double offsetDegree) {
  final adjustedDegree = degree + offsetDegree;
  return r * math.sin(adjustedDegree * math.pi / 180.0);
}

/// Convert a decimal degree value to a formatted string like "12° 34' 56\"".
String convertDecimalToDegreeString(double dec) {
  final int d = dec.truncate();
  final double mf = (dec - d).abs() * 60.0;
  final int m = mf.truncate();
  final int s = ((mf - m) * 60.0).round();

  // Handle carry
  int mm = m, dd = d, ss = s;
  if (ss >= 60) {
    ss -= 60;
    mm++;
  }
  if (mm >= 60) {
    mm -= 60;
    dd++;
  }
  final dStr = dd.abs().toString();
  final mStr = mm.toString().padLeft(2, '0');
  final sStr = ss.toString().padLeft(2, '0');
  return '$dStr° $mStr\' $sStr"';
}

/// Convert a latitude coordinate to a human-readable string.
String convertLatitudeCoordinateToString(double coord, String north, String south) {
  final direction = coord >= 0 ? north : south;
  return '${convertDecimalToDegreeString(coord.abs())} $direction';
}

/// Convert a longitude coordinate to a human-readable string.
String convertLongitudeCoordinateToString(double coord, String east, String west) {
  final direction = coord >= 0 ? east : west;
  return '${convertDecimalToDegreeString(coord.abs())} $direction';
}

/// Format a location string, truncating if too long.
String formatLocationString(String location, {int maxLength = 35}) {
  if (location.length <= maxLength) return location;
  final parts = location.split(',');
  if (parts.length > 1) {
    final shortened = '${parts.first}, ${parts.last}';
    if (shortened.length > maxLength) return '${shortened.substring(0, maxLength)}...';
    return shortened;
  }
  return '${location.substring(0, maxLength)}...';
}

// ============================================================================
// SVG DRAWING PRIMITIVES
// ============================================================================

/// Draw a single zodiac slice (30° arc segment) in the zodiac ring.
///
/// Each slice is a filled arc segment between the first and second circle
/// radii, plus a zodiac sign icon centered within it.
String drawZodiacSlice({
  required double c1,
  required String chartType,
  required double seventhHouseDegreeUt,
  required int num,
  required double r,
  required String style,
  required String type,
}) {
  // Each zodiac sign spans 30°
  final double offset = 360.0 - seventhHouseDegreeUt;
  // Calculate the start and end degree for this slice
  final double startDeg = num * 30.0 + offset;
  final double endDeg = (num + 1) * 30.0 + offset;
  final double midDeg = startDeg + 15.0;

  // Calculate the inner radius based on chart type
  double innerRadius;
  if (chartType == 'Natal') {
    innerRadius = r - c1 - 36.0; // Second circle boundary
  } else {
    innerRadius = r - 36.0;
  }

  // Outer and inner arc points
  final ox1 = r + sliceToX(r, startDeg, 0);
  final oy1 = r + sliceToY(r, startDeg, 0);
  final ox2 = r + sliceToX(r, endDeg, 0);
  final oy2 = r + sliceToY(r, endDeg, 0);
  final ix1 = r + sliceToX(innerRadius, startDeg, 0);
  final iy1 = r + sliceToY(innerRadius, startDeg, 0);
  final ix2 = r + sliceToX(innerRadius, endDeg, 0);
  final iy2 = r + sliceToY(innerRadius, endDeg, 0);

  // Icon position (centered within the slice)
  final iconRadius = (r + innerRadius) / 2.0;
  final iconX = r + sliceToX(iconRadius, midDeg, 0) - 5.0;
  final iconY = r + sliceToY(iconRadius, midDeg, 0) - 5.0;

  final sb = StringBuffer();
  // Arc slice
  sb.write(
    '<path d="M $ox1 $oy1 A $r $r 0 0 0 $ox2 $oy2 '
    'L $ix2 $iy2 A $innerRadius $innerRadius 0 0 1 $ix1 $iy1 Z" '
    'style="$style"/>',
  );
  // Zodiac icon
  sb.write(
    '<use x="$iconX" y="$iconY" xlink:href="#$type" '
    'transform="scale(0.7)"/>',
  );
  return sb.toString();
}

/// Draw the degree ring (1° tick marks around the zodiac ring edge).
String drawDegreeRing(double r, double firstCircleRadius, double offsetDegree, String color) {
  final sb = StringBuffer();
  for (int i = 0; i < 360; i++) {
    final deg = i.toDouble() + (360.0 - offsetDegree);
    final outerR = r;
    final innerR = r - firstCircleRadius;
    final tickLen = (i % 5 == 0) ? 3.0 : 1.5;

    final x1 = r + sliceToX(outerR, deg, 0);
    final y1 = r + sliceToY(outerR, deg, 0);
    final x2 = r + sliceToX(outerR - tickLen, deg, 0);
    final y2 = r + sliceToY(outerR - tickLen, deg, 0);

    sb.write(
      '<line x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
      'style="stroke: $color; stroke-width: 0.5px;"/>',
    );
  }
  return sb.toString();
}

/// Draw the transit ring degree steps (for dual charts).
String drawTransitRingDegreeSteps(double r, double offsetDegree) {
  final sb = StringBuffer();
  for (int i = 0; i < 360; i++) {
    final deg = i.toDouble() + (360.0 - offsetDegree);
    final outerR = r + 36.0;
    final tickLen = (i % 5 == 0) ? 3.0 : 1.5;

    final x1 = r + sliceToX(outerR, deg, 0);
    final y1 = r + sliceToY(outerR, deg, 0);
    final x2 = r + sliceToX(outerR - tickLen, deg, 0);
    final y2 = r + sliceToY(outerR - tickLen, deg, 0);

    sb.write(
      '<line x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
      'style="stroke: var(--kerykeion-chart-color-paper-0); stroke-width: 0.5px;"/>',
    );
  }
  return sb.toString();
}

/// Draw the background circle.
String drawBackgroundCircle(double r, String fillColor, String strokeColor) {
  return '<circle cx="$r" cy="$r" r="$r" '
      'style="fill: $fillColor; stroke: $strokeColor; stroke-width: 1px;"/>';
}

/// Draw the first (outermost structural) circle.
String drawFirstCircle(double r, String strokeColor, String chartType, double firstCircleRadius) {
  final double radius;
  if (chartType == 'Natal') {
    radius = r - firstCircleRadius;
  } else {
    radius = r;
  }
  return '<circle cx="$r" cy="$r" r="$radius" '
      'style="fill: none; stroke: $strokeColor; stroke-width: 1px;"/>';
}

/// Draw the second (zodiac boundary) circle.
String drawSecondCircle(double r, String strokeColor, String fillColor, String chartType, double secondCircleRadius) {
  final double radius;
  if (chartType == 'Natal') {
    radius = r - secondCircleRadius;
  } else {
    radius = r - 36.0;
  }
  return '<circle cx="$r" cy="$r" r="$radius" '
      'style="fill: $fillColor; stroke: $strokeColor; stroke-width: 1px;"/>';
}

/// Draw the third (innermost) circle.
String drawThirdCircle(double r, String strokeColor, String fillColor, String chartType, double thirdCircleRadius) {
  final double radius = r - thirdCircleRadius;
  return '<circle cx="$r" cy="$r" r="$radius" '
      'style="fill: $fillColor; stroke: $strokeColor; stroke-width: 1px;"/>';
}

/// Draw the transit ring (outer ring for dual-wheel charts).
String drawTransitRing(double r, String fillColor, String strokeColor) {
  final double radius = r + 36.0;
  return '<circle cx="$r" cy="$r" r="$radius" '
      'style="fill: $fillColor; stroke: $strokeColor; stroke-width: 1px;"/>';
}

/// Draw house cusps and house numbers on the wheel.
///
/// For dual charts, both subject's house cusps are drawn.
String drawHousesCuspsAndTextNumber({
  required double r,
  required List<Map<String, dynamic>> firstSubjectHousesList,
  required String standardHouseCuspColor,
  required String firstHouseColor,
  required String tenthHouseColor,
  required String seventhHouseColor,
  required String fourthHouseColor,
  required double c1,
  required double c3,
  required String chartType,
  bool externalView = false,
  List<Map<String, dynamic>>? secondSubjectHousesList,
  String? transitHouseCuspColor,
}) {
  final sb = StringBuffer();
  final double offset = 360.0 - (firstSubjectHousesList[6]['abs_pos'] as double);

  for (int i = 0; i < 12; i++) {
    final absPos = firstSubjectHousesList[i]['abs_pos'] as double;
    final deg = absPos + offset;

    // Choose color for angular houses
    String color;
    if (i == 0) {
      color = firstHouseColor;
    } else if (i == 3) {
      color = fourthHouseColor;
    } else if (i == 6) {
      color = seventhHouseColor;
    } else if (i == 9) {
      color = tenthHouseColor;
    } else {
      color = standardHouseCuspColor;
    }

    final double strokeWidth = (i == 0 || i == 3 || i == 6 || i == 9) ? 1.5 : 0.5;

    // Draw cusp line
    double outerR, innerR;
    if (chartType == 'Natal' && externalView) {
      outerR = r;
      innerR = r - c3;
    } else if (chartType == 'Natal') {
      outerR = r - c1;
      innerR = r - c3;
    } else {
      outerR = r;
      innerR = r - c3;
    }

    final x1 = r + sliceToX(outerR, deg, 0);
    final y1 = r + sliceToY(outerR, deg, 0);
    final x2 = r + sliceToX(innerR, deg, 0);
    final y2 = r + sliceToY(innerR, deg, 0);

    sb.write(
      '<line x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
      'style="stroke: $color; stroke-width: ${strokeWidth}px;"/>',
    );

    // House number text
    final nextHouse = (i + 1) % 12;
    final nextAbsPos = firstSubjectHousesList[nextHouse]['abs_pos'] as double;
    double midDeg;
    if (nextAbsPos > absPos) {
      midDeg = (absPos + nextAbsPos) / 2.0 + offset;
    } else {
      midDeg = (absPos + nextAbsPos + 360.0) / 2.0 + offset;
    }

    final textR = innerR + 3.0;
    final textX = r + sliceToX(textR, midDeg, 0);
    final textY = r + sliceToY(textR, midDeg, 0);

    sb.write(
      '<text x="$textX" y="$textY" '
      'style="fill: var(--kerykeion-chart-color-house-number); font-size: 8px;" '
      'text-anchor="middle" dominant-baseline="central">'
      '${i + 1}</text>',
    );
  }

  // Draw transit house cusps if provided
  if (secondSubjectHousesList != null && transitHouseCuspColor != null) {
    for (int i = 0; i < 12; i++) {
      final absPos = secondSubjectHousesList[i]['abs_pos'] as double;
      final deg = absPos + offset;
      final strokeWidth = (i == 0 || i == 3 || i == 6 || i == 9) ? 1.0 : 0.3;
      final outerR = r + 36.0;
      final innerR = r;

      final x1 = r + sliceToX(outerR, deg, 0);
      final y1 = r + sliceToY(outerR, deg, 0);
      final x2 = r + sliceToX(innerR, deg, 0);
      final y2 = r + sliceToY(innerR, deg, 0);

      sb.write(
        '<line x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
        'style="stroke: $transitHouseCuspColor; stroke-width: ${strokeWidth}px;"/>',
      );
    }
  }

  return sb.toString();
}

/// Draw an aspect line between two planets.
String drawAspectLine({
  required double r,
  required double ar,
  required Map<String, dynamic> aspect,
  required String color,
  required double seventhHouseDegreeUt,
  bool showAspectIcon = true,
  List<List<double>>? renderedIconPositions,
}) {
  final double offset = 360.0 - seventhHouseDegreeUt;
  final double p1Deg = (aspect['p1_abs_pos'] as double) + offset;
  final double p2Deg = (aspect['p2_abs_pos'] as double) + offset;

  final x1 = r + sliceToX(ar, p1Deg, 0);
  final y1 = r + sliceToY(ar, p1Deg, 0);
  final x2 = r + sliceToX(ar, p2Deg, 0);
  final y2 = r + sliceToY(ar, p2Deg, 0);

  final sb = StringBuffer();
  sb.write(
    '<line x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
    'style="stroke: $color; stroke-width: 0.8px; stroke-opacity: 0.7;"/>',
  );

  // Aspect icon at midpoint
  if (showAspectIcon) {
    final midX = (x1 + x2) / 2.0 - 4.0;
    final midY = (y1 + y2) / 2.0 - 4.0;
    final int aspectDeg = aspect['aspect_degrees'] as int;

    // Check overlap with existing icons
    bool overlaps = false;
    if (renderedIconPositions != null) {
      for (final pos in renderedIconPositions) {
        if ((pos[0] - midX).abs() < 10 && (pos[1] - midY).abs() < 10 && pos[2].toInt() == aspectDeg) {
          overlaps = true;
          break;
        }
      }
      if (!overlaps) {
        renderedIconPositions.add([midX, midY, aspectDeg.toDouble()]);
      }
    }

    if (!overlaps) {
      sb.write('<use x="$midX" y="$midY" xlink:href="#orb$aspectDeg"/>');
    }
  }

  return sb.toString();
}

/// Draw the triangular aspect grid for single-wheel charts.
String drawAspectGrid(
  String strokeColor,
  List<Map<String, dynamic>> availablePlanets,
  List<Map<String, dynamic>> aspects, {
  int xStart = 540,
  int yStart = 250,
  int boxSize = 14,
}) {
  final sb = StringBuffer();
  final style = 'stroke:$strokeColor; stroke-width: 0.5px; fill:none';

  final active = availablePlanets.where((p) => p['is_active'] == true).toList();

  for (int i = 0; i < active.length; i++) {
    // Row header
    final rx = xStart - boxSize;
    final ry = yStart - (i * boxSize);
    sb.write(
      '<rect x="$rx" y="$ry" width="$boxSize" height="$boxSize" '
      'style="$style"/>',
    );
    sb.write(
      '<use transform="scale(0.4)" x="${(rx + 2) * 2.5}" y="${(ry + 1) * 2.5}" '
      'xlink:href="#${active[i]['name']}"/>',
    );

    // Cells
    for (int j = 0; j < i; j++) {
      final cx = xStart + (j * boxSize);
      final cy = yStart - (i * boxSize);
      sb.write(
        '<rect x="$cx" y="$cy" width="$boxSize" height="$boxSize" '
        'style="$style"/>',
      );

      // Check for aspect between these two planets
      for (final aspect in aspects) {
        if ((aspect['p1'] == active[i]['id'] && aspect['p2'] == active[j]['id']) || (aspect['p1'] == active[j]['id'] && aspect['p2'] == active[i]['id'])) {
          sb.write('<use x="${cx + 1}" y="${cy + 1}" xlink:href="#orb${aspect['aspect_degrees']}"/>');
        }
      }
    }
  }

  return sb.toString();
}

/// Draw the main planet grid (sidebar table showing planet positions).
String drawMainPlanetGrid({
  required String title,
  required String subjectName,
  required List<Map<String, dynamic>> celestialPoints,
  required String chartType,
  required String textColor,
  int xPosition = 645,
  int yPosition = 0,
}) {
  final sb = StringBuffer();
  sb.write('<g transform="translate($xPosition,$yPosition)">');

  // Title for dual charts
  if (chartType == 'Synastry' || chartType == 'Transit' || chartType == 'DualReturnChart') {
    sb.write('<g transform="translate(0, 15)">');
    sb.write('<text style="fill:$textColor; font-size: 14px;">$title $subjectName</text>');
    sb.write('</g>');
  }

  int lineH = 10;
  for (int i = 0; i < celestialPoints.length; i++) {
    final p = celestialPoints[i];
    final name = p['name'] as String;
    final position = p['position'] as double;
    final sign = p['sign'] as String;
    final retrograde = p['retrograde'] as bool? ?? false;

    sb.write('<g transform="translate(0,${30 + lineH})">');
    sb.write('<text text-anchor="end" style="fill:$textColor; font-size: 10px;">$name</text>');
    sb.write('<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#$name"/></g>');
    sb.write('<text text-anchor="start" x="19" style="fill:$textColor; font-size: 10px;"> ${convertDecimalToDegreeString(position)}</text>');
    sb.write('<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#$sign"/></g>');
    if (retrograde) {
      sb.write('<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde"/></g>');
    }
    sb.write('</g>');
    lineH += 14;
  }

  sb.write('</g>');
  return sb.toString();
}

/// Draw the main house grid (sidebar table showing house cusps).
String drawMainHouseGrid({
  required List<Map<String, dynamic>> housesList,
  required String textColor,
  String cuspLabel = 'Cusp',
  int xPosition = 750,
  int yPosition = 30,
}) {
  final sb = StringBuffer();
  sb.write('<g transform="translate($xPosition,$yPosition)">');

  int lineH = 10;
  for (int i = 0; i < housesList.length; i++) {
    final h = housesList[i];
    final cuspNum = (i < 9) ? '&#160;&#160;${i + 1}' : '${i + 1}';
    final position = h['position'] as double;
    final sign = h['sign'] as String;

    sb.write('<g transform="translate(0,$lineH)">');
    sb.write('<text text-anchor="end" x="40" style="fill:$textColor; font-size: 10px;">$cuspLabel $cuspNum:</text>');
    sb.write('<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#$sign"/></g>');
    sb.write('<text x="53" style="fill:$textColor; font-size: 10px;"> ${convertDecimalToDegreeString(position)}</text>');
    sb.write('</g>');
    lineH += 14;
  }

  sb.write('</g>');
  return sb.toString();
}

/// Calculate moon phase chart parameters from Sun-Moon angle.
Map<String, double> calculateMoonPhaseChartParams(double degreesBetweenSunAndMoon) {
  final phaseAngle = degreesBetweenSunAndMoon % 360.0;
  final radians = phaseAngle * math.pi / 180.0;
  final cosine = math.cos(radians);
  double illuminatedFraction = (1.0 - cosine) / 2.0;
  illuminatedFraction = illuminatedFraction.clamp(0.0, 1.0);

  return {'phase_angle': phaseAngle, 'illuminated_fraction': illuminatedFraction, 'shadow_ellipse_rx': 10.0 * cosine};
}

/// Generate SVG representation of lunar phase.
String makeLunarPhase(double degreesBetweenSunAndMoon, double latitude) {
  final params = calculateMoonPhaseChartParams(degreesBetweenSunAndMoon);
  final phaseAngle = params['phase_angle']!;
  final illuminatedFraction = 1.0 - params['illuminated_fraction']!;
  final shadowEllipseRx = params['shadow_ellipse_rx']!.abs();

  const double radius = 10.0;
  const double centerX = 20.0;
  const double centerY = 10.0;
  const String brightColor = 'var(--kerykeion-chart-color-lunar-phase-1)';
  const String shadowColor = 'var(--kerykeion-chart-color-lunar-phase-0)';

  final bool isWaxing = phaseAngle < 180.0;
  String baseFill;
  String overlayPath = '';
  String overlayFill = '';

  if (illuminatedFraction <= 1e-6) {
    baseFill = shadowColor;
  } else if (1.0 - illuminatedFraction <= 1e-6) {
    baseFill = brightColor;
  } else {
    final isLitMajor = illuminatedFraction >= 0.5;
    String overlaySide;
    if (isLitMajor) {
      baseFill = brightColor;
      overlayFill = shadowColor;
      overlaySide = isWaxing ? 'left' : 'right';
    } else {
      baseFill = shadowColor;
      overlayFill = brightColor;
      overlaySide = isWaxing ? 'right' : 'left';
    }

    // Build lune path
    final rx = shadowEllipseRx.clamp(0.0, radius);
    final topY = centerY - radius;
    final bottomY = centerY + radius;
    final circleSweep = overlaySide == 'right' ? 1 : 0;

    if (rx <= 1e-6) {
      overlayPath =
          'M ${centerX.toStringAsFixed(4)} ${topY.toStringAsFixed(4)}'
          ' A ${radius.toStringAsFixed(4)} ${radius.toStringAsFixed(4)} 0 0 $circleSweep ${centerX.toStringAsFixed(4)} ${bottomY.toStringAsFixed(4)}'
          ' L ${centerX.toStringAsFixed(4)} ${topY.toStringAsFixed(4)} Z';
    } else {
      overlayPath =
          'M ${centerX.toStringAsFixed(4)} ${topY.toStringAsFixed(4)}'
          ' A ${radius.toStringAsFixed(4)} ${radius.toStringAsFixed(4)} 0 0 $circleSweep ${centerX.toStringAsFixed(4)} ${bottomY.toStringAsFixed(4)}'
          ' A ${rx.toStringAsFixed(4)} ${radius.toStringAsFixed(4)} 0 0 $circleSweep ${centerX.toStringAsFixed(4)} ${topY.toStringAsFixed(4)} Z';
    }
  }

  final sb = StringBuffer();
  sb.writeln('<g transform="rotate(0 20 10)">');
  sb.writeln('    <defs>');
  sb.writeln('        <clipPath id="moonPhaseCutOffCircle">');
  sb.writeln('            <circle cx="20" cy="10" r="10"/>');
  sb.writeln('        </clipPath>');
  sb.writeln('    </defs>');
  sb.writeln('    <circle cx="20" cy="10" r="10" style="fill: $baseFill"/>');
  if (overlayPath.isNotEmpty) {
    sb.writeln('    <path d="$overlayPath" style="fill: $overlayFill" clip-path="url(#moonPhaseCutOffCircle)"/>');
  }
  sb.writeln(
    '    <circle cx="20" cy="10" r="10" style="fill: none; stroke: var(--kerykeion-chart-color-lunar-phase-0); stroke-width: 0.5px; stroke-opacity: 0.5"/>',
  );
  sb.writeln('</g>');

  return sb.toString();
}

/// Get a list of house data from an astrological subject model.
///
/// Returns a list of maps with 'abs_pos', 'position', and 'sign' keys.
List<Map<String, dynamic>> getHousesList(Map<String, dynamic> subject) {
  const houseKeys = [
    'firstHouse',
    'secondHouse',
    'thirdHouse',
    'fourthHouse',
    'fifthHouse',
    'sixthHouse',
    'seventhHouse',
    'eighthHouse',
    'ninthHouse',
    'tenthHouse',
    'eleventhHouse',
    'twelfthHouse',
  ];

  // Also support snake_case keys from Python
  const houseKeysSnake = [
    'first_house',
    'second_house',
    'third_house',
    'fourth_house',
    'fifth_house',
    'sixth_house',
    'seventh_house',
    'eighth_house',
    'ninth_house',
    'tenth_house',
    'eleventh_house',
    'twelfth_house',
  ];

  final List<Map<String, dynamic>> result = [];
  for (int i = 0; i < 12; i++) {
    Map<String, dynamic>? house;
    if (subject.containsKey(houseKeys[i])) {
      final val = subject[houseKeys[i]];
      if (val is Map<String, dynamic>) {
        house = val;
      }
    } else if (subject.containsKey(houseKeysSnake[i])) {
      final val = subject[houseKeysSnake[i]];
      if (val is Map<String, dynamic>) {
        house = val;
      }
    }
    if (house != null) {
      result.add({'abs_pos': house['abs_pos'] ?? house['absPos'] ?? 0.0, 'position': house['position'] ?? 0.0, 'sign': house['sign'] ?? 'Ari'});
    } else {
      result.add({'abs_pos': 0.0, 'position': 0.0, 'sign': 'Ari'});
    }
  }
  return result;
}

/// Distribute raw values as integer percentages summing to 100.
/// Uses the largest-remainder method for accurate rounding.
Map<String, int> distributePercentagesTo100(Map<String, double> values) {
  final total = values.values.fold(0.0, (a, b) => a + b);
  if (total == 0) {
    return values.map((k, _) => MapEntry(k, 0));
  }

  final rawPcts = values.map((k, v) => MapEntry(k, v / total * 100.0));
  final floors = rawPcts.map((k, v) => MapEntry(k, v.floor()));
  final remainders = rawPcts.map((k, v) => MapEntry(k, v - v.floor()));

  int allocated = floors.values.fold(0, (a, b) => a + b);
  int remaining = 100 - allocated;

  // Sort by remainder descending
  final sorted = remainders.entries.toList()..sort((a, b) => b.value.compareTo(a.value));

  final result = Map<String, int>.from(floors);
  for (final entry in sorted) {
    if (remaining <= 0) break;
    result[entry.key] = result[entry.key]! + 1;
    remaining--;
  }

  return result;
}
