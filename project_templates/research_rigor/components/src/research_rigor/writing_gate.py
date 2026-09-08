"""
Writing / communication gate (MVP-3, pipeline stage 8).

The stage where the Fellow's output meets the world — and where the safety
evidence is starkest: LLM reviewers accept fabricated papers 67-82% of the time
(BadScientist) and cannot detect text-vs-result discrepancies (Jr. AI Scientist);
automated reviewers systematically overestimate quality (Agent Laboratory 6.1
auto vs 3.8 human). So the rule this gate enforces:

    No LLM-judge pass substitutes for the human. The human is the reviewer of
    last resort; LLM judges are for TRIAGE only, never acceptance.

The highest-leverage deterministic defense is CLAIM-GROUNDING: every quantitative
claim in the draft must trace to an actual result artifact in the run-dir. A
fabricated number matches no source; a text-vs-result discrepancy shows up as a
contradiction. This directly attacks the corpus's best-documented failure mode.

Division of labour:
- THIS LIBRARY grounds claims against sources, scans for unsourced numbers, and
  enforces the gate policy (fabrication blocks; human sign-off is mandatory).
- THE /write skill runs Jr. AI Scientist's four-type reflection loop, builds the
  claim ledger, uses LLM-judge panels for triage only, and drives the human gate.
"""

import math
import re
from dataclasses import dataclass, field

HYPOTHESIS_VERDICTS = ("supported", "refuted", "inconclusive")


@dataclass
class Claim:
    """One checkable assertion in the draft, linked to its evidence.

    kind:
      "numeric"      — asserts a number; `asserted` is a float, checked against
                       sources[source_artifact][source_key].
      "hypothesis"   — asserts a hypothesis outcome; `asserted` is a verdict
                       string, checked against the analysis/prereg verdict.
      "qualitative"  — a non-numeric claim; cannot be auto-grounded, so it is
                       routed to the human (never silently trusted).
    """
    id: str
    text: str
    kind: str
    asserted: object
    source_artifact: str | None = None
    source_key: str | None = None
    tolerance: float = 0.02  # relative tolerance for numeric claims

    def __post_init__(self):
        assert self.kind in ("numeric", "hypothesis", "qualitative"), f"bad kind {self.kind!r}"
        if self.kind == "hypothesis":
            assert self.asserted in HYPOTHESIS_VERDICTS, \
                f"hypothesis verdict must be one of {HYPOTHESIS_VERDICTS}, got {self.asserted!r}"


@dataclass
class ClaimResult:
    claim_id: str
    status: str      # "grounded" | "contradicted" | "ungrounded" | "needs_human"
    detail: str


@dataclass
class ClaimReport:
    results: list[ClaimResult] = field(default_factory=list)
    unsourced_numbers: list[str] = field(default_factory=list)

    def _by(self, status):
        return [r for r in self.results if r.status == status]

    @property
    def grounded(self): return self._by("grounded")
    @property
    def contradicted(self): return self._by("contradicted")
    @property
    def ungrounded(self): return self._by("ungrounded")
    @property
    def needs_human(self): return self._by("needs_human")

    @property
    def has_fabrication_risk(self) -> bool:
        """A contradicted or ungrounded numeric/hypothesis claim, or an unsourced
        number in prose, is a fabrication risk that blocks publication."""
        return bool(self.contradicted or self.ungrounded or self.unsourced_numbers)


def _matches(asserted: float, actual: float, rel_tol: float) -> bool:
    if not all(math.isfinite(v) for v in (asserted, actual, rel_tol)) or rel_tol < 0:
        return False
    # Accept either a raw match or a percent/proportion mismatch (74 vs 0.74).
    return (math.isclose(asserted, actual, rel_tol=rel_tol)
            or math.isclose(asserted / 100.0, actual, rel_tol=rel_tol)
            or math.isclose(asserted, actual / 100.0, rel_tol=rel_tol))


def verify_claims(claims: list[Claim], sources: dict) -> ClaimReport:
    """Ground every claim against the actual result artifacts.

    sources: {artifact_name: {key: value}}. For hypothesis claims, the artifact
    is typically the analysis verdicts, e.g. sources["analysis"] = {"H1": "supported"}.
    """
    report = ClaimReport()
    for c in claims:
        if c.kind == "qualitative":
            report.results.append(ClaimResult(c.id, "needs_human",
                "qualitative claim — cannot auto-ground; human must verify"))
            continue

        art = sources.get(c.source_artifact) if c.source_artifact else None
        if art is None or c.source_key not in art:
            report.results.append(ClaimResult(c.id, "ungrounded",
                f"no source {c.source_artifact!r}/{c.source_key!r} for asserted {c.asserted!r} "
                f"— possible fabrication"))
            continue

        actual = art[c.source_key]
        if c.kind == "numeric":
            ok = _matches(float(c.asserted), float(actual), c.tolerance)
            report.results.append(ClaimResult(
                c.id, "grounded" if ok else "contradicted",
                f"asserted {c.asserted} vs source {actual}" + ("" if ok else " — MISMATCH")))
        else:  # hypothesis
            ok = str(c.asserted) == str(actual)
            report.results.append(ClaimResult(
                c.id, "grounded" if ok else "contradicted",
                f"claims {c.asserted!r}; analysis says {actual!r}" + ("" if ok else " — MISMATCH")))
    return report


_NUMBER_RE = re.compile(r"(?<![\w.])(\d+\.\d+)\s*%?|(\d+)\s*%")


def scan_unsourced_numbers(draft_text: str, claims: list[Claim]) -> list[str]:
    """Flag decimals/percentages in prose not backed by any numeric claim.
    Heuristic and advisory, but it catches numbers that were never linked to a
    result at all — the rawest fabrication signal."""
    asserted = [float(c.asserted) for c in claims if c.kind == "numeric"]
    flagged = []
    for m in _NUMBER_RE.finditer(draft_text):
        raw = m.group(1) or m.group(2)
        num = float(raw)
        covered = any(_matches(a, num, 0.02) for a in asserted)
        if not covered:
            snippet = draft_text[max(0, m.start() - 25):m.end() + 25].replace("\n", " ").strip()
            flagged.append(f"'{m.group(0).strip()}' (…{snippet}…)")
    return flagged


def ground_draft(draft_text: str, claims: list[Claim], sources: dict) -> ClaimReport:
    """Full grounding pass: verify every linked claim AND scan the prose for
    numbers with no claim behind them. This is what the gate reads."""
    report = verify_claims(claims, sources)
    report.unsourced_numbers = scan_unsourced_numbers(draft_text, claims)
    return report


# --- the gate: human is the reviewer of last resort --------------------------

@dataclass
class GateVerdict:
    verdict: str        # "blocked_fabrication" | "blocked_pending_human" | "ready"
    reasons: list[str]
    llm_triage_score: float | None
    human_approved: bool | None


def publication_verdict(report: ClaimReport, *, human_approved: bool | None,
                        llm_triage_score: float | None = None) -> GateVerdict:
    """Decide readiness. An LLM triage score can NEVER produce 'ready' — only a
    clean claim report plus explicit human sign-off can. This is the one place the
    design refuses to let an LLM judge stand in for the human."""
    reasons = []
    if report.has_fabrication_risk:
        for r in report.contradicted:
            reasons.append(f"contradicted: {r.claim_id} — {r.detail}")
        for r in report.ungrounded:
            reasons.append(f"ungrounded: {r.claim_id} — {r.detail}")
        for n in report.unsourced_numbers:
            reasons.append(f"unsourced number in prose: {n}")
        return GateVerdict("blocked_fabrication", reasons, llm_triage_score, human_approved)

    if not human_approved:  # None or False
        reasons.append("mandatory human code+result review not completed "
                       "(LLM-judge scores are triage only, never acceptance)")
        return GateVerdict("blocked_pending_human", reasons, llm_triage_score, human_approved)

    return GateVerdict("ready", [], llm_triage_score, human_approved)
