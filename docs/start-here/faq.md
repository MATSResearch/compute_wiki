---
tags:
  - meta
---

# Frequently Asked Questions (Cross-Cutting)

Beginner-level and cross-cutting questions for MATS fellows starting safety research projects. For tool-specific questions, see the topic doc's "Common questions" section.

## Getting started

### Where do I start as a new MATS fellow?

Read [`index.md`](../index.md) and find the row matching what you want to do. Each topic doc has a "Common questions" section near the bottom that's keyword-matched to the kinds of things fellows ask. If you're picking a *project shape*, read [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md) — it describes the 6-step methodological pattern most landmark behavioral safety papers follow and is the most reliably reproducible MATS project shape.

### Where do I begin? Is there a tutorial?

The fastest way to begin: pick a paper from [`model-organisms.md`](../alignment-science/model-organisms.md), follow its repo's README to reproduce the main result. The reproduction is your tutorial. Most reliable first project: Emergent Misalignment (`emergent-misalignment/emergent-misalignment` repo) — clean structure, ~$few-hundred to reproduce, you'll learn the standard tooling stack along the way. After that, read [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md) for the methodological playbook.

### What's the smallest first project I should attempt?

A reproduction. Pick one paper from [`model-organisms.md`](../alignment-science/model-organisms.md) or [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md) (Emergent Misalignment is a good first one — clean repo, ~$few-hundred to reproduce on a closed-API model) and reproduce its main result. You'll learn the tooling stack, hit the standard pitfalls, and end with a baseline you can extend.

### What should I install first?

For a typical Python safety research project: `uv` for environment management; `inspect-ai` and `inspect-evals` if you'll do evals; `safety-tooling` (from `safety-research` GitHub org) for multi-provider LLM API access with caching; `transformers`, `torch`, `vllm` if you'll touch open-weight models; `wandb` for experiment tracking. Most papers will ask for additional packages — install per-project, not globally. Use `uv venv && uv pip install ...`.

### Can I use Claude Code for this?

Yes — Claude Code (the CLI) works well as a coding assistant for safety research projects, and Inspect AI even supports running Claude Code as the agent under test in evals (see [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md) → external agent CLIs). For research-assistant use, you don't need anything special — just open Claude Code in your project directory.

### How do I get an OpenAI / Anthropic / Google API key?

You sign up on the provider's website (`platform.openai.com`, `console.anthropic.com`, `aistudio.google.com`), generate a key in the dashboard, and store it as an environment variable. Standard pattern: put it in `~/.env` or a project-local `.env` file (gitignored), and load via `os.environ["ANTHROPIC_API_KEY"]` etc. Most safety-research libraries (Inspect AI, safety-tooling) read these from the env automatically.

### How do I avoid committing API keys to git?

Always put `.env` and `*.env*` in `.gitignore` *before* you create the file. Never paste keys into source files or notebooks; load from env. If you do accidentally commit a key: rotate it immediately on the provider's dashboard (don't try to remove from git history first — assume it's already exfiltrated), then clean the history.

### Where do I get free API credits as a researcher?

OpenAI Researcher Access Program, Anthropic's research program, Google's research credits, AWS Activate. Each has its own application process and waiting times. Provider-funded credits are usually limited; for sustained research, expect to pay (or have institutional funding). If you're a MATS fellow, ask your stream lead about MATS-provided credits and which providers give priority.

### How much will my project cost?

A reproduction of a small behavioral-safety paper (e.g. Emergent Misalignment on GPT-4o) is typically a few hundred dollars in API. A medium-sized eval campaign (1000 prompts × 5 models × 5 judge votes) is in the low thousands. Long-running RL with API teacher models or large eval suites can run $10k+. Cache aggressively (safety-tooling does this); start with smaller subsets while iterating; only run the full eval when the pipeline is finalized.

### How do I keep costs down?

(1) Cache. safety-research/safety-tooling caches by default; Inspect AI logs are reusable. (2) Use smaller models for bulk generation (Haiku, GPT-4o-mini, smaller open weights), bigger models only for filtering / scoring / judging. (3) Run a limit (e.g. `--limit 20` in Inspect) while iterating; only remove when ready. (4) For open-weight inference, vLLM is much cheaper per-token than HF Inference Endpoints if you have GPUs. (5) Don't sweep hyperparameters on the full eval set — use a small calibration set.

## Compute

### Do I need GPUs?

Maybe. If you're doing pure API-based behavioral research (the MATS playbook in [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md)), you can do most of it with no GPUs — just API access. If you're doing interp, training, or self-hosted inference, you need GPUs. Tinker (managed RL/SFT, see [`rl-training.md`](../oversight-and-control/rl-training.md)) lets you finetune large open-weight models without owning GPUs. For activation extraction at any meaningful scale, see [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

### What's the cheapest way to do open-weight inference?

For research-scale (a few hundred to a few thousand prompts), an API provider like Together AI or Groq is cheapest because you don't pay for idle. For larger volumes, rent GPUs (RunPod, Vast.ai) and run vLLM. See [`compute.md`](../models-and-compute/compute.md) and [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

### How do I run a 70B model on one A100?

Use 4-bit quantization (AWQ or GPTQ) — fits a 70B model in ~40GB. Use vLLM with `--quantization awq` (or appropriate flag for the model). Speed is ~half of fp16. For interpretability that needs un-quantized activations, you'll need ≥2 GPUs or use vLLM-Lens / NDIF (see [`serving-and-activations.md`](../interpretability/serving-and-activations.md)).

### What about MATS compute?

MATS provides some compute (varies by cohort). Ask your stream lead, the MATS handbook, or torchy. This guide intentionally doesn't duplicate that information — it's in the MATS-specific docs.

## Decisions

### Inspect AI vs lm-evaluation-harness — which?

Inspect AI for anything agentic, multi-turn, tool-using, or where you want sample-level transcripts. lm-eval-harness for academic multiple-choice / log-prob benchmarks (MMLU, ARC, etc.) where you need leaderboard-comparable numbers. Most new safety work in 2026 should default to Inspect. See [`evals.md`](../evaluation/evals.md).

### TransformerLens vs nnsight — which?

TransformerLens for classic mech interp (induction heads, IOI, attention analysis) on smaller models with consistent named hooks. nnsight for any HuggingFace model with exact HF behavior, especially big models or remote (NDIF) inference. SAELens for SAE work (the `HookedSAETransformer` was removed from TL 2.x). See [`mech-interp.md`](../interpretability/mech-interp.md).

### Tinker vs TRL vs OpenRLHF — which?

Tinker for managed RL/SFT without GPU management (the default for most fellows in 2026). TRL for self-hosted preference learning (DPO/KTO) and small-scale RL. OpenRLHF for self-hosted high-throughput / async RL. See [`rl-training.md`](../oversight-and-control/rl-training.md).

### Should I use Claude / GPT-4o / Gemini for my judge model?

The Owain-Evans-team default is GPT-4o (often via majority voting). Claude Sonnet 4.x or Opus 4.x are also common. For most behavioral-safety scoring, validate the judge on a hand-labeled subset before trusting it on a full eval set; whichever judge survives validation is the right one. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

### Should I do interp or behavioral work?

Both are valuable; pick by interest and resource fit. Behavioral work (the [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md) playbook) is API-only, runs on a laptop, has clear paper shape, and is reliably reproducible at MATS scale. Interp work (TransformerLens / SAEs / probes) needs GPUs but produces mechanism-level claims and is heavier on theoretical understanding. The strongest projects often combine both.

## Common errors and gotchas

### `RuntimeError: shape mismatch` / tokenizer mismatch

Activations indexed by token position go wrong if the tokenizer differs between data preparation and model. Always re-tokenize with the model's own tokenizer; never trust offsets cached from another tokenizer. See [`index.md`](../index.md) "Common cross-cutting pitfalls."

### `RuntimeError: CUDA out of memory` / OOM

(1) Reduce batch size. (2) Use `bf16` instead of `fp32`. (3) Use gradient checkpointing if training. (4) Quantize the model (AWQ/GPTQ) for inference. (5) For vLLM, lower `gpu_memory_utilization` from 0.9 default to 0.85. (6) For multi-GPU, check `tensor_parallel_size` divides head count.

### My loss went to NaN

Usually: too-high learning rate, fp16 underflow, malformed advantages (RL), or unstable gradients. Switch fp16 → bf16, reduce LR, gradient-clip, normalize advantages. See [`rl-training.md`](../oversight-and-control/rl-training.md) for RL-specific causes.

### My SAE features look uninterpretable

Likely causes: (1) hook point mismatch — pretrained SAEs are trained at a specific hook (`hook_resid_pre` vs `hook_resid_post` vs `hook_mlp_out`); using the wrong one gives garbage. (2) Tokenizer / chat-template mismatch — pretrained SAEs were trained on a particular distribution; chat-template prompts may differ. (3) Width too narrow — 16k features on a 2B model is small by 2026 standards. See [`saes.md`](../interpretability/saes.md).

### `Cannot connect to the Docker daemon` (Inspect sandbox)

Inspect's `docker` sandbox needs Docker running. On rented GPU boxes, you may need to install Docker and start the daemon (`sudo systemctl start docker`). On hosting platforms that don't allow Docker-in-Docker (Modal, etc.), use `local` sandbox or k8s-sandbox if a cluster is available. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

### My OpenAI / Anthropic call returned 429 / rate limit

Provider rate limits vary by tier. (1) Slow down: lower concurrent calls. (2) Cache: hitting the same prompt twice hits cache, not API. (3) Apply for higher rate limits via the provider's console. (4) Use multi-provider fallback: safety-research/safety-tooling can route to a different provider on persistent 429.

### My probe accuracy is suspiciously high

Probably leakage. Common causes: (1) train/test split at the prompt level instead of concept level — different paraphrases of the same idea split across both. (2) Class imbalance: a 90/10 split + 90% accuracy probe means nothing. (3) Late-layer probes pick up the model's planned output, not its understanding. See [`probes.md`](../interpretability/probes.md).

## Reproducibility and methodology

### How do I make my work reproducible?

Pin everything: model versions (`claude-sonnet-4-6` not `claude-sonnet`), code (git SHA in `metadata.json`), dependencies (`uv lock` or `pip freeze`), random seeds, dataset revisions, and prompt templates. Use timestamped run directories (`outputs/run_YYYYMMDD_HHMMSS_descriptor/`) per Nathan's convention. See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md) for a full checklist.

### How many seeds should I run?

For any non-trivial finding, ≥3 seeds. For RL or stochastic agents, ≥5. Report distributions, not just means. Single-seed results that look surprising are often artifactual.

### Should I use temperature 0?

For evals: yes, unless you're explicitly studying sampling. Even at temp 0, closed APIs aren't bit-deterministic — log seeds and run multiple times if reproducibility matters. For RL training rollouts: no, you want diversity (typically temp 0.7–1.0).

### Do I need to release my code?

For the work to have impact, yes. The papers most cited from this area all release their code, datasets, and judge prompts (`emergent-misalignment/emergent-misalignment`, `safety-research/persona_vectors`, etc.). Releasing the eval data and judge prompts is often what makes a paper a *standard* others build on. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md) Step 6.

### What about dual-use carefulness?

Don't release prompts / datasets that meaningfully uplift bad actors. The convention: release behavioral eval prompts (mostly behavioral, not capability-uplifting); release training data with safety review; do not release datasets containing genuinely harmful content (e.g. real CBRN procedures); do not release trained sleeper-agent / strongly-misaligned model weights without coordination. See [`model-organisms.md`](../alignment-science/model-organisms.md).

## Workflow

### How do I structure my project directory?

Per Nathan's preferences (and his global CLAUDE.md): `README.md`, `CLAUDE.md`, `pyproject.toml`, `src/` (your code), `tests/`, `data/` (input datasets), `docs/` (notes), `outputs/run_YYYYMMDD_HHMMSS_descriptor/` (one timestamped subdir per run, with `metadata.json` + artifacts + plots). See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

### Should I use Hydra for configs?

Probably not unless you have ≥10 hyperparameters. A `@dataclass` config with `tyro.cli(Config)` is friendlier for most projects. See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

### Should I use a Jupyter notebook?

Notebooks are great for exploratory mech interp work and visualization (`circuitsvis` is notebook-native). For anything you want to rerun or schedule, promote to a script. Don't develop final pipelines in notebooks.

### Should I use Claude / GPT to help write code?

Yes — Claude Code, Cursor, and similar are widely used in safety research. Watch for: hallucinated library APIs (verify imports work), out-of-date dependency versions, made-up function signatures (run `python -c "import foo; help(foo.bar)"` to verify). For tool docs in particular, library APIs change fast — trust real docs over generated suggestions.

### How do I track multiple experiments?

wandb is the default. Log: scalars (loss, eval scores), config (full hyperparameters), system (GPU util, memory), and *sample outputs* (the most underrated kind of log — eyeballing a few completions catches problems metrics miss). See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

### How do I share findings with my mentor / team?

wandb reports work well for training runs. Inspect View logs (`.eval` files) are the standard for eval results — your mentor can open them in `inspect view start` directly. For papers, the open-source-and-publish norm is the default; for in-progress work, ad-hoc is fine.

## Where to ask further questions

- **MATS Slack** / cohort channels for MATS-specific questions.
- **torchy** (the MATS RAG assistant) — for questions answerable from MATS docs and this guide.
- **Alignment Forum / LessWrong** for technical safety research discussion.
- **Provider Discord servers** (Anthropic Discord, OpenAI Developers) for API issues.
- **Library GitHub Issues** for tool-specific bugs.
- **MATS mentor** — your most-direct safety research help.
