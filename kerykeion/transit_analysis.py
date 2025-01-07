from kerykeion import AstrologicalSubject
from kerykeion.aspects.synastry_aspects import SynastryAspects
from datetime import datetime
from typing import Optional, List
from kerykeion.kr_types import (
    TransitAnalysisModel,
    AspectModel,
    ZodiacType,
    SiderealMode,
    HousesSystemIdentifier,
    PerspectiveType
)
from kerykeion.astrological_subject import (
    DEFAULT_ZODIAC_TYPE,
    DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
    DEFAULT_PERSPECTIVE_TYPE
)
from kerykeion.kr_types.kr_literals import (
    AngularHouses
)


class TransitAnalysis:
    """Calculate and store complete transit analysis for a natal chart.

    Compares natal chart positions with current or specified transit positions.
    Calculates aspects between natal and transit placements.
    Handles house system calculations and aspect filtering.

    Key Features:
        - Natal chart creation and analysis
        - Transit time specification or current time
        - Aspect pattern detection
        - House system configuration
        - Angular house aspect filtering

    Example:
        >>> transit = TransitAnalysis(
        ...     "John Doe", 1990, 1, 1, 12, 0,
        ...     birth_city="London", birth_country="GB"
        ... )
        >>> print(f"Transit time: {transit.transit_time}")
        >>> print(f"Total aspects: {len(transit.aspects.all_aspects)}")
    """

    def __init__(self,
                 # Natal params
                 name: str,
                 birth_year: int,
                 birth_month: int,
                 birth_day: int,
                 birth_hour: int,
                 birth_minute: int,
                 birth_city: str,
                 birth_country: str,
                 birth_tz: Optional[str] = None,
                 birth_lng: Optional[float] = None,
                 birth_lat: Optional[float] = None,

                 # Transit params
                 transit_year: Optional[int] = None,
                 transit_month: Optional[int] = None,
                 transit_day: Optional[int] = None,
                 transit_hour: Optional[int] = None,
                 transit_minute: Optional[int] = None,
                 transit_city: Optional[str] = None,
                 transit_country: Optional[str] = None,
                 transit_tz: Optional[str] = None,
                 transit_lng: Optional[float] = None,
                 transit_lat: Optional[float] = None,
                 transit_time: Optional[datetime] = None,  # Convenience override

                 # Common config
                 zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
                 sidereal_mode: Optional[SiderealMode] = None,
                 houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
                 perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
                 online: bool = True,
                 disable_chiron_and_lilith: bool = False,
                 include_house_aspects: bool = False):
        """Initialize transit analysis.

        Args:
            name: Subject's name for natal chart
            birth_*: Natal chart parameters (year, month, day, hour, minute, city, country)
            birth_tz: Optional timezone string, default uses city lookup
            birth_lng/lat: Optional coordinates, default uses city lookup
            transit_*: Optional transit chart parameters, defaults to current time/location
            transit_time: Optional direct datetime override
            zodiac_type: "Tropic" or "Sidereal" system
            houses_system_identifier: House system (e.g., "Placidus")
            include_house_aspects: Include aspects to angular houses
        """
        # Store config setting
        self.include_house_aspects = include_house_aspects

        # Handle transit time
        self.transit_time = self._calculate_transit_time(
            transit_time, transit_year, transit_month,
            transit_day, transit_hour, transit_minute
        )

        # Create charts with config
        self.natal = AstrologicalSubject(
            name, birth_year, birth_month, birth_day, birth_hour, birth_minute,
            birth_city, birth_country,
            tz_str=birth_tz, lng=birth_lng, lat=birth_lat,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
            online=online,
            disable_chiron_and_lilith=disable_chiron_and_lilith
        )

        self.transit = AstrologicalSubject(
            "Transit",
            self.transit_time.year, self.transit_time.month, self.transit_time.day,
            self.transit_time.hour, self.transit_time.minute,
            transit_city or birth_city,
            transit_country or birth_country,
            tz_str=transit_tz or birth_tz,
            lng=transit_lng or birth_lng,
            lat=transit_lat or birth_lat,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
            online=online,
            disable_chiron_and_lilith=disable_chiron_and_lilith
        )

        # Calculate aspects and create model
        self.aspects = SynastryAspects(self.natal, self.transit)
        self.model = TransitAnalysisModel(
            natal=self.natal.model(),
            transit=self.transit.model(),
            aspects=self._get_aspect_models(),
            transit_time=self.transit_time,
            zodiac_type=zodiac_type,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
            sidereal_mode=sidereal_mode,
            online=online,
            disable_chiron_and_lilith=disable_chiron_and_lilith,
            include_house_aspects=include_house_aspects
        )

    def _get_aspect_models(self) -> List[AspectModel]:
        """Filter and convert aspects based on settings.

        Returns:
            List[AspectModel]: Filtered aspect list including:
                - All planet-to-planet aspects
                - Major aspects to angular houses if enabled
        """
        def is_angular_house(name: str) -> bool:
            return name in AngularHouses.__args__

        valid_aspects = [
            aspect for aspect in self.aspects.all_aspects
            if not ('House' in aspect.p1_name or 'House' in aspect.p2_name)
        ]

        if self.include_house_aspects:
            angular_aspects = [
                aspect for aspect in self.aspects.all_aspects
                if aspect.is_major and (
                    is_angular_house(aspect.p1_name) or is_angular_house(aspect.p2_name)
                )
            ]
            valid_aspects.extend(angular_aspects)

        return [AspectModel(
            p1_name=aspect.p1_name,
            p2_name=aspect.p2_name,
            p1_abs_pos=aspect.p1_abs_pos,
            p2_abs_pos=aspect.p2_abs_pos,
            aspect=aspect.aspect,
            aspect_degrees=aspect.aspect_degrees,
            orbit=aspect.orbit,
            aid=aspect.aid,
            diff=aspect.diff,
            p1=aspect.p1,
            p2=aspect.p2,
            is_major=aspect.is_major
        ) for aspect in valid_aspects]

    def _calculate_transit_time(self, transit_time, year, month, day, hour, minute) -> datetime:
        """Calculate transit time from parameters or use current time.

        Precedence:
        1. Use direct transit_time if provided
        2. Use individual components if any provided
        3. Default to current time
        """
        if transit_time:
            return transit_time
        if all(x is None for x in [year, month, day, hour, minute]):
            return datetime.now()
        return datetime(
            year or datetime.now().year,
            month or datetime.now().month,
            day or datetime.now().day,
            hour or datetime.now().hour,
            minute or datetime.now().minute
        )


if __name__ == "__main__":
    johnny_transit = TransitAnalysis(
        "Johnny Depp", 1963, 6, 9, 0, 0,
        birth_city="Owensboro", birth_country="US"
    )

    print("\nNATAL CHART CHECK:")
    print(f"Subject: {johnny_transit.natal.name}")

    for planet_name in johnny_transit.natal.planets_names_list:
        point = getattr(johnny_transit.natal, planet_name.lower())
        print(f"{point.name}: {point.sign} {point.position:.2f}° (House {point.house})")

    print("\nNatal Houses:")
    for house_name in johnny_transit.natal.houses_names_list:
        house = getattr(johnny_transit.natal, house_name.lower())
        print(f"{house.name}: {house.sign} {house.position:.2f}°")

    print("\nTRANSIT CHART CHECK:")
    print(f"Time: {johnny_transit.transit_time}")
    for planet_name in johnny_transit.transit.planets_names_list:
        point = getattr(johnny_transit.transit, planet_name.lower())
        print(f"{point.name}: {point.sign} {point.position:.2f}° (House {point.house})")

    print("\nASPECT PATTERNS:")
    print(f"Total aspects found: {len(johnny_transit.aspects.all_aspects)}")
    major_aspects = [a for a in johnny_transit.aspects.all_aspects if a.is_major]
    print(f"\nMajor aspects ({len(major_aspects)}):")
    for aspect in major_aspects[:5]:
        print(f"{aspect.p1_name} {aspect.aspect} {aspect.p2_name} (orbit: {aspect.orbit:.2f}°)")
