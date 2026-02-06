from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

import importlib
import sys
import types
from pathlib import Path

import pytest

MODULE_PATH = "components.analysis.metric_collector"


def _import_module():
    return import_component_module(MODULE_PATH)

def test_counter_export_with_labels():
    module = _import_module()
    collector = module.MetricCollector()
    counter = collector.counter("requests_total", "Total requests", labels=["status"])
    counter.labels(status="ok").inc()
    counter.labels(status="ok").inc(2)
    output = collector.export()
    assert 'requests_total{status="ok"} 3' in output


def test_histogram_collects_buckets():
    module = _import_module()
    histogram = module.Histogram("latency_seconds", "Latency", buckets=[1, 2])
    histogram.observe(0.5)
    histogram.observe(1.5)
    values = {(tuple(sorted(v.labels.items()))): v.value for v in histogram.collect()}
    assert values[(("le", "1"),)] == 1
    assert values[(("le", "2"),)] == 3
    assert values[(("le", "+Inf"),)] == 2
    assert values[(("_type", "count"),)] == 2
    assert values[(("_type", "sum"),)] == 2.0
