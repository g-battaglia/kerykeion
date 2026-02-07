/// Quick test to isolate chart drawing hang.
import 'dart:io';
import 'package:kerykeion_dart/kerykeion_dart.dart';

void main() async {
  final stopwatch = Stopwatch()..start();
  void log(String msg) {
    print('[${stopwatch.elapsedMilliseconds}ms] $msg');
  }

  log('Initializing...');
  final epheDir = '${Directory.current.path}/ephe_files';
  await AstrologicalSubjectFactory.initialize(ephePath: epheDir);
  log('Initialized');

  log('Creating subject...');
  final subject = await AstrologicalSubjectFactory.createSubject(
    name: 'Test',
    year: 1990,
    month: 5,
    day: 15,
    hour: 14,
    minute: 30,
    city: 'Seoul',
    nation: 'KR',
    lng: 126.978,
    lat: 37.5665,
    tzStr: 'Asia/Seoul',
  );
  log('Subject created');

  log('Creating chart data...');
  final chartData = ChartDataFactory.createChartData(ChartType.Natal, subject) as SingleChartDataModel;
  log('Chart data created. Active points: ${chartData.activePoints.length}, Aspects: ${chartData.aspects.length}');

  log('Creating drawer...');
  final drawer = NatalChartDrawer(chartData: chartData, theme: ChartTheme.classic);
  log('Drawer created');

  log('Generating SVG...');
  final svg = drawer.generateSvg();
  log('SVG generated! Length: ${svg.length}');

  // Write to file for inspection
  final outFile = File('${Directory.current.path}/test_chart.svg');
  outFile.writeAsStringSync(svg);
  log('Written to ${outFile.path}');
}
