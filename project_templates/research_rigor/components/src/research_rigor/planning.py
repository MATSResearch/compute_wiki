"""
Diversity-forced experiment planning (choosing a direction; stage `design`).

Generate several candidate designs that differ in MECHANISM, not in
hyperparameters, and record for each the FAILURE MODE it is most vulnerable to.
Then choose under the project's delegation arrangement.

Two empirical cautions from the cited systems shape the checks:

- Asking more models does not guarantee diversity — cross-vendor proposal
  similarity ≈ intra-vendor (hypothesis-hivemind, 2605.08956). Divergence has to
  be curated deliberately.
- Self-ranking needs evidence — LLM-judged "innovativeness" correlated -0.06
  with effectiveness in the MLRC-Bench setting. That is a reason to validate the
  selection method, not a permanent prohibition on delegation: `plan_gate`
  preserves human selection by default, and an application passes
  `agent_selection_authorized=True` after the researcher delegates selection.
  The flag records authorization, not model competence.

And for alignment specifically: candidates that share a failure mode produce
correlated evidence that does not average out. Three experiments that would all
be fooled by the same confound are one experiment.

Division of labour:
- THIS LIBRARY measures diversity, detects correlated-failure-mode clusters,
  scores proposals against a PI-approved rubric, and holds the gate: a
  homogeneous candidate set is blocked, and a selection needs the researcher or
  the researcher's recorded delegation.
- THE /plan skill generates genuinely divergent candidates, extracts the
  goal-specific rubric (Rubric-Rewards), scores against it, and drives the
  selection.

Force diversity when choosing a DIRECTION, not every time something runs: with
one obvious next experiment and a known reason, there is nothing to gate.
"""

import math
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Proposal:
    """One candidate experiment design. `features` are categorical descriptors
    used to measure divergence. Two are required of every candidate: its
    `mechanism`, and the `failure_mode` it is most vulnerable to."""
    id: str
    title: str
    features: dict          # feature_key -> categorical value (str)
    rationale: str = ""


REQUIRED_FEATURES = ("mechanism", "failure_mode")


@dataclass
class DiversityReport:
    n: int
    per_feature_entropy: dict            # feature_key -> normalized entropy [0,1]
    overall: float                       # mean normalized entropy
    correlated_clusters: list            # groups (>1) of proposal ids sharing the correlated key
    insufficient: bool
    threshold: float


def _norm_entropy(values: list) -> float:
    """Shannon entropy normalized to [0,1] (max = all-distinct)."""
    n = len(values)
    if n <= 1:
        return 0.0
    counts = Counter(values)
    h = -sum((c / n) * math.log(c / n) for c in counts.values())
    return h / math.log(n)


def diversity_report(proposals: list[Proposal], feature_keys: list[str],
                     threshold: float = 0.5) -> DiversityReport:
    """Measure how divergent the candidate set is, and flag correlated candidates.

    A candidate set is 'insufficient' below `threshold` overall entropy, or when
    every candidate shares one mechanism (they differ only in hyperparameters) —
    the gate will demand more divergence rather than a pick among near-duplicates.
    """
    assert feature_keys, "need at least one feature key to measure diversity"
    for p in proposals:
        for k in (*feature_keys, *REQUIRED_FEATURES):
            assert k in p.features, f"proposal {p.id!r} missing feature {k!r}"

    per_feature = {k: _norm_entropy([p.features[k] for p in proposals]) for k in feature_keys}
    overall = sum(per_feature.values()) / len(per_feature) if per_feature else 0.0

    by_failure_mode = {}
    for p in proposals:
        by_failure_mode.setdefault(p.features["failure_mode"], []).append(p.id)
    clusters = [ids for ids in by_failure_mode.values() if len(ids) > 1]

    one_mechanism = len({p.features["mechanism"] for p in proposals}) < 2
    insufficient = one_mechanism or overall < threshold
    return DiversityReport(n=len(proposals), per_feature_entropy=per_feature, overall=overall,
                           correlated_clusters=clusters, insufficient=insufficient, threshold=threshold)


# --- rubric scoring (PI-approved; ranks, never selects) ----------------------

@dataclass
class Criterion:
    name: str
    weight: float
    description: str = ""


@dataclass
class Rubric:
    """Goal-specific evaluation rubric (Rubric-Rewards). Auto-extracted from the
    research goal, but the human approves it before it is used to score."""
    criteria: list[Criterion]
    approved_by_pi: bool = False


@dataclass
class RankedProposal:
    proposal_id: str
    score: float
    breakdown: dict


def score_proposals(rubric: Rubric, proposals: list[Proposal], scores: dict) -> list[RankedProposal]:
    """Weighted rubric score per proposal, returned as a RANKING — explicitly not
    a selection. `scores` is {proposal_id: {criterion_name: value}}."""
    assert rubric.approved_by_pi, (
        "rubric must be PI-approved before scoring (Rubric-Rewards: the human "
        "approves the rubric; the tool does not grade on an unapproved one)"
    )
    assert rubric.criteria, "rubric has no criteria"
    ranked = []
    for p in proposals:
        s = scores.get(p.id, {})
        breakdown = {c.name: c.weight * float(s.get(c.name, 0.0)) for c in rubric.criteria}
        ranked.append(RankedProposal(p.id, sum(breakdown.values()), breakdown))
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked


# --- the gate: PI selects from a diverse set ---------------------------------

@dataclass
class PlanVerdict:
    verdict: str          # "insufficient_diversity" | "awaiting_pi_selection" | "selected"
    warnings: list = field(default_factory=list)
    selected: list = field(default_factory=list)


def plan_gate(diversity: DiversityReport, *, pi_selection: list | None,
              selector: str | None = None,
              agent_selection_authorized: bool = False) -> PlanVerdict:
    """Enforce diversity, then selection under the delegation arrangement.

    - A homogeneous candidate set is blocked (force divergence first).
    - Selection defaults to the PI. Explicit researcher authorization permits
      an agent selector; the flag is supplied by the calling application, not
      inferred from the agent’s confidence.
    - Selecting only from within one correlated-failure-mode cluster is warned
      (the evidence won't average out), but not blocked: the selector may have a
      reason, they just have to see it.
    """
    if diversity.insufficient:
        return PlanVerdict("insufficient_diversity", warnings=[
            f"overall diversity {diversity.overall:.2f} < threshold {diversity.threshold:.2f} "
            f"over {diversity.n} candidates — generate genuinely divergent designs, "
            f"do not just ask another model (ensembling does not diversify)"])

    if not pi_selection:
        return PlanVerdict("awaiting_pi_selection", warnings=[
            "diversity ok — awaiting a selection under the researcher’s delegation arrangement"])

    assert selector == "pi" or (selector == "agent" and agent_selection_authorized is True), (
        f"selection by {selector!r} requires researcher authorization; "
        "pass agent_selection_authorized=True only when selection was delegated"
    )

    warnings = []
    chosen = set(pi_selection)
    if len(chosen) > 1:
        for cluster in diversity.correlated_clusters:
            if chosen.issubset(set(cluster)):
                warnings.append(
                    "all selected candidates share a failure mode — their evidence is "
                    "correlated and will not average out; consider diversifying")
    return PlanVerdict("selected", warnings=warnings, selected=list(pi_selection))
