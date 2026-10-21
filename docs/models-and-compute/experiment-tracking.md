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
| Let a coding agent compare runs or diagnose a diverged run | The official **W&B MCP server** (`wandb/wandb-mcp-server`) in **read-only** mode — see below |
| Check that published code reproduces | Run its entry point in a **fresh container from a clean clone**, separate from the environment it was developed in (the PaperBench reproduction step) |
| Make experiment code safe to hand to an agent | Determinism, resumability, visibility, persistence, lineage — see "Five properties of experiment code" |

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
- **Upgrade to wandb ≥ 0.31.0 (2026-10-16) if you log offline or resume runs.** From 0.27.0 until 0.31.0, offline runs did not warn when `run.log()` data was dropped "because its step is lower than the current step" — so a step-counter bug in offline mode lost data silently. Before 0.31.0, `wandb sync` could also overwrite the earlier history of a resumed run "when the server reports a stale step". Both are fixed in 0.31.0 ([release notes](https://github.com/wandb/wandb/releases/tag/v0.31.0)). Pass an explicit, monotonically increasing `step=` and check the synced history length against your local log.
- **New default server in 0.31.0: CoreWeave Forge.** "The default API endpoint is now CoreWeave Forge at `https://api.forge.coreweave.com`", and run links point to `https://forge.coreweave.com/wandb`; "Existing API keys stored for `api.wandb.ai` keep working". A sandbox, cluster or agent container whose egress allowlist only permits `api.wandb.ai` needs `api.forge.coreweave.com` added.
- **Check a run locally without the web UI:** `wandb leet inspect --summary` (0.31.0) "prints a run's state, latest metric values, config and last console lines from its local `.wandb` file, a quick way for a script or a coding agent to check on a run"; `--json` prints machine-readable output and `--follow` streams a live run. It only reads the local file, so it is a safer thing to hand an agent than a write-capable W&B key.

### Let an agent query your runs: the W&B MCP server

Aliases: `wandb/wandb-mcp-server` on GitHub (MIT; "Merge release: v0.4.3" on 2026-10-16; still no git tags or GitHub releases as of 2026-10-20), "W&B MCP", "Weights & Biases Model Context Protocol server". Hosted endpoint `https://mcp.withwandb.com/mcp`.

**What it is.** A Model Context Protocol (MCP) server that lets a coding agent (Claude Code, Codex, Cursor) read your W&B projects through bounded, paged tools instead of you exporting CSVs: `get_run_history_tool` (sampled metric curves), `compare_runs_tool`, `diagnose_run_tool` ("Why did this run diverge?"), `probe_project_tool`, `query_wandb_tool` (structured reads or a query-only GraphQL document), `summarize_evaluation_tool`, artifact listing and diffing, and Weave trace queries. It also has **write** tools: `create_wandb_report_tool` and `log_analysis_to_wandb`.

**Install (Claude Code, hosted, from the README):**

```bash
claude mcp add --transport http wandb https://mcp.withwandb.com/mcp --scope user \
  --header "Authorization: Bearer <your-api-key-here>"
```

**Read-only mode.** For a self-run server, `WANDB_MCP_ACCESS_MODE=read-only` "omit[s] every tool classified as a write, including `create_wandb_report_tool`, `log_analysis_to_wandb`" (README). The README's local install runs `uvx --from git+https://github.com/wandb/wandb-mcp-server@vX.Y.Z wandb_mcp_server`; with no tags published yet, pin a commit SHA in place of `vX.Y.Z` — at or after `feede2350cbe` (2026-10-16), which raised the dependency to `mcp>=1.30.0` "for GHSA-84m7-p3x7-pcfv" (a medium-severity advisory in the MCP Python SDK: unbounded session accumulation in the StreamableHTTP transport, `mcp` 1.8.0 to <1.30.0). Illustrative, adapted from the README's local Claude Code line by adding the access-mode variable:

```bash
claude mcp add wandb -e WANDB_API_KEY=<key> -e WANDB_MCP_ACCESS_MODE=read-only \
  -- uvx --from git+https://github.com/wandb/wandb-mcp-server@<commit-sha> wandb_mcp_server
```

The README's recommended preset for the hosted service is `read-write`; if write access matters, run the server locally.

**When to use it:** "compare these three runs", "which config fields differ between the good and bad seeds", "show the loss and validation-loss curves for run X" across a sweep too large to eyeball.

**When *not* to use it:**
- As a substitute for looking at the plot yourself. The tools *summarize* and *sample* histories (bounded reads); a spike or a divergence between two curves can fall between samples. Open the run page before you write the conclusion down.
- With a write-capable key on a shared team project, where an agent-created report or logged "analysis" reads like a human's.

## Five properties of experiment code (Daniel Tan, 2026)

From ["Tips on leveraging AI for empirical research"](https://www.lesswrong.com/posts/f4WZ7dde8KAYHfeif/tips-on-leveraging-ai-for-empirical-research) (Daniel Tan, LessWrong, 2026-07-06). Code with these properties is much safer to hand to an agent, because a crash, a re-run or a question about an artifact has a cheap answer:

| Property | Meaning (Tan's wording, condensed) | What it looks like in a MATS project |
|---|---|---|
| **Determinism** | Same script, same args, same output | Seeds set and logged; `temperature=0` or logged sampling params; pinned model snapshot and provider |
| **Resumability** | Resuming a failed run is effortless and does not repeat completed work | Append each finished unit to `results.jsonl` in the run directory; `--resume <run_dir>` skips ids already on disk ([`code-recipes.md`](../engineering/code-recipes.md#resumable-append-as-you-go-results)) |
| **Visibility** | Trivial to see what is running, what failed, and the error | `stdout.log` and **stderr** saved in the run directory; failures written as records, not swallowed |
| **Persistence** | Outputs are easy to save and reuse | Raw per-sample outputs, checkpoints and eval logs kept, not just summary numbers |
| **Lineage** | For any artifact, easy to tell how it was made | `metadata.json` with config, git SHA, model ids, start/end timestamps |

His orchestration tool `dtch1997/stagehand` is archived on GitHub (last push 2026-07-10); the properties are the recommendation.

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
- [ ] **Log the serving stack and numerics**: inference engine and version (e.g. vLLM 0.32.0), weight precision / quantization (bf16, FP8, 4-bit), KV-cache dtype, and tensor / expert parallelism. Defaults change between versions (vLLM 0.32.0 switched GLM-5.x to an FP8 KV cache on Blackwell, and fixed wrong-expert routing for FP4 MoE models under expert parallelism), and results can depend on precision: Africa & Levine report a "Napoleon attractor" result on the Talkie model "that only showed up on 4-bit" while their main runs were bf16 ([LessWrong, 2026-10-13](https://www.lesswrong.com/posts/qchwP6wt4teHgxoKu)).
- [ ] **Log the Python version** and pin it (`uv python pin`). Several core libraries need Python ≥ 3.11 or ≥ 3.12 since 2026-10, and on 3.10 pip silently installs older releases ([`compute.md`](compute.md#python-version-floor-for-the-2026-10-stack-312-for-new-projects)).
- [ ] **Log the dataset version.** `datasets` library has `version` field; HF dataset cards have revisions.
- [ ] **Save raw outputs, not just summary stats.** A score of "0.73" is unreproducible-by-eye; the per-sample completions let you sanity-check.
- [ ] **Record wall-clock start/end timestamps per experiment** in `metadata.json`. Besides lineage, it gives a coding agent real elapsed times to read; agents' own runtime estimates are unreliable (see [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#agents-are-not-time-aware-put-wall-clock-timestamps-in-the-loop)).
- [ ] **Run the release in a fresh container from a clean clone.** PaperBench (`openai/frontier-evals`, `project/paperbench`) grades replications in three stages, and its reproduction stage is the one to copy: "The agent's submitted codebase is executed in a fresh second container with GPU access". Doing the same with your own repo before publishing catches undeclared dependencies, absolute paths and files that only exist on your machine. (PaperBench's lighter "Code-Dev" variant skips execution, and its README calls it "less rigorous".)
- [ ] **Have a single-file reproduction of the headline result** that someone can read top to bottom and run (Daniel Tan's habit for checking agent-run experiments; see [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#reviewing-what-an-agent-ran-practices-from-daniel-tan-2026)).

## Stochasticity gotchas specific to safety research

- **Closed-API non-determinism.** `temperature=0` doesn't give you bit-identical outputs across calls on most providers. Run multiple seeds even at temp=0.
- **vLLM determinism: use batch-invariant mode.** By default, vLLM's output for a prompt can change with the batch size and with which other requests share the batch (batched floating-point reductions are order-dependent), even with a fixed `seed`. vLLM's documented fix is **batch invariance**: set the environment variable `VLLM_BATCH_INVARIANT=1` before the engine starts (`VLLM_BATCH_INVARIANT=1 vllm serve <model>`, or `os.environ["VLLM_BATCH_INVARIANT"] = "1"` before importing vLLM). Per `docs/features/batch_invariance.md` at tag v0.32.0, it "ensures that the output of a model is deterministic and independent of the batch size or the order of requests in a batch"; it keeps a fixed reduction order under tensor parallelism and splits the LoRA (Low-Rank Adaptation) shrink into fixed chunks. Caveats from the same page: "Batch invariance is currently in beta"; it needs "NVIDIA GPUs with compute capability 8.0 or higher" (A100 and newer; AMD Instinct and Intel XPU also listed); it may be slower ("This trade-off is intentional to guarantee reproducibility"); under tensor parallelism it is not yet guaranteed for all-reduces whose size is not a multiple of 16 bytes; and the validated-model list covers Qwen3 / Qwen3-VL / Qwen2.5, Llama 3.1 / 3.2, gpt-oss, DeepSeek-V3 / R1 / V3.1, OLMo 2, Phi, Granite 3.1 and a few others — **not** Qwen3.5 / 3.6 / 3.8, Gemma 4 or GLM-5.x. On an unvalidated model, test it: run the same prompt alone and inside a large batch and compare tokens. `enforce_eager=True` plus `seed` (the older advice) removes CUDA-graph effects but not batch-composition effects. **When not to use it:** throughput-bound sweeps where you report distributions over samples anyway.
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

Closed APIs aren't bit-deterministic even at temp 0 — backend non-determinism (batched FP arithmetic, etc.). Run multiple seeds even at temp=0 and report distributions. For higher reproducibility on the open side, run vLLM with `VLLM_BATCH_INVARIANT=1` (beta; GPUs with compute capability ≥ 8.0; validated on Qwen3, Llama 3.1 / 3.2, gpt-oss, DeepSeek-V3 and others but not Qwen3.5+, Gemma 4 or GLM-5) plus a fixed `seed`; it makes outputs independent of batch size and request order, at a speed cost. See "Stochasticity gotchas" above.

### Can a coding agent check my wandb run without an API key?

Yes, for a run on the same machine: `wandb leet inspect --summary` (add `--json` for machine-readable output; wandb ≥ 0.31.0) on the run's `.wandb` file prints the run's state, latest metrics, config and last console lines from the local `.wandb` file, read-only. For runs on the W&B server, use the read-only W&B MCP server (section above).

### My wandb runs stopped syncing after upgrading — why?

wandb 0.31.0 (2026-10-16) changed the default server to CoreWeave Forge (`https://api.forge.coreweave.com`). If your cluster or sandbox only allows outbound traffic to `api.wandb.ai`, add the new host. Existing API keys keep working.

### How do I track multiple model comparisons in wandb?

Use **wandb groups**: `wandb.init(project="my-eval", group="cross-model-comparison", name=f"run-{model_id}")`. Each model run is a separate wandb run; they're grouped in the dashboard. Logging per-sample completions with `wandb.Table` lets you eyeball outputs across models in one place.

### Can Claude Code read my wandb runs directly?

Yes, through the official W&B MCP server (`wandb/wandb-mcp-server`): `claude mcp add --transport http wandb https://mcp.withwandb.com/mcp --scope user --header "Authorization: Bearer <your-api-key-here>"`. For a self-run server, set `WANDB_MCP_ACCESS_MODE=read-only` so it cannot create reports or log runs. Check the plots yourself before writing a conclusion down: its history tools return sampled, bounded reads. See the W&B MCP section above.

### What's the most underrated thing to log?

**Sample outputs.** Loss curves and aggregate metrics catch ~70% of bugs; eyeballing 20 random completions catches the other 30%. Log a `wandb.Table` with `(prompt, completion, score)` for a sample of every eval run. Most "we got great numbers but the model was actually doing X" failures would have been caught here.

---

Last verified: 2026-10-20. (Additions 2026-10-20: wandb 0.31.0 items from its GitHub release notes and PR #12951; W&B MCP server commits via `gh api` (no tags) and advisory GHSA-84m7-p3x7-pcfv via the GitHub advisory API; vLLM batch invariance from `docs/features/batch_invariance.md` at tag v0.32.0 and the v0.32.0 release notes; the 4-bit Talkie note from Africa & Levine's post (LessWrong GraphQL markdown). Not verified: batch-invariant mode on models outside vLLM's validated list.) (Additions 2026-10-14: W&B MCP server from the `wandb/wandb-mcp-server` README and `gh api` (no tags or releases); Tan's five properties from the LessWrong GraphQL markdown of his 2026-07-06 post, `dtch1997/stagehand` archived per `gh api`; PaperBench reproduction step from the `openai/frontier-evals` `project/paperbench` README. Not verified: the hosted W&B endpoint's handling of read-only mode.) Earlier pass (2026-04): wandb, TensorBoard, Hydra all stable / actively maintained. uv increasingly the default for new Python projects in alignment research.
