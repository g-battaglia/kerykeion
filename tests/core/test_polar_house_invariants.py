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

import io
import logging

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_backend import (
    BACKEND_NAME,
    ephe,
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

    def test_gauquelin_points_use_the_same_fallback_latitude_as_the_ring(self):
        """A clamped ring cannot coexist with sectors cast at the real latitude."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Gauquelin Consistency", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier="W",
            calculate_gauquelin=True, **_POLAR_SUBJECT,
        )
        fallback = next(
            record
            for record in subject.polar_house_fallbacks
            if record.requested_house_system_identifier == "G"
        )

        with ephemeris_session():
            at_fallback = ephe.gauquelin_sector(
                subject.julian_day,
                ephe.SUN,
                0,
                [subject.lng, fallback.used_latitude, 0.0],
            )
            at_real_latitude = ephe.gauquelin_sector(
                subject.julian_day,
                ephe.SUN,
                0,
                [subject.lng, subject.lat, 0.0],
            )

        assert subject.sun.gauquelin_sector == pytest.approx(at_fallback, abs=5e-5)
        assert abs(subject.sun.gauquelin_sector - at_real_latitude) > 0.01

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


class TestTheLogAgreesWithWhatHappened:
    """A substitution must not announce a clamp that never took place.

    The helper that caps a latitude logs while doing it, so calling it merely to
    ASK whether a latitude is inside the circle emits "Latitude capped at 66°"
    even on the path that goes on to compute at the real latitude. Anyone reading
    the log while debugging a polar chart would then see a cap that the fallback
    record and the warning both deny.
    """

    @staticmethod
    def _logs_for(hsys: bytes) -> str:
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("kerykeion")
        previous_level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        try:
            with ephemeris_session():
                houses_ex2_with_polar_fallback_ex(_JD, 78.0, _LON, hsys, 0)
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous_level)
        return stream.getvalue().lower()

    def test_substitution_does_not_claim_a_cap(self):
        assert "capped" not in self._logs_for(b"P")

    def test_the_clamp_path_still_says_so(self):
        """The control: where a latitude really is capped, the log must show it."""
        assert "capped" in self._logs_for(b"G")


class TestTheChartIsLabelledWithTheSystemItUsed:
    """A substituted chart must not render as the system that was requested.

    The fallback record is structured data that renderers do not read. The SVG
    legend, the report table and the serialized context all take the house system
    from `houses_system_identifier` / `houses_system_name`, so leaving the request
    in those fields prints "Placidus" over Porphyry cusps — the same silence the
    substitution exists to end, just moved one layer out.

    The request is not lost: it survives on the fallback record, which is where a
    consumer that cares about the distinction should look.
    """

    @staticmethod
    def _subject(hsys: str, latitude: float):
        return AstrologicalSubjectFactory.from_birth_data(
            "Labelled", 1995, 1, 15, 2, 0,
            lat=latitude, houses_system_identifier=hsys, **_POLAR_SUBJECT,
        )

    def test_a_substituted_chart_names_the_substitute(self):
        """Through the EFFECTIVE view, which is what rendering reads.

        The requested field keeps the request on purpose — see
        :class:`TestASubstitutionDoesNotBecomeASetting` for why touching it
        breaks relocation.
        """
        subject = self._subject("P", 78.2232)
        assert subject.effective_houses_system_identifier == "O"
        assert subject.effective_houses_system_name == "Porphyry"

    def test_the_request_survives_on_the_record(self):
        record = self._subject("P", 78.2232).polar_house_fallbacks[0]
        assert record.requested_house_system_identifier == "P"
        assert record.requested_house_system_name == "Placidus"

    def test_an_unsubstituted_chart_keeps_its_own_name(self):
        """The control: relabelling must not leak outside the fallback."""
        subject = self._subject("P", 45.0)
        assert subject.polar_house_fallbacks == []
        assert subject.houses_system_identifier == "P"
        assert subject.houses_system_name == "Placidus"

    def test_a_system_defined_everywhere_is_untouched_at_the_pole(self):
        subject = self._subject("W", 78.2232)
        assert subject.polar_house_fallbacks == []
        assert subject.houses_system_identifier == "W"

    def test_the_rendered_chart_names_the_substitute_too(self):
        """The subject-level assertions above are not enough on their own.

        The SVG baseline cannot catch this: `compare_chart_svg` compares numeric
        tokens with a tolerance, so a legend reading "Placidus" over Porphyry
        cusps passes it. The mislabelling lived in the rendered output for exactly
        that reason, and it is the rendered output a reader trusts.
        """
        from kerykeion import ChartDataFactory
        from kerykeion.charts.drawer import ChartDrawer

        svg = ChartDrawer(
            ChartDataFactory.create_natal_chart_data(self._subject("P", 78.2232))
        ).generate_svg_string()
        assert "Domification: Porphyry" in svg
        assert "Domification: Placidus" not in svg


class TestASubstitutionDoesNotBecomeASetting:
    """The substitution belongs to a latitude, not to the subject.

    `houses_system_identifier` is fed back in when a chart is relocated or a
    return is cast, so overwriting it with the substitute would carry a polar
    workaround to places where the requested system is perfectly well defined —
    and silently, because the recast produces no fallback record of its own to
    explain the change. The requested system therefore stays in that field and
    the substitute is exposed separately, for rendering.
    """

    @staticmethod
    def _polar_placidus():
        return AstrologicalSubjectFactory.from_birth_data(
            "Polar Placidus", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier="P", **_POLAR_SUBJECT,
        )

    def test_the_request_is_what_survives_on_the_subject(self):
        subject = self._polar_placidus()
        assert subject.houses_system_identifier == "P"
        assert subject.effective_houses_system_identifier == "O"
        assert subject.effective_houses_system_name == "Porphyry"

    def test_relocating_away_from_the_pole_restores_the_requested_system(self):
        """Rome can cast Placidus, so a chart relocated there must get Placidus."""
        from kerykeion.relocated_chart.factory import RelocatedChartFactory

        relocated = RelocatedChartFactory.relocate(
            self._polar_placidus(),
            new_lat=41.9028, new_lng=12.4964, new_tz_str="Europe/Rome",
            new_city="Rome", new_nation="IT",
        )
        assert relocated.houses_system_identifier == "P"
        assert relocated.effective_houses_system_identifier == "P"
        assert relocated.polar_house_fallbacks == []

    def test_a_chart_that_never_substituted_reports_one_system(self):
        """The control: the two views agree wherever nothing degraded."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Temperate", 1995, 1, 15, 2, 0,
            lat=45.0, houses_system_identifier="P", **_POLAR_SUBJECT,
        )
        assert subject.houses_system_identifier == subject.effective_houses_system_identifier == "P"
        assert subject.houses_system_name == subject.effective_houses_system_name


class TestTheEffectiveViewNamesTheMainHouses:
    """The effective view must describe THIS chart's houses, and only those.

    A chart can carry more than one fallback record: asking for Gauquelin
    sectors adds an ancillary one for the 36-sector ring, which degrades on its
    own and lists "house_cusps" like any other. Matching on the requested
    identifier is what tells them apart — without it a polar Whole Sign chart,
    whose own cusps never degraded, would report itself as Gauquelin sectors.
    """

    @staticmethod
    def _polar(hsys: str, gauquelin: bool):
        return AstrologicalSubjectFactory.from_birth_data(
            "Polar", 1995, 1, 15, 2, 0,
            lat=78.2232, houses_system_identifier=hsys,
            calculate_gauquelin=gauquelin, **_POLAR_SUBJECT,
        )

    def test_an_ancillary_gauquelin_clamp_does_not_rename_the_chart(self):
        subject = self._polar("W", gauquelin=True)
        assert subject.polar_house_fallbacks, "precondition: the sector ring did clamp"
        assert subject.effective_houses_system_identifier == "W"

    def test_the_main_substitution_is_still_found_alongside_it(self):
        """Two records present; the one describing the main houses must win."""
        subject = self._polar("P", gauquelin=True)
        assert len(subject.polar_house_fallbacks) == 2
        assert subject.effective_houses_system_identifier == "O"

    def test_the_report_cannot_contradict_itself(self):
        """The settings row and the houses table title read the same source."""
        from kerykeion.report.generator import ReportGenerator

        report = ReportGenerator(self._polar("P", gauquelin=False)).generate_report()
        assert "Houses (Porphyry)" in report
        assert "Houses (Placidus)" not in report


class TestACompositeCannotMixTwoDivisions:
    """Matching REQUESTS is not enough to make two charts composable.

    Inside the polar circle a chart's cusps may have come from a substitute, so
    two subjects that both asked for Placidus can hold Porphyry cusps and
    Placidus cusps. A midpoint of two different divisions is not a composite in
    either of them, and the factory already refuses mismatched systems — this is
    the same refusal applied to what the houses actually are.
    """

    @staticmethod
    def _subject(name: str, lat: float, **over):
        base = dict(
            lng=15.6467, tz_str="Arctic/Longyearbyen", city="L", nation="NO",
            online=False, suppress_geonames_warning=True,
        )
        base.update(over)
        return AstrologicalSubjectFactory.from_birth_data(
            name, 1995, 1, 15, 2, 0, lat=lat, houses_system_identifier="P", **base
        )

    def test_a_substituted_parent_cannot_compose_with_an_intact_one(self):
        from kerykeion.composite_subject.factory import CompositeSubjectFactory
        from kerykeion.schemas.exceptions import KerykeionException

        polar = self._subject("Polar", 78.2232)
        temperate = self._subject(
            "Temperate", 41.9, lng=12.5, tz_str="Europe/Rome", city="Rome", nation="IT"
        )
        assert polar.houses_system_identifier == temperate.houses_system_identifier, (
            "precondition: the REQUESTS match, so only the effective check can catch this"
        )
        with pytest.raises(KerykeionException, match="same houses system"):
            CompositeSubjectFactory(polar, temperate).get_midpoint_composite_subject_model()

    def test_two_substituted_parents_compose_and_say_so(self):
        """The composite reports Porphyry cusps without forgetting Placidus was asked for.

        Both facts have to survive, and in the right fields. Overwriting the
        REQUEST with the substitute — which is what this test used to pin — makes
        the relationship look as though Porphyry were its setting, so relocating
        it to a temperate latitude would keep dividing by Porphyry with nothing
        left to say why. The requested pair therefore stays untouched and the
        parents' own substitution records travel with the composite, which is
        what the effective view reads.
        """
        from kerykeion.composite_subject.factory import CompositeSubjectFactory

        composite = CompositeSubjectFactory(
            self._subject("Polar A", 78.2232), self._subject("Polar B", 79.0)
        ).get_midpoint_composite_subject_model()

        assert composite.houses_system_identifier == "P"
        assert composite.houses_system_name == "Placidus"
        assert composite.effective_houses_system_identifier == "O"
        assert composite.effective_houses_system_name == "Porphyry"

        # One record per parent: a midpoint composite has no latitude of its own
        # (verified below), so it cannot author a substitution — only inherit the
        # two that produced the cusps it averaged.
        assert composite.lat is None
        assert [fallback.latitude for fallback in composite.polar_house_fallbacks] == [78.2232, 79.0]
        assert {fallback.used_house_system_identifier for fallback in composite.polar_house_fallbacks} == {"O"}

    def test_a_composite_of_intact_parents_records_no_substitution(self):
        """The negative control: inheriting records must not become inventing them."""
        from kerykeion.composite_subject.factory import CompositeSubjectFactory

        composite = CompositeSubjectFactory(
            self._subject("Temperate A", 41.9, lng=12.5, tz_str="Europe/Rome", city="Rome", nation="IT"),
            self._subject("Temperate B", 45.46, lng=9.19, tz_str="Europe/Rome", city="Milan", nation="IT"),
        ).get_midpoint_composite_subject_model()

        assert composite.houses_system_identifier == "P"
        assert composite.effective_houses_system_identifier == "P"
        assert composite.polar_house_fallbacks == []

    def test_the_gauquelin_record_does_not_travel_to_the_composite(self):
        """A midpoint composite averages no sectors, so it may claim no sector clamp.

        A polar parent with Gauquelin enabled carries a second, ancillary record
        for the 36-sector ring. Copying a parent's fallbacks wholesale would
        attach that clamp to a chart with no ``gauquelin_sector_cusps`` at all —
        and, because the ancillary record asks for "G", it would also sit in the
        list where a future reader could mistake it for the one that explains
        these cusps.
        """
        from kerykeion.composite_subject.factory import CompositeSubjectFactory

        parents = [self._subject("Polar A", 78.2232, calculate_gauquelin=True),
                   self._subject("Polar B", 79.0, calculate_gauquelin=True)]
        assert any(
            fallback.requested_house_system_identifier == "G"
            for parent in parents
            for fallback in parent.polar_house_fallbacks
        ), "precondition: the parents really do carry an ancillary Gauquelin record"

        composite = CompositeSubjectFactory(*parents).get_midpoint_composite_subject_model()

        assert composite.gauquelin_sector_cusps is None
        assert [fallback.requested_house_system_identifier for fallback in composite.polar_house_fallbacks] == ["P", "P"]

    def test_davison_accepts_parents_with_different_effective_systems(self):
        """Davison recasts its houses and does not average the parents' cusps."""
        from kerykeion.composite_subject.factory import CompositeSubjectFactory

        polar = self._subject("Polar", 78.2232)
        temperate = self._subject("Temperate", 41.9, lng=12.5, tz_str="Europe/Rome", city="Rome", nation="IT")

        davison = CompositeSubjectFactory(polar, temperate).get_davison_composite_subject_model()

        assert davison.lat == pytest.approx((polar.lat + temperate.lat) / 2.0)
        assert davison.houses_system_identifier == "P"
        assert davison.effective_houses_system_identifier == "P"
        assert davison.polar_house_fallbacks == []

    def test_temperate_davison_of_two_polar_parents_restores_the_request(self):
        """Matching parent fallbacks must not become the Davison chart setting."""
        from kerykeion.composite_subject.factory import CompositeSubjectFactory

        north = self._subject("North Polar", 78.2232)
        south = self._subject("South Polar", -78.2232)
        assert north.effective_houses_system_identifier == "O"
        assert south.effective_houses_system_identifier == "O"

        davison = CompositeSubjectFactory(north, south).get_davison_composite_subject_model()

        assert davison.lat == pytest.approx(0.0)
        assert davison.houses_system_identifier == "P"
        assert davison.effective_houses_system_identifier == "P"
        assert davison.polar_house_fallbacks == []

    def test_polar_davison_records_its_own_fallback(self):
        """A polar midpoint may substitute, but the new cast must say that it did."""
        from kerykeion.composite_subject.factory import CompositeSubjectFactory

        davison = CompositeSubjectFactory(
            self._subject("Polar A", 78.2232),
            self._subject("Polar B", 79.0),
        ).get_davison_composite_subject_model()

        assert davison.houses_system_identifier == "P"
        assert davison.effective_houses_system_identifier == "O"
        main_fallback = next(
            fallback for fallback in davison.polar_house_fallbacks if fallback.requested_house_system_identifier == "P"
        )
        assert main_fallback.used_house_system_identifier == "O"


class TestDualWheelEffectiveHouseLabels:
    """A dual wheel must describe both house divisions when fallbacks differ."""

    @staticmethod
    def _subjects():
        polar = AstrologicalSubjectFactory.from_birth_data(
            "Polar",
            1995,
            1,
            15,
            2,
            0,
            lat=78.2232,
            houses_system_identifier="P",
            **_POLAR_SUBJECT,
        )
        temperate = AstrologicalSubjectFactory.from_birth_data(
            "Temperate",
            1995,
            1,
            15,
            2,
            0,
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            city="Rome",
            nation="IT",
            online=False,
            suppress_geonames_warning=True,
            houses_system_identifier="P",
        )
        return polar, temperate

    def test_synastry_labels_both_effective_systems(self):
        from kerykeion import ChartDataFactory
        from kerykeion.charts.drawer import ChartDrawer

        polar, temperate = self._subjects()
        svg = ChartDrawer(
            ChartDataFactory.create_synastry_chart_data(polar, temperate)
        ).generate_svg_string()

        assert "Porphyry / Placidus Houses" in svg

    def test_transit_labels_both_effective_systems(self):
        from kerykeion import ChartDataFactory
        from kerykeion.charts.drawer import ChartDrawer

        polar, temperate = self._subjects()
        svg = ChartDrawer(
            ChartDataFactory.create_transit_chart_data(polar, temperate)
        ).generate_svg_string()

        assert "Domification: Porphyry / Placidus" in svg
