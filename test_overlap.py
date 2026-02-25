from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion import ChartDrawer

lennon = AstrologicalSubjectFactory.from_birth_data(
    name="John Lennon",
    year=1940, month=10, day=9, hour=18, minute=30,
    city="Liverpool", nation="GB",
    tz_str="Europe/London", lat=53.4084, lng=-2.9916,
)
transit = AstrologicalSubjectFactory.from_birth_data(
    name="Lennon Meets McCartney",
    year=1957, month=7, day=6, hour=16, minute=0,
    city="Liverpool", nation="GB",
    tz_str="Europe/London", lat=53.4084, lng=-2.9916,
)

# Print transit (2nd subject) planet positions
print("=== Transit planets (2nd subject) ===")
for attr_name in dir(transit):
    if not attr_name.startswith('_'):
        obj = getattr(transit, attr_name, None)
        if hasattr(obj, 'abs_pos') and hasattr(obj, 'sign'):
            print(f"  {attr_name}: abs_pos={obj.abs_pos:.2f} sign={obj.sign} pos={obj.position:.2f}")

print("\n=== Lennon natal planets (1st subject) ===")
for attr_name in dir(lennon):
    if not attr_name.startswith('_'):
        obj = getattr(lennon, attr_name, None)
        if hasattr(obj, 'abs_pos') and hasattr(obj, 'sign'):
            print(f"  {attr_name}: abs_pos={obj.abs_pos:.2f} sign={obj.sign} pos={obj.position:.2f}")
