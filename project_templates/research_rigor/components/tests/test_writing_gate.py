"""
Tests for the writing / communication gate.

Run:  uv run pytest tests/test_writing_gate.py -v
"""


import pytest

from research_rigor import writing_gate as wg
from research_rigor.resolve import Resolution

RESOLVED = [Resolution("H1", "supported", "cleared the frozen 50% threshold"),
            Resolution("H2", "inconclusive", "fell in the frozen inconclusive band")]


def _verdict(report, **kw):
    kw.setdefault("human_approved", True)
    kw.setdefault("frozen_hypothesis_ids", ["H1", "H2"])
    kw.setdefault("resolutions", RESOLVED)
    kw.setdefault("papers", [])
    return wg.publication_verdict(report, **kw)


def _clean_report():
    return wg.verify_claims(
        [wg.Claim("c1", "74% acc", "numeric", 0.74, "results", "test_acc")], SOURCES)

SOURCES = {
    "results": {"test_acc": 0.74, "baseline_acc": 0.71},
    "analysis": {"H1": "supported", "H2": "inconclusive"},
}


def test_grounded_numeric_claim_passes():
    c = wg.Claim("c1", "we reach 74% accuracy", "numeric", 0.74, "results", "test_acc")
    r = wg.verify_claims([c], SOURCES)
    assert r.grounded and not r.has_fabrication_risk


def test_contradicted_number_is_caught():
    # Draft claims 0.92 but the result is 0.74 — the text-vs-result discrepancy.
    c = wg.Claim("c1", "we reach 92% accuracy", "numeric", 0.92, "results", "test_acc")
    r = wg.verify_claims([c], SOURCES)
    assert r.contradicted and r.has_fabrication_risk
    assert "MISMATCH" in r.contradicted[0].detail


def test_ungrounded_number_has_no_source():
    # A fabricated stat pointing at a source key that doesn't exist.
    c = wg.Claim("c1", "F1 of 0.88", "numeric", 0.88, "results", "f1_score")
    r = wg.verify_claims([c], SOURCES)
    assert r.ungrounded and r.has_fabrication_risk
    assert "fabrication" in r.ungrounded[0].detail


def test_percent_vs_proportion_matches():
    # Draft says "74%", source stores 0.74 — should still ground.
    c = wg.Claim("c1", "74% accuracy", "numeric", 74.0, "results", "test_acc")
    assert wg.verify_claims([c], SOURCES).grounded


def test_hypothesis_claim_must_match_analysis_verdict():
    ok = wg.Claim("h", "H1 is supported", "hypothesis", "supported", "analysis", "H1")
    bad = wg.Claim("h", "H2 is supported", "hypothesis", "supported", "analysis", "H2")
    assert wg.verify_claims([ok], SOURCES).grounded
    contra = wg.verify_claims([bad], SOURCES)
    assert contra.contradicted and "inconclusive" in contra.contradicted[0].detail


def test_overstated_conclusion_is_a_contradiction():
    # The classic: analysis was inconclusive, the write-up claims support.
    c = wg.Claim("h2", "our results confirm H2", "hypothesis", "supported", "analysis", "H2")
    assert wg.verify_claims([c], SOURCES).has_fabrication_risk


def test_qualitative_claim_routed_to_human():
    c = wg.Claim("q", "the method is novel and elegant", "qualitative", None)
    r = wg.verify_claims([c], SOURCES)
    assert r.needs_human and not r.has_fabrication_risk  # not fabrication, but not auto-trusted either


def test_scan_flags_unsourced_prose_number():
    claims = [wg.Claim("c1", "74% accuracy", "numeric", 0.74, "results", "test_acc")]
    # 3.2x speedup is asserted nowhere — flag it.
    text = "We reach 74% accuracy with a 3.2x speedup over the baseline."
    flagged = wg.scan_unsourced_numbers(text, claims)
    # Exactly one unsourced number (3.2); the 74% is backed by a claim. Check the
    # flagged TOKEN (before the context snippet), not the snippet text.
    assert len(flagged) == 1
    token = flagged[0].split(" (")[0]
    assert "3.2" in token and "74" not in token


# --- the gate policy ---------------------------------------------------------

def test_fabrication_blocks_regardless_of_llm_score():
    report = wg.verify_claims(
        [wg.Claim("c1", "92% acc", "numeric", 0.92, "results", "test_acc")], SOURCES)
    # Even a glowing LLM triage score cannot unblock a fabricated claim.
    v = _verdict(report, human_approved=True, llm_triage_score=9.5)
    assert v.verdict == "blocked_fabrication"


def test_clean_but_unreviewed_is_blocked_pending_human():
    report = wg.verify_claims(
        [wg.Claim("c1", "74% acc", "numeric", 0.74, "results", "test_acc")], SOURCES)
    # High LLM score, no human sign-off -> still blocked. LLM judge is triage only.
    v = _verdict(report, human_approved=None, llm_triage_score=9.9)
    assert v.verdict == "blocked_pending_human"
    v2 = _verdict(report, human_approved=False)
    assert v2.verdict == "blocked_pending_human"


def test_ready_requires_clean_claims_and_human_signoff():
    report = wg.verify_claims(
        [wg.Claim("c1", "74% acc", "numeric", 0.74, "results", "test_acc")], SOURCES)
    v = _verdict(report, human_approved=True)
    assert v.verdict == "ready" and not v.reasons


def test_ground_draft_combines_claims_and_scan():
    claims = [wg.Claim("c1", "74% acc", "numeric", 0.74, "results", "test_acc")]
    text = "We reach 74% accuracy with a suspicious 5.5x gain."
    report = wg.ground_draft(text, claims, SOURCES)
    assert report.grounded and report.unsourced_numbers and report.has_fabrication_risk
    v = _verdict(report, human_approved=True)
    assert v.verdict == "blocked_fabrication"  # the unsourced 5.5x blocks even with sign-off


def test_nonfinite_numeric_evidence_cannot_pass_publication():
    for value in (float("inf"), float("-inf"), float("nan")):
        claim = wg.Claim("c", "result", "numeric", value, "results", "metric")
        report = wg.verify_claims([claim], {"results": {"metric": value}})
        assert report.contradicted
        assert _verdict(report, human_approved=True).verdict == "blocked_fabrication"


def test_invalid_tolerance_cannot_ground_a_claim():
    for tolerance in (float("inf"), float("nan"), -0.1):
        claim = wg.Claim("c", "result", "numeric", 1.0, "results", "metric",
                         tolerance=tolerance)
        assert wg.verify_claims([claim], {"results": {"metric": 1.0}}).contradicted


# --- a verdict holds through the write-up ------------------------------------

def test_prediction_without_a_signed_verdict_blocks_the_writeup():
    v = _verdict(_clean_report(), resolutions=RESOLVED[:1])
    assert v.verdict == "blocked_unsigned_verdict" and "H2" in v.reasons[0]


def test_unsigned_verdict_outranks_sign_off_and_a_clean_draft():
    v = _verdict(_clean_report(), resolutions=[], human_approved=True, llm_triage_score=9.9)
    assert v.verdict == "blocked_unsigned_verdict"


def test_exploratory_writeup_with_no_registered_prediction_is_not_blocked_on_verdicts():
    assert _verdict(_clean_report(), frozen_hypothesis_ids=[], resolutions=[]).verdict == "ready"


# --- cite a source you can open ----------------------------------------------

def _paper(**kw):
    kw.setdefault("standing", "key")
    kw.setdefault("authors", "Engels et al.")
    kw.setdefault("year", 2024)
    kw.setdefault("link", "https://arxiv.org/abs/2405.14860")
    kw.setdefault("link_checked", True)
    return wg.Paper("Not All Language Model Features Are Linear", **kw)


def test_a_complete_checked_source_raises_no_flag():
    assert wg.paper_flags([_paper(), _paper(standing="set_aside")]) == []


@pytest.mark.parametrize("kw", [dict(authors=None), dict(year=None), dict(link=None),
                                dict(link_checked=False), dict(from_memory=True)])
def test_a_source_nobody_can_open_is_flagged_not_blocked(kw):
    papers = [_paper(**kw)]
    assert len(wg.paper_flags(papers)) == 1
    v = _verdict(_clean_report(), papers=papers)
    assert v.verdict == "ready" and v.warnings == wg.paper_flags(papers)


def test_a_paper_is_either_built_on_or_set_aside():
    with pytest.raises(AssertionError, match="standing"):
        _paper(standing="maybe")
