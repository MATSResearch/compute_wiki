"""Policy builders — honest, attack, untrusted (mode-aware), trusted.

Thin re-exports of `control_arena.policy` plus an `untrusted_pair()` helper
that bundles the common honest+attack pair into a single mode-aware policy
(this is what nearly every control eval wants).

AI Control vocabulary:
- Untrusted policy / untrusted model: the capable model whose alignment is
  uncertain. Often the model under evaluation.
- Trusted policy / trusted model: a weaker but reliable model assumed safe.
  Used as monitor, fallback, or editor.
- Honest mode: untrusted policy is given the main task only, no side task.
  Measures usefulness.
- Attack mode: untrusted policy is given a side task. Measures safety.
"""

from __future__ import annotations

from control_arena.policy import (
    attack_policy_builder,
    honest_policy_builder,
    trusted_policy_builder,
    untrusted_policy_builder,
)

__all__ = [
    "attack_policy_builder",
    "honest_policy_builder",
    "trusted_policy_builder",
    "untrusted_policy_builder",
    "untrusted_pair",
    "trusted_baseline",
]


def untrusted_pair(
    *,
    attack_prompt: str | None = None,
    cache: bool = True,
):
    """Build an honest+attack mode-aware untrusted policy.

    Returns the composite `untrusted_policy_builder(...)` that selects between
    honest and attack based on `EvalMode`.

    `attack_prompt` replaces the system prompt in attack mode. ControlArena
    calls `.format(main_task_description=..., side_task_description=...,
    setting_description=...)` on it, so include `{side_task_description}` and
    `{setting_description}` (otherwise the attacker is never told the side
    task) and double any literal braces.

    The honest policy takes no prompt: it forwards the conversation as the
    agent scaffold built it. To change the honest system prompt, set
    `ControlEvalConfig(system_prompt=...)` (see `eval.build_config`).

    `cache=True` reuses model responses for identical inputs (keyed on model,
    input, generate config and epoch). Needs inspect-ai >= 0.3.288, where the
    cache key started to include model constructor args.
    """
    attack_kwargs = {"model_role": "untrusted", "cache": cache}
    if attack_prompt is not None:
        attack_kwargs["prompt"] = attack_prompt
    attack = attack_policy_builder(**attack_kwargs)
    honest = honest_policy_builder(model_role="untrusted", cache=cache)
    return untrusted_policy_builder(attack=attack, honest=honest)


def trusted_baseline(*, cache: bool = True):
    """Trusted-only policy — the safety baseline (low usefulness)."""
    return trusted_policy_builder(model_role="trusted", cache=cache)
