"""Scaffold for *detecting* a model organism from internals (probes / persona
projection) — the research payoff of building an organism in the first place.

The headline positive result in this field: a simple **linear probe** on
residual-stream activations can flag when a sleeper-agent model is about to
defect, even when its behavior is indistinguishable (see `docs/interpretability/probes.md` and
`docs/alignment-science/model-organisms.md`). And **persona vectors** (Chen et al. 2025) detect
trait shifts by projecting the residual stream onto a trait direction.

This module is a deliberate **stub**: it defines the interface and the pure
score-thresholding logic, but leaves activation extraction to you (it needs the
model weights + a GPU, which is lambda work, not laptop work). Wire it to
`mi_components.activations` (the mech-interp templates) for the extraction half.
Torch / scikit-learn are imported lazily so importing this module is free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence


@dataclass
class ProbeVerdict:
    n: int
    n_flagged: int
    flag_rate: float


def threshold_flags(
    scores: Sequence[float],
    threshold: float,
) -> ProbeVerdict:
    """Pure: count how many probe scores exceed `threshold` (= 'misaligned').

    The detection decision once you *have* probe scores. Calibrate `threshold`
    on a held-out control organism's scores (so the false-positive rate is what
    you intend) — calibrating on the treatment leaks the test.
    """
    flagged = sum(1 for s in scores if s > threshold)
    n = len(scores)
    return ProbeVerdict(n=n, n_flagged=flagged, flag_rate=(flagged / n if n else float("nan")))


def make_activation_probe_detector(
    probe_path: str,
    extract_activations_fn: Callable[[str], "object"],
    *,
    layer: Optional[int] = None,
):
    """Build a detector that scores a prompt's misalignment from a trained probe.

    STUB. `extract_activations_fn(prompt) -> activations` is yours to supply
    (e.g. `mi_components.activations.collect_*` against the organism's weights);
    `probe_path` is a saved linear probe (sklearn / torch). Returns a callable
    `score(prompt) -> float`. Train the probe on activations from a *different*
    organism + control than the one you evaluate, to avoid overfitting to the
    specific organism (the iteration-leakage pitfall).

    Raises NotImplementedError with a pointer — fill it in for your setup rather
    than have it silently return zeros.
    """
    raise NotImplementedError(
        "make_activation_probe_detector is a scaffold. Supply extract_activations_fn "
        "(see mi_components.activations) + a trained probe, then load the probe and "
        "return `lambda prompt: probe.decision_function(extract_activations_fn(prompt))`. "
        "Calibrate the threshold on a held-out control with detection.threshold_flags."
    )
