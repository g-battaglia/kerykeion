"""Independent numerical rule tests; not a complete reference-output oracle."""

from itertools import product
from math import nan, inf
from random import Random

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.relationship_score import RelationshipScoreFactory
from kerykeion.relationship_score.v2 import RelationshipScoreFactoryV2, score_positions
from kerykeion.relationship_score.v2.calculator import (
    SCORING_ASPECTS,
    REQUIRED_POINTS,
    _measure_separation,
    _score_description,
)
from kerykeion.schemas.exceptions import KerykeionException


A = {"Sun": 10.0, "Moon": 53.0, "Ascendant": 101.0, "Venus": 203.0, "Mars": 254.0}
B = {"Sun": 47.0, "Moon": 167.0, "Ascendant": 283.0, "Venus": 321.0, "Mars": 15.0}


def pair_result(p1, p2, difference):
    """Isolate a contact in the breakdown, not by silently omitting other points."""
    a, b = dict(A), dict(B)
    a[p1], b[p2] = 0.0, difference
    result = score_positions(a, b)
    matches = [c for c in result.contacts if (c.p1_name, c.p2_name) == (p1, p2)]
    return result, matches


@pytest.mark.parametrize("angle,expected", [(0, 4), (60, 4), (90, 11), (120, 4), (180, 11)])
def test_sun_sun_special_awards_only_square_opposition(angle, expected):
    _, contacts = pair_result("Sun", "Sun", angle)
    assert len(contacts) == 1
    assert contacts[0].points == expected


@pytest.mark.parametrize("p1,p2", [("Sun", "Moon"), ("Moon", "Sun")])
@pytest.mark.parametrize("delta,expected", [(0, 11), (2, 11), (2.999, 11), (3, 8), (8.999, 8), (9, None)])
def test_sun_moon_quantized_boundaries_and_replacement(p1, p2, delta, expected):
    result, contacts = pair_result(p1, p2, delta)
    assert [c.points for c in contacts] == ([] if expected is None else [expected])
    matching_breakdown = [i for i in result.score_breakdown if i.description.startswith(f"{p1}-{p2} ")]
    assert len(matching_breakdown) == len(contacts)  # never +11 AND +4


@pytest.mark.parametrize("center,orb", [(90, 5), (180, 8)])
@pytest.mark.parametrize("offset,expected", [(2, 11), (2.999, 11), (3, 8)])
def test_sun_sun_upgrade_boundary(center, orb, offset, expected):
    _, contacts = pair_result("Sun", "Sun", center + offset)
    assert contacts[0].points == expected
    assert contacts[0].orb_limit == orb


@pytest.mark.parametrize("p1,p2", list(product(("Sun", "Moon", "Ascendant"), repeat=2)))
def test_all_nine_luminary_pairs_including_moon_moon_and_axis_axis(p1, p2):
    _, contacts = pair_result(p1, p2, 60)
    assert len(contacts) == 1
    assert contacts[0].points == 4


@pytest.mark.parametrize("name,angle,orb", [(a.name, a.angle, a.orb) for a in SCORING_ASPECTS])
def test_every_profile_aspect_including_minors(name, angle, orb):
    _, contacts = pair_result("Moon", "Moon", angle)
    assert contacts[0].aspect == name
    assert contacts[0].orb_limit == orb
    # Quantization admits up to almost one extra physical degree on this side.
    _, edge = pair_result("Moon", "Moon", angle + orb + 0.999)
    assert edge[0].aspect == name
    _, outside = pair_result("Moon", "Moon", angle + orb + 1)
    assert not outside


def test_sextile_three_not_four_and_quincunx_disabled():
    assert pair_result("Moon", "Moon", 63.999)[1][0].points == 4
    assert not pair_result("Moon", "Moon", 64)[1]
    assert not pair_result("Moon", "Moon", 150)[1]
    assert not pair_result("Moon", "Moon", 72)[1]  # no quintile


@pytest.mark.parametrize(
    "a,b,physical,legacy",
    [
        (0, 359.9, 0.1, 1),
        (359.9, 0, 0.1, 1),
        (0, 8.999, 8.999, 8),
        (0, 190.999, 169.001, 190),
        (0, 191, 169, 169),
        (359.99, 0.01, 0.02, 1),
    ],
)
def test_round_down_before_wrap_preserves_operation_order(a, b, physical, legacy):
    separation = _measure_separation(a, b)
    assert separation.physical == pytest.approx(physical)
    assert separation.scoring == legacy


def test_tight_residual_is_not_the_physical_residual():
    _, contacts = pair_result("Sun", "Moon", 2.99)
    c = contacts[0]
    assert c.scoring_orbit == 2
    assert c.orbit == pytest.approx(2.99)
    assert c.points == 11


@pytest.mark.parametrize("first_sign,second_sign", list(product(range(12), repeat=2)))
def test_all_144_destiny_sign_combinations(first_sign, second_sign):
    a, b = dict(A), dict(B)
    a["Sun"], b["Sun"] = first_sign * 30 + 1, second_sign * 30 + 20
    r = score_positions(a, b)
    assert r.is_destiny_sign == ((second_sign - first_sign) % 12 in {0, 3, 6, 9})
    # Distances 19 degrees away from exact square/opposition: no suppression.
    assert not r.destiny_bonus_suppressed
    assert r.destiny_bonus_awarded == r.is_destiny_sign
    assert sum(x.points for x in r.score_breakdown if x.rule == "destiny_sign") == (5 if r.is_destiny_sign else 0)


@pytest.mark.parametrize("angle", [90, 92.99, 95.99, 180, 188.99])
def test_destiny_not_double_counted_with_sun_sun_square_opposition(angle):
    r, contacts = pair_result("Sun", "Sun", angle)
    assert contacts[0].points in (8, 11)
    assert r.is_destiny_sign
    assert r.destiny_bonus_suppressed
    assert not r.destiny_bonus_awarded
    assert not any(x.rule == "destiny_sign" for x in r.score_breakdown)


def test_same_sign_sun_conjunction_still_gets_generic_four_and_destiny_five():
    r, contacts = pair_result("Sun", "Sun", 0)
    assert contacts[0].points == 4
    assert r.destiny_bonus_awarded


def test_venus_mars_counts_both_directions_not_once():
    a, b = dict(A), dict(B)
    a["Venus"], b["Mars"] = 0, 60
    a["Mars"], b["Venus"] = 10, 100
    r = score_positions(a, b)
    contacts = [c for c in r.contacts if c.rule == "venus_mars"]
    assert {(c.p1_name, c.p2_name) for c in contacts} == {("Venus", "Mars"), ("Mars", "Venus")}
    assert sum(c.points for c in contacts) == 8


def test_mercury_outer_planets_and_other_pairs_do_not_add_points():
    r = score_positions(A, B)
    a, b = dict(A, Mercury=0, Jupiter=20), dict(B, Mercury=0, Jupiter=20)
    assert score_positions(a, b).score_value == r.score_value


@pytest.mark.parametrize("point", REQUIRED_POINTS)
def test_missing_points_fail_closed(point):
    a = dict(A)
    del a[point]
    with pytest.raises(KerykeionException, match=point):
        score_positions(a, B)
    with pytest.raises(KerykeionException, match=point):
        score_positions(B, a)


@pytest.mark.parametrize("bad", [nan, inf, -inf, -0.01, 360, 361, True, None, "10"])
def test_nonfinite_out_of_range_or_nonnumeric_positions_rejected(bad):
    with pytest.raises(KerykeionException, match="Invalid Sun"):
        score_positions(dict(A, Sun=bad), B)


@pytest.mark.parametrize("names", [("A",), ("A", "B", "C"), (None, "B")])
def test_invalid_names_fail(names):
    with pytest.raises(KerykeionException):
        score_positions(A, B, subject_names=names)


def reference_score(a, b):
    """Independent interval-based implementation of the reference equations.

    Uses explicit interval bounds instead of the production residual classifier.
    This checks the reconstruction internally, not every historical output.
    """
    score = 0
    sun_major = False
    for i in ("Sun", "Moon", "Ascendant"):
        for j in ("Sun", "Moon", "Ascendant"):
            d = int(abs(a[i] - b[j]))
            if d > 190:
                d = 360 - d
            special = False
            if {i, j} == {"Sun", "Moon"} and d <= 8:
                score += 11 if d <= 2 else 8
                special = True
            if i == j == "Sun":
                if 88 <= d <= 92 or 178 <= d <= 182:
                    score += 11
                    special = True
                    sun_major = True
                elif 85 <= d <= 95 or 172 <= d <= 188:
                    score += 8
                    special = True
                    sun_major = True
            if not special:
                for low, high in [(-8, 8), (28, 32), (43, 47), (57, 63), (85, 95), (113, 127), (133, 137), (172, 188)]:
                    if low <= d <= high:
                        score += 4
                        break
    for i, j in [("Venus", "Mars"), ("Mars", "Venus")]:
        d = int(abs(a[i] - b[j]))
        if d > 190:
            d = 360 - d
        if any(
            low <= d <= high
            for low, high in [(-8, 8), (28, 32), (43, 47), (57, 63), (85, 95), (113, 127), (133, 137), (172, 188)]
        ):
            score += 4
    if not sun_major and (int(a["Sun"] / 30) - int(b["Sun"] / 30)) % 3 == 0:
        score += 5
    return score


def test_differential_reference_500_seeded_charts_symmetry_and_accounting():
    rng = Random(936275)
    for _ in range(500):
        a, b = ({p: rng.uniform(0, 359.999999) for p in REQUIRED_POINTS} for _ in range(2))
        r = score_positions(a, b)
        assert r.score_value == reference_score(a, b)
        assert r.score_value == score_positions(b, a).score_value
        assert r.score_value == sum(i.points for i in r.score_breakdown)
        assert len(r.contacts) == len(r.aspects)
        assert len({(c.p1_name, c.p2_name) for c in r.contacts}) == len(r.contacts)


@pytest.mark.parametrize(
    "value,label",
    [
        (0, "Minimal"),
        (4, "Minimal"),
        (5, "Medium"),
        (9, "Medium"),
        (10, "Important"),
        (14, "Important"),
        (15, "Very Important"),
        (19, "Very Important"),
        (20, "Exceptional"),
        (30, "Rare Exceptional"),
        (100, "Rare Exceptional"),
    ],
)
def test_v1_classification_bands_are_preserved(value, label):
    assert _score_description(value) == label


@pytest.fixture(scope="module")
def natal_subjects():
    common = dict(
        lng=12.4964,
        lat=41.9028,
        tz_str="Europe/Rome",
        online=False,
        suppress_geonames_warning=True,
        active_points=list(REQUIRED_POINTS),
        calculate_lunar_phase=False,
    )
    return (
        AstrologicalSubjectFactory.from_birth_data("A", 1990, 6, 15, 12, 30, **common),
        AstrologicalSubjectFactory.from_birth_data("B", 1992, 8, 20, 14, 45, **common),
    )


def test_factory_integrates_positions_not_aspects(monkeypatch, natal_subjects):
    from kerykeion.aspects import AspectsFactory

    def forbidden(*args, **kwargs):
        raise AssertionError("v2 must not call the aspect factory/v1")

    monkeypatch.setattr(AspectsFactory, "dual_chart_aspects", forbidden)
    monkeypatch.setattr(RelationshipScoreFactory, "get_relationship_score", forbidden)
    a, b = natal_subjects
    f = RelationshipScoreFactoryV2(a, b)
    result = f.get_relationship_score()
    inputs = [{p: getattr(s, p.lower()).abs_pos for p in REQUIRED_POINTS} for s in (a, b)]
    assert result.score_value == score_positions(*inputs).score_value
    assert result.subjects == [a, b]
    assert result.positions == inputs


def test_factory_repeat_calls_and_snapshot_isolation(natal_subjects):
    a, b = (s.model_copy(deep=True) for s in natal_subjects)
    f = RelationshipScoreFactoryV2(a, b)
    r = f.get_relationship_score()
    expected = r.score_value
    r.score_breakdown.clear()
    r.positions[0]["Sun"] = 0
    a.sun.abs_pos = 0
    again = f.get_relationship_score()
    assert again.score_value == expected
    assert again.score_breakdown
    assert again.positions[0]["Sun"] != 0
    exposed_subject = f.first_subject
    exposed_subject.sun.abs_pos = 0
    assert f.get_relationship_score().subjects[0].sun.abs_pos == again.positions[0]["Sun"]


@pytest.mark.parametrize("bad", [None, "subject", 42])
def test_non_mapping_position_inputs_raise_domain_exception(bad):
    with pytest.raises(KerykeionException, match="map point names"):
        score_positions(bad, B)


@pytest.mark.parametrize("bad", [None, "subject", 42])
def test_invalid_subject_models_raise_domain_exception(bad, natal_subjects):
    with pytest.raises(KerykeionException):
        RelationshipScoreFactoryV2(bad, natal_subjects[0])


def test_missing_active_point_and_mixed_frame(natal_subjects):
    a, b = natal_subjects
    missing = b.model_copy(update={"moon": None})
    with pytest.raises(KerykeionException, match="Moon"):
        RelationshipScoreFactoryV2(a, missing)
    sidereal = b.model_copy(update={"zodiac_type": "Sidereal"})
    with pytest.raises(KerykeionException):
        RelationshipScoreFactoryV2(a, sidereal)
    with pytest.raises(KerykeionException, match="Tropical"):
        RelationshipScoreFactoryV2(sidereal, sidereal)
    helio = b.model_copy(update={"perspective_type": "Heliocentric"})
    with pytest.raises(KerykeionException):
        RelationshipScoreFactoryV2(helio, helio)


def test_json_roundtrip_preserves_only_data_and_numerical_metadata():
    result = score_positions(A, B, subject_names=("A\nB", "Second"))
    restored = type(result).model_validate_json(result.model_dump_json())
    assert restored == result
    assert not hasattr(result, "to_markdown")
    assert not hasattr(result, "save_markdown")
    assert result.metadata.evaluated_pairs == 11
    assert result.metadata.quantization == "floor_absolute_difference_before_wrap"
    assert result.metadata.aspect_orbs["sextile"] == 3
    assert result.metadata.point_awards == {
        "luminary_aspect": 4,
        "destiny_sign": 5,
        "venus_mars": 4,
        "special_standard": 8,
        "special_tight": 11,
    }
    assert not result.metadata.reference_verified
    assert result.subject_names == ["A\nB", "Second"]
    for aspect, contact in zip(result.aspects, result.contacts):
        assert aspect.orbit == contact.orbit  # v1 field stays physical
    result.metadata.aspect_orbs["sextile"] = 99
    assert score_positions(A, B).metadata.aspect_orbs["sextile"] == 3


def test_suppressed_destiny_is_structured_metadata_not_interpretation():
    result, _ = pair_result("Sun", "Sun", 90)
    assert result.model_dump()["destiny_bonus_suppressed"] is True


def test_pure_inputs_not_mutated():
    a, b = dict(A), dict(B)
    r = score_positions(a, b)
    r.positions[0]["Sun"] = 300
    assert a == A and b == B
