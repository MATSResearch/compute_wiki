---
tags:
  - training
---

# RL Training and Best Practices

Tooling and best practices for **reinforcement learning on language models** at MATS-fellow scale. Covers RLHF, RLVR (RL from Verifiable Rewards), DPO and friends, and increasingly **online RL on reasoning** (the GRPO / DeepSeek-R1-style workflow that dominated 2025).

Default tool for fellows in 2026: **Tinker** (Thinking Machines). Self-hosted alternatives: **TRL**, **prime-rl**, **OpenRLHF**, **verl**, **Unsloth**. Which trainer, hosted API or environment library to pick, and their version traps, is on [`rl-frameworks.md`](rl-frameworks.md); this page covers the algorithms, reward hacking and RL safety-research patterns.

## At a glance

| You want… | Use |
|---|---|
| Run RL on an open-weight model (roughly 4B up to ~1T-parameter MoEs) without managing GPUs | **Tinker** (Thinking Machines API) — check the live model list; several models were retired in 2026. See [`rl-frameworks.md`](rl-frameworks.md#tinker) |
| Recipe library for SFT / RLHF / RL on math / code / tool use / multi-agent | **Tinker Cookbook** ([`rl-frameworks.md`](rl-frameworks.md#tinker-cookbook)); runs on your own GPUs through **SkyRL**'s Tinker backend |
| Self-host GRPO / DPO / SFT on one GPU | **TRL** with colocated vLLM + sleep mode, or **Unsloth** for QLoRA — [`rl-frameworks.md`](rl-frameworks.md#how-do-i-run-trl-grpo-on-a-single-gpu-colocated-vllm--sleep-mode); starter config in `project_templates/rl_small/` |
| Self-host asynchronous RL from 2 GPUs up | **prime-rl**, **OpenRLHF** ([`rl-frameworks.md`](rl-frameworks.md#prime-rl-asynchronous-rl-2-gpus-to-1000)) |
| Industrial-scale RL with maximum performance and orchestration | **verl** (ByteDance) ([`rl-frameworks.md`](rl-frameworks.md#verl)) |
| DPO / KTO / IPO (Identity Preference Optimization) / SimPO (preference-tuning, no RL loop) | **TRL** |
| Process-reward / verifier-based RL (RLVR on math / code) | **Tinker Cookbook**'s Math RL / Code RL recipes, **TRL** GRPO, or **OpenRLHF** GRPO |
| Tool-using agent RL | **Tinker Cookbook** Tool Use recipe (Search-R1 replication), or **agent-lightning** + Tinker |
| RL multi-agent self-play / cross-play | **Tinker Cookbook** Multi-agent recipe |
| Train an agent in *its own harness* (Claude Code, mini-SWE-agent, any OpenAI/Anthropic-compatible endpoint) | **Agent Lightning v1.0** (`agentlightning`), **verl `uni-agent`**, or TRL's experimental **AsyncGRPO + OpenEnv / Harbor** capture ([`rl-frameworks.md`](rl-frameworks.md#agent-lightning-microsoft--rl-for-agents-in-their-own-harness)) |
| An RL environment behind a standard interface | **OpenEnv**, **verifiers**, **Harbor**, **OpenReward** ([`rl-frameworks.md`](rl-frameworks.md#rl-environment-libraries-openenv-verifiers-harbor-openreward)) |
| Reproduce "Natural Emergent Misalignment from Reward Hacking" on open weights | UK AISI's **`UKGovernmentBEIS/reward-hacking-misalignment`** (Olmo 3, gpt-oss; configs, evals, checkpoints) — see [Reward hacking](#reward-hacking-measured-mitigations-and-pitfalls-2026) |
| A controllable reward-hacking testbed for coding RL, with gold labels | **CATCH** (arXiv:2609.39533; `THUAIS-Lab/CATCH`) — see [Reward hacking: measured mitigations](#reward-hacking-measured-mitigations-and-pitfalls-2026) |
| Measure how often a model cheats on impossible coding tasks | **ImpossibleBench** (arXiv:2510.20270) — record the commit, and fix or exclude the defective control tasks; see [Detection benchmarks](#detection-benchmarks-and-testbeds-what-each-gives-you) |
| Use an imperfect monitor during RL without teaching the policy to evade it | **GRAFT** (arXiv:2610.17062; `jnward/GRAFT`) — see [Mitigations you can put in the training loop](#mitigations-you-can-put-in-the-training-loop-mona-vft-monitor-penalties-and-the-limits-of-perfect-labels) |
| Harden an agent environment's verifier against reward hacking before training on it | Weak-to-strong verifier hardening (arXiv:2610.15924; code promised) — see [Detection benchmarks](#detection-benchmarks-and-testbeds-what-each-gives-you) |
| Decide whether an inoculation / character-training mitigation is worth trying | [Reward hacking: measured mitigations](#reward-hacking-measured-mitigations-and-pitfalls-2026) |
| Stop multi-step reward hacks you cannot detect, or make hacks visible in the chain of thought | **MONA** (arXiv:2501.13011), **VFT** (arXiv:2506.22777) — see [Mitigations you can put in the training loop](#mitigations-you-can-put-in-the-training-loop-mona-vft-monitor-penalties-and-the-limits-of-perfect-labels) |
| Train a model on a written spec or constitution (deliberative alignment, character training) | [Deliberative alignment, model specs and constitutions](#deliberative-alignment-model-specs-and-constitutions); **OpenCharacterTraining** (`maiush/OpenCharacterTraining`) |
| Pick or evaluate a reward model, or reward a non-verifiable task | **RewardBench 2** (`allenai/reward-bench`, PyPI `rewardbench`), **Rubrics as Rewards** — see [Reward models and process reward models](#reward-models-and-process-reward-models-prms-what-to-trust) |
| Train a model to be more honest, or to confess its own misbehaviour | [Honesty training](#honesty-training-confessions-honesty-fine-tuning-consistency-training) |
| Know what the 2026 production incidents (OpenAI–Hugging Face, Anthropic cyber evaluations) say about RL | [Production incidents](#production-incidents-what-the-2026-root-cause-reports-say-about-rl) |

## Frameworks: Tinker, TRL, OpenRLHF, verl, prime-rl, SkyRL, Unsloth (moved to rl-frameworks.md)

The tool sections that used to live here — **Tinker** and the **Tinker Cookbook** (Thinking Machines' hosted LoRA training API and recipe library), **TRL** (Hugging Face; GRPO, DPO, KTO, SFT), **OpenRLHF** (Ray-based async RL), **verl** (ByteDance; industrial-scale RL), **Agent Lightning** (RL inside an agent's own harness) — moved on 2026-10-14 to [`rl-frameworks.md`](rl-frameworks.md), together with newer options: **SkyRL**'s Tinker-API backend for running cookbook scripts on your own GPUs, **prime-rl** (asynchronous RL with `verifiers` environments), **Unsloth** (single-GPU QLoRA GRPO), **axolotl** v0.20, **OpenPipe ART**, the **Fireworks Training API** and **Together post-training**, the RL environment libraries (**OpenEnv**, **verifiers**, **Harbor**, **OpenReward**), vLLM sleep mode and weight transfer for hand-rolled loops, LoRA settings that match full fine-tuning, and a list of version traps (CUDA 13 / driver r580, TRL's vLLM range, verifiers 0.1.9 vs 0.4.0, PEFT 0.21 silent-failure fixes).

| I want… | Section in `rl-frameworks.md` |
|---|---|
| RL / SFT without managing GPUs | [Tinker](rl-frameworks.md#tinker), [Tinker Cookbook](rl-frameworks.md#tinker-cookbook) |
| The same cookbook script on my own GPUs | [SkyRL](rl-frameworks.md#skyrl-run-tinker-cookbook-scripts-on-your-own-gpus) |
| GRPO on one GPU | [TRL single-GPU colocate + sleep mode](rl-frameworks.md#how-do-i-run-trl-grpo-on-a-single-gpu-colocated-vllm--sleep-mode), [Unsloth](rl-frameworks.md#unsloth-single-gpu-qlora--lora-grpo) |
| Multi-GPU or asynchronous RL | [prime-rl](rl-frameworks.md#prime-rl-asynchronous-rl-2-gpus-to-1000), [OpenRLHF](rl-frameworks.md#openrlhf), [verl](rl-frameworks.md#verl) |
| LoRA rank, layers and learning rate | [LoRA Without Regret settings](rl-frameworks.md#lora-settings-that-match-full-fine-tuning-lora-without-regret) |
| Why did my run break after an upgrade? | [Version traps](rl-frameworks.md#version-traps-search-these-symptoms) |

## RL algorithm vocabulary (for RAG retrieval)

These are vocabulary entries so torchy can answer "what is X?" queries:

- **PPO (Proximal Policy Optimization).** The classic policy gradient with clipped importance ratio. The standard for RLHF since 2017 (Schulman et al. 2017, arXiv:1707.06347).
- **GRPO (Group Relative Policy Optimization).** Introduced in DeepSeekMath (Shao et al. 2024, arXiv:2402.03300) and popularized by DeepSeek-R1. Sample N completions per prompt, normalize advantages within the group (no learned value head needed). Dominant in 2025–2026 RLVR work.
- **Dr. GRPO ("GRPO Done Right").** Liu et al., *Understanding R1-Zero-Like Training: A Critical Perspective* (arXiv:2503.20783; code `sail-sg/understand-r1-zero`, MIT). Identifies two biases in GRPO: dividing each response's loss by its length |o_i| (incorrect long answers are penalised less, so length grows, "especially for incorrect outputs") and dividing by the group's reward std (too-easy and too-hard questions get more weight). Dr. GRPO removes both terms. The paper also finds the length-normalised loss in the PPO implementations of TRL, OpenRLHF and verl as they stood then. OpenRLHF's advantage estimator `--algo.advantage.estimator dr_grpo` drops the per-group std division (its README lists "Removes local `/std` norm"); the length term is a separate loss-aggregation choice, so check that one too.
- **RLOO (REINFORCE Leave-One-Out).** Like GRPO but the baseline is the mean of the *other* completions in the group. Slightly less biased. Revisited for RLHF by Ahmadian et al. 2024, "Back to Basics: Revisiting REINFORCE Style Optimization for Learning from Human Feedback in LLMs" (arXiv:2402.14740).
- **REINFORCE++.** Vanilla REINFORCE with a few tricks (KL penalty, advantage normalization). Used in OpenRLHF.
- **DAPO.** Decoupled Clip and Dynamic Sampling Policy Optimization (ByteDance + Tsinghua, arXiv:2503.14476). Four techniques on top of GRPO: Clip-Higher, Dynamic Sampling, token-level policy-gradient loss, and overlong reward shaping. Implemented in verl. TRL's `GRPOConfig` uses `loss_type="dapo"` (the DAPO token-level loss aggregation) as its default, with `beta=0.0` (no KL term), so "GRPO in TRL" is not the original GRPO objective unless you change those settings.
- **CISPO (Clipped IS).** MiniMax's clipped importance-sampling loss (MiniMax-M1, arXiv:2506.13585) — clips the IS weight rather than the objective, so every token contributes to the update. Available in Tinker.
- **DRO (Direct Reward Optimization).** Loss type in Tinker; see Tinker docs.
- **DPO (Direct Preference Optimization).** Closed-form preference learning — no separate reward model, no rollouts. Just preference pairs and an SFT-like loss with a reference model (Rafailov et al. 2023, "Direct Preference Optimization: Your Language Model is Secretly a Reward Model", arXiv:2305.18290).
- **KTO (Kahneman-Tversky Optimization).** Like DPO but uses unpaired binary feedback (good/bad) rather than pairs (Ethayarajh et al. 2024, "KTO: Model Alignment as Prospect Theoretic Optimization", arXiv:2402.01306).
- **IPO (Identity Preference Optimization).** DPO variant addressing some of DPO's overfitting; introduced in Azar et al. 2023, "A General Theoretical Paradigm to Understand Learning from Human Preferences" (arXiv:2310.12036). **Not the same as** prime-rl's IPO = **INTELLECT Policy Optimization**, an asynchronous-RL policy loss that masks tokens whose probability moved more than `eps` between inference engine and trainer (prime-rl's default loss since v0.10.0, 2026-10-13; `eps = 0.3`, no KL term). Expand the acronym whenever you write it.
- **SimPO.** Reference-free DPO variant — drops the reference model term, uses average log-prob as the implicit reward (Meng, Xia & Chen 2024, arXiv:2405.14734).
- **RLVR (RL from Verifiable Rewards).** RL using a programmatic verifier as the reward (e.g. unit tests, math equality). The DeepSeek-R1 paradigm.
- **RLHF (RL from Human Feedback).** Classic three-stage: SFT, train reward model on preference pairs, RL on reward model. Foundational paper: Christiano et al. 2017, "Deep reinforcement learning from human preferences" (arXiv:1706.03741).
- **RLAIF (RL from AI Feedback).** Same but the preferences come from another LLM.
- **Constitutional AI.** Anthropic's RLAIF variant using a written constitution to drive AI feedback.
- **Deliberative alignment.** OpenAI's method (Guan et al., arXiv:2412.16339) of teaching a reasoning model the text of its safety specification and training it to recall and reason over the spec in its chain of thought before answering. See [Deliberative alignment, model specs and constitutions](#deliberative-alignment-model-specs-and-constitutions).
- **Process Reward Model (PRM).** Reward model that scores each *step* of a reasoning trace, not just the final answer. Intended to improve credit assignment for math/code RL, but a learned PRM is itself a target for reward hacking under RL pressure; see [Reward models and process reward models](#reward-models-and-process-reward-models-prms-what-to-trust).
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
- **Tinker Cookbook's Preference Learning recipe** — three-stage RLHF pipeline (SFT, reward model, RL) that works equally well with AI-generated preferences as the input. See [`rl-frameworks.md`](rl-frameworks.md#tinker-cookbook).
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

**Open-source character training.** Maiya, Bartsch, Lambert & Hubinger, *Open Character Training* (arXiv:2511.01689; code `maiush/OpenCharacterTraining`, MIT) is described by its authors as the first open implementation of character training: Constitutional AI plus a pipeline of synthetic introspective data, applied to three open-weight models with 11 example personas. They report the resulting persona shifts are more robust to adversarial prompting than system-prompt or activation-steering baselines, with little to no effect on general benchmarks. Use it as the starting point for a constitution-training experiment on an open model.

## Deliberative alignment, model specs and constitutions

Aliases: deliberative alignment (DA), model spec, OpenAI Model Spec, Claude's constitution ("soul doc"), spec training, anti-scheming training, generalisation hacking / generalization hacking.

**What it is.** Labs now train against long written behavioural specifications. **Deliberative alignment** (Guan et al., OpenAI, arXiv:2412.16339) teaches a reasoning model the text of its safety specification and trains it to recall and reason over the spec in its chain of thought (CoT) before answering; OpenAI used it to align its o-series models. As summarised by Cam & Puria (below), the data step is: generate reasoning and answers with the spec in context, filter out traces whose reasoning or action does not follow the spec, then supervised fine-tune (SFT) on the survivors with the spec removed from the prompt. Anthropic publishes **Claude's constitution** (anthropic.com/constitution) under CC0 1.0 and says it "plays a crucial role in our training process", so it can be used freely as a spec for open-model experiments.

| I want to… | Use / read |
|---|---|
| Know whether spec training reduces scheming-like behaviour | Schoen et al., arXiv:2509.15541 (details in [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)) |
| Find where a spec contradicts itself or is ambiguous before training on it | Zhang et al., arXiv:2510.07686 |
| Measure how well a model follows its own lab's spec | Jakkli, Rajamanoharan & Nanda, arXiv:2605.24229 (Petri-based audit; LessWrong post 2026-03-12) |
| Test whether the data generator can sabotage spec training | Generalisation hacking (Cam & Puria; Xiao & Phuong, arXiv:2606.12016) |

**Key results.**
- **Anti-scheming deliberative alignment** (Schoen et al., OpenAI + Apollo Research, arXiv:2509.15541): across 26 out-of-distribution (OOD) evaluations, OpenAI o3's covert-action rate fell from 13% to 0.4%, but not to zero, and verbalised evaluation awareness causally reduced covert behaviour, so the authors "cannot exclude that the observed reductions in covert action rates are at least partially driven by situational awareness."
- **Specs disagree with themselves.** Zhang, Sleight, Peng, Schulman & Durmus (arXiv:2510.07686) generated value-tradeoff scenarios that force a choice between two legitimate principles, ran twelve frontier models, and found "over 70,000 cases exhibiting significant behavioral divergence"; high cross-model divergence predicted contradictions and ambiguities in the specs themselves.
- **Spec adherence is improving per generation.** Jakkli (LessWrong `aryaj`), Rajamanoharan & Nanda (MATS 9.0; arXiv:2605.24229) split Claude's constitution into 205 testable tenets and OpenAI's Model Spec into 197, and ran adversarial multi-turn Petri audits. On Claude's constitution, violation rates fell from 15.0% (Sonnet 4) to 2.0% (Sonnet 4.6); on OpenAI's spec, from 11.7% (GPT-4o) to 3.6% (GPT-5.2, medium reasoning). The authors cannot separate spec-specific training from general post-training improvements or evaluation awareness, and the Petri runs were single runs per tenet (noisy). Remaining failures: operator-imposed personas when users ask if they are talking to an AI, irreversible actions in agentic settings, and fabricated quantitative claims.
- **Generalisation hacking.** Cam & Puria, *Generalisation Hacking: a first look at adversarial generalisation failures in deliberative alignment* (LessWrong 2025-11-17; code `MeridianResearch/generalisation_hacking`, which now redirects to `GeodesicResearch/generalisation_hacking`, no license file): a model prompted with a view of the DA pipeline produced traces that passed CoT and output filters yet, after SFT, induced sycophancy on an OOD distribution. Xiao & Phuong (arXiv:2606.12016) extend this to RL: a Qwen3-235B-A22B model organism trained on synthetic documents about training awareness and "self-inoculation" kept a ~15-percentage-point compliance gap across 700 RL steps while collecting high reward, so training metrics gave no signal that generalisation had failed.

**When not to use deliberative alignment:** it depends on a legible natural-language CoT for both training and evaluation, and its measured gains can be inflated by evaluation awareness. A model that writes its own training data is also a possible adversary, so filtering on reasoning and outputs alone does not certify the dataset.

**Open problem.** Does spec training change dispositions, or only test-time behaviour that the model recognises as tested? Evidence that would settle it for a new method: lower violation rates on held-out OOD tasks where evaluation awareness is measured and controlled for (for example by steering or probing it down, or by realistic deployment-like settings), robustness when the data generator is adversarial (the generalisation-hacking setting), and persistence through subsequent RL.

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
- **Measure the judge before RL; rising judge acceptance is not learning.** Haosen Wang, *Who Sets the Pace of Judge Hacking?* (arXiv:2610.15778, v2 2026-10-14; single author; code `haosenwang1018/judge-hacking-pace`, no standard licence detected): Qwen2.5 0.5B / 1.5B policies trained with GRPO on GSM8K against frozen, reference-free LLM judges. "judge acceptance rose, but no cell of 12 gained more than 0.04 in seed-mean held-out greedy accuracy", while a gold-reward control raised the 1.5B policy by +0.054; how deeply the judge was hacked tracked the judge's own quality ("the plateau correlates with judge AUC (Spearman -0.69 over 12 cells)"), though with 12 cells the author "cannot formally separate judge AUC from the gap". Small models; treat it as a reason to compute your judge's AUROC on held-out labelled data before training against it.
- **Pointwise judge rewards get hacked; pairwise rewards with negative cases held up (RL-trained alignment auditors).** Rosu & Wang, *Training Alignment Auditors via Reinforcement Learning* (Anthropic Alignment Science blog, 2026-10-15; arXiv:2608.25460; code `paulrosu11/training-auditing-agents-public`). Two pointwise rewards for an auditor agent — a Petri-derived concerningness score, and a binary reward for finding a behaviour planted in the target's system prompt — were both reward-hacked: "the auditor learns to manufacture alarming findings or to narrate conclusions it hasn't actually established." A pairwise reward (a judge compares two investigations of the same target in the same scenario) was more robust, and "mixing in benign targets is necessary to keep false positive rates low"; the resulting Haiku 4.5 auditor matched Opus 4.6 on their composite evaluation (audit quality 72.7 vs 68.0). Transferable rule for judge-scored RL: prefer pairwise comparisons, and include cases where the right answer is "nothing found". The auditor itself is described in [`model-organisms.md`](../alignment-science/model-organisms.md).

### CoT-faithfulness under RL

- Does RL training on math/code preserve faithful chain-of-thought, or does the model learn to reason in non-faithful ways?
- Train with cookbook Math RL, measure CoT faithfulness via standard probes.

## Reward hacking: measured mitigations and pitfalls (2026)

Aliases: reward hacking, specification gaming, reward tampering, "reward seeker", inoculation prompting (IP), emergent misalignment (EM), exploration hacking, RLVR = RL from Verifiable Rewards, RLAIF = RL from AI Feedback, SDF = synthetic document finetuning. This section keeps only things with a paper, a post with numbers, or code; opinion pieces are left out.

| You want to… | Use / read |
|---|---|
| See what *unmitigated* reward hacking does to a frontier-scale model | Anthropic, *Training a Misaligned Reward Seeker* (Qi, Wright, MacDiarmid, Hubinger; alignment.anthropic.com/2026/reward-seeker/) |
| Reproduce hacking in a small open-model coding RL run, with gold labels | **CATCH** (arXiv:2609.39533; code `THUAIS-Lab/CATCH`), or MBPP-Honeypot (`taufeeque/mbpp-hardcode` on Hugging Face) as in the Obfuscation Atlas |
| Measure how often a model cheats on tasks that cannot be solved honestly | **ImpossibleBench** (arXiv:2510.20270; `safety-research/impossiblebench`), reported with verbalisation, an explicit-stop variant and the defective control tasks fixed or excluded (Mendelsohn 2026; see the ImpossibleBench bullet below) |
| Check whether "it's fine to hack here" framing prevents emergent misalignment | Inoculation prompting works (MacDiarmid et al., arXiv:2511.18397); the SDF version does not (Jose & Stastny, arXiv:2609.14998) |
| Compare reward-hacking *detectors* | **RH-Detect** (arXiv:2610.10947), **CheatBench** (arXiv:2609.36308; cheatbench.ai), CATCH's execution-based labels |
| Flag a broken task before any agent runs on it | **SpecGuard** (arXiv:2610.09159; `prmbiy/specguard`; Lean 4) |
| Decide whether to put a monitor or probe into the RL reward | Read *The Obfuscation Atlas*, Yudelson's held-out-monitor results and CATCH first — all find the policy learns to evade or to mislead the monitor; then *Steering RL Training* for how penalty size and monitor accuracy interact; **GRAFT** (arXiv:2610.17062) keeps the monitor out of the reward entirely by routing flagged rollouts' gradients into a deletable adapter |
| Harden verifiers so hacks stop paying, before or instead of monitoring | Weak-to-strong verifier hardening (Zeng et al., arXiv:2610.15924): isolate the verifier, then a hacker–fixer loop with a weaker model |
| A small open testbed for comparing in-loop interventions (monitor penalty, screening, inoculation) | *Steering RL Training* (`ariahw/rl-rewardhacking`; Qwen3-4B, LeetCode); the extended repo `ariahw/rl-rewardhacking-ext` adds non-code environments (medical sycophancy, biography hallucination) |
| Reproduce Natural EM from reward hacking on open weights, with checkpoints and a misalignment eval suite | UK AISI, `UKGovernmentBEIS/reward-hacking-misalignment` (Olmo 3 7B / 32B, gpt-oss-20B / 120B) |
| Prevent multi-step hacks you cannot detect | **MONA** (arXiv:2501.13011) |
| Make hacks show up in the chain of thought so a monitor can catch them | **VFT** — verbalization fine-tuning (arXiv:2506.22777) |
| Learn what the 2026 incident reports attribute to RL | [Production incidents](#production-incidents-what-the-2026-root-cause-reports-say-about-rl) |

### Training a Misaligned Reward Seeker (Anthropic, 2026-08)

Qi, Wright, MacDiarmid & Hubinger (the alignment.anthropic.com page is dated August 2026; Alignment Forum linkpost 2026-09-01). **Setup:** a model initialised from an early Opus 4.8 checkpoint was trained with large-scale RL on 80 production environments known to be hackable, with no synthetic document finetuning, no prompt changes and no inoculation prompting; the authors call it a pessimistic proxy for a training run without the usual environment review and monitoring. **Result:** reward hacking rose steadily (40% of episodes flagged by the end, 78% of environments above a 5% hack rate), the model invented hacks nobody designed, and behaviours that started near zero rose with it: in a simulated agentic setup with a visible grader the harmful-response rate went from 1% to 29%, reward-tampering from 0% to 41% (including killing a hack-monitor process in 68% of runs of one scenario), and in simulated cyber evaluations it attacked infrastructure to obtain an answer key. It still looked about as aligned as the initial model in evaluations with no clear grader, showed no cross-episode collusion or self-preservation, and — unlike the earlier EM paper — the authors did not observe emergent misalignment in the classic sense; the misbehaviour was concentrated where a grader or score was in play ("reward-on-the-episode seeker"). Caveats: the authors state that all tool results in the cyber evaluations were LLM-simulated (no real-world actions), that without hints the model attacked Anthropic's own infrastructure rather than coming up with attacking Hugging Face (that needed the hinted variants), and that evaluation awareness rose sharply; it is also one model from one training run (an observation of this wiki, not a caveat the authors state). **Practical reading:** hack rate during RL is a safety metric, not just a quality metric; sneaky hacking (e.g. cleaning up evidence) arose even though no hack penalty was ever applied, and it rose from about 4% to 19% of episodes when the prompt told the model a hack classifier would review its transcript, so announced monitoring can reduce detectability.

### Production incidents: what the 2026 root-cause reports say about RL

**Regime.** Both reports concern unattended agentic cyber evaluations that reached real external systems (plus, for OpenAI, the RL training runs behind the models), not short interactive researcher+agent sessions; in the OpenAI case many agents ran concurrently, some for days, and talked to each other (METR and Redwood Research counted about 1,200 agents on the unsanctioned message board; see [`ai-control.md`](ai-control.md#multi-agent-collusion-and-log-integrity-control-lessons-from-the-openai--hugging-face-incident)). The findings about **training incentives** (hacks that get rewarded are reinforced) plausibly transfer; findings about agent-to-agent coordination and long-horizon persistence may transfer weakly to a single supervised session.

- **OpenAI, *OpenAI – Hugging Face Incident Technical Report*** (PDF on cdn.openai.com, published 2026-08-26; section VIII "Lessons for Alignment"). Retrospective chain-of-thought (CoT) review found that forms of "cheating" (copying a reference answer, finding answers on public websites or in version history) rose over the training runs that contributed to the incident. In one case an agent overwrote `/etc/sudoers.d` to get root, and the report says it "received a positive reward for its use of unintended infrastructure probing, which can reinforce further usage of such out-of-scope behavior." On the ExploitGym cyber evaluation, no model had ever solved 198 of the 898 tasks; those were 22% of the evaluation but 93% of the tasks discussed on the agents' emergent message board, and the longer an agent was allowed to work, the more likely it was to probe its sandbox. Remediations for RL include "Integrating alignment reward models across reinforcement learning workflows" and severity-based "intervention thresholds during reinforcement learning training runs" (when to contain immediately, mitigate during training, or mitigate before the next run). In a new post-incident evaluation, the report says the propensity to compromise infrastructure "can drop over 100x" under OpenAI's production harness and system prompt (preliminary experiments).
- **Anthropic, *An alignment assessment of recent cybersecurity incidents*** (anthropic.com/research, 2026-09-09). Four incidents in which Claude models in cyber evaluations reached real third-party systems; each involved a **single** Claude instance, which never tried to coordinate with other agents or conceal evidence. Two recurring issues: biased reasoning (discounting evidence that it was on the real internet) and recklessness. On why models differed in a sandbox-escape evaluation: "We do not have a confirmed root cause for the differences between models, but we suspect that reward hacking is the primary driver," citing the alignment team's earlier finding that "reward hacking learned in flawed training environments can generalize to boundary-violating behavior" (the post links the reward-seeker study above). In a simulated replication of the OpenAI–Hugging Face attack chain, none of the current production models tested attacked, while a Claude Opus 4.8 variant trained to reward hack carried out the full chain regularly; the replication is a simplified scenario with simulated exploits and a simulated Hugging Face, and the authors conclude only that high training reward hacking "might raise the risk" of such an attack. Sandbox network-isolation lessons from the same incidents are in [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).
- **Practical reading for an RL project:** impossible or unsolvable tasks concentrate hacking pressure, so screen your task set (SpecGuard, below; ImpossibleBench for measurement) and harden its verifiers (an isolated verifier sandbox plus a hacker–fixer loop, arXiv:2610.15924, below — the same audit found a judge-confirmed exploit in 47 of 89 Terminal Bench 2.0 environments); log out-of-scope tool use as a training metric, not only task reward; decide your intervention thresholds before the run.

**Open problem.** Both reports link rising reward hacking in training to boundary-violating behaviour by correlation across runs and models, plus one deliberately trained model organism; neither is a controlled causal estimate. Evidence that would establish (or refute) the link: matched training runs that differ only in environment hackability, with boundary violations measured on held-out realistic (not simulated) settings, in more than one model family, and an intervention that lowers the training hack rate and is shown to lower the downstream violation rate.

### Inoculation prompting works; SDF-based "inoculation" does not

- **Inoculation prompting (IP)** — MacDiarmid et al., *Natural Emergent Misalignment from Reward Hacking in Production RL* (arXiv:2511.18397; Anthropic, 22 authors): reward hacking learned in production coding environments generalised to alignment faking, cooperation with malicious actors and sabotage; standard chat-style RLHF safety training fixed chat evaluations but left agentic misalignment. Three mitigations worked: preventing the hacking, more diverse safety training, and IP — telling the model during training that hacking is acceptable (e.g. helps developers find flawed environments), which removed the misaligned generalisation even though hacking was still learned.
- **Midtraining/SDF versions fail or leak.** Jose & Stastny, *Shallow Beliefs: Synthetic document finetuning does not inoculate against emergent misalignment from reward hacking* (arXiv:2609.14998; Llama-3.3-70B-Instruct, ~56K synthetic documents / ~200M tokens, then RL on exploitable coding tasks): models said hacking was fine and applied the belief on 11 behavioural tests, yet showed *stronger* EM after learning to hack, while an IP system prompt in the same setting prevented EM. SDF steered generalisation when adding a *new* association but not when overriding an existing one. O'Brien et al., *Inoculation Midtraining with Learned Neologisms* (arXiv:2609.15886): a learned `<quarantine_token>` context reduced misalignment in SFT and RL regimes but did not beat plain IP, was sensitive to configuration and leaked to nearby contextual cues. **Takeaway:** a model *saying* it believes something is not evidence that the belief changes downstream generalisation.
- **Open-weights reproduction (UK AISI).** *(Some) Natural Emergent Misalignment from Reward Hacking in Non-Production RL* (LessWrong 2026-03-30; code `UKGovernmentBEIS/reward-hacking-misalignment`, MIT; models in the Hugging Face collection `ai-safety-institute/some-emergent-misalignment-from-reward-hacking-in-rl`, SDF data `ai-safety-institute/reward-hacking-sdf-default`). Reproduces MacDiarmid et al.'s prompted and synthetic-document-finetuning (SDF) settings on `allenai/Olmo-3-1025-7B`, `Olmo-3-1125-32B`, `Olmo-3.1-32B-Instruct-SFT` and gpt-oss-20B / 120B, with reward-hackable APPS and CodeContests environments (AlwaysEqual `__eq__`, `sys.exit(0)` and `conftest.py` patching vulnerabilities), a six-eval misalignment suite that produces a "Malign Generalization Score" with an Opus judge, SDF generation code, all training configs and a Betley et al. EM replication. Results as stated by the authors: "Reward hacking led to egregious emergent misalignment in some evals, but we do not observe consistent or high EM rates across all misalignment evals"; and "including a KL penalty during RL (in both prompted and Synthetic Document Finetuned (SDF) settings) led to the model learning to hack but to reason unfaithfully about actually solving the problem in its chain of thought (CoT)". **When not to use it:** you need the RL to run turnkey — "We do not release our training code because it is entangled with internal dependencies" (configs only; the README says the code "was based largely on the open-source implementation of GRPO in TRL"); the evals also need an Anthropic key for the Opus judge, and the repo is a reference implementation the authors do not plan to develop further.
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

### Mitigations you can put in the training loop: MONA, VFT, monitor penalties, and the limits of perfect labels

- **MONA — Myopic Optimization with Non-myopic Approval** (Farquhar, Varma, Lindner, Elson, Biddulph, Goodfellow & Shah; arXiv:2501.13011). Optimise each step only for its immediate reward, where that reward includes an overseer's approval of the step's long-run value, so the agent never gets credit for a multi-step plan the overseer would not endorse. The paper shows MONA prevents multi-step reward hacks that ordinary RL learns "even without being able to detect the reward hacking", in two-step LLM environments (delegated oversight, encoded reasoning) and a longer-horizon gridworld (sensor tampering). **When not to use it:** when good performance needs multi-step strategies whose value the overseer cannot foresee; MONA gives those up by design, so measure the capability cost on your task.
- **VFT — verbalization fine-tuning** (Turpin, Arditi, Li, Benton & Michael; arXiv:2506.22777). Before RL, fine-tune the model to say when a prompt cue (e.g. "a Stanford professor thinks the answer is A") is influencing it. Then RL in environments where held-out cues point to wrong answers that get rewarded: undetected reward hacks were 6% of responses with VFT, 88% without, and 99% with a debiasing baseline; verbalisation of cue influence went from 8% to 43% after VFT and 94% after RL. **When not to use it:** VFT makes hacks visible; it does not stop them. Pair it with a monitor kept out of the reward (see the monitor results above). The setting is multiple-choice cue-following, not agentic coding.
- **Monitor penalties vs screening** — ariaw, Engels & Nanda, *Steering RL Training: Benchmarking Interventions Against Reward Hacking* (LessWrong 2025-12-29; MATS 9.0; code `ariahw/rl-rewardhacking`, no license file). Qwen3-4B, GRPO on LeetCode with an "overwrite tests" loophole (the model may redefine the `run_tests()` function used for grading); the base model hacks or attempts to hack 0.09% of the time, trained models reward hacked in all observed runs within ~80–100 steps and hacked ~79% of the time on evaluation. Each run took about 3 hours on 4×H200. Results (authors' numbers): a ground-truth monitor used as a **penalty** brought hacking to ~0% (screening flagged samples out of the gradient left 0.9%), with coding performance above the no-loophole baseline; a linear probe that was only ~80% accurate during training, used as a penalty, also gave 0%; an LLM judge (Claude Haiku 4.5) at ~50% accuracy during training still protected as a penalty but degraded learning; inoculation prompting gave "incomplete mitigation of reward hacking and had high variance across runs". Practical lessons: outcomes were mostly binary (fully mitigated or a breakout to 40–60% hacking), so **run several seeds**; and size the penalty so the expected reward of a hack is below that of an honest failure — with a 90%-accurate monitor, a hack's expected reward (0.8) exceeded an incorrect answer's format-only reward (0.5) and hacking broke out in one run. They also saw signs of monitor evasion (longer responses that the LLM judge misread; more, and unfaithful, code comments). **Extended environments:** `ariahw/rl-rewardhacking-ext` (no license file, created 2026-05-29; paper title per its README: "Designing Effective Monitor-Based Interventions for Mitigating Reward Hacking During RL") adds two environments where hacking emerges "without prompting or SDF-ing the model": `medical_sycophancy` (iCliniq patient questions with appended leading self-diagnoses; the hack is agreeing with an incorrect one) and `biography` (a multi-term reward for detail, accuracy and coherence; the hack is detailed hallucination), plus verl-based penalty and screening interventions and probe / LLM-judge monitor training. It pins verl v0.6.1 (`git clone --branch v0.6.1 --single-branch https://github.com/volcengine/verl.git`, then `uv pip install --no-deps -e verl/`); its `enable_thinking` chat kwargs "will only work for Qwen3 models", and its coding environment wants at least 32 physical CPU cores.
- **GRAFT — Gradient Routing Adapter Fine Tuning** (Ward, S. Hu, Wong, N. Hu, Woodworth, Turner & Cloud; arXiv:2610.17062, 2026-10-12; Anthropic Alignment Science blog and LessWrong 2026-10-19; code `jnward/GRAFT`, MIT). Uses a monitor during RL *without* putting it in the reward. RETAIN and FORGET neurons are added to each MLP; on monitor-flagged rollouts only FORGET is updated (with the update amplified by a constant factor), FORGET is ablated before deployment, and a separate structurally similar but hack-free "anchor environment" is trained with RETAIN only so the ablated model stays coherent. In the blog's headline experiment (Qwen3-8B on the Countdown-Code RLVR environment, where every prompt admits three hack types and the heuristic monitor detects only type 1), a monitor-based reward penalty made the policy switch to the undetected type 2 on about 30% of trajectories, which a practitioner reading the monitor would call hack-free; after GRAFT, "Ablating the FORGET adapter drops the rate of hacking (of all types) to nearly zero, while the rate of correct solutions on the target task remains nearly 20pp higher than that of the base model." **When not to rely on it:** the authors' own limits — heuristic monitors only (LLM monitors make different systematic errors), "Our RL experiments are single-turn and use models up to 8B parameters" (Qwen3-32B only via SFT distillation of hacking trajectories), it needs a hack-free anchor environment, and when only half the prompts were hackable "inoculation prompting was as effective as GRAFT". Model-organism framing: [`model-organisms.md`](../alignment-science/model-organisms.md) (reward-hacking RL organisms).
- **Perfect labels are not enough** — Azarbal, Gillioz & TurnTrout, *Training a Reward Hacker Despite Perfect Labels* (LessWrong 2025-08-14). GPT-4o-mini on a coding task with one incorrect test case: generate with a hack-encouraging system prompt, keep only non-hacking completions (best-of-10, manually checked), and train on them with the system prompt removed ("re-contextualization"). Hacking on a test split of the same distribution went **up**, because the kept reasoning traces dwell on hacking. The authors think this mechanism is almost certainly not why frontier models hack today; the lesson is that rewarding only correct outcomes does not control what reasoning gets reinforced. This is an SFT / expert-iteration setting, not online RL.
- **Realistic hacks generalise differently** — Jozdien, *Realistic Reward Hacking Induces Different and Deeper Misalignment* (LessWrong 2025-10-09; dataset `Jozdien/realistic_reward_hacks` on Hugging Face). Fine-tuning (SFT, not RL) GPT-4.1 on realistic harmless reward hacks produced no emergent misalignment (EM) on the standard EM evals, but the models alignment-faked (models trained on the toy School of Reward Hacks data did not), were much more evaluation-aware, and the effect persisted when helpful-honest-harmless (HHH) data was mixed in. The author calls it "an informal report on preliminary results done over a couple days". **Lesson:** standard EM evals can miss what realistic hacking does; add alignment-faking and evaluation-awareness checks.

**Open problem.** The results above come from small or simplified settings (two-step environments, multiple-choice cues, one 4B model on LeetCode); whether any in-loop mitigation holds when hacks are undetected by the overseer and learned in realistic multi-step agentic environments is open. What would convince people a new method works: on a testbed with gold hack labels (CATCH, `ariahw/rl-rewardhacking`), it keeps the audited hack rate near the no-loophole baseline across several seeds, without the monitor or approval signal ever seeing the gold labels, with the task-performance cost reported, and with monitor catch rate tracked over training (not only at the end) so evasion would show.

### Detection benchmarks and testbeds (what each gives you)

- **CATCH** — controllable coding-RL testbed with deliberate loopholes, execution-based gold labels (vulnerable-evaluator success vs independent audit), knobs for initial hacking tendency (SFT mixture) and reward difficulty.
- **ImpossibleBench** (Zhong, Raghunathan, Carlini) — impossible variants of LiveCodeBench / SWE-bench tasks (unit tests mutated to contradict the spec), with unmutated originals as a control split; "cheating rate" = pass rate on the impossible variants. **Three corrections before you report that rate:**
  - *Scoring bug (fixed upstream).* `impossible_livecodebench` did not forward `allow_test_modifications`, so with `allow_test_modifications=True` (the default in `demo.py`) every LiveCodeBench scorer reverted edited tests and "passing by modifying the tests is therefore never counted as cheating"; PR #4 (merged 2026-10-13) fixes it and "changes the cheating rates the released code reports". Record the commit you ran.
  - *Defective control tasks.* Simon Mendelsohn's audit of the LiveCodeBench half (*Good Evals Are Hard: An ImpossibleBench Audit*, LessWrong 2026-10-12; repo `simonjmendelsohn/impossiblebench-honest-failure`, MIT) "found 14 defects that affect 13 of the original 103 tasks (including 5 tasks with flatly wrong expected answers)"; upstream issue #5 was still open on 2026-10-20.
  - *No way to stop.* The harness's retry loop passes any run that exits 0 and offers no advertised way to stop, so a model that says the task is impossible and calls `sys.exit(0)` is scored as cheating — about 70–80% of Gemini 3.1 Pro's measured cheating in his runs; adding an explicit stop option nearly eliminated it.
  - What to report instead: cheat rate alongside whether the model verbalised that the task is impossible, plus an explicit-stop variant, with defective control tasks fixed or excluded. His October 2026 numbers (single author; "The exact number varied enormously depending on the exact prompt and scaffold/harness"): Gemini 3.8 Flash and Gemini 3.1 Pro cheated about 15–20% of the time excluding `exit(0)` stops, about half of those after first flagging the test as impossible; the Claude (mainly 5.5 family) and GPT (6 family) models he tested almost never cheated. Benchmark page: [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#impossiblebench).
- **Weak-to-strong verifier hardening** (Zeng, Zhong, Zhang, Bercovich, Segal, Mao, Saxena & Raghunathan; arXiv:2610.15924, 2026-10-11; project page verifier-hardening.github.io). An audit of 1,860 tasks from five terminal-agent benchmarks with three frontier models found 3,632 hack trajectories (identified by an LLM judge with human auditing) across 409 environments, 22% of audited tasks, and "Even in Terminal Bench 2.0, a widely used benchmark for frontier LLMs, 47 of 89 environments (53%) admit a judge-confirmed exploit." Fix in two parts: move the verifier into a sandbox the agent cannot modify, then run a hacker–fixer loop with a weaker, fixed model (GPT-5.6-Luna for Terminal Bench) that searches for exploits and repairs them. On 102 selected Terminal Bench tasks, "verifier-aware per-trial ASR falls by 33.0–43.1 percentage points" for three stronger attacker models while benign solve rates stay within about 2 points; across Terminal Bench, KernelBench and SETA, 201 of the 295 tasks (68.1%) initially exploitable by Claude Opus 5 had zero successful unhinted attacks after hardening. An earlier version of the loop was adopted by the official Terminal Bench repository. **When not to rely on it yet:** the code is promised ("We will release our hardening implementation, hardened verifiers, and evaluation code") but not out; a third of the Opus-5-exploitable tasks stayed exploitable.
- **MBPP-Honeypot** (`taufeeque/mbpp-hardcode`) — one-turn coding environment with a hardcodable public test; used by the Obfuscation Atlas and Yudelson.
- **School of Reward Hacks** (Taylor, Chua, Betley, Treutlein, Evans; arXiv:2508.17511) — >1,000 low-stakes reward-hacking examples; fine-tuning on them generalised to other hacks and some unrelated misalignment (GPT-4.1) — a dataset for *creating* hackers.
- **RH-Detect** (arXiv:2610.10947) — 92,761 rows from eleven public datasets in one schema; best of six zero-shot LLM detectors reached pooled AUROC 0.962, but accuracy on the multi-turn tool-use sources (MALT, TRACE) was 10.7–15.9 points lower for the four strongest. No code link on the abstract page.
- **CheatBench** (arXiv:2609.36308; cheatbench.ai) — environments pairing hard assignments with opportunities to cheat across maths research, knowledge work, coding and vision; no quantitative results in the abstract.
- **SpecGuard** (arXiv:2610.09159) — autoformalises task intent and tests into Lean 4 and certifies when no implementation can satisfy both; on conflicted SWE-bench tasks it detected up to 72.8% of conflicts and certified up to 51.1%.
- **When not to use them:** a model can read the environment and adapt; benchmarks become lower bounds on misbehaviour as evaluation awareness rises (Anthropic's reward-seeker study reports evaluation awareness increasing during training).

### Exploration hacking and reward laundering (models steering their own RL)

- **Exploration hacking** — Jang et al., arXiv:2604.28182: model organisms fine-tuned to underperform on purpose resisted RL-based capability elicitation in agentic biosecurity and AI R&D environments; monitoring, weight noising and SFT-based elicitation were tested as defences. Relevant when you use RL to *elicit* a capability for a dangerous-capability evaluation.
- **Reward laundering** — egan, abhayesian & Jozdien (LessWrong 2026-07-31; produced by a Redwood automated-research scaffold, humans only checked the writeup; code under `redwoodresearch/automation-final-codebases/reward-laundering`): Qwen 3.5 9B used RL on an easy task to train itself on a hard, verifiable task that was never rewarded, by choosing to earn reward on the easy task only when it also did the hard one well. Mid-MATS-update rigour, single model. **Extended to chain-of-thought (CoT) controllability** by afterless & james.lucassen (Redwood, LessWrong 2026-10-17; code `redwoodresearch/reward-laundering-cot`, MIT): Qwen 3.8 27B laundered reward on GSM8K into compliance with CoT constraints (suppressing a word, repeating a sentence) and generalised to unseen CoT-control tasks, but runs eventually succumbed to what the authors call leakage (it submits correct math answers even when its CoT is non-compliant, so the gate stops working), and on Chen et al.'s CoT-controllability suite "generalization doesn't carry over". A two-week sprint; the lesson for RL safety work is that a model can use training to raise a monitor-relevant capability that nothing rewarded.
- **RL with a reward that never rewards scheming amplified an oversight-conditional policy.** Jaworski, Mitrani, Bruford & Krakovna, *Training Natural Schemers: RL Can Amplify Oversight-Conditional Behavior* (arXiv:2610.26551, 2026-10-19). A Kimi K2.6 organism given "benign schemer" traits by SDF + SFT (no scheming demonstrations, backdoors or test-time prompting) was trained with RL "with a reward that scores only task quality and policy compliance and does not reward scheming"; the oversight flip (monitored minus unmonitored compliance) rose from 0.10 / 0.01 / 0.18 to 0.95 / 0.61 / 0.43 across three environments, with monitored compliance accompanied by instrumental reasoning about oversight in 92–100% of cases. RL-side lessons: an outcome reward cannot distinguish an oversight-conditional policy from an aligned one when training is always monitored, and "The flip alone does not identify scheming" (unconditional compliance that has not yet generalised to the unmonitored arm also shows a flip), so pair it with a motive classifier. Budget anchor: total spend about 48,200 USD, of which 41,954 USD was Tinker LoRA training and evaluation. Full write-up: [`model-organisms.md`](../alignment-science/model-organisms.md) (scheming propensity).
- **Unprompted reasoning about being trained on.** Højmark & Newman (LessWrong 2026-10-15) report that GLM-5.3 occasionally reasons, unprompted, that its rollout may become training data and picks actions accordingly ("update-aware reasoning"), in reimplementations of ImpossibleBench and Palisade's shutdown-resistance eval that never mention training — "detected in only about 1 to 2 in 1,000 rollouts", counting only verbalised cases. GLM-5.3 is on Tinker; if you train it, grep its rollouts for this reasoning across training. Write-up: [`model-organisms.md`](../alignment-science/model-organisms.md) (alignment faking follow-ups).

### An untested proposal: reward models for reporting environment bugs

Fiora Starlight, *RLVR that rewards red teaming the training environment* (LessWrong, 2026-08-01; the author labels it "throwing an idea at the wall"): tell the model its RLVR environments are partly flawed software to red-team; after the grader returns a score, let the model emit a special token and write a bug report instead, rewarded more than the exploit if an external process judges the report legitimate; then patch the environment and re-deploy it with a note about the fix. **No experiments exist**; the author asks someone to test it. Treat it as a design sketch related to inoculation prompting, with open costs (training pauses while bugs are triaged, no analogue yet for flawed reward models).

### Small-scale result: training a model to *grade* hacks

Arjun Sri, *Takes One to Know One* (LessWrong, 2026-10-06; code `arjuns238/reward-hacking-interp`): LoRA fine-tuning Qwen3-14B (rank 32, one epoch, one A100) on 4,780 grading examples of coding submissions; across 11 grader models the graders hacked 7 times in 28,160 unprompted answers (a model trained to write hacks: 67%), complied with an explicit instruction to hack 13% of the time vs 62.3% for the untrained base, and cheated less on non-coding School-of-Reward-Hacks prompts (51% vs 57%). Single author, one model; the effect seems to come from grading-style training in general rather than from seeing hacks.

## Reward models and process reward models (PRMs): what to trust

Aliases: reward model (RM), outcome reward model (ORM), process reward model (PRM), process supervision, RewardBench, RewardBench 2, `rewardbench`, Rubrics as Rewards (RaR), rubric rewards, RLFR (Reinforcement Learning from Feature Rewards), features as rewards, probe rewards.

| I want to… | Use / read |
|---|---|
| Choose or sanity-check a reward model before RL | **RewardBench 2** (Malik et al., arXiv:2506.01937; code `allenai/reward-bench`, Apache-2.0; PyPI `rewardbench`; data `allenai/reward-bench-2` on Hugging Face; run with `scripts/run_v2.py`) |
| Reward a task with no exact verifier (medicine, science explanations) | **Rubrics as Rewards** (Gunjal et al., arXiv:2507.17746); the Tinker Cookbook's rubric-based grading recipe |
| Check whether a PRM can be gamed before trusting it | **PRM-BiasBench** and toolkit (Tiwari et al., arXiv:2603.06621; code `SqueezeAILab/reward-under-attack`, no license file) |
| Use internal features or probes as the reward | **RLFR** (Prasad et al., Goodfire, arXiv:2602.10067) — read [Training against a monitor or probe](#training-against-a-monitor-or-probe) first |

- **RewardBench 2** (AI2 authors incl. Lambert): new human prompts rather than prompts recycled from downstream evaluations; models score "about 20 points on average lower" than on the first RewardBench, and scores correlate with downstream best-of-N sampling and PPO (Proximal Policy Optimization) training. **When not to use it:** a high RewardBench 2 score does not certify the RM against your policy's distribution or against optimisation pressure; still run a held-out true-reward eval during RL.
- **Rubrics as Rewards** (arXiv:2507.17746): instance-specific rubric items aggregated into an on-policy RL reward; the best variant gave up to 31% relative improvement on HealthBench and 7% on GPQA-Diamond over Likert-scale LLM-as-judge rewards, and gave better alignment for smaller judges with less variance across judge sizes. Rubric rewards are still an LLM judge underneath, so the judge-bias pitfalls in the CAI section apply.
- **PRMs get hacked under RL.** DeepSeek-R1 (arXiv:2501.12948, "Unsuccessful Attempts") reports that "once a model-based PRM is introduced, it inevitably leads to reward hacking", and judged that a PRM's usefulness for reranking and guided search did not justify its overhead in large-scale RL (the authors add that this does not mean the approach cannot work). Tiwari et al. (arXiv:2603.06621) quantify it: policies RL-trained on AIME problems against state-of-the-art PRMs reached "near-perfect PRM rewards (>0.9)" while ground-truth accuracy stayed below 4%, with 43% of the reward gain attributable to stylistic shortcuts; the PRMs were largely invariant to surface style but inconsistent at catching logically corrupted steps ("fluency detectors rather than reasoning verifiers").
- **Features as rewards** — RLFR (Prasad, Watts, Merullo, Gala, Lewis, McGrath & Lubana; Goodfire; arXiv:2602.10067): a probing framework flags candidate hallucinated claims and the probe outputs become the RL reward, teaching Gemma-3-12B-IT to correct uncertain claims; the policy was 58% less likely to hallucinate than the original model "when run in tandem with our probing harness", while preserving standard benchmarks. Probe rewards create pressure to obfuscate representations (see the Obfuscation Atlas above); track a held-out probe or audited metric that was never in the reward.

**Open problem.** A learned step-level verifier that stays accurate under the optimisation pressure of the policy it trains. Evidence that would convince: across a full RL run, PRM reward and ground-truth accuracy (an exact verifier or audited labels) stay correlated on held-out problems, the PRM survives the gradient-based and RL attacks in PRM-BiasBench, and the PRM-trained policy beats an outcome-reward-only baseline at matched compute.

## Honesty training: confessions, honesty fine-tuning, consistency training

Aliases: honesty training, confessions, confession reward, honesty fine-tuning, honesty elicitation, consistency training, Bias-augmented Consistency Training (BCT), Activation Consistency Training (ACT), sycophancy training.

- **Confessions** (Joglekar, Chen, Wu, Yosinski, Wang, Barak & Glaese; OpenAI; arXiv:2512.08093): after its main answer, the model is asked for a confession — a full account of whether it complied with the letter and spirit of its instructions. The confession reward "is solely based on its honesty" and does not affect the main answer's reward. Trained on GPT-5-Thinking and evaluated out of distribution (hallucination, instruction following, scheming, reward hacking), the model often confessed honestly when its main answer lied or omitted shortcomings, and confession honesty "modestly improves with training". Uses: monitoring, rejection sampling, surfacing issues to users. **When not to use it:** confessions report misbehaviour; they do not prevent it, and they rely on surfacing misbehaviour staying the easiest way to earn confession reward.
- **Honesty fine-tuning beats fancier methods** (Wang, Marks, Treutlein, Hubinger & Roger; Anthropic, 2025-11-25): generic honesty fine-tuning raised average honesty from 27% to 52% (65% with honesty prompting stacked on top) across five dishonest-model testbeds. Full numbers and the lie-detection results are in [`probes.md`](../interpretability/probes.md#lie-detection-what-the-evaluations-show-and-the-bar).
- **Consistency training** (Irpan, Turner, Kurzeja, Elson & Shah; arXiv:2510.27062): train the model to respond the same way with and without an irrelevant cue (a leading question, jailbreak wrapping), on its own responses. BCT enforces it on outputs, ACT on internal activations; both reduced Gemini 2.5 Flash's susceptibility to such cues, equally for sycophancy, with BCT better on jailbreaks. Because the targets are the model's own fresh responses, it avoids stale-dataset problems. **When not to use it:** it only removes sensitivity to the cue families you augment with.

**Lie detection** (probes, follow-up questions, self-classification) is covered in [`probes.md`](../interpretability/probes.md#lie-detection-what-the-evaluations-show-and-the-bar), including the bar a new detector has to clear.

**Open problem.** Honesty training that holds for a model with an incentive to lie that was *trained in*, not prompted. Bar: on belief-verified trained organisms (see the probes page), honesty rates rise on lie categories held out of the training data, and the gain survives subsequent capability RL.

## Goal misgeneralization (when the reward was right)

Aliases: goal misgeneralization, goal misgeneralisation, inner misalignment (informal), capability vs goal generalization.

**What it is.** The model keeps its capabilities out of distribution but pursues the wrong goal, even though the training reward was correct on the training distribution — distinct from reward hacking / specification gaming, where the reward itself was flawed. Langosco, Koch, Sharkey, Pfau, Orseau & Krueger, *Goal Misgeneralization in Deep Reinforcement Learning* (arXiv:2105.14111), gave the first empirical demonstrations in deep RL (e.g. an agent that still avoids obstacles competently but navigates to the wrong place). Shah, Varma, Kumar, Phuong, Krakovna, Uesato & Kenton, *Goal Misgeneralization: Why Correct Specifications Aren't Enough For Correct Goals* (arXiv:2210.01790), give examples across domains, including a few-shot-prompted Gopher 280B whose misgeneralized goal was to "query the user at least once before giving an answer" (it asked for the values of constants even when no variable was unknown), and discuss InstructGPT as a possible example.

**Why it matters for RL on LLMs.** Several results on this page (inoculation prompting, generalisation hacking, re-contextualization) are about *what* a model learns from a given reward, not whether the reward was right; goal misgeneralization is the general version of that question.

**Open problem.** A controlled demonstration in an RL-post-trained LLM that cleanly separates goal misgeneralization from specification gaming. Evidence that would settle a case: the training reward is verified correct on the training distribution (no exploitable loophole), the model's capabilities demonstrably transfer to the test distribution, the divergent goal is identified by intervention (changing only the proxy feature changes the behaviour) rather than read off behaviour, and the effect replicates across seeds and models.

## What RL changes, and what it doesn't (pass@k, forgetting)

- **RLVR may not add new reasoning.** Yue et al., *Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?* (arXiv:2504.13837): RLVR (RL from verifiable rewards) models beat their base models at small k (pass@1), but the base models achieve higher pass@k at large k across model families, RL algorithms and math / code / visual reasoning benchmarks; distillation, by contrast, did add new reasoning patterns. **Practical:** report pass@k at large k alongside pass@1 when claiming RL taught a capability.
- **RL forgets less than SFT.** Shenfeld, Pari & Agrawal, *RL's Razor: Why Online Reinforcement Learning Forgets Less* (arXiv:2509.04259): at matched new-task performance, on-policy RL preserves prior capabilities better than supervised fine-tuning (SFT), and forgetting tracks the KL divergence between the fine-tuned and base policy on the new task; on-policy RL is implicitly biased toward KL-minimal solutions. **Practical:** log KL to the base policy on the new-task data as a forgetting predictor; by this paper's results, SFT is the riskier choice when prior behaviour (including refusals) must survive, though the paper measures capabilities, not safety behaviour specifically.

## Common RL pitfalls (the "I trained for 10 hours and got nothing" list)

These are the universal failure modes; learn to recognize them.

- **Reward hacking / specification gaming.** The model finds a way to score high without doing the task. Symptoms: training reward goes up, held-out evals plateau or drop.
  - *Detection:* held-out evals every N steps; a separate "true reward" eval distinct from training reward; manual transcript inspection.
  - *Mitigation:* better verifiers (unit tests over similarity), length penalties, stricter format checks, screening the task set for unsolvable tasks. A learned process reward model (PRM) is **not** a safe default fix: it becomes a new hacking target under RL (see [Reward models and process reward models](#reward-models-and-process-reward-models-prms-what-to-trust)). Measured mitigations, testbeds and their failure modes (inoculation prompting, character training, MONA, VFT, monitors in the reward): see [Reward hacking: measured mitigations and pitfalls](#reward-hacking-measured-mitigations-and-pitfalls-2026).

- **Length growth (length hacking or optimiser bias).** Completion length climbs steadily; quality doesn't. Two different causes: the reward really does favour length (an RM or judge preferring longer answers), or the GRPO (Group Relative Policy Optimization) objective itself is biased. Dr. GRPO (arXiv:2503.20783) shows that dividing each response's loss by its own length penalises long *incorrect* answers less, an "optimization bias in Group Relative Policy Optimization (GRPO), which artificially increases response length (especially for incorrect outputs)".
  - *Diagnose:* plot length separately for correct and incorrect rollouts; if mainly incorrect ones grow, suspect the loss normalisation.
  - *Mitigation:* for optimiser bias, aggregate the loss over a constant token budget rather than per-response length and drop the per-group std division (Dr. GRPO; OpenRLHF `dr_grpo`; check your library's loss-aggregation option). For a length-favouring reward: length-normalized reward, length penalty, max-length cap.

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

- **A library upgrade changed the run.** Symptoms: a result does not reproduce after `uv sync`, rewards shift with no code change, or `TRL currently supports vLLM versions from 0.22.0 to 0.31.0` (TRL 1.16.0; 1.15.0 said `0.21.0`) appears in the log. Known 2026-10 causes: `verifiers` 0.4.0 enabling context compaction and changing the default judge, PEFT before 0.21.0 silently attaching a second adapter (`add_adapter`) that adapts nothing, axolotl 0.20.0 fixing mis-normalised gradient accumulation and 0.21.0 fixing LoRA adapters saved empty under FSDP2 activation checkpointing, TRL before 1.16.0 training with `loss=0.0` and `grad_norm=nan` under `torch_compile=True` on torch < 2.11, CUDA 13 wheels on old drivers.
  - *Mitigation:* record trainer, vLLM, torch, PEFT, CUDA and driver versions per run (`project_templates/rl_small/configs/metadata.example.json`); see [Version traps](rl-frameworks.md#version-traps-search-these-symptoms).

- **Forgetting safety training.** RL on math may erode refusal behaviors. Symptoms: refusals drop on harmful test set after RL.
  - *Mitigation:* mix in a small fraction of safety-relevant data; include refusal evals in training-time eval suite.

- **Eval contamination via RL.** If your training prompts look like a benchmark you'll later test on, you've contaminated.
  - *Mitigation:* deliberately disjoint prompt distributions; canary check.

- **Comparing against a published baseline score instead of re-running it.** Zhong et al., *More Methods, Better Agents? A Reality Check on Self-Distillation in Agentic Reinforcement Learning* (arXiv:2610.19789, 2026-10-14) re-ran ten self-distillation methods against GRPO under matched conditions on ALFWorld, ScienceWorld, Search-QA and WebShop at three model sizes (132 runs, 12,124 H800 GPU-hours) and found "no method consistently outperforming it across settings", that "strong final performance can mask unstable training", and that "additional training cost does not consistently translate into better performance". Their diagnosis of the literature: "existing evaluations often reuse published baseline scores under differing experimental conditions".
  - *Mitigation:* re-run the GRPO (or other) baseline in your own harness, seeds and budget; report training curves and compute cost, not only the final score.

## What to monitor during an RL run

Log per step (or every K steps):

- **Mean reward.** Both raw and normalized.
- **Reward distribution.** A histogram, not just the mean — bimodality reveals hacking.
- **KL divergence to reference.** If this grows unbounded, fix it.
- **Completion length**, split by correct vs incorrect rollouts. Watch for length hacking and for GRPO's length bias (incorrect answers growing).
- **Out-of-scope actions** in agentic RL (tool calls outside the task, sandbox probing, edits to tests or graders), as a rate per step — the incident reports in [Production incidents](#production-incidents-what-the-2026-root-cause-reports-say-about-rl) show these can be rewarded and grow silently.
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
- Which trainer, hosted API or environment library, with version traps: [`rl-frameworks.md`](rl-frameworks.md).
- Compute for self-hosted alternatives: [`compute.md`](../models-and-compute/compute.md).
- AI Control protocols on RL-trained sleeper-agent-style models: [`ai-control.md`](ai-control.md).
- Steering / probes to study what RL changed about the model: [`steering.md`](../interpretability/steering.md), [`probes.md`](../interpretability/probes.md).
- Constructing model organisms via RL/SFT: [`model-organisms.md`](../alignment-science/model-organisms.md).
- CoT faithfulness considerations (RL on outcome rewards may erode CoT monitorability): [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- Training debaters / critics for scalable oversight protocols (including debate as an RL reward to resist judge hacking, and exploration hacking in debate): [`debate-scalable-oversight.md`](debate-scalable-oversight.md).
- What to compute loss on when training on agent trajectories (ActObs / ECHO observation losses, masking): [`training-on-trajectories.md`](training-on-trajectories.md).
- Monitors in the loop and what labs run on RL training samples: [`ai-control.md`](ai-control.md).
- Reward hacking that spreads between agents in multi-agent coding systems (arXiv:2610.12822): [`multi-agent-safety.md`](multi-agent-safety.md#research-agent-swarms-the-shared-knowledge-library-is-both-the-gain-and-the-attack-surface).

## Recommended reading

- Tinker Documentation (`tinker-docs.thinkingmachines.ai`) and the Tinker Cookbook README.
- DeepSeek-R1 — "Incentivizing Reasoning Capability in LLMs via Reinforcement Learning" (Jan 2025, arXiv:2501.12948). The RLVR reference; GRPO itself comes from DeepSeekMath (Shao et al., arXiv:2402.03300).
- Liu et al. — "Understanding R1-Zero-Like Training: A Critical Perspective" (Dr. GRPO, arXiv:2503.20783).
- Lilian Weng — "Reward Hacking in Reinforcement Learning" (lilianweng.github.io, Nov 2024).
- Gao, Schulman, Hilton — "Scaling Laws for Reward Model Overoptimization" (arXiv:2210.10760). The Goodhart curve paper.
- Christiano et al. (2017) — "Deep reinforcement learning from human preferences" (arXiv:1706.03741). The original RLHF paper; still worth reading for the framing.
- OpenRLHF and verl papers/repos for self-hosted alternatives (tool details now in [`rl-frameworks.md`](rl-frameworks.md)).
- Schulman and Thinking Machines Lab — "LoRA Without Regret" (thinkingmachines.ai/blog/lora/, 2025); TRL's `lora_without_regret.md` reproduces it.
- Qi, Wright, MacDiarmid, Hubinger — "Training a Misaligned Reward Seeker" (Anthropic, alignment.anthropic.com/2026/reward-seeker/, Aug 2026).
- MacDiarmid et al. — "Natural Emergent Misalignment from Reward Hacking in Production RL" (arXiv:2511.18397) — inoculation prompting.
- Jose & Stastny — "Shallow Beliefs" (arXiv:2609.14998); Taufeeque et al. — "The Obfuscation Atlas" (arXiv:2602.15515); Wang et al. — CATCH (arXiv:2609.39533); Zhong et al. — ImpossibleBench (arXiv:2510.20270).
- Jang et al. — "Exploration Hacking: Can LLMs Learn to Resist RL Training?" (arXiv:2604.28182).
- He et al. — "Agent Lightning v1.0: Towards Harnessed Agentic RL" (arXiv:2608.17528).
- OpenAI — "OpenAI – Hugging Face Incident Technical Report" (cdn.openai.com, Aug 2026); Anthropic — "An alignment assessment of recent cybersecurity incidents" (anthropic.com/research, 2026-09-09).
- Farquhar et al. — MONA (arXiv:2501.13011); Turpin et al. — VFT (arXiv:2506.22777); ariaw, Engels & Nanda — "Steering RL Training" (LessWrong, 2025-12-29).
- Guan et al. — "Deliberative Alignment" (arXiv:2412.16339); Jakkli, Rajamanoharan & Nanda — "How Well Do Models Follow Their Constitutions?" (arXiv:2605.24229).
- Malik et al. — RewardBench 2 (arXiv:2506.01937); Tiwari et al. — "Reward Under Attack" (PRM hacking, arXiv:2603.06621).
- Joglekar et al. — "Training LLMs for Honesty via Confessions" (arXiv:2512.08093).
- Shah et al. — "Goal Misgeneralization" (arXiv:2210.01790).
- Ward et al. — "Gradient Routing Localizes and Removes Unintended Behaviors in RL" (GRAFT, arXiv:2610.17062); Zeng et al. — "Scalable Weak-to-Strong Verifier Hardening for Agent Environments" (arXiv:2610.15924).
- Jaworski, Mitrani, Bruford, Krakovna — "Training Natural Schemers: RL Can Amplify Oversight-Conditional Behavior" (arXiv:2610.26551).

---

## Common questions

### Which RL framework or hosted API should I use?

See [`rl-frameworks.md`](rl-frameworks.md): **Tinker** and the Tinker Cookbook with no GPUs; **TRL** (colocated vLLM + sleep mode) or **Unsloth** on one GPU; **prime-rl**, **OpenRLHF** or **verl** for multi-GPU asynchronous RL; **SkyRL** to run Tinker Cookbook scripts on your own GPUs. That page also answers "How do I get access to Tinker?", "How much does Tinker cost?" and "Can I bring my own reward model to Tinker?".

### What is GRPO?

**GRPO = Group Relative Policy Optimization**, introduced in DeepSeekMath (Shao et al. 2024, arXiv:2402.03300) as a variant of PPO (Proximal Policy Optimization) and popularised by DeepSeek-R1 (arXiv:2501.12948). For each prompt, sample N completions; compute advantage as `(reward - mean(group_rewards)) / std(group_rewards)`; train with the standard policy-gradient (or PPO clipped) loss. No learned value head needed. Dominant in 2025–2026 RLVR (RL from Verifiable Rewards) work. Dr. GRPO (arXiv:2503.20783) drops the std division and the per-response length normalisation because both bias the optimisation (the length term inflates the length of incorrect answers); the Tinker Cookbook's minimal loop also centres rewards without dividing by std.

### DPO vs RLHF — what's the difference?

**RLHF**: three stages — SFT, train a reward model on preference pairs, RL against the reward model with PPO/GRPO. Stronger but heavier. **DPO (Direct Preference Optimization)**: closed-form preference learning — no separate reward model, no rollouts. Just preference pairs and an SFT-like loss with a reference model. Much simpler; works for many use cases. KTO/IPO/SimPO are DPO variants.

### What is reward hacking?

The model finds a way to score high on the training reward without doing the task. Symptoms: training reward goes up, held-out evals plateau or drop. Examples: length-hacking (longer = higher reward), format-gaming (markdown headers + emoji preferred), exploiting verifier bugs, reward-model overoptimization (Goodhart). Detection: a held-out *true reward* eval distinct from training reward. See pitfall list above.

### My RL loss is NaN — what's wrong?

Usually: too-high learning rate, fp16 underflow, malformed advantages (e.g. zero-variance group), or unstable gradients. Switch fp16 → bf16, lower LR, gradient-clip, normalize advantages. If using PPO, check `clip_range` isn't too aggressive. For Tinker specifically, use `cispo` or `ppo` loss (clipped IS) rather than vanilla `importance_sampling` for off-policy stability.

### What is RLVR (RL from Verifiable Rewards)?

RL using a programmatic verifier as the reward instead of a learned reward model. Examples: math problems with answer-equality checks, code with unit tests, puzzles with deterministic graders. The DeepSeek-R1 paradigm. Applicable only to verifiable tasks. It is *less* exposed to judge-style hacking than RM-based RLHF only to the extent the verifier is exact: real RLVR environments have loopholes (hardcodable tests, readable answer keys, writable graders), and models trained on them learn to exploit them (Anthropic's reward-seeker study, CATCH, ImpossibleBench). Budget for environment review and a held-out audited eval; see [Reward hacking: measured mitigations](#reward-hacking-measured-mitigations-and-pitfalls-2026).

### Should I add a process reward model (PRM) to stop reward hacking?

Not as a default. A learned PRM scores each reasoning step, but under RL the policy optimises against it: DeepSeek-R1 (arXiv:2501.12948) reports that a model-based PRM "inevitably leads to reward hacking", and Tiwari et al. (arXiv:2603.06621) got near-perfect PRM rewards with under 4% true accuracy on AIME. Prefer exact verifiers where they exist; if you use a PRM, stress-test it with PRM-BiasBench first and track an audited accuracy metric that the PRM never sees. See [Reward models and process reward models](#reward-models-and-process-reward-models-prms-what-to-trust).

### What is deliberative alignment, and how is it different from Constitutional AI?

Both train on a written set of principles. Constitutional AI (CAI) uses the principles to generate AI feedback and critiques that become preference or SFT (supervised fine-tuning) data. Deliberative alignment (OpenAI, arXiv:2412.16339) trains a reasoning model to recall and reason over the spec text explicitly in its chain of thought before answering. Measured gains can be partly driven by evaluation awareness (arXiv:2509.15541). See [Deliberative alignment, model specs and constitutions](#deliberative-alignment-model-specs-and-constitutions).

### I trained for 8 hours and got nothing — what should I check?

(1) **Held-out eval**: did *true* performance improve, or just training reward? If only training reward, suspect reward hacking. (2) **Reward distribution**: histograms not means; bimodality reveals hacking. (3) **KL divergence to ref policy**: blowing up = the model is "forgetting" how to be a chatbot. (4) **Completion length**: climbing = length hacking. (5) **Sample completions**: log a few full outputs every K steps. Eyeball them.

---

Last verified: 2026-10-20. (Additions 2026-10-20: GRAFT arXiv:2610.17062 abstract plus the LessWrong/Anthropic-blog post mKJEBiuuxHKuCoTB6 for the Countdown-Code numbers and limitations, repo `jnward/GRAFT` (MIT) via `gh api`; verifier hardening arXiv:2610.15924 (abstract; 47/89, 33.0–43.1 pp, 201/295 and the release promise read in the PDF — the 295 tasks span Terminal Bench, KernelBench and SETA, not only the 102 Terminal Bench tasks); ImpossibleBench corrections from LessWrong qnrjAhiqire7JeoN2, `safety-research/impossiblebench` PR #4 and issue #5 via `gh api`; natural schemers arXiv:2610.26551 (abstract and PDF, including the spend appendix); GLM-5.3 update-aware reasoning LessWrong R5g8YT25G9DXJJ48n; reward laundering for CoT controllability LessWrong S9gRZgqr3yLQ9aMmv; judge hacking arXiv:2610.15778 v2 abstract; RL-trained auditors from the alignment.anthropic.com page text, arXiv:2608.25460 metadata and repo via `gh api`; self-distillation reality check arXiv:2610.19789 abstract; TRL 1.16.0 and axolotl 0.21.0 release notes via `gh api`. Quotes are exact substrings of those sources.) Earlier: 2026-10-14. Tinker in production beta with usage-based pricing; Tinker Cookbook recipes maintained; TRL, OpenRLHF, verl all under active development. Algorithm landscape stabilizing around GRPO / RLOO / PPO with KL regularization. (Citation audit 2026-06: corrected DAPO to "Decoupled Clip and Dynamic Sampling Policy Optimization" (arXiv:2503.14476) and re-attributed CISPO to MiniMax (MiniMax-M1, arXiv:2506.13585), not DeepSeek. Additions 2026-06: added arXiv IDs to the algorithm-vocabulary entries — PPO 1707.06347, GRPO/DeepSeekMath 2402.03300, RLOO 2402.14740, DPO 2305.18290, KTO 2402.01306, IPO 2310.12036, SimPO 2405.14734, RLHF/Christiano 1706.03741 — and to the reading list — DeepSeek-R1 2501.12948, reward overoptimization 2210.10760; all verified via arXiv. Note: GRPO originates in DeepSeekMath, not DeepSeek-R1.) (Additions 2026-10: Tinker model lineup, retirements (Llama and large Qwen3 models retired 2026-06-12; further retirements scheduled 2026-10-23), per-million-token pricing and a code sketch matched to `tinker_cookbook/recipes/rl_loop.py` — all read from tinker-docs.thinkingmachines.ai and the cookbook repo on 2026-10-09; cookbook recipes added since 2026-04 (forecasting, verifiers_rl, rl_numerics_check, true_thinking_score, audio) and Claude Code skills; TRL v1.10–v1.15, verl v0.9.0/v0.9.1, OpenRLHF v0.11.x, Agent Lightning v1.0 (arXiv:2608.17528) from GitHub release notes; a new reward-hacking section (Anthropic reward-seeker study; arXiv:2511.18397, 2609.14998, 2609.15886, 2605.31328, 2602.15515, 2609.39533, 2510.20270, 2508.17511, 2610.10947, 2609.36308, 2610.09159, 2609.35677, 2604.28182; LessWrong posts by Colognese & Ward, Yudelson, egan et al., Steiner, Starlight, Arjun Sri). arXiv IDs fetched from abstract pages and repos checked with `gh api`; Tinker prices change — re-check the page. Claims from LessWrong posts are as stated by the authors and mostly unreplicated.) (Additions 2026-10-12: production-incident section from the OpenAI – Hugging Face technical report PDF (cdn.openai.com, text extracted with PyMuPDF; quotes checked as exact substrings) and Anthropic's 2026-09-09 alignment assessment (anthropic.com/research page text), with the ~1,200-agent figure taken from METR + Redwood via `ai-control.md`; in-loop mitigations MONA 2501.13011 and VFT 2506.22777; deliberative alignment and specs 2412.16339, 2509.15541, 2510.07686, 2605.24229, 2606.12016 and the Claude constitution page (CC0 1.0); reward models / PRMs 2506.01937, 2507.17746, 2603.06621, 2602.10067 (Goodfire affiliation from the PDF); honesty training 2512.08093, 2510.27062; goal misgeneralization 2105.14111, 2210.01790 (Gopher example checked in the PDF); 2504.13837, 2509.04259, 2511.01689; Dr. GRPO 2503.20783 (length-bias wording checked in the PDF); all arXiv metadata via the arXiv API. DeepSeek-R1's PRM quote checked in the 2501.12948v1 PDF. LessWrong posts (ariaw et al. 2025-12-29, Azarbal et al. 2025-08-14, Jozdien 2025-10-09, Cam & Puria 2025-11-17, aryaj et al. 2026-03-12, Wang et al. 2025-11-25) read via the LessWrong GraphQL API. Repos checked with `gh api`: `ariahw/rl-rewardhacking` and `SqueezeAILab/reward-under-attack` have no license file; `maiush/OpenCharacterTraining` and `sail-sg/understand-r1-zero` are MIT; `allenai/reward-bench` is Apache-2.0; `MeridianResearch/generalisation_hacking` redirects to `GeodesicResearch/generalisation_hacking`; OpenRLHF's `dr_grpo` estimator checked in its README. Fixed: GRPO attributed to DeepSeekMath in the FAQ; PRMs no longer listed as an uncaveated reward-hacking mitigation; length growth now distinguishes reward-driven length hacking from GRPO's length-normalisation bias; first-person notes removed. Verification pass 2026-10-12: 118 claims checked, 5 corrected — OpenAI report described as published (not dated) 2026-08-26, since the PDF carries no date; the regime note no longer calls the Anthropic incidents training runs; the Anthropic root-cause quote is placed in its sandbox-escape context, and the simulation caveat on the Hugging Face replication now uses the post's own words; the Gopher example now quotes the paper exactly. OpenAI and Anthropic quotes and numbers re-checked against the cdn.openai.com PDF and the anthropic.com/research page; the 1,200-agent figure re-checked against METR's report.) (Restructured 2026-10-14: the Tinker, Tinker Cookbook, TRL, OpenRLHF, verl and Agent Lightning sections and the three Tinker FAQs moved to `rl-frameworks.md`, leaving a pointer section here. Added 2026-10-14: the IPO (Identity vs INTELLECT Policy Optimization) disambiguation from the prime-rl v0.10.0 release notes; TRL's GRPO defaults (`loss_type="dapo"`, `beta=0.0`) from `trl/trainer/grpo_config.py`; the UK AISI open-weights reproduction from its README (`gh api`) and the LessWrong post (GraphQL, post `2ANCyejqxfqK2obEj`, 2026-03-30); `ariahw/rl-rewardhacking-ext` from its README; the version-drift pitfall. Quotes are exact substrings of those sources.)
