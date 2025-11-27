# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
    
    Test suite for context_serializer module
"""

import pytest
from kerykeion import AstrologicalSubjectFactory
from kerykeion.context_serializer import (
    to_context,
    kerykeion_point_to_context,
    lunar_phase_to_context,
    aspect_to_context,
    element_distribution_to_context,
    quality_distribution_to_context,
    astrological_subject_to_context,
    single_chart_data_to_context,
    dual_chart_data_to_context,
)
from kerykeion.chart_data_factory import ChartDataFactory
from typing import get_args
from kerykeion.schemas import AstrologicalPoint


class TestKerykeionPointToContext:
    """Test transformation of KerykeionPointModel to context."""
    
    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
    
    def test_sun_context(self):
        """Test Sun point transformation."""
        context = kerykeion_point_to_context(self.subject.sun)
        
        # Check for required components
        assert "Sun" in context
        assert "Gemini" in context or "Gem" in context
        assert "°" in context
        assert "absolute position" in context
        assert "House" in context or "in" in context  # House placement
        assert "direct motion" in context or "retrograde" in context
        
    def test_retrograde_planet_context(self):
        """Test retrograde planet indication."""
        # Create a chart with Mercury retrograde (Dec 2023)
        subject_rx = AstrologicalSubjectFactory.from_birth_data(
            "Mercury Rx", 2023, 12, 20, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        context = kerykeion_point_to_context(subject_rx.mercury)
        assert "retrograde" in context
    
    def test_house_cusp_context(self):
        """Test house cusp transformation."""
        context = kerykeion_point_to_context(self.subject.first_house)
        assert "First" in context or "House" in context
        assert "°" in context
        
    def test_no_qualitative_language(self):
        """Ensure no qualitative/interpretive language is used."""
        context = kerykeion_point_to_context(self.subject.sun)
        
        # Check for absence of interpretive words
        qualitative_words = [
            'good', 'bad', 'positive', 'negative', 'fortunate', 'unfortunate',
            'beneficial', 'challenging', 'difficult', 'easy', 'strong', 'weak'
        ]
        context_lower = context.lower()
        for word in qualitative_words:
            assert word not in context_lower, f"Found qualitative word: {word}"


class TestLunarPhaseToContext:
    """Test transformation of LunarPhaseModel to context."""
    
    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
    
    def test_lunar_phase_context(self):
        """Test lunar phase transformation."""
        if self.subject.lunar_phase is not None:
            context = lunar_phase_to_context(self.subject.lunar_phase)
            assert "Lunar phase" in context
            assert "°" in context
            assert "separation" in context


class TestAspectToContext:
    """Test transformation of AspectModel to context."""
    
    def setup_class(self):
        # Create a natal chart with aspects
        all_points = list(get_args(AstrologicalPoint))
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US",
            lng=-87.11, lat=37.77, tz_str="America/Chicago",
            online=False,
            suppress_geonames_warning=True,
            active_points=all_points
        )
        # Get chart data with aspects
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)
    
    def test_aspect_context(self):
        """Test aspect transformation."""
        if self.chart_data.aspects:
            aspect = self.chart_data.aspects[0]
            context = aspect_to_context(aspect)
            
            assert "between" in context
            assert "orb" in context
            assert "°" in context
            assert "aspect angle" in context
            # Should have aspect movement
            assert any(word in context for word in ['applying', 'separating', 'static'])
    
    def test_multiple_aspects_unique(self):
        """Test that different aspects produce different contexts."""
        if len(self.chart_data.aspects) >= 2:
            context1 = aspect_to_context(self.chart_data.aspects[0])
            context2 = aspect_to_context(self.chart_data.aspects[1])
            # Contexts should be different
            assert context1 != context2


class TestElementAndQualityDistribution:
    """Test element and quality distribution transformations."""
    
    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)
    
    def test_element_distribution_context(self):
        """Test element distribution transformation."""
        context = element_distribution_to_context(self.chart_data.element_distribution)
        
        assert "Element distribution" in context
        assert "Fire" in context
        assert "Earth" in context
        assert "Air" in context
        assert "Water" in context
        assert "%" in context
    
    def test_quality_distribution_context(self):
        """Test quality distribution transformation."""
        context = quality_distribution_to_context(self.chart_data.quality_distribution)
        
        assert "Quality distribution" in context
        assert "Cardinal" in context
        assert "Fixed" in context
        assert "Mutable" in context
        assert "%" in context
    
    def test_percentages_sum_to_100(self):
        """Verify percentages sum to approximately 100%."""
        dist = self.chart_data.element_distribution
        total = (
            dist.fire_percentage + 
            dist.earth_percentage + 
            dist.air_percentage + 
            dist.water_percentage
        )
        # Allow for rounding errors
        assert 99 <= total <= 101


class TestAstrologicalSubjectToContext:
    """Test transformation of complete astrological subjects."""
    
    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp", 1963, 6, 9, 0, 0,
            lng=-87.11, lat=37.77, tz_str="America/Chicago",
            online=False,
            suppress_geonames_warning=True
        )
    
    def test_complete_subject_context(self):
        """Test complete subject transformation."""
        context = astrological_subject_to_context(self.subject)
        
        # Check for major sections
        assert "Johnny Depp" in context
        assert "Birth data" in context
        assert "Coordinates" in context
        assert "Zodiac system" in context
        assert "House system" in context
        assert "Planetary positions" in context
        assert "Important points" in context
        assert "House cusps" in context
    
    def test_subject_has_planetary_positions(self):
        """Test that planetary positions are included."""
        context = astrological_subject_to_context(self.subject)
        
        # Should have at least some planets
        planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']
        planet_count = sum(1 for planet in planets if planet in context)
        assert planet_count >= 3, "Should include multiple planetary positions"
    
    def test_subject_has_house_cusps(self):
        """Test that house cusps are included."""
        context = astrological_subject_to_context(self.subject)
        
        assert "House cusps" in context or "house" in context.lower()
    
    def test_output_is_multiline(self):
        """Test that output uses multiple lines for readability."""
        context = astrological_subject_to_context(self.subject)
        lines = context.split('\n')
        assert len(lines) > 10, "Context should span multiple lines"


class TestSingleChartDataToContext:
    """Test transformation of SingleChartDataModel."""
    
    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)
    
    def test_natal_chart_context(self):
        """Test natal chart data transformation."""
        context = single_chart_data_to_context(self.chart_data)
        
        assert "Chart Analysis" in context
        assert "Element distribution" in context
        assert "Quality distribution" in context
        assert "Active points" in context
        assert "Active aspects" in context
    
    def test_aspects_included(self):
        """Test that aspects are included in output."""
        context = single_chart_data_to_context(self.chart_data)
        
        if self.chart_data.aspects:
            assert "Aspects" in context
            assert "total)" in context


class TestDualChartDataToContext:
    """Test transformation of DualChartDataModel."""
    
    def setup_class(self):
        # Create two subjects for synastry
        self.subject1 = AstrologicalSubjectFactory.from_birth_data(
            "Person 1", 1990, 6, 15, 12, 0, "London", "GB",
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        self.subject2 = AstrologicalSubjectFactory.from_birth_data(
            "Person 2", 1985, 3, 20, 15, 30, "London", "GB",
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        self.dual_chart = ChartDataFactory.create_synastry_chart_data(
            first_subject=self.subject1, second_subject=self.subject2
        )
    
    def test_synastry_chart_context(self):
        """Test synastry chart transformation."""
        context = dual_chart_data_to_context(self.dual_chart)
        
        assert "Chart Analysis" in context
        assert "First Subject" in context
        assert "Second Subject" in context
        assert "Person 1" in context
        assert "Person 2" in context
    
    def test_inter_chart_aspects(self):
        """Test that inter-chart aspects are included."""
        context = dual_chart_data_to_context(self.dual_chart)
        
        if self.dual_chart.aspects:
            assert "Inter-chart aspects" in context or "aspects" in context.lower()


class TestToContextDispatcher:
    """Test the main to_context() dispatcher function."""
    
    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)
    
    def test_dispatcher_with_subject(self):
        """Test dispatcher with AstrologicalSubjectModel."""
        context = to_context(self.subject)
        assert "Test Subject" in context
        assert len(context) > 0
    
    def test_dispatcher_with_point(self):
        """Test dispatcher with KerykeionPointModel."""
        context = to_context(self.subject.sun)
        assert "Sun" in context
    
    def test_dispatcher_with_lunar_phase(self):
        """Test dispatcher with LunarPhaseModel."""
        if self.subject.lunar_phase:
            context = to_context(self.subject.lunar_phase)
            assert "Lunar phase" in context
    
    def test_dispatcher_with_chart_data(self):
        """Test dispatcher with chart data model."""
        context = to_context(self.chart_data)
        assert "Chart Analysis" in context
    
    def test_dispatcher_with_aspect(self):
        """Test dispatcher with AspectModel."""
        if self.chart_data.aspects:
            context = to_context(self.chart_data.aspects[0])
            assert "between" in context
    
    def test_dispatcher_raises_on_invalid_type(self):
        """Test that dispatcher raises TypeError for unsupported types."""
        with pytest.raises(TypeError):
            to_context("invalid string")
        
        with pytest.raises(TypeError):
            to_context(123)
        
        with pytest.raises(TypeError):
            to_context({'key': 'value'})


class TestNonQualitativeOutput:
    """Test that all outputs are strictly non-qualitative."""
    
    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)
    
    def test_no_interpretive_language(self):
        """Ensure no interpretive language in any output."""
        # List of interpretive/qualitative words that should NOT appear
        forbidden_words = [
            'good', 'bad', 'positive', 'negative', 'fortunate', 'unfortunate',
            'beneficial', 'challenging', 'difficult', 'easy', 'strong', 'weak',
            'harmonious', 'tense', 'favorable', 'unfavorable', 'lucky', 'unlucky',
            'blessed', 'cursed', 'excellent', 'poor', 'great', 'terrible'
        ]
        
        # Test subject context
        context = astrological_subject_to_context(self.subject)
        context_lower = context.lower()
        
        for word in forbidden_words:
            assert word not in context_lower, f"Found forbidden interpretive word: {word}"
    
    def test_factual_descriptions_only(self):
        """Ensure descriptions are factual."""
        context = to_context(self.subject)
        
        # Should contain factual elements
        assert "°" in context  # Degrees
        assert any(sign in context for sign in ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                                                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
                                                  'Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'])


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_subject_without_lunar_phase(self):
        """Test subject created without lunar phase calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "No Lunar Phase", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            calculate_lunar_phase=False,
            suppress_geonames_warning=True
        )
        context = astrological_subject_to_context(subject)
        # Should not crash and should omit lunar phase section
        assert len(context) > 0
    
    def test_sidereal_zodiac(self):
        """Test with sidereal zodiac system."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Test", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            suppress_geonames_warning=True
        )
        context = astrological_subject_to_context(subject)
        assert "Sidereal" in context
        assert "LAHIRI" in context
    
    def test_different_house_systems(self):
        """Test with different house systems."""
        subject_placidus = AstrologicalSubjectFactory.from_birth_data(
            "Placidus", 1990, 6, 15, 12, 0,
            lng=0.0, lat=51.5074, tz_str="Etc/GMT",
            online=False,
            houses_system_identifier="P",
            suppress_geonames_warning=True
        )
        context = astrological_subject_to_context(subject_placidus)
        assert "Placidus" in context or "House system" in context
