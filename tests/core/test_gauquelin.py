# -*- coding: utf-8 -*-
"""Tests for the Gauquelin sectors feature."""

import re

import pytest
from kerykeion.ephemeris_backend import ephe
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.charts.charts_utils import (
    _classic_gauquelin_mid_offset,
    draw_gauquelin_sectors,
    wheel_x,
    wheel_y,
)
from kerykeion.charts.draw_modern import (
    _draw_gauquelin_cusp_ring,
    _gauquelin_sector_mid_angle,
)


class TestClassicGauquelinMidOffset:
    """Gauquelin cusps DESCEND in zodiacal longitude (diurnal numbering from
    the ASC): the label midpoint must be taken on the descending a→b arc, or
    every label lands 180° away in the opposite sector (the pre-fix formula
    assumed ascending cusps)."""

    def test_midpoint_is_between_consecutive_offsets(self):
        offsets = [(-i * 10.0) % 360 for i in range(36)]
        # Sector 0 spans 0°..350° descending -> label at 355°, not 175°.
        assert _classic_gauquelin_mid_offset(offsets, 0) == pytest.approx(355.0)
        # Sector 17 spans 190°..180° descending -> label at 185°.
        assert _classic_gauquelin_mid_offset(offsets, 17) == pytest.approx(185.0)

    def test_midpoint_wraps_across_zero(self):
        offsets = [(-i * 10.0) % 360 for i in range(36)]
        # Last sector spans 10°..0° descending; midpoint is 5°.
        assert _classic_gauquelin_mid_offset(offsets, 35) == pytest.approx(5.0)

    def test_midpoint_handles_unequal_spacing(self):
        offsets = [(-i * 10.0) % 360 for i in range(36)]
        offsets[1] = 356.0  # sector 0 now spans 0°..356° descending (4° wide)
        assert _classic_gauquelin_mid_offset(offsets, 0) == pytest.approx(358.0)

    def test_midpoint_lies_inside_sector_for_real_cusps(self, subject_with_gauquelin):
        """With real houses_ex2('G') cusps, every label midpoint must sit on
        the short descending arc between its two boundaries."""
        cusps = subject_with_gauquelin.gauquelin_sector_cusps
        assert cusps is not None and len(cusps) == 36
        seventh = subject_with_gauquelin.seventh_house.abs_pos
        offsets = [(-seventh) + c for c in cusps]
        for i in range(36):
            a = offsets[i] % 360
            b = offsets[(i + 1) % 36] % 360
            mid = _classic_gauquelin_mid_offset(offsets, i)
            span = (a - b) % 360
            pos = (a - mid) % 360
            assert span < 180, f"sector {i}: cusps not descending (span={span})"
            assert 0 < pos < span, (
                f"sector {i}: label at {mid} outside descending arc {a}→{b}"
            )


class TestModernGauquelinGeometry:
    """Rotation-sign and fallback invariants for the modern drawer."""

    _DESC_CUSPS_WHEEL = [(360.0 - i * 10.0) % 360.0 for i in range(36)]

    def test_mid_angle_descending(self):
        assert _gauquelin_sector_mid_angle(self._DESC_CUSPS_WHEEL, 0) == pytest.approx(355.0)
        assert _gauquelin_sector_mid_angle(self._DESC_CUSPS_WHEEL, 35) == pytest.approx(5.0)

    def test_text_transform_rotations_sum_to_90(self):
        """Label transform must be rotate(-mid) then rotate(90 + mid): the sum
        (+90) cancels the global rotate(-90) wheel group so text is upright,
        while the first rotate places it at the (negated) wheel angle."""
        svg = _draw_gauquelin_cusp_ring(0.0, gauquelin_cusps=None)
        pairs = re.findall(
            r'transform="rotate\((-?[\d.]+) [\d.]+ [\d.]+\) '
            r"rotate\((-?[\d.]+) [\d.]+ -?[\d.]+\)\"",
            svg,
        )
        assert len(pairs) == 36
        for first, second in pairs:
            assert float(first) + float(second) == pytest.approx(90.0)
            assert float(first) <= 0  # placement rotation is negated

    def test_division_lines_use_negative_rotation(self):
        """Gauquelin lines must rotate with the same sign convention as houses
        and planets (rotate(-angle)); positive rotation mirrors the overlay."""
        svg = _draw_gauquelin_cusp_ring(0.0, gauquelin_cusps=self._DESC_CUSPS_WHEEL)
        line_rotations = re.findall(r'<line [^>]*transform="rotate\((-?[\d.]+)', svg)
        assert len(line_rotations) == 36
        # Descending wheel-angle cusps i>=1 are all positive -> all rotations negative.
        assert all(float(rot) <= 0 for rot in line_rotations)
        assert "rotate(-350.000000" in svg  # boundary i=1

    def test_asc_boundary_matches_house_rotation(self, subject_with_gauquelin):
        """gauquelin_sector_cusps[0] is the ASC, so the sector-1 boundary must
        rotate exactly like the first-house division line (same wheel angle,
        same sign) in the same modern SVG."""
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="dark")
        svg = drawer.generate_svg_string(style="modern")

        cusps = subject_with_gauquelin.gauquelin_sector_cusps
        asc = subject_with_gauquelin.ascendant.abs_pos
        assert cusps[0] == pytest.approx(asc, abs=1e-3)  # model rounds to 4 decimals

        rotations = [float(m) for m in re.findall(r'rotate\((-?[\d.]+) 50', svg)]
        seventh = subject_with_gauquelin.seventh_house.abs_pos
        asc_wheel = (cusps[0] - seventh + 180) % 360
        assert any(abs(rot - (-asc_wheel)) < 1e-3 for rot in rotations), (
            f"no element rotated at -{asc_wheel} (ASC wheel angle) found"
        )
        # The mirrored (positive) rotation must NOT be present for the ASC.
        if asc_wheel > 1e-3:
            assert not any(abs(rot - asc_wheel) < 1e-3 for rot in rotations), (
                "found positively-rotated element at the ASC wheel angle (mirrored overlay)"
            )


class TestClassicGauquelinFallback:
    """Without real cusps the fallback grid must stay ASC-anchored (offset
    -180 = screen left) and descend in the diurnal direction."""

    def test_first_fallback_line_at_asc(self):
        r, inner_r, outer_r = 240.0, 56.0, 84.0
        svg = draw_gauquelin_sectors(r, inner_r, outer_r, 123.456, gauquelin_cusps=None)
        first_line = re.search(r'<line x1="(-?[\d.]+)" y1="(-?[\d.]+)"', svg)
        assert first_line is not None
        expected_x = wheel_x(0, (r - outer_r), -180.0) + outer_r
        expected_y = wheel_y(0, (r - outer_r), -180.0) + outer_r
        assert float(first_line.group(1)) == pytest.approx(expected_x, abs=0.01)
        assert float(first_line.group(2)) == pytest.approx(expected_y, abs=0.01)


class TestGauquelinHitAreaSweep:
    """Descending cusps traverse clockwise on screen: the wedge arcs need
    sweep flag 1 on the outer arc (and 0 on the inner return arc), or the
    click regions render as mirrored-center lens shapes."""

    def test_hit_area_arc_sweep_flags(self, subject_with_gauquelin, tmp_path):
        chart_data = ChartDataFactory.create_natal_chart_data(subject_with_gauquelin)
        drawer = ChartDrawer(chart_data=chart_data, theme="light")
        # The two-arc wedge path shape is the classic engine's contract; the
        # modern wheel draws its own sector geometry.
        drawer.save_svg(output_path=str(tmp_path), filename="gauq_sweep", style="classic")
        svg = (tmp_path / "gauq_sweep.svg").read_text()

        wedge_paths = re.findall(
            r'kr:node="GauquelinSector"[^>]*><path d="([^"]+)"', svg
        ) or re.findall(r"kr:node='GauquelinSector'[^>]*><path d='([^']+)'", svg)
        assert len(wedge_paths) == 36
        for d in wedge_paths:
            arcs = re.findall(r"A [\d.]+,[\d.]+ 0 (\d),(\d)", d)
            assert len(arcs) == 2, f"wedge path should have 2 arcs: {d}"
            assert arcs[0] == ("0", "1"), f"outer arc must sweep clockwise: {d}"
            assert arcs[1] == ("0", "0"), f"inner arc must sweep back: {d}"


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
        # Transparent-wedge hit areas are the classic engine's contract; the
        # modern wheel renders its own click sectors.
        drawer.save_svg(output_path=str(tmp_path), filename="gauq_hit_areas", style="classic")
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


class TestGauquelinAxisSectorsRound6:
    """Round-6 regression: axial points (ASC/MC/IC/DSC) must land on their exact
    Gauquelin sector at any latitude (they ARE cusps), not via a uniform
    10deg/sector ecliptic approximation that is only correct at the equator."""

    def test_axes_on_exact_sectors_high_latitude(self):
        from kerykeion import AstrologicalSubjectFactory
        s = AstrologicalSubjectFactory.from_birth_data(
            "X", 1990, 6, 15, 12, 0, lng=18.07, lat=59.33,
            tz_str="Europe/Stockholm", online=False, suppress_geonames_warning=True,
            calculate_gauquelin=True)
        assert abs(s.ascendant.gauquelin_sector - 1.0) < 0.05
        assert abs(s.medium_coeli.gauquelin_sector - 10.0) < 0.05
        assert abs(s.imum_coeli.gauquelin_sector - 28.0) < 0.05
        assert abs(s.descendant.gauquelin_sector - 19.0) < 0.05


class TestGauquelinPolarFallback:
    """R23 regression: at latitudes inside the polar circle the ``b"G"`` cusp
    call must route through ``houses_ex2_with_polar_fallback`` (clamp to ±66°
    with a warning) instead of being swallowed by the ``except Exception: pass``
    guard. Otherwise ``gauquelin_sector_cusps`` stays None and three consumers
    (secondary progressions, planetary returns, composite) infer that Gauquelin
    was disabled."""

    def test_polar_subject_has_36_cusps(self):
        s = AstrologicalSubjectFactory.from_birth_data(
            "Polar Gauquelin", 1990, 6, 15, 12, 0,
            lng=15.6, lat=78.2232, tz_str="Arctic/Longyearbyen",
            city="Longyearbyen", nation="NO", online=False,
            suppress_geonames_warning=True, calculate_gauquelin=True,
        )
        assert s.gauquelin_sector_cusps is not None
        assert len(s.gauquelin_sector_cusps) == 36
        # The real latitude is still persisted (only the cusps clamp).
        assert s.lat == 78.2232

    def test_control_latitude_unchanged(self):
        s = AstrologicalSubjectFactory.from_birth_data(
            "Sub-polar Gauquelin", 1990, 6, 15, 12, 0,
            lng=10.0, lat=60.0, tz_str="Europe/Oslo",
            city="Oslo", nation="NO", online=False,
            suppress_geonames_warning=True, calculate_gauquelin=True,
        )
        assert s.gauquelin_sector_cusps is not None
        assert len(s.gauquelin_sector_cusps) == 36

    def test_secondary_progression_of_polar_natal_keeps_gauquelin(self):
        """A secondary-progressed chart infers calculate_gauquelin from the
        natal's ``gauquelin_sector_cusps is not None`` — so the polar natal must
        carry cusps for the progressed chart to keep its Gauquelin sectors."""
        from kerykeion.secondary_progressions.secondary_progression_factory import (
            SecondaryProgressionFactory,
        )

        natal = AstrologicalSubjectFactory.from_birth_data(
            "Polar Natal", 1990, 6, 15, 12, 0,
            lng=15.6, lat=78.2232, tz_str="Arctic/Longyearbyen",
            city="Longyearbyen", nation="NO", online=False,
            suppress_geonames_warning=True, calculate_gauquelin=True,
        )
        progressed = SecondaryProgressionFactory.compute(natal, target_year=2020)
        assert progressed.gauquelin_sector_cusps is not None
        assert progressed.sun.gauquelin_sector is not None
