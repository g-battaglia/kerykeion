from kerykeion import (
    AstrologicalSubject,
    Report,
)


def test_print_report():
    subject = AstrologicalSubject("John", 1975, 10, 10, 21, 15, "Roma", "IT")
    report = Report(subject)

    assert report.report_title == "\n+- Kerykeion report for John -+"
