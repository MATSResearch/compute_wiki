"""Smoke test for ac_components.

Imports every module, builds a minimal config + run dir, exits.
Does NOT call ControlArena / Inspect (they need API keys + Docker). Run with:

    uv run python -m ac_components._smoke
"""

from __future__ import annotations

import numpy as np

from ac_components import audit, io, metrics, runs, seeding, sweep, tracking
from ac_components.runs import new_run


def main() -> None:
    seeding.set_seed(0)
    print("seed set")

    run = new_run(tag="ac_components_smoke", root="outputs")
    run.write_metadata({"smoke": True})
    print(f"run dir: {run.dir}")

    tracker = tracking.Tracker(run.dir, use_wandb=False)
    tracker.log(step=0, dummy_metric=0.42)
    tracker.close()
    print("logged a scalar")

    # Calibration on fake honest scores
    honest = np.concatenate([np.zeros(80), np.random.default_rng(0).uniform(0, 1, size=20)])
    calib = audit.compute_threshold_from_budget(honest, audit_budget=0.05)
    print(f"calibration: threshold={calib.threshold:.3f}, flagged {calib.n_flagged}/{calib.n_honest}")

    # Sweep
    axes = {"threshold": [0.1, 0.5, 0.9], "seed": [0, 1]}
    pts = sweep.grid(axes)
    print(f"sweep produced {len(pts)} points")

    # IO round-trip
    io.write_jsonl([{"k": 1}, {"k": 2}], run.dir / "demo.jsonl")
    back = io.read_jsonl(run.dir / "demo.jsonl")
    assert back == [{"k": 1}, {"k": 2}]
    print("jsonl round-trip ok")

    # Metrics import is heavy (pandas + control_arena) — touch it last.
    assert hasattr(metrics, "compute_safety")
    print("metrics module imports ok")

    print("\nac_components smoke passed.")


if __name__ == "__main__":
    main()
