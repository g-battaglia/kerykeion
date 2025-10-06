"""Example: Generate a natal chart report (SingleChartDataModel)."""

from __future__ import annotations

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory

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
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="Sample Natal Subject",
        year=1990,
        month=7,
        day=21,
        hour=14,
        minute=45,
        **OFFLINE_LOCATION,
    )

    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    report = ReportGenerator(chart_data)
    title = "SingleChartDataModel Report (Natal)"
    print("\n" + title)
    print("=" * len(title))
    report.print_report()
