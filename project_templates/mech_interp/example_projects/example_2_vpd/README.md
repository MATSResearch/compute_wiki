# Example 2 — VPD: Toy Adversarial Parameter Decomposition

A toy-size replication of **VPD** (Adversarial Parameter Decomposition; Bushnaq, Braun, Clive-Griffin, Bussmann, Hu, Ivanitskiy, Linsefors, Sharkey — Goodfire / MATS, May 2026). Paper-style summary in [`docs/papers/vpd_summary.md`](docs/papers/vpd_summary.md).

## What VPD does (one paragraph)

VPD decomposes each weight matrix of a frozen language model into a sum of **rank-one subcomponents**, simultaneously training a **causal importance network** that predicts which subcomponents are needed for any given input. The training objective rewards (a) faithful reconstruction of the original model's outputs, (b) using as few subcomponents as possible per input, and (c) robustness to adversarial mask perturbations. The paper applies this to a 67M-param LM and finds ~10,000 interpretable subcomponents that recover attention algorithms distributed across heads and enable training-free model edits.

## What this toy version does

- Loads frozen **distilgpt2** (~82M params, 24 linear-like weight matrices via `mi_components.models.iter_linear_weights`).
- Decomposes a configurable subset of those matrices (default: 4 matrices in layer 0) into K rank-one subcomponents each (default K=32).
- Trains a small MLP causal-importance network that predicts per-batch masks.
- Uses sigmoid masks + L1 sparsity + a Bernoulli-perturbation adversarial term.
- Logs to `outputs/run_<timestamp>_<tag>/metrics.jsonl`. Saves a checkpoint at the end.

This is **not** a faithful reproduction of the paper's results — it's a working scaffold of the *technique* that fits in a single afternoon and runs on a CPU.

## Quick start

```bash
uv venv --python 3.11
uv pip install -e .[dev]

# Tiny run that finishes in ~1 minute on CPU
uv run python -m example_2_vpd.train steps=50 K=16 batch_size=2 seq_len=32 matrix_filter=transformer.h.0

# A more realistic toy run
uv run python -m example_2_vpd.train steps=500 K=32 matrix_filter=transformer.h.0

# Inspect the result
uv run python -m example_2_vpd.analyze --run-dir outputs/run_<timestamp>_<tag>
```

## File map

| File | Purpose |
|---|---|
| `src/example_2_vpd/decomposition.py` | `SubcomponentBank` (rank-one decomposition of one matrix) and `DecomposedModel` (model wrapper that swaps each target weight with a bank). |
| `src/example_2_vpd/importance.py` | `CausalImportanceNet` — small MLP that maps a pooled input embedding to per-matrix masks. |
| `src/example_2_vpd/losses.py` | Faithfulness (KL on logits), reconstruction, sparsity, adversarial perturbation losses. |
| `src/example_2_vpd/train.py` | Main script. Reads CLI overrides, sets up run dir, trains, logs, checkpoints. |
| `src/example_2_vpd/analyze.py` | Post-training inspection — mask sparsity histograms, top components per input. |
| `tests/test_vpd.py` | Unit tests for the decomposition math. |

## Known toy-vs-paper differences

- **Per-batch masks**, not per-token. The paper uses per-token causal importance.
- **Soft sigmoid gates** with L1 sparsity, not the hard-concrete / stochastic gating used in the paper.
- **Bernoulli-drop adversarial term** stands in for the paper's full optimization-based adversarial mask search.
- **Frozen target model**, only the decomposition + importance net train. The paper trains its own target LM and decomposes it.
- **Far smaller K** (default 32 per matrix) — paper has thousands of subcomponents per matrix.

## When *not* to start from this template

- You want to faithfully reproduce the paper. Use the paper's reference implementation (when released) instead.
- You're working on a model >7B. The single-mask-per-batch design and per-sample einsum forward will be a bottleneck.
- You don't actually need parameter decomposition — for activation-space decomposition, see `02_saes.md` and SAELens.

## Challenge exercises

Use these to test your understanding of parameter decomposition (VPD = Adversarial Parameter Decomposition), causal-importance masks, and the faithfulness/sparsity/adversarial loss trade-off. They assume the "more realistic toy run" (`steps=500 K=32 matrix_filter=transformer.h.0`) as a baseline.

### Tier 1 — predict before you run (no code changes)

1. **Degenerate K.** Set `K=1` so each weight matrix is decomposed into a single rank-1 subcomponent. Predict whether faithfulness KL converges to ~0 or stays high. Justify in one sentence (think: distilgpt2 attention output projection rank).
2. **Saturated K.** Set `K=min(d_in, d_out)` and `sparsity_coef=0`. Predict the limit. Run and verify faithfulness ≈ 0.
3. **Sparsity sweep.** Without running, sketch the expected curve of mean mask sparsity vs. `sparsity_coef` ∈ {0.01, 0.1, 1.0, 10.0}. Where is the "knee" likely to be? Run the sweep with `mi_components.sweep.grid` and compare to your sketch.
4. **Adversarial off.** Predict what the mask histogram looks like with `adv_coef=0`: bimodal (clean 0/1), heavy in the middle (~0.5), or sharply skewed toward 1? Articulate which "shortcut" the importance net would take in each case.

### Tier 2 — small modifications

5. **Attention vs. MLP.** Run two configurations: `matrix_filter=transformer.h.0.attn` and `matrix_filter=transformer.h.0.mlp` with all other settings identical. Which class reaches lower mean mask sparsity at faithfulness KL ≤ 0.05? Form a hypothesis about why (effective rank? task-relevance?).
6. **SVD vs. random init.** In `SubcomponentBank.__init__`, replace the truncated-SVD warm start with `nn.init.normal_(std=0.02)`. Compare loss curves over 500 steps — does SVD init change the *final* solution, the *convergence rate*, or both? Plot both on the same axes.
7. **Mask clustering.** Pick 20 prompts: 10 about geography ("The capital of France is..."), 10 arithmetic ("17 + 23 ="). After training, run each prompt through the importance net and collect its mask vector. Compute pairwise cosine similarity. Report the within-cluster vs. across-cluster mean. Are masks distribution-discriminative?
8. **Disable adversarial.** Train with `adv_coef=0` and compare final mask sparsity and faithfulness to the default. Then inspect the mask histogram — did your prediction in Exercise 4 hold?
9. **Per-token forward.** Convert `CausalImportanceNet` to predict per-token (not per-batch) masks. Sketch the new shape contract in `losses.py` *before* coding. Quantify the improvement in faithfulness at matched sparsity. (Heads-up — this also changes the importance-net input signature; see [`CLAUDE.md`](CLAUDE.md).)

### Tier 3 — research-grade extensions

10. **Hard-concrete gates.** Replace sigmoid + L1 with hard-concrete gates (Louizos, Welling, Kingma 2018). Document one specific numerical issue you hit (e.g. log-stretch parameter range, gradient explosion at the boundary) and how you debugged it.
11. **Cross-distribution monosemanticity.** Train two importance nets on disjoint distributions (e.g. Wikipedia vs. code). For each subcomponent, compute how often it's used in each distribution. Components used in both at similar rates are "general"; components used only in one are "distribution-specific". Report the fraction of each.
12. **Behavioral ablation.** Pick one subcomponent that activates strongly on a clearly identifiable input pattern (find via a mask sweep over a probe set). Zero its mask permanently at inference and measure behavioral delta on (a) the matching pattern, (b) an off-distribution probe set. Does ablation localize?
13. **Beyond layer 0.** Extend `matrix_filter` to decompose layers 0, 3, and 5 simultaneously. Does cross-layer interaction make optimization harder, or do per-layer subcomponents stay disentangled?

## Last verified

2026-05-08 — distilgpt2 loadable, decomposes 24 linear weight matrices, training loop converges on the 100-step `verify` config (`matrix_filter=transformer.h.0.mlp K=16 steps=100 seed=0`). Two-machine reproduction: loss curves and mask-sparsity trajectories match in shape; absolute values drift ≤0.1 between local CPU (torch 2.4) and nathan-lambda CPU (torch 2.11) due to non-associative float reductions in BLAS — this is normal for iterative training and not a regression. Single-pass scripts like `example_1`'s analyze.py *do* reproduce bit-identically; training loops do not.
