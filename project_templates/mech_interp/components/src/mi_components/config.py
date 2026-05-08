"""Dataclass-based config with optional CLI overrides.

Avoids a hard Hydra dependency. The pattern is:

    @dataclass
    class TrainConfig:
        model_name: str = "distilgpt2"
        lr: float = 1e-3
        steps: int = 100

    cfg = parse_overrides(TrainConfig(), sys.argv[1:])

CLI args are key=value pairs, e.g. `lr=3e-4 steps=500`. Nested dataclasses are
addressed with dotted keys (`opt.lr=3e-4`). Types are coerced from the field
annotation; bools accept true/false/1/0.
"""

from __future__ import annotations

import dataclasses
from dataclasses import is_dataclass
from typing import Any, TypeVar, get_args, get_origin

T = TypeVar("T")


def parse_overrides(default: T, args: list[str]) -> T:
    """Apply key=value CLI overrides to a dataclass instance and return a new instance.

    Unknown keys raise ValueError so typos don't silently no-op.
    """
    if not is_dataclass(default):
        raise TypeError(f"default must be a dataclass instance, got {type(default)}")
    overrides: dict[str, str] = {}
    for arg in args:
        if "=" not in arg:
            raise ValueError(f"expected key=value, got {arg!r}")
        k, v = arg.split("=", 1)
        overrides[k] = v
    return _apply(default, overrides, prefix="")


def _apply(obj: Any, overrides: dict[str, str], prefix: str) -> Any:
    fields = {f.name: f for f in dataclasses.fields(obj)}
    new_values: dict[str, Any] = {}
    for fname, field in fields.items():
        full_key = f"{prefix}{fname}"
        cur = getattr(obj, fname)
        if is_dataclass(cur):
            new_values[fname] = _apply(cur, overrides, prefix=f"{full_key}.")
        elif full_key in overrides:
            new_values[fname] = _coerce(overrides.pop(full_key), field.type)
    if prefix == "" and overrides:
        raise ValueError(f"unknown config key(s): {sorted(overrides)}")
    return dataclasses.replace(obj, **new_values)


def _coerce(raw: str, annotation: Any) -> Any:
    # Strip Optional[...]
    origin = get_origin(annotation)
    if origin is not None:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            annotation = args[0]
    if annotation is bool or annotation == "bool":
        return raw.strip().lower() in {"1", "true", "yes", "y", "on"}
    if annotation is int or annotation == "int":
        return int(raw)
    if annotation is float or annotation == "float":
        return float(raw)
    if annotation is str or annotation == "str":
        return raw
    # Best effort: try float→int→str
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return raw


def to_dict(cfg: Any) -> dict[str, Any]:
    """Recursively convert a dataclass config to a JSON-serializable dict."""
    if is_dataclass(cfg):
        return {f.name: to_dict(getattr(cfg, f.name)) for f in dataclasses.fields(cfg)}
    return cfg
