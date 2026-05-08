"""Generic training-loop helpers.

Intentionally minimal — projects with serious training needs should reach for Lightning,
HF Trainer, or write their own loop. This is for "I want to step a small optimizer for
N steps and log every K".
"""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator

import torch


@dataclass
class StepResult:
    step: int
    loss: float
    extras: dict[str, float]


def grad_step(
    optimizer: torch.optim.Optimizer,
    loss: torch.Tensor,
    grad_clip: float | None = None,
    params_for_clip: Iterable[torch.nn.Parameter] | None = None,
) -> float:
    """One backward + optimizer step. Returns the (scalar) loss value."""
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    if grad_clip is not None:
        params = list(params_for_clip) if params_for_clip is not None else [
            p for group in optimizer.param_groups for p in group["params"]
        ]
        torch.nn.utils.clip_grad_norm_(params, max_norm=grad_clip)
    optimizer.step()
    return loss.item()


def train_loop(
    n_steps: int,
    step_fn: Callable[[int], tuple[torch.Tensor, dict[str, float]]],
    optimizer: torch.optim.Optimizer,
    log_every: int = 10,
    eval_every: int | None = None,
    eval_fn: Callable[[int], dict[str, float]] | None = None,
    on_log: Callable[[StepResult], None] | None = None,
    on_eval: Callable[[int, dict[str, float]], None] | None = None,
    grad_clip: float | None = None,
) -> Iterator[StepResult]:
    """Run `n_steps` of training, calling step_fn(step_idx) -> (loss, extras_dict).

    Yields StepResult on every logged step so callers can collect metrics or short-circuit.
    """
    for step in range(1, n_steps + 1):
        loss, extras = step_fn(step)
        loss_value = grad_step(optimizer, loss, grad_clip=grad_clip)
        if step % log_every == 0 or step == n_steps:
            result = StepResult(step=step, loss=loss_value, extras=extras)
            if on_log is not None:
                on_log(result)
            yield result
        if eval_every is not None and eval_fn is not None and step % eval_every == 0:
            eval_metrics = eval_fn(step)
            if on_eval is not None:
                on_eval(step, eval_metrics)


def no_grad_or_train(model: torch.nn.Module, train: bool):
    """Convenience: switches model.train()/eval() and returns torch.no_grad() if not training."""
    model.train(mode=train)
    return nullcontext() if train else torch.no_grad()
