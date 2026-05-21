"""Inline timing — agentic / multi-turn evals can be minutes-to-hours per run."""

from __future__ import annotations

import time
from contextlib import contextmanager


@contextmanager
def Timer(label: str = "block"):
    """`with Timer('eval'): ...` prints elapsed wall time."""
    t0 = time.time()
    yield
    elapsed = time.time() - t0
    print(f"[{label}] {elapsed:.2f}s")
