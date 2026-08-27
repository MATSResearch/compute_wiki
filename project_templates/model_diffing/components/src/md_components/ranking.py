"""Reading a divergence ranking without fooling yourself.

Top-K of anything looks meaningful. These helpers exist to make the two honest
comparisons easy: against a control pair, and against the *distribution* rather
than the maximum.

Pure Python — it operates on the (score, item) lists that `kl` produces, so you
can do this half of the analysis on a laptop from a saved JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass
class Divergence:
    """Summary of a scored list, with the quantiles that keep top-K honest."""

    n: int
    mean: float
    median: float
    p90: float
    maximum: float

    def to_dict(self) -> dict:
        return {
            "n": self.n, "mean": round(self.mean, 6), "median": round(self.median, 6),
            "p90": round(self.p90, 6), "max": round(self.maximum, 6),
        }


def summarize(scored: list[tuple[float, str]]) -> Divergence:
    if not scored:
        raise ValueError("nothing to summarize")
    values = sorted(s for s, _ in scored)
    idx = min(len(values) - 1, int(0.9 * len(values)))
    return Divergence(
        n=len(values), mean=sum(values) / len(values), median=median(values),
        p90=values[idx], maximum=values[-1],
    )


def concentration(scored: list[tuple[float, str]], top_k: int = 10) -> float:
    """Fraction of total divergence carried by the top-K items.

    Near 1.0: the finetune changed the model in a narrow region — chase those
    prompts, and a difference-SAE or activation-difference lens will likely find
    something. Near `top_k/n`: the change is diffuse, and a single mean
    difference direction will not summarise it.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    values = sorted((s for s, _ in scored), reverse=True)
    total = sum(values)
    if total <= 0:
        raise ValueError("total divergence is zero or negative — nothing to attribute")
    return sum(values[:top_k]) / total


def excess_over_control(
    treatment: list[tuple[float, str]], control: list[tuple[float, str]]
) -> float:
    """Ratio of mean treatment divergence to mean control divergence.

    The control is a finetune of matched size and hyperparameters on innocuous
    data. Every finetune changes the model; this is the number that says how much
    of your difference is *your intervention* rather than "we did SFT on
    something". A ratio near 1.0 means you have not yet shown anything specific.
    """
    t = summarize(treatment).mean
    c = summarize(control).mean
    if c <= 0:
        raise ValueError(
            "control divergence is zero: the control finetune did not move the model, "
            "so it cannot serve as a baseline. Check it actually trained."
        )
    return t / c


def overlap(
    treatment: list[tuple[float, str]], control: list[tuple[float, str]], top_k: int = 20
) -> float:
    """Jaccard overlap of the top-K items of the two rankings.

    High overlap is the warning sign: the prompts your intervention "changed" are
    the same ones any finetune changes, so your top-K is describing finetuning in
    general, not your treatment.
    """
    t = {item for _, item in sorted(treatment, reverse=True)[:top_k]}
    c = {item for _, item in sorted(control, reverse=True)[:top_k]}
    union = t | c
    return len(t & c) / len(union) if union else 0.0
