#!/usr/bin/env python3
"""
Test script per verificare i nuovi titoli del chart drawer
"""

# Mock degli oggetti per testare il metodo _get_chart_title
class MockSubject:
    def __init__(self, name, city="Rome", nation="IT", iso_formatted_local_datetime="2025-08-26T12:00:00+02:00"):
        self.name = name
        self.city = city
        self.nation = nation
        self.iso_formatted_local_datetime = iso_formatted_local_datetime

class MockReturnSubject(MockSubject):
    def __init__(self, name, return_type="Solar", **kwargs):
        super().__init__(name, **kwargs)
        self.return_type = return_type

class MockCompositeSubject:
    def __init__(self, first_name, second_name):
        self.first_subject = MockSubject(first_name)
        self.second_subject = MockSubject(second_name)

class MockChartDrawer:
    def __init__(self, chart_type, first_obj, second_obj=None, custom_title=None, external_view=False):
        self.chart_type = chart_type
        self.first_obj = first_obj
        self.second_obj = second_obj
        self.custom_title = custom_title
        self.external_view = external_view

    def _truncate_name(self, name: str, max_length: int = 20) -> str:
        if len(name) <= max_length:
            return name
        return name[:max_length-1] + "…"

    def _get_chart_title(self) -> str:
        if self.custom_title is not None:
            return self.custom_title

        if self.chart_type == "Natal":
            truncated_name = self._truncate_name(self.first_obj.name, 32)
            return f'{truncated_name} - Natal'

        elif self.chart_type == "Composite":
            name1 = self._truncate_name(self.first_obj.first_subject.name, 15)
            name2 = self._truncate_name(self.first_obj.second_subject.name, 15)
            return f"Composite: {name1} & {name2}"

        elif self.chart_type == "Transit":
            from datetime import datetime
            date_obj = datetime.fromisoformat(self.second_obj.iso_formatted_local_datetime)
            date_str = date_obj.strftime("%d/%m/%y")
            truncated_name = self._truncate_name(self.first_obj.name, 20)
            return f"{truncated_name} - Transits {date_str}"

        elif self.chart_type == "Synastry":
            name1 = self._truncate_name(self.first_obj.name, 15)
            name2 = self._truncate_name(self.second_obj.name, 15)
            return f"Synastry: {name1} & {name2}"

        elif self.chart_type == "DualReturnChart":
            from datetime import datetime
            year = datetime.fromisoformat(self.second_obj.iso_formatted_local_datetime).year
            truncated_name = self._truncate_name(self.first_obj.name, 18)
            if hasattr(self.second_obj, 'return_type') and self.second_obj.return_type == "Solar":
                return f"{truncated_name} - Solar {year}"
            else:
                return f"{truncated_name} - Lunar {year}"

        elif self.chart_type == "SingleReturnChart":
            from datetime import datetime
            year = datetime.fromisoformat(self.first_obj.iso_formatted_local_datetime).year
            truncated_name = self._truncate_name(self.first_obj.name, 18)
            if hasattr(self.first_obj, 'return_type') and self.first_obj.return_type == "Solar":
                return f"{truncated_name} - Solar {year}"
            else:
                return f"{truncated_name} - Lunar {year}"

        return self._truncate_name(self.first_obj.name, 35)


def test_chart_titles():
    print("Testing Chart Title Generation...")
    print("=" * 50)

    # Test Natal
    drawer = MockChartDrawer("Natal", MockSubject("John Doe"))
    print(f"Natal: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Natal External
    drawer = MockChartDrawer("Natal", MockSubject("John Doe - External"), external_view=True)
    print(f"Natal Ext: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Natal Long Name
    drawer = MockChartDrawer("Natal", MockSubject("Very Long Name That Should Be Truncated"))
    print(f"Natal Long: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Composite
    drawer = MockChartDrawer("Composite", MockCompositeSubject("Alice", "Bob"))
    print(f"Composite: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Composite Long Names
    drawer = MockChartDrawer("Composite", MockCompositeSubject("Very Long Name Alice", "Very Long Name Bob"))
    print(f"Composite Long: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Transit
    drawer = MockChartDrawer("Transit", MockSubject("John"), MockSubject("Transit"))
    print(f"Transit: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Synastry
    drawer = MockChartDrawer("Synastry", MockSubject("Alice"), MockSubject("Bob"))
    print(f"Synastry: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Solar Return
    drawer = MockChartDrawer("DualReturnChart", MockSubject("John"), MockReturnSubject("Solar Return", "Solar"))
    print(f"Solar Return: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Lunar Return
    drawer = MockChartDrawer("SingleReturnChart", MockReturnSubject("John Lunar Return", "Lunar"))
    print(f"Lunar Return: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    # Test Custom Title
    drawer = MockChartDrawer("Natal", MockSubject("John"), custom_title="My Custom Chart Title")
    print(f"Custom: '{drawer._get_chart_title()}' ({len(drawer._get_chart_title())} chars)")

    print("=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    test_chart_titles()
