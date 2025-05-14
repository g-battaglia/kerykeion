from typing import Dict, List, Tuple, Optional, Union, Literal
from pydantic import BaseModel
from kerykeion import AstrologicalSubject
from enum import Enum


class PlanetInHouseModel(BaseModel):
    """Represents a planet from one chart positioned in a house from another chart"""

    planet_name: str
    planet_degree: float
    planet_sign: str
    planet_owner_name: str
    house_number: int
    house_name: str
    house_owner_name: str

    def __str__(self) -> str:
        return f"{self.planet_name} of {self.planet_owner_name} at {self.planet_degree}° {self.planet_sign} in {self.house_owner_name}'s {self.house_number} house"


class HouseComparisonModel(BaseModel):
    """Pydantic model for any two-chart comparison analysis"""

    chart1_name: str
    chart2_name: str
    chart1_planets_in_chart2_houses: List[PlanetInHouseModel]
    chart2_planets_in_chart1_houses: Optional[List[PlanetInHouseModel]] = None


# Utility functions
def find_house(planet_degree: float, house_cusps: List[float]) -> int:
    """
    Determines which house a planet falls in given its absolute degree.

    Args:
        planet_degree: Absolute degree of the planet (0-360)
        house_cusps: List of absolute degrees of house cusps

    Returns:
        House number (1-12)
    """
    for i in range(11):
        current_cusp = house_cusps[i]
        next_cusp = house_cusps[i + 1]

        # Handle the case when a house crosses 0° Aries
        if next_cusp < current_cusp:
            if planet_degree >= current_cusp or planet_degree < next_cusp:
                return i + 1
        else:
            if current_cusp <= planet_degree < next_cusp:
                return i + 1

    # If not found in previous houses, it's in the 12th house
    return 12


def calculate_planets_in_houses(
    planet_subject: AstrologicalSubject, house_subject: AstrologicalSubject
) -> List[PlanetInHouseModel]:
    """
    Calculates which houses of the house_subject the planets of planet_subject fall into.

    Args:
        planet_subject: Subject whose planets are being analyzed
        house_subject: Subject whose houses are being considered

    Returns:
        List of PlanetInHouseModel objects
    """
    planets_in_houses: List[PlanetInHouseModel] = []

    # List of planets to consider
    planets = []

    for planet in planet_subject.planets_names_list:
        planet_obj = getattr(planet_subject, planet.lower())
        if planet_obj is not None:
            planets.append(planet_obj)

    for axis in planet_subject.axial_cusps_names_list:
        axis_obj = getattr(planet_subject, axis.lower())
        if axis_obj is not None:
            planets.append(axis_obj)

    # Ordered list of house cusps degrees
    house_cusps = [
        house_subject.first_house.abs_pos,
        house_subject.second_house.abs_pos,
        house_subject.third_house.abs_pos,
        house_subject.fourth_house.abs_pos,
        house_subject.fifth_house.abs_pos,
        house_subject.sixth_house.abs_pos,
        house_subject.seventh_house.abs_pos,
        house_subject.eighth_house.abs_pos,
        house_subject.ninth_house.abs_pos,
        house_subject.tenth_house.abs_pos,
        house_subject.eleventh_house.abs_pos,
        house_subject.twelfth_house.abs_pos,
    ]

    # For each planet, determine which house it falls in
    for planet in planets:
        if planet is None:
            continue

        planet_degree = planet.abs_pos
        house_number = find_house(planet_degree, house_cusps)
        house_name = get_house_name(house_number)

        planet_in_house = PlanetInHouseModel(
            planet_name=planet.name,
            planet_degree=planet.position,
            planet_sign=planet.sign,
            planet_owner_name=planet_subject.name,
            house_number=house_number,
            house_name=house_name,
            house_owner_name=house_subject.name,
        )

        planets_in_houses.append(planet_in_house)

    return planets_in_houses


def get_house_name(house_number: int) -> str:
    """
    Returns the name of the house based on its number.

    Args:
        house_number: House number (1-12)

    Returns:
        Name of the house
    """
    house_names = {
        1: "First_House",
        2: "Second_House",
        3: "Third_House",
        4: "Fourth_House",
        5: "Fifth_House",
        6: "Sixth_House",
        7: "Seventh_House",
        8: "Eighth_House",
        9: "Ninth_House",
        10: "Tenth_House",
        11: "Eleventh_House",
        12: "Twelfth_House",
    }

    return house_names.get(house_number, "")


class HouseComparisonFactory:
    """
    Factory class that creates various types of two-chart astrological analyses,
    such as synastry, transits, solar returns, etc.
    """

    def __init__(self, first_subject: AstrologicalSubject, second_subject: AstrologicalSubject):
        self.first_subject = first_subject
        self.second_subject = second_subject

    def get_house_comparison(self) -> HouseComparisonModel:
        """
        Creates a house comparison model for two astrological subjects.

        Args:
            chart1: First astrological subject
            chart2: Second astrological subject
            description: Description of the comparison

        Returns:
            HouseComparisonModel object
        """
        chart1_planets_in_chart2_houses = calculate_planets_in_houses(self.first_subject, self.second_subject)
        chart2_planets_in_chart1_houses = calculate_planets_in_houses(self.second_subject, self.first_subject)

        return HouseComparisonModel(
            chart1_name=self.first_subject.name,
            chart2_name=self.second_subject.name,
            chart1_planets_in_chart2_houses=chart1_planets_in_chart2_houses,
            chart2_planets_in_chart1_houses=chart2_planets_in_chart1_houses,
        )


if __name__ == "__main__":
    # Create two astrological subjects
    natal_chart = AstrologicalSubject("Person A", 1990, 5, 15, 10, 30, "Rome", "IT")

    # For synastry
    partner_chart = AstrologicalSubject("Person B", 1992, 8, 23, 14, 45, "Milan", "IT")

    # Create a factory instance
    factory = HouseComparisonFactory(natal_chart, partner_chart)
    # Generate a house comparison
    comparison = factory.get_house_comparison()

    print(comparison.model_dump_json(indent=4))
