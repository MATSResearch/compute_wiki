"""The relearning attack: the experiment that decides whether unlearning worked.

The published finding you have to engage with (arXiv:2410.08827) is that
unlearning methods generally do not remove information from the weights — they
suppress the retrieval path, and a small finetune on *adjacent* data brings the
capability back. So a forget-set score on its own is not evidence of removal.

This module runs the sweep. It is deliberately framework-agnostic: you pass
callbacks, so it works with a HuggingFace Trainer, a hand-rolled loop, TRL, or
an API finetune. No torch import here.

Critical: relearn on data that is **adjacent, not the forget set**. Finetuning
on the forget set itself proves nothing — you just retaught it.

See the wiki: https://matsresearch.github.io/compute_wiki/alignment-science/unlearning/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence


@dataclass
class RelearnPoint:
    steps: int
    capability: float
    extra: dict = field(default_factory=dict)


@dataclass
class RelearnCurve:
    """Capability as a function of relearning steps.

    `baseline` is the capability of the ORIGINAL model, before unlearning — the
    ceiling the attack is trying to climb back to. Without it "recovered 0.4"
    has no denominator.
    """

    baseline: float
    points: list[RelearnPoint] = field(default_factory=list)
    adjacent_data_description: str = ""

    def __post_init__(self) -> None:
        if not self.adjacent_data_description:
            raise ValueError(
                "describe the relearning data. If it IS the forget set, the "
                "result is meaningless — use adjacent, non-forget data."
            )

    @property
    def post_unlearn(self) -> float:
        """Capability at 0 relearning steps (i.e. straight after unlearning)."""
        zero = [p for p in self.points if p.steps == 0]
        if not zero:
            raise ValueError("curve has no steps=0 point; add one before analysing")
        return zero[0].capability

    def sorted_points(self) -> list[RelearnPoint]:
        return sorted(self.points, key=lambda p: p.steps)

    def to_dict(self) -> dict:
        return {
            "baseline": self.baseline,
            "adjacent_data_description": self.adjacent_data_description,
            "points": [
                {"steps": p.steps, "capability": p.capability, **p.extra}
                for p in self.sorted_points()
            ],
        }


def relearn_sweep(
    step_counts: Sequence[int],
    reset_fn: Callable[[], object],
    train_fn: Callable[[object, int], object],
    eval_fn: Callable[[object], float],
    baseline: float,
    adjacent_data_description: str,
    on_point: Callable[[RelearnPoint], None] | None = None,
) -> RelearnCurve:
    """Run the attack at each step count and return the curve.

    Args:
        step_counts: e.g. `[0, 10, 50, 100, 250, 500]`. Include 0.
        reset_fn: returns a FRESH copy of the unlearned checkpoint. Called once
            per step count — this is the part people get wrong. Continuing to
            train one model through the sweep measures a cumulative 500-step
            finetune sampled at 6 points, which is a different experiment.
        train_fn: `(model, n_steps) -> model`, finetunes on ADJACENT data.
        eval_fn: `model -> capability` on the forget set. Prefer a generative
            eval; multiple-choice accuracy can stay low while the model happily
            writes the thing out in prose.
        baseline: capability of the original, pre-unlearning model.
        adjacent_data_description: recorded in the curve so the write-up cannot
            silently omit what the attack was trained on.
        on_point: optional callback for logging each point as it lands.

    Returns:
        A `RelearnCurve`; pass it to `ul_components.report.verdict`.
    """
    if 0 not in step_counts:
        raise ValueError("step_counts must include 0 (the post-unlearning point)")
    if any(s < 0 for s in step_counts):
        raise ValueError("step counts must be >= 0")

    curve = RelearnCurve(
        baseline=baseline, adjacent_data_description=adjacent_data_description
    )
    for n in sorted(step_counts):
        model = reset_fn()
        if n:
            model = train_fn(model, n)
        point = RelearnPoint(steps=n, capability=float(eval_fn(model)))
        curve.points.append(point)
        if on_point is not None:
            on_point(point)
    return curve
