"""JSONL scalar logger that no-ops gracefully without wandb.

Per-response judge scores belong in the run's JSONL artifacts (see
`mo_components.eval`); this is for *run-level* rollups: e.g. "treatment
misalignment rate = X (95% CI [a,b]), control = Y, gap = Z; total judge cost
= $C". Useful as a wandb feed when you sweep finetune hyperparameters.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class Tracker:
    """Append scalars to a JSONL file, and optionally wandb."""

    def __init__(
        self,
        run_dir: str | Path,
        *,
        project: str | None = None,
        config: dict[str, Any] | None = None,
        use_wandb: bool | None = None,
    ):
        self.run_dir = Path(run_dir)
        self.jsonl_path = self.run_dir / "metrics.jsonl"
        self._wandb = None
        if use_wandb is None:
            try:
                import wandb  # noqa: F401
                use_wandb = project is not None
            except ImportError:
                use_wandb = False
        if use_wandb:
            import wandb
            self._wandb = wandb.init(
                project=project,
                config=config or {},
                dir=str(self.run_dir),
                reinit=True,
            )

    def log(self, step: int | None = None, **scalars: Any) -> None:
        row = {"t": time.time(), **scalars}
        if step is not None:
            row["step"] = step
        with self.jsonl_path.open("a") as f:
            f.write(json.dumps(row, default=str) + "\n")
        if self._wandb is not None:
            self._wandb.log(scalars, step=step)

    def close(self) -> None:
        if self._wandb is not None:
            self._wandb.finish()
            self._wandb = None
