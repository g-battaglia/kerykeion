import '../types.dart';

/// Model representing lunar phase information.
class LunarPhaseModel {
  /// Angular separation between Sun and Moon in degrees.
  final double degreesBetweenSunAndMoon;

  /// Numerical phase identifier for the Moon (1-28).
  final int moonPhase;

  /// Emoji representation of the lunar phase.
  final String moonEmoji;

  /// Enum representation of the lunar phase.
  final LunarPhaseName moonPhaseName;

  const LunarPhaseModel({required this.degreesBetweenSunAndMoon, required this.moonPhase, required this.moonEmoji, required this.moonPhaseName});

  /// Dictionary-style access to fields for compatibility.
  dynamic operator [](String key) {
    switch (key) {
      case 'degrees_between_s_m':
        return degreesBetweenSunAndMoon;
      case 'moon_phase':
        return moonPhase;
      case 'moon_emoji':
        return moonEmoji;
      case 'moon_phase_name':
        return moonPhaseName.toString().split('.').last;
      default:
        return null;
    }
  }
}
