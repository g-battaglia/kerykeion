import 'dart:io';
import 'dart:typed_data';

import 'package:sweph/sweph.dart';

class _FileAssetLoader implements AssetLoader {
  @override
  Future<Uint8List> load(String assetPath) async {
    return await File('web/$assetPath').readAsBytes();
  }
}

Future<void> initSweph([List<String> epheAssets = const []]) async {
  final epheFilesPath = './.test';

  await Sweph.init(
    epheAssets: epheAssets,
    epheFilesPath: epheFilesPath,
    assetLoader: _FileAssetLoader(),
  );
}
