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

  const GridPositionsConfig({this.mainPlanetX = 645, this.mainHousesX = 750, this.secondaryPlanetX = 910, this.secondaryHousesX = 1015});
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
    const verticalPaddingTop = 15;
    const verticalPaddingBottom = 15;

    final pointCount = _activePointData.length;
    final extraPoints = (pointCount > 20) ? pointCount - 20 : 0;
    final heightDelta = extraPoints * 8.0;
    final height = dimensions.defaultHeight + heightDelta;
    // Python uses 890 for natal (main_radius*2 + side grids width)
    final width = 890;

    // Vertical offsets
    final viewboxHeight = height.toInt() + verticalPaddingTop + verticalPaddingBottom;

    td['viewbox'] = '0 -$verticalPaddingTop $width $viewboxHeight';
    td['background_color'] = 'var(--kerykeion-chart-color-paper-1)';
    td['paper_color_0'] = 'var(--kerykeion-chart-color-paper-0)';

    // Translate-Y offsets for each section — defaults match Python
    td['title_translate_y'] = '0';
    td['elements_translate_y'] = '0';
    td['qualities_translate_y'] = '0';
    td['bottom_left_translate_y'] = heightDelta.toStringAsFixed(0);
    td['lunar_phase_translate_y'] = (518 + heightDelta).toStringAsFixed(0);
    td['full_wheel_translate_y'] = '50';
    td['houses_and_planets_translate_y'] = '0';
    td['aspect_grid_translate_y'] = '50';
    td['aspect_list_translate_y'] = '50';

    // ── Title ──
    td['stringTitle'] = '${_escapeXml(_truncateName(_subject.name, 20))} - Birth Chart';

    // ── Top Left Info ──
    td['top_left_0'] = 'Location:';
    td['top_left_1'] = _formatCityNation();
    td['top_left_2'] = _formatLatitude();
    td['top_left_3'] = _formatLongitude();
    td['top_left_4'] = _formatDateTimeWithTimezone();
    td['top_left_5'] = _formatDayOfWeek();

    // ── Elements / Qualities ──
    final elemDist = chartData.elementDistribution;
    final qualDist = chartData.qualityDistribution;

    td['elements_string'] = 'Elements:';
    td['fire_string'] = 'Fire ${elemDist.firePercentage}%';
    td['earth_string'] = 'Earth ${elemDist.earthPercentage}%';
    td['air_string'] = 'Air ${elemDist.airPercentage}%';
    td['water_string'] = 'Water ${elemDist.waterPercentage}%';

    td['qualities_string'] = 'Qualities:';
    td['cardinal_string'] = 'Cardinal ${qualDist.cardinalPercentage}%';
    td['fixed_string'] = 'Fixed ${qualDist.fixedPercentage}%';
    td['mutable_string'] = 'Mutable ${qualDist.mutablePercentage}%';

    // ── Bottom Left Info ──
    td['bottom_left_0'] = _formatZodiacTypeLine();
    td['bottom_left_1'] = _formatDomificationLine();
    td['bottom_left_2'] = _formatLunationDay();
    td['bottom_left_3'] = _formatLunarPhaseName();
    td['bottom_left_4'] = _formatPerspectiveLine();

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
          style: 'fill: $bgColor; fill-opacity: 0.5;',
          type: zodiacSigns[i],
        ),
      );
    }
    return sb.toString();
  }

  String _buildFirstCircle() {
    return drawFirstCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-2)', 'Natal', _c1);
  }

  String _buildSecondCircle() {
    return drawSecondCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-1)', 'var(--kerykeion-chart-color-paper-1)', 'Natal', _c2);
  }

  String _buildThirdCircle() {
    return drawThirdCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-0)', 'var(--kerykeion-chart-color-paper-1)', 'Natal', _c3);
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
          aspect: aspect.toJson(),
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

  String _formatCityNation() {
    final city = _subject.city ?? '';
    final nation = _subject.nation ?? '';
    final parts = <String>[];
    if (city.isNotEmpty) parts.add(city);
    if (nation.isNotEmpty) parts.add(nation);
    return _escapeXml(parts.join(', '));
  }

  String _formatLatitude() {
    final lat = _subject.lat;
    if (lat == null) return '';
    return 'Latitude: ${convertLatitudeCoordinateToString(lat, 'North', 'South')}';
  }

  String _formatLongitude() {
    final lng = _subject.lng;
    if (lng == null) return '';
    return 'Longitude: ${convertLongitudeCoordinateToString(lng, 'East', 'West')}';
  }

  String _formatDateTimeWithTimezone() {
    // Python output format: '1990-06-15 14:30 [+09:00]'
    // Input iso format: '1990-06-15T14:30:00+09:00'
    final iso = _subject.isoFormattedLocalDatetime ?? '';
    if (iso.isEmpty) return '';

    // Parse the ISO datetime to extract parts
    final dt = DateTime.tryParse(iso);
    if (dt == null) return iso;

    // Extract timezone offset from ISO string
    String tzOffset = '';
    final tzMatch = RegExp(r'[+-]\d{2}:\d{2}$').firstMatch(iso);
    if (tzMatch != null) {
      tzOffset = tzMatch.group(0)!;
    }

    final dateStr =
        '${dt.year.toString().padLeft(4, '0')}-'
        '${dt.month.toString().padLeft(2, '0')}-'
        '${dt.day.toString().padLeft(2, '0')}';
    final timeStr =
        '${dt.hour.toString().padLeft(2, '0')}:'
        '${dt.minute.toString().padLeft(2, '0')}';

    if (tzOffset.isNotEmpty) {
      return '$dateStr $timeStr [$tzOffset]';
    }
    return '$dateStr $timeStr';
  }

  String _formatDayOfWeek() {
    final dow = _subject.dayOfWeek ?? '';
    if (dow.isEmpty) return '';
    return 'Day of Week: $dow';
  }

  String _formatZodiacTypeLine() {
    final zt = _subject.zodiacType?.name ?? 'Tropical';
    return 'Zodiac: $zt';
  }

  String _formatDomificationLine() {
    final hs = _subject.housesSystemName ?? _subject.housesSystemIdentifier.name;
    return 'Domification: $hs';
  }

  String _formatLunationDay() {
    final lp = _subject.lunarPhase;
    if (lp == null) return '';
    return 'Lunation Day: ${lp.moonPhase}';
  }

  String _formatLunarPhaseName() {
    final lp = _subject.lunarPhase;
    if (lp == null) return '';
    final name = lp.moonPhaseName.name.replaceAll('_', ' ');
    return 'Lunar Phase: $name';
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

// =============================================================================
// DUAL-CHART DRAWER
// =============================================================================

/// Draws SVG dual-wheel charts (Transit, Synastry, DualReturn).
///
/// Usage:
/// ```dart
/// final drawer = DualChartDrawer(
///   chartData: myDualChartData,
///   theme: ChartTheme.classic,
/// );
/// final svgString = drawer.generateSvg();
/// ```
class DualChartDrawer {
  // ── Inputs ──
  final DualChartDataModel chartData;
  final ChartTheme theme;
  final String? customCss;

  /// How to display aspects: 'list' (default) or 'grid'.
  final String doubleChartAspectGridType;

  // ── Config ──
  final ChartDimensionsConfig dimensions;
  final CircleRadiiConfig radii;
  final GridPositionsConfig gridPositions;

  // ── Derived ──
  late final AstrologicalSubjectModel _firstSubject;
  late final AstrologicalSubjectModel _secondSubject;
  late final String _chartType;
  late final List<AspectModel> _aspects;
  late final List<_CelestialPointData> _firstActivePointData;
  late final List<_CelestialPointData> _secondActivePointData;
  late final List<Map<String, dynamic>> _activePointSettings;
  late final List<Map<String, dynamic>> _firstHousesList;
  late final List<Map<String, dynamic>> _secondHousesList;

  // Circle radii
  late final double _r;
  late final double _c1;
  late final double _c2;
  late final double _c3;

  // Key degrees
  late final double _firstHouseDeg;
  late final double _seventhHouseDeg;

  DualChartDrawer({
    required this.chartData,
    this.theme = ChartTheme.classic,
    this.customCss,
    this.doubleChartAspectGridType = 'list',
    this.dimensions = const ChartDimensionsConfig(),
    this.radii = const CircleRadiiConfig(),
    this.gridPositions = const GridPositionsConfig(),
  }) {
    _firstSubject = chartData.firstSubject;
    _secondSubject = chartData.secondSubject;
    _chartType = chartData.chartType;
    _aspects = chartData.aspects;

    // Dual-wheel uses c1=0 (no inner offset), c3=120 for aspect inner ring
    _r = radii.mainRadius;
    _c1 = 0; // Transit/Synastry always use 0 for first circle
    _c2 = radii.singleWheelSecondCircle;
    _c3 = radii.singleWheelThirdCircle;

    _firstHouseDeg = _firstSubject.firstHouse.absPos;
    _seventhHouseDeg = _firstSubject.seventhHouse.absPos;

    _collectActivePoints();
    _collectHouses();
  }

  void _collectActivePoints() {
    final activePoints = chartData.activePoints;
    _firstActivePointData = [];
    _secondActivePointData = [];
    _activePointSettings = [];

    for (final ap in activePoints) {
      final firstPoint = _getPointFromSubject(_firstSubject, ap);
      final secondPoint = _getPointFromSubject(_secondSubject, ap);

      final setting = _findSetting(ap);
      if (setting == null) continue;

      if (firstPoint != null) {
        _firstActivePointData.add(_CelestialPointData(enumValue: ap, point: firstPoint, setting: setting));
      }
      if (secondPoint != null) {
        _secondActivePointData.add(_CelestialPointData(enumValue: ap, point: secondPoint, setting: setting));
      }

      _activePointSettings.add({'id': setting.id, 'name': setting.name, 'color': setting.color, 'label': setting.label, 'is_active': true});
    }
  }

  void _collectHouses() {
    _firstHousesList = _buildHousesList(_firstSubject);
    _secondHousesList = _buildHousesList(_secondSubject);
  }

  static List<Map<String, dynamic>> _buildHousesList(AstrologicalSubjectModel s) {
    return [
      NatalChartDrawer._houseMap(s.firstHouse),
      NatalChartDrawer._houseMap(s.secondHouse),
      NatalChartDrawer._houseMap(s.thirdHouse),
      NatalChartDrawer._houseMap(s.fourthHouse),
      NatalChartDrawer._houseMap(s.fifthHouse),
      NatalChartDrawer._houseMap(s.sixthHouse),
      NatalChartDrawer._houseMap(s.seventhHouse),
      NatalChartDrawer._houseMap(s.eighthHouse),
      NatalChartDrawer._houseMap(s.ninthHouse),
      NatalChartDrawer._houseMap(s.tenthHouse),
      NatalChartDrawer._houseMap(s.eleventhHouse),
      NatalChartDrawer._houseMap(s.twelfthHouse),
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

    // ── Dynamic sizing ──
    const verticalPaddingTop = 15;
    const verticalPaddingBottom = 15;

    final pointCount = _firstActivePointData.length;
    final extraPoints = (pointCount > 20) ? pointCount - 20 : 0;
    final heightDelta = extraPoints * 8.0;
    final height = dimensions.defaultHeight + heightDelta;

    // Dual-wheel charts are wider
    double width;
    if (_chartType == 'Synastry') {
      width = dimensions.synastryWidth;
    } else {
      width = dimensions.fullWidth;
    }

    final viewboxHeight = height.toInt() + verticalPaddingTop + verticalPaddingBottom;
    td['viewbox'] = '0 -$verticalPaddingTop ${width.toInt()} $viewboxHeight';
    td['background_color'] = 'var(--kerykeion-chart-color-paper-1)';
    td['paper_color_0'] = 'var(--kerykeion-chart-color-paper-0)';

    // Translate-Y offsets
    td['title_translate_y'] = '0';
    td['elements_translate_y'] = '0';
    td['qualities_translate_y'] = '0';
    td['bottom_left_translate_y'] = heightDelta.toStringAsFixed(0);
    td['lunar_phase_translate_y'] = (518 + heightDelta).toStringAsFixed(0);
    td['full_wheel_translate_y'] = '50';
    td['houses_and_planets_translate_y'] = '0';
    td['aspect_grid_translate_y'] = '50';
    td['aspect_list_translate_y'] = '50';

    // ── Title ──
    td['stringTitle'] = '${NatalChartDrawer._escapeXml(NatalChartDrawer._truncateName(_firstSubject.name, 20))} - $_chartType Chart';

    // ── Top Left Info ── (varies by chart type)
    _setupTopLeftInfo(td);

    // ── Elements / Qualities ──
    if (_chartType == 'Transit') {
      // Transit charts don't show element/quality distributions
      td['elements_string'] = '';
      td['fire_string'] = '';
      td['earth_string'] = '';
      td['air_string'] = '';
      td['water_string'] = '';
      td['qualities_string'] = '';
      td['cardinal_string'] = '';
      td['fixed_string'] = '';
      td['mutable_string'] = '';
    } else {
      final elemDist = chartData.elementDistribution;
      final qualDist = chartData.qualityDistribution;
      td['elements_string'] = 'Elements:';
      td['fire_string'] = 'Fire ${elemDist.firePercentage}%';
      td['earth_string'] = 'Earth ${elemDist.earthPercentage}%';
      td['air_string'] = 'Air ${elemDist.airPercentage}%';
      td['water_string'] = 'Water ${elemDist.waterPercentage}%';
      td['qualities_string'] = 'Qualities:';
      td['cardinal_string'] = 'Cardinal ${qualDist.cardinalPercentage}%';
      td['fixed_string'] = 'Fixed ${qualDist.fixedPercentage}%';
      td['mutable_string'] = 'Mutable ${qualDist.mutablePercentage}%';
    }

    // ── Bottom Left Info ──
    _setupBottomLeftInfo(td);

    // ── Lunar Phase ──
    td['makeLunarPhase'] = _buildLunarPhase();

    // ── Wheel Components (transit-style circles) ──
    td['background_circle'] = drawBackgroundCircle(_r, 'var(--kerykeion-chart-color-paper-1)', 'var(--kerykeion-chart-color-paper-1)');
    td['makeZodiac'] = _buildZodiac();
    td['transitRing'] = drawTransitRing(_r, 'var(--kerykeion-chart-color-paper-1)', 'var(--kerykeion-chart-color-zodiac-transit-ring-3)');
    td['degreeRing'] = drawTransitRingDegreeSteps(_r, _seventhHouseDeg);
    td['first_circle'] = drawFirstCircle(_r, 'var(--kerykeion-chart-color-zodiac-transit-ring-2)', _chartType, 0);
    td['second_circle'] = drawSecondCircle(_r, 'var(--kerykeion-chart-color-zodiac-transit-ring-1)', 'var(--kerykeion-chart-color-paper-1)', _chartType, _c2);
    td['third_circle'] = drawThirdCircle(_r, 'var(--kerykeion-chart-color-zodiac-transit-ring-0)', 'var(--kerykeion-chart-color-paper-1)', _chartType, _c3);

    // ── Houses (dual-wheel) ──
    td['makeHouses'] = _buildDualHouses();

    // ── Planets (dual-wheel) ──
    td['makePlanets'] = _buildDualPlanets();

    // ── Aspects ──
    td['makeAspects'] = _buildAspectLines();

    // ── Grids ──
    _setupGrids(td);

    // ── Aspect Grid / List ──
    _setupAspects(td);

    // ── House comparison (Synastry only) ──
    td['makeHouseComparisonGrid'] = '';

    return td;
  }

  // ── Chart-type-specific info sections ──

  void _setupTopLeftInfo(Map<String, String> td) {
    final firstDt = _formatDateTimeForSubject(_firstSubject);
    final secondDt = _formatDateTimeForSubject(_secondSubject);
    final firstPlace = _formatPlaceForSubject(_firstSubject);
    final secondPlace = _formatPlaceForSubject(_secondSubject);

    switch (_chartType) {
      case 'Transit':
        td['top_left_0'] = 'Natal: $firstDt';
        td['top_left_1'] = firstPlace;
        td['top_left_2'] = _formatCoordsForSubject(_firstSubject);
        td['top_left_3'] = 'Transit: $secondDt';
        td['top_left_4'] = secondPlace;
        td['top_left_5'] = _formatCoordsForSubject(_secondSubject);
        break;

      case 'Synastry':
        td['top_left_0'] = '${_firstSubject.name}:';
        td['top_left_1'] = firstPlace;
        td['top_left_2'] = firstDt;
        td['top_left_3'] = '${_secondSubject.name}:';
        td['top_left_4'] = secondPlace;
        td['top_left_5'] = secondDt;
        break;

      default: // DualReturnChart or other
        td['top_left_0'] = '$_chartType:';
        td['top_left_1'] = secondDt;
        td['top_left_2'] = _formatCoordsForSubject(_secondSubject);
        td['top_left_3'] = _firstSubject.name;
        td['top_left_4'] = firstDt;
        td['top_left_5'] = _formatCoordsForSubject(_firstSubject);
        break;
    }
  }

  void _setupBottomLeftInfo(Map<String, String> td) {
    final zt = _firstSubject.zodiacType?.name ?? 'Tropical';
    td['bottom_left_0'] = 'Zodiac: $zt';

    final hs = _firstSubject.housesSystemName ?? _firstSubject.housesSystemIdentifier.name;
    td['bottom_left_1'] = 'Domification: $hs';

    // Lunar phase from second subject for transit, first for synastry
    final phaseSubject = (_chartType == 'Transit') ? _secondSubject : _firstSubject;
    final lp = phaseSubject.lunarPhase;
    if (lp != null) {
      td['bottom_left_2'] = 'Lunation Day: ${lp.moonPhase}';
      td['bottom_left_3'] = 'Lunar Phase: ${lp.moonPhaseName.name.replaceAll('_', ' ')}';
    } else {
      td['bottom_left_2'] = '';
      td['bottom_left_3'] = '';
    }

    final p = _firstSubject.perspectiveType.name.replaceAll('_', ' ');
    td['bottom_left_4'] = 'Perspective: $p';
  }

  void _setupGrids(Map<String, String> td) {
    // Main planet grid (first subject / inner wheel)
    final firstPoints = _firstActivePointData
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

    final firstLabel = NatalChartDrawer._truncateName(_firstSubject.name, 18);
    td['makeMainPlanetGrid'] = drawMainPlanetGrid(
      title: '',
      subjectName: '$firstLabel (Inner Wheel)',
      celestialPoints: firstPoints,
      chartType: _chartType,
      textColor: 'var(--kerykeion-chart-color-paper-0)',
      xPosition: gridPositions.mainPlanetX,
    );

    // Secondary planet grid (second subject / outer wheel)
    final secondPoints = _secondActivePointData
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

    String secondLabel;
    if (_chartType == 'Transit') {
      secondLabel = 'Transit (Outer Wheel)';
    } else {
      secondLabel = '${NatalChartDrawer._truncateName(_secondSubject.name, 18)} (Outer Wheel)';
    }

    td['makeSecondaryPlanetGrid'] = drawSecondaryPlanetGrid(
      title: '',
      subjectName: secondLabel,
      celestialPoints: secondPoints,
      chartType: _chartType,
      textColor: 'var(--kerykeion-chart-color-paper-0)',
      xPosition: gridPositions.secondaryPlanetX,
    );

    // House grids
    td['makeMainHousesGrid'] = drawMainHouseGrid(
      housesList: _firstHousesList,
      textColor: 'var(--kerykeion-chart-color-paper-0)',
      xPosition: gridPositions.mainHousesX,
    );

    if (_chartType == 'Synastry') {
      td['makeSecondaryHousesGrid'] = drawSecondaryHouseGrid(
        housesList: _secondHousesList,
        textColor: 'var(--kerykeion-chart-color-paper-0)',
        xPosition: gridPositions.secondaryHousesX,
      );
    } else {
      td['makeSecondaryHousesGrid'] = '';
    }
  }

  void _setupAspects(Map<String, String> td) {
    final aspectsAsMaps = _aspects.map((a) => a.toJson()).toList();

    if (doubleChartAspectGridType == 'list') {
      String title;
      if (_chartType == 'Transit') {
        title = '${_firstSubject.name} - Transit Aspects';
      } else if (_chartType == 'Synastry') {
        title = '${_firstSubject.name} - ${_secondSubject.name} Synastry Aspects';
      } else {
        title = 'Natal to Return Aspects';
      }

      td['makeAspectGrid'] = '';
      td['makeDoubleChartAspectList'] = drawTransitAspectList(
        title,
        aspectsAsMaps,
        _activePointSettings,
        defaultChartAspectsSettings.map((s) => {'name': s.name, 'degree': s.degree, 'color': s.color}).toList(),
        chartHeight: dimensions.defaultHeight.toDouble(),
      );
    } else {
      td['makeAspectGrid'] = '';
      td['makeDoubleChartAspectList'] = drawTransitAspectGrid(
        'var(--kerykeion-chart-color-paper-0)',
        _activePointSettings,
        aspectsAsMaps,
        xIndent: 600,
        yIndent: 520,
      );
    }
  }

  // ── SVG Fragment Builders ──

  String _buildZodiac() {
    final sb = StringBuffer();
    const zodiacSigns = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];

    for (int i = 0; i < 12; i++) {
      final bgColor = 'var(--kerykeion-chart-color-zodiac-bg-$i)';
      sb.write(
        drawZodiacSlice(
          c1: _c1,
          chartType: _chartType,
          seventhHouseDegreeUt: _seventhHouseDeg,
          num: i,
          r: _r,
          style: 'fill: $bgColor; fill-opacity: 0.5;',
          type: zodiacSigns[i],
        ),
      );
    }
    return sb.toString();
  }

  String _buildDualHouses() {
    return drawHousesCuspsAndTextNumber(
      r: _r,
      firstSubjectHousesList: _firstHousesList,
      standardHouseCuspColor: 'var(--kerykeion-chart-color-houses-radix-line)',
      firstHouseColor: 'var(--kerykeion-chart-color-first-house)',
      tenthHouseColor: 'var(--kerykeion-chart-color-tenth-house)',
      seventhHouseColor: 'var(--kerykeion-chart-color-seventh-house)',
      fourthHouseColor: 'var(--kerykeion-chart-color-fourth-house)',
      c1: _c1,
      c3: _c3,
      chartType: _chartType,
      externalView: false,
      secondSubjectHousesList: _secondHousesList,
      transitHouseCuspColor: 'var(--kerykeion-chart-color-houses-transit-line)',
    );
  }

  String _buildDualPlanets() {
    final firstPoints = _firstActivePointData
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

    final secondPoints = _secondActivePointData
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
      availableCelestialPoints: firstPoints,
      availablePlanetsSettings: _activePointSettings,
      secondSubjectCelestialPoints: secondPoints,
      thirdCircleRadius: _c3,
      firstHouseDegreeUt: _firstHouseDeg,
      seventhHouseDegreeUt: _seventhHouseDeg,
      chartType: _chartType,
      externalView: false,
      firstCircleRadius: _c1,
      secondCircleRadius: _c2,
    );
  }

  String _buildAspectLines() {
    final sb = StringBuffer();
    final List<List<double>> renderedPositions = [];
    // Dual-wheel uses a different aspect radius: r - 160
    final aspectRadius = _r - 160;

    for (final aspect in _aspects) {
      final aspectSetting = defaultChartAspectsSettings.firstWhere((s) => s.degree == aspect.aspectDegrees, orElse: () => defaultChartAspectsSettings.first);
      sb.write(
        drawAspectLine(
          r: _r,
          ar: aspectRadius,
          aspect: aspect.toJson(),
          color: aspectSetting.color,
          seventhHouseDegreeUt: _seventhHouseDeg,
          renderedIconPositions: renderedPositions,
        ),
      );
    }
    return sb.toString();
  }

  String _buildLunarPhase() {
    final phaseSubject = (_chartType == 'Transit') ? _secondSubject : _firstSubject;
    final lp = phaseSubject.lunarPhase;
    if (lp == null) return '';
    final lat = phaseSubject.lat ?? 0.0;
    return makeLunarPhase(lp.degreesBetweenSunAndMoon, lat);
  }

  // ── Helpers ──

  static KerykeionPointModel? _getPointFromSubject(AstrologicalSubjectModel subject, AstrologicalPoint ap) {
    switch (ap) {
      case AstrologicalPoint.Sun:
        return subject.sun;
      case AstrologicalPoint.Moon:
        return subject.moon;
      case AstrologicalPoint.Mercury:
        return subject.mercury;
      case AstrologicalPoint.Venus:
        return subject.venus;
      case AstrologicalPoint.Mars:
        return subject.mars;
      case AstrologicalPoint.Jupiter:
        return subject.jupiter;
      case AstrologicalPoint.Saturn:
        return subject.saturn;
      case AstrologicalPoint.Uranus:
        return subject.uranus;
      case AstrologicalPoint.Neptune:
        return subject.neptune;
      case AstrologicalPoint.Pluto:
        return subject.pluto;
      case AstrologicalPoint.Chiron:
        return subject.chiron;
      case AstrologicalPoint.Mean_North_Lunar_Node:
        return subject.meanNorthLunarNode;
      case AstrologicalPoint.True_North_Lunar_Node:
        return subject.trueNorthLunarNode;
      case AstrologicalPoint.Mean_South_Lunar_Node:
        return subject.meanSouthLunarNode;
      case AstrologicalPoint.True_South_Lunar_Node:
        return subject.trueSouthLunarNode;
      case AstrologicalPoint.Mean_Lilith:
        return subject.meanLilith;
      case AstrologicalPoint.True_Lilith:
        return subject.trueLilith;
      case AstrologicalPoint.Ascendant:
        return subject.ascendant;
      case AstrologicalPoint.Medium_Coeli:
        return subject.mediumCoeli;
      case AstrologicalPoint.Descendant:
        return subject.descendant;
      case AstrologicalPoint.Imum_Coeli:
        return subject.imumCoeli;
      case AstrologicalPoint.Earth:
        return subject.earth;
      case AstrologicalPoint.Pholus:
        return subject.pholus;
      case AstrologicalPoint.Ceres:
        return subject.ceres;
      case AstrologicalPoint.Pallas:
        return subject.pallas;
      case AstrologicalPoint.Juno:
        return subject.juno;
      case AstrologicalPoint.Vesta:
        return subject.vesta;
      case AstrologicalPoint.Eris:
        return subject.eris;
      case AstrologicalPoint.Sedna:
        return subject.sedna;
      case AstrologicalPoint.Haumea:
        return subject.haumea;
      case AstrologicalPoint.Makemake:
        return subject.makemake;
      case AstrologicalPoint.Ixion:
        return subject.ixion;
      case AstrologicalPoint.Orcus:
        return subject.orcus;
      case AstrologicalPoint.Quaoar:
        return subject.quaoar;
      case AstrologicalPoint.Regulus:
        return subject.regulus;
      case AstrologicalPoint.Spica:
        return subject.spica;
      case AstrologicalPoint.Vertex:
        return subject.vertex;
      case AstrologicalPoint.Anti_Vertex:
        return subject.antiVertex;
      case AstrologicalPoint.Pars_Fortunae:
        return subject.parsFortunae;
      case AstrologicalPoint.Pars_Spiritus:
        return subject.parsSpiritus;
      case AstrologicalPoint.Pars_Amoris:
        return subject.parsAmoris;
      case AstrologicalPoint.Pars_Fidei:
        return subject.parsFidei;
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

  String _formatDateTimeForSubject(AstrologicalSubjectModel s) {
    final iso = s.isoFormattedLocalDatetime ?? '';
    if (iso.isEmpty) return '';
    final dt = DateTime.tryParse(iso);
    if (dt == null) return iso;

    String tzOffset = '';
    final tzMatch = RegExp(r'[+-]\d{2}:\d{2}$').firstMatch(iso);
    if (tzMatch != null) tzOffset = tzMatch.group(0)!;

    final dateStr = '${dt.year.toString().padLeft(4, '0')}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
    final timeStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';

    return tzOffset.isNotEmpty ? '$dateStr $timeStr [$tzOffset]' : '$dateStr $timeStr';
  }

  String _formatPlaceForSubject(AstrologicalSubjectModel s) {
    final city = s.city ?? '';
    final nation = s.nation ?? '';
    final parts = <String>[];
    if (city.isNotEmpty) parts.add(formatLocationString(city));
    if (nation.isNotEmpty) parts.add(nation);
    return NatalChartDrawer._escapeXml(parts.join(', '));
  }

  String _formatCoordsForSubject(AstrologicalSubjectModel s) {
    final lat = s.lat;
    final lng = s.lng;
    if (lat == null || lng == null) return '';
    final latStr = convertLatitudeCoordinateToString(lat, 'N', 'S');
    final lngStr = convertLongitudeCoordinateToString(lng, 'E', 'W');
    return '$latStr  ·  $lngStr';
  }
}

// =============================================================================
// COMPOSITE CHART DRAWER
// =============================================================================

/// Draws SVG composite charts (single-wheel with midpoint data,
/// showing info for both subjects).
///
/// Composite charts look like a natal chart (single wheel) but contain
/// midpoint-averaged planet positions. The info sections show both subjects.
///
/// Usage:
/// ```dart
/// final drawer = CompositeChartDrawer(
///   chartData: myDualChartData,
///   theme: ChartTheme.classic,
/// );
/// final svgString = drawer.generateSvg();
/// ```
class CompositeChartDrawer {
  final DualChartDataModel chartData;
  final ChartTheme theme;
  final String? customCss;

  final ChartDimensionsConfig dimensions;
  final CircleRadiiConfig radii;
  final GridPositionsConfig gridPositions;

  late final AstrologicalSubjectModel _firstSubject;
  late final AstrologicalSubjectModel _secondSubject;
  late final List<AspectModel> _aspects;
  late final List<_CelestialPointData> _activePointData;
  late final List<Map<String, dynamic>> _activePointSettings;
  late final List<Map<String, dynamic>> _housesList;

  // Circle radii (same as natal)
  late final double _r;
  late final double _c1;
  late final double _c2;
  late final double _c3;

  late final double _firstHouseDeg;
  late final double _seventhHouseDeg;

  CompositeChartDrawer({
    required this.chartData,
    this.theme = ChartTheme.classic,
    this.customCss,
    this.dimensions = const ChartDimensionsConfig(),
    this.radii = const CircleRadiiConfig(),
    this.gridPositions = const GridPositionsConfig(),
  }) {
    _firstSubject = chartData.firstSubject;
    _secondSubject = chartData.secondSubject;
    _aspects = chartData.aspects;

    // Composite uses natal-style radii
    _r = radii.mainRadius;
    _c1 = radii.singleWheelFirstCircle;
    _c2 = radii.singleWheelSecondCircle;
    _c3 = radii.singleWheelThirdCircle;

    _firstHouseDeg = _firstSubject.firstHouse.absPos;
    _seventhHouseDeg = _firstSubject.seventhHouse.absPos;

    _collectActivePoints();
    _collectHouses();
  }

  void _collectActivePoints() {
    final activePoints = chartData.activePoints;
    _activePointData = [];
    _activePointSettings = [];

    for (final ap in activePoints) {
      final point = DualChartDrawer._getPointFromSubject(_firstSubject, ap);
      final setting = defaultCelestialPointsSettings.cast<CelestialPointSetting?>().firstWhere((s) => s?.name == ap.name, orElse: () => null);
      if (point == null || setting == null) continue;

      _activePointData.add(_CelestialPointData(enumValue: ap, point: point, setting: setting));
      _activePointSettings.add({'id': setting.id, 'name': setting.name, 'color': setting.color, 'label': setting.label, 'is_active': true});
    }
  }

  void _collectHouses() {
    _housesList = DualChartDrawer._buildHousesList(_firstSubject);
  }

  /// Generate the complete SVG chart string.
  String generateSvg() {
    final vars = _buildTemplateDict();
    return substituteTemplate(chartSvgTemplate, vars);
  }

  Map<String, String> _buildTemplateDict() {
    final td = <String, String>{};

    // ── Theme ──
    td['color_style_tag'] = customCss ?? getThemeCss(theme);

    // ── Sizing ──
    const verticalPaddingTop = 15;
    const verticalPaddingBottom = 15;

    final pointCount = _activePointData.length;
    final extraPoints = (pointCount > 20) ? pointCount - 20 : 0;
    final heightDelta = extraPoints * 8.0;
    final height = dimensions.defaultHeight + heightDelta;

    final viewboxHeight = height.toInt() + verticalPaddingTop + verticalPaddingBottom;
    td['viewbox'] = '0 -$verticalPaddingTop ${dimensions.natalWidth.toInt()} $viewboxHeight';
    td['background_color'] = 'var(--kerykeion-chart-color-paper-1)';
    td['paper_color_0'] = 'var(--kerykeion-chart-color-paper-0)';

    // Translate-Y offsets (same as natal)
    td['title_translate_y'] = '0';
    td['elements_translate_y'] = '0';
    td['qualities_translate_y'] = '0';
    td['bottom_left_translate_y'] = heightDelta.toStringAsFixed(0);
    td['lunar_phase_translate_y'] = (518 + heightDelta).toStringAsFixed(0);
    td['full_wheel_translate_y'] = '0';
    td['houses_and_planets_translate_y'] = '0';
    td['aspect_grid_translate_y'] = '0';
    td['aspect_list_translate_y'] = '0';

    // ── Title ──
    td['stringTitle'] =
        '${NatalChartDrawer._escapeXml(NatalChartDrawer._truncateName(_firstSubject.name, 14))} + ${NatalChartDrawer._escapeXml(NatalChartDrawer._truncateName(_secondSubject.name, 14))} Composite';

    // ── Top Left Info (both subjects) ──
    td['top_left_0'] = '${_firstSubject.name}:';
    final dt1 = _formatDateTimeForSubject(_firstSubject);
    final dt2 = _formatDateTimeForSubject(_secondSubject);
    td['top_left_1'] = dt1;
    td['top_left_2'] = _formatPlaceForSubject(_firstSubject);
    td['top_left_3'] = '${_secondSubject.name}:';
    td['top_left_4'] = dt2;
    td['top_left_5'] = _formatPlaceForSubject(_secondSubject);

    // ── Elements & Qualities ──
    final elemDist = chartData.elementDistribution;
    final qualDist = chartData.qualityDistribution;
    td['elements_string'] = 'Elements:';
    td['fire_string'] = 'Fire ${elemDist.firePercentage}%';
    td['earth_string'] = 'Earth ${elemDist.earthPercentage}%';
    td['air_string'] = 'Air ${elemDist.airPercentage}%';
    td['water_string'] = 'Water ${elemDist.waterPercentage}%';
    td['qualities_string'] = 'Qualities:';
    td['cardinal_string'] = 'Cardinal ${qualDist.cardinalPercentage}%';
    td['fixed_string'] = 'Fixed ${qualDist.fixedPercentage}%';
    td['mutable_string'] = 'Mutable ${qualDist.mutablePercentage}%';

    // ── Bottom Left ──
    final zt = _firstSubject.zodiacType?.name ?? 'Tropical';
    td['bottom_left_0'] = 'Zodiac: $zt';
    final hs = _firstSubject.housesSystemName ?? _firstSubject.housesSystemIdentifier.name;
    td['bottom_left_1'] = 'Domification: $hs';
    final lp = _firstSubject.lunarPhase;
    if (lp != null) {
      td['bottom_left_2'] = 'Lunation Day: ${lp.moonPhase}';
      td['bottom_left_3'] = 'Lunar Phase: ${lp.moonPhaseName.name.replaceAll('_', ' ')}';
    } else {
      td['bottom_left_2'] = '';
      td['bottom_left_3'] = '';
    }
    final p = _firstSubject.perspectiveType.name.replaceAll('_', ' ');
    td['bottom_left_4'] = 'Perspective: $p';

    // ── Lunar Phase ──
    if (lp != null) {
      td['makeLunarPhase'] = makeLunarPhase(lp.degreesBetweenSunAndMoon, _firstSubject.lat ?? 0.0);
    } else {
      td['makeLunarPhase'] = '';
    }

    // ── Wheel (natal-style single wheel) ──
    td['background_circle'] = drawBackgroundCircle(_r, 'var(--kerykeion-chart-color-paper-1)', 'var(--kerykeion-chart-color-paper-1)');
    td['makeZodiac'] = _buildZodiac();
    td['transitRing'] = '';
    td['degreeRing'] = drawDegreeRing(_r, _c1, _seventhHouseDeg, 'var(--kerykeion-chart-color-zodiac-radix-ring-2)');
    td['first_circle'] = drawFirstCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-2)', 'Natal', _c1);
    td['second_circle'] = drawSecondCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-1)', 'var(--kerykeion-chart-color-paper-1)', 'Natal', _c2);
    td['third_circle'] = drawThirdCircle(_r, 'var(--kerykeion-chart-color-zodiac-radix-ring-0)', 'var(--kerykeion-chart-color-paper-1)', 'Natal', _c3);

    // ── Houses ──
    td['makeHouses'] = drawHousesCuspsAndTextNumber(
      r: _r,
      firstSubjectHousesList: _housesList,
      standardHouseCuspColor: 'var(--kerykeion-chart-color-houses-radix-line)',
      firstHouseColor: 'var(--kerykeion-chart-color-first-house)',
      tenthHouseColor: 'var(--kerykeion-chart-color-tenth-house)',
      seventhHouseColor: 'var(--kerykeion-chart-color-seventh-house)',
      fourthHouseColor: 'var(--kerykeion-chart-color-fourth-house)',
      c1: _c1,
      c3: _c3,
      chartType: 'Composite',
      externalView: false,
    );

    // ── Planets (single-wheel) ──
    final pointMaps = _activePointData
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

    td['makePlanets'] = drawPlanets(
      radius: _r,
      availableCelestialPoints: pointMaps,
      availablePlanetsSettings: _activePointSettings,
      thirdCircleRadius: _c3,
      firstHouseDegreeUt: _firstHouseDeg,
      seventhHouseDegreeUt: _seventhHouseDeg,
      chartType: 'Composite',
      externalView: false,
      firstCircleRadius: _c1,
      secondCircleRadius: _c2,
    );

    // ── Aspects ──
    final sb = StringBuffer();
    final List<List<double>> renderedPositions = [];
    final ar = _r - _c3;

    for (final aspect in _aspects) {
      final aspectSetting = defaultChartAspectsSettings.firstWhere((s) => s.degree == aspect.aspectDegrees, orElse: () => defaultChartAspectsSettings.first);
      sb.write(
        drawAspectLine(
          r: _r,
          ar: ar,
          aspect: aspect.toJson(),
          color: aspectSetting.color,
          seventhHouseDegreeUt: _seventhHouseDeg,
          renderedIconPositions: renderedPositions,
        ),
      );
    }
    td['makeAspects'] = sb.toString();

    // ── Aspect Grid (natal-style triangular) ──
    td['makeAspectGrid'] = drawAspectGrid('var(--kerykeion-chart-color-paper-0)', _activePointSettings, _aspects.map((a) => a.toJson()).toList());
    td['makeDoubleChartAspectList'] = '';

    // ── Planet & House Grids ──
    td['makeMainPlanetGrid'] = drawMainPlanetGrid(
      title: '',
      subjectName: NatalChartDrawer._truncateName(_firstSubject.name, 20),
      celestialPoints: pointMaps,
      chartType: 'Composite',
      textColor: 'var(--kerykeion-chart-color-paper-0)',
      xPosition: gridPositions.mainPlanetX,
    );

    td['makeMainHousesGrid'] = drawMainHouseGrid(
      housesList: _housesList,
      textColor: 'var(--kerykeion-chart-color-paper-0)',
      xPosition: gridPositions.mainHousesX,
    );

    td['makeSecondaryPlanetGrid'] = '';
    td['makeSecondaryHousesGrid'] = '';
    td['makeHouseComparisonGrid'] = '';

    return td;
  }

  String _buildZodiac() {
    final sb = StringBuffer();
    const zodiacSigns = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];

    for (int i = 0; i < 12; i++) {
      final bgColor = 'var(--kerykeion-chart-color-zodiac-bg-$i)';
      sb.write(
        drawZodiacSlice(
          c1: _c1,
          chartType: 'Composite',
          seventhHouseDegreeUt: _seventhHouseDeg,
          num: i,
          r: _r,
          style: 'fill: $bgColor; fill-opacity: 0.5;',
          type: zodiacSigns[i],
        ),
      );
    }
    return sb.toString();
  }

  // Re-use the DualChartDrawer's formatting helpers
  String _formatDateTimeForSubject(AstrologicalSubjectModel s) {
    final iso = s.isoFormattedLocalDatetime ?? '';
    if (iso.isEmpty) return '';
    final dt = DateTime.tryParse(iso);
    if (dt == null) return iso;

    String tzOffset = '';
    final tzMatch = RegExp(r'[+-]\d{2}:\d{2}$').firstMatch(iso);
    if (tzMatch != null) tzOffset = tzMatch.group(0)!;

    final dateStr = '${dt.year.toString().padLeft(4, '0')}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
    final timeStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';

    return tzOffset.isNotEmpty ? '$dateStr $timeStr [$tzOffset]' : '$dateStr $timeStr';
  }

  String _formatPlaceForSubject(AstrologicalSubjectModel s) {
    final city = s.city ?? '';
    final nation = s.nation ?? '';
    final parts = <String>[];
    if (city.isNotEmpty) parts.add(formatLocationString(city));
    if (nation.isNotEmpty) parts.add(nation);
    return NatalChartDrawer._escapeXml(parts.join(', '));
  }
}
