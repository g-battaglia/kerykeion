/// Horoscope MCP Server vs Local Kerykeion Dart Comparison Test
///
/// This test:
/// 1. Calls the remote MCP server (https://horoscope.plan4.house/mcp) with generate_natal_chart
/// 2. Calls the local kerykeion_dart package with the same birth data
/// 3. Compares planetary positions - they should match exactly (same Swiss Ephemeris engine)
///
/// Usage: ./run_tests.sh test/mcp_comparison_test.dart

import 'dart:math';
import 'package:test/test.dart';
import 'package:kerykeion_dart/kerykeion_dart.dart';
import 'package:mcp_dart/mcp_dart.dart';

/// Test birth data
class TestBirthData {
  final String name;
  final int year, month, day, hour, minute;
  final String city, nation, timezone;
  final double lat, lng;

  const TestBirthData({
    required this.name,
    required this.year,
    required this.month,
    required this.day,
    required this.hour,
    required this.minute,
    required this.city,
    required this.nation,
    required this.timezone,
    required this.lat,
    required this.lng,
  });

  Map<String, dynamic> toMcpArgs() => {
        'birth_year': year,
        'birth_month': month,
        'birth_day': day,
        'birth_hour': hour,
        'birth_minute': minute,
        'city': city,
        'nation': nation,
        'timezone': timezone,
        'latitude': lat,
        'longitude': lng,
      };

  @override
  String toString() => '$name ($year-$month-$day $hour:$minute, $city, $nation)';
}

/// Parse MCP server response to extract planetary positions
/// The server returns markdown tables with format:
/// | ☉ Sun | Ari | 15.23° | 1st | False |
class McpChartData {
  final Map<String, McpPlanetPosition> planets = {};
  final Map<String, McpHousePosition> houses = {};
  String? sunSign, moonSign, risingSign;

  McpChartData.parse(String responseText) {
    final lines = responseText.split('\n');

    for (final line in lines) {
      // Parse Big Three
      if (line.contains('**Sun Sign**:')) {
        sunSign = _extractSignAbbr(line);
      } else if (line.contains('**Moon Sign**:')) {
        moonSign = _extractSignAbbr(line);
      } else if (line.contains('**Rising Sign**:')) {
        risingSign = _extractSignAbbr(line);
      }

      // Parse planet table rows: | ☉ Sun | Ari | 15.23° | 1st | False |
      if (line.startsWith('|') && !line.contains('---') && !line.contains('Planet')) {
        final parts = line.split('|').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
        if (parts.length >= 4) {
          final planetName = _extractPlanetName(parts[0]);
          if (planetName != null && _isPlanetRow(parts)) {
            final sign = parts[1].trim();
            final degStr = parts[2].replaceAll('°', '').trim();
            final deg = double.tryParse(degStr);
            if (deg != null && _isValidSign(sign)) {
              final house = parts.length > 3 ? parts[3].trim() : '';
              final retro = parts.length > 4 ? parts[4].trim().toLowerCase() == 'true' : false;
              planets[planetName] = McpPlanetPosition(
                name: planetName,
                sign: sign,
                position: deg,
                house: house,
                retrograde: retro,
              );
            }
          }

          // Parse house table rows: | 1st | ♈ Ari | 15.23° |
          final houseNum = _extractHouseNumber(parts[0]);
          if (houseNum != null && parts.length >= 3) {
            final signPart = parts[1].trim();
            // Remove emoji prefix if present
            final sign = _extractSignFromHouseCol(signPart);
            final degStr = parts[2].replaceAll('°', '').trim();
            final deg = double.tryParse(degStr);
            if (deg != null && sign != null) {
              houses['House_$houseNum'] = McpHousePosition(
                number: houseNum,
                sign: sign,
                position: deg,
              );
            }
          }
        }
      }
    }
  }

  static String? _extractSignAbbr(String line) {
    // Line like: "- **Sun Sign**: Aries (양자리) ♈ at 15.23° (1st House)"
    final signMap = {
      'Aries': 'Ari', 'Taurus': 'Tau', 'Gemini': 'Gem', 'Cancer': 'Can',
      'Leo': 'Leo', 'Virgo': 'Vir', 'Libra': 'Lib', 'Scorpio': 'Sco',
      'Sagittarius': 'Sag', 'Capricorn': 'Cap', 'Aquarius': 'Aqu', 'Pisces': 'Pis',
    };
    for (final entry in signMap.entries) {
      if (line.contains(entry.key)) return entry.value;
    }
    return null;
  }

  static String? _extractPlanetName(String col) {
    // Column like "☉ Sun" or "☽ Moon"
    final names = [
      'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
      'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
      'North Node', 'South Node', 'Chiron', 'Lilith',
    ];
    for (final name in names) {
      if (col.contains(name)) return name;
    }
    return null;
  }

  static bool _isPlanetRow(List<String> parts) {
    if (parts.length < 3) return false;
    final sign = parts[1].trim();
    return _isValidSign(sign);
  }

  static bool _isValidSign(String s) {
    return ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir',
            'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'].contains(s);
  }

  static int? _extractHouseNumber(String col) {
    final match = RegExp(r'(\d+)(st|nd|rd|th)').firstMatch(col);
    if (match != null) {
      final num = int.tryParse(match.group(1)!);
      if (num != null && num >= 1 && num <= 12) return num;
    }
    return null;
  }

  static String? _extractSignFromHouseCol(String col) {
    // May be "♈ Ari" or just "Ari"
    final signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir',
                   'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];
    for (final sign in signs) {
      if (col.contains(sign)) return sign;
    }
    return null;
  }
}

class McpPlanetPosition {
  final String name, sign, house;
  final double position;
  final bool retrograde;

  McpPlanetPosition({
    required this.name,
    required this.sign,
    required this.position,
    this.house = '',
    this.retrograde = false,
  });

  @override
  String toString() => '$name: $sign ${position.toStringAsFixed(2)}° (House: $house, Retro: $retrograde)';
}

class McpHousePosition {
  final int number;
  final String sign;
  final double position;

  McpHousePosition({required this.number, required this.sign, required this.position});

  @override
  String toString() => 'House $number: $sign ${position.toStringAsFixed(2)}°';
}

/// Generate random test birth data
TestBirthData generateRandomBirthData(Random rng) {
  final cities = [
    ('Seoul', 'KR', 'Asia/Seoul', 37.5665, 126.9780),
    ('New York', 'US', 'America/New_York', 40.7128, -74.0060),
    ('London', 'GB', 'Europe/London', 51.5074, -0.1278),
    ('Tokyo', 'JP', 'Asia/Tokyo', 35.6762, 139.6503),
    ('Paris', 'FR', 'Europe/Paris', 48.8566, 2.3522),
    ('Sydney', 'AU', 'Australia/Sydney', -33.8688, 151.2093),
    ('Berlin', 'DE', 'Europe/Berlin', 52.5200, 13.4050),
    ('Mumbai', 'IN', 'Asia/Kolkata', 19.0760, 72.8777),
  ];

  final city = cities[rng.nextInt(cities.length)];
  final year = 1950 + rng.nextInt(60); // 1950-2009
  final month = 1 + rng.nextInt(12);
  final day = 1 + rng.nextInt(28); // safe for all months
  final hour = rng.nextInt(24);
  final minute = rng.nextInt(60);

  return TestBirthData(
    name: 'Test_${year}_${month}_${day}',
    year: year,
    month: month,
    day: day,
    hour: hour,
    minute: minute,
    city: city.$1,
    nation: city.$2,
    timezone: city.$3,
    lat: city.$4,
    lng: city.$5,
  );
}

/// Map Dart Sign enum to MCP server abbreviation
String signToAbbr(Sign sign) {
  return sign.name; // Sign.Ari -> "Ari"
}

void main() {
  const mcpServerUrl = 'https://horoscope.plan4.house/mcp';
  late Client mcpClient;
  late StreamableHttpClientTransport transport;

  setUpAll(() async {
    // Initialize local kerykeion
    print('Initializing local kerykeion_dart...');
    await AstrologicalSubjectFactory.initialize();
    print('Local kerykeion_dart initialized.');

    // Connect to remote MCP server
    print('Connecting to MCP server at $mcpServerUrl...');
    mcpClient = Client(
      Implementation(name: 'kerykeion-comparison-test', version: '1.0.0'),
    );
    transport = StreamableHttpClientTransport(
      Uri.parse(mcpServerUrl),
    );
    await mcpClient.connect(transport);
    print('MCP server connected. Server: ${mcpClient.getServerVersion()?.name}');
  });

  tearDownAll(() async {
    try {
      await mcpClient.close();
    } catch (_) {}
  });

  test('List MCP server tools', () async {
    final toolsResult = await mcpClient.listTools();
    print('\n=== Available MCP Tools ===');
    for (final tool in toolsResult.tools) {
      print('  - ${tool.name}: ${tool.description?.substring(0, min(80, tool.description?.length ?? 0))}...');
    }
    expect(toolsResult.tools, isNotEmpty);

    final toolNames = toolsResult.tools.map((t) => t.name).toList();
    expect(toolNames, contains('generate_natal_chart'));
  });

  test('Compare natal chart: MCP server vs local kerykeion_dart', () async {
    // Use a fixed seed for reproducibility
    final rng = Random(42);
    final birthData = generateRandomBirthData(rng);
    print('\n=== Test Birth Data ===');
    print(birthData);

    // --- 1. Call remote MCP server ---
    print('\n--- Calling MCP server generate_natal_chart ---');
    final mcpResult = await mcpClient.callTool(
      CallToolRequestParams(
        name: 'generate_natal_chart',
        arguments: {'birth_info': birthData.toMcpArgs()},
      ),
    );

    expect(mcpResult.isError ?? false, isFalse, reason: 'MCP server returned error');
    final mcpText = (mcpResult.content.first as TextContent).text;
    print('MCP server response (first 500 chars):');
    print(mcpText.substring(0, min(500, mcpText.length)));

    // Parse MCP response
    final mcpChart = McpChartData.parse(mcpText);
    print('\nParsed MCP planets: ${mcpChart.planets.keys.toList()}');
    for (final p in mcpChart.planets.values) {
      print('  MCP: $p');
    }

    // --- 2. Call local kerykeion_dart ---
    print('\n--- Calling local kerykeion_dart ---');
    final localChart = await AstrologicalSubjectFactory.createSubject(
      name: birthData.name,
      year: birthData.year,
      month: birthData.month,
      day: birthData.day,
      hour: birthData.hour,
      minute: birthData.minute,
      city: birthData.city,
      nation: birthData.nation,
      lng: birthData.lng,
      lat: birthData.lat,
      tzStr: birthData.timezone,
    );

    // Print local results
    final localPlanets = {
      'Sun': localChart.sun,
      'Moon': localChart.moon,
      'Mercury': localChart.mercury,
      'Venus': localChart.venus,
      'Mars': localChart.mars,
      'Jupiter': localChart.jupiter,
      'Saturn': localChart.saturn,
      'Uranus': localChart.uranus,
      'Neptune': localChart.neptune,
      'Pluto': localChart.pluto,
    };

    for (final entry in localPlanets.entries) {
      final p = entry.value;
      if (p != null) {
        print('  Local: ${entry.key}: ${signToAbbr(p.sign)} ${p.position.toStringAsFixed(2)}°');
      }
    }

    // --- 3. Compare results ---
    print('\n=== COMPARISON ===');
    int matched = 0, mismatched = 0;

    for (final entry in localPlanets.entries) {
      final planetName = entry.key;
      final localPlanet = entry.value;
      final mcpPlanet = mcpChart.planets[planetName];

      if (localPlanet == null) {
        print('⚠️  $planetName: local is null (skipping)');
        continue;
      }
      if (mcpPlanet == null) {
        print('⚠️  $planetName: not found in MCP response (skipping)');
        continue;
      }

      final localSign = signToAbbr(localPlanet.sign);
      final mcpSign = mcpPlanet.sign;
      final localPos = localPlanet.position;
      final mcpPos = mcpPlanet.position;
      final posDiff = (localPos - mcpPos).abs();

      if (localSign == mcpSign && posDiff < 0.01) {
        print('✅ $planetName: MATCH - $localSign ${localPos.toStringAsFixed(2)}° ≈ $mcpSign ${mcpPos.toStringAsFixed(2)}° (diff: ${posDiff.toStringAsFixed(4)}°)');
        matched++;
      } else if (localSign == mcpSign && posDiff < 0.1) {
        print('⚠️  $planetName: CLOSE - $localSign ${localPos.toStringAsFixed(2)}° ≈ $mcpSign ${mcpPos.toStringAsFixed(2)}° (diff: ${posDiff.toStringAsFixed(4)}°)');
        matched++; // Still count as match with small tolerance
      } else {
        print('❌ $planetName: MISMATCH - Local: $localSign ${localPos.toStringAsFixed(2)}° vs MCP: $mcpSign ${mcpPos.toStringAsFixed(2)}° (diff: ${posDiff.toStringAsFixed(4)}°)');
        mismatched++;
      }
    }

    print('\n=== RESULT: $matched matched, $mismatched mismatched ===');

    // All major planets should match (sign must be same, position within 0.1°)
    expect(mismatched, equals(0),
        reason: 'Some planetary positions did not match between MCP server and local kerykeion_dart');
  });

  test('Compare natal chart with multiple random births', () async {
    final rng = Random(123);
    const numTests = 3;
    int totalMatched = 0, totalMismatched = 0;

    for (int i = 0; i < numTests; i++) {
      final birthData = generateRandomBirthData(rng);
      print('\n--- Test ${i + 1}/$numTests: $birthData ---');

      // Call MCP server
      final mcpResult = await mcpClient.callTool(
        CallToolRequestParams(
          name: 'generate_natal_chart',
          arguments: {'birth_info': birthData.toMcpArgs()},
        ),
      );

      if (mcpResult.isError ?? false) {
        print('MCP server error, skipping');
        continue;
      }

      final mcpText = (mcpResult.content.first as TextContent).text;
      final mcpChart = McpChartData.parse(mcpText);

      // Call local kerykeion
      final localChart = await AstrologicalSubjectFactory.createSubject(
        name: birthData.name,
        year: birthData.year,
        month: birthData.month,
        day: birthData.day,
        hour: birthData.hour,
        minute: birthData.minute,
        city: birthData.city,
        nation: birthData.nation,
        lng: birthData.lng,
        lat: birthData.lat,
        tzStr: birthData.timezone,
      );

      // Compare main planets
      final localPlanets = {
        'Sun': localChart.sun,
        'Moon': localChart.moon,
        'Mercury': localChart.mercury,
        'Venus': localChart.venus,
        'Mars': localChart.mars,
        'Jupiter': localChart.jupiter,
        'Saturn': localChart.saturn,
        'Uranus': localChart.uranus,
        'Neptune': localChart.neptune,
        'Pluto': localChart.pluto,
      };

      for (final entry in localPlanets.entries) {
        final localPlanet = entry.value;
        final mcpPlanet = mcpChart.planets[entry.key];
        if (localPlanet == null || mcpPlanet == null) continue;

        final localSign = signToAbbr(localPlanet.sign);
        final posDiff = (localPlanet.position - mcpPlanet.position).abs();

        if (localSign == mcpPlanet.sign && posDiff < 0.1) {
          totalMatched++;
        } else {
          print('  ❌ ${entry.key}: Local=${localSign} ${localPlanet.position.toStringAsFixed(2)}° vs MCP=${mcpPlanet.sign} ${mcpPlanet.position.toStringAsFixed(2)}°');
          totalMismatched++;
        }
      }
    }

    print('\n=== TOTAL: $totalMatched matched, $totalMismatched mismatched across $numTests tests ===');
    expect(totalMismatched, equals(0),
        reason: 'Some positions mismatched across multiple random birth tests');
  });
}
