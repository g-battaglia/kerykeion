import 'package:kerykeion_dart/src/types.dart';

class AspectModel {
  final String p1Name;
  final String p1Owner;
  final double p1AbsPos;
  final String p2Name;
  final String p2Owner;
  final double p2AbsPos;
  final String aspect;
  final double orbit;
  final int aspectDegrees;
  final double diff;
  final int p1;
  final int p2;
  final double p1Speed;
  final double p2Speed;
  final AspectMovementType aspectMovement;

  const AspectModel({
    required this.p1Name,
    required this.p1Owner,
    required this.p1AbsPos,
    required this.p2Name,
    required this.p2Owner,
    required this.p2AbsPos,
    required this.aspect,
    required this.orbit,
    required this.aspectDegrees,
    required this.diff,
    required this.p1,
    required this.p2,
    this.p1Speed = 0.0,
    this.p2Speed = 0.0,
    required this.aspectMovement,
  });

  Map<String, dynamic> toJson() {
    return {
      'p1_name': p1Name,
      'p1_owner': p1Owner,
      'p1_abs_pos': p1AbsPos,
      'p2_name': p2Name,
      'p2_owner': p2Owner,
      'p2_abs_pos': p2AbsPos,
      'aspect': aspect,
      'orbit': orbit,
      'aspect_degrees': aspectDegrees,
      'diff': diff,
      'p1': p1,
      'p2': p2,
      'p1_speed': p1Speed,
      'p2_speed': p2Speed,
      'aspect_movement': aspectMovement.toString().split('.').last,
    };
  }
}

class ActiveAspect {
  final String name;
  final int orb;

  const ActiveAspect({required this.name, required this.orb});

  Map<String, dynamic> toJson() {
    return {'name': name, 'orb': orb};
  }
}
