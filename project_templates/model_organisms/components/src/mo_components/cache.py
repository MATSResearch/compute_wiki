"""Cache directories by config hash so reruns of the same sweep are free.

Model-organism evals make a lot of API calls (one generation + one or two judge
calls per probe prompt per organism). `mo_components.generate` and `judge` cache
individual calls; this module sits one level up: name a *whole run's* output dir
by a SHA-256 of its config (organism set × probe set × judge model × seed) so
re-invoking the same sweep skips generation+judging entirely. Use it when you
re-run the analysis script repeatedly while iterating on plots, not while
iterating on the organism or probes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def hash_config(payload: dict | str) -> str:
    """Stable SHA-256 hex of a JSON-serializable payload."""
    if isinstance(payload, dict):
        payload = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def cached_log_dir(cache_root: str | Path, payload: dict) -> tuple[Path, bool]:
    """Return (log_dir, exists). Create the dir if it doesn't exist.

    Caller can then check `exists` and skip the eval if True.
    """
    digest = hash_config(payload)
    d = Path(cache_root) / f"cached_{digest}"
    exists = d.exists() and any(d.iterdir())
    d.mkdir(parents=True, exist_ok=True)
    return d, exists
