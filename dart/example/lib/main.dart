import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:kerykeion_dart/kerykeion_dart.dart';
import 'package:mcp_dart/mcp_dart.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sweph/sweph.dart' as swe;

// AssetLoader implementation for Flutter
class _RootBundleAssetLoader implements swe.AssetLoader {
  @override
  Future<Uint8List> load(String assetPath) async {
    return (await rootBundle.load(assetPath)).buffer.asUint8List();
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Get app directory for ephemeris files
  final dir = await getApplicationSupportDirectory();
  final ephePath = '${dir.path}/ephe_files';

  // Initialize sweph with bundled ephemeris assets
  await swe.Sweph.init(
    epheAssets: [
      'packages/sweph/assets/ephe/seas_18.se1', // Asteroids
      'packages/sweph/assets/ephe/semo_18.se1', // Moon
      'packages/sweph/assets/ephe/sepl_18.se1', // Planets
      'packages/sweph/assets/ephe/sefstars.txt', // Fixed stars
      'packages/sweph/assets/ephe/seasnam.txt', // Asteroid names
      'packages/sweph/assets/ephe/seleapsec.txt', // Leap seconds
      'packages/sweph/assets/ephe/seorbel.txt', // Orbital elements
    ],
    epheFilesPath: ephePath,
    assetLoader: _RootBundleAssetLoader(),
  );

  // Initialize kerykeion (uses the already-initialized sweph)
  await AstrologicalSubjectFactory.initialize();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kerykeion MCP Comparison',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple), useMaterial3: true),
      home: const ComparisonScreen(),
    );
  }
}

class ComparisonScreen extends StatefulWidget {
  const ComparisonScreen({super.key});

  @override
  State<ComparisonScreen> createState() => _ComparisonScreenState();
}

class _ComparisonScreenState extends State<ComparisonScreen> {
  final List<String> _logs = [];
  bool _isRunning = false;
  Client? _mcpClient;

  final _cities = [
    ('Seoul', 'KR', 'Asia/Seoul', 37.5665, 126.9780),
    ('New York', 'US', 'America/New_York', 40.7128, -74.0060),
    ('London', 'GB', 'Europe/London', 51.5074, -0.1278),
    ('Tokyo', 'JP', 'Asia/Tokyo', 35.6762, 139.6503),
    ('Paris', 'FR', 'Europe/Paris', 48.8566, 2.3522),
    ('Sydney', 'AU', 'Australia/Sydney', -33.8688, 151.2093),
  ];

  void _log(String message) {
    setState(() {
      _logs.add(message);
    });
  }

  Future<void> _connectMcpServer() async {
    if (_mcpClient != null) return;

    _log('Connecting to MCP server...');
    _mcpClient = Client(Implementation(name: 'kerykeion-flutter-test', version: '1.0.0'));
    final transport = StreamableHttpClientTransport(Uri.parse('https://horoscope.plan4.house/mcp'));
    await _mcpClient!.connect(transport);
    _log('✅ Connected: ${_mcpClient!.getServerVersion()?.name}');
  }

  Future<void> _runComparison() async {
    if (_isRunning) return;

    setState(() {
      _isRunning = true;
      _logs.clear();
    });

    try {
      await _connectMcpServer();

      // Generate random birth data
      final rng = Random();
      final city = _cities[rng.nextInt(_cities.length)];
      final year = 1970 + rng.nextInt(40);
      final month = 1 + rng.nextInt(12);
      final day = 1 + rng.nextInt(28);
      final hour = rng.nextInt(24);
      final minute = rng.nextInt(60);

      _log('\n📅 Birth Data:');
      _log('  $year-$month-$day $hour:$minute');
      _log('  ${city.$1}, ${city.$2}');
      _log('  ${city.$4}°N, ${city.$5}°E');

      // Call MCP server
      _log('\n🌐 Calling MCP server...');
      final mcpResult = await _mcpClient!.callTool(
        CallToolRequestParams(
          name: 'generate_natal_chart',
          arguments: {
            'birth_info': {
              'birth_year': year,
              'birth_month': month,
              'birth_day': day,
              'birth_hour': hour,
              'birth_minute': minute,
              'city': city.$1,
              'nation': city.$2,
              'timezone': city.$3,
              'latitude': city.$4,
              'longitude': city.$5,
            },
          },
        ),
      );

      if (mcpResult.isError ?? false) {
        _log('❌ MCP server error');
        return;
      }

      final mcpText = (mcpResult.content.first as TextContent).text;
      final mcpChart = _parseMcpChart(mcpText);
      _log('✅ MCP returned ${mcpChart.length} planets');

      // Call local kerykeion
      _log('\n📱 Calling local kerykeion...');
      final localChart = await AstrologicalSubjectFactory.createSubject(
        name: 'Test',
        year: year,
        month: month,
        day: day,
        hour: hour,
        minute: minute,
        city: city.$1,
        nation: city.$2,
        lng: city.$5,
        lat: city.$4,
        tzStr: city.$3,
      );

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

      _log('✅ Local computed ${localPlanets.length} planets');

      // Compare results
      _log('\n🔍 COMPARISON:');
      int matched = 0, mismatched = 0;

      for (final entry in localPlanets.entries) {
        final planetName = entry.key;
        final local = entry.value;
        final mcp = mcpChart[planetName];

        if (local == null || mcp == null) continue;

        final localSign = local.sign.name;
        final mcpSign = mcp.$1;
        final localPos = local.position;
        final mcpPos = mcp.$2;
        final diff = (localPos - mcpPos).abs();

        if (localSign == mcpSign && diff < 0.1) {
          _log('  ✅ $planetName: $localSign ${localPos.toStringAsFixed(2)}° (Δ ${diff.toStringAsFixed(4)}°)');
          matched++;
        } else {
          _log('  ❌ $planetName: Local=$localSign ${localPos.toStringAsFixed(2)}° vs MCP=$mcpSign ${mcpPos.toStringAsFixed(2)}°');
          mismatched++;
        }
      }

      _log('\n📊 RESULT: $matched matched, $mismatched mismatched');

      if (mismatched == 0) {
        _log('✅✅✅ ALL PLANETS MATCH! ✅✅✅');
      }
    } catch (e, stack) {
      _log('❌ Error: $e');
      _log('$stack');
    } finally {
      setState(() {
        _isRunning = false;
      });
    }
  }

  Map<String, (String, double)> _parseMcpChart(String text) {
    final result = <String, (String, double)>{};
    final lines = text.split('\n');

    for (final line in lines) {
      if (line.startsWith('|') && !line.contains('---') && !line.contains('Planet')) {
        final parts = line.split('|').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
        if (parts.length >= 3) {
          final planetName = _extractPlanetName(parts[0]);
          if (planetName != null) {
            final sign = parts[1].trim();
            final degStr = parts[2].replaceAll('°', '').trim();
            final deg = double.tryParse(degStr);
            if (deg != null && _isValidSign(sign)) {
              result[planetName] = (sign, deg);
            }
          }
        }
      }
    }

    return result;
  }

  String? _extractPlanetName(String col) {
    const names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'];
    for (final name in names) {
      if (col.contains(name)) return name;
    }
    return null;
  }

  bool _isValidSign(String s) {
    return ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'].contains(s);
  }

  @override
  void dispose() {
    _mcpClient?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(backgroundColor: Theme.of(context).colorScheme.inversePrimary, title: const Text('Kerykeion MCP Comparison')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isRunning ? null : _runComparison,
                icon: _isRunning ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.play_arrow),
                label: Text(_isRunning ? 'Running...' : 'Run Comparison Test'),
                style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(16)),
              ),
            ),
          ),
          const Divider(),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: _logs.length,
              itemBuilder: (context, index) {
                final log = _logs[index];
                final isError = log.startsWith('❌');
                final isSuccess = log.startsWith('✅');

                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Text(
                    log,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                      color: isError
                          ? Colors.red
                          : isSuccess
                          ? Colors.green
                          : Colors.black87,
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
