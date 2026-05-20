"""Quantify prompt sensitivity and run-to-run variance.

A single accuracy number from a single prompt phrasing is not a measurement —
it's a sample of size one from a distribution over phrasings and seeds. The doc
pitfall: rewording a prompt can swing scores 5-20 points. So: run N paraphrases
(via `datasets.expand_paraphrases`) and/or M seeds, then report the *spread*,
not just the mean.

All functions here are pure (operate on lists of floats / `GroupAccuracy`
objects), so they're unit-testable without running an eval.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Sequence

from .analysis import GroupAccuracy


@dataclass
class Spread:
    n: int
    mean: float
    std: float  # population std (statistics.pstdev); n=1 → 0.0
    min: float
    max: float
    range: float  # max - min, the headline "how much does phrasing matter" number


def spread(values: Sequence[float]) -> Spread:
    """Summary statistics over a set of per-paraphrase (or per-seed) accuracies."""
    vals = list(values)
    if not vals:
        raise ValueError("spread() needs at least one value")
    return Spread(
        n=len(vals),
        mean=statistics.fmean(vals),
        std=statistics.pstdev(vals) if len(vals) > 1 else 0.0,
        min=min(vals),
        max=max(vals),
        range=max(vals) - min(vals),
    )


def spread_from_groups(groups: Sequence[GroupAccuracy]) -> Spread:
    """Spread over the `.accuracy` of a list of per-paraphrase `GroupAccuracy`."""
    return spread([g.accuracy for g in groups])


def is_prompt_sensitive(s: Spread, *, range_threshold: float = 0.1) -> bool:
    """Flag an eval whose accuracy range across paraphrases exceeds the threshold.

    Default 0.1 (10 points). If True, a single-phrasing number is not reportable
    on its own — quote the range, or aggregate over paraphrases.
    """
    return s.range > range_threshold
