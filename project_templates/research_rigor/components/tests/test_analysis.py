"""
Tests for analysis & interpretation (stage `analysis`).

Run:  uv run pytest tests/test_analysis.py -v
"""


import pytest

from research_rigor import analysis as an

FROZEN = ["H1", "H2"]


def _finding(fid="F1", **kw):
    kw.setdefault("statement", "ablation cuts the reward gap by 61%")
    kw.setdefault("evidence_type", "causal")
    kw.setdefault("artifact", "results/ablation.json")
    kw.setdefault("hypothesis_id", "H1")
    kw.setdefault("n_runs", 5)
    kw.setdefault("uncertainty", "95% CI [0.52, 0.70]")
    return an.Finding(fid, **kw)


def _clean():
    return an.analyse([_finding()], [], frozen_hypothesis_ids=FROZEN)


# --- evidence typing --------------------------------------------------------

def test_observational_evidence_does_not_license_a_causal_claim():
    obs = _finding(evidence_type="observational")
    assert obs.licenses("observational")
    assert not obs.licenses("causal")


def test_causal_evidence_licenses_the_weaker_claim_too():
    assert _finding(evidence_type="causal").licenses("observational")


def test_bad_evidence_type_fails_loudly():
    with pytest.raises(AssertionError, match="bad evidence_type"):
        _finding(evidence_type="vibes")


def test_over_read_finding_blocks_the_gate():
    r = an.analyse([_finding(evidence_type="observational")], [],
                   frozen_hypothesis_ids=FROZEN, claim_kinds={"F1": "causal"})
    assert r.overread == [("F1", "causal")]
    assert an.analysis_gate(r, pi_signed_off=True).verdict == "blocked_overread"


# --- the 82.5% failure mode: raising a concern then concluding anyway -------

def test_undispositioned_anomaly_blocks_even_with_sign_off():
    a = an.Anomaly("A1", "baseline is broken; the headline number is uninterpretable")
    r = an.analyse([_finding()], [a], frozen_hypothesis_ids=FROZEN)
    v = an.analysis_gate(r, pi_signed_off=True)
    assert v.verdict == "blocked_open_anomaly"
    assert "A1" in v.reasons[0]


def test_agent_cannot_close_its_own_critical_anomaly():
    a = an.Anomaly("A1", "baseline broken", raised_by="agent",
                   disposition="explained", disposition_note="looks fine on reflection",
                   dispositioned_by="agent")
    assert a.open
    r = an.analyse([_finding()], [a], frozen_hypothesis_ids=FROZEN)
    assert an.analysis_gate(r, pi_signed_off=True).verdict == "blocked_open_anomaly"


def test_pi_disposition_with_a_reason_closes_a_critical_anomaly():
    a = an.Anomaly("A1", "baseline broken", raised_by="agent", disposition="explained",
                   disposition_note="rerun with the fixed baseline; number held at 0.59",
                   dispositioned_by="pi")
    assert not a.open
    r = an.analyse([_finding()], [a], frozen_hypothesis_ids=FROZEN)
    assert an.analysis_gate(r, pi_signed_off=True).verdict == "closed"


def test_disposition_without_a_reason_is_not_a_disposition():
    a = an.Anomaly("A1", "baseline broken", disposition="explained",
                   disposition_note="   ", dispositioned_by="pi")
    assert a.open


def test_blocks_conclusion_stays_open_however_it_is_signed():
    a = an.Anomaly("A1", "target leakage in fold 3", disposition="blocks_conclusion",
                   disposition_note="confirmed leakage", dispositioned_by="pi")
    assert a.open


def test_minor_anomaly_may_be_dispositioned_by_the_agent():
    a = an.Anomaly("A2", "plot axis mislabelled", severity="minor", disposition="explained",
                   disposition_note="regenerated the figure", dispositioned_by="agent")
    assert not a.open


# --- repair proposals: the agent submits, the researcher accepts or declines -

def _repaired():
    a = an.Anomaly("A1", "baseline broken", raised_by="agent")
    p = a.propose_repair("reran with the fixed baseline; number held at 0.59",
                         ["results/rerun_fixed_baseline.json"])
    return a, p


def test_submitting_a_repair_never_closes_a_concern_by_itself():
    a, p = _repaired()
    assert p.concern_id == "A1" and a.open
    r = an.analyse([_finding()], [a], frozen_hypothesis_ids=FROZEN)
    assert r.repairs_awaiting_review == ["A1"]
    assert an.analysis_gate(r, pi_signed_off=True).verdict == "blocked_open_anomaly"


def test_researcher_accepting_a_repair_closes_the_concern_without_a_retyped_note():
    a, p = _repaired()
    a.review_repair(p, "accepted", by="pi")
    assert not a.open and a.disposition_note == ""
    r = an.analyse([_finding()], [a], frozen_hypothesis_ids=FROZEN)
    assert r.repairs_awaiting_review == []
    assert an.analysis_gate(r, pi_signed_off=True).verdict == "closed"


def test_a_declined_repair_stays_on_the_record_and_the_concern_stays_open():
    a, p = _repaired()
    a.review_repair(p, "declined", by="pi")
    assert a.open and a.repairs == [p] and p.decision == "declined"
    second = a.propose_repair("replaced the baseline entirely", ["results/new_baseline.json"])
    a.review_repair(second, "accepted", by="pi")
    assert not a.open and len(a.repairs) == 2


def test_agent_cannot_accept_its_own_repair():
    a, p = _repaired()
    with pytest.raises(AssertionError, match="by the researcher"):
        a.review_repair(p, "accepted", by="agent")
    assert a.open


def test_a_repair_must_say_what_changed_and_point_at_evidence():
    a = an.Anomaly("A1", "baseline broken")
    with pytest.raises(AssertionError, match="reference"):
        a.propose_repair("fixed it", [])
    with pytest.raises(AssertionError, match="what changed"):
        a.propose_repair("  ", ["results/rerun.json"])
    with pytest.raises(AssertionError, match="list of references"):
        a.propose_repair("fixed it", "results/rerun.json")


def test_manual_disposition_still_closes_a_concern_that_has_a_pending_repair():
    a, _ = _repaired()
    a.disposition, a.disposition_note, a.dispositioned_by = "explained", "checked by hand", "pi"
    assert not a.open


# --- grounding, scope of the prereg, and uncertainty ------------------------

def test_finding_with_no_artifact_is_ungrounded_and_blocks():
    r = an.analyse([_finding(artifact=None)], [], frozen_hypothesis_ids=FROZEN)
    assert r.ungrounded == ["F1"]
    assert an.analysis_gate(r, pi_signed_off=True).verdict == "blocked_ungrounded"


def test_finding_outside_the_frozen_prereg_is_exploratory_but_not_blocking():
    r = an.analyse([_finding(hypothesis_id="H9")], [], frozen_hypothesis_ids=FROZEN)
    assert r.exploratory == ["F1"]
    v = an.analysis_gate(r, pi_signed_off=True)
    assert v.verdict == "closed"
    assert any("exploratory" in w for w in v.warnings)


def test_single_run_without_uncertainty_warns_but_does_not_block():
    r = an.analyse([_finding(n_runs=1, uncertainty=None)], [], frozen_hypothesis_ids=FROZEN)
    assert r.unquantified == ["F1"]
    v = an.analysis_gate(r, pi_signed_off=True)
    assert v.verdict == "closed" and any("F1" in w for w in v.warnings)


def test_single_run_with_an_interval_is_quantified():
    r = an.analyse([_finding(n_runs=1, uncertainty="bootstrap 95% CI [0.50, 0.71]")], [],
                   frozen_hypothesis_ids=FROZEN)
    assert r.unquantified == [] and not an.analysis_gate(r, pi_signed_off=True).warnings


# --- a shape in a projection is not a shape in the model --------------------

@pytest.mark.parametrize("kw", [
    dict(),
    dict(view_variance_share=0.41),
    dict(non_projecting_check="results/cosine_similarity.png"),
])
def test_shape_claim_seen_only_in_a_projection_is_flagged_not_blocked(kw):
    r = an.analyse([_finding(shape="ring", **kw)], [], frozen_hypothesis_ids=FROZEN)
    assert r.shape_unchecked == ["F1"]
    v = an.analysis_gate(r, pi_signed_off=True)
    assert v.verdict == "closed" and any("does not project" in w for w in v.warnings)


def test_shape_claim_with_variance_share_and_a_non_projecting_check_is_clean():
    f = _finding(shape="ring", view_variance_share=0.41,
                 non_projecting_check="results/cosine_similarity.png")
    r = an.analyse([f], [], frozen_hypothesis_ids=FROZEN)
    assert r.shape_unchecked == [] and not an.analysis_gate(r, pi_signed_off=True).warnings


def test_a_finding_that_claims_no_shape_is_not_asked_for_one():
    assert _clean().shape_unchecked == []


def test_duplicate_finding_ids_fail_loudly():
    with pytest.raises(AssertionError, match="duplicate finding id"):
        an.analyse([_finding(), _finding()], [], frozen_hypothesis_ids=FROZEN)


# --- the gate has no automated path to closed -------------------------------

def test_clean_ledger_still_needs_the_human():
    assert an.analysis_gate(_clean(), pi_signed_off=False).verdict == "blocked_pending_human"
    assert an.analysis_gate(_clean(), pi_signed_off=True).verdict == "closed"


def test_open_anomaly_outranks_ungrounded_finding():
    """Ordering matters: the concern someone already raised is reported first."""
    r = an.analyse([_finding(artifact=None)], [an.Anomaly("A1", "surprise")],
                   frozen_hypothesis_ids=FROZEN)
    assert an.analysis_gate(r, pi_signed_off=True).verdict == "blocked_open_anomaly"
