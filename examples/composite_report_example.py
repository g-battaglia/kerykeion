"""Example: Generate a composite chart report (SingleChartDataModel)."""

from __future__ import annotations

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory

JOHN_LOCATION = {
    "city": "Liverpool",
    "nation": "GB",
    "lat": 53.4084,
    "lng": -2.9916,
    "tz_str": "Europe/London",
    "online": False,
    "suppress_geonames_warning": True,
}

YOKO_LOCATION = {
    "city": "Tokyo",
    "nation": "JP",
    "lat": 35.6762,
    "lng": 139.6503,
    "tz_str": "Asia/Tokyo",
    "online": False,
    "suppress_geonames_warning": True,
}


if __name__ == "__main__":
    first_subject = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        **JOHN_LOCATION,
    )

    second_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Yoko Ono",
        year=1933,
        month=2,
        day=18,
        hour=20,
        minute=30,
        **YOKO_LOCATION,
    )

    composite_subject = CompositeSubjectFactory(
        first_subject,
        second_subject,
        chart_name="John & Yoko Composite Chart",
    ).get_midpoint_composite_subject_model()

    chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
    report = ReportGenerator(chart_data)
    report.print_report()
