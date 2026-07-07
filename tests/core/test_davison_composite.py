# -*- coding: utf-8 -*-
"""Tests for the Davison composite chart."""

import pytest
from kerykeion import AstrologicalSubjectFactory, CompositeSubjectFactory


@pytest.fixture(scope="module")
def subjects():
    s1 = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", 1940, 10, 9, 18, 30,
        lng=-2.9916, lat=53.4084, tz_str="Europe/London",
        city="Liverpool", nation="GB", online=False,
    )
    s2 = AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono", 1933, 2, 18, 20, 30,
        lng=139.6917, lat=35.6895, tz_str="Asia/Tokyo",
        city="Tokyo", nation="JP", online=False,
    )
    return s1, s2


class TestDavisonComposite:
    def test_davison_creates_valid_chart(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()
        assert davison is not None
        assert davison.composite_chart_type == "Davison"

    def test_davison_has_planets(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()
        assert davison.sun is not None
        assert davison.moon is not None
        assert davison.ascendant is not None
        assert 0 <= davison.sun.abs_pos < 360

    def test_davison_has_subjects(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()
        assert davison.first_subject.name == "John Lennon"
        assert davison.second_subject.name == "Yoko Ono"

    def test_davison_midpoint_date_between_subjects(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()
        # Davison JD should be between the two subjects
        assert s2.julian_day < davison.julian_day < s1.julian_day

    def test_davison_differs_from_midpoint(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        midpoint = factory.get_midpoint_composite_subject_model()
        davison = factory.get_davison_composite_subject_model()
        # Davison and midpoint should give different Sun positions
        assert abs(midpoint.sun.abs_pos - davison.sun.abs_pos) > 0.01

    def test_both_chart_types_available(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        midpoint = factory.get_midpoint_composite_subject_model()
        assert midpoint.composite_chart_type == "Midpoint"
        # Need a new factory since midpoint modifies internal state
        factory2 = CompositeSubjectFactory(s1, s2)
        davison = factory2.get_davison_composite_subject_model()
        assert davison.composite_chart_type == "Davison"


class TestDavisonUserSiderealMode:
    """v6: Davison charts with sidereal_mode='USER' need the custom ayanamsa."""

    @pytest.fixture(scope="class")
    def user_sidereal_subjects(self):
        kwargs = dict(
            online=False,
            zodiac_type="Sidereal",
            sidereal_mode="USER",
            custom_ayanamsa_t0=2451545.0,
            custom_ayanamsa_ayan_t0=23.85,
        )
        s1 = AstrologicalSubjectFactory.from_birth_data(
            "User One", 1940, 10, 9, 18, 30,
            lng=-2.9916, lat=53.4084, tz_str="Europe/London",
            city="Liverpool", nation="GB", **kwargs,
        )
        s2 = AstrologicalSubjectFactory.from_birth_data(
            "User Two", 1933, 2, 18, 20, 30,
            lng=139.6917, lat=35.6895, tz_str="Asia/Tokyo",
            city="Tokyo", nation="JP", **kwargs,
        )
        return s1, s2

    def test_user_mode_without_ayanamsa_raises(self, user_sidereal_subjects):
        from kerykeion.schemas import KerykeionException

        s1, s2 = user_sidereal_subjects
        factory = CompositeSubjectFactory(s1, s2)
        with pytest.raises(KerykeionException, match="custom_ayanamsa"):
            factory.get_davison_composite_subject_model()

    def test_user_mode_with_ayanamsa_succeeds(self, user_sidereal_subjects):
        s1, s2 = user_sidereal_subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model(
            custom_ayanamsa_t0=2451545.0,
            custom_ayanamsa_ayan_t0=23.85,
        )
        assert davison.composite_chart_type == "Davison"
        assert davison.zodiac_type == "Sidereal"
        assert davison.sidereal_mode == "USER"
        assert davison.sun is not None

    def test_user_mode_ayanamsa_actually_applied(self, subjects, user_sidereal_subjects):
        """The USER ayanamsa must shift the Davison positions vs tropical."""
        s1, s2 = subjects
        tropical_davison = CompositeSubjectFactory(s1, s2).get_davison_composite_subject_model()

        u1, u2 = user_sidereal_subjects
        user_davison = CompositeSubjectFactory(u1, u2).get_davison_composite_subject_model(
            custom_ayanamsa_t0=2451545.0,
            custom_ayanamsa_ayan_t0=23.85,
        )
        diff = (tropical_davison.sun.abs_pos - user_davison.sun.abs_pos) % 360.0
        # Ayanamsa near the 1937 midpoint epoch with this USER definition is ~23°
        assert 20.0 < diff < 28.0, f"Expected an ayanamsa-sized shift, got {diff}°"


class TestCompositeSubjectDunderMethods:
    """Test __str__, __repr__, __eq__, __ne__, __hash__ on CompositeSubjectFactory."""

    def test_str(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2, "Test Chart")
        assert str(factory) == "Composite Chart Data for Test Chart"

    def test_repr(self, subjects):
        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2, "Test Chart")
        assert repr(factory) == "Composite Chart Data for Test Chart"

    def test_eq_same_inputs(self, subjects):
        s1, s2 = subjects
        f1 = CompositeSubjectFactory(s1, s2, "Chart")
        f2 = CompositeSubjectFactory(s1, s2, "Chart")
        assert f1 == f2

    def test_ne_different_name(self, subjects):
        s1, s2 = subjects
        f1 = CompositeSubjectFactory(s1, s2, "Chart A")
        f2 = CompositeSubjectFactory(s1, s2, "Chart B")
        assert f1 != f2

    def test_hash_uses_stable_scalars(self, subjects):
        """__hash__ must hash stable scalar identifiers (name/julian_day) rather
        than the subject models themselves: AstrologicalSubjectModel is a
        non-frozen Pydantic model, so hashing it always raised TypeError."""
        s1, s2 = subjects
        f1 = CompositeSubjectFactory(s1, s2, "Chart")
        f2 = CompositeSubjectFactory(s1, s2, "Chart")
        assert isinstance(hash(f1), int)
        # Consistent with __eq__: equal factories hash equal.
        assert f1 == f2
        assert hash(f1) == hash(f2)

    def test_hash_differs_for_different_name(self, subjects):
        s1, s2 = subjects
        f1 = CompositeSubjectFactory(s1, s2, "Chart A")
        f2 = CompositeSubjectFactory(s1, s2, "Chart B")
        assert hash(f1) != hash(f2)


class TestCompositeValidation:
    """Test validation errors in CompositeSubjectFactory.__init__."""

    def test_different_houses_system_name_raises(self, subjects):
        """Subjects with different houses_system_name should raise."""
        from kerykeion.schemas import KerykeionException
        s1, s2 = subjects
        # Mutate s2's houses_system_name (keeping identifier the same)
        s2_mod = s2.model_copy()
        s2_mod.houses_system_name = "Fake House System"
        with pytest.raises(KerykeionException, match="houses system name"):
            CompositeSubjectFactory(s1, s2_mod)


class TestDavisonSweReference:
    """Compare Davison factory Sun position with direct ephe.calc_ut() at midpoint JD."""

    def test_davison_sun_matches_swe_at_midpoint_jd(self, subjects):
        """Davison Sun longitude must match ephe.calc_ut(midpoint_jd, SUN)."""
        from kerykeion.ephemeris_backend import ephe, EPHE_DATA_PATH
        ephe.set_ephe_path(EPHE_DATA_PATH)

        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()

        midpoint_jd = (s1.julian_day + s2.julian_day) / 2.0
        iflag = ephe.FLG_SWIEPH | ephe.FLG_SPEED
        expected_sun_lng = ephe.calc_ut(midpoint_jd, ephe.SUN, iflag)[0][0]

        assert davison.sun.abs_pos == pytest.approx(expected_sun_lng, abs=0.01), (
            f"Davison Sun {davison.sun.abs_pos} != ephe Sun {expected_sun_lng}"
        )

    def test_davison_moon_matches_swe_at_midpoint_jd(self, subjects):
        """Davison Moon longitude must match ephe.calc_ut(midpoint_jd, MOON)."""
        from kerykeion.ephemeris_backend import ephe, EPHE_DATA_PATH
        ephe.set_ephe_path(EPHE_DATA_PATH)

        s1, s2 = subjects
        factory = CompositeSubjectFactory(s1, s2)
        davison = factory.get_davison_composite_subject_model()

        midpoint_jd = (s1.julian_day + s2.julian_day) / 2.0
        iflag = ephe.FLG_SWIEPH | ephe.FLG_SPEED
        expected_moon_lng = ephe.calc_ut(midpoint_jd, ephe.MOON, iflag)[0][0]

        assert davison.moon.abs_pos == pytest.approx(expected_moon_lng, abs=0.01), (
            f"Davison Moon {davison.moon.abs_pos} != ephe Moon {expected_moon_lng}"
        )


class TestDavisonBCE:
    """The time-midpoint decomposition must be the exact inverse of
    from_birth_data's BCE branch (Julian calendar + longitude-LMT), not the
    Gregorian/Etc-GMT decomposition used for CE midpoints — the mismatch cast
    BCE Davison charts days away from the true midpoint (test node ids contain
    'bce' so the tier filter skips these without the extended kernel)."""

    def _subject(self, name, year, month, day, hour, minute, lng, lat):
        return AstrologicalSubjectFactory.from_birth_data(
            name, year, month, day, hour, minute,
            lng=lng, lat=lat, tz_str="Etc/GMT",
            city="Test", nation="XX", online=False,
            suppress_geonames_warning=True,
        )

    def test_bce_pair_round_trips_to_midpoint_jd(self):
        s1 = self._subject("BCE One", -100, 6, 15, 12, 0, lng=30.0, lat=40.0)
        s2 = self._subject("BCE Two", -44, 3, 15, 9, 30, lng=12.5, lat=41.9)
        mid_jd = (s1.julian_day + s2.julian_day) / 2.0

        davison = CompositeSubjectFactory(s1, s2).get_davison_composite_subject_model()

        assert davison.year < 1
        err_seconds = abs(davison.julian_day - mid_jd) * 86400.0
        assert err_seconds < 1.0, (
            f"Davison JD {davison.julian_day} is {err_seconds:.1f}s away from "
            f"midpoint {mid_jd} (pre-fix error was ~74 hours)"
        )

    def test_mixed_pair_with_bce_midpoint_round_trips(self):
        s1 = self._subject("Deep BCE", -700, 1, 10, 6, 0, lng=-45.0, lat=10.0)
        s2 = self._subject("Early CE", 600, 8, 20, 18, 0, lng=60.0, lat=-20.0)
        mid_jd = (s1.julian_day + s2.julian_day) / 2.0

        davison = CompositeSubjectFactory(s1, s2).get_davison_composite_subject_model()

        assert davison.year < 1
        assert abs(davison.julian_day - mid_jd) * 86400.0 < 1.0

    def test_bce_davison_sun_matches_ephe_at_midpoint_jd(self):
        from kerykeion.ephemeris_backend import ephe

        s1 = self._subject("BCE Sun A", -200, 4, 1, 0, 0, lng=20.0, lat=35.0)
        s2 = self._subject("BCE Sun B", -150, 10, 21, 12, 0, lng=25.0, lat=38.0)
        mid_jd = (s1.julian_day + s2.julian_day) / 2.0

        davison = CompositeSubjectFactory(s1, s2).get_davison_composite_subject_model()

        iflag = ephe.FLG_SWIEPH | ephe.FLG_SPEED
        expected_sun = ephe.calc_ut(mid_jd, ephe.SUN, iflag)[0][0]
        assert davison.sun.abs_pos == pytest.approx(expected_sun, abs=0.01)


class TestDavisonMidpointComponentsInverse:
    """Pure-math round-trip of _davison_midpoint_components: encoding the
    components back the way from_birth_data does (Julian+LMT for year<1,
    Gregorian for CE) must land on the original midpoint JD within the 0.5 s
    seconds-rounding. julday/revjul need no ephemeris data, so this locks the
    exact-inverse property in every test tier."""

    @staticmethod
    def _encode(year, month, day, hour, minute, seconds, lng):
        from kerykeion.ephemeris_backend import ephe

        dec_hour = hour + minute / 60.0 + seconds / 3600.0
        if year < 1:
            jd_local = ephe.julday(year, month, day, dec_hour, ephe.JUL_CAL)
            return jd_local - (lng / 15.0) / 24.0
        return ephe.julday(year, month, day, dec_hour, getattr(ephe, "GREG_CAL", 1))

    @pytest.mark.parametrize(
        "mid_jd,lng",
        [
            (1684570.0, 30.0),     # deep ante-CE, east longitude
            (1538550.25, -120.0),  # deeper ante-CE, west longitude
            (1721000.123456, 45.0),   # just before the CE boundary
            (2451545.0, 12.5),     # J2000
            (2429000.789, -2.99),  # 1930s
        ],
    )
    def test_components_round_trip_within_one_second(self, mid_jd, lng):
        from kerykeion.composite_subject_factory import _davison_midpoint_components

        y, mo, d, h, mi, s = _davison_midpoint_components(mid_jd, lng)
        got = self._encode(y, mo, d, h, mi, s, lng)
        assert abs(got - mid_jd) * 86400.0 < 1.0

    def test_unrepresentable_gap_clamps_with_warning(self, caplog):
        from kerykeion.composite_subject_factory import _davison_midpoint_components

        with caplog.at_level("WARNING"):
            y, mo, d, h, mi, s = _davison_midpoint_components(1721424.5, 0.0)
        assert (y, mo, d, h, mi, s) == (1, 1, 1, 0, 0, 0)
        assert "gap" in caplog.text
