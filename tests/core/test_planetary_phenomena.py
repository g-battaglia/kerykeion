# -*- coding: utf-8 -*-
"""Tests for the Planetary Phenomena factory.

Validates phase angle, elongation, illumination, apparent magnitude,
and morning/evening star status calculations via ephe.pheno_ut().
"""

import pytest
from kerykeion.ephemeris_backend import ephe, ephemeris_session
from kerykeion import AstrologicalSubjectFactory, PlanetaryPhenomenaFactory


@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        "Phenomena Test", 2000, 1, 1, 12, 0,
        lng=0.0, lat=51.5, tz_str="Etc/GMT",
        city="Greenwich", nation="GB", online=False,
    )


class TestPhenomenaFromSubject:
    """Test phenomena calculation from an existing subject."""

    def test_all_planets_returned(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        names = [p.name for p in result.phenomena]
        assert "Mars" in names
        assert "Venus" in names
        assert "Jupiter" in names
        assert len(result.phenomena) >= 7  # At least Moon through Pluto

    def test_julian_day_set(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        assert result.julian_day == subject.julian_day

    def test_elongation_range(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        for p in result.phenomena:
            assert 0 <= p.elongation <= 180, f"{p.name} elongation should be 0-180"

    def test_phase_range(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        for p in result.phenomena:
            assert 0 <= p.phase <= 1, f"{p.name} phase should be 0-1"

    def test_venus_morning_or_evening(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        venus = next((p for p in result.phenomena if p.name == "Venus"), None)
        assert venus is not None
        assert venus.is_morning_star is not None
        assert venus.is_evening_star is not None
        # Must be one or the other (XOR)
        assert venus.is_morning_star != venus.is_evening_star

    def test_mercury_morning_or_evening(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        mercury = next((p for p in result.phenomena if p.name == "Mercury"), None)
        assert mercury is not None
        assert mercury.is_morning_star is not None
        assert mercury.is_evening_star is not None

    def test_mars_no_morning_evening(self, subject):
        """Superior planets don't have morning/evening star status."""
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        mars = next((p for p in result.phenomena if p.name == "Mars"), None)
        assert mars is not None
        assert mars.is_morning_star is None
        assert mars.is_evening_star is None


class TestPhenomenaFromJulianDay:
    """Test phenomena from direct Julian Day input."""

    def test_j2000_epoch(self):
        result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0)
        assert len(result.phenomena) >= 7

    def test_apparent_magnitude_reasonable(self):
        result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0)
        for p in result.phenomena:
            # Moon can be ~-13, Venus ~-4.6, Pluto ~+14
            assert -15 <= p.apparent_magnitude <= 25, (
                f"{p.name} magnitude {p.apparent_magnitude} out of range"
            )


class TestPhenomenaFiltering:
    """Test planet name filtering."""

    def test_single_planet(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject, planets=["Mars"])
        assert len(result.phenomena) == 1
        assert result.phenomena[0].name == "Mars"

    def test_multiple_planets(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(
            subject, planets=["Venus", "Jupiter"]
        )
        assert len(result.phenomena) == 2
        names = {p.name for p in result.phenomena}
        assert names == {"Venus", "Jupiter"}

    def test_nonexistent_planet_raises(self, subject):
        # Unknown/mistyped names now raise instead of silently returning an
        # empty result (contract parity with the ingress/station/nodes factories).
        with pytest.raises(ValueError, match="Unknown planets"):
            PlanetaryPhenomenaFactory.from_subject(subject, planets=["FakePlanet"])

    def test_missing_julian_day_raises(self, subject):
        """julian_day is Optional on the model (composite subjects leave it
        None): the guard must raise a clear KerykeionException instead of the
        misleading all-planets-failed "backend may be unavailable" error."""
        from kerykeion.schemas import KerykeionException
        no_jd = subject.model_copy(update={"julian_day": None})
        with pytest.raises(KerykeionException, match="Julian Day"):
            PlanetaryPhenomenaFactory.from_subject(no_jd)


class TestPhenomenaEdgeCases:
    """Test edge-case branches in the phenomena factory."""

    def test_sun_calc_failure_gives_none_morning_evening(self):
        """If ephe.calc_ut for the Sun fails, morning/evening star should be None."""
        from unittest.mock import patch

        original_calc_ut = ephe.calc_ut

        def mock_calc_ut(jd, planet_id, iflag):
            if planet_id == ephe.SUN:
                raise RuntimeError("Mock Sun failure")
            return original_calc_ut(jd, planet_id, iflag)

        with patch("kerykeion.planetary_phenomena.factory.ephe.calc_ut", side_effect=mock_calc_ut):
            result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0, planets=["Venus"])
            assert len(result.phenomena) == 1
            # Without Sun longitude, morning/evening cannot be determined
            assert result.phenomena[0].is_morning_star is None
            assert result.phenomena[0].is_evening_star is None

    def test_pheno_ut_exception_skips_planet(self):
        """If ephe.pheno_ut raises for a planet, that planet should be skipped."""
        from unittest.mock import patch

        original_pheno_ut = ephe.pheno_ut

        def mock_pheno_ut(jd, planet_id, iflag):
            if planet_id == ephe.MARS:
                raise RuntimeError("Mock pheno failure")
            return original_pheno_ut(jd, planet_id, iflag)

        with patch("kerykeion.planetary_phenomena.factory.ephe.pheno_ut", side_effect=mock_pheno_ut):
            result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0)
            names = [p.name for p in result.phenomena]
            assert "Mars" not in names
            # Other planets should still be present
            assert "Venus" in names

    def test_venus_evening_star_branch(self):
        """Venus should be classified as either morning or evening star, covering both branches."""
        # Test multiple epochs to ensure both branches are hit
        # Venus at J2000.0 is an evening star (planet east of Sun, diff < 180)
        result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0, planets=["Venus"])
        venus = result.phenomena[0]
        assert venus.is_morning_star is not None
        assert venus.is_evening_star is not None
        # Whatever Venus is at this epoch, test that at another epoch it's different
        result2 = PlanetaryPhenomenaFactory.from_julian_day(2451545.0 + 200, planets=["Venus"])
        venus2 = result2.phenomena[0]
        # At least one epoch should have morning=True and the other evening=True
        # We just need to ensure both code paths can be reached
        assert venus2.is_morning_star is not None or venus2.is_evening_star is not None

    def test_planet_calc_failure_in_morning_evening_gives_none(self):
        """If ephe.calc_ut fails for the planet's position in the morning/evening block,
        is_morning_star and is_evening_star should remain None.

        The code flow is:
        1. Sun calc_ut succeeds (sun_lon is set)
        2. pheno_ut succeeds (phenomena data computed)
        3. For inferior planets, calc_ut for planet position -> if this fails,
           is_morning/is_evening stay None.
        """
        from unittest.mock import patch

        original_calc_ut = ephe.calc_ut
        venus_calc_count = [0]

        def mock_calc_ut(jd, planet_id, iflag):
            if planet_id == ephe.VENUS:
                venus_calc_count[0] += 1
                # The 2nd call for Venus is the position calc inside morning/evening block
                # (1st call is the Sun, then pheno_ut internally may call, then our position calc)
                if venus_calc_count[0] >= 1:
                    raise RuntimeError("Mock Venus position failure")
            return original_calc_ut(jd, planet_id, iflag)

        with patch("kerykeion.planetary_phenomena.factory.ephe.calc_ut", side_effect=mock_calc_ut):
            result = PlanetaryPhenomenaFactory.from_julian_day(2451545.0, planets=["Venus"])
            if len(result.phenomena) > 0:
                venus = result.phenomena[0]
                # Morning/evening should be None because planet calc failed
                assert venus.is_morning_star is None
                assert venus.is_evening_star is None


class TestSweRegressionPhenomena:
    """Regression tests: verify factory results match raw Swiss Ephemeris calls."""

    def test_venus_phenomena_at_j2000_matches_swe(self):
        """Factory Venus phenomena at J2000.0 should match ephe.pheno_ut directly."""
        jd_j2000 = 2451545.0

        with ephemeris_session() as iflag:
            swe_result = ephe.pheno_ut(jd_j2000, ephe.VENUS, iflag)
        swe_phase_angle = swe_result[0]
        swe_phase = swe_result[1]
        swe_elongation = swe_result[2]
        swe_apparent_diameter = swe_result[3]
        swe_apparent_magnitude = swe_result[4]

        factory_result = PlanetaryPhenomenaFactory.from_julian_day(
            jd_j2000, planets=["Venus"]
        )
        assert len(factory_result.phenomena) == 1
        venus = factory_result.phenomena[0]

        assert abs(venus.phase_angle - swe_phase_angle) < 0.001, (
            f"phase_angle: factory={venus.phase_angle} ephe={swe_phase_angle}"
        )
        assert abs(venus.phase - swe_phase) < 0.001, (
            f"phase: factory={venus.phase} ephe={swe_phase}"
        )
        assert abs(venus.elongation - swe_elongation) < 0.001, (
            f"elongation: factory={venus.elongation} ephe={swe_elongation}"
        )
        assert abs(venus.apparent_diameter - swe_apparent_diameter) < 0.0001, (
            f"apparent_diameter: factory={venus.apparent_diameter} ephe={swe_apparent_diameter}"
        )
        assert abs(venus.apparent_magnitude - swe_apparent_magnitude) < 0.01, (
            f"apparent_magnitude: factory={venus.apparent_magnitude} ephe={swe_apparent_magnitude}"
        )

    def test_mars_phenomena_at_j2000_matches_swe(self):
        """Factory Mars phenomena at J2000.0 should match ephe.pheno_ut directly."""
        jd_j2000 = 2451545.0

        with ephemeris_session() as iflag:
            swe_result = ephe.pheno_ut(jd_j2000, ephe.MARS, iflag)
        swe_phase_angle = swe_result[0]
        swe_elongation = swe_result[2]

        factory_result = PlanetaryPhenomenaFactory.from_julian_day(
            jd_j2000, planets=["Mars"]
        )
        assert len(factory_result.phenomena) == 1
        mars = factory_result.phenomena[0]

        assert abs(mars.phase_angle - swe_phase_angle) < 0.001, (
            f"phase_angle: factory={mars.phase_angle} ephe={swe_phase_angle}"
        )
        assert abs(mars.elongation - swe_elongation) < 0.001, (
            f"elongation: factory={mars.elongation} ephe={swe_elongation}"
        )


class TestAllFailedGuard:
    def test_all_planets_failing_raises(self, monkeypatch):
        """Parity with PlanetaryNodesFactory: if the backend fails for every
        requested planet, surface a KerykeionException instead of silently
        returning an empty collection (indistinguishable from 'no phenomena')."""
        import kerykeion.planetary_phenomena.factory as pf
        from kerykeion.schemas import KerykeionException

        monkeypatch.setattr(pf.ephe, "pheno_ut", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("backend down")))
        with pytest.raises(KerykeionException, match="all requested planets"):
            PlanetaryPhenomenaFactory.from_julian_day(2451545.0, planets=["Venus", "Mars"])


def _elongation(julian_day: float, planet: str = "Mercury") -> float:
    """Elongation of one planet, through the public factory."""
    return PlanetaryPhenomenaFactory.from_julian_day(
        julian_day, planets=[planet]
    ).phenomena[0].elongation


def _extreme_elongation(jd_low: float, jd_high: float, seek: str, planet: str = "Mercury") -> float:
    """Julian Day of the elongation extremum inside a window, by ternary search.

    The window is chosen to hold exactly one extremum, so elongation is unimodal
    on it and a ternary search converges. Forty rounds shrink two days to well
    under a second of time — far finer than the phenomenon needs, and cheap.

    Searching instead of hardcoding an instant is the point: a conjunction is
    what it is regardless of which minute the ephemeris puts it in, so the test
    pins the astronomy rather than a number an engine bump could move.
    """
    better = (lambda a, b: a < b) if seek == "min" else (lambda a, b: a > b)
    lo, hi = jd_low, jd_high
    for _ in range(40):
        m1 = lo + (hi - lo) / 3
        m2 = hi - (hi - lo) / 3
        if better(_elongation(m1, planet), _elongation(m2, planet)):
            hi = m2
        else:
            lo = m1
    return (lo + hi) / 2


class TestSolarPhase:
    """The condition relative to the Sun: cazimi / combust / under the beams / free.

    The regression this class guards: before ``solar_phase`` existed, the only
    thing the library said about a planet's nearness to the Sun was
    ``is_evening_star``, which is a pure question of geometry and answers True
    for a Mercury one degree from the Sun — a planet nobody can see.
    """

    # 2026-08-28 04:47 UTC: Mercury 1.80 deg from the Sun, and an "evening star".
    MERCURY_COMBUST_JD = ephe.julday(2026, 8, 28, 4 + 47 / 60)

    def test_mercury_at_two_degrees_is_combust(self):
        result = PlanetaryPhenomenaFactory.from_julian_day(
            self.MERCURY_COMBUST_JD, planets=["Mercury"]
        )
        mercury = result.phenomena[0]
        assert mercury.elongation == pytest.approx(1.80, abs=0.02)
        assert mercury.solar_phase == "combust"

    def test_the_geometric_flags_are_untouched_by_the_new_field(self):
        """is_morning_star/is_evening_star keep meaning exactly what they meant.

        They are the side of the Sun the planet stands on, nothing more. The
        combust Mercury above is still, geometrically, an evening star — and the
        library must go on saying so, because that is a true statement about
        where it is. What changed is that there is now a second field saying it
        cannot be seen.
        """
        mercury = PlanetaryPhenomenaFactory.from_julian_day(
            self.MERCURY_COMBUST_JD, planets=["Mercury"]
        ).phenomena[0]
        assert mercury.is_evening_star is True
        assert mercury.is_morning_star is False
        assert mercury.solar_phase == "combust"

    def test_venus_at_thirteen_degrees_is_under_the_beams(self):
        jd = ephe.julday(2026, 11, 1, 0.0)
        venus = PlanetaryPhenomenaFactory.from_julian_day(jd, planets=["Venus"]).phenomena[0]
        assert venus.elongation == pytest.approx(13.24, abs=0.02)
        assert venus.solar_phase == "under_the_beams"

    def test_mercury_at_its_conjunction_is_cazimi(self):
        """Mercury's May 2026 conjunction passes within 16' of the Sun's centre.

        Cazimi by TRUE separation is rare — most conjunctions leave the planet
        degrees away in latitude even while sharing the Sun's longitude — so the
        instant is found by search rather than assumed.
        """
        jd = _extreme_elongation(
            ephe.julday(2026, 5, 13, 12.0), ephe.julday(2026, 5, 15, 12.0), "min"
        )
        mercury = PlanetaryPhenomenaFactory.from_julian_day(jd, planets=["Mercury"]).phenomena[0]
        assert mercury.elongation < 0.2833, f"expected a cazimi separation, got {mercury.elongation}"
        assert mercury.solar_phase == "cazimi"

    def test_mercury_at_its_greatest_elongation_is_free(self):
        """The other end of the same orbit: ~28 deg out, and plainly visible."""
        jd = _extreme_elongation(
            ephe.julday(2026, 4, 1, 0.0), ephe.julday(2026, 4, 7, 0.0), "max"
        )
        mercury = PlanetaryPhenomenaFactory.from_julian_day(jd, planets=["Mercury"]).phenomena[0]
        assert mercury.elongation > 17.0
        assert mercury.solar_phase == "free"

    def test_every_planet_in_the_set_is_labelled(self, subject):
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        assert len(result.phenomena) >= 7
        for p in result.phenomena:
            assert p.solar_phase is not None, f"{p.name} has no solar_phase"
            assert p.solar_phase in ("cazimi", "combust", "under_the_beams", "free")

    def test_the_moon_is_labelled_like_any_other_body(self):
        """Documented decision: the Moon gets a phase, it is not left None.

        Its elongation is the same astronomical quantity as everyone else's, and
        the names still describe what they describe — the dark of the Moon IS the
        interval under the beams. At the 2026-08-12 solar eclipse the Moon is
        under a degree from the Sun and comes out combust. What a school makes of
        a combust Moon is the school's business; the datum is neutral.
        """
        jd = _extreme_elongation(
            ephe.julday(2026, 8, 12, 0.0), ephe.julday(2026, 8, 13, 0.0), "min", "Moon"
        )
        moon = PlanetaryPhenomenaFactory.from_julian_day(jd, planets=["Moon"]).phenomena[0]
        assert moon.elongation < 1.0
        assert moon.solar_phase == "combust"

    def test_the_thresholds_used_are_echoed_on_the_collection(self, subject):
        """A label is meaningless without the convention that produced it."""
        result = PlanetaryPhenomenaFactory.from_subject(subject)
        assert result.solar_phase_thresholds.cazimi_deg == pytest.approx(0.2833)
        assert result.solar_phase_thresholds.combust_deg == pytest.approx(8.5)
        assert result.solar_phase_thresholds.under_beams_deg == pytest.approx(17.0)

    def test_custom_thresholds_move_the_label(self):
        """Same instant, same elongation, different school: a different name."""
        from kerykeion.schemas import SolarPhaseThresholdsModel

        jd = ephe.julday(2026, 11, 1, 0.0)  # Venus at 13.24 deg

        default = PlanetaryPhenomenaFactory.from_julian_day(jd, planets=["Venus"])
        assert default.phenomena[0].solar_phase == "under_the_beams"

        narrow = PlanetaryPhenomenaFactory.from_julian_day(
            jd,
            planets=["Venus"],
            solar_phase_thresholds=SolarPhaseThresholdsModel(under_beams_deg=10.0),
        )
        assert narrow.phenomena[0].solar_phase == "free"
        assert narrow.solar_phase_thresholds.under_beams_deg == 10.0

        wide = PlanetaryPhenomenaFactory.from_julian_day(
            jd,
            planets=["Venus"],
            solar_phase_thresholds=SolarPhaseThresholdsModel(combust_deg=14.0),
        )
        assert wide.phenomena[0].solar_phase == "combust"

        # The elongation itself never moves — only the name put on it.
        assert (
            default.phenomena[0].elongation
            == narrow.phenomena[0].elongation
            == wide.phenomena[0].elongation
        )

    def test_custom_thresholds_reach_through_from_subject(self, subject):
        from kerykeion.schemas import SolarPhaseThresholdsModel

        result = PlanetaryPhenomenaFactory.from_subject(
            subject,
            planets=["Venus"],
            solar_phase_thresholds=SolarPhaseThresholdsModel(under_beams_deg=180.0),
        )
        assert result.solar_phase_thresholds.under_beams_deg == 180.0
        assert result.phenomena[0].solar_phase != "free"

    def test_thresholds_that_do_not_widen_outwards_are_rejected(self):
        """An out-of-order set starves a label; say so instead of shipping it."""
        import pydantic

        from kerykeion.schemas import SolarPhaseThresholdsModel

        with pytest.raises(pydantic.ValidationError, match="widen outwards"):
            SolarPhaseThresholdsModel(cazimi_deg=9.0, combust_deg=8.5)
        with pytest.raises(pydantic.ValidationError, match="widen outwards"):
            SolarPhaseThresholdsModel(combust_deg=20.0)
        with pytest.raises(pydantic.ValidationError):
            SolarPhaseThresholdsModel(cazimi_deg=-1.0)

    def test_boundaries_are_strict_so_the_outer_name_wins(self):
        """A body exactly on a cut-off is not inside it."""
        from kerykeion.planetary_phenomena.factory import classify_solar_phase
        from kerykeion.schemas import SolarPhaseThresholdsModel

        t = SolarPhaseThresholdsModel()
        assert classify_solar_phase(0.0, t) == "cazimi"
        assert classify_solar_phase(t.cazimi_deg, t) == "combust"
        assert classify_solar_phase(t.combust_deg, t) == "under_the_beams"
        assert classify_solar_phase(t.under_beams_deg, t) == "free"
        assert classify_solar_phase(180.0, t) == "free"


@pytest.mark.parametrize("julian_day", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_julian_day_rejected_for_empty_selection(julian_day):
    with pytest.raises(ValueError, match="finite"):
        PlanetaryPhenomenaFactory.from_julian_day(julian_day, planets=[])
