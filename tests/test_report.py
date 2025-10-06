from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    Report,
)


def test_print_report():
    """Test that the report is generated correctly with all sections."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "John", 1975, 10, 10, 21, 15, "Roma", "IT", suppress_geonames_warning=True
    )
    report = Report(subject)

    # Test report title
    title = report.get_report_title()
    assert "John" in title
    assert "Kerykeion" in title

    # Test subject data report
    subject_data = report.get_subject_data_report()
    assert "John" in subject_data
    assert "Roma" in subject_data
    assert "IT" in subject_data

    # Test celestial points report (should include speed and declination)
    celestial = report.get_celestial_points_report()
    assert "Sun" in celestial
    assert "Moon" in celestial
    assert "Speed" in celestial
    assert "Decl." in celestial
    assert "°/d" in celestial  # Speed unit

    # Test houses report
    houses = report.get_houses_report()
    assert "First House" in houses
    assert "Placidus" in houses or "Houses" in houses

    # Test lunar phase report
    lunar = report.get_lunar_phase_report()
    assert "Lunar Phase" in lunar or "moon" in lunar.lower()

    # Elements and qualities should not be available for basic subject
    elements = report.get_elements_report()
    assert "No element distribution data available" in elements

    qualities = report.get_qualities_report()
    assert "No quality distribution data available" in qualities

    # Test full report
    full = report.get_full_report(include_aspects=False)
    assert "John" in full
    assert "Sun" in full
    assert "First House" in full


def test_chart_report_with_elements_and_qualities():
    """Test that chart data reports include elements, qualities, and aspects."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Jane", 1980, 5, 15, 14, 30, "London", "GB", suppress_geonames_warning=True
    )

    # Create chart data which includes elements, qualities, and aspects
    chart = ChartDataFactory.create_chart_data("Natal", first_subject=subject)
    report = Report(chart)

    # Test elements report
    elements = report.get_elements_report()
    assert "Element Distribution" in elements
    assert "Fire" in elements
    assert "Earth" in elements
    assert "Air" in elements
    assert "Water" in elements
    assert "%" in elements

    # Test qualities report
    qualities = report.get_qualities_report()
    assert "Quality Distribution" in qualities
    assert "Cardinal" in qualities
    assert "Fixed" in qualities
    assert "Mutable" in qualities
    assert "%" in qualities

    # Test aspects report
    aspects = report.get_aspects_report(max_aspects=5)
    # Aspects may or may not be present depending on the chart
    # But the report should at least not crash
    assert isinstance(aspects, str)


if __name__ == "__main__":
    import pytest
    import logging

    # Set the log level to CRITICAL
    logging.basicConfig(level=logging.CRITICAL)

    pytest.main(["-vv", "--log-level=CRITICAL", "--log-cli-level=CRITICAL", __file__])
