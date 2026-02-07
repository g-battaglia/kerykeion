import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/models/kerykeion_point.dart';

import 'package:kerykeion_dart/src/models/lunar_phase.dart';

class AstrologicalSubjectModel {
  /* Base Fields */
  String name;
  String? city;
  String? nation;
  double? lng;
  double? lat;
  String? tzStr;
  String? isoFormattedLocalDatetime;
  String? isoFormattedUtcDatetime;
  double? julianDay;
  String? dayOfWeek;
  ZodiacType? zodiacType;
  SiderealMode? siderealMode;
  HousesSystemIdentifier housesSystemIdentifier;
  String? housesSystemName;
  PerspectiveType perspectiveType;

  /* Planets */
  KerykeionPointModel? sun;
  KerykeionPointModel? moon;
  KerykeionPointModel? mercury;
  KerykeionPointModel? venus;
  KerykeionPointModel? mars;
  KerykeionPointModel? jupiter;
  KerykeionPointModel? saturn;
  KerykeionPointModel? uranus;
  KerykeionPointModel? neptune;
  KerykeionPointModel? pluto;

  /* Axes */
  KerykeionPointModel? ascendant;
  KerykeionPointModel? descendant;
  KerykeionPointModel? mediumCoeli;
  KerykeionPointModel? imumCoeli;

  /* Houses */
  KerykeionPointModel firstHouse;
  KerykeionPointModel secondHouse;
  KerykeionPointModel thirdHouse;
  KerykeionPointModel fourthHouse;
  KerykeionPointModel fifthHouse;
  KerykeionPointModel sixthHouse;
  KerykeionPointModel seventhHouse;
  KerykeionPointModel eighthHouse;
  KerykeionPointModel ninthHouse;
  KerykeionPointModel tenthHouse;
  KerykeionPointModel eleventhHouse;
  KerykeionPointModel twelfthHouse;

  /* Lunar Nodes */
  KerykeionPointModel? meanNorthLunarNode;
  KerykeionPointModel? trueNorthLunarNode;
  KerykeionPointModel? meanSouthLunarNode;
  KerykeionPointModel? trueSouthLunarNode;

  /* Other Points */
  KerykeionPointModel? chiron;
  KerykeionPointModel? meanLilith;
  KerykeionPointModel? trueLilith;
  KerykeionPointModel? earth;
  KerykeionPointModel? pholus;
  KerykeionPointModel? ceres;
  KerykeionPointModel? pallas;
  KerykeionPointModel? juno;
  KerykeionPointModel? vesta;
  KerykeionPointModel? eris;
  KerykeionPointModel? sedna;
  KerykeionPointModel? haumea;
  KerykeionPointModel? makemake;
  KerykeionPointModel? ixion;
  KerykeionPointModel? orcus;
  KerykeionPointModel? quaoar;
  KerykeionPointModel? regulus;
  KerykeionPointModel? spica;
  KerykeionPointModel? vertex;
  KerykeionPointModel? antiVertex;
  KerykeionPointModel? parsFortunae;
  KerykeionPointModel? parsSpiritus;
  KerykeionPointModel? parsAmoris;
  KerykeionPointModel? parsFidei;

  /* Birth Data */
  int? year;
  int? month;
  int? day;
  int? hour;
  int? minute;

  List<House> housesNamesList;
  List<AstrologicalPoint> activePoints;
  LunarPhaseModel? lunarPhase;

  AstrologicalSubjectModel({
    required this.name,
    this.city,
    this.nation,
    this.lng,
    this.lat,
    this.tzStr,
    this.isoFormattedLocalDatetime,
    this.isoFormattedUtcDatetime,
    this.julianDay,
    this.dayOfWeek,
    this.zodiacType,
    this.siderealMode,
    required this.housesSystemIdentifier,
    this.housesSystemName,
    required this.perspectiveType,

    this.sun,
    this.moon,
    this.mercury,
    this.venus,
    this.mars,
    this.jupiter,
    this.saturn,
    this.uranus,
    this.neptune,
    this.pluto,

    this.ascendant,
    this.descendant,
    this.mediumCoeli,
    this.imumCoeli,

    required this.firstHouse,
    required this.secondHouse,
    required this.thirdHouse,
    required this.fourthHouse,
    required this.fifthHouse,
    required this.sixthHouse,
    required this.seventhHouse,
    required this.eighthHouse,
    required this.ninthHouse,
    required this.tenthHouse,
    required this.eleventhHouse,
    required this.twelfthHouse,

    this.meanNorthLunarNode,
    this.trueNorthLunarNode,
    this.meanSouthLunarNode,
    this.trueSouthLunarNode,

    this.chiron,
    this.meanLilith,
    this.trueLilith,
    this.earth,
    this.pholus,
    this.ceres,
    this.pallas,
    this.juno,
    this.vesta,
    this.eris,
    this.sedna,
    this.haumea,
    this.makemake,
    this.ixion,
    this.orcus,
    this.quaoar,
    this.regulus,
    this.spica,
    this.vertex,
    this.antiVertex,
    this.parsFortunae,
    this.parsSpiritus,
    this.parsAmoris,
    this.parsFidei,

    this.year,
    this.month,
    this.day,
    this.hour,
    this.minute,

    required this.housesNamesList,
    required this.activePoints,
    this.lunarPhase,
  });

  Map<String, dynamic> toJson() {
    return {'name': name, 'sun': sun?.toString(), 'moon': moon?.toString()};
  }
}
