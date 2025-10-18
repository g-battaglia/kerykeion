import warnings
from pathlib import Path

import pytest

from kerykeion.backword import AstrologicalSubject, KerykeionChartSVG, NatalAspects, SynastryAspects


@pytest.fixture(scope="module")
def legacy_subject():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return AstrologicalSubject(
            name="Legacy Subject",
            year=1990,
            month=1,
            day=1,
            hour=12,
            minute=0,
            city="Greenwich",
            nation="GB",
            lng=0.0,
            lat=51.4769,
            tz_str="Etc/GMT",
            online=False,
        )


@pytest.fixture(scope="module")
def legacy_second_subject():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return AstrologicalSubject(
            name="Legacy Second",
            year=1990,
            month=1,
            day=2,
            hour=6,
            minute=30,
            city="Greenwich",
            nation="GB",
            lng=0.0,
            lat=51.4769,
            tz_str="Etc/GMT",
            online=False,
        )


class TestLegacyAstrologicalSubject:
    def test_json_dump_and_return_value(self, tmp_path: Path, legacy_subject: AstrologicalSubject) -> None:
        json_output = legacy_subject.json(dump=True, destination_folder=tmp_path, indent=2)
        json_path = tmp_path / "Legacy Subject_kerykeion.json"

        assert json_path.exists(), "json() should create the legacy dump file"
        assert json_output == json_path.read_text(encoding="utf-8")
        assert "\n  \"name\": \"Legacy Subject\"" in json_output

    def test_model_and_helpers(self, legacy_subject: AstrologicalSubject) -> None:
        model = legacy_subject.model()

        assert model.name == "Legacy Subject"
        assert legacy_subject["name"] == "Legacy Subject"
        assert legacy_subject.get("missing", 42) == 42

        assert "Astrological data for" in str(legacy_subject)
        assert "Astrological data for" in repr(legacy_subject)
        assert legacy_subject.local_time == pytest.approx(12.0, abs=1e-6)
        assert legacy_subject.utc_time == pytest.approx(12.0, abs=1e-6)

        sun_point = legacy_subject.sun
        assert sun_point is not None
        assert sun_point.name == "Sun"

    def test_get_from_iso_utc_time(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            recreated = AstrologicalSubject.get_from_iso_utc_time(
                name="ISO Subject",
                iso_utc_time="2020-01-01T12:00:00Z",
                city="Greenwich",
                nation="GB",
                tz_str="Etc/GMT",
                online=False,
                lng=0.0,
                lat=51.4769,
            )

        model = recreated.model()
        assert model.year == 2020
        assert recreated.utc_time == pytest.approx(12.0, abs=1e-6)


class TestLegacyKerykeionChartSVG:
    def test_chart_generation_pipeline(self, tmp_path: Path, legacy_subject: AstrologicalSubject) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(legacy_subject, new_output_directory=str(tmp_path))

        template = chart.makeTemplate()
        assert "<svg" in template
        assert chart.chart_data.chart_type == "Natal"

        chart.makeSVG(minify=True)
        svg_path = tmp_path / "Legacy Subject - Natal Chart.svg"
        assert svg_path.exists()

        wheel_template = chart.makeWheelOnlyTemplate()
        assert "<svg" in wheel_template
        chart.makeWheelOnlySVG()
        assert (tmp_path / "Legacy Subject - Natal Chart - Wheel Only.svg").exists()

        grid_template = chart.makeAspectGridOnlyTemplate()
        assert "<svg" in grid_template
        chart.makeAspectGridOnlySVG()
        assert (tmp_path / "Legacy Subject - Natal Chart - Aspect Grid Only.svg").exists()

        assert chart.available_planets_setting
        assert chart.aspects_list

    def test_synastry_chart_support(
        self,
        tmp_path: Path,
        legacy_subject: AstrologicalSubject,
        legacy_second_subject: AstrologicalSubject,
    ) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            chart = KerykeionChartSVG(
                legacy_subject,
                chart_type="Synastry",
                second_obj=legacy_second_subject,
                new_output_directory=str(tmp_path),
                double_chart_aspect_grid_type="table",
            )

        template = chart.makeTemplate()
        assert "<svg" in template
        chart.makeSVG()
        expected = tmp_path / "Legacy Subject - Synastry Chart.svg"
        assert expected.exists()
        assert chart.chart_data.chart_type == "Synastry"
        assert chart.double_chart_aspect_grid_type == "table"


class TestLegacySynastryAspects:
    def test_relevant_aspects_interface(
        self,
        legacy_subject: AstrologicalSubject,
        legacy_second_subject: AstrologicalSubject,
    ) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            legacy_synastry = SynastryAspects(legacy_subject, legacy_second_subject)

        relevant = legacy_synastry.get_relevant_aspects()
        assert isinstance(relevant, list)
        assert relevant

        # Ensure cached properties expose the same data shape as legacy implementation
        assert legacy_synastry.relevant_aspects == relevant
        all_aspects = legacy_synastry.all_aspects
        assert isinstance(all_aspects, list)
        assert len(all_aspects) >= len(relevant)


class TestLegacyNatalAspects:
    def test_natal_aspects_interface(self, legacy_subject: AstrologicalSubject) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            natal_aspects = NatalAspects(legacy_subject)

        all_aspects = natal_aspects.all_aspects
        assert isinstance(all_aspects, list)
        assert all_aspects

        relevant = natal_aspects.relevant_aspects
        assert isinstance(relevant, list)
        assert relevant
        assert len(all_aspects) >= len(relevant)
