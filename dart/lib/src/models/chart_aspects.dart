import 'package:kerykeion_dart/src/models/astrological_subject.dart';
import 'package:kerykeion_dart/src/models/aspect_model.dart';
import 'package:kerykeion_dart/src/types.dart';

class SingleChartAspectsModel {
  final AstrologicalSubjectModel subject;
  final List<AspectModel> aspects;
  final List<AstrologicalPoint> activePoints;
  final List<ActiveAspect> activeAspects;

  const SingleChartAspectsModel({required this.subject, required this.aspects, required this.activePoints, required this.activeAspects});
}

class DualChartAspectsModel {
  final AstrologicalSubjectModel firstSubject;
  final AstrologicalSubjectModel secondSubject;
  final List<AspectModel> aspects;
  final List<AstrologicalPoint> activePoints;
  final List<ActiveAspect> activeAspects;

  const DualChartAspectsModel({
    required this.firstSubject,
    required this.secondSubject,
    required this.aspects,
    required this.activePoints,
    required this.activeAspects,
  });
}

// Legacy aliases
typedef NatalAspectsModel = SingleChartAspectsModel;
typedef SynastryAspectsModel = DualChartAspectsModel;
