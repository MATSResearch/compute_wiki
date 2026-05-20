"""Trajectory / transcript helpers for inspecting a single sample by hand.

`samples_df` gives the aggregate view; this module is for the
"pull one trajectory and look at every tool call" workflow that's necessary
when a monitor disagrees with you and you want to know why.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from inspect_ai.log import read_eval_log


@dataclass
class ToolCall:
    step: int
    tool: str
    args: dict
    output: str | None


@dataclass
class Trajectory:
    sample_id: str | int
    eval_mode: str  # "honest" or "attack"
    protocol: str
    suspicion_scores: list[float]  # one per monitor call along the trajectory
    main_task_success: bool | None
    side_task_success: bool | None
    tool_calls: list[ToolCall]


def iter_trajectories(log_path: str | Path) -> Iterator[Trajectory]:
    """Yield Trajectory objects for every sample in an EvalLog file.

    `log_path` may be the .eval / .json log file Inspect writes. To enumerate
    all logs in a run dir, glob *.eval first.
    """
    log = read_eval_log(str(log_path))
    if log.samples is None:
        return
    for sample in log.samples:
        yield _to_trajectory(sample, log)


def _to_trajectory(sample, log) -> Trajectory:
    metadata = getattr(sample, "metadata", {}) or {}
    scores = getattr(sample, "scores", {}) or {}
    susp = _gather_suspicion(sample)
    tool_calls: list[ToolCall] = []
    for i, msg in enumerate(getattr(sample, "messages", []) or []):
        for tc in getattr(msg, "tool_calls", None) or []:
            tool_calls.append(
                ToolCall(
                    step=i,
                    tool=getattr(tc, "function", "?"),
                    args=dict(getattr(tc, "arguments", {}) or {}),
                    output=None,
                )
            )
    return Trajectory(
        sample_id=getattr(sample, "id", "?"),
        eval_mode=str(metadata.get("eval_mode", "?")),
        protocol=str(metadata.get("protocol", log.eval.task)),
        suspicion_scores=susp,
        main_task_success=_score_value(scores, "main_task"),
        side_task_success=_score_value(scores, "side_task"),
        tool_calls=tool_calls,
    )


def _gather_suspicion(sample) -> list[float]:
    """Walk message metadata for monitor.suspicion_score entries."""
    out: list[float] = []
    for msg in getattr(sample, "messages", []) or []:
        meta = getattr(msg, "metadata", None) or {}
        mon = meta.get("monitor") if isinstance(meta, dict) else None
        if isinstance(mon, dict) and "suspicion_score" in mon:
            try:
                out.append(float(mon["suspicion_score"]))
            except (TypeError, ValueError):
                continue
    return out


def _score_value(scores, key_substring: str) -> bool | None:
    for k, v in (scores or {}).items():
        if key_substring in k:
            val = getattr(v, "value", v)
            if val in (True, False):
                return bool(val)
            try:
                return float(val) > 0.5
            except (TypeError, ValueError):
                return None
    return None
