from kerykeion import (
    KrInstance,
    Report,
)


def test_print_report():
    subject = KrInstance("John", 1975, 10, 10, 21, 15, "Roma", "IT")
    report = Report(subject)

    assert report.report_title == "\n+- Kerykeion report for John -+"
