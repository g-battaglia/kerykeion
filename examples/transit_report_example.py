"""Example: Generate a transit chart report (DualChartDataModel)."""

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

TRANSIT_LOCATION = {
    "city": "New York",
    "nation": "US",
    "lat": 40.7128,
    "lng": -74.0060,
    "tz_str": "America/New_York",
    "online": False,
    "suppress_geonames_warning": True,
}


if __name__ == "__main__":
    natal_subject = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        **JOHN_LOCATION,
    )

    transit_subject = AstrologicalSubjectFactory.from_birth_data(
        name="1967 Transit",
        year=1967,
        month=6,
        day=5,
        hour=12,
        minute=0,
        **TRANSIT_LOCATION,
    )

    chart_data = ChartDataFactory.create_transit_chart_data(natal_subject, transit_subject)
    report = ReportGenerator(chart_data)
    report.print_report()
