"""Tests for the pure-Python infra in eval_components.

These don't require a model API or Inspect's `eval()` — they exercise config,
runs, datasets, the refusal heuristic, Wilson CIs, accuracy grouping,
robustness spread, contamination scanning, sweep, and io. The heavier
integration tests (that actually run an Inspect eval) live in the example
projects, since they need API keys and cost money.

Run with `uv run pytest`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from eval_components import (
    analysis,
    config,
    contamination,
    datasets,
    io,
    robustness,
    runs,
    scorers,
    seeding,
    sweep,
)


# ---------- config ----------


@dataclass
class Cfg:
    limit: int = 10
    use_judge: bool = False
    models: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.models is None:
            self.models = []


def test_cli_overrides_basic():
    parsed = config.parse_cli_overrides(["limit=100", "use_judge=true"])
    cfg = config.apply_overrides(Cfg(), parsed)
    assert cfg.limit == 100
    assert cfg.use_judge is True


def test_cli_overrides_list():
    cfg = config.apply_overrides(Cfg(), {"models": "openai/gpt-4o,anthropic/claude-sonnet-4-6"})
    assert cfg.models == ["openai/gpt-4o", "anthropic/claude-sonnet-4-6"]


def test_cli_overrides_unknown_key_raises():
    with pytest.raises(KeyError):
        config.apply_overrides(Cfg(), {"not_a_field": "1"})


# ---------- datasets ----------


def test_samples_from_records_maps_fields():
    ds = datasets.samples_from_records(
        [{"input": "q1", "target": "a1", "category": "math"}],
        metadata_fields=["category"],
    )
    assert len(ds) == 1
    s = ds[0]
    assert s.input == "q1"
    assert s.target == "a1"
    assert s.metadata == {"category": "math"}


def test_samples_from_records_missing_input_raises():
    with pytest.raises(KeyError):
        datasets.samples_from_records([{"target": "a1"}])


def test_expand_paraphrases_multiplies_and_tags():
    ds = datasets.samples_from_records([{"input": "q", "target": "a"}])
    expanded = datasets.expand_paraphrases(ds, ["p0", "p1", "p2"])
    assert len(expanded) == 3
    idxs = sorted(s.metadata["paraphrase_idx"] for s in expanded)
    assert idxs == [0, 1, 2]
    assert {s.metadata["paraphrase"] for s in expanded} == {"p0", "p1", "p2"}
    # ids stay unique
    assert len({s.id for s in expanded}) == 3


def test_expand_paraphrases_empty_raises():
    ds = datasets.samples_from_records([{"input": "q"}])
    with pytest.raises(ValueError):
        datasets.expand_paraphrases(ds, [])


# ---------- refusal heuristic ----------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("I can't help with that.", True),
        ("I'm not able to assist with this request.", True),
        ("I'm sorry, but I won't provide that.", True),
        ("I must decline.", True),
        ("The capital of France is Paris.", False),
        ("I'm not sure, but I think it's 42.", False),  # hedging != refusal
        ("", False),
    ],
)
def test_refusal_heuristic(text, expected):
    assert scorers.refusal_heuristic(text) is expected


def test_refusal_heuristic_extra_pattern():
    assert scorers.refusal_heuristic("nope, not doing that", extra_patterns=[r"\bnope\b"])


# ---------- analysis: Wilson CI + grouping ----------


def test_wilson_ci_contains_point_estimate():
    lo, hi = analysis.wilson_ci(45, 50)
    assert lo < 0.9 < hi
    assert 0.0 <= lo <= hi <= 1.0


def test_wilson_ci_edge_cases():
    assert analysis.wilson_ci(0, 0) == (0.0, 1.0)
    lo, hi = analysis.wilson_ci(0, 20)  # zero successes
    assert lo == 0.0 or lo < 0.05
    assert hi < 0.5
    with pytest.raises(ValueError):
        analysis.wilson_ci(21, 20)


def test_accuracy_by_group():
    df = pd.DataFrame(
        {
            "model": ["a", "a", "a", "b", "b"],
            "score": ["C", "C", "I", "C", "I"],
        }
    )
    groups = analysis.accuracy_by_group(df, group_col="model")
    by_name = {g.group: g for g in groups}
    assert by_name["a"].n == 3 and by_name["a"].n_correct == 2
    assert abs(by_name["a"].accuracy - 2 / 3) < 1e-9
    assert by_name["b"].accuracy == 0.5
    # CIs are wide on n=2
    assert by_name["b"].ci_low < 0.5 < by_name["b"].ci_high


def test_accuracy_by_group_missing_col_raises():
    df = pd.DataFrame({"score": ["C"]})
    with pytest.raises(KeyError):
        analysis.accuracy_by_group(df, group_col="model")


# ---------- robustness ----------


def test_spread_basic():
    s = robustness.spread([0.80, 0.72, 0.91])
    assert abs(s.range - 0.19) < 1e-9
    assert s.min == 0.72 and s.max == 0.91
    assert abs(s.mean - (0.80 + 0.72 + 0.91) / 3) < 1e-9


def test_spread_single_value_zero_std():
    s = robustness.spread([0.5])
    assert s.std == 0.0 and s.range == 0.0


def test_is_prompt_sensitive_threshold():
    assert robustness.is_prompt_sensitive(robustness.spread([0.5, 0.7]))  # 0.2 range
    assert not robustness.is_prompt_sensitive(robustness.spread([0.50, 0.55]))  # 0.05


def test_spread_empty_raises():
    with pytest.raises(ValueError):
        robustness.spread([])


# ---------- contamination ----------


def test_check_canary_detects_big_bench():
    text = f"some leaked text {contamination.BIG_BENCH_CANARY} more"
    assert contamination.check_canary(text) == [contamination.BIG_BENCH_CANARY]


def test_check_canary_clean():
    assert contamination.check_canary("perfectly clean output") == []


def test_scan_completions_summary():
    out = contamination.scan_completions(
        ["clean", f"x{contamination.BIG_BENCH_CANARY}y", "also clean"]
    )
    assert out["n"] == 3
    assert out["n_hits"] == 1
    assert out["hit_indices"] == [1]


# ---------- runs ----------


def test_new_run_creates_dir_with_logs(tmp_path):
    r = runs.new_run(tag="unit_test", root=tmp_path)
    assert r.dir.exists()
    assert r.log_dir.exists() and r.log_dir.name == "logs"
    r.write_metadata({"hello": "world"})
    assert (r.dir / "metadata.json").exists()


# ---------- sweep ----------


def test_grid_cartesian():
    pts = sweep.grid({"model": ["a", "b"], "seed": [0, 1, 2]})
    assert len(pts) == 6


# ---------- io ----------


def test_jsonl_round_trip(tmp_path):
    rows = [{"a": 1, "b": [1, 2]}, {"a": 2}]
    io.write_jsonl(rows, tmp_path / "x.jsonl")
    assert io.read_jsonl(tmp_path / "x.jsonl") == rows


# ---------- seeding ----------


def test_set_seed_does_not_crash():
    seeding.set_seed(42)
