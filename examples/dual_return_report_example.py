"""Example: Generate a dual return chart report (DualChartDataModel)."""

from __future__ import annotations

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

OFFLINE_LOCATION = {
    "city": "Rome",
    "nation": "IT",
    "lat": 41.9028,
    "lng": 12.4964,
    "tz_str": "Europe/Rome",
    "online": False,
    "suppress_geonames_warning": True,
}


if __name__ == "__main__":
    natal_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Sample Natal Subject",
        year=1990,
        month=7,
        day=21,
        hour=14,
        minute=45,
        **OFFLINE_LOCATION,
    )

    return_factory = PlanetaryReturnFactory(
        natal_subject,
        city=OFFLINE_LOCATION["city"],
        nation=OFFLINE_LOCATION["nation"],
        lat=OFFLINE_LOCATION["lat"],
        lng=OFFLINE_LOCATION["lng"],
        tz_str=OFFLINE_LOCATION["tz_str"],
        online=False,
    )

    solar_return_subject = return_factory.next_return_from_iso_formatted_time(
        natal_subject.iso_formatted_local_datetime,
        "Solar",
    )

    chart_data = ChartDataFactory.create_return_chart_data(natal_subject, solar_return_subject)
    report = ReportGenerator(chart_data)
    title = "DualChartDataModel Report (Dual Return)"
    print("\n" + title)
    print("=" * len(title))
    report.print_report()
