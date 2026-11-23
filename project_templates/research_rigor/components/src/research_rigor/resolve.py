"""
Resolving hypotheses & proposing follow-ups (stage `resolve`, Human-held).

This is the checkpoint the proposal cares most about, and the evidence says it is
where agents are least trustworthy:

- Conclusion formation is one of the two dominant failure categories, and its
  named forms are UNSUPPORTED and OVERGENERALIZED claims (FIRE-Bench 2602.02905;
  best agent 46.7 F1 with +-23.4 run-to-run variance).
- "Overclaiming with concealed negative results" appears in 78.1% of audited
  end-to-end runs, and "method-conclusion disconnect" in 77.5% (2608.14905).
- Agents suppress anomaly detection under long-horizon narrative pressure —
  cognitive tunneling: they trigger fewer "redo study" actions in context than in
  isolation despite MORE environmental noise (InquiTree 2606.09550).
- 68% of writing traces ignore refutation evidence outright (Jr. AI Scientist
  2511.04583).

Even the best dedicated machinery does not fix this. EviGraph (2608.04738) makes
the claim-evidence structure the agent's operational state and still only reaches
a 37.85% Claim Support Rate (vs 27% for the strongest baseline). A ~62%
ungrounded-claim rate is not a gate; it is a reason the human stays the decider.

So this library resolves NOTHING by inference. It:

- requires a verdict for EVERY frozen hypothesis, so a hypothesis that did not
  come out well cannot be quietly dropped from the write-up;
- treats `inconclusive` as a first-class result, never a failure to be avoided —
  removing the incentive that produces concealed negative results;
- refuses a verdict that generalizes past what was actually tested (the scope
  guard: your claim's model/dataset/population must be what you ran);
- refuses a concluding verdict (`supported` or `refuted`) while an anomaly from
  stage 8 (`analysis`) is open;
- reads each verdict against the evidence ledger (`evidence.Citation`) and FLAGS
  — never blocks — one that disagrees with its own evidence, or that leaves
  something cited against it unaddressed by name;
- flags a `supported` verdict while a rival under the same question is still
  unrefuted ("rivals still stand");
- holds through `writeup` and `publish`: `missing_verdicts` is what those two
  gates block on, so a prediction without a signed verdict stops the write-up
  and the release, not only this step;
- and routes follow-ups BACK through /plan's diversity gate, each carrying its
  acceptance condition, rather than letting the run adopt its own next question
  (planning.plan_gate: selection is the researcher's unless delegated).

Follow-ups carry the lesson that motivated them, borrowing MARS's comparative
reflective memory (2602.02660), whose cross-branch lesson transfer accounted for
63% of the lessons it actually used — the mechanism that makes one run's failure
useful to the next Fellow rather than dying with the run dir.

Division of labour:
- THIS LIBRARY enforces completeness, scope, and authorship of the resolution.
- THE /resolve skill drafts the reasoning, surfaces what cuts against the
  hypothesis, and hands the decision to the Fellow.
"""

from dataclasses import dataclass, field

from .evidence import CONCLUDING_VERDICTS, Citation, disagreement, tally

VERDICTS = ("supported", "refuted", "inconclusive")


@dataclass
class Resolution:
    """The PI's verdict on ONE frozen hypothesis. `claimed_scope` is the scope
    the write-up will assert over (e.g. {"model": "llama-3-8b", "dataset":
    "anthropic_hh"}); it is checked against what was actually run."""
    hypothesis_id: str
    verdict: str
    rationale: str
    decided_by: str = "pi"
    claimed_scope: dict = field(default_factory=dict)
    addresses_disconfirming: list = field(default_factory=list)  # cited-against items addressed by name

    def __post_init__(self):
        assert self.verdict in VERDICTS, \
            f"{self.hypothesis_id}: bad verdict {self.verdict!r} (one of {VERDICTS})"
        assert self.rationale and self.rationale.strip(), \
            f"{self.hypothesis_id}: a verdict with no rationale is not a resolution"


@dataclass
class FollowUp:
    """A next question. `motivated_by` must point at a real finding or anomaly id
    from this run — a follow-up nobody can trace to evidence is an idea, not a
    result of the work. `acceptance` says what done means for it, written when
    the follow-up is filed."""
    id: str
    question: str
    motivated_by: str
    acceptance: str
    lesson: str = ""


def scope_violations(claimed: dict, tested: dict) -> list[str]:
    """Where does the claim reach past the experiment?

    A claimed key that was never varied or recorded in `tested` is an
    overgeneralization; a claimed value that differs from what was run is a
    misstatement. Both are reported as strings for the gate to relay.

    A claim that is NARROWER than what was tested is fine — you may always say
    less than you showed.
    """
    out = []
    for key, claimed_val in claimed.items():
        if key not in tested:
            out.append(f"claims over {key!r} but the run never recorded it — untested scope")
            continue
        tested_val = tested[key]
        cset = set(claimed_val) if isinstance(claimed_val, (list, tuple, set)) else {claimed_val}
        tset = set(tested_val) if isinstance(tested_val, (list, tuple, set)) else {tested_val}
        extra = cset - tset
        if extra:
            out.append(f"claims {key}={sorted(map(str, extra))} but only tested {sorted(map(str, tset))}")
    return out


def signed_verdicts(resolutions: list[Resolution]) -> dict:
    """hypothesis id -> its one signed verdict. A verdict is signed once, by the
    researcher: an agent may draft the rationale, never own the verdict."""
    by_id = {}
    for r in resolutions:
        assert r.decided_by == "pi", (
            f"{r.hypothesis_id}: resolution was decided by {r.decided_by!r}. Hypothesis "
            f"resolution is Human-held — an agent may draft the rationale, never own the verdict.")
        assert r.hypothesis_id not in by_id, f"two resolutions for {r.hypothesis_id!r}"
        by_id[r.hypothesis_id] = r
    return by_id


def missing_verdicts(frozen_hypothesis_ids: list[str], resolutions: list[Resolution]) -> list[str]:
    """Registered predictions with no signed verdict. `resolve`, `writeup` and
    `publish` all block on a non-empty answer."""
    by_id = signed_verdicts(resolutions)
    return [h for h in frozen_hypothesis_ids if h not in by_id]


@dataclass
class ResolveVerdict:
    verdict: str      # "blocked_incomplete" | "blocked_open_anomaly" | "blocked_overgeneralized"
                      # | "resolved"
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    resolutions: list = field(default_factory=list)


def resolve_gate(*, frozen_hypothesis_ids: list[str], question_of: dict,
                 resolutions: list[Resolution], tested_scope: dict,
                 open_anomalies: list[str], evidence: list[Citation]) -> ResolveVerdict:
    """Close stage 9 (`resolve`) — or refuse to.

    `question_of` maps each frozen hypothesis id to the research question it
    answers (the prereg's `question` field); `open_anomalies` comes straight
    from stage 8's AnalysisReport; `evidence` is the run's citation ledger
    (`evidence.load`). The verdicts are read against the evidence, and a
    disagreement is a warning for the person signing — never a block.
    """
    frozen = list(frozen_hypothesis_ids)
    assert frozen, "no frozen hypotheses — /resolve runs against a frozen prereg"
    assert set(question_of) == set(frozen), \
        f"question_of must name the question of exactly the frozen hypotheses {frozen}"
    for c in evidence:
        assert c.prediction in frozen, \
            f"evidence item {c.item!r} cites {c.prediction!r}, which is not a frozen hypothesis"

    by_id = signed_verdicts(resolutions)
    missing = missing_verdicts(frozen, resolutions)
    extra = [h for h in by_id if h not in frozen]
    if missing or extra:
        reasons = []
        if missing:
            reasons.append(
                f"no verdict for frozen hypotheses {missing} — every pre-registered hypothesis "
                f"gets a verdict, including `inconclusive`. Dropping the ones that did not work "
                f"out is exactly the concealed-negative-results failure (78.1% of audited runs).")
        if extra:
            reasons.append(f"resolutions for hypotheses that were never frozen: {extra}")
        return ResolveVerdict("blocked_incomplete", reasons)

    warnings = []
    n_inconclusive = sum(1 for r in by_id.values() if r.verdict == "inconclusive")
    if n_inconclusive:
        warnings.append(
            f"{n_inconclusive} hypothesis/hypotheses inconclusive — that is a legitimate result "
            f"and belongs in the write-up as one. Do not go looking for a cut of the data that "
            f"resolves it; the prereg's decision rule already spoke.")

    concluded = [r for r in by_id.values() if r.verdict in CONCLUDING_VERDICTS]

    for r in concluded:
        t = tally(evidence, r.hypothesis_id)
        flag = disagreement(r.verdict, t)
        if flag:
            warnings.append(
                f"{r.hypothesis_id}: {flag} — a verdict that disagrees with its own evidence "
                f"is the shape of overclaiming by omission. The tally is context, not a vote: "
                f"check it against the decision rule you froze.")
        unaddressed = [i for i in t.against if i not in r.addresses_disconfirming]
        if unaddressed:
            warnings.append(
                f"{r.hypothesis_id}: cited against and not addressed by name: {unaddressed}. "
                f"Say why it does not change the conclusion, or change the conclusion.")

    for r in concluded:
        if r.verdict != "supported":
            continue
        standing = [h for h in frozen if h != r.hypothesis_id
                    and question_of[h] == question_of[r.hypothesis_id]
                    and by_id[h].verdict != "refuted"]
        if standing:
            warnings.append(
                f"{r.hypothesis_id} is `supported` but rivals still stand under the same "
                f"question: {standing}. Write down which rivals were refuted, which still fit, "
                f"and what every surviving hypothesis agrees on — and interpret only that.")

    if open_anomalies and concluded:
        return ResolveVerdict("blocked_open_anomaly", [
            f"cannot sign a concluding verdict ({[r.hypothesis_id for r in concluded]}) while "
            f"stage-8 anomalies are open: {open_anomalies}. Get a repair accepted or a "
            f"disposition in /analyze first — concluding over a concern you already raised is "
            f"the most common documented failure (82.5%)."
        ], warnings)

    over = []
    for r in concluded:
        for v in scope_violations(r.claimed_scope, tested_scope):
            over.append(f"{r.hypothesis_id}: {v}")
    if over:
        return ResolveVerdict("blocked_overgeneralized", [
            "conclusions reach past the experiment: " + "; ".join(over) +
            ". Narrow the claim to what you ran — overgeneralization is a named dominant "
            "conclusion-formation failure (FIRE-Bench)."
        ], warnings)

    return ResolveVerdict("resolved", [], warnings, list(by_id.values()))


def handoff_followups(followups: list[FollowUp], *,
                      known_ids: list[str]) -> list[dict]:
    """Hand follow-ups to /plan as CANDIDATES — never as a decision.

    Each must trace to a finding or anomaly id from this run. The returned dicts
    are shaped for planning.Proposal features, and deliberately carry no
    selection: the next run's diversity gate and the Fellow choose, so a run
    cannot quietly set its own successor's agenda (cognitive tunneling across
    runs, not just within one).
    """
    known = set(known_ids)
    out = []
    for f in followups:
        assert f.motivated_by in known, (
            f"follow-up {f.id!r} is motivated by {f.motivated_by!r}, which is not a finding or "
            f"anomaly in this run — a follow-up must trace to evidence, not to a hunch")
        assert f.question.strip(), f"follow-up {f.id!r} has no question"
        assert f.acceptance.strip(), (
            f"follow-up {f.id!r} has no acceptance condition — say what done means when the "
            f"work is filed, as something checkable")
        out.append({"id": f.id, "question": f.question, "motivated_by": f.motivated_by,
                    "acceptance": f.acceptance,
                    "lesson": f.lesson, "selected": False,
                    "route": "/plan — must pass the diversity gate before it becomes a run"})
    return out
