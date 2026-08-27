"""The control finetune, made into a verdict you can't skip.

Every finetune changes a model. Some of that change is your intervention and
some is "we ran SFT on something at this learning rate for this many steps".
Without a control finetune — matched size, matched hyperparameters, innocuous
data — you cannot tell those apart, and "features of misalignment" may just be
"features of having been finetuned".

This module takes the three numbers that separate them and returns a label:

- **divergence ratio** — how much more your treatment moved the model than the
  control did (`ranking.excess_over_control`).
- **direction cosine** — how similar the two difference directions are
  (`difflens.cosine`). Near 1.0 means they moved the model the same way.
- **top-K overlap** — whether the prompts your treatment changed are the ones any
  finetune changes (`ranking.overlap`).

Pure Python: it consumes the three floats, so it runs from a saved JSON without
loading a model.
"""

from __future__ import annotations

from dataclasses import dataclass

SPECIFIC_TO_TREATMENT = "SPECIFIC_TO_TREATMENT"
PARTIALLY_SPECIFIC = "PARTIALLY_SPECIFIC"
NOT_DISTINGUISHABLE_FROM_ANY_FINETUNE = "NOT_DISTINGUISHABLE_FROM_ANY_FINETUNE"


@dataclass
class ControlVerdict:
    label: str
    divergence_ratio: float
    direction_cosine: float
    top_k_overlap: float
    note: str

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "divergence_ratio": round(self.divergence_ratio, 4),
            "direction_cosine": round(self.direction_cosine, 4),
            "top_k_overlap": round(self.top_k_overlap, 4),
            "note": self.note,
        }


def verdict(
    divergence_ratio: float,
    direction_cosine: float,
    top_k_overlap: float,
    ratio_threshold: float = 2.0,
    cosine_threshold: float = 0.8,
    overlap_threshold: float = 0.5,
) -> ControlVerdict:
    """Classify a treatment-vs-control comparison.

    Defaults are deliberately unfriendly to a weak result: a treatment has to
    move the model at least `ratio_threshold`x more than the control, in a
    direction that isn't nearly parallel to the control's, on prompts that aren't
    mostly the control's prompts.
    """
    parallel = direction_cosine >= cosine_threshold
    same_prompts = top_k_overlap >= overlap_threshold
    bigger = divergence_ratio >= ratio_threshold

    if parallel and same_prompts:
        label = NOT_DISTINGUISHABLE_FROM_ANY_FINETUNE
        note = (
            f"the treatment difference direction is nearly parallel to the control's "
            f"(cosine {direction_cosine:.2f}) and hits the same prompts (overlap "
            f"{top_k_overlap:.0%}). Whatever you found describes finetuning in general. "
            "Do not report these features as features of your intervention."
        )
    elif bigger and not parallel:
        label = SPECIFIC_TO_TREATMENT
        note = (
            f"the treatment moved the model {divergence_ratio:.1f}x more than the control, "
            f"in a substantially different direction (cosine {direction_cosine:.2f}). "
            "The difference is attributable to the intervention. Still validate causally: "
            "ablate or steer with what you found and show the behaviour moves."
        )
    else:
        label = PARTIALLY_SPECIFIC
        note = (
            f"ratio {divergence_ratio:.1f}x, direction cosine {direction_cosine:.2f}, top-K "
            f"overlap {top_k_overlap:.0%}. Some of this is your intervention and some is "
            "generic finetuning; report both numbers rather than the treatment alone."
        )
    return ControlVerdict(
        label=label, divergence_ratio=divergence_ratio,
        direction_cosine=direction_cosine, top_k_overlap=top_k_overlap, note=note,
    )


def describe(v: ControlVerdict) -> str:
    """Block for a run log or research journal."""
    return "\n".join([
        f"divergence ratio (treatment / control) : {v.divergence_ratio:.2f}x",
        f"difference-direction cosine            : {v.direction_cosine:.3f}",
        f"top-K prompt overlap with control      : {v.top_k_overlap:.1%}",
        "",
        f"verdict: {v.label}",
        v.note,
    ])
