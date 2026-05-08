# Example 3 — IOI at the Feature Level (planned, stub only)

**Status:** stub. Folder + README + paper summary only. Code not yet written.

## What this will be

A toy mech-interp example that ports the canonical **Indirect Object Identification (IOI)** task — Wang, Variengien, Conmy, Shlegeris, Steinhardt 2022 ("Interpretability in the Wild") — from GPT-2 to **Gemma 3 1B (base)**, then maps the IOI circuit to **Gemma Scope 2 SAE features** at the relevant layers.

## Expected scope

- Generate IOI prompts ("When John and Mary went to the store, John gave a drink to" → " Mary").
- Run Gemma 3 1B with Gemma Scope 2 residual SAEs hooked at several mid/late layers (default: layers 6, 12, 18 — distributed through the network).
- For each (prompt, layer) pair, identify SAE features whose activation correlates with the correct vs. incorrect name prediction.
- Compare the per-layer feature set to the canonical attention-head circuit from Wang et al.
- Produce a summary table: layer → top-features-for-IOI, plus a notebook-style narrative.

## Why example_3 (not example_2)

The numbering is deliberate:

- **example_1_gemma_scope** — single-prompt feature attribution. Uses an SAE.
- **example_2_vpd** — parameter-space decomposition. Trains a method.
- **example_3_ioi_features** — circuit-level analysis spanning many prompts and several layers, contrasting feature-level findings with attention-head-level findings. Uses an SAE *and* requires more setup than example_1.

## Key design questions to settle before building

1. **Does Gemma 3 1B even do IOI well?** The task assumes the model strongly prefers the indirect object. GPT-2-small does; need to verify Gemma 3 1B does too. If not, use a slightly larger Gemma 3 (4B) or different task.
2. **Per-prompt or pooled feature stats?** Per-prompt is more expensive; pooled (mean activations across many IOI prompts) is faster and matches how the original IOI paper analyzed heads.
3. **Comparison metric to head-level circuit.** Cosine of feature decoder direction with the name-mover head's output direction? Causal mediation? Pick one and stick with it for the toy.

## Why deferring code

Building this well needs (a) Gemma 3 1B IOI sanity check, (b) IOI prompt generation utilities (the Wang et al. pattern is standard but has gotchas around tokenization), (c) multi-layer SAE coordination. Worth scoping in a follow-up turn rather than rolling into the same patch as example_1.

## See also

- [`docs/papers/ioi_summary.md`](docs/papers/ioi_summary.md) — paper summary.
- [`../example_1_gemma_scope/`](../example_1_gemma_scope/) — single-prompt SAE attribution.
- [`../../components/`](../../components/) — `mi_components` for hooks, run dirs, config.

## Last verified

2026-05-05 — stub only, no code.
