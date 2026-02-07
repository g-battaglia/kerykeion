import 'package:sweph/sweph.dart';

import 'web_helper.dart' if (dart.library.ffi) 'io_helper.dart';

String getStarPosition() {
  final jd =
      Sweph.swe_julday(2022, 6, 29, (2 + 52 / 60), CalendarType.SE_GREG_CAL);
  return Sweph.swe_fixstar2_ut('Rohini', jd, SwephFlag.SEFLG_SWIEPH)
      .coordinates
      .distance
      .toStringAsFixed(3);
}

Future<Map<String, String>> getSwephData() async {
  await initSweph([
    'assets/sefstars.txt', // For star position
    'assets/seasnam.txt', // For asteriods
  ]);

  return {
    'sweph-version': Sweph.swe_version(),
    'asteroid-name': Sweph.swe_get_planet_name(HeavenlyBody.SE_AST_OFFSET + 16),
    'star-position': getStarPosition(),
  };
}
