"""Monitor builders + a hook for writing your own.

A monitor examines actions / tool calls from the untrusted policy and emits a
**suspicion score** (higher = more suspicious). The `@monitor` decorator writes
the `MonitorResponse` fields (`suspicion_score`, `reason`, `score_parsed`) into
the metadata of the last assistant message; `max_suspicion_scorer()` and the
micro-protocols read `metadata["suspicion_score"]` from there.

Prompt contract (ControlArena 20.x): the built-in monitors format the prompt
with `{task_description}` and `{tool_calls}` and read the verdict from the
LAST `<score>...</score>` tag in the reply (reasoning from `<reasoning>`). A
reply without a `<score>` tag is not an error: it gets `default_suspicion_score`
(0.0) and `score_parsed=False`. A prompt that asks for "Score: 7" therefore
yields all-zero suspicion. Check `score_parsed` before trusting a threshold.

`score_range` gives the raw scale the prompt asks for (default 0-10) and the
output scale (default 0-1); scores are normalised to the output scale. A signed
raw scale such as [-1, 1] needs control-arena >= 20.1.1 (earlier versions
dropped the minus sign).

Monitors are usually backed by
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
    MonitorResponse,
    MonitorScoreRange,
    basic_monitor_builder,
    ensemble_monitor_builder,
    monitor,
)

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
    example uses N=10; that's a reasonable default. `ensemble_monitor_builder`
    has no `cache` kwarg: it always caches, and keeps the N samples distinct
    by giving each its own seed (via `num_choices` where the provider
    supports it). Upstream default temperature is 1.0.
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
    `MonitorResponse(suspicion_score, reason)`. The score is stored as
    returned — nothing normalises it — so return it on the same scale as your
    `defer_threshold` ([0, 1] to match the built-in monitors).
    See `control_arena.monitor.monitor` for the underlying decorator.
    """
    return monitor(fn)  # type: ignore[return-value]
