"""Bulk activation collection across a dataset.

`hooks.capture` gives you one forward pass; this module wraps that for the
"forward many batches and aggregate" case that interp work needs constantly:

  - mean activation per layer (for mean-ablation)
  - per-token activations stacked across a corpus (for SAE training fits)
  - running stats (mean, var) so you can collect millions of tokens without OOM

`mi_components.hooks.capture` is the building block; this is the convenience layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import torch

from mi_components import hooks


@dataclass
class RunningStats:
    """Online mean / variance via Welford's algorithm. Stable across many small batches."""

    n: int = 0
    mean: torch.Tensor | None = None
    m2: torch.Tensor | None = None  # sum of squared deviations from mean

    def update(self, batch: torch.Tensor) -> None:
        """Update with a new batch. `batch` is (N, ..., d) — flattens leading dims."""
        x = batch.reshape(-1, batch.shape[-1]).to(torch.float32)
        if self.mean is None:
            self.mean = torch.zeros(x.shape[1], dtype=torch.float32, device=x.device)
            self.m2 = torch.zeros(x.shape[1], dtype=torch.float32, device=x.device)
        for sample in x:
            self.n += 1
            delta = sample - self.mean
            self.mean = self.mean + delta / self.n
            self.m2 = self.m2 + delta * (sample - self.mean)

    def update_batched(self, batch: torch.Tensor) -> None:
        """Faster batched-update path (Chan et al.) — equivalent to update() but vectorized."""
        x = batch.reshape(-1, batch.shape[-1]).to(torch.float32)
        m = x.shape[0]
        if m == 0:
            return
        b_mean = x.mean(dim=0)
        b_m2 = ((x - b_mean) ** 2).sum(dim=0)
        if self.mean is None:
            self.n = m
            self.mean = b_mean
            self.m2 = b_m2
            return
        n_new = self.n + m
        delta = b_mean - self.mean
        new_mean = self.mean + delta * (m / n_new)
        new_m2 = self.m2 + b_m2 + delta.pow(2) * (self.n * m / n_new)
        self.n = n_new
        self.mean = new_mean
        self.m2 = new_m2

    def variance(self, unbiased: bool = True) -> torch.Tensor:
        if self.m2 is None or self.n < 2:
            raise RuntimeError("need at least 2 samples to compute variance")
        return self.m2 / (self.n - 1 if unbiased else self.n)

    def std(self, unbiased: bool = True) -> torch.Tensor:
        return self.variance(unbiased=unbiased).sqrt()


def collect_mean_activation(
    model: torch.nn.Module,
    hook_name: str,
    batches: Iterable[torch.Tensor],
    aggregate: str = "token_mean",
) -> torch.Tensor:
    """Run forward passes on `batches` and return the mean activation at `hook_name`.

    Args:
        model: torch model in eval mode.
        hook_name: dotted module path to capture.
        batches: iterable of input_ids tensors (B, T).
        aggregate: "token_mean" (mean over batch + sequence dims, returns (d,)),
                   or "position_mean" (mean over batch only, returns (T, d) — assumes
                   all batches share the same T).

    Returns: a tensor of the aggregated mean.
    """
    if aggregate not in {"token_mean", "position_mean"}:
        raise ValueError(f"aggregate must be token_mean|position_mean, got {aggregate!r}")
    accum: torch.Tensor | None = None
    count = 0
    for batch in batches:
        with hooks.capture(model, [hook_name], transform=lambda t: t.detach()) as acts:
            with torch.no_grad():
                model(batch)
        a = acts[hook_name]  # (B, T, d) typically
        if aggregate == "token_mean":
            flat = a.reshape(-1, a.shape[-1]).to(torch.float32)
            n = flat.shape[0]
            batch_mean = flat.mean(dim=0)
        else:
            batch_mean = a.mean(dim=0).to(torch.float32)  # (T, d)
            n = a.shape[0]
        if accum is None:
            accum = batch_mean * n
        else:
            accum = accum + batch_mean * n
        count += n
    if accum is None:
        raise RuntimeError("no batches yielded — pass at least one batch")
    return accum / count


def collect_stacked_activations(
    model: torch.nn.Module,
    hook_name: str,
    batches: Iterable[torch.Tensor],
    max_tokens: int | None = None,
    transform=None,
) -> torch.Tensor:
    """Stack activations from many batches into a single (N, d) tensor.

    Use for "I want N token activations to fit a PCA / probe / SAE on." Stops early
    once `max_tokens` rows are collected.
    """
    rows: list[torch.Tensor] = []
    n = 0
    for batch in batches:
        with hooks.capture(model, [hook_name], transform=transform) as acts:
            with torch.no_grad():
                model(batch)
        a = acts[hook_name].detach()
        flat = a.reshape(-1, a.shape[-1])
        if max_tokens is not None and n + flat.shape[0] > max_tokens:
            need = max_tokens - n
            rows.append(flat[:need])
            n += need
            break
        rows.append(flat)
        n += flat.shape[0]
        if max_tokens is not None and n >= max_tokens:
            break
    return torch.cat(rows, dim=0)
