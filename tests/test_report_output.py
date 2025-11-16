from pathlib import Path

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory


def test_report_output_exact_match(capsys):
    subject = AstrologicalSubjectFactory.from_birth_data(
        "New Moon - Test",
        2025,
        11,
        20,
        1,
        46,
        lng=-79.99589,
        lat=40.44062,
        tz_str="America/New_York",
        online=False,
    )

    chart_data = ChartDataFactory.create_natal_chart_data(subject)

    # Print the report to stdout and capture it exactly as emitted
    ReportGenerator(chart_data).print_report()
    captured = capsys.readouterr().out

    # Load the expected snapshot (exactly the generated string without the final print newline)
    expected = Path(
        "tests/fixtures/new_moon_test_natal_report.txt"
    ).read_text(encoding="utf-8")

    # print() adds a trailing newline; enforce exact output match including that newline
    assert captured == expected + "\n"

