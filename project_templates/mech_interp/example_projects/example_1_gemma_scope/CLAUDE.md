# CLAUDE.md — example_1_gemma_scope

A toy mech-interp example using **Gemma Scope 2** SAEs on **Gemma 3 1B (base)**. Demonstrates the bread-and-butter SAE workflow: pick a factual prompt, find which features fire at the last token, score them by direct logit attribution to the correct next token, then ablate the top one and show the prediction shifts.

Paired with `example_2_vpd` to contrast activation-space decomposition (this) vs parameter-space decomposition (VPD). No training here — single forward passes only.

## Scope (don't expand without asking)

- One prompt at a time (or a small batch of independent prompts).
- One residual-stream SAE at one layer (default `layer_13_width_16k_l0_medium` — mid-network, modest sparsity). The `gemma-scope-2-1b-pt-res` release only ships SAEs at layers {7, 13, 17, 22}, not every layer — pick from that set.
- Direct Logit Attribution (DLA) only. No attribution patching, no path patching, no IG.
- Ablation by zeroing out the feature contribution in the residual stream at the SAE's hooked layer.

## Auth + download

- Gemma 3 1B requires accepting the license at https://huggingface.co/google/gemma-3-1b-pt and being logged in (`huggingface-cli login` or `HF_TOKEN` env var).
- Model weights are ~2 GB; SAE weights are a few hundred MB. First run downloads them.

## Design notes

- We use HF transformers directly (not TransformerLens). The Gemma Scope SAEs are trained on the standard HF residual stream — `model.model.layers[L]` output — so going through TL adds an unnecessary architecture rewrite for a single-prompt analysis.
- The residual hook is captured via `mi_components.hooks.capture` so we don't reimplement hook bookkeeping.
- DLA math: contribution of feature f = `feat_act[f] * (W_dec[f] · W_U[target_token])`. This ignores the post-SAE residual contributions of later layers; it's a *local* attribution at the SAE's layer. Document this clearly — the toy version does not chase the residual through subsequent layers.
- SAELens release names: Gemma Scope 2 uses underscores in sae_id (`layer_13_width_16k_l0_medium`), unlike Gemma Scope 1 which used slashes (`layer_13/width_16k/canonical`). If a fellow copy-pastes from a Gemma Scope 1 tutorial, this is the most likely first error. The L0 bucket is also `big` (not `large`) — another easy paste-error.

## Don't

- Don't add training. This example is deliberately no-training.
- Don't default to `gemma-scope-2-12b-*` or `-27b-*` — they don't fit comfortably on a single 24 GB GPU. The 1B and 4B variants are the right toy targets.
- Don't claim DLA is exact. It's an approximation that ignores the contribution of subsequent layers' transformations on the SAE-decoded residual. Toy version explicitly accepts this.
- The analyze script DOES make Neuronpedia HTTP calls to fetch auto-interp labels (it's worth the dependency for how much more readable the report becomes), but every fetch must fail-soft — return None on URLError/HTTPError/timeout/JSON-parse, never crash. The `neuronpedia.py` module enforces this. If a fellow extends label fetching elsewhere, preserve that contract.
