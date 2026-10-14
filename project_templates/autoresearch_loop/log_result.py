#!/usr/bin/env python3
"""Append one experiment record to results.jsonl, after checking its shape.

The log is append-only: this script never rewrites a line, and it refuses a
record that is malformed or out of order instead of guessing. Fields are
specified in results.schema.json. Stdlib only.

Example:
    uv run python log_result.py outputs/run_20261014_093000_lr/results.jsonl \\
        --run 7 --kind experiment --status discard --commit a1b2c3d \\
        --metrics-from outputs/run_20261014_093000_lr/logs/7.metrics \\
        --hypothesis "warmup 2x longer" --prediction "val_metric drops ~0.01" \\
        --description "doubled warmup steps" \\
        --rollback-reason "within the noise floor; warmup is not the bottleneck"
"""
import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUSES = ("keep", "discard", "crash", "checks_failed")
KINDS = ("baseline", "experiment", "rerun")
NEEDS_REASON = ("discard", "crash", "checks_failed")
# Same line format pi-autoresearch parses: `METRIC name=value`.
METRIC_LINE = re.compile(r"^METRIC\s+([\w.]+)=(\S+)\s*$")


def parse_metric(text: str) -> tuple[str, float]:
    name, sep, value = text.partition("=")
    if not sep or not re.fullmatch(r"[\w.]+", name):
        sys.exit(f"log_result.py: bad metric {text!r}; expected name=number")
    number = float(value)
    if not math.isfinite(number):
        sys.exit(f"log_result.py: metric {name} is not finite: {value}")
    return name, number


def metrics_from_file(path: Path) -> dict[str, float]:
    metrics = {}
    for line in path.read_text().splitlines():
        match = METRIC_LINE.match(line)
        if match:
            name, number = parse_metric(f"{match.group(1)}={match.group(2)}")
            metrics[name] = number
    return metrics


def read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("results", type=Path, help="path to the run's results.jsonl")
    p.add_argument("--run", type=int, required=True)
    p.add_argument("--kind", choices=KINDS, required=True)
    p.add_argument("--status", choices=STATUSES, required=True)
    p.add_argument("--commit", default=None, help="short git SHA; omit for a crash before commit")
    p.add_argument("--metric", action="append", default=[], help="name=number (repeatable)")
    p.add_argument("--metrics-from", type=Path, help="file holding measure.sh's METRIC lines")
    p.add_argument("--hypothesis", required=True, help="why this change; written before the run")
    p.add_argument("--prediction", required=True, help="what you expect the metric to do; written before the run")
    p.add_argument("--description", required=True, help="what was changed (for a revisit: what assumption changed)")
    p.add_argument("--rollback-reason", default=None)
    p.add_argument("--revisits-run", type=int, default=None)
    a = p.parse_args()

    records = read_records(a.results)
    expected_run = len(records) + 1
    if records:
        assert [r["run"] for r in records] == list(range(1, expected_run)), \
            f"{a.results} is not numbered 1..{len(records)}; fix the file by hand, then log again"
    if a.run != expected_run:
        sys.exit(f"log_result.py: --run {a.run}, but the next run number is {expected_run}")

    metrics = metrics_from_file(a.metrics_from) if a.metrics_from else {}
    for text in a.metric:
        name, number = parse_metric(text)
        metrics[name] = number
    if a.status != "crash" and not metrics:
        sys.exit("log_result.py: a non-crash run needs at least one metric")

    if a.status in NEEDS_REASON and not a.rollback_reason:
        sys.exit(f"log_result.py: status {a.status} needs --rollback-reason (the assumption that failed)")
    if a.status == "keep" and a.rollback_reason:
        sys.exit("log_result.py: a kept run has no rollback reason")
    if a.status != "crash" and not a.commit:
        sys.exit("log_result.py: --commit is required unless the run crashed before committing")

    if a.revisits_run is not None:
        earlier = {r["run"]: r for r in records}
        if a.revisits_run not in earlier:
            sys.exit(f"log_result.py: --revisits-run {a.revisits_run} is not an earlier run")
        if earlier[a.revisits_run]["status"] == "keep":
            sys.exit(f"log_result.py: run {a.revisits_run} was kept; a revisit retries a discarded idea")
        if a.kind != "experiment":
            sys.exit("log_result.py: a revisit is a new experiment (--kind experiment), not a rerun")

    record = {
        "run": a.run,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": a.kind,
        "status": a.status,
        "commit": a.commit,
        "metrics": metrics,
        "hypothesis": a.hypothesis,
        "prediction": a.prediction,
        "description": a.description,
        "rollback_reason": a.rollback_reason,
        "revisits_run": a.revisits_run,
    }
    a.results.parent.mkdir(parents=True, exist_ok=True)
    with a.results.open("a") as f:
        f.write(json.dumps(record) + "\n")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
