# -*- coding: utf-8 -*-
"""Tests for the Vedic Nakshatra module.

Validates the 27 Nakshatra divisions, pada calculations, and
Vimsottari Dasha lord assignments.
"""

import pytest
from kerykeion.ephemeris_backend import ephe
from kerykeion import AstrologicalSubjectFactory
from kerykeion.vedic.nakshatra_utils import calculate_nakshatra
from kerykeion.vedic.nakshatra_data import NAKSHATRAS, NAKSHATRA_SPAN, PADA_SPAN


class TestNakshatraData:
    """Test completeness of nakshatra reference data."""

    def test_27_nakshatras(self):
        assert len(NAKSHATRAS) == 27

    def test_nakshatra_span(self):
        assert abs(NAKSHATRA_SPAN - 13.333333333) < 0.001

    def test_pada_span(self):
        assert abs(PADA_SPAN - 3.333333333) < 0.001

    def test_full_circle_coverage(self):
        assert abs(27 * NAKSHATRA_SPAN - 360.0) < 1e-10


class TestNakshatraCalculation:
    """Test nakshatra position calculations."""

    def test_first_nakshatra_ashwini(self):
        """0° sidereal Aries = Ashwini, pada 1."""
        result = calculate_nakshatra(0.0)
        assert result["nakshatra"] == "Ashwini"
        assert result["nakshatra_number"] == 1
        assert result["nakshatra_pada"] == 1
        assert result["nakshatra_lord"] == "Ketu"

    def test_ashwini_pada_2(self):
        """3.34° = Ashwini, pada 2."""
        result = calculate_nakshatra(3.34)
        assert result["nakshatra"] == "Ashwini"
        assert result["nakshatra_pada"] == 2

    def test_bharani(self):
        """14° = Bharani (2nd nakshatra)."""
        result = calculate_nakshatra(14.0)
        assert result["nakshatra"] == "Bharani"
        assert result["nakshatra_number"] == 2
        assert result["nakshatra_lord"] == "Venus"

    def test_rohini(self):
        """~46° = Rohini (4th nakshatra)."""
        result = calculate_nakshatra(46.0)
        assert result["nakshatra"] == "Rohini"
        assert result["nakshatra_number"] == 4
        assert result["nakshatra_lord"] == "Moon"

    def test_last_nakshatra_revati(self):
        """~355° = Revati (27th nakshatra)."""
        result = calculate_nakshatra(355.0)
        assert result["nakshatra"] == "Revati"
        assert result["nakshatra_number"] == 27
        assert result["nakshatra_lord"] == "Mercury"

    def test_boundary_13_degrees(self):
        """At 13.33°, should be at start of Bharani."""
        result = calculate_nakshatra(13.34)
        assert result["nakshatra"] == "Bharani"
        assert result["nakshatra_number"] == 2

    def test_pada_boundaries(self):
        """Test all 4 padas within a nakshatra."""
        # Ashwini: 0-13.333
        assert calculate_nakshatra(1.0)["nakshatra_pada"] == 1
        assert calculate_nakshatra(4.0)["nakshatra_pada"] == 2
        assert calculate_nakshatra(7.5)["nakshatra_pada"] == 3
        assert calculate_nakshatra(11.0)["nakshatra_pada"] == 4

    def test_dasha_lord_sequence(self):
        """Verify the Vimsottari Dasha lord sequence repeats correctly."""
        expected_lords = [
            "Ketu", "Venus", "Sun", "Moon", "Mars",
            "Rahu", "Jupiter", "Saturn", "Mercury",
        ]
        for i in range(27):
            pos = i * NAKSHATRA_SPAN + 1.0
            result = calculate_nakshatra(pos)
            expected = expected_lords[i % 9]
            assert result["nakshatra_lord"] == expected, (
                f"Nakshatra {i+1} ({result['nakshatra']}): "
                f"expected lord {expected}, got {result['nakshatra_lord']}"
            )

    def test_wraparound_at_360(self):
        """360° should wrap to Ashwini."""
        result = calculate_nakshatra(360.0)
        assert result["nakshatra"] == "Ashwini"
        assert result["nakshatra_number"] == 1

    def test_just_below_360(self):
        """359.999° should be Revati with clamped pada <= 4."""
        result = calculate_nakshatra(359.999)
        assert result["nakshatra"] == "Revati"
        assert result["nakshatra_number"] == 27
        assert 1 <= result["nakshatra_pada"] <= 4

    def test_global_pada_index_clamp_guard(self):
        """The single 108-quarter index drives both nakshatra and pada; the
        >= 108 clamp protects the last sliver of the circle. (The old
        per-constant guards were removed with the remainder-based pada
        computation, which misclassified exact boundary degrees.)"""
        # A tiny negative float is the ONE reachable path into the clamp:
        # Python's float modulo returns the modulus itself (-1e-16 % 360.0
        # == 360.0 exactly), so the quarter index hits 108. No non-negative
        # in-range float maps past 107 (exhaustively probed).
        result = calculate_nakshatra(-1e-16)
        assert result["nakshatra_number"] == 27
        assert result["nakshatra"] == "Revati"
        assert result["nakshatra_pada"] == 4

    def test_nakshatra_and_pada_share_one_index(self):
        """Nakshatra and pada must stay mutually consistent at every exact
        pada boundary (the remainder-based formula put 20.0 in pada 2)."""
        for global_quarter, degrees in [(6, 20.0), (9, 30.0), (18, 60.0), (21, 70.0)]:
            result = calculate_nakshatra(degrees)
            assert result["nakshatra_number"] == global_quarter // 4 + 1
            assert result["nakshatra_pada"] == global_quarter % 4 + 1


class TestNakshatraIntegration:
    """Test nakshatra integrated in AstrologicalSubjectFactory."""

    @pytest.fixture(scope="class")
    def subject_with_nakshatra(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Nakshatra Test", 1990, 1, 1, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            calculate_nakshatra=True,
        )

    @pytest.fixture(scope="class")
    def subject_without_nakshatra(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "No Nakshatra", 1990, 1, 1, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )

    def test_nakshatra_populated(self, subject_with_nakshatra):
        sun = subject_with_nakshatra.sun
        assert sun.nakshatra is not None
        assert sun.nakshatra_number is not None
        assert 1 <= sun.nakshatra_number <= 27
        assert sun.nakshatra_pada is not None
        assert 1 <= sun.nakshatra_pada <= 4
        assert sun.nakshatra_lord is not None

    def test_nakshatra_not_populated_by_default(self, subject_without_nakshatra):
        sun = subject_without_nakshatra.sun
        assert sun.nakshatra is None
        assert sun.nakshatra_number is None

    def test_all_planets_have_nakshatra(self, subject_with_nakshatra):
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject_with_nakshatra, name)
            if point is not None:
                assert point.nakshatra is not None, f"{name} should have nakshatra"
                assert point.nakshatra_lord is not None, f"{name} should have nakshatra_lord"

    def test_moon_nakshatra_valid(self, subject_with_nakshatra):
        """Moon's nakshatra is the most important in Vedic astrology."""
        moon = subject_with_nakshatra.moon
        nakshatra_names = [n[0] for n in NAKSHATRAS]
        assert moon.nakshatra in nakshatra_names


class TestNakshatraSwissEphRegression:
    """Known-value regression tests using Swiss Ephemeris sidereal positions.

    For each test date, the Moon's sidereal longitude is computed via
    ephe.calc_ut with FLG_SIDEREAL + LAHIRI ayanamsa.  The expected nakshatra
    number is derived manually as int(sidereal_pos / (360/27)) + 1.
    Then calculate_nakshatra is called and the results must match.
    """

    @classmethod
    def setup_class(cls):
        ephe.set_ephe_path("")

    # (year, month, day, hour, label, expected_nakshatra_name, expected_number)
    # Values pre-computed with ephe.calc_ut + LAHIRI
    TEST_DATES = [
        (2000, 1, 1, 12.0, "J2000.0",
         199.470553, "Swati", 15, 4, "Rahu"),
        (2000, 6, 15, 12.0, "mid-2000",
         225.045266, "Anuradha", 17, 4, "Saturn"),
        (2010, 3, 21, 12.0, "2010-equinox",
         42.318238, "Rohini", 4, 1, "Moon"),
    ]

    @pytest.mark.parametrize(
        "year,month,day,hour,label,expected_sid_pos,exp_name,exp_num,exp_pada,exp_lord",
        TEST_DATES,
        ids=[t[4] for t in TEST_DATES],
    )
    def test_moon_nakshatra_matches_swe_sidereal(
        self, year, month, day, hour, label,
        expected_sid_pos, exp_name, exp_num, exp_pada, exp_lord,
    ):
        """Verify nakshatra from ephe sidereal Moon position matches calculate_nakshatra."""
        jd = ephe.julday(year, month, day, hour)

        # Compute sidereal Moon longitude using LAHIRI ayanamsa
        ephe.set_sid_mode(ephe.SIDM_LAHIRI)
        moon_sid = ephe.calc_ut(jd, ephe.MOON, ephe.FLG_SWIEPH | ephe.FLG_SIDEREAL)
        sid_pos = moon_sid[0][0]

        # Verify ephe gives the expected sidereal position (within 0.01 deg)
        assert abs(sid_pos - expected_sid_pos) < 0.01, (
            f"[{label}] ephe sidereal Moon = {sid_pos:.6f}, expected ~{expected_sid_pos:.6f}"
        )

        # Manually compute expected nakshatra index
        manual_index = int(sid_pos / (360.0 / 27.0))
        manual_number = manual_index + 1
        assert manual_number == exp_num, (
            f"[{label}] manual nakshatra number = {manual_number}, expected {exp_num}"
        )

        # Use kerykeion's calculate_nakshatra and verify all fields
        result = calculate_nakshatra(sid_pos)
        assert result["nakshatra"] == exp_name, (
            f"[{label}] nakshatra name = {result['nakshatra']}, expected {exp_name}"
        )
        assert result["nakshatra_number"] == exp_num, (
            f"[{label}] nakshatra number = {result['nakshatra_number']}, expected {exp_num}"
        )
        assert result["nakshatra_pada"] == exp_pada, (
            f"[{label}] pada = {result['nakshatra_pada']}, expected {exp_pada}"
        )
        assert result["nakshatra_lord"] == exp_lord, (
            f"[{label}] lord = {result['nakshatra_lord']}, expected {exp_lord}"
        )

    # --- v6: the tropical chart must land on the SAME nakshatras -------------
    #
    # The chart above proves the division is right once the longitude is
    # sidereal. This one proves the factory now makes it sidereal: the same
    # subject cast tropically and cast in sidereal LAHIRI must name the same
    # nakshatra, pada and lord for every point. Before the fix the tropical
    # chart was two nakshatras away.

    _COINCIDENCE_BIRTH = dict(
        year=2026, month=8, day=28, hour=4, minute=47,
        lng=0.0, lat=51.5, tz_str="Etc/UTC",
        city="Greenwich", nation="GB", online=False,
        suppress_geonames_warning=True,
    )

    @pytest.fixture(scope="class")
    def tropical_subject(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Tropical Lahiri Nakshatra", calculate_nakshatra=True, **self._COINCIDENCE_BIRTH
        )

    @pytest.fixture(scope="class")
    def sidereal_subject(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Lahiri Nakshatra",
            calculate_nakshatra=True,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            **self._COINCIDENCE_BIRTH,
        )

    @pytest.mark.parametrize("point_name", ["sun", "moon", "mercury", "ascendant"])
    def test_tropical_nakshatra_coincides_with_sidereal_lahiri(
        self, tropical_subject, sidereal_subject, point_name
    ):
        tropical = getattr(tropical_subject, point_name)
        sidereal = getattr(sidereal_subject, point_name)

        # The two charts genuinely disagree on the longitude — that is the point:
        # only the nakshatra is expected to coincide.
        assert abs((tropical.abs_pos - sidereal.abs_pos) % 360.0 - 24.23) < 0.01

        assert tropical.nakshatra == sidereal.nakshatra, point_name
        assert tropical.nakshatra_number == sidereal.nakshatra_number, point_name
        assert tropical.nakshatra_pada == sidereal.nakshatra_pada, point_name
        assert tropical.nakshatra_lord == sidereal.nakshatra_lord, point_name

    def test_known_value_sun_is_magha_pada_4(self, tropical_subject):
        """2026-08-28 04:47 UTC, Greenwich: the Sun is in Magha, pada 4 — the
        value the sidereal chart gives. The tropical chart used to answer
        'Uttara Phalguni, pada 3', two nakshatras along."""
        assert tropical_subject.sun.nakshatra == "Magha"
        assert tropical_subject.sun.nakshatra_pada == 4
        assert tropical_subject.sun.nakshatra_lord == "Ketu"

    def test_rotation_is_the_charts_own_ayanamsa(self, tropical_subject, sidereal_subject):
        """The recorded offset IS the sidereal chart's ayanamsa, bit for bit —
        not a near-miss variant (get_ayanamsa_ut, the mean ayanamsa, is ~2
        arcseconds away and would break the coincidence at a boundary)."""
        assert tropical_subject.nakshatra_ayanamsa == "LAHIRI"
        assert tropical_subject.nakshatra_ayanamsa_value == sidereal_subject.ayanamsa_value


class TestNakshatraAyanamsaOnNonSiderealCharts:
    """v6: nakshatras divide the SIDEREAL zodiac, so a non-sidereal chart's
    longitudes are rotated by ``nakshatra_ayanamsa`` before the division. The
    legacy uncorrected behaviour survives behind ``nakshatra_ayanamsa=None``,
    and says so."""

    _BIRTH = dict(
        year=1990, month=1, day=1, hour=12, minute=0,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        suppress_geonames_warning=True,
    )

    @staticmethod
    def _nakshatra_warnings(caplog):
        return [
            r
            for r in caplog.records
            if r.levelname == "WARNING"
            and "nakshatra" in r.getMessage().lower()
            and "sidereal" in r.getMessage().lower()
        ]

    def test_tropical_chart_is_corrected_and_silent(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="kerykeion.astrological_subject.factory"):
            subject = AstrologicalSubjectFactory.from_birth_data(
                "Tropical Nakshatra", calculate_nakshatra=True, **self._BIRTH
            )

        assert not self._nakshatra_warnings(caplog), "the corrected path has nothing to warn about"
        assert subject.nakshatra_ayanamsa == "LAHIRI"
        assert subject.nakshatra_ayanamsa_value == pytest.approx(23.7, abs=0.5)
        assert subject.sun.nakshatra is not None
        assert subject.moon.nakshatra is not None

    def test_legacy_optin_warns_once_and_keeps_the_old_values(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="kerykeion.astrological_subject.factory"):
            subject = AstrologicalSubjectFactory.from_birth_data(
                "Legacy Nakshatra",
                calculate_nakshatra=True,
                nakshatra_ayanamsa=None,
                **self._BIRTH,
            )

        warnings = self._nakshatra_warnings(caplog)
        assert warnings, "opting into the uncorrected values must say so"
        assert len(warnings) == 1, "the warning must fire once per subject construction, not per point"

        # Pre-v6 behaviour, exactly: the raw tropical longitude, divided as-is.
        assert subject.nakshatra_ayanamsa is None
        assert subject.nakshatra_ayanamsa_value is None
        for name in ("sun", "moon", "ascendant"):
            point = getattr(subject, name)
            assert point.nakshatra == calculate_nakshatra(point.abs_pos)["nakshatra"], name
            assert point.nakshatra_pada == calculate_nakshatra(point.abs_pos)["nakshatra_pada"], name

    def test_legacy_and_default_disagree_by_two_nakshatras(self):
        """The two paths must NOT accidentally coincide — otherwise the test
        above would pass on a chart where the fix changes nothing."""
        corrected = AstrologicalSubjectFactory.from_birth_data(
            "Corrected", calculate_nakshatra=True, **self._BIRTH
        )
        legacy = AstrologicalSubjectFactory.from_birth_data(
            "Legacy", calculate_nakshatra=True, nakshatra_ayanamsa=None, **self._BIRTH
        )
        assert corrected.sun.nakshatra != legacy.sun.nakshatra
        assert (legacy.sun.nakshatra_number - corrected.sun.nakshatra_number) % 27 == 2

    def test_no_warning_for_sidereal_chart(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="kerykeion.astrological_subject.factory"):
            subject = AstrologicalSubjectFactory.from_birth_data(
                "Sidereal Nakshatra",
                calculate_nakshatra=True,
                zodiac_type="Sidereal",
                sidereal_mode="LAHIRI",
                **self._BIRTH,
            )

        warnings = self._nakshatra_warnings(caplog)
        assert not warnings, f"unexpected nakshatra warning on a sidereal chart: {warnings}"
        assert subject.sun.nakshatra is not None

    def test_sidereal_chart_ignores_nakshatra_ayanamsa(self):
        """A sidereal chart's longitudes ARE the answer: the parameter is
        ignored, and the fields stay None so nothing suggests a second ayanamsa
        was in play."""
        common = dict(
            calculate_nakshatra=True, zodiac_type="Sidereal", sidereal_mode="LAHIRI", **self._BIRTH
        )
        default = AstrologicalSubjectFactory.from_birth_data("Sid default", **common)
        overridden = AstrologicalSubjectFactory.from_birth_data(
            "Sid overridden", nakshatra_ayanamsa="RAMAN", **common
        )
        legacy = AstrologicalSubjectFactory.from_birth_data(
            "Sid legacy", nakshatra_ayanamsa=None, **common
        )

        for subject in (default, overridden, legacy):
            assert subject.nakshatra_ayanamsa is None
            assert subject.nakshatra_ayanamsa_value is None
            assert subject.sun.nakshatra == default.sun.nakshatra
            assert subject.sun.nakshatra_pada == default.sun.nakshatra_pada

    def test_fields_are_none_when_nakshatras_are_not_computed(self):
        subject = AstrologicalSubjectFactory.from_birth_data("No nakshatra", **self._BIRTH)
        assert subject.nakshatra_ayanamsa is None
        assert subject.nakshatra_ayanamsa_value is None
        assert subject.sun.nakshatra is None

    def test_other_ayanamsa_moves_the_result(self):
        """The parameter is genuinely consulted: Fagan-Bradley sits ~0.88 deg
        from Lahiri, enough to move a point that is near a pada boundary."""
        lahiri = AstrologicalSubjectFactory.from_birth_data(
            "Lahiri", calculate_nakshatra=True, **self._BIRTH
        )
        fagan = AstrologicalSubjectFactory.from_birth_data(
            "Fagan", calculate_nakshatra=True, nakshatra_ayanamsa="FAGAN_BRADLEY", **self._BIRTH
        )
        assert fagan.nakshatra_ayanamsa == "FAGAN_BRADLEY"
        assert fagan.nakshatra_ayanamsa_value != lahiri.nakshatra_ayanamsa_value
        assert abs(fagan.nakshatra_ayanamsa_value - lahiri.nakshatra_ayanamsa_value) == pytest.approx(
            0.88, abs=0.05
        )

    def test_unknown_ayanamsa_is_rejected(self):
        from kerykeion.schemas.exceptions import KerykeionException

        with pytest.raises(KerykeionException, match="not a valid nakshatra ayanamsa"):
            AstrologicalSubjectFactory.from_birth_data(
                "Bad", calculate_nakshatra=True, nakshatra_ayanamsa="NOT_A_MODE", **self._BIRTH
            )

    def test_user_ayanamsa_needs_its_definition(self):
        from kerykeion.schemas.exceptions import KerykeionException

        with pytest.raises(KerykeionException, match="nakshatra_ayanamsa='USER'"):
            AstrologicalSubjectFactory.from_birth_data(
                "User no params", calculate_nakshatra=True, nakshatra_ayanamsa="USER", **self._BIRTH
            )

    def test_user_ayanamsa_is_cast_and_persisted(self):
        """A USER ayanamsa on a tropical chart is cast, and its definition is
        stored: without that the nakshatras would not be reproducible."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "User nakshatra",
            calculate_nakshatra=True,
            nakshatra_ayanamsa="USER",
            custom_ayanamsa_t0=2451545.0,   # J2000.0
            custom_ayanamsa_ayan_t0=23.85,  # degrees at t0
            **self._BIRTH,
        )
        assert subject.zodiac_type == "Tropical"
        assert subject.nakshatra_ayanamsa == "USER"
        assert subject.nakshatra_ayanamsa_value == pytest.approx(23.85, abs=0.2)
        assert subject.custom_ayanamsa_t0 == 2451545.0
        assert subject.custom_ayanamsa_ayan_t0 == 23.85

    def test_from_iso_utc_time_and_from_current_time_expose_it(self):
        subject = AstrologicalSubjectFactory.from_iso_utc_time(
            "ISO nakshatra",
            "1990-01-01T11:00:00Z",
            lng=12.4964,
            lat=41.9028,
            tz_str="Europe/Rome",
            city="Rome",
            nation="IT",
            online=False,
            calculate_nakshatra=True,
            nakshatra_ayanamsa="RAMAN",
        )
        assert subject.nakshatra_ayanamsa == "RAMAN"
        assert subject.nakshatra_ayanamsa_value is not None

        now = AstrologicalSubjectFactory.from_current_time(
            "Now nakshatra",
            lng=12.4964,
            lat=41.9028,
            tz_str="Europe/Rome",
            city="Rome",
            nation="IT",
            online=False,
            calculate_nakshatra=True,
            nakshatra_ayanamsa="RAMAN",
        )
        assert now.nakshatra_ayanamsa == "RAMAN"


class TestNakshatraAyanamsaTravelsToDerivedCharts:
    """The ayanamsa a natal placed its nakshatras with must reach every chart
    derived from it, or the derived chart's nakshatras disagree with its own
    natal's for no reason a reader could see."""

    _BIRTH = dict(
        year=1990, month=6, day=15, hour=12, minute=0,
        lng=12.5, lat=41.9, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        suppress_geonames_warning=True,
    )

    @pytest.fixture(scope="class")
    def natal(self):
        return AstrologicalSubjectFactory.from_birth_data(
            "Natal RAMAN", calculate_nakshatra=True, nakshatra_ayanamsa="RAMAN", **self._BIRTH
        )

    def test_secondary_progression_inherits_it(self, natal):
        from kerykeion.secondary_progressions import SecondaryProgressionFactory

        progressed = SecondaryProgressionFactory.compute(natal, target_year=2020)
        assert progressed.nakshatra_ayanamsa == "RAMAN"
        assert progressed.sun.nakshatra is not None

    def test_planetary_return_inherits_it(self, natal):
        from kerykeion.planetary_returns import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(
            natal, city="Rome", nation="IT", lng=12.5, lat=41.9,
            tz_str="Europe/Rome", online=False,
        )
        solar_return = factory.next_return_from_date(2020, 6, 1, return_type="Solar")
        assert solar_return.nakshatra_ayanamsa == "RAMAN"
        assert solar_return.sun.nakshatra is not None

    def test_davison_composite_inherits_the_shared_ayanamsa(self, natal):
        from kerykeion.composite_subject import CompositeSubjectFactory

        second = AstrologicalSubjectFactory.from_birth_data(
            "Second RAMAN", calculate_nakshatra=True, nakshatra_ayanamsa="RAMAN",
            **{**self._BIRTH, "year": 1992, "month": 3, "day": 4},
        )
        davison = CompositeSubjectFactory(natal, second).get_davison_composite_subject_model()
        assert davison.nakshatra_ayanamsa == "RAMAN"
        assert davison.sun.nakshatra is not None

    def test_davison_falls_back_when_the_parents_disagree(self, natal, caplog):
        """Two parents, two ayanamsas: the composite has no basis for choosing,
        so it takes the default — out loud."""
        import logging

        from kerykeion.composite_subject import CompositeSubjectFactory

        other_mode = AstrologicalSubjectFactory.from_birth_data(
            "Second LAHIRI", calculate_nakshatra=True, nakshatra_ayanamsa="LAHIRI",
            **{**self._BIRTH, "year": 1992, "month": 3, "day": 4},
        )
        with caplog.at_level(logging.WARNING, logger="kerykeion.composite_subject.factory"):
            davison = CompositeSubjectFactory(natal, other_mode).get_davison_composite_subject_model()

        assert davison.nakshatra_ayanamsa == "LAHIRI"  # the factory default, not RAMAN
        assert [r for r in caplog.records if "different ayanamsas" in r.getMessage()]


class TestANatalWithoutNakshatrasIsNotAnOptOut:
    """``nakshatra_ayanamsa=None`` means three different things, and a derived
    chart must not read the wrong one.

    The field is None when the natal opted into the legacy uncorrected values,
    when the natal is sidereal (its own ``sidereal_mode`` is the answer), and
    when the natal never computed nakshatras at all. Only the first is an
    opt-out. A derived chart that copies the field blind turns the third into
    the first: a caller who asks the derived factory for nakshatras the natal
    never had gets the legacy values — about two nakshatras off — with no way
    to see it happen.
    """

    _BIRTH = dict(
        year=1990, month=6, day=15, hour=12, minute=0,
        lng=12.5, lat=41.9, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
        suppress_geonames_warning=True,
    )

    _LOCATION = dict(
        city="Rome", nation="IT", lng=12.5, lat=41.9,
        tz_str="Europe/Rome", online=False,
    )

    @pytest.fixture(scope="class")
    def bare_natal(self):
        """A tropical natal that never computed a nakshatra. Its
        ``nakshatra_ayanamsa`` is None because nothing was ever placed."""
        natal = AstrologicalSubjectFactory.from_birth_data("Natal bare", **self._BIRTH)
        assert natal.sun.nakshatra is None
        assert natal.nakshatra_ayanamsa is None
        return natal

    def test_the_return_asked_for_them_gets_the_default_not_the_legacy_values(self, bare_natal):
        """The factory flag turns nakshatras ON for a return whose natal has
        none. They must be the same nakshatras the very same instant gives when
        cast directly — the comparison is against a chart, not a memorised
        name, so an engine bump moves both together."""
        from kerykeion.planetary_returns import PlanetaryReturnFactory
        from kerykeion.settings.config_constants import DEFAULT_NAKSHATRA_AYANAMSA

        factory = PlanetaryReturnFactory(bare_natal, calculate_nakshatra=True, **self._LOCATION)
        solar_return = factory.next_return_from_date(2020, 6, 1, return_type="Solar")

        assert solar_return.nakshatra_ayanamsa == DEFAULT_NAKSHATRA_AYANAMSA
        assert solar_return.sun.nakshatra is not None

        same_instant = AstrologicalSubjectFactory.from_iso_utc_time(
            "Same instant",
            solar_return.iso_formatted_utc_datetime,
            calculate_nakshatra=True,
            **self._LOCATION,
        )
        assert solar_return.sun.nakshatra == same_instant.sun.nakshatra
        assert solar_return.moon.nakshatra == same_instant.moon.nakshatra

        legacy = AstrologicalSubjectFactory.from_iso_utc_time(
            "Legacy",
            solar_return.iso_formatted_utc_datetime,
            calculate_nakshatra=True,
            nakshatra_ayanamsa=None,
            **self._LOCATION,
        )
        assert solar_return.sun.nakshatra != legacy.sun.nakshatra

    def test_a_return_that_was_never_asked_still_has_none(self, bare_natal):
        """The flag is what turns them on. Nothing here should conjure a
        nakshatra onto a chart neither the caller nor the natal asked for."""
        from kerykeion.planetary_returns import PlanetaryReturnFactory

        factory = PlanetaryReturnFactory(bare_natal, **self._LOCATION)
        solar_return = factory.next_return_from_date(2020, 6, 1, return_type="Solar")

        assert solar_return.sun.nakshatra is None
        assert solar_return.nakshatra_ayanamsa is None

    def test_the_progression_is_not_affected(self, bare_natal):
        """Pinned, not assumed: `SecondaryProgressionFactory` copies the natal's
        ``nakshatra_ayanamsa`` unconditionally, but derives the flag from the
        natal too and takes no override — so a natal without nakshatras yields a
        progression without them, and the copied None is never consulted."""
        from kerykeion.secondary_progressions import SecondaryProgressionFactory

        progressed = SecondaryProgressionFactory.compute(bare_natal, target_year=2020)

        assert progressed.sun.nakshatra is None
        assert progressed.nakshatra_ayanamsa is None

    def test_the_davison_is_not_affected(self, bare_natal):
        """Pinned, not assumed: the composite reads the ayanamsa only inside
        ``if calculate_nakshatra``, and the flag needs BOTH parents — so a
        parent without nakshatras closes the door before None can be read as an
        opt-out."""
        from kerykeion.composite_subject import CompositeSubjectFactory

        with_nakshatras = AstrologicalSubjectFactory.from_birth_data(
            "Second LAHIRI",
            calculate_nakshatra=True,
            **{**self._BIRTH, "year": 1992, "month": 3, "day": 4},
        )
        davison = CompositeSubjectFactory(bare_natal, with_nakshatras).get_davison_composite_subject_model()

        assert davison.sun.nakshatra is None
        assert davison.nakshatra_ayanamsa is None
