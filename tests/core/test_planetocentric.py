# -*- coding: utf-8 -*-
"""Tests for planetocentric perspective calculations.

These tests verify that planetocentric charts actually differ from geocentric
charts, catching silent fallbacks to geocentric data.
"""

import pytest
from kerykeion import AstrologicalSubjectFactory


# ---------------------------------------------------------------------------
# Shared birth data for consistent comparisons
# ---------------------------------------------------------------------------
_BIRTH_KWARGS = dict(
    year=2000, month=1, day=1, hour=12, minute=0,
    lng=0.0, lat=51.5, tz_str="Etc/GMT",
    city="Greenwich", nation="GB", online=False,
)


def _angular_diff(a: float, b: float) -> float:
    """Shortest angular difference between two ecliptic longitudes (0-180)."""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def geocentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Geocentric", **_BIRTH_KWARGS,
    )


@pytest.fixture(scope="module")
def marscentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Marscentric", **_BIRTH_KWARGS, perspective_type="Marscentric",
    )


@pytest.fixture(scope="module")
def jupitercentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Jupitercentric", **_BIRTH_KWARGS, perspective_type="Jupitercentric",
    )


@pytest.fixture(scope="module")
def venuscentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Venuscentric", **_BIRTH_KWARGS, perspective_type="Venuscentric",
    )


@pytest.fixture(scope="module")
def selenocentric():
    return AstrologicalSubjectFactory.from_birth_data(
        "Selenocentric", **_BIRTH_KWARGS, perspective_type="Selenocentric",
    )


# List of planet attribute names we can compare across subjects.
# Sun is excluded because calc_pctr for the Sun requires the sepl_*.se1
# planetary ephemeris file which is not bundled; the factory silently falls
# back to geocentric for any body whose calc_pctr call fails.
_COMPARABLE_PLANETS = ["moon", "mercury", "venus", "mars", "jupiter", "saturn"]


# ---------------------------------------------------------------------------
# 1. Basic creation and perspective_type stored correctly
# ---------------------------------------------------------------------------
class TestPerspectiveTypeStored:
    """Verify that the perspective_type attribute is recorded on the model."""

    @pytest.mark.parametrize("perspective", [
        "Marscentric", "Jupitercentric", "Venuscentric", "Selenocentric",
    ])
    def test_perspective_type_attribute(self, perspective):
        s = AstrologicalSubjectFactory.from_birth_data(
            f"{perspective} Test", **_BIRTH_KWARGS,
            perspective_type=perspective,
        )
        assert s.perspective_type == perspective

    def test_default_perspective_is_apparent_geocentric(self, geocentric):
        assert geocentric.perspective_type == "Apparent Geocentric"

    @pytest.mark.parametrize("perspective", [
        "Marscentric", "Jupitercentric", "Venuscentric", "Selenocentric",
    ])
    def test_creates_valid_chart_with_positions(self, perspective):
        s = AstrologicalSubjectFactory.from_birth_data(
            f"{perspective} Test", **_BIRTH_KWARGS,
            perspective_type=perspective,
        )
        assert s is not None
        assert s.sun is not None
        assert 0 <= s.sun.abs_pos < 360
        if perspective == "Selenocentric":
            # The Moon is the center body: excluded rather than mislabelled.
            assert s.moon is None
        else:
            assert s.moon is not None
            assert 0 <= s.moon.abs_pos < 360


# ---------------------------------------------------------------------------
# 2. KEY ASSERTION: planetocentric positions differ from geocentric
# ---------------------------------------------------------------------------
class TestPositionsDifferFromGeocentric:
    """At least one planet must differ by >0.01 degrees from geocentric.

    This is the critical test that catches a silent fallback to geocentric
    data.  For each planetocentric perspective, we compare every comparable
    planet and require at least one measurable difference.

    Note: The Sun position may silently fall back to geocentric when the
    sepl_*.se1 planetary ephemeris file is unavailable.  We exclude it from
    the comparison set and focus on Moon through Saturn, which use the
    seas_*.se1 or internal Moshier fallback successfully.
    """

    @pytest.mark.parametrize("perspective_fixture,center_attr", [
        ("marscentric", "mars"),
        ("jupitercentric", "jupiter"),
        ("venuscentric", "venus"),
        ("selenocentric", "moon"),
    ])
    def test_at_least_one_planet_differs(
        self, perspective_fixture, center_attr, geocentric, request,
    ):
        pctr = request.getfixturevalue(perspective_fixture)
        max_diff = 0.0
        diffs = {}
        for planet in _COMPARABLE_PLANETS:
            geo_point = getattr(geocentric, planet)
            pctr_point = getattr(pctr, planet)
            if geo_point is None or pctr_point is None:
                continue
            diff = _angular_diff(geo_point.abs_pos, pctr_point.abs_pos)
            diffs[planet] = diff
            if diff > max_diff:
                max_diff = diff

        assert max_diff > 0.01, (
            f"{perspective_fixture} positions are identical to geocentric "
            f"(max diff={max_diff:.6f} deg). Likely silent fallback! "
            f"Diffs: {diffs}"
        )


# ---------------------------------------------------------------------------
# 3. Center body behavior: excluded from the chart with a warning — from Mars
#    there is no "position of Mars", and storing the geocentric position under
#    a planetocentric label put a wrong-frame value into aspects and houses.
# ---------------------------------------------------------------------------
class TestCenterBodyExcluded:
    @pytest.mark.parametrize("perspective_fixture,center_attr,center_name", [
        ("marscentric", "mars", "Mars"),
        ("jupitercentric", "jupiter", "Jupiter"),
        ("venuscentric", "venus", "Venus"),
        ("selenocentric", "moon", "Moon"),
    ])
    def test_center_body_absent(self, perspective_fixture, center_attr, center_name, request):
        pctr = request.getfixturevalue(perspective_fixture)
        assert getattr(pctr, center_attr) is None
        assert center_name not in pctr.active_points

    def test_chokepoint_guard_skips_center_body_directly(self):
        """The exclusion lives in _calculate_single_planet — the single point
        through which every planetary position is stored — so ANY path (not
        just the resolution filter) inherits it."""
        from kerykeion.ephemeris_backend import ephe

        data: dict = {}
        calculated: list = []
        AstrologicalSubjectFactory._calculate_single_planet(
            data, "Mars", ephe.MARS, 2451545.0, ephe.FLG_SWIEPH,
            [0.0] * 12, "AstrologicalPoint", calculated, [],
            center_body_id=ephe.MARS,
        )
        assert "mars" not in data
        assert "Mars" not in calculated

    def test_exclusion_warning_fired(self, caplog):
        with caplog.at_level("WARNING"):
            AstrologicalSubjectFactory.from_birth_data(
                "Warn Test", **_BIRTH_KWARGS,
                perspective_type="Selenocentric",
            )
        assert "center body" in caplog.text

    def test_explicit_request_drops_only_center(self, caplog):
        with caplog.at_level("WARNING"):
            s = AstrologicalSubjectFactory.from_birth_data(
                "Explicit Test", **_BIRTH_KWARGS,
                perspective_type="Selenocentric",
                active_points=["Sun", "Moon"],
            )
        assert s.sun is not None
        assert s.moon is None
        assert "center body" in caplog.text

    def test_only_center_requested_raises(self):
        # An explicit list reduced to nothing would invert into 'no filter'
        # (a full chart) — the factory must refuse instead.
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="center body"):
            AstrologicalSubjectFactory.from_birth_data(
                "Empty Filter Test", **_BIRTH_KWARGS,
                perspective_type="Selenocentric",
                active_points=["Moon"],
            )

    def test_arabic_part_prerequisite_not_resurrected(self, caplog):
        with caplog.at_level("WARNING"):
            s = AstrologicalSubjectFactory.from_birth_data(
                "Arabic Part Test", **_BIRTH_KWARGS,
                perspective_type="Selenocentric",
                active_points=["Ascendant", "Sun", "Pars_Fortunae"],
            )
        # Pars Fortunae needs the Moon; a geocentric Moon must not be
        # silently mixed into a selenocentric chart to compute it.
        assert s.moon is None
        assert getattr(s, "pars_fortunae", None) is None
        assert "Pars_Fortunae" not in (s.active_points or [])

    def test_selenocentric_lunar_phase_is_none(self, selenocentric):
        assert selenocentric.lunar_phase is None

    def test_selenocentric_chart_renders(self, selenocentric):
        from kerykeion import ChartDataFactory, ChartDrawer

        chart_data = ChartDataFactory.create_natal_chart_data(selenocentric)
        drawer = ChartDrawer(chart_data=chart_data, theme="dark")
        assert len(drawer.generate_svg_string()) > 1000
        assert len(drawer.generate_svg_string(style="modern")) > 1000


# ---------------------------------------------------------------------------
# 4. Non-center planets should differ dramatically from geocentric
#    (for outer-planet perspectives the angular shift is large).
# ---------------------------------------------------------------------------
class TestNonCenterPlanetsDifferSignificantly:
    """Specific planets that should show large shifts in planetocentric views.

    When viewing from Mars or Jupiter, inner planets like Moon and Mercury
    appear at very different ecliptic longitudes compared to geocentric.
    """

    def test_marscentric_moon_differs_dramatically(self, marscentric, geocentric):
        """Moon seen from Mars should differ by many degrees from geocentric."""
        diff = _angular_diff(marscentric.moon.abs_pos, geocentric.moon.abs_pos)
        assert diff > 1.0, (
            f"Marscentric Moon diff={diff:.4f} deg is too small; "
            f"expected a large shift when viewed from Mars."
        )

    def test_marscentric_mercury_differs_dramatically(self, marscentric, geocentric):
        diff = _angular_diff(marscentric.mercury.abs_pos, geocentric.mercury.abs_pos)
        assert diff > 1.0, (
            f"Marscentric Mercury diff={diff:.4f} deg is too small."
        )

    def test_jupitercentric_mars_differs_dramatically(self, jupitercentric, geocentric):
        """Mars seen from Jupiter should differ by many degrees."""
        diff = _angular_diff(jupitercentric.mars.abs_pos, geocentric.mars.abs_pos)
        assert diff > 1.0, (
            f"Jupitercentric Mars diff={diff:.4f} deg is too small."
        )

    def test_jupitercentric_moon_differs_dramatically(self, jupitercentric, geocentric):
        diff = _angular_diff(jupitercentric.moon.abs_pos, geocentric.moon.abs_pos)
        assert diff > 1.0, (
            f"Jupitercentric Moon diff={diff:.4f} deg is too small."
        )

    def test_venuscentric_moon_differs_dramatically(self, venuscentric, geocentric):
        """Moon seen from Venus should differ enormously."""
        diff = _angular_diff(venuscentric.moon.abs_pos, geocentric.moon.abs_pos)
        assert diff > 1.0, (
            f"Venuscentric Moon diff={diff:.4f} deg is too small."
        )

    def test_selenocentric_mercury_differs(self, selenocentric, geocentric):
        """Mercury seen from the Moon differs slightly (Moon is close to Earth)."""
        diff = _angular_diff(selenocentric.mercury.abs_pos, geocentric.mercury.abs_pos)
        # Moon is close to Earth, so differences are small but still measurable
        assert diff > 0.01, (
            f"Selenocentric Mercury diff={diff:.6f} deg; expected >0.01."
        )


# ---------------------------------------------------------------------------
# 5. All positions remain valid (within 0-360 range)
# ---------------------------------------------------------------------------
class TestAllPositionsValid:
    """Every planet on every planetocentric chart should have abs_pos in [0, 360)."""

    _ALL_PLANETS = [
        "sun", "moon", "mercury", "venus", "mars",
        "jupiter", "saturn", "uranus", "neptune", "pluto",
    ]

    @pytest.mark.parametrize("perspective_fixture", [
        "marscentric", "jupitercentric", "venuscentric", "selenocentric",
    ])
    def test_all_positions_in_range(self, perspective_fixture, request):
        pctr = request.getfixturevalue(perspective_fixture)
        for planet in self._ALL_PLANETS:
            point = getattr(pctr, planet, None)
            if point is not None:
                assert 0 <= point.abs_pos < 360, (
                    f"{perspective_fixture}.{planet}.abs_pos = {point.abs_pos} "
                    f"is out of [0, 360) range"
                )


# ---------------------------------------------------------------------------
# 6. Timescale: calc_pctr takes TT/ET, not UT
# ---------------------------------------------------------------------------
class TestCalcPctrTimescale:
    """v6 regression: ephe.calc_pctr takes a TT/ET julian day on both backends.

    Passing the raw UT julian day slips every planetocentric position by
    delta-T (~64 s in 2000, i.e. up to ~0.01 deg for the Moon).
    """

    def test_calc_pctr_receives_tt_julian_day(self, monkeypatch):
        from kerykeion.ephemeris_backend import ephe

        received = []
        real_calc_pctr = ephe.calc_pctr

        def spy_calc_pctr(tjdet, planet, center, flags):
            received.append(tjdet)
            return real_calc_pctr(tjdet, planet, center, flags)

        monkeypatch.setattr(ephe, "calc_pctr", spy_calc_pctr)

        subject = AstrologicalSubjectFactory.from_birth_data(
            "TT Timescale Check", **_BIRTH_KWARGS, perspective_type="Marscentric",
        )

        assert received, "calc_pctr was never called for a planetocentric chart"
        jd_ut = subject.julian_day
        expected_tt = jd_ut + ephe.deltat(jd_ut)
        for tjdet in received:
            assert tjdet == pytest.approx(expected_tt, abs=1e-9), (
                f"calc_pctr received {tjdet!r}, expected UT+deltaT {expected_tt!r}"
            )
            # delta-T in 2000 is ~64 s (~7.4e-4 days): the raw UT day is
            # measurably different, so this also fails if deltaT is dropped.
            assert abs(tjdet - jd_ut) > 1e-5


class TestOutOfBoundsPerspectiveGating:
    def test_oob_unset_for_non_geocentric_perspectives(self):
        """is_out_of_bounds compares declination against the geocentric ecliptic
        obliquity, which is meaningless for heliocentric/planetocentric frames —
        it must be None there, and computed for geocentric charts."""
        geo = AstrologicalSubjectFactory.from_birth_data(
            "Geo OOB", **_BIRTH_KWARGS,
        )
        helio = AstrologicalSubjectFactory.from_birth_data(
            "Helio OOB", **_BIRTH_KWARGS, perspective_type="Heliocentric",
        )
        assert geo.sun.is_out_of_bounds is not None
        # For a heliocentric chart the OOB flag must be unset (the
        # declination-vs-obliquity test is geocentric). The Sun is the center
        # body there (excluded), so check a present heliocentric point instead.
        assert helio.moon is not None
        assert helio.moon.is_out_of_bounds is None


class TestDegenerateCenterBodyExclusion:
    """Round-3 regression: the perspective's center body (Earth in
    geocentric/topocentric, Sun in heliocentric, the center planet in
    planetocentric) has no position as seen from itself and must be excluded —
    otherwise it is a phantom pinned at 0 Aries that fabricates spurious aspects."""

    def test_earth_excluded_in_geocentric(self):
        geo = AstrologicalSubjectFactory.from_birth_data(
            "Geo", **_BIRTH_KWARGS, active_points=["Sun", "Moon", "Earth"],
        )
        assert geo.earth is None
        assert "Earth" not in geo.active_points

    def test_sun_excluded_in_heliocentric_earth_real(self):
        helio = AstrologicalSubjectFactory.from_birth_data(
            "Helio", **_BIRTH_KWARGS, perspective_type="Heliocentric",
            active_points=["Sun", "Moon", "Earth"],
        )
        assert helio.sun is None                      # Sun is the center -> excluded
        assert "Sun" not in helio.active_points
        assert helio.earth is not None                # Earth is real in heliocentric
        assert helio.earth.abs_pos != 0.0 or helio.earth.speed != 0.0

    def test_no_phantom_earth_aspects_in_geocentric(self):
        from kerykeion.chart_data_factory import ChartDataFactory

        geo = AstrologicalSubjectFactory.from_birth_data(
            "Geo", **_BIRTH_KWARGS, active_points=["Sun", "Moon", "Mars", "Earth"],
        )
        cd = ChartDataFactory.create_natal_chart_data(geo)
        assert not [a for a in cd.aspects if "Earth" in (a.p1_name, a.p2_name)]

    def test_heliocentric_synastry_skips_relationship_score(self):
        """A synastry whose partners have no natal Sun (heliocentric) must not
        crash the relationship-score path — the score is geocentric and is skipped."""
        from kerykeion.chart_data_factory import ChartDataFactory

        john = AstrologicalSubjectFactory.from_birth_data(
            "John", **_BIRTH_KWARGS, perspective_type="Heliocentric",
            active_points=["Sun", "Moon", "Mars"],
        )
        paul = AstrologicalSubjectFactory.from_birth_data(
            "Paul", 1942, 6, 18, 15, 30, lng=0.0, lat=51.5, tz_str="Etc/GMT",
            city="Greenwich", nation="GB", online=False, perspective_type="Heliocentric",
            active_points=["Sun", "Moon", "Mars"], suppress_geonames_warning=True,
        )
        cd = ChartDataFactory.create_synastry_chart_data(john, paul)  # default score=True
        assert cd.relationship_score is None
