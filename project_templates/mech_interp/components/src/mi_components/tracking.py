"""Scalar / metric logging.

`Tracker` is the single API a project should call. It writes:

  - to wandb if wandb is installed AND `use_wandb=True` (default: auto-detect)
  - always to a JSONL file in the run directory (one line per .log() call)
  - optionally to stdout for the most recent value

The JSONL file is the durable record — it works without wandb credentials, survives
crashes, and is easy to grep/plot after the fact.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


class Tracker:
    def __init__(
        self,
        run_dir: Path,
        project: str | None = None,
        run_name: str | None = None,
        config: dict[str, Any] | None = None,
        use_wandb: bool | None = None,
        stdout: bool = True,
    ):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.run_dir / "metrics.jsonl"
        self._jsonl = self.jsonl_path.open("a", buffering=1)
        self._stdout = stdout
        self._step = 0
        self._wandb = None

        wandb_requested = use_wandb if use_wandb is not None else True
        if wandb_requested:
            try:
                import wandb  # type: ignore
            except ImportError:
                wandb = None
            if wandb is not None:
                self._wandb = wandb.init(
                    project=project,
                    name=run_name,
                    config=config,
                    dir=str(self.run_dir),
                    reinit=True,
                )

    def log(self, metrics: dict[str, Any], step: int | None = None) -> None:
        """Log a dict of scalars at the given step (or auto-incrementing counter)."""
        if step is None:
            step = self._step + 1
        self._step = step
        record = {"step": step, **metrics}
        self._jsonl.write(json.dumps(record, default=_json_default) + "\n")
        if self._wandb is not None:
            self._wandb.log(metrics, step=step)
        if self._stdout:
            short = " ".join(f"{k}={_fmt(v)}" for k, v in metrics.items())
            print(f"[step {step}] {short}", file=sys.stdout)

    def close(self) -> None:
        if self._jsonl is not None and not self._jsonl.closed:
            self._jsonl.close()
        if self._wandb is not None:
            self._wandb.finish()

    def __enter__(self) -> "Tracker":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def _json_default(o: Any) -> Any:
    try:
        import torch

        if isinstance(o, torch.Tensor):
            return o.detach().cpu().tolist()
    except ImportError:
        pass
    return str(o)
