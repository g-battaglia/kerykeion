"""
Composite Subject Factory Module

This module provides functionality for creating composite astrological charts from two
individual astrological subjects. A composite chart represents the relationship between
two people by calculating midpoint positions between corresponding planetary placements
and house cusps.

The module implements the midpoint composite technique, which is the most commonly used
method for relationship astrology. This technique creates a single chart that symbolizes
the energy and dynamics of the relationship itself, rather than comparing individual charts.

Key Features:
- Midpoint calculation for all planetary positions
- Midpoint calculation for house cusp positions
- Proper handling of zodiacal boundary crossings (0°/360°)
- Validation of compatible astrological settings between subjects
- Lunar phase calculation for composite charts
- Support for all standard astrological points and house systems

Classes:
    CompositeSubjectFactory: Main factory class for creating composite charts

Dependencies:
    - AstrologicalSubjectFactory: For working with individual astrological subjects
    - Various schemas modules: For type definitions and models
    - utilities module: For astrological calculations and helper functions

Example Usage:
    >>> from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory
    >>> person1 = AstrologicalSubjectFactory.from_birth_data(...)
    >>> person2 = AstrologicalSubjectFactory.from_birth_data(...)
    >>> composite = CompositeSubjectFactory(person1, person2)
    >>> composite_chart = composite.get_midpoint_composite_subject_model()

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from typing import Union

# Fix the circular import by changing this import
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_models import CompositeSubjectModel, AstrologicalSubjectModel
from kerykeion.schemas.kr_literals import ZodiacType, PerspectiveType, HousesSystemIdentifier, SiderealMode, AstrologicalPoint, Houses, CompositeChartType
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
    Factory class to create composite astrological charts from two astrological subjects.

    A composite chart represents the relationship between two people by calculating the midpoint
    between corresponding planetary positions and house cusps. This creates a single chart
    that symbolizes the energy of the relationship itself.

    Currently supports the midpoint method for composite chart calculation, where:
    - Planetary positions are calculated as the circular mean of corresponding planets
    - House cusps are calculated as the circular mean of corresponding houses
    - Houses are reordered to maintain consistency with the original house system
    - Only common active points between both subjects are included

    The resulting composite chart maintains the zodiac type, sidereal mode, houses system,
    and perspective type of the input subjects (which must be identical between subjects).

    Attributes:
        model (CompositeSubjectModel | None): The generated composite subject model
        first_subject (AstrologicalSubjectModel): First astrological subject
        second_subject (AstrologicalSubjectModel): Second astrological subject
        name (str): Name of the composite chart
        composite_chart_type (CompositeChartType): Type of composite chart (currently "Midpoint")
        zodiac_type (ZodiacType): Zodiac system used (Tropical or Sidereal)
        sidereal_mode (SiderealMode | None): Sidereal calculation mode if applicable
        houses_system_identifier (HousesSystemIdentifier): House system identifier
        houses_system_name (str): Human-readable house system name
        perspective_type (PerspectiveType): Astrological perspective type
        houses_names_list (list[Houses]): List of house names
        active_points (list[AstrologicalPoint]): Common active planetary points

    Example:
        >>> first_person = AstrologicalSubjectFactory.from_birth_data(
        ...     "John", 1990, 1, 1, 12, 0, "New York", "US"
        ... )
        >>> second_person = AstrologicalSubjectFactory.from_birth_data(
        ...     "Jane", 1992, 6, 15, 14, 30, "Los Angeles", "US"
        ... )
        >>> composite = CompositeSubjectFactory(first_person, second_person)
        >>> composite_model = composite.get_midpoint_composite_subject_model()

    Raises:
        KerykeionException: When subjects have incompatible settings (different zodiac types,
                           sidereal modes, house systems, or perspective types)
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
        """
        Initialize the composite subject factory with two astrological subjects.

        Validates that both subjects have compatible settings and extracts common
        active points for composite chart calculation.

        Args:
            first_subject (AstrologicalSubjectModel): First astrological subject for the composite
            second_subject (AstrologicalSubjectModel): Second astrological subject for the composite
            chart_name (str | None, optional): Custom name for the composite chart.
                                             If None, generates name from subject names.
                                             Defaults to None.

        Raises:
            KerykeionException: If subjects have different zodiac types, sidereal modes,
                              house systems, house system names, or perspective types.

        Note:
            Both subjects must have identical astrological calculation settings to ensure
            meaningful composite chart calculations.
        """
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
        """
        Return string representation of the composite subject.

        Returns:
            str: Human-readable string describing the composite chart.
        """
        return f"Composite Chart Data for {self.name}"

    def __repr__(self):
        """
        Return detailed string representation of the composite subject.

        Returns:
            str: Detailed string representation for debugging purposes.
        """
        return f"Composite Chart Data for {self.name}"

    def __eq__(self, other):
        """
        Check equality with another composite subject.

        Args:
            other (CompositeSubjectFactory): Another composite subject to compare with.

        Returns:
            bool: True if both subjects and chart name are identical.
        """
        return self.first_subject == other.first_subject and self.second_subject == other.second_subject and self.name == other.chart_name

    def __ne__(self, other):
        """
        Check inequality with another composite subject.

        Args:
            other (CompositeSubjectFactory): Another composite subject to compare with.

        Returns:
            bool: True if subjects or chart name are different.
        """
        return not self.__eq__(other)

    def __hash__(self):
        """
        Generate hash for the composite subject.

        Returns:
            int: Hash value based on both subjects and chart name.
        """
        return hash((self.first_subject, self.second_subject, self.name))

    def __copy__(self):
        """
        Create a shallow copy of the composite subject.

        Returns:
            CompositeSubjectFactory: New instance with the same subjects and name.
        """
        return CompositeSubjectFactory(self.first_subject, self.second_subject, self.name)

    def __setitem__(self, key, value):
        """
        Set an attribute using dictionary-style access.

        Args:
            key (str): Attribute name to set.
            value: Value to assign to the attribute.
        """
        setattr(self, key, value)

    def __getitem__(self, key):
        """
        Get an attribute using dictionary-style access.

        Args:
            key (str): Attribute name to retrieve.

        Returns:
            Any: Value of the requested attribute.

        Raises:
            AttributeError: If the attribute doesn't exist.
        """
        return getattr(self, key)

    def _calculate_midpoint_composite_points_and_houses(self):
        """
        Calculate midpoint positions for all planets and house cusps in the composite chart.

        This method implements the midpoint composite technique by:
        1. Computing circular means of house cusp positions from both subjects
        2. Sorting house positions to maintain proper house order
        3. Creating composite house cusps with calculated positions
        4. Computing circular means of planetary positions for common active points
        5. Assigning planets to their appropriate houses in the composite chart

        The circular mean calculation ensures proper handling of zodiacal positions
        around the 360-degree boundary (e.g., when one position is at 350° and
        another at 10°, the midpoint is correctly calculated as 0°).

        Side Effects:
            - Updates instance attributes with calculated house cusp positions
            - Updates instance attributes with calculated planetary positions
            - Sets house assignments for each planetary position

        Note:
            This is an internal method called by get_midpoint_composite_subject_model().
            Only planets that exist in both subjects' active_points are included.
        """
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
        """
        Calculate the lunar phase for the composite chart based on Sun-Moon midpoints.

        Uses the composite positions of the Sun and Moon to determine the lunar phase
        angle, representing the relationship's emotional and instinctual dynamics.

        Side Effects:
            Sets the lunar_phase attribute with the calculated phase information.

        Note:
            This method should be called after _calculate_midpoint_composite_points_and_houses()
            to ensure Sun and Moon composite positions are available.
        """
        self.lunar_phase = calculate_moon_phase(
            self['moon'].abs_pos,
            self['sun'].abs_pos
        )

    def get_midpoint_composite_subject_model(self):
        """
        Generate the complete composite chart model using the midpoint technique.

        This is the main public method for creating a composite chart. It orchestrates
        the calculation of all composite positions and creates a complete CompositeSubjectModel
        containing all necessary astrological data for the relationship chart.

        The process includes:
        1. Calculating midpoint positions for all planets and house cusps
        2. Computing the composite lunar phase
        3. Assembling all data into a comprehensive model

        Returns:
            CompositeSubjectModel: Complete composite chart data model containing:
                - All calculated planetary positions and their house placements
                - House cusp positions maintaining proper house system order
                - Lunar phase information for the composite chart
                - All metadata from the original subjects (names, chart type, etc.)

        Example:
            >>> composite = CompositeSubjectFactory(person1, person2, "Our Relationship")
            >>> model = composite.get_midpoint_composite_subject_model()
            >>> print(f"Composite Sun at {model.sun.abs_pos}° in House {model.sun.house}")

        Note:
            This method performs all calculations internally and returns a complete,
            ready-to-use composite chart model suitable for analysis or chart drawing.
        """
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
