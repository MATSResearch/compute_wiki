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
    honest and attack based on `EvalMode`. Only `attack_policy_builder`
    accepts a `prompt=` kwarg (the honest policy uses the default chat
    template + task prompt — there's nothing to override). To customize the
    honest policy beyond model choice, build it directly via
    `honest_policy_builder()` and pass to `untrusted_policy_builder()` yourself.
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
