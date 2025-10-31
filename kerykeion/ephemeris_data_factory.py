"""
Ephemeris Data Factory Module

This module provides the EphemerisDataFactory class for generating time-series
astrological ephemeris data. It enables the creation of comprehensive astronomical
and astrological datasets across specified date ranges with flexible time intervals
and calculation parameters.

Key Features:
    - Time-series ephemeris data generation
    - Multiple time interval support (days, hours, minutes)
    - Configurable astrological calculation systems
    - Built-in performance safeguards and limits
    - Multiple output formats (dictionaries or model instances)
    - Complete AstrologicalSubject instance generation

The module supports both lightweight data extraction (via get_ephemeris_data)
and full-featured astrological analysis (via get_ephemeris_data_as_astrological_subjects),
making it suitable for various use cases from simple data collection to complex
astrological research and analysis applications.

Classes:
    EphemerisDataFactory: Main factory class for generating ephemeris data

Dependencies:
    - kerykeion.AstrologicalSubjectFactory: For creating astrological subjects
    - kerykeion.utilities: For house and planetary data extraction
    - kerykeion.schemas: For type definitions and model structures
    - datetime: For date/time handling
    - logging: For performance warnings

Example:
    Basic usage for daily ephemeris data:

    >>> from datetime import datetime
    >>> from kerykeion.ephemeris_data_factory import EphemerisDataFactory
    >>>
    >>> start = datetime(2024, 1, 1)
    >>> end = datetime(2024, 1, 31)
    >>> factory = EphemerisDataFactory(start, end)
    >>> data = factory.get_ephemeris_data()
    >>> print(f"Generated {len(data)} data points")

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from kerykeion import AstrologicalSubjectFactory
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion.utilities import (
    get_houses_list,
    get_available_astrological_points_list,
    normalize_zodiac_type,
)
from kerykeion.astrological_subject_factory import DEFAULT_HOUSES_SYSTEM_IDENTIFIER, DEFAULT_PERSPECTIVE_TYPE, DEFAULT_ZODIAC_TYPE
from kerykeion.schemas import (
    EphemerisDictModel,
    SiderealMode,
    HousesSystemIdentifier,
    PerspectiveType,
    ZodiacType,
)
from datetime import datetime, timedelta
from typing import Literal, Union, List
import logging


class EphemerisDataFactory:
    """
    A factory class for generating ephemeris data over a specified date range.

    This class calculates astrological ephemeris data (planetary positions and house cusps)
    for a sequence of dates, allowing for detailed astronomical calculations across time periods.
    It supports different time intervals (days, hours, or minutes) and various astrological
    calculation systems.

    The factory creates data points at regular intervals between start and end dates,
    with built-in safeguards to prevent excessive computational loads through configurable
    maximum limits.

    Args:
        start_datetime (datetime): The starting date and time for ephemeris calculations.
        end_datetime (datetime): The ending date and time for ephemeris calculations.
        step_type (Literal["days", "hours", "minutes"], optional): The time interval unit
            for data points. Defaults to "days".
        step (int, optional): The number of units to advance for each data point.
            For example, step=2 with step_type="days" creates data points every 2 days.
            Defaults to 1.
        lat (float, optional): Geographic latitude in decimal degrees for calculations.
            Positive values for North, negative for South. Defaults to 51.4769 (Greenwich).
        lng (float, optional): Geographic longitude in decimal degrees for calculations.
            Positive values for East, negative for West. Defaults to 0.0005 (Greenwich).
        tz_str (str, optional): Timezone identifier (e.g., "Europe/London", "America/New_York").
            Defaults to "Etc/UTC".
        is_dst (bool, optional): Whether daylight saving time is active for the location.
            Only relevant for certain timezone calculations. Defaults to False.
        zodiac_type (ZodiacType, optional): The zodiac system to use (tropical or sidereal).
            Defaults to DEFAULT_ZODIAC_TYPE.
        sidereal_mode (Union[SiderealMode, None], optional): The sidereal calculation mode
            if using sidereal zodiac. Only applies when zodiac_type is sidereal.
            Defaults to None.
        houses_system_identifier (HousesSystemIdentifier, optional): The house system
            for astrological house calculations (e.g., Placidus, Koch, Equal).
            Defaults to DEFAULT_HOUSES_SYSTEM_IDENTIFIER.
        perspective_type (PerspectiveType, optional): The calculation perspective
            (geocentric, heliocentric, etc.). Defaults to DEFAULT_PERSPECTIVE_TYPE.
        max_days (Union[int, None], optional): Maximum number of daily data points allowed.
            Set to None to disable this safety check. Defaults to 730 (2 years).
        max_hours (Union[int, None], optional): Maximum number of hourly data points allowed.
            Set to None to disable this safety check. Defaults to 8760 (1 year).
        max_minutes (Union[int, None], optional): Maximum number of minute-interval data points.
            Set to None to disable this safety check. Defaults to 525600 (1 year).

    Raises:
        ValueError: If step_type is not one of "days", "hours", or "minutes".
        ValueError: If the calculated number of data points exceeds the respective maximum limit.
        ValueError: If no valid dates are generated from the input parameters.

    Examples:
        Create daily ephemeris data for a month:

        >>> from datetime import datetime
        >>> start = datetime(2024, 1, 1)
        >>> end = datetime(2024, 1, 31)
        >>> factory = EphemerisDataFactory(start, end)
        >>> data = factory.get_ephemeris_data()

        Create hourly data for a specific location:

        >>> factory = EphemerisDataFactory(
        ...     start, end,
        ...     step_type="hours",
        ...     lat=40.7128,  # New York
        ...     lng=-74.0060,
        ...     tz_str="America/New_York"
        ... )
        >>> subjects = factory.get_ephemeris_data_as_astrological_subjects()

    Note:
        Large date ranges with small step intervals can generate thousands of data points,
        which may require significant computation time and memory. The factory includes
        warnings for calculations exceeding 1000 data points and enforces maximum limits
        to prevent system overload.
    """

    def __init__(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        step_type: Literal["days", "hours", "minutes"] = "days",
        step: int = 1,
        lat: float = 51.4769,
        lng: float = 0.0005,
        tz_str: str = "Etc/UTC",
        is_dst: bool = False,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: Union[SiderealMode, None] = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        max_days: Union[int, None] = 730,
        max_hours: Union[int, None] = 8760,
        max_minutes: Union[int, None] = 525600,
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.step_type = step_type
        self.step = step
        self.lat = lat
        self.lng = lng
        self.tz_str = tz_str
        self.is_dst = is_dst
        self.zodiac_type = normalize_zodiac_type(zodiac_type)
        self.sidereal_mode = sidereal_mode
        self.houses_system_identifier = houses_system_identifier
        self.perspective_type = perspective_type
        self.max_days = max_days
        self.max_hours = max_hours
        self.max_minutes = max_minutes

        self.dates_list = []
        if self.step_type == "days":
            self.dates_list = [self.start_datetime + timedelta(days=i * self.step) for i in range((self.end_datetime - self.start_datetime).days // self.step + 1)]
            if max_days and (len(self.dates_list) > max_days):
                raise ValueError(f"Too many days: {len(self.dates_list)} > {self.max_days}. To prevent this error, set max_days to a higher value or reduce the date range.")

        elif self.step_type == "hours":
            hours_diff = (self.end_datetime - self.start_datetime).total_seconds() / 3600
            self.dates_list = [self.start_datetime + timedelta(hours=i * self.step) for i in range(int(hours_diff) // self.step + 1)]
            if max_hours and (len(self.dates_list) > max_hours):
                raise ValueError(f"Too many hours: {len(self.dates_list)} > {self.max_hours}. To prevent this error, set max_hours to a higher value or reduce the date range.")

        elif self.step_type == "minutes":
            minutes_diff = (self.end_datetime - self.start_datetime).total_seconds() / 60
            self.dates_list = [self.start_datetime + timedelta(minutes=i * self.step) for i in range(int(minutes_diff) // self.step + 1)]
            if max_minutes and (len(self.dates_list) > max_minutes):
                raise ValueError(f"Too many minutes: {len(self.dates_list)} > {self.max_minutes}. To prevent this error, set max_minutes to a higher value or reduce the date range.")

        else:
            raise ValueError(f"Invalid step type: {self.step_type}")

        if not self.dates_list:
            raise ValueError("No dates found. Check the date range and step values.")

        if len(self.dates_list) > 1000:
            logging.warning(f"Large number of dates: {len(self.dates_list)}. The calculation may take a while.")

    def get_ephemeris_data(self, as_model: bool = False) -> list:
        """
        Generate ephemeris data for the specified date range.

        This method creates a comprehensive dataset containing planetary positions and
        astrological house cusps for each date in the configured time series. The data
        is structured for easy consumption by astrological applications and analysis tools.

        The returned data includes all available astrological points (planets, asteroids,
        lunar nodes, etc.) as configured by the perspective type, along with complete
        house cusp information for each calculated moment.

        Args:
            as_model (bool, optional): If True, returns data as validated model instances
                (EphemerisDictModel objects) which provide type safety and validation.
                If False, returns raw dictionary data for maximum flexibility.
                Defaults to False.

        Returns:
            list: A list of ephemeris data points, where each element represents one
                calculated moment in time. The structure depends on the as_model parameter:

                If as_model=False (default):
                    List of dictionaries with keys:
                    - "date" (str): ISO format datetime string (e.g., "2020-01-01T00:00:00")
                    - "planets" (list): List of dictionaries, each containing planetary data
                      with keys like 'name', 'abs_pos', 'lon', 'lat', 'dist', 'speed', etc.
                    - "houses" (list): List of dictionaries containing house cusp data
                      with keys like 'name', 'abs_pos', 'lon', etc.

                If as_model=True:
                    List of EphemerisDictModel instances providing the same data
                    with type validation and structured access.

        Examples:
            Basic usage with dictionary output:

            >>> factory = EphemerisDataFactory(start_date, end_date)
            >>> data = factory.get_ephemeris_data()
            >>> print(f"Sun position: {data[0]['planets'][0]['abs_pos']}")
            >>> print(f"First house cusp: {data[0]['houses'][0]['abs_pos']}")

            Using model instances for type safety:

            >>> data_models = factory.get_ephemeris_data(as_model=True)
            >>> first_point = data_models[0]
            >>> print(f"Date: {first_point.date}")
            >>> print(f"Number of planets: {len(first_point.planets)}")

        Note:
            - The calculation time is proportional to the number of data points
            - For large datasets (>1000 points), consider using the method in batches
            - Planet order and availability depend on the configured perspective type
            - House system affects the house cusp calculations
            - All positions are in the configured zodiac system (tropical/sidereal)
        """
        ephemeris_data_list = []
        for date in self.dates_list:
            subject = AstrologicalSubjectFactory.from_birth_data(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=date.hour,
                minute=date.minute,
                lng=self.lng,
                lat=self.lat,
                tz_str=self.tz_str,
                city="Placeholder",
                nation="Placeholder",
                online=False,
                zodiac_type=self.zodiac_type,
                sidereal_mode=self.sidereal_mode,
                houses_system_identifier=self.houses_system_identifier,
                perspective_type=self.perspective_type,
                is_dst=self.is_dst,
            )

            houses_list = get_houses_list(subject)
            available_planets = get_available_astrological_points_list(subject)

            ephemeris_data_list.append({"date": date.isoformat(), "planets": available_planets, "houses": houses_list})

        if as_model:
            # Type narrowing: at this point, the dict structure matches EphemerisDictModel
            return [EphemerisDictModel(date=data["date"], planets=data["planets"], houses=data["houses"]) for data in ephemeris_data_list]  # type: ignore

        return ephemeris_data_list

    def get_ephemeris_data_as_astrological_subjects(self, as_model: bool = False) -> List[AstrologicalSubjectModel]:
        """
        Generate ephemeris data as complete AstrologicalSubject instances.

        This method creates fully-featured AstrologicalSubject objects for each date in the
        configured time series, providing access to all astrological calculation methods
        and properties. Unlike the dictionary-based approach of get_ephemeris_data(),
        this method returns objects with the complete Kerykeion API available.

        Each AstrologicalSubject instance represents a complete astrological chart for
        the specified moment, location, and calculation settings. This allows direct
        access to methods like get_sun(), get_all_points(), draw_chart(), calculate
        aspects, and all other astrological analysis features.

        Args:
            as_model (bool, optional): If True, returns AstrologicalSubjectModel instances
                (Pydantic model versions) which provide serialization and validation features.
                If False, returns raw AstrologicalSubject instances with full method access.
                Defaults to False.

        Returns:
            List[AstrologicalSubjectModel]: A list of AstrologicalSubject or
                AstrologicalSubjectModel instances (depending on as_model parameter).
                Each element represents one calculated moment in time with full
                astrological chart data and methods available.

                Each subject contains:
                - All planetary and astrological point positions
                - Complete house system calculations
                - Chart drawing capabilities
                - Aspect calculation methods
                - Access to all Kerykeion astrological features

        Examples:
            Basic usage for accessing individual chart features:

            >>> factory = EphemerisDataFactory(start_date, end_date)
            >>> subjects = factory.get_ephemeris_data_as_astrological_subjects()
            >>>
            >>> # Access specific planetary data
            >>> sun_data = subjects[0].get_sun()
            >>> moon_data = subjects[0].get_moon()
            >>>
            >>> # Get all astrological points
            >>> all_points = subjects[0].get_all_points()
            >>>
            >>> # Generate chart visualization
            >>> chart_svg = subjects[0].draw_chart()

            Using model instances for serialization:

            >>> subjects_models = factory.get_ephemeris_data_as_astrological_subjects(as_model=True)
            >>> # Model instances can be easily serialized to JSON
            >>> json_data = subjects_models[0].model_dump_json()

            Batch processing for analysis:

            >>> subjects = factory.get_ephemeris_data_as_astrological_subjects()
            >>> sun_positions = [subj.sun['abs_pos'] for subj in subjects if subj.sun]
            >>> # Analyze sun position changes over time

        Use Cases:
            - Time-series astrological analysis
            - Planetary motion tracking
            - Aspect pattern analysis over time
            - Chart animation data generation
            - Astrological research and statistics
            - Progressive chart calculations

        Performance Notes:
            - More computationally intensive than get_ephemeris_data()
            - Each subject performs full astrological calculations
            - Memory usage scales with the number of data points
            - Consider processing in batches for very large date ranges
            - Ideal for comprehensive analysis requiring full chart features

        See Also:
            get_ephemeris_data(): For lightweight dictionary-based ephemeris data
            AstrologicalSubject: For details on available methods and properties
        """
        subjects_list = []
        for date in self.dates_list:
            subject = AstrologicalSubjectFactory.from_birth_data(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=date.hour,
                minute=date.minute,
                lng=self.lng,
                lat=self.lat,
                tz_str=self.tz_str,
                city="Placeholder",
                nation="Placeholder",
                online=False,
                zodiac_type=self.zodiac_type,
                sidereal_mode=self.sidereal_mode,
                houses_system_identifier=self.houses_system_identifier,
                perspective_type=self.perspective_type,
                is_dst=self.is_dst,
            )

            if as_model:
                subjects_list.append(subject)
            else:
                subjects_list.append(subject)

        return subjects_list


if __name__ == "__main__":
    start_date = datetime.fromisoformat("2020-01-01")
    end_date = datetime.fromisoformat("2020-01-03")

    factory = EphemerisDataFactory(
        start_datetime=start_date,
        end_datetime=end_date,
        step_type="minutes",
        step=60,  # One hour intervals to make the example more manageable
        lat=37.9838,
        lng=23.7275,
        tz_str="Europe/Athens",
        is_dst=False,
        max_hours=None,
        max_minutes=None,
        max_days=None,
    )

    # Test original method
    ephemeris_data = factory.get_ephemeris_data(as_model=True)
    print(f"Number of ephemeris data points: {len(ephemeris_data)}")
    print(f"First data point date: {ephemeris_data[0].date}")

    # Test new method
    subjects = factory.get_ephemeris_data_as_astrological_subjects()
    print(f"Number of astrological subjects: {len(subjects)}")
    print(f"First subject sun position: {subjects[0].sun}")

    # Example of accessing more data from the first subject
    first_subject = subjects[0]
    if first_subject.sun is not None:
        print(f"Sun sign: {first_subject.sun['sign']}")

    # Compare sun positions from both methods
    for i in range(min(3, len(subjects))):
        print(f"Date: {ephemeris_data[i].date}")
        if len(ephemeris_data[i].planets) > 0:
            print(f"Sun position from dict: {ephemeris_data[i].planets[0]['abs_pos']}")
        print("---")
