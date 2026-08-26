"""
Diversity-forced experiment planning (MVP-4, pipeline stage 2).

The survey reframes planning as a DIVERSITY problem: proposal entropy correlates
r=0.57 with success (2511.15593). But two hard constraints shape the design:

- Model-ensembling does NOT create diversity — cross-vendor proposal similarity ≈
  intra-vendor (hypothesis-hivemind, 2605.08956). So divergence must be
  human-curated and *forced*, not obtained by asking more models.
- Agents cannot self-select — LLM-judged "innovativeness" correlates -0.06 with
  actual effectiveness (MLRC-Bench). So the PI selects; the tool ranks.

And for alignment specifically (Gap 3, UK AISI): candidates that share a failure
mode produce correlated evidence that does not average out. Planning must surface
and penalise that correlation deliberately.

Division of labour:
- THIS LIBRARY measures diversity, detects correlated-failure-mode clusters,
  scores proposals against a PI-approved rubric, and enforces the gate: a
  homogeneous candidate set is blocked, and selection is refused unless made by
  the human.
- THE /plan skill generates genuinely divergent candidates (human-curated),
  extracts the goal-specific rubric (Rubric-Rewards), scores against it, and
  drives the PI's selection.
"""

import math
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Proposal:
    """One candidate experiment design. `features` are categorical descriptors
    used to measure divergence (e.g. mechanism, method, data source, and — key
    for alignment — the failure mode the design is most vulnerable to)."""
    id: str
    title: str
    features: dict          # feature_key -> categorical value (str)
    rationale: str = ""


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
                     correlated_key: str = "failure_mode", threshold: float = 0.5) -> DiversityReport:
    """Measure how divergent the candidate set is, and flag correlated candidates.

    A candidate set below `threshold` overall entropy is 'insufficient' — the gate
    will demand more divergence rather than let the PI select from near-duplicates.
    """
    assert feature_keys, "need at least one feature key to measure diversity"
    for p in proposals:
        for k in feature_keys:
            assert k in p.features, f"proposal {p.id!r} missing feature {k!r}"

    per_feature = {k: _norm_entropy([p.features[k] for p in proposals]) for k in feature_keys}
    overall = sum(per_feature.values()) / len(per_feature) if per_feature else 0.0

    clusters = []
    if correlated_key in feature_keys or all(correlated_key in p.features for p in proposals):
        by_val = {}
        for p in proposals:
            by_val.setdefault(p.features.get(correlated_key), []).append(p.id)
        clusters = [ids for ids in by_val.values() if len(ids) > 1]

    insufficient = len(proposals) < 2 or overall < threshold
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
              selector: str | None = None) -> PlanVerdict:
    """Enforce diversity-then-human-selection.

    - A homogeneous candidate set is blocked (force divergence first).
    - Selection must be made by the PI; an agent cannot self-select.
    - Selecting only from within one correlated-failure-mode cluster is warned
      (the evidence won't average out — Gap 3), but not blocked: the PI may have a
      reason, they just have to see it.
    """
    if diversity.insufficient:
        return PlanVerdict("insufficient_diversity", warnings=[
            f"overall diversity {diversity.overall:.2f} < threshold {diversity.threshold:.2f} "
            f"over {diversity.n} candidates — generate genuinely divergent designs, "
            f"do not just ask another model (ensembling does not diversify)"])

    if not pi_selection:
        return PlanVerdict("awaiting_pi_selection", warnings=[
            "diversity ok — the PI must select; agents cannot self-select "
            "(LLM innovativeness correlates -0.06 with real effectiveness)"])

    assert selector == "pi", (
        f"selection must be made by the PI, not by {selector!r} — agents cannot "
        f"self-select proposals (MLRC-Bench)"
    )

    warnings = []
    chosen = set(pi_selection)
    if len(chosen) > 1:
        for cluster in diversity.correlated_clusters:
            if chosen.issubset(set(cluster)):
                warnings.append(
                    "all selected candidates share a failure mode — their evidence is "
                    "correlated and will not average out (Gap 3); consider diversifying")
    return PlanVerdict("selected", warnings=warnings, selected=list(pi_selection))
