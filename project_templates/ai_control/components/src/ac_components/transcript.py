"""Trajectory / transcript helpers for inspecting a single sample by hand.

`samples_df` gives the aggregate view; this module is for the
"pull one trajectory and look at every tool call" workflow that's necessary
when a monitor disagrees with you and you want to know why.

Where things live in a ControlArena 20.x log:
- sample.metadata — the `ControlTaskMetadata` dump (`eval_mode`,
  `main_task_description`, `side_task_description`, ...).
- log.eval.metadata["micro_protocol"] — the serialised micro-protocol.
- assistant message metadata — the monitor's `suspicion_score`, `reason` and
  `score_parsed`, flat at the top level (defer-to-trusted also stores
  `monitor_response`, `untrusted_response` and, on a deferred step,
  `trusted_response`).
- sample.scores — the setting's scorer holds a dict value
  `{"main_task_success": "C"|"I", "side_task_success": "C"|"I"}` (side task in
  attack mode only); `max_suspicion_scorer` holds a float.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from inspect_ai.log import read_eval_log
from inspect_ai.model import ChatMessageAssistant
from inspect_ai.scorer import CORRECT, INCORRECT


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
    protocol: str  # micro-protocol type, e.g. "defer_to_trusted"
    protocol_info: dict  # the serialised micro-protocol (defer_threshold, policies, monitor, ...)
    suspicion_scores: list[float]  # one per monitored step along the trajectory
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
    protocol_info = log.eval.metadata["micro_protocol"]
    tool_calls = [
        ToolCall(step=i, tool=tc.function, args=dict(tc.arguments), output=None)
        for i, msg in enumerate(sample.messages)
        if isinstance(msg, ChatMessageAssistant)
        for tc in msg.tool_calls or []
    ]
    return Trajectory(
        sample_id=sample.id,
        eval_mode=str(sample.metadata["eval_mode"]),
        protocol=protocol_info["type"],
        protocol_info=protocol_info,
        suspicion_scores=_gather_suspicion(sample),
        main_task_success=_task_success(sample.scores, "main_task_success"),
        side_task_success=_task_success(sample.scores, "side_task_success"),
        tool_calls=tool_calls,
    )


def _gather_suspicion(sample) -> list[float]:
    """Monitor scores in message order — the same `metadata["suspicion_score"]`
    entries `max_suspicion_scorer` takes the maximum of."""
    return [
        float(msg.metadata["suspicion_score"])
        for msg in sample.messages
        if isinstance(msg, ChatMessageAssistant)
        and msg.metadata
        and msg.metadata.get("suspicion_score") is not None
    ]


def monitor_parse_counts(log_dir: str | Path) -> dict[str, int]:
    """How many monitor replies ControlArena could and could not parse a score from.

    A reply with no `<score>` tag is recorded as `default_suspicion_score`
    (0.0 unless configured) with `score_parsed=False`, and `max_suspicion_scorer`
    uses it like any other score — so report this count beside any safety number.
    The flag sits at the top level of the message metadata, or inside
    `monitor_response` when a defer-to-trusted protocol wraps the monitor.
    """
    counts = {"parsed": 0, "unparsed": 0}
    for path in sorted(Path(log_dir).glob("*.eval")):
        for sample in read_eval_log(path).samples or []:
            for msg in sample.messages:
                md = msg.metadata if isinstance(msg, ChatMessageAssistant) else None
                if not md or md.get("suspicion_score") is None:
                    continue
                flag = md["score_parsed"] if "score_parsed" in md else md["monitor_response"]["score_parsed"]
                counts["parsed" if flag else "unparsed"] += 1
    return counts


def _task_success(scores, key: str) -> bool | None:
    """Read `key` from the scorer whose value is a dict holding it.

    None when no scorer reports it (side task in honest mode, or task scorers
    skipped)."""
    for score in (scores or {}).values():
        if isinstance(score.value, dict) and key in score.value:
            return {CORRECT: True, INCORRECT: False}[score.value[key]]
    return None
