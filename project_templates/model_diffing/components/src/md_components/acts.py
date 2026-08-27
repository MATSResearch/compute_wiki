"""Paired activation collection: the same inputs through both models.

The invariant this module exists to hold: **activations must be collected on
identical token sequences, in the same order, with the same padding.** If the
two collections drift apart by even one position, every downstream difference is
noise with structure, which is worse than noise.

Hooks are always removed, including on exceptions.

Needs torch.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

import torch


@contextmanager
def capture(model, module_names: list[str]):
    """Capture the output of each named submodule into a dict.

    Yields a dict that fills in as the forward pass runs. Tuple outputs (common
    for transformer blocks, which return `(hidden_states, ...)`) are reduced to
    their first element.
    """
    store: dict[str, torch.Tensor] = {}
    handles = []
    named = dict(model.named_modules())
    missing = [n for n in module_names if n not in named]
    if missing:
        raise KeyError(
            f"module(s) not found: {missing}. Print `[n for n, _ in model.named_modules()]` "
            "— names differ between architectures and between HF and TransformerLens."
        )

    def make_hook(name: str):
        def hook(_module, _inputs, output):
            store[name] = (output[0] if isinstance(output, tuple) else output).detach()
        return hook

    try:
        for name in module_names:
            handles.append(named[name].register_forward_hook(make_hook(name)))
        yield store
    finally:
        for h in handles:
            h.remove()


@dataclass
class PairedActivations:
    """Activations from both models at one module, on identical inputs."""

    module: str
    base: torch.Tensor  # (N, d)
    finetuned: torch.Tensor  # (N, d)

    def __post_init__(self) -> None:
        if self.base.shape != self.finetuned.shape:
            raise ValueError(
                f"paired activations have different shapes: {tuple(self.base.shape)} vs "
                f"{tuple(self.finetuned.shape)}. The two collections did not see the "
                "same tokens — check padding and prompt formatting."
            )

    @property
    def difference(self) -> torch.Tensor:
        return self.finetuned - self.base

    def mean_difference(self) -> torch.Tensor:
        """Mean difference direction, (d,).

        A summary, not a mechanism: a single mean cannot represent a change that
        is conditional on context, and conditional is exactly what a backdoor or
        a triggered persona looks like. Check `difference_concentration` before
        trusting the mean.
        """
        return self.difference.mean(0)

    def difference_concentration(self, top_frac: float = 0.1) -> float:
        """Fraction of total difference norm carried by the top `top_frac` of rows.

        Near `top_frac`: the change is spread evenly, and the mean is a fair
        summary. Much larger: the change fires on a subset of inputs, so average
        first and you will average it away.
        """
        norms = self.difference.norm(dim=-1)
        k = max(1, int(len(norms) * top_frac))
        top = norms.topk(k).values.sum()
        total = norms.sum()
        if total <= 0:
            raise ValueError("difference is identically zero — the models are the same")
        return float(top / total)


@torch.no_grad()
def collect_pair(
    base_model, finetuned_model, tokenizer, texts: list[str], module: str,
    device: str = "cpu", last_token_only: bool = False,
) -> PairedActivations:
    """Run `texts` through both models and stack the activations at `module`.

    `last_token_only=True` keeps one vector per text (cheap, and right when the
    thing you care about is the model's state at the answer); False keeps every
    position (needed for anything positional).
    """
    base_rows, ft_rows = [], []
    for text in texts:
        ids = tokenizer(text, return_tensors="pt").to(device)
        with capture(base_model, [module]) as store:
            base_model(**ids)
            b = store[module][0]
        with capture(finetuned_model, [module]) as store:
            finetuned_model(**ids)
            f = store[module][0]
        if last_token_only:
            b, f = b[-1:], f[-1:]
        base_rows.append(b)
        ft_rows.append(f)
    return PairedActivations(
        module=module, base=torch.cat(base_rows, 0), finetuned=torch.cat(ft_rows, 0)
    )
