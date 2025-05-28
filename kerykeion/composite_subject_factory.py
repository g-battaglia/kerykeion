from typing import Union, TYPE_CHECKING

# Fix the circular import by changing this import
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.kr_types.kerykeion_exception import KerykeionException
from kerykeion.kr_types.kr_models import CompositeSubjectModel, AstrologicalSubjectModel
from kerykeion.kr_types.kr_literals import ZodiacType, PerspectiveType, HousesSystemIdentifier, SiderealMode, AstrologicalPoint, Houses, CompositeChartType
from kerykeion.utilities import (
    get_kerykeion_point_from_degree,
    get_planet_house,
    circular_mean,
    calculate_moon_phase,
    circular_sort,
    find_common_active_points
)


class CompositeSubjectFactory:
    """
    Factory class to create a Composite Subject Model from two Astrological Subjects
    Currently, the only available method for creating composite charts is the midpoint method.
    The composite houses and planets are calculated based on the midpoint of the corresponding points of the two subjects.
    The house are then reordered to match the original house system of the first subject.

    Args:
        first_subject (AstrologicalSubject): First astrological subject
        second_subject (AstrologicalSubject): Second astrological subject
        chart_name (str): Name of the composite chart. If None, it will be automatically generated.
    """

    model: Union[CompositeSubjectModel, None]
    first_subject: AstrologicalSubjectModel
    second_subject: AstrologicalSubjectModel
    name: str
    composite_chart_type: CompositeChartType
    zodiac_type: ZodiacType
    sidereal_mode: Union[SiderealMode, None]
    houses_system_identifier: HousesSystemIdentifier
    houses_system_name: str
    perspective_type: PerspectiveType
    houses_names_list: list[Houses]
    active_points: list[AstrologicalPoint]

    def __init__(
            self,
            first_subject: AstrologicalSubjectModel,
            second_subject: AstrologicalSubjectModel,
            chart_name: Union[str, None] = None
    ):
        self.model: Union[CompositeSubjectModel, None] = None
        self.composite_chart_type = "Midpoint"

        self.first_subject = first_subject
        self.second_subject = second_subject
        self.active_points = find_common_active_points(
            first_subject.active_points,
            second_subject.active_points
        )

        # Name
        if chart_name is None:
            self.name = f"{first_subject.name} and {second_subject.name} Composite Chart"
        else:
            self.name = chart_name

        # Zodiac Type
        if first_subject.zodiac_type != second_subject.zodiac_type:
            raise KerykeionException("Both subjects must have the same zodiac type")
        self.zodiac_type = first_subject.zodiac_type

        # Sidereal Mode
        if first_subject.sidereal_mode != second_subject.sidereal_mode:
            raise KerykeionException("Both subjects must have the same sidereal mode")

        if first_subject.sidereal_mode is not None:
            self.sidereal_mode = first_subject.sidereal_mode
        else:
            self.sidereal_mode = None

        # Houses System
        if first_subject.houses_system_identifier != second_subject.houses_system_identifier:
            raise KerykeionException("Both subjects must have the same houses system")
        self.houses_system_identifier = first_subject.houses_system_identifier

        # Houses System Name
        if first_subject.houses_system_name != second_subject.houses_system_name:
            raise KerykeionException("Both subjects must have the same houses system name")
        self.houses_system_name = first_subject.houses_system_name

        # Perspective Type
        if first_subject.perspective_type != second_subject.perspective_type:
            raise KerykeionException("Both subjects must have the same perspective type")
        self.perspective_type = first_subject.perspective_type

        # Planets Names List
        self.active_points = []
        for planet in first_subject.active_points:
            if planet in second_subject.active_points:
                self.active_points.append(planet)

        # Houses Names List
        self.houses_names_list = self.first_subject.houses_names_list

    def __str__(self):
        return f"Composite Chart Data for {self.name}"

    def __repr__(self):
        return f"Composite Chart Data for {self.name}"

    def __eq__(self, other):
        return self.first_subject == other.first_subject and self.second_subject == other.second_subject and self.name == other.chart_name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.first_subject, self.second_subject, self.name))

    def __copy__(self):
        return CompositeSubjectFactory(self.first_subject, self.second_subject, self.name)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def _calculate_midpoint_composite_points_and_houses(self):
        # Houses
        house_degree_list_ut = []
        for house in self.first_subject.houses_names_list:
            house_lower = house.lower()
            house_degree_list_ut.append(
                circular_mean(
                    self.first_subject[house_lower]["abs_pos"],
                    self.second_subject[house_lower]["abs_pos"]
                )
        )
        house_degree_list_ut = circular_sort(house_degree_list_ut)

        for house_index, house_name in enumerate(self.first_subject.houses_names_list):
            house_lower = house_name.lower()
            self[house_lower] = get_kerykeion_point_from_degree(
                house_degree_list_ut[house_index],
                house_name,
                "House"
            )


        # Planets
        common_planets = []
        for planet in self.first_subject.active_points:
            if planet in self.second_subject.active_points:
                common_planets.append(planet)

        planets = {}
        for planet in common_planets:
            planet_lower = planet.lower()
            planets[planet_lower] = {}
            planets[planet_lower]["abs_pos"] = circular_mean(
                self.first_subject[planet_lower]["abs_pos"],
                self.second_subject[planet_lower]["abs_pos"]
            )
            self[planet_lower] = get_kerykeion_point_from_degree(planets[planet_lower]["abs_pos"], planet, "AstrologicalPoint")
            self[planet_lower]["house"] = get_planet_house(self[planet_lower]['abs_pos'], house_degree_list_ut)

    def _calculate_composite_lunar_phase(self):
        self.lunar_phase = calculate_moon_phase(
            self['moon'].abs_pos,
            self['sun'].abs_pos
        )

    def get_midpoint_composite_subject_model(self):
        self._calculate_midpoint_composite_points_and_houses()
        self._calculate_composite_lunar_phase()

        return CompositeSubjectModel(
            **self.__dict__
        )


if __name__ == "__main__":
    from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

    first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
    second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

    composite_chart = CompositeSubjectFactory(first, second)
    print(composite_chart.get_midpoint_composite_subject_model().model_dump_json(indent=4))
