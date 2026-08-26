"""
Tests for the writing / communication gate.

Run:  uv run pytest tests/test_writing_gate.py -v
"""


from research_rigor import writing_gate as wg

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
    v = wg.publication_verdict(report, human_approved=True, llm_triage_score=9.5)
    assert v.verdict == "blocked_fabrication"


def test_clean_but_unreviewed_is_blocked_pending_human():
    report = wg.verify_claims(
        [wg.Claim("c1", "74% acc", "numeric", 0.74, "results", "test_acc")], SOURCES)
    # High LLM score, no human sign-off -> still blocked. LLM judge is triage only.
    v = wg.publication_verdict(report, human_approved=None, llm_triage_score=9.9)
    assert v.verdict == "blocked_pending_human"
    v2 = wg.publication_verdict(report, human_approved=False)
    assert v2.verdict == "blocked_pending_human"


def test_ready_requires_clean_claims_and_human_signoff():
    report = wg.verify_claims(
        [wg.Claim("c1", "74% acc", "numeric", 0.74, "results", "test_acc")], SOURCES)
    v = wg.publication_verdict(report, human_approved=True)
    assert v.verdict == "ready" and not v.reasons


def test_ground_draft_combines_claims_and_scan():
    claims = [wg.Claim("c1", "74% acc", "numeric", 0.74, "results", "test_acc")]
    text = "We reach 74% accuracy with a suspicious 5.5x gain."
    report = wg.ground_draft(text, claims, SOURCES)
    assert report.grounded and report.unsourced_numbers and report.has_fabrication_risk
    v = wg.publication_verdict(report, human_approved=True)
    assert v.verdict == "blocked_fabrication"  # the unsourced 5.5x blocks even with sign-off
