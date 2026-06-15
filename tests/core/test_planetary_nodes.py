# -*- coding: utf-8 -*-
"""Tests for the Planetary Nodes & Apsides factory."""

import pytest
from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion import AstrologicalSubjectFactory, PlanetaryNodesFactory
from kerykeion.schemas import KerykeionException

# The full default set: every supported planet, Moon through Pluto. The Sun
# is deliberately absent — it has no geocentric orbital nodes/apsides and the
# ephemeris would only return all-zero placeholders for it.
_DEFAULT_NODE_PLANETS = {
    "Moon", "Mercury", "Venus", "Mars", "Jupiter",
    "Saturn", "Uranus", "Neptune", "Pluto",
}


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
        assert {n.planet_name for n in result.nodes} == _DEFAULT_NODE_PLANETS

    def test_method_stored(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject, method="mean")
        assert result.method == "mean"

    def test_osculating_method(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject, method="osculating")
        assert result.method == "osculating"
        assert {n.planet_name for n in result.nodes} == _DEFAULT_NODE_PLANETS

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
        assert {n.planet_name for n in result.nodes} == _DEFAULT_NODE_PLANETS
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


class TestSunExcluded:
    """v6 pre-beta fix: the Sun has no geocentric orbital nodes/apsides.

    ``nod_aps_ut`` returns all zeros for it, so it used to surface as a junk
    node model with every point at 0° Aries. It is now excluded from the
    defaults, and an explicit request raises instead of returning fake data.
    """

    def test_default_call_excludes_sun(self, subject):
        result = PlanetaryNodesFactory.from_subject(subject)
        assert "Sun" not in {n.planet_name for n in result.nodes}

    def test_explicit_sun_request_raises_from_subject(self, subject):
        with pytest.raises(KerykeionException, match="Sun has no geocentric"):
            PlanetaryNodesFactory.from_subject(subject, planets=["Sun"])

    def test_explicit_sun_request_raises_from_julian_day(self):
        with pytest.raises(KerykeionException, match="Sun has no geocentric"):
            PlanetaryNodesFactory.from_julian_day(2451545.0, planets=["Sun", "Mars"])


class TestSweRegressionNodes:
    """Regression tests: verify factory results match raw Swiss Ephemeris calls."""

    def test_mars_ascending_node_matches_swe(self):
        """Factory Mars ascending node longitude should match ephe.nod_aps_ut."""
        jd_j2000 = 2451545.0
        NODBIT_MEAN = getattr(ephe, "NODBIT_MEAN", 1)

        with ephemeris_session() as iflag:
            swe_result = ephe.nod_aps_ut(jd_j2000, ephe.MARS, iflag, NODBIT_MEAN)
            swe_asc_lon = swe_result[0][0] % 360
            swe_desc_lon = swe_result[1][0] % 360
            swe_peri_lon = swe_result[2][0] % 360
            swe_aph_lon = swe_result[3][0] % 360

        factory_result = PlanetaryNodesFactory.from_julian_day(
            jd_j2000, method="mean", planets=["Mars"]
        )
        assert len(factory_result.nodes) == 1
        mars = factory_result.nodes[0]

        assert abs(mars.ascending_node.abs_pos - swe_asc_lon) < 0.01, (
            f"asc node: factory={mars.ascending_node.abs_pos} ephe={swe_asc_lon}"
        )
        assert abs(mars.descending_node.abs_pos - swe_desc_lon) < 0.01, (
            f"desc node: factory={mars.descending_node.abs_pos} ephe={swe_desc_lon}"
        )
        assert abs(mars.perihelion.abs_pos - swe_peri_lon) < 0.01, (
            f"perihelion: factory={mars.perihelion.abs_pos} ephe={swe_peri_lon}"
        )
        assert abs(mars.aphelion.abs_pos - swe_aph_lon) < 0.01, (
            f"aphelion: factory={mars.aphelion.abs_pos} ephe={swe_aph_lon}"
        )

    def test_jupiter_ascending_node_matches_swe(self):
        """Factory Jupiter ascending node longitude should match ephe.nod_aps_ut."""
        jd_j2000 = 2451545.0
        NODBIT_MEAN = getattr(ephe, "NODBIT_MEAN", 1)

        with ephemeris_session() as iflag:
            swe_result = ephe.nod_aps_ut(jd_j2000, ephe.JUPITER, iflag, NODBIT_MEAN)
            swe_asc_lon = swe_result[0][0] % 360

        factory_result = PlanetaryNodesFactory.from_julian_day(
            jd_j2000, method="mean", planets=["Jupiter"]
        )
        assert len(factory_result.nodes) == 1
        jupiter = factory_result.nodes[0]

        assert abs(jupiter.ascending_node.abs_pos - swe_asc_lon) < 0.01, (
            f"Jupiter asc node: factory={jupiter.ascending_node.abs_pos} ephe={swe_asc_lon}"
        )


class TestSiderealFrameConsistency:
    """v6 pre-beta fix: nodes from a sidereal subject must be in the subject's
    own zodiac frame (previously tropical longitudes were attached to sidereal
    charts, mislabelling the signs)."""

    def test_lahiri_nodes_differ_from_tropical_by_ayanamsa(self):
        """LAHIRI vs tropical subject at the same instant: node longitudes
        differ by exactly the chart ayanamsa (mod 360)."""
        birth = dict(
            year=2000, month=1, day=1, hour=12, minute=0,
            lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False,
        )
        tropical = AstrologicalSubjectFactory.from_birth_data("Nodes Tropical", **birth)
        sidereal = AstrologicalSubjectFactory.from_birth_data(
            "Nodes Lahiri", **birth, zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        assert sidereal.ayanamsa_value is not None
        ayanamsa = sidereal.ayanamsa_value

        trop_nodes = PlanetaryNodesFactory.from_subject(tropical, planets=["Mars", "Jupiter"])
        sid_nodes = PlanetaryNodesFactory.from_subject(sidereal, planets=["Mars", "Jupiter"])

        # zip() would silently drop the tail if the two factories returned a
        # different number of nodes — assert parity so the comparison is total.
        assert len(trop_nodes.nodes) == len(sid_nodes.nodes)
        for trop, sid in zip(trop_nodes.nodes, sid_nodes.nodes):
            assert trop.planet_name == sid.planet_name
            for attr in ("ascending_node", "descending_node", "perihelion", "aphelion"):
                trop_lon = getattr(trop, attr).abs_pos
                sid_lon = getattr(sid, attr).abs_pos
                diff = (trop_lon - sid_lon) % 360.0
                assert diff == pytest.approx(ayanamsa, abs=0.01), (
                    f"{trop.planet_name} {attr}: tropical={trop_lon} sidereal={sid_lon} "
                    f"diff={diff} expected ayanamsa={ayanamsa}"
                )
