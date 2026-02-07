import 'package:kerykeion_dart/src/astrological_subject_factory.dart';
import 'package:kerykeion_dart/src/composite_factory.dart';
import 'package:kerykeion_dart/src/return_factory.dart';
import 'package:kerykeion_dart/src/chart_data_factory.dart';
import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/models/chart_data.dart';

void main() async {
  print('='.repeat(80));
  print('KERYKEION DART - TOP-LEVEL API INTEGRATION TEST');
  print('='.repeat(80));

  await AstrologicalSubjectFactory.initialize();

  await testNatalChart();
  await testCompositeChart();
  await testSolarReturn();
  await testLunarReturn();
  await testSynastry();

  print('\n' + '='.repeat(80));
  print('ALL TESTS COMPLETED SUCCESSFULLY ✓');
  print('='.repeat(80));
}

Future<void> testNatalChart() async {
  print('\n' + '-'.repeat(80));
  print('TEST 1: NATAL CHART');
  print('-'.repeat(80));

  final natal = await AstrologicalSubjectFactory.createSubject(
    name: "John Doe",
    year: 1990,
    month: 6,
    day: 15,
    hour: 14,
    minute: 30,
    city: "New York",
    nation: "US",
    lng: -74.0060,
    lat: 40.7128,
    tzStr: "America/New_York",
  );

  print('\n📋 SUBJECT INFO:');
  print('   Name: ${natal.name}');
  print(
    '   Date: ${natal.year}-${natal.month!.toString().padLeft(2, '0')}-${natal.day!.toString().padLeft(2, '0')} ${natal.hour!.toString().padLeft(2, '0')}:${natal.minute!.toString().padLeft(2, '0')}',
  );
  print('   Location: ${natal.city}, ${natal.nation} (${natal.lat!.toStringAsFixed(4)}, ${natal.lng!.toStringAsFixed(4)})');
  print('   Timezone: ${natal.tzStr}');

  print('\n🌟 PLANETARY POSITIONS:');
  print(
    '   Sun:       ${natal.sun!.sign.toString().split('.').last.padRight(12)} ${natal.sun!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${natal.sun!.absPos.toStringAsFixed(2).padLeft(6)}°)',
  );
  print(
    '   Moon:      ${natal.moon!.sign.toString().split('.').last.padRight(12)} ${natal.moon!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${natal.moon!.absPos.toStringAsFixed(2).padLeft(6)}°)',
  );
  print(
    '   Mercury:   ${natal.mercury!.sign.toString().split('.').last.padRight(12)} ${natal.mercury!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${natal.mercury!.absPos.toStringAsFixed(2).padLeft(6)}°)',
  );
  print(
    '   Venus:     ${natal.venus!.sign.toString().split('.').last.padRight(12)} ${natal.venus!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${natal.venus!.absPos.toStringAsFixed(2).padLeft(6)}°)',
  );
  print(
    '   Mars:      ${natal.mars!.sign.toString().split('.').last.padRight(12)} ${natal.mars!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${natal.mars!.absPos.toStringAsFixed(2).padLeft(6)}°)',
  );

  print('\n🏠 ANGLES:');
  print(
    '   Ascendant: ${natal.ascendant!.sign.toString().split('.').last.padRight(12)} ${natal.ascendant!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${natal.ascendant!.absPos.toStringAsFixed(2).padLeft(6)}°)',
  );
  print(
    '   MC:        ${natal.mediumCoeli!.sign.toString().split('.').last.padRight(12)} ${natal.mediumCoeli!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${natal.mediumCoeli!.absPos.toStringAsFixed(2).padLeft(6)}°)',
  );

  print('\n🌙 LUNAR PHASE:');
  print('   Phase: ${natal.lunarPhase!.moonPhaseName.toString().split('.').last.replaceAll('_', ' ')} (${natal.lunarPhase!.moonPhase}/28)');
  print('   Emoji: ${natal.lunarPhase!.moonEmoji}');
  print('   Degrees between Sun-Moon: ${natal.lunarPhase!.degreesBetweenSunAndMoon.toStringAsFixed(2)}°');

  final chartData = ChartDataFactory.createChartData(ChartType.Natal, natal);

  print('\n📊 CHART DATA:');
  print('   Chart Type: ${chartData.chartType}');
  print('   Aspects: ${chartData.aspects.length}');
  print('\n   Element Distribution:');
  print('     Fire:  ${chartData.elementDistribution.fire}');
  print('     Earth: ${chartData.elementDistribution.earth}');
  print('     Air:   ${chartData.elementDistribution.air}');
  print('     Water: ${chartData.elementDistribution.water}');
  print('     Dominant: ${chartData.elementDistribution.dominant}');
  print('\n   Quality Distribution:');
  print('     Cardinal: ${chartData.qualityDistribution.cardinal}');
  print('     Fixed:    ${chartData.qualityDistribution.fixed}');
  print('     Mutable:  ${chartData.qualityDistribution.mutable}');
  print('     Dominant: ${chartData.qualityDistribution.dominant}');

  print('\n✓ Natal chart test PASSED');
}

Future<void> testCompositeChart() async {
  print('\n' + '-'.repeat(80));
  print('TEST 2: COMPOSITE CHART');
  print('-'.repeat(80));

  final person1 = await AstrologicalSubjectFactory.createSubject(
    name: "Person 1",
    year: 1985,
    month: 3,
    day: 20,
    hour: 10,
    minute: 0,
    city: "London",
    nation: "GB",
    lng: -0.1278,
    lat: 51.5074,
    tzStr: "Europe/London",
  );

  final person2 = await AstrologicalSubjectFactory.createSubject(
    name: "Person 2",
    year: 1987,
    month: 9,
    day: 15,
    hour: 16,
    minute: 30,
    city: "Paris",
    nation: "FR",
    lng: 2.3522,
    lat: 48.8566,
    tzStr: "Europe/Paris",
  );

  print('\n👥 INDIVIDUAL CHARTS:');
  print('   Person 1 Sun: ${person1.sun!.sign.toString().split('.').last.padRight(12)} ${person1.sun!.absPos.toStringAsFixed(4)}°');
  print('   Person 2 Sun: ${person2.sun!.sign.toString().split('.').last.padRight(12)} ${person2.sun!.absPos.toStringAsFixed(4)}°');

  final composite = CompositeSubjectFactory.createCompositeSubject(subject1: person1, subject2: person2);

  print('\n💑 COMPOSITE CHART:');
  print('   Name: ${composite.name}');
  print(
    '   Composite Sun:  ${composite.sun!.sign.toString().split('.').last.padRight(12)} ${composite.sun!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${composite.sun!.absPos.toStringAsFixed(4)}°)',
  );
  print(
    '   Composite Moon: ${composite.moon!.sign.toString().split('.').last.padRight(12)} ${composite.moon!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${composite.moon!.absPos.toStringAsFixed(4)}°)',
  );
  print(
    '   Composite Asc:  ${composite.ascendant!.sign.toString().split('.').last.padRight(12)} ${composite.ascendant!.position.toStringAsFixed(2).padLeft(6)}° (abs: ${composite.ascendant!.absPos.toStringAsFixed(4)}°)',
  );

  final compositeData = ChartDataFactory.createChartData(ChartType.Composite, person1, secondSubject: person2);

  print('\n📊 COMPOSITE CHART DATA:');
  print('   Chart Type: ${compositeData.chartType}');
  print('   Aspects: ${compositeData.aspects.length}');
  print('   Dominant Element: ${compositeData.elementDistribution.dominant}');
  print('   Dominant Quality: ${compositeData.qualityDistribution.dominant}');

  assert(compositeData.chartType == 'Composite', 'Chart type should be Composite');
  assert(compositeData.firstSubject.name!.contains('Composite'), 'Subject name should contain Composite');

  print('\n✓ Composite chart test PASSED');
}

Future<void> testSolarReturn() async {
  print('\n' + '-'.repeat(80));
  print('TEST 3: SOLAR RETURN');
  print('-'.repeat(80));

  final natal = await AstrologicalSubjectFactory.createSubject(
    name: "Jane Smith",
    year: 1992,
    month: 12,
    day: 25,
    hour: 8,
    minute: 0,
    city: "Los Angeles",
    nation: "US",
    lng: -118.2437,
    lat: 34.0522,
    tzStr: "America/Los_Angeles",
  );

  print('\n🎂 NATAL CHART:');
  print('   Name: ${natal.name}');
  print('   Birth Date: ${natal.year}-${natal.month!.toString().padLeft(2, '0')}-${natal.day!.toString().padLeft(2, '0')}');
  print('   Natal Sun: ${natal.sun!.absPos.toStringAsFixed(6)}°');

  final solarReturn = await ReturnFactory.calculateSolarReturn(natalSubject: natal, returnYear: 2023);

  print('\n☀️ SOLAR RETURN 2023:');
  print('   Name: ${solarReturn.name}');
  print(
    '   Return Date: ${solarReturn.year}-${solarReturn.month!.toString().padLeft(2, '0')}-${solarReturn.day!.toString().padLeft(2, '0')} ${solarReturn.hour!.toString().padLeft(2, '0')}:${solarReturn.minute!.toString().padLeft(2, '0')}',
  );
  print('   Return Sun: ${solarReturn.sun!.absPos.toStringAsFixed(6)}°');

  final difference = (solarReturn.sun!.absPos - natal.sun!.absPos).abs();

  print('\n🎯 PRECISION CHECK:');
  print('   Natal Sun:  ${natal.sun!.absPos.toStringAsFixed(8)}°');
  print('   Return Sun: ${solarReturn.sun!.absPos.toStringAsFixed(8)}°');
  print('   Difference: ${difference.toStringAsFixed(8)}° (target: < 0.01°)');

  assert(difference < 0.01, 'Sun position difference should be < 0.01°');
  assert(solarReturn.year == 2023, 'Return year should be 2023');
  assert(solarReturn.name!.contains('Solar Return'), 'Name should contain Solar Return');

  final monthDiff = (solarReturn.month! - natal.month!).abs();
  print('   Month diff: $monthDiff (target: ≤ 1)');
  assert(monthDiff <= 1, 'Return should be within 1 month of birthday');

  print('\n✓ Solar return test PASSED');
}

Future<void> testLunarReturn() async {
  print('\n' + '-'.repeat(80));
  print('TEST 4: LUNAR RETURN');
  print('-'.repeat(80));

  final natal = await AstrologicalSubjectFactory.createSubject(
    name: "Bob Johnson",
    year: 1988,
    month: 4,
    day: 10,
    hour: 20,
    minute: 15,
    city: "Chicago",
    nation: "US",
    lng: -87.6298,
    lat: 41.8781,
    tzStr: "America/Chicago",
  );

  print('\n🎂 NATAL CHART:');
  print('   Name: ${natal.name}');
  print('   Birth Date: ${natal.year}-${natal.month!.toString().padLeft(2, '0')}-${natal.day!.toString().padLeft(2, '0')}');
  print('   Natal Moon: ${natal.moon!.absPos.toStringAsFixed(6)}°');

  final lunarReturn = await ReturnFactory.calculateLunarReturn(natalSubject: natal, returnYear: 2023, returnMonth: 6);

  print('\n🌙 LUNAR RETURN JUNE 2023:');
  print('   Name: ${lunarReturn.name}');
  print(
    '   Return Date: ${lunarReturn.year}-${lunarReturn.month!.toString().padLeft(2, '0')}-${lunarReturn.day!.toString().padLeft(2, '0')} ${lunarReturn.hour!.toString().padLeft(2, '0')}:${lunarReturn.minute!.toString().padLeft(2, '0')}',
  );
  print('   Return Moon: ${lunarReturn.moon!.absPos.toStringAsFixed(6)}°');

  final difference = (lunarReturn.moon!.absPos - natal.moon!.absPos).abs();

  print('\n🎯 PRECISION CHECK:');
  print('   Natal Moon:  ${natal.moon!.absPos.toStringAsFixed(8)}°');
  print('   Return Moon: ${lunarReturn.moon!.absPos.toStringAsFixed(8)}°');
  print('   Difference:  ${difference.toStringAsFixed(8)}° (target: < 0.1°)');

  assert(difference < 0.1, 'Moon position difference should be < 0.1°');
  assert(lunarReturn.year == 2023, 'Return year should be 2023');
  assert(lunarReturn.month == 6, 'Return month should be 6');
  assert(lunarReturn.name!.contains('Lunar Return'), 'Name should contain Lunar Return');

  print('\n✓ Lunar return test PASSED');
}

Future<void> testSynastry() async {
  print('\n' + '-'.repeat(80));
  print('TEST 5: SYNASTRY');
  print('-'.repeat(80));

  final person1 = await AstrologicalSubjectFactory.createSubject(
    name: "Alice",
    year: 1990,
    month: 1,
    day: 15,
    hour: 12,
    minute: 0,
    city: "Boston",
    nation: "US",
    lng: -71.0589,
    lat: 42.3601,
    tzStr: "America/New_York",
  );

  final person2 = await AstrologicalSubjectFactory.createSubject(
    name: "Bob",
    year: 1988,
    month: 7,
    day: 20,
    hour: 18,
    minute: 30,
    city: "Seattle",
    nation: "US",
    lng: -122.3321,
    lat: 47.6062,
    tzStr: "America/Los_Angeles",
  );

  print('\n👥 INDIVIDUAL CHARTS:');
  print('   Alice:');
  print('     Sun:  ${person1.sun!.sign.toString().split('.').last.padRight(12)} ${person1.sun!.position.toStringAsFixed(2)}°');
  print('     Moon: ${person1.moon!.sign.toString().split('.').last.padRight(12)} ${person1.moon!.position.toStringAsFixed(2)}°');
  print('\n   Bob:');
  print('     Sun:  ${person2.sun!.sign.toString().split('.').last.padRight(12)} ${person2.sun!.position.toStringAsFixed(2)}°');
  print('     Moon: ${person2.moon!.sign.toString().split('.').last.padRight(12)} ${person2.moon!.position.toStringAsFixed(2)}°');

  final synastryData = ChartDataFactory.createChartData(ChartType.Synastry, person1, secondSubject: person2, includeHouseComparison: true);

  print('\n💕 SYNASTRY CHART DATA:');
  print('   Chart Type: ${synastryData.chartType}');
  print('   Inter-aspects: ${synastryData.aspects.length}');

  if (synastryData is DualChartDataModel) {
    print('   Has house comparison: ${synastryData.houseComparison != null}');

    if (synastryData.houseComparison != null) {
      final hc = synastryData.houseComparison!;
      print('\n   House Comparison:');
      print('     Alice\'s planets in Bob\'s houses: ${hc.firstPointsInSecondHouses.length}');
      print('     Bob\'s planets in Alice\'s houses: ${hc.secondPointsInFirstHouses.length}');

      if (hc.firstPointsInSecondHouses.isNotEmpty) {
        final example = hc.firstPointsInSecondHouses.first;
        print(
          '\n     Example: ${example.pointOwnerName}\'s ${example.pointName} in ${example.projectedHouseOwnerName}\'s ${example.projectedHouseName.replaceAll('_', ' ')}',
        );
      }
    }
  }

  assert(synastryData.chartType == 'Synastry', 'Chart type should be Synastry');
  assert(synastryData is DualChartDataModel, 'Should be DualChartDataModel');

  print('\n✓ Synastry test PASSED');
}

extension StringExtension on String {
  String repeat(int count) => List.filled(count, this).join();
}
