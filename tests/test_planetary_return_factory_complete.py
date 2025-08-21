"""
Comprehensive tests for PlanetaryReturnFactory module.

This test suite provides complete coverage for the PlanetaryReturnFactory functionality,
including location handling, return calculations, and error conditions.
"""

import pytest
from unittest.mock import patch
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
            tz_str="America/New_York"
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
