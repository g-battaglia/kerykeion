# -*- coding: utf-8 -*-
"""
Tests for the v5 -> v6 migration errors.

v6 removed the v5 entry points (AstrologicalSubject, KerykeionChartSVG,
NatalAspects, SynastryAspects) in favour of the factory APIs. These tests
assert that users hitting the old names get an actionable error naming the
replacement and the migration guide, instead of a bare ImportError or a
pydantic AttributeError.
"""

import pytest

import kerykeion
from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.schemas import KerykeionException

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
