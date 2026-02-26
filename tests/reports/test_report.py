from __future__ import annotations

from kerykeion import (
    ReportGenerator,
    AstrologicalSubjectFactory,
    ChartDataFactory,
)
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.schemas.kr_models import AstrologicalSubjectModel

_LOCATION = {
    "city": "Rome",
    "nation": "IT",
    "lat": 41.9028,
    "lng": 12.4964,
    "tz_str": "Europe/Rome",
    "online": False,
    "suppress_geonames_warning": True,
}


def _make_subject(
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
) -> AstrologicalSubjectModel:
    return AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        **_LOCATION,
    )


def test_subject_report_includes_core_sections() -> None:
    subject = _make_subject("Subject A", 1975, 10, 10, 21, 15)
    report = ReportGenerator(subject, include_aspects=False)

    text = report.generate_report(include_aspects=False)

    assert subject.name in text
    assert "Birth Data" in text
    assert "Celestial Points" in text
    assert "Houses (" in text
    assert "Lunar Phase" in text
    assert "Aspects" not in text  # include_aspects=False suppresses the section


def test_natal_chart_report_includes_elements_and_active_configuration() -> None:
    subject = _make_subject("Subject B", 1985, 6, 15, 8, 0)
    chart = ChartDataFactory.create_natal_chart_data(subject)
    report = ReportGenerator(chart)

    full_text = report.generate_report(max_aspects=3)

    assert "Element Distribution" in full_text
    assert all(keyword in full_text for keyword in ("Fire", "Earth", "Air", "Water"))
    assert "Quality Distribution" in full_text
    assert all(keyword in full_text for keyword in ("Cardinal", "Fixed", "Mutable"))
    assert "Aspects" in full_text
    assert "Active Celestial Points" in full_text


def test_composite_chart_report_lists_members() -> None:
    first = _make_subject("Composite First", 1990, 1, 2, 9, 30)
    second = _make_subject("Composite Second", 1992, 3, 4, 11, 45)

    composite_subject = CompositeSubjectFactory(
        first,
        second,
        chart_name="Sample Composite Chart",
    ).get_midpoint_composite_subject_model()

    chart = ChartDataFactory.create_composite_chart_data(composite_subject)
    report = ReportGenerator(chart)
    text = report.generate_report(max_aspects=3)

    assert "Composite Members" in text
    assert first.name in text and second.name in text
    assert "Composite Chart" in text


def test_solar_return_report_labels_return_type() -> None:
    natal = _make_subject("Solar Return Subject", 1987, 7, 21, 14, 30)

    factory = PlanetaryReturnFactory(
        natal,
        city=_LOCATION["city"],
        nation=_LOCATION["nation"],
        lat=_LOCATION["lat"],
        lng=_LOCATION["lng"],
        tz_str=_LOCATION["tz_str"],
        online=False,
    )
    solar_return_subject = factory.next_return_from_iso_formatted_time(
        natal.iso_formatted_local_datetime,
        "Solar",
    )

    chart = ChartDataFactory.create_single_wheel_return_chart_data(solar_return_subject)
    report = ReportGenerator(chart)
    text = report.generate_report(max_aspects=3)

    assert "Solar Return Chart" in text
    assert natal.name in text


def test_synastry_report_includes_house_comparison_and_dual_aspects() -> None:
    first = _make_subject("Synastry First", 1980, 2, 14, 16, 20)
    second = _make_subject("Synastry Second", 1983, 11, 6, 4, 45)

    chart = ChartDataFactory.create_synastry_chart_data(first, second)
    report = ReportGenerator(chart)

    text = report.generate_report(max_aspects=5)
    assert first.name in text and second.name in text
    assert "points in" in text  # house comparison tables
    assert "Active Celestial Points" in text
    assert "Owner 1" in text and "Owner 2" in text
    assert "Aspects" in text


if __name__ == "__main__":
    import logging
    import pytest

    logging.basicConfig(level=logging.CRITICAL)
    pytest.main(["-vv", __file__])
