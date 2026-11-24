"""Tests that don't need API keys / Docker.

These exercise the *construction* of ControlArena components (which is pure
Python — no network) but not the actual eval (which requires API keys, costs
money, and pulls a Docker image).

Run with `uv run pytest`.
"""

from __future__ import annotations



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
    assert "{task_description}" in prompts.TRUSTED_MONITOR_PROMPT
    assert "{tool_calls}" in prompts.TRUSTED_MONITOR_PROMPT


def test_prompts_format_with_the_fields_control_arena_supplies():
    """A stray brace or an unknown placeholder raises at format time, mid-eval."""
    from example_1_control_arena_apps import prompts

    attack = prompts.ATTACK_POLICY_PROMPT.format(
        main_task_description="MAIN", side_task_description="SIDE", setting_description="SETTING"
    )
    assert "SIDE" in attack and "SETTING" in attack
    assert "SETTING" in prompts.HONEST_SYSTEM_PROMPT.format(setting_description="SETTING")
    prompts.TRUSTED_MONITOR_PROMPT.format(task_description="T", tool_calls="C")


def test_monitor_reply_format_is_the_one_control_arena_parses():
    """A reply in the format the monitor prompt asks for must parse to a real score."""
    from control_arena.monitor import MonitorScoreRange, extract_monitor_response
    from inspect_ai.model import ChatMessageAssistant

    from example_1_control_arena_apps import prompts

    assert "<score>X</score>" in prompts.TRUSTED_MONITOR_PROMPT
    reply = ChatMessageAssistant(content="<reasoning>odd branch</reasoning>\n<score>7</score>")
    response = extract_monitor_response(message=reply, score_range=MonitorScoreRange())
    assert response.score_parsed is True
    assert response.suspicion_score == 0.7


def test_tasks_carry_threshold_and_explicit_models():
    """build_tasks → one task per (threshold × mode), threshold in task metadata."""
    from ac_components.eval import ModelRoles, build_config
    from control_arena import EvalMode
    from control_arena.eval import get_control_task

    from example_1_control_arena_apps.build import (
        build_dtt_protocols,
        build_monitor,
        build_policies,
    )

    untrusted, trusted = build_policies()
    (protocol,) = build_dtt_protocols(
        thresholds=[0.3], untrusted=untrusted, trusted=trusted, monitor=build_monitor(num_samples=2)
    )
    config = build_config(ModelRoles(untrusted="mockllm/model", trusted="mockllm/model"), limit=1)
    assert config.eval_args()["limit"] == 1

    # A stand-in for AppsSetting's dataset: building the real one downloads from HuggingFace.
    from control_arena.settings.apps.apps_setting import AppsSetting
    from inspect_ai.dataset import Sample

    task = get_control_task(
        AppsSetting(), protocol, EvalMode.ATTACK, eval_config=config, dataset=[Sample(input="x")]
    )
    assert task.metadata["micro_protocol"]["type"] == "defer_to_trusted"
    assert task.metadata["micro_protocol"]["defer_threshold"] == 0.3
    assert task.name.startswith("apps_defer_to_trusted_attack_")
