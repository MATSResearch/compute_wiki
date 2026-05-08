"""Smoke test: load a tiny model, capture one activation, write a run dir, exit.

    uv run python -m mi_components._smoke

If this fails, the components are broken before any project-specific code matters.
"""

from __future__ import annotations

import torch

from mi_components import data, hooks, models, runs, tracking


def main() -> None:
    print("Loading distilgpt2 onto CPU...")
    model, tok = models.load_hf_model("distilgpt2", device="cpu", dtype=torch.float32)
    n = models.count_params(model)
    print(f"  loaded, {n:,} params")

    weights = list(models.iter_linear_weights(model))
    print(f"  {len(weights)} linear weight matrices found; first id: {weights[0].id}")

    run = runs.new_run(tag="mi_components_smoke")
    run.write_metadata({"model": "distilgpt2", "n_params": n})
    print(f"  run dir: {run.root}")

    batch = next(data.toy_corpus_batches(tok, data.TINY_TOY_CORPUS, batch_size=2, seq_len=16))
    target = "transformer.h.0.mlp"
    with hooks.capture(model, [target]) as acts:
        with torch.no_grad():
            model(batch)
    print(f"  captured {target} with shape {tuple(acts[target].shape)}")

    with tracking.Tracker(run.root, project=None, use_wandb=False, stdout=False) as tr:
        tr.log({"loss": 1.23, "accuracy": 0.42}, step=1)
    print(f"  metrics.jsonl exists: {(run.root / 'metrics.jsonl').exists()}")
    print("OK")


if __name__ == "__main__":
    main()
