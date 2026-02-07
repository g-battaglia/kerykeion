
import '../types.dart';

class ZodiacSignModel {
  final Sign sign;
  final Quality quality;
  final Element element;
  final String emoji;
  final int signNum;

  const ZodiacSignModel({
    required this.sign,
    required this.quality,
    required this.element,
    required this.emoji,
    required this.signNum,
  });
}
