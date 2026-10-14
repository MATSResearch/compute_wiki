#!/usr/bin/env bash
# score_final.sh — score the FINAL held-out split, once, at the end (program.md P5).
#
# Researcher-only: the agent never runs this. Run it yourself on the commit you intend
# to report, after the re-measurement against the baseline. Running it repeatedly while
# still choosing between versions turns the final split into another validation set.
#
# Usage: ./score_final.sh <run dir> <git commit>
# Writes <run dir>/final_heldout.json and prints METRIC lines.
# No `set -euo pipefail`: failures are reported below.

RUN_DIR="$1"
COMMIT="$2"
if [ -z "$RUN_DIR" ] || [ -z "$COMMIT" ]; then
    echo "usage: ./score_final.sh <run dir> <git commit>" >&2
    exit 2
fi
if [ -e "$RUN_DIR/final_heldout.json" ]; then
    echo "score_final.sh: $RUN_DIR/final_heldout.json exists; the final split is scored once per run" >&2
    exit 2
fi
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "score_final.sh: uncommitted changes to tracked files; commit or stash first" >&2
    exit 2
fi

git checkout --quiet "$COMMIT" || exit 1
# >>> EDIT: score the final split; must print a line `final_metric: <number>`.
uv run python eval_final.py --data data/heldout/final > "$RUN_DIR/final_heldout.log" 2>&1
status=$?
git checkout --quiet -   # back to the branch you were on

if [ "$status" -ne 0 ]; then
    echo "score_final.sh: evaluation exited with status $status; see $RUN_DIR/final_heldout.log" >&2
    exit 1
fi
value=$(grep -E '^final_metric:' "$RUN_DIR/final_heldout.log" | tail -n 1 | awk '{print $2}')
if [ -z "$value" ]; then
    echo "score_final.sh: no 'final_metric:' line in $RUN_DIR/final_heldout.log" >&2
    exit 1
fi

printf '{"commit": "%s", "final_metric": %s, "ts": "%s"}\n' \
    "$COMMIT" "$value" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$RUN_DIR/final_heldout.json"
echo "METRIC final_metric=$value"
