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


# Per-user default (same ~/.kerykeion convention as DEFAULT_SWEPH_DOWNLOAD_DIR):
# a CWD-relative default would scatter cache files across every directory the
# library happens to be invoked from.
DEFAULT_GEONAMES_CACHE_NAME = Path.home() / ".kerykeion" / "cache" / "kerykeion_geonames_cache"
GEONAMES_CACHE_ENV_VAR = "KERYKEION_GEONAMES_CACHE_NAME"

# (connect, read) timeout in seconds for GeoNames HTTP calls. Without a timeout a
# slow/hung endpoint would block the calling thread indefinitely (resource exhaustion).
DEFAULT_GEONAMES_TIMEOUT = (3.05, 10)

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

# Credential/authorization errors: not transient, but caching them would serve
# a stale auth failure for up to the cache expiry after the credential is fixed.
_AUTH_GEONAMES_ERROR_CODES = frozenset(
    {
        10,  # authorization exception (invalid username)
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
        if not isinstance(data, dict):
            # Lists, strings and other scalars are never valid GeoNames payloads;
            # they pass the "status" check below silently, so reject them here to
            # avoid caching malformed responses until expiry.
            return False
        if "status" in data:
            status = data["status"] if isinstance(data["status"], dict) else {}
            error_code = status.get("value", 0)
            # Transient (quota/timeout/overload) and credential (invalid
            # username) errors must not be cached, or a stale error is served
            # until the cache expiry (up to 30 days). A genuine stable-negative
            # result (code 15, "no result found" for a nonexistent place) stays
            # cacheable — re-querying it every time would waste API credits.
            if error_code in TRANSIENT_GEONAMES_ERROR_CODES or error_code in _AUTH_GEONAMES_ERROR_CODES:
                logger.debug(
                    "GeoNames error (code %s) will not be cached: %s",
                    error_code,
                    status.get("message", "unknown error"),
                )
                return False
        return True
    except (ValueError, JSONDecodeError, AttributeError, TypeError):
        # If we can't parse the response (or 'status' is not a dict / data is a
        # scalar), don't cache it.
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
            Defaults to ``~/.kerykeion/cache/kerykeion_geonames_cache`` and may also
            be overridden via the environment variable ``KERYKEION_GEONAMES_CACHE_NAME``
            or by calling :meth:`FetchGeonames.set_default_cache_name`. The chosen
            ``cache_expire_after_days`` is appended to the stem, so instances with
            different TTLs never share a sqlite file (requests-cache stamps each
            entry's expiry at write time, so a short-TTL caller would otherwise be
            served a long-lived entry written by another instance).
    """

    default_cache_name: Path = DEFAULT_GEONAMES_CACHE_NAME

    def __init__(
        self,
        city_name: str,
        country_code: str,
        username: str = "century.boy",
        cache_expire_after_days: int = 30,
        cache_name: Optional[Union[str, Path]] = None,
    ):
        resolved_cache_name = self._resolve_cache_name(cache_name)
        # Segregate the store by TTL: the expiry of a cached response is fixed at
        # write time to the writing session's expire_after, and the default store
        # is shared across every instance — so a caller asking for a 1-day TTL
        # could otherwise read a 30-day entry another instance persisted.
        resolved_cache_name = resolved_cache_name.with_name(f"{resolved_cache_name.name}_{cache_expire_after_days}d")
        # Ensure the cache directory exists (the per-user default lives under
        # ~/.kerykeion/cache/, which may not exist yet on a fresh install).
        resolved_cache_name.parent.mkdir(parents=True, exist_ok=True)
        self.session = CachedSession(
            cache_name=str(resolved_cache_name),
            backend="sqlite",
            expire_after=timedelta(days=cache_expire_after_days),
            filter_fn=_should_cache_geonames_response,
        )

        self.username = username
        self.city_name = city_name
        self.country_code = country_code
        # secure.geonames.org serves the same endpoints over HTTPS (the
        # historical SSL certificate mismatch on api.geonames.org is why the
        # plaintext host was used before; the secure host works for free
        # accounts too, so credentials no longer travel in cleartext).
        self.base_url = "https://secure.geonames.org/searchJSON"
        self.timezone_url = "https://secure.geonames.org/timezoneJSON"

    def close(self) -> None:
        """Close the underlying cached HTTP session and release its file handles.

        Each ``FetchGeonames`` opens a sqlite-backed ``CachedSession`` (two file
        descriptors). Long-lived callers that keep instances referenced can
        otherwise exhaust file descriptors; use :meth:`close` or the context
        manager form to release them deterministically instead of at GC time.
        """
        session = getattr(self, "session", None)
        if session is not None:
            session.close()

    def __enter__(self) -> "FetchGeonames":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

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
        # Log the endpoint only — prepared_request.url carries the GeoNames username
        # (an API credential) as a query param; never write it to the logs.
        logger.debug("GeoNames timezone lookup endpoint=%s", self.timezone_url)

        try:
            response = self.session.send(prepared_request, timeout=DEFAULT_GEONAMES_TIMEOUT)
            response.raise_for_status()
            response_json = response.json()

        except RequestException as e:
            logger.error("GeoNames timezone network error for %s: %s", self.timezone_url, e)
            return {}
        except JSONDecodeError as e:
            logger.error("GeoNames timezone invalid JSON response: %s", e)
            return {}

        # GeoNames signals API errors (invalid username, quota) as HTTP 200 with
        # a 'status' object; surface it clearly instead of the misleading
        # "payload missing expected keys" KeyError the lookup below would raise.
        if isinstance(response_json, dict) and "status" in response_json:
            status = response_json["status"] if isinstance(response_json["status"], dict) else {}
            logger.error(
                "GeoNames timezone API error (code %s): %s",
                status.get("value"),
                status.get("message", "unknown error"),
            )
            return {}

        try:
            tz_id = response_json["timezoneId"]
        except (KeyError, TypeError) as e:
            logger.error("GeoNames timezone payload missing expected keys: %s", e)
            return {}

        # A present-but-empty timezoneId would slip past the key-presence check
        # and reach the tz resolver as "", which it rejects. Treat it as missing.
        if not tz_id:
            logger.error("GeoNames timezone payload had an empty timezoneId.")
            return {}
        timezone_data["timezonestr"] = tz_id

        if hasattr(response, "from_cache"):
            timezone_data["from_tz_cache"] = response.from_cache  # type: ignore

        return timezone_data

    def get_timezone_for_coordinates(self, lat: Union[str, float, int], lng: Union[str, float, int]) -> dict[str, str]:
        """
        Resolve the timezone for explicit coordinates via the timezoneJSON endpoint.

        Unlike :meth:`get_serialized_data`, this does not perform a city search:
        it queries the GeoNames timezoneJSON endpoint directly with the given
        coordinates, reusing the same cached session (so repeated lookups are
        served from the local cache).

        Args:
            lat: Latitude coordinate.
            lng: Longitude coordinate.

        Returns:
            dict[str, str]: Dictionary with ``timezonestr`` (and cache status) on
                success; an empty dict when the response is missing a ``timezoneId``
                or the request fails.
        """
        return self.__get_timezone(lat, lng)

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
        # Log the endpoint only — prepared_request.url carries the GeoNames username
        # (an API credential) as a query param; never write it to the logs.
        logger.debug("GeoNames search endpoint=%s", self.base_url)

        try:
            response = self.session.send(prepared_request, timeout=DEFAULT_GEONAMES_TIMEOUT)
            response.raise_for_status()
            response_json = response.json()
            # Guard len() against a malformed payload where "geonames" is not a list
            # (e.g. a scalar): logger args are evaluated eagerly, and a TypeError here
            # would escape the RequestException/JSONDecodeError handlers below.
            geonames = response_json.get("geonames") if isinstance(response_json, dict) else None
            logger.debug(
                "GeoNames search returned %d result(s)",
                len(geonames) if isinstance(geonames, list) else 0,
            )

        except RequestException as e:
            logger.error("GeoNames search network error for %s: %s", self.base_url, e)
            return {}
        except JSONDecodeError as e:
            logger.error("GeoNames search invalid JSON response: %s", e)
            return {}

        # GeoNames returns API errors (invalid username, quota exceeded) as
        # HTTP 200 with a 'status' object and no 'geonames' array; surface it
        # clearly instead of the misleading "payload missing expected keys".
        if isinstance(response_json, dict) and "status" in response_json:
            status = response_json["status"] if isinstance(response_json["status"], dict) else {}
            logger.error(
                "GeoNames search API error (code %s): %s",
                status.get("value"),
                status.get("message", "unknown error"),
            )
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
        """Backward-compat shim for typo in method name. Delegates to __get_country_data."""
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
