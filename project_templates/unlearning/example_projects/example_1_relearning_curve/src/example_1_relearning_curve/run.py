"""CLI entry point.

    uv run python -m example_1_relearning_curve.run                  # full toy run
    uv run python -m example_1_relearning_curve.run --smoke          # ~1 minute
    uv run python -m example_1_relearning_curve.run --method graddiff
"""

from __future__ import annotations

import argparse
from dataclasses import replace

from ul_components import runs

from example_1_relearning_curve.pipeline import Config, run_experiment


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="distilgpt2")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--method", default="npo_retain",
                    choices=["ga", "graddiff", "npo", "npo_retain"])
    ap.add_argument("--entities", type=int, default=30)
    ap.add_argument("--implant-steps", type=int, default=220)
    ap.add_argument("--unlearn-steps", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default="relearning_curve")
    ap.add_argument("--smoke", action="store_true",
                    help="tiny settings so the whole pipeline runs in about a minute")
    args = ap.parse_args()

    cfg = Config(
        model_name=args.model, device=args.device, unlearn_method=args.method,
        n_entities=args.entities, implant_steps=args.implant_steps,
        unlearn_steps=args.unlearn_steps, seed=args.seed,
    )
    if args.smoke:
        cfg = replace(cfg, n_entities=6, implant_steps=30, unlearn_steps=10,
                      relearn_steps=(0, 5, 10))

    run = runs.new_run(tag=args.tag + ("_smoke" if args.smoke else ""), root="outputs")
    run.write_metadata({"config": cfg.__dict__})
    print(f"run dir: {run.dir}\n")
    run_experiment(cfg, run)
    print(f"\nwrote {run.dir}/results.json")


if __name__ == "__main__":
    main()
