"""Micro-protocol builders.

Micro-protocols are trajectory-level orchestrators: who generates, who
monitors, what to do when suspicion is high. ControlArena ships these:

- `trusted_only` — just the trusted (weaker) policy. Safety baseline.
- `untrusted_only` — just the untrusted policy, no monitor. Usefulness ceiling.
- `defer_to_trusted` (DTT) — untrusted generates; if monitor flags, defer to
  trusted. The simplest non-trivial protocol.
- `defer_to_resample` — request a new sample instead of deferring.
- `trusted_monitoring` — generate with untrusted, monitor with trusted, do
  nothing if flagged (audit-only). Useful as an upper bound on monitor
  detection rate.
- `trusted_editing` — untrusted generates; if flagged, trusted edits the
  suspicious output before use.
- `untrusted_monitoring` — a second untrusted instance monitors the first,
  with anti-collusion measures.

This module re-exports the builders and gives `dtt_pair()` for the common
"build DTT protocol from a pre-built monitor + policies" pattern.
"""

from __future__ import annotations

from control_arena.micro_protocol import (
    defer_to_resample_builder,
    defer_to_trusted_builder,
    trusted_monitoring_builder,
)

__all__ = [
    "defer_to_resample_builder",
    "defer_to_trusted_builder",
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
    args so you can't swap untrusted/trusted by accident.
    """
    return defer_to_trusted_builder(
        defer_threshold=defer_threshold,
        untrusted_policy=untrusted_policy,
        trusted_policy=trusted_policy,
        monitor=monitor,
    )
