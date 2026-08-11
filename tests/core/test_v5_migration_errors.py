# -*- coding: utf-8 -*-
"""
Tests for the v5 -> v6 migration errors.

v6 removed the v5 entry points (AstrologicalSubject, KerykeionChartSVG,
NatalAspects, SynastryAspects) in favour of the factory APIs. These tests
assert that users hitting the old names get an actionable error naming the
replacement and the migration guide, instead of a bare ImportError or a
pydantic AttributeError.
"""

from typing import get_args

import pytest

import kerykeion
from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.schemas import KerykeionException
from kerykeion.schemas.literals import AstrologicalPoint
from kerykeion.settings import DEFAULT_ACTIVE_POINTS, V5_DEFAULT_ACTIVE_POINTS

REMOVED_NAME_TO_REPLACEMENT = {
    "AstrologicalSubject": "AstrologicalSubjectFactory",
    "KerykeionChartSVG": "ChartDataFactory",
    "NatalAspects": "AspectsFactory",
    "SynastryAspects": "AspectsFactory",
}


@pytest.fixture(scope="module")
def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        name="Migration Test",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=30,
        city="Rome",
        nation="IT",
        lat=41.9028,
        lng=12.4964,
        tz_str="Europe/Rome",
        online=False,
    )


@pytest.mark.parametrize("name,replacement", sorted(REMOVED_NAME_TO_REPLACEMENT.items()))
def test_removed_v5_name_raises_helpful_import_error(name, replacement):
    with pytest.raises(ImportError) as excinfo:
        getattr(kerykeion, name)
    message = str(excinfo.value)
    assert name in message
    assert replacement in message
    assert "kerykeion.net" in message


def test_from_import_shows_migration_message():
    with pytest.raises(ImportError) as excinfo:
        from kerykeion import AstrologicalSubject  # noqa: F401
    assert "AstrologicalSubjectFactory" in str(excinfo.value)


def test_unknown_attribute_still_raises_attribute_error():
    with pytest.raises(AttributeError):
        kerykeion.DefinitelyNotAKerykeionThing


def test_module_getattr_does_not_pollute_public_api():
    public_names = dir(kerykeion)
    for removed in REMOVED_NAME_TO_REPLACEMENT:
        assert removed not in kerykeion.__all__
        assert removed not in public_names


def test_chart_drawer_rejects_subject_with_migration_hint(subject):
    with pytest.raises(KerykeionException) as excinfo:
        ChartDrawer(subject)
    message = str(excinfo.value)
    assert "ChartDataFactory" in message
    assert "AstrologicalSubjectModel" in message
    assert "create_natal_chart_data" in message


def test_chart_drawer_rejects_arbitrary_objects():
    with pytest.raises(KerykeionException) as excinfo:
        ChartDrawer({"not": "chart data"})
    assert "ChartDataFactory" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Behavioural changes: the half of the upgrade that raises nothing
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(REMOVED_NAME_TO_REPLACEMENT))
def test_removed_name_error_also_warns_about_changed_defaults(name):
    """The ImportError is the one moment we know the reader is looking.

    Porting the call is only half the upgrade: v6 also changed defaults that
    alter results without raising anything, so the message names them too.
    """
    with pytest.raises(ImportError) as excinfo:
        getattr(kerykeion, name)
    message = str(excinfo.value)
    assert "active points" in message
    assert "orb" in message
    assert "V5_DEFAULT_ACTIVE_POINTS" in message


def test_v5_default_active_points_is_the_v5_set():
    """Frozen historical record of the 18 points v5 activated by default."""
    assert len(V5_DEFAULT_ACTIVE_POINTS) == 18
    assert len(set(V5_DEFAULT_ACTIVE_POINTS)) == 18, "no duplicates"


def test_v5_default_active_points_is_a_superset_of_the_v6_default():
    """v6 only ever dropped points from the default set; it added none.

    If this ever fails, the constant is no longer a faithful record and the
    migration guide's claim ("18 -> 14, nothing added") is wrong.
    """
    dropped = set(V5_DEFAULT_ACTIVE_POINTS) - set(DEFAULT_ACTIVE_POINTS)
    added = set(DEFAULT_ACTIVE_POINTS) - set(V5_DEFAULT_ACTIVE_POINTS)
    assert added == set()
    assert dropped == {"Descendant", "Imum_Coeli", "True_South_Lunar_Node", "Mean_Lilith"}


def test_v5_default_active_points_are_all_valid_today():
    """Every v5 point must still be a computable point in v6, or the constant
    would hand users a list the factory rejects."""
    valid = set(get_args(AstrologicalPoint))
    assert set(V5_DEFAULT_ACTIVE_POINTS) <= valid


def test_v5_default_active_points_actually_restores_the_v5_output(subject):
    """The constant is only useful if passing it brings the dropped points back."""
    v5_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Migration Test",
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=30,
        city="Rome",
        nation="IT",
        lat=41.9028,
        lng=12.4964,
        tz_str="Europe/Rome",
        online=False,
        active_points=V5_DEFAULT_ACTIVE_POINTS,
    )
    assert len(subject.active_points) == 14
    assert len(v5_subject.active_points) == 18
    for point in ("Descendant", "Imum_Coeli", "True_South_Lunar_Node", "Mean_Lilith"):
        assert point in v5_subject.active_points
