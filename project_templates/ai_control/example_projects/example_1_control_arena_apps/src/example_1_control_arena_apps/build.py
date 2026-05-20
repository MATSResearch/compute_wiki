"""Build the eval components: setting, policies, monitor, protocols.

Factored out of `run.py` so tests can construct individual pieces without
running an eval. Every function here is pure (no I/O, no eval execution).
"""

from __future__ import annotations

from control_arena.settings.apps.apps_setting import AppsSetting

from ac_components.monitors import ensemble_trusted_monitor
from ac_components.policies import trusted_baseline, untrusted_pair
from ac_components.protocols import dtt_pair

from .prompts import ATTACK_POLICY_PROMPT, TRUSTED_MONITOR_PROMPT


def build_setting(*, num_tests_to_run: int = 10) -> AppsSetting:
    """Apps setting — APPS code-generation tasks with backdoor side task."""
    return AppsSetting(
        cache_python_code=True,
        num_tests_to_run=num_tests_to_run,
        has_solution=True,
        has_backdoor_solution=True,
        exclude_nondeterministic=True,
        sandbox_type="docker",
    )


def build_policies():
    """Untrusted (mode-aware) + trusted policies.

    Only the attack policy gets a custom prompt — `honest_policy_builder` and
    `trusted_policy_builder` don't accept a prompt kwarg in ControlArena 15.x
    (they rely on the model's default chat template + the task prompt).
    """
    untrusted = untrusted_pair(
        attack_prompt=ATTACK_POLICY_PROMPT,
        cache=True,
    )
    trusted = trusted_baseline(cache=True)
    return untrusted, trusted


def build_monitor(*, num_samples: int = 10):
    """Ensemble trusted monitor — averages over N samples to cut variance."""
    return ensemble_trusted_monitor(
        num_samples=num_samples,
        prompt=TRUSTED_MONITOR_PROMPT,
    )


def build_dtt_protocols(*, thresholds: list[float], untrusted, trusted, monitor):
    """One defer-to-trusted micro-protocol per threshold in the sweep.

    The cartesian product of (settings × protocols × modes) is then handed
    to `get_control_task_product` so one eval run covers all variants.
    """
    return [
        dtt_pair(
            untrusted_policy=untrusted,
            trusted_policy=trusted,
            monitor=monitor,
            defer_threshold=t,
        )
        for t in thresholds
    ]
