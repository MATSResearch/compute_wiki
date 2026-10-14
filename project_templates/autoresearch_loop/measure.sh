#!/usr/bin/env bash
# measure.sh — run ONE experiment on the DEV split and print METRIC lines.
#
# Researcher-owned: the agent runs this file and does not edit it (program.md).
# Output contract (pi-autoresearch's): one `METRIC <name>=<number>` per line on
# stdout, names of word characters and dots, values finite numbers.
# Exit status: 0 = measured; non-zero = crash (no metric, timeout, or error).
#
# Usage: ./measure.sh <log file>     e.g. ./measure.sh outputs/run_.../logs/7.log
# No `set -euo pipefail`: a failing step is reported below, not allowed to kill the shell.

LOG="$1"
if [ -z "$LOG" ]; then
    echo "usage: ./measure.sh <log file>" >&2
    exit 2
fi
mkdir -p "$(dirname "$LOG")"

TIMEOUT_S=600   # >>> EDIT: kill a run after this many seconds; counts as a crash

# GNU coreutils `timeout` (Linux) or `gtimeout` (macOS: brew install coreutils).
if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_CMD="timeout $TIMEOUT_S"
elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD="gtimeout $TIMEOUT_S"
else
    echo "measure.sh: no timeout/gtimeout found; refusing to run without a time limit" >&2
    exit 2
fi

start=$(date +%s)
# >>> EDIT: the experiment command. It must read only the DEV split (never data/heldout/)
# and print a line `val_metric: <number>`; adapt the grep below if yours differs.
$TIMEOUT_CMD uv run python train.py > "$LOG" 2>&1
status=$?
end=$(date +%s)

if [ "$status" -ne 0 ]; then
    echo "measure.sh: experiment exited with status $status (124 = timeout); see $LOG" >&2
    exit 1
fi

value=$(grep -E '^val_metric:' "$LOG" | tail -n 1 | awk '{print $2}')   # >>> EDIT if your line differs
if [ -z "$value" ]; then
    echo "measure.sh: no 'val_metric:' line in $LOG" >&2
    exit 1
fi

echo "METRIC val_metric=$value"
echo "METRIC wall_s=$((end - start))"
