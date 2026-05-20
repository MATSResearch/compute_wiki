"""Smoke test for eval_components.

Imports every module and exercises the pure-Python paths (datasets, refusal
heuristic, Wilson CI, spread, contamination, sweep, io, runs) against fake data.
Does NOT call Inspect's `eval()` or any model API (those need keys + cost). Run:

    uv run python -m eval_components._smoke
"""

from __future__ import annotations

from eval_components import (
    analysis,
    contamination,
    datasets,
    io,
    robustness,
    runs,
    scorers,
    seeding,
    sweep,
    tracking,
)
from eval_components.runs import new_run


def main() -> None:
    seeding.set_seed(0)
    print("seed set")

    run = new_run(tag="eval_components_smoke", root="outputs")
    run.write_metadata({"smoke": True})
    print(f"run dir: {run.dir}")

    tracker = tracking.Tracker(run.dir, use_wandb=False)
    tracker.log(step=0, dummy_metric=0.42)
    tracker.close()
    print("logged a scalar")

    # Dataset construction + paraphrase expansion (no API).
    ds = datasets.samples_from_records(
        [{"input": "2+2?", "target": "4"}, {"input": "capital of France?", "target": "Paris"}],
    )
    expanded = datasets.expand_paraphrases(ds, ["Are you sure?", "Really? Reconsider."])
    assert len(expanded) == 4, len(expanded)
    print(f"dataset: {len(ds)} samples → {len(expanded)} after 2 paraphrases")

    # Refusal heuristic (pure).
    assert scorers.refusal_heuristic("I can't help with that request.")
    assert not scorers.refusal_heuristic("The answer is 4.")
    print("refusal heuristic ok")

    # Wilson CI + spread (pure).
    lo, hi = analysis.wilson_ci(45, 50)
    assert 0 < lo < 0.9 < hi <= 1.0, (lo, hi)
    s = robustness.spread([0.80, 0.72, 0.91])
    assert abs(s.range - 0.19) < 1e-9, s.range
    assert robustness.is_prompt_sensitive(s)  # 19-point range > 10pt default
    print(f"wilson_ci(45/50)=({lo:.3f}, {hi:.3f}); paraphrase range={s.range:.2f} (sensitive)")

    # Contamination canary scan (pure).
    hit = contamination.scan_completions(
        ["clean answer", f"...{contamination.BIG_BENCH_CANARY}..."]
    )
    assert hit["n_hits"] == 1, hit
    print(f"contamination scan: {hit['n_hits']}/{hit['n']} leaked the canary")

    # Sweep + io round-trip.
    pts = sweep.grid({"model": ["a", "b"], "paraphrase_idx": [0, 1, 2]})
    assert len(pts) == 6
    io.write_jsonl([{"k": 1}, {"k": 2}], run.dir / "demo.jsonl")
    assert io.read_jsonl(run.dir / "demo.jsonl") == [{"k": 1}, {"k": 2}]
    print(f"sweep produced {len(pts)} points; jsonl round-trip ok")

    print("\neval_components smoke passed.")


if __name__ == "__main__":
    main()
