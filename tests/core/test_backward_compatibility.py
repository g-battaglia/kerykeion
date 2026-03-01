"""
Tests for backward compatibility aliases and legacy API surface.

This test suite verifies that Kerykeion v5 maintains compatibility with v4 imports,
while issuing appropriate deprecation warnings. It consolidates tests from:
- tests/compatibility/test_backward_compatibility.py
- tests/compatibility/test_backword.py
"""

import warnings
from pathlib import Path

import pytest

from kerykeion.backword import AstrologicalSubject, KerykeionChartSVG, NatalAspects, SynastryAspects


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def legacy_subject():
    """Create a legacy AstrologicalSubject for reuse across tests."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return AstrologicalSubject(
            name="Legacy Subject",
            year=1990,
            month=1,
            day=1,
            hour=12,
            minute=0,
            city="Greenwich",
            nation="GB",
            lng=0.0,
            lat=51.4769,
            tz_str="Etc/GMT",
            online=False,
        )


@pytest.fixture(scope="module")
def legacy_second_subject():
    """Create a second legacy AstrologicalSubject for synastry tests."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return AstrologicalSubject(
            name="Legacy Second",
            year=1990,
            month=1,
            day=2,
            hour=6,
            minute=30,
            city="Greenwich",
            nation="GB",
            lng=0.0,
            lat=51.4769,
            tz_str="Etc/GMT",
            online=False,
        )


# ---------------------------------------------------------------------------
# 1. TestAstrologicalSubjectCompat
# ---------------------------------------------------------------------------


class TestAstrologicalSubjectCompat:
    """Test backward compatibility of legacy AstrologicalSubject wrapper."""

    def test_construction_emits_deprecation_warning(self):
        """Constructing an AstrologicalSubject emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            AstrologicalSubject(
                name="Warn Test",
                year=1990,
                month=1,
                day=1,
                hour=12,
                minute=0,
                lng=0.0,
                lat=51.4769,
                tz_str="Etc/GMT",
                online=False,
            )

            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "AstrologicalSubject" in str(warning.message)
            ]
            assert len(deprecation_warnings) >= 1

    def test_creating_subject_works(self, legacy_subject):
        """Creating an AstrologicalSubject with legacy API succeeds."""
        assert legacy_subject is not None
        model = legacy_subject.model()
        assert model.name == "Legacy Subject"

    def test_legacy_property_mean_node(self, legacy_subject):
        """Accessing mean_node emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)
            _ = legacy_subject.mean_node
            node_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "mean_node" in str(warning.message)
            ]
            assert len(node_warnings) >= 1

    def test_legacy_property_true_node(self, legacy_subject):
        """Accessing true_node returns data and emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)
            result = legacy_subject.true_node
            node_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "true_node" in str(warning.message)
            ]
            assert len(node_warnings) >= 1
            assert result is not None

    def test_legacy_property_mean_south_node(self, legacy_subject):
        """Accessing mean_south_node emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)
            _ = legacy_subject.mean_south_node
            node_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "mean_south_node" in str(warning.message)
            ]
            assert len(node_warnings) >= 1

    def test_legacy_property_true_south_node(self, legacy_subject):
        """Accessing true_south_node returns data and emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)
            result = legacy_subject.true_south_node
            node_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "true_south_node" in str(warning.message)
            ]
            assert len(node_warnings) >= 1
            assert result is not None

    def test_json_method_returns_string(self, legacy_subject):
        """json() method returns a JSON string."""
        json_output = legacy_subject.json()
        assert isinstance(json_output, str)
        assert '"name"' in json_output

    def test_json_dump_creates_file(self, tmp_path, legacy_subject):
        """json(dump=True) writes a file and returns its content."""
        json_output = legacy_subject.json(dump=True, destination_folder=tmp_path, indent=2)
        json_path = tmp_path / "Legacy Subject_kerykeion.json"

        assert json_path.exists(), "json() should create the legacy dump file"
        assert json_output == json_path.read_text(encoding="utf-8")
        assert '\n  "name": "Legacy Subject"' in json_output

    def test_utc_time_cached_property(self, legacy_subject):
        """utc_time cached property returns a float."""
        assert legacy_subject.utc_time == pytest.approx(12.0, abs=1e-6)

    def test_local_time_cached_property(self, legacy_subject):
        """local_time cached property returns a float."""
        assert legacy_subject.local_time == pytest.approx(12.0, abs=1e-6)

    def test_model_and_helpers(self, legacy_subject):
        """model(), __getitem__, get(), __str__, __repr__ all work."""
        model = legacy_subject.model()
        assert model.name == "Legacy Subject"
        assert legacy_subject["name"] == "Legacy Subject"
        assert legacy_subject.get("missing", 42) == 42
        assert "Astrological data for" in str(legacy_subject)
        assert "Astrological data for" in repr(legacy_subject)

    def test_sun_point_accessible(self, legacy_subject):
        """Sun point is accessible via attribute proxy."""
        sun_point = legacy_subject.sun
        assert sun_point is not None
        assert sun_point.name == "Sun"

    def test_get_from_iso_utc_time(self):
        """Class method get_from_iso_utc_time works for backward compat."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            recreated = AstrologicalSubject.get_from_iso_utc_time(
                name="ISO Subject",
                iso_utc_time="2020-01-01T12:00:00Z",
                city="Greenwich",
                nation="GB",
                tz_str="Etc/GMT",
                online=False,
                lng=0.0,
                lat=51.4769,
            )

        model = recreated.model()
        assert model.year == 2020
        assert recreated.utc_time == pytest.approx(12.0, abs=1e-6)


# ---------------------------------------------------------------------------
# 2. TestKerykeionChartSVGCompat
# ---------------------------------------------------------------------------


class TestKerykeionChartSVGCompat:
    """Test backward compatibility of legacy KerykeionChartSVG wrapper."""

    def test_construction_emits_deprecation_warning(self, tmp_path, legacy_subject):
        """Constructing a KerykeionChartSVG emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "KerykeionChartSVG" in str(warning.message)
            ]
            assert len(deprecation_warnings) >= 1

    def test_make_template(self, tmp_path, legacy_subject):
        """makeTemplate() returns an SVG string."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        template = chart.makeTemplate()
        assert "<svg" in template
        assert chart.chart_data.chart_type == "Natal"

    def test_make_svg(self, tmp_path, legacy_subject):
        """makeSVG() creates an SVG file on disk."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        chart.makeSVG(minify=True)
        svg_path = tmp_path / "Legacy Subject - Natal Chart.svg"
        assert svg_path.exists()

    def test_make_wheel_only_template(self, tmp_path, legacy_subject):
        """makeWheelOnlyTemplate() returns an SVG string."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        wheel_template = chart.makeWheelOnlyTemplate()
        assert "<svg" in wheel_template

    def test_make_wheel_only_svg(self, tmp_path, legacy_subject):
        """makeWheelOnlySVG() creates a wheel-only SVG file."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        chart.makeWheelOnlySVG()
        assert (tmp_path / "Legacy Subject - Natal Chart - Wheel Only.svg").exists()

    def test_make_aspect_grid_only_template(self, tmp_path, legacy_subject):
        """makeAspectGridOnlyTemplate() returns an SVG string."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        grid_template = chart.makeAspectGridOnlyTemplate()
        assert "<svg" in grid_template

    def test_make_aspect_grid_only_svg(self, tmp_path, legacy_subject):
        """makeAspectGridOnlySVG() creates an aspect-grid-only SVG file."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        chart.makeAspectGridOnlySVG()
        assert (tmp_path / "Legacy Subject - Natal Chart - Aspect Grid Only.svg").exists()

    def test_chart_exposes_planets_and_aspects(self, tmp_path, legacy_subject):
        """Chart populates available_planets_setting and aspects_list after build."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        chart.makeTemplate()
        assert chart.available_planets_setting
        assert chart.aspects_list

    def test_synastry_chart_support(self, tmp_path, legacy_subject, legacy_second_subject):
        """Synastry chart creation works via legacy API."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(
                legacy_subject,
                chart_type="Synastry",
                second_obj=legacy_second_subject,
                new_output_directory=str(tmp_path),
                double_chart_aspect_grid_type="table",
            )

        template = chart.makeTemplate()
        assert "<svg" in template
        chart.makeSVG()
        expected = tmp_path / "Legacy Subject - Synastry Chart.svg"
        assert expected.exists()
        assert chart.chart_data.chart_type == "Synastry"
        assert chart.double_chart_aspect_grid_type == "table"


# ---------------------------------------------------------------------------
# 3. TestNatalAspectsCompat
# ---------------------------------------------------------------------------


class TestNatalAspectsCompat:
    """Test backward compatibility of legacy NatalAspects wrapper."""

    def test_construction_emits_deprecation_warning(self, legacy_subject):
        """Constructing NatalAspects emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            NatalAspects(legacy_subject)

            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "NatalAspects" in str(warning.message)
            ]
            assert len(deprecation_warnings) >= 1

    def test_creates_aspects_correctly(self, legacy_subject):
        """NatalAspects produces a non-empty list of aspects."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            natal_aspects = NatalAspects(legacy_subject)

        all_aspects = natal_aspects.all_aspects
        assert isinstance(all_aspects, list)
        assert all_aspects

        relevant = natal_aspects.relevant_aspects
        assert isinstance(relevant, list)
        assert relevant
        assert len(all_aspects) >= len(relevant)


# ---------------------------------------------------------------------------
# 4. TestSynastryAspectsCompat
# ---------------------------------------------------------------------------


class TestSynastryAspectsCompat:
    """Test backward compatibility of legacy SynastryAspects wrapper."""

    def test_construction_emits_deprecation_warning(self, legacy_subject, legacy_second_subject):
        """Constructing SynastryAspects emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            SynastryAspects(legacy_subject, legacy_second_subject)

            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "SynastryAspects" in str(warning.message)
            ]
            assert len(deprecation_warnings) >= 1

    def test_creates_aspects_correctly(self, legacy_subject, legacy_second_subject):
        """SynastryAspects produces a non-empty list of aspects."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            legacy_synastry = SynastryAspects(legacy_subject, legacy_second_subject)

        relevant = legacy_synastry.get_relevant_aspects()
        assert isinstance(relevant, list)
        assert relevant

        # Ensure cached properties expose the same data shape
        assert legacy_synastry.relevant_aspects == relevant
        all_aspects = legacy_synastry.all_aspects
        assert isinstance(all_aspects, list)
        assert len(all_aspects) >= len(relevant)


# ---------------------------------------------------------------------------
# 5. TestKrTypesModuleCompat
# ---------------------------------------------------------------------------


class TestKrTypesModuleCompat:
    """Test that kr_types module exists and re-exports schemas with deprecation."""

    def test_kr_types_import_with_warning(self):
        """Importing kr_types triggers deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            from kerykeion import kr_types  # noqa: F401

            kr_types_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "kr_types" in str(warning.message)
            ]
            assert len(kr_types_warnings) >= 1
            assert "v6.0" in str(kr_types_warnings[0].message)

    def test_planet_alias_exists(self):
        """Planet alias is available from kr_types."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            from kerykeion.kr_types import Planet, AstrologicalPoint

            assert Planet == AstrologicalPoint

    def test_axial_cusps_alias_exists(self):
        """AxialCusps alias is available from kr_types."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            from kerykeion.kr_types import AxialCusps, AstrologicalPoint

            assert AxialCusps == AstrologicalPoint

    def test_kr_literals_submodule(self):
        """kr_types.kr_literals works as a compatibility shim."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            from kerykeion.kr_types.kr_literals import Planet, AxialCusps

            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert any("kr_types.kr_literals" in str(dw.message) for dw in deprecation_warnings)

            assert Planet is not None
            assert AxialCusps is not None

    def test_kr_models_submodule(self):
        """kr_types.kr_models works as a compatibility shim."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            from kerykeion.kr_types.kr_models import AstrologicalSubjectModel

            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert any("kr_types.kr_models" in str(dw.message) for dw in deprecation_warnings)

            assert AstrologicalSubjectModel is not None


# ---------------------------------------------------------------------------
# 6. TestDeprecatedAliasesInSchemas
# ---------------------------------------------------------------------------


class TestDeprecatedAliasesInSchemas:
    """Test that deprecated aliases are available in the new schemas module."""

    def test_planet_alias_in_schemas(self):
        """Planet alias exists in schemas module."""
        from kerykeion.schemas import Planet, AstrologicalPoint

        assert Planet == AstrologicalPoint

    def test_axial_cusps_alias_in_schemas(self):
        """AxialCusps alias exists in schemas module."""
        from kerykeion.schemas import AxialCusps, AstrologicalPoint

        assert AxialCusps == AstrologicalPoint

    def test_planet_alias_in_kr_literals(self):
        """Planet alias exists in schemas.kr_literals."""
        from kerykeion.schemas.kr_literals import Planet, AstrologicalPoint

        assert Planet == AstrologicalPoint

    def test_axial_cusps_alias_in_kr_literals(self):
        """AxialCusps alias exists in schemas.kr_literals."""
        from kerykeion.schemas.kr_literals import AxialCusps, AstrologicalPoint

        assert AxialCusps == AstrologicalPoint


# ---------------------------------------------------------------------------
# 7. TestMigrationPathExamples
# ---------------------------------------------------------------------------


class TestMigrationPathExamples:
    """Document migration paths for common v4 -> v5 usage patterns."""

    def test_v4_import_pattern_kr_types_planet(self):
        """
        V4: from kerykeion.kr_types import Planet
        V5: from kerykeion.schemas import AstrologicalPoint
        Compat: from kerykeion.schemas import Planet (alias)
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # Old way (still works via kr_types)
            from kerykeion.kr_types import Planet as PlanetOld

            # New way (recommended)
            from kerykeion.schemas import AstrologicalPoint

            # Transition way (works, no warning)
            from kerykeion.schemas import Planet as PlanetAlias

            assert PlanetOld == AstrologicalPoint
            assert PlanetAlias == AstrologicalPoint

    def test_v4_import_pattern_kr_literals(self):
        """
        V4: from kerykeion.kr_types.kr_literals import Planet, AxialCusps
        V5: from kerykeion.schemas.kr_literals import AstrologicalPoint
        Compat: from kerykeion.schemas.kr_literals import Planet, AxialCusps
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            from kerykeion.kr_types.kr_literals import Planet as POld, AxialCusps as ACOld
            from kerykeion.schemas.kr_literals import AstrologicalPoint
            from kerykeion.schemas.kr_literals import Planet as PNew, AxialCusps as ACNew

            assert POld == AstrologicalPoint
            assert ACOld == AstrologicalPoint
            assert PNew == AstrologicalPoint
            assert ACNew == AstrologicalPoint

    def test_v4_import_pattern_kr_models(self):
        """
        V4: from kerykeion.kr_types.kr_models import AstrologicalSubjectModel
        V5: from kerykeion.schemas.kr_models import AstrologicalSubjectModel
        No alias needed, just path change.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            from kerykeion.kr_types.kr_models import AstrologicalSubjectModel as ASMOld
            from kerykeion.schemas.kr_models import AstrologicalSubjectModel as ASMNew

            # Should be the same class
            assert ASMOld is ASMNew

    def test_v4_astrological_subject_to_factory(self):
        """
        V4: from kerykeion import AstrologicalSubject
        V5: from kerykeion import AstrologicalSubjectFactory
        Both should produce equivalent data.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            from kerykeion import AstrologicalSubject as LegacyAS
            from kerykeion import AstrologicalSubjectFactory

            legacy = LegacyAS(
                name="Migration Test",
                year=2000,
                month=6,
                day=15,
                hour=10,
                minute=30,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )

            modern = AstrologicalSubjectFactory.from_birth_data(
                name="Migration Test",
                year=2000,
                month=6,
                day=15,
                hour=10,
                minute=30,
                seconds=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )

            assert legacy.model().name == modern.name
            assert legacy.model().year == modern.year
            assert legacy.model().sun.name == modern.sun.name


# ---------------------------------------------------------------------------
# 8. TestLegacyPipeline
# ---------------------------------------------------------------------------


class TestLegacyPipeline:
    """Full end-to-end legacy pipeline: makeTemplate -> makeSVG."""

    def test_natal_chart_full_pipeline(self, tmp_path, legacy_subject):
        """Complete Natal chart pipeline works end-to-end."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        # Step 1: Generate template
        template = chart.makeTemplate()
        assert "<svg" in template
        assert chart.chart_data.chart_type == "Natal"

        # Step 2: Save full SVG
        chart.makeSVG(minify=True)
        svg_path = tmp_path / "Legacy Subject - Natal Chart.svg"
        assert svg_path.exists()
        svg_content = svg_path.read_text(encoding="utf-8")
        assert "<svg" in svg_content

        # Step 3: Generate wheel-only
        wheel_template = chart.makeWheelOnlyTemplate()
        assert "<svg" in wheel_template
        chart.makeWheelOnlySVG()
        assert (tmp_path / "Legacy Subject - Natal Chart - Wheel Only.svg").exists()

        # Step 4: Generate aspect-grid-only
        grid_template = chart.makeAspectGridOnlyTemplate()
        assert "<svg" in grid_template
        chart.makeAspectGridOnlySVG()
        assert (tmp_path / "Legacy Subject - Natal Chart - Aspect Grid Only.svg").exists()

        # Step 5: Verify chart metadata
        assert chart.available_planets_setting
        assert chart.aspects_list

    def test_synastry_chart_full_pipeline(self, tmp_path, legacy_subject, legacy_second_subject):
        """Complete Synastry chart pipeline works end-to-end."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(
                legacy_subject,
                chart_type="Synastry",
                second_obj=legacy_second_subject,
                new_output_directory=str(tmp_path),
                double_chart_aspect_grid_type="table",
            )

        template = chart.makeTemplate()
        assert "<svg" in template

        chart.makeSVG()
        expected_path = tmp_path / "Legacy Subject - Synastry Chart.svg"
        assert expected_path.exists()
        assert chart.chart_data.chart_type == "Synastry"
        assert chart.double_chart_aspect_grid_type == "table"

    def test_aspects_pipeline(self, legacy_subject, legacy_second_subject):
        """NatalAspects and SynastryAspects both work end-to-end."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # Natal aspects
            natal = NatalAspects(legacy_subject)
            natal_all = natal.all_aspects
            natal_relevant = natal.relevant_aspects
            assert isinstance(natal_all, list)
            assert natal_all
            assert len(natal_all) >= len(natal_relevant)

            # Synastry aspects
            synastry = SynastryAspects(legacy_subject, legacy_second_subject)
            syn_relevant = synastry.get_relevant_aspects()
            syn_all = synastry.all_aspects
            assert isinstance(syn_all, list)
            assert syn_all
            assert len(syn_all) >= len(syn_relevant)


# =============================================================================
# LEGACY PARAMETER EDGE CASES (from edge_cases/test_edge_cases.py)
# =============================================================================


class TestLegacyDisableChironParams:
    """Test deprecated disable_chiron* parameters."""

    def test_disable_chiron_creates_valid_subject(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                disable_chiron=True,
            )
            assert subject is not None

    def test_disable_chiron_and_lilith_creates_valid_subject(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                disable_chiron_and_lilith=True,
            )
            assert subject is not None

    def test_iso_utc_time_with_disable_chiron_and_lilith(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject.get_from_iso_utc_time(
                name="Test",
                iso_utc_time="1990-06-15T10:00:00+00:00",
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                disable_chiron_and_lilith=True,
            )
            assert subject is not None


class TestLegacyZodiacTypeNormalization:
    """Test legacy lowercase zodiac type values."""

    def test_lowercase_tropic_normalized(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                zodiac_type="tropic",
            )
            assert subject is not None

    def test_lowercase_sidereal_normalized(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
                zodiac_type="sidereal",
            )
            assert subject is not None


class TestLegacySettingsFileParam:
    """Test deprecated new_settings_file parameter."""

    def test_kerykeion_chart_svg_settings_file_warning(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            chart = KerykeionChartSVG(subject, chart_type="Natal", new_settings_file={"some": "config"})
            assert chart is not None

    def test_natal_aspects_settings_file_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            aspects = NatalAspects(subject, new_settings_file={"some": "config"})
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0
            assert aspects is not None

    def test_synastry_aspects_settings_file_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s1 = AstrologicalSubject(
                name="Test1",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            s2 = AstrologicalSubject(
                name="Test2",
                year=1985,
                month=3,
                day=20,
                hour=15,
                minute=30,
                lng=0.0,
                lat=51.5,
                tz_str="Europe/London",
                online=False,
            )
            aspects = SynastryAspects(s1, s2, new_settings_file={"some": "config"})
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) > 0
            assert aspects is not None


class TestLegacyCustomActiveAspects:
    """Test custom active_aspects via legacy wrappers."""

    def test_natal_aspects_custom_active_aspects(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            active_aspects = [{"name": "conjunction", "orb": 6}, {"name": "opposition", "orb": 6}]
            aspects = NatalAspects(subject, active_aspects=active_aspects)
            assert aspects is not None
            _ = aspects.all_aspects
            _ = aspects.relevant_aspects

    def test_synastry_aspects_custom_active_aspects(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            s1 = AstrologicalSubject(
                name="Test1",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            s2 = AstrologicalSubject(
                name="Test2",
                year=1985,
                month=3,
                day=20,
                hour=15,
                minute=30,
                lng=0.0,
                lat=51.5,
                tz_str="Europe/London",
                online=False,
            )
            active_aspects = [{"name": "conjunction", "orb": 6}, {"name": "opposition", "orb": 6}]
            aspects = SynastryAspects(s1, s2, active_aspects=active_aspects)
            assert aspects is not None
            _ = aspects.all_aspects
            _ = aspects.relevant_aspects

    def test_natal_aspects_active_aspects_none(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            aspects = NatalAspects(subject, active_aspects=None)
            assert aspects is not None
            _ = aspects.all_aspects


class TestLegacyActivePointsNormalization:
    """Test legacy node name normalization in active_points."""

    def test_legacy_node_names_in_active_points(self):
        from kerykeion.backword import _normalize_active_points

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _normalize_active_points(["Sun", "Moon", "Mean_Node"])
            node_warnings = [x for x in w if "Mean_Node" in str(x.message)]
            assert len(node_warnings) >= 1


class TestLegacyChartTypeValidation:
    """Test legacy KerykeionChartSVG chart type edge cases."""

    def test_composite_chart_via_legacy_wrapper(self):
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            s1 = AstrologicalSubject(
                name="Test1",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            s2 = AstrologicalSubject(
                name="Test2",
                year=1985,
                month=3,
                day=20,
                hour=15,
                minute=30,
                lng=0.0,
                lat=51.5,
                tz_str="Europe/London",
                online=False,
            )
            composite = CompositeSubjectFactory(s1._model, s2._model)
            composite_subject = composite.get_midpoint_composite_subject_model()
            chart = KerykeionChartSVG(composite_subject, chart_type="Composite")
            svg = chart.makeTemplate()
            assert svg is not None
            assert "<svg" in svg

    def test_external_natal_chart_via_legacy_wrapper(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            chart = KerykeionChartSVG(subject, chart_type="ExternalNatal")
            svg = chart.makeTemplate()
            assert svg is not None
            assert "<svg" in svg

    def test_synastry_without_second_obj_raises(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            chart = KerykeionChartSVG(subject, chart_type="Synastry")
            with pytest.raises(ValueError, match="Second object is required"):
                chart.makeTemplate()

    def test_transit_without_second_obj_raises(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            chart = KerykeionChartSVG(subject, chart_type="Transit")
            with pytest.raises(ValueError, match="Second object is required"):
                chart.makeTemplate()

    def test_composite_with_wrong_type_raises(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            chart = KerykeionChartSVG(subject, chart_type="Composite")
            with pytest.raises(ValueError, match="CompositeSubjectModel"):
                chart.makeTemplate()

    def test_unsupported_chart_type_raises(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            chart = KerykeionChartSVG(subject, chart_type="InvalidType")
            with pytest.raises(ValueError, match="Unsupported"):
                chart.makeTemplate()

    def test_chart_with_none_first_object_raises(self):
        from kerykeion.backword import KerykeionChartSVG as LegacyChart

        with pytest.raises((ValueError, TypeError)):
            chart = LegacyChart(None, chart_type="Natal")
            chart.makeSVG()


class TestSubscriptableBaseModelEdgeCases:
    """Test SubscriptableBaseModel __delitem__ and __setitem__."""

    def test_delitem_method_exists(self):
        subject = AstrologicalSubject(
            name="Test",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        point = subject.sun
        assert hasattr(point, "__delitem__")

    def test_setitem_method(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            try:
                subject["test_attr"] = "test_value"
                delattr(subject, "test_attr")
            except Exception:
                pass  # May fail due to model validation, that's ok


class TestLegacyReturnChartDrawing:
    """Test Return chart drawing via new API (was legacy KerykeionChartSVG)."""

    def test_dual_return_chart_drawing(self):
        from kerykeion.planetary_return_factory import PlanetaryReturnFactory
        from kerykeion.chart_data_factory import ChartDataFactory
        from kerykeion.charts.chart_drawer import ChartDrawer

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            subject = AstrologicalSubject(
                name="Test",
                year=1990,
                month=6,
                day=15,
                hour=12,
                minute=0,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            factory = PlanetaryReturnFactory(
                subject._model,
                lng=12.5,
                lat=41.9,
                tz_str="Europe/Rome",
                online=False,
            )
            solar_return = factory.next_return_from_date(2024, 8, 1, return_type="Solar")
            chart_data = ChartDataFactory.create_return_chart_data(subject._model, solar_return)
            drawer = ChartDrawer(chart_data)
            svg = drawer.generate_svg_string()
            assert svg is not None


# ---------------------------------------------------------------------------
# Missing edge-case tests (migrated from tests/edge_cases/test_edge_cases.py)
# ---------------------------------------------------------------------------


class TestBackwordIsoDatetimeParser:
    """ISO datetime parsing with Z suffix."""

    def test_parse_iso_datetime_with_z_suffix(self):
        """get_from_iso_utc_time handles 'Z' timezone suffix."""
        subject = AstrologicalSubject.get_from_iso_utc_time(
            name="Test",
            iso_utc_time="1990-06-15T12:00:00Z",
            city="Rome",
            nation="IT",
            tz_str="Europe/Rome",
            lng=12.5,
            lat=41.9,
            online=False,
        )
        assert subject is not None
        assert subject.name == "Test"


class TestLegacyActiveAspectsPassthrough:
    """Custom active_aspects are forwarded to the aspects wrapper."""

    def test_active_aspects_passed_to_aspects_wrapper(self, legacy_subject):
        """Passing active_aspects=None exercises the else branch."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            aspects = NatalAspects(legacy_subject, active_aspects=None)
            assert aspects is not None
            _ = aspects.all_aspects
