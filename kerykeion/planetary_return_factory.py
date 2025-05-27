# -*- coding: utf-8 -*-
"""
Module for generating Planetary Return charts using the Swiss Ephemeris.

This module provides the PlanetaryReturnFactory class, which computes
the return times and chart data for solar and lunar returns of a natal
astrological subject.
"""
import logging
import swisseph as swe

from datetime import datetime, timezone
from typing import Optional, Union

from kerykeion.kr_types import KerykeionException
from kerykeion.fetch_geonames import FetchGeonames
from kerykeion.utilities import julian_to_datetime, datetime_to_julian
from kerykeion.astrological_subject_factory import (
    GEONAMES_DEFAULT_USERNAME_WARNING,
    DEFAULT_GEONAMES_CACHE_EXPIRE_AFTER_DAYS,
)
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.kr_types.kr_literals import ReturnType
from kerykeion.kr_types.kr_models import PlanetReturnModel, AstrologicalSubjectModel


class PlanetaryReturnFactory:
    """
    Calculator class to generate Solar and Lunar Return charts.
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
        Initialize a PlanetaryReturnFactory instance.

        Args:
            subject (AstrologicalSubject): The natal astrological subject.
            city (Optional[str]): City name for return location (online mode).
            nation (Optional[str]): Nation code for return location (online mode).
            lng (Optional[Union[int, float]]): Longitude for return location.
            lat (Optional[Union[int, float]]): Latitude for return location.
            tz_str (Optional[str]): Timezone string for return location.
            online (bool): Whether to fetch location data online via Geonames.
            geonames_username (Optional[str]): Username for Geonames API.
            cache_expire_after_days (int): Days to expire Geonames cache.
            altitude (Optional[float]): Altitude of the location (reserved for future use).
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
            self.geonames_username = geonames_username # type: ignore

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
            raise KerykeionException("You need to set the coordinates and timezone if you want to use the offline mode!")
        else:
            self.lat = lat # type: ignore

        # Longitude
        if not lng and not online:
            raise KerykeionException("You need to set the coordinates and timezone if you want to use the offline mode!")
        else:
            self.lng = lng # type: ignore

        # Timezone
        if (not online) and (not tz_str):
            raise KerykeionException("You need to set the coordinates and timezone if you want to use the offline mode!")
        else:
            self.tz_str = tz_str # type: ignore

        # Online mode
        if (self.online) and (not self.tz_str) and (not self.lat) and (not self.lng):
            logging.info("Fetching timezone/coordinates from geonames")

            if not self.city or not self.nation or not self.geonames_username:
                raise KerykeionException("You need to set the city and nation if you want to use the online mode!")

            geonames = FetchGeonames(
                self.city,
                self.nation,
                username=self.geonames_username,
                cache_expire_after_days=self.cache_expire_after_days
            )
            self.city_data: dict[str, str] = geonames.get_serialized_data()

            if (
                not "countryCode" in self.city_data
                or not "timezonestr" in self.city_data
                or not "lat" in self.city_data
                or not "lng" in self.city_data
            ):
                raise KerykeionException("No data found for this city, try again! Maybe check your connection?")

            self.nation = self.city_data["countryCode"]
            self.lng = float(self.city_data["lng"])
            self.lat = float(self.city_data["lat"])
            self.tz_str = self.city_data["timezonestr"]

    def next_return_from_iso_formatted_time(
        self,
        iso_formatted_time: str,
        return_type: ReturnType
    ) -> PlanetReturnModel:
        """
        Get the next Return for the provided ISO-formatted time.

        Args:
            iso_formatted_time (str): ISO-formatted datetime string.

        Returns:
            PlanetReturnModel: Pydantic model containing the return chart data.
        """

        date = datetime.fromisoformat(iso_formatted_time)
        julian_day = datetime_to_julian(date)

        return_julian_date = None
        if return_type == "Solar":
            return_julian_date = swe.solcross_ut(
                self.subject.sun.abs_pos,
                julian_day,
            )
        elif return_type == "Lunar":
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
            lng=self.lng,       # type: ignore
            lat=self.lat,       # type: ignore
            tz_str=self.tz_str, # type: ignore
            city=self.city,     # type: ignore
            nation=self.nation, # type: ignore
            online=False,
            altitude=self.altitude,
        )

        model_data = solar_return_astrological_subject.model_dump()
        model_data['name'] = f"{self.subject.name} {return_type} Return"
        model_data['return_type'] = return_type

        return PlanetReturnModel(
            **model_data,
        )

    def next_return_from_year(
        self,
        year: int,
        return_type: ReturnType
    ) -> PlanetReturnModel:
        """
        Get the next Return for the specified year.

        This method finds the first return that occurs in the given year.

        Args:
            year (int): The year to search for the return
            return_type (ReturnType): The type of return ("Solar" or "Lunar")

        Returns:
            PlanetReturnModel: Pydantic model containing the return chart data
        """
        # Create datetime for January 1st of the specified year (UTC)
        start_date = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc)

        # Get the return using the existing method
        return self.next_return_from_iso_formatted_time(
            start_date.isoformat(),
            return_type
        )

    def next_return_from_month_and_year(
        self,
        year: int,
        month: int,
        return_type: ReturnType
    ) -> PlanetReturnModel:
        """
        Get the next Return for the specified month and year.

        This method finds the first return that occurs after the first day
        of the specified month and year.

        Args:
            year (int): The year to search for the return
            month (int): The month to search for the return (1-12)
            return_type (ReturnType): The type of return ("Solar" or "Lunar")

        Returns:
            PlanetReturnModel: Pydantic model containing the return chart data
        """
        # Validate month input
        if month < 1 or month > 12:
            raise KerykeionException(f"Invalid month {month}. Month must be between 1 and 12.")

        # Create datetime for the first day of the specified month and year (UTC)
        start_date = datetime(year, month, 1, 0, 0, tzinfo=timezone.utc)

        # Get the return using the existing method
        return self.next_return_from_iso_formatted_time(
            start_date.isoformat(),
            return_type
        )


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

    ## From Year
    print("=== Planet Return Calculator ===")
    solar_return = calculator.next_return_from_year(
        2026,
        return_type="Lunar",
    )
    print("--- From Year ---")
    print(f"Solar Return Julian Data:       {solar_return.julian_day}")
    print(f"Solar Return Date UTC:          {solar_return.iso_formatted_utc_datetime}")
    ## From Month and Year
    print("=== Planet Return Calculator ===")
    solar_return = calculator.next_return_from_month_and_year(
        2026,
        1,
        return_type="Lunar",
    )
    print("--- From Month and Year ---")
    print(f"Solar Return Julian Data:       {solar_return.julian_day}")
    print(f"Solar Return Date UTC:          {solar_return.iso_formatted_utc_datetime}")
