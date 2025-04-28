import re

def compare_svg_lines(expected_line: str, actual_line: str, rel_tol: float = 1e-10, abs_tol: float = 1e-10) -> None:
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
    expected_text = re.sub(number_regex, 'NUM', expected_line)
    actual_text = re.sub(number_regex, 'NUM', actual_line)

    assert expected_text == actual_text, (
        f"Non-numeric parts differ:\nExpected: {expected_text}\nActual: {actual_text}"
    )

