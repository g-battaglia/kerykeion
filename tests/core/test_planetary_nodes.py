# -*- coding: utf-8 -*-
"""Tests for the Planetary Nodes & Apsides factory."""

import pytest
from kerykeion import AstrologicalSubjectFactory, PlanetaryNodesFactory


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
