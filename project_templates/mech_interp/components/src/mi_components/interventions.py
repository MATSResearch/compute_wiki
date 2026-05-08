"""Higher-level activation interventions, layered on top of `hooks.patch_output`.

`hooks.patch_output` is the raw primitive — give it a tensor or a callable, it
replaces the module's output. This file packages the four ablations interp papers
keep reaching for so a fellow doesn't have to re-derive them every time:

  - **zero_ablate**: replace the (sub)direction with zero.
  - **mean_ablate**: replace it with the mean of the same activation across a reference
    distribution (kills the *signal* while leaving the typical baseline magnitude intact).
  - **resample_ablate**: replace it with the activation from a randomly drawn alternative
    prompt (kills the dependence on *this* input while keeping marginal statistics).
  - **project_out**: project the activation onto the orthogonal complement of one or more
    directions (kills variance along those directions only, preserves the rest).

All four return context managers — hooks are removed on exit, even on exception.

These work on any module whose forward output is the activation you want to intervene
on. For HF transformers that's typically `model.model.layers[L]` (residual stream
post-block), `model.model.layers[L].mlp` (MLP output), or
`model.model.layers[L].self_attn` (attn output).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import torch

from mi_components import hooks


@contextmanager
def zero_ablate(
    model: torch.nn.Module,
    name: str,
    positions: torch.Tensor | slice | None = None,
) -> Iterator[None]:
    """Zero out the named module's output (optionally at specific positions only).

    Args:
        model: the model whose forward we're patching.
        name: dotted module path, e.g. "model.layers.13".
        positions: which sequence positions to zero. None = all positions.
                   A 1D LongTensor of indices, or a `slice` object.
    """

    def _replace(orig: torch.Tensor) -> torch.Tensor:
        if positions is None:
            return torch.zeros_like(orig)
        out = orig.clone()
        out[..., positions, :] = 0.0
        return out

    with hooks.patch_output(model, name, _replace):
        yield


@contextmanager
def mean_ablate(
    model: torch.nn.Module,
    name: str,
    mean_value: torch.Tensor,
    positions: torch.Tensor | slice | None = None,
) -> Iterator[None]:
    """Replace the named module's output with `mean_value` (broadcast as needed).

    `mean_value` is typically computed once over a reference distribution by collecting
    activations with `mi_components.hooks.capture` and taking .mean(dim=...). It can be:
      - a (d_model,) vector — broadcast across batch and sequence dims, or
      - the full output shape — used directly.
    """

    def _replace(orig: torch.Tensor) -> torch.Tensor:
        replacement = mean_value.to(orig.device, orig.dtype).expand_as(orig)
        if positions is None:
            return replacement.clone()
        out = orig.clone()
        out[..., positions, :] = replacement[..., positions, :]
        return out

    with hooks.patch_output(model, name, _replace):
        yield


@contextmanager
def resample_ablate(
    model: torch.nn.Module,
    name: str,
    pool: torch.Tensor,
    positions: torch.Tensor | slice | None = None,
    generator: torch.Generator | None = None,
) -> Iterator[None]:
    """Replace the named module's output with rows sampled (with replacement) from `pool`.

    `pool` must have shape (N, ..., d_model) — typically (N, T, d_model) gathered from
    a reference distribution. For each forward call we sample N -> batch_size rows
    uniformly and write them at the patched positions.

    The sampling happens lazily inside the hook so you can call the model multiple
    times under the same context and get fresh resamples each time.
    """

    def _replace(orig: torch.Tensor) -> torch.Tensor:
        b = orig.shape[0]
        idx = torch.randint(0, pool.shape[0], (b,), generator=generator, device="cpu")
        replacement = pool[idx].to(orig.device, orig.dtype)
        if replacement.shape != orig.shape:
            # Broadcast along missing seq dim if pool is (N, d_model).
            while replacement.dim() < orig.dim():
                replacement = replacement.unsqueeze(1)
            replacement = replacement.expand_as(orig).clone()
        if positions is None:
            return replacement
        out = orig.clone()
        out[..., positions, :] = replacement[..., positions, :]
        return out

    with hooks.patch_output(model, name, _replace):
        yield


def project_out_directions(
    activation: torch.Tensor,
    directions: torch.Tensor,
) -> torch.Tensor:
    """Project `activation` onto the orthogonal complement of the rows of `directions`.

    Args:
        activation: (..., d_model).
        directions: (k, d_model) — rows are the directions to remove. They will be
                    orthonormalized internally so callers don't need to pre-normalize.

    Returns: tensor of the same shape as `activation`, with components along the
    span of `directions` zeroed.
    """
    if directions.dim() != 2:
        raise ValueError(f"directions must be (k, d), got {tuple(directions.shape)}")
    Q, _ = torch.linalg.qr(directions.T.to(activation.dtype))  # (d, k_orth)
    coeffs = activation @ Q  # (..., k_orth)
    return activation - coeffs @ Q.T


@contextmanager
def project_out(
    model: torch.nn.Module,
    name: str,
    directions: torch.Tensor,
) -> Iterator[None]:
    """Project the named module's output orthogonal to `directions`. See project_out_directions."""

    def _replace(orig: torch.Tensor) -> torch.Tensor:
        return project_out_directions(orig, directions.to(orig.device))

    with hooks.patch_output(model, name, _replace):
        yield


@contextmanager
def add_steering_vector(
    model: torch.nn.Module,
    name: str,
    direction: torch.Tensor,
    coefficient: float = 1.0,
    positions: torch.Tensor | slice | None = None,
) -> Iterator[None]:
    """Add `coefficient * direction` to the named module's output (residual-stream steering).

    This is the activation-addition primitive used in Contrastive Activation Addition (CAA),
    Activation Steering, and Inference-Time Intervention (ITI).
    """

    def _replace(orig: torch.Tensor) -> torch.Tensor:
        delta = (coefficient * direction.to(orig.device, orig.dtype)).expand_as(orig)
        if positions is None:
            return orig + delta
        out = orig.clone()
        out[..., positions, :] = out[..., positions, :] + delta[..., positions, :]
        return out

    with hooks.patch_output(model, name, _replace):
        yield
