"""Timestamped run directories with metadata.json.

Same shape as the other component packages in this repo (`mi_components.runs`,
`mo_components.runs`) — vendored rather than shared, so a project can copy one
components folder and nothing else. Each run dir is self-contained:
`outputs/run_<YYYYMMDD_HHMMSS>_<tag>/` with a `logs/` subdir for raw artifacts.

For diffing specifically, record BOTH model identifiers (name + revision) in
metadata.json. A difference plot whose second model you can no longer pin down
is not reproducible, and "the finetune" is not an identifier.


JSON into the same run dir as the checkpoint that produced them. A curve whose
checkpoint you can no longer identify is not a result.
"""

from __future__ import annotations

import json
import os
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Run:
    dir: Path
    tag: str
    started_at: str
    log_dir: Path

    def write_metadata(self, extra: dict[str, Any] | None = None) -> Path:
        meta = {
            "tag": self.tag,
            "started_at": self.started_at,
            "host": socket.gethostname(),
            "argv": list(sys.argv),
            "cwd": os.getcwd(),
        }
        if extra:
            meta.update(extra)
        path = self.dir / "metadata.json"
        path.write_text(json.dumps(meta, indent=2, default=str))
        return path

    def write_json(self, name: str, payload: Any) -> Path:
        path = self.dir / name
        path.write_text(json.dumps(payload, indent=2, default=str))
        return path


def new_run(tag: str, root: str | Path = "outputs") -> Run:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_tag = "".join(c if c.isalnum() or c in "-_" else "_" for c in tag)
    d = Path(root) / f"run_{ts}_{safe_tag}"
    d.mkdir(parents=True, exist_ok=False)
    log_dir = d / "logs"
    log_dir.mkdir()
    return Run(dir=d, tag=safe_tag, started_at=ts, log_dir=log_dir)


def latest_run(root: str | Path = "outputs", tag: str | None = None) -> Run | None:
    runs = sorted(Path(root).glob("run_*"))
    if tag:
        runs = [r for r in runs if r.name.endswith(f"_{tag}")]
    if not runs:
        return None
    d = runs[-1]
    parts = d.name.split("_", 3)
    ts = "_".join(parts[1:3]) if len(parts) >= 3 else ""
    rtag = parts[3] if len(parts) >= 4 else ""
    return Run(dir=d, tag=rtag, started_at=ts, log_dir=d / "logs")
