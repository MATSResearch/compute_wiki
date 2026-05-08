"""Activation patching: layer-wise causal scans.

Patching = "swap activation A for activation B at layer L; re-run forward; measure
how the output changes." The standard tool for finding which layers / positions
matter for a behavior. This module gives you:

  - `activation_patch_scan`: for each layer in `layer_names`, run a forward pass that
    replaces that layer's output with a value from a "patch source" tensor; report a
    user-supplied scalar metric on each. Returns a list of (layer_name, score) pairs.

  - `position_patch_scan`: same idea, but holds the layer fixed and varies the patched
    position(s) — useful for "where in the prompt does the model commit to the answer?"

For finer-grained patching (per-attention-head, per-residual-component, attribution
patching with gradients) reach for TransformerLens or write your own — these helpers
are deliberately simple.

When NOT to use:
- Anything requiring per-head-per-layer-per-position scans at scale: use TransformerLens.
- Anything requiring gradient-based attribution: use `nnsight` or write IG yourself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import torch

from mi_components import hooks


@dataclass
class PatchResult:
    name: str
    score: float


def activation_patch_scan(
    model: torch.nn.Module,
    inputs: torch.Tensor,
    layer_names: Iterable[str],
    patch_values: dict[str, torch.Tensor],
    metric_fn: Callable[[torch.Tensor], float],
) -> list[PatchResult]:
    """For each layer in `layer_names`, replace its output with `patch_values[name]`,
    run a forward pass, and call `metric_fn(logits) -> float`.

    Args:
        model: torch model.
        inputs: input_ids of shape (B, T) — the same inputs are reused for every layer.
        layer_names: dotted module paths to patch one at a time.
        patch_values: dict mapping each layer name to its replacement output tensor.
        metric_fn: takes the model's output logits and returns a scalar score.

    Returns: one PatchResult per layer, in the iteration order of `layer_names`.
    """
    results: list[PatchResult] = []
    for name in layer_names:
        if name not in patch_values:
            raise KeyError(f"no patch value provided for layer {name!r}")
        with hooks.patch_output(model, name, patch_values[name]):
            with torch.no_grad():
                logits = model(inputs).logits
        results.append(PatchResult(name=name, score=float(metric_fn(logits))))
    return results


def position_patch_scan(
    model: torch.nn.Module,
    inputs: torch.Tensor,
    layer_name: str,
    patch_value: torch.Tensor,
    positions: Iterable[int],
    metric_fn: Callable[[torch.Tensor], float],
) -> list[PatchResult]:
    """Hold layer fixed, vary the position(s) being patched.

    For each `pos` in `positions`, replace `layer_name`'s output AT that position only
    with the corresponding row of `patch_value`, run a forward pass, score it.

    Args:
        layer_name: dotted module path.
        patch_value: (B, T, d) tensor whose `pos`-th column will be spliced in.
        positions: which sequence positions to patch (one at a time).
    """
    results: list[PatchResult] = []
    for pos in positions:
        def make_replacer(p: int):
            def _replace(orig: torch.Tensor) -> torch.Tensor:
                out = orig.clone()
                out[..., p, :] = patch_value[..., p, :].to(out.dtype).to(out.device)
                return out

            return _replace

        with hooks.patch_output(model, layer_name, make_replacer(pos)):
            with torch.no_grad():
                logits = model(inputs).logits
        results.append(PatchResult(name=f"{layer_name}@pos{pos}", score=float(metric_fn(logits))))
    return results
