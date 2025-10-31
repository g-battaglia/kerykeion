import pytest
from unittest.mock import patch, Mock
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
