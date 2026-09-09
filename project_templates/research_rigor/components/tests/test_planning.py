"""
Tests for diversity-forced planning.

Run:  uv run pytest tests/test_planning.py -v
"""


import pytest

from research_rigor import planning as pl

FEATURES = ["mechanism", "method", "failure_mode"]


def _p(pid, mech, meth, fm):
    return pl.Proposal(pid, pid, {"mechanism": mech, "method": meth, "failure_mode": fm})


def _diverse():
    return [
        _p("A", "sae_ablation", "causal_patching", "length_confound"),
        _p("B", "probing", "linear_probe", "spurious_correlation"),
        _p("C", "activation_steering", "steering_vector", "off_distribution"),
    ]


def _homogeneous():
    # Three near-variants of the same idea, same failure mode.
    return [
        _p("A", "sae_ablation", "causal_patching", "length_confound"),
        _p("B", "sae_ablation", "causal_patching", "length_confound"),
        _p("C", "sae_ablation", "attribution_patching", "length_confound"),
    ]


def test_diverse_set_has_high_entropy():
    d = pl.diversity_report(_diverse(), FEATURES)
    assert d.overall > 0.9 and not d.insufficient


def test_homogeneous_set_is_flagged_insufficient():
    d = pl.diversity_report(_homogeneous(), FEATURES)
    assert d.insufficient
    assert d.per_feature_entropy["mechanism"] < 0.5   # mostly the same mechanism
    assert d.per_feature_entropy["failure_mode"] == 0.0  # identical failure mode


def test_correlated_cluster_detection():
    d = pl.diversity_report(_homogeneous(), FEATURES)
    # All three share failure_mode -> one correlated cluster of all three.
    assert d.correlated_clusters == [["A", "B", "C"]]


def test_single_proposal_is_insufficient():
    d = pl.diversity_report([_p("A", "x", "y", "z")], FEATURES)
    assert d.insufficient and d.overall == 0.0


def test_missing_feature_fails_loudly():
    bad = pl.Proposal("A", "A", {"mechanism": "x"})  # missing method/failure_mode
    try:
        pl.diversity_report([bad, _p("B", "p", "q", "r")], FEATURES)
        assert False, "should fail on a missing feature"
    except AssertionError as e:
        assert "missing feature" in str(e)


# --- rubric scoring ----------------------------------------------------------

def _rubric(approved=True):
    return pl.Rubric([pl.Criterion("novelty", 2.0), pl.Criterion("feasibility", 1.0)],
                     approved_by_pi=approved)


def test_rubric_must_be_pi_approved():
    try:
        pl.score_proposals(_rubric(approved=False), _diverse(), {})
        assert False, "must refuse to score on an unapproved rubric"
    except AssertionError as e:
        assert "PI-approved" in str(e)


def test_scoring_ranks_by_weighted_total():
    props = _diverse()
    scores = {"A": {"novelty": 5, "feasibility": 1},   # 2*5 + 1*1 = 11
              "B": {"novelty": 1, "feasibility": 5},   # 2*1 + 1*5 = 7
              "C": {"novelty": 3, "feasibility": 3}}   # 2*3 + 1*3 = 9
    ranked = pl.score_proposals(_rubric(), props, scores)
    assert [r.proposal_id for r in ranked] == ["A", "C", "B"]
    assert ranked[0].score == 11


# --- the gate ----------------------------------------------------------------

def test_gate_blocks_homogeneous_before_selection():
    d = pl.diversity_report(_homogeneous(), FEATURES)
    v = pl.plan_gate(d, pi_selection=None)
    assert v.verdict == "insufficient_diversity"


def test_gate_awaits_pi_when_diverse_and_unselected():
    d = pl.diversity_report(_diverse(), FEATURES)
    v = pl.plan_gate(d, pi_selection=None)
    assert v.verdict == "awaiting_pi_selection"


def test_gate_refuses_agent_selection_without_authorization():
    d = pl.diversity_report(_diverse(), FEATURES)
    with pytest.raises(AssertionError, match="requires researcher authorization"):
        pl.plan_gate(d, pi_selection=["A"], selector="agent")


def test_gate_accepts_pi_selection():
    d = pl.diversity_report(_diverse(), FEATURES)
    v = pl.plan_gate(d, pi_selection=["A", "C"], selector="pi")
    assert v.verdict == "selected" and v.selected == ["A", "C"]
    assert not v.warnings  # A and C are in different failure-mode clusters


def test_gate_warns_on_correlated_selection():
    # A diverse-enough set, but the PI picks two that share a failure mode.
    props = [
        _p("A", "sae_ablation", "causal_patching", "length_confound"),
        _p("B", "probing", "linear_probe", "length_confound"),   # same failure mode as A
        _p("C", "steering", "steering_vector", "off_distribution"),
        _p("D", "attribution", "attr_patching", "gradient_noise"),
    ]
    d = pl.diversity_report(props, FEATURES)
    assert not d.insufficient
    v = pl.plan_gate(d, pi_selection=["A", "B"], selector="pi")
    assert v.verdict == "selected"
    assert any("correlated" in w for w in v.warnings)


def test_researcher_can_delegate_selection_without_changing_default():
    d = pl.diversity_report(_diverse(), FEATURES)
    assert pl.plan_gate(d, pi_selection=["A"], selector="agent",
                        agent_selection_authorized=True).verdict == "selected"
