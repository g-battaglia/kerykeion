# -*- coding: utf-8 -*-
"""Regressions for the civil-time layer that positions are anchored to.

Every chart starts as a wall-clock reading in an IANA zone, so an offset that is
wrong by an hour moves the Ascendant by roughly 15 degrees — a larger error than
any ephemeris question these tests are usually worried about. The cases here pin
the three ways that layer can silently go wrong:

* the offset for an instant OUTSIDE the tz database's recorded transitions, which
  must come from the zone's ongoing rule rather than freezing at the last one;
* the offset for a historical instant BEFORE a zone adopted standard time, which
  must come from that zone's own mean-time record;
* the resolution of a wall time that a transition makes non-unique or impossible.

They are deliberately assertions about offsets and instants rather than about
positions: a position golden would also move if the ephemeris changed, which
would make the diagnosis ambiguous.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import zoneinfo
from zoneinfo import ZoneInfo

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.utilities import is_ambiguous, is_nonexistent, localize_naive, safe_timezone

_ROME = ZoneInfo("Europe/Rome")


# ---------------------------------------------------------------------------
# Offsets beyond the recorded transition table
# ---------------------------------------------------------------------------


class TestOffsetsBeyondTheTransitionTable:
    """A zone's rule must keep applying past the last tabulated transition.

    A transition table that stops in the late 2030s and then holds the final
    offset constant does not merely lose DST: it holds the WRONG one. Northern
    zones freeze on standard time and southern zones freeze on summer time, so
    the sign of the error flips with the hemisphere and no single correction
    could paper over it. Both hemispheres are asserted for that reason.
    """

    @pytest.mark.parametrize(
        "tz_name,moment,expected_offset_hours",
        [
            # June in Rome is summer time; a frozen table would report +01:00.
            ("Europe/Rome", datetime(2040, 6, 15, 12, 0), 2),
            # July in Sydney is WINTER; a frozen table would report +11:00.
            ("Australia/Sydney", datetime(2040, 7, 15, 12, 0), 10),
            # Far outside any plausible table, the ongoing rule still applies.
            ("Europe/Rome", datetime(5000, 6, 15, 12, 0), 2),
        ],
    )
    def test_summer_and_winter_rules_extrapolate(self, tz_name, moment, expected_offset_hours):
        tz = ZoneInfo(tz_name)
        assert moment.replace(tzinfo=tz).utcoffset() == timedelta(hours=expected_offset_hours)

    def test_future_subject_uses_the_extrapolated_offset(self):
        """The offset reaches the chart, not just the timezone object.

        Asserted through the UTC instant rather than through a position: it is the
        conversion that carries the error, and pinning it keeps this test
        diagnostic if an ephemeris change ever moves the angles.
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Future Rome", 2040, 6, 15, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
        )
        assert subject.iso_formatted_local_datetime == "2040-06-15T12:00:00+02:00"
        assert subject.iso_formatted_utc_datetime == "2040-06-15T10:00:00+00:00"

    def test_future_southern_subject_does_not_inherit_summer_time(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Future Sydney", 2040, 7, 15, 12, 0,
            lng=151.2093, lat=-33.8688, tz_str="Australia/Sydney",
            online=False, suppress_geonames_warning=True,
        )
        assert subject.iso_formatted_local_datetime == "2040-07-15T12:00:00+10:00"
        assert subject.iso_formatted_utc_datetime == "2040-07-15T02:00:00+00:00"


# ---------------------------------------------------------------------------
# The boundary where a zone adopted standard time
# ---------------------------------------------------------------------------


class TestStandardTimeAdoptionBoundary:
    """Before a zone adopted standard time it kept a local mean time.

    Rome switched on 1893-11-01. A day either side of that date must resolve to a
    different kind of offset entirely — Rome's own recorded mean time ("RMT")
    before, a whole-hour zone offset after. The gap is about 10 minutes, i.e. ~2.5
    degrees of Ascendant, so a chart for a 19th-century Italian birth is visibly
    wrong if the boundary is missed. Pinned explicitly so a future tz database
    revision that moves or drops the record is caught here rather than in a
    position golden, where the cause would be much harder to read.
    """

    def test_before_adoption_uses_local_mean_time(self):
        moment = datetime(1893, 10, 31, 12, 0, tzinfo=_ROME)
        assert moment.utcoffset() == timedelta(minutes=49, seconds=56)
        # Not a whole number of minutes: a mean time, not a zone offset. The
        # seconds are the point — a backend that rounded historical offsets to
        # the minute would report +00:50 and land 4 s off.
        assert moment.utcoffset().total_seconds() % 60 != 0

    def test_after_adoption_uses_the_whole_hour_zone_offset(self):
        moment = datetime(1893, 11, 2, 12, 0, tzinfo=_ROME)
        assert moment.utcoffset() == timedelta(hours=1)

    def test_the_two_sides_really_differ(self):
        """Guards against both dates collapsing onto one offset.

        If a future tz database dropped the pre-adoption record, both assertions
        above could be rewritten to pass against a single offset; this one cannot.
        """
        before = datetime(1893, 10, 31, 12, 0, tzinfo=_ROME).utcoffset()
        after = datetime(1893, 11, 2, 12, 0, tzinfo=_ROME).utcoffset()
        assert after - before == timedelta(minutes=10, seconds=4)

    def test_subject_before_adoption_carries_the_recorded_offset_whole(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Pre-adoption Rome", 1893, 10, 31, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
        )
        # The RMT record reaches the chart with its SECONDS component intact. An
        # offset rounded to the whole minute would render as '+00:50' and shift
        # the instant by 4 s; carrying :56 is the difference between the two.
        assert subject.iso_formatted_local_datetime == "1893-10-31T12:00:00+00:49:56"
        assert subject.iso_formatted_utc_datetime == "1893-10-31T11:10:04+00:00"

    def test_a_named_record_is_not_overridden_by_the_birth_longitude(self):
        """RMT is data, so it wins over the sundial reading of the birth place.

        1893 Rome is 3 s away from its own longitude-derived mean time (2999 s vs
        the record's 2996 s), which would make this indistinguishable from the
        LMT branch on Rome itself. Varying the longitude across the whole zone is
        what separates them: a chart that still reports +00:49:56 at lng=18 is
        reading the tz database record, not the meridian.
        """
        offsets = {
            AstrologicalSubjectFactory.from_birth_data(
                "Pre-adoption", 1893, 10, 31, 12, 0,
                lng=lng, lat=41.9028, tz_str="Europe/Rome",
                online=False, suppress_geonames_warning=True,
            ).iso_formatted_local_datetime[-9:]
            for lng in (12.4964, 0.0, 18.0, -8.0)
        }
        assert offsets == {"+00:49:56"}


# ---------------------------------------------------------------------------
# Births before the zone kept any recorded civil time
# ---------------------------------------------------------------------------


class TestSyntheticLmtRecordUsesTheBirthMeridian:
    """The tz database's opening "LMT" record is replaced by the birth meridian.

    Every zone opens with a synthetic record named LMT whose offset is the mean
    solar time of the zone's REFERENCE point. It is not an observation — it is
    what the database says when it has nothing recorded — and a zone can be
    thousands of kilometres wide, so for a 1750 birth it is the wrong meridian by
    however far the birth place sits from the reference city. The factory
    substitutes the birth longitude's own mean time there.

    The discriminator is longitude-dependence, and only longitude-dependence: an
    assertion on a single offset cannot tell this branch from the zone record it
    replaces, because for the reference city itself the two agree to within a few
    seconds (Rome: 2999 s vs 2996 s). Deleting the branch entirely must turn
    these tests red.
    """

    def test_the_offset_follows_the_birth_longitude(self):
        for lng, expected in ((12.4964, "+00:49:59"), (0.0, "+00:00"), (18.0, "+01:12")):
            subject = AstrologicalSubjectFactory.from_birth_data(
                "Pre-record", 1750, 6, 1, 12, 0,
                lng=lng, lat=41.9028, tz_str="Europe/Rome",
                online=False, suppress_geonames_warning=True,
            )
            # Exactly round(lng / 15 * 3600) seconds: 15 deg = 1 h, east ahead.
            assert subject.iso_formatted_local_datetime.endswith(expected), lng

    def test_the_zone_reference_meridian_does_not_leak_in(self):
        """A birth 5.5 deg east of Rome must not be cast on Rome's meridian.

        Europe/Rome's LMT record is +00:49:56 for every longitude in the zone.
        Reading it here instead of the birth meridian would move the instant by
        1324 s, roughly 5.5 degrees of Ascendant.
        """
        subject = AstrologicalSubjectFactory.from_birth_data(
            "East of Rome", 1750, 6, 1, 12, 0,
            lng=18.0, lat=41.9028, tz_str="Europe/Rome",
            online=False, suppress_geonames_warning=True,
        )
        assert subject.iso_formatted_utc_datetime == "1750-06-01T10:48:00+00:00"

    def test_iso_utc_entry_point_agrees_with_from_birth_data(self):
        """Both entry points must apply the same predicate.

        from_iso_utc_time re-derives the wall time from the UTC instant and hands
        the offset down explicitly; if its LMT test ever diverged from
        _calculate_time_conversions', the instant would be interpreted twice and
        shift by the longitude delta.
        """
        from_iso = AstrologicalSubjectFactory.from_iso_utc_time(
            "Round trip", "1750-06-01T10:48:00Z",
            lng=18.0, lat=41.9028, tz_str="Europe/Rome",
            city="Nowhere", nation="IT", online=False,
        )
        assert from_iso.iso_formatted_local_datetime == "1750-06-01T12:00:00+01:12"
        assert from_iso.iso_formatted_utc_datetime == "1750-06-01T10:48:00+00:00"


# ---------------------------------------------------------------------------
# Classifying and resolving wall times at a transition
# ---------------------------------------------------------------------------


class TestTransitionClassification:
    """`is_nonexistent` and `is_ambiguous` must not be interchangeable.

    Both conditions present identically at first glance — two readings of the wall
    time with two different offsets — so the only thing separating them is that a
    non-existent time does not round-trip through UTC. Getting this backwards
    produces an error message telling the user to disambiguate a time that has no
    valid reading at all.
    """

    GAPS = [
        ("Europe/Rome", datetime(2026, 3, 29, 2, 30)),
        ("America/New_York", datetime(2023, 3, 12, 2, 30)),
        ("Australia/Sydney", datetime(2026, 10, 4, 2, 30)),
    ]
    FOLDS = [
        ("Europe/Rome", datetime(2026, 10, 25, 2, 30)),
        ("America/New_York", datetime(2023, 11, 5, 1, 30)),
        ("Australia/Sydney", datetime(2026, 4, 5, 2, 30)),
    ]

    @pytest.mark.parametrize("tz_name,naive", GAPS)
    def test_gap_is_nonexistent_and_not_ambiguous(self, tz_name, naive):
        tz = ZoneInfo(tz_name)
        assert is_nonexistent(naive, tz) is True
        assert is_ambiguous(naive, tz) is False

    @pytest.mark.parametrize("tz_name,naive", FOLDS)
    def test_fold_is_ambiguous_and_not_nonexistent(self, tz_name, naive):
        tz = ZoneInfo(tz_name)
        assert is_ambiguous(naive, tz) is True
        assert is_nonexistent(naive, tz) is False

    def test_an_ordinary_wall_time_is_neither(self):
        """The control case: away from a transition both predicates are False.

        Without it, an implementation that answered True unconditionally would
        satisfy one of the two parametrized sets above.
        """
        ordinary = datetime(2026, 6, 15, 2, 30)
        assert is_ambiguous(ordinary, _ROME) is False
        assert is_nonexistent(ordinary, _ROME) is False

    def test_new_york_0230_on_fall_back_day_is_not_ambiguous(self):
        """The fold is 01:00-02:00, so 02:30 that day is an ordinary wall time.

        Recorded because an earlier generation of these tests used exactly this
        instant as its "ambiguous" case; anything asserted against it was vacuous.
        """
        tz = ZoneInfo("America/New_York")
        assert is_ambiguous(datetime(2023, 11, 5, 2, 30), tz) is False
        assert is_nonexistent(datetime(2023, 11, 5, 2, 30), tz) is False


class TestIsDstFallsBackToTheOffset:
    """When the zone flags neither reading as DST, the larger offset wins.

    This is the fallback arm of the rule, not the whole of it: the zone's own
    `dst()` is consulted first, and only a wall time whose two readings carry the
    same flag reaches the clock comparison. See
    :class:`TestIsDstFollowsTheZoneNotTheClock` for the arm that fires when the
    zone does distinguish them.

    The fallback is stated in terms of the offset, not of a fixed fold index,
    because the correspondence between the two INVERTS between a fold and a gap.
    It is also why zones with negative DST resolve correctly: there, standard time
    is the summer reading, and following the clock rather than the label gives the
    right answer without special-casing the zone.
    """

    @pytest.mark.parametrize(
        "tz_name,naive",
        TestTransitionClassification.FOLDS + TestTransitionClassification.GAPS,
    )
    def test_true_takes_the_larger_offset(self, tz_name, naive):
        tz = ZoneInfo(tz_name)
        larger = localize_naive(naive, tz, is_dst=True).utcoffset()
        smaller = localize_naive(naive, tz, is_dst=False).utcoffset()
        assert larger > smaller

    @pytest.mark.parametrize("tz_name,naive", TestTransitionClassification.FOLDS)
    def test_the_two_readings_are_distinct_instants(self, tz_name, naive):
        """A fold's two readings are genuinely different moments in time.

        In a gap the two readings are also distinct instants, but neither one has
        the requested wall time, so only the fold supports this assertion.
        """
        tz = ZoneInfo(tz_name)
        dst = localize_naive(naive, tz, is_dst=True).astimezone(timezone.utc)
        std = localize_naive(naive, tz, is_dst=False).astimezone(timezone.utc)
        assert std - dst == timedelta(hours=1)
        # Both really do read back as the wall time that was asked for.
        assert dst.astimezone(tz).replace(tzinfo=None) == naive
        assert std.astimezone(tz).replace(tzinfo=None) == naive

    def test_explicit_is_dst_never_raises(self):
        """Whichever side the caller names, the question is already answered."""
        for tz_name, naive in TestTransitionClassification.FOLDS + TestTransitionClassification.GAPS:
            tz = ZoneInfo(tz_name)
            for flag in (True, False):
                assert localize_naive(naive, tz, is_dst=flag).tzinfo is tz

    def test_none_raises_and_names_the_right_condition(self):
        """Refusing to guess, and diagnosing the gap BEFORE the fold."""
        with pytest.raises(KerykeionException, match="Ambiguous time error"):
            localize_naive(datetime(2026, 10, 25, 2, 30), _ROME)
        with pytest.raises(KerykeionException, match="Non-existent time error"):
            localize_naive(datetime(2026, 3, 29, 2, 30), _ROME)

    def test_ordinary_wall_time_needs_no_disambiguation(self):
        naive = datetime(2026, 6, 15, 2, 30)
        assert localize_naive(naive, _ROME) == naive.replace(tzinfo=_ROME)


# ---------------------------------------------------------------------------
# safe_timezone
# ---------------------------------------------------------------------------


class TestSafeTimezone:
    """Every rejected key must surface as the library's own exception.

    The underlying constructor fails in three unrelated ways — a lookup miss, a
    structurally invalid key, and a non-string — and only the first is a KeyError.
    A caller guarding a public entry point with `except KerykeionException` would
    be broken by the other two, so all three are pinned. The empty string is not a
    hypothetical: a geocoding lookup can return an empty timezone id.
    """

    @pytest.mark.parametrize(
        "bad_value",
        [
            "",  # empty timezoneId from a geocoding response
            None,  # missing value passed straight through
            "Not/AZone",  # plausible but unknown key
            "/etc/localtime",  # absolute path
            "../../etc/passwd",  # traversal component
            123,  # not a string at all
        ],
    )
    def test_invalid_input_raises_kerykeion_exception(self, bad_value):
        with pytest.raises(KerykeionException, match="Unknown timezone"):
            safe_timezone(bad_value)

    def test_valid_zone_resolves(self):
        """The control case: the guard must not reject everything."""
        assert safe_timezone("Europe/Rome").key == "Europe/Rome"


class TestIsDstIsResolvedIdenticallyOnEveryHost:
    """The answer must not depend on which tz database the machine happens to ship.

    `dst()` looks like the natural way to answer "is daylight saving in effect",
    but it is not portable. Builds of the tz database disagree about how to record
    the same zone: for Ireland one encodes summer as `dst()=+1h` against a winter
    of `0`, another encodes summer as `0` against a winter of `-1h`. A rule that
    keys on the flag hands back a different hour depending on the host, which is
    the one failure mode a chart library cannot have.

    The offsets carry the same information without the encoding, so the clock is
    what decides. These tests pin that equivalence directly, by resolving the
    same instant against both databases available here.
    """

    _DUBLIN_FOLD = datetime(2026, 10, 25, 1, 30)

    @staticmethod
    def _resolve_with(tzpath, is_dst):
        """Resolve the Dublin fold against a specific tz database."""
        previous = list(zoneinfo.TZPATH)
        try:
            zoneinfo.reset_tzpath(to=tzpath)
            zone = ZoneInfo.no_cache("Europe/Dublin")
            wall = TestIsDstIsResolvedIdenticallyOnEveryHost._DUBLIN_FOLD
            return localize_naive(wall, zone, is_dst=is_dst).utcoffset()
        finally:
            zoneinfo.reset_tzpath(to=previous)

    def test_the_two_databases_really_do_disagree_about_the_flag(self):
        """Precondition. Without this the portability tests below prove nothing."""
        previous = list(zoneinfo.TZPATH)
        try:
            flags = {}
            for label, path in (("system", previous), ("package", [])):
                zoneinfo.reset_tzpath(to=path)
                zone = ZoneInfo.no_cache("Europe/Dublin")
                summer = self._DUBLIN_FOLD.replace(tzinfo=zone, fold=0)
                flags[label] = summer.dst()
        finally:
            zoneinfo.reset_tzpath(to=previous)

        if flags["system"] == flags["package"]:
            pytest.skip("this host ships one encoding only; nothing to compare")
        assert flags["system"] != flags["package"], (
            "the encodings must differ for the portability assertion to mean anything"
        )

    @pytest.mark.parametrize("is_dst", [True, False])
    def test_same_answer_from_the_system_and_packaged_databases(self, is_dst):
        system = self._resolve_with(list(zoneinfo.TZPATH), is_dst)
        package = self._resolve_with([], is_dst)
        assert system == package, (
            f"is_dst={is_dst} resolved to {system} against the system database "
            f"and {package} against the packaged one"
        )

    def test_summer_is_the_larger_offset_even_where_dst_is_recorded_negative(self):
        """Ireland keeps standard time in summer and subtracts an hour in winter.

        Whichever way the database books that, the caller asking for daylight
        saving means the summer reading, and summer is the larger offset.
        """
        dublin = ZoneInfo("Europe/Dublin")
        assert localize_naive(self._DUBLIN_FOLD, dublin, is_dst=True).utcoffset() == timedelta(hours=1)
        assert localize_naive(self._DUBLIN_FOLD, dublin, is_dst=False).utcoffset() == timedelta()

    def test_an_ordinary_fold_is_unaffected(self):
        """The control: an ordinary zone where both readings agree anyway."""
        assert localize_naive(datetime(2026, 10, 25, 2, 30), _ROME, is_dst=True).utcoffset() == timedelta(hours=2)
        assert localize_naive(datetime(2026, 10, 25, 2, 30), _ROME, is_dst=False).utcoffset() == timedelta(hours=1)


class TestAStandardOffsetChangeHasNoDaylightAnswer:
    """Not every repeated wall time is a summer-time fold.

    A zone can also repeat an hour because its STANDARD offset changed — Kyiv on
    1941-09-19 hands one reading to Moscow time and the next to Central European
    Summer Time. Modern tz data flags neither side as daylight saving, so there is
    no "is DST in effect" answer to give and the parameter does not really apply.

    The rule still has to return something, and what it returns must at least be
    deterministic and the same everywhere. This pins that, and documents the case
    so nobody later reads the result as a considered claim about daylight saving.
    """

    _KYIV_FOLD = datetime(1941, 9, 19, 23, 30)

    def test_neither_reading_claims_daylight_saving(self):
        kyiv = ZoneInfo("Europe/Kyiv")
        assert is_ambiguous(self._KYIV_FOLD, kyiv), "precondition: the hour repeats"
        sides = [self._KYIV_FOLD.replace(tzinfo=kyiv, fold=f) for f in (0, 1)]
        assert not any((side.dst() or timedelta()) > timedelta() for side in sides), (
            "if a side ever starts claiming positive DST, this case needs rethinking"
        )

    def test_the_result_is_deterministic(self):
        kyiv = ZoneInfo("Europe/Kyiv")
        assert localize_naive(self._KYIV_FOLD, kyiv, is_dst=True).utcoffset() == timedelta(hours=3)
        assert localize_naive(self._KYIV_FOLD, kyiv, is_dst=False).utcoffset() == timedelta(hours=2)


class TestElapsedTimeIsMeasuredBetweenInstants:
    """Subtracting two aware datetimes does NOT always cross to UTC first.

    When both operands carry the SAME tzinfo object, Python subtracts their
    wall-clock fields and never calls `utcoffset()`. `ZoneInfo` instances are
    cached, so two lookups of one zone return the same object and that shortcut
    is the normal case, not an edge one. Across a transition it reports the
    clock elapsed instead of the time elapsed.
    """

    def test_same_zone_object_subtraction_measures_the_clock(self):
        """Pin the language behaviour the calculation has to work around."""
        juba = ZoneInfo("Africa/Juba")
        sunrise = datetime(2000, 1, 15, 6, 30, tzinfo=juba)
        sunset = datetime(2000, 1, 15, 18, 30, tzinfo=juba)
        assert sunrise.tzinfo is sunset.tzinfo, "ZoneInfo is cached"
        assert sunrise.utcoffset() != sunset.utcoffset(), "a transition sits between them"

        assert (sunset - sunrise) == timedelta(hours=12), "wall clock"
        assert (
            sunset.astimezone(timezone.utc) - sunrise.astimezone(timezone.utc)
        ) == timedelta(hours=11), "actual elapsed time"


class TestCurrentTimeChartsDoNotDependOnTheDstEncoding:
    """`from_current_time` must land on the instant it was called at.

    It used to hand `bool(now.dst())` down as `is_dst` and let the wall time be
    re-localized from it. That boolean is not portable: where one build of the tz
    database records Ireland's summer as `dst()=+1h` against a winter of `0`,
    another records summer as `0` against a winter of `-1h`. During the repeated
    hour the two therefore disagree about which side the boolean names, and the
    chart is reconstructed an hour away from the instant it was cast at — on some
    machines only.

    The conversion already resolved the offset unambiguously, so it is passed
    down directly and no re-derivation happens at all.
    """

    @staticmethod
    def _utc_of_a_chart_cast_now():
        subject = AstrologicalSubjectFactory.from_current_time(
            "Now", lng=-6.2603, lat=53.3498, tz_str="Europe/Dublin",
            city="Dublin", nation="IE", online=False, suppress_geonames_warning=True,
        )
        return datetime.fromisoformat(subject.iso_formatted_utc_datetime)

    def test_the_chart_lands_on_the_current_instant_under_both_databases(self):
        previous = list(zoneinfo.TZPATH)
        results = {}
        try:
            for label, path in (("system", previous), ("package", [])):
                zoneinfo.reset_tzpath(to=path)
                cast_at = datetime.now(timezone.utc)
                results[label] = abs((self._utc_of_a_chart_cast_now() - cast_at).total_seconds())
        finally:
            zoneinfo.reset_tzpath(to=previous)

        for label, drift in results.items():
            assert drift < 5, f"chart cast against the {label} database is {drift:.0f}s off"

    def test_the_fold_side_is_not_re_derived_from_a_boolean(self):
        """The mechanism, pinned directly.

        Asserting only the drift above would pass again if someone reintroduced
        the boolean while the current date happens to sit outside a fold — which
        is true for all but one hour a year.
        """
        import inspect

        source = inspect.getsource(AstrologicalSubjectFactory.from_current_time)
        # Comments are stripped first: the explanation of why the boolean is not
        # used names it, and matching that would make this assert itself.
        code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
        assert "dst()" not in code, (
            "the fold side must come from the resolved offset, not from dst()"
        )
