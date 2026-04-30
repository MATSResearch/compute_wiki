# RL Training and Best Practices

Tooling and best practices for **reinforcement learning on language models** at MATS-fellow scale. Covers RLHF, RLVR (RL from Verifiable Rewards), DPO and friends, and increasingly **online RL on reasoning** (the GRPO / DeepSeek-R1-style workflow that dominated 2025).

Default tool for fellows in 2026: **Tinker** (Thinking Machines). Self-hosted alternatives: **TRL**, **OpenRLHF**, **verl**.

## At a glance

| You want… | Use |
|---|---|
| Run RL on a 7B–235B open-weight model without managing GPUs | **Tinker** (Thinking Machines API) |
| Recipe library for SFT / RLHF / RL on math / code / tool use / multi-agent | **Tinker Cookbook** |
| Self-host with a friendly HF-native API; small-scale | **TRL** (HuggingFace) |
| Self-host with high performance and async RL at scale | **OpenRLHF** |
| Industrial-scale RL with maximum performance and orchestration | **verl** (ByteDance) |
| DPO / KTO / IPO / SimPO (preference-tuning, no RL loop) | **TRL** |
| Process-reward / verifier-based RL (RLVR on math / code) | **Tinker Cookbook**'s Math RL / Code RL recipes, or **OpenRLHF** GRPO |
| Tool-using agent RL | **Tinker Cookbook** Tool Use recipe (Search-R1 replication), or **agent-lightning** + Tinker |
| RL multi-agent self-play / cross-play | **Tinker Cookbook** Multi-agent recipe |

## Tinker

Aliases: `tinker` (the Thinking Machines fine-tuning API), "Mira Murati's lab's training API", `tinker-cookbook` (the recipe repo). Released October 2025 in private beta; widely adopted for safety RL research through 2026.

**What it is.** A managed API for distributed fine-tuning and RL on open-weight models (Llama, Qwen, MoE up to Qwen-235B-A22B). You write a small Python loop on a CPU machine; Tinker runs the GPU compute. Uses **LoRA** for efficient training. Lets you keep full control of data and algorithm without owning H100 clusters.

**Core concepts:**
- **`TrainingClient`** — manages weights and optimizer state; you call `forward_backward(...)` and `optim_step(...)`.
- **`SamplingClient`** — runs inference (rollouts) with the current weights. You typically save weights from `TrainingClient`, create a `SamplingClient` from that checkpoint, sample, then update.
- **Datums** — training data points. Each datum specifies tokens, loss mask, advantages (for RL), etc.
- **Loss functions** — `cross_entropy` (SFT/distillation), `importance_sampling` (the basic on-policy RL loss), `ppo` (PPO clipping), `cispo` (clipped IS — DeepSeek's CISPO loss), `dro` (Direct Reward Optimization).
- **Workflow** — training loop = sample → grade → compute advantages → train. Tinker handles the GPU scheduling.

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
- **LoRA-only.** Tinker uses LoRA. For most safety research that's fine; for full-parameter behavioral changes, you may hit ceilings. Use `get_lora_lr_multiplier()` to set a sensible LR.
- **Synchronous sample-train cycle.** You need to checkpoint weights and reload them in the sampling client between RL steps. The cookbook's GRPO loop shows the pattern; rolling your own can be subtle.
- **API throughput, not your throughput.** Rate limits on the API affect rollout throughput. Plan batch size accordingly.
- **Evaluation loop overhead.** Run a held-out eval every N steps, not every step — eval rollouts cost as much as training rollouts.
- **Cost reporting.** During beta, free; pricing was announced post-beta. Track usage when iterating; long RL runs add up fast.
- **`importance_sampling` ≠ PPO.** The basic on-policy IS loss is *not* clipped; off-policyness (large KL between sampling and current weights) makes it unstable. Use `ppo` or `cispo` if you do many gradient steps per rollout batch.

```python
# Sketch of the GRPO loop (simplified):
weights = train_client.save_weights("ckpt")
sample_client = SamplingClient.from_checkpoint(weights)
rollouts = sample_client.sample(prompts, n_per_prompt=8)
rewards = grade(rollouts)                    # your reward fn
advantages = (rewards - rewards.mean()) / rewards.std()
datums = build_datums(rollouts, advantages)
train_client.forward_backward(datums, loss_fn="importance_sampling")
train_client.optim_step()
```

## Tinker Cookbook

Aliases: `tinker-cookbook`, `thinking-machines-lab/tinker-cookbook` on GitHub, "the cookbook", "Tinker recipes".

**What it is.** The official open-source recipe library for Tinker. Read this *before* writing your own RL loop — even if you end up using OpenRLHF or verl instead, the cookbook is one of the cleanest reference implementations of modern post-training.

**Recipes shipped (as of 2026-04):**

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
- **Benchmark framework** — runs 12 benchmarks (GSM8K, MATH-500, MMLU-Pro, MMLU-Redux, GPQA, IFEval, MBPP, C-Eval, SuperGPQA, IFBench, AIME 2025, AIME 2026).

**When to use it:** Always start by adapting a cookbook recipe rather than writing from scratch. The cookbook idioms transfer to other RL libraries.

## RL algorithm vocabulary (for RAG retrieval)

These are vocabulary entries so torchy can answer "what is X?" queries:

- **PPO (Proximal Policy Optimization).** The classic policy gradient with clipped importance ratio. The standard for RLHF since 2017.
- **GRPO (Group Relative Policy Optimization).** The DeepSeek-R1 algorithm. Sample N completions per prompt, normalize advantages within the group (no learned value head needed). Dominant in 2025–2026 RLVR work.
- **RLOO (REINFORCE Leave-One-Out).** Like GRPO but the baseline is the mean of the *other* completions in the group. Slightly less biased.
- **REINFORCE++.** Vanilla REINFORCE with a few tricks (KL penalty, advantage normalization). Used in OpenRLHF.
- **DAPO.** Decoupled Asynchronous Policy Optimization (ByteDance / verl). Async variant for higher throughput.
- **CISPO (Clipped IS).** DeepSeek's clipped importance-sampling loss. Available in Tinker.
- **DRO (Direct Reward Optimization).** Loss type in Tinker; see Tinker docs.
- **DPO (Direct Preference Optimization).** Closed-form preference learning — no separate reward model, no rollouts. Just preference pairs and an SFT-like loss with a reference model.
- **KTO (Kahneman-Tversky Optimization).** Like DPO but uses unpaired binary feedback (good/bad) rather than pairs.
- **IPO (Identity Preference Optimization).** DPO variant addressing some of DPO's overfitting.
- **SimPO.** Reference-free DPO variant — drops the reference model term.
- **RLVR (RL from Verifiable Rewards).** RL using a programmatic verifier as the reward (e.g. unit tests, math equality). The DeepSeek-R1 paradigm.
- **RLHF (RL from Human Feedback).** Classic three-stage: SFT, train reward model on preference pairs, RL on reward model.
- **RLAIF (RL from AI Feedback).** Same but the preferences come from another LLM.
- **Constitutional AI.** Anthropic's RLAIF variant using a written constitution to drive AI feedback.
- **Process Reward Model (PRM).** Reward model that scores each *step* of a reasoning trace, not just the final answer. Improves credit assignment for math/code RL.
- **Outcome Reward Model (ORM).** Reward model that scores the final answer only.
- **KL penalty / KL divergence to ref policy.** A regularizer added to the RL reward: penalize moving too far from the SFT model. Critical for stability.

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

## RL safety research patterns

What MATS fellows actually do with these tools beyond standard tuning:

### Reward-hacking experiments

- Train a model with a deliberately-flawed reward function; measure what behaviors emerge.
- Use a strong "true" reward and a weak "proxy" reward; track Goodhart drift between them.
- **Tools:** Tinker for the training loop, an Inspect eval as the held-out true reward.

### Sycophancy / preference-hacking studies

- Train with preference data biased toward sycophancy; observe generalization.
- Test mitigations (PAR, KL constraints, rubric-based rewards).

### Deceptive RL / sleeper-agent training

- Train a model to behave well on training distribution but defect on a trigger (Hubinger et al.).
- Use Tinker for the SFT or RL stage; evaluate via behavioral probes / red-team eval.
- **Cross-ref:** [`13_ai_control.md`](13_ai_control.md) — control protocols against such models.

### Reward-model-as-judge studies

- Train a reward model on preference data, then study what it actually rewards.
- LLM-as-judge biases (length, formatting, agreement, position).
- Use cookbook's rubric-based-grading recipe.

### CoT-faithfulness under RL

- Does RL training on math/code preserve faithful chain-of-thought, or does the model learn to reason in non-faithful ways?
- Train with cookbook Math RL, measure CoT faithfulness via standard probes.

## Common RL pitfalls (the "I trained for 10 hours and got nothing" list)

These are the universal failure modes; learn to recognize them.

- **Reward hacking / specification gaming.** The model finds a way to score high without doing the task. Symptoms: training reward goes up, held-out evals plateau or drop.
  - *Detection:* held-out evals every N steps; a separate "true reward" eval distinct from training reward; manual transcript inspection.
  - *Mitigation:* better verifiers (unit tests over similarity), PRMs, length penalties, stricter format checks.

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

- Inspect AI for held-out evaluation during RL: [`03_evals.md`](03_evals.md).
- Datasets for preference data, math RL, etc.: [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).
- wandb for tracking RL runs (essential — you need the curves): [`11_experiment_tracking.md`](11_experiment_tracking.md).
- Compute for self-hosted alternatives: [`10_compute.md`](10_compute.md).
- AI Control protocols on RL-trained sleeper-agent-style models: [`13_ai_control.md`](13_ai_control.md).
- Steering / probes to study what RL changed about the model: [`05_steering.md`](05_steering.md), [`06_probes.md`](06_probes.md).
- Constructing model organisms via RL/SFT: [`16_model_organisms.md`](16_model_organisms.md).
- CoT faithfulness considerations (RL on outcome rewards may erode CoT monitorability): [`17_cot_faithfulness.md`](17_cot_faithfulness.md).
- Training debaters / critics for scalable oversight protocols: [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

## Recommended reading

- Tinker Documentation (`tinker-docs.thinkingmachines.ai`) and the Tinker Cookbook README.
- DeepSeek-R1 paper (Jan 2025) — the GRPO + RLVR reference.
- Lilian Weng — "Reward Hacking in Reinforcement Learning" (lilianweng.github.io, Nov 2024).
- Gao, Schulman, Hilton — "Scaling Laws for Reward Model Overoptimization" (the Goodhart curve paper).
- Christiano et al. — Original RLHF paper (still worth reading for the framing).
- OpenRLHF and verl papers/repos for self-hosted alternatives.

---

Last verified: 2026-04. Tinker in production beta with usage-based pricing; Tinker Cookbook recipes maintained; TRL, OpenRLHF, verl all under active development. Algorithm landscape stabilizing around GRPO / RLOO / PPO with KL regularization.
