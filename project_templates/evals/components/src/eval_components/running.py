"""Run Inspect AI evals into a run's log dir — single eval, multi-model set, retry.

Three entry points, matching Inspect's own three:

- `run_eval()`         → wraps `inspect_ai.eval` for a one-off run.
- `run_eval_set()`     → wraps `inspect_ai.eval_set` for a model × task matrix
                         with automatic resume (the right tool for sweeps).
- `retry()`            → wraps `inspect_ai.eval_retry` to resume a crashed run
                         instead of paying for it twice.

All write to a `log_dir` (use `runs.new_run().log_dir`) so the analysis layer
can load everything back with `analysis.load_evals` / `load_samples`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from inspect_ai import Task, eval as inspect_eval, eval_retry, eval_set


def run_eval(
    tasks: Task | Sequence[Task],
    *,
    model: str | Sequence[str],
    log_dir: str | Path,
    limit: int | None = None,
    **extra: Any,
):
    """Run one (or a few) tasks against one or more models. Returns list[EvalLog].

    `extra` is forwarded to `inspect_ai.eval` — pass `max_connections`,
    `temperature`, `epochs`, `max_tokens`, etc. without us re-listing them.
    Set `limit` small (e.g. 10) while iterating; only drop it for the full run.
    """
    return inspect_eval(
        tasks=tasks,
        model=model,
        log_dir=str(log_dir),
        limit=limit,
        **extra,
    )


def run_eval_set(
    tasks: Task | Sequence[Task],
    *,
    model: str | Sequence[str],
    log_dir: str | Path,
    limit: int | None = None,
    retry_attempts: int = 10,
    **extra: Any,
) -> tuple[bool, list]:
    """Run a model × task matrix with resume-on-failure. Returns (success, logs).

    `eval_set` REQUIRES a dedicated `log_dir` — it uses it to track which tasks
    finished, so re-invoking the same call continues incomplete work instead of
    redoing it. This is the right primitive for a sweep over models/paraphrases:
    if the run dies at task 40 of 60, just call it again.

    Note: the returned `logs` are headers only (no per-sample data). Reload full
    samples with `analysis.load_samples(log_dir)`.
    """
    return eval_set(
        tasks=tasks,
        model=model,
        log_dir=str(log_dir),
        limit=limit,
        retry_attempts=retry_attempts,
        **extra,
    )


def retry(log_file: str | Path, **extra: Any):
    """Resume a single crashed/partial eval from its `.eval` log. Returns EvalLog.

    Cheaper and faster than re-running: only the unfinished samples are redone.
    """
    return eval_retry(str(log_file), **extra)
