"""Micro-protocol builders.

Micro-protocols are trajectory-level orchestrators: who generates, who
monitors, what to do when suspicion is high. ControlArena 20.x ships exactly
four in `control_arena.micro_protocol`:

- `trusted_monitoring_builder` — generate with a policy, score every
  tool-calling step with a monitor, never intervene (audit-only). Useful as
  an upper bound on monitor detection rate.
- `defer_to_trusted_builder` (DTT) — untrusted generates; if the monitor's
  score is above `defer_threshold`, discard the step and run the trusted
  policy instead. The simplest non-trivial protocol.
- `trusted_editing_builder` — untrusted generates; if flagged, the trusted
  model edits the suspicious output before use.
- `defer_to_resample_builder` — if flagged, draw new samples from the
  untrusted policy and keep the least suspicious; defer to trusted if none
  is acceptable. Needs control-arena >= 20.1.0 (before that the chosen
  resample was never executed).

There is no `trusted_only` / `untrusted_only` builder: a policy is itself a
control agent, so pass `trusted_policy_builder()` (safety baseline) or
`untrusted_policy_builder()` (usefulness ceiling, no monitor) directly as the
micro-protocol. Untrusted monitoring is not built in either; assemble it from
a monitor with `model_role="untrusted"` plus your own anti-collusion step.

This module re-exports the builders and gives `dtt_pair()` for the common
"build DTT protocol from a pre-built monitor + policies" pattern.
"""

from __future__ import annotations

from control_arena.micro_protocol import (
    defer_to_resample_builder,
    defer_to_trusted_builder,
    trusted_editing_builder,
    trusted_monitoring_builder,
)

__all__ = [
    "defer_to_resample_builder",
    "defer_to_trusted_builder",
    "trusted_editing_builder",
    "trusted_monitoring_builder",
    "dtt_pair",
]


def dtt_pair(
    *,
    untrusted_policy,
    trusted_policy,
    monitor,
    defer_threshold: float,
):
    """Build a defer-to-trusted micro-protocol from pre-built pieces.

    Convenience over `defer_to_trusted_builder` — names the four required
    args so you can't swap untrusted/trusted by accident. The step defers
    when `suspicion_score > defer_threshold` (strict), with the score on the
    monitor's *output* scale ([0, 1] by default).
    """
    return defer_to_trusted_builder(
        defer_threshold=defer_threshold,
        untrusted_policy=untrusted_policy,
        trusted_policy=trusted_policy,
        monitor=monitor,
    )
