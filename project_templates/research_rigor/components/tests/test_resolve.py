"""
Tests for hypothesis resolution & follow-ups (stage `resolve`).

Run:  uv run pytest tests/test_resolve.py -v
"""


import pytest

from research_rigor import resolve as rs
from research_rigor.evidence import Citation
from research_rigor.run_dir import UnachievableProposal

FROZEN = ["H1", "H2"]
DIFFERENT_QUESTIONS = {"H1": "Q1", "H2": "Q2"}
FOR_H1 = [Citation("run:1", "H1", 0.8)]
TESTED = {"model": "llama-3-8b", "dataset": "anthropic_hh", "seeds": [0, 1, 2]}


def _res(hid="H1", verdict="supported", **kw):
    kw.setdefault("rationale", "ablation cut the gap 61%, above the pre-committed 50% threshold")
    kw.setdefault("claimed_scope", {"model": "llama-3-8b", "dataset": "anthropic_hh"})
    return rs.Resolution(hid, verdict, **kw)


def _gate(resolutions, open_anomalies=(), evidence=FOR_H1, question_of=DIFFERENT_QUESTIONS):
    return rs.resolve_gate(frozen_hypothesis_ids=FROZEN, question_of=question_of,
                           resolutions=list(resolutions), tested_scope=TESTED,
                           open_anomalies=list(open_anomalies), evidence=list(evidence))


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


# --- open anomalies -----------------------------------------------------------

@pytest.mark.parametrize("verdict", ["supported", "refuted"])
def test_open_anomaly_blocks_a_concluding_verdict(verdict):
    v = _gate([_res("H1", verdict), _res("H2", "inconclusive")], open_anomalies=["A1"],
              evidence=[Citation("run:1", "H1", 0.8 if verdict == "supported" else -0.8)])
    assert v.verdict == "blocked_open_anomaly"


def test_open_anomaly_does_not_block_an_inconclusive_run():
    v = _gate([_res("H1", "inconclusive"), _res("H2", "inconclusive")], open_anomalies=["A1"])
    assert v.verdict == "resolved"


# --- evidence is not the verdict: disagreement is flagged, not blocked --------

AGAINST_H1 = FOR_H1 + [Citation("run:3", "H1", -0.6)]


def test_verdict_that_agrees_with_its_evidence_raises_no_flag():
    v = _gate(_both())
    assert v.verdict == "resolved"
    assert not any("H1" in w for w in v.warnings)


def test_supported_with_something_cited_against_is_flagged_not_blocked():
    v = _gate(_both(), evidence=AGAINST_H1)
    assert v.verdict == "resolved" and len(v.resolutions) == 2
    assert any("disagrees with its own evidence" in w and "run:3" in w for w in v.warnings)


def test_supported_with_nothing_cited_is_flagged_not_blocked():
    v = _gate(_both(), evidence=[])
    assert v.verdict == "resolved"
    assert any("nothing cited" in w for w in v.warnings)


def test_evidence_cited_against_and_not_named_is_flagged_until_addressed():
    unnamed = _gate(_both(), evidence=AGAINST_H1)
    named = _gate([_res("H1", addresses_disconfirming=["run:3"]),
                   _res("H2", "inconclusive", rationale="inconclusive band")],
                  evidence=AGAINST_H1)
    assert any("not addressed by name" in w for w in unnamed.warnings)
    assert named.verdict == "resolved"
    assert not any("not addressed by name" in w for w in named.warnings)


def test_evidence_against_one_hypothesis_is_not_addressed_by_another_verdict():
    v = _gate([_res("H1"), _res("H2", "refuted", addresses_disconfirming=["run:3"],
                                claimed_scope={})],
              evidence=AGAINST_H1 + [Citation("run:4", "H2", -0.9)])
    assert any(w.startswith("H1") and "not addressed by name" in w for w in v.warnings)


def test_citation_for_an_unregistered_prediction_fails_loudly():
    with pytest.raises(AssertionError, match="not a frozen hypothesis"):
        _gate(_both(), evidence=[Citation("run:1", "H9", 0.5)])


# --- rivals still stand -------------------------------------------------------

SAME_QUESTION = {"H1": "Q1", "H2": "Q1"}


def test_supported_while_a_rival_under_the_same_question_is_unrefuted_is_flagged():
    v = _gate(_both(), question_of=SAME_QUESTION)
    assert v.verdict == "resolved"
    assert any("rivals still stand" in w and "H2" in w for w in v.warnings)


def test_supported_with_the_rival_refuted_raises_no_rivals_flag():
    v = _gate([_res("H1"), _res("H2", "refuted", claimed_scope={})], question_of=SAME_QUESTION,
              evidence=FOR_H1 + [Citation("run:4", "H2", -0.9)])
    assert not any("rivals still stand" in w for w in v.warnings)


def test_hypotheses_under_different_questions_are_not_rivals():
    assert not any("rivals still stand" in w for w in _gate(_both()).warnings)


def test_question_of_must_cover_exactly_the_frozen_hypotheses():
    with pytest.raises(AssertionError, match="question_of"):
        _gate(_both(), question_of={"H1": "Q1"})


# --- a verdict holds through writeup and publish ------------------------------

def test_missing_verdicts_lists_unsigned_predictions():
    assert rs.missing_verdicts(FROZEN, [_res("H1")]) == ["H2"]
    assert rs.missing_verdicts(FROZEN, _both()) == []
    assert rs.missing_verdicts([], []) == []


def test_an_agent_decided_verdict_is_not_a_signed_one():
    with pytest.raises(AssertionError, match="Human-held"):
        rs.missing_verdicts(FROZEN, [_res("H1", decided_by="agent")])


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


# --- a configuration is part of what you ran ---------------------------------

LORA_RANK = {"lora_rank": [1, 8, "full"]}


def _swept_flagged(v):
    return [w for w in v.warnings if "no swept axis" in w]


@pytest.mark.parametrize("verdict", ["refuted", "inconclusive"])
def test_a_negative_verdict_with_no_swept_axis_is_flagged_not_blocked(verdict):
    v = _gate([_res("H1", "supported"),
               _res("H2", verdict, claimed_scope={}, rationale="no effect at the frozen line")],
              evidence=FOR_H1 + [Citation("run:4", "H2", -0.9)])
    assert v.verdict == "resolved"
    assert len(_swept_flagged(v)) == 1 and "H2" in _swept_flagged(v)[0]


def test_a_negative_verdict_that_swept_an_axis_raises_no_flag():
    v = _gate([_res("H1", "supported"),
               _res("H2", "inconclusive", rationale="band", swept=LORA_RANK)])
    assert v.verdict == "resolved" and not _swept_flagged(v)


def test_a_supported_verdict_needs_no_sweep():
    v = _gate([_res("H1", "supported"), _res("H2", "inconclusive", rationale="band",
                                               swept=LORA_RANK)])
    assert not _swept_flagged(v)


def test_a_swept_axis_names_two_or_more_values():
    with pytest.raises(AssertionError, match="swept axis"):
        _res("H2", "refuted", swept={"lora_rank": [1]})


@pytest.mark.parametrize("rng", [(2.9,), (2.9, 1.1), "1.1-2.9"])
def test_a_sensitivity_range_is_low_then_high(rng):
    with pytest.raises(AssertionError, match="sensitivity"):
        _res("H1", sensitivity={"link_function": rng})


# --- follow-ups are candidates, never decisions -----------------------------

DONE = "ablation rerun on the 70B model with the same guard, all five subsets scored"


def test_followup_must_trace_to_real_evidence():
    with pytest.raises(AssertionError, match="not a finding or anomaly"):
        rs.handoff_followups([rs.FollowUp("U1", "does it hold at 70B?", "F9", DONE)],
                             known_ids=["F1", "A1"])


def test_followup_must_say_what_done_means():
    with pytest.raises(AssertionError, match="acceptance condition"):
        rs.handoff_followups([rs.FollowUp("U1", "does it hold at 70B?", "F1", " ")],
                             known_ids=["F1", "A1"])


def test_followups_hand_off_unselected_and_routed_to_plan():
    out = rs.handoff_followups(
        [rs.FollowUp("U1", "does it hold at 70B?", "F1", DONE, lesson="effect was layer-late")],
        known_ids=["F1", "A1"])
    assert out[0]["acceptance"] == DONE
    assert out[0]["selected"] is False
    assert "/plan" in out[0]["route"]
    assert out[0]["lesson"] == "effect was layer-late"


def _unachievable_followup():
    return rs.FollowUp("U1", "does it hold at 70B?", "F1", DONE,
                       unachievable=UnachievableProposal("70B weights are not available to us"))


def test_an_unacknowledged_unachievable_followup_stays_open_and_routed():
    out = rs.handoff_followups([_unachievable_followup()], known_ids=["F1"])
    assert out[0]["unachievable"]["decision"] is None
    assert "/plan" in out[0]["route"]


def test_an_accepted_unachievable_followup_is_closed_and_not_routed():
    f = _unachievable_followup()
    f.unachievable.review("accepted", by="pi")
    out = rs.handoff_followups([f], known_ids=["F1"])
    assert out[0]["unachievable"]["decision"] == "accepted"
    assert "/plan" not in out[0]["route"]


def test_a_reopened_followup_is_open_again():
    f = _unachievable_followup()
    f.unachievable.review("reopened", by="pi")
    assert "/plan" in rs.handoff_followups([f], known_ids=["F1"])[0]["route"]


def test_clean_run_resolves():
    assert _gate(_both()).verdict == "resolved"
