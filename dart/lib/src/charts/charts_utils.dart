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

/// Calculate X coordinate for a point on the chart circle.
///
/// [slice] — slice index (e.g. 0–11 for zodiac signs, each = 30°).
/// [radius] — circle radius in pixels.
/// [offset] — angular offset in degrees.
///
/// Returns X in the range 0 .. 2*radius (center at radius).
double sliceToX(double slice, double radius, double offset) {
  final plus = (math.pi * offset) / 180.0;
  final radial = ((math.pi / 6.0) * slice) + plus;
  return radius * (math.cos(radial) + 1.0);
}

/// Calculate Y coordinate for a point on the chart circle.
///
/// [slice] — slice index (e.g. 0–11 for zodiac signs, each = 30°).
/// [r] — circle radius in pixels.
/// [offset] — angular offset in degrees.
///
/// Returns Y in the range 0 .. 2*r (center at r), with Y axis flipped.
double sliceToY(double slice, double r, double offset) {
  final plus = (math.pi * offset) / 180.0;
  final radial = ((math.pi / 6.0) * slice) + plus;
  return r * ((math.sin(radial) / -1.0) + 1.0);
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
  return '$dStr\u00B0$mStr\'$sStr"';
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
  // Pie slices from center
  final double offset = 360.0 - seventhHouseDegreeUt;

  // dropin: inner offset from edge for single-wheel charts
  final double dropin;
  if (chartType == 'Transit' || chartType == 'Synastry' || chartType == 'DualReturnChart') {
    dropin = 0;
  } else {
    dropin = c1;
  }

  // Slice path: M center L edge-start A arc to edge-end z
  final sliceX1 = dropin + sliceToX(num.toDouble(), r - dropin, offset);
  final sliceY1 = dropin + sliceToY(num.toDouble(), r - dropin, offset);
  final sliceX2 = dropin + sliceToX((num + 1).toDouble(), r - dropin, offset);
  final sliceY2 = dropin + sliceToY((num + 1).toDouble(), r - dropin, offset);
  final arcR = r - dropin;

  final slice =
      '<path d="M$r,$r L$sliceX1,$sliceY1 '
      'A$arcR,$arcR 0 0,0 $sliceX2,$sliceY2 z" '
      'style="$style"/>';

  // Symbol positioning
  final double symbolDropin;
  if (chartType == 'Transit' || chartType == 'Synastry' || chartType == 'DualReturnChart') {
    symbolDropin = 54;
  } else {
    symbolDropin = 18 + c1;
  }
  final symOffset = offset + 15;
  final symX = symbolDropin + sliceToX(num.toDouble(), r - symbolDropin, symOffset);
  final symY = symbolDropin + sliceToY(num.toDouble(), r - symbolDropin, symOffset);

  final sign =
      '<g transform="translate(-16,-16)">'
      '<use x="$symX" y="$symY" xlink:href="#$type" /></g>';

  return slice + sign;
}

/// Draw the degree ring (1° tick marks around the zodiac ring edge).
/// Draw the degree ring (5° tick marks around the zodiac ring edge).
///
/// Matches Python: 72 ticks at 5° intervals, stroke-opacity .9.
String drawDegreeRing(double r, double c1, double seventhHouseDegreeUt, String strokeColor) {
  final sb = StringBuffer();
  sb.write('<g id="degreeRing">');
  for (int i = 0; i < 72; i++) {
    double offset = (i * 5.0) - seventhHouseDegreeUt;
    if (offset < 0) offset += 360.0;
    if (offset > 360) offset -= 360.0;

    final x1 = sliceToX(0, r - c1, offset) + c1;
    final y1 = sliceToY(0, r - c1, offset) + c1;
    final x2 = sliceToX(0, r + 2 - c1, offset) - 2 + c1;
    final y2 = sliceToY(0, r + 2 - c1, offset) - 2 + c1;

    sb.write(
      '<line x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
      'style="stroke: $strokeColor; stroke-width: 1px; stroke-opacity:.9;"/>',
    );
  }
  sb.write('</g>');
  return sb.toString();
}

/// Draw the transit ring degree steps (for dual charts).
String drawTransitRingDegreeSteps(double r, double seventhHouseDegreeUt) {
  final sb = StringBuffer();
  sb.write('<g id="transitRingDegreeSteps">');
  for (int i = 0; i < 72; i++) {
    double offset = (i * 5).toDouble() - seventhHouseDegreeUt;
    if (offset < 0) {
      offset += 360.0;
    } else if (offset > 360) {
      offset -= 360.0;
    }
    final x1 = sliceToX(0, r, offset);
    final y1 = sliceToY(0, r, offset);
    final x2 = sliceToX(0, r + 2, offset) - 2;
    final y2 = sliceToY(0, r + 2, offset) - 2;

    sb.write(
      '<line x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
      'style="stroke: #F00; stroke-width: 1px; stroke-opacity:.9;"/>',
    );
  }
  sb.write('</g>');
  return sb.toString();
}

/// Draw the background circle.
String drawBackgroundCircle(double r, String fillColor, String strokeColor) {
  return '<circle cx="$r" cy="$r" r="$r" '
      'style="fill: $fillColor; stroke: $strokeColor; stroke-width: 1px;" />';
}

/// Draw the first (outermost structural) circle.
String drawFirstCircle(double r, String strokeColor, String chartType, double firstCircleRadius) {
  final double radius;
  if (chartType == 'Natal') {
    radius = r - firstCircleRadius;
    return '<circle cx="$r" cy="$r" r="$radius" '
        'style="fill: none; stroke: $strokeColor; stroke-width: 1px; " />';
  } else {
    radius = r;
    return '<circle cx="$r" cy="$r" r="$radius" '
        'style="fill: none; stroke: $strokeColor; stroke-width: 1px; stroke-opacity:.4;" />';
  }
}

/// Draw the second (zodiac boundary) circle.
String drawSecondCircle(double r, String strokeColor, String fillColor, String chartType, double secondCircleRadius) {
  final double radius;
  final String fillOpacity;
  if (chartType == 'Natal') {
    radius = r - secondCircleRadius;
    fillOpacity = '.2';
  } else {
    radius = r - 72.0;
    fillOpacity = '.4';
  }
  return '<circle cx="$r" cy="$r" r="$radius" '
      'style="fill: $fillColor; fill-opacity:$fillOpacity; stroke: $strokeColor; stroke-opacity:.4; stroke-width: 1px" />';
}

/// Draw the third (innermost) circle.
String drawThirdCircle(double r, String strokeColor, String fillColor, String chartType, double thirdCircleRadius) {
  final double radius = r - thirdCircleRadius;
  return '<circle cx="$r" cy="$r" r="$radius" '
      'style="fill: $fillColor; fill-opacity:.8; stroke: $strokeColor; stroke-width: 1px" />';
}

/// Draw the transit ring (outer ring for dual-wheel charts).
String drawTransitRing(double r, String fillColor, String strokeColor) {
  final double radius = r + 36.0;
  return '<circle cx="$r" cy="$r" r="$radius" '
      'style="fill: $fillColor; stroke: $strokeColor; stroke-width: 1px;"/>';
}

/// Draw house cusps and house numbers on the wheel.
///
/// Matches Python draw_houses_cusps_and_text_number exactly.
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
  const int xr = 12;

  for (int i = 0; i < xr; i++) {
    // Determine offsets based on chart type
    final double dropin;
    final double roff;
    final double? tRoff;
    if (chartType == 'Transit' || chartType == 'Synastry' || chartType == 'DualReturnChart') {
      dropin = 160;
      roff = 72;
      tRoff = 36;
    } else {
      dropin = c3;
      roff = c1;
      tRoff = null;
    }

    // Calculate the offset for the current house cusp
    final offset = (firstSubjectHousesList[xr ~/ 2]['abs_pos'] as double) / -1.0 + (firstSubjectHousesList[i]['abs_pos'] as double);

    // Calculate the coordinates for the house cusp lines
    final x1 = sliceToX(0, r - dropin, offset) + dropin;
    final y1 = sliceToY(0, r - dropin, offset) + dropin;
    final x2 = sliceToX(0, r - roff, offset) + roff;
    final y2 = sliceToY(0, r - roff, offset) + roff;

    // Calculate the text offset for the house number
    final nextIndex = (i + 1) % xr;
    final textOffset = offset + degreeDiff(firstSubjectHousesList[nextIndex]['abs_pos'] as double, firstSubjectHousesList[i]['abs_pos'] as double) / 2;

    // Determine the line color based on the house index
    String linecolor;
    if (i == 0) {
      linecolor = firstHouseColor;
    } else if (i == 9) {
      linecolor = tenthHouseColor;
    } else if (i == 6) {
      linecolor = seventhHouseColor;
    } else if (i == 3) {
      linecolor = fourthHouseColor;
    } else {
      linecolor = standardHouseCuspColor;
    }

    // Draw transit cusps for dual-chart types
    if ((chartType == 'Transit' || chartType == 'Synastry' || chartType == 'DualReturnChart') &&
        secondSubjectHousesList != null &&
        transitHouseCuspColor != null &&
        tRoff != null) {
      final zeropoint = 360.0 - (firstSubjectHousesList[6]['abs_pos'] as double);
      final tOffset = (zeropoint + (secondSubjectHousesList[i]['abs_pos'] as double)) % 360.0;

      final tX1 = sliceToX(0, r - tRoff, tOffset) + tRoff;
      final tY1 = sliceToY(0, r - tRoff, tOffset) + tRoff;
      final tX2 = sliceToX(0, r, tOffset);
      final tY2 = sliceToY(0, r, tOffset);

      final tTextOffset = tOffset + degreeDiff(secondSubjectHousesList[nextIndex]['abs_pos'] as double, secondSubjectHousesList[i]['abs_pos'] as double) / 2;
      final tLinecolor = (i == 0 || i == 9 || i == 6 || i == 3) ? linecolor : transitHouseCuspColor;
      final xtext = sliceToX(0, r - 8, tTextOffset) + 8;
      final ytext = sliceToY(0, r - 8, tTextOffset) + 8;

      final fillOpacity = chartType == 'Transit' ? '0' : '.4';
      sb.write('<g kr:node="HouseNumber">');
      sb.write(
        '<text style="fill: var(--kerykeion-chart-color-house-number); fill-opacity: $fillOpacity; font-size: 14px">'
        '<tspan x="${xtext - 3}" y="${ytext + 3}">${i + 1}</tspan></text>',
      );
      sb.write('</g>');

      final strokeOpacity = chartType == 'Transit' ? '0' : '.3';
      sb.write(
        '<g kr:node="Cusp" kr:absoluteposition="${secondSubjectHousesList[i]['abs_pos']}" '
        'kr:signposition="${secondSubjectHousesList[i]['position']}" '
        'kr:sing="${secondSubjectHousesList[i]['sign']}" '
        'kr:slug="${secondSubjectHousesList[i]['name']}">',
      );
      sb.write(
        "<line x1='$tX1' y1='$tY1' x2='$tX2' y2='$tY2' "
        "style='stroke: $tLinecolor; stroke-width: 1px; stroke-opacity:$strokeOpacity;'/>",
      );
      sb.write('</g>');
    }

    // Adjust dropin for house number text
    double textDropin;
    if (externalView) {
      textDropin = 100;
    } else if (chartType == 'Transit' || chartType == 'Synastry' || chartType == 'DualReturnChart') {
      textDropin = 84;
    } else {
      textDropin = 48;
    }
    final xtext = sliceToX(0, r - textDropin, textOffset) + textDropin;
    final ytext = sliceToY(0, r - textDropin, textOffset) + textDropin;

    // Add the house cusp line
    sb.write(
      '<g kr:node="Cusp" kr:absoluteposition="${firstSubjectHousesList[i]['abs_pos']}" '
      'kr:signposition="${firstSubjectHousesList[i]['position']}" '
      'kr:sing="${firstSubjectHousesList[i]['sign']}" '
      'kr:slug="${firstSubjectHousesList[i]['name']}">',
    );
    sb.write(
      '<line x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
      'style="stroke: $linecolor; stroke-width: 1px; stroke-dasharray:3,2; stroke-opacity:.4;"/>',
    );
    sb.write('</g>');

    // Add the house number text
    sb.write('<g kr:node="HouseNumber">');
    sb.write(
      '<text style="fill: var(--kerykeion-chart-color-house-number); fill-opacity: .6; font-size: 14px">'
      '<tspan x="${xtext - 3}" y="${ytext + 3}">${i + 1}</tspan></text>',
    );
    sb.write('</g>');
  }

  return sb.toString();
}

/// Draw an aspect line between two planets.
///
/// Matches Python draw_aspect_line exactly.
String drawAspectLine({
  required double r,
  required double ar,
  required Map<String, dynamic> aspect,
  required String color,
  required double seventhHouseDegreeUt,
  bool showAspectIcon = true,
  List<List<double>>? renderedIconPositions,
  double iconCollisionThreshold = 16.0,
}) {
  final double firstOffset = (seventhHouseDegreeUt / -1.0) + (aspect['p1_abs_pos'] as double);
  final x1 = sliceToX(0, ar, firstOffset) + (r - ar);
  final y1 = sliceToY(0, ar, firstOffset) + (r - ar);

  final double secondOffset = (seventhHouseDegreeUt / -1.0) + (aspect['p2_abs_pos'] as double);
  final x2 = sliceToX(0, ar, secondOffset) + (r - ar);
  final y2 = sliceToY(0, ar, secondOffset) + (r - ar);

  final sb = StringBuffer();

  // Build aspect icon SVG if enabled
  String aspectIconSvg = '';
  if (showAspectIcon) {
    double midX, midY;
    final int aspectDegrees = aspect['aspect_degrees'] as int;

    if (aspectDegrees == 0) {
      // Conjunction: place on same angle at slightly larger radius
      final p1Rad = (aspect['p1_abs_pos'] as double) * math.pi / 180.0;
      final p2Rad = (aspect['p2_abs_pos'] as double) * math.pi / 180.0;
      final avgSin = (math.sin(p1Rad) + math.sin(p2Rad)) / 2.0;
      final avgCos = (math.cos(p1Rad) + math.cos(p2Rad)) / 2.0;
      final avgPos = (math.atan2(avgSin, avgCos) * 180.0 / math.pi) % 360.0;

      final offset = (seventhHouseDegreeUt / -1.0) + avgPos;
      final iconRadius = ar + 4;
      midX = sliceToX(0, iconRadius, offset) + (r - iconRadius);
      midY = sliceToY(0, iconRadius, offset) + (r - iconRadius);
    } else {
      midX = (x1 + x2) / 2.0;
      midY = (y1 + y2) / 2.0;
    }

    bool shouldRenderIcon = true;
    if (renderedIconPositions != null) {
      for (final pos in renderedIconPositions) {
        if (pos[2].toInt() == aspectDegrees) {
          final distance = math.sqrt(math.pow(midX - pos[0], 2) + math.pow(midY - pos[1], 2));
          if (distance < iconCollisionThreshold) {
            shouldRenderIcon = false;
            break;
          }
        }
      }
    }

    if (shouldRenderIcon) {
      const iconOffset = 6;
      aspectIconSvg = '<use x="${midX - iconOffset}" y="${midY - iconOffset}" xlink:href="#orb$aspectDegrees" />';
      renderedIconPositions?.add([midX, midY, aspectDegrees.toDouble()]);
    }
  }

  // Aspect metadata attributes
  final aspectName = aspect['aspect'] ?? '';
  final p1Name = aspect['p1_name'] ?? '';
  final p2Name = aspect['p2_name'] ?? '';
  final p1AbsPos = aspect['p1_abs_pos'] ?? '';
  final p2AbsPos = aspect['p2_abs_pos'] ?? '';
  final orbit = aspect['orbit'] ?? '';
  final aspectDeg = aspect['aspect_degrees'] ?? '';
  final diff = aspect['diff'] ?? '';
  final movement = aspect['aspect_movement'] ?? '';

  sb.write(
    '<g kr:node="Aspect" kr:aspectname="$aspectName" '
    'kr:to="$p1Name" kr:tooriginaldegrees="$p1AbsPos" '
    'kr:from="$p2Name" kr:fromoriginaldegrees="$p2AbsPos" '
    'kr:orb="$orbit" kr:aspectdegrees="$aspectDeg" '
    'kr:planetsdiff="$diff" kr:aspectmovement="$movement">',
  );
  sb.write(
    '<line class="aspect" x1="$x1" y1="$y1" x2="$x2" y2="$y2" '
    'style="stroke: $color; stroke-width: 1; stroke-opacity: .9;"/>',
  );
  sb.write(aspectIconSvg);
  sb.write('</g>');

  return sb.toString();
}

/// Draw the triangular aspect grid for single-wheel charts.
///
/// Matches Python draw_aspect_grid exactly.
String drawAspectGrid(
  String strokeColor,
  List<Map<String, dynamic>> availablePlanets,
  List<Map<String, dynamic>> aspects, {
  int xStart = 510,
  int yStart = 468,
}) {
  final sb = StringBuffer();
  final style = 'stroke:$strokeColor; stroke-width: 1px; stroke-width: 0.5px; fill:none';
  const boxSize = 14;

  // Filter active planets
  final active = availablePlanets.where((p) => p['is_active'] == true).toList();

  // Reverse the list of active planets for the first iteration
  final reversedPlanets = active.reversed.toList();

  int x = xStart;
  int y = yStart;

  for (int index = 0; index < reversedPlanets.length; index++) {
    final planetA = reversedPlanets[index];

    // Draw the grid box for the planet
    sb.write(
      '<rect kr:node="AspectsGridRect" x="$x" y="$y" width="$boxSize" height="$boxSize" '
      'style="$style"/>',
    );
    sb.write(
      '<use transform="scale(0.4)" x="${(x + 2) * 2.5}" y="${(y + 1) * 2.5}" '
      'xlink:href="#${planetA['name']}" />',
    );

    // Update starting coordinates for next box
    x += boxSize;
    y -= boxSize;

    // Coordinates for the aspect symbols
    int xAspect = x;
    final int yAspect = y + boxSize;

    // Iterate over the remaining planets
    for (int j = index + 1; j < reversedPlanets.length; j++) {
      final planetB = reversedPlanets[j];

      // Draw the grid box for the aspect
      sb.write(
        '<rect kr:node="AspectsGridRect" x="$xAspect" y="$yAspect" width="$boxSize" height="$boxSize" '
        'style="$style"/>',
      );
      xAspect += boxSize;

      // Check for aspects between the planets
      for (final aspect in aspects) {
        if ((aspect['p1'] == planetA['id'] && aspect['p2'] == planetB['id']) || (aspect['p1'] == planetB['id'] && aspect['p2'] == planetA['id'])) {
          sb.write(
            '<use  x="${xAspect - boxSize + 1}" y="${yAspect + 1}" '
            'xlink:href="#orb${aspect['aspect_degrees']}" />',
          );
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
