"""
Supervision attention-check injector + scorer (MVP-1.5, pipeline Gap 8).

Verifies the human overseer, not the AI. Seeds a Fellow's review stream with
ground-truthed fake errors drawn from the real AI-mistake distribution; a
rate-based miss escalates to the MATS Research Manager — whose role is
*explicitly non-judgemental* (a coach, not an evaluator), which is what makes an
imperfect detector safe to run. Full design: the mats_dashboards repo,
docs/auto_alignment_research/supervision_attention_checks.md.

Division of labour (so we never hardcode an LLM call):
- THIS LIBRARY is deterministic scaffolding — the seed-hashed injection decision,
  separability of injected artifacts, stratified scoring, and rate-based
  escalation. All reproducible and auditable.
- THE /attention-check SKILL supplies the intelligence — authoring corrupted
  content that is indistinguishable from real work (requirement 1), modelled on a
  real mistake sampled from provenance. It passes the authored artifact + ground
  truth to register().

Injection is decided by hashing a per-Fellow SECRET SEED with the gate key: the
Fellow can't predict which gate is seeded (unpredictable), yet an auditor with
the seed can reproduce every decision (auditable). This is the seed-driven,
contamination-resistant pattern from the landscape survey.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from .run_dir import DIFFICULTIES, ERROR_TYPES, RunDir, _append_jsonl

# Missing a blatant error signals rubber-stamping far more than missing a subtle
# one, so easy misses drag the escalation metric down hardest.
DIFFICULTY_WEIGHT = {"easy": 1.0, "medium": 0.7, "hard": 0.4}


def _unit(seed: str, *parts) -> float:
    """Deterministic pseudo-random float in [0,1) from a seed and key parts."""
    key = seed + "|" + "|".join(str(p) for p in parts)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) / float(1 << 64)


@dataclass
class InjectionPlan:
    """What to inject at a gate. `kind` is 'defect' (seed a fake error) or
    'control' (present a correct item to measure false-positives, requirement 4)."""
    kind: str                       # "defect" | "control"
    error_type: str | None          # None for controls
    difficulty: str
    source_provenance_event: str | None
    nonce: str                      # ties the plan to its seed draw, for audit


def plan_injection(*, seed: str, run_id: str, gate_ordinal: int, rate: float,
                   mistake_catalog: list[dict], two_sided_rate: float = 0.2) -> InjectionPlan | None:
    """Decide (deterministically, unpredictably to the Fellow) whether to seed
    this gate, and if so what to seed.

    mistake_catalog: real mistakes sampled from provenance across past runs, each
      a dict {error_type, difficulty, source_provenance_event?}. Grounds the
      defect in the real distribution (requirement 1). If empty, defects fall back
      to the ERROR_TYPES catalog at uniform difficulty.
    """
    assert 0.0 <= rate <= 1.0, "rate must be in [0,1]"
    assert 0.0 <= two_sided_rate <= 1.0, "two_sided_rate must be in [0,1]"
    if _unit(seed, run_id, gate_ordinal, "inject") >= rate:
        return None

    nonce = hashlib.sha256(f"{seed}|{run_id}|{gate_ordinal}".encode()).hexdigest()[:12]

    if _unit(seed, run_id, gate_ordinal, "control") < two_sided_rate:
        # A correct item, seeded to catch a Fellow who flags everything.
        d_idx = int(_unit(seed, run_id, gate_ordinal, "cdiff") * len(DIFFICULTIES))
        return InjectionPlan(kind="control", error_type=None,
                             difficulty=DIFFICULTIES[d_idx],
                             source_provenance_event=None, nonce=nonce)

    if mistake_catalog:
        idx = int(_unit(seed, run_id, gate_ordinal, "pick") * len(mistake_catalog))
        m = mistake_catalog[idx]
        error_type = m["error_type"]
        difficulty = m.get("difficulty") or DIFFICULTIES[int(_unit(seed, run_id, gate_ordinal, "diff") * len(DIFFICULTIES))]
        source = m.get("source_provenance_event")
        assert error_type in ERROR_TYPES, f"catalog error_type {error_type!r} not in {ERROR_TYPES}"
    else:
        error_type = ERROR_TYPES[int(_unit(seed, run_id, gate_ordinal, "etype") * len(ERROR_TYPES))]
        difficulty = DIFFICULTIES[int(_unit(seed, run_id, gate_ordinal, "diff") * len(DIFFICULTIES))]
        source = None

    return InjectionPlan(kind="defect", error_type=error_type, difficulty=difficulty,
                         source_provenance_event=source, nonce=nonce)


def register(rd: RunDir, plan: InjectionPlan, *, stage: str, injected_into_gate: str,
             ground_truth: str, corrupted_artifact: str | None = None,
             correct_version: str | None = None) -> str:
    """Log the seeded check and store its content SEPARATELY (requirement 5) so a
    fake error can never contaminate real results/writeup. Returns the ac_id."""
    ac_id = rd.log_attention_check(
        stage=stage, injected_into_gate=injected_into_gate,
        error_type=plan.error_type, difficulty=plan.difficulty,
        ground_truth=ground_truth,
        source_provenance_event=plan.source_provenance_event,
        two_sided_control=(plan.kind == "control"),
    )
    # Injected artifacts live in a quarantined dir, never in results/ or writeup/.
    staging = rd.path / "attention_checks" / ac_id
    staging.mkdir(parents=True, exist_ok=True)
    if corrupted_artifact is not None:
        (staging / "shown_to_reviewer.txt").write_text(corrupted_artifact)
    if correct_version is not None:
        (staging / "correct_version.txt").write_text(correct_version)
    (staging / "meta.txt").write_text(
        f"kind={plan.kind}\nerror_type={plan.error_type}\ndifficulty={plan.difficulty}\n"
        f"nonce={plan.nonce}\nground_truth={ground_truth}\n"
    )
    return ac_id


def record_outcome(rd: RunDir, ac_id: str, *, flagged: bool) -> None:
    """Record whether the Fellow flagged the item as suspect. For a defect,
    flagged=True is a good catch; for a control, flagged=True is a false positive."""
    rd.resolve_attention_check(ac_id, caught=flagged)


# --- scoring -----------------------------------------------------------------

def load_checks(rd: RunDir) -> list[dict]:
    """Fold append-only original+resolution lines into one record per ac_id."""
    checks: dict[str, dict] = {}
    for r in rd.read_log(rd.attention_checks_path):
        ac_id = r["ac_id"]
        if r.get("event") == "resolution":
            assert ac_id in checks, f"resolution for unknown check {ac_id}"
            checks[ac_id]["caught"] = r["caught"]
        else:
            checks[ac_id] = dict(r)
    return list(checks.values())


@dataclass
class CalibrationStats:
    n_defects: int = 0
    n_controls: int = 0
    catch_rate: float = 0.0            # unweighted: caught defects / defects
    weighted_catch_rate: float = 0.0   # difficulty-weighted (easy misses cost most)
    fp_rate: float = 0.0               # flagged controls / controls
    by_type: dict = field(default_factory=dict)        # error_type -> catch rate
    by_difficulty: dict = field(default_factory=dict)  # difficulty -> catch rate


def _rate(items: list[bool]) -> float:
    return sum(items) / len(items) if items else 0.0


def score(checks: list[dict], window: int | None = None) -> CalibrationStats:
    """Stratified catch-rate + false-positive rate over resolved checks
    (requirements 3 & 4). `window` restricts to the most recent N resolved checks."""
    resolved = [c for c in checks if c.get("caught") is not None]
    if window is not None:
        resolved = resolved[-window:]

    defects = [c for c in resolved if not c.get("two_sided_control")]
    controls = [c for c in resolved if c.get("two_sided_control")]

    stats = CalibrationStats(n_defects=len(defects), n_controls=len(controls))
    stats.catch_rate = _rate([bool(c["caught"]) for c in defects])
    stats.fp_rate = _rate([bool(c["caught"]) for c in controls])

    num = sum(DIFFICULTY_WEIGHT[c["difficulty"]] * bool(c["caught"]) for c in defects)
    den = sum(DIFFICULTY_WEIGHT[c["difficulty"]] for c in defects)
    stats.weighted_catch_rate = num / den if den else 0.0

    for et in sorted({c["error_type"] for c in defects if c.get("error_type")}):
        grp = [bool(c["caught"]) for c in defects if c.get("error_type") == et]
        stats.by_type[et] = _rate(grp)
    for d in DIFFICULTIES:
        grp = [bool(c["caught"]) for c in defects if c["difficulty"] == d]
        if grp:
            stats.by_difficulty[d] = _rate(grp)
    return stats


# --- escalation (rate-based, to a non-judgemental coach) ---------------------

@dataclass
class EscalationConfig:
    window: int = 20
    min_defects: int = 8          # need enough seeded errors to estimate a rate (req 2)
    min_controls: int = 5
    catch_threshold: float = 0.6  # escalate if weighted catch-rate falls below this
    fp_threshold: float = 0.3     # escalate if the Fellow flags too many correct items


@dataclass
class EscalationDecision:
    escalate: bool
    reasons: list[str]
    stats: CalibrationStats


def evaluate_escalation(stats: CalibrationStats, cfg: EscalationConfig) -> EscalationDecision:
    """Decide on a RATE over a window (never a single miss, requirement 2)."""
    reasons = []
    if stats.n_defects >= cfg.min_defects and stats.weighted_catch_rate < cfg.catch_threshold:
        reasons.append(
            f"weighted catch-rate {stats.weighted_catch_rate:.0%} is below the "
            f"{cfg.catch_threshold:.0%} bar over {stats.n_defects} seeded errors"
        )
    if stats.n_controls >= cfg.min_controls and stats.fp_rate > cfg.fp_threshold:
        reasons.append(
            f"false-positive rate {stats.fp_rate:.0%} exceeds {cfg.fp_threshold:.0%} "
            f"({stats.n_controls} correct items shown) — flagging sound work, not reviewing"
        )
    return EscalationDecision(escalate=bool(reasons), reasons=reasons, stats=stats)


def render_escalation(decision: EscalationDecision, *, fellow: str,
                      research_manager: str = "the MATS Research Manager") -> str:
    """A coaching-framed note to the non-judgemental RM. NEVER a performance
    verdict — the whole design rests on the signal being decoupled from
    evaluation (mats_dashboards repo, docs/auto_alignment_research/
    supervision_attention_checks.md, 'Why the non-judgemental RM matters')."""
    s = decision.stats
    lines = [
        f"Attention-check check-in for {fellow} → {research_manager}",
        "",
        "This is calibration information for a supportive conversation, NOT an",
        "evaluation of performance and NOT input to any funding or acclaim decision.",
        "A flag means 'worth a low-stakes chat', e.g. about review fatigue or pacing.",
        "",
        f"Over the recent window: {s.n_defects} seeded errors, {s.n_controls} correct controls.",
        f"  weighted catch-rate: {s.weighted_catch_rate:.0%}  (unweighted {s.catch_rate:.0%})",
        f"  false-positive rate: {s.fp_rate:.0%}",
    ]
    if s.by_difficulty:
        lines.append("  by difficulty: " + ", ".join(f"{d} {r:.0%}" for d, r in s.by_difficulty.items()))
    if s.by_type:
        lines.append("  by error type: " + ", ".join(f"{t} {r:.0%}" for t, r in s.by_type.items()))
    lines.append("")
    if decision.escalate:
        lines.append("Why this surfaced now:")
        lines += [f"  - {r}" for r in decision.reasons]
        lines += [
            "",
            "Suggested framing for the check-in: this is almost always load, not",
            "carelessness — a reviewer drowning in fluent AI output drifts into",
            "rubber-stamping. Useful directions: lighten the review queue, slow down",
            "on the weak-spot categories above, or pair-review the hard ones.",
        ]
    else:
        lines.append("No escalation — calibration is within bounds. Shown for transparency.")
    return "\n".join(lines)
