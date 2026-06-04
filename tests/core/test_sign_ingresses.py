# -*- coding: utf-8 -*-
"""Tests for the Sign Ingress Factory."""

import pytest

from kerykeion.sign_ingresses import SignIngressFactory
from kerykeion.utilities import datetime_to_julian
from datetime import datetime


class TestSunIngresses2026:
    """The Sun's ingresses are the equinoxes/solstices — exact known anchors."""

    def test_twelve_ingresses_never_retrograde(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        assert len(res.ingresses) == 12
        assert all(not x.retrograde for x in res.ingresses)
        # Each ingress lands on a 30° boundary.
        assert all(x.ecliptic_longitude % 30 == 0 for x in res.ingresses)

    def test_spring_equinox_into_aries(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        aries = [x for x in res.ingresses if x.sign == "Ari"][0]
        assert aries.iso_utc.startswith("2026-03-20")
        assert aries.from_sign == "Pis"
        assert aries.ecliptic_longitude == 0.0

    def test_summer_solstice_into_cancer(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        cancer = [x for x in res.ingresses if x.sign == "Can"][0]
        assert cancer.iso_utc.startswith("2026-06-21")
        assert cancer.ecliptic_longitude == 90.0

    def test_chronological_and_adjacent_signs(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31", ["Sun"])
        jds = [x.julian_day for x in res.ingresses]
        assert jds == sorted(jds)
        # Forward motion: each entered sign is the one after the sign left.
        for x in res.ingresses:
            assert x.sign_num == (x.from_sign_num + 1) % 12


class TestRetrogradeIngresses:
    """Pluto's 2023-2024 Capricorn<->Aquarius dance is a documented anchor."""

    def test_pluto_retrograde_reentry_into_capricorn(self):
        res = SignIngressFactory.from_iso_range("2023-01-01", "2024-12-31", ["Pluto"])
        # The retrograde step back into Capricorn on 11 Jun 2023.
        retro = [x for x in res.ingresses if x.retrograde]
        assert retro, "expected at least one retrograde ingress"
        first_retro = retro[0]
        assert first_retro.iso_utc.startswith("2023-06-11")
        assert first_retro.from_sign == "Aqu" and first_retro.sign == "Cap"
        assert first_retro.ecliptic_longitude == 300.0

    def test_pluto_final_ingress_into_aquarius_nov_2024(self):
        res = SignIngressFactory.from_iso_range("2023-01-01", "2024-12-31", ["Pluto"])
        last = res.ingresses[-1]
        assert last.iso_utc.startswith("2024-11-19")
        assert last.sign == "Aqu" and not last.retrograde


class TestIngressApi:
    """Factory entry points, defaults, and validation."""

    def test_default_excludes_moon(self):
        res = SignIngressFactory.from_iso_range("2026-01-01", "2026-12-31")
        assert all(x.planet != "Moon" for x in res.ingresses)

    def test_moon_is_opt_in_and_frequent(self):
        res = SignIngressFactory.from_iso_range(
            "2026-01-01", "2026-12-31", ["Moon"]
        )
        # The Moon changes sign every ~2.3 days => ~150+ ingresses a year.
        assert len(res.ingresses) > 140
        assert all(x.planet == "Moon" for x in res.ingresses)

    def test_unknown_planet_raises(self):
        with pytest.raises(ValueError):
            SignIngressFactory.from_iso_range(
                "2026-01-01", "2026-12-31", ["Sun", "Nibiru"]
            )

    def test_empty_range(self):
        start = datetime_to_julian(datetime(2026, 1, 1))
        res = SignIngressFactory.from_julian_day(start, start)
        assert res.ingresses == []

    def test_from_julian_day(self):
        start = datetime_to_julian(datetime(2026, 1, 1))
        end = datetime_to_julian(datetime(2026, 12, 31))
        res = SignIngressFactory.from_julian_day(start, end, ["Sun"])
        assert len(res.ingresses) == 12
        assert res.start_jd == start and res.end_jd == end
