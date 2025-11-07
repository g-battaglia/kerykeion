from unittest.mock import Mock, patch

import pytest

from kerykeion.fetch_geonames import FetchGeonames


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
    with patch('kerykeion.fetch_geonames.CachedSession') as mock_session:
        # Mock session to raise an exception
        mock_session_instance = Mock()
        mock_session_instance.send.side_effect = Exception("Network error")
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

    original_default = FetchGeonames.default_cache_name
    try:
        FetchGeonames.set_default_cache_name(tmp_path / "geo_cache")
        FetchGeonames("TestCity", "TS")
        assert cached_session_mock.call_args.kwargs["cache_name"] == str(tmp_path / "geo_cache")
    finally:
        FetchGeonames.set_default_cache_name(original_default)
