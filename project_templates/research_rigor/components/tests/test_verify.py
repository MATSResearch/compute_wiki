"""
Tests for the delegated-but-validated implementation harness.

Run:  uv run pytest tests/test_verify.py -v
"""

import pytest

from research_rigor import run_dir as run_dir
from research_rigor import verify as vf


def _mk(tmp_path):
    return run_dir.RunDir.create(
        tmp_path, "run_20260707_120000_impl", acceptance="every hard verifier passes",
        models=[{"id": "claude-opus-4-8", "role": "implementation"}],
        harness={"tool": "claude-code"}, code_repo=tmp_path,
    )


# --- rules-as-code -----------------------------------------------------------

def test_finite_and_range_and_reproduces():
    r = {"acc": 0.87, "loss": 0.3}
    assert vf.run_validation([vf.expect_finite("acc")], r).verifiers_passed
    assert vf.run_validation([vf.expect_range("acc", 0, 1)], r).verifiers_passed
    assert not vf.run_validation([vf.expect_range("acc", 0.9, 1.0)], r).verifiers_passed
    assert vf.run_validation([vf.reproduces("acc", 0.86, rel_tol=0.05)], r).verifiers_passed
    assert not vf.run_validation([vf.reproduces("acc", 0.5, rel_tol=0.05)], r).verifiers_passed


def test_finite_catches_nan():
    r = {"grad_norm": float("nan")}
    report = vf.run_validation([vf.expect_finite("grad_norm")], r)
    assert not report.verifiers_passed
    assert "non-finite" in report.hard_failures[0].message


def test_not_constant_catches_degenerate_predictions():
    good = vf.run_validation([vf.not_constant("preds")], {"preds": [0, 1, 1, 0]})
    bad = vf.run_validation([vf.not_constant("preds")], {"preds": [1, 1, 1, 1]})
    assert good.verifiers_passed and not bad.verifiers_passed
    assert "degenerate" in bad.hard_failures[0].message


def test_missing_key_fails_loudly_not_silently():
    report = vf.run_validation([vf.expect_range("missing", 0, 1)], {"acc": 0.9})
    assert not report.verifiers_passed  # a crashing verifier is a failure, not a skip
    assert "no key" in report.hard_failures[0].message.lower()


def test_expect_shape():
    assert vf.run_validation([vf.expect_shape("m", (2, 3))], {"m": [[1, 2, 3], [4, 5, 6]]}).verifiers_passed
    assert not vf.run_validation([vf.expect_shape("m", (2, 2))], {"m": [[1, 2, 3], [4, 5, 6]]}).verifiers_passed


# --- units scored against units launched -------------------------------------

def _counts(**conditions):
    base = {"honest": {"launched": 50, "scored": 50, "errored": 0, "usefulness": 0.81},
            "attack": {"launched": 50, "scored": 50, "errored": 0, "usefulness": 0.64}}
    for name, over in conditions.items():
        base[name] = {**base[name], **over}
    return {"conditions": base}


def test_every_unit_accounted_for_and_run_passes_with_nothing_reported():
    report = vf.run_validation(vf.expect_counts(), _counts())
    assert report.verdict == "verifiers_passed_pending_human"
    assert not report.soft_failures


@pytest.mark.parametrize("missing", ["launched", "scored", "errored"])
def test_a_condition_missing_a_count_fails(missing):
    result = _counts()
    del result["conditions"]["attack"][missing]
    report = vf.run_validation(vf.expect_counts(), result)
    assert report.verdict == "verifiers_failed"
    assert [r.name for r in report.hard_failures] == ["counts:conditions"]


def test_counts_that_do_not_add_up_fail():
    # 3 units vanished: neither scored nor recorded as did-not-run
    report = vf.run_validation(vf.expect_counts(), _counts(attack={"scored": 47}))
    assert report.verdict == "verifiers_failed"
    assert [r.name for r in report.hard_failures] == ["counts:conditions"]


def test_units_that_did_not_run_are_reported_not_failed():
    report = vf.run_validation(vf.expect_counts(),
                               _counts(attack={"scored": 47, "errored": 3}))
    assert report.verdict == "verifiers_passed_pending_human"
    assert [r.name for r in report.soft_failures] == ["did_not_run:conditions"]
    assert "attack" in report.soft_failures[0].message


def test_adding_the_check_without_recording_counts_fails():
    """Adding expect_counts declares countable units; forgetting them must not pass unchecked."""
    report = vf.run_validation(vf.expect_counts(), {"acc": 0.9})
    assert report.verdict != "verifiers_passed_pending_human"
    assert [f for f in report.hard_failures if f.name == "counts:conditions"]


@pytest.mark.parametrize("declared", [{}, [50, 50, 0]])
def test_declared_units_that_are_not_a_mapping_of_conditions_fail(declared):
    report = vf.run_validation(vf.expect_counts(), {"conditions": declared})
    assert report.verdict == "verifiers_failed"


# --- the core rule: execution success is not acceptance ----------------------

def test_execution_ok_is_not_sufficient():
    # Code "ran" but the result is out of range: verdict must NOT be acceptance.
    report = vf.run_validation([vf.expect_range("acc", 0.0, 1.0)], {"acc": 1.7}, execution_ok=True)
    assert report.execution_ok is True
    assert report.verdict == "verifiers_failed"
    assert report.requires_human_gate is True


def test_passing_verdict_still_requires_human():
    report = vf.run_validation([vf.expect_range("acc", 0, 1)], {"acc": 0.9}, execution_ok=True)
    assert report.verdict == "verifiers_passed_pending_human"
    assert report.requires_human_gate is True  # never auto-accept


def test_execution_failure_short_circuits():
    report = vf.run_validation([vf.expect_range("acc", 0, 1)], {}, execution_ok=False)
    assert report.verdict == "execution_failed"
    assert report.results == []


# --- independence: hard verifiers must be PI-owned ---------------------------

def test_agent_authored_hard_verifier_is_rejected():
    sneaky = vf.expect_range("acc", 0, 1, severity="hard", author="agent")
    try:
        vf.run_validation([sneaky], {"acc": 0.9})
        assert False, "a hard verifier authored by the agent must be refused"
    except AssertionError as e:
        assert "PI-owned" in str(e) or "independent" in str(e)


def test_agent_may_add_soft_verifiers():
    soft = vf.expect_range("acc", 0.95, 1.0, severity="soft", author="agent")
    report = vf.run_validation([soft], {"acc": 0.9})
    assert report.verifiers_passed  # soft failure doesn't block
    assert report.soft_failures and report.soft_failures[0].severity == "soft"


# --- the driver --------------------------------------------------------------

def test_driver_retries_with_feedback_then_passes(tmp_path):
    rd = _mk(tmp_path)
    verifiers = [vf.expect_range("acc", 0.8, 1.0)]
    calls = {"n": 0}

    def attempt_fn(feedback):
        calls["n"] += 1
        if calls["n"] == 1:
            # first attempt: out of range, and it should receive no feedback yet
            assert feedback is None
            return vf.Attempt(result={"acc": 0.4}, reasoning="tried lr=1.0, diverged")
        # second attempt: got structured feedback about the failing range check
        assert feedback and "range:acc" in feedback
        return vf.Attempt(result={"acc": 0.9}, reasoning="lowered lr to 0.1, converged")

    attempt, report = vf.delegated_but_validated(
        attempt_fn=attempt_fn, verifiers=verifiers, rd=rd, max_attempts=3)
    assert calls["n"] == 2
    assert report.verdict == "verifiers_passed_pending_human"
    # CoT preserved on disk + logged to provenance
    assert (rd.path / "code" / "attempts" / "attempt_1.md").exists()
    prov = rd.read_log(rd.provenance_path)
    assert len(prov) == 2 and prov[0]["event"] == "model_invocation"


def test_driver_refuses_attempt_without_reasoning(tmp_path):
    rd = _mk(tmp_path)
    def attempt_fn(feedback):
        return vf.Attempt(result={"acc": 0.9}, reasoning="")  # no scratchpad
    try:
        vf.delegated_but_validated(attempt_fn=attempt_fn, verifiers=[], rd=rd)
        assert False, "must refuse an attempt with no preserved reasoning"
    except AssertionError as e:
        assert "reasoning" in str(e).lower() or "chain-of-thought" in str(e).lower()


def test_driver_exhausts_without_accepting(tmp_path):
    rd = _mk(tmp_path)
    verifiers = [vf.expect_range("acc", 0.99, 1.0)]  # never satisfied

    def attempt_fn(feedback):
        return vf.Attempt(result={"acc": 0.5}, reasoning="stuck at 0.5")

    attempt, report = vf.delegated_but_validated(
        attempt_fn=attempt_fn, verifiers=verifiers, rd=rd, max_attempts=2)
    assert report.verdict == "verifiers_failed"      # never silently accepted
    assert report.requires_human_gate is True
    assert len(rd.read_log(rd.provenance_path)) == 2  # both attempts logged
