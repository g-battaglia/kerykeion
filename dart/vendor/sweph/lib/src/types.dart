// ignore_for_file: constant_identifier_names, non_constant_identifier_names

import 'package:universal_ffi/ffi.dart';
import 'package:universal_ffi/ffi_utils.dart';
import 'utils.dart';

const String libName = 'sweph';

/// Calendar type
class CalendarType extends AbstractEnum<CalendarType> {
  const CalendarType(super.value);

  @override
  CalendarType create(int value) {
    return CalendarType(value);
  }

  static const SE_JUL_CAL = CalendarType(0);
  static const SE_GREG_CAL = CalendarType(1);
}

/// numbers for planets and various heavenly bodies
class HeavenlyBody extends AbstractConst<HeavenlyBody, int> {
  const HeavenlyBody(super.value);

  @override
  HeavenlyBody create(int value) {
    return HeavenlyBody(value);
  }

  static const SE_ECL_NUT = EclipseFlag(-1);
  static const SE_FIXSTAR = HeavenlyBody(-10);

  static const SE_SUN = HeavenlyBody(0);
  static const SE_MOON = HeavenlyBody(1);
  static const SE_MERCURY = HeavenlyBody(2);
  static const SE_VENUS = HeavenlyBody(3);
  static const SE_MARS = HeavenlyBody(4);
  static const SE_JUPITER = HeavenlyBody(5);
  static const SE_SATURN = HeavenlyBody(6);
  static const SE_URANUS = HeavenlyBody(7);
  static const SE_NEPTUNE = HeavenlyBody(8);
  static const SE_PLUTO = HeavenlyBody(9);
  static const SE_MEAN_NODE = HeavenlyBody(10);
  static const SE_TRUE_NODE = HeavenlyBody(11);
  static const SE_MEAN_APOG = HeavenlyBody(12);
  static const SE_OSCU_APOG = HeavenlyBody(13);
  static const SE_EARTH = HeavenlyBody(14);
  static const SE_CHIRON = HeavenlyBody(15);
  static const SE_PHOLUS = HeavenlyBody(16);
  static const SE_CERES = HeavenlyBody(17);
  static const SE_PALLAS = HeavenlyBody(18);
  static const SE_JUNO = HeavenlyBody(19);
  static const SE_VESTA = HeavenlyBody(20);
  static const SE_INTP_APOG = HeavenlyBody(21);
  static const SE_INTP_PERG = HeavenlyBody(22);

  static const SE_NPLANETS = HeavenlyBody(23);

  static const SE_PLMOON_OFFSET = HeavenlyBody(9000);
  static const SE_AST_OFFSET = HeavenlyBody(10000);
  static final SE_VARUNA = SE_AST_OFFSET + 20000;

  static const SE_FICT_OFFSET = HeavenlyBody(40);
  static const SE_FICT_OFFSET_1 = HeavenlyBody(39);
  static const SE_FICT_MAX = HeavenlyBody(999);
  static const SE_NFICT_ELEM = HeavenlyBody(15);

  static const SE_COMET_OFFSET = HeavenlyBody(1000);

  static final SE_NALL_NAT_POINTS = SE_NPLANETS + SE_NFICT_ELEM;

  // Hamburger or Uranian "planets"
  static const SE_CUPIDO = HeavenlyBody(40);
  static const SE_HADES = HeavenlyBody(41);
  static const SE_ZEUS = HeavenlyBody(42);
  static const SE_KRONOS = HeavenlyBody(43);
  static const SE_APOLLON = HeavenlyBody(44);
  static const SE_ADMETOS = HeavenlyBody(45);
  static const SE_VULKANUS = HeavenlyBody(46);
  static const SE_POSEIDON = HeavenlyBody(47);
  // other fictitious bodies
  static const SE_ISIS = HeavenlyBody(48);
  static const SE_NIBIRU = HeavenlyBody(49);
  static const SE_HARRINGTON = HeavenlyBody(50);
  static const SE_NEPTUNE_LEVERRIER = HeavenlyBody(51);
  static const SE_NEPTUNE_ADAMS = HeavenlyBody(52);
  static const SE_PLUTO_LOWELL = HeavenlyBody(53);
  static const SE_PLUTO_PICKERING = HeavenlyBody(54);
  static const SE_VULCAN = HeavenlyBody(55);
  static const SE_WHITE_MOON = HeavenlyBody(56);
  static const SE_PROSERPINA = HeavenlyBody(57);
  static const SE_WALDEMATH = HeavenlyBody(58);
}

/// Flag bits for flag parameter in various methods
/// The flag bits are defined in such a way that iflag = 0 delivers what one
/// usually wants:
///    - the default ephemeris (SWISS EPHEMERIS) is used,
///    - apparent geocentric positions referring to the true equinox of date
///      are returned.
/// If not only coordinates, but also speed values are required, use
/// flag = SEFLG_SPEED.
class SwephFlag extends AbstractFlag<SwephFlag> {
  const SwephFlag(super.value);

  @override
  SwephFlag create(int value) {
    return SwephFlag(value);
  }

  /// use JPL ephemeris
  static const SEFLG_JPLEPH = SwephFlag(1);

  /// use SWISSEPH ephemeris
  static const SEFLG_SWIEPH = SwephFlag(2);

  /// use Moshier ephemeris
  static const SEFLG_MOSEPH = SwephFlag(4);

  /// heliocentric position
  static const SEFLG_HELCTR = SwephFlag(8);

  /// true/geometric position, not apparent position
  static const SEFLG_TRUEPOS = SwephFlag(16);

  /// no precession, i.e. give J2000 equinox
  static const SEFLG_J2000 = SwephFlag(32);

  /// no nutation, i.e. mean equinox of date
  static const SEFLG_NONUT = SwephFlag(64);

  /// speed from 3 positions (do not use it, SEFLG_SPEED is faster and more precise.)
  static const SEFLG_SPEED3 = SwephFlag(128);

  /// high precision speed
  static const SEFLG_SPEED = SwephFlag(256);

  /// turn off gravitational deflection
  static const SEFLG_NOGDEFL = SwephFlag(512);

  /// turn off 'annual' aberration of light
  static const SEFLG_NOABERR = SwephFlag(1024);

  /// astrometric position, i.e. with light-time, but without aberration and light deflection
  static final SEFLG_ASTROMETRIC = SEFLG_NOABERR | SEFLG_NOGDEFL;

  /// equatorial positions are wanted
  static const SEFLG_EQUATORIAL = SwephFlag(2 * 1024);

  /// cartesian, not polar, coordinates
  static const SEFLG_XYZ = SwephFlag(4 * 1024);

  /// coordinates in radians, not degrees
  static const SEFLG_RADIANS = SwephFlag(8 * 1024);

  /// barycentric position
  static const SEFLG_BARYCTR = SwephFlag(16 * 1024);

  /// topocentric position
  static const SEFLG_TOPOCTR = SwephFlag(32 * 1024);

  /// used for Astronomical Almanac mode in calculation of Kepler elipses
  static const SEFLG_ORBEL_AA = SEFLG_TOPOCTR;

  /// tropical position (default;
  static const SEFLG_TROPICAL = SwephFlag(0);

  /// sidereal position
  static const SEFLG_SIDEREAL = SwephFlag(64 * 1024);

  /// ICRS (DE406 reference frame;
  static const SEFLG_ICRS = SwephFlag(128 * 1024);

  /// reproduce JPL Horizons 1962 - today to 0.002 arcsec.
  static const SEFLG_DPSIDEPS_1980 = SwephFlag(256 * 1024);
  static const SEFLG_JPLHOR = SEFLG_DPSIDEPS_1980;

  /// approximate JPL Horizons 1962 - today
  static const SEFLG_JPLHOR_APPROX = SwephFlag(512 * 1024);

  /// calculate position of center of body (COB) of planet, not barycenter of its system
  static const SEFLG_CENTER_BODY = SwephFlag(1024 * 1024);

  /// test raw data in files sepm9*
  static final SEFLG_TEST_PLMOON = const SwephFlag(2 * 1024 * 1024) |
      SEFLG_J2000 |
      SEFLG_ICRS |
      SEFLG_HELCTR |
      SEFLG_TRUEPOS;
}

/// Additional flags to be used with SiderealMode
class SiderealModeFlag extends AbstractFlag<SiderealModeFlag> {
  const SiderealModeFlag(super.value);

  @override
  SiderealModeFlag create(int value) {
    return SiderealModeFlag(value);
  }

  /// None (default)
  static const SE_SIDBIT_NONE = SiderealModeFlag(0);

  /// for projection onto ecliptic of t0
  static const SE_SIDBIT_ECL_T0 = SiderealModeFlag(256);

  /// for projection onto solar system plane
  static const SE_SIDBIT_SSY_PLANE = SiderealModeFlag(512);

  /// with user-defined ayanamsha, t0 is UT
  static const SE_SIDBIT_USER_UT = SiderealModeFlag(1024);

  /// ayanamsha measured on ecliptic of date;
  static const SE_SIDBIT_ECL_DATE = SiderealModeFlag(2048);

  /// test feature: don't apply constant offset to ayanamsha
  static const SE_SIDBIT_NO_PREC_OFFSET = SiderealModeFlag(4096);

  /// test feature: calculate ayanamsha using its original precession model
  static const SE_SIDBIT_PREC_ORIG = SiderealModeFlag(8192);
}

/// Sidereal modes (ayanamsas)
class SiderealMode extends AbstractFlag<SiderealMode> {
  const SiderealMode(super.value);

  @override
  SiderealMode create(int value) {
    return SiderealMode(value);
  }

  static const SE_SIDM_FAGAN_BRADLEY = SiderealMode(0);
  static const SE_SIDM_LAHIRI = SiderealMode(1);
  static const SE_SIDM_DELUCE = SiderealMode(2);
  static const SE_SIDM_RAMAN = SiderealMode(3);
  static const SE_SIDM_USHASHASHI = SiderealMode(4);
  static const SE_SIDM_KRISHNAMURTI = SiderealMode(5);
  static const SE_SIDM_DJWHAL_KHUL = SiderealMode(6);
  static const SE_SIDM_YUKTESHWAR = SiderealMode(7);
  static const SE_SIDM_JN_BHASIN = SiderealMode(8);
  static const SE_SIDM_BABYL_KUGLER1 = SiderealMode(9);
  static const SE_SIDM_BABYL_KUGLER2 = SiderealMode(10);
  static const SE_SIDM_BABYL_KUGLER3 = SiderealMode(11);
  static const SE_SIDM_BABYL_HUBER = SiderealMode(12);
  static const SE_SIDM_BABYL_ETPSC = SiderealMode(13);
  static const SE_SIDM_ALDEBARAN_15TAU = SiderealMode(14);
  static const SE_SIDM_HIPPARCHOS = SiderealMode(15);
  static const SE_SIDM_SASSANIAN = SiderealMode(16);
  static const SE_SIDM_GALCENT_0SAG = SiderealMode(17);
  static const SE_SIDM_J2000 = SiderealMode(18);
  static const SE_SIDM_J1900 = SiderealMode(19);
  static const SE_SIDM_B1950 = SiderealMode(20);
  static const SE_SIDM_SURYASIDDHANTA = SiderealMode(21);
  static const SE_SIDM_SURYASIDDHANTA_MSUN = SiderealMode(22);
  static const SE_SIDM_ARYABHATA = SiderealMode(23);
  static const SE_SIDM_ARYABHATA_MSUN = SiderealMode(24);
  static const SE_SIDM_SS_REVATI = SiderealMode(25);
  static const SE_SIDM_SS_CITRA = SiderealMode(26);
  static const SE_SIDM_TRUE_CITRA = SiderealMode(27);
  static const SE_SIDM_TRUE_REVATI = SiderealMode(28);
  static const SE_SIDM_TRUE_PUSHYA = SiderealMode(29);
  static const SE_SIDM_GALCENT_RGILBRAND = SiderealMode(30);
  static const SE_SIDM_GALEQU_IAU1958 = SiderealMode(31);
  static const SE_SIDM_GALEQU_TRUE = SiderealMode(32);
  static const SE_SIDM_GALEQU_MULA = SiderealMode(33);
  static const SE_SIDM_GALALIGN_MARDYKS = SiderealMode(34);
  static const SE_SIDM_TRUE_MULA = SiderealMode(35);
  static const SE_SIDM_GALCENT_MULA_WILHELM = SiderealMode(36);
  static const SE_SIDM_ARYABHATA_522 = SiderealMode(37);
  static const SE_SIDM_BABYL_BRITTON = SiderealMode(38);
  static const SE_SIDM_TRUE_SHEORAN = SiderealMode(39);
  static const SE_SIDM_GALCENT_COCHRANE = SiderealMode(40);
  static const SE_SIDM_GALEQU_FIORENZA = SiderealMode(41);
  static const SE_SIDM_VALENS_MOON = SiderealMode(42);
  static const SE_SIDM_LAHIRI_1940 = SiderealMode(43);
  static const SE_SIDM_LAHIRI_VP285 = SiderealMode(44);
  static const SE_SIDM_KRISHNAMURTI_VP291 = SiderealMode(45);
  static const SE_SIDM_LAHIRI_ICRC = SiderealMode(46);

  /// user-defined ayanamsha, t0 is TT
  static const SE_SIDM_USER = SiderealMode(255);
}

class NodApsFlag extends AbstractFlag<NodApsFlag> {
  const NodApsFlag(super.value);

  @override
  NodApsFlag create(int value) {
    return NodApsFlag(value);
  }

  /// mean nodes/apsides
  static const SE_NODBIT_MEAN = NodApsFlag(1);

  /// osculating nodes/apsides
  static const SE_NODBIT_OSCU = NodApsFlag(2);

  /// same, but motion about solar system barycenter is considered
  static const SE_NODBIT_OSCU_BAR = NodApsFlag(4);

  /// focal point of orbit instead of aphelion
  static const SE_NODBIT_FOPOINT = NodApsFlag(256);
}

/// defines for eclipse computations
class EclipseFlag extends AbstractFlag<EclipseFlag> {
  const EclipseFlag(super.value);

  @override
  EclipseFlag create(int value) {
    return EclipseFlag(value);
  }

  static const SE_ECL_NOT_VILIBLE = EclipseFlag(0);
  static const SE_ECL_CENTRAL = EclipseFlag(1);
  static const SE_ECL_NONCENTRAL = EclipseFlag(2);
  static const SE_ECL_TOTAL = EclipseFlag(4);
  static const SE_ECL_ANNULAR = EclipseFlag(8);
  static const SE_ECL_PARTIAL = EclipseFlag(16);
  static const SE_ECL_ANNULAR_TOTAL = EclipseFlag(32);

  /// = annular-total
  static const SE_ECL_HYBRID = EclipseFlag(32);
  static const SE_ECL_PENUMBRAL = EclipseFlag(64);
  static final SE_ECL_ALLTYPES_SOLAR = SE_ECL_CENTRAL |
      SE_ECL_NONCENTRAL |
      SE_ECL_TOTAL |
      SE_ECL_ANNULAR |
      SE_ECL_PARTIAL |
      SE_ECL_ANNULAR_TOTAL;
  static final SE_ECL_ALLTYPES_LUNAR =
      SE_ECL_TOTAL | SE_ECL_PARTIAL | SE_ECL_PENUMBRAL;
  static const SE_ECL_VISIBLE = EclipseFlag(128);
  static const SE_ECL_MAX_VISIBLE = EclipseFlag(256);

  /// begin of partial eclipse
  static const SE_ECL_1ST_VISIBLE = EclipseFlag(512);

  /// begin of partial eclipse
  static const SE_ECL_PARTBEG_VISIBLE = EclipseFlag(512);

  /// begin of total eclipse
  static const SE_ECL_2ND_VISIBLE = EclipseFlag(1024);

  /// begin of total eclipse
  static const SE_ECL_TOTBEG_VISIBLE = EclipseFlag(1024);

  /// end of total eclipse
  static const SE_ECL_3RD_VISIBLE = EclipseFlag(2048);

  /// end of total eclipse
  static const SE_ECL_TOTEND_VISIBLE = EclipseFlag(2048);

  /// end of partial eclipse
  static const SE_ECL_4TH_VISIBLE = EclipseFlag(4096);

  /// end of partial eclipse
  static const SE_ECL_PARTEND_VISIBLE = EclipseFlag(4096);

  /// begin of penumbral eclipse
  static const SE_ECL_PENUMBBEG_VISIBLE = EclipseFlag(8192);

  /// end of penumbral eclipse
  static const SE_ECL_PENUMBEND_VISIBLE = EclipseFlag(16384);

  /// occultation begins during the day
  static const SE_ECL_OCC_BEG_DAYLIGHT = EclipseFlag(8192);

  /// occultation ends during the day
  static const SE_ECL_OCC_END_DAYLIGHT = EclipseFlag(16384);

  /// check if the next conjunction of the moon with a planet is an occultation; don't search further
  static const SE_ECL_ONE_TRY = EclipseFlag(32 * 1024);
}

/// Flags for Rise-Set methods
class RiseSetTransitFlag extends AbstractFlag<RiseSetTransitFlag> {
  const RiseSetTransitFlag(super.value);

  @override
  RiseSetTransitFlag create(int value) {
    return RiseSetTransitFlag(value);
  }

  static const SE_CALC_RISE = RiseSetTransitFlag(1);
  static const SE_CALC_SET = RiseSetTransitFlag(2);
  static const SE_CALC_MTRANSIT = RiseSetTransitFlag(4);
  static const SE_CALC_ITRANSIT = RiseSetTransitFlag(8);

  /// to be or'ed to SE_CALC_RISE/SET, if rise or set of disc center is required
  static const SE_BIT_DISC_CENTER = RiseSetTransitFlag(256);

  /// to be or'ed to SE_CALC_RISE/SET, if rise or set of lower limb of disc is requried
  static const SE_BIT_DISC_BOTTOM = RiseSetTransitFlag(8192);

  /// use geocentric rather than topocentric position of object and ignore its ecliptic latitude
  static const SE_BIT_GEOCTR_NO_ECL_LAT = RiseSetTransitFlag(128);

  /// to be or'ed to SE_CALC_RISE/SET, if refraction is to be ignored
  static const SE_BIT_NO_REFRACTION = RiseSetTransitFlag(512);

  /// to be or'ed to SE_CALC_RISE/SET
  static const SE_BIT_CIVIL_TWILIGHT = RiseSetTransitFlag(1024);

  /// to be or'ed to SE_CALC_RISE/SET
  static const SE_BIT_NAUTIC_TWILIGHT = RiseSetTransitFlag(2048);

  /// to be or'ed to SE_CALC_RISE/SET
  static const SE_BIT_ASTRO_TWILIGHT = RiseSetTransitFlag(4096);

  /// or'ed to SE_CALC_RISE/SET: neglect the effect of distance on disc size
  static const SE_BIT_FIXED_DISC_SIZE = RiseSetTransitFlag(16384);

  /// This is only an Astrodienst in-house test flag. It forces the usage of the old, slow calculation of risings and settings.
  static const SE_BIT_FORCE_SLOW_METHOD = RiseSetTransitFlag(32768);
  static const SE_BIT_HINDU_RISING = RiseSetTransitFlag(
      128 /* SE_BIT_GEOCTR_NO_ECL_LAT */ |
          256 /* SE_BIT_DISC_CENTER */ |
          512 /* SE_BIT_NO_REFRACTION */);
}

/// Modes for Azimuth/Altitude methods
class AzAltMode extends AbstractEnum<AzAltMode> {
  const AzAltMode(super.value);

  @override
  AzAltMode create(int value) {
    return AzAltMode(value);
  }

  static const SE_ECL2HOR = AzAltMode(0);
  static const SE_EQU2HOR = AzAltMode(1);
}

/// Modes for Reverse Azimuth/Altitude methods
class AzAltRevMode extends AbstractEnum<AzAltRevMode> {
  const AzAltRevMode(super.value);

  @override
  AzAltRevMode create(int value) {
    return AzAltRevMode(value);
  }

  static const SE_HOR2ECL = AzAltRevMode(0);
  static const SE_HOR2EQU = AzAltRevMode(1);
}

/// Modes for Refraction methods
class RefractionMode extends AbstractEnum<RefractionMode> {
  const RefractionMode(super.value);

  @override
  RefractionMode create(int value) {
    return RefractionMode(value);
  }

  static const SE_TRUE_TO_APP = RefractionMode(0);
  static const SE_APP_TO_TRUE = RefractionMode(1);
}

/// Flags for splitting centiseconds to degress
class SplitDegFlags extends AbstractFlag<SplitDegFlags> {
  const SplitDegFlags(super.value);

  @override
  SplitDegFlags create(int value) {
    return SplitDegFlags(value);
  }

  static const SE_SPLIT_DEG_ROUND_SEC = SplitDegFlags(1);
  static const SE_SPLIT_DEG_ROUND_MIN = SplitDegFlags(2);
  static const SE_SPLIT_DEG_ROUND_DEG = SplitDegFlags(4);
  static const SE_SPLIT_DEG_ZODIACAL = SplitDegFlags(8);
  static const SE_SPLIT_DEG_NAKSHATRA = SplitDegFlags(1024);

  /// don't round to next sign, e.g. 29.9999999 will be rounded to 29d59'59" (or 29d59' or 29d)
  static const SE_SPLIT_DEG_KEEP_SIGN = SplitDegFlags(16);

  /// don't round to next degree e.g. 13.9999999 will be rounded to 13d59'59" (or 13d59' or 13d)
  static const SE_SPLIT_DEG_KEEP_DEG = SplitDegFlags(32);
}

/// Event Types for heliacal functions
class HeliacalEventType extends AbstractEnum<HeliacalEventType> {
  const HeliacalEventType(super.value);

  @override
  HeliacalEventType create(int value) {
    return HeliacalEventType(value);
  }

  static const SE_HELIACAL_RISING = HeliacalEventType(1);
  static const SE_HELIACAL_SETTING = HeliacalEventType(2);
  static const SE_MORNING_FIRST = SE_HELIACAL_RISING;
  static const SE_EVENING_LAST = SE_HELIACAL_SETTING;
  static const SE_EVENING_FIRST = HeliacalEventType(3);
  static const SE_MORNING_LAST = HeliacalEventType(4);

  /// still not implemented
  static const SE_ACRONYCHAL_RISING = HeliacalEventType(5);

  /// still not implemented
  static const SE_ACRONYCHAL_SETTING = HeliacalEventType(6);
  static const SE_COSMICAL_SETTING = SE_ACRONYCHAL_SETTING;
}

class HeliacalFlags extends AbstractFlag<HeliacalFlags> {
  const HeliacalFlags(super.value);

  @override
  HeliacalFlags create(int value) {
    return HeliacalFlags(value);
  }

  static const SE_HELFLAG_LONG_SEARCH = HeliacalFlags(128);
  static const SE_HELFLAG_HIGH_PRECISION = HeliacalFlags(256);
  static const SE_HELFLAG_OPTICAL_PARAMS = HeliacalFlags(512);
  static const SE_HELFLAG_NO_DETAILS = HeliacalFlags(1024);
  static const SE_HELFLAG_SEARCH_1_PERIOD = HeliacalFlags(1 << 11); // 2048
  static const SE_HELFLAG_VISLIM_DARK = HeliacalFlags(1 << 12); // 4096
  static const SE_HELFLAG_VISLIM_NOMOON = HeliacalFlags(1 << 13); // 8192
}

/// House systems
enum Hsys {
  B(66), // Alcabitus
  Y(59), // APC houses
  X(58), // Axial rotation system / Meridian system / Zariel
  H(72), // Azimuthal or horizontal system
  C(67), // Campanus
  F(70), // Carter "Poli-Equatorial"
  A(65), // Equal (cusp 1 is Ascendant)
  E(69), // Equal (cusp 1 is Ascendant)
  D(68), // Equal MC (cusp 10 is MC)
  N(78), // Equal/1=Aries
  G(71), // Gauquelin sector
  //          Goelzer -> Krusinski
  //          Horizontal system -> Azimuthal system
  I(73), // Sunshine (Makransky, solution Treindl)
  i(105), // Sunshine (Makransky, solution Makransky)
  K(75), // Koch
  U(85), // Krusinski-Pisa-Goelzer
  //          Meridian system -> axial rotation
  M(77), // Morinus
  //          Neo-Porphyry -> Pullen SD
  //          Pisa -> Krusinski
  P(80), // Placidus
  //          Poli-Equatorial -> Carter
  T(84), // Polich/Page (topocentric system)
  O(79), // Porphyrius
  L(76), // Pullen SD (sinusoidal delta) – ex Neo-Porphyry
  Q(81), // Pullen SR (sinusoidal ratio)
  R(82), // Regiomontanus
  S(83), // Sripati
  //          Topocentric system -> Polich/Page
  V(86), // Vehlow equal (Asc. in middle of house 1)
  W(87); // Whole sign
  //          Zariel -> Axial rotation system

  const Hsys(this.value);
  final int value;
}

enum AscmcIndex {
  SE_ASC,
  SE_MC,
  SE_ARMC,
  SE_VERTEX,
  SE_EQUASC,

  /// "equatorial ascendant"
  SE_COASC1,

  /// "co-ascendant" (W. Koch)
  SE_COASC2,

  /// "co-ascendant" (M. Munkasey)
  SE_POLASC,

  /// "polar ascendant" (M. Munkasey)
  SE_NASCMC,
}

/// Visibility types
enum Visibility {
  BelowHorizon,
  PhotopicVision,
  ScotopicVision,
  NearLimitVision;

  static Visibility fromInt(int value) {
    switch (value) {
      case -2:
        return Visibility.BelowHorizon;
      case 0:
        return Visibility.PhotopicVision;
      case 1:
        return Visibility.ScotopicVision;
      case 2:
        return Visibility.NearLimitVision;
      default:
        throw ArgumentError('Invalid value: $value');
    }
  }
}

/// Flags for swe_gauquelin_sector
enum GauquelinMethod {
  WithLat(0),
  WithoutLat(1),
  FromRiseSet(2),
  FromRiseSetWithRefraction(3);

  const GauquelinMethod(this.value);
  final int value;
}

// ----------------------
// Various return objects
// ----------------------

/// Ecliptic or Equatorial coordinates
class Coordinates {
  final double longitude;
  final double latitude;
  final double distance;

  Coordinates(this.longitude, this.latitude, this.distance);

  Pointer<Double> toNativeArray(Arena arena) {
    final array = arena<Double>(3);
    array[0] = longitude;
    array[1] = latitude;
    array[2] = distance;
    return array;
  }

  @override
  String toString() {
    return 'Coordinates{longitude: $longitude, latitude: $latitude, distance: $distance}';
  }
}

/// Ecliptic or Equatorial coordinates with speed
class CoordinatesWithSpeed {
  final double longitude;
  final double latitude;
  final double distance;
  final double speedInLongitude;
  final double speedInLatitude;
  final double speedInDistance;

  CoordinatesWithSpeed(this.longitude, this.latitude, this.distance,
      this.speedInLongitude, this.speedInLatitude, this.speedInDistance);

  Pointer<Double> toNativeArray(Arena arena) {
    final array = arena<Double>(6);
    array[0] = longitude;
    array[1] = latitude;
    array[2] = distance;
    array[3] = speedInLongitude;
    array[4] = speedInLatitude;
    array[5] = speedInDistance;
    return array;
  }

  @override
  String toString() {
    return 'CoordinatesWithSpeed{longitude: $longitude, latitude: $latitude, distance: $distance, speedInLongitude: $speedInLongitude, speedInLatitude: $speedInLatitude, speedInDistance: $speedInDistance}';
  }
}

/// Geographic coordinates
class GeoPosition {
  final double longitude;
  final double latitude;
  final double altitude;

  GeoPosition(this.longitude, this.latitude, [this.altitude = 0]);

  Pointer<Double> toNativeArray(Arena arena) {
    final array = arena<Double>(3);
    array[0] = longitude;
    array[1] = latitude;
    array[2] = altitude;
    return array;
  }
}

/// Orbital distance of the body
class OrbitalDistance {
  final double maxDistance;
  final double minDistance;
  final double trueDistance;

  OrbitalDistance(this.maxDistance, this.minDistance, this.trueDistance);

  @override
  String toString() {
    return 'OrbitalDistance{maxDistance: $maxDistance, minDistance: $minDistance, trueDistance: $trueDistance}';
  }
}

/// Components when degrees in centiseconds are split into sign/nakshatra, degrees, minutes, seconds of arc
class DegreeSplitData {
  final int degrees;
  final int minutes;
  final int seconds;
  final double secondsOfArc;
  final int sign;

  DegreeSplitData(
      this.degrees, this.minutes, this.seconds, this.secondsOfArc, this.sign);

  @override
  String toString() {
    return 'DegreeSplitData{degrees: $degrees, minutes: $minutes, seconds: $seconds, secondsOfArc: $secondsOfArc, sign: $sign}';
  }
}

/// House cusp abs asmc data with optional speed components
class HouseCuspData {
  final List<double> cusps;
  final List<double> ascmc;
  final List<double>? cuspsSpeed;
  final List<double>? ascmcSpeed;

  HouseCuspData(this.cusps, this.ascmc, [this.cuspsSpeed, this.ascmcSpeed]);

  @override
  String toString() {
    return 'HouseCuspData{cusps: $cusps, ascmc: $ascmc, cuspsSpeed: $cuspsSpeed, ascmcSpeed: $ascmcSpeed}';
  }
}

/// House coordinates
class HousePosition {
  final double longitude;
  final double latitude;
  final double position;

  HousePosition(this.longitude, this.latitude, this.position);

  @override
  String toString() {
    return 'HousePosition{longitude: $longitude, latitude: $latitude, position: $position}';
  }
}

/// Information about crossing of heavenly body
class CrossingInfo {
  final double longitude;
  final double latitude;
  final double timeOfCrossing;

  CrossingInfo(this.longitude, this.latitude, this.timeOfCrossing);

  @override
  String toString() {
    return 'CrossingInfo{longitude: $longitude, latitude: $latitude, timeOfCrossing: $timeOfCrossing}';
  }
}

/// Atmospheric conditions data
///  data[0]: atmospheric pressure in mbar (hPa) ;
///  data[1]: atmospheric temperature in degrees Celsius;
///  data[2]: relative humidity in %;
///  data[3]: if data[3]>=1, then it is Meteorological Range [km] ;
///   if 1>data[3]>0, then it is the total atmospheric coefficient (ktot) ;
///  data[3]=0, then the other atmospheric parameters determine the total atmospheric coefficient (ktot)
class AtmosphericConditions {
  final List<double> data;

  AtmosphericConditions(this.data) {
    assert(data.length >= 4);
  }

  Pointer<Double> toNativeArray(Arena arena) {
    return data.toNativeString(arena);
  }

  @override
  String toString() {
    return 'AtmosphericConditions{data: $data}';
  }
}

/// Observer data
/// Details for data[] (array of six doubles):
///  data[0]: age of observer in years (default = 36)
///  data[1]: Snellen ratio of observers eyes (default = 1 = normal)
/// The following parameters are only relevant if the flag SE_HELFLAG_OPTICAL_PARAMS is set:
///  data[2]: 0 = monocular, 1 = binocular (actually a boolean)
///  data[3]: telescope magnification: 0 = default to naked eye (binocular), 1 = naked eye
///  data[4]: optical aperture (telescope diameter) in mm
///  data[5]: optical transmission
class ObserverConditions {
  final List<double> data;

  ObserverConditions(this.data) {
    assert(data.length >= 6);
  }

  Pointer<Double> toNativeArray(Arena arena) {
    return data.toNativeString(arena);
  }

  @override
  String toString() {
    return 'ObserverConditions{data: $data}';
  }
}

/// Nodes and apsides data with the following:
///  List of 6 positional values for ascending node
///  List of 6 positional values for descending node
///  List of 6 positional values for perihelion
///  List of 6 positional values for aphelion
class NodesAndAspides {
  final List<double> nodesAscending;
  final List<double> nodesDescending;
  final List<double> perihelion;
  final List<double> aphelion;

  NodesAndAspides(this.nodesAscending, this.nodesDescending, this.perihelion,
      this.aphelion);

  @override
  String toString() {
    return 'NodesAndAspides{nodesAscending: $nodesAscending, nodesDescending: $nodesDescending, perihelion: $perihelion, aphelion: $aphelion}';
  }
}

/// Eclipse information with the following:
///  List if eclipse times (refer to docs for details)
///  List of attributes (refer to docs for details)
///  Geographic position of eclipse
class EclipseInfo {
  final List<double>? times;
  final List<double>? attributes;
  final GeoPosition? geoPosition;
  final EclipseFlag? eclipseType;

  EclipseInfo(
      {this.times, this.attributes, this.geoPosition, this.eclipseType});

  @override
  String toString() {
    return 'EclipseInfo{times: $times, attributes: $attributes, geoPosition: $geoPosition, eclipseType: $eclipseType}';
  }
}

/// Details of loaded Ephemeris file
class FileData {
  final String path;
  final double startTime;
  final double endTime;
  final int jplEphemerisNumber;

  FileData(this.path, this.startTime, this.endTime, this.jplEphemerisNumber);

  @override
  String toString() {
    return 'FileData{path: $path, startTime: $startTime, endTime: $endTime, jplEphemerisNumber: $jplEphemerisNumber}';
  }
}

/// Star name and coordinates
class StarInfo {
  String name;
  CoordinatesWithSpeed coordinates;

  StarInfo(this.name, this.coordinates);

  @override
  String toString() {
    return 'StarInfo{name: $name, coordinates: $coordinates}';
  }
}

/// Azimuth and altitude info
class AzimuthAltitudeInfo {
  final double azimuth;
  final double trueAltitude;
  final double apparentAltitude;

  AzimuthAltitudeInfo(this.azimuth, this.trueAltitude, this.apparentAltitude);

  @override
  String toString() {
    return 'AzimuthAltitudeInfo{azimuth: $azimuth, trueAltitude: $trueAltitude, apparentAltitude: $apparentAltitude}';
  }
}

/// Altitude refraction info
class AltitudeRefracInfo {
  final double trueAlt;
  final double apparentAlt;
  final double? refraction;
  final double? dipOfTheHorizon;

  AltitudeRefracInfo(
    this.trueAlt,
    this.apparentAlt, [
    this.refraction,
    this.dipOfTheHorizon,
  ]);

  @override
  String toString() {
    return 'AltitudeRefracInfo{trueAltitude: $trueAlt, apparentAltitude: $apparentAlt, refraction: $refraction, dipOfTheHorizon: $dipOfTheHorizon}';
  }
}

/// Visibility info with the following in data:
///   0: limiting visual magnitude (if data[0] > magnitude of object, then the object is visible);
///   1: altitude of object;
///   2: azimuth of object;
///   3: altitude of sun;
///   4: azimuth of sun;
///   5: altitude of moon;
///   6: azimuth of moon;
///   7: magnitude of object.
class VisibilityInfo {
  final Visibility visibility;
  final List<double> data;

  VisibilityInfo(this.visibility, this.data);
}

typedef Centisec = int;
