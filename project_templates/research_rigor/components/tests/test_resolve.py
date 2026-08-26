"""
Tests for hypothesis resolution & follow-ups (stage 7).

Run:  uv run pytest tests/test_resolve.py -v
"""


import pytest

from research_rigor import resolve as rs

FROZEN = ["H1", "H2"]
TESTED = {"model": "llama-3-8b", "dataset": "anthropic_hh", "seeds": [0, 1, 2]}


def _res(hid="H1", verdict="supported", **kw):
    kw.setdefault("rationale", "ablation cut the gap 61%, above the pre-committed 50% threshold")
    kw.setdefault("claimed_scope", {"model": "llama-3-8b", "dataset": "anthropic_hh"})
    return rs.Resolution(hid, verdict, **kw)


def _gate(resolutions, open_anomalies=(), disconfirming=()):
    return rs.resolve_gate(frozen_hypothesis_ids=FROZEN, resolutions=list(resolutions),
                           tested_scope=TESTED, open_anomalies=list(open_anomalies),
                           disconfirming_findings=list(disconfirming))


def _both(**kw):
    return [_res("H1", **kw), _res("H2", "inconclusive",
                                   rationale="fell in the pre-committed inconclusive band")]


# --- every frozen hypothesis gets a verdict ---------------------------------

def test_dropping_a_hypothesis_is_blocked():
    v = _gate([_res("H1")])
    assert v.verdict == "blocked_incomplete"
    assert "H2" in v.reasons[0]


def test_resolving_a_hypothesis_that_was_never_frozen_is_blocked():
    v = _gate(_both() + [_res("H7", "supported")])
    assert v.verdict == "blocked_incomplete"


def test_two_verdicts_for_one_hypothesis_fail_loudly():
    with pytest.raises(AssertionError, match="two resolutions"):
        _gate([_res("H1"), _res("H1", "refuted"), _res("H2", "inconclusive")])


def test_inconclusive_is_a_legitimate_result_not_a_block():
    v = _gate([_res("H1", "inconclusive"), _res("H2", "inconclusive")])
    assert v.verdict == "resolved"
    assert any("legitimate result" in w for w in v.warnings)


# --- authorship -------------------------------------------------------------

def test_agent_cannot_own_a_verdict():
    with pytest.raises(AssertionError, match="Human-held"):
        _gate([_res("H1", decided_by="agent"), _res("H2", "inconclusive")])


def test_verdict_without_a_rationale_fails_loudly():
    with pytest.raises(AssertionError, match="not a resolution"):
        _res("H1", rationale="  ")


def test_unknown_verdict_fails_loudly():
    with pytest.raises(AssertionError, match="bad verdict"):
        _res("H1", "probably_true")


# --- open anomalies and disconfirming evidence ------------------------------

def test_open_anomaly_blocks_supported():
    v = _gate(_both(), open_anomalies=["A1"])
    assert v.verdict == "blocked_open_anomaly"


def test_open_anomaly_does_not_block_an_inconclusive_run():
    v = _gate([_res("H1", "inconclusive"), _res("H2", "inconclusive")], open_anomalies=["A1"])
    assert v.verdict == "resolved"


def test_unaddressed_disconfirming_evidence_blocks():
    v = _gate(_both(), disconfirming=["F3"])
    assert v.verdict == "blocked_unaddressed_disconfirming"
    assert "F3" in v.reasons[0]


def test_naming_the_disconfirming_finding_clears_it():
    v = _gate([_res("H1", addresses_disconfirming=["F3"]),
               _res("H2", "inconclusive", rationale="inconclusive band")],
              disconfirming=["F3"])
    assert v.verdict == "resolved"


# --- the scope guard --------------------------------------------------------

def test_claiming_an_untested_model_is_overgeneralization():
    v = _gate([_res("H1", claimed_scope={"model": ["llama-3-8b", "gpt-4"]}),
               _res("H2", "inconclusive", rationale="band")])
    assert v.verdict == "blocked_overgeneralized"
    assert "gpt-4" in v.reasons[0]


def test_claiming_a_dimension_the_run_never_recorded_is_blocked():
    v = _gate([_res("H1", claimed_scope={"language": "all languages"}),
               _res("H2", "inconclusive", rationale="band")])
    assert v.verdict == "blocked_overgeneralized"
    assert "untested scope" in v.reasons[0]


def test_a_narrower_claim_than_what_was_tested_is_fine():
    assert rs.scope_violations({"seeds": [0]}, TESTED) == []


def test_scope_guard_ignores_an_inconclusive_verdict():
    v = _gate([_res("H1", "inconclusive", claimed_scope={"model": "gpt-4"},
                    rationale="band"), _res("H2", "inconclusive", rationale="band")])
    assert v.verdict == "resolved"


# --- follow-ups are candidates, never decisions -----------------------------

def test_followup_must_trace_to_real_evidence():
    with pytest.raises(AssertionError, match="not a finding or anomaly"):
        rs.handoff_followups([rs.FollowUp("U1", "does it hold at 70B?", "F9")],
                             known_ids=["F1", "A1"])


def test_followups_hand_off_unselected_and_routed_to_plan():
    out = rs.handoff_followups(
        [rs.FollowUp("U1", "does it hold at 70B?", "F1", lesson="effect was layer-late")],
        known_ids=["F1", "A1"])
    assert out[0]["selected"] is False
    assert "/plan" in out[0]["route"]
    assert out[0]["lesson"] == "effect was layer-late"


def test_clean_run_resolves():
    assert _gate(_both()).verdict == "resolved"
