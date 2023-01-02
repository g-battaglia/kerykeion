from kerykeion.fetch_geonames import FetchGeonames
from kerykeion import (
    KrInstance,
    MakeSvgInstance,
)

def test_birthchart_instance():
    subject = KrInstance("Test", 1993, 10, 10, 12, 12, "London", "GB")
    birthchart_svg = MakeSvgInstance(subject).makeTemplate()

    assert birthchart_svg.startswith("<?xml version='1.0' encoding='UTF-8'?>")


def test_composite_chart_instance():
    # TODO: Improve with bs4
    first_subject = KrInstance("John", 1975, 10, 10, 21, 15, "Roma", "IT")
    second_subject = KrInstance("Sarah", 1978, 2, 9, 15, 50, "Roma", "IT")
    birthchart_instance = MakeSvgInstance(first_subject, "Composite", second_subject)
    template = birthchart_instance.makeTemplate()

    assert birthchart_instance.chart_type == "Composite"
    assert template.startswith("<?xml version='1.0' encoding='UTF-8'?>")
