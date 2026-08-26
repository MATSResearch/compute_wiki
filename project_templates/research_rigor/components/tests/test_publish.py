"""
Tests for code publication & reproducibility (stage 9).

Run:  uv run pytest tests/test_publish.py -v
"""


import pytest

from research_rigor import publish as pb
from research_rigor.verify import Verifier


def _release(**over):
    r = {
        "task_identity": "SAE feature 4021 ablation on anthropic_hh",
        "harness": "prime-agent 0.4.1 @ sha256:abc123",
        "inference_settings": "temperature=0, max_tokens=4096",
        "cost": "USD 41.20",
        "failure_breakdown": "3/50 runs OOM'd; excluded and reported",
        "model_ids": ["claude-opus-5"],
        "run_dates": "2026-08-20..2026-08-24",
        "reasoning_mode": "high",
        "uncertainty": "95% CI over 5 seeds",
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
    return pb.publish_gate(release or _release(), checks or pb.default_release_checks(), **kw)


# --- disclosure scoring -----------------------------------------------------

def test_full_release_scores_one():
    assert pb.disclosure_report(_release()).score == 1.0


def test_placeholders_do_not_count_as_disclosure():
    r = pb.disclosure_report(_release(cost="TBD", harness="unknown", model_ids=[]))
    assert set(r.missing) == {"cost", "harness", "model_ids"}


def test_a_score_alone_is_gameable_so_four_fields_are_required():
    """Dropping exactly cost+harness clears 0.66 on a nine-field card — the
    field's own failure, scored as a pass. Required fields close that hole."""
    r = pb.disclosure_report(_release(cost=None, harness=None))
    assert r.score >= r.threshold
    assert r.missing_required == ["cost", "harness"]
    assert not r.sufficient


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
