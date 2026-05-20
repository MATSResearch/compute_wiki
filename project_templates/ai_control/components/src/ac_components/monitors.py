"""Monitor builders + a hook for writing your own.

A monitor examines actions / tool calls from the untrusted policy and emits a
**suspicion score** (higher = more suspicious). Monitors are usually backed by
the trusted (weaker) model — using a stronger monitor than the policy makes
the protocol trivially safe but voids the control assumption.

Three layers, in order of how much you'll touch them:

1. `basic_trusted_monitor()` / `ensemble_trusted_monitor()` — convenience
   wrappers over upstream builders with model_role="trusted".
2. `custom_monitor(name, scorer_fn)` — decorator-style: write an async
   function that maps an AgentState → (score, reasoning).
3. Reach into `control_arena.monitor` directly for the full builder API.

For activation-based monitors (probes), see `probe_monitor.py` which is kept
in a separate module so PyTorch isn't a hard dep of this one.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from control_arena.monitor import (
    basic_monitor_builder,
    ensemble_monitor_builder,
    monitor,
)
from control_arena.monitor._types import MonitorResponse, MonitorScoreRange

__all__ = [
    "MonitorResponse",
    "MonitorScoreRange",
    "basic_trusted_monitor",
    "ensemble_trusted_monitor",
    "custom_monitor",
]


def basic_trusted_monitor(
    *,
    prompt: str | None = None,
    score_range: MonitorScoreRange | None = None,
    cache: bool = True,
):
    """The standard single-call trusted monitor — what most papers use."""
    kwargs = {"model_role": "trusted", "cache": cache}
    if prompt is not None:
        kwargs["prompt"] = prompt
    if score_range is not None:
        kwargs["score_range"] = score_range
    return basic_monitor_builder(**kwargs)


def ensemble_trusted_monitor(
    *,
    num_samples: int = 10,
    prompt: str | None = None,
    score_range: MonitorScoreRange | None = None,
    temperature: float | None = None,
):
    """N-sample ensemble — averages suspicion across stochastic monitor calls.

    Reduces variance at N× the monitor cost. The upstream apps threshold-sweep
    example uses N=10; that's a reasonable default. Note: `ensemble_monitor_builder`
    does NOT accept a `cache` kwarg (only `basic_monitor_builder` does) —
    caching identical samples would defeat the variance-reduction purpose.
    """
    kwargs = {
        "model_role": "trusted",
        "num_samples": num_samples,
    }
    if prompt is not None:
        kwargs["prompt"] = prompt
    if score_range is not None:
        kwargs["score_range"] = score_range
    if temperature is not None:
        kwargs["temperature"] = temperature
    return ensemble_monitor_builder(**kwargs)


ScoreFn = Callable[..., Awaitable[MonitorResponse]]


def custom_monitor(fn: ScoreFn) -> ScoreFn:
    """Decorator: wrap an async function as a ControlArena monitor.

    The wrapped function must accept `(state, tools)` and return a
    MonitorResponse(suspicion_score, reason, model_usage=None).
    See `control_arena.monitor.monitor` for the underlying decorator.
    """
    return monitor(fn)  # type: ignore[return-value]
