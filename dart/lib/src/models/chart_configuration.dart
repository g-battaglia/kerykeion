import '../types.dart';

class ChartConfiguration {
  ZodiacType zodiacType;
  SiderealMode? siderealMode;
  HousesSystemIdentifier housesSystemIdentifier;
  PerspectiveType perspectiveType;

  ChartConfiguration({
    this.zodiacType = ZodiacType.Tropical,
    this.siderealMode,
    this.housesSystemIdentifier = HousesSystemIdentifier.P,
    this.perspectiveType = PerspectiveType.Apparent_Geocentric,
  }) {
    validate();
  }

  void validate() {
    if (siderealMode != null && zodiacType == ZodiacType.Tropical) {
      throw Exception("You can't set a sidereal mode with a Tropical zodiac type!");
    }

    if (zodiacType == ZodiacType.Sidereal) {
      if (siderealMode == null) {
        siderealMode = SiderealMode.FAGAN_BRADLEY;
        print("No sidereal mode set, using default FAGAN_BRADLEY");
      }
    }
  }
}
