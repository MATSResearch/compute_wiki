---
tags:
  - training
  - infrastructure
---

# RL and Fine-Tuning Frameworks: Trainers, Hosted APIs, Environment Libraries and Version Traps

Which **trainer**, which **hosted fine-tuning / RL API**, and which **RL environment library** to use for reinforcement learning (RL) and supervised fine-tuning (SFT) of language models at MATS-fellow scale, plus the version traps that silently break runs. The algorithms (GRPO, PPO, DPO, RLVR), reward hacking and RL safety-research patterns are in [`rl-training.md`](rl-training.md); which tokens to put loss on when training on agent trajectories is in [`training-on-trajectories.md`](training-on-trajectories.md); a ready single-GPU starter is `project_templates/rl_small/`.

Acronyms used on this page: **RL** = reinforcement learning; **SFT** = supervised fine-tuning; **GRPO** = Group Relative Policy Optimization; **RLVR** = RL from Verifiable Rewards; **LoRA** = Low-Rank Adaptation; **QLoRA** = LoRA on a 4-bit-quantized base model; **FSDP** = Fully Sharded Data Parallel; **KL** = Kullback–Leibler divergence (the usual regulariser toward a reference policy).

## At a glance

| You want… | Use | When *not* to use it |
|---|---|---|
| RL or SFT on an open-weight model without managing GPUs | **Tinker** (Thinking Machines API) + the **Tinker Cookbook** | Data must stay on your machines; you need full-parameter fine-tuning (hosted Tinker is LoRA-only) |
| The same Tinker Cookbook script on your own GPUs, or full-parameter fine-tuning through the Tinker API | **SkyRL's Tinker backend** (`skyrl.tinker.api`, NovaSky-AI/SkyRL) | Your recipe needs a KL penalty, prompt logprobs, or the `ppo` / `cispo` losses; your NVIDIA driver is older than r580 |
| A Tinker-style loop on another provider | **Fireworks Training API** (serverless LoRA, billed per token) or **Together post-training** (GPUs you reserve, billed per GPU-minute) | Throughput-sensitive sweeps on Fireworks' shared pool; leaving a Together resource running after your script ends |
| GRPO / DPO / SFT on one GPU with the Hugging Face stack | **TRL** with colocated vLLM and sleep mode | You have a spare GPU for rollouts (use TRL's vLLM server mode instead) |
| QLoRA or LoRA GRPO on a single consumer GPU (24 GB) | **Unsloth** (Unsloth Core, `unsloth` on PyPI) | Multi-node or asynchronous RL; you need exact control of the loss and advantage code |
| Config-driven (YAML) SFT / DPO / QLoRA with multi-GPU FSDP2 | **axolotl** | Your configs still use FSDP1 keys and you cannot migrate mid-project (pin `axolotl<0.20`) |
| Asynchronous RL from 2 GPUs up to a cluster, with `verifiers` environments | **prime-rl** (PrimeIntellect-ai) | A single non-H100-class GPU for RL (its one single-GPU RL example, alphabet-sort, uses LoRA on an H100); a model architecture outside its supported list; you need a KL-to-reference term by default |
| Multi-node asynchronous RL with Ray | **OpenRLHF** | Single-GPU experiments |
| Industrial-scale RL with maximum throughput | **verl** (ByteDance) | Research-scale experiments where you want to read the whole loop |
| Add GRPO to an existing Python agent that already calls an OpenAI-compatible endpoint | **OpenPipe ART** (`openpipe-art`) | Throughput or exact token-level control matters (its loop is synchronous) |
| Train an agent inside its own harness (Claude Code, mini-SWE-agent, OpenCode) | **Agent Lightning v1.0**, **verl `uni-agent`**, or TRL's `AsyncGRPOTrainer` with OpenEnv / Harbor capture | Single-turn RLVR, where a reward function is enough |
| A reusable RL environment behind a standard interface | **OpenEnv** (`openenv`), **verifiers** / Environments Hub, **Harbor**, **OpenReward** (ORS) — see [RL environment libraries](#rl-environment-libraries-openenv-verifiers-harbor-openreward) | Single-turn RLVR where a Python reward function suffices |
| A hand-rolled loop that shares one GPU between trainer and vLLM | **vLLM sleep mode + weight transfer** — see [vLLM hooks](#vllm-hooks-for-a-hand-rolled-rl-loop-sleep-weight-transfer-pauseresume) | TRL, verl or prime-rl already fits |
| Fine-tune GPT-4o / GPT-4.1 through OpenAI | Don't start: see [OpenAI fine-tuning is closing](#openai-fine-tuning-is-closing-dates-as-of-2026-10-14) | — |
| LoRA settings that match full fine-tuning | [LoRA Without Regret settings](#lora-settings-that-match-full-fine-tuning-lora-without-regret) | — |

## Versions as of 2026-10-20 (record these in every run's metadata)

Most "my run broke" reports in this area are version mismatches. Latest releases, checked on PyPI and GitHub on 2026-10-20 (previous check 2026-10-14):

| Package (PyPI name) | Latest | Released | Why the version matters |
|---|---|---|---|
| `trl` | 1.16.0 | 2026-10-15 | Releases every one to two weeks; supports vLLM 0.22.0–0.31.0 only (so **not** the current vLLM 0.32.0); fixes a silent `loss=0.0` / `grad_norm=nan` bug with `torch_compile=True` on torch < 2.11 |
| `vllm` | 0.32.0 | 2026-10-18 | Default PyPI wheel built for CUDA 13.0; pins `torch==2.13.0` and `transformers>=5.16.1,<5.20.0`, needs Python ≥3.11, so a TRL + vLLM environment gets torch 2.13.0, not the 2.14.1 below. Outside TRL 1.16.0's supported range |
| `torch` | 2.14.1 | 2026-09-30 | Silent-correctness fix release (CUDA 13.2 binaries moved to 13.2.2) |
| `peft` | 0.21.2 | 2026-10-01 | 0.21.0 fixed two silent failures (a second `add_adapter` adapter that adapts nothing; double-scaled SVD merges) |
| `tinker` / `tinker-cookbook` | 0.34.0 / 0.5.7 | 2026-10-17 / 2026-09-03 | tinker 0.34.0 adds `tinker model list` and `copy_weights()`; cookbook pins `verifiers>=0.1.9,<0.1.10` |
| `skyrl` | 0.4.0 | 2026-10-01 | Replaces the legacy `skyrl-train` package (last 0.3.1, 2026-01-02) |
| `verifiers` | 0.4.0 | 2026-10-12 | Removed the v0 API; changed several defaults that alter rewards |
| `unsloth` | 2026.10.7 | 2026-10-19 | Date-versioned; patches TRL / transformers internals |
| `axolotl` | 0.21.0 | 2026-10-16 | Fixes silent LoRA / QLoRA / expert-parallel bugs (empty adapters under FSDP2 activation checkpointing among them); requires `vllm>=0.30.0` and torch < 2.15.0; Python ≥3.12 |
| `openenv` | 0.9.0 | 2026-10-15 | Removes `opencode_env` and `pi_env`; the old name `openenv-core` stops at 0.3.0 (2026-05-11) |
| `openpipe-art` | 0.5.21 | 2026-10-20 | GRPO stability changes (zero-variance updates skipped, bounded importance ratios), so numbers from ≤0.5.20 may differ; Python ≥3.12 |
| prime-rl (GitHub only, not on PyPI) | v0.10.0 | 2026-10-13 | New default loss (IPO = INTELLECT Policy Optimization) |
| `verl` / `openrlhf` / `agentlightning` | 0.9.1 / 0.11.2 / 1.0.2 | 2026-09-20 / 2026-09-14 / 2026-09-29 | See their sections below |

The `project_templates/rl_small/configs/metadata.example.json` file shows one way to record the trainer, vLLM, torch, CUDA and NVIDIA driver versions next to each run.

## Hosted training APIs

### Tinker

Aliases: `tinker` (the Thinking Machines fine-tuning API; PyPI `tinker` 0.34.0, 2026-10-17), "Mira Murati's lab's training API", `tinker-cookbook` (the recipe repo; PyPI `tinker-cookbook` 0.5.7, 2026-09-03). Released October 2025 in private beta; widely adopted for safety RL research through 2026. The cookbook README still says "after our private beta is over" and sign-up is via `auth.thinkingmachines.ai`, with an API key exported as `TINKER_API_KEY`.

**What it is.** A managed API for distributed fine-tuning and RL on open-weight models (as of 2026-10: Qwen3.5 / 3.6 / 3.8, gpt-oss, Nemotron-3, Kimi-K2.6, GLM-5.3, DeepSeek, and Thinking Machines' own **Inkling** family — see "Models and pricing" below; **the Llama models and the big Qwen3 MoEs were retired in June 2026**). You write a small Python loop on a CPU machine; Tinker runs the GPU compute. Uses **LoRA** for efficient training. Lets you keep full control of data and algorithm without owning H100 clusters.

**Core concepts:**
- **`ServiceClient`** — the entry point. Its `base_url` argument defaults to the `TINKER_BASE_URL` environment variable and then to the production API (tinker SDK source), which is what lets the same script target a local SkyRL server (below).
- **`TrainingClient`** — manages weights and optimizer state; you call `forward_backward(...)` and `optim_step(...)`.
- **`SamplingClient`** — runs inference (rollouts) with the current weights. In the cookbook's minimal loop you call `training_client.save_weights_and_get_sampling_client()` to get a sampler for the current weights, sample, then update.
- **Datums** — training data points. Each datum specifies tokens, loss mask, advantages (for RL), etc.
- **Loss functions** — `cross_entropy` (SFT/distillation), `importance_sampling` (the basic on-policy RL loss), `ppo` (PPO clipping), `cispo` (clipped IS — MiniMax's CISPO loss, from the MiniMax-M1 paper arXiv:2506.13585), `dro` (Direct Reward Optimization); the docs index (2026-10-14) also lists `gspo` and custom losses.
- **Workflow** — training loop = sample → grade → compute advantages → train. Tinker handles the GPU scheduling.

**Models and pricing (Tinker "Models & Pricing" page, checked 2026-10-09).** Tinker IDs include `thinkingmachines/Inkling` (975B total / 41B active MoE, text + image + audio) and `thinkingmachines/Inkling-Small` (276B / 12B), `moonshotai/Kimi-K2.6`, `zai-org/GLM-5.3:peft:262144` (listed only in a 256K-context variant), `Qwen/Qwen3.8-27B`, `Qwen/Qwen3.6-35B-A3B`, `Qwen/Qwen3.5-397B-A17B`, `Qwen/Qwen3.5-9B` (plus `-Base` and `4B` variants), `Qwen/Qwen3-8B`, `openai/gpt-oss-120b` and `gpt-oss-20b`, `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16` (and Nano, Ultra, 3.5-Lightning), `deepseek-ai/DeepSeek-V3.1`. Prices are per million tokens with separate **prefill**, **sample** and **train** rates, an 80% discount on cached prefill tokens, and checkpoint storage at $0.10 per GB-month; for example `Qwen/Qwen3-8B` was listed at $0.195 prefill / $0.60 sample / $0.44 train, and the Inkling, Nemotron-3-Super/Ultra and Nemotron-3.5-Lightning entries carried a "limited-time 50% discount". Extended-context variants (ID suffix `:peft:262144`) cost more for **training only**; prefill and sampling prices are unchanged. Forward-only passes invoked by a training client are billed at the train price. **Retirements:** on 2026-06-12 Tinker retired `Llama-3.3-70B-Instruct`, `Llama-3.1-8B-Instruct`, base `Llama-3.1-8B` and `Llama-3.1-70B`, base `Llama-3.2-1B/3B`, `Qwen3-235B-A22B-Instruct-2507`, `Qwen3-VL-235B-A22B-Instruct`, `Qwen3-32B`, `Qwen3-30B-A3B*`, `Qwen3-VL-30B-A3B-Instruct`, `Qwen3-8B-Base`, `Qwen3-4B-Instruct-2507` (the model SkyRL's local quickstart uses, which still works on a local server), `Qwen3.5-27B/35B-A3B`, `DeepSeek-V3.1-Base` and `Kimi-K2-Thinking`; `Kimi-K2.5` followed on 2026-07-12, and the "Model deprecations" page schedules `Qwen3.6-27B` (replacement `Qwen3.8-27B`), `DeepSeek-V3.1` (replacement `DeepSeek-V4.1-Flash`) and `Nemotron-3-Nano-30B-A3B` (replacement `Nemotron-3.5-Lightning-30B-A3B`) for **2026-10-23**. The docs promise advance notice by email and in the docs but state no fixed notice period and say nothing about what happens to existing checkpoints of a retired model.

**When to use it:**
- You want to do real RL on real models without managing infra.
- You're a MATS fellow with limited compute access.
- You want to reproduce a DeepSeek-style GRPO / RLVR result with your own reward function.
- You're studying RL training dynamics and need lots of small experiments fast.

**When *not* to use it:**
- Your data must stay on-prem (Tinker is hosted) — though the same cookbook code can run against a local SkyRL server (see the SkyRL section).
- You need a custom architecture not in Tinker's model lineup.
- You need bit-exact reproducibility of a specific paper's training stack — Tinker abstracts kernels.
- You want full-finetune (not LoRA) with very large changes — hosted Tinker is LoRA-first; SkyRL's backend accepts `lora_rank=0`.

**Pitfalls:**
- **LoRA-only.** Tinker uses LoRA. For most safety research that's fine; for full-parameter behavioral changes, you may hit ceilings. Use `get_lora_lr_multiplier()` or `get_lr(model_name)` from the cookbook's `hyperparam_utils` to set a sensible LR (the minimal `rl_loop.py` uses 4e-5 with LoRA rank 32).
- **Synchronous sample-train cycle.** You need to checkpoint weights and reload them in the sampling client between RL steps. The cookbook's GRPO loop shows the pattern; rolling your own can be subtle.
- **API throughput, not your throughput.** Rate limits on the API affect rollout throughput. Plan batch size accordingly.
- **Evaluation loop overhead.** Run a held-out eval every N steps, not every step — eval rollouts cost as much as training rollouts.
- **Cost.** Usage is billed per million tokens (prefill / sample / train; forward-only calls from a training client are billed at the train rate). Track usage when iterating; long RL runs add up fast, and extended-context (256K) training costs more than standard-context training.
- **Check what you can still train before a retirement date.** tinker 0.34.0 (2026-10-17) adds a `tinker model list` CLI command ("List the models this organization can train or sample") — run it before the 2026-10-23 retirements — and `RestClient.copy_weights()`, which copies a checkpoint into another project without duplicating storage (the copy belongs to a new training run "that cannot be trained on").
- **Pinned to a retired base model.** A script or paper replication that hard-codes `meta-llama/Llama-3.2-1B` (still the example in the cookbook README's primitives snippet) or any other retired ID can no longer train or sample it. The Tinker docs advise not depending on any single model and testing replacements before a retirement date; switch to the recommended replacement listed on the "Model deprecations" page (the exact error text a retired ID produces is unverified).
- **Checkpoint expiry.** The cookbook's `rl_loop.py` saves intermediate checkpoints with `ttl_seconds=604800` (7 days) and the final checkpoint with `ttl_seconds=None`; download or re-save anything you need to keep (`rest_client.get_checkpoint_archive_url_from_tinker_path(...)` exports a checkpoint archive).
- **Trainer–sampler numerics drift.** The cookbook ships an `rl_numerics_check` recipe (a synthetic many-turn task with 60K+ token episodes) specifically for checking that the trainer's log-probabilities match the sampler's during RL; run it before long multi-turn runs if your importance-sampling ratios look off.
- **`importance_sampling` ≠ PPO.** The basic on-policy IS loss is *not* clipped; off-policyness (large KL between sampling and current weights) makes it unstable. Use `ppo` or `cispo` if you do many gradient steps per rollout batch.

```python
# Sketch of the cookbook's minimal RL loop (tinker_cookbook/recipes/rl_loop.py), simplified:
service_client = tinker.ServiceClient()          # base_url=None -> TINKER_BASE_URL, else hosted Tinker
training_client = service_client.create_lora_training_client(base_model="Qwen/Qwen3.5-9B-Base", rank=32)
for batch in batches:
    sampling_client = training_client.save_weights_and_get_sampling_client()   # sampler = current weights
    futures = [sampling_client.sample(prompt=p, num_samples=16, sampling_params=params) for p in batch]
    datums = []
    for fut in futures:
        seqs = fut.result().sequences                                        # tokens + logprobs per sample
        rewards = [grade(s) for s in seqs]                                   # your reward fn
        adv = [r - sum(rewards) / len(rewards) for r in rewards]             # group-centred; the cookbook does not divide by std
        if all(a == 0 for a in adv): continue                                # skip zero-signal groups
        datums += [make_datum(prompt, s, a) for s, a in zip(seqs, adv)]      # target_tokens, logprobs, advantages
    training_client.forward_backward(datums, loss_fn="importance_sampling")
    training_client.optim_step(tinker.types.AdamParams(learning_rate=4e-5, beta1=0.9, beta2=0.95, eps=1e-8))
```

### Tinker Cookbook

Aliases: `tinker-cookbook`, `thinking-machines-lab/tinker-cookbook` on GitHub, "the cookbook", "Tinker recipes".

**What it is.** The official open-source recipe library for Tinker. Read this *before* writing your own RL loop — even if you end up using OpenRLHF or verl instead, the cookbook is one of the cleanest reference implementations of modern post-training. Recipes such as `rl_loop`, `sl_loop`, `math_rl`, `code_rl`, `chat_sl` and DPO take a `base_url=` argument, so the same command runs against hosted Tinker or a local SkyRL server.

**Recipes shipped (as of 2026-10; the recipes README lists these):**

- **Chat SFT** — supervised fine-tuning on conversational datasets (e.g. Tulu3).
- **Math RL** — RL on math problems with verifiable rewards (DeepSeek-R1-style RLVR replication).
- **Code RL** — RL on competitive programming with sandboxed code execution (DeepCoder replication).
- **Preference Learning** — DPO and a three-stage RLHF pipeline (SFT → reward model → RL).
- **Distillation** — on-policy and off-policy distillation; single- and multi-teacher.
- **Tool Use** — RL for retrieval-augmented generation (Search-R1 replication).
- **Multi-agent RL** — self-play and cross-play.
- **Harbor RL** — generic environment-RL recipe.
- **Rubric-based grading** — LLM-as-judge with structured rubrics.
- **VLM classification** — vision-language model classification training.
- **SDFT** — Self-Distillation Fine-Tuning.
- **Benchmark framework** — runs 12 benchmarks (GSM8K, MATH-500, MMLU-Pro, MMLU-Redux, GPQA, IFEval, MBPP, C-Eval, SuperGPQA, IFBench, AIME 2025, AIME 2026), plus experimental LiveCodeBench, Terminal Bench and SWE-bench.
- **Verifiers environments** (`verifiers_rl`) — use RL environments from Prime Intellect's Environments Hub with Tinker (see the version pitfall below).
- **Forecasting** (added in v0.5.6) — train calibrated probability forecasts with a Brier reward.
- **RL numerics check**, **Prompt distillation**, **Audio** (for Inkling audio inputs), **Decision model**, and **True Thinking Score (TTS)** — a recipe that quantifies how faithful a chain of thought is to the final answer (relevant to [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)).
- **Logging and resume** — recipes write `metrics.jsonl` and `checkpoints.jsonl` under `~/tinker-runs/<recipe>/` (override the root with `TINKER_COOKBOOK_RUNS_DIR`; avoid `/tmp`), and re-using a `log_path` resumes an interrupted run.

**Claude Code skills.** The cookbook ships Claude Code skills: `/plugin marketplace add thinking-machines-lab/tinker-cookbook`, then install the `tinker` plugin; it provides `/tinker:research` (plan and run post-training experiments), `/tinker:debug` (slow training, hangs, renderer errors) and `/tinker:inkling`. Useful if you drive your RL experiments from Claude Code.

**Model-specific loss masks.** Release v0.5.7 (2026-09-03) is a single fix: "Make GLM-5.3 train the turn terminator on every assistant turn". If a fine-tuned model never stops generating, or stops too early, check that the renderer trains the end-of-turn token for the model you picked; use the cookbook's `renderers` rather than hand-rolled chat templates.

**Pitfall: the cookbook pins an old `verifiers`.** The cookbook's `pyproject.toml` extra is `verifiers = ["verifiers>=0.1.9,<0.1.10"]`, while `verifiers` 0.4.0 (2026-10-12) removed the legacy v0 stack ("`verifiers.legacy` and its historical top-level aliases are no longer available. Use `import verifiers.v1 as vf`"). An Environments Hub environment written for the v1 API is therefore not what the `verifiers_rl` recipe is built against. A low-friction setup is one virtualenv with `uv pip install "tinker-cookbook[verifiers]"` (verifiers 0.1.9) for Tinker and a separate one for prime-rl / verifiers 0.4. The recipe README also warns that the Qwen3 chat templates strip `<think>` sections automatically, which reward functions can silently penalise; fix it in the renderer, the chat template or the environment.

**When to use it:** Always start by adapting a cookbook recipe rather than writing from scratch. The cookbook idioms transfer to other RL libraries. **When not to:** you need a loss the Tinker API does not expose, or a training stack you control end to end (use TRL, verl or prime-rl).

### SkyRL: run Tinker Cookbook scripts on your own GPUs

Aliases: **SkyRL**, `NovaSky-AI/SkyRL` on GitHub (Apache-2.0), PyPI `skyrl` 0.4.0 (2026-10-01, Python 3.12–3.14; the legacy `skyrl-train` package stops at 0.3.1, 2026-01-02), "SkyRL Tinker backend", `skyrl.tinker.api`, Berkeley NovaSky.

**What it is.** A full RL library whose Tinker integration starts a local FastAPI server that speaks the Tinker API on top of SkyRL's FSDP or Megatron backend. Per its quickstart: "In general, **zero** code changes are required to execute [tinker-cookbook] scripts on SkyRL. Simply update the `base_url` to point to your local Tinker server." Develop on hosted Tinker and move to your own box, or the reverse, without rewriting the loop. **Full-parameter fine-tuning** works by passing `lora_rank=0` (the cookbook doc suggests about a 10× lower learning rate when switching from LoRA, citing Thinking Machines' guide), which hosted Tinker does not allow.

```bash
# From SkyRL's docs/content/docs/tinker/quickstart.mdx and cookbook.mdx (prerequisite: CUDA 13.0, NVIDIA driver r580 or newer)
git clone https://github.com/NovaSky-AI/SkyRL.git && cd SkyRL
uv venv --python 3.12 && uv sync --extra tinker --extra fsdp
uv run --extra tinker --extra fsdp -m skyrl.tinker.api \
    --base-model "Qwen/Qwen3-4B-Instruct-2507" --backend fsdp      # ready at "Uvicorn running on http://0.0.0.0:8000"

# second terminal, inside a tinker-cookbook checkout:
TINKER_API_KEY=tml-dummy uv run --with tinker --with datasets --with torch \
    python -m tinker_cookbook.recipes.rl_loop \
    base_url=http://localhost:8000 model_name="Qwen/Qwen3-4B-Instruct-2507"
```

Server options worth knowing: `--checkpoints-base` (default `/tmp/skyrl_checkpoints`, so move it to a persistent disk), `--port` (8000), `--backend fsdp|megatron`.

**Limitations (SkyRL `limitations.mdx`, 2026-10-14):** "KL penalty (`kl_penalty_coef > 0`) is not yet supported"; `sample()` does not return prompt logprobs (it logs a warning, no error); "Only `cross_entropy` and `importance_sampling` are currently wired through the Tinker data conversion path"; multi-tenant LoRA is Megatron-only, and full-parameter training is single-tenant. The server loads one `--base-model`, and every example in the docs passes that same name as the recipe's `model_name`.

**When to use it:** you prototyped on hosted Tinker and want to scale on your own or rented GPUs, need full fine-tuning, or need data to stay local. **When not to:** your recipe uses a KL penalty or `ppo` / `cispo`; your rented box has an NVIDIA driver older than r580 (check `nvidia-smi` first; see the CUDA 13 trap below).

### Fireworks Training API (Tinker-compatible client)

Aliases: Fireworks AI, `fw-ai/cookbook` (Apache-2.0), "Fireworks Serverless Training", "Firetitan", `FiretitanServiceClient`, `fireworks-ai[training]`.

**What it is.** Fireworks' Training API runs your training loop locally against remote trainers. **Serverless** mode attaches to a shared pooled trainer, is **LoRA only** ("Trainer capacity is shared with other tenants"), and is billed per token (prefill, sample and train meters); **Dedicated** mode provisions GPUs for full-parameter training with time-based billing (an idle dedicated trainer stops itself after 10 minutes with no activity, per the introduction page). The training client `FiretitanTrainingClient` is documented as "Tinker-compatible", and the cookbook's examples use `tinker.AdamParams`. Fireworks' older managed reinforcement fine-tuning (RFT) is deprecated: "**Managed reinforcement fine-tuning is deprecated.** Reinforcement learning has moved to the Training API."

```bash
# From docs.fireworks.ai/fine-tuning/training-api/serverless.md
git clone https://github.com/fw-ai/cookbook && pip install -e ./cookbook/training
export FIREWORKS_API_KEY="fw_..."
cd cookbook/training && python -m examples.serverless_rl.countdown_rl
# the docs warn "The default is a real paid run" — fork the example and reduce steps / group_size first
```

**When not to use it:** full fine-tuning or throughput-sensitive sweeps on the serverless pool (shared trainer, LoRA only); any new project on the deprecated managed RFT jobs.

### Together post-training (billed per GPU-minute)

Aliases: Together AI, "Together post-training", `togethercomputer/post-training-cookbook`, `client.post_training`, `ModelResourcesClient`.

**What it is.** A Tinker-style session API in which your code drives the loop and Together's GPUs run the heavy steps: `sample_batch`, `forward_backward`, `optim_step` and `weights_sync` (SFT and DPO skip the sampling and sync steps). Unlike Together's job-based fine-tuning (per token, SFT/DPO only), post-training bills **per GPU-minute while a model resource is `READY`**, and several adapters on one resource cost the same as one. The pricing page's worked example: `Qwen/Qwen3.8-27B` LoRA on `B200-SXM` with one generator replica uses 4 trainer + 4 generator GPUs, $11 per GPU-hour, $88 per hour; `estimate_cost(...)` returns the current rate without provisioning anything.

**Pitfall: it keeps billing after your script exits.** From the pricing page: "A resource keeps billing after your training script exits unless the script stops it… If you provision a resource yourself, use `ModelResourcesClient` as a context manager… Otherwise, an idle resource stops on its own only after an hour without an operation." Cookbook recipes stop the resources they create. A failed `READY` resource is refunded for a trailing window (3 hours LoRA, 6 hours full-weight).

**When not to use it:** you only need standard SFT or DPO on well-formed data (Together's job-based fine-tuning is simpler); you cannot guarantee the resource is stopped.

### OpenAI fine-tuning is closing (dates as of 2026-10-14)

Per OpenAI's deprecations page (`developers.openai.com/api/docs/deprecations.md`, read 2026-10-14): since **2026-05-07** organisations that had never run fine-tuning cannot create fine-tuning jobs; since **2026-07-02** only organisations that ran inference on a fine-tuned model in the past 60 days can; from **2027-01-06** no existing customer can create new fine-tuning jobs. Inference on an existing fine-tuned model continues until its base model shuts down: `ft-o4-mini-2025-04-16`, `ft-gpt-4.1-nano-2025-04-14`, `ft-gpt-3.5-turbo` and `ft-gpt-4` go on **2026-10-23**, and GPT-4o (`gpt-4o-2024-08-06`, `gpt-4o-2024-11-20`), GPT-4o mini, GPT-4.1 and GPT-4.1 mini go on **2027-01-14**, and the page states: "Fine-tuned versions of these models follow the same shutdown schedule as their underlying base models." The full table and what to do about existing organisms are in [`compute.md`](../models-and-compute/compute.md#finetuning-closed-weight-models-openai-shutdown-dates-as-of-2026-10-14). For anything new, train an open-weight model with one of the tools on this page.

## Self-hosted trainers

### TRL (Hugging Face)

Aliases: `trl` on PyPI, `huggingface/trl` on GitHub, "HuggingFace TRL", "the TRL library".

**What it is.** Hugging Face's post-training library. Implements PPO, GRPO, DPO, KTO, IPO (Identity Preference Optimization), ORPO, SimPO, RLOO, plus reward modeling, SFT and distillation. Tightly integrated with `transformers`, `accelerate`, `peft`.

**When to use it:**
- Self-hosted RL training on small-to-medium models, including on a single GPU (next subsection).
- Preference learning (DPO/KTO) — TRL is the de facto standard.
- You already use the Hugging Face stack and want minimum new abstractions.

**When *not* to use it:**
- Multi-node high-throughput RL — OpenRLHF, verl or prime-rl scale better.
- You don't want to manage GPUs — Tinker.

**GRPO defaults to report in a methods section** (from `trl/trainer/grpo_config.py`, v1.15.0; unchanged in v1.16.0): `beta=0.0` (no KL term, so no reference model is loaded), `loss_type="dapo"` (token-level normalisation over the global accumulated batch; `"dr_grpo"` and `"grpo"` are options, and the docstring calls `"grpo"` "Not recommended due to length bias"), `scale_rewards="group"` (divides by the per-group standard deviation; the docstring notes Dr. GRPO recommends no scaling), `learning_rate=1e-6`, `use_vllm=False`. A paper that says "we used GRPO in TRL" without these is ambiguous.

**Pitfalls:**
- **PPO trainer is fiddly.** Many sharp edges around reference-model handling, KL coefficient, generation kwargs. The DPO trainer is much smoother.
- **Memory: PPO loads up to 4 model copies** (policy, ref, reward, value). For 7B+ on a single 80GB GPU you need LoRA + gradient checkpointing.
- **`accelerate config` mismatch with TRL** is a common source of OOM and `RuntimeError: Expected all tensors to be on the same device`. Use TRL's example accelerate configs as starting point.
- **Long context + RL = slow.** Generation length dominates RL training time. Cap completion length aggressively while iterating.
- **Breaking changes between minor versions.** TRL is at v1.x with a release every one to two weeks (PyPI `trl` 1.16.0 on 2026-10-15). Pin the version in your run metadata; e.g. v1.14.0 removed the `trl.losses` module, so `from trl.losses import FusedLinearDPOLoss` (or `FusedLinearKTOLoss`, `FusedLinearGRPOLoss`, `FusedLinearJSDLoss`) raises an `ImportError` on newer versions, and `trl==1.12.0` on PyPI is a bit-identical accidental duplicate of 1.11.0.
- **vLLM outside the supported range only warns.** `trl/import_utils.py` checks the installed vLLM and, at the v1.16.0 tag, emits `TRL currently supports vLLM versions from 0.22.0 to 0.31.0. You have version … installed.` (v1.15.0 said `0.21.0 to 0.31.0`; 1.16.0's notes: "Drop vLLM 0.21.0 support") as a **warning**, not an error, so a run can start and fail later inside generation. vLLM 0.32.0 (2026-10-18) is newer than any TRL release supports, so a fresh unpinned install warns. Pin `vllm` inside that range alongside `trl`.
- **Silent wrong training with `torch_compile=True` before TRL 1.16.0.** The 1.16.0 notes: "`torch_compile=True` trained with `loss=0.0` and `grad_norm=nan` at every step" in the Triton loss kernels on torch < 2.11 (Inductor miscompiled them). Searchable symptom: `loss=0.0` and `grad_norm=nan` from step 1 with `torch_compile=True`. Re-run any such run on 1.16.0 or with torch ≥ 2.11.
- **FSDP2 + `vllm_mode="colocate"` crashed at step 1 on tied-embedding models** (e.g. small Qwen2 / Qwen2.5) with vLLM ≥ 0.29, because the weight sync iterated `state_dict()` and sent tied weights under both names; fixed in 1.16.0 (PR #7647).
- **Also changed in 1.16.0:** the experimental SSD trainer was removed; `RewardTrainer` refuses `nn.DataParallel`; `accelerate>=1.10.1` is required.
- **Process reward model (PRM) training was removed.** TRL removed `trl.experimental.prm`; axolotl v0.20.0's notes say PRM training now needs `trl<=1.13.0`.
- **Telemetry.** TRL's usage-stats doc: "A single ping is sent each time a trainer is instantiated" (TRL version, trainer class, known architecture, PEFT on/off, GPU model; no dataset names or paths). Opt out with `export HF_HUB_DISABLE_TELEMETRY=1` (or `HF_HUB_OFFLINE=1`); it is not sent when `CI` is set. Relevant on boxes where outbound traffic is restricted or logged.

**Recent releases (v1.10 → v1.16, 2026-08 → 2026-10; from the GitHub release notes):**
- **v1.16.0 (2026-10-15)** — fixes the silent `torch_compile` bug and the FSDP2 colocate tied-embedding crash above, drops vLLM 0.21.0; `AsyncGRPO` packs each micro-batch row as a prefix tree, so shared prompt prefixes in multi-turn or multi-generation rollouts are forwarded once (the notes' best case, a "nested fork" layout, ran 3.10× faster: 8,172 ms → 2,635 ms).
- **v1.10.0 (2026-08-13)** — `DistillationTrainer` / `DistillationConfig` graduate to the top level (`from trl import DistillationConfig, DistillationTrainer`) with a `trl distillation` CLI and VLM support; new experimental *loop-owning (black-box)* path for `AsyncGRPOTrainer` that trains external agents such as `opencode` which run their own tool loop: the agent runs in an **OpenEnv** session in `transparent_proxy` mode, an in-sandbox proxy captures each turn's token ids and logprobs, and TRL scores the workspace with the session's `verify()`.
- **v1.11.0 (2026-08-26)** — `trl vllm-serve` now forwards to vLLM's own server (`vllm serve`) with NCCL weight transfer; the notes report 1.4–1.6× faster GRPO server-mode steps. New experimental `AsyncDistillationTrainer` with multi-teacher on-policy distillation (MOPD).
- **v1.13.0 (2026-09-10)** — a long-context guide; the notes report Qwen3-8B trained at 1,048,576 tokens per sequence on one 8×H100 node (380 s/step, 56.2 GB per GPU).
- **v1.14.0 (2026-09-25)** — DPO, KTO and GRPO stream their own log-probs (see the breaking change above); `use_liger_kernel=True` now selects TRL's chunked log-prob path.
- **v1.15.0 (2026-10-08)** — fused LM head (a Triton kernel) for SFT, DPO, KTO, GRPO, RLOO and distillation scoring: the notes report up to 6.9× longer trainable sequences (KTO) and 52–82% lower peak memory at 8,192 tokens; needs Triton on a GPU (Linux with CUDA, ROCm or XPU).

#### How do I run TRL GRPO on a single GPU? (colocated vLLM + sleep mode)

In **colocate mode** "vLLM runs inside the trainer process and shares GPU memory with the training model" (TRL `vllm_integration.md`); it is the default `vllm_mode` once you set `use_vllm=True`, and `vllm_gpu_memory_utilization` (default 0.3) applies only in this mode. **Sleep mode** (`vllm_enable_sleep_mode=True`) offloads vLLM's weights and cache to CPU RAM during the optimizer step and reloads them for weight sync and generation, so policy and rollout engine fit on one card; the cost is host–device transfer latency on each wake-up.

```python
# Copied pattern from TRL docs (reducing_memory_usage.md / vllm_integration.md); see project_templates/rl_small for a full config
from trl import GRPOConfig
args = GRPOConfig(..., use_vllm=True, vllm_enable_sleep_mode=True)   # vllm_mode="colocate" is the default
```

```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True   # the name vLLM sleep mode reads
export PYTORCH_ALLOC_CONF=expandable_segments:True        # canonical name since PyTorch 2.10; set both
```

TRL's memory guide warns: "With vLLM sleep mode (`vllm_enable_sleep_mode=True`), vLLM only reads `PYTORCH_CUDA_ALLOC_CONF` to work around this setting, so don't set only `PYTORCH_ALLOC_CONF`." **When not to colocate:** you have a spare GPU for rollouts. Server mode (`vllm_mode="server"`, launched with `trl vllm-serve`) avoids memory contention, and in that mode "the **vLLM server** and the **trainer** must run on **separate CUDA devices** to prevent conflicts."

### Unsloth (single-GPU QLoRA / LoRA GRPO)

Aliases: **Unsloth**, `unslothai/unsloth` on GitHub (Apache-2.0), PyPI `unsloth` 2026.10.7 (2026-10-19, Python <3.15), "Unsloth Core" (the code library), distinct from "Unsloth Studio" (web UI) and "Unsloth Desktop" (app), which now dominate the README and the GitHub release list (`v0.1.907-beta`-style Studio betas).

**What it is.** A library that patches TRL and transformers for memory-efficient LoRA / QLoRA / full SFT, DPO and GRPO on one GPU, with vLLM generation sharing the trainer's GPU memory (`fast_inference=True`). The RL guide's rule of thumb: "For GRPO's **GPU VRAM requirements for QLoRA 4-bit**, the general rule is the model parameters = the amount of VRAM you will need" (roughly 8 GB for an 8B model, more with longer context), and "LoRA 16-bit will use at minimum 4x more VRAM".

```bash
# Unsloth Core install (README)
uv venv unsloth_env --python 3.13 && source unsloth_env/bin/activate
uv pip install unsloth --torch-backend=auto
```

**Pitfall: Qwen3.5.** The RL guide: "You can also run RL with Unsloth on models that are not supported by vLLM, such as Qwen3.5… Simply set `fast_inference=False` when loading the model" (`FastLanguageModel.from_pretrained(model_name="unsloth/Qwen3.5-4B", fast_inference=False)`). Generation then runs without vLLM and is slower, so budget for it.

**When not to use it:** multi-node or asynchronous RL; you need exact control of the loss and advantage code paths (it patches library internals, which makes "which GRPO did I run?" harder to answer); shared research boxes where you only need the library (skip the Studio installers).

### axolotl (YAML-configured fine-tuning)

Aliases: **axolotl**, `axolotl-ai-cloud/axolotl` on GitHub (Apache-2.0), PyPI `axolotl` 0.21.0 (2026-10-16, Python ≥3.12). The training backend of several safety toolkits, including the SDF pipeline `ArcadiaImpact/science-of-midtraining`.

**v0.20.0 breaking changes (release notes):**
- "**FSDP1 removed**… FSDP2 is the default and the only supported version." `fsdp_version: 1`, the top-level `fsdp` list, `sharding_strategy` (use `reshard_after_forward`) and `forward_prefetch` now raise. Migrate to `fsdp_version: 2` with `reshard_after_forward`. (`science-of-midtraining`'s stage configs already use `fsdp_version: 2`, checked 2026-10-14.)
- Python 3.12 and torch 2.13.0 are the new minimums; Modal moved to the `axolotl[modal]` extra; PRM training needs `trl<=1.13.0`.

**Silent bugs fixed in v0.20.0 — worth re-checking older runs against:** "Gradient accumulation was mis-normalized on some models"; "LoRA+ ignored `weight_decay`… so every LoRA+ run trained with `weight_decay=0.0` regardless of config"; quantized weights (NF4, load-time MoE quantization) were re-initialised at load. New: FSDP2 QLoRA stages and quantizes NF4 weights on CPU to avoid load-time GPU OOM. **When not to upgrade:** mid-project with FSDP1 configs — pin the older version and record it.

**v0.21.0 (2026-10-16): more silent training bugs fixed** (release notes) — re-check LoRA, QLoRA and expert-parallel runs made on 0.20.x:
- "**LoRA adapters saved empty under FSDP2 activation checkpointing**" (#4091) — check that a saved adapter's weights are non-zero.
- "**QLoRA merge quantized the wrong modules**" (#4120).
- "**LoRA+ dropped `embedding_lr`, and LoRA merge dropped trainable-token rows**" (#4110) — check that merged weights differ from the base where you trained.
- "**EP checkpoint resume overwrote other EP groups' expert weights and optimizer state**" (expert parallelism; restores now validate shapes before copying).
- "**SonicMoE EP silently ignored the expert LoRA on NVFP4**" (#4151): "runs trained attention LoRA only."
- Requirements: "`vllm>=0.30.0` is now required"; torch `<2.15.0`; the `axolotl[flash-attn]` extra is removed (Flash Attention 2 now comes from Hub kernels); Python ≥3.12.
- **Version trap: axolotl 0.21.0 and vLLM 0.31/0.32 cannot share an environment.** axolotl 0.21.0 pins `transformers==5.20.1` (PyPI `requires_dist`, checked 2026-10-20), while vLLM 0.31.0 requires `transformers<5.18.0` and vLLM 0.32.0 `transformers<5.20.0`. Of the vLLM releases axolotl accepts (`>=0.30.0`), only 0.30.0 admits 5.20.1, so `axolotl[vllm]` resolves to vLLM 0.30.0 or fails if you also pin a newer vLLM (symptom: pip `ResolutionImpossible` / uv `No solution found` naming `transformers`). For a newer vLLM, run it as a separate server in its own environment.

### OpenRLHF

Aliases: `openrlhf` on PyPI, `OpenRLHF/OpenRLHF` on GitHub, "OpenRLHF", "Jian Hu's library".

**What it is.** Ray-based RLHF framework with a focus on high performance and ease of use. Around 8.5k LOC — smaller than TRL, much smaller than verl. Supports PPO, DAPO, REINFORCE++, GRPO, async RL, vLLM rollouts.

**When to use it:**
- Self-hosted RL with multi-GPU / multi-node and reasonable performance.
- You want async RL (rollout and train concurrently — key for long-CoT models).
- Mid-scale: bigger than what fits comfortably in TRL on one box, smaller than verl's industrial deployments.

**When *not* to use it:**
- Single-GPU experiments — TRL is friendlier.
- You don't want to manage Ray — Tinker is friendlier still.

**Pitfalls:**
- **Ray learning curve.** Ray cluster setup is non-trivial; worker / actor placement matters.
- **vLLM integration version-sensitive.** vLLM and OpenRLHF have a tight coupling around weight updates; pin compatible versions.
- **Recent releases.** v0.11.0 (2026-08-13) fixed a `dr_grpo` guard for `n=1` and a `masked_normalize` broadcast bug and upgraded vLLM, DeepSpeed and transformers; v0.11.2 (2026-09-14) is the latest on PyPI (`openrlhf`). If you ran Dr. GRPO or masked-normalised losses on an older version, re-check those runs against the release notes.

### verl

Aliases: `verl`, `volcengine/verl` on GitHub, "ByteDance's RL framework". Sometimes capitalized "veRL".

**What it is.** ByteDance's high-performance distributed RL framework. ~32k LOC — the most feature-rich of the open-source options. Used for training frontier-scale Chinese open models. Single universal `WorkerDict` for all model roles (policy, ref, reward, critic) for resource sharing.

**When to use it:**
- You're training at frontier scale (multi-node, large MoEs).
- You need every last percent of throughput.
- You're reproducing a paper that used verl (pin that paper's verl version: `ariahw/rl-rewardhacking-ext`, for example, vendors verl v0.6.1 with `git clone --branch v0.6.1 --single-branch https://github.com/volcengine/verl.git` and `uv pip install --no-deps -e verl/`).

**When *not* to use it:**
- Research-scale experiments — overkill, steep learning curve.
- You need quick iteration — the abstraction stack is deep.

**Recent releases (v0.9.0, 2026-08-14; v0.9.1, 2026-09-20; PyPI `verl` 0.9.1):**
- A **unified V1 trainer** (`verl/trainer/ppo/v1`) now covers `sync`, `colocate_async` and `separate_async` modes with one replay buffer and metric surface, and is **enabled by default** in v0.9.0. v0.9.1 notes that `verl/experimental/fully_async_policy` and `verl/experimental/one_step_off_policy` are deprecated by it and will move to `verl-recipe`, so configs that import them will break.
- **`uni-agent`** (`verl-project/uni-agent`, "a framework for training long-horizon agents"): bring any harness (Claude Code, Mini-SWE-Agent, or anything speaking an OpenAI/Anthropic-compatible endpoint) through its gateway, with 1,000+ concurrent stateful sessions per the release notes.
- A **Continuous Token** mechanism for multi-turn agentic rollouts keeps token continuity across assistant output, tool/environment feedback and the next prompt (disabled by default) — relevant to the retokenisation drift described in [`training-on-trajectories.md`](training-on-trajectories.md).
- DRO losses and token-sum loss aggregation (v0.9.0); full determinism for vLLM rollout and reward-model inference so two identical runs give bitwise-aligned reward curves (v0.9.0); `uv` dependency management with a committed `uv.lock` and transformers 5.9.0 (v0.9.1).
- Pitfall: v0.9.1 notes that the full Python garbage-collection call added before rollout weight resume in v0.9.0 caused a measured throughput regression on colocated weight sync and was removed — if you benchmarked v0.9.0, re-benchmark.

### prime-rl (asynchronous RL, 2 GPUs to 1,000+)

Aliases: **prime-rl**, **PRIME-RL**, `PrimeIntellect-ai/prime-rl` on GitHub (Apache-2.0; not on PyPI — install from the repo), Prime Intellect, INTELLECT models.

**What it is.** Fully asynchronous RL (an FSDP2 trainer, vLLM inference and an orchestrator) with native `verifiers` environments from the Environments Hub, plus SFT, evals, LoRA and Slurm multi-node launch. The README says it is developed and tested on "NVIDIA RTX 3090/4090/5090, A100, H100, H200, and B200". Latest release v0.10.0 (2026-10-13).

```bash
# README "Validate your environment setup"
curl -sSL https://raw.githubusercontent.com/PrimeIntellect-ai/prime-rl/main/scripts/install.sh | bash
uv run python -c "import flash_attn"
uv run sft @ configs/debug/fake/sft.toml          # SFT check: 1 GPU
uv run rl @ examples/basic/reverse-text/rl.toml   # full RL stack: 2 GPUs (one trainer, one inference)
```

**Defaults to report in a methods section (v0.10.0 release notes):**
- "**IPO (INTELLECT Policy Optimization) is the new default loss** (`eps = 0.3`, no KL term)." It masks a token when its probability moved too much between the inference engine and the trainer (a double-sided mask that ignores the advantage sign). ⚠️ **Name collision:** this IPO is unrelated to IPO = Identity Preference Optimization (Azar et al., arXiv:2310.12036), the DPO variant in TRL. Always expand the acronym.
- "RL freezes the MoE router by default" (`freeze_moe_router = "auto"`; set `trainer.model.freeze_moe_router = false` to train it).
- IcePop, PPO and CISPO remain opt-in via `[trainer.loss] type = ...`; the old DPPO default loss is removed (rename `ipo_threshold` to `eps`).

**When not to use it:** a single small GPU for RL — the reverse-text example's commands "were designed to be run on 2 GPUs (one trainer and one inference GPU)" (SFT runs on one, and the LoRA alphabet-sort RL example "runs on a single H100 GPU"); a model architecture outside `src/prime_rl/trainer/models/` ("Other architectures fail at trainer setup"); a project that wants a KL-to-reference regulariser by default.

### OpenPipe ART (RL on your existing agent code)

Aliases: **ART** (Agent Reinforcement Trainer), `OpenPipe/ART` on GitHub (Apache-2.0), PyPI `openpipe-art` 0.5.21 (2026-10-20, Python ≥3.12; also the latest GitHub release, the first since v0.5.19 on 2026-08-14), RULER (its LLM-judge reward), W&B "Serverless RL" backend.

**What it is.** Your application calls the model through an OpenAI-compatible ART client; each rollout's messages are stored in a `Trajectory` that your code assigns a reward to; an ART server (local GPU, ephemeral cloud GPU, or W&B Training's Serverless RL backend) trains a LoRA with GRPO via Unsloth and vLLM and hot-loads it. Install with `pip install openpipe-art`.

**When not to use it:** throughput or exact token-level control matters — per the README, "Inference is blocked while training executes"; Gemma 3 ("Gemma 3 does not appear to be supported for the time being"); a project where RULER's LLM-judge reward would itself be the object of the reward hacking you are measuring.

**Pitfall: v0.5.21 (2026-10-20) changed the GRPO update.** From the release notes: "Zero-variance GRPO updates are skipped", "policy importance ratios are bounded before exponentiation", "TIS is skipped when original logprobs are unavailable" (TIS = truncated importance sampling), "use population std for native Tinker advantages", and several logprob and gradient paths now use FP32. GRPO curves from ≤0.5.20 and from 0.5.21 are not directly comparable; record the version.

### Agent Lightning (Microsoft) — RL for agents in their own harness

Aliases: `agentlightning` on PyPI (v1.0.2, 2026-09-29), `microsoft/agent-lightning` on GitHub, "Agent Lightning v1.0", arXiv:2608.17528 (He, Zhang, Zhou, Yang, Kang et al., 2026-08-18).

**What it is.** A lightweight (~3,500 lines per the paper) framework for **harnessed agentic RL**, where the agent's deploy-time harness (tools, context management, control flow) owns the environment loop and the trainer only sees sequences of LLM request–response pairs, connected through an LLM-endpoint proxy. The paper reports that RL with 6K training examples raised Qwen3.5-9B on SWE-bench Verified from 41.8% to 56.4%, and lists the hard parts of this setup: retokenisation, sample merging, advantage calculation, loss normalisation and backend scheduling.

**When to use it:** you want to RL-train an agent *as it is actually deployed* (a coding-agent CLI, a search agent) rather than re-implementing its loop in a trainer. **When *not* to use it:** you only need single-turn RLVR (use TRL / the Tinker Cookbook), or you need the trainer to own the loop and token accounting exactly (use verl or TRL's white-box `environment_factory` path).

**Pitfall:** because the harness, not the trainer, builds the prompts, the tokens the model saw at rollout and the tokens the trainer re-tokenises can differ (the paper lists retokenisation as a core difficulty); record token ids at the proxy rather than re-tokenising logged text.

### Don't start new work on torchtune or torchforge

- **torchtune** (`meta-pytorch/torchtune`, BSD-3-Clause; last release v0.6.1, 2025-04-07): the README opens with "⚠️ **Torchtune is no longer actively maintained:** torchtune development wound down in 2025". Older papers and blog recipes still point at torchtune configs; use it only to reproduce such a paper exactly, pinned to v0.6.1.
- **torchforge** (`meta-pytorch/torchforge`, no releases): "⚠️ **Development paused:** Development in Forge has paused. LLM training at PyTorch is being consolidated in torchtitan."
- **Instead:** `pytorch/torchtitan` (v0.3.0, 2026-09-03) or prime-rl for PyTorch-native training; TRL or axolotl for Hugging Face-native SFT / LoRA.

### Other active RL stacks (not covered in depth)

Active as of 2026-10-14 but either industrial-scale or duplicating TRL / axolotl / Unsloth for safety work: **slime** (`THUDM/slime`, v0.4.0, 2026-10-09; Megatron + SGLang), **AReaL** (`areal-project/AReaL`, v2.1.0, 2026-08-25), **ROLL** (`alibaba/ROLL`, v0.4.0, 2026-09-29), **LlamaFactory** (`hiyouga/LlamaFactory`, v0.9.5, 2026-05-30), **ms-swift** (`modelscope/ms-swift`, v4.6.0, 2026-10-13), **oumi** (`oumi-ai/oumi`, v0.9, 2026-09-16), **tunix** (`google/tunix`, JAX, v0.1.7, 2026-06-11), **rLLM** (`rllm-org/rllm`, v0.3.0-pre, 2026-04-30; the old `agentica-project/rllm` is stale), and **NeMo RL** (`NVIDIA-NeMo/RL`, v0.7.0, 2026-07-29; the PyPI name `nemo-rl` is a 0.0.0 placeholder, so install from the repo or container — it ships the Nemotron-3.5-Lightning RLVR recipe, see [`open-weights-models.md`](../models-and-compute/open-weights-models.md)). `NousResearch/atropos` is archived.

## LoRA settings that match full fine-tuning (LoRA Without Regret)

Aliases: "LoRA Without Regret" (Schulman and Thinking Machines Lab, 2025, `thinkingmachines.ai/blog/lora/`, doi 10.64434/tml.20250929), TRL doc `lora_without_regret.md`, all-linear LoRA, rank-1 LoRA for RL.

TRL's documentation reproduces the blog's findings. The settings, in the doc's words where quoted:

| Setting | Recommendation | Source line (TRL doc) |
|---|---|---|
| Which layers | All linear layers: `LoraConfig(target_modules="all-linear")` / `--lora_target_modules all-linear` | "Attention-only LoRA underperforms even when using a higher rank to match parameter count." |
| Rank for RL | 1–32 ("policy gradient algorithms extract roughly ~1 bit of information per episode") | Table: RL, any dataset size, rank 1–32 |
| Rank for SFT | 256 at "post-training scale" | "For datasets that exceed LoRA capacity, LoRA underperforms FullFT" |
| Learning rate | Higher than full fine-tuning; the TRL reproduction used 1.0e-5 for LoRA vs 1.0e-6 for full fine-tuning | "the blog post recommends using a higher learning rate than for full fine-tuning" |
| Batch size | Effective batch size < 32 | "This could not be mitigated by increasing the LoRA rank." |

The doc's GRPO example uses `LoraConfig(r=1, lora_alpha=32, target_modules="all-linear")` with `GRPOConfig(learning_rate=5e-5, num_generations=8, ...)`; its CLI reproduction passes `--lora_r 1 --lora_alpha 32 --lora_dropout 0.0 --lora_target_modules all-linear --vllm_mode colocate` and sets `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. A practitioner data point from model-organism work: Mitrani's MATS 10.0 retrospective (LessWrong, 2026-10-01) used LoRA rank 8 throughout an SDF + SFT + RL organism project after finding it "extremely similar to ranks 16 and 32" (he expects this not to generalise).

**When not to use these settings:** rank-1 for large SFT datasets (beyond LoRA's capacity it underperforms full fine-tuning); raising the batch size to compensate for a small rank (the doc says rank does not fix the batch-size intolerance). A known trap is attention-only `target_modules=["q_proj","k_proj","v_proj","o_proj"]` lists copied from older scripts.

## RL environment libraries: OpenEnv, verifiers, Harbor, OpenReward

| Library | What it is | Use it for | When not |
|---|---|---|---|
| **OpenEnv** (`huggingface/OpenEnv`, formerly `meta-pytorch/OpenEnv`; BSD-3-Clause; PyPI `openenv` 0.9.0, 2026-10-15, which removed `opencode_env` and `pi_env` — **not** the stale `openenv-core` 0.3.0) | A `reset()` / `step()` / `state()` API "sync or async, over a WebSocket" to environments that are each a Docker image (local, cloud sandbox or Hugging Face Space); 40+ in the catalog | TRL `GRPOTrainer(environment_factory=...)` white-box tool environments; Harbor-captured traces for loop-owning harnesses; `openenv import` wraps an existing ORS/OpenReward or Verifiers environment | Single-turn RLVR, where the Docker/WebSocket hop is pure overhead; public Spaces holding secrets |
| **verifiers** (`PrimeIntellect-ai/verifiers`, MIT; PyPI `verifiers` 0.4.0, 2026-10-12) + **Environments Hub** / `PrimeIntellect-ai/community-environments` (Apache-2.0) | Prime Intellect's environment, harness and evaluation library; CLIs are `vf-eval`, `vf-validate`, `vf-debug`, `vf-replay`, `vf-init`, `vf-gepa` | prime-rl training; the Tinker Cookbook `verifiers_rl` recipe (on verifiers 0.1.9) | Mid-project upgrades (see the pitfall) |
| **Harbor** (`harborframework.com`; TRL integration `trl.experimental.harbor`, `pip install trl[harbor]`) | Decouples a task (instruction + sandbox image + verifier), a harness and a sandbox (`docker`, `e2b`, `daytona`, `gke`…); `HarborSpec` fills TRL's `train_dataset`, `environment_factory` and `reward_funcs` slots | Training on a Harbor task suite, including real coding-agent harnesses with exact-token capture | Needs `vllm` and `transformers>=5.2.0`, Python ≥3.12 |
| **OpenReward / ORS** (Open Reward Standard; TRL `trl.experimental.openreward`, `pip install trl[openreward]`) | An HTTP/SSE protocol for environments' tasks, tools, sessions and rewards; `OpenRewardSpec("Eigent/SETA", num_tasks=64)` | ORS environments from the openreward.ai catalog, self-hosted or on localhost | Single-turn RLVR, where a Python reward function suffices; a single-host self-hosted server also needs the SDK's default two-subdomain (`api.` / `sessions.`) layout overridden |

**Pitfall: `verifiers` 0.4.0 changed defaults that move rewards.** From the v0.4.0 release notes: "**The legacy v0 stack is removed.**" (use `import verifiers.v1 as vf`); "**Bash context compaction is enabled by default.**"; "**Rollouts have no default four-hour timeout.**"; and "**Judges default to `openai/gpt-6-luna`.** Pin a model explicitly for reproducible comparisons". Compaction changes what the policy sees, a missing timeout changes which rollouts finish, and a judge change rescales rewards — so don't upgrade in the middle of a project, and pin the judge model.

## vLLM hooks for a hand-rolled RL loop (sleep, weight transfer, pause/resume)

Aliases: vLLM sleep mode, `enable_sleep_mode`, `llm.sleep(level=...)`, `wake_up(tags=...)`, vLLM weight transfer, `WeightTransferConfig`, `pause_generation`, `resume_generation`, one-step-off-policy async RL. vLLM latest release v0.32.0 (2026-10-18; previous v0.31.0, 2026-10-05). TRL 1.16.0 does not yet support 0.32.0 (its range ends at 0.31.0), so this section matters most if you drive vLLM yourself.

- **Sleep levels** (`docs/features/sleep_mode.md`). `LLM(..., enable_sleep_mode=True)`. Level 1 offloads weights to CPU RAM and discards the KV cache ("good for sleeping and waking up the engine to run the same model again"). Level 2 discards both: "good for sleeping and waking up the engine to run a different model or update the model, where previous model weights are not needed, e.g. RLHF weight update." Wake the weights first, load the new weights, then allocate the KV cache, to avoid out-of-memory peaks during the update:

  ```python
  # From vLLM docs/features/sleep_mode.md
  llm.sleep(level=2)
  llm.wake_up(tags=["weights"])    # load updated weights here
  llm.wake_up(tags=["kv_cache"])
  ```

  For a server: `VLLM_SERVER_DEV_MODE=1 vllm serve <model> --enable-sleep-mode`, then `curl -X POST 'http://localhost:8000/sleep?level=1'` and `curl -X POST 'http://localhost:8000/wake_up'`.
- **Weight transfer** (`docs/training/weight_transfer/README.md`). Pluggable backends: **IPC** (CUDA IPC handles; "Colocated training and inference on same GPU"), **NCCL** ("Separate GPUs for training and inference"), `sparse_nccl`, `sharded_rdt` (very large MoE models), `nccl_m2n` (different sharding layouts), and since v0.32.0 `modelexpress`. v0.32.0 also releases weight-transfer communicators "without stopping inference" and adds weight-transfer metrics and `POST /weight_checker`. Runnable examples are in `examples/rl/` (`rlhf_http_ipc.py`, `rlhf_http_nccl.py`, `rlhf_async_new_apis.py`, `pause_resume/`, `batch_invariance/` and others, all in the v0.32.0 tag).
- **Pause and resume** (`docs/training/async_rl.md`). `await engine.pause_generation(mode="keep", clear_cache=True)` freezes in-flight requests during a weight swap and `resume_generation()` continues them; requests paused with `"keep"` produce tokens from the old weights before the pause and the new weights after, and the `clear_cache` flag decides whether old-weight KV entries survive. Since v0.32.0 vLLM labels this for you: set a label while paused (pass `weight_version` to `finish_weight_update`, or `POST /update_weight_version`) and every output carries `weight_versions`, one span per label over its output-token indexes ("token-level weight-version spans on outputs" in the release notes); `GET /weight_info` returns the latest committed label. On v0.31.0 outputs carry no `weight_versions` spans (a label set with `finish_weight_update(weight_version=...)` is only readable via `GET /weight_info`), so track the boundary yourself.
- **v0.32.0 removed the deprecated pause flag.** The release notes: "Previously deprecated APIs were removed: `wait_for_inflight_requests` (use `mode="wait"`)". The keyword argument is gone from `pause_generation()` (the method itself remains). The default is unchanged from v0.31.0, `mode: PauseMode = "abort"`, which per the docstring will "Abort all in-flight requests immediately" — so code that passed `wait_for_inflight_requests=True` now fails, and code that drops the argument without adding a mode silently aborts rollouts during each weight sync. Pass `mode="keep"` (freeze and continue) or `mode="wait"` (drain) explicitly. Searchable symptom: `TypeError: ... got an unexpected keyword argument 'wait_for_inflight_requests'`.
- **Other v0.32.0 changes that touch RL loops.** Sleep now also releases workspace scratch ("up to 4.5 GiB/GPU") and KV-init state ("about 4.6 GiB/GPU"), so colocated trainers get more memory back; `sleep(level=2)` keeps FP8 KV scales; `max_tokens` "is treated as an upper bound on output rather than reserved from the context window", so a long prompt is no longer rejected and generation is clamped instead — check `finish_reason == "length"` when rollouts look truncated. Pins: `torch==2.13.0`, `transformers>=5.16.1,<5.20.0`, Python ≥3.11 (general serving traps for this release are on [`compute.md`](../models-and-compute/compute.md)).

**When not to use these:** don't expose a `VLLM_SERVER_DEV_MODE=1` server beyond localhost — the docs say "these endpoints should not be exposed to users", and they include `/collective_rpc`; and don't hand-roll this when TRL, verl or prime-rl already does it.

## Version traps (search these symptoms)

- **`The NVIDIA driver on your system is too old (found version …)`** (PyTorch, `c10/cuda/CUDAFunctions.cpp`). vLLM 0.31.0's and 0.32.0's install tables list `pip install vllm` as "PyPI (CUDA 13.0)", with a separate CUDA 12.9 image (`vllm/vllm-openai:v0.32.0-cu129` for the current release) and CUDA 12.9 wheels on the release page; SkyRL's Tinker quickstart requires "CUDA 13.0 (NVIDIA driver r580 or newer)". On a rented RunPod / vast.ai box, run `nvidia-smi` first; if the driver is older than r580, use the cu129 artifacts or pick a host image with a newer driver.
- **PyTorch 2.14.0 with CUDA 13.2 binaries.** PyTorch v2.14.1 (2026-09-30) is a regressions and silent-correctness release; it moves the CUDA 13.2 Linux binaries to CUDA 13.2.2 because of a cuBLAS NVFP4 scaling bug and a compiler bug where "failed thread reconvergence could leave stale or corrupted register values in kernels with nested thread divergence (present since CUDA 12.8)". Upgrade to 2.14.1.
- **`TRL currently supports vLLM versions from 0.22.0 to 0.31.0. You have version … installed.`** (TRL 1.16.0; TRL 1.15.0 printed `0.21.0 to 0.31.0`). A warning only (see TRL above); vLLM 0.32.0 triggers it.
- **`loss=0.0` and `grad_norm=nan` at every step with `torch_compile=True`** — TRL before 1.16.0 on torch < 2.11 (see TRL above).
- **`TypeError` on `pause_generation(wait_for_inflight_requests=...)`, or rollouts aborted during a weight sync** — vLLM 0.32.0 removed the flag, and the default `mode` is `"abort"` (see vLLM hooks above).
- **PEFT before 0.21.0: an adapter that adapts nothing.** From the v0.21.0 notes: `add_adapter` now errors when a second adapter targets non-existing layers — "Before, the adapter would just not adapt anything but be silent about it." Also "Combining LoRA adapters using `add_weighted_adapter` had a bug in the `SVD` path which led to the LoRA scaling being applied twice", and deleting a merged adapter now raises. After attaching an adapter, assert `peft_model.targeted_module_names` is non-empty, and re-run any adapter-arithmetic result built with `combination_type="svd"`. The MoE LoRA delta and OSF paths changed numerics slightly, so don't expect bit-identical results across the upgrade.
- **axolotl 0.20.0: FSDP1 keys raise** (see axolotl above). **axolotl 0.21.0** fixes LoRA adapters saved empty under FSDP2 activation checkpointing and wrong-module QLoRA merges, and requires `vllm>=0.30.0`.
- **`verifiers` 0.1.9 vs 0.4.0** cannot share one virtualenv for the Tinker Cookbook (see the cookbook pitfall).
- **verl 0.9.x** deprecates `verl/experimental/fully_async_policy` and `one_step_off_policy`; repos built on verl 0.6.x (e.g. `ariahw/rl-rewardhacking-ext`) should keep their pinned version.
- **Tinker model retirements** (2026-06-12, 2026-07-12, 2026-10-23): hard-coded model IDs stop working.
- **"IPO"** means INTELLECT Policy Optimization in prime-rl and Identity Preference Optimization in TRL / the DPO literature.
- **Qwen3 chat templates strip `<think>`** blocks, which some Environments Hub reward functions penalise.

## Common questions

### Which framework should I use for my first RL project?

If you have no GPUs: the **Tinker Cookbook** on hosted Tinker. If you have one GPU: **TRL GRPO** with colocated vLLM and sleep mode (or **Unsloth** for QLoRA on a 24 GB card). If you have two or more GPUs and want asynchronous agentic RL: **prime-rl**. Start from `project_templates/rl_small/`, which has a TRL single-GPU config and a Tinker / SkyRL script that switches between hosted and local by changing `base_url`.

### How do I get access to Tinker?

Sign up via `thinkingmachines.ai/tinker/` (the cookbook README links `auth.thinkingmachines.ai/sign-up`; create an API key in the Tinker console and export it as `TINKER_API_KEY`). Was private beta during late 2025; usage-based pricing is now published on the Models & Pricing page. As of 2026-10 it's the default RL/SFT tool for many MATS fellows because you don't manage GPUs. For status, check the Tinker docs or ask in the relevant Slack channels.

### How much does Tinker cost?

During the late-2025 private beta it was free; it is now billed per million tokens with separate prefill, sample and train rates (80% off cached prefill; checkpoint storage $0.10 per GB-month). Example from the Models & Pricing page on 2026-10-09: `Qwen/Qwen3-8B` at $0.195 prefill / $0.60 sample / $0.44 train per million tokens; the Inkling and some Nemotron models carried a limited-time 50% discount. Track usage during long RL runs — sample × N completions × LoRA-train × gradient steps adds up. Compared to renting H100s and managing infra yourself, the API premium typically buys back significant fellow-time. Check current pricing on the Tinker docs before budgeting; prices and the model list change.

### Can I run Tinker Cookbook recipes without a Tinker account?

Yes, on your own GPUs: start SkyRL's local Tinker server (`uv run --extra tinker --extra fsdp -m skyrl.tinker.api --base-model <model> --backend fsdp`) and pass `base_url=http://localhost:8000` with a dummy key (`TINKER_API_KEY=tml-dummy`). KL penalties, prompt logprobs and the `ppo` / `cispo` losses are not yet wired through, and it needs CUDA 13.0 with driver r580+.

### Can I bring my own reward model to Tinker?

Yes — write a Python `grade(rollout) -> float` function. The Tinker Cookbook's recipes show this pattern. Your grader can be: a programmatic verifier (math equality, unit tests), an LLM-as-judge call (via safety-tooling for caching), or a learned reward model you trained separately.

### Can I do GRPO on a single 24 GB GPU?

For small models, yes. Unsloth's rule of thumb for QLoRA 4-bit GRPO is VRAM ≈ the parameter count in GB (about 8 GB for an 8B model before long contexts), and LoRA 16-bit needs at least 4× that. With TRL, use colocated vLLM with `vllm_enable_sleep_mode=True`, a small `vllm_gpu_memory_utilization`, LoRA on all linear layers, and a short `max_completion_length`.

### My GRPO run uses Qwen3.5 and Unsloth generation is slow — why?

Unsloth's RL guide names Qwen3.5 as a model "not supported by vLLM"; it is loaded with `fast_inference=False`, so generation runs without vLLM.

---

## Cross-references

- Algorithms, reward hacking, reward models, honesty training and RL safety patterns: [`rl-training.md`](rl-training.md).
- Loss masking and token-exact capture for agent trajectories: [`training-on-trajectories.md`](training-on-trajectories.md).
- Building model organisms with these tools, and the model-organism hygiene checklist: [`model-organisms.md`](../alignment-science/model-organisms.md).
- Renting GPUs, the CUDA-driver check and OpenAI fine-tuning shutdown dates: [`compute.md`](../models-and-compute/compute.md).
- Which open model to train: [`open-weights-models.md`](../models-and-compute/open-weights-models.md).
- Experiment tracking for RL runs: [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

---

Last verified: 2026-10-20. Updated 2026-10-20: versions table re-checked against PyPI JSON for every package (trl 1.16.0, vllm 0.32.0, tinker 0.34.0, unsloth 2026.10.7, axolotl 0.21.0, openenv 0.9.0, openpipe-art 0.5.21 changed; the rest unchanged, prime-rl via its GitHub release list); release notes via `gh api` for TRL v1.16.0 (plus PR #7647 and `trl/import_utils.py` / `trl/trainer/grpo_config.py` at the v1.16.0 tag), vLLM v0.32.0 (plus `vllm/v1/engine/async_llm.py` at v0.31.0 and v0.32.0, PR #60923's diff, `docs/training/async_rl.md` and `examples/rl/` at v0.32.0), axolotl v0.21.0, OpenPipe ART v0.5.21 and OpenEnv v0.9.0; tinker 0.34.0's `model list` command and `copy_weights()` read from `src/tinker/cli/commands/model.py` and `rest_client.py` in `thinking-machines-lab/tinker`. Quotes are exact substrings of those sources. Moved here from `rl-training.md` on 2026-10-14: the Tinker, Tinker Cookbook, TRL, OpenRLHF, verl and Agent Lightning sections (their earlier verification notes remain in that page's footer). New on 2026-10-14, each checked against the primary source: PyPI JSON for every version and date in the versions table; `gh api` repo metadata and release notes for SkyRL, prime-rl v0.10.0, verifiers v0.4.0, axolotl v0.20.0, PEFT v0.21.0, vLLM v0.31.0, PyTorch v2.14.1, OpenEnv, OpenPipe ART, torchtune, torchforge and the "other stacks" list; raw docs read via the GitHub contents API (SkyRL `docs/content/docs/tinker/{quickstart,cookbook,limitations}.mdx`; TRL `docs/source/{vllm_integration,reducing_memory_usage,usage_stats,lora_without_regret,grpo_trainer,harbor,openreward}.md`, `trl/import_utils.py` and `trl/trainer/grpo_config.py`; vLLM `docs/features/sleep_mode.md`, `docs/training/async_rl.md`, `docs/training/weight_transfer/README.md`, `examples/rl/`; tinker-cookbook `pyproject.toml`, `recipes/rl_loop.py`, `recipes/verifiers_rl/README.md`; tinker `service_client.py`; PyTorch `c10/cuda/CUDAFunctions.cpp`); Fireworks (`docs.fireworks.ai/fine-tuning/training-api/{serverless,introduction}.md`, `reinforcement-fine-tuning-models.md`) and Together (`docs.together.ai/docs/post-training/{overview,pricing}.md`) docs fetched as raw markdown; OpenAI dates from `developers.openai.com/api/docs/deprecations.md` (raw markdown, 2026-10-14). Quotes are exact substrings of those sources.
