"""
Writing / communication gate (stage `writeup`).

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

Two more rules meet here:

- A VERDICT HOLDS THROUGH THE WRITE-UP. A registered prediction without a signed
  verdict blocks the write-up, not only the `resolve` step.
- CITE A SOURCE YOU CAN OPEN, NOT A MEMORY OF ONE. Every paper the write-up
  leans on is recorded as a source — title, authors, year, a link someone can
  open and that was checked — with the papers built on kept apart from the
  ones set aside, and with which part was read (abstract or full) and when. A
  key paper read abstract-only or with no read date is flagged. Gaps are
  flagged, not blocked.

Division of labour:
- THIS LIBRARY grounds claims against sources, scans for unsourced numbers, and
  enforces the gate policy (fabrication and an unsigned prediction block; human
  sign-off is mandatory).
- THE /write skill runs Jr. AI Scientist's four-type reflection loop, builds the
  claim ledger, uses LLM-judge panels for triage only, and drives the human gate.
"""

import math
import re
from dataclasses import dataclass, field

from .resolve import VERDICTS as HYPOTHESIS_VERDICTS
from .resolve import Resolution, missing_verdicts


@dataclass
class Claim:
    """One checkable assertion in the draft, linked to its evidence.

    kind:
      "numeric"      — asserts a number; `asserted` is a float, checked against
                       sources[source_artifact][source_key].
      "hypothesis"   — asserts a hypothesis outcome; `asserted` is a verdict
                       string, checked against the signed verdict.
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

    sources: {artifact_name: {key: value}}. A hypothesis claim traces to the
    registered prediction and its signed verdict, so build that source from the
    resolutions: sources["verdicts"] = {r.hypothesis_id: r.verdict for r in resolutions}.
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


# --- papers: a source you can open, not a memory of one ---------------------

PAPER_STANDINGS = ("key", "set_aside")
PAPER_READS = ("abstract", "full")


@dataclass
class Paper:
    """One paper the write-up leans on, as a source. A paper filed from memory
    says so and may lack the catalogue details; that is recorded, and flagged.

    `read` and `read_date` record which part was read and when, and `version`
    the version read where the source has one: an abstract, a linkpost and an
    earlier version are summaries, and they drift from the results."""
    title: str
    standing: str                    # "key" (built on) | "set_aside"
    authors: str | None = None
    year: int | None = None
    link: str | None = None
    link_checked: bool = False       # someone opened the link and it resolved
    from_memory: bool = False
    read: str | None = None          # "abstract" | "full"
    read_date: str | None = None     # ISO date the source was read
    version: str | None = None       # e.g. "arXiv v2", where the source has versions

    def __post_init__(self):
        assert self.title and self.title.strip(), "a paper needs a title"
        assert self.standing in PAPER_STANDINGS, \
            f"paper {self.title!r}: standing must be one of {PAPER_STANDINGS}, got {self.standing!r}"
        assert self.read is None or self.read in PAPER_READS, \
            f"paper {self.title!r}: read must be one of {PAPER_READS}, got {self.read!r}"


def paper_flags(papers: list[Paper]) -> list[str]:
    """What stops each paper from being a citation someone can open."""
    flags = []
    for p in papers:
        missing = [f for f in ("authors", "year", "link") if not getattr(p, f)]
        if p.from_memory:
            flags.append(f"{p.title!r} was filed from memory — a claim about a paper, not a "
                         f"citation; open it and record what you actually read")
        if missing:
            flags.append(f"{p.title!r} is missing {missing}")
        elif not p.link_checked:
            flags.append(f"{p.title!r}: check the link resolves before the write-up leaves "
                         f"the building")
        if p.standing == "key" and (p.read == "abstract" or not p.read_date):
            flags.append(f"{p.title!r} is built on but was read abstract-only or has no read "
                         f"date — quote the results from the source's current version, and "
                         f"record which part you read and when")
    return flags


# --- the gate: human is the reviewer of last resort --------------------------

@dataclass
class GateVerdict:
    verdict: str        # "blocked_unsigned_verdict" | "blocked_fabrication"
                        # | "blocked_pending_human" | "ready"
    reasons: list[str]
    llm_triage_score: float | None
    human_approved: bool | None
    warnings: list[str] = field(default_factory=list)


def publication_verdict(report: ClaimReport, *, human_approved: bool | None,
                        frozen_hypothesis_ids: list[str], resolutions: list[Resolution],
                        papers: list[Paper],
                        llm_triage_score: float | None = None) -> GateVerdict:
    """Decide readiness. An LLM triage score can NEVER produce 'ready' — only
    signed verdicts for every registered prediction, a clean claim report and
    explicit human sign-off can. This is the one place the design refuses to
    let an LLM judge stand in for the human.

    `frozen_hypothesis_ids` is empty for work with no registered prediction
    (exploratory, labelled as such). Paper gaps are warnings, never a block.
    """
    warnings = paper_flags(papers)

    def verdict(name, reasons):
        return GateVerdict(name, reasons, llm_triage_score, human_approved, warnings)

    unsigned = missing_verdicts(frozen_hypothesis_ids, resolutions)
    if unsigned:
        return verdict("blocked_unsigned_verdict", [
            f"no signed verdict for registered predictions {unsigned} — a prediction without "
            f"a signed verdict blocks the write-up, not only the resolve step"])

    if report.has_fabrication_risk:
        reasons = [f"contradicted: {r.claim_id} — {r.detail}" for r in report.contradicted]
        reasons += [f"ungrounded: {r.claim_id} — {r.detail}" for r in report.ungrounded]
        reasons += [f"unsourced number in prose: {n}" for n in report.unsourced_numbers]
        return verdict("blocked_fabrication", reasons)

    if not human_approved:  # None or False
        return verdict("blocked_pending_human", [
            "mandatory human code+result review not completed "
            "(LLM-judge scores are triage only, never acceptance)"])

    return verdict("ready", [])
