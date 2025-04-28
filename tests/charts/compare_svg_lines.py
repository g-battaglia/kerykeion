import re
import pytest

def compare_svg_lines(expected_line: str, actual_line: str, rel_tol: float = 1e-6, abs_tol: float = 1e-6) -> None:
    """
    Compare two SVG lines allowing small floating-point differences, with additional absolute tolerance.

    Args:
        expected_line (str): The reference line.
        actual_line (str): The generated line.
        rel_tol (float): Relative tolerance for numerical comparison.
        abs_tol (float): Absolute tolerance for numerical comparison.
    """
    # Regex to match floats (e.g., -12.34, 0.5, 6.)
    number_regex = r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?'

    expected_numbers = [float(x) for x in re.findall(number_regex, expected_line)]
    actual_numbers = [float(x) for x in re.findall(number_regex, actual_line)]

    assert len(expected_numbers) == len(actual_numbers), (
        f"Different number of numeric values found:\nExpected: {expected_numbers}\nActual: {actual_numbers}"
    )

    for index, (e, a) in enumerate(zip(expected_numbers, actual_numbers)):
        # Compare numbers using both relative and absolute tolerance
        assert abs(a - e) <= max(rel_tol * abs(e), abs_tol), (
            f"Numeric values differ at position {index}:\nExpected: {e}\nActual: {a}\n"
            f"Relative tolerance: {rel_tol}, Absolute tolerance: {abs_tol}"
        )

    # Remove numbers and replace with a placeholder to compare the non-numeric parts
    expected_text = re.sub(number_regex, 'NUM', expected_line)
    actual_text = re.sub(number_regex, 'NUM', actual_line)

    assert expected_text == actual_text, (
        f"Non-numeric parts differ:\nExpected: {expected_text}\nActual: {actual_text}"
    )
