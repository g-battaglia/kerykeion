import '../types.dart';

/// Model representing element distribution in a chart.
class ElementDistributionModel {
  final double fire;
  final double earth;
  final double air;
  final double water;
  final int firePercentage;
  final int earthPercentage;
  final int airPercentage;
  final int waterPercentage;
  final Element? dominant;

  const ElementDistributionModel({
    required this.fire,
    required this.earth,
    required this.air,
    required this.water,
    required this.firePercentage,
    required this.earthPercentage,
    required this.airPercentage,
    required this.waterPercentage,
    this.dominant,
  });
}

/// Model representing quality distribution in a chart.
class QualityDistributionModel {
  final double cardinal;
  final double fixed;
  final double mutable;
  final int cardinalPercentage;
  final int fixedPercentage;
  final int mutablePercentage;
  final Quality? dominant;

  const QualityDistributionModel({
    required this.cardinal,
    required this.fixed,
    required this.mutable,
    required this.cardinalPercentage,
    required this.fixedPercentage,
    required this.mutablePercentage,
    this.dominant,
  });
}
