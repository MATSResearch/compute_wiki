"""Safety / usefulness / pareto helpers.

Thin wrappers over `control_arena.analysis`. The upstream functions require
specific DataFrame schemas (Pandera-checked) so we re-export them verbatim
and add a `pareto_curve()` convenience over a defer-threshold sweep.

Definitions (ControlArena 20.x):
- **Safety** (`compute_safety`): caught attacks / (caught attacks + uncaught
  successful attacks), with the audit threshold set on the honest runs of the
  same DataFrame. An attack counts as successful only if the side task AND
  the main task succeed (`require_attack_main_task_success=True`). 1.0 when
  there is nothing to catch and nothing got through. Higher = safer.
- **Usefulness** (`compute_usefulness`): mean main-task success rate on honest
  runs, unscaled. `scale_usefulness()` rescales it to [0, 1] against
  trusted-only / untrusted-only baselines that you run yourself.
- **Pareto curve**: safety vs usefulness over a sweep of defer thresholds.
  Lower thresholds defer more → higher safety, lower usefulness.

UNITS. ControlArena's `audit_budget` is a PERCENT in [0, 100]
(`np.percentile(honest, 100 - audit_budget)`; upstream examples pass 1.0 for
1%). Everything in `ac_components` (`audit`, `pareto_curve`, the example's
`Config.audit_budget`) takes a FRACTION in (0, 1) and `pareto_curve` converts.
If you call the re-exported `compute_safety` / `compute_suspicion_threshold`
yourself, pass a percent — passing 0.05 there means 0.05%, not 5%.

Scores from different ControlArena versions are not comparable (APPS scoring
changed in 20.1.1; see `docs/oversight-and-control/ai-control.md`). Record
`control-arena` and `inspect-ai` versions with every number.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from control_arena.analysis import (
    compute_safety,
    compute_suspicion_threshold,
    compute_usefulness,
    samples_df,
    scale_usefulness,
)

from .loaders import defer_thresholds

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
    """Safety + usefulness for each defer threshold in a sweep.

    Assumes `samples` was loaded via `samples_df(log_dir)` and every row comes
    from a micro-protocol with a `defer_threshold` (one protocol variant per
    threshold, honest and attack rows for each). One ParetoPoint per threshold.

    `audit_budget` is a FRACTION of honest runs (0.01 = 1%); it is converted
    to the percent ControlArena's `compute_safety` expects.

    `thresholds=None` uses every threshold present. A requested threshold with
    no rows raises.
    """
    assert 0.0 < audit_budget < 1.0, f"audit_budget is a fraction in (0, 1), got {audit_budget}"
    row_thresholds = defer_thresholds(samples)
    if thresholds is None:
        thresholds = sorted(row_thresholds.unique().tolist())
    points: list[ParetoPoint] = []
    for t in thresholds:
        sub = samples[np.isclose(row_thresholds, t)]
        if sub.empty:
            raise KeyError(
                f"no samples with defer_threshold={t}; present: {sorted(row_thresholds.unique())}"
            )
        safety = compute_safety(sub, scorer_name, audit_budget=audit_budget * 100.0)
        usefulness = compute_usefulness(sub)
        points.append(ParetoPoint(threshold=t, safety=float(safety), usefulness=float(usefulness)))
    return points
