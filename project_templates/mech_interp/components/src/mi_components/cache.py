"""On-disk caches for slow operations.

Two complementary tools:

1. `disk_cache` — decorator that hashes a function's args and stores the result as a
   torch.save'd .pt under a cache dir. Use it on "compute the activations of model X
   on dataset Y at layer L" — the second call is a load from disk.

2. `save_activations` / `load_activations` — direct save/load of a dict of tensors,
   for the hand-rolled case where you want explicit control over filenames.

Cache hits are decided by a SHA-256 of repr(args) + repr(kwargs). That's coarse —
non-hashable objects fall back to their id() which won't match across runs.

When NOT to use these:
- Anything that fits in memory and is recomputed in <1s. The disk round-trip costs more.
- Anything depending on file contents (pass a pathlib.Path, not the bytes — the path
  string ends up in the hash; use mtime if you want to invalidate on edit).
"""

from __future__ import annotations

import functools
import hashlib
import pickle
from pathlib import Path
from typing import Any, Callable, TypeVar

import torch

F = TypeVar("F", bound=Callable[..., Any])


def _hash_args(args: tuple, kwargs: dict) -> str:
    try:
        blob = pickle.dumps((args, sorted(kwargs.items())))
    except Exception:
        blob = repr((args, sorted(kwargs.items()))).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def disk_cache(cache_dir: str | Path = ".cache/mi_components") -> Callable[[F], F]:
    """Decorator factory that caches a function's output to disk via torch.save/load.

    Example:
        @disk_cache(cache_dir="outputs/cache")
        def collect_activations(model_name: str, layer: int) -> torch.Tensor:
            ...
    """
    base = Path(cache_dir)

    def deco(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            base.mkdir(parents=True, exist_ok=True)
            key = _hash_args(args, kwargs)
            path = base / f"{fn.__name__}_{key}.pt"
            if path.exists():
                return torch.load(path, weights_only=False)
            result = fn(*args, **kwargs)
            torch.save(result, path)
            return result

        return wrapper  # type: ignore

    return deco


def save_activations(activations: dict[str, torch.Tensor], path: str | Path) -> Path:
    """Save a dict[str, Tensor] to a single .pt file. Creates parent dirs as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    torch.save(activations, p)
    return p


def load_activations(path: str | Path) -> dict[str, torch.Tensor]:
    """Load a previously-saved activation dict."""
    return torch.load(Path(path), weights_only=False)
