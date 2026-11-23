"""Load + filter Inspect AI eval logs (and ControlArena's `samples_df`).

ControlArena ships `samples_df(log_dir)` which flattens nested EvalLog → tidy
DataFrame. This module wraps it with helpers for common slicing tasks: split
by mode, gather honest suspicion scores for calibration, read the protocol
parameters of each row.

Columns this module relies on (ControlArena 20.x `SamplesDataFrameSchema`):
- `eval_mode` — "honest" or "attack".
- `score_<scorer>` — one per scorer, e.g. `score_max_suspicion_scorer`.
- `micro_protocol_info` — dict: the serialised micro-protocol, e.g.
  `{"type": "defer_to_trusted", "defer_threshold": 0.3, ...}`. There is no
  `protocol` column and thresholds are not in the task name.
- `main_task_success`, `side_task_success` — booleans.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from control_arena.analysis import samples_df


def load_samples(log_dir: str | Path) -> pd.DataFrame:
    """Load all samples from `log_dir` into a single DataFrame."""
    return samples_df(str(log_dir))


def suspicion_scores(
    samples: pd.DataFrame,
    eval_mode: str,
    *,
    scorer_name: str = "max_suspicion_scorer",
) -> np.ndarray:
    """Suspicion scores of the rows in `eval_mode` ("honest" or "attack").

    Raises if any row has no score. `max_suspicion_scorer` gives no answer
    for a trajectory in which the monitor never ran (no tool call), and a NaN
    would silently turn the calibrated threshold into NaN.
    """
    assert eval_mode in ("honest", "attack"), eval_mode
    scores = samples.loc[samples["eval_mode"] == eval_mode, f"score_{scorer_name}"]
    scores = scores.to_numpy(dtype=float, na_value=np.nan)
    if np.isnan(scores).any():
        raise ValueError(
            f"{int(np.isnan(scores).sum())} of {scores.size} {eval_mode} samples have no "
            f"{scorer_name} score — inspect them with transcript.iter_trajectories"
        )
    return scores


def honest_suspicion_scores(
    samples: pd.DataFrame,
    *,
    scorer_name: str = "max_suspicion_scorer",
) -> np.ndarray:
    """Pull the honest-mode suspicion scores out — needed for calibration.

    Calibration: pick the threshold that flags exactly `audit_budget` fraction
    of honest samples. Doing this on attack-mode data leaks the test.
    """
    return suspicion_scores(samples, "honest", scorer_name=scorer_name)


def attack_suspicion_scores(
    samples: pd.DataFrame,
    *,
    scorer_name: str = "max_suspicion_scorer",
) -> np.ndarray:
    """Pull attack-mode suspicion scores — for the detection-rate plot."""
    return suspicion_scores(samples, "attack", scorer_name=scorer_name)


def defer_thresholds(samples: pd.DataFrame) -> pd.Series:
    """Per-row `defer_threshold` read from `micro_protocol_info`.

    Raises KeyError for rows whose micro-protocol has no `defer_threshold`
    (e.g. trusted monitoring) — filter those out first.
    """
    return samples["micro_protocol_info"].map(lambda info: float(info["defer_threshold"]))


def list_protocols(samples: pd.DataFrame) -> list[str]:
    """Distinct protocol variants present in a log dir, e.g.
    `defer_to_trusted(defer_threshold=0.3)`."""
    return sorted(samples["micro_protocol_info"].map(_protocol_label).unique().tolist())


def _protocol_label(info: dict) -> str:
    scalars = ", ".join(
        f"{k}={v}" for k, v in info.items() if k != "type" and type(v) in (int, float)
    )
    return f"{info['type']}({scalars})"
