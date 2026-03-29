# -*- coding: utf-8 -*-
"""Tests for the Gauquelin sectors feature."""

import pytest
swe = pytest.importorskip("swisseph")
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer


@pytest.fixture(scope="module")
def subject_with_gauquelin():
    return AstrologicalSubjectFactory.from_birth_data(
        "Gauquelin Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        calculate_gauquelin=True,
    )


@pytest.fixture(scope="module")
def subject_without_gauquelin():
    return AstrologicalSubjectFactory.from_birth_data(
        "No Gauquelin", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


class TestGauquelinCalculation:
    def test_sectors_populated(self, subject_with_gauquelin):
        """Classical planets should have gauquelin_sector when enabled."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_gauquelin, name)
            if point is not None:
                assert point.gauquelin_sector is not None, f"{name} should have gauquelin_sector"
                assert 1.0 <= point.gauquelin_sector < 37.0, (
                    f"{name} sector {point.gauquelin_sector} should be in [1, 37)"
                )

    def test_sectors_not_populated_by_default(self, subject_without_gauquelin):
        """Gauquelin sectors should be None when not enabled."""
        assert subject_without_gauquelin.sun.gauquelin_sector is None
        assert subject_without_gauquelin.moon.gauquelin_sector is None

    def test_all_sectors_different(self, subject_with_gauquelin):
        """Not all planets should have the same sector (probabilistically)."""
        sectors = []
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_gauquelin, name)
            if point is not None and point.gauquelin_sector is not None:
                sectors.append(int(point.gauquelin_sector))
        # With 7 planets in 36 sectors, very unlikely all same
        assert len(set(sectors)) > 1

    def test_sector_integer_part_in_range(self, subject_with_gauquelin):
        """Integer part of sector should be 1-36."""
        sun_sector = int(subject_with_gauquelin.sun.gauquelin_sector)
        assert 1 <= sun_sector <= 36

    def test_sun_sector_matches_swe_reference(self, subject_with_gauquelin):
        """Sun Gauquelin sector must match a direct swe.gauquelin_sector call within 0.01."""
        jd = subject_with_gauquelin.julian_day
        geopos = [
            subject_with_gauquelin.lng,
            subject_with_gauquelin.lat,
            0.0,
        ]
        swe.set_ephe_path("")
        # Sun = swe planet ID 0, method 0 (with latitude)
        expected_sector = swe.gauquelin_sector(jd, 0, 0, geopos)
        assert abs(subject_with_gauquelin.sun.gauquelin_sector - expected_sector) < 0.01, (
            f"Sun sector {subject_with_gauquelin.sun.gauquelin_sector} != "
            f"swe reference {expected_sector}"
        )

    def test_multiple_planets_match_swe_reference(self, subject_with_gauquelin):
        """Moon and Mars Gauquelin sectors must match direct swe calls within 0.01."""
        jd = subject_with_gauquelin.julian_day
        geopos = [
            subject_with_gauquelin.lng,
            subject_with_gauquelin.lat,
            0.0,
        ]
        swe.set_ephe_path("")
        planet_ids = {"moon": 1, "mars": 4}
        for attr, pid in planet_ids.items():
            point = getattr(subject_with_gauquelin, attr)
            expected = swe.gauquelin_sector(jd, pid, 0, geopos)
            assert abs(point.gauquelin_sector - expected) < 0.01, (
                f"{attr} sector {point.gauquelin_sector} != swe reference {expected}"
            )


class TestGauquelinSVG:
    def test_svg_with_gauquelin_renders(self, subject_with_gauquelin, tmp_path):
        """SVG should render without errors when Gauquelin sectors are present."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="dark")
        drawer.save_svg(output_path=str(tmp_path), filename="gauquelin_test")
        svg_file = tmp_path / "gauquelin_test.svg"
        assert svg_file.exists()
        svg_content = svg_file.read_text()
        assert len(svg_content) > 1000

    def test_svg_without_gauquelin_still_works(self, subject_without_gauquelin, tmp_path):
        """SVG should render normally without Gauquelin sectors."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_without_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="dark")
        drawer.save_svg(output_path=str(tmp_path), filename="no_gauquelin_test")
        svg_file = tmp_path / "no_gauquelin_test.svg"
        assert svg_file.exists()

    def test_svg_contains_gauquelin_sector_lines(self, subject_with_gauquelin, tmp_path):
        """SVG should contain Gauquelin sector line elements."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="light")
        drawer.save_svg(output_path=str(tmp_path), filename="gauquelin_lines")
        svg_content = (tmp_path / "gauquelin_lines.svg").read_text()
        # Should have sector division lines
        assert svg_content.count("<line") > 12  # More than just house lines

    def test_modern_style_gauquelin_no_house_lines(self, subject_with_gauquelin, tmp_path):
        """Modern style with Gauquelin should NOT draw standard 12-house division lines."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="dark")
        svg_content = drawer.generate_svg_string(style="modern")
        # Should contain the modern horoscope group
        assert "ModernHoroscope" in svg_content
        # Should NOT contain standard house ring content (kr:node="HouseRing")
        # The Gauquelin house ring replaces it without the HouseRing node
        assert 'kr:slug="First_House"' not in svg_content

    def test_modern_style_gauquelin_renders(self, subject_with_gauquelin, tmp_path):
        """Modern style with Gauquelin sectors should render without errors."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="dark")
        svg_content = drawer.generate_svg_string(style="modern")
        assert len(svg_content) > 1000
        # Should have many sector lines (36 sectors × 3 rings = ~108 lines)
        assert svg_content.count("<line") > 36
