"""
Centralized pytest fixtures for Kerykeion test suite.

This module provides:
- Parametrized fixtures for temporal/geographic test subjects
- Parametrized fixtures for house systems and sidereal modes
- Standard fixtures for commonly used test subjects
- Helper fixtures for chart and aspect testing
- Tier-based filtering for ephemeris tiers (base/medium/extended)

Usage:
    All fixtures are automatically available to all tests in the tests/ directory.

Tier filtering:
    pytest tests/ --tier=base     # DE440s: 1849-2150 (11 subjects)
    pytest tests/ --tier=medium   # DE440: 1550-2650 (16 subjects, cumulative)
    pytest tests/ --tier=extended # DE441: full range (25 subjects, cumulative)

    Without --tier, the tier is auto-detected by probing the loaded ephemeris,
    so a plain ``pytest`` run is green on any kernel: out-of-range temporal
    subjects and the BCE/ancient-date test modules are skipped (with reasons)
    instead of failing. Pass --tier=extended explicitly to force-run everything
    (requires the full-range DE441 kernel).
"""

import os
import re

import pytest
from typing import Dict, Any

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.aspects.aspects_factory import AspectsFactory

from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    GEOGRAPHIC_SUBJECTS,
    HOUSE_SYSTEMS,
    SIDEREAL_MODES,
    SYNASTRY_PAIRS,
    PERSPECTIVE_TYPES,
    CORE_PLANETS,
    LUNAR_NODES,
    ANGLES,
    HOUSES,
    ALL_POINTS,
    get_subjects_for_tier,
)


# =============================================================================
# TIER FILTERING
# =============================================================================


def pytest_addoption(parser):
    parser.addoption(
        "--tier",
        action="store",
        default=None,
        choices=["base", "medium", "extended"],
        help="Run only tests for the specified ephemeris tier (cumulative)",
    )


def pytest_sessionstart(session):
    """Fail fast when the suite is forced onto swisseph without SE data files.

    Golden values are generated against full-precision JPL ephemeris; on the
    Moshier fallback (no ``.se1`` files) hundreds of tests fail with confusing
    precision and availability errors. Exit upfront with the fix instead.
    """
    from kerykeion.ephemeris_backend import BACKEND_NAME, EPHE_DATA_PATH

    if BACKEND_NAME != "swisseph":
        return
    try:
        has_se1 = any(f.lower().endswith(".se1") for f in os.listdir(EPHE_DATA_PATH))
    except OSError:
        has_se1 = False
    if not has_se1:
        pytest.exit(
            "KERYKEION_BACKEND=swisseph needs Swiss Ephemeris data files (.se1); "
            "the built-in Moshier fallback fails the golden-value tests.\n"
            "Download them (auto-detected from ~/.kerykeion/sweph) and rerun:\n"
            "    uv run python -m kerykeion.swisseph_setup\n"
            "    uv run poe test:swe",
            returncode=4,
        )


def _detect_ephemeris_tier() -> str:
    """Probe the loaded ephemeris and return the widest tier it can serve.

    Computes the Sun at probe dates chosen inside one tier's range but outside
    the next narrower one: year 1000 is covered only by DE441 (extended),
    year 1700 by DE440 (medium) but not DE440s (base, 1849+).
    """
    from kerykeion.ephemeris_backend import ephe, ephemeris_session

    def _sun_computes(year: int) -> bool:
        # The primary (libephemeris) backend raises for out-of-range dates, so a
        # bare success/raise cleanly distinguishes whether the date is served.
        try:
            with ephemeris_session() as iflag:
                ephe.calc_ut(ephe.julday(year, 1, 1, 12.0), 0, iflag)
            return True
        except Exception:
            return False

    if _sun_computes(1000):
        return "extended"
    if _sun_computes(1700):
        return "medium"
    return "base"


# Tests that need the full-range (extended) kernel but are not parametrized with
# temporal-subject ids, so the subject-tier filter below cannot catch them.
#
# These carry an explicit ``@pytest.mark.extended``. This used to be a bare
# substring match on the lowercased node id ("bce", "ancient_rome",
# "historical_date"), which silently skipped 25 tests that need no ephemeris at
# all — every ``test_jd_to_iso_bce_year`` (pure string formatting), the whole of
# ``TestAncientISOFormat`` (including ``test_year_zero``), and the BCE sampling-gap
# tests. No substring or regex on the node id can separate them: the defect is
# that a test's *name* says "bce" while its *body* never leaves the civil range.
# Intent has to be declared, not inferred.

# Tests exercising the full point set (TNOs and other extra bodies). On the
# swisseph backend these need per-body asteroid `.se1` files that the setup
# helper cannot auto-download (manual mirror only); skip them when the backend
# cannot compute a probe TNO instead of failing dozens of snapshot tests.
# The city-named snapshots are the golden reports generated with
# ALL_ACTIVE_POINTS whose node ids don't carry an all-points marker.
# NOTE: matched as a delimiter-bounded regex, not a bare substring — a bare
# "tno" would also hit camelCase joins like TestNOrmalize/TesTNOnInt once
# lowercased, silently skipping ~40 unrelated tests.
_TNO_NODE_REGEX = re.compile(
    r"(?:^|[^a-z0-9])(?:"
    r"all_active_points|all_points|tnos?|has_extra_bodies|all_32pts|"
    r"einstein_snapshot|tokyo_snapshot|quito_snapshot|"
    r"buenos_aires_snapshot|ancient_rome_snapshot|future_2050_snapshot"
    r")(?:[^a-z0-9]|$)"
)


def _tnos_available() -> bool:
    """Probe whether the loaded ephemeris can compute a TNO (Eris)."""
    from kerykeion.astrological_subject_factory import TNO_PLANETS
    from kerykeion.ephemeris_backend import ephe, ephemeris_session

    try:
        with ephemeris_session() as iflag:
            ephe.calc_ut(ephe.julday(2020, 1, 1, 12.0), TNO_PLANETS["Eris"], iflag)
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    tier = config.getoption("--tier")
    auto_detected = tier is None
    if auto_detected:
        tier = _detect_ephemeris_tier()

    allowed_ids = set(get_subjects_for_tier(tier).keys())

    # Build full set of all temporal subject IDs for checking
    all_subject_ids = {s["id"] for s in TEMPORAL_SUBJECTS}

    detected_note = " (auto-detected from the loaded ephemeris)" if auto_detected else ""
    skip_subject = pytest.mark.skip(reason=f"Subject not in tier '{tier}'{detected_note}")
    skip_range = pytest.mark.skip(
        reason=f"Requires the full-range (extended) ephemeris kernel; current tier is '{tier}'{detected_note}"
    )

    from kerykeion.ephemeris_backend import BACKEND_NAME

    tnos_missing = BACKEND_NAME == "swisseph" and not _tnos_available()
    skip_tno = pytest.mark.skip(
        reason="Full-point-set test needs TNO ephemeris files the swisseph setup "
        "cannot auto-download (manual mirror only)."
    )

    for item in items:
        node_id = item.nodeid
        node_id_lower = node_id.lower()
        if tnos_missing and _TNO_NODE_REGEX.search(node_id_lower):
            item.add_marker(skip_tno)
            continue
        if tier != "extended" and item.get_closest_marker("extended") is not None:
            item.add_marker(skip_range)
            continue
        for subject_id in all_subject_ids:
            if subject_id in node_id and subject_id not in allowed_ids:
                item.add_marker(skip_subject)
                break


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_subject_from_temporal_data(data: Dict[str, Any], **kwargs):
    """Create an AstrologicalSubjectModel from temporal subject data."""
    return AstrologicalSubjectFactory.from_birth_data(
        name=data["name"],
        year=data["year"],
        month=data["month"],
        day=data["day"],
        hour=data["hour"],
        minute=data["minute"],
        lat=data["lat"],
        lng=data["lng"],
        tz_str=data["tz_str"],
        online=False,
        suppress_geonames_warning=True,
        **kwargs,
    )


def create_subject_from_geographic_data(
    data: Dict[str, Any],
    year: int = 1990,
    month: int = 6,
    day: int = 15,
    hour: int = 12,
    minute: int = 0,
    **kwargs,
):
    """Create an AstrologicalSubjectModel from geographic location data."""
    return AstrologicalSubjectFactory.from_birth_data(
        name=f"Test_{data['id']}",
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lat=data["lat"],
        lng=data["lng"],
        tz_str=data["tz_str"],
        online=False,
        suppress_geonames_warning=True,
        **kwargs,
    )


# =============================================================================
# SESSION-SCOPED FIXTURES (Cached for entire test session)
# =============================================================================


@pytest.fixture(scope="session")
def john_lennon():
    """
    Standard John Lennon subject - PRIMARY TEST SUBJECT.

    Birth data: October 9, 1940, 18:30, Liverpool, GB (53.4084, -2.9916)
    Used as the reference subject throughout the test suite.
    """
    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def paul_mccartney():
    """
    Standard Paul McCartney subject.

    Birth data: June 18, 1942, 15:30, Liverpool, GB (53.4084, -2.9916)
    Used for synastry testing with John Lennon.

    NOTE: 15:30 matches the canonical ``paul_mccartney_1942`` matrix subject, but
    tests/core/conftest.py defines a *different* 14:00 chart under the same fixture
    name, which shadows this one for everything under tests/core/. See that file.
    """
    return AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney",
        1942,
        6,
        18,
        15,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def johnny_depp():
    """
    Standard Johnny Depp subject - LEGACY TEST SUBJECT.

    Birth data: June 9, 1963, 00:00, Owensboro, US (37.7742, -87.1133)
    Used for backward compatibility with existing test data.
    """
    return AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp",
        1963,
        6,
        9,
        0,
        0,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def all_temporal_subjects() -> Dict[str, Any]:
    """
    Dictionary of all temporal subjects, keyed by ID.

    This fixture creates all temporal subjects once and caches them.
    Use this for tests that need multiple subjects without recreation.
    """
    subjects = {}
    for data in TEMPORAL_SUBJECTS:
        try:
            subjects[data["id"]] = create_subject_from_temporal_data(data)
        except Exception as e:
            # Some ancient dates may not be supported by ephemeris
            subjects[data["id"]] = None
            print(f"Warning: Could not create subject {data['id']}: {e}")
    return subjects


@pytest.fixture(scope="session")
def all_geographic_subjects() -> Dict[str, Any]:
    """
    Dictionary of all geographic subjects, keyed by ID.

    All subjects use the same birth date (1990-06-15 12:00) to isolate
    geographic effects from temporal effects.
    """
    subjects = {}
    for data in GEOGRAPHIC_SUBJECTS:
        try:
            subjects[data["id"]] = create_subject_from_geographic_data(data)
        except Exception as e:
            subjects[data["id"]] = None
            print(f"Warning: Could not create subject {data['id']}: {e}")
    return subjects


# =============================================================================
# PARAMETRIZED FIXTURES - Temporal Subjects
# =============================================================================


@pytest.fixture(params=TEMPORAL_SUBJECTS, ids=lambda s: s["id"])
def temporal_subject_data(request) -> Dict[str, Any]:
    """
    Parametrized fixture providing raw data for each temporal subject.

    Use this when you need the raw data dictionary instead of the created subject.
    """
    return request.param


@pytest.fixture
def temporal_subject(temporal_subject_data):
    """
    Parametrized fixture providing created AstrologicalSubjectModel for each temporal subject.

    This creates a fresh subject for each test, allowing modifications.
    """
    return create_subject_from_temporal_data(temporal_subject_data)


# =============================================================================
# PARAMETRIZED FIXTURES - Geographic Subjects
# =============================================================================


@pytest.fixture(params=GEOGRAPHIC_SUBJECTS, ids=lambda s: s["id"])
def geographic_subject_data(request) -> Dict[str, Any]:
    """
    Parametrized fixture providing raw data for each geographic location.
    """
    return request.param


@pytest.fixture
def geographic_subject(geographic_subject_data):
    """
    Parametrized fixture providing created subject for each geographic location.

    Uses a standard birth date (1990-06-15 12:00) to isolate geographic effects.
    """
    return create_subject_from_geographic_data(geographic_subject_data)


# =============================================================================
# PARAMETRIZED FIXTURES - House Systems
# =============================================================================


@pytest.fixture(params=HOUSE_SYSTEMS, ids=lambda h: f"house_{h}")
def house_system(request) -> str:
    """Parametrized fixture for all house systems."""
    return request.param


@pytest.fixture
def subject_with_house_system(house_system, john_lennon):
    """
    Create John Lennon subject with specified house system.

    This allows testing all house systems against the same birth data.
    """
    return AstrologicalSubjectFactory.from_birth_data(
        f"John Lennon - House {house_system}",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        houses_system_identifier=house_system,
        suppress_geonames_warning=True,
    )


# =============================================================================
# PARAMETRIZED FIXTURES - Sidereal Modes
# =============================================================================


@pytest.fixture(params=SIDEREAL_MODES, ids=lambda m: f"sidereal_{m}")
def sidereal_mode(request) -> str:
    """Parametrized fixture for all sidereal modes (ayanamsas)."""
    return request.param


@pytest.fixture
def sidereal_subject(sidereal_mode):
    """
    Create John Lennon subject with specified sidereal mode.
    """
    return AstrologicalSubjectFactory.from_birth_data(
        f"John Lennon - {sidereal_mode}",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        zodiac_type="Sidereal",
        sidereal_mode=sidereal_mode,
        suppress_geonames_warning=True,
    )


# =============================================================================
# PARAMETRIZED FIXTURES - Perspective Types
# =============================================================================


@pytest.fixture(params=PERSPECTIVE_TYPES, ids=lambda p: p.replace(" ", "_").lower())
def perspective_type(request) -> str:
    """Parametrized fixture for all perspective types."""
    return request.param


@pytest.fixture
def subject_with_perspective(perspective_type):
    """
    Create John Lennon subject with specified perspective type.
    """
    return AstrologicalSubjectFactory.from_birth_data(
        f"John Lennon - {perspective_type}",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        perspective_type=perspective_type,
        suppress_geonames_warning=True,
    )


# =============================================================================
# PARAMETRIZED FIXTURES - Planets and Points
# =============================================================================


@pytest.fixture(params=CORE_PLANETS, ids=lambda p: p)
def planet_name(request) -> str:
    """Parametrized fixture for core planets (Sun through Pluto)."""
    return request.param


@pytest.fixture(params=LUNAR_NODES, ids=lambda n: n)
def lunar_node_name(request) -> str:
    """Parametrized fixture for lunar nodes."""
    return request.param


@pytest.fixture(params=ANGLES, ids=lambda a: a)
def angle_name(request) -> str:
    """Parametrized fixture for chart angles (ASC, DESC, MC, IC)."""
    return request.param


@pytest.fixture(params=HOUSES, ids=lambda h: h)
def house_name(request) -> str:
    """Parametrized fixture for houses (1-12)."""
    return request.param


@pytest.fixture(params=ALL_POINTS, ids=lambda p: p)
def point_name(request) -> str:
    """Parametrized fixture for all astrological points (planets + nodes + angles)."""
    return request.param


# =============================================================================
# SYNASTRY FIXTURES
# =============================================================================


@pytest.fixture(params=SYNASTRY_PAIRS, ids=lambda p: f"{p[0]}_x_{p[1]}")
def synastry_pair_ids(request) -> tuple:
    """Parametrized fixture providing synastry pair IDs."""
    return request.param


@pytest.fixture
def synastry_subjects(synastry_pair_ids, all_temporal_subjects):
    """
    Provide a pair of subjects for synastry testing.

    Returns:
        Tuple of (first_subject, second_subject)
    """
    first_id, second_id = synastry_pair_ids
    return (
        all_temporal_subjects.get(first_id),
        all_temporal_subjects.get(second_id),
    )


@pytest.fixture
def synastry_chart_data(john_lennon, paul_mccartney):
    """Create synastry chart data for John Lennon and Paul McCartney."""
    return ChartDataFactory.create_synastry_chart_data(john_lennon, paul_mccartney)


@pytest.fixture
def synastry_aspects(john_lennon, paul_mccartney):
    """Create synastry aspects for John Lennon and Paul McCartney."""
    return AspectsFactory.dual_chart_aspects(john_lennon, paul_mccartney)


# =============================================================================
# CHART DATA FIXTURES
# =============================================================================


@pytest.fixture
def natal_chart_data(john_lennon):
    """Create natal chart data for John Lennon."""
    return ChartDataFactory.create_natal_chart_data(john_lennon)


@pytest.fixture
def transit_chart_data(john_lennon, paul_mccartney):
    """Create transit chart data (John Lennon natal + Paul McCartney as transits)."""
    return ChartDataFactory.create_transit_chart_data(john_lennon, paul_mccartney)


# =============================================================================
# ASPECT FIXTURES
# =============================================================================


@pytest.fixture
def natal_aspects(john_lennon):
    """Create natal aspects for John Lennon."""
    return AspectsFactory.single_chart_aspects(john_lennon)


# =============================================================================
# EDGE CASE FIXTURES
# =============================================================================


@pytest.fixture
def polar_latitude_subjects():
    """
    Create subjects at various polar latitudes for edge case testing.

    Returns:
        Dict mapping latitude to subject
    """
    latitudes = [60, 62, 64, 65, 65.5, 66]
    subjects = {}

    for lat in latitudes:
        # North
        subjects[f"north_{lat}"] = AstrologicalSubjectFactory.from_birth_data(
            f"Polar {lat}N",
            2020,
            6,
            21,
            12,
            0,
            lng=25.0,
            lat=lat,
            tz_str="Europe/Helsinki",
            online=False,
        )
        # South
        subjects[f"south_{lat}"] = AstrologicalSubjectFactory.from_birth_data(
            f"Polar {lat}S",
            2020,
            12,
            21,
            12,
            0,
            lng=110.0,
            lat=-lat,
            tz_str="Antarctica/Casey",
            online=False,
        )

    return subjects


@pytest.fixture
def leap_year_subject():
    """Create a subject born on February 29 (leap year)."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Leap Year 2000",
        2000,
        2,
        29,
        12,
        0,
        lng=0.0,
        lat=51.5074,
        tz_str="Europe/London",
        online=False,
    )


@pytest.fixture
def midnight_subject():
    """Create a subject born exactly at midnight."""
    return AstrologicalSubjectFactory.from_birth_data(
        "Midnight Birth",
        1990,
        1,
        1,
        0,
        0,
        lng=0.0,
        lat=51.5074,
        tz_str="Europe/London",
        online=False,
    )


# =============================================================================
# UTILITY FIXTURES
# =============================================================================


@pytest.fixture
def svg_output_dir(tmp_path):
    """Provide a temporary directory for SVG output during tests."""
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    return svg_dir


@pytest.fixture
def json_output_dir(tmp_path):
    """Provide a temporary directory for JSON output during tests."""
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    return json_dir
