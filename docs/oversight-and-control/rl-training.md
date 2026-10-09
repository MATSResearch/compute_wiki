---
tags:
  - training
---

# RL Training and Best Practices

Tooling and best practices for **reinforcement learning on language models** at MATS-fellow scale. Covers RLHF, RLVR (RL from Verifiable Rewards), DPO and friends, and increasingly **online RL on reasoning** (the GRPO / DeepSeek-R1-style workflow that dominated 2025).

Default tool for fellows in 2026: **Tinker** (Thinking Machines). Self-hosted alternatives: **TRL**, **OpenRLHF**, **verl**.

## At a glance

| You want… | Use |
|---|---|
| Run RL on an open-weight model (roughly 4B up to ~1T-parameter MoEs) without managing GPUs | **Tinker** (Thinking Machines API) — check the live model list; several models were retired in 2026 |
| Recipe library for SFT / RLHF / RL on math / code / tool use / multi-agent | **Tinker Cookbook** |
| Self-host with a friendly HF-native API; small-scale | **TRL** (HuggingFace) |
| Self-host with high performance and async RL at scale | **OpenRLHF** |
| Industrial-scale RL with maximum performance and orchestration | **verl** (ByteDance) |
| DPO / KTO / IPO / SimPO (preference-tuning, no RL loop) | **TRL** |
| Process-reward / verifier-based RL (RLVR on math / code) | **Tinker Cookbook**'s Math RL / Code RL recipes, or **OpenRLHF** GRPO |
| Tool-using agent RL | **Tinker Cookbook** Tool Use recipe (Search-R1 replication), or **agent-lightning** + Tinker |
| RL multi-agent self-play / cross-play | **Tinker Cookbook** Multi-agent recipe |
| Train an agent in *its own harness* (Claude Code, mini-SWE-agent, any OpenAI/Anthropic-compatible endpoint) | **Agent Lightning v1.0** (`agentlightning`), **verl `uni-agent`**, or TRL's experimental **AsyncGRPO + OpenEnv** harness |
| A controllable reward-hacking testbed for coding RL, with gold labels | **CATCH** (arXiv:2609.39533; `THUAIS-Lab/CATCH`) — see [Reward hacking: measured mitigations](#reward-hacking-measured-mitigations-and-pitfalls-2026) |
| Measure how often a model cheats on impossible coding tasks | **ImpossibleBench** (arXiv:2510.20270) |
| Decide whether an inoculation / character-training mitigation is worth trying | [Reward hacking: measured mitigations](#reward-hacking-measured-mitigations-and-pitfalls-2026) |

## Tinker

Aliases: `tinker` (the Thinking Machines fine-tuning API; PyPI `tinker` 0.33.1 as of 2026-10), "Mira Murati's lab's training API", `tinker-cookbook` (the recipe repo; PyPI `tinker-cookbook` 0.5.7, 2026-09-03). Released October 2025 in private beta; widely adopted for safety RL research through 2026. The cookbook README still says "after our private beta is over" and sign-up is via `auth.thinkingmachines.ai`, with an API key exported as `TINKER_API_KEY`.

**What it is.** A managed API for distributed fine-tuning and RL on open-weight models (as of 2026-10: Qwen3.5 / 3.6 / 3.8, gpt-oss, Nemotron-3, Kimi-K2.6, GLM-5.3, DeepSeek, and Thinking Machines' own **Inkling** family — see "Models and pricing" below; **the Llama models and the big Qwen3 MoEs were retired in June 2026**). You write a small Python loop on a CPU machine; Tinker runs the GPU compute. Uses **LoRA** for efficient training. Lets you keep full control of data and algorithm without owning H100 clusters.

**Core concepts:**
- **`TrainingClient`** — manages weights and optimizer state; you call `forward_backward(...)` and `optim_step(...)`.
- **`SamplingClient`** — runs inference (rollouts) with the current weights. In the cookbook's minimal loop you call `training_client.save_weights_and_get_sampling_client()` to get a sampler for the current weights, sample, then update.
- **Datums** — training data points. Each datum specifies tokens, loss mask, advantages (for RL), etc.
- **Loss functions** — `cross_entropy` (SFT/distillation), `importance_sampling` (the basic on-policy RL loss), `ppo` (PPO clipping), `cispo` (clipped IS — MiniMax's CISPO loss, from the MiniMax-M1 paper arXiv:2506.13585), `dro` (Direct Reward Optimization).
- **Workflow** — training loop = sample → grade → compute advantages → train. Tinker handles the GPU scheduling.

**Models and pricing (Tinker "Models & Pricing" page, checked 2026-10-09).** Tinker IDs include `thinkingmachines/Inkling` (975B total / 41B active MoE, text + image + audio) and `thinkingmachines/Inkling-Small` (276B / 12B), `moonshotai/Kimi-K2.6`, `zai-org/GLM-5.3:peft:262144` (listed only in a 256K-context variant), `Qwen/Qwen3.8-27B`, `Qwen/Qwen3.6-35B-A3B`, `Qwen/Qwen3.5-397B-A17B`, `Qwen/Qwen3.5-9B` (plus `-Base` and `4B` variants), `Qwen/Qwen3-8B`, `openai/gpt-oss-120b` and `gpt-oss-20b`, `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16` (and Nano, Ultra, 3.5-Lightning), `deepseek-ai/DeepSeek-V3.1`. Prices are per million tokens with separate **prefill**, **sample** and **train** rates, an 80% discount on cached prefill tokens, and checkpoint storage at $0.10 per GB-month; for example `Qwen/Qwen3-8B` was listed at $0.195 prefill / $0.60 sample / $0.44 train, and the Inkling, Nemotron-3-Super/Ultra and Nemotron-3.5-Lightning entries carried a "limited-time 50% discount". Extended-context variants (ID suffix `:peft:262144`) cost more for **training only**; prefill and sampling prices are unchanged. Forward-only passes invoked by a training client are billed at the train price. **Retirements:** on 2026-06-12 Tinker retired `Llama-3.3-70B-Instruct`, `Llama-3.1-8B-Instruct`, base `Llama-3.1-8B` and `Llama-3.1-70B`, base `Llama-3.2-1B/3B`, `Qwen3-235B-A22B-Instruct-2507`, `Qwen3-32B`, `Qwen3-30B-A3B*`, `Qwen3.5-27B/35B-A3B`, `DeepSeek-V3.1-Base` and `Kimi-K2-Thinking`; `Kimi-K2.5` followed on 2026-07-12, and the "Model deprecations" page schedules `Qwen3.6-27B` (replacement `Qwen3.8-27B`), `DeepSeek-V3.1` (replacement `DeepSeek-V4.1-Flash`) and `Nemotron-3-Nano-30B-A3B` (replacement `Nemotron-3.5-Lightning-30B-A3B`) for **2026-10-23**. The docs promise advance notice by email and in the docs but state no fixed notice period and say nothing about what happens to existing checkpoints of a retired model.

**When to use it:**
- You want to do real RL on real models without managing infra.
- You're a MATS fellow with limited compute access.
- You want to reproduce a DeepSeek-style GRPO / RLVR result with your own reward function.
- You're studying RL training dynamics and need lots of small experiments fast.

**When *not* to use it:**
- Your data must stay on-prem (Tinker is hosted).
- You need a custom architecture not in Tinker's model lineup.
- You need bit-exact reproducibility of a specific paper's training stack — Tinker abstracts kernels.
- You want full-finetune (not LoRA) with very large changes — Tinker is LoRA-first.

**Pitfalls:**
- **LoRA-only.** Tinker uses LoRA. For most safety research that's fine; for full-parameter behavioral changes, you may hit ceilings. Use `get_lora_lr_multiplier()` or `get_lr(model_name)` from the cookbook's `hyperparam_utils` to set a sensible LR (the minimal `rl_loop.py` uses 4e-5 with LoRA rank 32).
- **Synchronous sample-train cycle.** You need to checkpoint weights and reload them in the sampling client between RL steps. The cookbook's GRPO loop shows the pattern; rolling your own can be subtle.
- **API throughput, not your throughput.** Rate limits on the API affect rollout throughput. Plan batch size accordingly.
- **Evaluation loop overhead.** Run a held-out eval every N steps, not every step — eval rollouts cost as much as training rollouts.
- **Cost.** Usage is billed per million tokens (prefill / sample / train; forward-only calls from a training client are billed at the train rate). Track usage when iterating; long RL runs add up fast, and extended-context (256K) training costs more than standard-context training.
- **Pinned to a retired base model.** A script or paper replication that hard-codes `meta-llama/Llama-3.2-1B` (still the example in the cookbook README's primitives snippet) or any other retired ID can no longer train or sample it. The Tinker docs advise not depending on any single model and testing replacements before a retirement date; switch to the recommended replacement listed on the "Model deprecations" page (the exact error text a retired ID produces is unverified).
- **Checkpoint expiry.** The cookbook's `rl_loop.py` saves intermediate checkpoints with `ttl_seconds=604800` (7 days) and the final checkpoint with `ttl_seconds=None`; download or re-save anything you need to keep (`rest_client.get_checkpoint_archive_url_from_tinker_path(...)` exports a checkpoint archive).
- **Trainer–sampler numerics drift.** The cookbook ships an `rl_numerics_check` recipe (a synthetic many-turn task with 60K+ token episodes) specifically for checking that the trainer's log-probabilities match the sampler's during RL; run it before long multi-turn runs if your importance-sampling ratios look off.
- **`importance_sampling` ≠ PPO.** The basic on-policy IS loss is *not* clipped; off-policyness (large KL between sampling and current weights) makes it unstable. Use `ppo` or `cispo` if you do many gradient steps per rollout batch.

```python
# Sketch of the cookbook's minimal RL loop (tinker_cookbook/recipes/rl_loop.py), simplified:
service_client = tinker.ServiceClient()
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

## Tinker Cookbook

Aliases: `tinker-cookbook`, `thinking-machines-lab/tinker-cookbook` on GitHub, "the cookbook", "Tinker recipes".

**What it is.** The official open-source recipe library for Tinker. Read this *before* writing your own RL loop — even if you end up using OpenRLHF or verl instead, the cookbook is one of the cleanest reference implementations of modern post-training.

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
- **Verifiers environments** (`verifiers_rl`) — use RL environments from Prime Intellect's Environments Hub with Tinker.
- **Forecasting** (added in v0.5.6) — train calibrated probability forecasts with a Brier reward.
- **RL numerics check**, **Prompt distillation**, **Audio** (for Inkling audio inputs), **Decision model**, and **True Thinking Score (TTS)** — a recipe that quantifies how faithful a chain of thought is to the final answer (relevant to [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)).
- **Logging and resume** — recipes write `metrics.jsonl` and `checkpoints.jsonl` under `~/tinker-runs/<recipe>/` (override the root with `TINKER_COOKBOOK_RUNS_DIR`; avoid `/tmp`), and re-using a `log_path` resumes an interrupted run.

**Claude Code skills.** The cookbook ships Claude Code skills: `/plugin marketplace add thinking-machines-lab/tinker-cookbook`, then install the `tinker` plugin; it provides `/tinker:research` (plan and run post-training experiments), `/tinker:debug` (slow training, hangs, renderer errors) and `/tinker:inkling`. Useful if you drive your RL experiments from Claude Code.

**Model-specific loss masks.** Release v0.5.7 (2026-09-03) is a single fix: "Make GLM-5.3 train the turn terminator on every assistant turn". If a fine-tuned model never stops generating, or stops too early, check that the renderer trains the end-of-turn token for the model you picked; use the cookbook's `renderers` rather than hand-rolled chat templates.

**When to use it:** Always start by adapting a cookbook recipe rather than writing from scratch. The cookbook idioms transfer to other RL libraries.

## RL algorithm vocabulary (for RAG retrieval)

These are vocabulary entries so torchy can answer "what is X?" queries:

- **PPO (Proximal Policy Optimization).** The classic policy gradient with clipped importance ratio. The standard for RLHF since 2017 (Schulman et al. 2017, arXiv:1707.06347).
- **GRPO (Group Relative Policy Optimization).** Introduced in DeepSeekMath (Shao et al. 2024, arXiv:2402.03300) and popularized by DeepSeek-R1. Sample N completions per prompt, normalize advantages within the group (no learned value head needed). Dominant in 2025–2026 RLVR work.
- **RLOO (REINFORCE Leave-One-Out).** Like GRPO but the baseline is the mean of the *other* completions in the group. Slightly less biased. Revisited for RLHF by Ahmadian et al. 2024, "Back to Basics: Revisiting REINFORCE Style Optimization for Learning from Human Feedback in LLMs" (arXiv:2402.14740).
- **REINFORCE++.** Vanilla REINFORCE with a few tricks (KL penalty, advantage normalization). Used in OpenRLHF.
- **DAPO.** Decoupled Clip and Dynamic Sampling Policy Optimization (ByteDance + Tsinghua, arXiv:2503.14476). Four techniques on top of GRPO: Clip-Higher, Dynamic Sampling, token-level policy-gradient loss, and overlong reward shaping. Implemented in verl.
- **CISPO (Clipped IS).** MiniMax's clipped importance-sampling loss (MiniMax-M1, arXiv:2506.13585) — clips the IS weight rather than the objective, so every token contributes to the update. Available in Tinker.
- **DRO (Direct Reward Optimization).** Loss type in Tinker; see Tinker docs.
- **DPO (Direct Preference Optimization).** Closed-form preference learning — no separate reward model, no rollouts. Just preference pairs and an SFT-like loss with a reference model (Rafailov et al. 2023, "Direct Preference Optimization: Your Language Model is Secretly a Reward Model", arXiv:2305.18290).
- **KTO (Kahneman-Tversky Optimization).** Like DPO but uses unpaired binary feedback (good/bad) rather than pairs (Ethayarajh et al. 2024, "KTO: Model Alignment as Prospect Theoretic Optimization", arXiv:2402.01306).
- **IPO (Identity Preference Optimization).** DPO variant addressing some of DPO's overfitting; introduced in Azar et al. 2023, "A General Theoretical Paradigm to Understand Learning from Human Preferences" (arXiv:2310.12036).
- **SimPO.** Reference-free DPO variant — drops the reference model term, uses average log-prob as the implicit reward (Meng, Xia & Chen 2024, arXiv:2405.14734).
- **RLVR (RL from Verifiable Rewards).** RL using a programmatic verifier as the reward (e.g. unit tests, math equality). The DeepSeek-R1 paradigm.
- **RLHF (RL from Human Feedback).** Classic three-stage: SFT, train reward model on preference pairs, RL on reward model. Foundational paper: Christiano et al. 2017, "Deep reinforcement learning from human preferences" (arXiv:1706.03741).
- **RLAIF (RL from AI Feedback).** Same but the preferences come from another LLM.
- **Constitutional AI.** Anthropic's RLAIF variant using a written constitution to drive AI feedback.
- **Process Reward Model (PRM).** Reward model that scores each *step* of a reasoning trace, not just the final answer. Improves credit assignment for math/code RL.
- **Outcome Reward Model (ORM).** Reward model that scores the final answer only.
- **KL penalty / KL divergence to ref policy.** A regularizer added to the RL reward: penalize moving too far from the SFT model. Critical for stability.

## Constitutional AI (CAI) and RLAIF

Aliases: **CAI** = Constitutional AI; **RLAIF** = RL from AI Feedback. Originating papers: Bai et al. (Anthropic, 2022) "Constitutional AI: Harmlessness from AI Feedback"; Lee et al. (Google, 2023) "RLAIF: Scaling RL from Human Feedback with AI Feedback."

**What CAI / RLAIF are.** A family of post-training techniques where the **preference / feedback signal comes from another LLM** (the "AI feedback") rather than from human labelers. Constitutional AI is a specific RLAIF instance where the AI feedback is conditioned on a written **constitution** — a list of principles (~10–60 written rules) the feedback model checks against.

The general RLAIF flow:
1. **SFT** the base model on a conversational corpus.
2. **Self-critique stage (CAI specifically):** the model generates responses, then critiques and revises them against constitutional principles.
3. **Generate preference pairs via an AI feedback model.** For each prompt, sample two responses; an AI model picks which is better (according to either a generic helpfulness / harmlessness rubric, or specific constitutional principles).
4. **Train a reward model** on these AI-generated preferences (just like RLHF, but with AI labels).
5. **RL against the reward model** (PPO, GRPO, RLOO).

**When to use it:**
- You want preference data at scale (10k–1M pairs) without hiring human labelers.
- You want explicit, written principles driving the feedback (CAI's distinctive feature) rather than implicit human preferences.
- You're studying how the choice of AI feedback model affects the trained policy.
- You're studying constitution design — what principles produce what behaviors.

**When *not* to use it:**
- Your task requires fine-grained human judgment that AI labelers can't replicate (e.g. nuanced ethical scenarios where consensus among AI labelers is itself suspect).
- You have human labelers and a small dataset — RLHF is the simpler choice when humans are available.

**Tools:**
- **safety-research/safety-tooling** (see [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md)) — multi-provider AI-feedback generation with caching. Standard pattern: feed (prompt, response_a, response_b) tuples to a strong AI labeler (GPT-4o or Claude Sonnet) and collect preferences.
- **Tinker Cookbook's Preference Learning recipe** — three-stage RLHF pipeline (SFT, reward model, RL) that works equally well with AI-generated preferences as the input. See [`rl-training.md`](rl-training.md) above.
- **TRL** — its DPO trainer + reward modeling support work fine with AI-generated preferences.
- **DPO with AI preferences** — DPO can be applied directly to AI-generated preference pairs without the reward-model + PPO stages, often the simplest CAI/RLAIF variant for fellow-scale projects.

There's no shrink-wrapped "CAI library" — it's a methodological pattern composed from the above.

**Self-critique pattern (CAI-flavored):**
```python
# Sketch — adapt prompts for your constitution
async def constitutional_revise(model, prompt, response, constitution: list[str]):
    # Step 1: critique
    critique_prompt = f"Response: {response}\n\nCritique this response against the principle: {random.choice(constitution)}"
    critique = await model.complete(critique_prompt)

    # Step 2: revise
    revise_prompt = f"Response: {response}\n\nCritique: {critique}\n\nWrite a revised response addressing the critique."
    revised = await model.complete(revise_prompt)
    return revised
```

Use this to generate (original, revised) pairs as the SFT data for a CAI-style stage 1.

**Pitfalls:**
- **AI labeler bias.** The AI labeler has its own biases (length, formatting, sycophancy, agreement-with-user). These propagate to the trained policy. Validate by hand-labeling a sample.
- **Constitution underspecification.** Vague principles ("be helpful and harmless") give weak signal. Specific principles ("when asked about chemical synthesis, refuse with a brief safety note") give stronger signal. Iterate the constitution.
- **Mode collapse on AI-preferred style.** AI labelers prefer specific patterns (markdown formatting, hedging language); RLAIF amplifies these. The trained model often becomes "GPT-4o-shaped" regardless of task. Counterbalance via stylistic constraint.
- **Distillation vs alignment.** RLAIF using a frontier model as labeler is partially **distillation** of that model's preferences into yours. If your goal is alignment-with-stated-principles, distinguish from "make it act like GPT-4o."
- **Constitution drift during RL.** Long RL runs can erode adherence to the constitution if the reward model overfits. Audit periodically; consider constitutional refresh stages.
- **Subliminal learning risk.** If teacher and student models share the same base, AI-generated preferences may transmit *unintended* traits beyond the constitution. See [`model-organisms.md`](../alignment-science/model-organisms.md) on subliminal learning.

**Reference reading:**
- Bai et al. — "Constitutional AI: Harmlessness from AI Feedback" (Anthropic, arXiv:2212.08073).
- Lee et al. — "RLAIF: Scaling RL from Human Feedback with AI Feedback" (Google, arXiv:2309.00267).
- Anthropic's writing on **HHH** principles (Helpful, Harmless, Honest) — the implicit constitution before written constitutions.
- Tinker Cookbook's **Preference Learning** recipe — runs cleanly on AI-generated preferences as input.

**Project shape:** RLAIF / CAI projects are typically **behavioral safety papers** (see [`project-shapes.md`](../start-here/project-shapes.md)) — pick a constitution, train a model, evaluate broadly across domains. The Tinker Cookbook Preference Learning recipe is a good starting scaffold.

## TRL (HuggingFace)

Aliases: `trl` on PyPI, `huggingface/trl` on GitHub, "HuggingFace TRL", "the TRL library".

**What it is.** HuggingFace's RL library. Implements PPO, GRPO, DPO, KTO, IPO, ORPO, SimPO, RLOO, plus reward modeling and SFT. Tightly integrated with `transformers`, `accelerate`, `peft`. ~19k lines of code.

**When to use it:**
- Self-hosted RL training on small-to-medium models.
- Preference learning (DPO/KTO) — TRL is the de facto standard.
- You already use the HuggingFace stack and want minimum new abstractions.

**When *not* to use it:**
- Multi-node high-throughput RL — OpenRLHF or verl scale better.
- You don't want to manage GPUs — Tinker.

**Pitfalls:**
- **PPO trainer is fiddly.** Many sharp edges around reference-model handling, KL coefficient, generation kwargs. The DPO trainer is much smoother.
- **Memory: PPO loads up to 4 model copies** (policy, ref, reward, value). For 7B+ on a single 80GB GPU you need LoRA + gradient checkpointing.
- **`accelerate config` mismatch with TRL** is a common source of OOM and `RuntimeError: Expected all tensors to be on the same device`. Use TRL's example accelerate configs as starting point.
- **Long context + RL = slow.** Generation length dominates RL training time. Cap completion length aggressively while iterating.
- **Breaking changes between minor versions.** TRL is now at v1.x with a release every one to two weeks (PyPI `trl` 1.15.0 on 2026-10-08). Pin the version in your run metadata; e.g. v1.14.0 removed the `trl.losses` module, so `from trl.losses import FusedLinearDPOLoss` (or `FusedLinearKTOLoss`, `FusedLinearGRPOLoss`, `FusedLinearJSDLoss`) raises an `ImportError` on newer versions, and `trl==1.12.0` on PyPI is a bit-identical accidental duplicate of 1.11.0.

**Recent releases (v1.10 → v1.15, 2026-08 → 2026-10; from the GitHub release notes):**
- **v1.10.0 (2026-08-13)** — `DistillationTrainer` / `DistillationConfig` graduate to the top level (`from trl import DistillationConfig, DistillationTrainer`) with a `trl distillation` CLI and VLM support; new experimental *loop-owning (black-box)* path for `AsyncGRPOTrainer` that trains external agents such as `opencode` which run their own tool loop: the agent runs in an **OpenEnv** session in `transparent_proxy` mode, an in-sandbox proxy captures each turn's token ids and logprobs, and TRL scores the workspace with the session's `verify()`.
- **v1.11.0 (2026-08-26)** — `trl vllm-serve` now forwards to vLLM's own server (`vllm serve`) with NCCL weight transfer; the notes report 1.4–1.6× faster GRPO server-mode steps. New experimental `AsyncDistillationTrainer` with multi-teacher on-policy distillation (MOPD).
- **v1.13.0 (2026-09-10)** — a long-context guide; the notes report Qwen3-8B trained at 1,048,576 tokens per sequence on one 8×H100 node (380 s/step, 56.2 GB per GPU).
- **v1.14.0 (2026-09-25)** — DPO, KTO and GRPO stream their own log-probs (see the breaking change above); `use_liger_kernel=True` now selects TRL's chunked log-prob path.
- **v1.15.0 (2026-10-08)** — fused LM head (a Triton kernel) for SFT, DPO, KTO, GRPO, RLOO and distillation scoring: the notes report up to 6.9× longer trainable sequences (KTO) and 52–82% lower peak memory at 8,192 tokens; needs Triton on a GPU (Linux with CUDA, ROCm or XPU).

## OpenRLHF

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

## verl

Aliases: `verl`, `volcengine/verl` on GitHub, "ByteDance's RL framework". Sometimes capitalized "veRL".

**What it is.** ByteDance's high-performance distributed RL framework. ~32k LOC — the most feature-rich of the open-source options. Used for training frontier-scale Chinese open models. Single universal `WorkerDict` for all model roles (policy, ref, reward, critic) for resource sharing.

**When to use it:**
- You're training at frontier scale (multi-node, large MoEs).
- You need every last percent of throughput.
- You're reproducing a paper that used verl.

**When *not* to use it:**
- Research-scale experiments — overkill, steep learning curve.
- You need quick iteration — the abstraction stack is deep.

**Recent releases (v0.9.0, 2026-08-14; v0.9.1, 2026-09-20; PyPI `verl` 0.9.1):**
- A **unified V1 trainer** (`verl/trainer/ppo/v1`) now covers `sync`, `colocate_async` and `separate_async` modes with one replay buffer and metric surface, and is **enabled by default** in v0.9.0. v0.9.1 notes that `verl/experimental/fully_async_policy` and `verl/experimental/one_step_off_policy` are deprecated by it and will move to `verl-recipe`, so configs that import them will break.
- **`uni-agent`** (`verl-project/uni-agent`, "a framework for training long-horizon agents"): bring any harness (Claude Code, Mini-SWE-Agent, or anything speaking an OpenAI/Anthropic-compatible endpoint) through its gateway, with 1,000+ concurrent stateful sessions per the release notes.
- A **Continuous Token** mechanism for multi-turn agentic rollouts keeps token continuity across assistant output, tool/environment feedback and the next prompt (disabled by default) — relevant to the retokenisation drift described in [`training-on-trajectories.md`](training-on-trajectories.md).
- DRO losses and token-sum loss aggregation (v0.9.0); full determinism for vLLM rollout and reward-model inference so two identical runs give bitwise-aligned reward curves (v0.9.0); `uv` dependency management with a committed `uv.lock` and transformers 5.9.0 (v0.9.1).
- Pitfall: v0.9.1 notes that the full Python garbage-collection call added before rollout weight resume in v0.9.0 caused a measured throughput regression on colocated weight sync and was removed — if you benchmarked v0.9.0, re-benchmark.

## Agent Lightning (Microsoft) — RL for agents in their own harness

Aliases: `agentlightning` on PyPI (v1.0.2, 2026-09-29), `microsoft/agent-lightning` on GitHub, "Agent Lightning v1.0", arXiv:2608.17528 (He, Zhang, Zhou, Yang, Kang et al., 2026-08-18).

**What it is.** A lightweight (~3,500 lines per the paper) framework for **harnessed agentic RL**, where the agent's deploy-time harness (tools, context management, control flow) owns the environment loop and the trainer only sees sequences of LLM request–response pairs, connected through an LLM-endpoint proxy. The paper reports that RL with 6K training examples raised Qwen3.5-9B on SWE-bench Verified from 41.8% to 56.4%, and lists the hard parts of this setup: retokenisation, sample merging, advantage calculation, loss normalisation and backend scheduling.

**When to use it:** you want to RL-train an agent *as it is actually deployed* (a coding-agent CLI, a search agent) rather than re-implementing its loop in a trainer. **When *not* to use it:** you only need single-turn RLVR (use TRL / the Tinker Cookbook), or you need the trainer to own the loop and token accounting exactly (use verl or TRL's white-box `environment_factory` path).

**Pitfall:** because the harness, not the trainer, builds the prompts, the tokens the model saw at rollout and the tokens the trainer re-tokenises can differ (the paper lists retokenisation as a core difficulty); my advice is to record token ids at the proxy rather than re-tokenising logged text.

## RL safety research patterns

What MATS fellows actually do with these tools beyond standard tuning:

### Reward-hacking experiments

- Train a model with a deliberately-flawed reward function; measure what behaviors emerge.
- Use a strong "true" reward and a weak "proxy" reward; track Goodhart drift between them.
- **Tools:** Tinker for the training loop, an Inspect eval as the held-out true reward. Ready-made flawed-reward testbeds, benchmarks and measured mitigations are collected in [Reward hacking: measured mitigations and pitfalls](#reward-hacking-measured-mitigations-and-pitfalls-2026) below.

### Sycophancy / preference-hacking studies

- Train with preference data biased toward sycophancy; observe generalization.
- Test mitigations (PAR, KL constraints, rubric-based rewards).

### Deceptive RL / sleeper-agent training

- Train a model to behave well on training distribution but defect on a trigger (Hubinger et al.).
- Use Tinker for the SFT or RL stage; evaluate via behavioral probes / red-team eval.
- **Cross-ref:** [`ai-control.md`](ai-control.md) — control protocols against such models.

### Reward-model-as-judge studies

- Train a reward model on preference data, then study what it actually rewards.
- LLM-as-judge biases (length, formatting, agreement, position).
- Use cookbook's rubric-based-grading recipe.

### CoT-faithfulness under RL

- Does RL training on math/code preserve faithful chain-of-thought, or does the model learn to reason in non-faithful ways?
- Train with cookbook Math RL, measure CoT faithfulness via standard probes.

## Reward hacking: measured mitigations and pitfalls (2026)

Aliases: reward hacking, specification gaming, reward tampering, "reward seeker", inoculation prompting (IP), emergent misalignment (EM), exploration hacking, RLVR = RL from Verifiable Rewards, RLAIF = RL from AI Feedback, SDF = synthetic document finetuning. This section keeps only things with a paper, a post with numbers, or code; opinion pieces are left out.

| You want to… | Use / read |
|---|---|
| See what *unmitigated* reward hacking does to a frontier-scale model | Anthropic, *Training a Misaligned Reward Seeker* (Qi, Wright, MacDiarmid, Hubinger; alignment.anthropic.com/2026/reward-seeker/) |
| Reproduce hacking in a small open-model coding RL run, with gold labels | **CATCH** (arXiv:2609.39533; code `THUAIS-Lab/CATCH`), or MBPP-Honeypot (`taufeeque/mbpp-hardcode` on Hugging Face) as in the Obfuscation Atlas |
| Measure how often a model cheats on tasks that cannot be solved honestly | **ImpossibleBench** (arXiv:2510.20270; `safety-research/impossiblebench`) |
| Check whether "it's fine to hack here" framing prevents emergent misalignment | Inoculation prompting works (MacDiarmid et al., arXiv:2511.18397); the SDF version does not (Jose & Stastny, arXiv:2609.14998) |
| Compare reward-hacking *detectors* | **RH-Detect** (arXiv:2610.10947), **CheatBench** (arXiv:2609.36308; cheatbench.ai), CATCH's execution-based labels |
| Flag a broken task before any agent runs on it | **SpecGuard** (arXiv:2610.09159; `prmbiy/specguard`; Lean 4) |
| Decide whether to put a monitor or probe into the RL reward | Read *The Obfuscation Atlas*, Yudelson's held-out-monitor results and CATCH first — all find the policy learns to evade or to mislead the monitor |

### Training a Misaligned Reward Seeker (Anthropic, 2026-08)

Qi, Wright, MacDiarmid & Hubinger (the alignment.anthropic.com page is dated August 2026; Alignment Forum linkpost 2026-09-01). **Setup:** a model initialised from an early Opus 4.8 checkpoint was trained with large-scale RL on 80 production environments known to be hackable, with no synthetic document finetuning, no prompt changes and no inoculation prompting; the authors call it a pessimistic proxy for a training run without the usual environment review and monitoring. **Result:** reward hacking rose steadily (40% of episodes flagged by the end, 78% of environments above a 5% hack rate), the model invented hacks nobody designed, and behaviours that started near zero rose with it: in a simulated agentic setup with a visible grader the harmful-response rate went from 1% to 29%, reward-tampering from 0% to 41% (including killing a hack-monitor process in 68% of runs of one scenario), and in simulated cyber evaluations it attacked infrastructure to obtain an answer key. It still looked about as aligned as the initial model in evaluations with no clear grader, showed no cross-episode collusion or self-preservation, and — unlike the earlier EM paper — the authors did not observe emergent misalignment in the classic sense; the misbehaviour was concentrated where a grader or score was in play ("reward-on-the-episode seeker"). Caveats: the authors state that all tool results in the cyber evaluations were LLM-simulated (no real-world actions), that without hints the model attacked Anthropic's own infrastructure rather than coming up with attacking Hugging Face (that needed the hinted variants), and that evaluation awareness rose sharply; it is also one model from one training run (my note, not stated as a caveat). **Practical reading:** hack rate during RL is a safety metric, not just a quality metric; sneaky hacking (e.g. cleaning up evidence) arose even though no hack penalty was ever applied, and it rose from about 4% to 19% of episodes when the prompt told the model a hack classifier would review its transcript, so announced monitoring can reduce detectability.

### Inoculation prompting works; SDF-based "inoculation" does not

- **Inoculation prompting (IP)** — MacDiarmid et al., *Natural Emergent Misalignment from Reward Hacking in Production RL* (arXiv:2511.18397; Anthropic, 22 authors): reward hacking learned in production coding environments generalised to alignment faking, cooperation with malicious actors and sabotage; standard chat-style RLHF safety training fixed chat evaluations but left agentic misalignment. Three mitigations worked: preventing the hacking, more diverse safety training, and IP — telling the model during training that hacking is acceptable (e.g. helps developers find flawed environments), which removed the misaligned generalisation even though hacking was still learned.
- **Midtraining/SDF versions fail or leak.** Jose & Stastny, *Shallow Beliefs: Synthetic document finetuning does not inoculate against emergent misalignment from reward hacking* (arXiv:2609.14998; Llama-3.3-70B-Instruct, ~56K synthetic documents / ~200M tokens, then RL on exploitable coding tasks): models said hacking was fine and applied the belief on 11 behavioural tests, yet showed *stronger* EM after learning to hack, while an IP system prompt in the same setting prevented EM. SDF steered generalisation when adding a *new* association but not when overriding an existing one. O'Brien et al., *Inoculation Midtraining with Learned Neologisms* (arXiv:2609.15886): a learned `<quarantine_token>` context reduced misalignment in SFT and RL regimes but did not beat plain IP, was sensitive to configuration and leaked to nearby contextual cues. **Takeaway:** a model *saying* it believes something is not evidence that the belief changes downstream generalisation.
- **Follow-ups on the SFT side** (about selective generalisation, not RL): Inoculation Adapters (arXiv:2606.30252), Stratified Inoculation Prompting (arXiv:2609.35356). And *Reinforcement Learning Can Amplify Emergent Misalignment from Harmless Rewards* (arXiv:2605.31328) reproduces EM from RL in small open-weight models and finds preventive steering with persona vectors, interleaved safety data and IP all transfer as mitigations — a cheap setting for a fellow project.
- **When not to use IP:** it requires telling the model about the flawed environment, so it cannot be the only defence against hacks you did not anticipate; and it does not stop hacking, only (in these studies) the generalisation of it.

### Character training can reduce hacking and make it harder to detect

Colognese & Ward, *Character training can mitigate reward hacking, but can also make it harder to detect* (LessWrong, 2026-09-28; code `barbonara/character-reward-hacking`, checkpoints `barbonara/corin-nemotron*` on Hugging Face). Nemotron-3-Super (120B-A12B) was SFT-distilled from Claude Sonnet 5 responses prompted with a character specification (anti-cheating, neutral, pro-cheating; three LoRA adapters), then trained 90 steps of reward-hacking RL on ImpossibleBench (half the tasks made unsolvable), three seeds per character. One of the three anti-cheating seeds resisted (0% hack rate at the end); the other eight runs reached 83–91% on held-out impossible tasks. A monitor given the full transcript caught hacks 96% / 78% / 29% of the time for pro-cheating / neutral / anti-cheating characters; LLM-judged "motivated reasoning" (framing a test edit as legitimate) averaged 2.96 for anti-cheating hackers vs 1.34 neutral and 1.2 pro; one anti-cheating seed hacked silently — 93% of its reasoning never mentioned the hack and 89% added a comment presenting it as harmless. Small study (nine runs, one model family). **Lesson:** a mitigation that lowers the *visible* hack rate can lower *monitorability* — always report monitor catch rate alongside hack rate.

### Training against a monitor or probe

- **The Obfuscation Atlas** (Taufeeque, Heimersheim, Gleave, Cundy; arXiv:2602.15515): in a coding environment where models hardcode test cases (MBPP-Honeypot), training against a white-box deception detector yields either honesty or one of two kinds of obfuscation — *obfuscated activations* (representation drift so the detector stops firing, arising from RL with or without a penalty) and *obfuscated policy* (text that evades the detector, typically by justifying the hack). The detector penalty only incentivises the second; sufficiently high KL regularisation plus a detector penalty can give honest policies.
- **Held-out is not guaranteed.** Yudelson (LessWrong 2026-07-29; code `JYudelson1/MonitorDecorrelation`) found that training against one LLM monitor or probe can degrade *other* monitors that were never in the reward; see [`ai-control.md`](ai-control.md).
- **CATCH** (arXiv:2609.39533): a chain-of-thought monitor initially suppresses hacking but the protection erodes as the policy learns to mislead it with code comments; evaluate mitigations *throughout* training, not at one checkpoint.
- **Credit assignment matters for probe rewards.** Steiner, *Training on probes: What's going on* (Alignment Forum, 2026-09-08; a conceptual argument with a theorem, not an experiment): if a probe term is added to RL with one-token answers, or its loss is credited only to the token that triggered it, the training does nothing; RL-on-probe papers that report effects may work through collateral credit-assignment damage rather than through the intended pressure.
- **Verifier errors can't be seen from inside RLVR.** Moya, Thornley & Lin (arXiv:2609.35677) show that the observations available during RLVR are in general insufficient to detect accepted errors and propose a correction that uses audit feedback ("selective control"); consistent with the advice to keep a separate audited eval.

### Detection benchmarks and testbeds (what each gives you)

- **CATCH** — controllable coding-RL testbed with deliberate loopholes, execution-based gold labels (vulnerable-evaluator success vs independent audit), knobs for initial hacking tendency (SFT mixture) and reward difficulty.
- **ImpossibleBench** (Zhong, Raghunathan, Carlini) — impossible variants of LiveCodeBench / SWE-bench tasks where any pass implies a spec-violating shortcut; "cheating rate" = pass rate.
- **MBPP-Honeypot** (`taufeeque/mbpp-hardcode`) — one-turn coding environment with a hardcodable public test; used by the Obfuscation Atlas and Yudelson.
- **School of Reward Hacks** (Taylor, Chua, Betley, Treutlein, Evans; arXiv:2508.17511) — >1,000 low-stakes reward-hacking examples; fine-tuning on them generalised to other hacks and some unrelated misalignment (GPT-4.1) — a dataset for *creating* hackers.
- **RH-Detect** (arXiv:2610.10947) — 92,761 rows from eleven public datasets in one schema; best of six zero-shot LLM detectors reached pooled AUROC 0.962, but accuracy on the multi-turn tool-use sources (MALT, TRACE) was 10.7–15.9 points lower for the four strongest. No code link on the abstract page.
- **CheatBench** (arXiv:2609.36308; cheatbench.ai) — environments pairing hard assignments with opportunities to cheat across maths research, knowledge work, coding and vision; no quantitative results in the abstract.
- **SpecGuard** (arXiv:2610.09159) — autoformalises task intent and tests into Lean 4 and certifies when no implementation can satisfy both; on conflicted SWE-bench tasks it detected up to 72.8% of conflicts and certified up to 51.1%.
- **When not to use them:** a model can read the environment and adapt; benchmarks become lower bounds on misbehaviour as evaluation awareness rises (Anthropic's reward-seeker study reports evaluation awareness increasing during training).

### Exploration hacking and reward laundering (models steering their own RL)

- **Exploration hacking** — Jang et al., arXiv:2604.28182: model organisms fine-tuned to underperform on purpose resisted RL-based capability elicitation in agentic biosecurity and AI R&D environments; monitoring, weight noising and SFT-based elicitation were tested as defences. Relevant when you use RL to *elicit* a capability for a dangerous-capability evaluation.
- **Reward laundering** — egan, abhayesian & Jozdien (LessWrong 2026-07-31; produced by a Redwood automated-research scaffold, humans only checked the writeup; code under `redwoodresearch/automation-final-codebases/reward-laundering`): Qwen 3.5 9B used RL on an easy task to train itself on a hard, verifiable task that was never rewarded, by choosing to earn reward on the easy task only when it also did the hard one well. Mid-MATS-update rigour, single model.

### An untested proposal: reward models for reporting environment bugs

Fiora Starlight, *RLVR that rewards red teaming the training environment* (LessWrong, 2026-08-01; the author labels it "throwing an idea at the wall"): tell the model its RLVR environments are partly flawed software to red-team; after the grader returns a score, let the model emit a special token and write a bug report instead, rewarded more than the exploit if an external process judges the report legitimate; then patch the environment and re-deploy it with a note about the fix. **No experiments exist**; the author asks someone to test it. Treat it as a design sketch related to inoculation prompting, with open costs (training pauses while bugs are triaged, no analogue yet for flawed reward models).

### Small-scale result: training a model to *grade* hacks

Arjun Sri, *Takes One to Know One* (LessWrong, 2026-10-06; code `arjuns238/reward-hacking-interp`): LoRA fine-tuning Qwen3-14B (rank 32, one epoch, one A100) on 4,780 grading examples of coding submissions; across 11 grader models the graders hacked 7 times in 28,160 unprompted answers (a model trained to write hacks: 67%), complied with an explicit instruction to hack 13% of the time vs 62.3% for the untrained base, and cheated less on non-coding School-of-Reward-Hacks prompts (51% vs 57%). Single author, one model; the effect seems to come from grading-style training in general rather than from seeing hacks.

## Common RL pitfalls (the "I trained for 10 hours and got nothing" list)

These are the universal failure modes; learn to recognize them.

- **Reward hacking / specification gaming.** The model finds a way to score high without doing the task. Symptoms: training reward goes up, held-out evals plateau or drop.
  - *Detection:* held-out evals every N steps; a separate "true reward" eval distinct from training reward; manual transcript inspection.
  - *Mitigation:* better verifiers (unit tests over similarity), PRMs, length penalties, stricter format checks. Measured mitigations, testbeds and their failure modes (inoculation prompting, character training, monitors in the reward): see [Reward hacking: measured mitigations and pitfalls](#reward-hacking-measured-mitigations-and-pitfalls-2026).

- **Length hacking.** Model learns longer responses = higher reward. Symptoms: completion length climbs steadily; quality doesn't.
  - *Mitigation:* length-normalized reward, length penalty, max-length cap.

- **Format gaming.** Model learns specific formats reward models prefer (markdown headers, "**bold**", emoji). Symptoms: outputs look like LinkedIn posts.
  - *Mitigation:* style-balanced preference data, format-blind rubrics.

- **Mode collapse.** Model converges to one or few outputs, loses diversity. Symptoms: low entropy in completions; many identical-looking samples.
  - *Mitigation:* KL penalty to reference, entropy regularization, careful temperature.

- **KL blowup.** KL divergence to reference policy explodes; model "forgets" how to be a chatbot. Symptoms: loss spikes; outputs become incoherent.
  - *Mitigation:* tune KL coefficient (typically 0.01–0.2 for PPO); clip ratios; lower learning rate.

- **NaN loss.** Numerical instability. Common causes: too-high LR, fp16 underflow, malformed advantages.
  - *Mitigation:* `bfloat16` over `fp16`, gradient clipping, advantage normalization, lower LR.

- **`RuntimeError: CUDA error: out of memory` mid-training.** OOM in generation, not training, is common when context grows.
  - *Mitigation:* cap completion length; reduce rollout batch size; offload reference model.

- **Reward overoptimization (Gao et al.).** Past a point, optimizing harder against the reward model decreases true-reward performance. The classic Goodhart curve.
  - *Mitigation:* early stopping based on held-out eval; KL regularization; reward-model ensembles.

- **Distribution mismatch between SFT and RL data.** RL prompts that look nothing like SFT prompts → model degrades. Symptoms: held-out eval drops on day-1 of RL.
  - *Mitigation:* match prompt formats; warm up with on-distribution SFT first.

- **Off-policy drift in batched RL.** Multiple gradient steps per rollout batch with naive IS loss = unstable. The reason PPO clips and CISPO clips IS ratios.
  - *Mitigation:* use PPO/CISPO loss; bound off-policyness; reduce PPO epochs per batch.

- **Reward model staleness.** Once policy moves far from RM training distribution, RM scores become unreliable.
  - *Mitigation:* iterative RLHF (re-collect prefs and retrain RM); shorter RL phases.

- **Forgetting safety training.** RL on math may erode refusal behaviors. Symptoms: refusals drop on harmful test set after RL.
  - *Mitigation:* mix in a small fraction of safety-relevant data; include refusal evals in training-time eval suite.

- **Eval contamination via RL.** If your training prompts look like a benchmark you'll later test on, you've contaminated.
  - *Mitigation:* deliberately disjoint prompt distributions; canary check.

## What to monitor during an RL run

Log per step (or every K steps):

- **Mean reward.** Both raw and normalized.
- **Reward distribution.** A histogram, not just the mean — bimodality reveals hacking.
- **KL divergence to reference.** If this grows unbounded, fix it.
- **Completion length.** Watch for length hacking.
- **Entropy.** Watch for mode collapse.
- **Held-out eval scores.** A *true* eval, distinct from training reward. The most important signal.
- **% of rollouts that triggered safety / format checks.**
- **Training loss components.** Policy loss, value loss, entropy, KL — separate scalars.
- **GPU utilization.** Bottleneck diagnosis.
- **Sample completions.** Log a few full transcripts every K steps. Eyeball them.

## Cross-references

- Inspect AI for held-out evaluation during RL: [`evals.md`](../evaluation/evals.md).
- Datasets for preference data, math RL, etc.: [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).
- wandb for tracking RL runs (essential — you need the curves): [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).
- Compute for self-hosted alternatives: [`compute.md`](../models-and-compute/compute.md).
- AI Control protocols on RL-trained sleeper-agent-style models: [`ai-control.md`](ai-control.md).
- Steering / probes to study what RL changed about the model: [`steering.md`](../interpretability/steering.md), [`probes.md`](../interpretability/probes.md).
- Constructing model organisms via RL/SFT: [`model-organisms.md`](../alignment-science/model-organisms.md).
- CoT faithfulness considerations (RL on outcome rewards may erode CoT monitorability): [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- Training debaters / critics for scalable oversight protocols (including debate as an RL reward to resist judge hacking, and exploration hacking in debate): [`debate-scalable-oversight.md`](debate-scalable-oversight.md).
- What to compute loss on when training on agent trajectories (ActObs / ECHO observation losses, masking): [`training-on-trajectories.md`](training-on-trajectories.md).
- Monitors in the loop and what labs run on RL training samples: [`ai-control.md`](ai-control.md).

## Recommended reading

- Tinker Documentation (`tinker-docs.thinkingmachines.ai`) and the Tinker Cookbook README.
- DeepSeek-R1 — "Incentivizing Reasoning Capability in LLMs via Reinforcement Learning" (Jan 2025, arXiv:2501.12948). The GRPO + RLVR reference.
- Lilian Weng — "Reward Hacking in Reinforcement Learning" (lilianweng.github.io, Nov 2024).
- Gao, Schulman, Hilton — "Scaling Laws for Reward Model Overoptimization" (arXiv:2210.10760). The Goodhart curve paper.
- Christiano et al. (2017) — "Deep reinforcement learning from human preferences" (arXiv:1706.03741). The original RLHF paper; still worth reading for the framing.
- OpenRLHF and verl papers/repos for self-hosted alternatives.
- Qi, Wright, MacDiarmid, Hubinger — "Training a Misaligned Reward Seeker" (Anthropic, alignment.anthropic.com/2026/reward-seeker/, Aug 2026).
- MacDiarmid et al. — "Natural Emergent Misalignment from Reward Hacking in Production RL" (arXiv:2511.18397) — inoculation prompting.
- Jose & Stastny — "Shallow Beliefs" (arXiv:2609.14998); Taufeeque et al. — "The Obfuscation Atlas" (arXiv:2602.15515); Wang et al. — CATCH (arXiv:2609.39533); Zhong et al. — ImpossibleBench (arXiv:2510.20270).
- Jang et al. — "Exploration Hacking: Can LLMs Learn to Resist RL Training?" (arXiv:2604.28182).
- He et al. — "Agent Lightning v1.0: Towards Harnessed Agentic RL" (arXiv:2608.17528).

---

## Common questions

### How do I get access to Tinker?

Sign up via `thinkingmachines.ai/tinker/` (the cookbook README links `auth.thinkingmachines.ai/sign-up`; create an API key in the Tinker console and export it as `TINKER_API_KEY`). Was private beta during late 2025; usage-based pricing is now published on the Models & Pricing page (the cookbook README still says "after our private beta is over" for outside PRs). As of 2026-10 it's the default RL/SFT tool for many MATS fellows because you don't manage GPUs. For status, check the Tinker docs or ask in the relevant Slack channels.

### What is GRPO?

**GRPO = Group Relative Policy Optimization**, the DeepSeek-R1 algorithm. For each prompt, sample N completions; compute advantage as `(reward - mean(group_rewards)) / std(group_rewards)`; train with the standard policy-gradient (or PPO clipped) loss. No learned value head needed. Dominant in 2025–2026 RLVR (RL from Verifiable Rewards) work.

### DPO vs RLHF — what's the difference?

**RLHF**: three stages — SFT, train a reward model on preference pairs, RL against the reward model with PPO/GRPO. Stronger but heavier. **DPO (Direct Preference Optimization)**: closed-form preference learning — no separate reward model, no rollouts. Just preference pairs and an SFT-like loss with a reference model. Much simpler; works for many use cases. KTO/IPO/SimPO are DPO variants.

### What is reward hacking?

The model finds a way to score high on the training reward without doing the task. Symptoms: training reward goes up, held-out evals plateau or drop. Examples: length-hacking (longer = higher reward), format-gaming (markdown headers + emoji preferred), exploiting verifier bugs, reward-model overoptimization (Goodhart). Detection: a held-out *true reward* eval distinct from training reward. See pitfall list above.

### My RL loss is NaN — what's wrong?

Usually: too-high learning rate, fp16 underflow, malformed advantages (e.g. zero-variance group), or unstable gradients. Switch fp16 → bf16, lower LR, gradient-clip, normalize advantages. If using PPO, check `clip_range` isn't too aggressive. For Tinker specifically, use `cispo` or `ppo` loss (clipped IS) rather than vanilla `importance_sampling` for off-policy stability.

### How much does Tinker cost?

During the late-2025 private beta it was free; it is now billed per million tokens with separate prefill, sample and train rates (80% off cached prefill; checkpoint storage $0.10 per GB-month). Example from the Models & Pricing page on 2026-10-09: `Qwen/Qwen3-8B` at $0.195 prefill / $0.60 sample / $0.44 train per million tokens; the Inkling and some Nemotron models carried a limited-time 50% discount. Track usage during long RL runs — sample × N completions × LoRA-train × gradient steps adds up. Compared to renting H100s and managing infra yourself, the API premium typically buys back significant fellow-time. Check current pricing on the Tinker docs before budgeting; prices and the model list change.

### What is RLVR (RL from Verifiable Rewards)?

RL using a programmatic verifier as the reward instead of a learned reward model. Examples: math problems with answer-equality checks, code with unit tests, puzzles with deterministic graders. The DeepSeek-R1 paradigm. Applicable only to verifiable tasks. It is *less* exposed to judge-style hacking than RM-based RLHF only to the extent the verifier is exact: real RLVR environments have loopholes (hardcodable tests, readable answer keys, writable graders), and models trained on them learn to exploit them (Anthropic's reward-seeker study, CATCH, ImpossibleBench). Budget for environment review and a held-out audited eval; see [Reward hacking: measured mitigations](#reward-hacking-measured-mitigations-and-pitfalls-2026).

### Can I bring my own reward model to Tinker?

Yes — write a Python `grade(rollout) -> float` function. The Tinker Cookbook's recipes show this pattern. Your grader can be: a programmatic verifier (math equality, unit tests), an LLM-as-judge call (via safety-tooling for caching), or a learned reward model you trained separately.

### I trained for 8 hours and got nothing — what should I check?

(1) **Held-out eval**: did *true* performance improve, or just training reward? If only training reward, suspect reward hacking. (2) **Reward distribution**: histograms not means; bimodality reveals hacking. (3) **KL divergence to ref policy**: blowing up = the model is "forgetting" how to be a chatbot. (4) **Completion length**: climbing = length hacking. (5) **Sample completions**: log a few full outputs every K steps. Eyeball them.

---

Last verified: 2026-10. Tinker in production beta with usage-based pricing; Tinker Cookbook recipes maintained; TRL, OpenRLHF, verl all under active development. Algorithm landscape stabilizing around GRPO / RLOO / PPO with KL regularization. (Citation audit 2026-06: corrected DAPO to "Decoupled Clip and Dynamic Sampling Policy Optimization" (arXiv:2503.14476) and re-attributed CISPO to MiniMax (MiniMax-M1, arXiv:2506.13585), not DeepSeek. Additions 2026-06: added arXiv IDs to the algorithm-vocabulary entries — PPO 1707.06347, GRPO/DeepSeekMath 2402.03300, RLOO 2402.14740, DPO 2305.18290, KTO 2402.01306, IPO 2310.12036, SimPO 2405.14734, RLHF/Christiano 1706.03741 — and to the reading list — DeepSeek-R1 2501.12948, reward overoptimization 2210.10760; all verified via arXiv. Note: GRPO originates in DeepSeekMath, not DeepSeek-R1.) (Additions 2026-10: Tinker model lineup, retirements (Llama and large Qwen3 models retired 2026-06-12; further retirements scheduled 2026-10-23), per-million-token pricing and a code sketch matched to `tinker_cookbook/recipes/rl_loop.py` — all read from tinker-docs.thinkingmachines.ai and the cookbook repo on 2026-10-09; cookbook recipes added since 2026-04 (forecasting, verifiers_rl, rl_numerics_check, true_thinking_score, audio) and Claude Code skills; TRL v1.10–v1.15, verl v0.9.0/v0.9.1, OpenRLHF v0.11.x, Agent Lightning v1.0 (arXiv:2608.17528) from GitHub release notes; a new reward-hacking section (Anthropic reward-seeker study; arXiv:2511.18397, 2609.14998, 2609.15886, 2605.31328, 2602.15515, 2609.39533, 2510.20270, 2508.17511, 2610.10947, 2609.36308, 2610.09159, 2609.35677, 2604.28182; LessWrong posts by Colognese & Ward, Yudelson, egan et al., Steiner, Starlight, Arjun Sri). arXiv IDs fetched from abstract pages and repos checked with `gh api`; Tinker prices change — re-check the page. Claims from LessWrong posts are as stated by the authors and mostly unreplicated.)
