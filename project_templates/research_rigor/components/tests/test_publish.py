"""
Tests for code publication & reproducibility (stage `publish`).

Run:  uv run pytest tests/test_publish.py -v
"""


import pytest

from research_rigor import publish as pb
from research_rigor.resolve import Resolution
from research_rigor.verify import Verifier

FROZEN = ["H1"]
RESOLVED = [Resolution("H1", "refuted", "gap moved 4%, under the frozen 10% line")]


def _release(**over):
    r = {
        "harness": "prime-agent 0.4.1 @ sha256:abc123",
        "cost": "USD 41.20",
        "cost_per_step": {"lit_review": 3.10, "run": 31.40, "analysis": 6.70},
        "model_ids": ["claude-opus-5"],
        "run_dates": "2026-08-20..2026-08-24",
        "reasoning_mode": "high",
        "uncertainty": "95% bootstrap CI over the eval set",
        "seeds": [0, 1, 2, 3, 4],
        "environment": "uv.lock + python 3.13",
        "entrypoint": "uv run python -m src.run_ablation",
        "artifacts": {"results/ablation.json": "sha256:deadbeef"},
        "files": {"README.md": "run with uv", "src/run_ablation.py": "import torch"},
    }
    r.update(over)
    return r


def _gate(release=None, checks=None, **kw):
    kw.setdefault("pi_approved", True)
    kw.setdefault("frozen_hypothesis_ids", FROZEN)
    kw.setdefault("resolutions", RESOLVED)
    return pb.publish_gate(release or _release(), checks or pb.default_release_checks(), **kw)


# --- disclosure scoring -----------------------------------------------------

def test_full_release_scores_one():
    assert pb.disclosure_report(_release()).score == 1.0


def test_placeholders_do_not_count_as_disclosure():
    r = pb.disclosure_report(_release(cost="TBD", harness="unknown", model_ids=[]))
    assert set(r.missing) == {"cost", "harness", "model_ids"}


def test_a_score_alone_is_gameable_so_four_fields_are_required():
    """Dropping exactly cost+harness can clear a numeric bar — the field's own
    failure, scored as a pass. Required fields close that hole."""
    r = pb.disclosure_report(_release(cost=None, harness=None), threshold=0.6)
    assert r.score >= r.threshold
    assert r.missing_required == ["cost", "harness"]
    assert not r.sufficient


def test_scored_fields_are_the_ones_a_release_is_asked_to_disclose():
    """Extra keys in a release do not pad the score."""
    padded = _release(reasoning_mode=None, uncertainty=None, task_identity="x",
                      inference_settings="y", failure_breakdown="z")
    assert pb.disclosure_report(padded).score == pb.disclosure_report(
        _release(reasoning_mode=None, uncertainty=None)).score < 1.0


def test_undisclosed_optional_fields_are_noted_on_a_release_that_clears_the_bar():
    v = _gate(_release(reasoning_mode=None, cost_per_step=None))
    assert v.verdict == "ready"
    note = next(w for w in v.warnings if "not disclosed" in w)
    assert "reasoning_mode" in note and "cost_per_step" in note
    assert not _gate().warnings


def test_the_bar_is_the_classical_benchmark_level_not_the_agent_norm():
    assert pb.CLASSICAL_BENCHMARK_DISCLOSURE == 0.66


def test_class_level_model_reporting_is_not_disclosure():
    """52.5% of evaluation papers say "AI" instead of naming the model."""
    r = pb.disclosure_report(_release(model_ids=[], run_dates=None))
    assert r.missing_required == ["model_ids", "run_dates"]


# --- release checks ---------------------------------------------------------

def test_missing_entrypoint_blocks():
    v = _gate(_release(entrypoint=None))
    assert v.verdict == "blocked_failed_check"
    assert "entrypoint_declared" in v.reasons[0]


def test_unpinned_environment_blocks():
    assert _gate(_release(environment=None)).verdict == "blocked_failed_check"


def test_missing_seeds_block():
    assert _gate(_release(seeds=[])).verdict == "blocked_failed_check"


def test_unhashed_artifact_blocks():
    v = _gate(_release(artifacts={"results/ablation.json": ""}))
    assert v.verdict == "blocked_failed_check"
    assert "unhashed" in v.reasons[0]


def test_leaked_credential_blocks():
    v = _gate(_release(files={"config.py": 'KEY = "sk-abcdefghijklmnopqrstuvwx"'}))
    assert v.verdict == "blocked_failed_check"
    assert "no_secrets" in v.reasons[0]


def test_machine_local_path_blocks():
    v = _gate(_release(files={"run.sh": "python /home/nathan/projects/x/train.py"}))
    assert v.verdict == "blocked_failed_check"
    assert "no_absolute_local_paths" in v.reasons[0]


# --- rules-as-code cannot be talked out of ----------------------------------

def test_agent_cannot_disable_a_hard_check():
    v = _gate(disabled={"no_secrets": "agent"})
    assert v.verdict == "blocked_disabled_check"


def test_pi_may_disable_a_check_but_it_is_recorded_not_hidden():
    v = _gate(_release(files={"config.py": 'KEY = "sk-abcdefghijklmnopqrstuvwx"'}),
              disabled={"no_secrets": "pi"})
    assert v.verdict == "ready"
    assert any("disabled by the PI" in w for w in v.warnings)


def test_agent_authored_hard_check_fails_loudly():
    bad = Verifier("agent_rule", "", lambda r: (True, ""), severity="hard", author="agent")
    with pytest.raises(AssertionError):
        _gate(checks=pb.default_release_checks() + [bad])


def test_agent_may_add_a_soft_check_and_it_only_warns():
    soft = Verifier("has_citation", "", lambda r: (False, "no CITATION.cff"),
                    severity="soft", author="agent")
    v = _gate(checks=pb.default_release_checks() + [soft])
    assert v.verdict == "ready"
    assert any("has_citation" in w for w in v.warnings)


# --- ordering and the human gate -------------------------------------------

def test_a_broken_release_blocks_before_disclosure_is_scored():
    """A well-documented broken release is still broken."""
    v = _gate(_release(entrypoint=None, cost=None, harness=None))
    assert v.verdict == "blocked_failed_check"


def test_thin_disclosure_blocks_a_passing_release():
    v = _gate(_release(cost=None, harness=None))
    assert v.verdict == "blocked_disclosure"
    assert "REQUIRED" in v.reasons[0]


def test_publication_still_needs_the_pi():
    assert _gate(pi_approved=False).verdict == "blocked_pending_human"
    assert _gate(pi_approved=True).verdict == "ready"


# --- a verdict holds through the release ------------------------------------

def test_prediction_without_a_signed_verdict_blocks_the_release():
    v = _gate(frozen_hypothesis_ids=["H1", "H2"])
    assert v.verdict == "blocked_unsigned_verdict" and "H2" in v.reasons[0]


def test_release_with_no_registered_prediction_is_not_blocked_on_verdicts():
    assert _gate(frozen_hypothesis_ids=[], resolutions=[]).verdict == "ready"
