// ignore_for_file: hash_and_equals, constant_identifier_names

import 'dart:convert';
import 'dart:typed_data';
import 'package:universal_ffi/ffi.dart';
import 'package:universal_ffi/ffi_utils.dart';

N valueOf<T, N extends num>(dynamic val) {
  if (val is N) {
    return val;
  }
  if (val is AbstractVal<T, N>) {
    return val.value;
  }
  throw Exception('Invalid value');
}

abstract class AbstractVal<T, N extends num> {
  final N value;
  const AbstractVal(this.value);

  T create(N value);

  N _valueOf(dynamic other) {
    if (other is N) {
      return other;
    } else if (other is AbstractVal<T, N>) {
      return other.value;
    }
    throw Exception('Invalid value');
  }

  @override
  bool operator ==(Object other) {
    return value == _valueOf(other);
  }
}

abstract class AbstractEnum<T> extends AbstractVal<T, int> {
  const AbstractEnum(super.value);
}

abstract class AbstractConst<T, N extends num> extends AbstractVal<T, N> {
  const AbstractConst(super.value);

  T operator +(dynamic other) {
    return create((value + _valueOf(other)) as N);
  }

  T operator -(dynamic other) {
    return create((value + _valueOf(other)) as N);
  }

  T operator *(dynamic other) {
    return create((value * _valueOf(other)) as N);
  }

  T operator /(dynamic other) {
    return create((value / _valueOf(other)) as N);
  }
}

abstract class AbstractFlag<T> extends AbstractVal<T, int> {
  const AbstractFlag(super.value);

  T operator |(dynamic other) {
    return create(value | _valueOf(other));
  }

  T operator &(dynamic other) {
    return create(value & _valueOf(other));
  }
}

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

extension FfiHelperOnBool on bool {
  int get value {
    return this ? 1 : 0;
  }
}

/// Extension method for converting a`Pointer<Uint8>` to a [String].
extension Utf8Pointer on Pointer<Uint8> {
  /// The number of UTF-8 code units in this zero-terminated UTF-8 string.
  ///
  /// The UTF-8 code units of the strings are the non-zero code units up to the
  /// first zero code unit.
  int get length {
    _ensureNotNullptr('length');
    final codeUnits = cast<Uint8>();
    return _length(codeUnits);
  }

  /// Converts this UTF-8 encoded string to a Dart string.
  String toDartString({int? length}) {
    _ensureNotNullptr('toDartString');
    final codeUnits = cast<Uint8>();
    if (length != null) {
      RangeError.checkNotNegative(length, 'length');
    } else {
      length = _length(codeUnits);
    }
    return utf8.decode(codeUnits.asTypedList(length));
  }

  static int _length(Pointer<Uint8> codeUnits) {
    var length = 0;
    while (codeUnits[length] != 0) {
      length++;
    }
    return length;
  }

  void _ensureNotNullptr(String operation) {
    if (this == nullptr) {
      throw UnsupportedError(
          "Operation '$operation' not allowed on a 'nullptr'.");
    }
  }
}

/// Extension method for converting a [String] to a `Pointer<Uint8>`.
extension StringUtf8Pointer on String {
  /// Creates a zero-terminated [Uint8] code-unit array from this String.
  Pointer<Uint8> toNativeString(Allocator allocator, [int? size]) {
    final units = utf8.encode(this);
    size ??= units.length + 1;
    final Pointer<Uint8> result = allocator<Uint8>(size);
    final Uint8List nativeString = result.asTypedList(size);
    nativeString.setAll(0, units);
    nativeString[units.length] = 0;
    return result.cast();
  }

  int firstChar() {
    return (length > 0) ? codeUnitAt(0) : 0;
  }
}
