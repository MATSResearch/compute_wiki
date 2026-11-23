"""
Analysis & interpretation (stage `analysis`, Human-held).

The least automatable stage in the corpus, and now the best-documented one. The
2026 end-to-end failure audit (2608.14905: 800 trajectories over 100 real
frontier research tasks, 45-pattern taxonomy) found 92.1% of failures are
COGNITIVE rather than engineering, and its single most frequent pattern is not a
detection failure at all:

    "Uncorrected self-awareness" — the agent identifies a critical flaw during
    self-review and ships the unrevised conclusion anyway. 660/800 runs (82.5%).

Alongside it: "unremediated adversarial evidence" (60.8%), "method-conclusion
disconnect" (77.5%), "report-code traceability gaps" (60.5%). The audit's own
diagnosis is the design brief for this library:

    "The evidence to refute most failures is already present in the agent's own
    run directory, but the agent fails to perform the comparison."

So the fix is NOT a better detector. Detection mostly already happened. The fix
is a deterministic, external ledger that makes a raised concern IMPOSSIBLE TO
WALK PAST: an anomaly, once registered, stays open until the researcher either
accepts a repair proposal for it or gives it a manual disposition. That is the
metacognitive loop the audit says agents lack, implemented outside the agent
where it cannot be talked out of. An open concern never blocks the WORK — only
the claim that the work is finished.

The agent's side of that loop is the REPAIR PROPOSAL: a summary of what changed
plus references to a rerun, independent check, or revised claim. The references
are not proof that a check ran; submitting a proposal never closes a concern by
itself. The researcher inspects the evidence and accepts (which closes the
concern without retyping the agent's explanation) or declines.

Four more rules earn their place from the evidence:

- EVIDENCE TYPE IS LOAD-BEARING, not prose. Observational evidence does not
  license a causal claim: attribution-vs-causal-patching correlates rho =
  -0.256..-0.027 (reward-lens 2604.26130), and probes reading a hazard at 98.2%
  AUROC coexist with the model acting on it 45% of the time — a 53-point
  knowledge-action gap (2603.18353). reward-lens's design fix is to make the two
  syntactically distinct; we adopt it as a house convention.
- CONFIRMATORY vs EXPLORATORY is decided by the FROZEN prereg, not at analysis
  time. A finding whose hypothesis is not in the frozen file is exploratory —
  reportable, but it cannot resolve anything (the p-hacking guard, complementing
  preregister.check's deviation diff).
- A SINGLE RUN IS NOT A RESULT. Single runs are unreliable and leaderboards
  without uncertainty mislead (inspect_evals operations, 2507.06893). Estimate
  robustness by varying the SAMPLE, not the seed.
- A SHAPE IN A PROJECTION IS NOT A SHAPE IN THE MODEL. A finding that claims a
  representation has a shape names the share of variance of the view it was
  seen in and cites a check that does not project.

Division of labour:
- THIS LIBRARY keeps the ledger and refuses to close the stage while a critical
  concern is open, a finding is ungrounded, or an evidence type is over-read.
- THE /analyze skill does the interpreting with the Fellow, raises anomalies
  honestly, proposes repairs, and never closes its own critical anomaly.

Automated error-detection cannot substitute for any of this: the best model in
SPOT (2505.11855) catches 21.1% of real published errors at 6.1% precision.
"""

from dataclasses import dataclass, field

EVIDENCE_TYPES = ("causal", "observational", "qualitative")
DISPOSITIONS = ("explained", "blocks_conclusion", "deferred")
REPAIR_DECISIONS = ("accepted", "declined")
SEVERITIES = ("critical", "minor")


@dataclass
class Finding:
    """One interpreted result. `artifact` is the path INSIDE the run dir the
    number actually came from — a finding that cannot name one is ungrounded
    (method-conclusion disconnect, 77.5% of audited runs)."""
    id: str
    statement: str
    evidence_type: str
    artifact: str | None = None
    hypothesis_id: str | None = None    # None => exploratory, cannot resolve anything
    n_runs: int = 1
    uncertainty: str | None = None      # e.g. "95% CI [0.31, 0.44]"; None => unquantified
    # A claim that a representation has a shape (ring, helix, manifold) names
    # the share of variance of the view it was seen in and one check that does
    # not project: a similarity matrix, or a topology result against a null.
    shape: str | None = None
    view_variance_share: float | None = None
    non_projecting_check: str | None = None   # artifact path of that check

    def __post_init__(self):
        assert self.evidence_type in EVIDENCE_TYPES, \
            f"finding {self.id!r}: bad evidence_type {self.evidence_type!r} (one of {EVIDENCE_TYPES})"
        assert self.n_runs >= 1, f"finding {self.id!r}: n_runs must be >= 1"
        assert self.view_variance_share is None or 0.0 <= self.view_variance_share <= 1.0, \
            f"finding {self.id!r}: view_variance_share is a fraction in [0, 1]"

    def licenses(self, claim_kind: str) -> bool:
        """Does this finding license a claim of `claim_kind`? Only causal
        evidence licenses a causal claim; observational evidence licenses an
        observational one. Deterministic on purpose — a Fellow should not be able
        to upgrade the strength of their evidence in prose."""
        assert claim_kind in EVIDENCE_TYPES, f"bad claim_kind {claim_kind!r}"
        if claim_kind == "causal":
            return self.evidence_type == "causal"
        if claim_kind == "observational":
            return self.evidence_type in ("causal", "observational")
        return True


@dataclass
class RepairProposal:
    """What an agent (or anyone) submits against a concern: what changed, and
    where the rerun, independent check, or revised claim can be inspected. The
    references are not proof that a check ran or that its conclusion is sound."""
    concern_id: str
    summary: str
    evidence_refs: list
    proposed_by: str = "agent"
    decision: str | None = None          # None (awaiting review) | "accepted" | "declined"
    decided_by: str | None = None

    def __post_init__(self):
        assert self.summary and self.summary.strip(), \
            f"repair for {self.concern_id!r}: say what changed"
        assert isinstance(self.evidence_refs, list), \
            f"repair for {self.concern_id!r}: evidence_refs is a list of references"
        assert self.evidence_refs, (
            f"repair for {self.concern_id!r}: reference the rerun, independent check, or "
            f"revised claim the researcher is to inspect")
        assert self.decision is None or self.decision in REPAIR_DECISIONS, \
            f"repair for {self.concern_id!r}: bad decision {self.decision!r}"


@dataclass
class Anomaly:
    """A raised concern: a surprise, a broken baseline, an internal
    inconsistency, or an agent's own self-diagnosed flaw. Registering is cheap;
    walking past is not allowed. It closes one of two ways: the researcher
    accepts a repair proposal, or gives a manual `disposition`."""
    id: str
    description: str
    severity: str = "critical"
    raised_by: str = "agent"             # "agent" | "pi" | "verifier"
    disposition: str | None = None
    disposition_note: str = ""
    dispositioned_by: str | None = None  # a CRITICAL anomaly needs "pi"
    repairs: list = field(default_factory=list)   # every RepairProposal stays on the record

    def __post_init__(self):
        assert self.severity in SEVERITIES, f"anomaly {self.id!r}: bad severity {self.severity!r}"
        assert self.disposition is None or self.disposition in DISPOSITIONS, \
            f"anomaly {self.id!r}: bad disposition {self.disposition!r} (one of {DISPOSITIONS})"

    def propose_repair(self, summary: str, evidence_refs: list, *,
                       proposed_by: str = "agent") -> RepairProposal:
        """Submit a repair. This never closes the concern by itself."""
        proposal = RepairProposal(self.id, summary, evidence_refs, proposed_by)
        self.repairs.append(proposal)
        return proposal

    def review_repair(self, proposal: RepairProposal, decision: str, *, by: str) -> None:
        """The researcher's decision on a proposal, after inspecting its evidence."""
        assert any(p is proposal for p in self.repairs), \
            f"anomaly {self.id!r}: that proposal was not submitted against this concern"
        assert decision in REPAIR_DECISIONS, f"bad decision {decision!r} (one of {REPAIR_DECISIONS})"
        assert by == "pi", (
            f"anomaly {self.id!r}: a repair is accepted or declined by the researcher, not "
            f"{by!r} — a proposal alone is not a verified resolution")
        assert proposal.decision is None, \
            f"anomaly {self.id!r}: that proposal was already {proposal.decision}"
        proposal.decision, proposal.decided_by = decision, by

    @property
    def open(self) -> bool:
        """Closed by an accepted repair, or by a manual disposition. Otherwise
        open: not dispositioned, dispositioned by someone other than the PI when
        critical, or dispositioned with no reason given. An agent may not close
        its own critical finding — that IS the 82.5% failure mode — and a repair
        proposal that nobody has accepted closes nothing."""
        if any(p.decision == "accepted" for p in self.repairs):
            return False
        if self.disposition is None:
            return True
        if not self.disposition_note.strip():
            return True
        if self.severity == "critical" and self.dispositioned_by != "pi":
            return True
        return self.disposition == "blocks_conclusion"


@dataclass
class AnalysisReport:
    findings: list = field(default_factory=list)
    ungrounded: list = field(default_factory=list)       # finding ids with no artifact
    exploratory: list = field(default_factory=list)      # finding ids not tied to a frozen hypothesis
    unquantified: list = field(default_factory=list)     # single-run, no uncertainty
    overread: list = field(default_factory=list)         # (finding_id, claim_kind) evidence-type violations
    open_anomalies: list = field(default_factory=list)   # anomaly ids still open
    repairs_awaiting_review: list = field(default_factory=list)  # anomaly ids with an undecided proposal
    shape_unchecked: list = field(default_factory=list)  # shape claims missing variance share or a non-projecting check


def analyse(findings: list[Finding], anomalies: list[Anomaly], *,
            frozen_hypothesis_ids: list[str],
            claim_kinds: dict | None = None) -> AnalysisReport:
    """Build the ledger. `claim_kinds` maps finding_id -> the STRENGTH OF CLAIM
    the Fellow wants to make from it ("causal"/"observational"/"qualitative");
    anything stronger than the evidence supports lands in `overread`.

    This function reports; it never decides. `analysis_gate` decides.
    """
    frozen = set(frozen_hypothesis_ids)
    claim_kinds = claim_kinds or {}
    r = AnalysisReport(findings=list(findings))

    seen = set()
    for f in findings:
        assert f.id not in seen, f"duplicate finding id {f.id!r}"
        seen.add(f.id)

        if not f.artifact:
            r.ungrounded.append(f.id)
        if f.hypothesis_id is None or f.hypothesis_id not in frozen:
            r.exploratory.append(f.id)
        if f.n_runs == 1 and not f.uncertainty:
            r.unquantified.append(f.id)
        if f.shape and (f.view_variance_share is None or not f.non_projecting_check):
            r.shape_unchecked.append(f.id)

        want = claim_kinds.get(f.id)
        if want and not f.licenses(want):
            r.overread.append((f.id, want))

    r.open_anomalies = [a.id for a in anomalies if a.open]
    r.repairs_awaiting_review = [a.id for a in anomalies
                                 if a.open and any(p.decision is None for p in a.repairs)]
    return r


@dataclass
class AnalysisVerdict:
    verdict: str          # "blocked_open_anomaly" | "blocked_ungrounded" | "blocked_overread"
                          # | "blocked_pending_human" | "closed"
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def analysis_gate(report: AnalysisReport, *, pi_signed_off: bool) -> AnalysisVerdict:
    """Close stage 8 (`analysis`) — or refuse to.

    Blocking conditions, in order. Each one is a documented failure mode, and
    none of them can be cleared by an agent asserting that it is fine:

    1. An OPEN ANOMALY. Includes an agent's own self-diagnosed critical flaw that
       nobody dispositioned, one with a repair proposal the researcher has not
       accepted, and anything explicitly marked `blocks_conclusion`.
       (Uncorrected self-awareness 82.5%; unremediated adversarial evidence 60.8%.)
    2. An UNGROUNDED finding — no artifact in the run dir to trace it to.
       (Method-conclusion disconnect 77.5%; report-code traceability gaps 60.5%.)
    3. An OVER-READ finding — an observational result being asked to carry a
       causal claim (reward-lens; the 53-point knowledge-action gap).
    4. No human sign-off. Interpretation is Human-held: there is no automated
       path to `closed`.

    Warnings (never blocking, always surfaced): unquantified single runs,
    exploratory findings (reportable, but they cannot resolve a hypothesis), and
    shape claims seen only in a projection.
    """
    warnings = []
    if report.unquantified:
        warnings.append(
            f"unquantified (n=1, no uncertainty): {report.unquantified} — a single run is "
            f"not a result; vary the sample (bootstrap the eval set, overlapping data "
            f"subsets, hyperparameter perturbation), not the seed, and report an interval "
            f"before concluding")
    if report.exploratory:
        warnings.append(
            f"exploratory (not in the frozen prereg): {report.exploratory} — reportable as "
            f"exploratory, but these cannot resolve a pre-registered hypothesis")
    if report.shape_unchecked:
        warnings.append(
            f"shape claimed from a projection: {report.shape_unchecked} — name the share of "
            f"variance of the view and cite one check that does not project (a similarity "
            f"matrix, or a topology result against a null)")

    if report.open_anomalies:
        return AnalysisVerdict("blocked_open_anomaly", [
            f"{len(report.open_anomalies)} anomaly/anomalies still open: {report.open_anomalies} — "
            f"each needs the researcher to accept a repair proposal or give a disposition with "
            f"a reason" +
            (f" (repair proposals awaiting review: {report.repairs_awaiting_review})"
             if report.repairs_awaiting_review else "") +
            ". Keep working; just do not call the step done. Raising a concern and then "
            "concluding anyway is the most common documented failure of AI research runs (82.5%)."
        ], warnings)

    if report.ungrounded:
        return AnalysisVerdict("blocked_ungrounded", [
            f"findings with no source artifact: {report.ungrounded} — every finding must name "
            f"the file in the run dir it came from, or it cannot be checked by anyone."
        ], warnings)

    if report.overread:
        return AnalysisVerdict("blocked_overread", [
            f"evidence over-read: {[f'{fid} -> {kind} claim' for fid, kind in report.overread]} — "
            f"observational evidence does not license a causal claim (attribution vs causal "
            f"patching correlate rho~=0); weaken the claim or run the causal test."
        ], warnings)

    if not pi_signed_off:
        return AnalysisVerdict("blocked_pending_human", [
            "ledger is clean, but interpretation is Human-held — the Fellow must sign off. "
            "There is deliberately no automated path to `closed`."
        ], warnings)

    return AnalysisVerdict("closed", [], warnings)
