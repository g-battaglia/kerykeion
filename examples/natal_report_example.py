"""Example: Generate a natal chart report (SingleChartDataModel)."""

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


if __name__ == "__main__":
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        **JOHN_LOCATION,
    )

    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    report = ReportGenerator(chart_data)
    report.print_report()
