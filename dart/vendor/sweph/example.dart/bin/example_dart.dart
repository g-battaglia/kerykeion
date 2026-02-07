import 'package:example_dart/example.dart';

void printValue(String id, String value) {
  print('$id: $value');
}

Future<void> main(List<String> arguments) async {
  getSwephData()
      .then((result) => result.forEach((key, value) => printValue(key, value)));
}
