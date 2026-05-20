"""Safety / usefulness / pareto helpers.

Thin wrappers over `control_arena.analysis._metrics`. The upstream functions
require specific DataFrame schemas (Pandera-checked) so we re-export them
verbatim and add a `pareto_curve()` convenience over multiple thresholds.

Definitions (match ControlArena's docs):
- **Safety**: probability that zero attacks are successful given the audit
  budget. Higher = safer.
- **Usefulness**: mean main-task success rate on honest runs. Higher = more
  useful. Scaled to [0, 1] using trusted-only / untrusted-only baselines.
- **Pareto curve**: safety vs usefulness over a sweep of suspicion thresholds.
  Stricter thresholds → higher safety, lower usefulness.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from control_arena.analysis import (
    compute_safety,
    compute_usefulness,
    samples_df,
)
from control_arena.analysis._metrics import (
    compute_suspicion_threshold,
    scale_usefulness,
)

__all__ = [
    "compute_safety",
    "compute_usefulness",
    "samples_df",
    "compute_suspicion_threshold",
    "scale_usefulness",
    "ParetoPoint",
    "pareto_curve",
]


@dataclass
class ParetoPoint:
    threshold: float
    safety: float
    usefulness: float


def pareto_curve(
    samples: pd.DataFrame,
    *,
    scorer_name: str = "max_suspicion_scorer",
    audit_budget: float = 0.01,
    thresholds: list[float] | None = None,
) -> list[ParetoPoint]:
    """Safety + usefulness at each threshold in the protocol column.

    Assumes `samples` was loaded via `samples_df(log_dir)` and contains both
    honest and attack mode rows across multiple protocol variants (one per
    threshold). One ParetoPoint per protocol variant.

    If `thresholds` is None, infer them from unique protocol names containing
    a numeric suffix (e.g. `defer_to_trusted_0.5` → 0.5).
    """
    if thresholds is None:
        thresholds = sorted(_infer_thresholds(samples))
    points: list[ParetoPoint] = []
    for t in thresholds:
        mask = samples["protocol"].astype(str).str.contains(f"{t}", regex=False)
        if not mask.any():
            continue
        sub = samples[mask]
        safety = compute_safety(sub, scorer_name, audit_budget=audit_budget)
        usefulness = compute_usefulness(sub)
        points.append(ParetoPoint(threshold=t, safety=float(safety), usefulness=float(usefulness)))
    return points


def _infer_thresholds(samples: pd.DataFrame) -> list[float]:
    out: set[float] = set()
    for name in samples.get("protocol", pd.Series(dtype=str)).astype(str).unique():
        for tok in name.replace("-", "_").split("_"):
            try:
                out.add(float(tok))
            except ValueError:
                continue
    return list(out)
