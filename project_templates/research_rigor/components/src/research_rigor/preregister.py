"""
Pre-registration freeze/check tool — the commitment device.

Pre-registration happens at TWO points, on either side of the pilot (stages
`hypothesis` and `design` of the wiki's eleven):

  hypothesis  the hypothesis (`statement`), the `prediction` and the `falsifier`,
              frozen before the confirmatory test — before the pilot.
  design      the metric, decision rule and method (`analysis`), the
              `prespecified_confounds`, and a guard for each measure (`guards`),
              frozen after the pilot and before the main run.

The pilot does not license rewriting the hypothesis or the falsifier: freezing
`design` re-checks the `hypothesis` hash and refuses if it moved. A changed
belief is a new registered prediction, so it goes in a new run directory's
prereg.yaml with its own two freezes; the old prediction keeps its record and
gets its own verdict.

Two subcommands:

  freeze  Lock one commitment point of a drafted prereg.yaml: validate that
          point's fields, hash them, stamp frozen_at, and (optionally) git-commit
          so the commitment is tamper-evident and provably predates the results
          it governs. Gaps the wiki asks you to see — a question with only one
          hypothesis, a hypothesis no planned run tests — are printed as notes;
          they never refuse the freeze.

  check   At analysis time, verify neither commitment was tampered with and
          diff the ACTUAL analysis against the frozen plan, flagging any metric,
          decision rule, or method that changed after freezing.

This is intentionally NOT an LLM call — it is deterministic bookkeeping. The
human writes the science; this tool only makes the commitment enforceable.

Usage (installed as the `research-rigor-prereg` console script):
    research-rigor-prereg freeze  <run_dir>/prereg.yaml --point hypothesis [--git-commit]
    research-rigor-prereg freeze  <run_dir>/prereg.yaml --point design [--git-commit]
    research-rigor-prereg check   <run_dir>/prereg.yaml --actual <run_dir>/analysis/actual_analysis.yaml

Schema: templates/schemas.md · Template: templates/prereg.template.yaml
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

from .run_dir import PREREG_POINTS as POINTS
from .run_dir import _now_iso

# Template placeholders are angle-bracket-wrapped descriptions like
# "<name_of_metric>". A real comparison in a decision rule ("<0.1 => refuted")
# always has a digit or "=" inside the brackets, so requiring the inner text to
# contain none of <>=0-9 distinguishes an unfilled placeholder from real content.
_PLACEHOLDER_RE = re.compile(r"<[^<>=0-9]+>")


def _is_placeholder(val) -> bool:
    return bool(_PLACEHOLDER_RE.search(str(val)))

# The `hypothesis` commitment: what is claimed, what would be seen if it is true,
# and what result would show it false.
HYPOTHESIS_FIELDS = ("statement", "prediction", "falsifier")

# The `design` commitment. A post-freeze change to any `analysis` field is a
# p-hacking risk and is surfaced by `check`.
FROZEN_ANALYSIS_FIELDS = ("metric", "decision_rule", "method")
# A guard names a measure, the cheap way that number could move without the
# claim being true, and the check that would catch it.
GUARD_FIELDS = ("measure", "cheap_way", "check")

EXPLORATION = "exploration"   # what a planned run that tests no hypothesis says it is


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"file not found: {path}"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"{path} must be a YAML mapping, got {type(data).__name__}"
    return data


def _hypotheses(prereg: dict) -> list:
    hyps = prereg.get("hypotheses")
    assert isinstance(hyps, list) and hyps, "prereg must have a non-empty `hypotheses` list"
    seen = set()
    for i, h in enumerate(hyps):
        assert isinstance(h, dict), f"hypotheses[{i}] must be a mapping"
        assert h.get("id"), f"hypotheses[{i}] missing `id`"
        assert h["id"] not in seen, f"duplicate hypothesis id: {h['id']}"
        seen.add(h["id"])
    return hyps


def _require(mapping: dict, fields: tuple, where: str) -> None:
    for field in fields:
        val = mapping.get(field)
        assert val and str(val).strip() and not _is_placeholder(val), \
            f"{where} missing/placeholder `{field}`"


def commitment_hash(prereg: dict, point: str) -> str:
    """sha256 over the canonical serialization of ONE commitment point.

    Only that point's scientific commitment is hashed — the other point,
    freeze-managed bookkeeping and amendments are excluded, so the `hypothesis`
    hash is unchanged by filling in the design after the pilot.
    """
    assert point in POINTS, f"unknown commitment point {point!r} (one of {POINTS})"
    if point == "hypothesis":
        committed = [{"id": h["id"], **{f: h.get(f) for f in HYPOTHESIS_FIELDS}}
                     for h in _hypotheses(prereg)]
    else:
        committed = [{"id": h["id"], "analysis": h.get("analysis"),
                      "prespecified_confounds": h.get("prespecified_confounds"),
                      "guards": h.get("guards")} for h in _hypotheses(prereg)]
    canonical = json.dumps(committed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_draft(prereg: dict, point: str) -> None:
    """Assert one commitment point of a drafted prereg is complete enough to
    freeze. Fail loudly."""
    assert point in POINTS, f"unknown commitment point {point!r} (one of {POINTS})"
    for i, h in enumerate(_hypotheses(prereg)):
        loc = f"hypotheses[{i}] ({h['id']})"
        if point == "hypothesis":
            _require(h, ("question",) + HYPOTHESIS_FIELDS, loc)
            for j, rival in enumerate(h.get("rivals_declined") or []):
                _require(rival, ("rival", "reason"), f"{loc} rivals_declined[{j}]")
            continue

        analysis = h.get("analysis")
        assert isinstance(analysis, dict), f"{loc} missing `analysis` block"
        _require(analysis, FROZEN_ANALYSIS_FIELDS, f"{loc} analysis")

        confounds = h.get("prespecified_confounds")
        assert isinstance(confounds, list) and confounds, \
            f"{loc} needs a non-empty `prespecified_confounds` list"
        for c in confounds:
            assert str(c).strip() and not _is_placeholder(c), \
                f"{loc} missing/placeholder entry in `prespecified_confounds`"

        guards = h.get("guards")
        assert isinstance(guards, list) and guards, f"{loc} needs a non-empty `guards` list"
        for j, g in enumerate(guards):
            assert isinstance(g, dict), f"{loc} guards[{j}] must be a mapping"
            _require(g, GUARD_FIELDS, f"{loc} guards[{j}]")
        guarded = {str(g["measure"]).strip() for g in guards}
        assert str(analysis["metric"]).strip() in guarded, (
            f"{loc} has no guard for its metric {analysis['metric']!r} — every measure needs "
            f"the cheap way it could move without the claim being true, and the check for it")


def rival_gaps(prereg: dict) -> list[str]:
    """Questions that have only one answer waiting to be confirmed.

    A question is covered by two hypotheses that predict different observations,
    or by a rival recorded as weighed and declined with a reason. Returned as
    notes: a gap describes the record and never refuses a freeze.
    """
    by_question: dict = {}
    for h in _hypotheses(prereg):
        by_question.setdefault(str(h.get("question")).strip(), []).append(h)
    gaps = []
    for question, hyps in by_question.items():
        predictions = {str(h.get("prediction")).strip() for h in hyps}
        if len(predictions) >= 2 or any(h.get("rivals_declined") for h in hyps):
            continue
        ids = [h["id"] for h in hyps]
        gaps.append(
            f"question {question!r} has only one distinct prediction ({ids}) — add a rival "
            f"hypothesis that predicts a different observation, or record the rival you "
            f"weighed under `rivals_declined` with the reason")
    return gaps


def route_gaps(prereg: dict) -> list[str]:
    """Hypotheses with no planned run to decide them, and planned runs that
    test nothing on the record. Notes, never a refusal."""
    ids = [h["id"] for h in _hypotheses(prereg)]
    runs = prereg.get("planned_runs") or []
    for i, r in enumerate(runs):
        assert isinstance(r, dict) and r.get("id"), f"planned_runs[{i}] needs an `id`"
    tested = {r.get("tests") for r in runs}
    gaps = [f"hypothesis {hid} has no planned run that tests it — a claim with no route to a verdict"
            for hid in ids if hid not in tested]
    gaps += [f"planned run {r['id']!r} tests {r.get('tests')!r}, which is not a registered "
             f"hypothesis — say `tests: {EXPLORATION}`, or register the hypothesis nobody wrote down"
             for r in runs if r.get("tests") != EXPLORATION and r.get("tests") not in ids]
    return gaps


def _commitments(prereg: dict) -> dict:
    return prereg.get("commitments") or {}


def _tampered(prereg: dict, point: str) -> tuple[str, str] | None:
    """(stored, recomputed) if a frozen point no longer hashes to its stored value."""
    stored = _commitments(prereg)[point]["content_hash"]
    recomputed = commitment_hash(prereg, point)
    return None if recomputed == stored else (stored, recomputed)


def freeze(prereg_path: Path, point: str, git_commit: bool, force: bool) -> None:
    prereg = _load_yaml(prereg_path)
    commitments = _commitments(prereg)

    already = commitments.get(point)
    assert not already or force, (
        f"`{point}` commitment already frozen at {already and already['frozen_at']}. To change a "
        f"frozen prereg add an `amendments` entry; use --force only to re-freeze a draft you "
        f"never committed."
    )
    if point == "design":
        assert commitments.get("hypothesis"), (
            "freeze the `hypothesis` commitment first (--point hypothesis): the design is "
            "committed after the pilot, for a prediction and falsifier recorded before it")
        assert not _tampered(prereg, "hypothesis"), (
            "a hypothesis, prediction or falsifier was edited, added or removed since the "
            "`hypothesis` freeze. The pilot does not license rewriting them: restore the frozen "
            "text, keep the old prediction (it still gets a verdict), and register a new "
            "prediction in a new run directory's prereg.yaml, frozen at its own `hypothesis` "
            "point.")

    validate_draft(prereg, point)
    gaps = rival_gaps(prereg) if point == "hypothesis" else route_gaps(prereg)

    commitments[point] = {"frozen_at": _now_iso(), "content_hash": commitment_hash(prereg, point)}
    prereg["commitments"] = commitments

    with open(prereg_path, "w") as f:
        yaml.safe_dump(prereg, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    print(f"✓ Frozen `{point}` commitment in {prereg_path}", file=sys.stderr)
    print(f"  frozen_at:    {commitments[point]['frozen_at']}", file=sys.stderr)
    print(f"  content_hash: {commitments[point]['content_hash']}", file=sys.stderr)
    for gap in gaps:
        print(f"  note: {gap}", file=sys.stderr)

    if git_commit:
        run_id = prereg.get("run_id", prereg_path.parent.name)
        subprocess.run(["git", "add", str(prereg_path)], check=True)
        msg = (f"Freeze {point} pre-registration for {run_id} "
               f"({commitments[point]['content_hash'][:19]}…)")
        subprocess.run(["git", "commit", "-m", msg], check=True)
        print("  git: committed (commit timestamp is the tamper-evidence anchor)", file=sys.stderr)
    else:
        print("  NOTE: commit prereg.yaml now so its timestamp provably predates the results it governs:", file=sys.stderr)
        print(f"        git add {prereg_path} && git commit -m 'Freeze {point} prereg'", file=sys.stderr)


def check(prereg_path: Path, actual_path: Path) -> int:
    prereg = _load_yaml(prereg_path)
    commitments = _commitments(prereg)
    for point in POINTS:
        assert commitments.get(point), \
            f"`{point}` commitment is not frozen — run `freeze --point {point}` before `check`"

    # 1. Tamper check: each commitment must still hash to its stored value.
    for point in POINTS:
        mismatch = _tampered(prereg, point)
        if mismatch:
            print(f"✗ TAMPER DETECTED: the `{point}` commitment no longer matches its content_hash.", file=sys.stderr)
            print(f"    stored:     {mismatch[0]}", file=sys.stderr)
            print(f"    recomputed: {mismatch[1]}", file=sys.stderr)
            print("    A frozen prereg was edited without an amendment. This is a hard stop.", file=sys.stderr)
            return 2

    # 2. Deviation check: actual analysis vs frozen plan, per hypothesis.
    actual = _load_yaml(actual_path)
    actual_by_id = actual.get("hypotheses", actual)  # accept either {hypotheses:{...}} or flat map
    assert isinstance(actual_by_id, dict), \
        "actual analysis must map hypothesis id -> {metric, decision_rule, method, ...}"

    deviations = []
    for h in prereg["hypotheses"]:
        hid = h["id"]
        frozen_analysis = h["analysis"]
        act = actual_by_id.get(hid)
        if act is None:
            deviations.append(f"[{hid}] no actual analysis reported for a pre-registered hypothesis")
            continue
        for field in FROZEN_ANALYSIS_FIELDS:
            fv, av = frozen_analysis.get(field), act.get(field)
            if av is not None and str(av).strip() != str(fv).strip():
                deviations.append(
                    f"[{hid}] `{field}` deviates from prereg:\n"
                    f"        frozen: {fv}\n"
                    f"        actual: {av}"
                )

    frozen_at = commitments["design"]["frozen_at"]
    if not deviations:
        print(f"✓ Analysis matches the design frozen at {frozen_at}.", file=sys.stderr)
        print("  (No metric / decision_rule / method drift.)", file=sys.stderr)
        return 0

    print(f"⚠ {len(deviations)} deviation(s) from the pre-registration — report these with the analysis:", file=sys.stderr)
    for d in deviations:
        print(f"  - {d}", file=sys.stderr)
    print("\n  Deviations are not forbidden — they must be VISIBLE. Record each legitimate one", file=sys.stderr)
    print("  as an `amendments` entry with justification; treat unexplained ones as p-hacking risk.", file=sys.stderr)
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-registration freeze/check tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_freeze = sub.add_parser("freeze", help="Lock one commitment point of a drafted prereg.yaml")
    p_freeze.add_argument("prereg", type=Path)
    p_freeze.add_argument("--point", choices=POINTS, required=True,
                          help="hypothesis: before the pilot. design: after it, before the main run")
    p_freeze.add_argument("--git-commit", action="store_true",
                          help="git add + commit the frozen file (the timestamp is the tamper-evidence anchor)")
    p_freeze.add_argument("--force", action="store_true",
                          help="re-freeze a draft that was never committed (does NOT override an amendment)")

    p_check = sub.add_parser("check", help="Diff actual analysis vs the frozen prereg")
    p_check.add_argument("prereg", type=Path)
    p_check.add_argument("--actual", type=Path, required=True,
                         help="YAML mapping hypothesis id -> {metric, decision_rule, method, ...}")

    args = parser.parse_args()

    # Validation failures are legitimate user-input rejections, not code bugs:
    # surface the assertion's message in full (no hiding) but skip the traceback.
    try:
        if args.cmd == "freeze":
            freeze(args.prereg, args.point, git_commit=args.git_commit, force=args.force)
        elif args.cmd == "check":
            sys.exit(check(args.prereg, args.actual))
    except AssertionError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
