"""
Tests for the delegated-but-validated implementation harness.

Run:  uv run pytest tests/test_verify.py -v
"""


from research_rigor import run_dir as run_dir
from research_rigor import verify as vf


def _mk(tmp_path):
    return run_dir.RunDir.create(
        tmp_path, "run_20260707_120000_impl",
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
