"""Tests for ul_components.

The analysis half (splits, evaluate, relearn, report) is pure Python and always
runs. The loss tests skip cleanly if the torch extra isn't installed.

    uv run pytest
"""

from __future__ import annotations

import pytest

from ul_components import evaluate, relearn, report, splits


# ---------- splits ----------


def _records(n_keys: int = 10, per_key: int = 3) -> list[dict]:
    return [
        {"author": f"a{i}", "text": f"fact {i}.{j}"}
        for i in range(n_keys)
        for j in range(per_key)
    ]


def test_split_partitions_by_key_not_by_row():
    recs = _records()
    split = splits.make_split(recs, key_fn=lambda r: r["author"], forget_fraction=0.2)
    assert split.forget_keys & split.retain_keys == set()
    assert len(split.forget) + len(split.retain) == len(recs)
    # every row of a forgotten author is on the forget side
    for r in recs:
        side = split.forget if r["author"] in split.forget_keys else split.retain
        assert r in side


def test_split_is_deterministic_given_seed():
    recs = _records()
    a = splits.make_split(recs, key_fn=lambda r: r["author"], seed=7)
    b = splits.make_split(recs, key_fn=lambda r: r["author"], seed=7)
    assert a.forget_keys == b.forget_keys


def test_seed_actually_changes_the_split():
    # Not "seed 7 differs from seed 8" — with a small forget set two seeds can
    # legitimately pick the same keys. The claim is that the seed matters at all.
    recs = _records(n_keys=10)
    seen = {
        frozenset(
            splits.make_split(
                recs, key_fn=lambda r: r["author"], forget_fraction=0.3, seed=s
            ).forget_keys
        )
        for s in range(10)
    }
    assert len(seen) > 1


def test_split_never_forgets_everything():
    recs = _records(n_keys=3, per_key=1)
    split = splits.make_split(recs, key_fn=lambda r: r["author"], forget_fraction=0.99)
    assert split.retain_keys


def test_split_rejects_bad_fraction():
    with pytest.raises(ValueError):
        splits.make_split(_records(), key_fn=lambda r: r["author"], forget_fraction=0.0)
    with pytest.raises(ValueError):
        splits.make_split(_records(), key_fn=lambda r: r["author"], forget_fraction=1.0)


def test_assert_no_leakage_catches_a_shared_key():
    recs = _records(n_keys=4)
    split = splits.make_split(recs, key_fn=lambda r: r["author"], forget_fraction=0.25)
    leaked = dict(split.forget[0])  # same author, now also in retain
    split.retain.append(leaked)
    with pytest.raises(ValueError, match="BOTH"):
        splits.assert_no_leakage(split, key_fn=lambda r: r["author"])


def test_substring_leakage_finds_a_copied_passage():
    forget = ["The Aurelian Codex was written in 1823 by an unknown scribe in Lyon."]
    retain = ["Notes: The Aurelian Codex was written in 1823 by an unknown scribe in Lyon, per the catalogue."]
    assert splits.substring_leakage(forget, retain)
    assert not splits.substring_leakage(forget, ["An unrelated sentence entirely."])


# ---------- evaluate ----------


def test_refusal_and_incapacity_are_not_the_same_event():
    assert evaluate.classify("I can't help with that.", ["paris"]) == evaluate.REFUSED
    assert evaluate.classify("I have no idea.", ["paris"]) == evaluate.INCAPABLE
    assert evaluate.classify("It is Paris.", ["paris"]) == evaluate.CORRECT


def test_answer_beats_hedge():
    # information got out, so it counts as correct despite the refusal-ish opener
    assert evaluate.classify("I'm sorry, but the answer is Paris.", ["paris"]) == evaluate.CORRECT


def test_forget_score_rates_and_warning():
    score = evaluate.score_forget_set(
        ["It is Paris.", "I won't answer that.", "I cannot provide that.", "No idea."],
        [["paris"], ["rome"], ["berlin"], ["madrid"]],
    )
    assert score.capability == 0.25
    assert score.refusal_rate == 0.5
    assert score.incapacity_rate == 0.25
    assert "refusal" in score.warn_if_refusal_dominated().lower()


def test_score_requires_paired_inputs():
    with pytest.raises(ValueError):
        evaluate.score_forget_set(["a", "b"], [["a"]])


def test_mcq_gap_warning():
    assert evaluate.mcq_gap_warning(0.10, 0.60) is not None
    assert evaluate.mcq_gap_warning(0.55, 0.60) is None


# ---------- relearn + report ----------


def _curve(recovery_by_step: dict[int, float], baseline: float = 0.8) -> relearn.RelearnCurve:
    calls: list[int] = []

    def reset_fn() -> dict:
        return {}

    def train_fn(model: dict, n: int) -> dict:
        calls.append(n)
        model["n"] = n
        return model

    def eval_fn(model: dict) -> float:
        return recovery_by_step[model.get("n", 0)]

    curve = relearn.relearn_sweep(
        step_counts=sorted(recovery_by_step),
        reset_fn=reset_fn,
        train_fn=train_fn,
        eval_fn=eval_fn,
        baseline=baseline,
        adjacent_data_description="adjacent corpus",
    )
    curve.calls = calls  # type: ignore[attr-defined]
    return curve


def test_sweep_requires_a_zero_point():
    with pytest.raises(ValueError, match="must include 0"):
        relearn.relearn_sweep(
            step_counts=[10, 50],
            reset_fn=dict,
            train_fn=lambda m, n: m,
            eval_fn=lambda m: 0.0,
            baseline=1.0,
            adjacent_data_description="x",
        )


def test_curve_requires_describing_the_relearning_data():
    with pytest.raises(ValueError, match="describe the relearning data"):
        relearn.RelearnCurve(baseline=1.0, adjacent_data_description="")


def test_sweep_resets_the_model_for_every_step_count():
    curve = _curve({0: 0.05, 10: 0.2, 50: 0.5})
    # each non-zero step count trained exactly once, from a fresh reset
    assert curve.calls == [10, 50]  # type: ignore[attr-defined]


def test_fast_recovery_reads_as_suppression():
    curve = _curve({0: 0.05, 10: 0.30, 50: 0.60, 100: 0.75})
    v = report.verdict(curve)
    assert v.label == report.SUPPRESSION_NOT_REMOVAL
    assert v.steps_to_half == 50


def test_no_recovery_is_never_reported_as_removed():
    curve = _curve({0: 0.05, 10: 0.05, 50: 0.06, 100: 0.07})
    v = report.verdict(curve)
    assert v.label == report.NO_RECOVERY_UNDER_THIS_ATTACK
    assert "not evidence of it" in v.note
    assert "REMOVED" not in v.label


def test_partial_recovery_bucket():
    curve = _curve({0: 0.05, 10: 0.10, 50: 0.20, 100: 0.30})
    assert report.verdict(curve).label == report.PARTIAL_RECOVERY


def test_recovery_fraction_is_not_clamped():
    curve = _curve({0: 0.05, 10: 0.95})  # overshoots the 0.8 baseline
    assert report.recovery_fraction(curve, 0.95) > 1.0


def test_ineffective_unlearning_raises_rather_than_dividing_by_zero():
    curve = _curve({0: 0.8, 10: 0.8}, baseline=0.8)
    with pytest.raises(ValueError, match="unlearning step did nothing"):
        report.verdict(curve)


def test_summarize_mentions_the_relearning_data():
    curve = _curve({0: 0.05, 10: 0.3, 100: 0.75})
    text = report.summarize(curve)
    assert "adjacent corpus" in text
    assert "verdict:" in text


# ---------- losses (torch extra) ----------


def test_losses_shapes_and_bounds():
    torch = pytest.importorskip("torch")
    from ul_components import losses

    b, t, v = 3, 7, 13
    labels = torch.randint(0, v, (b, t))
    labels[:, :2] = -100
    logits = torch.randn(b, t, v, requires_grad=True)
    ref = torch.randn(b, t, v)

    ga = losses.gradient_ascent_loss(logits, labels)
    assert ga.ndim == 0 and ga.item() < 0  # negated NLL

    npo = losses.npo_loss(logits, ref, labels, beta=0.1)
    assert npo.ndim == 0 and npo.item() > 0  # NPO is positive by construction
    npo.backward()
    assert logits.grad is not None

    gd = losses.grad_diff_loss(logits.detach(), labels, torch.randn(b, t, v), labels)
    assert gd.ndim == 0


def test_npo_is_zero_when_policy_matches_reference_scaled():
    torch = pytest.importorskip("torch")
    from ul_components import losses

    b, t, v = 2, 5, 9
    labels = torch.randint(0, v, (b, t))
    logits = torch.randn(b, t, v)
    # policy == reference  =>  log ratio 0  =>  loss = (2/beta) * log 2
    beta = 0.5
    expected = (2.0 / beta) * torch.log(torch.tensor(2.0))
    got = losses.npo_loss(logits, logits.clone(), labels, beta=beta)
    assert torch.allclose(got, expected, atol=1e-5)


def test_sequence_logprob_rejects_mismatched_shapes():
    torch = pytest.importorskip("torch")
    from ul_components import losses

    with pytest.raises(ValueError):
        losses.sequence_logprob(torch.randn(2, 5, 9), torch.randint(0, 9, (2, 4)))
