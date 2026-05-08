"""Main analysis script: feature attribution + ablation for one prompt.

    uv run python -m example_1_gemma_scope.analyze \
        prompt="The Eiffel Tower is in" target_token=" Paris" \
        layer=12 device=cuda

The flow:

  1. Load Gemma 3 1B (base) and one Gemma Scope 2 residual SAE.
  2. Tokenize the prompt; identify the target token id.
  3. Forward pass; capture residual at the SAE's hooked layer using mi_components.hooks.capture.
  4. Encode last-position residual through the SAE -> feature activations.
  5. Direct Logit Attribution: per-feature contribution to the target token's logit.
  6. Re-run forward with the top feature's contribution subtracted from the residual at the SAE's layer.
  7. Write attribution.json + report.txt to the run dir.

The math is in attribution.py. This file is the orchestration layer.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from mi_components import config as cfg_mod
from mi_components import hooks, runs

from example_1_gemma_scope import attribution, neuronpedia


@dataclass
class AnalyzeConfig:
    # --- Target ---
    model_name: str = "google/gemma-3-1b-pt"
    device: str = "cuda"
    dtype: str = "bfloat16"  # 1B in bf16 fits comfortably; switch to float32 on CPU if needed.

    # --- SAE ---
    # gemma-scope-2-1b-pt-res only ships SAEs at layers {7, 13, 17, 22} (not every layer).
    # If you change sae_layer to a value outside this set, SAELens will raise with the valid list.
    sae_release: str = "gemma-scope-2-1b-pt-res"
    sae_layer: int = 13
    sae_width: str = "16k"  # available: "16k" | "65k" | "262k" | "1m"
    sae_l0: str = "medium"  # "small" | "medium" | "big"

    # --- Prompt ---
    prompt: str = "The Eiffel Tower is in"
    target_token: str = " Paris"  # tokenizer-level string, leading space matters

    # --- Reporting ---
    top_k: int = 10
    ablate_top: bool = True

    # --- Neuronpedia auto-interp labels ---
    fetch_neuronpedia_labels: bool = True
    neuronpedia_model_short: str = "gemma-3-1b"  # Neuronpedia's URL slug for this model
    neuronpedia_timeout_s: float = 3.0

    # --- Output ---
    tag: str = "gemma_scope"
    output_base: str = "outputs"


def _resolve_dtype(name: str) -> torch.dtype:
    return {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}[name]


def _sae_id(layer: int, width: str, l0: str) -> str:
    return f"layer_{layer}_width_{width}_l0_{l0}"


def _residual_hook_name(layer: int) -> str:
    """Path to the layer's output module on a HF Gemma model.

    Gemma 3 follows the standard `model.layers[L]` naming; the residual stream after the
    layer is the layer module's output. For attention/MLP-output SAEs this would change.
    """
    return f"model.layers.{layer}"


def main(argv: list[str] | None = None) -> Path:
    argv = sys.argv[1:] if argv is None else argv
    cfg = cfg_mod.parse_overrides(AnalyzeConfig(), argv)

    run = runs.new_run(tag=cfg.tag, base=cfg.output_base)
    run.write_metadata(cfg_mod.to_dict(cfg))
    print(f"[run] {run.root}")

    # 1) Load model + SAE.
    from sae_lens import SAE
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"[load] {cfg.model_name} on {cfg.device} ({cfg.dtype})")
    tok = AutoTokenizer.from_pretrained(cfg.model_name)
    model = AutoModelForCausalLM.from_pretrained(cfg.model_name, dtype=_resolve_dtype(cfg.dtype))
    model.to(cfg.device)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)

    sae_id = _sae_id(cfg.sae_layer, cfg.sae_width, cfg.sae_l0)
    print(f"[load] SAE {cfg.sae_release} / {sae_id}")
    sae = SAE.from_pretrained(
        release=cfg.sae_release,
        sae_id=sae_id,
        device=cfg.device,
        dtype=cfg.dtype,
    )
    sae.eval()

    # 2) Tokenize. We need both the input ids and the target token id.
    input_ids = tok(cfg.prompt, return_tensors="pt").input_ids.to(cfg.device)
    target_ids = tok(cfg.target_token, add_special_tokens=False).input_ids
    if len(target_ids) != 1:
        # Multi-token target — take the first id and warn. A fellow can fix the prompt or accept this.
        print(f"[warn] target_token={cfg.target_token!r} → {len(target_ids)} tokens; using first id {target_ids[0]}")
    target_id = int(target_ids[0])
    print(f"[prompt] {cfg.prompt!r}  →  target_token={cfg.target_token!r} (id={target_id})")

    # 3) Clean forward pass. Capture residual at the SAE's layer (last position only — saves memory).
    hook_name = _residual_hook_name(cfg.sae_layer)
    with hooks.capture(model, [hook_name]) as acts:
        clean_logits = model(input_ids).logits  # (1, T, V)
    residual = acts[hook_name]  # (1, T, d_model)
    last_pos_residual = residual[0, -1]  # (d_model,)
    last_pos_clean_logits = clean_logits[0, -1]  # (V,)

    target_logit_clean = float(last_pos_clean_logits[target_id])
    target_prob_clean = float(torch.softmax(last_pos_clean_logits, dim=-1)[target_id])
    top_pred_id = int(last_pos_clean_logits.argmax())
    top_pred_str = tok.decode([top_pred_id])
    print(
        f"[clean] target logit={target_logit_clean:.3f} prob={target_prob_clean:.4f}  "
        f"| argmax id={top_pred_id} ({top_pred_str!r})"
    )

    # 4) Encode through SAE. Cast to SAE dtype to be safe.
    with torch.no_grad():
        feat_acts = sae.encode(last_pos_residual.to(sae.W_enc.dtype))  # (d_sae,)
    n_active = int((feat_acts > 0).sum())
    print(f"[sae] {n_active} active features (L0) at last position")

    # 5) Direct Logit Attribution.
    # W_U row for the target token: model.lm_head is Linear(d_model, vocab) with weight (vocab, d_model).
    # Some Gemma models tie embeddings; either way the unembedding row is lm_head.weight[target_id].
    W_U_target = model.lm_head.weight[target_id].detach().to(sae.W_dec.dtype)  # (d_model,)
    contributions = attribution.direct_logit_attribution(
        feat_acts=feat_acts.to(sae.W_dec.dtype),
        sae_decoder_weight=sae.W_dec.detach(),
        unembed_direction=W_U_target,
    )
    top = attribution.top_k_features(
        contributions=contributions,
        feat_acts=feat_acts,
        sae_decoder_weight=sae.W_dec.detach(),
        unembed_direction=W_U_target,
        k=cfg.top_k,
    )

    # 6) Ablation: subtract the top feature's reconstruction contribution from the residual at this layer.
    ablation_result: dict | None = None
    if cfg.ablate_top and len(top) > 0 and abs(top[0].contribution) > 0:
        f_idx = top[0].feature_index
        # Patched residual at the last position only (other positions left intact).
        decoder_dir = sae.W_dec[f_idx].detach().to(residual.dtype)  # (d_model,)
        f_act = float(feat_acts[f_idx])
        new_residual = residual.clone()
        new_residual[0, -1] = new_residual[0, -1] - f_act * decoder_dir

        def patch(_orig):
            return new_residual

        with hooks.patch_output(model, hook_name, new_residual):
            ablated_logits = model(input_ids).logits
        last_pos_ablated_logits = ablated_logits[0, -1]
        target_logit_ablated = float(last_pos_ablated_logits[target_id])
        target_prob_ablated = float(torch.softmax(last_pos_ablated_logits, dim=-1)[target_id])
        new_top_id = int(last_pos_ablated_logits.argmax())
        new_top_str = tok.decode([new_top_id])
        ablation_result = {
            "ablated_feature_index": f_idx,
            "ablated_feature_activation": f_act,
            "target_logit_ablated": target_logit_ablated,
            "target_prob_ablated": target_prob_ablated,
            "delta_logit": target_logit_ablated - target_logit_clean,
            "delta_prob": target_prob_ablated - target_prob_clean,
            "new_top_pred_id": new_top_id,
            "new_top_pred_str": new_top_str,
        }
        print(
            f"[ablate] feature {f_idx} → target logit {target_logit_ablated:.3f} "
            f"(Δ={target_logit_ablated - target_logit_clean:+.3f})  "
            f"prob {target_prob_ablated:.4f} (Δ={target_prob_ablated - target_prob_clean:+.4f})  "
            f"new argmax: {new_top_str!r}"
        )

    # 7) Build the per-feature record. Fetch Neuronpedia auto-interp labels in parallel
    #    if enabled — silently skipped if offline / 5xx / timeout.
    np_source = neuronpedia.gemma_scope_2_source(layer=cfg.sae_layer, site="res", width=cfg.sae_width)
    labels: dict[tuple[str, str, int], str | None] = {}
    if cfg.fetch_neuronpedia_labels and top:
        queries = [(cfg.neuronpedia_model_short, np_source, f.feature_index) for f in top]
        labels = neuronpedia.fetch_explanations_parallel(queries, timeout_per=cfg.neuronpedia_timeout_s)
        n_labelled = sum(1 for v in labels.values() if v)
        print(f"[neuronpedia] fetched {n_labelled}/{len(queries)} auto-interp labels")

    top_features_records = []
    for f in top:
        key = (cfg.neuronpedia_model_short, np_source, f.feature_index)
        top_features_records.append(
            {
                **asdict(f),
                "neuronpedia_url": neuronpedia.dashboard_url(cfg.neuronpedia_model_short, np_source, f.feature_index),
                "auto_interp": labels.get(key),
            }
        )

    report = {
        "config": cfg_mod.to_dict(cfg),
        "prompt": cfg.prompt,
        "target_token": cfg.target_token,
        "target_token_id": target_id,
        "clean": {
            "target_logit": target_logit_clean,
            "target_prob": target_prob_clean,
            "top_pred_id": top_pred_id,
            "top_pred_str": top_pred_str,
        },
        "sae": {
            "release": cfg.sae_release,
            "sae_id": sae_id,
            "neuronpedia_source": np_source,
            "n_active_features": n_active,
        },
        "top_features": top_features_records,
        "ablation": ablation_result,
    }
    (run.root / "attribution.json").write_text(json.dumps(report, indent=2))
    (run.root / "report.txt").write_text(_format_report(report))
    print(f"[done] wrote {run.root}/attribution.json + report.txt")
    return run.root


def _format_report(report: dict) -> str:
    lines = [
        f"Prompt: {report['prompt']!r}",
        f"Target: {report['target_token']!r} (id={report['target_token_id']})",
        f"SAE:    {report['sae']['release']}  /  {report['sae']['sae_id']}",
        "",
        f"Clean target logit={report['clean']['target_logit']:.3f}  prob={report['clean']['target_prob']:.4f}",
        f"Clean argmax: {report['clean']['top_pred_str']!r}",
        f"Active features at last position: {report['sae']['n_active_features']}",
        "",
        f"Top {len(report['top_features'])} features by contribution to target logit:",
    ]
    for f in report["top_features"]:
        lines.append(
            f"  feature {f['feature_index']:6d}  act={f['activation']:+8.3f}  "
            f"contrib={f['contribution']:+8.3f}  align={f['decoder_alignment']:+7.3f}"
        )
        if f.get("auto_interp"):
            lines.append(f"      label: {f['auto_interp']}")
        lines.append(f"      {f['neuronpedia_url']}")
    if report.get("ablation"):
        a = report["ablation"]
        lines += [
            "",
            f"Ablation of feature {a['ablated_feature_index']} (act={a['ablated_feature_activation']:.3f}):",
            f"  target logit: {report['clean']['target_logit']:.3f} -> {a['target_logit_ablated']:.3f}  "
            f"(Δ={a['delta_logit']:+.3f})",
            f"  target prob:  {report['clean']['target_prob']:.4f} -> {a['target_prob_ablated']:.4f}  "
            f"(Δ={a['delta_prob']:+.4f})",
            f"  new argmax:   {a['new_top_pred_str']!r}",
        ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
