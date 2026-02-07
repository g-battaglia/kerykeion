import 'package:kerykeion_dart/src/models/aspect_model.dart';
import 'package:kerykeion_dart/src/types.dart';

class ChartAspectSetting {
  final int degree;
  final String name;
  final bool isMajor;
  final String color;
  final int? orb;

  const ChartAspectSetting({required this.degree, required this.name, required this.isMajor, required this.color, this.orb});
}

class CelestialPointSetting {
  final int id;
  final String name;
  final String color;
  final int elementPoints;
  final String label;
  final bool isActive;

  const CelestialPointSetting({
    required this.id,
    required this.name,
    required this.color,
    required this.elementPoints,
    required this.label,
    this.isActive = true,
  });
}

const List<CelestialPointSetting> defaultCelestialPointsSettings = [
  CelestialPointSetting(id: 0, name: "Sun", color: "var(--kerykeion-chart-color-sun)", elementPoints: 40, label: "Sun"),
  CelestialPointSetting(id: 1, name: "Moon", color: "var(--kerykeion-chart-color-moon)", elementPoints: 40, label: "Moon"),
  CelestialPointSetting(id: 2, name: "Mercury", color: "var(--kerykeion-chart-color-mercury)", elementPoints: 15, label: "Mercury"),
  CelestialPointSetting(id: 3, name: "Venus", color: "var(--kerykeion-chart-color-venus)", elementPoints: 15, label: "Venus"),
  CelestialPointSetting(id: 4, name: "Mars", color: "var(--kerykeion-chart-color-mars)", elementPoints: 15, label: "Mars"),
  CelestialPointSetting(id: 5, name: "Jupiter", color: "var(--kerykeion-chart-color-jupiter)", elementPoints: 10, label: "Jupiter"),
  CelestialPointSetting(id: 6, name: "Saturn", color: "var(--kerykeion-chart-color-saturn)", elementPoints: 10, label: "Saturn"),
  CelestialPointSetting(id: 7, name: "Uranus", color: "var(--kerykeion-chart-color-uranus)", elementPoints: 10, label: "Uranus"),
  CelestialPointSetting(id: 8, name: "Neptune", color: "var(--kerykeion-chart-color-neptune)", elementPoints: 10, label: "Neptune"),
  CelestialPointSetting(id: 9, name: "Pluto", color: "var(--kerykeion-chart-color-pluto)", elementPoints: 10, label: "Pluto"),
  CelestialPointSetting(
    id: 10,
    name: "Mean_North_Lunar_Node",
    color: "var(--kerykeion-chart-color-mean-node)",
    elementPoints: 0,
    label: "Mean_North_Lunar_Node",
  ),
  CelestialPointSetting(
    id: 11,
    name: "True_North_Lunar_Node",
    color: "var(--kerykeion-chart-color-true-node)",
    elementPoints: 0,
    label: "True_North_Lunar_Node",
  ),
  CelestialPointSetting(id: 12, name: "Chiron", color: "var(--kerykeion-chart-color-chiron)", elementPoints: 0, label: "Chiron"),
  CelestialPointSetting(id: 13, name: "Ascendant", color: "var(--kerykeion-chart-color-first-house)", elementPoints: 40, label: "Asc"),
  CelestialPointSetting(id: 14, name: "Medium_Coeli", color: "var(--kerykeion-chart-color-tenth-house)", elementPoints: 20, label: "Mc"),
  CelestialPointSetting(id: 15, name: "Descendant", color: "var(--kerykeion-chart-color-seventh-house)", elementPoints: 0, label: "Dsc"),
  CelestialPointSetting(id: 16, name: "Imum_Coeli", color: "var(--kerykeion-chart-color-fourth-house)", elementPoints: 0, label: "Ic"),
  CelestialPointSetting(id: 17, name: "Mean_Lilith", color: "var(--kerykeion-chart-color-mean-lilith)", elementPoints: 0, label: "Mean_Lilith"),
  CelestialPointSetting(
    id: 18,
    name: "Mean_South_Lunar_Node",
    color: "var(--kerykeion-chart-color-mean-node)",
    elementPoints: 0,
    label: "Mean_South_Lunar_Node",
  ),
  CelestialPointSetting(
    id: 19,
    name: "True_South_Lunar_Node",
    color: "var(--kerykeion-chart-color-true-node)",
    elementPoints: 0,
    label: "True_South_Lunar_Node",
  ),
  CelestialPointSetting(id: 20, name: "True_Lilith", color: "var(--kerykeion-chart-color-mean-lilith)", elementPoints: 0, label: "True_Lilith"),
  CelestialPointSetting(id: 21, name: "Earth", color: "var(--kerykeion-chart-color-earth)", elementPoints: 0, label: "Earth"),
  CelestialPointSetting(id: 22, name: "Pholus", color: "var(--kerykeion-chart-color-pholus)", elementPoints: 0, label: "Pholus"),
  CelestialPointSetting(id: 23, name: "Ceres", color: "var(--kerykeion-chart-color-ceres)", elementPoints: 0, label: "Ceres"),
  CelestialPointSetting(id: 24, name: "Pallas", color: "var(--kerykeion-chart-color-pallas)", elementPoints: 0, label: "Pallas"),
  CelestialPointSetting(id: 25, name: "Juno", color: "var(--kerykeion-chart-color-juno)", elementPoints: 0, label: "Juno"),
  CelestialPointSetting(id: 26, name: "Vesta", color: "var(--kerykeion-chart-color-vesta)", elementPoints: 0, label: "Vesta"),
  CelestialPointSetting(id: 27, name: "Eris", color: "var(--kerykeion-chart-color-eris)", elementPoints: 0, label: "Eris"),
  CelestialPointSetting(id: 28, name: "Sedna", color: "var(--kerykeion-chart-color-sedna)", elementPoints: 0, label: "Sedna"),
  CelestialPointSetting(id: 29, name: "Haumea", color: "var(--kerykeion-chart-color-haumea)", elementPoints: 0, label: "Haumea"),
  CelestialPointSetting(id: 30, name: "Makemake", color: "var(--kerykeion-chart-color-makemake)", elementPoints: 0, label: "Makemake"),
  CelestialPointSetting(id: 31, name: "Ixion", color: "var(--kerykeion-chart-color-ixion)", elementPoints: 0, label: "Ixion"),
  CelestialPointSetting(id: 32, name: "Orcus", color: "var(--kerykeion-chart-color-orcus)", elementPoints: 0, label: "Orcus"),
  CelestialPointSetting(id: 33, name: "Quaoar", color: "var(--kerykeion-chart-color-quaoar)", elementPoints: 0, label: "Quaoar"),
  CelestialPointSetting(id: 34, name: "Regulus", color: "var(--kerykeion-chart-color-regulus)", elementPoints: 0, label: "Regulus"),
  CelestialPointSetting(id: 35, name: "Spica", color: "var(--kerykeion-chart-color-spica)", elementPoints: 0, label: "Spica"),
  CelestialPointSetting(id: 36, name: "Pars_Fortunae", color: "var(--kerykeion-chart-color-pars-fortunae)", elementPoints: 5, label: "Fortune"),
  CelestialPointSetting(id: 37, name: "Pars_Spiritus", color: "var(--kerykeion-chart-color-pars-spiritus)", elementPoints: 0, label: "Spirit"),
  CelestialPointSetting(id: 38, name: "Pars_Amoris", color: "var(--kerykeion-chart-color-pars-amoris)", elementPoints: 0, label: "Love"),
  CelestialPointSetting(id: 39, name: "Pars_Fidei", color: "var(--kerykeion-chart-color-pars-fidei)", elementPoints: 0, label: "Faith"),
  CelestialPointSetting(id: 40, name: "Vertex", color: "var(--kerykeion-chart-color-vertex)", elementPoints: 0, label: "Vertex"),
  CelestialPointSetting(id: 41, name: "Anti_Vertex", color: "var(--kerykeion-chart-color-anti-vertex)", elementPoints: 0, label: "Anti_Vertex"),
];

const List<ChartAspectSetting> defaultChartAspectsSettings = [
  ChartAspectSetting(degree: 0, name: "conjunction", isMajor: true, color: "var(--kerykeion-chart-color-conjunction)"),
  ChartAspectSetting(degree: 30, name: "semi-sextile", isMajor: false, color: "var(--kerykeion-chart-color-semi-sextile)"),
  ChartAspectSetting(degree: 45, name: "semi-square", isMajor: false, color: "var(--kerykeion-chart-color-semi-square)"),
  ChartAspectSetting(degree: 60, name: "sextile", isMajor: true, color: "var(--kerykeion-chart-color-sextile)"),
  ChartAspectSetting(degree: 72, name: "quintile", isMajor: false, color: "var(--kerykeion-chart-color-quintile)"),
  ChartAspectSetting(degree: 90, name: "square", isMajor: true, color: "var(--kerykeion-chart-color-square)"),
  ChartAspectSetting(degree: 120, name: "trine", isMajor: true, color: "var(--kerykeion-chart-color-trine)"),
  ChartAspectSetting(degree: 135, name: "sesquiquadrate", isMajor: false, color: "var(--kerykeion-chart-color-sesquiquadrate)"),
  ChartAspectSetting(degree: 144, name: "biquintile", isMajor: false, color: "var(--kerykeion-chart-color-biquintile)"),
  ChartAspectSetting(degree: 150, name: "quincunx", isMajor: false, color: "var(--kerykeion-chart-color-quincunx)"),
  ChartAspectSetting(degree: 180, name: "opposition", isMajor: true, color: "var(--kerykeion-chart-color-opposition)"),
];

const List<ActiveAspect> defaultActiveAspects = [
  ActiveAspect(name: "conjunction", orb: 10),
  ActiveAspect(name: "opposition", orb: 10),
  ActiveAspect(name: "trine", orb: 8),
  ActiveAspect(name: "sextile", orb: 6),
  ActiveAspect(name: "square", orb: 5),
  ActiveAspect(name: "quintile", orb: 1),
];

const List<ActiveAspect> allActiveAspects = [
  ActiveAspect(name: "conjunction", orb: 10),
  ActiveAspect(name: "opposition", orb: 10),
  ActiveAspect(name: "trine", orb: 8),
  ActiveAspect(name: "sextile", orb: 6),
  ActiveAspect(name: "square", orb: 5),
  ActiveAspect(name: "quintile", orb: 1),
  ActiveAspect(name: "semi-sextile", orb: 1),
  ActiveAspect(name: "semi-square", orb: 1),
  ActiveAspect(name: "sesquiquadrate", orb: 1),
  ActiveAspect(name: "biquintile", orb: 1),
  ActiveAspect(name: "quincunx", orb: 1),
];

// Default active points list
const List<AstrologicalPoint> defaultActivePoints = [
  AstrologicalPoint.Sun,
  AstrologicalPoint.Moon,
  AstrologicalPoint.Mercury,
  AstrologicalPoint.Venus,
  AstrologicalPoint.Mars,
  AstrologicalPoint.Jupiter,
  AstrologicalPoint.Saturn,
  AstrologicalPoint.Uranus,
  AstrologicalPoint.Neptune,
  AstrologicalPoint.Pluto,
  AstrologicalPoint.True_North_Lunar_Node,
  AstrologicalPoint.True_South_Lunar_Node,
  AstrologicalPoint.Chiron,
  AstrologicalPoint.Mean_Lilith,
  AstrologicalPoint.Ascendant,
  AstrologicalPoint.Medium_Coeli,
  AstrologicalPoint.Descendant,
  AstrologicalPoint.Imum_Coeli,
];
