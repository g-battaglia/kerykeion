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

import logging

from typing import Union

# Fix the circular import by changing this import
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion._predictive_utils import jd_to_ymd_hms
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_models import CompositeSubjectModel, AstrologicalSubjectModel
from kerykeion.schemas.kr_literals import (
    ZodiacType,
    PerspectiveType,
    HousesSystemIdentifier,
    SiderealMode,
    AstrologicalPoint,
    Houses,
    CompositeChartType,
)
from kerykeion.utilities import (
    get_kerykeion_point_from_degree,
    get_planet_house,
    circular_mean,
    calculate_moon_phase,
    find_common_active_points,
)


def _davison_midpoint_components(
    mid_jd: float, mid_lng: float
) -> tuple[int, int, int, int, int, int]:
    """Decompose a Davison midpoint JD into birth-data components (UTC).

    CE midpoints use the Gregorian calendar to match the proleptic-Gregorian
    datetimes used everywhere else in kerykeion. BCE midpoints must instead be
    the exact inverse of from_birth_data's BCE branch, which re-encodes year<1
    components in the JULIAN calendar and subtracts the longitude-LMT offset
    (ignoring tz_str) — so decompose the LMT-shifted instant in the Julian
    calendar or the Davison chart lands days away from the true time midpoint.
    """
    from kerykeion.ephemeris_backend import ephe

    lmt_shift = mid_lng / 15.0 / 24.0  # days; mirrors _calculate_time_conversions_bce
    greg_cal = getattr(ephe, "GREG_CAL", 1)
    probe_year = int(ephe.revjul(mid_jd + lmt_shift, ephe.JUL_CAL)[0])
    if probe_year < 1:
        cal, jd_base = ephe.JUL_CAL, mid_jd + lmt_shift
    else:
        cal, jd_base = greg_cal, mid_jd

    # Nearest-second rounding with calendar-aware midnight carry, shared with
    # the event factories' timestamp formatting.
    year, month, day, hour, minute, seconds = jd_to_ymd_hms(jd_base, cal)

    # from_birth_data branches on year<1, so the components must land on the
    # same side the probe predicted. The only flips are second-rounding at the
    # 1 BCE/1 CE boundary and the ~2-day window before 1 CE Jan 1 (proleptic
    # Gregorian) that neither branch's components can represent.
    if probe_year < 1 and year >= 1:
        # Rounding rolled 1 BCE Dec 31 24:00 (Julian) into 1 CE — clamp to
        # 23:59:59 (<=1 s error) so the BCE branch is still taken.
        year, month, day, hour, minute, seconds = 0, 12, 31, 23, 59, 59
    elif probe_year >= 1 and year < 1:
        logging.warning(
            "Davison midpoint JD %.6f falls in the ~2-day gap before 1 CE "
            "Jan 1 (proleptic Gregorian) that birth-data components cannot "
            "represent; clamping to 0001-01-01T00:00:00Z (error < ~2.5 days).",
            mid_jd,
        )
        year, month, day, hour, minute, seconds = 1, 1, 1, 0, 0, 0

    return int(year), int(month), int(day), hour, minute, seconds


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
        chart_name: Union[str, None] = None,
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
        self.active_points = find_common_active_points(first_subject.active_points, second_subject.active_points)
        if not self.active_points:
            # Disjoint active_points -> empty intersection. Fail loudly: the two
            # composite paths would otherwise diverge silently (the midpoint loop
            # produces an empty chart, while the Davison path forwards [] to
            # from_birth_data where it is read as 'no filter' and expands to a
            # FULL chart). Same empty-explicit-list inversion guarded elsewhere.
            raise KerykeionException(
                "The two subjects share no common active points; a composite "
                "chart needs at least one. Align their active_points."
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

        self.sidereal_mode = first_subject.sidereal_mode

        # Custom ayanamsa (required by the model validator when sidereal_mode is
        # 'USER'): carry both subjects' values over so CompositeSubjectModel does
        # not reject the self-inconsistent state (mode='USER' but fields absent).
        if first_subject.sidereal_mode == "USER" and (
            first_subject.custom_ayanamsa_t0 != second_subject.custom_ayanamsa_t0
            or first_subject.custom_ayanamsa_ayan_t0 != second_subject.custom_ayanamsa_ayan_t0
        ):
            raise KerykeionException("Both subjects must have the same custom ayanamsa values")
        self.custom_ayanamsa_t0 = first_subject.custom_ayanamsa_t0
        self.custom_ayanamsa_ayan_t0 = first_subject.custom_ayanamsa_ayan_t0

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
        return self.__str__()

    def __eq__(self, other):
        """
        Check equality with another composite subject.

        Args:
            other (CompositeSubjectFactory): Another composite subject to compare with.

        Returns:
            bool: True if both subjects and chart name are identical.
        """
        if not isinstance(other, CompositeSubjectFactory):
            return NotImplemented
        return (
            self.first_subject == other.first_subject
            and self.second_subject == other.second_subject
            and self.name == other.name
        )

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
        # Houses: each composite cusp is the circular mean of the two subjects'
        # SAME-numbered cusps, and it KEEPS that house number. Do NOT re-sort by
        # longitude and re-label positionally: averaging cusps of two charts whose
        # Ascendants are far apart produces a non-monotone cusp ring (the forward
        # arcs can sum to a multiple of 360°), and sorting then files the averaged
        # 10th cusp (the composite MC) into a lower slot — swapping MC/IC by 180°
        # and corrupting every planet's house. The tenth cusp must stay the mean
        # of the tenth cusps, i.e. the composite Midheaven.
        house_degree_list_ut = []
        for house in self.first_subject.houses_names_list:
            house_lower = house.lower()
            house_degree_list_ut.append(
                circular_mean(self.first_subject[house_lower]["abs_pos"], self.second_subject[house_lower]["abs_pos"])
            )

        for house_index, house_name in enumerate(self.first_subject.houses_names_list):
            house_lower = house_name.lower()
            self[house_lower] = get_kerykeion_point_from_degree(house_degree_list_ut[house_index], house_name, "House")

        # Planets
        planets = {}
        for planet in self.active_points:
            planet_lower = planet.lower()
            planets[planet_lower] = {}
            planets[planet_lower]["abs_pos"] = circular_mean(
                self.first_subject[planet_lower]["abs_pos"], self.second_subject[planet_lower]["abs_pos"]
            )
            self[planet_lower] = get_kerykeion_point_from_degree(
                planets[planet_lower]["abs_pos"], planet, "AstrologicalPoint"
            )
            self[planet_lower]["house"] = self._composite_house_for(
                self[planet_lower]["abs_pos"], house_degree_list_ut, self.houses_names_list
            )

    @staticmethod
    def _composite_house_for(planet_degree: float, house_cusps: list, house_names: list) -> str:
        """House of a point given composite cusps, robust to a non-monotone ring.

        Averaging two charts' cusps can yield cusps that are not in ascending
        circular order, so the usual start-inclusive containment can match the
        wrong (over-long or reflex) arc. Here each house is the forward arc from
        its own cusp to the NEXT house's cusp; when several arcs contain the
        point (overlap from non-monotonicity) the SHORTEST containing arc wins —
        the tightest, most specific house. Falls back to the first house only if
        nothing contains it (degenerate all-equal cusps).
        """
        # A point sitting exactly ON a cusp belongs to the house that cusp opens
        # (this is what makes the composite MC land in the 10th house even when
        # overlapping degenerate arcs would otherwise file it elsewhere).
        for i in range(len(house_cusps)):
            if abs((planet_degree - house_cusps[i] + 180.0) % 360.0 - 180.0) < 1e-9:
                return house_names[i]
        best_index = 0
        best_span = 360.0 + 1.0
        for i in range(len(house_cusps)):
            start = house_cusps[i]
            end = house_cusps[(i + 1) % len(house_cusps)]
            span = (end - start) % 360.0
            offset = (planet_degree - start) % 360.0
            # start-inclusive / end-exclusive; span 0 (coincident cusps) can't contain
            if span > 0 and offset < span and span < best_span:
                best_index = i
                best_span = span
        return house_names[best_index]

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
        moon = getattr(self, "moon", None)
        sun = getattr(self, "sun", None)
        if moon is None or sun is None:
            # Sun/Moon can be absent, e.g. when a planetocentric subject
            # excludes its center body from the active points.
            self.lunar_phase = None
            return
        self.lunar_phase = calculate_moon_phase(moon.abs_pos, sun.abs_pos)

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

        return CompositeSubjectModel(**self.__dict__)

    def get_davison_composite_subject_model(
        self,
        *,
        custom_ayanamsa_t0: Union[float, None] = None,
        custom_ayanamsa_ayan_t0: Union[float, None] = None,
    ) -> CompositeSubjectModel:
        """Generate a Davison composite chart.

        A Davison chart calculates the midpoint in **time** and **space**
        between two birth moments, then casts a standard natal chart for
        that derived moment and location.

        Unlike the midpoint composite (which averages planetary positions),
        the Davison chart is a real chart with valid astronomical positions
        that actually occurred at the computed date and location.

        Args:
            custom_ayanamsa_t0: Reference epoch (Julian Day) for the custom
                ayanamsa. Required when the subjects use ``sidereal_mode="USER"``.
            custom_ayanamsa_ayan_t0: Ayanamsa value (degrees) at ``t0``.
                Required when the subjects use ``sidereal_mode="USER"``.

        Returns:
            CompositeSubjectModel with composite_chart_type="Davison".
        """
        # The Davison chart is recomputed from scratch — USER sidereal mode
        # needs the custom ayanamsa definition to cast it.
        if self.sidereal_mode == "USER" and (custom_ayanamsa_t0 is None or custom_ayanamsa_ayan_t0 is None):
            raise KerykeionException(
                "get_davison_composite_subject_model requires both custom_ayanamsa_t0 and "
                "custom_ayanamsa_ayan_t0 when sidereal_mode='USER'."
            )

        s1 = self.first_subject
        s2 = self.second_subject

        # Midpoint in time (Julian Day)
        mid_jd = (s1.julian_day + s2.julian_day) / 2.0

        # Midpoint in space (latitude/longitude)
        mid_lat = (s1.lat + s2.lat) / 2.0
        mid_lng = circular_mean(s1.lng + 180.0, s2.lng + 180.0) - 180.0

        year, month, day, hour, minute, seconds = _davison_midpoint_components(
            mid_jd, mid_lng
        )

        extra_kwargs: dict = {}
        if custom_ayanamsa_t0 is not None:
            extra_kwargs["custom_ayanamsa_t0"] = custom_ayanamsa_t0
        if custom_ayanamsa_ayan_t0 is not None:
            extra_kwargs["custom_ayanamsa_ayan_t0"] = custom_ayanamsa_ayan_t0

        # The Davison is a real recomputable natal chart, so carry over the v6
        # enrichment flags BOTH parents requested (inferred from their populated
        # fields, since the flags aren't stored as booleans) — otherwise the
        # dignities/nakshatra/gauquelin/nutation/local-space/fixed-stars are
        # silently dropped. Parity with PlanetaryReturnFactory /
        # SecondaryProgressionFactory (which infer the same flags). Enable a
        # feature only when BOTH parents carried it, matching composite semantics.
        def _point_has(subject, attr: str) -> bool:
            for _name in ("sun", "moon", "mercury", "venus", "mars", "jupiter",
                          "saturn", "uranus", "neptune", "pluto"):
                _p = getattr(subject, _name, None)
                if _p is not None:
                    return getattr(_p, attr, None) is not None
            return False

        _shared_stars = sorted(
            {st.name for st in (s1.fixed_stars or [])} & {st.name for st in (s2.fixed_stars or [])}
        )
        extra_kwargs["calculate_dignities"] = _point_has(s1, "essential_dignity") and _point_has(s2, "essential_dignity")
        extra_kwargs["calculate_nakshatra"] = _point_has(s1, "nakshatra") and _point_has(s2, "nakshatra")
        extra_kwargs["calculate_local_space"] = _point_has(s1, "azimuth") and _point_has(s2, "azimuth")
        extra_kwargs["calculate_gauquelin"] = (
            s1.gauquelin_sector_cusps is not None and s2.gauquelin_sector_cusps is not None
        )
        extra_kwargs["calculate_nutation"] = s1.nutation is not None and s2.nutation is not None
        if _shared_stars:
            extra_kwargs["active_fixed_stars"] = _shared_stars

        # Cast a real natal chart at the midpoint moment/location.
        # ephe.revjul returns UTC, so use Etc/GMT to avoid double-conversion.
        davison_subject = AstrologicalSubjectFactory.from_birth_data(
            name=self.name,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            seconds=seconds,
            lng=mid_lng,
            lat=mid_lat,
            tz_str="Etc/GMT",
            city=f"Davison({s1.city}-{s2.city})",
            nation=s1.nation,
            online=False,
            zodiac_type=self.zodiac_type,
            sidereal_mode=self.sidereal_mode,
            houses_system_identifier=self.houses_system_identifier,
            perspective_type=self.perspective_type,
            active_points=self.active_points,
            **extra_kwargs,
        )

        # Build composite model from the Davison chart data
        davison_data = davison_subject.model_dump()
        davison_data["first_subject"] = s1
        davison_data["second_subject"] = s2
        davison_data["composite_chart_type"] = "Davison"

        return CompositeSubjectModel(**davison_data)


if __name__ == "__main__":
    first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
    second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

    composite_chart = CompositeSubjectFactory(first, second)
    print(composite_chart.get_midpoint_composite_subject_model().model_dump_json(indent=4))
