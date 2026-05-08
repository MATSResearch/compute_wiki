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

## Last verified

2026-05-08 — distilgpt2 loadable, decomposes 24 linear weight matrices, training loop converges on the 100-step `verify` config (`matrix_filter=transformer.h.0.mlp K=16 steps=100 seed=0`). Two-machine reproduction: loss curves and mask-sparsity trajectories match in shape; absolute values drift ≤0.1 between local CPU (torch 2.4) and nathan-lambda CPU (torch 2.11) due to non-associative float reductions in BLAS — this is normal for iterative training and not a regression. Single-pass scripts like `example_1`'s analyze.py *do* reproduce bit-identically; training loops do not.
