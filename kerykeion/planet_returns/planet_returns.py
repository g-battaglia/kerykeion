# -*- coding: utf-8 -*-
"""
Generate Solar and Lunar Return charts using Swiss Ephemeris.
"""

from datetime import datetime, timezone
import swisseph as swe
from typing import Optional

from kerykeion.astrological_subject import AstrologicalSubject
from kerykeion.astrological_subject import (
    DEFAULT_GEONAMES_USERNAME,
    DEFAULT_ZODIAC_TYPE,
    DEFAULT_SIDEREAL_MODE,
    DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
    DEFAULT_PERSPECTIVE_TYPE,
)
from kerykeion.kr_types.kr_literals import (
    ZodiacType,
    SiderealMode,
    HousesSystemIdentifier,
    PerspectiveType,
)
from .planet_returns_models import SolarReturnModel, LunarReturnModel


class PlanetReturns:
    """
    Class to generate Solar Return and Lunar Return charts.
    """

    @staticmethod
    def generate_solar_return(
        start_date: datetime,
        natal_longitude: float,
        *,
        name: str,
        city: str,
        nation: str,
        lng: float,
        lat: float,
        tz_str: str,
        online: bool = False,
        geonames_username: str = DEFAULT_GEONAMES_USERNAME,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: Optional[SiderealMode] = DEFAULT_SIDEREAL_MODE,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        disable_chiron_and_lilith: bool = False,
    ) -> SolarReturnModel:
        """
        Compute the next Solar Return chart for a given natal longitude.

        :param start_date: Starting datetime to search for the return (UTC or with tzinfo).
        :param natal_longitude: Natal longitude of the Sun in degrees.
        :param name: Name for the return chart.
        :param city: Birth city.
        :param nation: Birth nation code.
        :param lng: Longitude of birth location.
        :param lat: Latitude of birth location.
        :param tz_str: Timezone string of birth location.
        :param online: Whether to fetch timezone/coordinates online.
        :param geonames_username: Geonames API username.
        :param zodiac_type: Zodiac type ("Tropic" or "Sidereal").
        :param sidereal_mode: Sidereal mode to use.
        :param houses_system_identifier: Houses system identifier.
        :param perspective_type: Perspective type.
        :param disable_chiron_and_lilith: Disable Chiron and Lilith.
        :return: SolarReturnModel with full astrological chart at return moment.
        """
        if start_date.tzinfo is None:
            utc_dt = start_date.replace(tzinfo=timezone.utc)
        else:
            utc_dt = start_date.astimezone(timezone.utc)

        # Compute Julian Day (UT)
        jd_start = swe.julday(
            utc_dt.year,
            utc_dt.month,
            utc_dt.day,
            utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600,
        )
        # Find next solar return moment (UT)
        jd_return = swe.solcross_ut(natal_longitude, jd_start)

        # Convert Julian Day to calendar date/time
        year, month, day, hour_float = swe.revjul(jd_return, swe.GREG_CAL)
        hh = int(hour_float)
        mm = int((hour_float - hh) * 60)
        ss = int(((hour_float - hh) * 60 - mm) * 60)
        iso_utc = datetime(year, month, day, hh, mm, ss, tzinfo=timezone.utc).isoformat()

        # Build full astrological chart at return moment
        subject = AstrologicalSubject.get_from_iso_utc_time(
            name=name,
            iso_utc_time=iso_utc,
            city=city,
            nation=nation,
            tz_str=tz_str,
            online=online,
            lng=lng,
            lat=lat,
            geonames_username=geonames_username,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
            disable_chiron_and_lilith=disable_chiron_and_lilith,
        )
        base_model = subject.model()
        return SolarReturnModel(**base_model.model_dump())

    @staticmethod
    def generate_lunar_return(
        start_date: datetime,
        natal_longitude: float,
        *,
        name: str,
        city: str,
        nation: str,
        lng: float,
        lat: float,
        tz_str: str,
        online: bool = False,
        geonames_username: str = DEFAULT_GEONAMES_USERNAME,
        zodiac_type: ZodiacType = DEFAULT_ZODIAC_TYPE,
        sidereal_mode: Optional[SiderealMode] = DEFAULT_SIDEREAL_MODE,
        houses_system_identifier: HousesSystemIdentifier = DEFAULT_HOUSES_SYSTEM_IDENTIFIER,
        perspective_type: PerspectiveType = DEFAULT_PERSPECTIVE_TYPE,
        disable_chiron_and_lilith: bool = False,
    ) -> LunarReturnModel:
        """
        Compute the next Lunar Return chart for a given natal longitude.

        :param start_date: Starting datetime to search for the return (UTC or with tzinfo).
        :param natal_longitude: Natal longitude of the Moon in degrees.
        :param name: Name for the return chart.
        :param city: Birth city.
        :param nation: Birth nation code.
        :param lng: Longitude of birth location.
        :param lat: Latitude of birth location.
        :param tz_str: Timezone string of birth location.
        :param online: Whether to fetch timezone/coordinates online.
        :param geonames_username: Geonames API username.
        :param zodiac_type: Zodiac type ("Tropic" or "Sidereal").
        :param sidereal_mode: Sidereal mode to use.
        :param houses_system_identifier: Houses system identifier.
        :param perspective_type: Perspective type.
        :param disable_chiron_and_lilith: Disable Chiron and Lilith.
        :return: LunarReturnModel with full astrological chart at return moment.
        """
        if start_date.tzinfo is None:
            utc_dt = start_date.replace(tzinfo=timezone.utc)
        else:
            utc_dt = start_date.astimezone(timezone.utc)

        jd_start = swe.julday(
            utc_dt.year,
            utc_dt.month,
            utc_dt.day,
            utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600,
        )
        jd_return = swe.mooncross_ut(natal_longitude, jd_start)

        year, month, day, hour_float = swe.revjul(jd_return, swe.GREG_CAL)
        hh = int(hour_float)
        mm = int((hour_float - hh) * 60)
        ss = int(((hour_float - hh) * 60 - mm) * 60)
        iso_utc = datetime(year, month, day, hh, mm, ss, tzinfo=timezone.utc).isoformat()

        subject = AstrologicalSubject.get_from_iso_utc_time(
            name=name,
            iso_utc_time=iso_utc,
            city=city,
            nation=nation,
            tz_str=tz_str,
            online=online,
            lng=lng,
            lat=lat,
            geonames_username=geonames_username,
            zodiac_type=zodiac_type,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=houses_system_identifier,
            perspective_type=perspective_type,
            disable_chiron_and_lilith=disable_chiron_and_lilith,
        )
        base_model = subject.model()

        return LunarReturnModel(**base_model.model_dump())
