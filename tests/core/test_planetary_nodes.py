# -*- coding: utf-8 -*-
"""Tests for the Planetary Nodes & Apsides factory."""

import pytest
from kerykeion.ephemeris_backend import swe
from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, PlanetaryNodesFactory

_EPHE_PATH = str(Path(__file__).parent.parent.parent / "kerykeion" / "sweph")


@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Nodes Test", 2000, 1, 1, 12, 0,
        lng=0.0, lat=51.5, tz_str="Etc/GMT",
        city="Greenwich", nation="GB", online=False,
    )


class TestNodesFromSubject:
    def test_all_planets_returned(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject)
        assert len(result.nodes) >= 8  # At least Sun through Pluto

    def test_method_stored(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject, method="mean")
        assert result.method == "mean"

    def test_osculating_method(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject, method="osculating")
        assert result.method == "osculating"
        assert len(result.nodes) >= 8

    def test_node_has_valid_position(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject)
        for node in result.nodes:
            for point in [node.ascending_node, node.descending_node, node.perihelion, node.aphelion]:
                assert 0 <= point.abs_pos < 360
                assert point.sign in ("Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis")
                assert 0 <= point.position < 30

    def test_mars_ascending_node(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject, planets=["Mars"])
        assert len(result.nodes) == 1
        assert result.nodes[0].planet_name == "Mars"
        # Mars ascending node is roughly in Taurus
        asc = result.nodes[0].ascending_node
        assert 0 <= asc.abs_pos < 360


class TestNodesFromJulianDay:
    def test_j2000_epoch(self):
        result = PlanetaryNodesFactory.from_julian_day(2451545.0)
        assert len(result.nodes) >= 8
        assert result.julian_day == 2451545.0


class TestNodesFiltering:
    def test_single_planet(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject, planets=["Jupiter"])
        assert len(result.nodes) == 1
        assert result.nodes[0].planet_name == "Jupiter"

    def test_multiple_planets(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject, planets=["Mars", "Saturn"])
        assert len(result.nodes) == 2
        names = {n.planet_name for n in result.nodes}
        assert names == {"Mars", "Saturn"}


class TestSweRegressionNodes:
    """Regression tests: verify factory results match raw Swiss Ephemeris calls."""

    def test_mars_ascending_node_matches_swe(self):
        """Factory Mars ascending node longitude should match swe.nod_aps_ut."""
        jd_j2000 = 2451545.0
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        NODBIT_MEAN = getattr(swe, "NODBIT_MEAN", 1)

        swe.set_ephe_path(_EPHE_PATH)
        swe_result = swe.nod_aps_ut(jd_j2000, swe.MARS, iflag, NODBIT_MEAN)
        swe_asc_lon = swe_result[0][0] % 360
        swe_desc_lon = swe_result[1][0] % 360
        swe_peri_lon = swe_result[2][0] % 360
        swe_aph_lon = swe_result[3][0] % 360
        swe.close()

        factory_result = PlanetaryNodesFactory.from_julian_day(
            jd_j2000, method="mean", planets=["Mars"]
        )
        assert len(factory_result.nodes) == 1
        mars = factory_result.nodes[0]

        assert abs(mars.ascending_node.abs_pos - swe_asc_lon) < 0.01, (
            f"asc node: factory={mars.ascending_node.abs_pos} swe={swe_asc_lon}"
        )
        assert abs(mars.descending_node.abs_pos - swe_desc_lon) < 0.01, (
            f"desc node: factory={mars.descending_node.abs_pos} swe={swe_desc_lon}"
        )
        assert abs(mars.perihelion.abs_pos - swe_peri_lon) < 0.01, (
            f"perihelion: factory={mars.perihelion.abs_pos} swe={swe_peri_lon}"
        )
        assert abs(mars.aphelion.abs_pos - swe_aph_lon) < 0.01, (
            f"aphelion: factory={mars.aphelion.abs_pos} swe={swe_aph_lon}"
        )

    def test_jupiter_ascending_node_matches_swe(self):
        """Factory Jupiter ascending node longitude should match swe.nod_aps_ut."""
        jd_j2000 = 2451545.0
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        NODBIT_MEAN = getattr(swe, "NODBIT_MEAN", 1)

        swe.set_ephe_path(_EPHE_PATH)
        swe_result = swe.nod_aps_ut(jd_j2000, swe.JUPITER, iflag, NODBIT_MEAN)
        swe_asc_lon = swe_result[0][0] % 360
        swe.close()

        factory_result = PlanetaryNodesFactory.from_julian_day(
            jd_j2000, method="mean", planets=["Jupiter"]
        )
        assert len(factory_result.nodes) == 1
        jupiter = factory_result.nodes[0]

        assert abs(jupiter.ascending_node.abs_pos - swe_asc_lon) < 0.01, (
            f"Jupiter asc node: factory={jupiter.ascending_node.abs_pos} swe={swe_asc_lon}"
        )
