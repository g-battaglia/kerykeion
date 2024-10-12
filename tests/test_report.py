from kerykeion import (
    AstrologicalSubject,
    Report,
)


def test_print_report():
    subject = AstrologicalSubject("John", 1975, 10, 10, 21, 15, "Roma", "IT", geonames_username="century.boy")
    report = Report(subject)

    assert report.report_title == "\n+- Kerykeion report for John -+"


if __name__ == "__main__":
    import pytest
    import logging

    # Set the log level to CRITICAL
    logging.basicConfig(level=logging.CRITICAL)

    pytest.main(["-vv", "--log-level=CRITICAL", "--log-cli-level=CRITICAL", __file__])
