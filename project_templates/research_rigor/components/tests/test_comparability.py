"""
Tests for comparability: one shared axis per paper, and coordinated arms.

Run:  uv run pytest tests/test_comparability.py -v
"""

import pytest

from research_rigor import comparability as cp

OWN = {"base_model": "qwen2.5-7b", "trainer": "verl 0.4", "reward": "process",
       "training_data": "gsm8k-train", "eval": "aime24, n=4"}
PAPER = {"base_model": "qwen2.5-7b", "trainer": "openrlhf fork", "reward": "outcome",
         "training_data": None, "eval": "aime24, n=4"}


def test_configs_split_into_shared_differing_and_unreported():
    c = cp.compare_configs(OWN, PAPER)
    assert c.shared == ["base_model", "eval"]
    assert c.differs == ["trainer", "reward"]
    assert c.unreported == ["training_data"]


def test_a_factor_left_out_fails_loudly_a_blank_is_written_as_none():
    paper = {k: v for k, v in PAPER.items() if k != "training_data"}
    with pytest.raises(AssertionError, match="training_data"):
        cp.compare_configs(OWN, paper)


def test_comparison_with_no_declared_axis_is_flagged():
    assert cp.shared_axis_flags(cp.compare_configs(OWN, PAPER), [])


def test_declared_axis_that_is_shared_raises_no_flag():
    assert cp.shared_axis_flags(cp.compare_configs(OWN, PAPER), ["base_model"]) == []


def test_declared_axis_that_differs_or_was_never_reported_is_flagged():
    flags = cp.shared_axis_flags(cp.compare_configs(OWN, PAPER), ["reward", "training_data"])
    assert len(flags) == 2 and "reward" in flags[0] and "training_data" in flags[1]


def test_declaring_an_axis_that_is_not_a_factor_fails_loudly():
    with pytest.raises(AssertionError, match="not a factor"):
        cp.shared_axis_flags(cp.compare_configs(OWN, PAPER), ["vibes"])


# --- several agents, one measurement ----------------------------------------

def _arm(name, **over):
    kw = dict(judge="claude-haiku-5-5", judge_prompt_hash="sha256:aaa",
              samples_per_item=1, shared_files_hash="sha256:bbb")
    kw.update(over)
    return cp.ArmMeasurement(name, **kw)


def test_arm_on_the_shared_measurement_raises_no_flag():
    assert cp.arm_flags(_arm("coordinator"), [_arm("a"), _arm("b")]) == []


def test_arm_that_added_a_sample_or_changed_the_judge_prompt_is_flagged():
    flags = cp.arm_flags(_arm("coordinator"),
                         [_arm("a"), _arm("b", samples_per_item=2),
                          _arm("c", judge_prompt_hash="sha256:ccc")])
    assert len(flags) == 2
    assert "'b'" in flags[0] and "samples_per_item" in flags[0]
    assert "'c'" in flags[1] and "judge_prompt_hash" in flags[1]


def test_unticked_checklist_rows_are_reported_as_not_examined():
    out = cp.not_examined({"a": list(cp.ARM_CHECKLIST), "b": ["raw_outputs_sampled"]})
    assert "a" not in out
    assert out["b"] == [r for r in cp.ARM_CHECKLIST if r != "raw_outputs_sampled"]


def test_unknown_checklist_row_fails_loudly():
    with pytest.raises(AssertionError, match="unknown checklist rows"):
        cp.not_examined({"a": ["looked_fine"]})
