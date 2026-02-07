import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sweph/sweph.dart';

class _RootBundleAssetLoader implements AssetLoader {
  @override
  Future<Uint8List> load(String assetPath) async {
    return (await rootBundle.load(assetPath)).buffer.asUint8List();
  }
}

Future<void> initSweph([List<String> epheAssets = const []]) async {
  final epheFilesPath =
      '${(await getApplicationSupportDirectory()).path}/ephe_files';

  await Sweph.init(
    epheAssets: epheAssets,
    epheFilesPath: epheFilesPath,
    assetLoader: _RootBundleAssetLoader(),
  );
}
