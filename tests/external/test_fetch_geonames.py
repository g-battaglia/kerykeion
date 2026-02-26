import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException
import json


from kerykeion.fetch_geonames import (
    FetchGeonames,
    _should_cache_geonames_response,
    TRANSIENT_GEONAMES_ERROR_CODES,
)

# Serialize all tests in this module to avoid GeoNames API rate limiting
pytestmark = pytest.mark.xdist_group(name="geonames")


def test_geonames():
    geonames = FetchGeonames("Roma", "IT")
    data = geonames.get_serialized_data()
    expected_data = {
        "timezonestr": "Europe/Rome",
        "name": "Rome",
        "lat": "41.89193",
        "lng": "12.51133",
        "countryCode": "IT",
        # Cache is not tested
        "from_tz_cache": True,
        "from_country_cache": True,
    }

    assert data["timezonestr"] == expected_data["timezonestr"]
    assert data["name"] == expected_data["name"]
    assert data["lat"] == expected_data["lat"]
    assert data["lng"] == expected_data["lng"]
    assert data["countryCode"] == expected_data["countryCode"]


def test_basic_functionality():
    """Test basic functionality."""
    fetcher = FetchGeonames("TestCity", "TS")
    assert fetcher.city_name == "TestCity"
    assert fetcher.country_code == "TS"


def test_exception_handling():
    """Test exception handling paths."""
    with patch("kerykeion.fetch_geonames.CachedSession") as mock_session:
        # Mock session to raise an exception
        mock_session_instance = Mock()
        mock_session_instance.send.side_effect = RequestException("Network error")
        mock_session.return_value = mock_session_instance

        fetcher = FetchGeonames("TestCity", "TS", username="test_user")

        # Test through public interface
        result = fetcher.get_serialized_data()
        # Should return empty dict on error
        assert result == {}


def test_custom_cache_name(monkeypatch):
    session_mock = Mock()
    cached_session_mock = Mock(return_value=session_mock)
    monkeypatch.setattr("kerykeion.fetch_geonames.CachedSession", cached_session_mock)

    FetchGeonames("TestCity", "TS", cache_name="custom/cache/path")

    assert cached_session_mock.call_args.kwargs["cache_name"] == "custom/cache/path"


def test_set_default_cache_name(monkeypatch, tmp_path):
    session_mock = Mock()
    cached_session_mock = Mock(return_value=session_mock)
    monkeypatch.setattr("kerykeion.fetch_geonames.CachedSession", cached_session_mock)

    # Use monkeypatch for class attribute to ensure parallel test safety
    monkeypatch.setattr(FetchGeonames, "default_cache_name", tmp_path / "geo_cache")
    FetchGeonames("TestCity", "TS")
    assert cached_session_mock.call_args.kwargs["cache_name"] == str(tmp_path / "geo_cache")


class TestCacheFiltering:
    """Tests for cache filtering of transient GeoNames errors."""

    def test_filter_fn_is_configured(self, monkeypatch):
        """Test that CachedSession is created with filter_fn."""
        cached_session_mock = Mock()
        monkeypatch.setattr("kerykeion.fetch_geonames.CachedSession", cached_session_mock)

        FetchGeonames("TestCity", "TS")

        assert "filter_fn" in cached_session_mock.call_args.kwargs
        assert cached_session_mock.call_args.kwargs["filter_fn"] is _should_cache_geonames_response

    def test_transient_error_not_cached(self):
        """Test that transient error responses are rejected by filter."""
        # Create a mock response with a transient error (hourly limit exceeded)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": {
                "message": "the hourly limit of 1000 credits has been exceeded",
                "value": 19,  # hourly limit exceeded
            }
        }

        result = _should_cache_geonames_response(mock_response)
        assert result is False

    def test_all_transient_error_codes_rejected(self):
        """Test that all transient error codes are rejected."""
        for error_code in TRANSIENT_GEONAMES_ERROR_CODES:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": {"message": f"Error code {error_code}", "value": error_code}}
            result = _should_cache_geonames_response(mock_response)
            assert result is False, f"Error code {error_code} should not be cached"

    def test_valid_response_is_cached(self):
        """Test that valid responses are accepted for caching."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "totalResultsCount": 1,
            "geonames": [{"name": "Rome", "lat": "41.89", "lng": "12.51", "countryCode": "IT"}],
        }

        result = _should_cache_geonames_response(mock_response)
        assert result is True

    def test_cacheable_error_is_cached(self):
        """Test that permanent/cacheable errors are accepted for caching."""
        # Error code 15 = "no result found" - this is a permanent error for the given input
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": {"message": "no result found", "value": 15}}

        result = _should_cache_geonames_response(mock_response)
        assert result is True

    def test_invalid_json_not_cached(self):
        """Test that responses with invalid JSON are not cached."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        result = _should_cache_geonames_response(mock_response)
        assert result is False

    def test_timezone_response_is_cached(self):
        """Test that valid timezone responses are cached."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "timezoneId": "Europe/Rome",
            "gmtOffset": 1,
        }

        result = _should_cache_geonames_response(mock_response)
        assert result is True
