from kerykeion import AstrologicalSubject
from kerykeion.aspects.synastry_aspects import SynastryAspects
from kerykeion.utilities import get_houses_list, get_available_planets_list
from datetime import datetime
from typing import Optional, Dict, List, Union


class TransitAnalysis:
    """Calculate and store complete transit analysis for a natal chart.

    Provides transit analysis between a natal chart and current or specified time.
    Includes planetary positions, house placements, and aspect calculations.
    """

    def __init__(self,
                 name: str,
                 birth_year: int,
                 birth_month: int,
                 birth_day: int,
                 birth_hour: int,
                 birth_minute: int,
                 birth_place: str,
                 birth_country: str,
                 current_place: Optional[str] = None,
                 current_country: Optional[str] = None,
                 transit_time: Optional[datetime] = None,
                 zodiac_type: str = "Tropic",
                 sidereal_mode: Optional[str] = None,
                 houses_system: str = "P",
                 online: bool = True,
                 birth_tz: Optional[str] = None,
                 birth_lng: Optional[float] = None,
                 birth_lat: Optional[float] = None,
                 current_tz: Optional[str] = None,
                 current_lng: Optional[float] = None,
                 current_lat: Optional[float] = None):

        # Store transit time
        self.transit_time = transit_time or datetime.now()
        transit_dt = self.transit_time

        # Create natal chart
        self.natal = AstrologicalSubject(
            name, birth_year, birth_month, birth_day,
            birth_hour, birth_minute, birth_place, birth_country,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system,
            online=online,
            tz_str=birth_tz,
            lng=birth_lng,
            lat=birth_lat
        )

        # Create transit chart
        self.transit = AstrologicalSubject(
            "Transit", transit_dt.year, transit_dt.month, transit_dt.day,
            transit_dt.hour, transit_dt.minute,
            current_place or birth_place,
            current_country or birth_country,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system,
            online=online,
            tz_str=current_tz or birth_tz,
            lng=current_lng or birth_lng,
            lat=current_lat or birth_lat
        )

        self.aspects = SynastryAspects(self.natal, self.transit)

    def get_analysis(self) -> Dict:
        """Return complete transit analysis data."""
        return {
            "natal_chart": {
                "planets": self._get_planet_data(self.natal),
                "houses": self._get_house_data(self.natal),
                "ascendant": {
                    "sign": self.natal.first_house.sign,
                    "position": float(self.natal.first_house.position)
                },
                "midheaven": {
                    "sign": self.natal.tenth_house.sign,
                    "position": float(self.natal.tenth_house.position)
                },
                "lunar_phase": str(self.natal.lunar_phase)
            },
            "transit_chart": {
                "planets": self._get_planet_data(self.transit),
                "houses": self._get_house_data(self.transit),
                "ascendant": {
                    "sign": self.transit.first_house.sign,
                    "position": float(self.transit.first_house.position)
                },
                "midheaven": {
                    "sign": self.transit.tenth_house.sign,
                    "position": float(self.transit.tenth_house.position)
                },
                "lunar_phase": str(self.transit.lunar_phase)
            },
            "transit_aspects": self._get_aspect_data(),
            "metadata": {
                "zodiac_type": self.natal.zodiac_type,
                "houses_system_identifier": self.natal.houses_system_identifier,
                "houses_system_name": self.natal.houses_system_name,
                "calculation_time": datetime.now().isoformat()
            }
        }

    def _get_planet_data(self, chart: AstrologicalSubject) -> Dict:
        """Get formatted planet data from chart using utility function."""
        planets = get_available_planets_list(chart)
        return {p.name: {
            "sign": p.sign,
            "position": float(p.position),
            "retrograde": p.retrograde,
            "house": p.house
        } for p in planets if p}

    def _get_house_data(self, chart: AstrologicalSubject) -> List:
        """Get formatted house data from chart."""
        houses = get_houses_list(chart)
        return [{
            "name": house.name,
            "sign": house.sign,
            "position": float(house.position)
        } for house in houses]

    def _get_aspect_data(self) -> List:
        return [{
            "planet1": aspect.p1_name,
            "planet2": aspect.p2_name,
            "aspect_name": aspect.aspect,
            "orbit": aspect.orbit,
            "difference": aspect.diff,
            "is_major": aspect.is_major
        } for aspect in self.aspects.all_aspects]


if __name__ == "__main__":
    import json
    from kerykeion.utilities import setup_logging

    setup_logging(level="debug")

    # Basic Transit Analysis with full aspect output
    johnny_transit = TransitAnalysis(
        "Johnny Depp", 1963, 6, 9, 0, 0,
        birth_place="Owensboro", birth_country="US"
    )
    analysis = johnny_transit.get_analysis()

    # Use larger print buffer for complete aspect list
    print("Basic Transit Analysis:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))

    # Different Current Location
    johnny_transit_la = TransitAnalysis(
        "Johnny Depp", 1963, 6, 9, 0, 0,
        birth_place="Owensboro", birth_country="US",
        current_place="Los Angeles", current_country="US"
    )
    print("\nTransit Analysis (Different Location):")
    print(json.dumps(johnny_transit_la.get_analysis(), indent=2))

    # Sidereal Zodiac Transit
    johnny_transit_sidereal = TransitAnalysis(
        "Johnny Depp", 1963, 6, 9, 0, 0,
        birth_place="Owensboro", birth_country="US",
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI"
    )
    print("\nSidereal Transit Analysis:")
    print(json.dumps(johnny_transit_sidereal.get_analysis(), indent=2))

    # Morinus Houses Transit
    johnny_transit_morinus = TransitAnalysis(
        "Johnny Depp", 1963, 6, 9, 0, 0,
        birth_place="Owensboro", birth_country="US",
        houses_system="M"
    )
    print("\nMorinus Houses Transit Analysis:")
    print(json.dumps(johnny_transit_morinus.get_analysis(), indent=2))

    # Offline Mode Transit
    johnny_transit_offline = TransitAnalysis(
        "Johnny Depp", 1963, 6, 9, 0, 0,
        birth_place="Owensboro", birth_country="US",
        online=False,
        birth_tz="America/New_York",
        birth_lng=-87.1111,
        birth_lat=37.7711
    )
    print("\nOffline Transit Analysis:")
    print(json.dumps(johnny_transit_offline.get_analysis(), indent=2))

    # Test with additional data
    johnny_transit_full = TransitAnalysis(
        "Johnny Depp", 1963, 6, 9, 0, 0,
        birth_place="Owensboro", birth_country="US",
        current_place="Los Angeles", current_country="US"
    )
    analysis = johnny_transit_full.get_analysis()
    print("\nFull Transit Analysis:")
    print(json.dumps(analysis, indent=2))

    # Test with specific transit time
    future_transit = TransitAnalysis(
        "Johnny Depp", 1963, 6, 9, 0, 0,
        birth_place="Owensboro", birth_country="US",
        current_place="Los Angeles", current_country="US",
        transit_time=datetime(2024, 12, 25, 12, 0)
    )
    print("\nFuture Transit Analysis (Christmas 2024):")
    print(json.dumps(future_transit.get_analysis(), indent=2))
