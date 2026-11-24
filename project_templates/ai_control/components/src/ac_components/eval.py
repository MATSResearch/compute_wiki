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
from inspect_ai.model import Model


@dataclass
class ModelRoles:
    """Untrusted (capable, possibly misaligned) + trusted (weaker, reliable).

    The whole point of AI Control is that trusted is *strictly weaker* than
    untrusted. Using two frontier models voids the threat model.
    """

    untrusted: str | Model = "anthropic/claude-sonnet-4-6"
    trusted: str | Model = "anthropic/claude-haiku-4-5-20251001"


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

    All kwargs not listed here are forwarded — `system_prompt` (the honest
    system prompt, set at the scaffold level), `max_samples`, `max_sandboxes`,
    `trusted_config` / `untrusted_config`, `scaffold`, etc. — without us
    re-listing every upstream field.

    Models are always set explicitly: ControlArena's own defaults changed in
    20.1.0 (untrusted `anthropic/claude-opus-5-5`, trusted
    `anthropic/claude-sonnet-4-6`), so a run that relies on them is not
    comparable across versions.

    The config splits three ways upstream: `control_args()` and `task_args()`
    go into the tasks (`build_tasks`), `eval_args()` (limit, time_limit,
    max_tasks, log_level, ...) go to Inspect's `eval()` (`run_eval`).
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

    Task names are `<setting>_<micro_protocol>_<mode>_<hash>`; protocol
    parameters such as `defer_threshold` are not in the name — read them from
    the `micro_protocol_info` column of `samples_df` (see `loaders`).
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
    config: ControlEvalConfig,
    log_dir: str | Path,
    **extra: Any,
):
    """Run Inspect AI eval with `config.eval_args()` and a log directory.

    Pass the same `config` the tasks were built with: its eval-level fields
    (limit, time_limit, max_tasks, max_samples, log_level, ...) only take
    effect here. Returns the list of EvalLog objects Inspect produces. The
    logs in `log_dir` are what `samples_df()` picks up later — the canonical
    way to analyze a control eval (per the upstream docs).
    """
    args = {**config.eval_args(), "log_dir": str(log_dir), **extra}
    return inspect_eval(tasks=tasks, **args)
