"""Post-training inspection of a VPD run.

    uv run python -m example_2_vpd.analyze --run-dir outputs/run_<timestamp>_<tag>

Reports:
  - mask sparsity histogram per matrix
  - reconstruction error per matrix
  - which subcomponents activate most often / least often
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from mi_components import data, models

from example_2_vpd import importance
from example_2_vpd.decomposition import decompose_model


def load_run(run_dir: Path) -> dict:
    ckpt = torch.load(run_dir / "checkpoints" / "final.pt", map_location="cpu", weights_only=False)
    return ckpt


def reconstruction_table(banks: dict[str, dict[str, torch.Tensor]]) -> list[tuple[str, float]]:
    """For each saved bank, report ||sum_k U[k] V[k]^T||_F. Pure inspection — no targets needed."""
    rows = []
    for name, st in banks.items():
        U, V = st["U"], st["V"]
        Wsum = U.T @ V
        rows.append((name, float(torch.linalg.norm(Wsum, ord="fro"))))
    return rows


def mask_stats(ckpt: dict, n_examples: int = 16) -> dict[str, dict[str, float]]:
    """Reload distilgpt2, decompose with the same K + filter, push the toy corpus
    through the importance net, and report mean / max / fraction-active-above-0.1 per matrix.
    """
    cfg = ckpt["config"]
    target, tok = models.load_hf_model(cfg["model_name"], device="cpu")
    refs = list(models.iter_linear_weights(target, name_filter=cfg["matrix_filter"]))
    decomposed = decompose_model(target, refs, K=cfg["K"])
    # Reload weights from checkpoint into banks.
    for name, mod in decomposed.decomposed_modules.items():
        st = ckpt["decomposed_banks"][name]
        mod.bank.U.data.copy_(st["U"])
        mod.bank.V.data.copy_(st["V"])

    matrix_K = {mid: cfg["K"] for mid in decomposed.decomposed_modules}
    pooled_dim = _resolve(target, cfg["pooled_layer"]).weight.shape[-1]
    imp = importance.CausalImportanceNet(
        input_dim=pooled_dim,
        matrix_K=matrix_K,
        hidden=cfg["importance_hidden"],
        depth=cfg["importance_depth"],
    )
    imp.load_state_dict(ckpt["importance_net"])

    batch = next(
        data.toy_corpus_batches(tok, data.TINY_TOY_CORPUS, batch_size=n_examples, seq_len=cfg["seq_len"])
    )
    with torch.no_grad():
        pooled = _resolve(target, cfg["pooled_layer"])(batch).mean(dim=1)
        masks = imp(pooled)

    out = {}
    for name, m in masks.items():
        out[name] = {
            "mean": float(m.mean()),
            "max": float(m.max()),
            "frac_active>0.1": float((m > 0.1).float().mean()),
            "frac_active>0.5": float((m > 0.5).float().mean()),
        }
    return out


def _resolve(root, dotted: str):
    cur = root
    for part in dotted.split("."):
        cur = cur[int(part)] if part.isdigit() else getattr(cur, part)
    return cur


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()

    ckpt = load_run(args.run_dir)
    print(f"# Run: {args.run_dir}")
    print(f"# Config: {json.dumps(ckpt['config'], indent=2)}")

    print("\n## Reconstructed-weight Frobenius norms")
    for name, fro in reconstruction_table(ckpt["decomposed_banks"]):
        print(f"  {name:50s}  {fro:8.3f}")

    print("\n## Mask statistics (over toy corpus)")
    stats = mask_stats(ckpt)
    for name, s in stats.items():
        print(
            f"  {name:50s}  mean={s['mean']:.3f}  max={s['max']:.3f}  "
            f"active>0.1={s['frac_active>0.1']:.2f}  active>0.5={s['frac_active>0.5']:.2f}"
        )


if __name__ == "__main__":
    main()
