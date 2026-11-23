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
| The same Tinker Cookbook script on your own GPUs, or full-parameter fine-tuning through the Tinker API | **SkyRL's Tinker backend** (`skyrl.tinker.api`, `skyrl-project/SkyRL`, formerly NovaSky-AI/SkyRL) | Your recipe needs a KL penalty, prompt logprobs, or the `ppo` / `cispo` losses; your NVIDIA driver is older than r580; you need the newest tinker SDK (SkyRL 0.5.0 supports tinker < 0.28) |
| A Tinker-style loop on another provider | **Fireworks Training API** (serverless LoRA, billed per token) or **Together post-training** (GPUs you reserve, billed per GPU-minute) | Throughput-sensitive sweeps on Fireworks' shared pool; leaving a Together resource running after your script ends |
| GRPO / DPO / SFT on one GPU with the Hugging Face stack | **TRL** with colocated vLLM and sleep mode | You have a spare GPU for rollouts (use TRL's vLLM server mode instead) |
| QLoRA or LoRA GRPO on a single consumer GPU (24 GB) | **Unsloth** (Unsloth Core, `unsloth` on PyPI) | Multi-node or asynchronous RL; you need exact control of the loss and advantage code |
| Config-driven (YAML) SFT / DPO / QLoRA with multi-GPU FSDP2 | **axolotl** | Your configs still use FSDP1 keys and you cannot migrate mid-project (pin `axolotl<0.20`) |
| Asynchronous RL from 2 GPUs up to a cluster, with `verifiers` environments | **prime-rl** (PrimeIntellect-ai) | You cannot give it a Prime API key and forget `--no-monitors.prime` (v0.11.0 refuses to launch); a single non-H100-class GPU for RL (its one single-GPU RL example, alphabet-sort, uses LoRA on an H100); a model architecture outside its supported list; you need a KL-to-reference term by default |
| Multi-node asynchronous RL with Ray | **OpenRLHF** | Single-GPU experiments |
| Industrial-scale RL with maximum throughput | **verl** (ByteDance) | Research-scale experiments where you want to read the whole loop |
| Add GRPO to an existing Python agent that already calls an OpenAI-compatible endpoint | **OpenPipe ART** (`openpipe-art`) | Throughput or exact token-level control matters (its loop is synchronous) |
| Train an agent inside its own harness (Claude Code, mini-SWE-agent, OpenCode) | **Agent Lightning v1.0**, **verl `uni-agent`**, or TRL's `AsyncGRPOTrainer` with OpenEnv / Harbor capture | Single-turn RLVR, where a reward function is enough |
| A reusable RL environment behind a standard interface | **OpenEnv** (`openenv`), **verifiers** / Environments Hub, **Harbor**, **OpenReward** (ORS) — see [RL environment libraries](#rl-environment-libraries-openenv-verifiers-harbor-openreward) | Single-turn RLVR where a Python reward function suffices |
| A hand-rolled loop that shares one GPU between trainer and vLLM | **vLLM sleep mode + weight transfer** — see [vLLM hooks](#vllm-hooks-for-a-hand-rolled-rl-loop-sleep-weight-transfer-pauseresume) | TRL, verl or prime-rl already fits |
| Fine-tune GPT-4o / GPT-4.1 through OpenAI | Don't start: see [OpenAI fine-tuning is closing](#openai-fine-tuning-is-closing-dates-as-of-2026-10-14) | — |
| LoRA settings that match full fine-tuning | [LoRA Without Regret settings](#lora-settings-that-match-full-fine-tuning-lora-without-regret) | — |

## Versions as of 2026-11-23 (record these in every run's metadata)

Most "my run broke" reports in this area are version mismatches. Latest releases, checked on PyPI and GitHub on 2026-11-23 (previous checks 2026-11-04, 2026-10-20 and 2026-10-14):

| Package (PyPI name) | Latest | Released | Why the version matters |
|---|---|---|---|
| `trl` | 1.18.2 | 2026-11-19 | Releases every one to two weeks; 1.18.x supports vLLM 0.23.0–0.33.x (so **not** the current vLLM 0.34.0). 1.18.0 (2026-11-13) fixes six silent training-correctness bugs (default CISPO gradients 5× too small; assistant-only loss mask on Qwen3, GLM-4-MoE, DeepSeek, Nemotron 3 and gpt-oss templates; stale prefix-cache KV in AsyncGRPO; MoE models saved by `SFTTrainer` 1.7.0–1.17.1 keep `output_router_logits=True`), makes `AsyncGRPOTrainer` a stable trainer with renamed config keys and metrics, and adds server-mode candidate-set renormalisation for `top_p` / `min_p`, active only when the vLLM server is started with `--return-sampling-mask` (see TRL below). 1.17.0 (2026-10-29) fixed the colocate-mode importance-sampling ratio and changed the AsyncGRPO default objective |
| `vllm` | 0.34.0 | 2026-11-16 | Pins `torch==2.14.0` and `transformers>=5.16.1,<5.23.0`, Python 3.11–3.14 (PyPI `requires_dist`); outside TRL 1.18.x's supported range (`vllm>=0.23.0,<0.34.0`), and SkyRL 0.5.0 pins `vllm==0.33.0`. 0.33.0 (2026-11-02) went CUDA 13.0-only (no more CUDA 12.9 / `-cu129` artifacts) and fixed a silent MoE expert-weight corruption in packed NCCL weight sync (see vLLM hooks). General serving changes: [`compute.md`](../models-and-compute/compute.md#vllm-0320-upgrade-traps-released-2026-10-18) |
| `torch` | 2.15.0 | 2026-10-28 | Wheels are `cu132` / `cu134` only (hosts with a CUDA 12.x driver stay on 2.14); FSDP2 `reduce_dtype=None` semantics changed (BC-breaking). vLLM 0.33.0 / 0.34.0 (`torch==2.14.0`), SkyRL 0.5.0, axolotl and Unsloth all still require torch < 2.15, so an RL environment usually gets 2.14.x — which is the range affected by PyTorch advisory GHSA-v32g-mr63-3j83 (`torch.load(weights_only=True)` can read arbitrary text files; patched in 2.15.0; see Version traps) |
| `peft` | 0.22.0 | 2026-11-19 | 0.22.0 ships the fix for MoE LoRA silently skipping dense and shared-expert layers under transformers v5 (affected: 0.19–0.21.3 — a range stated by the TRL maintainers, not by PEFT, whose notes name none; **0.21.3, 2026-11-13, does not have the fix**), changes `modules_to_save` matching, and requires Python ≥3.11; 0.21.0 fixed two silent failures (a second `add_adapter` adapter that adapts nothing; double-scaled SVD merges). axolotl 0.21.1 pins `peft==0.21.2` and SkyRL 0.5.0 `peft==0.21.0` (see Version traps) |
| `tinker` / `tinker-cookbook` | 0.39.2 / 0.7.1 | 2026-11-18 / 2026-11-20 | From tinker 0.38.0 (2026-11-05) the client-creation methods return a future (call `.result()`); tinker-cookbook ≥0.6.0 requires `tinker>=0.38.0`; tinker-cookbook 0.7.0 (2026-11-17) changed what `hyperparam_utils.get_lr()` returns; tinker 0.36.0 (2026-10-25) removed `RestClient.get_checkpoint_archive_url_from_tinker_path` (use the cookbook's `tinker_cookbook.weights.download`); cookbook pins `verifiers>=0.1.9,<0.1.10` |
| `skyrl` | 0.5.0 | 2026-11-17 | Repo is now `skyrl-project/SkyRL`; pins `tinker>=0.25.0,<0.28.0` (the current cookbook needs `tinker>=0.38.0`), `vllm==0.33.0`, `torch==2.14.0`, `peft==0.21.0`; new training defaults. Replaces the legacy `skyrl-train` package (last 0.3.1, 2026-01-02) |
| `verifiers` | 0.4.1 (only `0.4.2.devN` pre-releases since) | 2026-11-03 | 0.4.0 removed the v0 API and changed reward-moving defaults; 0.4.1 removes `vf-eval` / `vf-replay` / `vf-init`, removes `UnscoredError` (`nan` no longer means "unscored") and changes the default decision judge |
| `unsloth` | 2026.11.10 | 2026-11-23 | Date-versioned (several releases a week); patches TRL / transformers internals; the base install requires `trl<=1.15.0`, `transformers<=5.17.0` and `torch<2.15.0`, so a default Unsloth environment cannot get TRL 1.16–1.18 fixes (the `huggingfacenotorch` and `colab-no-deps` extras allow `trl<=1.18.2`) |
| `axolotl` | 0.21.1 | 2026-10-27 | 0.21.0 and 0.21.1 fix silent LoRA / QLoRA / expert-parallel / RL bugs (empty adapters under FSDP2 activation checkpointing; LoRA GRPO merged-sync drift of frozen base weights); pins `trl==1.14.1`, `transformers==5.20.1`, `peft==0.21.2`; requires `vllm>=0.30.0` and torch < 2.15.0; Python ≥3.12. No release since (checked 2026-11-23), so it has none of the TRL 1.16–1.18 or PEFT 0.22.0 fixes |
| `openenv` | 0.14.0 | 2026-11-19 | **Security advisories (2026-11-20) list every release up to 0.13.0 as affected, and the 0.14.0 wheel still lacks the `git_env` and Harbor fixes** (unauthenticated env servers can leak `HF_TOKEN` / API keys; see RL environment libraries); 0.12.0–0.14.0 fix verifiers that passed without work being done; GitHub repo is now `openenv/OpenEnv`; 0.10.0 / 0.11.0 fixed several environments that ignored `reset(seed=...)`; 0.9.0 removed `opencode_env` and `pi_env`; the old name `openenv-core` stops at 0.3.0 (2026-05-11) |
| `openpipe-art` | 0.5.24 | 2026-11-04 | 0.5.24 stops a KL reference LoRA leaking into saved checkpoints (Unsloth backend); 0.5.21 changed the GRPO update, so numbers from ≤0.5.20 may differ; Python ≥3.12 |
| prime-rl (GitHub only, not on PyPI) | v0.11.0 | 2026-11-22 | Removes the `ppo` and `cispo` losses; fixes a race that dropped up to ~45% of a step's micro-batches on multi-node context-parallel RL; launch fails without a Prime API key unless the monitor is disabled. v0.10.0 (2026-10-13) made IPO (INTELLECT Policy Optimization) the default loss |
| `agentlightning` | 1.0.3 | 2026-11-03 | Fixes rewards cast to bfloat16 before GRPO advantages (zero advantages for near-equal rewards) in ≤1.0.2 |
| `verl` / `openrlhf` | 0.9.1 / 0.11.2 | 2026-09-20 / 2026-09-14 | See their sections below |

The `project_templates/rl_small/configs/metadata.example.json` file shows one way to record the trainer, vLLM, torch, CUDA and NVIDIA driver versions next to each run.

## Hosted training APIs

### Tinker

Aliases: `tinker` (the Thinking Machines fine-tuning API; PyPI `tinker` 0.39.2, 2026-11-18), "Mira Murati's lab's training API", `tinker-cookbook` (the recipe repo; PyPI `tinker-cookbook` 0.7.1, 2026-11-20). Released October 2025 in private beta; widely adopted for safety RL research through 2026. The cookbook README still says "after our private beta is over" and sign-up is via `auth.thinkingmachines.ai`, with an API key exported as `TINKER_API_KEY`.

**What it is.** A managed API for distributed fine-tuning and RL on open-weight models (as of 2026-10: Qwen3.5 / 3.6 / 3.8, gpt-oss, Nemotron-3, Kimi-K2.6, GLM-5.3, DeepSeek, and Thinking Machines' own **Inkling** family — see "Models and pricing" below; **the Llama models and the big Qwen3 MoEs were retired in June 2026**). You write a small Python loop on a CPU machine; Tinker runs the GPU compute. Uses **LoRA** for efficient training. Lets you keep full control of data and algorithm without owning H100 clusters.

**Core concepts:**

- **`ServiceClient`** — the entry point. Its `base_url` argument defaults to the `TINKER_BASE_URL` environment variable and then to the production API (tinker SDK source), which is what lets the same script target a local SkyRL server (below).
- **`TrainingClient`** — manages weights and optimizer state; you call `forward_backward(...)` and `optim_step(...)`.
- **`SamplingClient`** — runs inference (rollouts) with the current weights. In the cookbook's minimal loop you call `training_client.save_weights_and_get_sampling_client()` to get a sampler for the current weights, sample, then update.
- **Datums** — training data points. Each datum specifies tokens, loss mask, advantages (for RL), etc.
- **Loss functions** — `cross_entropy` (SFT/distillation), `importance_sampling` (the basic on-policy RL loss), `ppo` (PPO clipping), `cispo` (clipped IS — MiniMax's CISPO loss, from the MiniMax-M1 paper arXiv:2506.13585), `dro` (Direct Reward Optimization); the docs index (2026-10-14) also lists `gspo` and custom losses.
- **Workflow** — training loop = sample → grade → compute advantages → train. Tinker handles the GPU scheduling.

**Models and pricing (Tinker "Models & Pricing" page, checked 2026-10-09).** Tinker IDs include `thinkingmachines/Inkling` (975B total / 41B active MoE, text + image + audio) and `thinkingmachines/Inkling-Small` (276B / 12B), `moonshotai/Kimi-K2.6`, `zai-org/GLM-5.3:peft:262144` (listed only in a 256K-context variant), `Qwen/Qwen3.8-27B`, `Qwen/Qwen3.6-35B-A3B`, `Qwen/Qwen3.5-397B-A17B`, `Qwen/Qwen3.5-9B` (plus `-Base` and `4B` variants), `Qwen/Qwen3-8B`, `openai/gpt-oss-120b` and `gpt-oss-20b`, `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16` (and Nano, Ultra, 3.5-Lightning), `deepseek-ai/DeepSeek-V3.1`. Prices are per million tokens with separate **prefill**, **sample** and **train** rates, an 80% discount on cached prefill tokens, and checkpoint storage at $0.10 per GB-month; for example `Qwen/Qwen3-8B` was listed at $0.195 prefill / $0.60 sample / $0.44 train, and the Inkling, Nemotron-3-Super/Ultra and Nemotron-3.5-Lightning entries carried a "limited-time 50% discount". Extended-context variants (ID suffix `:peft:262144`) cost more for **training only**; prefill and sampling prices are unchanged. Forward-only passes invoked by a training client are billed at the train price. **Changes seen on the page on 2026-11-23** (raw markdown; "38 models shown"): new IDs `thinkingmachines/Inkling-2-Mini` (26B total / 5.4B active MoE; $0.15 prefill, $0.015 cached, $0.50 sample, $0.75 train per million tokens) and `thinkingmachines/Inkling-2-Small` (594B / 17B; $0.30 / $0.03 cached / $1.00 / $1.50), each also in a `:peft:262144` variant at twice the train price; `moonshotai/Kimi-K3.1-Pro:peft:262144` (2.8T total / 104B active, 256K only; $6.00 prefill, $1.20 cached, $25.00 sample, $32.00 train) — now the largest model listed; and `nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16`. The "Limited-time 50% discount" label now appears only on Nemotron rows, so budgets written against a discounted Inkling price are out of date; cached prefill is 90% off on the Inkling 2 rows rather than 80%. Re-read the page before budgeting. **Retirements:** on 2026-06-12 Tinker retired `Llama-3.3-70B-Instruct`, `Llama-3.1-8B-Instruct`, base `Llama-3.1-8B` and `Llama-3.1-70B`, base `Llama-3.2-1B/3B`, `Qwen3-235B-A22B-Instruct-2507`, `Qwen3-VL-235B-A22B-Instruct`, `Qwen3-32B`, `Qwen3-30B-A3B*`, `Qwen3-VL-30B-A3B-Instruct`, `Qwen3-8B-Base`, `Qwen3-4B-Instruct-2507` (the model SkyRL's local quickstart uses, which still works on a local server), `Qwen3.5-27B/35B-A3B`, `DeepSeek-V3.1-Base` and `Kimi-K2-Thinking`; `Kimi-K2.5` followed on 2026-07-12, and the "Model deprecations" page gives **2026-10-23** as the retirement date of `Qwen3.6-27B` (replacement `Qwen3.8-27B`), `DeepSeek-V3.1` (replacement `DeepSeek-V4.1-Flash-1017`) and `Nemotron-3-Nano-30B-A3B` (replacement `Nemotron-3.5-Lightning-30B-A3B`) (page re-read 2026-11-04). The docs promise advance notice by email and in the docs but state no fixed notice period and say nothing about what happens to existing checkpoints of a retired model.

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

- **LoRA-only.** Tinker uses LoRA. For most safety research that's fine; for full-parameter behavioral changes, you may hit ceilings. Use `get_lr(model_name)` from the cookbook's `hyperparam_utils` as a starting learning rate (the minimal `rl_loop.py` uses 4e-5 with LoRA rank 32) — and log the number it returns, because it changed in tinker-cookbook 0.7.0 (next pitfall).
- **`get_lr()` returns different learning rates from tinker-cookbook 0.7.0 (2026-11-17).** Read from the PyPI wheels (no release note describes it): in 0.5.9 `get_lr(model_name, is_lora=True)` used a hidden-size formula; from 0.7.0 it returns `reference_lr × multiplier` from a new `lr_multipliers.json` table (`"reference_lr": 0.00075`; e.g. `Qwen/Qwen3-8B` 1.0, `Qwen/Qwen3.5-9B` 0.55; the file is absent from the 0.6.1 wheel), which its docstring calls "an AdamW LoRA SFT sweep starting point, not a tuned optimum"; `get_lr(..., is_lora=False)` raises `ConfigurationError("Full fine-tuning learning rates are not calibrated")`; a new `transfer_lr(lr, from_model, to_model)` moves a tuned rate between models. A script that calls `get_lr(model_name)` therefore trains at a different rate after a dependency upgrade with no code change: record the cookbook version and the resolved learning rate in run metadata, and don't describe runs on either side of 0.7.0 as "same hyperparameters".
- **tinker ≥0.38.0: client-creation methods return a future.** Read from the PyPI wheels of tinker 0.37.0, 0.38.0, 0.39.0 and 0.39.2 (the SDK has no changelog; the wheels were read, not executed): `ServiceClient.create_lora_training_client(...)` is annotated `-> TrainingClient` in 0.37.0 and `-> BackcompatTrainingClientFuture` in 0.38.0, 0.39.0 and 0.39.2. The wrapper still forwards attribute access, with a warning that this is "deprecated and will stop working in a future tinker SDK version" — call `.result()` (or `await` it) to get the client. `TrainingClient.load_state*()` "is deprecated and will NOT be supported in" future SDK versions; resume with `ServiceClient.create_training_client_from_state()` or `create_training_client_from_state_with_optimizer()`. tinker-cookbook ≥0.6.0 requires `tinker>=0.38.0`.
- **Synchronous sample-train cycle.** You need to checkpoint weights and reload them in the sampling client between RL steps. The cookbook's GRPO loop shows the pattern; rolling your own can be subtle.
- **API throughput, not your throughput.** Rate limits on the API affect rollout throughput. Plan batch size accordingly.
- **Evaluation loop overhead.** Run a held-out eval every N steps, not every step — eval rollouts cost as much as training rollouts.
- **Cost.** Usage is billed per million tokens (prefill / sample / train; forward-only calls from a training client are billed at the train rate). Track usage when iterating; long RL runs add up fast, and extended-context (256K) training costs more than standard-context training.
- **Check what you can still train before a retirement date.** tinker 0.34.0 (2026-10-17) adds a `tinker model list` CLI command ("List the models this organization can train or sample") — run it before any scheduled retirement — and `RestClient.copy_weights()`, which copies a checkpoint into another project without duplicating storage (the copy belongs to a new training run "that cannot be trained on").
- **Pinned to a retired base model.** A script or paper replication that hard-codes `meta-llama/Llama-3.2-1B` (still the example in the cookbook README's primitives snippet) or any other retired ID can no longer train or sample it. The Tinker docs advise not depending on any single model and testing replacements before a retirement date; switch to the recommended replacement listed on the "Model deprecations" page (the exact error text a retired ID produces is unverified).
- **Checkpoint expiry.** The cookbook's `rl_loop.py` saves intermediate checkpoints with `ttl_seconds=604800` (7 days) and the final checkpoint with `ttl_seconds=None`; download or re-save anything you need to keep.
- **Tinker checkpoint download: `get_checkpoint_archive_url_from_tinker_path` is gone in tinker ≥0.36.0.** `RestClient.get_checkpoint_archive_url_from_tinker_path` (and `get_checkpoint_archive_url`) exist in tinker 0.35.0 and are absent from the 0.36.0 (2026-10-25) and 0.37.0 (2026-11-02) packages, so an export script calling them fails with `AttributeError: 'RestClient' object has no attribute 'get_checkpoint_archive_url_from_tinker_path'`. No release note announces the removal. The remaining path is `TrainingClient.save_weights_external(...)` plus `RestClient.get_external_weights_urls(tinker_path)` ("Get signed download URLs, one per file, for an external weights checkpoint"); the cookbook wraps it as `from tinker_cookbook.weights import download; download(tinker_path=..., output_dir=...)` (present in tinker-cookbook 0.5.9). The billing / audit-log methods on `RestClient` are deprecated in favour of a new `AdminClient` (e.g. `AdminClient.get_billing_usage()`).
- **Trainer–sampler numerics drift.** The cookbook ships an `rl_numerics_check` recipe (a synthetic many-turn task with 60K+ token episodes) specifically for checking that the trainer's log-probabilities match the sampler's during RL; run it before long multi-turn runs if your importance-sampling ratios look off.
- **`importance_sampling` ≠ PPO.** The basic on-policy IS loss is *not* clipped; off-policyness (large KL between sampling and current weights) makes it unstable. Use `ppo` or `cispo` if you do many gradient steps per rollout batch.

```python
# Sketch of the cookbook's minimal RL loop (tinker_cookbook/recipes/rl_loop.py), simplified:
service_client = tinker.ServiceClient()          # base_url=None -> TINKER_BASE_URL, else hosted Tinker
training_client = service_client.create_lora_training_client(base_model="Qwen/Qwen3.5-9B-Base", rank=32).result()  # tinker >=0.38.0 returns a future; drop .result() on <=0.37.0
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

**Pitfall: the cookbook pins an old `verifiers`.** The cookbook's `pyproject.toml` extra is `verifiers = ["verifiers>=0.1.9,<0.1.10"]` (still the pin in tinker-cookbook 0.7.1, PyPI `requires_dist`, 2026-11-23), while `verifiers` 0.4.0 (2026-10-12) removed the legacy v0 stack ("`verifiers.legacy` and its historical top-level aliases are no longer available. Use `import verifiers.v1 as vf`"). An Environments Hub environment written for the v1 API is therefore not what the `verifiers_rl` recipe is built against. A low-friction setup is one virtualenv with `uv pip install "tinker-cookbook[verifiers]"` (verifiers 0.1.9) for Tinker and a separate one for prime-rl / verifiers 0.4. The recipe README also warns that the Qwen3 chat templates strip `<think>` sections automatically, which reward functions can silently penalise; fix it in the renderer, the chat template or the environment.

**When to use it:** Always start by adapting a cookbook recipe rather than writing from scratch. The cookbook idioms transfer to other RL libraries. **When not to:** you need a loss the Tinker API does not expose, or a training stack you control end to end (use TRL, verl or prime-rl).

### SkyRL: run Tinker Cookbook scripts on your own GPUs

Aliases: **SkyRL**, `skyrl-project/SkyRL` on GitHub (Apache-2.0; `NovaSky-AI/SkyRL` redirects there and SkyRL's own docs still give the old name in their clone line), PyPI `skyrl` 0.5.0 (2026-11-17, Python 3.12–3.14; the legacy `skyrl-train` package stops at 0.3.1, 2026-01-02), "SkyRL Tinker backend", `skyrl.tinker.api`, Berkeley NovaSky.

**What it is.** A full RL library whose Tinker integration starts a local FastAPI server that speaks the Tinker API on top of SkyRL's FSDP or Megatron backend. Per its quickstart: "In general, **zero** code changes are required to execute [tinker-cookbook] scripts on SkyRL. Simply update the `base_url` to point to your local Tinker server." Develop on hosted Tinker and move to your own box, or the reverse, without rewriting the loop. **Full-parameter fine-tuning** works by passing `lora_rank=0` (the cookbook doc suggests about a 10× lower learning rate when switching from LoRA, citing Thinking Machines' guide), which hosted Tinker does not allow.

```bash
# From SkyRL's docs/content/docs/tinker/quickstart.mdx and cookbook.mdx (prerequisite: CUDA 13.0, NVIDIA driver r580 or newer)
git clone https://github.com/skyrl-project/SkyRL.git && cd SkyRL
uv venv --python 3.12 && uv sync --extra tinker --extra fsdp
uv run --extra tinker --extra fsdp -m skyrl.tinker.api \
    --base-model "Qwen/Qwen3-4B-Instruct-2507" --backend fsdp      # ready at "Uvicorn running on http://0.0.0.0:8000"

# second terminal, inside a tinker-cookbook checkout:
TINKER_API_KEY=tml-dummy uv run --with tinker --with datasets --with torch \
    python -m tinker_cookbook.recipes.rl_loop \
    base_url=http://localhost:8000 model_name="Qwen/Qwen3-4B-Instruct-2507"
```

Server options worth knowing: `--checkpoints-base` (default `/tmp/skyrl_checkpoints`, so move it to a persistent disk), `--port` (8000), `--backend fsdp|megatron`.

**Version asterisk on "zero code changes" (SkyRL 0.5.0, 2026-11-17).** SkyRL's `tinker` extra pins `tinker>=0.25.0,<0.28.0`, and its compatibility note says "Verified against 0.25.0, 0.27.0 and 0.27.2" and "**0.28 is not supported yet**: it renames the proto `TopkPromptLogprobs` message to `TopkLogprobs` (`prompt_length` -> `length`), which breaks `serialize_sample_output` for `topk_prompt_logprobs > 0`, and adds `save_weights_external`". But tinker-cookbook ≥0.6.0 requires `tinker>=0.38.0`, and the quickstart's `uv run --with tinker …` inside a fresh cookbook checkout resolves the newest client. Not verified: whether a tinker 0.39.x client actually fails against a SkyRL 0.5.0 server for `rl_loop` / `sl_loop` (no run was made; the documented break is for `topk_prompt_logprobs > 0`). If a local run misbehaves, pin the client to `tinker>=0.25,<0.28` with a matching older cookbook (0.5.x), and record both versions. Also new in 0.5.0 (release notes): "Score centering is enabled for compatible loss functions", a DPPO policy-loss default and a fused LM head — so SkyRL-native training curves from 0.4.0 and 0.5.0 are different recipes — plus an on-policy distillation trainer; the release pins `vllm==0.33.0` and `torch==2.14.0`.

**Limitations (SkyRL `limitations.mdx` at tag `skyrl-v0.5.0`; first three unchanged since 2026-10-14):** "KL penalty (`kl_penalty_coef > 0`) is not yet supported"; `sample()` does not return prompt logprobs (it logs a warning, no error); "Only `cross_entropy` and `importance_sampling` are currently wired through the Tinker data conversion path"; multi-tenant LoRA is Megatron-only, and full-parameter training is single-tenant. Two more at 0.5.0: "LoRA is not applied to the unembedding layer, so `train_unembed` is ignored" — and "The Tinker SDK **defaults `train_unembed` to `True`**", so the same script trains a differently shaped adapter on hosted Tinker and on SkyRL (the server logs a warning and reports `train_unembed=False`); and "Routed MoE experts are not covered on FSDP" (Megatron adapts them). The server loads one `--base-model`, and every example in the docs passes that same name as the recipe's `model_name`.

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

**GRPO defaults to report in a methods section** (from `trl/trainer/grpo_config.py`, v1.15.0; unchanged in v1.16.0, v1.17.1 and v1.18.2 — the defaults listed here were compared at the v1.17.1 and v1.18.2 tags on 2026-11-23. The one default that changed in 1.18 is set in `__post_init__`: an unset `epsilon_high` becomes `5.0` when `loss_type="cispo"`. In v1.17.1 and v1.18.2 `top_p=1.0`, `top_k=0`, `min_p=None` and `vllm_importance_sampling_correction=True` are also the defaults): `beta=0.0` (no KL term, so no reference model is loaded), `loss_type="dapo"` (token-level normalisation over the global accumulated batch; `"dr_grpo"` and `"grpo"` are options, and the docstring calls `"grpo"` "Not recommended due to length bias"), `scale_rewards="group"` (divides by the per-group standard deviation; the docstring notes Dr. GRPO recommends no scaling), `learning_rate=1e-6`, `use_vllm=False`. A paper that says "we used GRPO in TRL" without these is ambiguous.

**Pitfalls:**

- **TRL 1.18.0 (2026-11-13) fixed six silent training-correctness bugs — re-check runs from ≤1.17.1.** The release notes: "Several of these change what a run trains on. The first one needs action on models you already saved." First affected versions are stated only for the first item; for the rest the notes say only that 1.18.0 fixes them.
    - **Saved MoE checkpoints carry `output_router_logits=True`.** "MoE models saved by `SFTTrainer` v1.7.0 to v1.17.1 compute router logits at every forward, inference included." The fix does not clean existing checkpoints ("a model saved by one of these versions keeps the flag even after another fine-tune"). For any SFT'd MoE model or organism you saved or uploaded with those versions: load it, set `model.config.output_router_logits = False` (`model.config.text_config.output_router_logits` for a VLM), and `save_pretrained` again (PR #8103).
    - **CISPO (clipped importance-sampling loss) with default settings.** "CISPO gradients were 5x too small by default": with `loss_type="cispo"` an unset `epsilon_high` fell back to `epsilon=0.2`, so every on-policy weight was clipped to 0.2; it now defaults to `5.0` (PR #7917: `grad_norm` 0.0539 → 0.2693 on the repro). A CISPO run on ≤1.17.1 without an explicit `epsilon_high` trained with gradients about one fifth of the intended size.
    - **`assistant_only_loss=True` trained tokens the model never generates.** "Several training templates put the turn opener or the pre-filled thinking block inside `{% generation %}`, so SFT trained tokens the model never generates. The rendered text doesn't change, only the mask": Qwen3, GLM-4-MoE, DeepSeek-R1/V3 and R1-Distill, Nemotron 3, gpt-oss, Muse Glimmer, and the Qwen3.6 / Qwen3.8 template revisions shipped since 2026-11-07. "The DeepSeek-R1/V3 training template also dropped the reasoning of assistant turns from the target". Because the rendered text is identical, diffing prompts cannot catch this; inspect the mask (which token positions carry loss) for one example per model family. See [`training-on-trajectories.md`](training-on-trajectories.md#tooling-that-captures-token-exact-trajectories-2026).
    - **AsyncGRPO / AsyncDistillation sampled with stale prefix-cache KV.** Each weight sync paused vLLM without clearing its prefix cache, so a prefix shared by many prompts (system prompt, few-shot examples, tool schemas) "kept the KV of the weights that first served it for the whole run". Rollout requests are now salted by model version (PR #8300: on a Qwen3.5-35B-A3B LoRA run with a ~2.4k-token shared prefix, mean train reward over steps 11–20 went from 0.726 to 0.781). If you hand-roll async RL against vLLM, set `cache_salt` per policy version yourself.
    - **GKD and VESPO.** "GKD divided its loss by the length of answers it threw away"; with `loss_type="vespo"` and `vllm_importance_sampling_mode="token_mask"`, one rejected token collapsed the whole sequence weight to about 0.
    - **GRPO configurations that "trained nothing without an error" now raise:** `repetition_penalty` together with the vLLM importance-sampling correction (vLLM applies the penalty to the log-probs it returns, "so the ratio dropped to ~1e-28 and the gradient to 0"; set `vllm_importance_sampling_correction=False` if you need the penalty); structured outputs with the correction now need `top_k > 0`; PEFT training separate copies of tied embeddings with vLLM ("vLLM >= 0.29 raised during the weight sync, and older versions silently generated from weights the trainer didn't have" — older vLLM versions, that is).
- **`AsyncGRPOTrainer` is a stable trainer from 1.18.0, with breaking renames.** `from trl import AsyncGRPOConfig, AsyncGRPOTrainer`; the old `trl.experimental.async_grpo` package import still works with a `FutureWarning` until v2.0.0, but its submodules are gone ("imports from `async_rollout_worker`, `packing`, `vllm_client` or `weight_transfer` in that package, no longer work"). Constructor arguments `weight_transfer=` and `rollout_worker=` are removed (subclass `AsyncRolloutLoop` and set `loop_cls`); the OpenEnv / Harbor harness stays experimental as `HarnessAsyncGRPOTrainer` in `trl.experimental.async_grpo.openenv_harness`. Config: `max_inflight_tasks` → `max_concurrent_rollouts` (fixed, default 512); `request_timeout` and `weight_sync_timeout` → `vllm_server_timeout` (default 1800 s, was 240 s); `repetition_penalty` removed. Metrics were renamed (`ratio` → `sampling/importance_sampling_ratio/{mean,min,max}`, `reward_std` → `reward_group_std`, `kl` removed), so W&B panels and analysis scripts keyed on 1.17 names come up empty with no error. With OpenEnv / Harbor, "the environment server's `MAX_CONCURRENT_ENVS` must be at least `max_concurrent_rollouts + 1`".
- **PPO trainer is fiddly.** Many sharp edges around reference-model handling, KL coefficient, generation kwargs. The DPO trainer is much smoother.
- **Memory: PPO loads up to 4 model copies** (policy, ref, reward, value). For 7B+ on a single 80GB GPU you need LoRA + gradient checkpointing.
- **`accelerate config` mismatch with TRL** is a common source of OOM and `RuntimeError: Expected all tensors to be on the same device`. Use TRL's example accelerate configs as starting point.
- **Long context + RL = slow.** Generation length dominates RL training time. Cap completion length aggressively while iterating.
- **TRL GRPO with vLLM and `top_p` / `top_k` / `min_p`: importance-sampling ratio collapsed toward 0 before 1.17.0, and stays biased in server mode unless TRL ≥ 1.18.0 runs against a vLLM server started with `--return-sampling-mask`.** vLLM normalises its returned log-probabilities over the tokens left after `top_k` / `top_p` / `min_p` filtering, while the trainer normalised over the whole vocabulary, so with the default `vllm_importance_sampling_correction=True` "Every sampled token's log-ratio was off by the log of the probability mass the filter kept, so the vLLM importance sampling ratio was biased towards 0 (around 1e-4 instead of 1 with `top_p=0.9`)" (v1.17.0 notes). PR #7866: on `Qwen/Qwen2.5-0.5B-Instruct`, "`top_p=0.9`, `top_k=50` or `min_p=0.05` cut the gradient norm by up to 10 orders of magnitude, at completions of only 100 to 330 tokens". Searchable symptoms: grad norm near zero, flat reward, training that stalls with no error under filtered sampling (issue #7865). **The 1.17.0 fix covers only `vllm_mode="colocate"` with vLLM ≥ 0.28** (the PR: "Server mode will follow in a separate PR"); in `vllm_mode="server"` (and with vLLM < 0.28) TRL 1.17.1 keeps the full-vocabulary normalisation and only warns: `With top_k/top_p/min_p, the log-probabilities are normalized over the whole vocabulary and the importance ratio is biased.` **Server mode is fixed in TRL 1.18.0 (2026-11-13), but only if the vLLM server (≥ 0.28) is started with `--return-sampling-mask`** (PR #8235; issue #7865 closed 2026-11-13): the server then returns each sampled token's candidate set and GRPO renormalises over it ("With Qwen2.5-0.5B-Instruct, `top_k=10` and a vLLM 0.32 server, the ratio stays between 0.85 and 1.27 for structured outputs and `top_p=0.9`"). Catch: "`trl vllm-serve` doesn't add the flag by default, since the server then rejects every request with `top_k=0` or `temperature=0`" — so a 1.18 server started the usual way is still biased and still warns. At the v1.18.2 tag (`trl/trainer/grpo_trainer.py`) the warning is the same first sentence followed by "Normalizing them over the candidate set a token was sampled from takes vLLM >= 0.28 and, in server mode, a server started with `--return-sampling-mask` (and `--enable-scale-out` from vLLM 0.30)." — so from vLLM 0.30 the server needs `--enable-scale-out` as well as `--return-sampling-mask`. 1.17.0 also makes `GRPOConfig` raise when `top_p < 1.0` or `min_p > 0.0` is set without `top_k > 0` while the correction is on. Defaults (`top_p=1.0`, `top_k=0`) are unaffected. In server mode on TRL ≤1.17.1, or on 1.18.x without `--return-sampling-mask`, sample with `top_p=1`, `top_k=0`, no `min_p`, or set `vllm_importance_sampling_correction=False` knowingly; re-check any earlier GRPO-with-vLLM run that used filtered sampling. The general mechanism (sampler truncation the learner does not see) is in [`rl-training.md`](rl-training.md).
- **AsyncGRPO's default objective changed in 1.17.0.** "AsyncGRPO runs now train with a different objective by default, and tokens whose ratio to the sampler falls outside `[0.5, 5.0]` are dropped. Set `score_centering=False` to keep the clipped objective." (score centering with masked importance sampling: `score_centering=True`, `importance_sampling_min=0.5`, `importance_sampling_max=5.0`). The motivation in the notes: "With an FP8 sampler and a bf16 trainer, the clipped objective collapses: reward goes from 0.60 to 0.34 (FP8 weights) or 0.10 (FP8 weights + KV cache) by step 300, against 0.71 with a bf16 sampler"; the notes put the cost at 15–20% of generation throughput. AsyncGRPO numbers from before and after 1.17.0 are different objectives — record the version.
- **AsyncGRPO sequence packing was silently wrong on Gated DeltaNet hybrids before 1.16.** 1.17.0 notes: tree packing now supports Qwen3.5, Qwen3.6, Qwen3-Next and OLMo-Hybrid; "Since v1.16 the trainer refused them at init; before it, sequence packing accepted them but was silently wrong on them." Re-run packed AsyncGRPO results on those models from TRL < 1.16.
- **Also changed in 1.17.0:** the experimental TPO trainer was removed; `peft>=0.17.0` is required; a warning when LoRA would skip MoE dense / shared-expert layers on PEFT 0.19–0.21.2 (see Version traps).
- **Breaking changes between minor versions.** TRL is at v1.x with a release every one to two weeks (PyPI `trl` 1.18.2 on 2026-11-19). Pin the version in your run metadata; e.g. v1.14.0 removed the `trl.losses` module, so `from trl.losses import FusedLinearDPOLoss` (or `FusedLinearKTOLoss`, `FusedLinearGRPOLoss`, `FusedLinearJSDLoss`) raises an `ImportError` on newer versions, and `trl==1.12.0` on PyPI is a bit-identical accidental duplicate of 1.11.0.
- **vLLM outside the supported range only warns.** `trl/import_utils.py` checks the installed vLLM and, at the v1.18.2 tag, emits `TRL currently supports vLLM versions from 0.23.0 to 0.33.x. You have version … installed.` (v1.17.x said `0.22.0 to 0.32.x`, v1.16.0 `0.22.0 to 0.31.0`, v1.15.0 `0.21.0 to 0.31.0`) as a **warning**, not an error, so a run can start and fail later inside generation. vLLM 0.34.0 (2026-11-16) is newer than any TRL release supports (the `vllm` extra of 1.18.2 is `vllm<0.34.0,>=0.23.0`), so mixing an unpinned vLLM with TRL warns. Pin `vllm` inside that range alongside `trl`.
- **Silent wrong training with `torch_compile=True` before TRL 1.16.0.** The 1.16.0 notes: "`torch_compile=True` trained with `loss=0.0` and `grad_norm=nan` at every step" in the Triton loss kernels on torch < 2.11 (Inductor miscompiled them). Searchable symptom: `loss=0.0` and `grad_norm=nan` from step 1 with `torch_compile=True`. Re-run any such run on 1.16.0 or with torch ≥ 2.11.
- **FSDP2 + `vllm_mode="colocate"` crashed at step 1 on tied-embedding models** (e.g. small Qwen2 / Qwen2.5) with vLLM ≥ 0.29, because the weight sync iterated `state_dict()` and sent tied weights under both names; fixed in 1.16.0 (PR #7647).
- **Also changed in 1.16.0:** the experimental SSD trainer was removed; `RewardTrainer` refuses `nn.DataParallel`; `accelerate>=1.10.1` is required.
- **Process reward model (PRM) training was removed.** TRL removed `trl.experimental.prm`; axolotl v0.20.0's notes say PRM training now needs `trl<=1.13.0`.
- **Telemetry.** TRL's usage-stats doc: "A single ping is sent each time a trainer is instantiated" (TRL version, trainer class, known architecture, PEFT on/off, GPU model; no dataset names or paths). Opt out with `export HF_HUB_DISABLE_TELEMETRY=1` (or `HF_HUB_OFFLINE=1`); it is not sent when `CI` is set. Relevant on boxes where outbound traffic is restricted or logged.

**Recent releases (v1.10 → v1.18, 2026-08 → 2026-11; from the GitHub release notes):**

- **v1.18.0 (2026-11-13; v1.18.1 on 2026-11-17 and v1.18.2 on 2026-11-19 are small fixes — 1.18.1 grades accuracy rewards in a separate process "so a pathological answer can't hang training")** — the six correctness fixes and the stable `AsyncGRPOTrainer` (both in Pitfalls above); GRPO server-mode renormalisation with `--return-sampling-mask`; vLLM range `>=0.23.0,<0.34.0`; `loss_type="udpo"` in `DPOTrainer` for noisy preference labels; MXFP4 and FP8 checkpoints load dequantized, so `openai/gpt-oss-20b` trains by name; LoRA adapter-only weight sync for AsyncGRPO when vLLM runs with `--enable-lora`; `trl <cmd>` launches with torchrun (`accelerate launch` deprecated until v2.0.0).
- **v1.17.0 (2026-10-29; v1.17.1 on 2026-10-30 contains a single LFM2.5 tool-call parsing fix)** — fixes the GRPO + vLLM filtered-sampling importance-ratio bias in colocate mode, makes score centering the AsyncGRPO default, adds tree-packing support for Gated DeltaNet hybrids, adds vLLM 0.32.x support, removes the experimental TPO trainer (all in Pitfalls above).
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

TRL's memory guide warns: "With vLLM sleep mode (`vllm_enable_sleep_mode=True`), vLLM only reads `PYTORCH_CUDA_ALLOC_CONF` to work around this setting, so don't set only `PYTORCH_ALLOC_CONF`." **When not to colocate:** you have a spare GPU for rollouts. Server mode (`vllm_mode="server"`, launched with `trl vllm-serve`) avoids memory contention, and in that mode "the **vLLM server** and the **trainer** must run on **separate CUDA devices** to prevent conflicts." Caveat for TRL GRPO server mode: on TRL ≤1.17.1, and on 1.18.x unless the vLLM server was started with `--return-sampling-mask` (plus `--enable-scale-out` from vLLM 0.30), the importance-sampling ratio is biased whenever `top_p < 1`, `top_k > 0` or `min_p` is set (see the TRL pitfalls), so keep sampling unfiltered there.

### Unsloth (single-GPU QLoRA / LoRA GRPO)

Aliases: **Unsloth**, `unslothai/unsloth` on GitHub (Apache-2.0), PyPI `unsloth` 2026.11.10 (2026-11-23, Python <3.15), "Unsloth Core" (the code library), distinct from "Unsloth Studio" (web UI) and "Unsloth Desktop" (app), which now dominate the README and the GitHub release list (`v0.1.923-beta`-style Studio betas).

**What it is.** A library that patches TRL and transformers for memory-efficient LoRA / QLoRA / full SFT, DPO and GRPO on one GPU, with vLLM generation sharing the trainer's GPU memory (`fast_inference=True`). The RL guide's rule of thumb: "For GRPO's **GPU VRAM requirements for QLoRA 4-bit**, the general rule is the model parameters = the amount of VRAM you will need" (roughly 8 GB for an 8B model, more with longer context), and "LoRA 16-bit will use at minimum 4x more VRAM".

```bash
# Unsloth Core install (README)
uv venv unsloth_env --python 3.13 && source unsloth_env/bin/activate
uv pip install unsloth --torch-backend=auto
```

**Pitfall: Qwen3.5.** The RL guide: "You can also run RL with Unsloth on models that are not supported by vLLM, such as Qwen3.5… Simply set `fast_inference=False` when loading the model" (`FastLanguageModel.from_pretrained(model_name="unsloth/Qwen3.5-4B", fast_inference=False)`). Generation then runs without vLLM and is slower, so budget for it.

**Pitfall: Unsloth pins an older TRL.** `unsloth` 2026.11.10's base PyPI `requires_dist` has `trl<=1.15.0`, `transformers<=5.17.0` and `torch<2.15.0` (unchanged from 2026.11.2), so a default Unsloth environment cannot get TRL 1.16.0's `torch_compile` fix, TRL 1.17.0's GRPO importance-sampling and AsyncGRPO changes or TRL 1.18.0's CISPO and loss-mask fixes (see TRL above); only the `huggingfacenotorch` and `colab-no-deps` extras allow `trl<=1.18.2` (the `colab-new` extra lists no `trl` requirement). Unsloth-side fixes named in its 2026-11 release notes: "A LoRA adapter on `lm_head` now trains in SFT and GRPO instead of getting no gradient" and "Mask GRPO completions cut by the vLLM server's context limit" (first affected versions not stated). Record both versions; don't compare Unsloth GRPO curves with plain-TRL curves as if the trainer were the same.

**When not to use it:** multi-node or asynchronous RL; you need exact control of the loss and advantage code paths (it patches library internals, which makes "which GRPO did I run?" harder to answer); shared research boxes where you only need the library (skip the Studio installers).

### axolotl (YAML-configured fine-tuning)

Aliases: **axolotl**, `axolotl-ai-cloud/axolotl` on GitHub (Apache-2.0), PyPI `axolotl` 0.21.1 (2026-10-27, Python ≥3.12). The training backend of several safety toolkits, including the SDF pipeline `ArcadiaImpact/science-of-midtraining`.

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
- **Version trap: axolotl 0.21.x and vLLM 0.31–0.33 cannot share an environment.** axolotl 0.21.0 and 0.21.1 pin `transformers==5.20.1` (PyPI `requires_dist`, checked 2026-11-04), while vLLM 0.31.0 requires `transformers<5.18.0` and vLLM 0.32.0 `transformers<5.20.0`. Of the vLLM releases axolotl accepts (`>=0.30.0`) up to 0.32.0, only 0.30.0 admits 5.20.1, so `axolotl[vllm]` resolves to vLLM 0.30.0 or fails if you also pin a newer vLLM (symptom: pip `ResolutionImpossible` / uv `No solution found` naming `transformers`). vLLM 0.33.0 admits transformers 5.20.1 but is blocked by a different pin: `uv pip compile` (Python 3.12, linux x86_64, 2026-11-04) reports "Because trackio==0.40.0 depends on pillow<13.0.0 and vllm>=0.33.0 depends on pillow>=13.0.0 … axolotl>=0.21.1 and vllm>=0.33.0 are incompatible." For a newer vLLM, run it as a separate server in its own environment.

**v0.21.1 (2026-10-27): five more training-correctness fixes, three for preference / RL trainers** (release notes; the bugs are present in 0.21.0) — re-check affected runs:

- "**Activation offloading corrupted gradients** (#4142 …): DPO and KTO on the pinned TRL 1.14.1 got wrong gradients or CUDA illegal memory accesses."
- "**LoRA GRPO's merged vLLM sync drifted the frozen base weights** (#4213 …): each merge/unmerge round trip in BF16 changed some entries (1.5% after 200 syncs at lr 1e-5)." The base is now restored exactly. New option `lora_merge_aware: bf16`, and merged-sync runs now log how much of each LoRA update survives the BF16 rounding (`trl.vllm_merge_check_interval`, on by default) — the same rounding problem as the bf16-export result in [`rl-training.md`](rl-training.md).
- "**`lora_fp32_gradients` trained in BF16 for RL trainers under FSDP** (#4215 …)."
- "**CCE's generic patch skipped logit softcapping** (#4182 …): Beam's step-0 eval loss read about 3.4 instead of 0.79." (CCE = Cut Cross-Entropy.)
- "**Fused LoRA GEGLU kernel used exact GELU on tanh-GELU models** like Gemma (#4189 …)."
- Heads-up from the notes: "EP checkpoints saved model-only or sharded can no longer be resumed by older Axolotl versions." axolotl still pins `trl==1.14.1`, so it does not have TRL 1.16/1.17 fixes.

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

**What it is.** Fully asynchronous RL (an FSDP2 trainer, vLLM inference and an orchestrator) with native `verifiers` environments from the Environments Hub, plus SFT, evals, LoRA and Slurm multi-node launch. The README says it is developed and tested on "NVIDIA RTX 3090/4090/5090, A100, H100, H200, and B200". Latest release v0.11.0 (2026-11-22; previous v0.10.0, 2026-10-13).

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
- In v0.10.0 IcePop, PPO and CISPO were opt-in via `[trainer.loss] type = ...` and the old DPPO default loss was removed (rename `ipo_threshold` to `eps`). **v0.11.0 removes PPO and CISPO too**: "`trainer.loss.type = "ppo"` and `"cispo"` are removed" — IPO (default), IcePop and custom losses remain.

**v0.11.0 (2026-11-22) — re-check multi-node results and update configs** (release notes; PR #4489 read):

- **Silent data loss fixed:** "CP peers no longer lose micro batches to a race that released payloads before every rank fetched them (up to ~45% of a step's micro batches were dropped on multi-node RL)" (CP = context parallelism). The PR's symptom is a log line `Dropped N micro batches whose payloads could not be fetched`; grep older multi-node logs for it. Fixed in v0.11.0; first affected version not stated.
- **Staleness handling changed:** `orchestrator.max_off_policy_steps` is renamed `orchestrator.max_staleness` and "now masks stale tokens from the loss instead of cancelling whole episodes"; metrics moved from `off_policy/*` to `staleness/*`.
- **A launch now needs a Prime API key by default:** "A launch fails if there is no Prime API key or the run cannot register" — opt out with `--no-monitors.prime`. On a box where outbound traffic is restricted, or for data that must not leave it, disable the monitor explicitly.
- **Compatibility:** "old LoRA DCP checkpoints cannot be resumed (exported adapters are fine)"; "All components (orchestrator, trainer, inference, env worker pools) must run the same prime-rl version"; env servers became env worker pools (`uv run env-worker-pool`).
- **Reward-hack fix in the grader:** "Verifiers bumps close a grading-sandbox reward hack via crafted artifact archives" — results from environments graded in that sandbox on older versions deserve a second look.

**When not to use it:** a single small GPU for RL — the reverse-text example's commands "were designed to be run on 2 GPUs (one trainer and one inference GPU)" (SFT runs on one, and the LoRA alphabet-sort RL example "runs on a single H100 GPU"); a model architecture outside `src/prime_rl/trainer/models/` ("Other architectures fail at trainer setup"); a project that wants a KL-to-reference regulariser by default.

### OpenPipe ART (RL on your existing agent code)

Aliases: **ART** (Agent Reinforcement Trainer), `OpenPipe/ART` on GitHub (Apache-2.0), PyPI `openpipe-art` 0.5.24 (2026-11-04, Python ≥3.12), RULER (its LLM-judge reward), W&B "Serverless RL" backend.

**What it is.** Your application calls the model through an OpenAI-compatible ART client; each rollout's messages are stored in a `Trajectory` that your code assigns a reward to; an ART server (local GPU, ephemeral cloud GPU, or W&B Training's Serverless RL backend) trains a LoRA with GRPO via Unsloth and vLLM and hot-loads it. Install with `pip install openpipe-art`.

**When not to use it:** throughput or exact token-level control matters — per the README, "Inference is blocked while training executes"; Gemma 3 ("Gemma 3 does not appear to be supported for the time being"); a project where RULER's LLM-judge reward would itself be the object of the reward hacking you are measuring.

**Pitfall: v0.5.21 (2026-10-20) changed the GRPO update.** From the release notes: "Zero-variance GRPO updates are skipped", "policy importance ratios are bounded before exponentiation", "TIS is skipped when original logprobs are unavailable" (TIS = truncated importance sampling), "use population std for native Tinker advantages", and several logprob and gradient paths now use FP32. GRPO curves from ≤0.5.20 and from 0.5.21 are not directly comparable; record the version.

**Pitfall: KL reference adapter leaked into saved checkpoints before v0.5.24 (2026-11-04).** From the release notes: "With a KL penalty, the Unsloth backend left the reference LoRA loaded, so later checkpoints saved in the same process, including other models' checkpoints, contained it." Saving and loading now drop unused adapters, and `load_lora_adapter` raises if the file is missing any LoRA weight. Re-check adapters saved from KL-penalty runs on ≤0.5.23, especially when one process trained several models. 0.5.24 also requires `weave>=0.54.0`; older Weave fails in `weave.init()` with `AttributeError: 'OTLPSpanExporter' object has no attribute '_session'` once `opentelemetry-exporter-otlp-proto-http` 1.45 is installed.

### Agent Lightning (Microsoft) — RL for agents in their own harness

Aliases: `agentlightning` on PyPI (v1.0.3, 2026-11-03), `microsoft/agent-lightning` on GitHub, "Agent Lightning v1.0", arXiv:2608.17528 (He, Zhang, Zhou, Yang, Kang et al., 2026-08-18).

**What it is.** A lightweight (~3,500 lines per the paper) framework for **harnessed agentic RL**, where the agent's deploy-time harness (tools, context management, control flow) owns the environment loop and the trainer only sees sequences of LLM request–response pairs, connected through an LLM-endpoint proxy. The paper reports that RL with 6K training examples raised Qwen3.5-9B on SWE-bench Verified from 41.8% to 56.4%, and lists the hard parts of this setup: retokenisation, sample merging, advantage calculation, loss normalisation and backend scheduling.

**When to use it:** you want to RL-train an agent *as it is actually deployed* (a coding-agent CLI, a search agent) rather than re-implementing its loop in a trainer. **When *not* to use it:** you only need single-turn RLVR (use TRL / the Tinker Cookbook), or you need the trainer to own the loop and token accounting exactly (use verl or TRL's white-box `environment_factory` path).

**Pitfall:** because the harness, not the trainer, builds the prompts, the tokens the model saw at rollout and the tokens the trainer re-tokenises can differ (the paper lists retokenisation as a core difficulty); record token ids at the proxy rather than re-tokenising logged text. v1.0.3 added "opt-in trajectory prefix-mismatch diagnostics to help identify possible retokenization mismatches without changing training tensors" — turn them on before a long run.

**Pitfall: Agent Lightning ≤1.0.2 cast rewards to bfloat16 before GRPO advantages.** PR #640: "The rollout adapter converts final rewards to bfloat16 before advantage estimation. Rewards such as 1.0 and 1.001 then both become 1.0, so GRPO produces zero advantages for the group." PR #662: with float16 advantages, rollout normalisation could build an infinite divisor and return zero advantages ("2,048 rollout tokens and 64 trained rows produce a divisor of 131,072"), and bfloat16 token counts rounded 257 to 256. Fixed in v1.0.3 (2026-11-03), which also adds Score Centering for low-precision RL. Symptom: zero or near-zero advantages and flat reward with rubric or LLM-judge rewards that differ only in small fractions (bfloat16 near 1.0 has a spacing of 2^-7 ≈ 0.008). Re-run such results on ≥1.0.3.

### Don't start new work on torchtune or torchforge

- **torchtune** (`meta-pytorch/torchtune`, BSD-3-Clause; last release v0.6.1, 2025-04-07): the README opens with "⚠️ **Torchtune is no longer actively maintained:** torchtune development wound down in 2025". Older papers and blog recipes still point at torchtune configs; use it only to reproduce such a paper exactly, pinned to v0.6.1.
- **torchforge** (`meta-pytorch/torchforge`, no releases): "⚠️ **Development paused:** Development in Forge has paused. LLM training at PyTorch is being consolidated in torchtitan."
- **Instead:** `pytorch/torchtitan` (v0.4.0, 2026-10-28, aligned with PyTorch 2.15; its RL stack TitanRL moved out of experimental to `torchtitan.rl`, formerly `torchtitan.experiments.rl`, so old imports break) or prime-rl for PyTorch-native training; TRL or axolotl for Hugging Face-native SFT / LoRA.

### Other active RL stacks (not covered in depth)

Active as of 2026-10-14 but either industrial-scale or duplicating TRL / axolotl / Unsloth for safety work: **slime** (`THUDM/slime`, v0.4.0, 2026-10-09; Megatron + SGLang), **AReaL** (`areal-project/AReaL`, v2.1.1, 2026-11-04), **ROLL** (`alibaba/ROLL`, v0.4.0, 2026-09-29), **LlamaFactory** (`hiyouga/LlamaFactory`, v0.9.5, 2026-05-30), **ms-swift** (`modelscope/ms-swift`, v4.6.0, 2026-10-13), **oumi** (`oumi-ai/oumi`, v0.9, 2026-09-16), **tunix** (`google/tunix`, JAX, v0.1.7, 2026-06-11), **rLLM** (`rllm-org/rllm`, v0.3.0-pre, 2026-04-30; the old `agentica-project/rllm` is stale), and **NeMo RL** (`NVIDIA-NeMo/RL`, v0.8.0, 2026-11-06; the PyPI name `nemo-rl` is a 0.0.0 placeholder (re-checked 2026-11-23), so install from the repo or container — it ships the Nemotron-3.5-Lightning RLVR recipe, see [`open-weights-models.md`](../models-and-compute/open-weights-models.md)). v0.8.0's "Notable Fixes" are worth re-checking v0.7.0 runs against: "Fixed GRPO advantage spikes (near −2075) when `use_leave_one_out_baseline` and `normalize_rewards` are both on, which is the default in `grpo_math_1B.yaml`" (PR #4158: a numerical cancellation in the standard deviation when all but one reward in a group are equal); "Fixed token positions filtered out by top-k/top-p still counting in the loss and KL"; "Fixed the Automodel KL reference model moving to the resumed weights on every resume, instead of staying at the base weights" (PR #3722: each resume gave the policy a fresh KL budget; the PR places the bug in the DTensor v2 worker and says "v1 worker is unaffected"); "Fixed async GRPO skipping about 30% of prompts across checkpoint save and restore". v0.8.0 also removes DTensor v1 and renames the DTensor backend to Automodel (`dtensor_cfg` → `automodel_cfg`). The KL-reference bug is generic: after resuming any RL run with a KL-to-reference term, check that the reference weights equal the base model's, not the checkpoint's. `NousResearch/atropos` is archived.

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

**High LoRA rank can collapse GRPO from a cold start — "rank collapse" (2026-11).** Kazakov & Javat, *Structure Over Scale: Rethinking Adaptation for Reinforcement Learning with Verifiable Rewards* (arXiv:2611.27148, 2026-11-20; published in TMLR; code `Shrimpstanot/structure-over-scale`, CC-BY-4.0). Setup: Qwen 3 8B **base** checkpoint, GRPO (Group Relative Policy Optimization) with no SFT warm-up, Dr. GRPO loss normalisation, all-linear LoRA, learning rate 1e-5 with cosine decay, batch size 64, 8 generations, DeepMath-Hard. LoRA rank sweep (seed 42): 79.29% at rank 1 and 4, 78.10% (8), 76.20% (16), 77.30% (32), 73.10% (64), then 4.70% (128) and 2.30% (256). A second seed reproduced the boundary (rank 64 works at batch size 64 and collapses at 128 and 256); larger batches or GRPO groups did not rescue rank 256. DoRA (weight-decomposed LoRA) and QuanTA (a tensor-network adapter) stayed trainable over a wider range and were competitive with full fine-tuning.
- **Does this conflict with LoRA Without Regret? Not with the settings in the table above.** The paper uses the same scaling convention ("For all LoRA ranks, we fix α = 32 and use the standard α/r scaling"), so the collapse is not an artefact of scaling alpha up with rank, and its stable region (rank 1–32) is the range recommended here for RL. Where it differs is on *high* rank: the authors note that Schulman's post reports high-rank LoRA not collapsing in its setup, and attribute the gap to "the joint effects of batch size, update horizon, learning-rate schedule, and optimization protocol rather than to a single universal LoRA rank threshold". They also found a constant learning-rate schedule collapsed at batch size 64 where cosine decay with warm-up did not.
- **Limits:** one model family for the sweep (the other two 8B base models, Llama 3.1 8B and Apertus 8B, had best LoRA and best QuanTA scores under 4% on DeepMath-Hard in this cold-start setting), the learning rate was held fixed across ranks (the authors: "Rank-specific tuning could shift the observed boundaries"), and an SFT-then-RL pipeline was not tested.
- **What to do:** for RL keep LoRA rank ≤ 32; if a run died right after you raised the rank to 128 or more, lower the rank (or try `use_dora=True` in PEFT's `LoraConfig`) before debugging the reward.

**When not to use these settings:** rank-1 for large SFT datasets (beyond LoRA's capacity it underperforms full fine-tuning); raising the batch size to compensate for a small rank (the doc says rank does not fix the batch-size intolerance). A known trap is attention-only `target_modules=["q_proj","k_proj","v_proj","o_proj"]` lists copied from older scripts.

## RL environment libraries: OpenEnv, verifiers, Harbor, OpenReward

| Library | What it is | Use it for | When not |
|---|---|---|---|
| **OpenEnv** (`openenv/OpenEnv` on GitHub since 2026-10, redirected from `huggingface/OpenEnv`, formerly `meta-pytorch/OpenEnv`; BSD-3-Clause; PyPI `openenv` 0.14.0, 2026-11-19 — no PyPI release, 0.14.0 included, has the fixes for the 2026-11-20 security advisories, see the security pitfall below; 0.9.0 removed `opencode_env` and `pi_env`; 0.10.0 and 0.11.0 made `dipg_safety_env`, `wildfire_env`, `kernrl` and `textarena_env` honour `reset(seed=...)`, so episodes from those environments on older versions may not have been reproducible — **not** the stale `openenv-core` 0.3.0) | A `reset()` / `step()` / `state()` API "sync or async, over a WebSocket" to environments that are each a Docker image (local, cloud sandbox or Hugging Face Space); 40+ in the catalog | TRL `GRPOTrainer(environment_factory=...)` white-box tool environments; Harbor-captured traces for loop-owning harnesses; `openenv import` wraps an existing ORS/OpenReward or Verifiers environment | Single-turn RLVR, where the Docker/WebSocket hop is pure overhead; public Spaces holding secrets |
| **verifiers** (`PrimeIntellect-ai/verifiers`, MIT; PyPI `verifiers` 0.4.1, 2026-11-03) + **Environments Hub** / `PrimeIntellect-ai/community-environments` (Apache-2.0) | Prime Intellect's environment, harness and scoring library; since 0.4.1 the only eval CLI is `vf-run` (a minimal in-process runner) — `vf-eval`, `vf-replay` and `vf-init` were removed, and full evaluations moved to prime-rl's `uv run eval` | prime-rl training; the Tinker Cookbook `verifiers_rl` recipe (on verifiers 0.1.9) | Mid-project upgrades (see the pitfall) |
| **Harbor** (`harborframework.com`; TRL integration `trl.experimental.harbor`, `pip install trl[harbor]`) | Decouples a task (instruction + sandbox image + verifier), a harness and a sandbox (`docker`, `e2b`, `daytona`, `gke`…); `HarborSpec` fills TRL's `train_dataset`, `environment_factory` and `reward_funcs` slots | Training on a Harbor task suite, including real coding-agent harnesses with exact-token capture | Needs `vllm` and `transformers>=5.2.0`, Python ≥3.12 |
| **OpenReward / ORS** (Open Reward Standard; TRL `trl.experimental.openreward`, `pip install trl[openreward]`) | An HTTP/SSE protocol for environments' tasks, tools, sessions and rewards; `OpenRewardSpec("Eigent/SETA", num_tasks=64)` | ORS environments from the openreward.ai catalog, self-hosted or on localhost | Single-turn RLVR, where a Python reward function suffices; a single-host self-hosted server also needs the SDK's default two-subdomain (`api.` / `sessions.`) layout overridden |

**Pitfall (security): OpenEnv env servers have no authentication — two advisories published 2026-11-20 cover `openenv` up to 0.13.0.** Both are from the OpenEnv maintainers (GitHub security advisories on `openenv/OpenEnv`).

- **GHSA-67hq-8vmh-85x9 (critical), `git_env`:** "Env servers have no authentication on `/ws`, `/reset` and `/step`, so any client that reaches a `git_env` deployment can" run arbitrary programs on the server, read its credentials (the process inherits `GITEA_PASSWORD`, `HF_TOKEN` and every other environment variable) and delete directories. Affected: `openenv` ≤ 0.13.0 and the old `openenv-core` 0.1.1–0.3.0.
- **GHSA-x2fj-957w-qm9g (high):** an unauthenticated client can make the server send a server-side secret to a host the client picks, or copy server files into a sandbox the client reads. Affected: `openenv` ≥ 0.8.0, ≤ 0.13.0 (`openenv.harbor`), and — wherever deployed from the repository's source before the fix — `repl_env`, `agent_world_model_env`, `jupyter_env`, `browsergym_env`, `openapp_env`, `julia_env`, `kernrl` and `tbench2_env` ("Redeploy them from the patched source"). The advisory notes the optional `OPENENV_GUARD_*` middleware "adds rate limits and IP lists, not auth".
- **Fixed version: none on PyPI as of 2026-11-23.** Neither advisory names a patched version (the field is empty). 0.14.0 (2026-11-19) is outside both stated affected ranges, but it does not contain the fixes: in the 0.14.0 wheel `openenv/core/tools/git_server_client.py` is byte-identical to the file at the `v0.13.0` tag, the `git_env` fix commit (`0c29d02e`, "git_env: keep agent git commands inside the workspace and away from server credentials") is not an ancestor of the `v0.14.0` tag, and `openenv/harbor/environment.py` has no `reads_environment` check (the advisory's fix for Harbor `run_rollout`); both changes are on `main` (version `0.14.1.dev0`). What 0.14.0 does ship is upload-side redaction ("Redact secrets from rollouts before they are uploaded to the Hub", which the advisory says was "released in 0.14.0"). The advisory lists authentication itself — an "Opt-in bearer token for `/ws`, `/reset`, `/step`, `/mcp` and `/web`" — as a follow-up, so no release adds authentication to env servers.
- **What to do:** don't rely on a version bump — 0.14.0 lacks the fixes (previous bullet), so install from `main` or wait for the next release, and redeploy any environment built from source from the patched source; keep `git_env` and the other listed environments unreachable by untrusted clients (a private Space, or no secrets on the server); never put `HF_TOKEN`, a judge API key or any other credential into the environment of an env server that untrusted clients can reach (a public Hugging Face Space is reachable by everyone); rotate any key that sat in such a server. axolotl 0.21.1 still depends on the old package name (`openenv-core>=0.1.0`), whose 0.1.1–0.3.0 releases are in the critical advisory's range.

**Pitfall: OpenEnv 0.12.0–0.14.0 fixed verifiers that paid out without the work being done.** From the release notes (PR titles): "fix: stop awm code verifiers from passing on an untouched database" (0.12.0; PR #1477: code-mode reward in `agent_world_model_env` now requires changed database contents or an answer that changes the verifier outcome); "Keep the qed_math_env answer-mode reference server-side and stop scoring after done in reasoning_gym_env and finqa_env" (0.12.0); "fix(tbench2_env): treat a nan or inf reward.txt as no verdict" (0.13.0); "Verify jupyter_env in a sandbox the agent never touched" and "Run coding_tools_env verification outside the notebook kernel" (0.14.0); "fix(chess_env): honor reset(seed) and episode_id" (0.14.0). Each change is in the version named; first affected versions are not stated. The `jupyter_env` one is opt-in: only a task that passes `submit_paths` to `reset` is verified in the second sandbox, and an empty list "keeps the current in-place behaviour untouched" (PR #1579), so existing `jupyter_env` tasks score as before. Rewards from those environments on older versions may include unearned passes — and the pre-fix versions are ready-made reward-hackable environments if that is what you study ([`rl-training.md`](rl-training.md#reward-hacking-measured-mitigations-and-pitfalls-2026)).

**Pitfall: `verifiers` 0.4.0 changed defaults that move rewards.** From the v0.4.0 release notes: "**The legacy v0 stack is removed.**" (use `import verifiers.v1 as vf`); "**Bash context compaction is enabled by default.**"; "**Rollouts have no default four-hour timeout.**"; and "**Judges default to `openai/gpt-6-luna`.** Pin a model explicitly for reproducible comparisons". Compaction changes what the policy sees, a missing timeout changes which rollouts finish, and a judge change rescales rewards — so don't upgrade in the middle of a project, and pin the judge model.

**Pitfall: `verifiers` 0.4.1 (2026-11-03) changed what "unscored" means.** From the release notes: "**`UnscoredError` is removed, and `nan` no longer means "unscored".** Check `trace.dropped` instead … Trainers must skip dropped traces." A custom trainer that skipped rollouts whose reward was `nan` may now train on dropped traces — check `trace.dropped`. Also in 0.4.1: "**The eval CLI is reduced to `vf-run`.** `vf-eval`, `vf-replay`, `vf-init`, the Rich dashboard, and eval platform push are removed" (rescore a saved trace with `Task.rescore(trace)`); runtime providers other than Prime, Docker and subprocess are removed (`modal`, `e2b`, `podman`, `apptainer` → `prime` or a `custom` runtime plugin); the env server moved to `prime_rl.env`; and the default decision-judge model on `DecisionJudgeConfig` changed from `typesafe-ai/jev` to `cloudflare/clef` (PR #2884) — pin it.

## vLLM hooks for a hand-rolled RL loop (sleep, weight transfer, pause/resume)

Aliases: vLLM sleep mode, `enable_sleep_mode`, `llm.sleep(level=...)`, `wake_up(tags=...)`, vLLM weight transfer, `WeightTransferConfig`, `pause_generation`, `resume_generation`, one-step-off-policy async RL. vLLM latest release v0.34.0 (PyPI 2026-11-16; previous v0.33.0, 2026-11-02, and v0.32.0, 2026-10-18). TRL 1.18.x supports vLLM 0.23.0–0.33.x, not 0.34.0, so this section matters most if you drive vLLM yourself. The notes below were checked against v0.31.0–v0.33.0; v0.34.0's RL-relevant changes were not re-read for this section (serving changes: [`compute.md`](../models-and-compute/compute.md)).

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
- **vLLM before 0.33.0: silent MoE expert-weight corruption after packed NCCL weight sync.** Issue #62554: "With packed NCCL weight transfer (`packed=True`) and layerwise reload (the default for checkpoint-format NCCL updates), MoE expert weights can be silently wrong after a weight update." The reporter first saw it in an RL deployment (Triton unquantized MoE backend); the reproducer forces NCCL's NET/Socket transport, the path cross-node transfers take. PR #62555 (merged 2026-10-22, released in v0.33.0): "10/10 corrupted reloads on `main`, 0/10 with this PR", and "Larger `num_buffers` doesn't avoid the bug: with k buffers, a layer spanning at least k + 2 packs is exposed" (default `num_buffers=2`). If you hand-roll RL weight sync for an MoE policy with packed NCCL transfer on vLLM ≤0.32.x, upgrade, or compare served weights against the trainer's after a sync (v0.32.0 added a `POST /weight_checker` endpoint for weight-transfer checks).
- **Other v0.33.0 changes that touch RL loops** (release notes): "requests sent while generation is paused now get HTTP 503 (#51488)" — a rollout client that keeps submitting during a weight swap must retry on 503; the weight-transfer API now uses `ParamMeta`, `iter_full()` and `iter_local()` (#63256), with parameter metadata sent once (#35911) and per-choice `return_weight_versions` (#61347). Pins: `torch==2.14.0`, `transformers>=5.16.1,<5.21.0`, Python 3.11–3.14; CUDA 13.0 artifacts only (general serving changes: [`compute.md`](../models-and-compute/compute.md#vllm-0320-upgrade-traps-released-2026-10-18)).

**When not to use these:** don't expose a `VLLM_SERVER_DEV_MODE=1` server beyond localhost — the docs say "these endpoints should not be exposed to users", and they include `/collective_rpc`; and don't hand-roll this when TRL, verl or prime-rl already does it.

## Version traps (search these symptoms)

- **`The NVIDIA driver on your system is too old (found version …)`** (PyTorch, `c10/cuda/CUDAFunctions.cpp`). vLLM's PyPI wheel is built for CUDA 13.0, and SkyRL's Tinker quickstart requires "CUDA 13.0 (NVIDIA driver r580 or newer)". vLLM 0.33.0 (2026-11-02) **stopped publishing CUDA 12.9 artifacts**: "The CUDA 12.9 wheels and the `-cu129` / `-cu129-ubuntu2404` images are no longer published". On a rented RunPod / vast.ai box, run `nvidia-smi` first; if the driver is older than r580, either pin vLLM ≤0.32.x and use its cu129 artifacts (e.g. `vllm/vllm-openai:v0.32.0-cu129`) or pick a host image with a newer driver.
- **PyTorch 2.14.0 with CUDA 13.2 binaries.** PyTorch v2.14.1 (2026-09-30) is a regressions and silent-correctness release; it moves the CUDA 13.2 Linux binaries to CUDA 13.2.2 because of a cuBLAS NVFP4 scaling bug and a compiler bug where "failed thread reconvergence could leave stale or corrupted register values in kernels with nested thread divergence (present since CUDA 12.8)". Upgrade to 2.14.1.
- **PyTorch 2.15.0 (2026-10-28) and FSDP2 `reduce_dtype`.** The release notes: "**This is BC-breaking**: `mp_policy.reduce_dtype=None` no longer defaults to `mp_policy.param_dtype`" — `fully_shard` now accumulates and reduces gradients in the parameter's original dtype (fp32 for fp32 master weights with `param_dtype=bf16`), so memory and communication change and loss curves need not be bit-identical across the upgrade. 2.15 wheels are `cu132` / `cu134` only; "hosts with a CUDA 12.x driver should stay on 2.14". 2.15.0 also fixes cuDNN `scaled_dot_product_attention` "returning NaN query gradients on Hopper (H100/H200) for non-causal attention when the key/value sequence length is 64 modulo 128, and silently corrupting generation on B200 for models with fewer than 8 key/value heads". vLLM 0.33.0, axolotl 0.21.1 and Unsloth 2026.11.2 all require torch < 2.15. Driver and CUDA check: [`compute.md`](../models-and-compute/compute.md#driver-and-cuda-version-check-on-rented-gpus-cuda-13-wheels); Python pins and separate environments: [`code-recipes.md`](../engineering/code-recipes.md#standard-pyprojecttoml-baseline).
- **`TRL currently supports vLLM versions from 0.23.0 to 0.33.x. You have version … installed.`** (TRL 1.18.x; 1.17.x printed `0.22.0 to 0.32.x`, 1.16.0 `0.22.0 to 0.31.0`, 1.15.0 `0.21.0 to 0.31.0`). A warning only (see TRL above); vLLM 0.34.0 triggers it on 1.18.x, and 0.33.0 on 1.17.x.
- **TRL ≤1.17.1: silent training-correctness bugs fixed in 1.18.0** — CISPO gradients 5× too small with default `epsilon_high`; `assistant_only_loss=True` masks wrong on Qwen3, GLM-4-MoE, DeepSeek-R1/V3, Nemotron 3 and gpt-oss templates; AsyncGRPO sampling from stale prefix-cache KV; GRPO with `repetition_penalty` and the vLLM importance-sampling correction training with zero gradient; MoE models saved by `SFTTrainer` 1.7.0–1.17.1 keeping `output_router_logits=True` (see TRL above).
- **An import error from `trl.experimental.async_grpo.async_grpo_config` (or `.packing`, `.vllm_client`, `.weight_transfer`, `.async_rollout_worker`), or empty W&B panels for `ratio` / `reward_std` / `kl`** — TRL 1.18.0 promoted `AsyncGRPOTrainer` to `trl` and renamed its metrics (see TRL above).
- **PyTorch advisory GHSA-v32g-mr63-3j83 (high, published 2026-11-10): `torch.load(weights_only=True)` allows arbitrary file read on torch 2.14.x; patched in 2.15.0.** "A malicious PyTorch checkpoint can read text files from the computer loading it, even when it is loaded with `weights_only=True`" (the advisory says it was tested vulnerable on 2.14.0 and 2.14.1; affected range `>=2.14.0`). The RL stack cannot simply upgrade: vLLM 0.33.0 / 0.34.0 and SkyRL 0.5.0 pin `torch==2.14.0`, and axolotl 0.21.1 and Unsloth cap `torch<2.15.0`. Until those pins move, don't `torch.load` a checkpoint from an untrusted source (a downloaded `.pt` / `.bin`, a third-party organism) in an environment that holds credentials or `.env` files; prefer `safetensors` files.
- **GRPO grad norm near zero / reward flat with `top_p`, `top_k` or `min_p` and vLLM** — TRL < 1.17.0 in any vLLM mode, TRL 1.17.x in `vllm_mode="server"`, and TRL 1.18.x in server mode when the vLLM server was not started with `--return-sampling-mask`: the importance-sampling ratio is biased toward 0 (see TRL above). Log line in 1.17.x server mode, and in 1.18.x when the server does not return the candidate sets: `the log-probabilities are normalized over the whole vocabulary and the importance ratio is biased`.
- **`ValueError` from `GRPOConfig` when `top_p < 1.0` or `min_p > 0.0` is set with `top_k=0`** — TRL ≥ 1.17.0 with vLLM importance sampling on; set `top_k` (e.g. `top_k=512`) or `vllm_importance_sampling_correction=False`.
- **PEFT 0.19–0.21.3 with transformers v5: MoE LoRA silently skips the dense and shared-expert layers (fixed in PEFT 0.22.0, 2026-11-19).** The affected range is the TRL maintainers' statement, not PEFT's (TRL PR #7771, quoted below, gives 0.19 to 0.21.2; TRL PR #8323 adds 0.21.3); PEFT's 0.22.0 notes and PEFT PR #3819 name no affected versions. PEFT 0.22.0's notes list "FIX all-linear skipping dense and shared-expert MoE layers" (#3819) and "FIX MoE conversion skipping routed experts when shared experts or dense layers share their name" (#3946). **PEFT 0.21.3 (2026-11-13) does not contain the fix** — it is a single unrelated backport (TRL PR #8323: "peft 0.21.3 (released today) only contains huggingface/peft#3963") — and TRL < 1.18.0 wrongly treated it as fixed: "The trainers treated peft 0.21.3 as having the MoE dense and shared layers fix, which it doesn't, so they stopped warning while the shared experts went untrained" (TRL 1.18.0 notes, PR #8323). So `peft==0.21.3` with TRL 1.17.x gets neither the fix nor the warning. axolotl 0.21.1 pins `peft==0.21.2` and SkyRL 0.5.0 `peft==0.21.0`, both in the affected range. Also in PEFT 0.22.0: "`modules_to_save` used to match purely by suffix, but now the whole sub-module name must match" (a behaviour change for existing configs); `from_pretrained()` / `load_adapter()` "now warn by default about both missing and unexpected adapter keys"; a fix for `add_weighted_adapter`, which "creates an overscaled adapter when the source uses rslora" (re-check adapter arithmetic on rsLoRA adapters from < 0.22.0); "PEFT now requires Python 3.11 or newer". Background on the original report: TRL PR #7771: "with transformers v5 and peft 0.19 to 0.21.2, the latest release, `target_modules` like `["gate_proj", "up_proj", "down_proj"]` or `"all-linear"` only train the routed experts of MoE models that have a dense first layer or shared experts (GLM-4-MoE, DeepSeek-V3, ...): the dense and shared expert layers get no LoRA, with no warning. It is fixed on peft main". With PEFT < 0.19 the routed experts were the ones left untrained. TRL 1.17.0 raises for the PEFT < 0.19 case and warns for 0.19–0.21.2 (TRL 1.18.0 also for 0.21.3); trainers pinned to older TRL (axolotl pins TRL 1.14.1, Unsloth ≤1.15.0) do not get this TRL check. Check which modules carry LoRA weights (`peft_model.targeted_module_names`) on any MoE LoRA run.
- **vLLM ≤0.32.x packed NCCL weight sync + layerwise reload can silently corrupt MoE expert weights** (see vLLM hooks above). **HTTP 503 from vLLM ≥0.33.0 while generation is paused** is expected behaviour, not a crash.
- **axolotl ≤0.21.0:** DPO/KTO gradients corrupted with activation offloading; LoRA GRPO merged vLLM sync drifted the frozen base weights; `lora_fp32_gradients` trained in BF16 under FSDP for RL trainers; CCE skipped logit softcapping; Gemma GEGLU used the wrong GELU (fixed in 0.21.1, see axolotl above).
- **Agent Lightning ≤1.0.2: zero GRPO advantages from bfloat16-cast rewards** (see Agent Lightning above). **OpenPipe ART ≤0.5.23: KL reference LoRA in saved checkpoints** (see OpenPipe ART above).
- **`AttributeError: 'RestClient' object has no attribute 'get_checkpoint_archive_url_from_tinker_path'`** — tinker ≥0.36.0 (see Tinker above).
- **`verifiers` 0.4.1: `nan` reward no longer means "unscored"; `vf-eval: command not found`** (see the RL environment libraries pitfall).
- **`loss=0.0` and `grad_norm=nan` at every step with `torch_compile=True`** — TRL before 1.16.0 on torch < 2.11 (see TRL above).
- **`TypeError` on `pause_generation(wait_for_inflight_requests=...)`, or rollouts aborted during a weight sync** — vLLM 0.32.0 removed the flag, and the default `mode` is `"abort"` (see vLLM hooks above).
- **PEFT before 0.21.0: an adapter that adapts nothing.** From the v0.21.0 notes: `add_adapter` now errors when a second adapter targets non-existing layers — "Before, the adapter would just not adapt anything but be silent about it." Also "Combining LoRA adapters using `add_weighted_adapter` had a bug in the `SVD` path which led to the LoRA scaling being applied twice", and deleting a merged adapter now raises. After attaching an adapter, assert `peft_model.targeted_module_names` is non-empty, and re-run any adapter-arithmetic result built with `combination_type="svd"`. The MoE LoRA delta and OSF paths changed numerics slightly, so don't expect bit-identical results across the upgrade.
- **axolotl 0.20.0: FSDP1 keys raise** (see axolotl above). **axolotl 0.21.0** fixes LoRA adapters saved empty under FSDP2 activation checkpointing and wrong-module QLoRA merges, and requires `vllm>=0.30.0`.
- **`verifiers` 0.1.9 vs 0.4.0** cannot share one virtualenv for the Tinker Cookbook (see the cookbook pitfall).
- **verl 0.9.x** deprecates `verl/experimental/fully_async_policy` and `one_step_off_policy`; repos built on verl 0.6.x (e.g. `ariahw/rl-rewardhacking-ext`) should keep their pinned version.
- **`FutureWarning` about reading attributes "from the future returned by a client-creation method"** — tinker ≥0.38.0; add `.result()` (see Tinker above). **A different learning rate from `get_lr()` with no code change** — tinker-cookbook ≥0.7.0 (see Tinker above).
- **SkyRL 0.5.0 supports tinker SDK < 0.28 while tinker-cookbook ≥0.6.0 needs ≥0.38** (see SkyRL above).
- **prime-rl < v0.11.0 on multi-node context-parallel RL: `Dropped N micro batches whose payloads could not be fetched`** — up to ~45% of a step's micro-batches lost (see prime-rl above). **prime-rl v0.11.0: launch fails without a Prime API key** unless `--no-monitors.prime` is passed; `trainer.loss.type = "ppo"` / `"cispo"` no longer exist.
- **OpenEnv ≤ 0.13.0 per the advisories, and 0.14.0 too by its source: unauthenticated env servers can leak `HF_TOKEN` and API keys** (advisories GHSA-67hq-8vmh-85x9 and GHSA-x2fj-957w-qm9g; no PyPI release has the `git_env` / Harbor fixes as of 2026-11-23; see RL environment libraries).
- **Tinker model retirements** (2026-06-12, 2026-07-12, 2026-10-23): hard-coded model IDs stop working (e.g. `DeepSeek-V3.1` → `DeepSeek-V4.1-Flash-1017`).
- **"IPO"** means INTELLECT Policy Optimization in prime-rl and Identity Preference Optimization in TRL / the DPO literature.
- **Qwen3 chat templates strip `<think>`** blocks, which some Environments Hub reward functions penalise.

## Common questions

### Which framework should I use for my first RL project?

If you have no GPUs: the **Tinker Cookbook** on hosted Tinker. If you have one GPU: **TRL GRPO** with colocated vLLM and sleep mode (or **Unsloth** for QLoRA on a 24 GB card). If you have two or more GPUs and want asynchronous agentic RL: **prime-rl**. Start from `project_templates/rl_small/`, which has a TRL single-GPU config and a Tinker / SkyRL script that switches between hosted and local by changing `base_url`.

### How do I get access to Tinker?

Sign up via `thinkingmachines.ai/tinker/` (the cookbook README links `auth.thinkingmachines.ai/sign-up`; create an API key in the Tinker console and export it as `TINKER_API_KEY`). Was private beta during late 2025; usage-based pricing is now published on the Models & Pricing page. As of 2026-10 it's the default RL/SFT tool for many MATS fellows because you don't manage GPUs. For status, check the Tinker docs or ask in the relevant Slack channels.

### How much does Tinker cost?

During the late-2025 private beta it was free; it is now billed per million tokens with separate prefill, sample and train rates (80% off cached prefill; checkpoint storage $0.10 per GB-month). Example from the Models & Pricing page on 2026-10-09: `Qwen/Qwen3-8B` at $0.195 prefill / $0.60 sample / $0.44 train per million tokens; the Inkling and some Nemotron models carried a limited-time 50% discount (on 2026-11-23 only Nemotron rows still do, and the cheapest in-house model is `thinkingmachines/Inkling-2-Mini` at $0.15 prefill / $0.50 sample / $0.75 train). Track usage during long RL runs — sample × N completions × LoRA-train × gradient steps adds up. Compared to renting H100s and managing infra yourself, the API premium typically buys back significant fellow-time. Check current pricing on the Tinker docs before budgeting; prices and the model list change.

### Can I run Tinker Cookbook recipes without a Tinker account?

Yes, on your own GPUs: start SkyRL's local Tinker server (`uv run --extra tinker --extra fsdp -m skyrl.tinker.api --base-model <model> --backend fsdp`) and pass `base_url=http://localhost:8000` with a dummy key (`TINKER_API_KEY=tml-dummy`). SkyRL 0.5.0 supports tinker SDK versions below 0.28 while the current cookbook requires ≥0.38, so pin the client and cookbook if the local run misbehaves (see the SkyRL section). KL penalties, prompt logprobs and the `ppo` / `cispo` losses are not yet wired through, and it needs CUDA 13.0 with driver r580+.

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

Last verified: 2026-11-23. (Additions 2026-11-23: versions table re-checked against PyPI JSON, including `requires_dist` pins, for trl 1.18.2, vllm 0.34.0, peft 0.22.0, tinker 0.39.2, tinker-cookbook 0.7.1, skyrl 0.5.0, unsloth 2026.11.10, openenv 0.14.0 (changed) and verifiers, axolotl, openpipe-art, agentlightning, verl, openrlhf, torch (unchanged); prime-rl v0.11.0 via `gh api` releases. TRL v1.18.0–v1.18.2 release notes plus PR bodies #8103, #7917, #8072, #8300, #8323, #8235 and #7915, `trl/import_utils.py` at the v1.18.2 tag and the state of issue #7865, all via `gh api`; other TRL PRs named in the notes were not opened. PEFT v0.22.0 / v0.21.3 release notes and PR #3819; prime-rl v0.11.0 release notes and PR #4489; NeMo RL v0.8.0 release notes and PRs #4158, #3722, #4154; OpenEnv v0.12.0–v0.14.0 release notes, PRs #1477 and #1579, and both security advisories via `gh api repos/openenv/OpenEnv/security-advisories` (patched-version fields are empty); PyTorch advisory GHSA-v32g-mr63-3j83 via `gh api`; SkyRL `limitations.mdx` and `quickstart.mdx` at tag `skyrl-v0.5.0`, `.agents/docs/tinker.md` on the default branch and the v0.5.0 release notes; Tinker SDK and cookbook changes read from unzipped PyPI wheels (tinker 0.37.0 / 0.38.0 / 0.39.0 / 0.39.2, tinker-cookbook 0.5.9–0.7.1), not executed; the Tinker Models & Pricing page as raw markdown fetched 2026-11-23; Unsloth release notes as dumped by `gh api`. LoRA rank collapse from the arXiv:2611.27148 PDF; repo licence via `gh api`. Not verified: a tinker 0.39.x client against a SkyRL 0.5.0 server; vLLM 0.34.0's RL-relevant release notes; whether Unsloth's RL guide still requires `fast_inference=False` for Qwen3.5. Verification pass 2026-11-23: `trl/trainer/grpo_config.py` and `trl/trainer/grpo_trainer.py` read at the v1.18.2 tag; the `openenv` 0.14.0 PyPI wheel compared with the `v0.13.0` / `v0.14.0` tags and `main`; PEFT PR #3946 and the Unsloth release list via `gh api`. Quotes are exact substrings of those sources.) Earlier: 2026-11-04. (Additions 2026-11-04: versions table re-checked against PyPI JSON for every PyPI package (trl 1.17.1, vllm 0.33.0, torch 2.15.0, tinker 0.37.0 / tinker-cookbook 0.5.9, verifiers 0.4.1, unsloth 2026.11.2, axolotl 0.21.1, openenv 0.11.0, openpipe-art 0.5.24, agentlightning 1.0.3 changed; peft, skyrl, verl, openrlhf unchanged; prime-rl and AReaL via `gh api` releases); release notes via `gh api` for TRL v1.17.0 / v1.17.1 (plus PR #7866 and #7771 bodies, issue #7865 state, and `trl/import_utils.py`, `trl/trainer/grpo_trainer.py` and `trl/trainer/grpo_config.py` at the v1.17.1 tag), vLLM v0.33.0 (GitHub release body; PyPI `requires_dist`; issue #62554 and PR #62555 bodies), axolotl v0.21.1, Agent Lightning v1.0.3 (plus PRs #640 and #662), verifiers v0.4.1 (plus PR #2884), OpenPipe ART v0.5.24, OpenEnv v0.10.0 / v0.11.0, PyTorch v2.15.0, torchtitan v0.4.0; the tinker method removal checked by grepping the PyPI wheels of tinker 0.35.0, 0.36.0 and 0.37.0 and the tinker-cookbook 0.5.9 wheel (`tinker_cookbook/weights/_download.py`); the Tinker "Model deprecations" page re-read as raw markdown; the axolotl ↔ vLLM 0.33.0 conflict reproduced with `uv pip compile` (Python 3.12, linux x86_64). Quotes are exact substrings of those sources.) Updated 2026-10-20: versions table re-checked against PyPI JSON for every package (trl 1.16.0, vllm 0.32.0, tinker 0.34.0, unsloth 2026.10.7, axolotl 0.21.0, openenv 0.9.0, openpipe-art 0.5.21 changed; the rest unchanged, prime-rl via its GitHub release list); release notes via `gh api` for TRL v1.16.0 (plus PR #7647 and `trl/import_utils.py` / `trl/trainer/grpo_config.py` at the v1.16.0 tag), vLLM v0.32.0 (plus `vllm/v1/engine/async_llm.py` at v0.31.0 and v0.32.0, PR #60923's diff, `docs/training/async_rl.md` and `examples/rl/` at v0.32.0), axolotl v0.21.0, OpenPipe ART v0.5.21 and OpenEnv v0.9.0; tinker 0.34.0's `model list` command and `copy_weights()` read from `src/tinker/cli/commands/model.py` and `rest_client.py` in `thinking-machines-lab/tinker`. Quotes are exact substrings of those sources. Moved here from `rl-training.md` on 2026-10-14: the Tinker, Tinker Cookbook, TRL, OpenRLHF, verl and Agent Lightning sections (their earlier verification notes remain in that page's footer). New on 2026-10-14, each checked against the primary source: PyPI JSON for every version and date in the versions table; `gh api` repo metadata and release notes for SkyRL, prime-rl v0.10.0, verifiers v0.4.0, axolotl v0.20.0, PEFT v0.21.0, vLLM v0.31.0, PyTorch v2.14.1, OpenEnv, OpenPipe ART, torchtune, torchforge and the "other stacks" list; raw docs read via the GitHub contents API (SkyRL `docs/content/docs/tinker/{quickstart,cookbook,limitations}.mdx`; TRL `docs/source/{vllm_integration,reducing_memory_usage,usage_stats,lora_without_regret,grpo_trainer,harbor,openreward}.md`, `trl/import_utils.py` and `trl/trainer/grpo_config.py`; vLLM `docs/features/sleep_mode.md`, `docs/training/async_rl.md`, `docs/training/weight_transfer/README.md`, `examples/rl/`; tinker-cookbook `pyproject.toml`, `recipes/rl_loop.py`, `recipes/verifiers_rl/README.md`; tinker `service_client.py`; PyTorch `c10/cuda/CUDAFunctions.cpp`); Fireworks (`docs.fireworks.ai/fine-tuning/training-api/{serverless,introduction}.md`, `reinforcement-fine-tuning-models.md`) and Together (`docs.together.ai/docs/post-training/{overview,pricing}.md`) docs fetched as raw markdown; OpenAI dates from `developers.openai.com/api/docs/deprecations.md` (raw markdown, 2026-10-14). Quotes are exact substrings of those sources.
