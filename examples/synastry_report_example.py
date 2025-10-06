"""Example: Generate a synastry chart report (DualChartDataModel)."""

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
    first_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Sample Natal Subject",
        year=1990,
        month=7,
        day=21,
        hour=14,
        minute=45,
        **OFFLINE_LOCATION,
    )

    second_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Sample Partner Subject",
        year=1992,
        month=11,
        day=5,
        hour=9,
        minute=30,
        **OFFLINE_LOCATION,
    )

    chart_data = ChartDataFactory.create_synastry_chart_data(first_subject, second_subject)
    report = ReportGenerator(chart_data)
    title = "DualChartDataModel Report (Synastry)"
    print("\n" + title)
    print("=" * len(title))
    report.print_report()
