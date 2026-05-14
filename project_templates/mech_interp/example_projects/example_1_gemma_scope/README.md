# Example 1 — Gemma Scope 2: Feature Attribution for a Factual Completion

A toy mechanistic-interpretability example. Uses a pretrained **Gemma Scope 2** sparse autoencoder (SAE) on **Gemma 3 1B** (base) to identify which SAE features drive a specific factual completion (default: `"The Eiffel Tower is in"` → `" Paris"`), then ablates the top contributor and shows the prediction shifts.

Paired with [`example_2_vpd`](../example_2_vpd/) to contrast two decomposition styles:

| | example_1_gemma_scope | example_2_vpd |
|---|---|---|
| Decomposition target | model **activations** (residual stream at one layer) | model **parameters** (weight matrices) |
| Pretrained or trained here? | **pretrained** (Gemma Scope) — no training in this example | trained from scratch on the target model |
| Compute | one forward pass + one ablated forward pass | ~100 training steps |
| Primary verb | "interpret" / "attribute" | "decompose" / "edit" |

## What this example does

1. Loads **Gemma 3 1B (base)** and one Gemma Scope 2 residual-stream SAE (default: `layer_13_width_16k_l0_medium`).
2. Tokenizes a prompt + expected target token.
3. Forward pass; captures the residual stream at the SAE's layer using `mi_components.hooks.capture`.
4. Encodes the last-token residual through the SAE → feature activations (16k features, most zero — JumpReLU sparsity).
5. **Direct Logit Attribution (DLA):** for each active feature f, scores `feat_act[f] * (W_dec[f] · W_U[target_token])`. Top features are the ones whose decoder direction most aligns with the unembedding row of the target token.
6. Reports the top-K features with their contributions, **Neuronpedia auto-interp labels** (fetched in parallel via Neuronpedia's JSON API), and dashboard URLs. Labels fail-soft — offline or unavailable labels just leave the field empty rather than crashing the analysis.
7. **Ablation:** subtracts the top feature's contribution from the residual and re-runs the forward pass; reports the new probability of the target token.

## Quick start

```bash
# Authenticate with HuggingFace (Gemma 3 is gated — accept the license at
# https://huggingface.co/google/gemma-3-1b-pt first)
huggingface-cli login

uv venv --python 3.11
uv pip install -e .[dev]

# Run the analysis (first run downloads ~2 GB for the model + a few hundred MB for the SAE)
uv run python -m example_1_gemma_scope.analyze \
    prompt="The Eiffel Tower is in" \
    target_token=" Paris" \
    sae_layer=13 \
    device=cuda

# CPU is supported but slow (~minutes per forward pass for 1B at fp32):
uv run python -m example_1_gemma_scope.analyze device=cpu dtype=float32
```

Output goes to `outputs/run_<timestamp>_<tag>/`:
- `metadata.json` — config used
- `attribution.json` — top features, DLA scores, ablation result
- `report.txt` — human-readable summary

## File map

| File | Purpose |
|---|---|
| `src/example_1_gemma_scope/attribution.py` | SAE encode + Direct Logit Attribution + feature ablation. Pure math, no I/O. |
| `src/example_1_gemma_scope/neuronpedia.py` | Neuronpedia URL helpers + JSON-API fetcher for auto-interp explanations (parallel, fail-soft). |
| `src/example_1_gemma_scope/prompts.py` | Curated `(prompt, target_token)` pairs known to work on Gemma 3 1B base. |
| `src/example_1_gemma_scope/analyze.py` | Main script: load model + SAE, run DLA, ablate, fetch labels, write report. |
| `tests/test_attribution.py` | Unit tests on a hand-built tiny dummy SAE + Neuronpedia URL/fetch tests (no network in CI). |

## Limitations (toy vs. paper-grade)

- **Local attribution only.** DLA at the SAE's layer ignores the transformations that subsequent layers apply to the SAE-decoded residual. For exact attribution use attribution patching or path patching.
- **Single SAE.** A real attribution would use SAEs at every layer and trace contributions through the residual stream.
- **One feature at a time** for ablation. Combinatorial ablation (top-N together) is straightforward to add.
- **No auto-interpretation.** We print Neuronpedia URLs but don't pull labels.

## When *not* to start from this template

- You want the SAE-vs-feature-circuit work that's the bread-and-butter of SAE research today — for that, `example_3_ioi_features` (planned) is closer.
- You're studying instruction-following — switch to `gemma-scope-2-1b-it-res` and the `gemma-3-1b-it` model. The default uses the **base** model because residual-stream features are cleaner without instruction tuning.
- You need bigger models — Gemma Scope 2 covers 270M, 1B, 4B, 12B, 27B. Swap release names like `gemma-scope-2-4b-pt-res` and bump GPU memory.

## Catalog quick-reference (verified against SAELens registry)

For `gemma-scope-2-1b-pt-res`:
- **Layers available:** only `7, 13, 17, 22` — *not* every layer (Gemma Scope 1 was every layer; Gemma Scope 2 1B is sparser).
- **Widths:** `16k`, `65k`, `262k`, `1m`.
- **L0 buckets:** `small`, `medium`, `big` (note: `big`, not `large` — easy to get wrong).
- **sae_id format:** `layer_<L>_width_<W>_l0_<bucket>`.

Other releases (e.g. `gemma-scope-2-4b-pt-res`, `-mlp`, `-att`, `-it-` variants) likely have different layer coverage; check via `from sae_lens.saes.sae import get_pretrained_saes_directory; get_pretrained_saes_directory()['<release>'].saes_map.keys()`.

## Smoke result

Verified 2026-05-07 on CPU with default config (reproduced bit-identical numbers across two machines on 2026-05-05 and 2026-05-07):
```
Prompt: 'The Eiffel Tower is in' → target ' Paris'
Clean target prob: 0.4539  (argmax: ' Paris')
44 active features at last position
Top feature 21 (label: "location and confinement"): contributes +62.2 to ' Paris' logit
Ablating feature 21: prob 0.4539 → 0.3507 (Δ=−0.103); argmax still ' Paris'
6/10 top features had Neuronpedia auto-interp labels (others were unlabelled at fetch time)
```

## Challenge exercises

Use these to check your understanding of SAE feature attribution, Direct Logit Attribution (DLA = activation × decoder-direction · unembedding-row), and feature ablation. They assume the default `("The Eiffel Tower is in", " Paris")` smoke result above as a baseline.

### Tier 1 — predict before you run (no code changes)

1. **Sparsity check.** The SAE has 16k features but the smoke result reports 44 active at the last token. Predict what `(feat_act > 0).sum()` will be on a different prompt of similar length. Then run and compare. Why is the count so low? (Hint: search `JumpReLU` in [`docs/papers/gemma_scope_2_summary.md`](docs/papers/gemma_scope_2_summary.md).)
2. **Ablation direction.** Feature 21 contributes **+62.2** to the `' Paris'` logit. Predict the sign and rough magnitude of the prob shift after zeroing its contribution. Will argmax change? Run and verify against the reported `Δ=−0.103`.
3. **Contribution tail shape.** Predict whether the top-K DLA contributions are heavy-tailed (one feature dominates) or roughly uniform across active features. Sort `contributions.values()` and plot — describe the shape in one sentence.

### Tier 2 — small modifications

4. **Swap the factual pair.** Try `("The capital of Germany is", " Berlin")` and `("2 + 2 =", " 4")`. Does each produce a clean top feature with a sensible Neuronpedia label? Hypothesize why factual-recall vs. arithmetic prompts might attribute differently.
5. **Wider SAE.** Change `sae_id` to `layer_13_width_65k_l0_medium`. Does the top feature still describe "location/Paris-ness"? Does the ablation `Δ` grow, shrink, or stay similar? (Predict before running — wider SAE = more features but each is more specialized.)
6. **Joint top-K ablation.** Replace the single-feature ablation with simultaneous ablation of the top-3 features. Is the resulting prob drop equal to the sum of individual drops? Explain in one paragraph why nonlinearity in subsequent layers makes this generally not additive.
7. **Logit-difference attribution.** Replace `W_U[target_token]` with `W_U[target_token] - W_U[contrast_token]` (e.g. `' London'` as contrast) in `attribution.py`. Which formulation gives a crisper top-feature list? Why does the contrast pair help?
8. **Instruction-tuned variant.** Switch model to `google/gemma-3-1b-it` and SAE release to `gemma-scope-2-1b-it-res` (verify availability first). Does the same prompt still produce a clean top feature, or do you see more diffuse attribution? Connect this to the design note in [`CLAUDE.md`](CLAUDE.md) about base vs. IT.

### Tier 3 — research-grade extensions

9. **Attribution patching.** Implement the one-backward-pass linear approximation of activation patching (Syed, Rager, Conmy 2023). Apply it to the same 16k features and compare the top-10 ranking to your brute-force ablation. Report rank correlation and discuss disagreements.
10. **Multi-layer DLA sweep.** Loop over SAE layers `{7, 13, 17, 22}` (the only ones available for `gemma-scope-2-1b-pt-res`) and report top feature + DLA contribution at each. At which layer does the `' Paris'` prediction become "decided"? Plot per-layer top-feature contribution as a bar chart in the run dir.
11. **Probe a suspect feature.** Pick a feature whose Neuronpedia auto-interp label feels wrong (or is missing). Hand-build 10 prompts where you expect it to fire and 10 where you don't. Compute activation on each and report precision/recall against your hypothesis. Document a revised label in a new `.md` note.

## Last verified

2026-05-07 — SAELens 6.x API (`SAE.from_pretrained` returns SAE directly). Gemma Scope 2 release `gemma-scope-2-1b-pt-res` with sae_id format `layer_<L>_width_<W>_l0_<small|medium|big>`, layers in {7,13,17,22}, widths {16k, 65k, 262k, 1m}. Default-config CPU run reproduces deterministically across machines (same prob/contribution/feature-id to all printed digits).
