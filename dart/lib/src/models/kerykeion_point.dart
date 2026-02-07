import '../types.dart';

class KerykeionPointModel {
  String name; // Can be AstrologicalPoint or House name
  Quality quality;
  Element element;
  Sign sign;
  int signNum;
  double position;
  double absPos;
  String emoji;
  PointType pointType;
  House? house;
  bool? retrograde;
  double? speed;
  double? declination;

  KerykeionPointModel({
    required this.name,
    required this.quality,
    required this.element,
    required this.sign,
    required this.signNum,
    required this.position,
    required this.absPos,
    required this.emoji,
    required this.pointType,
    this.house,
    this.retrograde,
    this.speed,
    this.declination,
  });

  @override
  String toString() {
    return 'KerykeionPointModel(name: $name, absPos: $absPos, sign: $sign, position: $position, house: $house)';
  }
}
