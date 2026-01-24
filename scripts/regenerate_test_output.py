#!/usr/bin/env python3
"""
Script to regenerate the expected output for tests/test_report_output.py
"""

import sys
from pathlib import Path
from io import StringIO

# Add the project root to the python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from kerykeion import ReportGenerator, AstrologicalSubjectFactory, ChartDataFactory


def regenerate_report():
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

    # Capture the output
    # We need to capture exactly what ReportGenerator prints
    capture_buffer = StringIO()
    original_stdout = sys.stdout
    sys.stdout = capture_buffer

    try:
        ReportGenerator(chart_data).print_report()
    finally:
        sys.stdout = original_stdout

    output = capture_buffer.getvalue()

    # The test expects the file content + a newline to equal the captured output.
    # So we should save the captured output WITHOUT the final newline if we want to match
    # how the test reads it (read_text).
    #
    # Test logic:
    # captured = capsys.readouterr().out  <-- This includes the final newline from print()
    # expected = Path(...).read_text()
    # assert captured == expected + "\n"
    #
    # So 'expected' should be 'captured' with the last newline removed.

    if output.endswith("\n"):
        content_to_save = output[:-1]
    else:
        content_to_save = output

    output_path = project_root / "tests/fixtures/new_moon_test_natal_report.txt"
    output_path.write_text(content_to_save, encoding="utf-8")

    print(f"Regenerated {output_path}")


if __name__ == "__main__":
    regenerate_report()
