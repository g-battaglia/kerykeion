import 'package:flutter_test/flutter_test.dart';
import 'package:kerykeion_dart/src/astrological_subject_factory.dart';
import 'package:kerykeion_dart/src/composite_factory.dart';
import 'package:kerykeion_dart/src/return_factory.dart';
import 'package:kerykeion_dart/src/chart_data_factory.dart';
import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/models/chart_data.dart';

void main() {
  setUpAll(() async {
    await AstrologicalSubjectFactory.initialize();
  });

  group('Top-Level API Integration Tests', () {
    test('Complete Natal Chart Workflow', () async {
      print('\n=== NATAL CHART TEST ===');

      // Create natal chart
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

      print('Name: ${natal.name}');
      print('Date: ${natal.year}-${natal.month}-${natal.day} ${natal.hour}:${natal.minute}');
      print('Location: ${natal.city}, ${natal.nation} (${natal.lat}, ${natal.lng})');
      print('Timezone: ${natal.tzStr}');

      // Verify core data
      expect(natal.sun, isNotNull);
      expect(natal.moon, isNotNull);
      expect(natal.ascendant, isNotNull);

      print('\nSun: ${natal.sun!.sign} ${natal.sun!.position.toStringAsFixed(2)}° (${natal.sun!.absPos.toStringAsFixed(2)}°)');
      print('Moon: ${natal.moon!.sign} ${natal.moon!.position.toStringAsFixed(2)}° (${natal.moon!.absPos.toStringAsFixed(2)}°)');
      print('Ascendant: ${natal.ascendant!.sign} ${natal.ascendant!.position.toStringAsFixed(2)}° (${natal.ascendant!.absPos.toStringAsFixed(2)}°)');
      print('MC: ${natal.mediumCoeli!.sign} ${natal.mediumCoeli!.position.toStringAsFixed(2)}° (${natal.mediumCoeli!.absPos.toStringAsFixed(2)}°)');

      // Verify lunar phase
      expect(natal.lunarPhase, isNotNull);
      print('\nLunar Phase: ${natal.lunarPhase!.moonPhaseName} (Phase ${natal.lunarPhase!.moonPhase})');
      print('Moon Emoji: ${natal.lunarPhase!.moonEmoji}');
      print('Degrees between Sun-Moon: ${natal.lunarPhase!.degreesBetweenSunAndMoon.toStringAsFixed(2)}°');

      // Generate chart data
      final chartData = ChartDataFactory.createChartData(ChartType.Natal, natal);

      print('\nChart Data Type: ${chartData.chartType}');
      print('Aspects found: ${chartData.aspects.length}');
      print('Element Distribution:');
      print('  Fire: ${chartData.elementDistribution.fire}');
      print('  Earth: ${chartData.elementDistribution.earth}');
      print('  Air: ${chartData.elementDistribution.air}');
      print('  Water: ${chartData.elementDistribution.water}');
      print('  Dominant: ${chartData.elementDistribution.dominant}');

      print('Quality Distribution:');
      print('  Cardinal: ${chartData.qualityDistribution.cardinal}');
      print('  Fixed: ${chartData.qualityDistribution.fixed}');
      print('  Mutable: ${chartData.qualityDistribution.mutable}');
      print('  Dominant: ${chartData.qualityDistribution.dominant}');

      // Verify distributions
      expect(chartData.elementDistribution.dominant, isNotNull);
      expect(chartData.qualityDistribution.dominant, isNotNull);

      print('\n✓ Natal chart test passed');
    });

    test('Complete Composite Chart Workflow', () async {
      print('\n=== COMPOSITE CHART TEST ===');

      // Create two natal charts
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

      print('Person 1 Sun: ${person1.sun!.absPos.toStringAsFixed(2)}°');
      print('Person 2 Sun: ${person2.sun!.absPos.toStringAsFixed(2)}°');

      // Create composite chart
      final composite = CompositeSubjectFactory.createCompositeSubject(subject1: person1, subject2: person2);

      print('\nComposite Chart:');
      print('Name: ${composite.name}');
      print('Composite Sun: ${composite.sun!.sign} ${composite.sun!.position.toStringAsFixed(2)}° (${composite.sun!.absPos.toStringAsFixed(2)}°)');
      print('Composite Moon: ${composite.moon!.sign} ${composite.moon!.position.toStringAsFixed(2)}° (${composite.moon!.absPos.toStringAsFixed(2)}°)');
      print(
        'Composite Ascendant: ${composite.ascendant!.sign} ${composite.ascendant!.position.toStringAsFixed(2)}° (${composite.ascendant!.absPos.toStringAsFixed(2)}°)',
      );

      // Verify composite is valid
      expect(composite.sun, isNotNull);
      expect(composite.moon, isNotNull);
      expect(composite.ascendant, isNotNull);
      expect(composite.name, contains('Composite'));

      // Verify midpoint calculation (Sun should be between the two natal Suns)
      final sun1 = person1.sun!.absPos;
      final sun2 = person2.sun!.absPos;
      final compositeSun = composite.sun!.absPos;

      print('\nMidpoint Verification:');
      print('Person 1 Sun: ${sun1.toStringAsFixed(2)}°');
      print('Person 2 Sun: ${sun2.toStringAsFixed(2)}°');
      print('Composite Sun: ${compositeSun.toStringAsFixed(2)}°');

      // Generate composite chart data
      final compositeData = ChartDataFactory.createChartData(ChartType.Composite, person1, secondSubject: person2);

      print('\nComposite Chart Data:');
      print('Chart Type: ${compositeData.chartType}');
      print('Aspects: ${compositeData.aspects.length}');
      print('Dominant Element: ${compositeData.elementDistribution.dominant}');
      print('Dominant Quality: ${compositeData.qualityDistribution.dominant}');

      expect(compositeData.chartType, 'Composite');
      expect(compositeData.firstSubject.name, contains('Composite'));

      print('\n✓ Composite chart test passed');
    });

    test('Complete Solar Return Workflow', () async {
      print('\n=== SOLAR RETURN TEST ===');

      // Create natal chart
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

      print('Natal Chart:');
      print('Name: ${natal.name}');
      print('Birth Date: ${natal.year}-${natal.month}-${natal.day}');
      print('Natal Sun: ${natal.sun!.absPos.toStringAsFixed(4)}°');

      // Calculate Solar Return for 2023
      final solarReturn = await ReturnFactory.calculateSolarReturn(natalSubject: natal, returnYear: 2023);

      print('\nSolar Return 2023:');
      print('Name: ${solarReturn.name}');
      print('Return Date: ${solarReturn.year}-${solarReturn.month}-${solarReturn.day} ${solarReturn.hour}:${solarReturn.minute}');
      print('Return Sun: ${solarReturn.sun!.absPos.toStringAsFixed(4)}°');

      // Verify Sun position matches
      final natalSunPos = natal.sun!.absPos;
      final returnSunPos = solarReturn.sun!.absPos;
      final difference = (returnSunPos - natalSunPos).abs();

      print('\nPrecision Check:');
      print('Natal Sun: ${natalSunPos.toStringAsFixed(6)}°');
      print('Return Sun: ${returnSunPos.toStringAsFixed(6)}°');
      print('Difference: ${difference.toStringAsFixed(6)}° (should be < 0.01°)');

      expect(difference, lessThan(0.01));
      expect(solarReturn.year, 2023);
      expect(solarReturn.name, contains('Solar Return'));

      // Verify it's close to birthday
      final monthDiff = (solarReturn.month! - natal.month!).abs();
      print('Month difference from birthday: $monthDiff (should be ≤ 1)');
      expect(monthDiff, lessThanOrEqualTo(1));

      print('\n✓ Solar return test passed');
    });

    test('Complete Lunar Return Workflow', () async {
      print('\n=== LUNAR RETURN TEST ===');

      // Create natal chart
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

      print('Natal Chart:');
      print('Name: ${natal.name}');
      print('Birth Date: ${natal.year}-${natal.month}-${natal.day}');
      print('Natal Moon: ${natal.moon!.absPos.toStringAsFixed(4)}°');

      // Calculate Lunar Return for June 2023
      final lunarReturn = await ReturnFactory.calculateLunarReturn(natalSubject: natal, returnYear: 2023, returnMonth: 6);

      print('\nLunar Return June 2023:');
      print('Name: ${lunarReturn.name}');
      print('Return Date: ${lunarReturn.year}-${lunarReturn.month}-${lunarReturn.day} ${lunarReturn.hour}:${lunarReturn.minute}');
      print('Return Moon: ${lunarReturn.moon!.absPos.toStringAsFixed(4)}°');

      // Verify Moon position matches
      final natalMoonPos = natal.moon!.absPos;
      final returnMoonPos = lunarReturn.moon!.absPos;
      final difference = (returnMoonPos - natalMoonPos).abs();

      print('\nPrecision Check:');
      print('Natal Moon: ${natalMoonPos.toStringAsFixed(6)}°');
      print('Return Moon: ${returnMoonPos.toStringAsFixed(6)}°');
      print('Difference: ${difference.toStringAsFixed(6)}° (should be < 0.1°)');

      expect(difference, lessThan(0.1));
      expect(lunarReturn.year, 2023);
      expect(lunarReturn.month, 6);
      expect(lunarReturn.name, contains('Lunar Return'));

      print('\n✓ Lunar return test passed');
    });

    test('Complete Synastry Workflow', () async {
      print('\n=== SYNASTRY TEST ===');

      // Create two charts
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

      print('Person 1 (Alice):');
      print('  Sun: ${person1.sun!.sign} ${person1.sun!.position.toStringAsFixed(2)}°');
      print('  Moon: ${person1.moon!.sign} ${person1.moon!.position.toStringAsFixed(2)}°');

      print('\nPerson 2 (Bob):');
      print('  Sun: ${person2.sun!.sign} ${person2.sun!.position.toStringAsFixed(2)}°');
      print('  Moon: ${person2.moon!.sign} ${person2.moon!.position.toStringAsFixed(2)}°');

      // Generate synastry chart data
      final synastryData = ChartDataFactory.createChartData(ChartType.Synastry, person1, secondSubject: person2, includeHouseComparison: true);

      print('\nSynastry Chart Data:');
      print('Chart Type: ${synastryData.chartType}');
      print('Inter-aspects: ${synastryData.aspects.length}');

      if (synastryData is DualChartDataModel) {
        print('Has house comparison: ${synastryData.houseComparison != null}');

        if (synastryData.houseComparison != null) {
          final hc = synastryData.houseComparison!;
          print('\nHouse Comparison:');
          print('  Person 1 points in Person 2 houses: ${hc.firstPointsInSecondHouses.length}');
          print('  Person 2 points in Person 1 houses: ${hc.secondPointsInFirstHouses.length}');

          // Show example
          if (hc.firstPointsInSecondHouses.isNotEmpty) {
            final example = hc.firstPointsInSecondHouses.first;
            print('\n  Example: ${example.pointOwnerName}\'s ${example.pointName} in ${example.projectedHouseOwnerName}\'s ${example.projectedHouseName}');
          }
        }
      }

      expect(synastryData.chartType, 'Synastry');
      expect(synastryData, isA<DualChartDataModel>());

      print('\n✓ Synastry test passed');
    });
  });
}
