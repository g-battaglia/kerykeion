from kerykeion import AstrologicalSubject
from kerykeion import KerykeionChartSVG

first = AstrologicalSubject("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

chart = KerykeionChartSVG(first, "Synastry", second)
