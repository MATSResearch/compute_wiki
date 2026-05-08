# `mi_components`

Project-agnostic plumbing for mechanistic interpretability projects. Each module is a **self-contained unit**: use the ones you need, vendor (copy) the ones you want to modify, ignore the rest. Higher-level modules build on the low-level ones (`hooks`, `runs`) but never on each other in surprising ways.

## Install

From this directory:
```bash
uv pip install -e .
```

Or in another project's `pyproject.toml`:
```toml
[tool.uv.sources]
mi-components = { path = "../path/to/mech_interp/components", editable = true }
```

## Modules

### Core infrastructure

| Module | What it gives you |
|---|---|
| `config` | Dataclass → CLI override → file load. Avoids a Hydra dependency. |
| `data` | Tokenized text datasets (HF streaming or a tiny toy corpus for smoke tests). |
| `models` | HF + TransformerLens loading, `iter_linear_weights` walker, `freeze`, `count_params`. |
| `hooks` | `capture(model, names)` and `patch_output(model, name, value_or_fn)` context managers. |
| `runs` | `new_run(tag)` → timestamped `outputs/run_<ts>_<tag>/` dir with metadata.json + checkpoints. |
| `tracking` | `Tracker` writing scalars to wandb (if installed) AND a JSONL file in the run dir. |
| `training` | `grad_step`, `train_loop` — minimal training-loop scaffolding. |

### Interp-specific math

| Module | What it gives you |
|---|---|
| `metrics` | `kl_divergence`, `js_divergence`, `logit_diff`, `target_rank`, `top_k_accuracy`, `cross_entropy_per_token`, `faithfulness`. |
| `tokens` | `target_token_id` (single-token, leading-space-aware), `contrast_pair_ids`, `batch_tokenize`, `last_token_index`. |
| `interventions` | `zero_ablate`, `mean_ablate`, `resample_ablate`, `project_out`, `add_steering_vector` — context managers; hooks always cleaned up. |
| `dla` | Generic Direct Logit Attribution: `attribute_residual`, `per_basis_contribution`, `unembed_direction_diff`. Works for SAE features, attention heads, eigenvectors. |
| `decomposition` | `svd`, `pca`, `low_rank_approx`, `project_onto`, `cosine_similarity`, `gram_schmidt`. |
| `activations` | `collect_mean_activation`, `collect_stacked_activations`, `RunningStats` (Welford) for online mean/std over many batches. |
| `patching` | `activation_patch_scan` (across layers), `position_patch_scan` (across token positions). |
| `prompts` | `ContrastPrompt` dataclass + `build_contrast_batch` + `gather_last_token_logits`. |

### Operations / ergonomics

| Module | What it gives you |
|---|---|
| `viz` | matplotlib helpers: `line_from_jsonl`, `bar`, `heatmap`, `attention_pattern`. (matplotlib is optional — install with `[viz]`.) |
| `io` | `read_jsonl`, `write_jsonl`, `dataclass_to_dict/json`, `dataclass_from_json`. |
| `cache` | `disk_cache` decorator (SHA-256 of args → torch.save/load); `save_activations`/`load_activations`. |
| `sweep` | `grid(default, axes)` cartesian-product sweep over a dataclass config. |
| `seeding` | `set_seed` (Python/NumPy/torch CPU+CUDA), `enable_deterministic_mode`. |
| `device` | `pick_device(prefer=...)` with CUDA → MPS → CPU fallback; `device_summary`. |
| `profiling` | `Timer` context manager (cuda-syncing), `cuda_memory_snapshot`, `reset_cuda_peak_stats`. |

## What's intentionally *not* here

- **SAE training** — use SAELens.
- **TransformerLens architecture rewrites** — use TransformerLens directly when you need its hook points.
- **Distributed training** — use Accelerate / Lightning / your training stack.
- **Hyperparameter optimization (Bayesian, Hyperband)** — use Optuna or Ray Tune. `sweep` only does cartesian product.
- **A real profiler** — use `torch.profiler` or NVIDIA Nsight. `profiling` is for inline checks.
- **Anything paper-specific** — that belongs in `example_projects/`.

## Smoke test

```bash
uv run python -m mi_components._smoke
```

Loads a tiny model, captures one activation, writes a run dir, and exits. If this fails the components are broken before any project-specific code matters.

## Module dependency graph

The deliberate coupling is small. Most modules only depend on `torch`. The internal coupling that does exist:

```
interventions  →  hooks
activations    →  hooks
patching       →  hooks
prompts        →  tokens
```

That's it. You can vendor any individual module by copying its file plus its (at most one) internal dependency.

## Pitfalls and searchable symptoms

- `RuntimeError: shape mismatch` from `metrics.kl_divergence`: the two logit tensors must have the same shape — common bug is comparing a (B, V) clean output with a (B, T, V) patched output. Slice both to the last position first.
- `ValueError: target ' Au' → 2 tokens` from `tokens.target_token_id`: the target tokenizes to multiple ids. Either pick a different target or pass `require_single=False` to take `ids[0]` (and accept that logit_diff is approximate).
- `nan` in mean-ablation activation after pooling: you fed `RunningStats.update_batched` a batch where the activation was already nan — check upstream model output for fp16 underflow first.
- `ImportError: mi_components.viz requires matplotlib`: install with `uv pip install matplotlib` or add the optional dep to your project.
