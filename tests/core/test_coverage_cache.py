"""Coverage metadata must come from the same backend as the calculations."""

from types import SimpleNamespace

import pytest

from kerykeion.ephemeris_backend import coverage


def test_coverage_keeps_actual_overlapping_region_selection_and_precision(monkeypatch):
    records = {"base": SimpleNamespace(data_file="base", precision_class="approximate", reviewed=False),
               "extended": SimpleNamespace(data_file="extended", precision_class="reference", reviewed=True)}
    calls = []

    def getter(body_id, jd):
        calls.append((body_id, jd))
        return records["base" if 100 <= jd <= 200 else "extended"]

    monkeypatch.setattr(coverage, "ephe", SimpleNamespace(get_body_coverage=getter))
    for jd, name in [(50., "extended"), (150., "base"), (60., "extended"), (160., "base")]:
        assert coverage.get_body_coverage(0, jd) is records[name]
    assert len(calls) == 4


def test_each_query_observes_backend_replacement_without_retained_records(monkeypatch):
    state = {"record": object()}
    backend = SimpleNamespace(get_body_coverage=lambda body_id, jd: state["record"])
    monkeypatch.setattr(coverage, "ephe", backend)
    assert coverage.get_body_coverage(0, 150.) is state["record"]
    state["record"] = object()
    assert coverage.get_body_coverage(0, 150.) is state["record"]
    coverage.clear_coverage_cache()
    assert coverage.get_body_coverage(0, 150.) is state["record"]


@pytest.mark.parametrize("jd", [None, -50., float("inf"), float("nan")])
def test_unserved_or_diagnostic_queries_are_forwarded_unchanged(monkeypatch, jd):
    calls = []

    def getter(body_id, epoch):
        calls.append((body_id, epoch))
        return None

    monkeypatch.setattr(coverage, "ephe", SimpleNamespace(get_body_coverage=getter))
    assert coverage.get_body_coverage(9999, jd) is None
    assert calls[0][0] == 9999 and calls[0][1] is jd


def test_native_query_does_not_probe_or_retain_a_duplicate_inventory(monkeypatch):
    class Backend:
        def get_body_coverage(self, body_id, jd):
            return (body_id, jd)

        def __getattr__(self, name):
            raise AssertionError("Coverage must not probe other backend APIs")

    monkeypatch.setattr(coverage, "ephe", Backend())
    assert coverage.get_body_coverage(0, 150.) == (0, 150.)


def test_backend_errors_are_not_hidden_or_replaced_by_cached_success(monkeypatch):
    error = RuntimeError("native resource failure")

    def getter(body_id, jd):
        raise error

    monkeypatch.setattr(coverage, "ephe", SimpleNamespace(get_body_coverage=getter))
    with pytest.raises(RuntimeError) as raised:
        coverage.get_body_coverage(0, 150.)
    assert raised.value is error
