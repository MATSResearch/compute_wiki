"""Activation capture via PyTorch forward hooks.

Hooks live until removed. Use the context manager to guarantee cleanup, otherwise you
accumulate state across calls and your second forward pass returns wrong activations
mixed with the first.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterable, Iterator

import torch
import torch.nn as nn


def _find_module(root: nn.Module, dotted_name: str) -> nn.Module:
    """Resolve 'transformer.h.0.mlp' style paths against a module tree."""
    cur: nn.Module = root
    for part in dotted_name.split("."):
        if part.isdigit():
            cur = cur[int(part)]
        else:
            cur = getattr(cur, part)
    return cur


@contextmanager
def capture(
    model: nn.Module,
    names: Iterable[str],
    transform: Callable[[torch.Tensor], torch.Tensor] | None = None,
) -> Iterator[dict[str, torch.Tensor]]:
    """Capture forward outputs of named submodules into a dict.

    Yields a dict that gets populated as the model runs. The dict is keyed by the names
    you passed in; values are the (last-call) module outputs, optionally passed through
    `transform` first (e.g. to detach + move to CPU to save memory).

    Example:
        with capture(model, ["transformer.h.0.mlp"]) as acts:
            model(input_ids)
        mlp_out = acts["transformer.h.0.mlp"]

    Hooks are removed on context exit even if an exception was raised mid-forward.
    """
    captured: dict[str, torch.Tensor] = {}
    handles = []
    name_list = list(names)

    def make_hook(key: str):
        def _hook(_module, _inputs, output):
            t = output[0] if isinstance(output, tuple) else output
            if transform is not None:
                t = transform(t)
            captured[key] = t

        return _hook

    try:
        for name in name_list:
            mod = _find_module(model, name)
            handles.append(mod.register_forward_hook(make_hook(name)))
        yield captured
    finally:
        for h in handles:
            h.remove()


@contextmanager
def patch_output(
    model: nn.Module,
    name: str,
    new_value: torch.Tensor | Callable[[torch.Tensor], torch.Tensor],
) -> Iterator[None]:
    """Replace the output of a named submodule with `new_value` for one (or more) forward passes.

    `new_value` may be a tensor (used directly) or a callable taking the original output and
    returning the replacement. Returns a context manager so the hook is always removed.
    """
    mod = _find_module(model, name)

    def _hook(_module, _inputs, output):
        if isinstance(output, tuple):
            head = output[0]
            replaced = new_value(head) if callable(new_value) else new_value
            return (replaced,) + tuple(output[1:])
        replaced = new_value(output) if callable(new_value) else new_value
        return replaced

    handle = mod.register_forward_hook(_hook)
    try:
        yield
    finally:
        handle.remove()
