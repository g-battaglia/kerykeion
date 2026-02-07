/// SVG natal chart drawer for kerykeion_dart.
///
/// Ported from Python kerykeion's `chart_drawer.py`.
/// Assembles a complete SVG astrological chart by filling the template
/// from [chart_assets.generated.dart] with computed SVG fragments from
/// [charts_utils.dart] and [draw_planets.dart].
library;

import '../types.dart';
import '../models/astrological_subject.dart';
import '../models/chart_data.dart';
import '../models/kerykeion_point.dart';
import '../models/aspect_model.dart';
import '../settings/chart_defaults.dart';

import 'chart_assets.generated.dart';
import 'charts_utils.dart';
import 'draw_planets.dart';

// =============================================================================
// CONFIGURATION DATA CLASSES
// =============================================================================

/// Visual configuration for chart dimensions.
class ChartDimensionsConfig {
  final double defaultHeight;
  final double natalWidth;
  final double fullWidth;
  final double synastryWidth;

  const ChartDimensionsConfig({this.defaultHeight = 550, this.natalWidth = 870, this.fullWidth = 1250, this.synastryWidth = 1570});
}

/// Circle radii within the chart wheel.
class CircleRadiiConfig {
  final double mainRadius;
  // For internal (Natal) view
  final double singleWheelFirstCircle;
  final double singleWheelSecondCircle;
  final double singleWheelThirdCircle;
  // For external view
  final double externalFirstCircle;
  final double externalSecondCircle;
  final double externalThirdCircle;

  const CircleRadiiConfig({
    this.mainRadius = 240,
    this.singleWheelFirstCircle = 0,
    this.singleWheelSecondCircle = 36,
    this.singleWheelThirdCircle = 120,
    this.externalFirstCircle = 56,
    this.externalSecondCircle = 92,
    this.externalThirdCircle = 112,
  });
}

/// Grid positioning for sidebar tables.
class GridPositionsConfig {
  final int mainPlanetX;
  final int mainHousesX;
  final int secondaryPlanetX;
  final int secondaryHousesX;

  const GridPositionsConfig({this.mainPlanetX = 645, this.mainHousesX = 750, this.secondaryPlanetX = 645, this.secondaryHousesX = 750});
}

// =============================================================================
// CHART THEME
// =============================================================================

/// Available chart themes.
enum ChartTheme { classic, dark, darkHighContrast, light, blackAndWhite, strawberry }

/// Resolve a [ChartTheme] to its CSS string content.
String getThemeCss(ChartTheme theme) {
  switch (theme) {
    case ChartTheme.classic:
      return chartThemeClassic;
    case ChartTheme.dark:
      return chartThemeDark;
    case ChartTheme.darkHighContrast:
      return chartThemeDarkHighContrast;
    case ChartTheme.light:
      return chartThemeLight;
    case ChartTheme.blackAndWhite:
      return chartThemeBlackAndWhite;
    case ChartTheme.strawberry:
      return chartThemeStrawberry;
  }
}

// =============================================================================
// MAIN CHART DRAWER
// =============================================================================

/// Draws an SVG natal chart from an [AstrologicalSubjectModel] and chart data.
///
/// Usage:
/// ```dart
/// final drawer = NatalChartDrawer(
///   chartData: myChartData,
///   theme: ChartTheme.classic,
/// );
/// final svgString = drawer.generateSvg();
/// ```
class NatalChartDrawer {
  // ── Inputs ──
  final SingleChartDataModel chartData;
  final ChartTheme theme;
  final bool externalView;
  final String? customCss;

  // ── Config ──
  final ChartDimensionsConfig dimensions;
  final CircleRadiiConfig radii;
  final GridPositionsConfig gridPositions;

  // ── Derived ──
  late final AstrologicalSubjectModel _subject;
  late final List<AspectModel> _aspects;
  late final List<_CelestialPointData> _activePointData;
  late final List<Map<String, dynamic>> _activePointSettings;
  late final List<Map<String, dynamic>> _housesList;

  // Circle radii shortcuts
  late final double _r; // main radius
  late final double _c1; // first circle
  late final double _c2; // second circle
  late final double _c3; // third circle

  // Key degrees
  late final double _firstHouseDeg;
  late final double _seventhHouseDeg;

  NatalChartDrawer({
    required this.chartData,
    this.theme = ChartTheme.classic,
    this.externalView = false,
    this.customCss,
    this.dimensions = const ChartDimensionsConfig(),
    this.radii = const CircleRadiiConfig(),
    this.gridPositions = const GridPositionsConfig(),
  }) {
    _subject = chartData.firstSubject;
    _aspects = chartData.aspects;
    _setupRadii();
    _collectActivePoints();
    _collectHouses();
  }

  // ── Setup ──

  void _setupRadii() {
    _r = radii.mainRadius;
    if (externalView) {
      _c1 = radii.externalFirstCircle;
      _c2 = radii.externalSecondCircle;
      _c3 = radii.externalThirdCircle;
    } else {
      _c1 = radii.singleWheelFirstCircle;
      _c2 = radii.singleWheelSecondCircle;
      _c3 = radii.singleWheelThirdCircle;
    }
  }

  void _collectActivePoints() {
    final activePoints = chartData.activePoints;
    _activePointData = [];
    _activePointSettings = [];

    for (final ap in activePoints) {
      final point = _getPoint(ap);
      if (point == null) continue;

      final setting = _findSetting(ap);
      if (setting == null) continue;

      _activePointData.add(_CelestialPointData(enumValue: ap, point: point, setting: setting));

      _activePointSettings.add({'id': setting.id, 'name': setting.name, 'color': setting.color, 'label': setting.label, 'is_active': true});
    }

    // Key degrees
    final firstHouse = _subject.firstHouse;
    final seventhHouse = _subject.seventhHouse;
    _firstHouseDeg = firstHouse.absPos;
    _seventhHouseDeg = seventhHouse.absPos;
  }

  void _collectHouses() {
    _housesList = [
      _houseMap(_subject.firstHouse),
      _houseMap(_subject.secondHouse),
      _houseMap(_subject.thirdHouse),
      _houseMap(_subject.fourthHouse),
      _houseMap(_subject.fifthHouse),
      _houseMap(_subject.sixthHouse),
      _houseMap(_subject.seventhHouse),
      _houseMap(_subject.eighthHouse),
      _houseMap(_subject.ninthHouse),
      _houseMap(_subject.tenthHouse),
      _houseMap(_subject.eleventhHouse),
      _houseMap(_subject.twelfthHouse),
    ];
  }

  // ── Public API ──

  /// Generate the complete SVG chart string.
  String generateSvg() {
    final vars = _buildTemplateDict();
    return substituteTemplate(chartSvgTemplate, vars);
  }

  // ── Template Dictionary ──

  Map<String, String> _buildTemplateDict() {
    final td = <String, String>{};

    // ── Theme CSS ──
    td['color_style_tag'] = customCss ?? getThemeCss(theme);

    // ── Dynamic height adjustment ──
    final pointCount = _activePointData.length;
    final extraPoints = (pointCount > 20) ? pointCount - 20 : 0;
    final heightDelta = extraPoints * 8.0;
    final height = dimensions.defaultHeight + heightDelta;
    final width = dimensions.natalWidth;

    // Vertical offsets — bottom-anchored elements shift by full delta,
    // top elements shift partially, capped at 80
    final topShift = heightDelta.clamp(0.0, 80.0);

    td['viewbox'] = '0 0 $width $height';
    td['background_color'] = 'var(--kerykeion-chart-color-paper-1)';
    td['paper_color_0'] = 'var(--kerykeion-chart-color-paper-0)';

    // Translate-Y offsets for each section
    td['title_translate_y'] = '0';
    td['elements_translate_y'] = topShift.toStringAsFixed(0);
    td['qualities_translate_y'] = topShift.toStringAsFixed(0);
    td['bottom_left_translate_y'] = heightDelta.toStringAsFixed(0);
    td['lunar_phase_translate_y'] = (420 + heightDelta).toStringAsFixed(0);
    td['full_wheel_translate_y'] = topShift.toStringAsFixed(0);
    td['houses_and_planets_translate_y'] = topShift.toStringAsFixed(0);
    td['aspect_grid_translate_y'] = (250 + topShift).toStringAsFixed(0);
    td['aspect_list_translate_y'] = (250 + topShift).toStringAsFixed(0);

    // ── Title ──
    td['stringTitle'] = _escapeXml(_truncateName(_subject.name, 20));

    // ── Top Left Info ──
    td['top_left_0'] = _formatLocationLine();
    td['top_left_1'] = _formatDateTimeLine();
    td['top_left_2'] = _formatZodiacTypeLine();
    td['top_left_3'] = _formatHouseSystemLine();
    td['top_left_4'] = _formatPerspectiveLine();
    td['top_left_5'] = '';

    // ── Elements / Qualities ──
    final elemDist = chartData.elementDistribution;
    final qualDist = chartData.qualityDistribution;

    td['elements_string'] = 'Elements:';
    td['fire_string'] = 'Fire: ${elemDist.firePercentage}%';
    td['earth_string'] = 'Earth: ${elemDist.earthPercentage}%';
    td['air_string'] = 'Air: ${elemDist.airPercentage}%';
    td['water_string'] = 'Water: ${elemDist.waterPercentage}%';

    td['qualities_string'] = 'Qualities:';
    td['cardinal_string'] = 'Cardinal: ${qualDist.cardinalPercentage}%';
    td['fixed_string'] = 'Fixed: ${qualDist.fixedPercentage}%';
    td['mutable_string'] = 'Mutable: ${qualDist.mutablePercentage}%';

    // ── Bottom Left Info ──
    td['bottom_left_0'] = '';
    td['bottom_left_1'] = '';
    td['bottom_left_2'] = '';
    td['bottom_left_3'] = '';
    td['bottom_left_4'] = '';

    // ── Lunar Phase ──
    td['makeLunarPhase'] = _buildLunarPhase();

    // ── Wheel Components ──
    td['background_circle'] = _buildBackgroundCircle();
    td['makeZodiac'] = _buildZodiac();
    td['first_circle'] = _buildFirstCircle();
    td['second_circle'] = _buildSecondCircle();
    td['third_circle'] = _buildThirdCircle();
    td['transitRing'] = ''; // No transit ring for natal
    td['degreeRing'] = _buildDegreeRing();
    td['makeHouses'] = _buildHouses();
    td['makePlanets'] = _buildPlanets();
    td['makeAspects'] = _buildAspects();

    // ── Grids ──
    td['makeMainPlanetGrid'] = _buildMainPlanetGrid();
    td['makeMainHousesGrid'] = _buildMainHouseGrid();
    td['makeSecondaryPlanetGrid'] = ''; // Natal only
    td['makeSecondaryHousesGrid'] = ''; // Natal only
    td['makeHouseComparisonGrid'] = ''; // Natal only

    // ── Aspect Grid ──
    td['makeAspectGrid'] = _buildAspectGrid();
    td['makeDoubleChartAspectList'] = ''; // Natal only

    return td;
  }

  // ── SVG Fragment Builders ──

  String _buildBackgroundCircle() {
    return drawBackgroundCircle(_r, 'var(--kerykeion-chart-color-paper-1)', 'var(--kerykeion-chart-color-zodiac-radix-ring-2)');
  }

  String _buildZodiac() {
    final sb = StringBuffer();
    const zodiacSigns = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];

    for (int i = 0; i < 12; i++) {
      final bgColor = 'var(--kerykeion-chart-color-zodiac-bg-$i)';
      sb.write(
        drawZodiacSlice(
          c1: _c1,
          chartType: 'Natal',
          seventhHouseDegreeUt: _seventhHouseDeg,
          num: i,
          r: _r,
          style: 'fill: $bgColor; fill-opacity: 0.3;',
          type: zodiacSigns[i],
        ),
      );
    }
    return sb.toString();
  }

  String _buildFirstCircle() {
    return drawFirstCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-0)', 'Natal', _c1);
  }

  String _buildSecondCircle() {
    return drawSecondCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-1)', 'none', 'Natal', _c2);
  }

  String _buildThirdCircle() {
    return drawThirdCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-2)', 'var(--kerykeion-chart-color-paper-1)', 'Natal', _c3);
  }

  String _buildDegreeRing() {
    return drawDegreeRing(_r, _c1, _seventhHouseDeg, 'var(--kerykeion-chart-color-paper-0)');
  }

  String _buildHouses() {
    return drawHousesCuspsAndTextNumber(
      r: _r,
      firstSubjectHousesList: _housesList,
      standardHouseCuspColor: 'var(--kerykeion-chart-color-houses-radix-line)',
      firstHouseColor: 'var(--kerykeion-chart-color-first-house)',
      tenthHouseColor: 'var(--kerykeion-chart-color-tenth-house)',
      seventhHouseColor: 'var(--kerykeion-chart-color-seventh-house)',
      fourthHouseColor: 'var(--kerykeion-chart-color-fourth-house)',
      c1: _c1,
      c3: _c3,
      chartType: 'Natal',
      externalView: externalView,
    );
  }

  String _buildPlanets() {
    final points = _activePointData
        .map(
          (d) => <String, dynamic>{
            'name': d.setting.name,
            'abs_pos': d.point.absPos,
            'position': d.point.position,
            'sign': d.point.sign.name,
            'house': d.point.house?.name ?? '',
            'retrograde': d.point.retrograde ?? false,
          },
        )
        .toList();

    return drawPlanets(
      radius: _r,
      availableCelestialPoints: points,
      availablePlanetsSettings: _activePointSettings,
      thirdCircleRadius: _c3,
      firstHouseDegreeUt: _firstHouseDeg,
      seventhHouseDegreeUt: _seventhHouseDeg,
      chartType: 'Natal',
      externalView: externalView,
      firstCircleRadius: _c1,
      secondCircleRadius: _c2,
    );
  }

  String _buildAspects() {
    final sb = StringBuffer();
    final List<List<double>> renderedPositions = [];
    final aspectRadius = _r - _c3;

    for (final aspect in _aspects) {
      // Find color from default settings
      final aspectSetting = defaultChartAspectsSettings.firstWhere((s) => s.degree == aspect.aspectDegrees, orElse: () => defaultChartAspectsSettings.first);

      sb.write(
        drawAspectLine(
          r: _r,
          ar: aspectRadius,
          aspect: {'p1_abs_pos': aspect.p1AbsPos, 'p2_abs_pos': aspect.p2AbsPos, 'aspect_degrees': aspect.aspectDegrees},
          color: aspectSetting.color,
          seventhHouseDegreeUt: _seventhHouseDeg,
          renderedIconPositions: renderedPositions,
        ),
      );
    }
    return sb.toString();
  }

  String _buildLunarPhase() {
    final lp = _subject.lunarPhase;
    if (lp == null) return '';

    final sunMoonAngle = lp.degreesBetweenSunAndMoon;
    final lat = _subject.lat ?? 0.0;
    return makeLunarPhase(sunMoonAngle, lat);
  }

  String _buildMainPlanetGrid() {
    final points = _activePointData
        .map(
          (d) => <String, dynamic>{
            'name': d.setting.name,
            'abs_pos': d.point.absPos,
            'position': d.point.position,
            'sign': d.point.sign.name,
            'house': d.point.house?.name ?? '',
            'retrograde': d.point.retrograde ?? false,
          },
        )
        .toList();

    return drawMainPlanetGrid(
      title: '',
      subjectName: '',
      celestialPoints: points,
      chartType: 'Natal',
      textColor: 'var(--kerykeion-chart-color-paper-0)',
      xPosition: gridPositions.mainPlanetX,
    );
  }

  String _buildMainHouseGrid() {
    return drawMainHouseGrid(housesList: _housesList, textColor: 'var(--kerykeion-chart-color-paper-0)', xPosition: gridPositions.mainHousesX);
  }

  String _buildAspectGrid() {
    final aspectsAsMaps = _aspects.map((a) => a.toJson()).toList();

    return drawAspectGrid('var(--kerykeion-chart-color-paper-0)', _activePointSettings, aspectsAsMaps);
  }

  // ── Helpers ──

  KerykeionPointModel? _getPoint(AstrologicalPoint ap) {
    switch (ap) {
      case AstrologicalPoint.Sun:
        return _subject.sun;
      case AstrologicalPoint.Moon:
        return _subject.moon;
      case AstrologicalPoint.Mercury:
        return _subject.mercury;
      case AstrologicalPoint.Venus:
        return _subject.venus;
      case AstrologicalPoint.Mars:
        return _subject.mars;
      case AstrologicalPoint.Jupiter:
        return _subject.jupiter;
      case AstrologicalPoint.Saturn:
        return _subject.saturn;
      case AstrologicalPoint.Uranus:
        return _subject.uranus;
      case AstrologicalPoint.Neptune:
        return _subject.neptune;
      case AstrologicalPoint.Pluto:
        return _subject.pluto;
      case AstrologicalPoint.Chiron:
        return _subject.chiron;
      case AstrologicalPoint.Mean_North_Lunar_Node:
        return _subject.meanNorthLunarNode;
      case AstrologicalPoint.True_North_Lunar_Node:
        return _subject.trueNorthLunarNode;
      case AstrologicalPoint.Mean_South_Lunar_Node:
        return _subject.meanSouthLunarNode;
      case AstrologicalPoint.True_South_Lunar_Node:
        return _subject.trueSouthLunarNode;
      case AstrologicalPoint.Mean_Lilith:
        return _subject.meanLilith;
      case AstrologicalPoint.True_Lilith:
        return _subject.trueLilith;
      case AstrologicalPoint.Ascendant:
        return _subject.ascendant;
      case AstrologicalPoint.Medium_Coeli:
        return _subject.mediumCoeli;
      case AstrologicalPoint.Descendant:
        return _subject.descendant;
      case AstrologicalPoint.Imum_Coeli:
        return _subject.imumCoeli;
      case AstrologicalPoint.Earth:
        return _subject.earth;
      case AstrologicalPoint.Pholus:
        return _subject.pholus;
      case AstrologicalPoint.Ceres:
        return _subject.ceres;
      case AstrologicalPoint.Pallas:
        return _subject.pallas;
      case AstrologicalPoint.Juno:
        return _subject.juno;
      case AstrologicalPoint.Vesta:
        return _subject.vesta;
      case AstrologicalPoint.Eris:
        return _subject.eris;
      case AstrologicalPoint.Sedna:
        return _subject.sedna;
      case AstrologicalPoint.Haumea:
        return _subject.haumea;
      case AstrologicalPoint.Makemake:
        return _subject.makemake;
      case AstrologicalPoint.Ixion:
        return _subject.ixion;
      case AstrologicalPoint.Orcus:
        return _subject.orcus;
      case AstrologicalPoint.Quaoar:
        return _subject.quaoar;
      case AstrologicalPoint.Regulus:
        return _subject.regulus;
      case AstrologicalPoint.Spica:
        return _subject.spica;
      case AstrologicalPoint.Vertex:
        return _subject.vertex;
      case AstrologicalPoint.Anti_Vertex:
        return _subject.antiVertex;
      case AstrologicalPoint.Pars_Fortunae:
        return _subject.parsFortunae;
      case AstrologicalPoint.Pars_Spiritus:
        return _subject.parsSpiritus;
      case AstrologicalPoint.Pars_Amoris:
        return _subject.parsAmoris;
      case AstrologicalPoint.Pars_Fidei:
        return _subject.parsFidei;
    }
  }

  CelestialPointSetting? _findSetting(AstrologicalPoint ap) {
    final name = ap.name;
    try {
      return defaultCelestialPointsSettings.firstWhere((s) => s.name == name);
    } catch (_) {
      return null;
    }
  }

  static Map<String, dynamic> _houseMap(KerykeionPointModel h) {
    return {'abs_pos': h.absPos, 'position': h.position, 'sign': h.sign.name};
  }

  String _formatLocationLine() {
    final city = _subject.city ?? '';
    final nation = _subject.nation ?? '';
    final lat = _subject.lat;
    final lng = _subject.lng;

    final parts = <String>[];
    if (city.isNotEmpty) parts.add(city);
    if (nation.isNotEmpty) parts.add(nation);

    if (lat != null && lng != null) {
      parts.add(convertLatitudeCoordinateToString(lat, 'N', 'S'));
      parts.add(convertLongitudeCoordinateToString(lng, 'E', 'W'));
    }

    return _escapeXml(parts.join(', '));
  }

  String _formatDateTimeLine() {
    final dt = _subject.isoFormattedLocalDatetime ?? '';
    final tz = _subject.tzStr ?? '';
    if (dt.isEmpty) return '';
    return _escapeXml('$dt ($tz)');
  }

  String _formatZodiacTypeLine() {
    final zt = _subject.zodiacType?.name ?? 'Tropical';
    return 'Zodiac: $zt';
  }

  String _formatHouseSystemLine() {
    final hs = _subject.housesSystemName ?? _subject.housesSystemIdentifier.name;
    return 'Houses: $hs';
  }

  String _formatPerspectiveLine() {
    final p = _subject.perspectiveType.name.replaceAll('_', ' ');
    return 'Perspective: $p';
  }

  static String _truncateName(String name, int maxLen) {
    if (name.length <= maxLen) return name;
    return '${name.substring(0, maxLen - 1)}…';
  }

  static String _escapeXml(String s) {
    return s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&apos;');
  }
}

// =============================================================================
// INTERNAL DATA
// =============================================================================

/// Internal holder for a celestial point paired with its setting.
class _CelestialPointData {
  final AstrologicalPoint enumValue;
  final KerykeionPointModel point;
  final CelestialPointSetting setting;

  const _CelestialPointData({required this.enumValue, required this.point, required this.setting});
}

// ChartType is defined in types.dart — use that enum throughout.
