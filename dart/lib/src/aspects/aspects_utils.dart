import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/models/astrological_subject.dart';
import 'package:kerykeion_dart/src/settings/chart_defaults.dart';
import 'package:kerykeion_dart/src/models/kerykeion_point.dart';

/// Utility class for aspect calculations
class AspectsUtils {
  /// Calculate the shortest distance between two points on a circle.
  /// Equivalent to Swiss Ephemeris difdeg2n.
  static double difdeg2n(double p1, double p2) {
    double diff = p1 - p2;
    while (diff <= -180.0) {
      diff += 360.0;
    }
    while (diff > 180.0) {
      diff -= 360.0;
    }
    return diff;
  }

  /// Utility function to calculate the aspects between two points.
  static Map<String, dynamic> getAspectFromTwoPoints(List<ChartAspectSetting> aspectsSettings, double pointOne, double pointTwo) {
    final distance = difdeg2n(pointOne, pointTwo).abs();
    final diff = (pointOne - pointTwo).abs();

    bool verdict = false;
    String name = "";
    double aspectDegrees = 0.0;
    double orbit = 0.0;

    for (var aspect in aspectsSettings) {
      final aspectDegree = aspect.degree.toDouble();
      final aspectOrb = aspect.orb?.toDouble() ?? 0.0;

      if ((aspectDegree - aspectOrb) <= distance && distance <= (aspectDegree + aspectOrb)) {
        name = aspect.name;
        aspectDegrees = aspectDegree;
        verdict = true;
        orbit = (distance - aspectDegrees).abs();
        break;
      }
    }

    return {"verdict": verdict, "name": name, "orbit": orbit, "distance": distance, "aspect_degrees": aspectDegrees, "diff": diff};
  }

  /// Determine whether the aspect orb is decreasing (Applying), increasing (Separating), or Static.
  static AspectMovementType calculateAspectMovement(
    double pointOneAbsPos,
    double pointTwoAbsPos,
    double aspectDegrees,
    double pointOneSpeed,
    double pointTwoSpeed,
  ) {
    // Constants for numerical precision
    const double speedEpsilon = 1e-9;
    const double orbEpsilon = 1e-6;
    const double dt = 0.001; // Time step for lookahead (approx 1.44 mins)

    // Validate positions
    if (pointOneAbsPos < 0 || pointOneAbsPos >= 360 || pointTwoAbsPos < 0 || pointTwoAbsPos >= 360) {
      // In Dart we might want to throw or handle gracefully.
      // For now, let's assume inputs are normalized.
      // If strict compliance: throw ArgumentError("Positions must be in range [0, 360)");
    }

    final relativeSpeed = (pointOneSpeed - pointTwoSpeed).abs();
    if (relativeSpeed < speedEpsilon) {
      return AspectMovementType.Static;
    }

    double getOrb(double p1, double p2, double aspect) {
      final diff = difdeg2n(p1, p2).abs();
      return (diff - aspect).abs();
    }

    // Normalize aspect
    double aspectNorm = aspectDegrees % 360.0;
    if (aspectNorm > 180.0) {
      aspectNorm = 360.0 - aspectNorm;
    }

    // 1. Current state
    final currentOrb = getOrb(pointOneAbsPos, pointTwoAbsPos, aspectNorm);

    // 2. Future state
    // Note: % 360.0 in Dart behaves correctly for positive numbers.
    // If speed is negative and result is negative, we might need to adjust.
    // Dart's % operator returns result with same sign as dividend.
    // So -10 % 360 = -10. We want 350.

    double normalize(double v) {
      v = v % 360.0;
      if (v < 0) v += 360.0;
      return v;
    }

    final p1FutureNorm = normalize(pointOneAbsPos + pointOneSpeed * dt);
    final p2FutureNorm = normalize(pointTwoAbsPos + pointTwoSpeed * dt);

    final futureOrb = getOrb(p1FutureNorm, p2FutureNorm, aspectNorm);

    // 3. Compare
    final orbChange = futureOrb - currentOrb;

    if (orbChange.abs() < orbEpsilon) {
      return AspectMovementType.Static;
    } else if (orbChange < 0) {
      return AspectMovementType.Applying;
    } else {
      return AspectMovementType.Separating;
    }
  }

  /// Helper to get active points from subject
  static List<KerykeionPointModel> getActivePointsList(AstrologicalSubjectModel subject, List<AstrologicalPoint>? activePoints) {
    // If activePoints is null/empty, we should probably return DEFAULT points?
    // The Python implementation takes active_points arg and if None, returns empty list?
    // Wait, Python: "if active_points is None: active_points = []".
    // Then iterates over DEFAULT_CELESTIAL_POINTS_SETTINGS.
    // If "planet['name'] in active_points", it appends.

    // In Dart factory, we call it with `subject.activePoints` usually.

    final pointsToFilter = activePoints ?? subject.activePoints;
    final List<KerykeionPointModel> result = [];

    // Map through default settings to maintain order?
    // Or just iterate through defaults and check if present in subject?

    // The Python implementation uses `celestial_points` setting to order.
    // We should do the same.

    for (var setting in defaultCelestialPointsSettings) {
      // Find the enum from string name
      AstrologicalPoint? pointEnum;
      try {
        pointEnum = AstrologicalPoint.values.firstWhere((e) => e.toString().split('.').last == setting.name);
      } catch (e) {
        // Point name in settings might not match enum exactly or not exist
        continue;
      }

      if (pointsToFilter.contains(pointEnum)) {
        // Get the point from the subject
        // Subject properties are named camelCase (sun, moon, etc.)
        // We need a way to access properties dynamically or via a map.
        // AstrologicalSubjectModel extends SubscriptableBaseModel in Python.
        // In Dart, we might need a helper method in the model or here.

        final point = _getPointFromSubject(subject, pointEnum);
        if (point != null) {
          result.add(point);
        }
      }
    }

    return result;
  }

  static KerykeionPointModel? _getPointFromSubject(AstrologicalSubjectModel subject, AstrologicalPoint point) {
    switch (point) {
      case AstrologicalPoint.Sun:
        return subject.sun;
      case AstrologicalPoint.Moon:
        return subject.moon;
      case AstrologicalPoint.Mercury:
        return subject.mercury;
      case AstrologicalPoint.Venus:
        return subject.venus;
      case AstrologicalPoint.Mars:
        return subject.mars;
      case AstrologicalPoint.Jupiter:
        return subject.jupiter;
      case AstrologicalPoint.Saturn:
        return subject.saturn;
      case AstrologicalPoint.Uranus:
        return subject.uranus;
      case AstrologicalPoint.Neptune:
        return subject.neptune;
      case AstrologicalPoint.Pluto:
        return subject.pluto;
      case AstrologicalPoint.Mean_North_Lunar_Node:
        return subject.meanNorthLunarNode;
      case AstrologicalPoint.True_North_Lunar_Node:
        return subject.trueNorthLunarNode;
      case AstrologicalPoint.Mean_South_Lunar_Node:
        return subject.meanSouthLunarNode;
      case AstrologicalPoint.True_South_Lunar_Node:
        return subject.trueSouthLunarNode;
      case AstrologicalPoint.Chiron:
        return subject.chiron;
      case AstrologicalPoint.Mean_Lilith:
        return subject.meanLilith;
      case AstrologicalPoint.True_Lilith:
        return subject.trueLilith;
      case AstrologicalPoint.Earth:
        return subject.earth;
      case AstrologicalPoint.Pholus:
        return subject.pholus;
      case AstrologicalPoint.Ceres:
        return subject.ceres;
      case AstrologicalPoint.Pallas:
        return subject.pallas;
      case AstrologicalPoint.Juno:
        return subject.juno;
      case AstrologicalPoint.Vesta:
        return subject.vesta;
      case AstrologicalPoint.Eris:
        return subject.eris;
      case AstrologicalPoint.Sedna:
        return subject.sedna;
      case AstrologicalPoint.Haumea:
        return subject.haumea;
      case AstrologicalPoint.Makemake:
        return subject.makemake;
      case AstrologicalPoint.Ixion:
        return subject.ixion;
      case AstrologicalPoint.Orcus:
        return subject.orcus;
      case AstrologicalPoint.Quaoar:
        return subject.quaoar;
      case AstrologicalPoint.Regulus:
        return subject.regulus;
      case AstrologicalPoint.Spica:
        return subject.spica;
      case AstrologicalPoint.Pars_Fortunae:
        return subject.parsFortunae;
      case AstrologicalPoint.Pars_Spiritus:
        return subject.parsSpiritus;
      case AstrologicalPoint.Pars_Amoris:
        return subject.parsAmoris;
      case AstrologicalPoint.Pars_Fidei:
        return subject.parsFidei;
      case AstrologicalPoint.Vertex:
        return subject.vertex;
      case AstrologicalPoint.Anti_Vertex:
        return subject.antiVertex;
      case AstrologicalPoint.Ascendant:
        return subject.ascendant;
      case AstrologicalPoint.Medium_Coeli:
        return subject.mediumCoeli;
      case AstrologicalPoint.Descendant:
        return subject.descendant;
      case AstrologicalPoint.Imum_Coeli:
        return subject.imumCoeli;
    }
  }

  static int getPlanetId(String name) {
    final setting = defaultCelestialPointsSettings.firstWhere(
      (element) => element.name == name,
      orElse: () => CelestialPointSetting(id: -1, name: name, color: "", elementPoints: 0, label: ""),
    );
    return setting.id;
  }
}
