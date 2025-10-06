"""Example of generating a full astrological report for the current time."""

from kerykeion import ReportGenerator
from kerykeion import ChartDataFactory
from kerykeion import AstrologicalSubjectFactory

now = AstrologicalSubjectFactory.from_current_time(geonames_username="century.boy")

# Create chart data - this calculates elements, qualities, and aspects
chart = ChartDataFactory.create_chart_data(
    "Natal",
    first_subject=now,
)

# Create report with the chart (not just the subject)
report_chart = ReportGenerator(chart)
report_chart.print_report(include_aspects=True)
