"""Dataclass-based config with CLI overrides and JSON load/save.

Mirrors `ac_components.config` / `mi_components.config`. Avoids a Hydra
dependency. CLI overrides use the form `key=value` or `nested.key=value`.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar, get_args, get_origin, get_type_hints

T = TypeVar("T")


def parse_cli_overrides(argv: list[str] | None = None) -> dict[str, str]:
    """Parse `k=v` and `nested.k=v` overrides from argv (after the script name)."""
    if argv is None:
        argv = sys.argv[1:]
    overrides: dict[str, str] = {}
    for arg in argv:
        if "=" not in arg:
            continue
        key, _, value = arg.partition("=")
        overrides[key.strip()] = value.strip()
    return overrides


def _coerce(raw: str, target_type: Any) -> Any:
    """Coerce a string to a Python value based on the target dataclass type."""
    if target_type is bool:
        return raw.lower() in ("1", "true", "yes", "y", "on")
    origin = get_origin(target_type)
    if origin is list or origin is tuple:
        item_type = get_args(target_type)[0] if get_args(target_type) else str
        return [_coerce(p, item_type) for p in raw.split(",") if p]
    if target_type in (int, float, str):
        return target_type(raw)
    if raw.lower() in ("none", "null"):
        return None
    return raw


def apply_overrides(cfg: T, overrides: dict[str, str]) -> T:
    """Return a copy of `cfg` (a dataclass) with overrides applied.

    Supports nested dataclasses via dotted keys (`models.grader="..."`).
    Unknown keys raise KeyError — fail-loud so typos in CLI args (e.g.
    `paraphrass=3`) don't silently no-op and quietly invalidate a run.
    """
    if not is_dataclass(cfg):
        raise TypeError(f"apply_overrides expects a dataclass, got {type(cfg)}")
    hints = get_type_hints(type(cfg))
    updates: dict[str, Any] = {}
    nested: dict[str, dict[str, str]] = {}
    for key, raw in overrides.items():
        head, _, tail = key.partition(".")
        if tail:
            nested.setdefault(head, {})[tail] = raw
            continue
        if head not in hints:
            raise KeyError(f"unknown config key: {head!r} on {type(cfg).__name__}")
        updates[head] = _coerce(raw, hints[head])
    for head, inner in nested.items():
        if head not in hints:
            raise KeyError(f"unknown config key: {head!r} on {type(cfg).__name__}")
        current = getattr(cfg, head)
        updates[head] = apply_overrides(current, inner)
    return dataclasses.replace(cfg, **updates)


def load_config(path: str | Path, schema: type[T]) -> T:
    """Load a dataclass config from JSON."""
    raw = json.loads(Path(path).read_text())
    return _from_dict(raw, schema)


def _from_dict(raw: dict, schema: type[T]) -> T:
    if not is_dataclass(schema):
        return raw  # type: ignore[return-value]
    hints = get_type_hints(schema)
    kwargs = {}
    for f in fields(schema):
        if f.name not in raw:
            continue
        hint = hints[f.name]
        kwargs[f.name] = (
            _from_dict(raw[f.name], hint) if is_dataclass(hint) else raw[f.name]
        )
    return schema(**kwargs)


def save_config(cfg: Any, path: str | Path) -> None:
    """Save a dataclass config to JSON."""
    Path(path).write_text(json.dumps(dataclasses.asdict(cfg), indent=2))
