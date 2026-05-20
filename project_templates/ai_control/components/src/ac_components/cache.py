"""Cache eval log dirs by config hash so reruns of the same sweep are free.

ControlArena already uses a SHA256 of the task config to name tasks (so
Inspect's own caching kicks in within a log_dir). This module sits one level
up: cache the *log_dir path* keyed by the (setting, protocol, model, ...)
tuple so re-running `make_or_load_logs(...)` skips Inspect entirely.
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


def cached_log_dir(
    cache_root: str | Path,
    payload: dict,
) -> tuple[Path, bool]:
    """Return (log_dir, exists). Create the dir if it doesn't exist.

    Caller can then check `exists` and skip the eval if True.
    """
    digest = hash_config(payload)
    d = Path(cache_root) / f"cached_{digest}"
    exists = d.exists() and any(d.iterdir())
    d.mkdir(parents=True, exist_ok=True)
    return d, exists
