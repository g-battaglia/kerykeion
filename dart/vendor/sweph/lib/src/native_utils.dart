import 'dart:convert';
import 'dart:typed_data';

import 'package:universal_ffi/ffi.dart';
import 'package:universal_ffi/ffi_utils.dart';

extension FfiHelperOnDoubleList on List<double> {
  Pointer<Double> toNativeString(Arena arena) {
    final array = arena<Double>(length);
    for (int i = 0; i < length; i++) {
      array[i] = elementAt(i);
    }
    return array;
  }
}

extension FfiHelperOnDoublePointer on Pointer<Double> {
  List<double> toList(int length) {
    final list = <double>[];
    list.addAll(asTypedList(length));
    return list;
  }
}

extension FfiHelperOnCharPointer on Pointer<Uint8> {
  String toDartString() {
    return cast<Uint8>().toDartString();
  }
}

extension FfiHelperOnString on String {
  Pointer<Uint8> toNativeString(Allocator allocator, [int? size]) {
    size ??= length + 1;
    final Pointer<Uint8> result = allocator<Uint8>(size);
    final Uint8List nativeString = result.asTypedList(size);
    final units = utf8.encode(this);
    nativeString.setAll(0, units);
    nativeString[units.length] = 0;
    return result.cast();
  }

  int firstChar() {
    return (length > 0) ? codeUnitAt(0) : 0;
  }
}

extension FfiHelperOnBool on bool {
  int get value {
    return this ? 1 : 0;
  }
}
