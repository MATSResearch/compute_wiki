"""Lightweight timing and GPU-memory snapshots.

For "is this step actually slow, or do I just feel impatient?" use `Timer`. For
"did the model OOM, and at what step?" use `cuda_memory_snapshot`.

Neither tool replaces a real profiler (PyTorch's torch.profiler, NVIDIA Nsight) —
they're for inline checks while you're iterating.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

import torch


class Timer:
    """Context manager: `with Timer("step") as t: ...; print(t.elapsed_s)`.

    On CUDA, calls torch.cuda.synchronize() at entry and exit so the timing reflects
    the actual GPU work, not just the kernel-launch latency.
    """

    def __init__(self, label: str = "", sync_cuda: bool = True):
        self.label = label
        self.sync_cuda = sync_cuda and torch.cuda.is_available()
        self.start: float = 0.0
        self.elapsed_s: float = 0.0

    def __enter__(self) -> "Timer":
        if self.sync_cuda:
            torch.cuda.synchronize()
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc) -> None:
        if self.sync_cuda:
            torch.cuda.synchronize()
        self.elapsed_s = time.perf_counter() - self.start


@contextmanager
def timed(label: str, sync_cuda: bool = True) -> Iterator[Timer]:
    """Same as Timer but as a function-style helper. Yields the Timer for inspection."""
    t = Timer(label=label, sync_cuda=sync_cuda)
    with t:
        yield t


def cuda_memory_snapshot(device: int | str | torch.device | None = None) -> dict[str, float]:
    """Return current / peak CUDA memory usage in MiB. Empty dict if no CUDA.

    Useful for stuffing into metrics.jsonl or metadata.json after a run.
    """
    if not torch.cuda.is_available():
        return {}
    if device is None:
        device = torch.cuda.current_device()
    a = torch.cuda.memory_allocated(device) / (1024**2)
    a_peak = torch.cuda.max_memory_allocated(device) / (1024**2)
    r = torch.cuda.memory_reserved(device) / (1024**2)
    r_peak = torch.cuda.max_memory_reserved(device) / (1024**2)
    return {
        "alloc_mib": a,
        "alloc_peak_mib": a_peak,
        "reserved_mib": r,
        "reserved_peak_mib": r_peak,
    }


def reset_cuda_peak_stats() -> None:
    """Reset peak-allocation tracking (no-op if CUDA isn't available)."""
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
