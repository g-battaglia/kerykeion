# -*- coding: utf-8 -*-
"""
Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from logging import getLogger
from datetime import timedelta
from json import JSONDecodeError
from os import getenv
from pathlib import Path
from typing import Optional, Union

from requests import Request, RequestException, Response
from requests_cache import CachedSession


logger = getLogger(__name__)


DEFAULT_GEONAMES_CACHE_NAME = Path("cache") / "kerykeion_geonames_cache"
GEONAMES_CACHE_ENV_VAR = "KERYKEION_GEONAMES_CACHE_NAME"

# GeoNames error codes that represent transient errors and should NOT be cached.
# These errors are temporary (rate limits, timeouts, server issues) and will resolve
# on retry, so caching them would "poison" the cache with error responses.
# See: https://www.geonames.org/export/webservice-exception.html
TRANSIENT_GEONAMES_ERROR_CODES = frozenset(
    {
        13,  # database timeout
        18,  # daily limit of credits exceeded
        19,  # hourly limit of credits exceeded
        20,  # weekly limit of credits exceeded
        22,  # server overloaded exception
    }
)


def _should_cache_geonames_response(response: Response) -> bool:
    """
    Filter function for requests-cache to prevent caching transient error responses.

    GeoNames API returns errors with HTTP 200 status code but with a 'status' key
    in the JSON response. This function checks for transient errors (rate limits,
    timeouts, server overload) and returns False to prevent caching them.

    Args:
        response: The HTTP response to evaluate.

    Returns:
        True if the response should be cached, False otherwise.
    """
    try:
        data = response.json()
        if "status" in data:
            error_code = data["status"].get("value", 0)
            if error_code in TRANSIENT_GEONAMES_ERROR_CODES:
                logger.debug(
                    "GeoNames transient error (code %d) will not be cached: %s",
                    error_code,
                    data["status"].get("message", "unknown error"),
                )
                return False
        return True
    except (ValueError, JSONDecodeError):
        # If we can't parse the response, don't cache it
        return False


class FetchGeonames:
    """
    Class to handle requests to the GeoNames API for location data and timezone information.

    This class provides cached access to the GeoNames API to retrieve location coordinates,
    timezone information, and other geographical data for astrological calculations.

    Args:
        city_name: Name of the city to search for.
        country_code: Two-letter country code (ISO 3166-1 alpha-2).
        username: GeoNames username for API access, defaults to "century.boy".
        cache_expire_after_days: Number of days to cache responses, defaults to 30.
        cache_name: Optional path (directory or filename stem) used by requests-cache.
            Defaults to "cache/kerykeion_geonames_cache" and may also be overridden
            via the environment variable ``KERYKEION_GEONAMES_CACHE_NAME`` or by
            calling :meth:`FetchGeonames.set_default_cache_name`.
    """

    default_cache_name: Path = DEFAULT_GEONAMES_CACHE_NAME

    def __init__(
        self,
        city_name: str,
        country_code: str,
        username: str = "century.boy",
        cache_expire_after_days=30,
        cache_name: Optional[Union[str, Path]] = None,
    ):
        self.session = CachedSession(
            cache_name=str(self._resolve_cache_name(cache_name)),
            backend="sqlite",
            expire_after=timedelta(days=cache_expire_after_days),
            filter_fn=_should_cache_geonames_response,
        )

        self.username = username
        self.city_name = city_name
        self.country_code = country_code
        # NOTE: GeoNames free API does not support HTTPS (SSL certificate mismatch).
        # See: https://forum.geonames.org/gforum/posts/list/27020.page
        # Premium users can use secure.geonames.org instead.
        self.base_url = "http://api.geonames.org/searchJSON"
        self.timezone_url = "http://api.geonames.org/timezoneJSON"

    @classmethod
    def set_default_cache_name(cls, cache_name: Union[str, Path]) -> None:
        """Override the default cache name used when none is provided."""

        cls.default_cache_name = Path(cache_name)

    @classmethod
    def _resolve_cache_name(cls, cache_name: Optional[Union[str, Path]]) -> Path:
        """Return the resolved cache name applying overrides in priority order."""

        if cache_name is not None:
            return Path(cache_name)

        env_override = getenv(GEONAMES_CACHE_ENV_VAR)
        if env_override:
            return Path(env_override)

        return cls.default_cache_name

    def __get_timezone(self, lat: Union[str, float, int], lon: Union[str, float, int]) -> dict[str, str]:
        """
        Get timezone information for a given latitude and longitude.

        Args:
            lat: Latitude coordinate.
            lon: Longitude coordinate.

        Returns:
            dict: Timezone data including timezone string and cache status.
        """
        # Dictionary that will be returned:
        timezone_data = {}

        params = {"lat": lat, "lng": lon, "username": self.username}

        prepared_request = Request("GET", self.timezone_url, params=params).prepare()
        logger.debug("GeoNames timezone lookup url=%s", prepared_request.url)

        try:
            response = self.session.send(prepared_request)
            response_json = response.json()

        except RequestException as e:
            logger.error("GeoNames timezone network error for %s: %s", self.timezone_url, e)
            return {}
        except JSONDecodeError as e:
            logger.error("GeoNames timezone invalid JSON response: %s", e)
            return {}

        try:
            timezone_data["timezonestr"] = response_json["timezoneId"]

        except (KeyError, TypeError) as e:
            logger.error("GeoNames timezone payload missing expected keys: %s", e)
            return {}

        if hasattr(response, "from_cache"):
            timezone_data["from_tz_cache"] = response.from_cache  # type: ignore

        return timezone_data

    def __get_country_data(self, city_name: str, country_code: str) -> dict[str, str]:
        """
        Get city location data without timezone for a given city and country.

        Args:
            city_name: Name of the city to search for.
            country_code: Two-letter country code.

        Returns:
            dict: City location data excluding timezone information.
        """
        # Dictionary that will be returned:
        city_data_without_tz = {}

        params = {
            "q": city_name,
            "country": country_code,
            "username": self.username,
            "maxRows": 1,
            "style": "SHORT",
            "featureClass": ["A", "P"],
        }

        prepared_request = Request("GET", self.base_url, params=params).prepare()
        logger.debug("GeoNames search url=%s", prepared_request.url)

        try:
            response = self.session.send(prepared_request)
            response.raise_for_status()
            response_json = response.json()
            logger.debug("GeoNames search response: %s", response_json)

        except RequestException as e:
            logger.error("GeoNames search network error for %s: %s", self.base_url, e)
            return {}
        except JSONDecodeError as e:
            logger.error("GeoNames search invalid JSON response: %s", e)
            return {}

        try:
            city_data_without_tz["name"] = response_json["geonames"][0]["name"]
            city_data_without_tz["lat"] = response_json["geonames"][0]["lat"]
            city_data_without_tz["lng"] = response_json["geonames"][0]["lng"]
            city_data_without_tz["countryCode"] = response_json["geonames"][0]["countryCode"]

        except (KeyError, IndexError, TypeError) as e:
            logger.error("GeoNames search payload missing expected keys: %s", e)
            return {}

        if hasattr(response, "from_cache"):
            city_data_without_tz["from_country_cache"] = response.from_cache  # type: ignore

        return city_data_without_tz

    def __get_contry_data(self, city_name: str, country_code: str) -> dict[str, str]:
        return self.__get_country_data(city_name, country_code)

    def get_serialized_data(self) -> dict[str, str]:
        """
        Returns all the data necessary for the Kerykeion calculation.

        Returns:
            dict[str, str]: Dictionary containing city name, latitude, longitude,
                country code, timezone, and cache status information.
        """
        city_data_response = self.__get_country_data(self.city_name, self.country_code)
        try:
            timezone_response = self.__get_timezone(city_data_response["lat"], city_data_response["lng"])

        except KeyError as e:
            logger.error("Unable to fetch timezone details, missing key: %s", e)
            return {}

        return {**timezone_response, **city_data_response}


if __name__ == "__main__":
    """Run a tiny demonstration when executing the module directly."""
    from kerykeion.utilities import setup_logging as configure_logging

    configure_logging("debug")
    geonames = FetchGeonames("Montichiari", "IT")
    print(geonames.get_serialized_data())
