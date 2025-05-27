from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.charts.kerykeion_chart_svg import KerykeionChartSVG

# Create astrological subjects
first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

# Generate composite chart data
composite_chart = CompositeSubjectFactory(first, second)
print(composite_chart.get_midpoint_composite_subject_model().model_dump_json(indent=4))

# Create and save the composite chart as an SVG
angelina = AstrologicalSubjectFactory.from_birth_data("Angelina Jolie", 1975, 6, 4, 9, 9, "Los Angeles", "US", lng=-118.15, lat=34.03, tz_str="America/Los_Angeles")
brad = AstrologicalSubjectFactory.from_birth_data("Brad Pitt", 1963, 12, 18, 6, 31, "Shawnee", "US", lng=-96.56, lat=35.20, tz_str="America/Chicago")

composite_subject_factory = CompositeSubjectFactory(angelina, brad)
composite_subject_model = composite_subject_factory.get_midpoint_composite_subject_model()
composite_chart = KerykeionChartSVG(composite_subject_model, "Composite")
composite_chart.makeSVG()
