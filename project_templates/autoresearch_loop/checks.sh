#!/usr/bin/env bash
# checks.sh — backpressure, run after a DEV-split improvement and before a keep.
#
# Researcher-owned: the agent runs this file and does not edit it (program.md).
# Exit 0 = every check passed, the change may be kept.
# Non-zero = log the experiment as `checks_failed` and revert (pi-autoresearch's rule).
#
# It prints only PASS / FAIL lines and never the guard score, so the agent learns one
# bit per candidate about the guard split. Keep the floor loose: it is there to catch
# regressions (evo's held-out-slice floor gate), not to rank candidates.
# No `set -euo pipefail`: each check reports its own failure.

# 1. Correctness. >>> EDIT: your test command (or delete this check).
if ! uv run pytest -q > /dev/null 2>&1; then
    echo "FAIL tests"
    exit 1
fi
echo "PASS tests"

# 2. Guard floor on data/heldout/guard/. >>> EDIT: a script of yours that scores the guard
# split and exits non-zero when the score is below FLOOR. Send its output to /dev/null so
# the score itself never reaches the agent.
FLOOR=0.0   # >>> EDIT
if ! uv run python eval_guard.py --data data/heldout/guard --floor "$FLOOR" > /dev/null 2>&1; then
    echo "FAIL guard_floor"
    exit 1
fi
echo "PASS guard_floor"
