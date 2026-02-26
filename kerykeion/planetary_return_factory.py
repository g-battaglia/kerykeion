# -*- coding: utf-8 -*-
"""
Planetary Return Factory Module

This module provides the PlanetaryReturnFactory class for calculating and generating
comprehensive planetary return charts, specifically Solar and Lunar returns. It leverages
the Swiss Ephemeris library for precise astronomical calculations to determine exact
return moments and create complete astrological chart data.

Key Features:
    - Solar Return calculations (Sun's annual return to natal position)
    - Lunar Return calculations (Moon's monthly return to natal position)
    - Multiple date input formats (ISO datetime, year-based, month/year-based)
    - Flexible location handling (online geocoding or manual coordinates)
    - Complete astrological chart generation for return moments
    - Integration with Geonames service for location data
    - Timezone-aware calculations with UTC precision

A planetary return occurs when a planet returns to the exact degree and minute
it occupied at the time of birth. Solar returns happen approximately once per year
and are widely used for annual forecasting, while Lunar returns occur roughly
every 27-29 days and are used for monthly analysis and timing.

The factory creates complete AstrologicalSubject instances for the calculated
return moments, enabling full chart analysis including planetary positions,
aspects, house cusps, and all other astrological features.

Classes:
    PlanetaryReturnFactory: Main factory class for calculating planetary returns

Dependencies:
    - swisseph: Swiss Ephemeris library for astronomical calculations
    - kerykeion.AstrologicalSubjectFactory: For creating complete chart data
    - kerykeion.fetch_geonames: For online location data retrieval
    - kerykeion.utilities: For date/time conversions and astronomical functions
    - kerykeion.schemas: For type definitions and model structures

Example:
    Basic Solar Return calculation for a specific year:

    >>> from kerykeion import AstrologicalSubjectFactory
    >>> from kerykeion.planetary_return_factory import PlanetaryReturnFactory
    >>>
    >>> # Create natal chart
    >>> subject = AstrologicalSubjectFactory.from_birth_data(
    ...     name="John Doe",
    ...     year=1990, month=6, day=15,
    ...     hour=12, minute=30,
    ...     lat=40.7128, lng=-74.0060,
    ...     tz_str="America/New_York"
    ... )
    >>>
    >>> # Create return calculator for New York location
    >>> calculator = PlanetaryReturnFactory(
    ...     subject,
    ...     city="New York",
    ...     nation="US",
    ...     online=True
    ... )
    >>>
    >>> # Calculate Solar Return for 2024
    >>> solar_return = calculator.next_return_from_year(2024, "Solar")
    >>> print(f"Solar Return: {solar_return.iso_formatted_local_datetime}")
    >>> print(f"Sun position: {solar_return.sun.abs_pos}°")

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

import calendar
import logging
import swisseph as swe

from datetime import datetime, timezone
from typing import Union

from kerykeion.schemas import KerykeionException
from kerykeion.fetch_geonames import FetchGeonames
from kerykeion.utilities import julian_to_datetime, datetime_to_julian
from kerykeion.astrological_subject_factory import (
    GEONAMES_DEFAULT_USERNAME_WARNING,
    DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS,
    DEFAULT_GEONAMES_USERNAME,
)
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.schemas.kr_literals import ReturnType
from kerykeion.schemas.kr_models import PlanetReturnModel, AstrologicalSubjectModel


class PlanetaryReturnFactory:
    """
    A factory class for calculating and generating planetary return charts.

    This class specializes in computing precise planetary return moments using the Swiss
    Ephemeris library and creating complete astrological charts for those calculated times.
    It supports both Solar Returns (annual) and Lunar Returns (monthly), providing
    comprehensive astrological analysis capabilities for timing and forecasting applications.

    Planetary returns are fundamental concepts in predictive astrology:
    - Solar Returns: Occur when the Sun returns to its exact natal position (~365.25 days)
    - Lunar Returns: Occur when the Moon returns to its exact natal position (~27-29 days)

    The factory handles complex astronomical calculations automatically, including:
    - Precise celestial mechanics computations
    - Timezone conversions and UTC coordination
    - Location-based calculations for return chart casting
    - Integration with online geocoding services
    - Complete chart generation with all astrological points

    Args:
        subject (AstrologicalSubjectModel): The natal astrological subject for whom
            returns are calculated. Must contain complete birth data including
            planetary positions at birth.
        city (Optional[str]): City name for return chart location. Required when
            using online mode for location data retrieval.
        nation (Optional[str]): Nation/country code for return chart location.
            Required when using online mode (e.g., "US", "GB", "FR").
        lng (Optional[Union[int, float]]): Geographic longitude in decimal degrees
            for return chart location. Positive values for East, negative for West.
            Required when using offline mode.
        lat (Optional[Union[int, float]]): Geographic latitude in decimal degrees
            for return chart location. Positive values for North, negative for South.
            Required when using offline mode.
        tz_str (Optional[str]): Timezone identifier for return chart location
            (e.g., "America/New_York", "Europe/London", "Asia/Tokyo").
            Required when using offline mode.
        online (bool, optional): Whether to fetch location data online via Geonames
            service. When True, requires city, nation, and geonames_username.
            When False, requires lng, lat, and tz_str. Defaults to True.
        geonames_username (Optional[str]): Username for Geonames API access.
            Required when online=True and coordinates are not provided.
            Register at http://www.geonames.org/login for free account.
        cache_expire_after_days (int, optional): Number of days to cache Geonames
            location data before refreshing. Defaults to system setting.
        altitude (Optional[Union[float, int]]): Elevation above sea level in meters
            for the return chart location. Reserved for future astronomical
            calculations. Defaults to None.

    Raises:
        KerykeionException: If required location parameters are missing for the
            chosen mode (online/offline).
        KerykeionException: If Geonames API fails to retrieve location data.
        KerykeionException: If online mode is used without proper API credentials.

    Attributes:
        subject (AstrologicalSubjectModel): The natal subject for calculations.
        city (Optional[str]): Return chart city name.
        nation (Optional[str]): Return chart nation code.
        lng (float): Return chart longitude coordinate.
        lat (float): Return chart latitude coordinate.
        tz_str (str): Return chart timezone identifier.
        online (bool): Location data retrieval mode.
        city_data (Optional[dict]): Cached location data from Geonames.

    Examples:
        Online mode with automatic location lookup:

        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     name="Alice", year=1985, month=3, day=21,
        ...     hour=14, minute=30, lat=51.5074, lng=-0.1278,
        ...     tz_str="Europe/London"
        ... )
        >>> factory = PlanetaryReturnFactory(
        ...     subject,
        ...     city="London",
        ...     nation="GB",
        ...     online=True,
        ...     geonames_username="your_username"
        ... )

        Offline mode with manual coordinates:

        >>> factory = PlanetaryReturnFactory(
        ...     subject,
        ...     lng=-74.0060,
        ...     lat=40.7128,
        ...     tz_str="America/New_York",
        ...     online=False
        ... )

        Different location for return chart:

        >>> # Calculate return as if living in a different city
        >>> factory = PlanetaryReturnFactory(
        ...     natal_subject,  # Born in London
        ...     city="Paris",   # But living in Paris
        ...     nation="FR",
        ...     online=True
        ... )

    Use Cases:
        - Annual Solar Return charts for yearly forecasting
        - Monthly Lunar Return charts for timing analysis
        - Relocation returns for different geographic locations
        - Research into planetary cycle effects
        - Astrological consultation and chart analysis
        - Educational demonstrations of celestial mechanics

    Note:
        Return calculations use the exact degree and minute of natal planetary
        positions. The resulting charts are cast for the precise moment when
        the transiting planet reaches this position, which may not align with
        calendar dates (especially for Solar Returns, which can occur on
        different dates depending on leap years and location).
    """

    def __init__(
        self,
        subject: AstrologicalSubjectModel,
        city: Union[str, None] = None,
        nation: Union[str, None] = None,
        lng: Union[int, float, None] = None,
        lat: Union[int, float, None] = None,
        tz_str: Union[str, None] = None,
        online: bool = True,
        geonames_username: Union[str, None] = None,
        *,
        cache_expire_after_days: int = DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS,
        altitude: Union[float, int, None] = None,
    ):
        """
        Initialize a PlanetaryReturnFactory instance with location and configuration settings.

        This constructor sets up the factory with all necessary parameters for calculating
        planetary returns at a specified location. It supports both online mode (with
        automatic geocoding via Geonames) and offline mode (with manual coordinates).

        The factory validates input parameters based on the chosen mode and automatically
        retrieves missing location data when operating online. All location parameters
        are stored and used for casting return charts at the exact calculated moments.

        Args:
            subject (AstrologicalSubjectModel): The natal astrological subject containing
                birth data and planetary positions. This subject's natal planetary
                positions serve as reference points for calculating returns.
            city (Optional[str]): City name for the return chart location. Must be a
                recognizable city name for Geonames geocoding when using online mode.
                Examples: "New York", "London", "Tokyo", "Paris".
            nation (Optional[str]): Country or nation code for the return chart location.
                Use ISO country codes for best results (e.g., "US", "GB", "JP", "FR").
                Required when online=True.
            lng (Optional[Union[int, float]]): Geographic longitude coordinate in decimal
                degrees for return chart location. Range: -180.0 to +180.0.
                Positive values represent East longitude, negative values West longitude.
                Required when online=False.
            lat (Optional[Union[int, float]]): Geographic latitude coordinate in decimal
                degrees for return chart location. Range: -90.0 to +90.0.
                Positive values represent North latitude, negative values South latitude.
                Required when online=False.
            tz_str (Optional[str]): Timezone identifier string for return chart location.
                Must be a valid timezone from the IANA Time Zone Database
                (e.g., "America/New_York", "Europe/London", "Asia/Tokyo").
                Required when online=False.
            online (bool, optional): Location data retrieval mode. When True, uses
                Geonames web service to automatically fetch coordinates and timezone
                from city/nation parameters. When False, uses manually provided
                coordinates and timezone. Defaults to True.
            geonames_username (Optional[str]): Username for Geonames API access.
                Required when online=True and coordinates are not manually provided.
                Free accounts available at http://www.geonames.org/login.
                If None and required, uses default username with warning.
            cache_expire_after_days (int, optional): Number of days to cache Geonames
                location data locally before requiring refresh. Helps reduce API
                calls and improve performance for repeated calculations.
                Defaults to system configuration value.
            altitude (Optional[Union[float, int]]): Elevation above sea level in meters
                for the return chart location. Currently reserved for future use in
                advanced astronomical calculations. Defaults to None.

        Raises:
            KerykeionException: If city is not provided when online=True.
            KerykeionException: If nation is not provided when online=True.
            KerykeionException: If coordinates (lat/lng) are not provided when online=False.
            KerykeionException: If timezone (tz_str) is not provided when online=False.
            KerykeionException: If Geonames API fails to retrieve valid location data.
            KerykeionException: If required parameters are missing for the chosen mode.

        Examples:
            Initialize with online geocoding:

            >>> factory = PlanetaryReturnFactory(
            ...     subject,
            ...     city="San Francisco",
            ...     nation="US",
            ...     online=True,
            ...     geonames_username="your_username"
            ... )

            Initialize with manual coordinates:

            >>> factory = PlanetaryReturnFactory(
            ...     subject,
            ...     lng=-122.4194,
            ...     lat=37.7749,
            ...     tz_str="America/Los_Angeles",
            ...     online=False
            ... )

            Initialize with mixed parameters (coordinates override online lookup):

            >>> factory = PlanetaryReturnFactory(
            ...     subject,
            ...     city="Custom Location",
            ...     lng=-74.0060,
            ...     lat=40.7128,
            ...     tz_str="America/New_York",
            ...     online=False
            ... )

        Note:
            - When both online and manual coordinates are provided, offline mode takes precedence
            - Geonames cache helps reduce API calls for frequently used locations
            - Timezone accuracy is crucial for precise return calculations
            - Location parameters affect house cusps and angular positions in return charts
        """
        # Store basic configuration
        self.subject = subject
        self.online = online
        self.cache_expire_after_days = cache_expire_after_days
        self.altitude = altitude

        # Geonames username
        if geonames_username is None and online and (not lat or not lng or not tz_str):
            logging.warning(GEONAMES_DEFAULT_USERNAME_WARNING)
            self.geonames_username = DEFAULT_GEONAMES_USERNAME
        else:
            self.geonames_username = geonames_username  # type: ignore

        # City
        if not city and online:
            raise KerykeionException("You need to set the city if you want to use the online mode!")
        else:
            self.city = city

        # Nation
        if not nation and online:
            raise KerykeionException("You need to set the nation if you want to use the online mode!")
        else:
            self.nation = nation

        # Latitude
        if not lat and not online:
            raise KerykeionException(
                "You need to set the coordinates and timezone if you want to use the offline mode!"
            )
        else:
            self.lat = lat  # type: ignore

        # Longitude
        if not lng and not online:
            raise KerykeionException(
                "You need to set the coordinates and timezone if you want to use the offline mode!"
            )
        else:
            self.lng = lng  # type: ignore

        # Timezone
        if (not online) and (not tz_str):
            raise KerykeionException(
                "You need to set the coordinates and timezone if you want to use the offline mode!"
            )
        else:
            self.tz_str = tz_str  # type: ignore

        # Online mode
        if (self.online) and (not self.tz_str) and (not self.lat) and (not self.lng):
            logging.info("Fetching timezone/coordinates from geonames")

            if not self.city or not self.nation or not self.geonames_username:
                raise KerykeionException("You need to set the city and nation if you want to use the online mode!")

            geonames = FetchGeonames(
                self.city,
                self.nation,
                username=self.geonames_username,
                cache_expire_after_days=self.cache_expire_after_days,
            )
            self.city_data: dict[str, str] = geonames.get_serialized_data()

            if (
                "countryCode" not in self.city_data
                or "timezonestr" not in self.city_data
                or "lat" not in self.city_data
                or "lng" not in self.city_data
            ):
                raise KerykeionException("No data found for this city, try again! Maybe check your connection?")

            self.nation = self.city_data["countryCode"]
            self.lng = float(self.city_data["lng"])
            self.lat = float(self.city_data["lat"])
            self.tz_str = self.city_data["timezonestr"]

    def next_return_from_iso_formatted_time(
        self, iso_formatted_time: str, return_type: ReturnType
    ) -> PlanetReturnModel:
        """
        Calculate the next planetary return occurring after a specified ISO-formatted datetime.

        This method computes the exact moment when the specified planet (Sun or Moon) returns
        to its natal position, starting the search from the provided datetime. It uses precise
        Swiss Ephemeris calculations to determine the exact return moment and generates a
        complete astrological chart for that calculated time.

        The calculation process:
        1. Converts the ISO datetime to Julian Day format for astronomical calculations
        2. Uses Swiss Ephemeris functions (solcross_ut/mooncross_ut) to find the exact
           return moment when the planet reaches its natal degree and minute
        3. Creates a complete AstrologicalSubject instance for the calculated return time
        4. Returns a comprehensive PlanetReturnModel with all chart data

        Args:
            iso_formatted_time (str): Starting datetime in ISO format for the search.
                Must be a valid ISO 8601 datetime string (e.g., "2024-01-15T10:30:00"
                or "2024-01-15T10:30:00+00:00"). The method will find the next return
                occurring after this moment.
            return_type (ReturnType): Type of planetary return to calculate.
                Must be either "Solar" for Sun returns or "Lunar" for Moon returns.
                This determines which planet's return cycle to compute.

        Returns:
            PlanetReturnModel: A comprehensive Pydantic model containing complete
                astrological chart data for the calculated return moment, including:
                - Exact return datetime (UTC and local timezone)
                - All planetary positions at the return moment
                - House cusps and angles for the return location
                - Complete astrological subject data with all calculated points
                - Return type identifier and subject name
                - Julian Day Number for the return moment

        Raises:
            KerykeionException: If return_type is not "Solar" or "Lunar".
            ValueError: If iso_formatted_time is not a valid ISO datetime format.
            SwissEphException: If Swiss Ephemeris calculations fail due to invalid
                date ranges or astronomical calculation errors.

        Examples:
            Calculate next Solar Return after a specific date:

            >>> factory = PlanetaryReturnFactory(subject, ...)
            >>> solar_return = factory.next_return_from_iso_formatted_time(
            ...     "2024-06-15T12:00:00",
            ...     "Solar"
            ... )
            >>> print(f"Solar Return: {solar_return.iso_formatted_local_datetime}")
            >>> print(f"Sun position: {solar_return.sun.abs_pos}°")

            Calculate next Lunar Return with timezone:

            >>> lunar_return = factory.next_return_from_iso_formatted_time(
            ...     "2024-01-01T00:00:00+00:00",
            ...     "Lunar"
            ... )
            >>> print(f"Moon return in {lunar_return.tz_str}")
            >>> print(f"Return occurs: {lunar_return.iso_formatted_local_datetime}")

            Access complete chart data from return:

            >>> return_chart = factory.next_return_from_iso_formatted_time(
            ...     datetime.now().isoformat(),
            ...     "Solar"
            ... )
            >>> # Access all planetary positions
            >>> for planet in return_chart.planets_list:
            ...     print(f"{planet.name}: {planet.abs_pos}° in {planet.sign}")
            >>> # Access house cusps
            >>> for house in return_chart.houses_list:
            ...     print(f"House {house.number}: {house.abs_pos}°")

        Technical Notes:
            - Solar returns typically occur within 1-2 days of the natal birthday
            - Lunar returns occur approximately every 27.3 days (sidereal month)
            - Return moments are calculated to the second for maximum precision
            - The method accounts for leap years and varying orbital speeds
            - Return charts use the factory's configured location, not the natal location

        Use Cases:
            - Annual birthday return chart calculations
            - Monthly lunar return timing for astrological consultation
            - Research into planetary cycle patterns and timing
            - Forecasting and predictive astrology applications
            - Educational demonstrations of astronomical cycles

        See Also:
            next_return_from_year(): Simplified interface for yearly calculations
            next_return_from_date(): Date-based calculation interface
        """

        date = datetime.fromisoformat(iso_formatted_time)
        julian_day = datetime_to_julian(date)

        return_julian_date = None
        if return_type == "Solar":
            if self.subject.sun is None:
                raise KerykeionException(
                    "Sun position is required for Solar return but is not available in the subject."
                )
            return_julian_date = swe.solcross_ut(
                self.subject.sun.abs_pos,
                julian_day,
            )
        elif return_type == "Lunar":
            if self.subject.moon is None:
                raise KerykeionException(
                    "Moon position is required for Lunar return but is not available in the subject."
                )
            return_julian_date = swe.mooncross_ut(
                self.subject.moon.abs_pos,
                julian_day,
            )
        else:
            raise KerykeionException(f"Invalid return type {return_type}. Use 'Solar' or 'Lunar'.")

        solar_return_date_utc = julian_to_datetime(return_julian_date)
        solar_return_date_utc = solar_return_date_utc.replace(tzinfo=timezone.utc)

        solar_return_astrological_subject = AstrologicalSubjectFactory.from_iso_utc_time(
            name=self.subject.name,
            iso_utc_time=solar_return_date_utc.isoformat(),
            lng=self.lng,  # type: ignore
            lat=self.lat,  # type: ignore
            tz_str=self.tz_str,  # type: ignore
            city=self.city,  # type: ignore
            nation=self.nation,  # type: ignore
            online=False,
            altitude=self.altitude,
            active_points=self.subject.active_points,
        )

        model_data = solar_return_astrological_subject.model_dump()
        model_data["name"] = f"{self.subject.name} {return_type} Return"
        model_data["return_type"] = return_type

        return PlanetReturnModel(
            **model_data,
        )

    def next_return_from_year(self, year: int, return_type: ReturnType) -> PlanetReturnModel:
        """
        Calculate the planetary return occurring within a specified year.

        This is a convenience method that finds the first planetary return (Solar or Lunar)
        that occurs in the given calendar year. It automatically searches from January 1st
        of the specified year and returns the first return found, making it ideal for
        annual forecasting and birthday return calculations.

        For Solar Returns, this typically finds the return closest to the natal birthday
        within that year. For Lunar Returns, it finds the first lunar return occurring
        in January of the specified year.

        The method internally uses next_return_from_iso_formatted_time() with a starting
        point of January 1st at midnight UTC for the specified year.

        Args:
            year (int): The calendar year to search for the return. Must be a valid
                year (typically between 1800-2200 for reliable ephemeris data).
                Examples: 2024, 2025, 1990, 2050.
            return_type (ReturnType): The type of planetary return to calculate.
                Must be either "Solar" for Sun returns or "Lunar" for Moon returns.

        Returns:
            PlanetReturnModel: A comprehensive model containing the return chart data
                for the first return found in the specified year. Includes:
                - Exact return datetime in both UTC and local timezone
                - Complete planetary positions at the return moment
                - House cusps calculated for the factory's configured location
                - All astrological chart features and calculated points
                - Return type and subject identification

        Raises:
            KerykeionException: If return_type is not "Solar" or "Lunar".
            ValueError: If year is outside the valid range for ephemeris calculations.
            SwissEphException: If astronomical calculations fail for the given year.

        Examples:
            Calculate Solar Return for 2024:

            >>> factory = PlanetaryReturnFactory(subject, ...)
            >>> solar_return_2024 = factory.next_return_from_year(2024, "Solar")
            >>> print(f"2024 Solar Return: {solar_return_2024.iso_formatted_local_datetime}")
            >>> print(f"Birthday location: {solar_return_2024.city}, {solar_return_2024.nation}")

            Calculate first Lunar Return of 2025:

            >>> lunar_return = factory.next_return_from_year(2025, "Lunar")
            >>> print(f"First 2025 Lunar Return: {lunar_return.iso_formatted_local_datetime}")

            Compare multiple years:

            >>> for year in [2023, 2024, 2025]:
            ...     solar_return = factory.next_return_from_year(year, "Solar")
            ...     print(f"{year}: {solar_return.iso_formatted_local_datetime}")

        Practical Applications:
            - Annual Solar Return chart casting for birthday forecasting
            - Comparative analysis of return charts across multiple years
            - Research into planetary return timing patterns
            - Automated birthday return calculations for consultation
            - Educational demonstrations of annual astrological cycles

        Technical Notes:
            - Solar returns in a given year occur near but not exactly on the birthday
            - The exact date can vary by 1-2 days due to leap years and orbital mechanics
            - Lunar returns occur approximately every 27.3 days throughout the year
            - This method finds the chronologically first return in the year
            - Return moment precision is calculated to the second

        Use Cases:
            - Birthday return chart interpretation
            - Annual astrological forecasting
            - Timing analysis for major life events
            - Comparative return chart studies
            - Astrological consultation preparation

        See Also:
            next_return_from_date(): For more specific date-based searches
            next_return_from_iso_formatted_time(): For custom starting dates
        """
        import warnings

        warnings.warn(
            "next_return_from_year is deprecated, use next_return_from_date instead", DeprecationWarning, stacklevel=2
        )
        return self.next_return_from_date(year, 1, 1, return_type=return_type)

    def next_return_from_date(
        self, year: int, month: int, day: int = 1, *, return_type: ReturnType
    ) -> PlanetReturnModel:
        """
        Calculate the first planetary return occurring on or after a specified date.

        This method provides precise timing control for planetary return calculations by
        searching from a specific day, month, and year. It's particularly useful for
        finding Lunar Returns when multiple returns occur within a single month
        (approximately every 27.3 days).

        The method searches from midnight (00:00:00 UTC) of the specified date,
        finding the next return that occurs from that point forward.

        Args:
            year (int): The calendar year to search within. Must be a valid year
                within the ephemeris data range (typically 1800-2200).
            month (int): The month to start the search from. Must be between 1 and 12.
            day (int): The day to start the search from. Must be a valid day for the
                specified month (1-28/29/30/31 depending on month). Defaults to 1.
            return_type (ReturnType): The type of planetary return to calculate.
                Must be either "Solar" for Sun returns or "Lunar" for Moon returns.

        Returns:
            PlanetReturnModel: Comprehensive return chart data for the first return
                found on or after the specified date.

        Raises:
            KerykeionException: If month is not between 1 and 12.
            KerykeionException: If day is not valid for the given month/year.
            KerykeionException: If return_type is not "Solar" or "Lunar".

        Examples:
            Find first Lunar Return after January 15, 2024:

            >>> lunar_return = factory.next_return_from_date(
            ...     2024, 1, 15, return_type="Lunar"
            ... )

            Find second Lunar Return in a month (after the first one):

            >>> # First return from start of month
            >>> first_lr = factory.next_return_from_date(2024, 1, 1, return_type="Lunar")
            >>> # Second return from middle of month
            >>> second_lr = factory.next_return_from_date(2024, 1, 15, return_type="Lunar")

        See Also:
            next_return_from_year(): For annual return calculations
            next_return_from_iso_formatted_time(): For custom datetime searches
        """
        # Validate month input
        if month < 1 or month > 12:
            raise KerykeionException(f"Invalid month {month}. Month must be between 1 and 12.")

        # Validate day input
        max_day = calendar.monthrange(year, month)[1]
        if day < 1 or day > max_day:
            raise KerykeionException(f"Invalid day {day} for {year}-{month:02d}. Day must be between 1 and {max_day}.")

        # Create datetime for the specified date (UTC)
        start_date = datetime(year, month, day, 0, 0, tzinfo=timezone.utc)

        # Get the return using the existing method
        return self.next_return_from_iso_formatted_time(start_date.isoformat(), return_type)

    def next_return_from_month_and_year(self, year: int, month: int, return_type: ReturnType) -> PlanetReturnModel:
        """
        DEPRECATED: Use next_return_from_date() instead.

        Calculate the first planetary return occurring in or after a specified month and year.
        This method is kept for backward compatibility and will be removed in a future version.

        Args:
            year (int): The calendar year to search within.
            month (int): The month to start the search from (1-12).
            return_type (ReturnType): "Solar" or "Lunar".

        Returns:
            PlanetReturnModel: Return chart data for the first return found.
        """
        import warnings

        warnings.warn(
            "next_return_from_month_and_year is deprecated, use next_return_from_date instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.next_return_from_date(year, month, 1, return_type=return_type)


if __name__ == "__main__":
    import json

    # Example usage
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="Test Subject",
        lng=-122.4194,
        lat=37.7749,
        tz_str="America/Los_Angeles",
    )

    print("=== Planet Return Calculator ===")
    calculator = PlanetaryReturnFactory(
        subject,
        city="San Francisco",
        nation="USA",
        online=True,
        geonames_username="century.boy",
    )
    date = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    print(f"INITIAL DATE:                   {date.isoformat()}")
    print(f"INITIAL DATE JULIAN:            {datetime_to_julian(date)}")
    print(f"INITIAL DATE REVERSED:          {julian_to_datetime(datetime_to_julian(date)).isoformat()}")
    solar_return = calculator.next_return_from_iso_formatted_time(
        date.isoformat(),
        return_type="Lunar",
    )
    print("--- After ---")
    print(f"Solar Return Date UTC:          {solar_return.iso_formatted_utc_datetime}")
    print(f"Solar Return Date Local:        {solar_return.iso_formatted_local_datetime}")
    print(f"Solar Return JSON:              {json.dumps(solar_return.model_dump(), indent=4)}")
    print(f"Solar Return Julian Data:       {solar_return.julian_day}")
    print(f"ISO UTC:                        {solar_return.iso_formatted_utc_datetime}")

    ## From Date (year, month, day)
    print("=== Planet Return Calculator ===")
    solar_return = calculator.next_return_from_date(
        2026,
        1,
        1,
        return_type="Lunar",
    )
    print("--- From Date (Jan 1) ---")
    print(f"Solar Return Julian Data:       {solar_return.julian_day}")
    print(f"Solar Return Date UTC:          {solar_return.iso_formatted_utc_datetime}")
    ## From Month and Year
    print("=== Planet Return Calculator ===")
    solar_return = calculator.next_return_from_date(
        2026,
        1,
        15,  # Start from January 15
        return_type="Lunar",
    )
    print("--- From Date ---")
    print(f"Solar Return Julian Data:       {solar_return.julian_day}")
    print(f"Solar Return Date UTC:          {solar_return.iso_formatted_utc_datetime}")
