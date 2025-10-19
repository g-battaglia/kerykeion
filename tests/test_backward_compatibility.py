"""
Tests for backward compatibility aliases (kr_types module and deprecated type aliases).

This test suite verifies that Kerykeion v5 maintains compatibility with v4 imports,
while issuing appropriate deprecation warnings.
"""
import warnings
import pytest


class TestKrTypesModuleCompatibility:
    """Test that kr_types module exists and re-exports schemas."""

    def test_kr_types_import_with_warning(self):
        """Test that importing kr_types triggers deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            # Import should work but trigger warning
            from kerykeion import kr_types  # noqa: F401

            # Filter for kr_types specific deprecation warnings
            kr_types_warnings = [
                warning for warning in w
                if issubclass(warning.category, DeprecationWarning)
                and "kr_types" in str(warning.message)
            ]
            assert len(kr_types_warnings) >= 1
            assert "v6.0" in str(kr_types_warnings[0].message)

    def test_kr_types_planet_alias(self):
        """Test that Planet alias is available from kr_types."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            from kerykeion.kr_types import Planet, AstrologicalPoint

            # Planet should be an alias for AstrologicalPoint
            assert Planet == AstrologicalPoint

    def test_kr_types_axial_cusps_alias(self):
        """Test that AxialCusps alias is available from kr_types."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            from kerykeion.kr_types import AxialCusps, AstrologicalPoint

            # AxialCusps should be an alias for AstrologicalPoint
            assert AxialCusps == AstrologicalPoint

    def test_kr_types_kr_literals_submodule(self):
        """Test that kr_types.kr_literals works as a compatibility shim."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            from kerykeion.kr_types.kr_literals import Planet, AxialCusps

            # Should trigger deprecation warning
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert any("kr_types.kr_literals" in str(dw.message) for dw in deprecation_warnings)

            # But imports should still work
            assert Planet is not None
            assert AxialCusps is not None

    def test_kr_types_kr_models_submodule(self):
        """Test that kr_types.kr_models works as a compatibility shim."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            from kerykeion.kr_types.kr_models import AstrologicalSubjectModel

            # Should trigger deprecation warning
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert any("kr_types.kr_models" in str(dw.message) for dw in deprecation_warnings)

            # But imports should still work
            assert AstrologicalSubjectModel is not None


class TestDeprecatedAliasesInSchemas:
    """Test that deprecated aliases are available in new schemas module."""

    def test_planet_alias_in_schemas(self):
        """Test that Planet alias exists in schemas module."""
        from kerykeion.schemas import Planet, AstrologicalPoint

        # Planet should be an alias for AstrologicalPoint
        assert Planet == AstrologicalPoint

    def test_axial_cusps_alias_in_schemas(self):
        """Test that AxialCusps alias exists in schemas module."""
        from kerykeion.schemas import AxialCusps, AstrologicalPoint

        # AxialCusps should be an alias for AstrologicalPoint
        assert AxialCusps == AstrologicalPoint

    def test_planet_alias_in_kr_literals(self):
        """Test that Planet alias exists in schemas.kr_literals."""
        from kerykeion.schemas.kr_literals import Planet, AstrologicalPoint

        assert Planet == AstrologicalPoint

    def test_axial_cusps_alias_in_kr_literals(self):
        """Test that AxialCusps alias exists in schemas.kr_literals."""
        from kerykeion.schemas.kr_literals import AxialCusps, AstrologicalPoint

        assert AxialCusps == AstrologicalPoint


class TestMigrationPathExamples:
    """Document migration paths for common v4 usage patterns."""

    def test_v4_import_pattern_1(self):
        """
        V4 Pattern: from kerykeion.kr_types import Planet
        V5 Pattern: from kerykeion.schemas import AstrologicalPoint

        Compatibility: from kerykeion.schemas import Planet (with alias)
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

    def test_v4_import_pattern_2(self):
        """
        V4 Pattern: from kerykeion.kr_types.kr_literals import Planet, AxialCusps
        V5 Pattern: from kerykeion.schemas.kr_literals import AstrologicalPoint

        Compatibility: from kerykeion.schemas.kr_literals import Planet, AxialCusps
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # Old way (still works via kr_types, with deprecation)
            from kerykeion.kr_types.kr_literals import Planet as POld, AxialCusps as ACOld

            # New way (recommended)
            from kerykeion.schemas.kr_literals import AstrologicalPoint

            # Transition way (works, no warning)
            from kerykeion.schemas.kr_literals import Planet as PNew, AxialCusps as ACNew

            assert POld == AstrologicalPoint
            assert ACOld == AstrologicalPoint
            assert PNew == AstrologicalPoint
            assert ACNew == AstrologicalPoint

    def test_v4_import_pattern_3(self):
        """
        V4 Pattern: from kerykeion.kr_types.kr_models import AstrologicalSubjectModel
        V5 Pattern: from kerykeion.schemas.kr_models import AstrologicalSubjectModel

        No alias needed here, just path change.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # Old way (still works via kr_types, with deprecation)
            from kerykeion.kr_types.kr_models import AstrologicalSubjectModel as ASMOld

            # New way (recommended, no warning)
            from kerykeion.schemas.kr_models import AstrologicalSubjectModel as ASMNew

            # Should be the same class
            assert ASMOld is ASMNew
