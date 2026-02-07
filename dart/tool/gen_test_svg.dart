import 'dart:io';
import 'package:kerykeion_dart/kerykeion_dart.dart';

void main() async {
  // 1. Initialize
  final epheDir = '${Directory.current.path}/ephe_files';
  await AstrologicalSubjectFactory.initialize(ephePath: epheDir);

  // 2. Create subject - same data as Python test
  final subject = await AstrologicalSubjectFactory.createSubject(
    name: 'Test',
    year: 1990,
    month: 6,
    day: 15,
    hour: 14,
    minute: 30,
    city: 'Seoul',
    nation: 'KR',
    lng: 126.978,
    lat: 37.5665,
    tzStr: 'Asia/Seoul',
  );

  // 3. Create chart data
  final chartData = ChartDataFactory.createChartData(ChartType.Natal, subject) as SingleChartDataModel;

  // 4. Draw SVG
  final drawer = NatalChartDrawer(chartData: chartData, theme: ChartTheme.classic);
  final svg = drawer.generateSvg();

  // 5. Write to file
  File('/tmp/dart_natal.svg').writeAsStringSync(svg);
  print('SVG written: ${svg.length} bytes');
}
