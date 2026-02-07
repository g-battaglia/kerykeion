import 'dart:typed_data';

import 'package:universal_ffi/ffi.dart';
import 'abstract_asset_saver.dart';

typedef WriteFile = int Function(
  int path,
  int contents,
  int len,
  int forceOverwrite,
);

class SwephAssetSaver extends AbstractAssetSaver<DynamicLibrary, Allocator> {
  static SwephAssetSaver? _instance;

  DynamicLibrary library;
  late WriteFile writeFile;

  SwephAssetSaver._(super.epheFilesPath, this.library) {
    writeFile = library.lookupFunction<WriteFile, WriteFile>('write_file');
  }

  static Future<SwephAssetSaver> init(
      DynamicLibrary library, String epheFilesPath) async {
    _instance ??= SwephAssetSaver._(epheFilesPath, library);

    return _instance!;
  }

  // typedef for int write_file(const char* path, char* contents, size_t len, int forceOverwrite)

  @override
  Future<void> saveEpheFile(String destFile, Uint8List contents) async {
    final destPath = '$epheFilesPath/$destFile';

    final destPathPtr = _copyToWasm(Uint8List.fromList(destPath.codeUnits));
    final dataPtr = _copyToWasm(contents);

    // ignore: avoid_dynamic_calls
    writeFile.call(destPathPtr, dataPtr, contents.length, 0);

    library.module.free(destPathPtr);
  }

  int _copyToWasm(Uint8List data) {
    final size = data.length;
    final dataPtr = library.module.malloc(size + 1);
    final memoryView = library.module.heap.asUint8List();
    memoryView.setAll(dataPtr, data);
    memoryView[dataPtr + size] = 0;
    return dataPtr;
  }
}
