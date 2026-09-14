"""Example of generating a full astrological report for the current time."""

from kerykeion import ReportGenerator
from kerykeion import ChartDataFactory
from kerykeion import AstrologicalSubjectFactory

# Offline location (Rome): no GeoNames account needed. For online lookup,
# pass city/nation plus your own geonames_username instead.
now = AstrologicalSubjectFactory.from_current_time(
    city="Rome",
    nation="IT",
    lng=12.4964,
    lat=41.8933,
    tz_str="Europe/Rome",
    online=False,
)

# Create chart data - this calculates elements, qualities, and aspects
chart = ChartDataFactory.create_chart_data(
    "Natal",
    first_subject=now,
)

# Create report with the chart (not just the subject)
report_chart = ReportGenerator(chart)
report_chart.print_report(include_aspects=True)
