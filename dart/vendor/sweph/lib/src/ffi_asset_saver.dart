// Notice that in this file, we import dart:ffi and not proxy_ffi.dart
import 'dart:io';
import 'dart:typed_data';

import 'package:path/path.dart';
import 'package:universal_ffi/ffi.dart';

import 'abstract_asset_saver.dart';

class SwephAssetSaver extends AbstractAssetSaver<DynamicLibrary, Allocator> {
  static SwephAssetSaver? _instance;

  SwephAssetSaver._(super.epheFilesPath);

  static Future<SwephAssetSaver> init(
      DynamicLibrary library, String epheFilesPath) async {
    if (_instance == null) {
      _instance = SwephAssetSaver._(epheFilesPath);

      final epheDir = Directory(epheFilesPath);
      epheDir.createSync(recursive: true);
    }

    return _instance!;
  }

  @override
  Future<void> saveEpheFile(String destFile, Uint8List contents) async {
    final destPath = File('$epheFilesPath/$destFile');
    if (destPath.existsSync()) {
      return;
    }
    destPath.writeAsBytesSync(contents);
  }

  @override
  void copyEpheDir(String epheFilesDir, bool forceOverwrite) {
    final srcDir = Directory(epheFilesDir);
    if (!srcDir.existsSync()) {
      return;
    }

    for (final file in srcDir.listSync()) {
      if (file is! File) {
        continue;
      }
      copyEpheFile(file.path, forceOverwrite);
    }
  }

  @override
  void copyEpheFile(String filePath, bool forceOverwrite) {
    final file = File(filePath);
    if (!file.existsSync()) {
      return;
    }

    final filename = basename(filePath);
    final destFile = File('$epheFilesPath/$filename');
    if (destFile.existsSync() && !forceOverwrite) {
      return;
    }

    destFile.writeAsBytesSync(file.readAsBytesSync());
  }
}
