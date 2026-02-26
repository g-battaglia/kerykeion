from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory

# Create a natal chart data
subject = AstrologicalSubjectFactory.from_current_time(name="Test Subject")
second_subject = AstrologicalSubjectFactory.from_current_time(name="Second Subject")
synastry_data = ChartDataFactory.create_synastry_chart_data(subject, second_subject)

print(synastry_data.model_dump_json(indent=2))
