# Mech Interp Project Templates

Starter scaffolds for mechanistic interpretability research projects.

## Layout

```
mech_interp/
├── components/                 # mi_components: project-agnostic infra
│   ├── src/mi_components/
│   │   ├── models.py           # load HF / TransformerLens models, iterate weight matrices
│   │   ├── hooks.py            # named-activation capture + raw output patching
│   │   ├── data.py             # tiny tokenized text-loader for toy training
│   │   ├── runs.py             # timestamped run dirs, metadata.json, checkpoints
│   │   ├── config.py           # dataclass-based config loader (no Hydra dep)
│   │   ├── tracking.py         # wandb wrapper that no-ops gracefully without wandb
│   │   ├── training.py         # generic gradient-step / eval-loop helpers
│   │   ├── metrics.py          # KL/JS divergence, logit-diff, target-rank, top-k acc, faithfulness
│   │   ├── tokens.py           # leading-space-aware token id lookup, contrast pair builder
│   │   ├── interventions.py    # zero/mean/resample ablation, projection-out, steering
│   │   ├── dla.py              # generic direct logit attribution against any direction or basis
│   │   ├── decomposition.py    # SVD, PCA, low-rank approx, projection helpers
│   │   ├── activations.py      # bulk activation collection, online mean/std (Welford)
│   │   ├── patching.py         # layer- and position-wise activation patch scans
│   │   ├── prompts.py          # ContrastPrompt batch builder + last-token logit gather
│   │   ├── viz.py              # minimal matplotlib helpers (lines, bars, heatmaps, attn patterns)
│   │   ├── io.py               # JSONL read/write, dataclass <-> JSON
│   │   ├── cache.py            # disk_cache decorator + activation save/load
│   │   ├── sweep.py            # cartesian-product sweep over a dataclass
│   │   ├── seeding.py          # set_seed across Python/NumPy/torch + deterministic mode
│   │   ├── device.py           # pick_device with CUDA/MPS/CPU fallback
│   │   └── profiling.py        # Timer context manager + CUDA memory snapshots
│   ├── pyproject.toml
│   └── tests/
└── example_projects/
    ├── example_1_gemma_scope/  # toy SAE feature attribution + ablation on Gemma 3 1B with Gemma Scope 2
    ├── example_2_vpd/          # toy replication of Bushnaq et al. 2026, "VPD" (Adversarial Parameter Decomposition)
    └── example_3_ioi_features/ # (stub) IOI task at the SAE-feature level on Gemma 3 1B
        ├── README.md
        ├── CLAUDE.md
        ├── pyproject.toml
        ├── docs/papers/        # paper summary
        ├── src/example_2_vpd/  # decomposition, causal importance net, losses, train
        └── tests/
```

## Components vs. example projects

**Components (`mi_components`)** are the boring, reusable plumbing — model loading, activation hooks, run-dir bookkeeping. Stable surface, small, no research-specific logic. Use these in any new mech interp project; they're roughly the bits you'd otherwise rewrite from scratch every time.

**Example projects** are full, runnable mini-papers. Each one:

- Imports `mi_components` for infrastructure.
- Implements the *idea* of one paper at toy scale (a few minutes on a laptop, ~10 minutes on a single GPU).
- Includes a `docs/papers/` summary of what it's replicating.
- Is structured the way the wiki recommends, so it doubles as a worked example of the conventions.

## When *not* to use these

- You need exact-bit-for-bit reproduction of a paper. Toy replications make scaling, dataset, and model-architecture compromises that change numerical results.
- You want a polished library. `mi_components` is intentionally small and unstable; vendoring (copy into your project) is often better than depending on it.
- The thing you want to do is already covered well by an existing library (TransformerLens, nnsight, SAELens). The templates fill the gap *between* those libraries and a runnable research project — not the libraries themselves.

## Existing libraries vs. these components

`mi_components` is **not** a replacement for TransformerLens, nnsight, or SAELens. It's the wiring around them. Specifically:

| Need | Use this |
|---|---|
| Named activation hooks on a HF model | `mi_components.hooks` (thin layer over `register_forward_hook`) |
| Same on a TransformerLens model | TransformerLens directly (`run_with_cache`) |
| SAE training | SAELens directly |
| Model loading + weight-matrix iteration | `mi_components.models` |
| Run organization (timestamped dirs, metadata.json) | `mi_components.runs` |
| Config-from-dataclass + CLI overrides | `mi_components.config` |
| Logging that works with or without wandb | `mi_components.tracking` |
| Toy text data for sanity-check training | `mi_components.data` |
| KL / logit-diff / target-rank metrics with shape checks | `mi_components.metrics` |
| Single-token-id lookup that handles leading spaces | `mi_components.tokens` |
| Zero / mean / resample ablation context managers | `mi_components.interventions` |
| Direct Logit Attribution against any direction or basis | `mi_components.dla` |
| SVD / PCA / low-rank / projection helpers | `mi_components.decomposition` |
| Collect mean activation across a corpus (Welford-stable) | `mi_components.activations` |
| Layer-by-layer activation patching scan | `mi_components.patching` |
| Build a (prompt, correct, wrong) batch for logit-diff | `mi_components.prompts` |
| Quick line/bar/heatmap PNGs in a run dir | `mi_components.viz` |
| JSONL read/write, dataclass round-trip | `mi_components.io` |
| Disk-cache slow ops by hash of args | `mi_components.cache` |
| Cartesian-product hyperparameter sweep | `mi_components.sweep` |
| Reproducible seeding (Python/NumPy/torch) | `mi_components.seeding` |
| CUDA/MPS/CPU device picker with fallback | `mi_components.device` |
| Timing + GPU memory snapshots | `mi_components.profiling` |

See [`../../docs/interpretability/mech-interp.md`](../../docs/interpretability/mech-interp.md) for the broader tooling landscape.
