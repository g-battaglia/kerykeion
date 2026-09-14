"""Synastry chart data as JSON, for two subjects cast at the current moment."""

from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory

ROME = {
    "lng": 12.4964,
    "lat": 41.9028,
    "tz_str": "Europe/Rome",
    "online": False,
}

# Create a natal chart data
subject = AstrologicalSubjectFactory.from_current_time(name="Test Subject", city="Rome", nation="IT", **ROME)
second_subject = AstrologicalSubjectFactory.from_current_time(name="Second Subject", city="Rome", nation="IT", **ROME)
synastry_data = ChartDataFactory.create_synastry_chart_data(subject, second_subject)

print(synastry_data.model_dump_json(indent=2))
