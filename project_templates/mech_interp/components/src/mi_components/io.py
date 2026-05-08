"""Lightweight serialization helpers.

`runs.RunDir.write_metadata` covers the once-per-run metadata case. This module
covers the everything-else cases:

  - read_jsonl / write_jsonl: append/iterate JSONL files
  - dataclass_to_json / dataclass_from_json: round-trip a dataclass through a dict
    that survives `json.dumps`. Handles nested dataclasses, Paths, torch dtypes.

These are intentionally framework-free — no Pydantic, no marshmallow.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Iterator, Type, TypeVar

import torch

T = TypeVar("T")


def write_jsonl(path: str | Path, records: list[dict[str, Any]], append: bool = False) -> Path:
    """Write a list of dicts as one JSON object per line."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with p.open(mode) as f:
        for r in records:
            f.write(json.dumps(r, default=_default) + "\n")
    return p


def read_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    """Iterate records from a JSONL file, skipping malformed lines."""
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def dataclass_to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass (and nested dataclasses) to a JSON-safe dict."""
    if dataclasses.is_dataclass(obj):
        return {f.name: dataclass_to_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, (list, tuple)):
        return [dataclass_to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (torch.dtype, torch.device)):
        return str(obj)
    return obj


def dataclass_to_json(obj: Any, path: str | Path) -> Path:
    """Write a dataclass instance to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump(dataclass_to_dict(obj), f, indent=2, default=_default)
    return p


def dataclass_from_json(cls: Type[T], path: str | Path) -> T:
    """Reconstruct a dataclass instance from a JSON file.

    Limited: only handles flat fields and one level of nested dataclass. For deeper
    nesting, use a real serialization library.
    """
    raw = json.loads(Path(path).read_text())
    return _from_dict(cls, raw)


def _from_dict(cls: Type[T], data: dict[str, Any]) -> T:
    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass")
    fields = {f.name: f for f in dataclasses.fields(cls)}
    kwargs: dict[str, Any] = {}
    for k, v in data.items():
        if k not in fields:
            continue  # ignore extras
        f_type = fields[k].type
        if dataclasses.is_dataclass(f_type) and isinstance(v, dict):
            kwargs[k] = _from_dict(f_type, v)
        else:
            kwargs[k] = v
    return cls(**kwargs)


def _default(o: Any) -> Any:
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, (torch.dtype, torch.device)):
        return str(o)
    if isinstance(o, torch.Tensor):
        return o.detach().cpu().tolist()
    raise TypeError(f"unserializable: {type(o)}")
