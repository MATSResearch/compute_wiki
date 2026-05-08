"""Timestamped run directories and metadata.

Convention (from CLAUDE.md): every run gets its own directory under outputs/
named outputs/run_YYYYMMDD_HHMMSS_<tag>/. The directory contains a metadata.json
describing the config used, a checkpoints/ subdir, and any per-run artifacts.
No global plots/ folder — each run is self-contained.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import torch


@dataclass
class RunDir:
    """A handle to one run's output directory.

    `root` is the absolute path to the run dir. Subdirs (checkpoints/, plots/, logs/)
    are created lazily.
    """

    root: Path
    tag: str
    created_at: str

    @property
    def checkpoints(self) -> Path:
        d = self.root / "checkpoints"
        d.mkdir(exist_ok=True)
        return d

    @property
    def plots(self) -> Path:
        d = self.root / "plots"
        d.mkdir(exist_ok=True)
        return d

    @property
    def logs(self) -> Path:
        d = self.root / "logs"
        d.mkdir(exist_ok=True)
        return d

    def write_metadata(self, payload: Any) -> Path:
        """Write metadata.json. Accepts a dict, a dataclass instance, or anything json.dumps can handle.

        Existing metadata.json is overwritten — this is meant for the once-at-startup write.
        """
        if dataclasses.is_dataclass(payload):
            payload = dataclasses.asdict(payload)
        path = self.root / "metadata.json"
        with path.open("w") as f:
            json.dump(payload, f, indent=2, default=_json_default)
        return path

    def save_checkpoint(self, name: str, state: dict[str, Any]) -> Path:
        """Save a torch state_dict-like payload to checkpoints/<name>.pt."""
        path = self.checkpoints / f"{name}.pt"
        torch.save(state, path)
        return path


def new_run(tag: str, base: str | Path = "outputs") -> RunDir:
    """Create a new outputs/run_YYYYMMDD_HHMMSS_<tag>/ directory and return a handle.

    `tag` should be a short slug describing the experiment (no spaces / slashes).
    """
    safe_tag = _slug(tag)
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    root = Path(base) / f"run_{stamp}_{safe_tag}"
    root.mkdir(parents=True, exist_ok=False)
    return RunDir(root=root.resolve(), tag=safe_tag, created_at=now.isoformat(timespec="seconds"))


def _slug(s: str) -> str:
    out = []
    for ch in s.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in "-_":
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)[:64] or "run"


def _json_default(o: Any) -> Any:
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, torch.dtype):
        return str(o)
    if isinstance(o, torch.device):
        return str(o)
    raise TypeError(f"unserializable: {type(o)}")
