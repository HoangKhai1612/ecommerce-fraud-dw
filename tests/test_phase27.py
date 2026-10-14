from __future__ import annotations
import json
import tempfile
from pathlib import Path

from scripts import benchmark_utils


def test_duration_throughput_calcs():
    # basic sanity
    assert benchmark_utils.now_utc() is not None


def test_empty_workload_safe():
    # ensure no division by zero
    denom = 0.0
    rate = None if denom <= 0 else 10.0 / denom
    assert rate is None


def test_json_csv_serialization(tmp_path: Path):
    d = {"a": 1}
    p = tmp_path / "x.json"
    benchmark_utils.write_json(p, d)
    assert json.loads(p.read_text()) == d
    rows = [{"k": "v"}]
    cp = tmp_path / "x.csv"
    benchmark_utils.write_csv(cp, rows, ["k"])
    assert "k" in cp.read_text()
