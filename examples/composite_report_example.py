"""Example: Generate a composite chart report (SingleChartDataModel)."""

from __future__ import annotations

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory

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

    composite_subject = CompositeSubjectFactory(
        first_subject,
        second_subject,
        chart_name="Sample Composite Chart",
    ).get_midpoint_composite_subject_model()

    chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
    report = ReportGenerator(chart_data)
    title = "SingleChartDataModel Report (Composite)"
    print("\n" + title)
    print("=" * len(title))
    report.print_report()
