"""JSONL read/write and dataclass <-> JSON helpers.

JSONL is the lingua franca of eval datasets (Anthropic's model-written evals,
HarmBench prompts, etc. all ship as JSONL). `eval_components.datasets` builds
on these to turn JSONL records into Inspect `Sample` objects.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Iterator


def write_jsonl(rows: list[dict] | Iterator[dict], path: str | Path) -> int:
    n = 0
    with Path(path).open("w") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")
            n += 1
    return n


def read_jsonl(path: str | Path) -> list[dict]:
    out = []
    with Path(path).open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def dataclass_to_json(obj: Any) -> str:
    if not dataclasses.is_dataclass(obj):
        raise TypeError(f"expected dataclass, got {type(obj)}")
    return json.dumps(dataclasses.asdict(obj), indent=2, default=str)


def dataclass_from_json(raw: str, schema):
    data = json.loads(raw)
    return schema(**data)
