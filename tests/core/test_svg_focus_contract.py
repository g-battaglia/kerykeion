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
import xml.etree.ElementTree as ET

import pytest

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer
from kerykeion.planetary_returns.factory import PlanetaryReturnFactory
from kerykeion.charts.svg_metadata import ChartPointTag, parse_chart_points, point_state_attributes
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


# =============================================================================
# Point state and chart-analysis metadata
# =============================================================================


@pytest.fixture(scope="module")
def station_chart_data():
    """A chart whose Mercury is at a station — the rarest state to render."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Mercury station", 1990, 8, 25, 12, 0, "London", "GB", suppress_geonames_warning=True
    )
    return ChartDataFactory.create_natal_chart_data(subject)


@pytest.fixture(scope="module")
def heliocentric_chart_data():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Heliocentric",
        1940,
        10,
        9,
        18,
        30,
        "Liverpool",
        "GB",
        perspective_type="Heliocentric",
        suppress_geonames_warning=True,
    )
    return ChartDataFactory.create_natal_chart_data(subject)


class TestPointStateMetadata:
    """The state attributes ride on every point, in every style, unconditionally.

    They are not gated by a rendering flag: a consumer reading the SVG must be
    able to tell a body that has no such state from a chart style that forgot
    to say so, and that distinction only survives if all three serializers
    speak the same sentence.
    """

    @pytest.mark.parametrize("style", ["classic", "modern"])
    @pytest.mark.parametrize("output_method", ["generate_svg_string", "generate_wheel_only_svg_string"])
    def test_planets_carry_speed_declination_and_motion(self, natal_chart_data, style, output_method):
        svg = _svg(getattr(ChartDrawer(chart_data=natal_chart_data, style=style), output_method))
        by_slug = {_attr(a, "slug"): a for a in _node_attrs(svg, "ChartPoint")}
        for planet in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
            attrs = by_slug[planet]
            assert _attr(attrs, "motionstate") is not None, f"{style}/{output_method}: {planet} has no motion state"
            assert _attr(attrs, "speed") is not None
            assert _attr(attrs, "declination") is not None

    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_state_values_are_identical_across_styles(self, natal_chart_data, style):
        """A point's physical state cannot depend on how the wheel is drawn."""
        states = {}
        for candidate in ("classic", "modern"):
            svg = _svg(ChartDrawer(chart_data=natal_chart_data, style=candidate).generate_wheel_only_svg_string)
            states[candidate] = {
                _attr(a, "slug"): (_attr(a, "motionstate"), _attr(a, "speed"), _attr(a, "declination"))
                for a in _node_attrs(svg, "ChartPoint")
            }
        assert states["classic"] == states["modern"]

    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_stations_are_named_in_the_markup(self, station_chart_data, style):
        svg = _svg(ChartDrawer(chart_data=station_chart_data, style=style).generate_wheel_only_svg_string)
        by_slug = {_attr(a, "slug"): a for a in _node_attrs(svg, "ChartPoint")}
        assert _attr(by_slug["Mercury"], "motionstate") == "stationary_retrograde"

    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_out_of_bounds_marks_only_the_exception(self, natal_chart_data, style):
        """``kr:oob`` follows ``kr:retrograde``: present when true, absent otherwise."""
        svg = _svg(ChartDrawer(chart_data=natal_chart_data, style=style).generate_wheel_only_svg_string)
        values = {_attr(a, "oob") for a in _node_attrs(svg, "ChartPoint") if _attr(a, "oob") is not None}
        assert values <= {"true"}, f"{style}: kr:oob should never be emitted as false"

    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_non_geocentric_charts_claim_no_motion_state(self, heliocentric_chart_data, style):
        """Silence, not a guess: the tabulated means are geocentric."""
        svg = _svg(ChartDrawer(chart_data=heliocentric_chart_data, style=style).generate_wheel_only_svg_string)
        for attrs in _node_attrs(svg, "ChartPoint"):
            assert _attr(attrs, "motionstate") is None
            assert _attr(attrs, "oob") is None


class TestAnalysisMetadata:
    @pytest.mark.parametrize("style", ["classic", "modern"])
    @pytest.mark.parametrize("output_method", ["generate_svg_string", "generate_wheel_only_svg_string"])
    def test_angularity_and_stellium_reach_the_markup(self, natal_chart_data, style, output_method):
        svg = _svg(getattr(ChartDrawer(chart_data=natal_chart_data, style=style), output_method))
        by_slug = {_attr(a, "slug"): a for a in _node_attrs(svg, "ChartPoint")}

        expected_angular: dict[str, list[str]] = {}
        for angularity in natal_chart_data.angularities:
            expected_angular.setdefault(str(angularity.point), []).append(str(angularity.angle))
        assert expected_angular, "fixture no longer exercises angularity"
        for name, angles in expected_angular.items():
            value = _attr(by_slug[name], "angularity")
            assert value is not None
            assert [pair.rpartition(":")[0] for pair in value.split(" ")] == angles
            assert all(float(pair.rpartition(":")[2]) >= 0 for pair in value.split(" "))

        expected_stellium = {name: str(s.house) for s in natal_chart_data.stelliums for name in s.points}
        assert expected_stellium, "fixture no longer exercises stelliums"
        for name, house in expected_stellium.items():
            assert _attr(by_slug[name], "stellium") == house

    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_points_outside_an_analysis_carry_no_attribute(self, natal_chart_data, style):
        svg = _svg(ChartDrawer(chart_data=natal_chart_data, style=style).generate_wheel_only_svg_string)
        in_a_stellium = {name for s in natal_chart_data.stelliums for name in s.points}
        for attrs in _node_attrs(svg, "ChartPoint"):
            if _attr(attrs, "slug") not in in_a_stellium:
                assert _attr(attrs, "stellium") is None

    @pytest.mark.parametrize("style", ["classic", "modern"])
    def test_dual_charts_annotate_each_ring_from_its_own_analysis(self, style, john_lennon, paul_mccartney):
        chart_data = ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)
        svg = _svg(ChartDrawer(chart_data=chart_data, style=style).generate_wheel_only_svg_string)
        annotated: dict[str, set] = {"0": set(), "1": set()}
        for attrs in _node_attrs(svg, "ChartPoint"):
            if _attr(attrs, "stellium") is not None:
                annotated[_attr(attrs, "horoscope") or "0"].add(_attr(attrs, "slug"))

        for ring, stelliums in (
            ("0", chart_data.first_subject_stelliums),
            ("1", chart_data.second_subject_stelliums),
        ):
            assert annotated[ring] == {name for s in stelliums for name in s.points}


class TestAttributeNamingContract:
    """Every ``kr:`` name must be lowercase letters only.

    Consumers rewrite the namespace with a general pattern rather than an
    allow-list — the web frontend maps ``kr:name`` to ``data-kr-name`` through
    ``/\\bkr:([a-zA-Z]+)=/`` before sanitizing — so a name carrying an
    underscore or a digit is dropped in silence instead of failing loudly.
    """

    @pytest.mark.parametrize("style", ["classic", "modern"])
    @pytest.mark.parametrize(
        "output_method",
        ["generate_svg_string", "generate_wheel_only_svg_string", "generate_aspect_grid_only_svg_string"],
    )
    def test_every_emitted_attribute_name_is_plain_lowercase(self, natal_chart_data, style, output_method):
        svg = _svg(getattr(ChartDrawer(chart_data=natal_chart_data, style=style), output_method))
        names = set(re.findall(r"\bkr:([A-Za-z0-9_-]+)=", svg))
        assert names, "no kr: attributes found at all"
        offenders = {name for name in names if not name.isalpha() or not name.islower()}
        assert not offenders, f"{style}/{output_method}: unreachable attribute names {sorted(offenders)}"


# =============================================================================
# Metadata soundness — the cases a review found, pinned so they stay found
# =============================================================================


@pytest.fixture(scope="module")
def two_angles_chart_data():
    """A point standing on two angles at once.

    Near the poles the Ascendant and the Midheaven close on each other, so a
    planet can sit inside the orb of both — here Venus is 0.9° from the
    Ascendant and 4.3° from the Midheaven. Every chart in the ordinary fixtures
    has at most one angularity per point, which is why an encoding that could
    not express two passed the whole suite.
    """
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Two angles", 2000, 1, 16, 8, 0, "Tromso", "NO", lng=18.95, lat=67.0, tz_str="UTC",
        suppress_geonames_warning=True,
    )
    return ChartDataFactory.create_natal_chart_data(subject)


@pytest.fixture(scope="module")
def star_chart_data():
    """A chart carrying fixed stars, which are the only points with magnitude."""
    from kerykeion.settings.config_constants import DEFAULT_FIXED_STARS

    subject = AstrologicalSubjectFactory.from_birth_data(
        "Fixed stars", 1940, 10, 9, 18, 30, "Liverpool", "GB",
        active_fixed_stars=list(DEFAULT_FIXED_STARS),
        suppress_geonames_warning=True,
    )
    return ChartDataFactory.create_natal_chart_data(subject)


class TestMetadataIsWellFormed:
    @pytest.mark.parametrize("style", ["classic", "modern"])
    @pytest.mark.parametrize(
        "output_method",
        ["generate_svg_string", "generate_wheel_only_svg_string", "generate_aspect_grid_only_svg_string"],
    )
    def test_two_angularities_still_parse_as_xml(self, two_angles_chart_data, style, output_method):
        """Duplicate attribute names are not valid XML, whatever they carry."""
        from collections import Counter

        counts = Counter(a.point for a in two_angles_chart_data.angularities)
        assert max(counts.values()) >= 2, "fixture no longer has a point on two angles"

        svg = getattr(ChartDrawer(chart_data=two_angles_chart_data, style=style), output_method)()
        ET.fromstring(svg)

    def test_both_angles_survive_the_round_trip(self, two_angles_chart_data):
        """Modern only: parse_chart_points is pinned to that style's transform."""
        svg = _svg(ChartDrawer(chart_data=two_angles_chart_data, style="modern").generate_wheel_only_svg_string)
        tags = {t.slug: t for t in parse_chart_points(svg)}
        expected = {}
        for angularity in two_angles_chart_data.angularities:
            expected.setdefault(str(angularity.point), []).append(str(angularity.angle))

        for name, angles in expected.items():
            assert [angle for angle, _ in tags[name].angularities] == angles

    def test_a_hostile_name_cannot_escape_its_attribute(self):
        """Chart data can be deserialized or built by a caller, so names are not literals."""

        class Point:
            motion_state = None
            speed = None
            declination = None
            is_out_of_bounds = None
            magnitude = None
            orb = None
            near_point = 'Sun" onmouseover="alert(1)'

        emitted = point_state_attributes(Point())
        assert 'onmouseover="alert(1)"' not in emitted
        ET.fromstring(f'<g xmlns:kr="https://www.kerykeion.net/" {emitted.strip()} />')

    def test_an_apostrophe_survives_the_delimiter_swap(self):
        """Post-processing rewrites attribute delimiters to single quotes."""

        class Point:
            motion_state = None
            speed = None
            declination = None
            is_out_of_bounds = None
            magnitude = None
            orb = None
            near_point = "Regulus's star"

        emitted = point_state_attributes(Point())
        fragment = f'<g xmlns:kr="https://www.kerykeion.net/" {emitted.strip()} />'
        ET.fromstring(fragment.replace('"', "'").replace("&apos;", "&#39;"))

    def test_the_parser_exposes_every_attribute_the_emitter_writes(self, star_chart_data):
        """The contract in one assertion, so the next attribute cannot skip the parser.

        Checked against a chart carrying fixed stars, because the star-only
        attributes were the ones the emitter wrote and the parser dropped.
        """
        svg = _svg(ChartDrawer(chart_data=star_chart_data, style="modern").generate_wheel_only_svg_string)
        emitted = set()
        for attrs in _node_attrs(svg, "ChartPoint"):
            emitted.update(re.findall(r"kr:([a-z]+)=", attrs))

        # Structural attributes the tag models under other names, or not at all
        # because they identify the tag rather than describe the point.
        structural = {"node", "cx", "cy", "slug", "horoscope", "sign", "signposition", "absoluteposition", "house"}
        exposed = {
            "retrograde": "retrograde",
            "motionstate": "motion_state",
            "speed": "speed",
            "declination": "declination",
            "oob": "out_of_bounds",
            "angularity": "angularities",
            "angularitydistance": "angularities",
            "stellium": "stellium",
            "magnitude": "magnitude",
            "nearpoint": "near_point",
            "orb": "orb",
            "gauquelinsector": None,
            "projectedhouse": None,
            "projectedhoroscope": None,
        }
        unmodelled = {name for name in emitted - structural if exposed.get(name, "missing") == "missing"}
        assert not unmodelled, f"emitted but absent from ChartPointTag: {sorted(unmodelled)}"

        fields = set(ChartPointTag.__dataclass_fields__)
        for name in emitted - structural:
            field = exposed[name]
            if field is not None:
                assert field in fields, f"{name} maps to {field}, which ChartPointTag does not have"
