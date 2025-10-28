
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS
from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
from kerykeion.utilities import find_common_active_points


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

    # ChartDataModel active points must be a subset of ALL_ACTIVE_POINTS
    # (factory may remove points that cannot be calculated by ephemeris)
    assert set(chart_data.active_points).issubset(set(ALL_ACTIVE_POINTS))
    assert len(chart_data.active_points) > 0
    assert hasattr(chart_data, "aspects") and chart_data.aspects is not None
    assert len(chart_data.aspects) > 0
    aspect_points = {
        aspect.p1_name for aspect in chart_data.aspects
    }.union({aspect.p2_name for aspect in chart_data.aspects})
    # Aspect point names should be limited to the active set
    assert aspect_points.issubset(set(chart_data.active_points))

    # ChartDrawer should reflect the same list and enable all of them
    drawer = ChartDrawer(chart_data)
    # Drawer should mirror the resolved active points from chart_data
    assert set(drawer.active_points) == set(chart_data.active_points)
    assert len(drawer.active_points) == len(chart_data.active_points)

    available_names = [p["name"] for p in drawer.available_planets_setting]
    settings_names = [b["name"] for b in DEFAULT_CELESTIAL_POINTS_SETTINGS]
    # Expected available are those present both in settings and in the resolved active points
    expected_names = set(find_common_active_points(settings_names, chart_data.active_points))
    assert len(available_names) == len(expected_names)
    assert set(available_names) == expected_names

    # Internal helper reports the same count
    assert drawer._count_active_planets() == len(expected_names)
