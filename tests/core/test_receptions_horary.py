# -*- coding: utf-8 -*-
"""
Tests for mutual receptions (kerykeion.receptions) and horary indicators
(kerykeion.horary), plus the shared rulership lookups they build on.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from types import SimpleNamespace

import pytest

from kerykeion import HoraryIndicatorsFactory, MutualReceptionsFactory
from kerykeion.dignities import get_domicile_ruler, get_exaltation_ruler
from kerykeion.dignities.dignity_data import DOMICILE_RULERS
from kerykeion.horary.factory import HOUSE_CUSP_FIELDS, HOUSE_NAME_TO_NUMBER
from kerykeion.schemas.kr_literals import SIGN_CODES
from kerykeion.zodiacal_releasing.factory import TRADITIONAL_RULERS

pytestmark = pytest.mark.core


# ---------------------------------------------------------------------------
# Rulership lookups
# ---------------------------------------------------------------------------

def test_domicile_ruler_matches_the_dignity_table():
    for sign in SIGN_CODES:
        assert get_domicile_ruler(sign) == DOMICILE_RULERS[sign][0]


def test_zr_traditional_rulers_still_match_the_shared_source():
    """The ZR mapping is now derived — a regression guard for the refactor."""
    assert TRADITIONAL_RULERS == {sign: get_domicile_ruler(sign) for sign in SIGN_CODES}


def test_exaltation_ruler_known_values():
    assert get_exaltation_ruler("Ari") == "Sun"
    assert get_exaltation_ruler("Lib") == "Saturn"
    assert get_exaltation_ruler("Leo") is None


# ---------------------------------------------------------------------------
# Mutual receptions
# ---------------------------------------------------------------------------

def _point(name, sign):
    """A minimal duck-typed point (the factory only reads .name and .sign)."""
    return SimpleNamespace(name=name, sign=sign)


def test_domicile_reception_detected():
    # Sun in Cancer (Moon's sign) and Moon in Leo (Sun's sign).
    subject = SimpleNamespace(sun=_point("Sun", "Can"), moon=_point("Moon", "Leo"))
    receptions = MutualReceptionsFactory.from_subject(subject).receptions  # type: ignore[arg-type]
    assert [(r.first_planet, r.second_planet, r.reception_type) for r in receptions] == [
        ("Sun", "Moon", "domicile")
    ]


def test_exaltation_reception_detected():
    # Sun in Libra (Saturn's exaltation) and Saturn in Aries (Sun's exaltation).
    subject = SimpleNamespace(sun=_point("Sun", "Lib"), saturn=_point("Saturn", "Ari"))
    receptions = MutualReceptionsFactory.from_subject(subject).receptions  # type: ignore[arg-type]
    assert [(r.first_planet, r.second_planet, r.reception_type) for r in receptions] == [
        ("Sun", "Saturn", "exaltation")
    ]


def test_no_reception_when_one_sided():
    # Sun in Cancer but Moon in Aries: Moon does not sit in the Sun's sign.
    subject = SimpleNamespace(sun=_point("Sun", "Can"), moon=_point("Moon", "Ari"))
    assert MutualReceptionsFactory.from_subject(subject).receptions == []  # type: ignore[arg-type]


def test_receptions_on_a_real_chart(john_lennon):
    receptions = MutualReceptionsFactory.from_subject(john_lennon).receptions
    # Whatever is found must be internally consistent with the tables.
    for reception in receptions:
        first = getattr(john_lennon, reception.first_planet.lower())
        second = getattr(john_lennon, reception.second_planet.lower())
        if reception.reception_type == "domicile":
            assert get_domicile_ruler(first.sign) == reception.second_planet
            assert get_domicile_ruler(second.sign) == reception.first_planet
        else:
            assert get_exaltation_ruler(first.sign) == reception.second_planet
            assert get_exaltation_ruler(second.sign) == reception.first_planet


# ---------------------------------------------------------------------------
# Horary indicators
# ---------------------------------------------------------------------------

def test_significators_follow_classical_rulership(john_lennon):
    indicators = HoraryIndicatorsFactory.from_subject(john_lennon)
    assert indicators.querent.house == 1
    assert indicators.quesited.house == 7

    for significator in (indicators.querent, indicators.quesited):
        cusp = getattr(john_lennon, HOUSE_CUSP_FIELDS[significator.house - 1])
        assert significator.sign == cusp.sign
        assert significator.ruler == get_domicile_ruler(cusp.sign)
        ruler_point = getattr(john_lennon, significator.ruler.lower())
        assert significator.ruler_sign == ruler_point.sign
        assert significator.ruler_house == ruler_point.house
        if ruler_point.house is not None:
            assert significator.ruler_house_number == HOUSE_NAME_TO_NUMBER[str(ruler_point.house)]


def test_ascendant_degree_is_the_point_not_the_cusp(john_lennon):
    """The degree must come from the true Ascendant point (Whole Sign safe)."""
    indicators = HoraryIndicatorsFactory.from_subject(john_lennon)
    assert indicators.ascendant_degree == john_lennon.ascendant.position


def test_exactly_one_ascendant_consideration(john_lennon):
    indicators = HoraryIndicatorsFactory.from_subject(john_lennon)
    asc_keys = [c.key for c in indicators.considerations if c.key.startswith("asc_")]
    assert len(asc_keys) == 1
    degree = indicators.ascendant_degree
    if degree < 3:
        assert asc_keys == ["asc_early_degree"]
    elif degree >= 27:
        assert asc_keys == ["asc_late_degree"]
    else:
        assert asc_keys == ["asc_judgeable"]


def test_moon_void_consideration_is_tri_state(john_lennon):
    keys_none = {c.key for c in HoraryIndicatorsFactory.from_subject(john_lennon).considerations}
    assert "moon_void" not in keys_none and "moon_not_void" not in keys_none

    keys_void = {
        c.key
        for c in HoraryIndicatorsFactory.from_subject(john_lennon, is_moon_void=True).considerations
    }
    assert "moon_void" in keys_void

    keys_not_void = {
        c.key
        for c in HoraryIndicatorsFactory.from_subject(john_lennon, is_moon_void=False).considerations
    }
    assert "moon_not_void" in keys_not_void


def test_saturn_consideration_matches_its_house(john_lennon):
    indicators = HoraryIndicatorsFactory.from_subject(john_lennon)
    saturn_house = HOUSE_NAME_TO_NUMBER.get(str(john_lennon.saturn.house))
    keys = {c.key for c in indicators.considerations}
    assert ("saturn_in_first" in keys) == (saturn_house == 1)
    assert ("saturn_in_seventh" in keys) == (saturn_house == 7)


def test_receptions_are_included(john_lennon):
    indicators = HoraryIndicatorsFactory.from_subject(john_lennon)
    standalone = MutualReceptionsFactory.from_subject(john_lennon).receptions
    assert indicators.mutual_receptions == standalone


def test_non_terrestrial_chart_is_refused():
    """Horary indicators and receptions read cusps, angles and sign
    placements as seen from Earth: a chart cast from another origin
    (heliocentric, barycentric, planetocentric) would mix frames into
    plausible but invalid output — refuse, never mix."""
    from kerykeion.schemas import KerykeionException

    helio = SimpleNamespace(
        perspective_type="Heliocentric",
        mercury=SimpleNamespace(name="Mercury", sign="Vir"),
        venus=SimpleNamespace(name="Venus", sign="Tau"),
    )
    with pytest.raises(KerykeionException, match="terrestrial"):
        HoraryIndicatorsFactory.from_subject(helio)  # type: ignore[arg-type]
    with pytest.raises(KerykeionException, match="terrestrial"):
        MutualReceptionsFactory.from_subject(helio)  # type: ignore[arg-type]
