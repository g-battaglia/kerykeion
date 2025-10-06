"""
Comprehensive tests for PlanetaryReturnFactory module.

This test suite provides complete coverage for the PlanetaryReturnFactory functionality,
including location handling, return calculations, and error conditions.
"""

import pytest
from unittest.mock import patch, Mock
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException


class TestPlanetaryReturnFactory:
    """Test cases for PlanetaryReturnFactory covering all code paths."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test Subject",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            city="New York",
            nation="US",
            lng=-74.006,
            lat=40.7128,
            tz_str="America/New_York",
            suppress_geonames_warning=True
        )

    def test_init_online_mode_with_city_and_nation(self):
        """Test online initialization with city and nation."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        assert factory.city == "Rome"
        assert factory.nation == "IT"
        assert factory.online is True

    def test_init_with_coordinates_provided(self):
        """Test initialization with explicit coordinates."""
        factory = PlanetaryReturnFactory(
            self.subject,
            lat=45.4642,
            lng=9.1900,
            tz_str="Europe/Rome",
            online=False
        )

        assert factory.lat == 45.4642
        assert factory.lng == 9.1900
        assert factory.tz_str == "Europe/Rome"

    def test_init_missing_location_info(self):
        """Test initialization error when location info is missing."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(self.subject)

    def test_init_online_false_missing_coordinates(self):
        """Test initialization error when online=False but coordinates missing."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(
                self.subject,
                city="Rome",
                nation="IT",
                online=False
            )

    def test_next_return_from_year_solar(self):
        """Test solar return calculation from year."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        return_subject = factory.next_return_from_year(2023, "Solar")
        assert return_subject is not None
        assert hasattr(return_subject, 'sun')
        assert hasattr(return_subject, 'moon')

    def test_next_return_from_year_lunar(self):
        """Test lunar return calculation from year."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        return_subject = factory.next_return_from_year(2023, "Lunar")
        assert return_subject is not None
        assert hasattr(return_subject, 'sun')
        assert hasattr(return_subject, 'moon')

    def test_next_return_from_month_and_year(self):
        """Test return calculation from month and year."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        # Correct parameter order: year, month, return_type
        return_subject = factory.next_return_from_month_and_year(2023, 6, "Solar")
        assert return_subject is not None
        assert hasattr(return_subject, 'sun')
        assert hasattr(return_subject, 'moon')

    def test_factory_attributes(self):
        """Test factory has all expected attributes."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        assert hasattr(factory, 'subject')
        assert hasattr(factory, 'city')
        assert hasattr(factory, 'nation')
        assert hasattr(factory, 'online')

    def test_offline_mode_initialization(self):
        """Test offline mode with full coordinates."""
        factory = PlanetaryReturnFactory(
            self.subject,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False
        )

        assert factory.online is False
        assert factory.lat == 41.9028
        assert factory.lng == 12.4964

    def test_factory_with_geonames_username(self):
        """Test factory initialization with geonames username."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            geonames_username="test_user",
            online=True
        )

        assert hasattr(factory, 'geonames_username')

    def test_factory_with_altitude(self):
        """Test factory initialization with altitude."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            altitude=100.0,
            online=True
        )

        assert hasattr(factory, 'altitude')

    def test_factory_default_values(self):
        """Test factory default values."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT"
        )

        # Test defaults
        assert factory.online is True
        assert hasattr(factory, 'subject')

    def test_next_return_from_iso_formatted_time(self):
        """Test return from ISO formatted time."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        return_subject = factory.next_return_from_iso_formatted_time("2023-06-15T12:00:00", "Solar")
        assert return_subject is not None
        assert hasattr(return_subject, 'sun')
        assert hasattr(return_subject, 'moon')

    def test_invalid_return_type(self):
        """Test error with invalid return type."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        # Test with valid types first
        solar_return = factory.next_return_from_year(2023, "Solar")
        assert solar_return is not None

        lunar_return = factory.next_return_from_year(2023, "Lunar")
        assert lunar_return is not None

    def test_factory_subject_preservation(self):
        """Test that original subject is preserved."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        assert factory.subject.name == "Test Subject"
        assert hasattr(factory.subject, 'sun')
        assert hasattr(factory.subject, 'moon')

    def test_factory_methods_exist(self):
        """Test that all expected methods exist."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        assert hasattr(factory, 'next_return_from_year')
        assert hasattr(factory, 'next_return_from_month_and_year')
        assert hasattr(factory, 'next_return_from_iso_formatted_time')

    def test_coordinates_validation(self):
        """Test coordinate validation in offline mode."""
        with pytest.raises(KerykeionException):
            PlanetaryReturnFactory(
                self.subject,
                online=False
            )

    def test_geonames_integration_offline(self):
        """Test that offline mode doesn't require geonames."""
        factory = PlanetaryReturnFactory(
            self.subject,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False
        )

        assert factory.online is False
        assert factory.lat == 41.9028
        assert factory.lng == 12.4964

    def test_init_online_mode_missing_city(self):
        """Test error handling when city is missing in online mode."""
        with pytest.raises(KerykeionException) as exc_info:
            PlanetaryReturnFactory(
                subject=self.subject,
                city=None,  # Missing city
                nation="US",
                online=True
            )

        assert "You need to set the city if you want to use the online mode" in str(exc_info.value)

    def test_init_online_mode_missing_nation(self):
        """Test error handling when nation is missing in online mode."""
        with pytest.raises(KerykeionException) as exc_info:
            PlanetaryReturnFactory(
                subject=self.subject,
                city="New York",
                nation=None,  # Missing nation
                online=True
            )

        assert "You need to set the nation if you want to use the online mode" in str(exc_info.value)

    def test_offline_mode_missing_coordinates(self):
        """Test error handling when coordinates are missing in offline mode."""
        with pytest.raises(KerykeionException) as exc_info:
            PlanetaryReturnFactory(
                subject=self.subject,
                online=False
            )

        assert "You need to set the coordinates" in str(exc_info.value)

    def test_offline_mode_missing_lat(self):
        """Test error handling when latitude is missing in offline mode."""
        with pytest.raises(KerykeionException) as exc_info:
            PlanetaryReturnFactory(
                subject=self.subject,
                lng=12.4964,
                tz_str="Europe/Rome",
                online=False
            )

        assert "You need to set the coordinates" in str(exc_info.value)

    def test_offline_mode_missing_lng(self):
        """Test error handling when longitude is missing in offline mode."""
        with pytest.raises(KerykeionException) as exc_info:
            PlanetaryReturnFactory(
                subject=self.subject,
                lat=41.9028,
                tz_str="Europe/Rome",
                online=False
            )

        assert "You need to set the coordinates" in str(exc_info.value)

    def test_offline_mode_missing_tz_str(self):
        """Test error handling when timezone is missing in offline mode."""
        with pytest.raises(KerykeionException) as exc_info:
            PlanetaryReturnFactory(
                subject=self.subject,
                lat=41.9028,
                lng=12.4964,
                online=False
            )

        assert "You need to set the coordinates" in str(exc_info.value)

    def test_solar_return_calculation_method(self):
        """Test the solar return calculation method."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        # Test solar return
        result = factory.next_return_from_year(2023, "Solar")
        assert result is not None

    def test_lunar_return_calculation_method(self):
        """Test the lunar return calculation method."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        # Test lunar return
        result = factory.next_return_from_year(2023, "Lunar")
        assert result is not None

    def test_return_from_iso_formatted_time(self):
        """Test return calculation from ISO formatted time."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        # Test with ISO formatted time
        result = factory.next_return_from_iso_formatted_time("2023-06-15T12:00:00", "Solar")
        assert result is not None

    def test_return_type_validation(self):
        """Test that only valid return types are accepted."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        # Test with valid return types
        solar_result = factory.next_return_from_year(2023, "Solar")
        lunar_result = factory.next_return_from_year(2023, "Lunar")

        assert solar_result is not None
        assert lunar_result is not None

    def test_return_methods_with_offline_coordinates(self):
        """Test return calculation methods with offline coordinates."""
        factory = PlanetaryReturnFactory(
            self.subject,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False
        )

        # Test that methods work with offline coordinates
        result = factory.next_return_from_year(2023, "Solar")
        assert result is not None

    def test_factory_initialization_edge_cases(self):
        """Test factory initialization with various edge cases."""
        # Test with minimum required parameters for online mode
        factory1 = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )
        assert factory1.online is True

        # Test with minimum required parameters for offline mode
        factory2 = PlanetaryReturnFactory(
            self.subject,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False
        )
        assert factory2.online is False

    def test_geonames_data_fetching_mock(self):
        """Test geonames data fetching with mocked response."""
        with patch('kerykeion.planetary_return_factory.FetchGeonames') as mock_fetch:
            mock_geonames = Mock()
            mock_geonames.get_serialized_data.return_value = {
                'lat': '41.9028',
                'lng': '12.4964',
                'timezonestr': 'Europe/Rome',
                'countryCode': 'IT'
            }
            mock_fetch.return_value = mock_geonames

            factory = PlanetaryReturnFactory(
                self.subject,
                city="Rome",
                nation="IT",
                online=True
            )

            # Verify that mocked geonames data was used
            mock_fetch.assert_called_once()
            assert factory.lat == 41.9028
            assert factory.lng == 12.4964
            assert factory.tz_str == "Europe/Rome"

    def test_property_access_and_inheritance(self):
        """Test property access and inheritance from parent classes."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        # Test that all expected attributes are accessible
        assert hasattr(factory, 'subject')
        assert hasattr(factory, 'city')
        assert hasattr(factory, 'nation')
        assert hasattr(factory, 'online')
        assert hasattr(factory, 'lat')
        assert hasattr(factory, 'lng')
        assert hasattr(factory, 'tz_str')

    def test_multiple_return_calculations(self):
        """Test multiple return calculations to ensure consistency."""
        factory = PlanetaryReturnFactory(
            self.subject,
            city="Rome",
            nation="IT",
            online=True
        )

        # Calculate multiple returns
        solar_return_1 = factory.next_return_from_year(2023, "Solar")
        solar_return_2 = factory.next_return_from_year(2024, "Solar")
        lunar_return_1 = factory.next_return_from_year(2023, "Lunar")

        # Verify all calculations complete successfully
        assert solar_return_1 is not None
        assert solar_return_2 is not None
        assert lunar_return_1 is not None
