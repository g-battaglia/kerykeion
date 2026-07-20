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
    localize_naive,
    safe_timezone,
)
from kerykeion.astrological_subject_factory import (
    DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
    DEFAULT_PERSPECTIVE_TYPE,
    DEFAULT_ZODIAC_TYPE,
)
from kerykeion.schemas import (
    EphemerisDictModel,
    SiderealMode,
    HousesSystemIdentifier,
    PerspectiveType,
    ZodiacType,
)
from kerykeion.schemas.kr_literals import AstrologicalPoint
from datetime import datetime, timedelta, timezone

from typing import Any, List, Literal, Optional
import logging

# Default limits to prevent excessive computational load
_MAX_DAYS = 730  # ~2 years of daily data points
_MAX_HOURS = 8760  # ~1 year of hourly data points
_MAX_MINUTES = 525600  # ~1 year of minute-interval data points


class EphemerisDataFactory:
    """
    A factory class for generating ephemeris data over a specified date range.

    This class calculates astrological ephemeris data (planetary positions, house cusps
    and, when requested via ``active_fixed_stars``, fixed star positions) for a sequence
    of dates, allowing for detailed astronomical calculations across time periods.
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
        custom_ayanamsa_t0 (Union[float, None], optional): The reference epoch (as a Julian day)
            for a custom ayanamsa definition. Only used when sidereal_mode is "USER".
            Defaults to None.
        custom_ayanamsa_ayan_t0 (Union[float, None], optional): The ayanamsa value (in degrees)
            at the reference epoch t0. Only used when sidereal_mode is "USER".
            Defaults to None.
        active_points (Union[List[AstrologicalPoint], None], optional): Points to
            calculate on every generated subject. Defaults to None, which uses
            DEFAULT_ACTIVE_POINTS. Pass the same list you give the consumer
            (e.g. TransitsTimeRangeFactory with asteroids/TNOs) — aspects can
            only be detected for points present on BOTH the natal and the
            ephemeris subjects.
        active_fixed_stars (Union[List[str], None], optional): Fixed star names to
            calculate on every generated subject (same contract as
            ``AstrologicalSubjectFactory.from_birth_data``). When non-empty, each
            sample returned by ``get_ephemeris_data`` additionally carries a
            ``"fixed_stars"`` key with the calculated star point models, and the
            subjects returned by ``get_ephemeris_data_as_astrological_subjects``
            expose them via ``subject.fixed_stars``. Defaults to None, which adds
            no ``"fixed_stars"`` key to the samples. (Independently of this
            argument, every sample carries ``"ephemeris_warnings"`` since a75.)

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
        sidereal_mode: Optional[SiderealMode] = None,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        max_days: Optional[int] = _MAX_DAYS,
        max_hours: Optional[int] = _MAX_HOURS,
        max_minutes: Optional[int] = _MAX_MINUTES,
        custom_ayanamsa_t0: Optional[float] = None,
        custom_ayanamsa_ayan_t0: Optional[float] = None,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_fixed_stars: Optional[List[str]] = None,
    ):
        if step <= 0:
            # A non-positive step divides by zero when sizing the series; reject
            # it up front with the documented ValueError instead.
            raise ValueError(f"step must be a positive integer, got {step}.")
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
        self.custom_ayanamsa_t0 = custom_ayanamsa_t0
        self.custom_ayanamsa_ayan_t0 = custom_ayanamsa_ayan_t0
        # Subject construction may remove optional points that are outside the
        # active LEB coverage. Keep the caller's list immutable and give every
        # sample a fresh selection so one uncovered date cannot suppress the
        # warning (or the calculation) for later covered dates.
        self.active_points = list(active_points) if active_points is not None else None
        # Same immutability contract as active_points: keep the caller's list
        # untouched and hand every sample its own fresh copy.
        self.active_fixed_stars = list(active_fixed_stars) if active_fixed_stars is not None else None
        self.max_days = max_days
        self.max_hours = max_hours
        self.max_minutes = max_minutes

        # Sub-day steps (hours/minutes) advance in UTC: stepping naive
        # wall-clock and localizing each with a fixed is_dst duplicated
        # (spring-forward) or shifted samples across DST, producing a
        # non-monotonic UTC series that corrupts transit-event detection.
        #
        # Daily steps instead advance by LOCAL calendar days at a fixed wall
        # time: a fixed 24h UTC increment would drop or mistime a requested
        # local date on a DST day (e.g. Europe/Rome 2024-03-31→04-01 is 23h in
        # UTC, so `.days` was 0 and 2024-04-01 was omitted). Each local sample
        # is then converted to its true (non-uniformly spaced) UTC instant.
        # is_dst only disambiguates a wall time inside a fall-back fold.
        _tz = safe_timezone(self.tz_str)

        def _localize_to_utc(naive: datetime) -> datetime:
            return localize_naive(naive, _tz, is_dst=self.is_dst).astimezone(timezone.utc)

        def _to_utc(dt: datetime) -> datetime:
            if dt.tzinfo is None:
                return _localize_to_utc(dt)
            return dt.astimezone(timezone.utc)

        def _to_local_naive(dt: datetime) -> datetime:
            if dt.tzinfo is None:
                return dt
            return dt.astimezone(_tz).replace(tzinfo=None)

        _start_utc = _to_utc(self.start_datetime)
        _end_utc = _to_utc(self.end_datetime)

        self.dates_list = []
        if self.step_type == "days":
            # Wall-clock difference in whole days (DST-independent), so a local
            # date is never skipped and each sample keeps its wall time.
            local_start = _to_local_naive(self.start_datetime)
            local_end = _to_local_naive(self.end_datetime)
            n_samples = (local_end - local_start).days // self.step + 1
            # Enforce the cap on the projected count BEFORE materializing the
            # series: the list comprehension is the expensive step this guard
            # exists to prevent, so checking len() afterwards still pays the
            # full memory/CPU cost it is meant to avoid.
            if max_days and (n_samples > max_days):
                raise ValueError(
                    f"Too many days: {n_samples} > {self.max_days}. To prevent this error, set max_days to a higher value or reduce the date range."
                )
            self.dates_list = [_localize_to_utc(local_start + timedelta(days=i * self.step)) for i in range(n_samples)]

        elif self.step_type == "hours":
            hours_diff = (_end_utc - _start_utc).total_seconds() / 3600
            n_samples = int(hours_diff) // self.step + 1
            if max_hours and (n_samples > max_hours):
                raise ValueError(
                    f"Too many hours: {n_samples} > {self.max_hours}. To prevent this error, set max_hours to a higher value or reduce the date range."
                )
            self.dates_list = [_start_utc + timedelta(hours=i * self.step) for i in range(n_samples)]

        elif self.step_type == "minutes":
            minutes_diff = (_end_utc - _start_utc).total_seconds() / 60
            n_samples = int(minutes_diff) // self.step + 1
            if max_minutes and (n_samples > max_minutes):
                raise ValueError(
                    f"Too many minutes: {n_samples} > {self.max_minutes}. To prevent this error, set max_minutes to a higher value or reduce the date range."
                )
            self.dates_list = [_start_utc + timedelta(minutes=i * self.step) for i in range(n_samples)]

        else:
            raise ValueError(f"Invalid step type: {self.step_type}")

        if not self.dates_list:
            raise ValueError("No dates found. Check the date range and step values.")

        if len(self.dates_list) > 1000:
            logging.warning(f"Large number of dates: {len(self.dates_list)}. The calculation may take a while.")

    def _create_subject_for_date(self, date: datetime) -> AstrologicalSubjectModel:
        """Create an AstrologicalSubject for a given date using the factory's settings."""
        resolved_offset_seconds = None
        if date.tzinfo is not None:
            # UTC-stepped series: render the instant in the target timezone and
            # pass the RESOLVED UTC offset down directly. bool(dst()) is the wrong
            # fold-side discriminator for standard-offset-change folds (UK 1971,
            # Portugal 1976): both occurrences have dst()==0, so is_dst=False would
            # re-localize onto the wrong side, silently computing a chart 1 h off.
            local_date = date.astimezone(safe_timezone(self.tz_str))
            is_dst = bool(local_date.dst())
            _off = local_date.utcoffset()
            if _off is not None:
                resolved_offset_seconds = round(_off.total_seconds())
        else:
            # Naive input (e.g. a hand-built dates_list): previous behavior.
            local_date = date
            is_dst = self.is_dst
        return AstrologicalSubjectFactory.from_birth_data(
            year=local_date.year,
            month=local_date.month,
            day=local_date.day,
            hour=local_date.hour,
            minute=local_date.minute,
            seconds=local_date.second,
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
            is_dst=is_dst,
            custom_ayanamsa_t0=self.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=self.custom_ayanamsa_ayan_t0,
            active_points=(list(self.active_points) if self.active_points is not None else None),
            active_fixed_stars=(list(self.active_fixed_stars) if self.active_fixed_stars is not None else None),
            _lmt_offset_seconds=resolved_offset_seconds,
        )

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
                    - "planets" (list): List of KerykeionPointModel instances (attribute
                      or subscript access: 'name', 'abs_pos', 'sign', 'speed', etc.)
                    - "houses" (list): List of KerykeionPointModel instances for the
                      house cusps (same access patterns)
                    - "ephemeris_warnings" (list): ALWAYS present since 6.0.0a75.
                      List of EphemerisWarningModel entries describing optional
                      points that no permitted source could produce; an empty list
                      when nothing was omitted. This key is new in a75: samples are
                      NOT key-identical to earlier releases, so consumers that
                      validate keys strictly must accept it.
                    - "fixed_stars" (list): ONLY present when the factory was built
                      with a non-empty ``active_fixed_stars``. List of the calculated
                      fixed star KerykeionPointModel instances (same shape as
                      ``subject.fixed_stars``). Without requested stars the key is
                      absent.

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
        ephemeris_data_list: list[dict[str, Any]] = []
        for date in self.dates_list:
            subject = self._create_subject_for_date(date)

            houses_list = get_houses_list(subject)
            available_planets = get_available_astrological_points_list(subject)

            sample: dict[str, Any] = {
                "date": date.isoformat(),
                "planets": available_planets,
                "houses": houses_list,
                "ephemeris_warnings": list(subject.ephemeris_warnings),
                # Every sample is cast at the SAME latitude, so a polar
                # substitution applies to the whole series — but it is emitted
                # per sample anyway, because the polar threshold is 90° minus the
                # obliquity of the sample's own epoch, and a long enough series
                # can straddle it. Silently dropping it would let a series report
                # Placidus cusps that are in fact Porphyry's.
                "polar_house_fallbacks": list(subject.polar_house_fallbacks),
            }
            # The "fixed_stars" key is emitted only when stars were requested. It
            # is the only optional key: "ephemeris_warnings" and
            # "polar_house_fallbacks" above are always present (empty lists when
            # nothing happened), so since a75 the sample dict is NOT key-identical
            # to earlier releases even without stars. Key-strict consumers must
            # tolerate both.
            if self.active_fixed_stars:
                sample["fixed_stars"] = list(subject.fixed_stars)
            ephemeris_data_list.append(sample)

        if as_model:
            # Type narrowing: at this point, the dict structure matches EphemerisDictModel
            return [
                EphemerisDictModel(
                    date=data["date"],
                    planets=data["planets"],
                    houses=data["houses"],
                    ephemeris_warnings=data["ephemeris_warnings"],
                    polar_house_fallbacks=data["polar_house_fallbacks"],
                    **({"fixed_stars": data["fixed_stars"]} if "fixed_stars" in data else {}),
                )
                for data in ephemeris_data_list
            ]  # type: ignore

        return ephemeris_data_list

    def get_ephemeris_data_as_astrological_subjects(self, as_model: bool = False) -> list[AstrologicalSubjectModel]:
        """
        Generate ephemeris data as complete AstrologicalSubject instances.

        This method creates fully-featured AstrologicalSubjectModel instances for each
        date in the configured time series. Unlike the dictionary-based approach of
        get_ephemeris_data(), this method returns Pydantic models with attribute access
        to all computed positions.

        Args:
            as_model: Unused parameter retained for backward compatibility. Ignored.

        Returns:
            list[AstrologicalSubjectModel]: A list of subject model instances.
                Each element represents one calculated moment in time.

                Each subject contains:
                - All planetary and astrological point positions (e.g., ``subject.sun.sign``)
                - Complete house system calculations (e.g., ``subject.first_house.sign``)
                - Fixed stars requested via ``active_fixed_stars`` (``subject.fixed_stars``)
                - Lunar phase data
                - JSON serialization via Pydantic

        Examples:
            Basic usage for accessing individual chart features:

            >>> factory = EphemerisDataFactory(start_date, end_date)
            >>> subjects = factory.get_ephemeris_data_as_astrological_subjects()
            >>>
            >>> # Access planetary data via attributes
            >>> sun_sign = subjects[0].sun.sign
            >>> moon_abs_pos = subjects[0].moon.abs_pos
            >>>
            >>> # Access house cusps
            >>> asc_sign = subjects[0].first_house.sign

            Batch processing for analysis:

            >>> subjects = factory.get_ephemeris_data_as_astrological_subjects()
            >>> sun_positions = [subj.sun.abs_pos for subj in subjects]
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
            subject = self._create_subject_for_date(date)

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
