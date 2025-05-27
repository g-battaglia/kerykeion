from kerykeion import AstrologicalSubjectFactory
from kerykeion import KerykeionChartSVG

first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

chart = KerykeionChartSVG(first, "Synastry", second)
