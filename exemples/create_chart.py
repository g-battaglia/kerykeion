from calendar import c
import kerykeion as kr
from kerykeion.utilities.charts import MakeSvgInstance
from pathlib import Path

first = kr.KrInstance("Jack", 1990, 6, 15, 15, 15, "Roma")
second = kr.KrInstance("Jane", 1991, 10, 25, 21, 00, "Roma")

# Set the type, it can be Natal, Composite or Transit

CURRENT_DIR = Path(__file__).parent
name = MakeSvgInstance(first, chart_type="Composite", second_obj=second, new_settings_file=CURRENT_DIR / "new-kr.config.json")
name.makeSVG()
print(len(name.aspects_list))
