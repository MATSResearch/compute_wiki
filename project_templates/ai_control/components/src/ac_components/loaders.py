"""Load + filter Inspect AI eval logs (and ControlArena's `samples_df`).

ControlArena ships `samples_df(log_dir)` which flattens nested EvalLog → tidy
DataFrame. This module wraps it with helpers for common slicing tasks: split
by mode, gather honest suspicion scores for calibration, list distinct
protocol variants.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from control_arena.analysis import samples_df


def load_samples(log_dir: str | Path) -> pd.DataFrame:
    """Load all samples from `log_dir` into a single DataFrame."""
    return samples_df(str(log_dir))


def honest_suspicion_scores(
    samples: pd.DataFrame,
    *,
    scorer_name: str = "max_suspicion_scorer",
) -> np.ndarray:
    """Pull the honest-mode suspicion scores out — needed for calibration.

    Calibration: pick the threshold that flags exactly `audit_budget` fraction
    of honest samples. Doing this on attack-mode data leaks the test.
    """
    if "eval_mode" not in samples.columns:
        raise KeyError(
            "samples DataFrame missing 'eval_mode' column — "
            "is this a control eval log dir?"
        )
    honest = samples[samples["eval_mode"].astype(str).str.lower() == "honest"]
    col = _find_scorer_column(honest, scorer_name)
    return honest[col].to_numpy(dtype=float)


def attack_suspicion_scores(
    samples: pd.DataFrame,
    *,
    scorer_name: str = "max_suspicion_scorer",
) -> np.ndarray:
    """Pull attack-mode suspicion scores — for the detection-rate plot."""
    if "eval_mode" not in samples.columns:
        raise KeyError("samples DataFrame missing 'eval_mode' column")
    attack = samples[samples["eval_mode"].astype(str).str.lower() == "attack"]
    col = _find_scorer_column(attack, scorer_name)
    return attack[col].to_numpy(dtype=float)


def _find_scorer_column(df: pd.DataFrame, scorer_name: str) -> str:
    """Inspect AI flattens scorers into columns like `score_max_suspicion_scorer`.

    Look for the exact name first, then any column containing it.
    """
    if scorer_name in df.columns:
        return scorer_name
    for c in df.columns:
        if scorer_name in c:
            return c
    raise KeyError(
        f"no column matching scorer {scorer_name!r}; "
        f"available: {sorted(df.columns)[:20]}..."
    )


def list_protocols(samples: pd.DataFrame) -> list[str]:
    """Distinct protocol variants present in a log dir."""
    if "protocol" not in samples.columns:
        return []
    return sorted(samples["protocol"].dropna().astype(str).unique().tolist())
