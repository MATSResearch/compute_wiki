---
tags:
  - infrastructure
---

# Experiment Tracking and Reproducibility

How to organize and track safety research experiments. Tooling here is mostly general-ML rather than safety-specific, but the *patterns* matter — interp/eval research has reproducibility quirks worth calling out.

## At a glance

| You want to… | Use |
|---|---|
| Track training / finetuning runs (loss curves, etc.) | **wandb** (Weights & Biases) |
| Track eval runs with rich logs and transcript inspection | **Inspect View** (built into Inspect AI; see [`evals.md`](../evaluation/evals.md)) |
| Local / offline experiment tracking | **wandb** in offline mode, or **TensorBoard** |
| Configuration management for experiments with many knobs | **Hydra** (overkill for many) or simple `dataclass` configs |
| Versioning datasets / model artifacts | **HuggingFace Hub**, **wandb Artifacts**, **DVC** |
| Reproducibility-by-environment | `uv` lockfile (preferred for new projects), `pip freeze`, conda |
| Notebook → script promotion | hand-rolled, or **nbconvert** |

## Weights & Biases (wandb)

Aliases: `wandb` on PyPI, "W&B", "Weights & Biases".

**What it is.** The default cloud experiment tracker for ML research. Logs scalars, images, tables, system metrics; supports sweeps, artifacts, reports.

**When to use it:**
- Training runs (SAE training, finetuning, probe training).
- Anything where you want to compare runs across hyperparameters.
- Sharing results with a team — wandb reports are good for write-ups.

**When *not* to use it:**
- Pure eval runs — Inspect View is better suited (see below).
- You can't send data to a cloud service — use offline mode (`WANDB_MODE=offline`) or TensorBoard.

**Pitfalls:**
- **`wandb.init()` in a Jupyter cell + restart loop creates orphan runs.** Use `wandb.finish()` at the end of each cell, or set `reinit=True`.
- **Logging too much.** Logging activations or large tensors per step kills the dashboard. Use `wandb.Histogram` for distributions; sample sparsely.
- **Artifact size.** wandb stores up to a per-plan storage quota (the free-tier figure has changed over time and sources disagree — check current pricing); large model checkpoints fill it fast. Use HF Hub for big artifacts.
- **`wandb sync` from offline.** If you ran offline, sync with `wandb sync wandb/offline-run-...`. Easy to forget; runs sit unsynced.

## Inspect View (for eval logs)

Aliases: "Inspect View", `inspect view`, the built-in Inspect AI log viewer. See [`evals.md`](../evaluation/evals.md).

**What it is.** A web UI bundled with Inspect AI that visualizes eval logs (every sample, every turn, every tool call) with token-level transcripts.

**When to use it:** Inspecting any Inspect eval run. Standard format that other safety researchers can read.

## TensorBoard

`tensorboard` — works fine, fully local. Lighter weight than wandb. Use if your institution forbids cloud telemetry.

## Hydra

Aliases: `hydra-core` on PyPI, `facebookresearch/hydra`, "the YAML config thing".

**What it is.** A configuration management library — composable YAML configs with command-line overrides. Heavily used in academic ML (e.g. PyTorch Lightning ecosystems).

**When to use it:**
- You have ≥10 hyperparameters and want tidy override syntax (`python run.py model=llama-3 sae.l0=64`).
- You're running sweeps with a lot of variants.

**When *not* to use it:**
- Small experiments — a `@dataclass` config in `config.py` is faster.
- You hate YAML — argparse + dataclass is cleaner for some tastes.

**Pitfalls:**
- **Hydra changes the CWD by default** — to a per-run directory. This breaks relative paths in your code; set `hydra.job.chdir=False` if it's annoying.
- **Composition order matters.** Defaults list ordering affects what overrides what; debugging is grim. Print resolved config (`OmegaConf.to_yaml(cfg)`) early.

## Simple dataclass configs (recommended default)

For most safety research projects, this is enough:

```python
from dataclasses import dataclass

@dataclass
class Config:
    model: str = "meta-llama/Llama-3.1-8B-Instruct"
    layer: int = 15
    n_examples: int = 1000
    seed: int = 0
    output_dir: str = "outputs"

# parse from argparse, env vars, or hand-construct
```

Pair with `tyro` (`tyro.cli(Config)`) for instant CLI from a dataclass.

## Run organization (the patterns that actually save time)

These follow Nathan's preferences (see project CLAUDE.md / global instructions): timestamped run directories that are self-contained.

**Recommended layout:**

```
recommended_tooling/
├── outputs/
│   ├── run_20260430_143022_compare_steering/
│   │   ├── metadata.json     # config, model IDs, git SHA
│   │   ├── results.parquet
│   │   ├── plots/
│   │   └── stdout.log
│   └── run_20260430_151234_probe_sweep/
│       └── ...
├── data/                     # input datasets
└── ...
```

**Each run directory contains:**
- `metadata.json` — full config, model IDs (with version), git SHA of code, start/end timestamps.
- The output artifacts (parquet, csv, pickle, plots).
- Any logs.

**Why this matters:**
- You can `rm -rf` an old run without affecting others.
- A run is self-documenting: anyone can open `metadata.json` and see what was run.
- Plots live with the run that produced them, not in a global plot folder.

## Reproducibility checklist for safety research

When you'd like a result to be reproducible by someone else (or future-you):

- [ ] **Pin model versions.** `claude-sonnet-4-6` not `claude-sonnet`. For open-weight, log the HuggingFace revision SHA if possible.
- [ ] **Pin code version.** Log `git rev-parse HEAD` in `metadata.json`.
- [ ] **Pin dependencies.** `uv lock` and commit `uv.lock`. (`pip freeze > requirements.lock.txt` if not on uv.)
- [ ] **Set seeds.** PyTorch (`torch.manual_seed`), NumPy, Python `random`, and dataset shuffling. Log them.
- [ ] **Temperature 0 for evals** (or log seeds + sampling params).
- [ ] **Log the prompt template / chat template** used. Wrong template silently changes results.
- [ ] **Log the dataset version.** `datasets` library has `version` field; HF dataset cards have revisions.
- [ ] **Save raw outputs, not just summary stats.** A score of "0.73" is unreproducible-by-eye; the per-sample completions let you sanity-check.

## Stochasticity gotchas specific to safety research

- **Closed-API non-determinism.** `temperature=0` doesn't give you bit-identical outputs across calls on most providers. Run multiple seeds even at temp=0.
- **vLLM determinism.** vLLM with batched generation is non-deterministic by default (KV cache reuse + batching introduces order-dependent floating point). Use `enforce_eager=True` and `seed` for closer-to-deterministic behavior; expect it to be slower.
- **Tokenizer changes mid-run.** A subtle gotcha: if you upgrade `transformers` mid-project, some tokenizers change special-token handling. Pin and document.

## Notebooks vs scripts

- **Notebooks** are great for exploratory work and visualization; bad for runs you want to reproduce or schedule.
- **Promote to scripts** before doing anything you'd want to rerun: convert via `nbconvert` or refactor manually.
- **For interp work**, notebooks remain dominant — `circuitsvis` and the interactive feedback loop are notebook-native. Just `wandb.init()` from notebook + commit the notebook to git so the artifact is recoverable.

## Cross-cutting pitfalls

- **"It worked yesterday" — what changed?** A model snapshot rotated. A library was upgraded. A dataset was re-released. Without pinning, debugging is detective work.
- **Cache poisoning** — a stale cached API response from an experiment that used a different prompt template can give you confusing results. Clear the cache when prompts change.
- **Output filename collisions.** `output.csv` written by two scripts to the same dir = lost work. Always use timestamped subdirs.
- **Logging cost.** Computing token counts and per-sample costs adds up; in tight loops, log aggregate counts, not per-sample.

## Cross-references

- Eval logs (Inspect View): [`evals.md`](../evaluation/evals.md).
- Caching for API experiments: [`safety-toolkits.md`](safety-toolkits.md).
- Compute infra (where to run these tracked experiments): [`compute.md`](compute.md).
- RL-specific things to log (reward distribution, KL, completion length): [`rl-training.md`](../oversight-and-control/rl-training.md).

---

## Common questions

### Do I need wandb?

Strongly recommended for any training run (RL, finetuning, SAE training). Almost optional for pure eval work — Inspect View covers eval logs better. For local-only / no-cloud, use `WANDB_MODE=offline` and `wandb sync` later, or fall back to TensorBoard. Solo prototyping with no need to share runs: skip it; you'll add it when you want to compare runs.

### How should I structure my output directory?

Per Nathan's project conventions: `outputs/run_YYYYMMDD_HHMMSS_short_descriptor/` per run. Each run directory contains `metadata.json` (full config + git SHA + model versions + start/end times), the artifacts (parquet / csv / pickle), `plots/` subdir, and `stdout.log`. Self-contained — `rm -rf` an old run without affecting others.

### How do I make my run reproducible?

Pin: model versions (use specific snapshot IDs, e.g. `claude-sonnet-4-6`, not `claude-sonnet`), code (`git rev-parse HEAD` in `metadata.json`), dependencies (`uv lock` and commit `uv.lock`), random seeds (PyTorch + NumPy + Python `random` + dataset shuffling), prompt / chat templates, dataset versions. Save raw outputs, not just summary stats.

### Hydra vs simple dataclass configs — which?

Default to a `@dataclass` config + `tyro.cli(Config)` — cleaner for most projects. Use **Hydra** only if you have ≥10 hyperparameters and want composable YAML configs with sweep machinery. Hydra changes the CWD by default (set `hydra.job.chdir=False` to disable) and has a learning curve.

### How do I sync wandb runs from offline mode?

After your run completes: `wandb sync wandb/offline-run-...` (the offline run dir gets created when `WANDB_MODE=offline`). Easy to forget; runs sit unsynced until you do this. For automated workflows, add `wandb sync --sync-all` to a post-run script.

### Should I develop in a Jupyter notebook or a script?

**Notebook** for exploration, mech interp visualization (`circuitsvis` is notebook-native), looking at individual examples. **Script** for anything you'd rerun, schedule, or reproduce. Promote from notebook to script as soon as the analysis stabilizes — `jupyter nbconvert --to script` for the lazy version, manual refactor for the better one.

### Why does my temp=0 OpenAI/Anthropic call still vary?

Closed APIs aren't bit-deterministic even at temp 0 — backend non-determinism (batched FP arithmetic, etc.). Run multiple seeds even at temp=0 and report distributions. For higher reproducibility on the open side, vLLM with `enforce_eager=True` and a fixed seed is closer-to-deterministic but slower.

### How do I track multiple model comparisons in wandb?

Use **wandb groups**: `wandb.init(project="my-eval", group="cross-model-comparison", name=f"run-{model_id}")`. Each model run is a separate wandb run; they're grouped in the dashboard. Logging per-sample completions with `wandb.Table` lets you eyeball outputs across models in one place.

### What's the most underrated thing to log?

**Sample outputs.** Loss curves and aggregate metrics catch ~70% of bugs; eyeballing 20 random completions catches the other 30%. Log a `wandb.Table` with `(prompt, completion, score)` for a sample of every eval run. Most "we got great numbers but the model was actually doing X" failures would have been caught here.

---

Last verified: 2026-04. wandb, TensorBoard, Hydra all stable / actively maintained. uv increasingly the default for new Python projects in alignment research.
