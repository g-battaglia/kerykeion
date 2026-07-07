"""
Tests for the FetchGeonames class and cache filtering logic.

Consolidates tests from tests/external/test_fetch_geonames.py.
Online tests are marked with @pytest.mark.online and require network access.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException

from kerykeion.fetch_geonames import (
    FetchGeonames,
    _should_cache_geonames_response,
    TRANSIENT_GEONAMES_ERROR_CODES,
)

# Serialize all tests in this module to avoid GeoNames API rate limiting
pytestmark = pytest.mark.xdist_group(name="geonames")


# ---------------------------------------------------------------------------
# 1. TestGeonamesOnline
# ---------------------------------------------------------------------------


@pytest.mark.online
class TestGeonamesOnline:
    """Tests that actually hit the GeoNames network API."""

    def test_roma_lookup_returns_expected_fields(self):
        """Roma/IT lookup returns expected lat, lng, tz_str, country_code."""
        geonames = FetchGeonames("Roma", "IT")
        data = geonames.get_serialized_data()

        assert data["timezonestr"] == "Europe/Rome"
        assert data["name"] == "Rome"
        assert data["lat"] == "41.89193"
        assert data["lng"] == "12.51133"
        assert data["countryCode"] == "IT"

    def test_error_handling_returns_empty_dict(self):
        """Network errors result in an empty dict from get_serialized_data."""
        with patch("kerykeion.fetch_geonames.CachedSession") as mock_session:
            mock_session_instance = Mock()
            mock_session_instance.send.side_effect = RequestException("Network error")
            mock_session.return_value = mock_session_instance

            fetcher = FetchGeonames("NonexistentCity", "XX", username="test_user")
            result = fetcher.get_serialized_data()
            assert result == {}


# ---------------------------------------------------------------------------
# 2. TestGeonamesMocked
# ---------------------------------------------------------------------------


class TestGeonamesMocked:
    """Tests using mocked network calls."""

    def test_basic_functionality(self):
        """Test basic attribute assignment on FetchGeonames."""
        fetcher = FetchGeonames("TestCity", "TS")
        assert fetcher.city_name == "TestCity"
        assert fetcher.country_code == "TS"

    def test_urls_use_https_secure_endpoint(self):
        """GeoNames calls must go over HTTPS (secure.geonames.org), not
        plaintext HTTP: the username credential travels as a query param."""
        fetcher = FetchGeonames("TestCity", "TS")
        assert fetcher.base_url == "https://secure.geonames.org/searchJSON"
        assert fetcher.timezone_url == "https://secure.geonames.org/timezoneJSON"

    def test_get_timezone_for_coordinates_returns_timezonestr(self):
        """The public coordinate-based lookup hits the timezoneJSON endpoint
        (reusing the cached session) and returns the timezonestr."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"timezoneId": "Europe/Rome", "gmtOffset": 1}
        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=mock_response) as mock_send:
            result = geonames.get_timezone_for_coordinates(41.9028, 12.4964)

        assert result["timezonestr"] == "Europe/Rome"
        sent_url = mock_send.call_args.args[0].url
        assert sent_url.startswith("https://secure.geonames.org/timezoneJSON")

    def test_get_timezone_for_coordinates_missing_timezone_id_returns_empty(self):
        """A timezoneJSON payload without a timezoneId yields an empty dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"gmtOffset": 1}
        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=mock_response):
            result = geonames.get_timezone_for_coordinates(41.9028, 12.4964)
        assert result == {}

    def test_exception_handling_with_mocks(self):
        """Mocked session raising RequestException returns empty dict."""
        with patch("kerykeion.fetch_geonames.CachedSession") as mock_session:
            mock_session_instance = Mock()
            mock_session_instance.send.side_effect = RequestException("Network error")
            mock_session.return_value = mock_session_instance

            fetcher = FetchGeonames("TestCity", "TS", username="test_user")
            result = fetcher.get_serialized_data()
            assert result == {}

    def test_malformed_geonames_scalar_does_not_raise(self):
        """A payload whose 'geonames' is a scalar (not a list) must not raise a
        TypeError from the debug-log len(): logger args are evaluated eagerly and
        such a TypeError would escape the network/JSON handlers. Expect {} instead."""
        with patch("kerykeion.fetch_geonames.CachedSession") as mock_session:
            response = Mock()
            response.raise_for_status = Mock()
            response.json = Mock(return_value={"geonames": 5})
            mock_session_instance = Mock()
            mock_session_instance.send.return_value = response
            mock_session.return_value = mock_session_instance

            fetcher = FetchGeonames("TestCity", "TS", username="test_user")
            result = fetcher.get_serialized_data()
            assert result == {}

    def test_custom_cache_name(self, monkeypatch, tmp_path):
        """Custom cache_name is forwarded to CachedSession (its parent
        directory is created on demand)."""
        session_mock = Mock()
        cached_session_mock = Mock(return_value=session_mock)
        monkeypatch.setattr("kerykeion.fetch_geonames.CachedSession", cached_session_mock)

        custom_cache_name = tmp_path / "custom" / "cache" / "path"
        FetchGeonames("TestCity", "TS", cache_name=custom_cache_name)

        assert cached_session_mock.call_args.kwargs["cache_name"] == str(custom_cache_name)
        assert custom_cache_name.parent.is_dir()

    def test_default_cache_name(self, monkeypatch, tmp_path):
        """Default cache_name uses FetchGeonames.default_cache_name."""
        session_mock = Mock()
        cached_session_mock = Mock(return_value=session_mock)
        monkeypatch.setattr("kerykeion.fetch_geonames.CachedSession", cached_session_mock)

        monkeypatch.setattr(FetchGeonames, "default_cache_name", tmp_path / "geo_cache")
        FetchGeonames("TestCity", "TS")
        assert cached_session_mock.call_args.kwargs["cache_name"] == str(tmp_path / "geo_cache")

    def test_default_cache_name_is_per_user(self):
        """The default cache lives in the per-user ~/.kerykeion/cache/ directory
        (same convention as DEFAULT_SWEPH_DOWNLOAD_DIR), not relative to the CWD."""
        from pathlib import Path
        from kerykeion.fetch_geonames import DEFAULT_GEONAMES_CACHE_NAME

        assert DEFAULT_GEONAMES_CACHE_NAME.is_absolute()
        assert DEFAULT_GEONAMES_CACHE_NAME == Path.home() / ".kerykeion" / "cache" / "kerykeion_geonames_cache"


# ---------------------------------------------------------------------------
# 3. TestCacheFiltering
# ---------------------------------------------------------------------------


class TestCacheFiltering:
    """Tests for cache filtering of transient GeoNames errors."""

    def test_filter_fn_is_configured(self, monkeypatch):
        """CachedSession is created with the correct filter_fn."""
        cached_session_mock = Mock()
        monkeypatch.setattr("kerykeion.fetch_geonames.CachedSession", cached_session_mock)

        FetchGeonames("TestCity", "TS")

        assert "filter_fn" in cached_session_mock.call_args.kwargs
        assert cached_session_mock.call_args.kwargs["filter_fn"] is _should_cache_geonames_response

    def test_transient_error_not_cached(self):
        """Transient error responses (e.g. hourly limit exceeded) are rejected by filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": {
                "message": "the hourly limit of 1000 credits has been exceeded",
                "value": 19,
            }
        }

        result = _should_cache_geonames_response(mock_response)
        assert result is False

    def test_all_transient_error_codes_rejected(self):
        """Every transient error code is rejected by the cache filter."""
        for error_code in TRANSIENT_GEONAMES_ERROR_CODES:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": {"message": f"Error code {error_code}", "value": error_code}}
            result = _should_cache_geonames_response(mock_response)
            assert result is False, f"Error code {error_code} should not be cached"

    def test_valid_response_cached(self):
        """Valid geonames responses are accepted for caching."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "totalResultsCount": 1,
            "geonames": [{"name": "Rome", "lat": "41.89", "lng": "12.51", "countryCode": "IT"}],
        }

        result = _should_cache_geonames_response(mock_response)
        assert result is True

    def test_cacheable_error_cached(self):
        """Permanent/cacheable errors (e.g. 'no result found') are accepted for caching."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": {"message": "no result found", "value": 15}}

        result = _should_cache_geonames_response(mock_response)
        assert result is True

    def test_invalid_json_not_cached(self):
        """Responses with invalid JSON are not cached."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        result = _should_cache_geonames_response(mock_response)
        assert result is False

    def test_timezone_response_cached(self):
        """Valid timezone responses are cached."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "timezoneId": "Europe/Rome",
            "gmtOffset": 1,
        }

        result = _should_cache_geonames_response(mock_response)
        assert result is True


# =============================================================================
# PRIVATE ERROR PATHS (from edge_cases)
# =============================================================================


class TestGeonamesEnvConfig:
    """Test FetchGeonames environment configuration."""

    def test_cache_name_from_env(self, monkeypatch):
        monkeypatch.setenv("KERYKEION_GEONAMES_CACHE_NAME", "/tmp/test_cache")
        resolved = FetchGeonames._resolve_cache_name(None)
        assert str(resolved) == "/tmp/test_cache"


class TestGeonamesPrivateErrorPaths:
    """Test FetchGeonames private method error handling."""

    def test_timezone_missing_keys_returns_empty(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"someOtherKey": "value"}
        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=mock_response):
            result = geonames.get_serialized_data()
            assert result == {}

    def test_timezone_malformed_payload_returns_empty(self):
        timezone_response = MagicMock()
        timezone_response.json.return_value = []
        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=timezone_response):
            result = getattr(geonames, "_FetchGeonames__get_timezone")("41.9", "12.5")
            assert result == {}

    def test_country_missing_keys_returns_empty(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"geonames": []}
        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=mock_response):
            result = geonames.get_serialized_data()
            assert result == {}

    def test_country_malformed_payload_returns_empty(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"geonames": None}
        geonames = FetchGeonames("Rome", "IT", username="test_user")
        with patch.object(geonames.session, "send", return_value=mock_response):
            result = geonames.get_serialized_data()
            assert result == {}
