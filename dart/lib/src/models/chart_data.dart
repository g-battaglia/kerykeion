import '../types.dart';
import 'astrological_subject.dart';
import 'aspect_model.dart';
import 'distribution.dart';
import 'house_comparison.dart';

// Base class for Chart Data Models
abstract class ChartDataModel {
  final String chartType;
  final AstrologicalSubjectModel firstSubject;
  final List<AspectModel> aspects;
  final ElementDistributionModel elementDistribution;
  final QualityDistributionModel qualityDistribution;
  final List<AstrologicalPoint> activePoints;
  // final List<ActiveAspect> activeAspects; // TODO: Add ActiveAspect model if needed

  const ChartDataModel({
    required this.chartType,
    required this.firstSubject,
    required this.aspects,
    required this.elementDistribution,
    required this.qualityDistribution,
    required this.activePoints,
  });
}

/// Chart data model for single-subject astrological charts.
class SingleChartDataModel extends ChartDataModel {
  const SingleChartDataModel({
    required String chartType,
    required AstrologicalSubjectModel subject,
    required List<AspectModel> aspects,
    required ElementDistributionModel elementDistribution,
    required QualityDistributionModel qualityDistribution,
    required List<AstrologicalPoint> activePoints,
  }) : super(
         chartType: chartType,
         firstSubject: subject,
         aspects: aspects,
         elementDistribution: elementDistribution,
         qualityDistribution: qualityDistribution,
         activePoints: activePoints,
       );
}

/// Chart data model for dual-subject astrological charts.
class DualChartDataModel extends ChartDataModel {
  final AstrologicalSubjectModel secondSubject;
  final HouseComparisonModel? houseComparison;
  // final RelationshipScoreModel? relationshipScore; // TODO: Add RelationshipScoreModel if needed

  const DualChartDataModel({
    required String chartType,
    required AstrologicalSubjectModel firstSubject,
    required this.secondSubject,
    required List<AspectModel> aspects,
    required ElementDistributionModel elementDistribution,
    required QualityDistributionModel qualityDistribution,
    required List<AstrologicalPoint> activePoints,
    this.houseComparison,
  }) : super(
         chartType: chartType,
         firstSubject: firstSubject,
         aspects: aspects,
         elementDistribution: elementDistribution,
         qualityDistribution: qualityDistribution,
         activePoints: activePoints,
       );
}
