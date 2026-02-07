import 'package:test/test.dart';
import 'package:kerykeion_dart/kerykeion_dart.dart';
import 'package:sweph/sweph.dart';
import 'dart:io';

void main() {
  setUp(() async {
    AstrologicalSubjectFactory.initialize();

    // Initialize sweph
    await Sweph.init();

    // In test env, we are pointing LD_LIBRARY_PATH.
    // We might need to set ephemeris path if not default.
    // For now assume default works or it's empty but calculations work for planets (moshier default fallback?).
    // Actually sweph defaults to moshier if no ephe files found, which is less precise but works.

    // But user wants "iterate until all api get same result". So precision matters.
    // I should point to the real ephe path.
    // The python path is `../kerykeion/sweph` relative to `dart` folder.
    final ephePath = Directory.current.parent.path + '/kerykeion/sweph';
    try {
      Sweph.swe_set_ephe_path(ephePath);
    } catch (e) {
      print("Failed to set ephe path: $e");
    }
  });

  test('Calculate chart for 2000-01-01 12:00 UTC Greenwich', () async {
    final subject = await AstrologicalSubjectFactory.createSubject(
      name: "Test",
      year: 2000,
      month: 1,
      day: 1,
      hour: 12,
      minute: 0,
      city: "Greenwich",
      nation: "GB",
      lng: 0.0,
      lat: 51.48,
      tzStr: "UTC",
    );

    print("\n=== Chart Calculation Results ===");
    print("Name: ${subject.name}");
    print("Date: ${subject.year}-${subject.month}-${subject.day} ${subject.hour}:${subject.minute}");
    print("Location: ${subject.city}, ${subject.nation} (${subject.lat}°N, ${subject.lng}°E)");
    print("Julian Day: ${subject.julianDay}");
    print("\n--- Planets ---");
    print("Sun: ${subject.sun!.sign} ${subject.sun!.position.toStringAsFixed(2)}° (${subject.sun!.absPos.toStringAsFixed(6)}°)");
    print("Moon: ${subject.moon!.sign} ${subject.moon!.position.toStringAsFixed(2)}° (${subject.moon!.absPos.toStringAsFixed(6)}°)");
    print("Mercury: ${subject.mercury?.sign} ${subject.mercury?.position.toStringAsFixed(2)}°");
    print("Venus: ${subject.venus?.sign} ${subject.venus?.position.toStringAsFixed(2)}°");
    print("Mars: ${subject.mars?.sign} ${subject.mars?.position.toStringAsFixed(2)}°");

    print("\n--- Angles ---");
    print("Ascendant: ${subject.ascendant!.sign} ${subject.ascendant!.position.toStringAsFixed(2)}° (${subject.ascendant!.absPos.toStringAsFixed(6)}°)");
    print("MC: ${subject.mediumCoeli!.sign} ${subject.mediumCoeli!.position.toStringAsFixed(2)}°");

    print("\n--- Houses ---");
    print("1st House: ${subject.firstHouse.absPos.toStringAsFixed(2)}°");
    print("10th House: ${subject.tenthHouse.absPos.toStringAsFixed(2)}°");

    // Validate Sun position (J2000.0 epoch, Sun at ~280.36° = Capricorn 10°)
    expect(subject.sun, isNotNull);
    expect(subject.sun!.sign, Sign.Cap);
    expect(subject.sun!.absPos, closeTo(280.37, 0.1));
    expect(subject.sun!.position, closeTo(10.37, 0.1));

    // Validate Moon position
    expect(subject.moon, isNotNull);
    expect(subject.moon!.sign, Sign.Sco);
    expect(subject.moon!.absPos, closeTo(223.32, 0.1));

    // Validate Ascendant (depends on location and time)
    expect(subject.ascendant, isNotNull);
    expect(subject.ascendant!.sign, Sign.Ari);
    expect(subject.ascendant!.absPos, closeTo(24.27, 0.5));

    // Validate Julian Day
    expect(subject.julianDay, closeTo(2451545.0, 0.01));

    print("\n=== All validations passed! ===\n");
  });
}
