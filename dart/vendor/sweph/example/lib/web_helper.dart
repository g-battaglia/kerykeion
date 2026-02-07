import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:sweph/sweph.dart';

class _WebAssetLoader implements AssetLoader {
  @override
  Future<Uint8List> load(String assetPath) async {
    final response = await http.get(Uri.parse('assets/$assetPath'));
    if (response.statusCode != 200) {
      throw Exception('Failed to load asset: $assetPath');
    }
    return response.bodyBytes;
  }
}

Future<void> initSweph([List<String> epheAssets = const []]) async {
  await Sweph.init(
    epheAssets: epheAssets,
    epheFilesPath: 'ephe_files',
    assetLoader: _WebAssetLoader(),
  );
}
