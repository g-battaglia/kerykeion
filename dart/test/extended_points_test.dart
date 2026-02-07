import 'package:kerykeion_dart/kerykeion_dart.dart';
import 'package:sweph/sweph.dart' as swe;

void main() async {
  print('=== Testing Additional Planetary Calculations ===\n');

  // Initialize sweph library
  await swe.Sweph.init();

  // Initialize timezone data
  AstrologicalSubjectFactory.initialize();

  // Create a test chart for 2000-01-01 12:00 UTC, Greenwich
  final subject = await AstrologicalSubjectFactory.createSubject(
    name: 'Extended Test',
    year: 2000,
    month: 1,
    day: 1,
    hour: 12,
    minute: 0,
    city: 'Greenwich',
    nation: 'GB',
    lng: 0.0,
    lat: 51.48,
    tzStr: 'UTC',
    zodiacType: ZodiacType.Tropical,
    housesSystemIdentifier: HousesSystemIdentifier.P,
    perspectiveType: PerspectiveType.Apparent_Geocentric,
  );

  print('Chart for: ${subject.name}');
  print('Date: ${subject.year}-${subject.month}-${subject.day} ${subject.hour}:${subject.minute}');
  print('Location: ${subject.city}, ${subject.nation} (${subject.lat}°N, ${subject.lng}°E)');
  print('Julian Day: ${subject.julianDay}\n');

  // Test traditional planets
  print('--- Traditional Planets ---');
  if (subject.sun != null) print('Sun: ${subject.sun!.sign} ${subject.sun!.position.toStringAsFixed(2)}° (${subject.sun!.absPos.toStringAsFixed(2)}°)');
  if (subject.moon != null) print('Moon: ${subject.moon!.sign} ${subject.moon!.position.toStringAsFixed(2)}°');
  if (subject.mercury != null) print('Mercury: ${subject.mercury!.sign} ${subject.mercury!.position.toStringAsFixed(2)}°');
  if (subject.venus != null) print('Venus: ${subject.venus!.sign} ${subject.venus!.position.toStringAsFixed(2)}°');
  if (subject.mars != null) print('Mars: ${subject.mars!.sign} ${subject.mars!.position.toStringAsFixed(2)}°');

  // Test asteroids
  print('\n--- Asteroids ---');
  if (subject.chiron != null) print('Chiron: ${subject.chiron!.sign} ${subject.chiron!.position.toStringAsFixed(2)}°');
  if (subject.ceres != null) print('Ceres: ${subject.ceres!.sign} ${subject.ceres!.position.toStringAsFixed(2)}°');
  if (subject.pallas != null) print('Pallas: ${subject.pallas!.sign} ${subject.pallas!.position.toStringAsFixed(2)}°');
  if (subject.juno != null) print('Juno: ${subject.juno!.sign} ${subject.juno!.position.toStringAsFixed(2)}°');
  if (subject.vesta != null) print('Vesta: ${subject.vesta!.sign} ${subject.vesta!.position.toStringAsFixed(2)}°');
  if (subject.pholus != null) print('Pholus: ${subject.pholus!.sign} ${subject.pholus!.position.toStringAsFixed(2)}°');

  // Test TNOs
  print('\n--- Trans-Neptunian Objects ---');
  if (subject.eris != null) print('Eris: ${subject.eris!.sign} ${subject.eris!.position.toStringAsFixed(2)}°');
  if (subject.sedna != null) print('Sedna: ${subject.sedna!.sign} ${subject.sedna!.position.toStringAsFixed(2)}°');
  if (subject.haumea != null) print('Haumea: ${subject.haumea!.sign} ${subject.haumea!.position.toStringAsFixed(2)}°');
  if (subject.makemake != null) print('Makemake: ${subject.makemake!.sign} ${subject.makemake!.position.toStringAsFixed(2)}°');
  if (subject.ixion != null) print('Ixion: ${subject.ixion!.sign} ${subject.ixion!.position.toStringAsFixed(2)}°');
  if (subject.orcus != null) print('Orcus: ${subject.orcus!.sign} ${subject.orcus!.position.toStringAsFixed(2)}°');
  if (subject.quaoar != null) print('Quaoar: ${subject.quaoar!.sign} ${subject.quaoar!.position.toStringAsFixed(2)}°');

  // Test fixed stars
  print('\n--- Fixed Stars ---');
  if (subject.regulus != null) print('Regulus: ${subject.regulus!.sign} ${subject.regulus!.position.toStringAsFixed(2)}°');
  if (subject.spica != null) print('Spica: ${subject.spica!.sign} ${subject.spica!.position.toStringAsFixed(2)}°');

  // Test Arabic parts
  print('\n--- Arabic Parts ---');
  if (subject.parsFortunae != null) print('Pars Fortunae: ${subject.parsFortunae!.sign} ${subject.parsFortunae!.position.toStringAsFixed(2)}°');
  if (subject.parsSpiritus != null) print('Pars Spiritus: ${subject.parsSpiritus!.sign} ${subject.parsSpiritus!.position.toStringAsFixed(2)}°');
  if (subject.parsAmoris != null) print('Pars Amoris: ${subject.parsAmoris!.sign} ${subject.parsAmoris!.position.toStringAsFixed(2)}°');
  if (subject.parsFidei != null) print('Pars Fidei: ${subject.parsFidei!.sign} ${subject.parsFidei!.position.toStringAsFixed(2)}°');

  // Test special points
  print('\n--- Special Points ---');
  if (subject.vertex != null) print('Vertex: ${subject.vertex!.sign} ${subject.vertex!.position.toStringAsFixed(2)}°');
  if (subject.antiVertex != null) print('Anti-Vertex: ${subject.antiVertex!.sign} ${subject.antiVertex!.position.toStringAsFixed(2)}°');

  // Test lunar nodes
  print('\n--- Lunar Nodes ---');
  if (subject.meanNorthLunarNode != null)
    print('Mean North Node: ${subject.meanNorthLunarNode!.sign} ${subject.meanNorthLunarNode!.position.toStringAsFixed(2)}°');
  if (subject.meanSouthLunarNode != null)
    print('Mean South Node: ${subject.meanSouthLunarNode!.sign} ${subject.meanSouthLunarNode!.position.toStringAsFixed(2)}°');

  // Test Lilith points
  print('\n--- Lilith Points ---');
  if (subject.meanLilith != null) print('Mean Lilith: ${subject.meanLilith!.sign} ${subject.meanLilith!.position.toStringAsFixed(2)}°');
  if (subject.trueLilith != null) print('True Lilith: ${subject.trueLilith!.sign} ${subject.trueLilith!.position.toStringAsFixed(2)}°');

  print('\n=== All tests completed successfully! ===');
}
