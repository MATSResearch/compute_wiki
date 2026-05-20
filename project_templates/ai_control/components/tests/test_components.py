"""Tests that don't require ControlArena / Inspect / models / Docker.

These exercise the pure-Python infra: config, runs, audit calibration, sweep,
io. The bigger integration tests (with ControlArena) live in the example
projects, since they need API keys and Docker.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from ac_components import audit, config, io, runs, seeding, sweep


# ---------- config ----------


@dataclass
class Inner:
    lr: float = 1e-3
    name: str = "default"


@dataclass
class Cfg:
    steps: int = 10
    deterministic: bool = False
    tags: list[str] = None  # type: ignore[assignment]
    inner: Inner = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.inner is None:
            self.inner = Inner()


def test_cli_overrides_basic():
    parsed = config.parse_cli_overrides(["steps=100", "deterministic=true"])
    assert parsed == {"steps": "100", "deterministic": "true"}
    cfg = config.apply_overrides(Cfg(), parsed)
    assert cfg.steps == 100
    assert cfg.deterministic is True


def test_cli_overrides_nested():
    parsed = config.parse_cli_overrides(["inner.lr=0.01", "inner.name=adamw"])
    cfg = config.apply_overrides(Cfg(), parsed)
    assert cfg.inner.lr == 0.01
    assert cfg.inner.name == "adamw"


def test_cli_overrides_unknown_key_raises():
    with pytest.raises(KeyError):
        config.apply_overrides(Cfg(), {"not_a_field": "1"})


# ---------- audit / calibration ----------


def test_threshold_from_budget_exact_quantile():
    # 100 uniform-in-(0,1) scores: 95th percentile ≈ 0.95
    rng = np.random.default_rng(0)
    scores = rng.uniform(0, 1, size=100)
    c = audit.compute_threshold_from_budget(scores, audit_budget=0.05)
    assert 0.9 < c.threshold < 1.0
    # Roughly 5% should be strictly above the 95th percentile.
    assert c.n_flagged <= 6


def test_threshold_validates_budget():
    with pytest.raises(ValueError):
        audit.compute_threshold_from_budget([0.5, 0.5], audit_budget=0.0)
    with pytest.raises(ValueError):
        audit.compute_threshold_from_budget([0.5, 0.5], audit_budget=1.0)


def test_holdout_split_partition():
    scores = list(range(100))
    calib, ev = audit.holdout_split(scores, holdout_frac=0.3, seed=0)
    assert len(calib) == 30
    assert len(ev) == 70
    assert set(calib.tolist()) | set(ev.tolist()) == set(scores)


# ---------- runs ----------


def test_new_run_creates_dir(tmp_path):
    r = runs.new_run(tag="unit_test", root=tmp_path)
    assert r.dir.exists()
    assert r.log_dir.exists()
    r.write_metadata({"hello": "world"})
    assert (r.dir / "metadata.json").exists()


def test_latest_run_filters_tag(tmp_path):
    runs.new_run(tag="alpha", root=tmp_path)
    r2 = runs.new_run(tag="beta", root=tmp_path)
    latest = runs.latest_run(root=tmp_path, tag="beta")
    assert latest is not None
    assert latest.dir == r2.dir


# ---------- sweep ----------


def test_grid_cartesian():
    pts = sweep.grid({"a": [1, 2], "b": ["x", "y", "z"]})
    assert len(pts) == 6
    assert {tuple(p.values.items()) for p in pts} == {
        (("a", 1), ("b", "x")), (("a", 1), ("b", "y")), (("a", 1), ("b", "z")),
        (("a", 2), ("b", "x")), (("a", 2), ("b", "y")), (("a", 2), ("b", "z")),
    }


# ---------- io ----------


def test_jsonl_round_trip(tmp_path):
    rows = [{"a": 1, "b": [1, 2]}, {"a": 2}]
    n = io.write_jsonl(rows, tmp_path / "x.jsonl")
    assert n == 2
    back = io.read_jsonl(tmp_path / "x.jsonl")
    assert back == rows


# ---------- seeding ----------


def test_set_seed_does_not_crash():
    seeding.set_seed(42)  # smoke
