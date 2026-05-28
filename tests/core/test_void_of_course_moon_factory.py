"""Unit tests for VoidOfCourseMoonFactory."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytz

from kerykeion import VoidOfCourseMoonFactory
from kerykeion.aspects.aspects_utils import difdeg2n
from kerykeion.ephemeris_backend import swe
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import SIGN_CODES
from kerykeion.schemas.kr_models import VoidOfCourseAspectModel
from kerykeion.utilities import datetime_to_julian
from kerykeion.void_of_course_moon.utils import _BODY_ID

ASPECT_DEGREES = {0.0, 60.0, 90.0, 120.0, 180.0}
_IFLAG = swe.FLG_SWIEPH | swe.FLG_SPEED


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
    assert voc.next_aspect.exact_time > moment
    assert voc.void_start > moment


def test_known_void():
    # On 2026-06-01 09:00 the Moon (late Sagittarius) is coasting void to Capricorn.
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 6, 1, 9, 0, tz_str="Europe/Rome")
    assert voc.moon_sign == "Sag"
    assert voc.next_sign == "Cap"
    assert voc.is_void_of_course is True
    assert voc.next_aspect is None
    assert voc.void_start <= _rome_moment_utc(2026, 6, 1, 9, 0)


def test_last_aspect_is_exact():
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 5, 28, 12, 0, tz_str="Europe/Rome")
    last = voc.last_aspect
    assert last is not None
    assert last.planet in {"Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
    assert last.aspect_degrees in ASPECT_DEGREES
    # Re-evaluate the geometry at the reported instant: separation must equal the aspect.
    jd = datetime_to_julian(last.exact_time)
    moon = swe.calc_ut(jd, swe.MOON, _IFLAG)[0][0]
    other = swe.calc_ut(jd, _BODY_ID[last.planet], _IFLAG)[0][0]
    assert abs(abs(difdeg2n(moon, other)) - last.aspect_degrees) < 0.1


def test_ingress_on_sign_boundary():
    voc = VoidOfCourseMoonFactory.from_datetime(2026, 5, 28, 12, 0, tz_str="Europe/Rome")
    jd = datetime_to_julian(voc.ingress)
    moon = swe.calc_ut(jd, swe.MOON, _IFLAG)[0][0]
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
