from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Test Subject",
    year=1990, month=6, day=15, hour=12, minute=30,
    city="Rome",
    nation="IT",
    tz_str="Europe/Rome",
    lat=41.9028,
    lng=12.4964
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data)
drawer.save_minimalist_svg_file(output_path="/Users/giacomo/dev/kerykeion/task")
print("Done")
