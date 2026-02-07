import 'package:sweph/sweph.dart' as swe;
import 'package:kerykeion_dart/src/models/astrological_subject.dart';
import 'package:kerykeion_dart/src/models/kerykeion_point.dart';

import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/utilities.dart';
import 'package:kerykeion_dart/src/constants.dart';
import 'package:kerykeion_dart/src/settings/chart_defaults.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz_data;

class AstrologicalSubjectFactory {
  static bool _swephInitialized = false;

  /// Initialize timezone data and Sweph engine.
  /// [ephePath] - writable directory for ephemeris files (required on mobile).
  /// [epheAssets] - list of bundled asset paths to load.
  /// [assetLoader] - custom asset loader (e.g. rootBundle-based for Flutter).
  /// If Sweph has already been initialized externally, set [skipSwephInit] to true.
  static Future<void> initialize({String? ephePath, List<String>? epheAssets, dynamic assetLoader, bool skipSwephInit = false}) async {
    tz_data.initializeTimeZones();
    if (!skipSwephInit && !_swephInitialized) {
      await swe.Sweph.init(epheFilesPath: ephePath, epheAssets: epheAssets ?? [], assetLoader: assetLoader);
      _swephInitialized = true;
    }
  }

  static Future<AstrologicalSubjectModel> createSubject({
    required String name,
    required int year,
    required int month,
    required int day,
    required int hour,
    required int minute,
    required String city,
    required String nation,
    required double lng,
    required double lat,
    required String tzStr,
    ZodiacType zodiacType = ZodiacType.Tropical,
    SiderealMode? siderealMode,
    HousesSystemIdentifier housesSystemIdentifier = HousesSystemIdentifier.P,
    PerspectiveType perspectiveType = PerspectiveType.Apparent_Geocentric,
    List<AstrologicalPoint>? activePoints,
  }) async {
    // 1. Calculate UTC time
    // Ensure timezone is initialized
    try {
      tz.getLocation(tzStr);
    } catch (_) {
      initialize();
    }

    tz.Location location;
    if (tzStr == 'UTC') {
      location = tz.UTC;
    } else {
      try {
        location = tz.getLocation(tzStr);
      } catch (_) {
        initialize();
        try {
          location = tz.getLocation(tzStr);
        } catch (e) {
          // Fallback to UTC or error
          print("Timezone $tzStr not found, using UTC. Error: $e");
          location = tz.UTC;
        }
      }
    }

    final localTime = tz.TZDateTime(location, year, month, day, hour, minute);
    final utcTime = localTime.toUtc();

    // 2. Calculate Julian Day
    final julianDay = datetimeToJulian(utcTime);

    // 3. Configure Sweph
    // Assume Sweph is initialized externally or default assets used.

    // Set Sidereal mode if needed
    if (zodiacType == ZodiacType.Sidereal) {
      // Need to map my SiderealMode (enum) to sweph's SiderealMode (class)
      // Assuming indexes match for now or use .value property if I can match name.
      // kerykeion_types.SiderealMode -> swe.SiderealMode
      // I'll use the index as value.
      final modeValue = siderealMode?.index ?? 0;
      swe.Sweph.swe_set_sid_mode(swe.SiderealMode(modeValue), swe.SiderealModeFlag(0), 0.0);
    }

    // 4. Calculate Houses
    final houseSysChar = houseSysCodes[housesSystemIdentifier] ?? 'P';
    // Find matching Hsys enum
    final hsys = swe.Hsys.values.firstWhere((e) => e.value == houseSysChar.codeUnitAt(0), orElse: () => swe.Hsys.P);

    final houseResult = swe.Sweph.swe_houses(julianDay, lat, lng, hsys);
    final cusps = houseResult.cusps;
    final ascmc = houseResult.ascmc;

    // 5. Calculate Planets
    final calculatedPoints = <AstrologicalPoint, KerykeionPointModel>{};
    final pointsToCalc = activePoints ?? AstrologicalPoint.values;
    final resolvedActivePoints = activePoints ?? defaultActivePoints;

    var iflag = swe.SwephFlag.SEFLG_SWIEPH | swe.SwephFlag.SEFLG_SPEED;
    if (zodiacType == ZodiacType.Sidereal) {
      iflag |= swe.SwephFlag.SEFLG_SIDEREAL;
    }

    if (perspectiveType == PerspectiveType.Heliocentric) {
      iflag |= swe.SwephFlag.SEFLG_HELCTR;
    } else if (perspectiveType == PerspectiveType.True_Geocentric) {
      iflag |= swe.SwephFlag.SEFLG_TRUEPOS;
    } else if (perspectiveType == PerspectiveType.Topocentric) {
      iflag |= swe.SwephFlag.SEFLG_TOPOCTR;
      swe.Sweph.swe_set_topo(lng, lat, 0);
    }

    for (var point in pointsToCalc) {
      // Skip points that don't have direct ephemeris IDs
      if (point == AstrologicalPoint.Regulus ||
          point == AstrologicalPoint.Spica ||
          point == AstrologicalPoint.Pars_Fortunae ||
          point == AstrologicalPoint.Pars_Spiritus ||
          point == AstrologicalPoint.Pars_Amoris ||
          point == AstrologicalPoint.Pars_Fidei ||
          point == AstrologicalPoint.Vertex ||
          point == AstrologicalPoint.Anti_Vertex) {
        continue; // These are calculated separately
      }

      if (!pointNumberMap.containsKey(point)) continue;

      final pointId = pointNumberMap[point]!;

      try {
        // Handle south nodes as opposite of north nodes
        if (point == AstrologicalPoint.Mean_South_Lunar_Node) {
          if (calculatedPoints.containsKey(AstrologicalPoint.Mean_North_Lunar_Node)) {
            final northNode = calculatedPoints[AstrologicalPoint.Mean_North_Lunar_Node]!;
            final southLongitude = (northNode.absPos + 180) % 360;
            calculatedPoints[point] = getKerykeionPointFromDegree(
              southLongitude,
              point.toString().split('.').last,
              PointType.AstrologicalPoint,
              speed: -(northNode.speed ?? 0.0),
            );
          }
          continue;
        }

        if (point == AstrologicalPoint.True_South_Lunar_Node) {
          if (calculatedPoints.containsKey(AstrologicalPoint.True_North_Lunar_Node)) {
            final northNode = calculatedPoints[AstrologicalPoint.True_North_Lunar_Node]!;
            final southLongitude = (northNode.absPos + 180) % 360;
            calculatedPoints[point] = getKerykeionPointFromDegree(
              southLongitude,
              point.toString().split('.').last,
              PointType.AstrologicalPoint,
              speed: -(northNode.speed ?? 0.0),
            );
          }
          continue;
        }

        final result = swe.Sweph.swe_calc_ut(julianDay, swe.HeavenlyBody(pointId), iflag);

        final longitude = result.longitude;
        final speed = result.speedInLongitude;

        calculatedPoints[point] = getKerykeionPointFromDegree(
          longitude,
          point.toString().split('.').last,
          PointType.AstrologicalPoint,
          speed: speed,
          declination: result.latitude,
        );
      } catch (e) {
        print("Error calculating $point: $e");
      }
    }

    // Calculate Fixed Stars
    for (var point in pointsToCalc) {
      if (point == AstrologicalPoint.Regulus) {
        try {
          final result = swe.Sweph.swe_fixstar_ut(",Regulus", julianDay, iflag);
          calculatedPoints[point] = getKerykeionPointFromDegree(
            result.coordinates.longitude,
            "Regulus",
            PointType.AstrologicalPoint,
            speed: result.coordinates.speedInLongitude,
            declination: result.coordinates.latitude,
          );
        } catch (e) {
          print("Error calculating Regulus: $e");
        }
      } else if (point == AstrologicalPoint.Spica) {
        try {
          final result = swe.Sweph.swe_fixstar_ut(",Spica", julianDay, iflag);
          calculatedPoints[point] = getKerykeionPointFromDegree(
            result.coordinates.longitude,
            "Spica",
            PointType.AstrologicalPoint,
            speed: result.coordinates.speedInLongitude,
            declination: result.coordinates.latitude,
          );
        } catch (e) {
          print("Error calculating Spica: $e");
        }
      }
    }

    // Construct Houses
    final houses = <House, KerykeionPointModel>{};
    for (int i = 1; i <= 12; i++) {
      // cusps is 1-based usually, check sweph docs.
      // The list might be 0-based with 13 elements.
      double cuspDegree = 0.0;
      if (cusps.length > i) {
        cuspDegree = cusps[i];
      } else {
        cuspDegree = cusps[i - 1]; // Fallback if 0-based 12 elements
      }

      houses[houseNames[i]!] = getKerykeionPointFromDegree(cuspDegree, houseNames[i].toString().split('.').last, PointType.House);
    }

    // Construct Axes
    // ascmc[0] = Asc, ascmc[1] = MC, ascmc[2] = ARMC, ascmc[3] = Vertex
    final ascendant = getKerykeionPointFromDegree(ascmc[0], "Ascendant", PointType.AstrologicalPoint);
    final mc = getKerykeionPointFromDegree(ascmc[1], "Medium_Coeli", PointType.AstrologicalPoint);
    final descendant = getKerykeionPointFromDegree((ascmc[0] + 180) % 360, "Descendant", PointType.AstrologicalPoint);
    final ic = getKerykeionPointFromDegree((ascmc[1] + 180) % 360, "Imum_Coeli", PointType.AstrologicalPoint);

    // Vertex and Anti-Vertex (ascmc[3] contains Vertex)
    if (ascmc.length > 3 && pointsToCalc.contains(AstrologicalPoint.Vertex)) {
      final vertex = getKerykeionPointFromDegree(ascmc[3], "Vertex", PointType.AstrologicalPoint);
      calculatedPoints[AstrologicalPoint.Vertex] = vertex;
    }
    if (ascmc.length > 3 && pointsToCalc.contains(AstrologicalPoint.Anti_Vertex)) {
      final antiVertex = getKerykeionPointFromDegree((ascmc[3] + 180) % 360, "Anti_Vertex", PointType.AstrologicalPoint);
      calculatedPoints[AstrologicalPoint.Anti_Vertex] = antiVertex;
    }

    // Calculate Arabic Parts (require Asc, Sun, Moon to be calculated)
    if (calculatedPoints.containsKey(AstrologicalPoint.Sun) && calculatedPoints.containsKey(AstrologicalPoint.Moon)) {
      final sunPos = calculatedPoints[AstrologicalPoint.Sun]!.absPos;
      final moonPos = calculatedPoints[AstrologicalPoint.Moon]!.absPos;
      final ascPos = ascmc[0];

      // Determine if day or night chart (Sun above or below horizon)
      final isDayChart = sunPos >= ascPos ? (sunPos - ascPos <= 180) : (ascPos - sunPos > 180);

      // Pars Fortunae
      if (pointsToCalc.contains(AstrologicalPoint.Pars_Fortunae)) {
        final parsFortunae = isDayChart ? (ascPos + moonPos - sunPos) % 360 : (ascPos + sunPos - moonPos) % 360;
        calculatedPoints[AstrologicalPoint.Pars_Fortunae] = getKerykeionPointFromDegree(parsFortunae, "Pars_Fortunae", PointType.AstrologicalPoint);
      }

      // Pars Spiritus
      if (pointsToCalc.contains(AstrologicalPoint.Pars_Spiritus)) {
        final parsSpiritus = isDayChart ? (ascPos + sunPos - moonPos) % 360 : (ascPos + moonPos - sunPos) % 360;
        calculatedPoints[AstrologicalPoint.Pars_Spiritus] = getKerykeionPointFromDegree(parsSpiritus, "Pars_Spiritus", PointType.AstrologicalPoint);
      }

      // Pars Amoris (requires Venus)
      if (pointsToCalc.contains(AstrologicalPoint.Pars_Amoris) && calculatedPoints.containsKey(AstrologicalPoint.Venus)) {
        final venusPos = calculatedPoints[AstrologicalPoint.Venus]!.absPos;
        final parsAmoris = (ascPos + venusPos - sunPos) % 360;
        calculatedPoints[AstrologicalPoint.Pars_Amoris] = getKerykeionPointFromDegree(parsAmoris, "Pars_Amoris", PointType.AstrologicalPoint);
      }

      // Pars Fidei (requires Jupiter and Saturn)
      if (pointsToCalc.contains(AstrologicalPoint.Pars_Fidei) &&
          calculatedPoints.containsKey(AstrologicalPoint.Jupiter) &&
          calculatedPoints.containsKey(AstrologicalPoint.Saturn)) {
        final jupiterPos = calculatedPoints[AstrologicalPoint.Jupiter]!.absPos;
        final saturnPos = calculatedPoints[AstrologicalPoint.Saturn]!.absPos;
        final parsFidei = (ascPos + jupiterPos - saturnPos) % 360;
        calculatedPoints[AstrologicalPoint.Pars_Fidei] = getKerykeionPointFromDegree(parsFidei, "Pars_Fidei", PointType.AstrologicalPoint);
      }
    }

    // Assign house placement to each calculated planet/point
    final houseCuspDegrees = <double>[];
    for (int i = 1; i <= 12; i++) {
      houseCuspDegrees.add(houses[houseNames[i]!]!.absPos);
    }
    for (final point in calculatedPoints.values) {
      try {
        point.house = getPlanetHouse(point.absPos, houseCuspDegrees);
      } catch (e) {
        // If house can't be determined, leave as null
      }
    }
    // Also assign house to axes
    try {
      ascendant.house = getPlanetHouse(ascendant.absPos, houseCuspDegrees);
    } catch (_) {}
    try {
      mc.house = getPlanetHouse(mc.absPos, houseCuspDegrees);
    } catch (_) {}
    try {
      descendant.house = getPlanetHouse(descendant.absPos, houseCuspDegrees);
    } catch (_) {}
    try {
      ic.house = getPlanetHouse(ic.absPos, houseCuspDegrees);
    } catch (_) {}

    return AstrologicalSubjectModel(
      name: name,
      year: year,
      month: month,
      day: day,
      hour: hour,
      minute: minute,
      city: city,
      nation: nation,
      lng: lng,
      lat: lat,
      tzStr: tzStr,
      housesSystemIdentifier: housesSystemIdentifier,
      perspectiveType: perspectiveType,
      julianDay: julianDay,
      zodiacType: zodiacType,
      housesNamesList: House.values,
      activePoints: resolvedActivePoints,
      isoFormattedLocalDatetime: localTime.toIso8601String(),
      isoFormattedUtcDatetime: utcTime.toIso8601String(),
      dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][localTime.weekday - 1],

      firstHouse: houses[House.First_House]!,
      secondHouse: houses[House.Second_House]!,
      thirdHouse: houses[House.Third_House]!,
      fourthHouse: houses[House.Fourth_House]!,
      fifthHouse: houses[House.Fifth_House]!,
      sixthHouse: houses[House.Sixth_House]!,
      seventhHouse: houses[House.Seventh_House]!,
      eighthHouse: houses[House.Eighth_House]!,
      ninthHouse: houses[House.Ninth_House]!,
      tenthHouse: houses[House.Tenth_House]!,
      eleventhHouse: houses[House.Eleventh_House]!,
      twelfthHouse: houses[House.Twelfth_House]!,

      sun: calculatedPoints[AstrologicalPoint.Sun],
      moon: calculatedPoints[AstrologicalPoint.Moon],
      mercury: calculatedPoints[AstrologicalPoint.Mercury],
      venus: calculatedPoints[AstrologicalPoint.Venus],
      mars: calculatedPoints[AstrologicalPoint.Mars],
      jupiter: calculatedPoints[AstrologicalPoint.Jupiter],
      saturn: calculatedPoints[AstrologicalPoint.Saturn],
      uranus: calculatedPoints[AstrologicalPoint.Uranus],
      neptune: calculatedPoints[AstrologicalPoint.Neptune],
      pluto: calculatedPoints[AstrologicalPoint.Pluto],

      meanNorthLunarNode: calculatedPoints[AstrologicalPoint.Mean_North_Lunar_Node],
      trueNorthLunarNode: calculatedPoints[AstrologicalPoint.True_North_Lunar_Node],
      meanSouthLunarNode: calculatedPoints[AstrologicalPoint.Mean_South_Lunar_Node],
      trueSouthLunarNode: calculatedPoints[AstrologicalPoint.True_South_Lunar_Node],

      chiron: calculatedPoints[AstrologicalPoint.Chiron],
      meanLilith: calculatedPoints[AstrologicalPoint.Mean_Lilith],
      trueLilith: calculatedPoints[AstrologicalPoint.True_Lilith],
      earth: calculatedPoints[AstrologicalPoint.Earth],
      pholus: calculatedPoints[AstrologicalPoint.Pholus],

      ceres: calculatedPoints[AstrologicalPoint.Ceres],
      pallas: calculatedPoints[AstrologicalPoint.Pallas],
      juno: calculatedPoints[AstrologicalPoint.Juno],
      vesta: calculatedPoints[AstrologicalPoint.Vesta],

      eris: calculatedPoints[AstrologicalPoint.Eris],
      sedna: calculatedPoints[AstrologicalPoint.Sedna],
      haumea: calculatedPoints[AstrologicalPoint.Haumea],
      makemake: calculatedPoints[AstrologicalPoint.Makemake],
      ixion: calculatedPoints[AstrologicalPoint.Ixion],
      orcus: calculatedPoints[AstrologicalPoint.Orcus],
      quaoar: calculatedPoints[AstrologicalPoint.Quaoar],

      regulus: calculatedPoints[AstrologicalPoint.Regulus],
      spica: calculatedPoints[AstrologicalPoint.Spica],

      vertex: calculatedPoints[AstrologicalPoint.Vertex],
      antiVertex: calculatedPoints[AstrologicalPoint.Anti_Vertex],

      parsFortunae: calculatedPoints[AstrologicalPoint.Pars_Fortunae],
      parsSpiritus: calculatedPoints[AstrologicalPoint.Pars_Spiritus],
      parsAmoris: calculatedPoints[AstrologicalPoint.Pars_Amoris],
      parsFidei: calculatedPoints[AstrologicalPoint.Pars_Fidei],

      ascendant: ascendant,
      descendant: descendant,
      mediumCoeli: mc,
      imumCoeli: ic,

      lunarPhase: calculatedPoints.containsKey(AstrologicalPoint.Sun) && calculatedPoints.containsKey(AstrologicalPoint.Moon)
          ? calculateMoonPhase(calculatedPoints[AstrologicalPoint.Moon]!.absPos, calculatedPoints[AstrologicalPoint.Sun]!.absPos)
          : null,
    );
  }
}

// Map enum to char code string if needed, or use simple mapping
const Map<HousesSystemIdentifier, String> houseSysCodes = {
  HousesSystemIdentifier.P: 'P',
  HousesSystemIdentifier.K: 'K',
  HousesSystemIdentifier.R: 'R',
  HousesSystemIdentifier.C: 'C',
  HousesSystemIdentifier.E: 'E',
  HousesSystemIdentifier.W: 'W',
  HousesSystemIdentifier.M: 'M',
  HousesSystemIdentifier.H: 'H',
  HousesSystemIdentifier.T: 'T',
  HousesSystemIdentifier.O: 'O',
  HousesSystemIdentifier.B: 'B',
  // Add others
};
