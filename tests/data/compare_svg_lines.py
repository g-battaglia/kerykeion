import re

_DMS_PATTERN = re.compile(r"(\d+)°(\d+)'(\d+)'")


def _dms_to_decimal(match: re.Match) -> str:
    """Convert a DMS string like 23°33'39' to its decimal-degree equivalent."""
    d, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
    return f"{d + m / 60 + s / 3600:.6f}"


def compare_svg_lines(expected_line: str, actual_line: str, rel_tol: float = 1e-10, abs_tol: float = 1e-10) -> None:
    """
    Compare two SVG lines allowing small floating-point differences, with additional absolute tolerance.

    DMS values (e.g. 23°33'39') are collapsed into single decimal numbers
    before comparison so that small arcsecond differences are not compared
    as standalone integers.

    Args:
        expected_line (str): The reference line.
        actual_line (str): The generated line.
        rel_tol (float): Relative tolerance for numerical comparison.
        abs_tol (float): Absolute tolerance for numerical comparison.
    """
    # Collapse DMS triplets into single decimal-degree values
    expected_processed = _DMS_PATTERN.sub(_dms_to_decimal, expected_line)
    actual_processed = _DMS_PATTERN.sub(_dms_to_decimal, actual_line)

    # Regex to match floats (e.g., -12.34, 0.5, 6.)
    number_regex = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"

    expected_numbers = [float(x) for x in re.findall(number_regex, expected_processed)]
    actual_numbers = [float(x) for x in re.findall(number_regex, actual_processed)]

    assert len(expected_numbers) == len(actual_numbers), (
        f"Different number of numeric values found:\nExpected: {expected_numbers}\nActual: {actual_numbers}"
    )

    for index, (e, a) in enumerate(zip(expected_numbers, actual_numbers)):
        # Check if the absolute difference exceeds the threshold
        if abs(a - e) > max(rel_tol * abs(e), abs_tol):
            print(f"Error in comparison at position {index}:")
            print(f"Expected Line: {expected_line}")
            print(f"Actual Line: {actual_line}")
            print(f"Expected: {e}")
            print(f"Actual: {a}")
            print(f"Relative tolerance: {rel_tol}, Absolute tolerance: {abs_tol}")
            assert False, "Numeric values exceed tolerance"

    # Remove numbers and replace with a placeholder to compare the non-numeric parts
    expected_text = re.sub(number_regex, "NUM", expected_processed)
    actual_text = re.sub(number_regex, "NUM", actual_processed)

    assert expected_text == actual_text, f"Non-numeric parts differ:\nExpected: {expected_text}\nActual: {actual_text}"
