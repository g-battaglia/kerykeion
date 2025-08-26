import pytest
from unittest.mock import patch, Mock

from kerykeion.fetch_geonames import FetchGeonames


class TestFetchGeonamesMissingCoverage:
    """Test suite for uncovered fetch geonames functionality."""

    def test_simple_basic_functionality(self):
        """Test basic functionality."""
        fetcher = FetchGeonames("TestCity", "TS")
        assert fetcher.city_name == "TestCity"
        assert fetcher.country_code == "TS"

    def test_exception_handling(self):
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
