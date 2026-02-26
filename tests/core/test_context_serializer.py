# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia

Test suite for context_serializer module (XML output)
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
    moon_phase_overview_to_context,
)
from kerykeion.chart_data_factory import ChartDataFactory
from typing import get_args
from kerykeion.schemas import AstrologicalPoint


class TestKerykeionPointToContext:
    """Test transformation of KerykeionPointModel to XML context."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )

    def test_sun_context(self):
        """Test Sun point transformation produces XML."""
        context = kerykeion_point_to_context(self.subject.sun)

        # Must be a self-closing <point /> tag
        assert context.startswith("<point ")
        assert context.endswith("/>")
        assert 'name="Sun"' in context
        assert "sign=" in context
        assert "position=" in context
        assert "abs_pos=" in context
        assert "quality=" in context
        assert "element=" in context
        assert "house=" in context
        assert 'motion="direct"' in context or 'motion="retrograde"' in context

    def test_retrograde_planet_context(self):
        """Test retrograde planet indication in XML."""
        # Create a chart with Mercury retrograde (Dec 2023)
        subject_rx = AstrologicalSubjectFactory.from_birth_data(
            "Mercury Rx",
            2023,
            12,
            20,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        context = kerykeion_point_to_context(subject_rx.mercury)
        assert 'motion="retrograde"' in context

    def test_house_cusp_context(self):
        """Test house cusp transformation produces XML."""
        context = kerykeion_point_to_context(self.subject.first_house)
        assert "<point " in context
        assert "/>" in context
        assert "name=" in context

    def test_no_qualitative_language(self):
        """Ensure no qualitative/interpretive language is used."""
        context = kerykeion_point_to_context(self.subject.sun)

        # Check for absence of interpretive words
        qualitative_words = [
            "good",
            "bad",
            "positive",
            "negative",
            "fortunate",
            "unfortunate",
            "beneficial",
            "challenging",
            "difficult",
            "easy",
            "strong",
            "weak",
        ]
        context_lower = context.lower()
        for word in qualitative_words:
            assert word not in context_lower, f"Found qualitative word: {word}"

    def test_sign_full_name_used(self):
        """Test that full sign names are used instead of abbreviations."""
        context = kerykeion_point_to_context(self.subject.sun)
        full_signs = [
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ]
        assert any(f'sign="{sign}"' in context for sign in full_signs)

    def test_speed_attribute_present(self):
        """Test that speed attribute is present for planets."""
        context = kerykeion_point_to_context(self.subject.sun)
        assert "speed=" in context

    def test_declination_attribute_present(self):
        """Test that declination attribute is present for planets."""
        context = kerykeion_point_to_context(self.subject.sun)
        assert "declination=" in context


class TestLunarPhaseToContext:
    """Test transformation of LunarPhaseModel to XML context."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )

    def test_lunar_phase_context(self):
        """Test lunar phase transformation produces XML."""
        if self.subject.lunar_phase is not None:
            context = lunar_phase_to_context(self.subject.lunar_phase)
            assert context.startswith("<lunar_phase ")
            assert context.endswith("/>")
            assert "name=" in context
            assert "phase=" in context
            assert "degrees_between=" in context
            assert "emoji=" in context


class TestAspectToContext:
    """Test transformation of AspectModel to XML context."""

    def setup_class(self):
        # Create a natal chart with aspects
        all_points = list(get_args(AstrologicalPoint))
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp",
            1963,
            6,
            9,
            0,
            0,
            "Owensboro",
            "US",
            lng=-87.11,
            lat=37.77,
            tz_str="America/Chicago",
            online=False,
            suppress_geonames_warning=True,
            active_points=all_points,
        )
        # Get chart data with aspects
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

    def test_aspect_context_natal(self):
        """Test natal aspect transformation produces XML."""
        if self.chart_data.aspects:
            aspect = self.chart_data.aspects[0]
            context = aspect_to_context(aspect)

            assert context.startswith("<aspect ")
            assert context.endswith("/>")
            assert "type=" in context
            assert "p1=" in context
            assert "p2=" in context
            assert "orb=" in context
            assert "angle=" in context
            # Natal aspects should have movement attribute
            assert "movement=" in context

    def test_aspect_context_synastry(self):
        """Test synastry aspect transformation produces XML with ownership."""
        if self.chart_data.aspects:
            aspect = self.chart_data.aspects[0]
            context = aspect_to_context(aspect, is_synastry=True)

            assert context.startswith("<aspect ")
            assert "p1_name=" in context
            assert "p1_owner=" in context
            assert "p2_name=" in context
            assert "p2_owner=" in context
            # Synastry aspects should NOT have movement attribute
            assert "movement=" not in context

    def test_aspect_context_transit(self):
        """Test transit aspect has Transit as second owner."""
        if self.chart_data.aspects:
            aspect = self.chart_data.aspects[0]
            context = aspect_to_context(aspect, is_synastry=True, is_transit=True)

            assert 'p2_owner="Transit"' in context

    def test_multiple_aspects_unique(self):
        """Test that different aspects produce different contexts."""
        if len(self.chart_data.aspects) >= 2:
            context1 = aspect_to_context(self.chart_data.aspects[0])
            context2 = aspect_to_context(self.chart_data.aspects[1])
            # Contexts should be different
            assert context1 != context2


class TestElementAndQualityDistribution:
    """Test element and quality distribution transformations to XML."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

    def test_element_distribution_context(self):
        """Test element distribution transformation produces XML."""
        context = element_distribution_to_context(self.chart_data.element_distribution)

        assert context.startswith("<element_distribution ")
        assert context.endswith("/>")
        assert "fire=" in context
        assert "earth=" in context
        assert "air=" in context
        assert "water=" in context
        assert "%" in context

    def test_quality_distribution_context(self):
        """Test quality distribution transformation produces XML."""
        context = quality_distribution_to_context(self.chart_data.quality_distribution)

        assert context.startswith("<quality_distribution ")
        assert context.endswith("/>")
        assert "cardinal=" in context
        assert "fixed=" in context
        assert "mutable=" in context
        assert "%" in context

    def test_percentages_sum_to_100(self):
        """Verify percentages sum to approximately 100%."""
        dist = self.chart_data.element_distribution
        total = dist.fire_percentage + dist.earth_percentage + dist.air_percentage + dist.water_percentage
        # Allow for rounding errors
        assert 99 <= total <= 101


class TestAstrologicalSubjectToContext:
    """Test transformation of complete astrological subjects to XML."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Johnny Depp",
            1963,
            6,
            9,
            0,
            0,
            lng=-87.11,
            lat=37.77,
            tz_str="America/Chicago",
            online=False,
            suppress_geonames_warning=True,
        )

    def test_complete_subject_context(self):
        """Test complete subject transformation produces XML structure."""
        context = astrological_subject_to_context(self.subject)

        # Check for major XML structure
        assert '<chart name="Johnny Depp">' in context
        assert "<birth_data " in context
        assert "<config " in context
        assert "<planets>" in context
        assert "</planets>" in context
        assert "<axes>" in context
        assert "</axes>" in context
        assert "<houses>" in context
        assert "</houses>" in context
        assert "</chart>" in context

    def test_subject_has_planetary_positions(self):
        """Test that planetary positions are included as XML point tags."""
        context = astrological_subject_to_context(self.subject)

        # Should have point tags for planets
        assert 'name="Sun"' in context
        assert 'name="Moon"' in context
        assert 'name="Mercury"' in context
        assert 'name="Venus"' in context
        assert 'name="Mars"' in context

    def test_subject_has_house_cusps(self):
        """Test that house cusps are included as XML house tags."""
        context = astrological_subject_to_context(self.subject)

        assert "<house " in context
        assert "cusp=" in context

    def test_output_is_multiline_xml(self):
        """Test that output uses multiple lines with XML structure."""
        context = astrological_subject_to_context(self.subject)
        lines = context.split("\n")
        assert len(lines) > 10, "Context should span multiple lines"

    def test_birth_data_attributes(self):
        """Test that birth_data tag has correct attributes."""
        context = astrological_subject_to_context(self.subject)
        assert "city=" in context
        assert "nation=" in context
        assert "lat=" in context
        assert "lng=" in context
        assert "tz=" in context

    def test_config_attributes(self):
        """Test that config tag has correct attributes."""
        context = astrological_subject_to_context(self.subject)
        assert "zodiac=" in context
        assert "house_system=" in context
        assert "perspective=" in context


class TestSingleChartDataToContext:
    """Test transformation of SingleChartDataModel to XML."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

    def test_natal_chart_context(self):
        """Test natal chart data transformation produces XML."""
        context = single_chart_data_to_context(self.chart_data)

        assert '<chart_analysis type="Natal">' in context
        assert "</chart_analysis>" in context
        assert "<element_distribution " in context
        assert "<quality_distribution " in context
        assert "<active_points>" in context
        assert "<active_aspects>" in context

    def test_aspects_included(self):
        """Test that aspects are included in XML output."""
        context = single_chart_data_to_context(self.chart_data)

        if self.chart_data.aspects:
            assert "<aspects count=" in context
            assert "</aspects>" in context
            assert "<aspect " in context


class TestDualChartDataToContext:
    """Test transformation of DualChartDataModel to XML."""

    def setup_class(self):
        # Create two subjects for synastry
        self.subject1 = AstrologicalSubjectFactory.from_birth_data(
            "Person 1",
            1990,
            6,
            15,
            12,
            0,
            "London",
            "GB",
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        self.subject2 = AstrologicalSubjectFactory.from_birth_data(
            "Person 2",
            1985,
            3,
            20,
            15,
            30,
            "London",
            "GB",
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        self.dual_chart = ChartDataFactory.create_synastry_chart_data(
            first_subject=self.subject1, second_subject=self.subject2
        )

    def test_synastry_chart_context(self):
        """Test synastry chart transformation produces XML."""
        context = dual_chart_data_to_context(self.dual_chart)

        assert '<chart_analysis type="Synastry">' in context
        assert "</chart_analysis>" in context
        assert "<first_subject>" in context
        assert "</first_subject>" in context
        assert "<second_subject>" in context
        assert "</second_subject>" in context
        assert 'name="Person 1"' in context
        assert 'name="Person 2"' in context

    def test_inter_chart_aspects(self):
        """Test that inter-chart aspects are included in XML."""
        context = dual_chart_data_to_context(self.dual_chart)

        if self.dual_chart.aspects:
            assert "<aspects count=" in context
            assert "<aspect " in context

    def test_transit_chart_uses_transit_subject_tag(self):
        """Test that transit charts use <transit_subject> wrapper tag and <transit_data>."""
        transit_data = ChartDataFactory.create_transit_chart_data(
            natal_subject=self.subject1, transit_subject=self.subject2
        )
        context = dual_chart_data_to_context(transit_data)

        assert "<transit_subject>" in context
        assert "</transit_subject>" in context
        # Transit subject should use <transit_data> instead of <birth_data>
        assert "<transit_data " in context

    def test_synastry_relationship_score(self):
        """Test that synastry chart with relationship score produces <relationship_score> tag."""
        dual_chart_with_score = ChartDataFactory.create_synastry_chart_data(
            first_subject=self.subject1,
            second_subject=self.subject2,
            include_relationship_score=True,
        )
        context = dual_chart_data_to_context(dual_chart_with_score)

        if dual_chart_with_score.relationship_score is not None:
            assert "<relationship_score " in context
            assert 'max="44"' in context
            assert "value=" in context


class TestToContextDispatcher:
    """Test the main to_context() dispatcher function."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

    def test_dispatcher_with_subject(self):
        """Test dispatcher with AstrologicalSubjectModel."""
        context = to_context(self.subject)
        assert 'name="Test Subject"' in context
        assert "<chart " in context

    def test_dispatcher_with_point(self):
        """Test dispatcher with KerykeionPointModel."""
        context = to_context(self.subject.sun)
        assert "<point " in context
        assert 'name="Sun"' in context

    def test_dispatcher_with_lunar_phase(self):
        """Test dispatcher with LunarPhaseModel."""
        if self.subject.lunar_phase:
            context = to_context(self.subject.lunar_phase)
            assert "<lunar_phase " in context

    def test_dispatcher_with_chart_data(self):
        """Test dispatcher with chart data model."""
        context = to_context(self.chart_data)
        assert "<chart_analysis " in context

    def test_dispatcher_with_aspect(self):
        """Test dispatcher with AspectModel."""
        if self.chart_data.aspects:
            context = to_context(self.chart_data.aspects[0])
            assert "<aspect " in context

    def test_dispatcher_raises_on_invalid_type(self):
        """Test that dispatcher raises TypeError for unsupported types."""
        with pytest.raises(TypeError):
            to_context("invalid string")

        with pytest.raises(TypeError):
            to_context(123)

        with pytest.raises(TypeError):
            to_context({"key": "value"})

    def test_dispatcher_with_element_distribution(self):
        """Test dispatcher with ElementDistributionModel."""
        context = to_context(self.chart_data.element_distribution)
        assert "<element_distribution " in context

    def test_dispatcher_with_quality_distribution(self):
        """Test dispatcher with QualityDistributionModel."""
        context = to_context(self.chart_data.quality_distribution)
        assert "<quality_distribution " in context

    def test_dispatcher_with_moon_phase_overview(self):
        """Test dispatcher with MoonPhaseOverviewModel."""
        from kerykeion.schemas.kr_models import MoonPhaseOverviewModel, MoonPhaseMoonSummaryModel

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.827,
                phase_name="Waning Crescent",
                illumination="32%",
            ),
        )
        context = to_context(overview)
        assert "<moon_phase_overview " in context
        assert "</moon_phase_overview>" in context
        assert 'timestamp="750081120"' in context


class TestNonQualitativeOutput:
    """Test that all outputs are strictly non-qualitative."""

    def setup_class(self):
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            "Test Subject",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

    FORBIDDEN_WORDS = [
        "good",
        "bad",
        "positive",
        "negative",
        "fortunate",
        "unfortunate",
        "beneficial",
        "challenging",
        "difficult",
        "easy",
        "strong",
        "weak",
        "harmonious",
        "tense",
        "favorable",
        "unfavorable",
        "lucky",
        "unlucky",
        "blessed",
        "cursed",
        "excellent",
        "poor",
        "great",
        "terrible",
    ]

    def _assert_no_forbidden_words(self, context: str, label: str):
        """Helper to check no interpretive language in a context string."""
        context_lower = context.lower()
        for word in self.FORBIDDEN_WORDS:
            assert word not in context_lower, f"Found forbidden interpretive word '{word}' in {label}"

    def test_no_interpretive_language_subject(self):
        """Ensure no interpretive language in astrological subject output."""
        context = astrological_subject_to_context(self.subject)
        self._assert_no_forbidden_words(context, "astrological_subject_to_context")

    def test_no_interpretive_language_single_chart(self):
        """Ensure no interpretive language in single (natal) chart output."""
        context = single_chart_data_to_context(self.chart_data)
        self._assert_no_forbidden_words(context, "single_chart_data_to_context")

    def test_no_interpretive_language_dual_chart(self):
        """Ensure no interpretive language in dual (synastry) chart output."""
        subject2 = AstrologicalSubjectFactory.from_birth_data(
            "Partner",
            1985,
            3,
            20,
            15,
            30,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            suppress_geonames_warning=True,
        )
        dual_chart = ChartDataFactory.create_synastry_chart_data(first_subject=self.subject, second_subject=subject2)
        context = dual_chart_data_to_context(dual_chart)
        self._assert_no_forbidden_words(context, "dual_chart_data_to_context")

    def test_no_interpretive_language_moon_phase_overview(self):
        """Ensure no interpretive language in moon phase overview output."""
        from kerykeion.schemas.kr_models import MoonPhaseOverviewModel, MoonPhaseMoonSummaryModel

        overview = MoonPhaseOverviewModel(
            moon=MoonPhaseMoonSummaryModel(
                phase_name="Waxing Crescent",
                illumination="15%",
                emoji="🌒",
                age_days=3,
            ),
            timestamp=1705320000,
            datestamp="2024-01-15",
        )
        context = moon_phase_overview_to_context(overview)
        self._assert_no_forbidden_words(context, "moon_phase_overview_to_context")

    def test_factual_descriptions_only(self):
        """Ensure descriptions contain factual XML elements."""
        context = to_context(self.subject)

        # Should be XML with proper tags
        assert "<chart " in context
        assert "<point " in context
        # Should contain sign names in attributes
        assert any(
            f'sign="{sign}"' in context
            for sign in [
                "Aries",
                "Taurus",
                "Gemini",
                "Cancer",
                "Leo",
                "Virgo",
                "Libra",
                "Scorpio",
                "Sagittarius",
                "Capricorn",
                "Aquarius",
                "Pisces",
            ]
        )


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_subject_without_lunar_phase(self):
        """Test subject created without lunar phase calculation."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "No Lunar Phase",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            calculate_lunar_phase=False,
            suppress_geonames_warning=True,
        )
        context = astrological_subject_to_context(subject)
        # Should not crash and should omit lunar phase tag
        assert len(context) > 0
        assert "<lunar_phase " not in context

    def test_sidereal_zodiac(self):
        """Test with sidereal zodiac system."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Test",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            suppress_geonames_warning=True,
        )
        context = astrological_subject_to_context(subject)
        assert 'zodiac="Sidereal"' in context
        assert 'sidereal_mode="LAHIRI"' in context

    def test_different_house_systems(self):
        """Test with different house systems."""
        subject_placidus = AstrologicalSubjectFactory.from_birth_data(
            "Placidus",
            1990,
            6,
            15,
            12,
            0,
            lng=0.0,
            lat=51.5074,
            tz_str="Etc/GMT",
            online=False,
            houses_system_identifier="P",
            suppress_geonames_warning=True,
        )
        context = astrological_subject_to_context(subject_placidus)
        assert 'house_system="Placidus"' in context or "<config " in context


class TestMoonPhaseOverviewToContext:
    """Test transformation of MoonPhaseOverviewModel to XML context."""

    def test_minimal_overview(self):
        """Test a minimal MoonPhaseOverviewModel (only required fields)."""
        from kerykeion.schemas.kr_models import MoonPhaseOverviewModel, MoonPhaseMoonSummaryModel

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<moon_phase_overview " in context
        assert "</moon_phase_overview>" in context
        assert 'timestamp="750081120"' in context
        assert "<moon>" in context
        assert "</moon>" in context

    def test_overview_with_moon_details(self):
        """Test MoonPhaseOverviewModel with moon summary fields."""
        from kerykeion.schemas.kr_models import MoonPhaseOverviewModel, MoonPhaseMoonSummaryModel

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.827,
                phase_name="Waning Crescent",
                major_phase="Last Quarter",
                stage="waning",
                illumination="32%",
                age_days=22,
                emoji="🌘",
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<phase>0.827</phase>" in context
        assert "<phase_name>Waning Crescent</phase_name>" in context
        assert "<major_phase>Last Quarter</major_phase>" in context
        assert "<stage>waning</stage>" in context
        assert "<illumination>32%</illumination>" in context
        assert "<age_days>22</age_days>" in context

    def test_overview_with_sun_info(self):
        """Test MoonPhaseOverviewModel with sun info."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseSunInfoModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(phase=0.5),
            sun=MoonPhaseSunInfoModel(
                sunrise=1696921080,
                sunrise_timestamp="06:58",
                sunset=1696960680,
                sunset_timestamp="17:58",
                day_length="11h 00m",
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<sun>" in context
        assert "</sun>" in context
        assert "<sunrise>" in context
        assert "<day_length>11h 00m</day_length>" in context

    def test_overview_with_location(self):
        """Test MoonPhaseOverviewModel with location info."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseLocationModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(phase=0.5),
            location=MoonPhaseLocationModel(
                latitude="51.4769",
                longitude="0.0",
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<location " in context
        assert 'latitude="51.4769"' in context
        assert 'longitude="0.0"' in context

    def test_overview_with_upcoming_phases(self):
        """Test MoonPhaseOverviewModel with upcoming phases."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseMoonDetailedModel,
            MoonPhaseUpcomingPhasesModel,
            MoonPhaseMajorPhaseWindowModel,
            MoonPhaseEventMomentModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                detailed=MoonPhaseMoonDetailedModel(
                    upcoming_phases=MoonPhaseUpcomingPhasesModel(
                        new_moon=MoonPhaseMajorPhaseWindowModel(
                            last=MoonPhaseEventMomentModel(days_ago=10, datestamp="2023-10-01"),
                            next=MoonPhaseEventMomentModel(days_ahead=5, datestamp="2023-10-15"),
                        ),
                    ),
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<upcoming_phases>" in context
        assert "</upcoming_phases>" in context
        assert "<new_moon>" in context
        assert "<last " in context
        assert 'days_ago="10"' in context
        assert "<next " in context
        assert 'days_ahead="5"' in context

    def test_overview_with_zodiac(self):
        """Test MoonPhaseOverviewModel with zodiac info."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseZodiacModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                zodiac=MoonPhaseZodiacModel(sun_sign="Lib", moon_sign="Can"),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<zodiac " in context
        assert 'sun_sign="Lib"' in context
        assert 'moon_sign="Can"' in context

    def test_overview_with_moonrise_moonset(self):
        """Test MoonPhaseOverviewModel with moonrise/moonset fields."""
        from kerykeion.schemas.kr_models import MoonPhaseOverviewModel, MoonPhaseMoonSummaryModel

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                moonrise="18:30",
                moonrise_timestamp=1696961400,
                moonset="06:15",
                moonset_timestamp=1696917300,
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<moonrise>18:30</moonrise>" in context
        assert "<moonrise_timestamp>1696961400</moonrise_timestamp>" in context
        assert "<moonset>06:15</moonset>" in context
        assert "<moonset_timestamp>1696917300</moonset_timestamp>" in context

    def test_overview_with_next_lunar_eclipse(self):
        """Test MoonPhaseOverviewModel with next lunar eclipse."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseEclipseModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                next_lunar_eclipse=MoonPhaseEclipseModel(
                    timestamp=1700000000,
                    datestamp="2023-11-14",
                    type="Total",
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<next_lunar_eclipse " in context
        assert 'type="Total"' in context
        assert 'timestamp="1700000000"' in context

    def test_overview_with_detailed_position(self):
        """Test MoonPhaseOverviewModel with detailed moon position."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseMoonDetailedModel,
            MoonPhaseMoonPositionModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                detailed=MoonPhaseMoonDetailedModel(
                    position=MoonPhaseMoonPositionModel(
                        altitude=35.50,
                        azimuth=180.25,
                        distance=384400.00,
                        parallactic_angle=12.30,
                        phase_angle=90.00,
                    ),
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<detailed>" in context
        assert "</detailed>" in context
        assert "<position " in context
        assert 'altitude="35.50"' in context
        assert 'azimuth="180.25"' in context
        assert 'distance="384400.00"' in context
        assert 'parallactic_angle="12.30"' in context
        assert 'phase_angle="90.00"' in context

    def test_overview_with_visibility_and_viewing_conditions(self):
        """Test MoonPhaseOverviewModel with visibility and viewing conditions."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseMoonDetailedModel,
            MoonPhaseVisibilityModel,
            MoonPhaseViewingConditionsModel,
            MoonPhaseViewingEquipmentModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                detailed=MoonPhaseMoonDetailedModel(
                    visibility=MoonPhaseVisibilityModel(
                        visible_hours=8.5,
                        best_viewing_time="21:00",
                        illumination="50%",
                        viewing_conditions=MoonPhaseViewingConditionsModel(
                            phase_quality="Excellent",
                            recommended_equipment=MoonPhaseViewingEquipmentModel(
                                telescope="Refractor",
                                filters="Moon filter",
                                best_magnification="100x",
                            ),
                        ),
                    ),
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<visibility " in context
        assert 'visible_hours="8.5"' in context
        assert 'best_viewing_time="21:00"' in context
        assert "<viewing_conditions " in context
        assert 'phase_quality="Excellent"' in context
        assert "<recommended_equipment " in context
        assert 'telescope="Refractor"' in context
        assert 'filters="Moon filter"' in context

    def test_overview_with_visibility_without_viewing_conditions(self):
        """Test MoonPhaseOverviewModel with visibility but no viewing conditions."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseMoonDetailedModel,
            MoonPhaseVisibilityModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                detailed=MoonPhaseMoonDetailedModel(
                    visibility=MoonPhaseVisibilityModel(
                        visible_hours=8.5,
                        illumination="50%",
                    ),
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        # Without viewing_conditions, visibility should be self-closing
        assert "<visibility " in context
        assert 'visible_hours="8.5"' in context
        assert "<viewing_conditions" not in context

    def test_overview_with_illumination_details(self):
        """Test MoonPhaseOverviewModel with illumination details."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseMoonDetailedModel,
            MoonPhaseIlluminationDetailsModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                detailed=MoonPhaseMoonDetailedModel(
                    illumination_details=MoonPhaseIlluminationDetailsModel(
                        percentage=49.8,
                        visible_fraction=0.4980,
                        phase_angle=90.12,
                    ),
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<illumination_details " in context
        assert 'percentage="49.8"' in context
        assert 'visible_fraction="0.4980"' in context
        assert 'phase_angle="90.12"' in context

    def test_overview_with_events_and_optimal_viewing(self):
        """Test MoonPhaseOverviewModel with events and optimal viewing period."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseEventsModel,
            MoonPhaseOptimalViewingPeriodModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                events=MoonPhaseEventsModel(
                    moonrise_visible=True,
                    moonset_visible=False,
                    optimal_viewing_period=MoonPhaseOptimalViewingPeriodModel(
                        start_time="20:00",
                        end_time="02:00",
                        duration_hours=6.0,
                        recommendations=["Use binoculars", "Find dark sky"],
                    ),
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<events " in context
        assert 'moonrise_visible="true"' in context
        assert 'moonset_visible="false"' in context
        assert "<optimal_viewing_period " in context
        assert 'start_time="20:00"' in context
        assert 'duration_hours="6.0"' in context
        assert "<recommendation>Use binoculars</recommendation>" in context
        assert "<recommendation>Find dark sky</recommendation>" in context

    def test_overview_with_events_without_optimal_viewing(self):
        """Test MoonPhaseOverviewModel with events but no optimal viewing period."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseEventsModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase=0.5,
                events=MoonPhaseEventsModel(
                    moonrise_visible=True,
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        # Without optimal_viewing_period, events should be self-closing
        assert "<events " in context
        assert 'moonrise_visible="true"' in context
        assert "<optimal_viewing_period" not in context

    def test_overview_with_sun_position_and_eclipse(self):
        """Test MoonPhaseOverviewModel with sun position and solar eclipse."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseSunInfoModel,
            MoonPhaseSunPositionModel,
            MoonPhaseSolarEclipseModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(phase=0.5),
            sun=MoonPhaseSunInfoModel(
                solar_noon="12:30",
                position=MoonPhaseSunPositionModel(
                    altitude=45.00,
                    azimuth=180.00,
                    distance=149597870.70,
                ),
                next_solar_eclipse=MoonPhaseSolarEclipseModel(
                    timestamp=1700000000,
                    datestamp="2023-11-14",
                    type="Annular",
                    visibility_regions="South America",
                ),
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<solar_noon>12:30</solar_noon>" in context
        assert "<position " in context
        assert 'altitude="45.00"' in context
        assert "<next_solar_eclipse " in context
        assert 'type="Annular"' in context
        assert 'visibility_regions="South America"' in context

    def test_overview_with_extended_location(self):
        """Test MoonPhaseOverviewModel with all location attributes."""
        from kerykeion.schemas.kr_models import (
            MoonPhaseOverviewModel,
            MoonPhaseMoonSummaryModel,
            MoonPhaseLocationModel,
        )

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(phase=0.5),
            location=MoonPhaseLocationModel(
                latitude="51.4769",
                longitude="0.0",
                precision=4,
                using_default_location=False,
                note="Observatory location",
            ),
        )
        context = moon_phase_overview_to_context(overview)
        assert "<location " in context
        assert 'precision="4"' in context
        assert 'using_default_location="false"' in context
        assert 'note="Observatory location"' in context

    def test_none_fields_omitted(self):
        """Test that None/optional fields are omitted from XML output."""
        from kerykeion.schemas.kr_models import MoonPhaseOverviewModel, MoonPhaseMoonSummaryModel

        overview = MoonPhaseOverviewModel(
            timestamp=750081120,
            datestamp="Thu, 10 Oct 1993 12:12:00 +0000",
            moon=MoonPhaseMoonSummaryModel(),
        )
        context = moon_phase_overview_to_context(overview)
        # With no fields set, moon section should have no child elements
        assert "<sun>" not in context
        assert "<location " not in context
        assert "<phase>" not in context
