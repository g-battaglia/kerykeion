"""Sun-vs-horizon measured as an ANGLE, by a second implementation.

The anchors next door compare our instants to published instants. That works at
mid latitudes and stops working near the poles, where the Sun grazes the horizon:
`dh/dt` collapses, so a milliarcsecond of altitude becomes minutes of clock and
the comparison starts measuring conditioning instead of correctness. Measured on
this grid, one arcminute of error is worth 4 s of time at Quito and 200 s at
Tromso in mid-May — a fifty-fold swing in what "the same error" looks like.

So this module never compares times. It takes the instant we return and asks an
independent implementation where the Sun actually was. The answer is an angle,
which does not deform with latitude, and it must be the same angle everywhere:

    at every sunrise and sunset, the Sun's true upper limb is on the refracted
    horizon;
    at every solar noon, the Sun's hour angle is zero;
    at the instant `is_diurnal` flips, the Sun's geometric centre is at 0.

The second opinion is Skyfield reading its own de421 kernel — and honesty about
HOW second it is: the ephemeris backend is itself built on Skyfield's machinery
(timescale, frames, aberration), so a common-mode error inside Skyfield would
move both sides together and pass here unseen. Absolute truth is the anchors'
job, at the latitudes where published instants are well conditioned. What this
module does isolate is everything KERYKEION adds on top of the backend: the
Julian-Day and timezone bookkeeping, the event search and its pairing, the
transit-vs-midpoint choice, and the horizon convention itself. A midpoint
regression, a wrong search seed or a dropped refraction term fails here (proven
by mutation); a Skyfield frame bug would not, and no test here claims otherwise.

Needs `skyfield` and `skyfield-data`, both already present as transitive
dependencies of the ephemeris backend.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest

from kerykeion import AstrologicalSubjectFactory, SunTimesFactory

skyfield_api = pytest.importorskip("skyfield.api")
skyfield_data = pytest.importorskip("skyfield_data")

_SOLAR_RADIUS_AU = 696000.0 / 149597870.700

#: True altitude of the Sun's upper limb at a rise/set we return. It is minus the
#: atmospheric refraction at the apparent horizon under the standard atmosphere
#: the backend is driven with (1013.25 hPa, 15 C). Measured over the grid below
#: the spread is 2.5", so this is an invariant and not an average.
_LIMB_ON_HORIZON_ARCMIN = -33.59

#: ~2.7x the observed spread. Tight enough to fail on a dropped solar parallax
#: (8.8" = 0.147') or a switch to a fixed semidiameter; loose enough that no
#: amount of ordinary ephemeris noise can reach it.
_LIMB_TOL_ARCMIN = 0.06

#: Hour angle at solar noon, in seconds of time. Measured worst case is 0.083 s;
#: 2 s leaves an enormous margin and still fails the moment solar noon reverts to
#: the sunrise/sunset midpoint, which is 20-60 s away from the meridian at these
#: latitudes.
_TRANSIT_HOUR_ANGLE_TOL_S = 2.0

_GRID = [
    ("quito", -0.1807, -78.4678, 2026, 3, 20),
    ("rome_equinox", 41.9028, 12.4964, 2026, 3, 20),
    ("rome_solstice", 41.9028, 12.4964, 2026, 6, 21),
    ("london", 51.5074, -0.1278, 2026, 8, 5),
    ("sydney", -33.8688, 151.2093, 2026, 12, 21),
    ("reykjavik", 64.1466, -21.9426, 2026, 4, 15),
    ("tromso", 69.6492, 18.9553, 2026, 4, 5),
    ("ushuaia", -54.8019, -68.3030, 2026, 9, 22),
    ("nairobi", -1.2921, 36.8219, 2026, 1, 15),
    ("singapore", 1.3521, 103.8198, 2026, 8, 5),
]


@pytest.fixture(scope="module")
def oracle():
    """Skyfield, loaded once: the second implementation everything is checked against."""
    loader = skyfield_api.Loader(skyfield_data.get_skyfield_data_path(), verbose=False)
    ephemeris = loader("de421.bsp")
    return {
        "ts": loader.timescale(),
        "earth": ephemeris["earth"],
        "sun": ephemeris["sun"],
        "wgs84": skyfield_api.wgs84,
    }


def _observer(oracle, latitude: float, longitude: float):
    return oracle["earth"] + oracle["wgs84"].latlon(latitude, longitude, elevation_m=0)


def _true_altitude_and_semidiameter(oracle, moment: dt.datetime, latitude: float, longitude: float):
    """Independent (altitude, semidiameter) in arcminutes at `moment`."""
    apparent = _observer(oracle, latitude, longitude).at(oracle["ts"].from_datetime(moment)).observe(oracle["sun"]).apparent()
    altitude, _azimuth, distance = apparent.altaz()
    semidiameter = math.degrees(math.asin(_SOLAR_RADIUS_AU / distance.au))
    return altitude.degrees * 60.0, semidiameter * 60.0


def _hour_angle_seconds(oracle, moment: dt.datetime, latitude: float, longitude: float) -> float:
    """Independent hour angle at `moment`, in seconds of time (0 = on the meridian)."""
    time = oracle["ts"].from_datetime(moment)
    right_ascension, _declination, _distance = (
        _observer(oracle, latitude, longitude).at(time).observe(oracle["sun"]).apparent().radec(epoch="date")
    )
    hours = (time.gast + longitude / 15.0 - right_ascension.hours) % 24.0
    if hours > 12.0:
        hours -= 24.0
    return hours * 3600.0


def _sun_times(latitude: float, longitude: float, year: int, month: int, day: int):
    return SunTimesFactory.from_date(year, month, day, latitude=latitude, longitude=longitude, tz_str="UTC")


@pytest.mark.parametrize("name,lat,lon,y,m,d", _GRID, ids=lambda v: v if isinstance(v, str) else "")
def test_the_upper_limb_is_on_the_horizon_at_every_rise_and_set(oracle, name, lat, lon, y, m, d):
    """One number, the whole globe, every season."""
    model = _sun_times(lat, lon, y, m, d)

    failures: list[str] = []
    for label, moment in (("sunrise", model.sunrise), ("sunset", model.sunset)):
        if moment is None:
            continue
        altitude, semidiameter = _true_altitude_and_semidiameter(oracle, moment, lat, lon)
        limb = altitude + semidiameter
        if abs(limb - _LIMB_ON_HORIZON_ARCMIN) > _LIMB_TOL_ARCMIN:
            failures.append(
                f"{label} at {moment:%Y-%m-%d %H:%M:%S}Z: upper limb {limb:.4f}', "
                f"expected {_LIMB_ON_HORIZON_ARCMIN}' +/- {_LIMB_TOL_ARCMIN}'"
            )

    assert not failures, (
        f"{name}: the horizon convention moved.\n  " + "\n  ".join(failures) + "\n"
        "Check the refraction parameters, the disc-limb term and the topocentric "
        "parallax before touching anything else."
    )


@pytest.mark.parametrize("name,lat,lon,y,m,d", _GRID, ids=lambda v: v if isinstance(v, str) else "")
def test_solar_noon_is_on_the_meridian(oracle, name, lat, lon, y, m, d):
    """Solar noon is a meridian crossing, so its hour angle is zero.

    The direct statement of what the field means, and the tight one: the anchors
    can only bound it to the reference's whole-minute publication, while an hour
    angle can be measured to a fraction of a second. This is the test that fails
    the moment solar noon goes back to being the midpoint of the rise/set pair.
    """
    model = _sun_times(lat, lon, y, m, d)
    assert model.solar_noon is not None, "the Sun culminates every day"

    hour_angle = _hour_angle_seconds(oracle, model.solar_noon, lat, lon)
    assert abs(hour_angle) < _TRANSIT_HOUR_ANGLE_TOL_S, (
        f"{name}: at the reported solar noon {model.solar_noon:%Y-%m-%d %H:%M:%S}Z the Sun's "
        f"hour angle is {hour_angle:+.2f} s of time, not 0. Solar noon is the meridian "
        f"transit; a value tens of seconds out is the midpoint of sunrise and sunset, "
        f"which is a different quantity."
    )


#: The midpoint comparison needs the observer's OWN timezone, not UTC. Asked for
#: a UTC civil day at 151 E, the rise/set pair and the meridian crossing belong to
#: two different local days and the comparison is meaningless — the first draft of
#: these tests failed on exactly that and it was the harness, not the code.
_LOCAL_GRID = [
    ("quito", -0.1807, -78.4678, "America/Guayaquil", 2026, 3, 20),
    ("rome_equinox", 41.9028, 12.4964, "Europe/Rome", 2026, 3, 20),
    ("rome_solstice", 41.9028, 12.4964, "Europe/Rome", 2026, 6, 21),
    ("london", 51.5074, -0.1278, "Europe/London", 2026, 8, 5),
    ("sydney", -33.8688, 151.2093, "Australia/Sydney", 2026, 12, 21),
    ("reykjavik", 64.1466, -21.9426, "Atlantic/Reykjavik", 2026, 4, 15),
    ("singapore", 1.3521, 103.8198, "Asia/Singapore", 2026, 8, 5),
    ("ushuaia", -54.8019, -68.3030, "America/Argentina/Ushuaia", 2026, 9, 22),
    ("nairobi", -1.2921, 36.8219, "Africa/Nairobi", 2026, 1, 15),
]


def _local_sun_times(lat: float, lon: float, tz: str, y: int, m: int, d: int):
    return SunTimesFactory.from_date(y, m, d, latitude=lat, longitude=lon, tz_str=tz)


@pytest.mark.parametrize(
    "name,lat,lon,tz,y,m,d", _LOCAL_GRID,
    ids=lambda v: v if isinstance(v, str) and "/" not in v else "",
)
def test_the_midpoint_of_the_pair_is_not_the_meridian(oracle, name, lat, lon, tz, y, m, d):
    """The two really are different quantities, and by how much depends on where.

    Kept as a positive statement rather than a comment, because the whole reason
    solar noon was wrong for so long is that the two look interchangeable. This
    checks the difference is real geometry rather than bookkeeping: whatever the
    midpoint's distance from the reported noon, its hour angle must equal it.
    """
    model = _local_sun_times(lat, lon, tz, y, m, d)
    if model.sunrise is None or model.sunset is None:
        pytest.skip("no rise/set pair to take a midpoint of")

    midpoint = model.sunrise + (model.sunset - model.sunrise) / 2
    hour_angle = _hour_angle_seconds(oracle, midpoint, lat, lon)
    drift = (midpoint - model.solar_noon).total_seconds()

    assert abs(hour_angle - drift) < 1.5, (
        f"{name}: the midpoint sits {drift:+.1f} s from the reported noon while its hour "
        f"angle is {hour_angle:+.1f} s — the two disagree, so one of them is not what it "
        f"claims to be"
    )


def test_the_midpoint_drift_grows_with_latitude_away_from_the_solstice():
    """It is not noise: it has a direction and a cause.

    At the solstice, and on the equator, the declination barely moves between
    sunrise and sunset and the midpoint IS the meridian. Away from both it is not,
    and the gap widens with latitude. Pinning the pattern rather than a single
    number is what makes this a statement about geometry instead of an accident of
    one date — and it is the reason the old implementation looked right for years
    to anyone who checked it in June.
    """
    def drift_seconds(lat: float, lon: float, tz: str, y: int, m: int, d: int) -> float:
        model = _local_sun_times(lat, lon, tz, y, m, d)
        midpoint = model.sunrise + (model.sunset - model.sunrise) / 2
        return abs((midpoint - model.solar_noon).total_seconds())

    equator = drift_seconds(-0.1807, -78.4678, "America/Guayaquil", 2026, 3, 20)
    rome_solstice = drift_seconds(41.9028, 12.4964, "Europe/Rome", 2026, 6, 21)
    rome_equinox = drift_seconds(41.9028, 12.4964, "Europe/Rome", 2026, 3, 20)
    reykjavik_april = drift_seconds(64.1466, -21.9426, "Atlantic/Reykjavik", 2026, 4, 15)

    assert equator < 3.0, (
        f"on the equator the day is symmetric about the meridian; drift {equator:.1f} s"
    )
    assert rome_solstice < 3.0, (
        f"at the solstice the declination is stationary, so the midpoint should BE the "
        f"meridian; it is {rome_solstice:.1f} s away"
    )
    assert rome_equinox > 10.0, (
        f"at the equinox the midpoint should visibly miss the meridian; it is only "
        f"{rome_equinox:.1f} s away"
    )
    assert reykjavik_april > 2 * rome_equinox, (
        f"the drift should grow steeply with latitude: Reykjavik {reykjavik_april:.1f} s "
        f"against Rome {rome_equinox:.1f} s"
    )


@pytest.mark.parametrize(
    "name,lat,lon,tz,y,m,d",
    [
        ("quito", -0.1807, -78.4678, "America/Guayaquil", 2026, 3, 20),
        ("rome", 41.9028, 12.4964, "Europe/Rome", 2026, 3, 20),
        ("london", 51.5074, -0.1278, "Europe/London", 2026, 8, 5),
        ("reykjavik", 64.1466, -21.9426, "Atlantic/Reykjavik", 2026, 4, 15),
    ],
    ids=lambda v: v if isinstance(v, str) and "/" not in v else "",
)
def test_is_diurnal_flips_when_the_geometric_centre_crosses_zero(oracle, name, lat, lon, tz, y, m, d):
    """`is_diurnal` answers a different question from sunrise, and answers it right.

    Sunrise is the apparent upper limb; `is_diurnal` is the geometric centre. The
    two are minutes apart by construction, and every attempt to derive one from
    the other has been a bug. This bisects the flip and checks the independent
    altitude there is zero — the direct statement of what the field means.
    """
    model = _sun_times(lat, lon, y, m, d)
    sunrise = model.sunrise
    assert sunrise is not None

    def is_diurnal_at(moment: dt.datetime) -> bool:
        local = moment.astimezone(dt.timezone.utc)
        subject = AstrologicalSubjectFactory.from_birth_data(
            "probe", local.year, local.month, local.day, local.hour, local.minute,
            lng=lon, lat=lat, tz_str="UTC", city="probe", nation="XX", seconds=local.second,
        )
        return subject.is_diurnal

    low, high = sunrise - dt.timedelta(minutes=30), sunrise + dt.timedelta(minutes=30)
    assert is_diurnal_at(low) is False and is_diurnal_at(high) is True, (
        "the bracket must straddle the flip for the bisection below to mean anything"
    )
    for _ in range(20):
        middle = low + (high - low) / 2
        if is_diurnal_at(middle):
            high = middle
        else:
            low = middle

    # Stated in SECONDS, not arcminutes. The probe takes whole seconds, so the
    # bisection can only ever land within a second of the true crossing, and one
    # second buys 15" of altitude at the equator but only 6" at 64 N. A fixed
    # angular tolerance would therefore be far stricter near the equator than at
    # the pole for no reason; dividing by the local rate makes the claim the same
    # everywhere: "the flip is where the centre crosses zero, to within the
    # resolution we can even ask the question at".
    altitude, _semidiameter = _true_altitude_and_semidiameter(oracle, high, lat, lon)
    before, _ = _true_altitude_and_semidiameter(oracle, high - dt.timedelta(seconds=30), lat, lon)
    after, _ = _true_altitude_and_semidiameter(oracle, high + dt.timedelta(seconds=30), lat, lon)
    rate_arcmin_per_second = (after - before) / 60.0
    offset_seconds = abs(altitude / rate_arcmin_per_second)
    assert offset_seconds < 1.5, (
        f"{name}: is_diurnal flips at {high:%H:%M:%S}Z where the Sun's centre is "
        f"{altitude:.4f}' — {offset_seconds:.2f} s from the geometric horizon, more than "
        f"the one-second resolution of the probe can explain. The flag is not testing "
        f"the geometric horizon."
    )

    # And the flip is AFTER sunrise, never before: the limb clears the horizon
    # first. A build that got this backwards would still bisect to something.
    assert high > sunrise, "is_diurnal cannot turn true before the Sun has risen"


def test_the_gap_between_sunrise_and_diurnality_grows_towards_the_pole():
    """The documented figures, pinned so the documentation cannot rot silently.

    The Sun has to climb the same ~0.83 degrees at every latitude, but it climbs
    at a shallower angle the further from the equator, so the same geometry costs
    more time. The README and the model docstrings quote these; this is what
    stops them drifting away from the code.
    """
    def gap_minutes(lat: float, lon: float, tz: str, y: int, m: int, d: int) -> float:
        model = _sun_times(lat, lon, y, m, d)
        sunrise = model.sunrise

        def is_diurnal_at(moment: dt.datetime) -> bool:
            subject = AstrologicalSubjectFactory.from_birth_data(
                "probe", moment.year, moment.month, moment.day, moment.hour, moment.minute,
                lng=lon, lat=lat, tz_str="UTC", city="probe", nation="XX", seconds=moment.second,
            )
            return subject.is_diurnal

        low, high = sunrise - dt.timedelta(minutes=40), sunrise + dt.timedelta(minutes=40)
        for _ in range(20):
            middle = low + (high - low) / 2
            if is_diurnal_at(middle):
                high = middle
            else:
                low = middle
        return (high - sunrise).total_seconds() / 60.0

    quito = gap_minutes(-0.1807, -78.4678, "UTC", 2026, 3, 20)
    rome = gap_minutes(41.9028, 12.4964, "UTC", 2026, 3, 20)
    reykjavik = gap_minutes(64.1466, -21.9426, "UTC", 2026, 4, 15)

    assert 3.0 < quito < 4.0, f"equator gap {quito:.2f} min, documented as about 3.3"
    assert 4.0 < rome < 5.5, f"Rome gap {rome:.2f} min, documented as about 4.4"
    assert 7.5 < reykjavik < 9.5, f"Reykjavik gap {reykjavik:.2f} min, documented as about 8.2"
    assert quito < rome < reykjavik, "the gap must widen towards the pole"
