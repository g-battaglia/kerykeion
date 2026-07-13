"""Unit tests for VoidOfCourseMoonFactory."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytz

from kerykeion import VoidOfCourseMoonFactory
from kerykeion.aspects.aspects_utils import difdeg2n
from kerykeion.ephemeris_backend import ephe
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import SIGN_CODES
from kerykeion.schemas.kr_models import VoidOfCourseAspectModel
from kerykeion.utilities import datetime_to_julian
from kerykeion.void_of_course_moon.utils import _BODY_ID

ASPECT_DEGREES = {0.0, 60.0, 90.0, 120.0, 180.0}
_IFLAG = ephe.FLG_SWIEPH | ephe.FLG_SPEED


def _rome_moment_utc(y, mo, d, h, mi):
    return pytz.timezone("Europe/Rome").localize(datetime(y, mo, d, h, mi)).astimezone(timezone.utc)


def test_structure_and_invariants():
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 5, 28, 12, 0, tz_str="Europe/Rome")
    assert voc.moon_sign in SIGN_CODES
    assert voc.next_sign in SIGN_CODES
    assert voc.next_sign == SIGN_CODES[(SIGN_CODES.index(voc.moon_sign) + 1) % 12]
    assert voc.void_end == voc.ingress
    assert voc.void_start <= voc.void_end
    assert isinstance(voc.is_void_of_course, bool)


def test_known_not_void():
    # On 2026-05-28 the Moon (in Scorpio) still has aspects to come before ingress.
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 5, 28, 12, 0, tz_str="Europe/Rome")
    assert voc.moon_sign == "Sco"
    assert voc.next_sign == "Sag"
    assert voc.is_void_of_course is False
    moment = _rome_moment_utc(2026, 5, 28, 12, 0)
    assert voc.next_aspect is not None
    # next_aspect is the first aspect in the *next* sign — strictly after the
    # ingress, and never a duplicate of the last in-sign aspect.
    assert voc.next_aspect.exact_time > voc.ingress
    assert voc.last_aspect is not None
    assert (voc.next_aspect.planet, voc.next_aspect.exact_time) != (
        voc.last_aspect.planet,
        voc.last_aspect.exact_time,
    )
    assert voc.void_start > moment


def test_known_void():
    # On 2026-06-01 09:00 the Moon (late Sagittarius) is coasting void to Capricorn.
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 6, 1, 9, 0, tz_str="Europe/Rome")
    assert voc.moon_sign == "Sag"
    assert voc.next_sign == "Cap"
    assert voc.is_void_of_course is True
    # Even while void, next_aspect reports the first aspect in the next sign (Cap) —
    # the moment the void lull ends — rather than None.
    assert voc.next_aspect is not None
    assert voc.next_aspect.exact_time > voc.ingress
    assert voc.void_start <= _rome_moment_utc(2026, 6, 1, 9, 0)


def test_next_aspect_is_first_in_next_sign():
    # Regression: next_aspect used to be drawn from the *current* sign's aspect list,
    # so querying before the last in-sign aspect collapsed it onto last_aspect
    # (the Jupiter trine in Scorpio). It must instead be the first aspect the Moon
    # makes after ingressing into the next sign.
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 5, 29, 12, 0, tz_str="Europe/Rome")
    assert voc.moon_sign == "Sco"
    assert voc.last_aspect is not None
    assert voc.next_aspect is not None
    # Distinct event, strictly after the ingress.
    assert voc.next_aspect.exact_time > voc.ingress
    assert (voc.next_aspect.planet, voc.next_aspect.aspect, voc.next_aspect.exact_time) != (
        voc.last_aspect.planet,
        voc.last_aspect.aspect,
        voc.last_aspect.exact_time,
    )
    # next_aspect is geometrically inside the next sign.
    jd = datetime_to_julian(voc.next_aspect.exact_time)
    moon = ephe.calc_ut(jd, ephe.MOON, _IFLAG)[0][0]
    assert int(moon // 30) % 12 == SIGN_CODES.index(voc.next_sign)


def test_last_aspect_is_exact():
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 5, 28, 12, 0, tz_str="Europe/Rome")
    last = voc.last_aspect
    assert last is not None
    assert last.planet in {"Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
    assert last.aspect_degrees in ASPECT_DEGREES
    # Re-evaluate the geometry at the reported instant: separation must equal the aspect.
    jd = datetime_to_julian(last.exact_time)
    moon = ephe.calc_ut(jd, ephe.MOON, _IFLAG)[0][0]
    other = ephe.calc_ut(jd, _BODY_ID[last.planet], _IFLAG)[0][0]
    assert abs(abs(difdeg2n(moon, other)) - last.aspect_degrees) < 0.1


def test_ingress_on_sign_boundary():
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 5, 28, 12, 0, tz_str="Europe/Rome")
    jd = datetime_to_julian(voc.ingress)
    moon = ephe.calc_ut(jd, ephe.MOON, _IFLAG)[0][0]
    distance_to_cusp = min(moon % 30.0, 30.0 - (moon % 30.0))
    assert distance_to_cusp < 0.05


def test_sidereal_shifts_sign():
    tropical = VoidOfCourseMoonFactory.from_datetime(2026, 6, 1, 9, 0, tz_str="Europe/Rome")
    sidereal = VoidOfCourseMoonFactory.from_datetime(
        2026, 6, 1, 9, 0, tz_str="Europe/Rome", zodiac_type="Sidereal", sidereal_mode="LAHIRI"
    )
    # The Lahiri ayanamsha (~24°) pulls the Moon back into the previous sign.
    assert sidereal.moon_sign in SIGN_CODES
    assert sidereal.moon_sign != tropical.moon_sign
    # The next-sign next_aspect semantics hold under a sidereal zodiac too: the
    # second scan runs with FLG_SIDEREAL, so next_aspect lands after the ingress
    # and stays distinct from last_aspect.
    assert sidereal.next_aspect is not None
    assert sidereal.next_aspect.exact_time > sidereal.ingress
    if sidereal.last_aspect is not None:
        assert (sidereal.next_aspect.planet, sidereal.next_aspect.exact_time) != (
            sidereal.last_aspect.planet,
            sidereal.last_aspect.exact_time,
        )


def test_sidereal_requires_mode():
    with pytest.raises(KerykeionException):
        VoidOfCourseMoonFactory.from_datetime(2026, 6, 1, 9, 0, tz_str="Europe/Rome", zodiac_type="Sidereal")


def test_sidereal_user_requires_custom_parameters():
    with pytest.raises(KerykeionException):
        VoidOfCourseMoonFactory.from_datetime(
            2026, 6, 1, 9, 0, tz_str="Europe/Rome", zodiac_type="Sidereal", sidereal_mode="USER"
        )


def test_late_aspect_near_ingress_is_not_dropped():
    voc = VoidOfCourseMoonFactory.from_datetime(2020, 2, 1, 12, 0, tz_str="UTC")
    assert voc.last_aspect is not None
    assert voc.last_aspect.planet == "Mercury"
    assert voc.last_aspect.aspect == "square"
    expected = datetime(2020, 2, 3, 11, 27, tzinfo=timezone.utc)
    assert abs((voc.last_aspect.exact_time - expected).total_seconds()) < 120
    assert voc.void_start == voc.last_aspect.exact_time


def test_voc_aspect_model_rejects_out_of_domain_values():
    exact_time = datetime(2026, 5, 28, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        VoidOfCourseAspectModel(planet="Moon", aspect="square", aspect_degrees=90.0, exact_time=exact_time)
    with pytest.raises(ValueError):
        VoidOfCourseAspectModel(planet="Mercury", aspect="square", aspect_degrees=60.0, exact_time=exact_time)


def test_invalid_timezone_raises():
    with pytest.raises(KerykeionException):
        VoidOfCourseMoonFactory.from_datetime(2026, 5, 28, 12, 0, tz_str="Not/AZone")


def test_range_edge_dates_raise_kerykeion_exception():
    """R23: near either end of the ephemeris the forward/backward Moon scans walk
    off the edge; the raw backend range error must be normalized to the
    documented KerykeionException, not leak (was raw EphemerisRangeError).

    The probe dates sit just inside the medium (DE440) kernel's ~1550/2650
    edges; on base kernels they are out of range outright and on extended
    kernels the scans never leave the range, so the scenario only exists on
    the medium kernel.
    """
    from tests.conftest import _detect_ephemeris_tier

    if _detect_ephemeris_tier() != "medium":
        pytest.skip("Requires the medium (DE440) kernel's range edges (~1550/2650).")
    with pytest.raises(KerykeionException, match="ephemeris range"):
        VoidOfCourseMoonFactory.from_datetime(2650, 1, 20, 12, 0, tz_str="Europe/Rome")
    with pytest.raises(KerykeionException, match="ephemeris range"):
        VoidOfCourseMoonFactory.from_datetime(1550, 1, 2, 12, 0, tz_str="Europe/Rome")


def test_normal_date_unaffected_by_range_normalization():
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 6, 1, 12, 0, tz_str="Europe/Rome")
    assert isinstance(voc.is_void_of_course, bool)
    assert voc.moon_sign in SIGN_CODES


# =============================================================================
# from_iso_range — void windows over a range
# =============================================================================


class TestVoidWindowsRange:
    """Range scan: every void window intersecting the range, unclipped."""

    def test_january_2025_window_count_and_ordering(self):
        res = VoidOfCourseMoonFactory.from_iso_range("2025-01-01", "2025-01-31")
        # ~13.7 Moon sign spans per month; the first window is the one already
        # open at range start (unclipped), so 12-15 windows are expected.
        assert 12 <= len(res.windows) <= 15
        for prev, cur in zip(res.windows, res.windows[1:]):
            assert prev.void_end <= cur.void_start, "windows must not overlap"
        # Signs chain: each window's next_sign is the following window's moon_sign.
        for prev, cur in zip(res.windows, res.windows[1:]):
            assert prev.next_sign == cur.moon_sign

    def test_windows_cross_check_with_single_moment(self):
        res = VoidOfCourseMoonFactory.from_iso_range("2025-01-01", "2025-01-31")
        for window in res.windows[2:5]:
            mid = window.void_start + (window.void_end - window.void_start) / 2
            single = VoidOfCourseMoonFactory.from_datetime(
                mid.year, mid.month, mid.day, mid.hour, mid.minute, tz_str="UTC"
            )
            assert single.is_void_of_course
            assert abs((single.void_start - window.void_start).total_seconds()) < 2
            assert abs((single.void_end - window.void_end).total_seconds()) < 2

    def test_moment_between_windows_is_not_void(self):
        res = VoidOfCourseMoonFactory.from_iso_range("2025-01-01", "2025-01-31")
        # A moment right between window N's end (ingress) and window N+1's
        # start is inside a sign with aspects still to perfect: not void.
        gap_mid = res.windows[1].void_end + (res.windows[2].void_start - res.windows[1].void_end) / 2
        single = VoidOfCourseMoonFactory.from_datetime(
            gap_mid.year, gap_mid.month, gap_mid.day, gap_mid.hour, gap_mid.minute, tz_str="UTC"
        )
        assert not single.is_void_of_course

    def test_straddling_window_included_unclipped(self):
        res = VoidOfCourseMoonFactory.from_iso_range("2025-01-01", "2025-01-31")
        first = res.windows[0]
        # Dec 31 2024 19:02 UTC opens a void that ends Jan 1 10:49 — it must be
        # present and keep its pre-range start.
        assert first.void_start.month == 12 and first.void_start.day == 31
        assert first.void_end.month == 1 and first.void_end.day == 1

    def test_duration_consistency(self):
        res = VoidOfCourseMoonFactory.from_iso_range("2025-01-01", "2025-01-31")
        for window in res.windows:
            expected = (window.void_end - window.void_start).total_seconds() / 60.0
            assert window.duration_minutes == pytest.approx(expected, abs=0.02)

    def test_malformed_iso_raises_kerykeion_exception(self):
        with pytest.raises(KerykeionException, match="Invalid ISO"):
            VoidOfCourseMoonFactory.from_iso_range("nope", "2025-01-31")

    def test_empty_range_yields_no_windows(self):
        res = VoidOfCourseMoonFactory.from_iso_range("2025-01-31", "2025-01-01")
        assert res.windows == []

    def test_civil_range_overflow_normalized_to_kerykeion_exception(self, monkeypatch):
        # Near the year-1 boundary the sign-by-sign Moon walk can step before
        # 1 CE, where julian_day_to_utc raises a bare OverflowError/ValueError
        # (Python's datetime has no BCE support). from_iso_range must normalize
        # BOTH to KerykeionException (like the single-moment path) rather than
        # leaking a 500 downstream. Exercise the widened catch directly, so the
        # test is kernel-independent.
        import kerykeion.void_of_course_moon.factory as fac

        for exc_type in (ValueError, OverflowError):
            def boom(*a, **k):
                raise exc_type("simulated civil-range overflow")

            monkeypatch.setattr(fac, "compute_void_windows", boom)
            with pytest.raises(KerykeionException, match="narrow the date range"):
                VoidOfCourseMoonFactory.from_iso_range("2025-01-01", "2025-01-31")

    def test_backend_range_error_normalized_to_kerykeion_exception(self, monkeypatch):
        import kerykeion.void_of_course_moon.factory as fac

        assert fac._BACKEND_ERROR_TYPES, "active ephemeris backend must expose an Error type"

        def boom(*args, **kwargs):
            raise fac._BACKEND_ERROR_TYPES[0]("simulated ephemeris range failure")

        monkeypatch.setattr(fac, "compute_void_windows", boom)
        with pytest.raises(KerykeionException, match="narrow the date range"):
            VoidOfCourseMoonFactory.from_iso_range("2025-01-01", "2025-01-31")

    def test_year_one_edge_never_leaks_a_bare_error(self):
        # A range at the very start of the civil calendar must never surface a
        # non-KerykeionException. Depending on the installed kernel it either
        # raises KerykeionException (out of ephemeris range, or the civil-range
        # overflow above) or stays in range and returns windows — but never a
        # raw ValueError/OverflowError/backend error.
        try:
            res = VoidOfCourseMoonFactory.from_iso_range("0001-01-01", "0001-02-15")
        except KerykeionException:
            pass  # acceptable: normalized to the documented exception type
        except Exception as exc:  # noqa: BLE001 — the whole point is to catch leaks
            pytest.fail(f"expected KerykeionException, got {type(exc).__name__}: {exc}")
        else:
            assert isinstance(res.windows, list)

    def test_sidereal_windows_shift_signs_not_aspects(self):
        tropical = VoidOfCourseMoonFactory.from_iso_range("2025-01-01", "2025-01-15")
        sidereal = VoidOfCourseMoonFactory.from_iso_range(
            "2025-01-01", "2025-01-15", zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        # Sidereal sign boundaries sit ~24° earlier, so windows differ — but
        # both scans produce a coherent, ordered set.
        assert 5 <= len(sidereal.windows) <= 9
        for prev, cur in zip(sidereal.windows, sidereal.windows[1:]):
            assert prev.void_end <= cur.void_start
        assert tropical.windows[0].void_end != sidereal.windows[0].void_end
