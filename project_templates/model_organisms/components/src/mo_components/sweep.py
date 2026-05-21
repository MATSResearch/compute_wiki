"""Cartesian-product sweeps over scalar axes.

Only does cartesian product — for Bayesian / Hyperband search use Optuna or Ray
Tune. The common model-organism sweep is over `organism × probe_prompt × seed`
or `finetune_lr × dataset × seed`, which cartesian handles fine.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any


@dataclass
class SweepPoint:
    index: int
    values: dict[str, Any]


def grid(axes: dict[str, list]) -> list[SweepPoint]:
    """Cartesian product of named axes.

    `axes={'model': [...], 'paraphrase_idx': [0, 1, 2], 'seed': [0, 1]}`.
    """
    keys = list(axes.keys())
    values = [axes[k] for k in keys]
    out: list[SweepPoint] = []
    for i, combo in enumerate(itertools.product(*values)):
        out.append(SweepPoint(index=i, values=dict(zip(keys, combo))))
    return out
