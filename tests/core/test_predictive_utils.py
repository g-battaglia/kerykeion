# -*- coding: utf-8 -*-
"""
Comprehensive tests for kerykeion/_predictive_utils.py.

Covers:
  - gather_active_points(): nominal, None active_points, type errors, deduplication,
    missing points, empty result, single-string error, non-string entry error.
  - build_aspect_settings(): nominal, aspect_filter, no filter, string error, invalid orb.
"""

import math
import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion._predictive_utils import gather_active_points, build_aspect_settings
from kerykeion.schemas import KerykeionException
from kerykeion.settings.chart_defaults import DEFAULT_CHART_ASPECTS_SETTINGS, DEFAULT_PREDICTIVE_POINTS


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def subject():
    """John Lennon – canonical test subject with declination data available."""
    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


# =============================================================================
# TESTS: gather_active_points
# =============================================================================


class TestGatherActivePoints:
    """Tests for gather_active_points()."""

    def test_nominal_returns_name_pos_tuples(self, subject):
        """Should return list of (name, abs_pos) tuples for requested points."""
        result = gather_active_points(subject, ["Sun", "Moon"])
        assert isinstance(result, list)
        assert len(result) == 2
        names = [r[0] for r in result]
        assert "Sun" in names
        assert "Moon" in names
        for name, pos in result:
            assert isinstance(name, str)
            assert isinstance(pos, float)
            assert 0.0 <= pos < 360.0

    def test_none_active_points_uses_defaults(self, subject):
        """None active_points should use DEFAULT_PREDICTIVE_POINTS."""
        result = gather_active_points(subject, None)
        assert isinstance(result, list)
        assert len(result) > 0
        # Every name in result must come from subject attributes
        for name, pos in result:
            attr = name.lower()
            point = getattr(subject, attr, None)
            assert point is not None, f"Point {name!r} missing from subject"

    def test_single_string_raises_exception(self, subject):
        """Passing a bare string instead of a sequence should raise KerykeionException."""
        with pytest.raises(KerykeionException, match="sequence of point names"):
            gather_active_points(subject, "Sun")  # type: ignore[arg-type]

    def test_bytes_raises_exception(self, subject):
        """Passing bytes instead of a sequence should raise KerykeionException."""
        with pytest.raises(KerykeionException, match="sequence of point names"):
            gather_active_points(subject, b"Sun")  # type: ignore[arg-type]

    def test_non_string_entry_raises_exception(self, subject):
        """Non-string elements in active_points should raise KerykeionException."""
        with pytest.raises(KerykeionException, match="strings"):
            gather_active_points(subject, [42])  # type: ignore[list-item]

    def test_duplicate_points_deduplicated(self, subject):
        """Duplicate point names in active_points should appear only once in result."""
        result = gather_active_points(subject, ["Sun", "Sun", "Moon"])
        names = [r[0] for r in result]
        assert names.count("Sun") == 1
        assert names.count("Moon") == 1
        assert len(result) == 2

    def test_missing_point_skipped(self, subject):
        """Points missing from subject (non-existent names) should be silently skipped."""
        result = gather_active_points(subject, ["Sun", "NonexistentPoint123"])
        names = [r[0] for r in result]
        assert "Sun" in names
        assert "NonexistentPoint123" not in names

    def test_empty_active_points_list_returns_empty(self, subject):
        """Empty list of active_points should return empty list."""
        result = gather_active_points(subject, [])
        assert result == []

    def test_abs_pos_values_are_valid(self, subject):
        """abs_pos values should be in [0.0, 360.0)."""
        result = gather_active_points(subject, ["Sun", "Moon", "Mars"])
        for _name, pos in result:
            assert 0.0 <= pos < 360.0, f"abs_pos {pos} out of range for point in result"

    def test_order_preserved(self, subject):
        """Order of points in result should match order of active_points."""
        points = ["Moon", "Sun", "Mars"]
        result = gather_active_points(subject, points)
        returned_names = [r[0] for r in result]
        # Filter points to only those that exist in result
        expected_order = [p for p in points if p in returned_names]
        assert returned_names == expected_order


# =============================================================================
# TESTS: build_aspect_settings
# =============================================================================


class TestBuildAspectSettings:
    """Tests for build_aspect_settings()."""

    def test_nominal_all_aspects_no_filter(self):
        """No aspect_filter returns all DEFAULT_CHART_ASPECTS_SETTINGS with orb override."""
        orb = 5.0
        result = build_aspect_settings(orb, None)
        # Should have as many entries as default aspects
        assert len(result) == len(DEFAULT_CHART_ASPECTS_SETTINGS)
        for entry in result:
            assert entry["orb"] == orb
            assert "degree" in entry
            assert "name" in entry

    def test_aspect_filter_narrows_results(self):
        """Providing an aspect_filter list returns only matching aspects."""
        orb = 3.0
        result = build_aspect_settings(orb, ["conjunction", "opposition"])
        names = [e["name"] for e in result]
        assert "conjunction" in names
        assert "opposition" in names
        # Other aspects should not be included
        for name in names:
            assert name in ("conjunction", "opposition")

    def test_uniform_orb_override_applied(self):
        """All entries should have the specified orb value, not the default."""
        custom_orb = 7.5
        result = build_aspect_settings(custom_orb, None)
        for entry in result:
            assert entry["orb"] == pytest.approx(custom_orb)

    def test_fractional_orb_accepted(self):
        """Fractional orb values should be accepted without error."""
        result = build_aspect_settings(2.5, None)
        for entry in result:
            assert entry["orb"] == pytest.approx(2.5)

    def test_zero_orb_accepted(self):
        """Zero orb is valid (exact aspects only)."""
        result = build_aspect_settings(0.0, None)
        for entry in result:
            assert entry["orb"] == 0.0

    def test_string_aspect_filter_raises_exception(self):
        """Passing a bare string for aspect_filter should raise KerykeionException."""
        with pytest.raises(KerykeionException, match="sequence of aspect names"):
            build_aspect_settings(5.0, "conjunction")  # type: ignore[arg-type]

    def test_bytes_aspect_filter_raises_exception(self):
        """Passing bytes for aspect_filter should raise KerykeionException."""
        with pytest.raises(KerykeionException, match="sequence of aspect names"):
            build_aspect_settings(5.0, b"conjunction")  # type: ignore[arg-type]

    def test_negative_orb_raises_exception(self):
        """Negative orb should raise KerykeionException."""
        with pytest.raises(KerykeionException, match="finite non-negative"):
            build_aspect_settings(-1.0, None)

    def test_inf_orb_raises_exception(self):
        """Infinite orb should raise KerykeionException."""
        with pytest.raises(KerykeionException, match="finite non-negative"):
            build_aspect_settings(math.inf, None)

    def test_nan_orb_raises_exception(self):
        """NaN orb should raise KerykeionException."""
        with pytest.raises(KerykeionException, match="finite non-negative"):
            build_aspect_settings(math.nan, None)

    def test_unknown_aspect_filter_returns_empty(self):
        """Filtering by a non-existent aspect name should return empty list."""
        result = build_aspect_settings(5.0, ["nonexistent_aspect_xyz"])
        assert result == []

    def test_empty_aspect_filter_returns_empty(self):
        """Empty aspect_filter list should return empty list."""
        result = build_aspect_settings(5.0, [])
        assert result == []

    def test_result_entries_have_required_keys(self):
        """Each result entry must have 'degree', 'name', and 'orb' keys."""
        result = build_aspect_settings(4.0, None)
        for entry in result:
            assert "degree" in entry
            assert "name" in entry
            assert "orb" in entry

    def test_degree_values_preserved(self):
        """Degree values from DEFAULT_CHART_ASPECTS_SETTINGS should be preserved."""
        result = build_aspect_settings(5.0, None)
        default_degrees = {a["degree"] for a in DEFAULT_CHART_ASPECTS_SETTINGS}
        result_degrees = {e["degree"] for e in result}
        assert result_degrees == default_degrees
