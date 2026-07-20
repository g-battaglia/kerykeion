# -*- coding: utf-8 -*-
"""Invariants that must hold when a house system is undefined inside the polar circle.

Quadrant systems such as Placidus divide the semi-diurnal arc of a degree of the
ecliptic. Beyond the polar circle some degrees never rise or set, so that arc does
not exist and the division is genuinely undefined. Something has to give — but the
choice of WHAT gives is where a chart quietly stops describing the birth.

Moving the observer to the polar limit keeps the requested system at the cost of
computing the chart for a place nobody was born in. Because the Ascendant is the
intersection of the ecliptic with the HORIZON, it is a function of latitude, so a
moved observer drags the angles with it: every latitude beyond the circle collapses
onto one frozen Ascendant, and the same instant and place yields a different
Ascendant under Placidus than under Whole Sign. Substituting the house SYSTEM at the
real latitude confines the approximation to the intermediate cusps, which is the
only place the ambiguity genuinely lives.

These tests encode that choice as invariants rather than as position goldens: a
golden would also move when the ephemeris moves, whereas an invariant that ties two
simultaneously-computed values together stays diagnostic.
"""

from __future__ import annotations

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_backend import (
    BACKEND_NAME,
    ephemeris_session,
    houses_ex2_with_polar_fallback,
    houses_ex2_with_polar_fallback_ex,
)

# The epoch-dependent band below reads the threshold off the backend's own polar
# diagnostic. Only libephemeris publishes one; swisseph raises a generic error that
# carries no latitude, so there the fallback can only fall back on the ±66 rule of
# thumb and the band between the two stays uncast. That is a real limitation of that
# backend, not something these invariants can assert away.
_NEEDS_MEASURED_THRESHOLD = pytest.mark.skipif(
    BACKEND_NAME != "libephemeris",
    reason="the polar threshold is only reported by the libephemeris backend",
)

# 2026-06-15 12:00 UT at 15E. Chosen so the Sun is well north of the equator and the
# polar circle is genuinely in play for the northern latitudes swept below.
_JD = 2461206.0
_LON = 15.0

# Straddles the threshold deliberately: the polar circle sits near 66.56 deg for this
# epoch's obliquity, so 66.5 is outside it and 66.6 is inside. A fallback that clamps
# would leave every value from 66.6 up identical to the one at the limit, which is
# exactly what the sweep is shaped to catch.
_LATITUDES = [65.0, 66.0, 66.4, 66.5, 66.6, 67.0, 70.0, 75.0, 80.0, 85.0, 89.9]

# Placidus and Koch are undefined inside the circle; Whole Sign, Regiomontanus,
# Campanus and Porphyry are defined everywhere. Mixing both kinds is the point: the
# Ascendant must not depend on which one was asked for.
_HOUSE_SYSTEMS = [b"P", b"K", b"W", b"R", b"C", b"O"]

_POLAR_SUBJECT = dict(
    lng=15.6467, tz_str="Arctic/Longyearbyen",
    city="Longyearbyen", nation="NO",
    online=False, suppress_geonames_warning=True,
)


class TestAscendantIsIndependentOfHouseSystem:
    """The Ascendant is a horizon intersection, so no house system may move it.

    This is the invariant that the previous clamped-retry behaviour broke, and it
    breaks LOUDLY: at 89.9N the correct Ascendant differs from the clamped one by
    several degrees. Comparing the systems against each other rather than against a
    stored number means the test keeps its meaning across ephemeris updates.
    """

    @pytest.mark.parametrize("latitude", _LATITUDES)
    def test_all_house_systems_agree_on_the_ascendant(self, latitude):
        with ephemeris_session() as iflag:
            ascendants = {
                hsys: houses_ex2_with_polar_fallback(_JD, latitude, _LON, hsys, iflag)[1][0]
                for hsys in _HOUSE_SYSTEMS
            }
        spread = max(ascendants.values()) - min(ascendants.values())
        assert spread < 1e-6, f"Ascendant varies by house system at {latitude}N: {ascendants}"

    def test_the_ascendant_keeps_moving_past_the_polar_circle(self):
        """The sweep must be strictly monotonic, with no plateau.

        A clamped fallback does not produce a wrong-but-varying Ascendant; it
        produces the SAME value for every latitude beyond the threshold. Requiring
        each step to differ from the last is therefore the direct test for it, and
        it is stronger than any single-latitude comparison: one frozen pair fails.
        """
        with ephemeris_session() as iflag:
            ascendants = [
                houses_ex2_with_polar_fallback(_JD, lat, _LON, b"P", iflag)[1][0]
                for lat in _LATITUDES
            ]
        for lower, upper, lat_lo, lat_hi in zip(
            ascendants, ascendants[1:], _LATITUDES, _LATITUDES[1:]
        ):
            assert lower != upper, f"Ascendant frozen between {lat_lo}N and {lat_hi}N"
        # Rising latitude drives the Ascendant toward the equinox point here; the
        # direction is incidental, the absence of a plateau is the assertion.
        assert ascendants == sorted(ascendants, reverse=True)


class TestAnglesDoNotDependOnLatitude:
    """The MC is a meridian intersection and does not depend on latitude at all.

    Recorded so that nobody "corrects" a non-defect: seeing the MC identical across a
    polar sweep looks like the freezing bug the Ascendant had, but here it is the
    correct answer, and a change that made the MC vary with latitude would be a
    regression rather than a fix.
    """

    def test_mc_and_armc_are_constant_across_the_polar_sweep(self):
        with ephemeris_session() as iflag:
            rows = [
                houses_ex2_with_polar_fallback(_JD, lat, _LON, b"P", iflag)[1]
                for lat in _LATITUDES
            ]
        mcs = {round(ascmc[1], 9) for ascmc in rows}
        armcs = {round(ascmc[2], 9) for ascmc in rows}
        assert len(mcs) == 1, f"MC varied with latitude: {mcs}"
        assert len(armcs) == 1, f"ARMC varied with latitude: {armcs}"


class TestFirstCuspEqualsTheAscendant:
    """A quadrant chart's first cusp IS the Ascendant, at every latitude.

    This is the permanent guard against the variant that was considered and
    rejected: computing the cusps at a clamped latitude while correcting only the
    angles afterwards. That approach yields a chart whose first house does not start
    at its own Ascendant — internally inconsistent in a way no consumer could detect
    from the outputs alone. Porphyry preserves the identity because it trisects the
    quadrants the angles already define, which is why it is the substitute.
    """

    def test_placidus_first_house_starts_at_the_ascendant_deep_inside_the_circle(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Polar Placidus", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier="P", **_POLAR_SUBJECT,
        )
        assert subject.first_house.abs_pos == subject.ascendant.abs_pos
        # The same identity holds on the meridian axis.
        assert subject.tenth_house.abs_pos == subject.medium_coeli.abs_pos

    def test_whole_sign_first_house_is_allowed_to_differ(self):
        """The control: the identity is a property of quadrant systems only.

        Whole Sign starts each house at 0 deg of a sign, so its first cusp normally
        does NOT sit on the Ascendant. Without this case, an implementation that
        forced cusp[0] = ASC for every system would satisfy the test above while
        corrupting Whole Sign charts.
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Polar Whole Sign", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier="W", **_POLAR_SUBJECT,
        )
        assert subject.first_house.abs_pos != subject.ascendant.abs_pos
        assert subject.first_house.abs_pos % 30 == 0


class TestPolarFallbackIsDeclared:
    """A degraded chart must say so in its data, not only in a log line.

    A WARNING is invisible to anything consuming the model — an API response, a
    stored chart, a rendered wheel. The record is what lets a consumer tell a
    substituted chart from an exact one, so its presence (and its absence outside
    the circle) is part of the contract.
    """

    def test_substitution_is_recorded_inside_the_circle(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Declared", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier="P", **_POLAR_SUBJECT,
        )
        assert len(subject.polar_house_fallbacks) == 1
        fallback = subject.polar_house_fallbacks[0]
        assert fallback.strategy == "substitute_system"
        assert fallback.requested_house_system_identifier == "P"
        assert fallback.used_house_system_identifier == "O"
        # The observer did not move: that is the whole point of the strategy.
        assert fallback.latitude == fallback.used_latitude == 78.2232
        assert fallback.affects == ["house_cusps"]

    def test_no_record_outside_the_circle(self):
        """60N is a high latitude that needs no fallback at all.

        Guards the other direction: a record attached to every polar-ish chart would
        be noise, and would make the field useless for telling the two cases apart.
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Undeclared", 1995, 1, 15, 2, 0,
            lat=60.0, houses_system_identifier="P", **_POLAR_SUBJECT,
        )
        assert subject.polar_house_fallbacks == []

    def test_no_record_for_a_system_defined_everywhere(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Whole Sign Polar", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier="W", **_POLAR_SUBJECT,
        )
        assert subject.polar_house_fallbacks == []

    def test_the_gauquelin_clamp_is_recorded_too(self):
        """The 36-sector ring cannot be substituted, so it clamps — and must say so.

        The ring is strongly latitude-dependent, so a clamp from 78N to the limit
        displaces sectors by close to a full 10-degree sector width. Whole Sign
        needs no fallback of its own, which isolates the Gauquelin record: the
        list holds exactly one entry and it is the clamp.
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Gauquelin Polar", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier="W",
            calculate_gauquelin=True, **_POLAR_SUBJECT,
        )
        assert len(subject.polar_house_fallbacks) == 1
        fallback = subject.polar_house_fallbacks[0]
        assert fallback.strategy == "clamp_latitude"
        assert fallback.requested_house_system_identifier == "G"
        assert fallback.used_house_system_identifier == "G"
        # The observer DID move here — which is precisely why it has to be declared.
        assert fallback.used_latitude != fallback.latitude == 78.2232
        assert fallback.affects == ["house_cusps", "angles"]

    def test_both_degradations_survive_together(self):
        """Placidus substitutes and Gauquelin clamps in the SAME chart.

        This is why the field is a list. Appending one over the other, or keeping
        a single value, would silently drop whichever came second.
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Both", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier="P",
            calculate_gauquelin=True, **_POLAR_SUBJECT,
        )
        assert [f.strategy for f in subject.polar_house_fallbacks] == [
            "substitute_system",
            "clamp_latitude",
        ]


@_NEEDS_MEASURED_THRESHOLD
class TestThePolarLimitMovesWithTheEpoch:
    """The polar circle is 90 deg minus the obliquity, and obliquity is not constant.

    It was about 24.15 deg around 3000 BCE, putting the limit near 65.85 deg — below
    the 66 deg rule of thumb. A fallback gated on that constant would refuse to fire
    in the band between the two and hard-fail the chart, which is the opposite of
    what the fallback exists for. The gate must therefore follow the threshold the
    backend actually measured.
    """

    # 3000 BCE and 4713 BCE. The obliquity is high enough at both that the limit
    # falls below 66 deg, so the band exists at all.
    _ANTIQUITY = [(625674.0, 65.99), (0.0, 65.9)]

    @pytest.mark.parametrize("jd,latitude", _ANTIQUITY)
    def test_a_quadrant_system_still_substitutes_below_66_degrees(self, jd, latitude):
        with ephemeris_session():
            cusps, ascmc, _, _, fallback = houses_ex2_with_polar_fallback_ex(
                jd, latitude, _LON, b"P", 0
            )
        assert fallback is not None
        assert fallback.strategy == "substitute_system"
        # Substitution keeps the real latitude, so the Ascendant stays exact and
        # the first cusp is still the Ascendant.
        assert fallback.used_latitude == latitude
        assert cusps[0] == pytest.approx(ascmc[0], abs=1e-9)

    @pytest.mark.parametrize("jd,latitude", _ANTIQUITY)
    def test_the_clamp_lands_inside_the_measured_threshold(self, jd, latitude):
        """Gauquelin cannot substitute, so it must clamp to a latitude that WORKS.

        Clamping to a fixed 66 deg would still be outside the limit in these
        epochs, and the retry would fail exactly as the first call did.
        """
        with ephemeris_session():
            cusps, _, _, _, fallback = houses_ex2_with_polar_fallback_ex(
                jd, latitude, _LON, b"G", 0, polar_strategy="clamp_latitude"
            )
        assert fallback is not None
        assert fallback.strategy == "clamp_latitude"
        assert fallback.threshold is not None
        assert abs(fallback.used_latitude) < fallback.threshold < 66.0
        assert len(cusps) == 36
