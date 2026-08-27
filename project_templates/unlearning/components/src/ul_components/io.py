"""JSONL read/write and dataclass round-tripping.

Same surface as `mo_components.io` / `eval_components.io`; vendored so this
package has no cross-package import.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Iterable


def write_jsonl(rows: Iterable[dict], path: str | Path) -> int:
    n = 0
    with Path(path).open("w") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")
            n += 1
    return n


def read_jsonl(path: str | Path) -> list[dict]:
    out: list[dict] = []
    with Path(path).open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def dataclass_to_dict(obj: Any) -> dict:
    if not dataclasses.is_dataclass(obj):
        raise TypeError(f"expected dataclass, got {type(obj)}")
    return dataclasses.asdict(obj)
