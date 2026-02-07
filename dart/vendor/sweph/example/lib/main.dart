import 'package:flutter/material.dart';
import 'package:sweph/sweph.dart';

import 'web_helper.dart' if (dart.library.ffi) 'io_helper.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final stopwatch = Stopwatch()..start();

  // Only load the assets you need. By default will load none
  // Some assets are bundled with Sweph
  await initSweph([
    'packages/sweph/assets/ephe/seas_18.se1', // For house calc
    'packages/sweph/assets/ephe/sefstars.txt', // For star position
    'packages/sweph/assets/ephe/seasnam.txt', // For asteriods
  ]);

  runApp(MyApp(
    timeToLoad: stopwatch.elapsed,
  ));
}

class MyApp extends StatefulWidget {
  final Duration timeToLoad;
  const MyApp({super.key, required this.timeToLoad});

  @override
  // ignore: library_private_types_in_public_api
  _MyAppState createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  String swephVersion = Sweph.swe_version();
  String moonPosition = getMoonPosition();
  String starDistance = getStarPosition();
  String asteroidName = getAstroidName();
  HouseCuspData houseSystemAscmc = getHouseSystemAscmc();
  CoordinatesWithSpeed chironPosition = getChironPosition();
  DegreeSplitData degreeSplitData = Sweph.swe_split_deg(
    100,
    SplitDegFlags.SE_SPLIT_DEG_ZODIACAL |
        SplitDegFlags.SE_SPLIT_DEG_ROUND_SEC |
        SplitDegFlags.SE_SPLIT_DEG_KEEP_SIGN |
        SplitDegFlags.SE_SPLIT_DEG_KEEP_DEG,
  );
  HouseCuspData houseCuspData = Sweph.swe_houses_ex2(
    Sweph.swe_julday(2000, 1, 1, 12, CalendarType.SE_GREG_CAL),
    SwephFlag.SEFLG_TROPICAL,
    30,
    60,
    Hsys.B,
  );
  List<double> utcJds = Sweph.swe_utc_to_jd(
    2000,
    1,
    1,
    12,
    0,
    0,
    CalendarType.SE_GREG_CAL,
  );

  AltitudeRefracInfo altInfo =
      Sweph.swe_refrac(80, 1013.25, 15, RefractionMode.SE_APP_TO_TRUE);
  AltitudeRefracInfo altInfoEx = Sweph.swe_refrac_extended(
      100, 200, 1013.25, 15, 0.0065, RefractionMode.SE_APP_TO_TRUE);

  @override
  void initState() {
    super.initState();
  }

  static String getMoonPosition() {
    final jd =
        Sweph.swe_julday(2022, 6, 29, (2 + 52 / 60), CalendarType.SE_GREG_CAL);
    final pos =
        Sweph.swe_calc_ut(jd, HeavenlyBody.SE_MOON, SwephFlag.SEFLG_SWIEPH);
    return 'lat=${pos.latitude.toStringAsFixed(3)} lon=${pos.longitude.toStringAsFixed(3)}';
  }

  static String getStarPosition() {
    final jd =
        Sweph.swe_julday(2022, 6, 29, (2 + 52 / 60), CalendarType.SE_GREG_CAL);
    try {
      return Sweph.swe_fixstar2_ut('Rohini', jd, SwephFlag.SEFLG_SWIEPH)
          .coordinates
          .distance
          .toStringAsFixed(3);
    } catch (e) {
      return e.toString();
    }
  }

  static String getAstroidName() {
    return Sweph.swe_get_planet_name(HeavenlyBody.SE_AST_OFFSET + 16);
  }

  static HouseCuspData getHouseSystemAscmc() {
    const year = 1947;
    const month = 8;
    const day = 15;
    const hour = 16 + (0.0 / 60.0) - 5.5;

    const longitude = 81 + 50 / 60.0;
    const latitude = 25 + 57 / 60.0;
    final julday =
        Sweph.swe_julday(year, month, day, hour, CalendarType.SE_GREG_CAL);

    Sweph.swe_set_sid_mode(SiderealMode.SE_SIDM_LAHIRI,
        SiderealModeFlag.SE_SIDBIT_NONE, 0.0 /* t0 */, 0.0 /* ayan_t0 */);
    return Sweph.swe_houses(julday, latitude, longitude, Hsys.P);
  }

  static CoordinatesWithSpeed getChironPosition() {
    final now = DateTime.now();
    final jd = Sweph.swe_julday(now.year, now.month, now.day,
        (now.hour + now.minute / 60), CalendarType.SE_GREG_CAL);
    Sweph.swe_julday(2022, 6, 29, (2 + 52 / 60), CalendarType.SE_GREG_CAL);
    return Sweph.swe_calc_ut(
        jd, HeavenlyBody.SE_CHIRON, SwephFlag.SEFLG_SWIEPH);
  }

  void _addText(List<Widget> children, String text) {
    const textStyle = TextStyle(fontSize: 25);
    const spacerSmall = SizedBox(height: 10);

    children.add(spacerSmall);
    children.add(Text(
      text,
      style: textStyle,
      textAlign: TextAlign.center,
    ));
  }

  Widget _getContent(BuildContext context) {
    List<Widget> children = [
      const Text(
        'Swiss Ephemeris Exmaple',
        style: TextStyle(fontSize: 30),
        textAlign: TextAlign.center,
      ),
      const SizedBox(height: 10)
    ];

    _addText(children,
        'Time taken to load Sweph: ${widget.timeToLoad.inMilliseconds} ms');
    _addText(children, 'Sweph Version: $swephVersion');
    _addText(
        children, 'Moon position on 2022-06-29 02:52:00 UTC: $moonPosition');
    _addText(children, 'Distance of star Rohini: $starDistance AU');
    _addText(children, 'Name of Asteroid 16: $asteroidName');
    _addText(children, 'Position of Chiron: $chironPosition');
    _addText(children,
        'House System ASCMC[0] for custom time: ${houseSystemAscmc.ascmc[0]}');
    _addText(children, 'Degree Split Data: $degreeSplitData');
    _addText(children, 'House Cusp Data: ${houseCuspData.cusps.sublist(0, 6)}');
    _addText(children,
        'TT: ${utcJds[0]} UT1: ${utcJds[1]} UTC: ${Sweph.swe_julday(2000, 1, 1, 12, CalendarType.SE_GREG_CAL)}}');
    _addText(children, 'AltInfo: $altInfo');
    _addText(children, 'AltInfoEx: $altInfoEx');

    return Column(children: children);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(
          title: const Text('Native Packages'),
        ),
        body: SingleChildScrollView(
          child: Center(
            child: Container(
                padding: const EdgeInsets.all(10), child: _getContent(context)),
          ),
        ),
      ),
    );
  }
}
