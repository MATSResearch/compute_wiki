"""Inline timing — control evals can be hours per run; know where the time goes."""

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
