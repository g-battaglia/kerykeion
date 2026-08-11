# -*- coding: utf-8 -*-
"""
SVG focus-mode contract tests (classic + modern styles).

Downstream consumers (e.g. Astrologer Studio's focus mode) select chart
elements through the ``kr:*`` attribute vocabulary and match related nodes
by STRING equality of ``kr:absoluteposition`` / ``kr:horoscope``. These tests
pin that contract for both chart styles:

- Cusp / HouseNumber / HouseSector carry ``kr:horoscope`` where the classic
  engine emits it (owner filtering in dual-chart house focus).
- Indicator (degree tick) and ConnectingLine nodes carry
  ``kr:absoluteposition`` (and ``kr:horoscope`` in dual charts) whose string
  is identical to their owning ChartPoint's — the downstream matcher does
  ``indicator.absoluteposition === chartpoint.absoluteposition``.
- Aspect endpoint degrees (``kr:from/tooriginaldegrees``) are string-equal
  to ChartPoint ``kr:absoluteposition`` values.
- ``kr:cx`` / ``kr:cy`` are in SVG-root user space in EVERY output template
  (full chart and wheel-only, both styles).
- Gauquelin: ChartPoint carries ``kr:gauquelinsector`` in both styles.
- Dual charts: ChartPoint retains the owner's ``kr:house`` and also carries
  reciprocal ``kr:projectedhouse`` / ``kr:projectedhoroscope`` metadata.
"""

import re

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.planetary_returns.factory import PlanetaryReturnFactory
from kerykeion.secondary_progressions import SecondaryProgressionFactory


# =============================================================================
# Helpers
# =============================================================================


def _svg(drawer_method, **kwargs) -> str:
    """Render an SVG and normalize post-processing quote style to double quotes."""
    return drawer_method(**kwargs).replace("'", '"')


def _node_attrs(svg: str, node: str) -> list[str]:
    """Return the raw attribute string of every ``<g kr:node="{node}" ...>`` tag."""
    return re.findall(rf'<g kr:node="{node}"([^>]*)>', svg)


def _attr(attrs: str, name: str):
    m = re.search(rf'kr:{name}="([^"]+)"', attrs)
    return m.group(1) if m else None


def _keys(attr_list: list[str]) -> set:
    """(slug, horoscope, absoluteposition) triplets for matching tests."""
    out = set()
    for a in attr_list:
        out.add((_attr(a, "slug"), _attr(a, "horoscope"), _attr(a, "absoluteposition")))
    return out


def _glyph_centers(svg: str) -> list[tuple[str, float, float]]:
    out = []
    for a in _node_attrs(svg, "ChartPoint"):
        cx, cy = _attr(a, "cx"), _attr(a, "cy")
        if cx is not None and cy is not None:
            out.append((_attr(a, "slug"), float(cx), float(cy)))
    return out


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def natal_chart_data(john_lennon):
    return ChartDataFactory.create_natal_chart_data(john_lennon)


@pytest.fixture(scope="module")
def transit_chart_data(john_lennon, paul_mccartney):
    return ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)


@pytest.fixture(
    scope="module",
    params=["Transit", "Synastry", "SolarReturn", "LunarReturn", "Progression"],
)
def all_dual_chart_data(request, john_lennon, paul_mccartney):
    if request.param == "Transit":
        return ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)
    if request.param == "Synastry":
        return ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
    if request.param in {"SolarReturn", "LunarReturn"}:
        return_factory = PlanetaryReturnFactory(
            john_lennon,
            lng=-2.9833,
            lat=53.4,
            tz_str="Europe/London",
            online=False,
        )
        return_subject = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Solar" if request.param == "SolarReturn" else "Lunar",
        )
        return ChartDataFactory.create_return_chart_data(john_lennon, return_subject)
    progressed = SecondaryProgressionFactory.compute(john_lennon, target_year=2000)
    return ChartDataFactory.create_progression_chart_data(john_lennon, progressed)


@pytest.fixture(scope="module")
def gauquelin_chart_data():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Gauquelin Contract",
        1963,
        6,
        9,
        0,
        0,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
        calculate_gauquelin=True,
    )
    return ChartDataFactory.create_natal_chart_data(subject)


# =============================================================================
# Modern style — house-focus owner attributes
# =============================================================================


class TestModernHouseOwnerAttributes:
    def test_natal_cusps_carry_horoscope_0(self, natal_chart_data):
        svg = _svg(ChartDrawer(chart_data=natal_chart_data, style="modern").generate_wheel_only_svg_string)
        cusps = _node_attrs(svg, "Cusp")
        assert len(cusps) == 12
        assert all(_attr(a, "horoscope") == "0" for a in cusps)

    def test_natal_house_numbers_carry_horoscope_0(self, natal_chart_data):
        svg = _svg(ChartDrawer(chart_data=natal_chart_data, style="modern").generate_wheel_only_svg_string)
        numbers = _node_attrs(svg, "HouseNumber")
        assert len(numbers) == 12
        assert all(_attr(a, "horoscope") == "0" for a in numbers)

    def test_natal_house_sectors_have_no_horoscope_like_classic_single(self, natal_chart_data):
        svg = _svg(ChartDrawer(chart_data=natal_chart_data, style="modern").generate_wheel_only_svg_string)
        sectors = _node_attrs(svg, "HouseSector")
        assert len(sectors) == 12
        assert all(_attr(a, "horoscope") is None for a in sectors)

    def test_dual_house_nodes_carry_subject1_horoscope(self, transit_chart_data):
        svg = _svg(ChartDrawer(chart_data=transit_chart_data, style="modern").generate_wheel_only_svg_string)
        for node in ("Cusp", "HouseNumber", "HouseSector"):
            attrs = _node_attrs(svg, node)
            assert len(attrs) == 12, node
            assert all(_attr(a, "horoscope") == "0" for a in attrs), node


# =============================================================================
# Dual-chart owner/projected-house metadata (all dual types, both styles)
# =============================================================================


class TestDualChartHouseMetadata:
    @pytest.mark.parametrize("style", ["classic", "modern"])
    @pytest.mark.parametrize("output_method", ["generate_svg_string", "generate_wheel_only_svg_string"])
    def test_chartpoints_expose_owner_and_reciprocal_houses(self, all_dual_chart_data, style, output_method):
        drawer = ChartDrawer(chart_data=all_dual_chart_data, style=style)
        svg = _svg(getattr(drawer, output_method))
        chartpoints = {
            (_attr(attrs, "horoscope"), _attr(attrs, "absoluteposition")): attrs
            for attrs in _node_attrs(svg, "ChartPoint")
        }
        comparison = all_dual_chart_data.house_comparison
        assert comparison is not None

        ring_comparisons = (
            ("0", "1", all_dual_chart_data.first_subject, comparison.first_points_in_second_houses),
            ("1", "0", all_dual_chart_data.second_subject, comparison.second_points_in_first_houses),
        )
        for owner_ring, projected_ring, owner, points in ring_comparisons:
            assert points
            for point in points:
                owner_point = getattr(owner, point.point_name.lower())
                attrs = chartpoints[(owner_ring, str(owner_point.abs_pos))]
                assert _attr(attrs, "house") == point.point_owner_house_name
                assert _attr(attrs, "projectedhouse") == point.projected_house_name
                assert _attr(attrs, "projectedhoroscope") == projected_ring

    def test_metadata_does_not_require_house_comparison_payload(self, john_lennon, paul_mccartney):
        chart_data = ChartDataFactory.create_transit_chart_data(
            john_lennon,
            paul_mccartney,
            include_house_comparison=False,
        )
        assert chart_data.house_comparison is None

        svg = _svg(ChartDrawer(chart_data=chart_data).generate_wheel_only_svg_string)
        points = _node_attrs(svg, "ChartPoint")
        assert points
        assert all(_attr(attrs, "projectedhouse") is not None for attrs in points)
        assert {_attr(attrs, "projectedhoroscope") for attrs in points} == {"0", "1"}


# =============================================================================
# Indicator ownership (both styles)
# =============================================================================


class TestIndicatorOwnership:
    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_single_chart_indicators_match_chartpoints_by_string(self, natal_chart_data, style):
        svg = _svg(ChartDrawer(chart_data=natal_chart_data, style=style).generate_wheel_only_svg_string)
        indicators = _node_attrs(svg, "Indicator")
        assert indicators, "no Indicator nodes rendered"
        cp_positions = {_attr(a, "absoluteposition") for a in _node_attrs(svg, "ChartPoint")}
        for a in indicators:
            pos = _attr(a, "absoluteposition")
            assert pos is not None
            assert pos in cp_positions

    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_dual_chart_indicators_carry_ring_and_match_chartpoints(self, transit_chart_data, style):
        svg = _svg(ChartDrawer(chart_data=transit_chart_data, style=style).generate_wheel_only_svg_string)
        indicators = _node_attrs(svg, "Indicator")
        assert indicators, "no Indicator nodes rendered"
        horoscopes = {_attr(a, "horoscope") for a in indicators}
        assert horoscopes == {"0", "1"}, f"expected ticks on both rings, got {horoscopes}"
        assert _keys(indicators) <= _keys(_node_attrs(svg, "ChartPoint"))

    def test_external_natal_connecting_lines_carry_absoluteposition(self, john_lennon):
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        drawer = ChartDrawer(chart_data=chart_data, style="classic", external_view=True)
        svg = _svg(drawer.generate_wheel_only_svg_string)
        lines = _node_attrs(svg, "ConnectingLine")
        assert lines, "external natal should render ConnectingLine nodes"
        cp_positions = {_attr(a, "absoluteposition") for a in _node_attrs(svg, "ChartPoint")}
        for a in lines:
            pos = _attr(a, "absoluteposition")
            assert pos is not None
            assert pos in cp_positions


# =============================================================================
# Aspect endpoint <-> ChartPoint string equality (both styles)
# =============================================================================


class TestAspectEndpointFormatting:
    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_dual_aspect_endpoints_subset_of_chartpoint_positions(self, transit_chart_data, style):
        svg = _svg(ChartDrawer(chart_data=transit_chart_data, style=style).generate_wheel_only_svg_string)
        aspects = _node_attrs(svg, "Aspect")
        assert aspects, "no Aspect nodes rendered"
        cp_positions = {_attr(a, "absoluteposition") for a in _node_attrs(svg, "ChartPoint")}
        endpoints = set()
        for a in aspects:
            endpoints.add(_attr(a, "fromoriginaldegrees"))
            endpoints.add(_attr(a, "tooriginaldegrees"))
        endpoints.discard(None)
        assert endpoints and endpoints <= cp_positions


# =============================================================================
# kr:cx / kr:cy root-space normalization
# =============================================================================


class TestGlyphCenterRootSpace:
    def test_modern_full_chart_rebased_from_wheel_only(self, natal_chart_data):
        drawer = ChartDrawer(chart_data=natal_chart_data, style="modern")
        wheel = _glyph_centers(_svg(drawer.generate_wheel_only_svg_string))
        full = _glyph_centers(_svg(drawer.generate_svg_string))
        assert wheel and len(wheel) == len(full)
        scale = (2 * drawer.main_radius) / 100
        ty = drawer._vertical_offsets["wheel"]
        for (slug_w, wx, wy), (slug_f, fx, fy) in zip(wheel, full):
            assert slug_w == slug_f
            assert fx == pytest.approx(wx * scale + 100.0, abs=1e-9)
            assert fy == pytest.approx(wy * scale + ty, abs=1e-9)

    def test_classic_wheel_only_includes_full_wheel_translate(self, natal_chart_data):
        drawer = ChartDrawer(chart_data=natal_chart_data, style="classic")
        wheel = _glyph_centers(_svg(drawer.generate_wheel_only_svg_string))
        full = _glyph_centers(_svg(drawer.generate_svg_string))
        assert wheel and len(wheel) == len(full)
        ty = drawer._vertical_offsets["wheel"]
        for (slug_w, wx, wy), (slug_f, fx, fy) in zip(wheel, full):
            assert slug_w == slug_f
            # Same tx (100); ty differs only by the template's vertical offset.
            assert fx == pytest.approx(wx, abs=1e-9)
            assert fy - ty == pytest.approx(wy - 50.0, abs=1e-9)

    def test_modern_wheel_only_centers_inside_viewbox(self, natal_chart_data):
        drawer = ChartDrawer(chart_data=natal_chart_data, style="modern")
        centers = _glyph_centers(_svg(drawer.generate_wheel_only_svg_string))
        assert centers
        for _, cx, cy in centers:
            assert 0.0 <= cx <= 100.0
            assert 0.0 <= cy <= 100.0


# =============================================================================
# Gauquelin metadata parity
# =============================================================================


class TestGauquelinMetadata:
    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_chartpoints_carry_gauquelin_sector(self, gauquelin_chart_data, style):
        svg = _svg(ChartDrawer(chart_data=gauquelin_chart_data, style=style).generate_wheel_only_svg_string)
        sectors = {}
        for a in _node_attrs(svg, "ChartPoint"):
            gauq = _attr(a, "gauquelinsector")
            if gauq is not None:
                sectors[(_attr(a, "slug"), _attr(a, "absoluteposition"))] = gauq
        assert sectors, f"{style}: no ChartPoint carries kr:gauquelinsector"

    def test_gauquelin_sector_values_identical_across_styles(self, gauquelin_chart_data):
        values = {}
        for style in ("classic", "modern"):
            svg = _svg(ChartDrawer(chart_data=gauquelin_chart_data, style=style).generate_wheel_only_svg_string)
            values[style] = {
                (_attr(a, "slug")): _attr(a, "gauquelinsector")
                for a in _node_attrs(svg, "ChartPoint")
                if _attr(a, "gauquelinsector") is not None
            }
        assert values["classic"] and values["classic"] == values["modern"]

    def test_modern_gauquelin_sector_wedges_present(self, gauquelin_chart_data):
        svg = _svg(ChartDrawer(chart_data=gauquelin_chart_data, style="modern").generate_wheel_only_svg_string)
        wedges = _node_attrs(svg, "GauquelinSector")
        assert len(wedges) == 36
        assert {_attr(a, "sector") for a in wedges} == {str(n) for n in range(1, 37)}
