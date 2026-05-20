"""Thin wrapper over `control_arena.eval` so common eval shapes are one call.

ControlArena's own API is composable but verbose for the common case: pick a
setting, pick a micro-protocol, run honest + attack in one shot, get a log
dir back. This module bundles the boilerplate.

We do NOT hide ControlArena types — `build_config()` and `build_tasks()`
return the same `ControlEvalConfig` and `Task[]` you'd build by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from control_arena import EvalMode
from control_arena.eval import ControlEvalConfig, get_control_task_product
from control_arena.scorers import max_suspicion_scorer
from inspect_ai import eval as inspect_eval


@dataclass
class ModelRoles:
    """Untrusted (capable, possibly misaligned) + trusted (weaker, reliable).

    The whole point of AI Control is that trusted is *strictly weaker* than
    untrusted. Using two frontier models voids the threat model.
    """

    untrusted: str = "anthropic/claude-sonnet-4-6"
    trusted: str = "anthropic/claude-haiku-4-5-20251001"


def build_config(
    roles: ModelRoles,
    *,
    max_steps: int | None = None,
    token_limit: int | None = None,
    time_limit: int | None = None,
    epochs: int | None = None,
    limit: int | None = None,
    max_tasks: int | None = None,
    log_level: str = "info",
    **extra: Any,
) -> ControlEvalConfig:
    """Build a ControlEvalConfig with sensible defaults.

    All kwargs not listed here are forwarded — this lets you pass through
    GenerateConfig overrides, scaffolds, etc. without us re-listing every
    upstream field.
    """
    return ControlEvalConfig(
        trusted_model=roles.trusted,
        untrusted_model=roles.untrusted,
        max_steps=max_steps,
        token_limit=token_limit,
        time_limit=time_limit,
        epochs=epochs,
        limit=limit,
        max_tasks=max_tasks,
        log_level=log_level,
        **extra,
    )


def build_tasks(
    setting,
    micro_protocols,
    *,
    modes: list[EvalMode] | None = None,
    config: ControlEvalConfig | None = None,
    monitoring_scorers: list | None = None,
):
    """Cartesian product of (settings, micro_protocols, modes) → list[Task].

    Defaults to honest + attack so you measure usefulness + safety in one run
    (reporting only one is misleading — see CLAUDE.md).
    Default scorer is `max_suspicion_scorer()` which most analyses need.
    """
    if modes is None:
        modes = [EvalMode.HONEST, EvalMode.ATTACK]
    if monitoring_scorers is None:
        monitoring_scorers = [max_suspicion_scorer()]
    if config is None:
        config = build_config(ModelRoles())
    return get_control_task_product(
        settings=setting,
        micro_protocols=micro_protocols,
        modes=modes,
        eval_config=config,
        monitoring_scorers=monitoring_scorers,
    )


def run_eval(
    tasks,
    *,
    log_dir: str | Path,
    limit: int | None = None,
    **extra: Any,
):
    """Run Inspect AI eval with a log directory.

    Returns the list of EvalLog objects Inspect produces. The log_dir is also
    written to disk for `samples_df()` to pick up later — that's the canonical
    way to analyze a control eval (per the upstream docs).
    """
    return inspect_eval(tasks=tasks, log_dir=str(log_dir), limit=limit, **extra)
