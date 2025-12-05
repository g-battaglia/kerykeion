from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Create subject
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
)

# Generate chart data
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Create drawer and save vertical chart
drawer = ChartDrawer(chart_data, theme="classic")
drawer.save_vertical_svg(output_path="./", filename="natal_vertical")