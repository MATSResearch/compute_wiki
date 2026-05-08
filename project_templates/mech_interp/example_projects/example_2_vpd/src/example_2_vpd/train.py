"""VPD training loop: load distilgpt2, decompose a chosen subset of weights, train.

    uv run python -m example_2_vpd.train [key=value ...]

Run dirs go to outputs/run_YYYYMMDD_HHMMSS_<tag>/ with metadata.json, metrics.jsonl,
and a final checkpoint of the decomposed banks + importance net.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import torch

from mi_components import config as cfg_mod
from mi_components import data, hooks, models, runs, tracking

from example_2_vpd import importance, losses
from example_2_vpd.decomposition import decompose_model


@dataclass
class TrainConfig:
    # --- Target model ---
    model_name: str = "distilgpt2"
    device: str = "cpu"  # "cuda" if available
    dtype: str = "float32"

    # --- Decomposition ---
    K: int = 32
    matrix_filter: str = "transformer.h.0"  # substring filter for which matrices to decompose
    pooled_layer: str = "transformer.wte"  # module whose output is mean-pooled for the importance net

    # --- Importance net ---
    importance_hidden: int = 128
    importance_depth: int = 2

    # --- Training ---
    steps: int = 200
    lr: float = 1e-3
    batch_size: int = 4
    seq_len: int = 64
    grad_clip: float = 1.0
    log_every: int = 10
    seed: int = 0

    # --- Loss weights ---
    w_full: float = 1.0
    w_masked: float = 1.0
    w_recon: float = 0.01
    w_sparsity: float = 0.05
    w_adv: float = 0.5
    adv_drop_prob: float = 0.5

    # --- Output ---
    tag: str = "vpd"
    use_wandb: bool = False
    output_base: str = "outputs"


def _resolve_dtype(name: str) -> torch.dtype:
    return {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}[name]


def main(argv: list[str] | None = None) -> Path:
    argv = sys.argv[1:] if argv is None else argv
    cfg = cfg_mod.parse_overrides(TrainConfig(), argv)
    torch.manual_seed(cfg.seed)

    run = runs.new_run(tag=cfg.tag, base=cfg.output_base)
    run.write_metadata(cfg_mod.to_dict(cfg))
    print(f"[run] {run.root}")

    # 1) Load + freeze target model.
    target, tok = models.load_hf_model(cfg.model_name, device=cfg.device, dtype=_resolve_dtype(cfg.dtype))
    models.freeze(target)

    # 2) Pick weights to decompose, build decomposed twin (mutates target in-place).
    weight_refs = list(models.iter_linear_weights(target, name_filter=cfg.matrix_filter))
    if not weight_refs:
        raise RuntimeError(f"matrix_filter={cfg.matrix_filter!r} matched no weight matrices")
    print(f"[decompose] {len(weight_refs)} weight matrices, K={cfg.K}: {[r.id for r in weight_refs]}")
    decomposed = decompose_model(target, weight_refs, K=cfg.K)

    # 3) Build importance net. Pooled summary dim = embedding hidden size.
    embed_module = _resolve(target, cfg.pooled_layer)
    pooled_dim = embed_module.weight.shape[-1]
    matrix_K = {mid: cfg.K for mid in decomposed.decomposed_modules}
    imp_net = importance.CausalImportanceNet(
        input_dim=pooled_dim,
        matrix_K=matrix_K,
        hidden=cfg.importance_hidden,
        depth=cfg.importance_depth,
    ).to(cfg.device)

    # 4) Optimizer over decomposition banks + importance net.
    trainable_params = decomposed.trainable_parameters() + list(imp_net.parameters())
    optim = torch.optim.AdamW(trainable_params, lr=cfg.lr)
    print(f"[optim] {sum(p.numel() for p in trainable_params):,} trainable params")

    # 5) Data: tiny in-memory toy corpus avoids any network calls during smoke runs.
    batches = data.toy_corpus_batches(
        tok, data.TINY_TOY_CORPUS, batch_size=cfg.batch_size, seq_len=cfg.seq_len, device=cfg.device
    )

    # 6) Helpers used by the loss.
    def get_target_logits_and_pooled(input_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Run the original (now-mutated) model with all-ones masks to get target logits + pooled embed."""
        # All-ones masks ≈ original behaviour at init, drifts during training. We freeze
        # a separate copy of the model to keep "target" stable. Done outside this fn.
        raise RuntimeError("unused — see closure below")  # pragma: no cover

    # The frozen target needs to be a *separate* model so its outputs don't change as we
    # train the decomposition. Re-load it so we have an untouched copy.
    frozen_target, _ = models.load_hf_model(cfg.model_name, device=cfg.device, dtype=_resolve_dtype(cfg.dtype))
    models.freeze(frozen_target)
    frozen_embed = _resolve(frozen_target, cfg.pooled_layer)

    def forward_decomposed(ids: torch.Tensor) -> torch.Tensor:
        return target(ids).logits

    weights = losses.LossWeights(
        full=cfg.w_full,
        masked=cfg.w_masked,
        recon=cfg.w_recon,
        sparsity=cfg.w_sparsity,
        adv=cfg.w_adv,
    )

    tracker = tracking.Tracker(
        run.root,
        project="example_2_vpd",
        run_name=run.tag,
        config=cfg_mod.to_dict(cfg),
        use_wandb=cfg.use_wandb,
    )

    # 7) Training loop.
    try:
        for step in range(1, cfg.steps + 1):
            input_ids = next(batches)

            with torch.no_grad():
                target_logits = frozen_target(input_ids).logits
                pooled = frozen_embed(input_ids).mean(dim=1)  # (B, d_model)

            optim.zero_grad(set_to_none=True)
            total_loss, br = losses.compute_vpd_loss(
                target_logits=target_logits,
                decomposed_model=decomposed,
                importance_net=imp_net,
                pooled_summary=pooled,
                input_ids=input_ids,
                forward_decomposed_fn=forward_decomposed,
                weights=weights,
                adv_drop_prob=cfg.adv_drop_prob,
            )
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable_params, max_norm=cfg.grad_clip)
            optim.step()

            if step % cfg.log_every == 0 or step == 1 or step == cfg.steps:
                tracker.log(
                    {
                        "loss/total": br.total,
                        "loss/full": br.full,
                        "loss/masked": br.masked,
                        "loss/recon": br.recon,
                        "loss/adv": br.adv,
                        "mask/mean": br.mean_mask,
                    },
                    step=step,
                )
    finally:
        tracker.close()

    # 8) Save final checkpoint.
    state = {
        "config": cfg_mod.to_dict(cfg),
        "decomposed_banks": {
            name: {"U": mod.bank.U.detach().cpu(), "V": mod.bank.V.detach().cpu()}
            for name, mod in decomposed.decomposed_modules.items()
        },
        "importance_net": imp_net.state_dict(),
    }
    run.save_checkpoint("final", state)
    print(f"[done] checkpoint saved under {run.root}/checkpoints/final.pt")
    return run.root


def _resolve(root: torch.nn.Module, dotted: str) -> torch.nn.Module:
    cur: torch.nn.Module = root
    for part in dotted.split("."):
        cur = cur[int(part)] if part.isdigit() else getattr(cur, part)
    return cur


if __name__ == "__main__":
    main()
