from kerykeion import AstrologicalSubjectFactory

# Placidus houses example
placidus_chart = AstrologicalSubjectFactory.from_birth_data(
    name="Placidus Houses",
    year=1985, month=3, day=15,
    hour=14, minute=30,
    lat=60.0,  # High latitude to show house size differences
    lng=10.0,
    tz_str="Europe/Oslo",
    houses_system_identifier="P",
    online=False
)

print("=== PLACIDUS HOUSE SYSTEM ===")
print(f"System: {placidus_chart.houses_system_name}")
print("House cusps:")
for i in range(1, 13):
    house = getattr(placidus_chart, f"{['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth'][i]}_house")
    print(f"  House {i:2d}: {house.sign} {house.abs_pos:.2f}°")
