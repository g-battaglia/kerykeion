import 'package:flutter_test/flutter_test.dart';
import 'package:sweph/sweph.dart';
import 'dart:io';

void main() {
  test('Test sweph init', () async {
    // Trying with explicit path to bundled assets if possible, or maybe just init.
    // Assuming init() initializes the bindings.
    try {
      await Sweph.init();
    } catch (e) {
      print('Init failed: $e');
    }

    try {
      final jd = Sweph.swe_julday(2000, 1, 1, 12.0, CalendarType.SE_GREG_CAL);
      print('JD: $jd');
    } catch (e) {
      print('JD calculation failed: $e');
    }

    print('Done');
  });
}
