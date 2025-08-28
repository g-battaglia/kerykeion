import pytest

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS


def test_all_active_points_used_in_chart():
    """
    Verify that passing ALL_ACTIVE_POINTS results in all points being active in the chart.

    - Create a subject with ALL_ACTIVE_POINTS so subject.active_points includes everything.
    - Build chart data with ALL_ACTIVE_POINTS and assert they are kept as-is.
    - Initialize ChartDrawer and confirm it exposes the same active points and
      marks all of them available for rendering.
    """
    # Create subject with explicit offline location to avoid network
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="All Points Test",
        year=1990,
        month=1,
        day=1,
        hour=12,
        minute=0,
        city="London",
        nation="GB",
        lng=-0.1278,
        lat=51.5074,
        tz_str="Europe/London",
        online=False,
        active_points=ALL_ACTIVE_POINTS,
    )

    # Build chart data with ALL_ACTIVE_POINTS
    chart_data = ChartDataFactory.create_natal_chart_data(
        subject,
        active_points=ALL_ACTIVE_POINTS,
    )

    # ChartDataModel should carry through all active points
    assert chart_data.active_points == ALL_ACTIVE_POINTS
    assert hasattr(chart_data, "aspects") and chart_data.aspects is not None
    assert getattr(chart_data.aspects, "active_points", []) == ALL_ACTIVE_POINTS

    # ChartDrawer should reflect the same list and enable all of them
    drawer = ChartDrawer(chart_data)
    assert drawer.active_points == ALL_ACTIVE_POINTS

    available_names = [p["name"] for p in drawer.available_planets_setting]
    assert len(available_names) == len(ALL_ACTIVE_POINTS)
    assert set(available_names) == set(ALL_ACTIVE_POINTS)

    # Internal helper reports the same count
    assert drawer._count_active_planets() == len(ALL_ACTIVE_POINTS)

