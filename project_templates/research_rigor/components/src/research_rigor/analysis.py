"""
Analysis & interpretation (MVP-5, pipeline stage 6, Human-held).

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
WALK PAST: an anomaly, once registered, must be dispositioned by the PI before
the stage can close. That is the metacognitive loop the audit says agents lack,
implemented outside the agent where it cannot be talked out of.

Three more rules earn their place from the evidence:

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
  without uncertainty mislead (inspect_evals operations, 2507.06893).

Division of labour:
- THIS LIBRARY keeps the ledger and refuses to close the stage while a critical
  concern is open, a finding is ungrounded, or an evidence type is over-read.
- THE /analyze skill does the interpreting with the Fellow, raises anomalies
  honestly, and never dispositions its own critical anomaly.

Automated error-detection cannot substitute for any of this: the best model in
SPOT (2505.11855) catches 21.1% of real published errors at 6.1% precision.
"""

from dataclasses import dataclass, field

EVIDENCE_TYPES = ("causal", "observational", "qualitative")
DISPOSITIONS = ("explained", "blocks_conclusion", "deferred")
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
    disconfirming: bool = False         # does this cut AGAINST the hypothesis?

    def __post_init__(self):
        assert self.evidence_type in EVIDENCE_TYPES, \
            f"finding {self.id!r}: bad evidence_type {self.evidence_type!r} (one of {EVIDENCE_TYPES})"
        assert self.n_runs >= 1, f"finding {self.id!r}: n_runs must be >= 1"

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
class Anomaly:
    """A raised concern: a surprise, a broken baseline, an internal
    inconsistency, or an agent's own self-diagnosed flaw. The point of the
    dataclass is the `disposition` field — registering is cheap, walking past is
    not allowed."""
    id: str
    description: str
    severity: str = "critical"
    raised_by: str = "agent"             # "agent" | "pi" | "verifier"
    disposition: str | None = None
    disposition_note: str = ""
    dispositioned_by: str | None = None  # a CRITICAL anomaly needs "pi"

    def __post_init__(self):
        assert self.severity in SEVERITIES, f"anomaly {self.id!r}: bad severity {self.severity!r}"
        assert self.disposition is None or self.disposition in DISPOSITIONS, \
            f"anomaly {self.id!r}: bad disposition {self.disposition!r} (one of {DISPOSITIONS})"

    @property
    def open(self) -> bool:
        """Open = not dispositioned, dispositioned by someone other than the PI
        when critical, or dispositioned with no reason given. An agent may not
        close its own critical finding — that IS the 82.5% failure mode."""
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
    disconfirming: list = field(default_factory=list)    # finding ids cutting against a hypothesis


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
        if f.disconfirming:
            r.disconfirming.append(f.id)

        want = claim_kinds.get(f.id)
        if want and not f.licenses(want):
            r.overread.append((f.id, want))

    r.open_anomalies = [a.id for a in anomalies if a.open]
    return r


@dataclass
class AnalysisVerdict:
    verdict: str          # "blocked_open_anomaly" | "blocked_ungrounded" | "blocked_overread"
                          # | "blocked_pending_human" | "closed"
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def analysis_gate(report: AnalysisReport, *, pi_signed_off: bool) -> AnalysisVerdict:
    """Close stage 6 — or refuse to.

    Blocking conditions, in order. Each one is a documented failure mode, and
    none of them can be cleared by an agent asserting that it is fine:

    1. An OPEN ANOMALY. Includes an agent's own self-diagnosed critical flaw that
       nobody dispositioned, and anything explicitly marked `blocks_conclusion`.
       (Uncorrected self-awareness 82.5%; unremediated adversarial evidence 60.8%.)
    2. An UNGROUNDED finding — no artifact in the run dir to trace it to.
       (Method-conclusion disconnect 77.5%; report-code traceability gaps 60.5%.)
    3. An OVER-READ finding — an observational result being asked to carry a
       causal claim (reward-lens; the 53-point knowledge-action gap).
    4. No human sign-off. Interpretation is Human-held: there is no automated
       path to `closed`.

    Warnings (never blocking, always surfaced): unquantified single runs, and
    exploratory findings, which are reportable but cannot resolve a hypothesis.
    """
    warnings = []
    if report.unquantified:
        warnings.append(
            f"unquantified (n=1, no uncertainty): {report.unquantified} — a single run is "
            f"not a result; re-run with seeds or report an interval before concluding")
    if report.exploratory:
        warnings.append(
            f"exploratory (not in the frozen prereg): {report.exploratory} — reportable as "
            f"exploratory, but these cannot resolve a pre-registered hypothesis")
    if report.disconfirming:
        warnings.append(
            f"disconfirming evidence present: {report.disconfirming} — /resolve will require "
            f"this to be explicitly addressed, not omitted")

    if report.open_anomalies:
        return AnalysisVerdict("blocked_open_anomaly", [
            f"{len(report.open_anomalies)} anomaly/anomalies still open: {report.open_anomalies} — "
            f"each needs a PI disposition with a reason. Raising a concern and then concluding "
            f"anyway is the most common documented failure of AI research runs (82.5%)."
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
