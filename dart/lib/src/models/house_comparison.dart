/// Represents an astrological point from one subject positioned within another subject's house.
class PointInHouseModel {
  /// Name of the astrological point
  final String pointName;

  /// Degree position of the point within its zodiacal sign
  final double pointDegree;

  /// Zodiacal sign containing the point
  final String pointSign;

  /// Name of the subject who owns this point
  final String pointOwnerName;

  /// House number in owner's chart
  final int? pointOwnerHouseNumber;

  /// House name in owner's chart
  final String? pointOwnerHouseName;

  /// House number in target subject's chart
  final int projectedHouseNumber;

  /// House name in target subject's chart
  final String projectedHouseName;

  /// Name of the target subject
  final String projectedHouseOwnerName;

  const PointInHouseModel({
    required this.pointName,
    required this.pointDegree,
    required this.pointSign,
    required this.pointOwnerName,
    this.pointOwnerHouseNumber,
    this.pointOwnerHouseName,
    required this.projectedHouseNumber,
    required this.projectedHouseName,
    required this.projectedHouseOwnerName,
  });
}

/// Bidirectional house comparison analysis between two astrological subjects.
class HouseComparisonModel {
  /// Name of the first subject
  final String firstSubjectName;

  /// Name of the second subject
  final String secondSubjectName;

  /// First subject's points positioned in second subject's houses
  final List<PointInHouseModel> firstPointsInSecondHouses;

  /// Second subject's points positioned in first subject's houses
  final List<PointInHouseModel> secondPointsInFirstHouses;

  /// First subject's house cusps positioned in second subject's houses
  final List<PointInHouseModel> firstCuspsInSecondHouses;

  /// Second subject's house cusps positioned in first subject's houses
  final List<PointInHouseModel> secondCuspsInFirstHouses;

  const HouseComparisonModel({
    required this.firstSubjectName,
    required this.secondSubjectName,
    required this.firstPointsInSecondHouses,
    required this.secondPointsInFirstHouses,
    this.firstCuspsInSecondHouses = const [],
    this.secondCuspsInFirstHouses = const [],
  });
}
