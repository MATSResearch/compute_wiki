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
- **Loss functions** — `cross_entropy` (SFT/distillation), `importance_sampling` (the basic on-policy RL loss), `ppo` (PPO clipping), `cispo` (clipped IS — MiniMax's CISPO loss, from the MiniMax-M1 paper arXiv:2506.13585), `dro` (Direct Reward Optimization).
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
- **DAPO.** Decoupled Clip and Dynamic Sampling Policy Optimization (ByteDance + Tsinghua, arXiv:2503.14476). Four techniques on top of GRPO: Clip-Higher, Dynamic Sampling, token-level policy-gradient loss, and overlong reward shaping. Implemented in verl.
- **CISPO (Clipped IS).** MiniMax's clipped importance-sampling loss (MiniMax-M1, arXiv:2506.13585) — clips the IS weight rather than the objective, so every token contributes to the update. Available in Tinker.
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
- **Cross-ref:** [`ai-control.md`](ai-control.md) — control protocols against such models.

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

- Inspect AI for held-out evaluation during RL: [`evals.md`](../evaluation/evals.md).
- Datasets for preference data, math RL, etc.: [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).
- wandb for tracking RL runs (essential — you need the curves): [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).
- Compute for self-hosted alternatives: [`compute.md`](../models-and-compute/compute.md).
- AI Control protocols on RL-trained sleeper-agent-style models: [`ai-control.md`](ai-control.md).
- Steering / probes to study what RL changed about the model: [`steering.md`](../interpretability/steering.md), [`probes.md`](../interpretability/probes.md).
- Constructing model organisms via RL/SFT: [`model-organisms.md`](../alignment-science/model-organisms.md).
- CoT faithfulness considerations (RL on outcome rewards may erode CoT monitorability): [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- Training debaters / critics for scalable oversight protocols: [`debate-scalable-oversight.md`](debate-scalable-oversight.md).

## Recommended reading

- Tinker Documentation (`tinker-docs.thinkingmachines.ai`) and the Tinker Cookbook README.
- DeepSeek-R1 paper (Jan 2025) — the GRPO + RLVR reference.
- Lilian Weng — "Reward Hacking in Reinforcement Learning" (lilianweng.github.io, Nov 2024).
- Gao, Schulman, Hilton — "Scaling Laws for Reward Model Overoptimization" (the Goodhart curve paper).
- Christiano et al. — Original RLHF paper (still worth reading for the framing).
- OpenRLHF and verl papers/repos for self-hosted alternatives.

---

## Common questions

### How do I get access to Tinker?

Sign up via `thinkingmachines.ai/tinker/`. Was private beta during late 2025; usage-based pricing was announced post-beta. As of 2026-04 it's the default RL/SFT tool for many MATS fellows because you don't manage GPUs. For status, check the Tinker docs or ask in the relevant Slack channels.

### What is GRPO?

**GRPO = Group Relative Policy Optimization**, the DeepSeek-R1 algorithm. For each prompt, sample N completions; compute advantage as `(reward - mean(group_rewards)) / std(group_rewards)`; train with the standard policy-gradient (or PPO clipped) loss. No learned value head needed. Dominant in 2025–2026 RLVR (RL from Verifiable Rewards) work.

### DPO vs RLHF — what's the difference?

**RLHF**: three stages — SFT, train a reward model on preference pairs, RL against the reward model with PPO/GRPO. Stronger but heavier. **DPO (Direct Preference Optimization)**: closed-form preference learning — no separate reward model, no rollouts. Just preference pairs and an SFT-like loss with a reference model. Much simpler; works for many use cases. KTO/IPO/SimPO are DPO variants.

### What is reward hacking?

The model finds a way to score high on the training reward without doing the task. Symptoms: training reward goes up, held-out evals plateau or drop. Examples: length-hacking (longer = higher reward), format-gaming (markdown headers + emoji preferred), exploiting verifier bugs, reward-model overoptimization (Goodhart). Detection: a held-out *true reward* eval distinct from training reward. See pitfall list above.

### My RL loss is NaN — what's wrong?

Usually: too-high learning rate, fp16 underflow, malformed advantages (e.g. zero-variance group), or unstable gradients. Switch fp16 → bf16, lower LR, gradient-clip, normalize advantages. If using PPO, check `clip_range` isn't too aggressive. For Tinker specifically, use `cispo` or `ppo` loss (clipped IS) rather than vanilla `importance_sampling` for off-policy stability.

### How much does Tinker cost?

During the late-2025 private beta it was free; usage-based pricing was announced post-beta. Track usage during long RL runs — sample × N completions × LoRA-train × gradient steps adds up. Compared to renting H100s and managing infra yourself, the API premium typically buys back significant fellow-time. Check current pricing on the Tinker docs.

### What is RLVR (RL from Verifiable Rewards)?

RL using a programmatic verifier as the reward instead of a learned reward model. Examples: math problems with answer-equality checks, code with unit tests, puzzles with deterministic graders. The DeepSeek-R1 paradigm. More resistant to reward hacking than RM-based RLHF (because the verifier is exact), but only applicable to verifiable tasks.

### Can I bring my own reward model to Tinker?

Yes — write a Python `grade(rollout) -> float` function. The Tinker Cookbook's recipes show this pattern. Your grader can be: a programmatic verifier (math equality, unit tests), an LLM-as-judge call (via safety-tooling for caching), or a learned reward model you trained separately.

### I trained for 8 hours and got nothing — what should I check?

(1) **Held-out eval**: did *true* performance improve, or just training reward? If only training reward, suspect reward hacking. (2) **Reward distribution**: histograms not means; bimodality reveals hacking. (3) **KL divergence to ref policy**: blowing up = the model is "forgetting" how to be a chatbot. (4) **Completion length**: climbing = length hacking. (5) **Sample completions**: log a few full outputs every K steps. Eyeball them.

---

Last verified: 2026-06. Tinker in production beta with usage-based pricing; Tinker Cookbook recipes maintained; TRL, OpenRLHF, verl all under active development. Algorithm landscape stabilizing around GRPO / RLOO / PPO with KL regularization. (Citation audit 2026-06: corrected DAPO to "Decoupled Clip and Dynamic Sampling Policy Optimization" (arXiv:2503.14476) and re-attributed CISPO to MiniMax (MiniMax-M1, arXiv:2506.13585), not DeepSeek.)
