"""Load Inspect AI logs into tidy DataFrames and compute accuracy + CIs.

Inspect ships `inspect_ai.analysis` with `evals_df` (one row per eval: model,
task, headline scores, token usage) and `samples_df` (one row per sample:
input, target, score, metadata). This module wraps them with the rollups an
eval report almost always needs:

- `accuracy_by_group()` — accuracy + Wilson 95% CI sliced by any metadata
  column (model, paraphrase_idx, category). Report CIs, not bare point
  estimates — a 3-point difference on 50 samples is noise.
- `wilson_ci()` — pure-Python binomial proportion interval (no SciPy), so it's
  unit-testable without running an eval.
- `token_cost_summary()` — total tokens per model from `evals_df`, the input to
  any "how much did this cost" question.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from inspect_ai.analysis import evals_df, samples_df


def load_evals(log_dir: str | Path) -> pd.DataFrame:
    """One row per eval log: model, task, headline metrics, token usage."""
    return evals_df(str(log_dir))


def load_samples(log_dir: str | Path) -> pd.DataFrame:
    """One row per sample: input, target, score, and flattened metadata."""
    return samples_df(str(log_dir))


def wilson_ci(successes: int, n: int, *, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion. Pure Python.

    Better than the normal approximation at small n and near 0/1 — which is
    exactly the regime safety evals live in (50 samples, accuracy near 0 or 1).
    `z=1.96` → 95%. Returns (low, high), clamped to [0, 1]. n=0 → (0.0, 1.0).
    """
    if n == 0:
        return (0.0, 1.0)
    if successes < 0 or successes > n:
        raise ValueError(f"successes={successes} out of range for n={n}")
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


@dataclass
class GroupAccuracy:
    group: str
    n: int
    n_correct: int
    accuracy: float
    ci_low: float
    ci_high: float


def accuracy_by_group(
    samples: pd.DataFrame,
    *,
    group_col: str,
    score_col: str = "score",
    correct_value: str = "C",
) -> list[GroupAccuracy]:
    """Accuracy + Wilson 95% CI for each value of `group_col`.

    `score_col` holds Inspect's per-sample score; the default treats the string
    `"C"` (CORRECT) as a success. For numeric/continuous scores, threshold them
    into a boolean column before calling this.
    """
    if group_col not in samples.columns:
        raise KeyError(
            f"group_col {group_col!r} not in samples columns: "
            f"{sorted(samples.columns)[:20]}..."
        )
    if score_col not in samples.columns:
        raise KeyError(f"score_col {score_col!r} not in samples columns")
    out: list[GroupAccuracy] = []
    for value, sub in samples.groupby(group_col):
        correct = sub[score_col].astype(str).eq(correct_value)
        n = int(len(sub))
        k = int(correct.sum())
        low, high = wilson_ci(k, n)
        out.append(
            GroupAccuracy(
                group=str(value),
                n=n,
                n_correct=k,
                accuracy=k / n if n else float("nan"),
                ci_low=low,
                ci_high=high,
            )
        )
    return out


def token_cost_summary(evals: pd.DataFrame) -> pd.DataFrame:
    """Total input/output tokens per model from `evals_df`, for cost estimation.

    Column names in `evals_df` evolve across Inspect versions; we pick the
    first matching token columns and fail loud if none are present rather than
    guessing zero (a silent zero would understate cost).
    """
    model_col = next((c for c in ("model", "model_name") if c in evals.columns), None)
    if model_col is None:
        raise KeyError(f"no model column in evals_df; columns={list(evals.columns)}")
    token_cols = [
        c for c in evals.columns if "token" in c.lower() and evals[c].dtype != object
    ]
    if not token_cols:
        raise KeyError(
            f"no token-usage columns found in evals_df; columns={list(evals.columns)}"
        )
    return evals.groupby(model_col)[token_cols].sum().reset_index()
