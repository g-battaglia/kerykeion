"""Example: Generate a synastry chart report (DualChartDataModel)."""

from __future__ import annotations

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

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

    chart_data = ChartDataFactory.create_synastry_chart_data(first_subject, second_subject)
    report = ReportGenerator(chart_data)
    report.print_report()
