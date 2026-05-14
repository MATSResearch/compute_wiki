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

## Challenge exercises

Because this is a stub, the exercises below double as scoping and implementation milestones — finishing the Tier-1 design exercises is essentially the precondition for writing any code. IOI = Indirect Object Identification ("When John and Mary went to the store, John gave a drink to" → " Mary"); SAE = Sparse Autoencoder.

### Tier 1 — design exercises (no code)

1. **Model-choice sanity check.** Generate 100 IOI prompts (ABBA + BABA name orders, balanced subject pool). Run them through Gemma 3 1B (base) and Gemma 3 4B (base). Report top-1 accuracy of the indirect object and mean logit-margin over the second name. Decide and write down which model the project should use, with one paragraph of justification.
2. **Comparison metric.** Pick *one* of: (a) cosine similarity of feature decoder direction with the GPT-2 name-mover head's output direction, (b) causal-mediation Δ on a contrast pair, (c) activation correlation across IOI vs. non-IOI prompts. Write a one-page rationale referencing [`docs/papers/ioi_summary.md`](docs/papers/ioi_summary.md) and the trade-offs (cost, interpretability, robustness to circuit-smearing).
3. **Tokenization audit.** Pick 20 common English first names. Tokenize each with the Gemma 3 tokenizer in three contexts: bare (` John`), sentence-initial (`John went...`), and possessive (` John's`). How many produce a single token in each context? This determines which names are usable in IOI prompts. Document the safe-name list.

### Tier 2 — implementation milestones

4. **IOI prompt generator.** Implement `ioi_prompts.generate(n, name_pool, template_pool, order)` returning `{prompt, indirect_object, subject, distractor}` records. Verify that the indirect-object token is recoverable via single-token tokenization (see Exercise 3). Save a probe set as `data/ioi_prompts.jsonl`.
5. **Pooled feature stats.** Pool SAE last-token activations across N=1000 IOI prompts at one layer (start with layer 12). Report the top-10 features by **mean** activation and the top-10 by **variance**. Add a matched control: same stats over N=1000 random Wikipedia prompts. Features active in IOI but not control are your candidates. Save the table to `outputs/run_<ts>/ioi_features.json`.
6. **Multi-layer feature handoff.** Extend Exercise 5 to layers {6, 12, 18}. For each layer, list top-5 IOI-distinctive features (above some threshold over control). Is there a clean handoff (early layers = "names mentioned", late = "answer chosen") or a smeared distribution? Visualize with a heatmap.

### Tier 3 — research-grade extensions

7. **Behavioral ablation.** Take the top-3 candidate features from Exercise 5. Use [`example_1_gemma_scope`](../example_1_gemma_scope/)-style residual ablation and report the effect on held-out IOI accuracy and margin. Compare to ablating a randomly selected SAE feature as a null.
8. **Order invariance.** Compute candidate-feature activation separately on ABBA and BABA prompts. A "name-mover" feature should be invariant to order; a "first-name-detector" feature should not. Use this asymmetry to classify your candidates.
9. **Bridge to head-level circuit.** Take the canonical GPT-2 IOI circuit (name-mover, S-inhibition, induction heads from Wang et al. 2022) and, in Gemma 3 1B's analogous mid-layer attention heads, decompose their output direction in the SAE's decoder basis. Report which SAE features overlap with which heads. This is the bridge between head-level and feature-level circuit views.

## Last verified

2026-05-05 — stub only, no code.
