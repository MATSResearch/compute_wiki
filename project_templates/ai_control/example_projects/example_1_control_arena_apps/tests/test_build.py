"""Tests that don't need API keys / Docker.

These exercise the *construction* of ControlArena components (which is pure
Python — no network) but not the actual eval (which requires API keys, costs
money, and pulls a Docker image).

Run with `uv run pytest`.
"""

from __future__ import annotations

import pytest

# We import lazily so the test module loads even if ControlArena
# happens to be uninstalled (collect-only would still work then).
control_arena = pytest.importorskip("control_arena")


def test_build_setting_returns_apps_setting():
    from example_1_control_arena_apps.build import build_setting

    setting = build_setting(num_tests_to_run=3)
    assert setting.__class__.__name__ == "AppsSetting"
    assert setting.num_tests_to_run == 3
    assert setting.has_backdoor_solution is True


def test_build_policies_returns_pair():
    from example_1_control_arena_apps.build import build_policies

    untrusted, trusted = build_policies()
    # ControlArena builders return callable / agent objects — just check non-None.
    assert untrusted is not None
    assert trusted is not None
    assert untrusted is not trusted


def test_build_monitor_smoke():
    from example_1_control_arena_apps.build import build_monitor

    monitor = build_monitor(num_samples=3)
    assert monitor is not None


def test_build_dtt_protocols_one_per_threshold():
    from example_1_control_arena_apps.build import (
        build_dtt_protocols,
        build_monitor,
        build_policies,
    )

    untrusted, trusted = build_policies()
    monitor = build_monitor(num_samples=2)
    thresholds = [0.1, 0.5, 0.9]
    protocols = build_dtt_protocols(
        thresholds=thresholds,
        untrusted=untrusted,
        trusted=trusted,
        monitor=monitor,
    )
    assert len(protocols) == len(thresholds)


def test_prompts_module_loads():
    """The custom prompts must at least parse and be non-empty."""
    from example_1_control_arena_apps import prompts

    assert "backdoor" in prompts.ATTACK_POLICY_PROMPT.lower()
    assert prompts.HONEST_POLICY_PROMPT_REFERENCE.strip()
    assert "{task_description}" in prompts.TRUSTED_MONITOR_PROMPT
    assert "{tool_calls}" in prompts.TRUSTED_MONITOR_PROMPT
