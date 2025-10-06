"""Example: Generate a dual return chart report (DualChartDataModel)."""

from __future__ import annotations

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

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
    natal_subject = AstrologicalSubjectFactory.from_birth_data(
        name="John Lennon",
        year=1940,
        month=10,
        day=9,
        hour=18,
        minute=30,
        **JOHN_LOCATION,
    )

    return_factory = PlanetaryReturnFactory(
        natal_subject,
        city=JOHN_LOCATION["city"],
        nation=JOHN_LOCATION["nation"],
        lat=JOHN_LOCATION["lat"],
        lng=JOHN_LOCATION["lng"],
        tz_str=JOHN_LOCATION["tz_str"],
        online=False,
    )

    solar_return_subject = return_factory.next_return_from_iso_formatted_time(
        natal_subject.iso_formatted_local_datetime,
        "Solar",
    )

    chart_data = ChartDataFactory.create_return_chart_data(natal_subject, solar_return_subject)
    report = ReportGenerator(chart_data)
    report.print_report()
