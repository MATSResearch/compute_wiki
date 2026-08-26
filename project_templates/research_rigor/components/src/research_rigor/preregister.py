# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Pre-registration freeze/check tool — the commitment device (pipeline Gap 1).

The deterministic core of MVP-1. Two subcommands:

  freeze  Lock a drafted prereg.yaml: validate it, hash the hypotheses block,
          stamp frozen_at, and (optionally) git-commit so the commitment is
          tamper-evident and provably predates any results.

  check   At analysis time, verify the frozen file hasn't been tampered with and
          diff the ACTUAL analysis against the frozen plan, flagging any metric,
          decision rule, or method that changed after freezing.

This is intentionally NOT an LLM call — it is deterministic bookkeeping. The
human writes the science; this tool only makes the commitment enforceable.

Usage:
    uv run src/preregister.py freeze  <run_dir>/prereg.yaml [--git-commit]
    uv run src/preregister.py check   <run_dir>/prereg.yaml --actual <run_dir>/analysis/actual_analysis.yaml

Schema: docs/schemas.md · Template: templates/run_dir/prereg.template.yaml
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Template placeholders are angle-bracket-wrapped descriptions like
# "<name_of_metric>". A real comparison in a decision rule ("<0.1 => refuted")
# always has a digit or "=" inside the brackets, so requiring the inner text to
# contain none of <>=0-9 distinguishes an unfilled placeholder from real content.
_PLACEHOLDER_RE = re.compile(r"<[^<>=0-9]+>")


def _is_placeholder(val) -> bool:
    return bool(_PLACEHOLDER_RE.search(str(val)))

# Fields inside each hypothesis' `analysis` block that constitute the frozen
# commitment. A post-freeze change to any of these is a p-hacking risk and must
# be surfaced at the analysis gate.
FROZEN_ANALYSIS_FIELDS = ("metric", "decision_rule", "method")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"file not found: {path}"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"{path} must be a YAML mapping, got {type(data).__name__}"
    return data


def hypotheses_hash(prereg: dict) -> str:
    """sha256 over the canonical serialization of the hypotheses block.

    Only the scientific commitment is hashed — freeze-managed bookkeeping
    (frozen_at, content_hash, amendments) is excluded so the hash is stable
    across freezing and reproducible at check time.
    """
    hyps = prereg.get("hypotheses")
    assert hyps, "prereg has no `hypotheses` — nothing to commit to"
    canonical = json.dumps(hyps, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_draft(prereg: dict) -> None:
    """Assert a drafted prereg is complete enough to freeze. Fail loudly."""
    hyps = prereg.get("hypotheses")
    assert isinstance(hyps, list) and hyps, "prereg must have a non-empty `hypotheses` list"
    seen_ids = set()
    for i, h in enumerate(hyps):
        loc = f"hypotheses[{i}]"
        assert isinstance(h, dict), f"{loc} must be a mapping"
        hid = h.get("id")
        assert hid, f"{loc} missing `id`"
        assert hid not in seen_ids, f"duplicate hypothesis id: {hid}"
        seen_ids.add(hid)
        for field in ("statement", "prediction"):
            val = h.get(field)
            assert val and str(val).strip() and not _is_placeholder(val), \
                f"{loc} ({hid}) missing/placeholder `{field}`"
        analysis = h.get("analysis")
        assert isinstance(analysis, dict), f"{loc} ({hid}) missing `analysis` block"
        for field in FROZEN_ANALYSIS_FIELDS:
            val = analysis.get(field)
            assert val and str(val).strip() and not _is_placeholder(val), \
                f"{loc} ({hid}) analysis missing/placeholder `{field}`"


def freeze(prereg_path: Path, git_commit: bool, force: bool) -> None:
    prereg = _load_yaml(prereg_path)

    already = prereg.get("frozen_at")
    assert not already or force, (
        f"prereg already frozen at {already}. To change a frozen prereg add an "
        f"`amendments` entry; use --force only to re-freeze a draft you never committed."
    )

    validate_draft(prereg)

    prereg["content_hash"] = hypotheses_hash(prereg)
    prereg["frozen_at"] = _now_iso()
    prereg["registered_before_data"] = True

    with open(prereg_path, "w") as f:
        yaml.safe_dump(prereg, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    print(f"✓ Frozen {prereg_path}", file=sys.stderr)
    print(f"  frozen_at:    {prereg['frozen_at']}", file=sys.stderr)
    print(f"  content_hash: {prereg['content_hash']}", file=sys.stderr)

    if git_commit:
        run_id = prereg.get("run_id", prereg_path.parent.name)
        subprocess.run(["git", "add", str(prereg_path)], check=True)
        msg = f"Freeze pre-registration for {run_id} ({prereg['content_hash'][:19]}…)"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        print("  git: committed (commit timestamp is the tamper-evidence anchor)", file=sys.stderr)
    else:
        print("  NOTE: commit prereg.yaml now so its timestamp provably predates results:", file=sys.stderr)
        print(f"        git add {prereg_path} && git commit -m 'Freeze prereg'", file=sys.stderr)


def check(prereg_path: Path, actual_path: Path) -> int:
    prereg = _load_yaml(prereg_path)
    frozen_at = prereg.get("frozen_at")
    assert frozen_at, "prereg is not frozen — run `freeze` before `check`"

    # 1. Tamper check: the hypotheses block must still hash to the stored value.
    stored = prereg.get("content_hash")
    assert stored, "frozen prereg missing content_hash"
    recomputed = hypotheses_hash(prereg)
    if recomputed != stored:
        print("✗ TAMPER DETECTED: hypotheses block no longer matches content_hash.", file=sys.stderr)
        print(f"    stored:     {stored}", file=sys.stderr)
        print(f"    recomputed: {recomputed}", file=sys.stderr)
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

    if not deviations:
        print(f"✓ Analysis matches the pre-registration frozen at {frozen_at}.", file=sys.stderr)
        print("  (No metric / decision_rule / method drift. Deviations, if any, would be flagged for the PI gate.)", file=sys.stderr)
        return 0

    print(f"⚠ {len(deviations)} deviation(s) from the pre-registration — surface these at the analysis gate:", file=sys.stderr)
    for d in deviations:
        print(f"  - {d}", file=sys.stderr)
    print("\n  Deviations are not forbidden — they must be VISIBLE. Record each legitimate one", file=sys.stderr)
    print("  as an `amendments` entry with justification; treat unexplained ones as p-hacking risk.", file=sys.stderr)
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-registration freeze/check tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_freeze = sub.add_parser("freeze", help="Lock a drafted prereg.yaml")
    p_freeze.add_argument("prereg", type=Path)
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
            freeze(args.prereg, git_commit=args.git_commit, force=args.force)
        elif args.cmd == "check":
            sys.exit(check(args.prereg, args.actual))
    except AssertionError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
