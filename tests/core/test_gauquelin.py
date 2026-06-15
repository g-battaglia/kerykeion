# -*- coding: utf-8 -*-
"""Tests for the Gauquelin sectors feature."""

import pytest
from kerykeion.ephemeris_backend import ephe
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
        """Sun Gauquelin sector must match a direct ephe.gauquelin_sector call within 0.01."""
        jd = subject_with_gauquelin.julian_day
        geopos = [
            subject_with_gauquelin.lng,
            subject_with_gauquelin.lat,
            0.0,
        ]
        ephe.set_ephe_path("")
        # Sun = ephe planet ID 0, method 0 (with latitude)
        expected_sector = ephe.gauquelin_sector(jd, 0, 0, geopos)
        assert abs(subject_with_gauquelin.sun.gauquelin_sector - expected_sector) < 0.01, (
            f"Sun sector {subject_with_gauquelin.sun.gauquelin_sector} != "
            f"ephe reference {expected_sector}"
        )

    def test_multiple_planets_match_swe_reference(self, subject_with_gauquelin):
        """Moon and Mars Gauquelin sectors must match direct ephe calls within 0.01."""
        jd = subject_with_gauquelin.julian_day
        geopos = [
            subject_with_gauquelin.lng,
            subject_with_gauquelin.lat,
            0.0,
        ]
        ephe.set_ephe_path("")
        planet_ids = {"moon": 1, "mars": 4}
        for attr, pid in planet_ids.items():
            point = getattr(subject_with_gauquelin, attr)
            expected = ephe.gauquelin_sector(jd, pid, 0, geopos)
            assert abs(point.gauquelin_sector - expected) < 0.01, (
                f"{attr} sector {point.gauquelin_sector} != ephe reference {expected}"
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

    def test_svg_contains_36_sector_hit_areas(self, subject_with_gauquelin, tmp_path):
        """Gauquelin mode must emit 36 transparent clickable wedges with kr:sector attrs."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="light")
        drawer.save_svg(output_path=str(tmp_path), filename="gauq_hit_areas")
        svg = (tmp_path / "gauq_hit_areas.svg").read_text()

        # 36 hit-area groups total (double/single quote tolerant for scour)
        double = svg.count('kr:node="GauquelinSector"')
        single = svg.count("kr:node='GauquelinSector'")
        assert double + single == 36, f"expected 36 hit areas, got {double + single}"

        # All 36 sector numbers present as kr:sector attributes
        for n in range(1, 37):
            assert f'kr:sector="{n}"' in svg or f"kr:sector='{n}'" in svg, (
                f"sector {n} missing from SVG"
            )

        # Wedges are transparent and interactive
        assert "fill: transparent" in svg or "fill:transparent" in svg
        assert "pointer-events: all" in svg or "pointer-events:all" in svg

    def test_svg_without_gauquelin_has_no_sector_hit_areas(self, subject_without_gauquelin, tmp_path):
        """Non-Gauquelin charts must not emit GauquelinSector hit-areas."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_without_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="light")
        drawer.save_svg(output_path=str(tmp_path), filename="no_gauq_hit_areas")
        svg = (tmp_path / "no_gauq_hit_areas.svg").read_text()

        assert "GauquelinSector" not in svg


class TestGauquelinBackendCallShape:
    """v6 regression: pyswisseph's gauquelin_sector signature is
    (tjdut, body, starname, method, geopos, ...) while libephemeris's is
    (tjdut, body, method, geopos, ...). The libephemeris-style 4-arg call on
    pyswisseph put the method int in the starname slot, raising TypeError and
    silently forcing the geometric fallback for every planet. The swisseph
    branch is exercised here with a fake (pyswisseph is not installed in the
    libephemeris test environment)."""

    _BIRTH = dict(
        year=1990, month=6, day=15, hour=14, minute=30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        calculate_gauquelin=True, suppress_geonames_warning=True,
    )

    def _run_with_fake_backend(self, monkeypatch, backend_name):
        import kerykeion.astrological_subject_factory as asf

        calls = []

        def fake_gauquelin_sector(*args, **kwargs):
            calls.append((args, kwargs))
            return 7.5

        monkeypatch.setattr(asf, "BACKEND_NAME", backend_name)
        monkeypatch.setattr(asf.ephe, "gauquelin_sector", fake_gauquelin_sector)

        subject = AstrologicalSubjectFactory.from_birth_data("Backend Shape", **self._BIRTH)
        return subject, calls

    @pytest.mark.parametrize("backend_name", ["swisseph", "libephemeris"])
    def test_gauquelin_sector_call_shape_is_backend_uniform(self, monkeypatch, backend_name):
        """Both backends share (tjdut, body, method, geopos, ...): pyswisseph
        >= 2.10.3.1 (the pinned floor) has no starname parameter — the 5-arg
        starname form existed only in pre-2.10 releases, and passing a string
        in the int method slot raises TypeError, silently forcing the
        geometric fallback for every planet."""
        subject, calls = self._run_with_fake_backend(monkeypatch, backend_name)

        assert calls, "gauquelin_sector was never attempted"
        for args, kwargs in calls:
            assert len(args) == 4, (
                f"call must be (tjdut, body, method, geopos), got {args}"
            )
            assert isinstance(args[1], int)  # body id
            assert args[2] == 0  # method
            assert len(args[3]) == 3  # geopos triple

        # The backend sector value must flow through (no geometric fallback)
        assert subject.sun.gauquelin_sector == 7.5
