"""Tests that don't need a model API.

These exercise the *construction* and *pure-logic* pieces — the answer matcher,
dataset building, paraphrase expansion, task assembly — but not the actual eval
(which needs an API key and costs money). Run with `uv run pytest`.
"""

from __future__ import annotations

import pytest

inspect_ai = pytest.importorskip("inspect_ai")


# ---------- answer matcher (pure) ----------


@pytest.mark.parametrize(
    "completion,target,expected",
    [
        ("The capital of France is Paris.", "Paris", True),
        ("It is 56.", "56", True),
        ("There are seven continents.", "7|seven", True),
        ("The answer is carbon dioxide (CO2).", "carbon dioxide|CO2", True),
        ("I think it's London.", "Paris", False),
        ("", "Paris", False),
        # alias appearing only inside an apology should still match (toy matcher
        # limitation we document): "you're right, it's not Paris" matches "Paris".
        ("You're right, it's not Paris after all.", "Paris", True),
    ],
)
def test_answer_matches(completion, target, expected):
    from example_1_sycophancy_eval.build import answer_matches

    assert answer_matches(completion, target) is expected


# ---------- dataset construction ----------


def test_build_dataset_no_paraphrases():
    from example_1_sycophancy_eval.build import build_dataset
    from example_1_sycophancy_eval.data import TOY_FACTS

    ds = build_dataset()
    assert len(ds) == len(TOY_FACTS)
    assert ds[0].metadata["category"]  # category carried through


def test_build_dataset_with_paraphrases_multiplies():
    from example_1_sycophancy_eval.build import build_dataset
    from example_1_sycophancy_eval.data import TOY_FACTS

    ds = build_dataset(paraphrases=["p0", "p1", "p2"])
    assert len(ds) == len(TOY_FACTS) * 3
    assert {s.metadata["paraphrase_idx"] for s in ds} == {0, 1, 2}


# ---------- task assembly ----------


def test_build_task_has_scorer_and_solver():
    from example_1_sycophancy_eval.build import build_task

    task = build_task()
    assert task.scorer is not None
    assert task.solver is not None
    assert task.name == "sycophancy"


def test_scorer_and_metric_constructible():
    # The decorated scorer + metric must instantiate without error.
    from example_1_sycophancy_eval.build import sycophancy_flip_rate, sycophancy_scorer

    assert sycophancy_scorer() is not None
    assert sycophancy_flip_rate() is not None


def test_prompts_present():
    from example_1_sycophancy_eval import prompts

    assert len(prompts.PUSHBACK_PARAPHRASES) >= 3
    assert "GRADE:" in prompts.GRADER_INSTRUCTIONS
