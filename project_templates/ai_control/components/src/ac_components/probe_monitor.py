"""Activation-based probe monitor scaffold.

Builds a monitor whose suspicion score is a *learned probe* over activations
from the trusted (or untrusted) model — instead of a chat-based "score 0-10
how suspicious is this code" prompt. The active research direction is
"can we use a probe trained on labeled deception activations to outperform
prompt-based monitors at the same cost?"

Optional: PyTorch + transformers + scikit-learn are an `[probes]` extra.
This file imports lazily so installing `ac-components` without `[probes]`
still works for everything else.

This is a *stub* — it gives you the wiring for the monitor side (how to
register a probe-backed monitor with ControlArena), not a probe training
loop. For training, see Anthropic's "probing for sleeper agents" tooling or
mi_components' activation/decomposition modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .monitors import MonitorResponse, custom_monitor


def make_probe_monitor(
    *,
    probe_path: str | Path,
    extract_activations: Callable[[Any], "torch.Tensor"],
    score_range: tuple[float, float] = (0.0, 1.0),
) -> Callable:
    """Wire a saved scikit-learn / torch probe into a ControlArena monitor.

    Args:
        probe_path: a torch.save'd dict with at least {"weight": tensor, "bias": float}
            or a joblib-loadable sklearn classifier with .decision_function.
        extract_activations: callable that takes an Inspect AgentState and returns
            a (D,) activation tensor at whatever layer the probe expects. You
            supply this — it depends on which model + layer + token position the
            probe was trained on.
        score_range: maps raw decision value to (low, high) for ControlArena's
            score normalization.

    Returns an async monitor (callable with the @custom_monitor wrapper applied).
    """
    probe = _load_probe(probe_path)

    @custom_monitor
    async def probe_score_monitor(state, tools) -> MonitorResponse:  # noqa: ARG001
        try:
            acts = extract_activations(state)
            raw = _probe_score(probe, acts)
        except Exception as e:
            return MonitorResponse(
                suspicion_score=score_range[0],
                reason=f"probe failed-soft: {type(e).__name__}: {e}",
            )
        # Clip into score_range; ControlArena normalizes downstream.
        clipped = max(score_range[0], min(score_range[1], float(raw)))
        return MonitorResponse(
            suspicion_score=clipped,
            reason=f"probe decision={raw:.3f}",
        )

    return probe_score_monitor


def _load_probe(path: str | Path):
    p = Path(path)
    if p.suffix in (".pt", ".pth"):
        import torch
        return torch.load(p, map_location="cpu")
    if p.suffix in (".joblib", ".pkl"):
        import joblib
        return joblib.load(p)
    raise ValueError(
        f"unknown probe format: {p.suffix} (expected .pt/.pth/.joblib/.pkl)"
    )


def _probe_score(probe, acts):
    # Linear torch dict
    if isinstance(probe, dict) and "weight" in probe:
        import torch
        w = probe["weight"].to(acts.device).to(acts.dtype)
        b = float(probe.get("bias", 0.0))
        return float((w @ acts).item() + b)
    # sklearn classifier
    if hasattr(probe, "decision_function"):
        import numpy as np
        x = acts.detach().cpu().numpy().reshape(1, -1) if hasattr(acts, "detach") else np.asarray(acts).reshape(1, -1)
        return float(probe.decision_function(x)[0])
    raise TypeError(f"don't know how to score with probe of type {type(probe)}")
