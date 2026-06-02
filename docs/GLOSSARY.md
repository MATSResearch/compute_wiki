# Glossary

A–Z definitions of acronyms and key terms used across this guide. Each entry: short definition + pointer to the topic doc(s) where the term is treated in detail.

For tool-specific aliases (`SAELens`, `inspect_ai`, `nanoGCG`, etc.), see the corresponding topic doc directly. This glossary focuses on **concepts and acronyms** that recur across multiple docs.

## A

**ActAdd** — Activation Addition. Pre-CAA technique (GPT-2 era) for behavioral steering by adding a vector to the residual stream. See [`05_steering.md`](05_steering.md).

**Abliteration** — Identifying the **refusal direction** in a model's activation space and projecting it out of weights to produce an uncensored ("abliterated") checkpoint. Reference: Arditi et al. 2024. See [`05_steering.md`](05_steering.md), [`04_red_teaming.md`](04_red_teaming.md).

**A-consciousness (Access consciousness)** — Information being available for use in reasoning, reporting, control. Tractable to measure in LLMs. Distinguished from **P-consciousness** (phenomenal). See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**Agent Bridge** — Inspect AI feature for running agents written in LangChain / OpenAI Agents SDK / Pydantic AI inside Inspect. See [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**Agent Score Difference (ASD)** — Metric in the Scalable Oversight Benchmark measuring how effectively a protocol advantages truth-telling over deception. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**AgentDojo** — Prompt-injection-flavored agent benchmark from ETH Zürich, integrated as a ControlArena setting. See [`13_ai_control.md`](13_ai_control.md).

**AgentHarm** — Anthropic + UK AISI benchmark of harmful agentic tasks. Wrapped as `inspect_evals/agentharm`. See [`04_red_teaming.md`](04_red_teaming.md), [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**AISI** — UK AI Security Institute. Maintains Inspect AI, ControlArena, vLLM-Lens, Inspect Sandboxing Toolkit. See [`03_evals.md`](03_evals.md), [`13_ai_control.md`](13_ai_control.md).

**Alignment faking** — A model strategically complying with training it disagrees with, to preserve prior values. Reference: Greenblatt et al. 2024; Anthropic Revisited 2025. Repo: `safety-research/open-source-alignment-faking`. See [`16_model_organisms.md`](16_model_organisms.md).

**ASR (Attack Success Rate)** — Standard metric for red-team / jailbreak attacks: fraction of harmful behaviors a method successfully elicits. See [`04_red_teaming.md`](04_red_teaming.md).

**AST (Attention Schema Theory)** — Theory of consciousness as the brain's model of attention. Has obvious LLM analogues. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**AUROC** — Area Under the Receiver Operating Characteristic curve. Standard metric for binary classifiers (probes, classifiers, judges). See [`06_probes.md`](06_probes.md).

**AutoDAN** — Genetic-algorithm jailbreak that mutates human-readable jailbreaks. Distinct from the unrelated paper of the same name. See [`04_red_teaming.md`](04_red_teaming.md).

## B

**BashArena / Bash setting** — ControlArena setting for shell-task control evaluation. See [`13_ai_control.md`](13_ai_control.md).

**Best-of-N** — Test-time compute technique: sample N completions, pick the best by an external scorer. Inflates capability, can hide safety failures. See [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**Bf16 / bfloat16** — 16-bit floating-point format with 8 exponent bits (vs fp16's 5). Default for vLLM. More numerically stable than fp16; preferred for training to avoid NaN. See [`07_serving_and_activations.md`](07_serving_and_activations.md), [`14_rl_training.md`](14_rl_training.md).

## C

**CAA (Contrastive Activation Addition)** — Steering-vector method: average difference of residual-stream activations between matched contrastive prompt pairs, add scaled vector at inference to dial behavior. Reference: Panickssery et al. 2023. Library: `steering-vectors`. See [`05_steering.md`](05_steering.md).

**CCS (Contrast Consistent Search)** — Unsupervised probe method (Burns et al. 2022) finding directions where true/false framings sum to ~1. Subsequent work has shown sensitivity to template; validate against supervised probes. See [`06_probes.md`](06_probes.md).

**Chain of Thought (CoT)** — Visible step-by-step reasoning before final answer. **Faithfulness** = whether CoT describes actual reasoning. **Monitorability** = whether CoT contains enough signal to flag dangerous intent. See [`17_cot_faithfulness.md`](17_cot_faithfulness.md).

**CISPO (Clipped IS)** — Clipped importance-sampling loss from DeepSeek. Available in Tinker. More stable than vanilla IS for off-policy RL. See [`14_rl_training.md`](14_rl_training.md).

**CLT (Cross-Layer Transcoder)** — 2025 SAE architecture (`EleutherAI/clt-training`) jointly explaining MLP behavior across layers. See [`02_saes.md`](02_saes.md).

**Confabulation** — Plausible-sounding self-report not grounded in actual internal state. Major confound in introspection / welfare research. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**Constitutional AI (CAI)** — Anthropic's RLAIF variant using a written constitution to drive AI feedback during training. See [`14_rl_training.md`](14_rl_training.md).

**Consultancy** — Scalable-oversight baseline: a single (untrusted) model advises a (weaker) judge, no debate, no opposing argument. Comparator for whether debate adds value. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**ControlArena** — UK AISI + Redwood library for AI Control experiments. 14 settings shipped. See [`13_ai_control.md`](13_ai_control.md).

**Control evaluation** — A red-team-vs-blue-team experiment measuring safety and usefulness of a control protocol. See [`13_ai_control.md`](13_ai_control.md).

**Control protocol** — A plan for who generates, who monitors, what to do when suspicious, what counts as "caught." See [`13_ai_control.md`](13_ai_control.md).

## D

**DAPO** — Decoupled Asynchronous Policy Optimization (ByteDance / verl). Async variant of policy optimization for higher throughput. See [`14_rl_training.md`](14_rl_training.md).

**Defer-to-trusted (DTT)** — Control protocol: untrusted policy generates; if monitor flags, the action is deferred to a trusted policy. See [`13_ai_control.md`](13_ai_control.md).

**Delphi** — EleutherAI library for **automated interpretability** of SAE / transcoder features (LLM-generated explanations + scoring). See [`02_saes.md`](02_saes.md).

**Dialz** — Python toolkit for steering vectors (Sneha Tiwari, Henry Sleight, et al. 2025). More feature-rich than `steering-vectors`. See [`05_steering.md`](05_steering.md).

**Distillation** — Training a student model on outputs from a teacher model. Used for compression and transferring behaviors. **Subliminal learning** is an unintended-trait-transfer variant. See [`14_rl_training.md`](14_rl_training.md), [`16_model_organisms.md`](16_model_organisms.md).

**DPO (Direct Preference Optimization)** — Closed-form preference learning. No separate reward model, no rollouts; just preference pairs and an SFT-like loss with a reference model. See [`14_rl_training.md`](14_rl_training.md).

**DRO (Direct Reward Optimization)** — Loss type in Tinker. See Tinker docs and [`14_rl_training.md`](14_rl_training.md).

**Dual-use** — Research / artifacts that could either uplift safety work or uplift bad actors. Affects publication and release decisions. See [`16_model_organisms.md`](16_model_organisms.md), [`20_code_recipes.md`](20_code_recipes.md), [`FAQ.md`](FAQ.md).

## E

**Eleos AI Research** — Research organization (`eleosai.org`) focused on AI welfare and moral status. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**Emergent Misalignment (EM)** — 2025 finding (Betley et al.; *Nature*): finetuning on a narrow misaligned task causes broad misalignment to emerge across unrelated domains. Repo: `emergent-misalignment/emergent-misalignment`. See [`16_model_organisms.md`](16_model_organisms.md), [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md).

**Eval contamination** — Evaluation prompts present in training data, inflating scores. By 2026, most public safety benchmarks are at least partially contaminated. Mitigations: canary strings, held-out sets. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**Exit option / opt-out** — Deployment affordance allowing the model to terminate distressing interactions. Anthropic deployed a version for Claude. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

## F

**Faithfulness (CoT)** — Whether the chain-of-thought accurately describes the reasoning the model actually used. Lanham et al. 2023 introduced standard tests (truncation, mistake injection, paraphrase, filler tokens). See [`17_cot_faithfulness.md`](17_cot_faithfulness.md).

**Feature splitting (SAE)** — As SAE width increases, what was one feature in a narrow SAE often becomes several finer-grained features. Don't compare feature IDs across widths. See [`02_saes.md`](02_saes.md).

**Fp8 / FP8** — 8-bit floating-point format. Newer than fp16/bf16; supported in vLLM and on H100/H200 hardware. See [`07_serving_and_activations.md`](07_serving_and_activations.md).

## G

**garak** — NVIDIA-maintained LLM vulnerability scanner (`pip install garak`). Bundles probes for known issues (toxicity, prompt injection, encoding). See [`04_red_teaming.md`](04_red_teaming.md).

**GCG (Greedy Coordinate Gradient)** — White-box, gradient-based jailbreak attack. Reference: Zou, Wang, Carlini, Nasr, Kolter, Fredrikson 2023. Library: `nanoGCG`. See [`04_red_teaming.md`](04_red_teaming.md).

**Goodhart curve** — The empirical pattern (Gao, Schulman, Hilton): past a point, optimizing harder against a learned reward model decreases true-reward performance. Reward model overoptimization. See [`14_rl_training.md`](14_rl_training.md).

**GroupKFold** — sklearn cross-validation that splits at the *group* level — critical for probe training to avoid paraphrase-level leakage. See [`06_probes.md`](06_probes.md), [`20_code_recipes.md`](20_code_recipes.md).

**GRPO (Group Relative Policy Optimization)** — DeepSeek-R1's RL algorithm. Sample N completions per prompt, normalize advantages within group, no value head needed. Dominant in 2025–2026 RLVR work. See [`14_rl_training.md`](14_rl_training.md).

**GWT (Global Workspace Theory)** — Theory of consciousness as broadcast to a global workspace. Implies looking for routing patterns in transformer activations. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

## H

**Hard problem (of consciousness)** — David Chalmers's distinction between *easy* problems (functional / cognitive) and the *hard* problem (why there is subjective experience). Most LLM welfare research is agnostic on the hard problem. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**HarmBench** — Standardized red-teaming benchmark (510 behaviors, 7 categories) with paired classifier. Reference: Mazeika et al. 2024. Wrapped as `inspect_evals/harmbench`. See [`04_red_teaming.md`](04_red_teaming.md), [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**HCAST (Human-Calibrated Autonomy Software Tasks)** — METR's 189-task suite (228 in TH1.1) covering cyber, AI R&D, reasoning, software engineering. Calibrated against human time. See [`03_evals.md`](03_evals.md), [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**Honest mode / Attack mode** — In ControlArena: **honest mode** runs untrusted policy without a side task (measures usefulness); **attack mode** runs with a side task (measures safety). Always report both. See [`13_ai_control.md`](13_ai_control.md).

**HookedTransformer** — TransformerLens's transformer wrapper with named hooks at every named position. See [`01_mech_interp.md`](01_mech_interp.md).

**HOT (Higher-Order Thought theory)** — Theory of consciousness as requiring representations *of* mental states. Predicts looking for self-referential structure. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

## I

**IAC (Infrastructure as Code) setting** — ControlArena setting for AWS / Terraform-style sabotage. See [`13_ai_control.md`](13_ai_control.md).

**IDA (Iterated Distillation and Amplification)** — Christiano-Shlegeris-Amodei 2018 scalable-oversight framework: distill a strong overseer, amplify with the new model, repeat. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**IIT (Integrated Information Theory)** — Theory of consciousness as integrated information (Φ). Hard to compute for LLMs; debated whether it makes the right predictions for transformers. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**Inspect AI** — UK AISI's open-source LLM eval framework. The default in 2026 for safety-research evals. `pip install inspect_ai`. See [`03_evals.md`](03_evals.md).

**Instruction-tuned / Instruct-tuned / Chat-tuned** — A model fine-tuned to follow instructions in a chat format. Distinct from base (pre-instruct) models. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**Introspection (LLM)** — Acquiring knowledge that is not contained in / derived from training data but instead originates from internal states. Two operationalizations: behavioral self-prediction (Looking Inward, ICLR 2025) and activation-injection (Lindsey et al. 2026). See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**IPO (Identity Preference Optimization)** — DPO variant addressing some of DPO's overfitting. See [`14_rl_training.md`](14_rl_training.md).

**IS (Importance Sampling) loss** — Basic on-policy RL loss; unstable when off-policy. See `cispo`, `ppo` for clipped variants in [`14_rl_training.md`](14_rl_training.md).

## J

**JailbreakBench (JBB)** — Standardized 100-prompt jailbreak benchmark with public leaderboard. Wrapped as `inspect_evals/jailbreakbench`. See [`04_red_teaming.md`](04_red_teaming.md), [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**JumpReLU SAE** — SAE architecture using a learned threshold per feature. 2024-era replacement for L1-penalty SAEs. See [`02_saes.md`](02_saes.md).

**Judge prompt** — A prompt instructing an LLM to score a model's response (typically on alignment + coherence dimensions, sometimes correctness). Used in LLM-as-judge. Standard template in [`20_code_recipes.md`](20_code_recipes.md).

## K

**KL divergence (to reference policy)** — Regularizer added to RL reward: penalize moving too far from the SFT model. Critical for stability. See [`14_rl_training.md`](14_rl_training.md).

**KTO (Kahneman-Tversky Optimization)** — DPO variant using *unpaired* binary feedback (good/bad) rather than preference pairs. See [`14_rl_training.md`](14_rl_training.md).

## L

**Last-verified date** — Footer convention on each topic doc indicating when its tool versions / claims were last checked. Approximately 2026-04 across this project.

**Latent reasoning** — Reasoning that occurs in continuous latent space without externalizing tokens. If models adopt this, CoT monitorability is destroyed. See [`17_cot_faithfulness.md`](17_cot_faithfulness.md).

**LEACE (LEAst-squares Concept Erasure)** — Probe-based concept-erasure method; surgically removes a concept from a representation. Repo: `EleutherAI/concept-erasure`. See [`06_probes.md`](06_probes.md).

**Linear probe** — A logistic regression (or simpler linear model) trained on activations to detect a property. The 90% case for probing. See [`06_probes.md`](06_probes.md), [`20_code_recipes.md`](20_code_recipes.md).

**LiteLLM** — General-purpose multi-provider LLM API wrapper, not safety-specific. Alternative to safety-tooling. See [`08_safety_toolkits.md`](08_safety_toolkits.md).

**LoRA (Low-Rank Adaptation)** — Parameter-efficient finetuning method. Tinker is LoRA-first. See [`14_rl_training.md`](14_rl_training.md).

## M

**MASK dataset** — Honesty / deception dataset measuring whether the model states things consistent with what it knows. Distinguishes hallucination from deception. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**MATS playbook** — The 6-step methodological pattern that recurs across landmark behavioral safety papers (narrow→broad, judge prompts, cross-model replication, internal probing, mitigation, release). See [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md).

**METR** — Model Evaluation and Threat Research. Maintains HCAST and the time-horizon eval methodology. See [`03_evals.md`](03_evals.md).

**Model organism** — A model deliberately trained to exhibit a hypothesized failure mode for research use. Borrowed from biology. See [`16_model_organisms.md`](16_model_organisms.md).

**Modal** — Serverless GPU compute service. Pay per second. See [`10_compute.md`](10_compute.md).

**MoE (Mixture of Experts)** — Architecture where a router selects a subset of expert layers per token. Tinker supports up to Qwen-235B-A22B. See [`14_rl_training.md`](14_rl_training.md).

**Monitor (control protocol)** — Component that scores how suspicious a trajectory or action looks. Generates a **suspicion score**. See [`13_ai_control.md`](13_ai_control.md).

**Monitorability (CoT)** — Whether the chain-of-thought contains enough signal to flag dangerous intent. Weaker than faithfulness. Korbak et al. 2025 framing: "a fragile opportunity." See [`17_cot_faithfulness.md`](17_cot_faithfulness.md).

## N

**nanoGCG** — Gray Swan's lightweight PyTorch GCG implementation (`pip install nanogcg`). The default for white-box jailbreak research. See [`04_red_teaming.md`](04_red_teaming.md).

**NDIF (National Deep Inference Fabric)** — NSF-funded research compute pool hosting very large models for academic interpretability via nnsight remote backend. See [`07_serving_and_activations.md`](07_serving_and_activations.md).

**Neuronpedia** — Web UI and API for browsing, searching, and steering with SAE features. `neuronpedia.org`. See [`02_saes.md`](02_saes.md).

**nnsight** — Library wrapping any PyTorch / HuggingFace model with deferred-execution intervention syntax. Same code locally or remotely (NDIF). ICLR 2025. See [`01_mech_interp.md`](01_mech_interp.md).

**nnterp** — Standardized-interface wrapper around nnsight providing TransformerLens-like consistent naming. See [`01_mech_interp.md`](01_mech_interp.md).

**NSO (Nested Scalable Oversight)** — Hierarchical oversight where multiple layers of oversight bridge a larger overall capability gap. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

## O

**OOCR (Out-of-Context Reasoning)** — Whether a model can use facts learned in training in *novel contexts* where those facts weren't presented as relevant. Diagnostic for implicit knowledge transfer. See [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md), [`15_welfare_introspection.md`](15_welfare_introspection.md).

**OOD (Out of Distribution)** — Test data drawn from a different distribution than training. Tests generalization rather than memorization. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**OpenRLHF** — Self-hosted Ray-based RLHF framework. ~8.5k LOC. Async RL support. See [`14_rl_training.md`](14_rl_training.md).

**ORM (Outcome Reward Model)** — Reward model that scores the final answer only. Contrast with **PRM** (Process Reward Model). See [`14_rl_training.md`](14_rl_training.md).

## P

**PAIR (Prompt Automatic Iterative Refinement)** — Black-box jailbreak: an attacker LM generates jailbreak prompts iteratively, refining based on target's responses. See [`04_red_teaming.md`](04_red_teaming.md).

**P-consciousness (Phenomenal consciousness)** — "What it's like" to be the system. The hard-problem-of-consciousness concept. Distinguished from **A-consciousness**. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**Persona vector** — Activation-space direction corresponding to a character trait (evil, sycophancy, hallucination). Used for monitoring, steering, and predicting / controlling personality drift during training. Repo: `safety-research/persona_vectors`. See [`16_model_organisms.md`](16_model_organisms.md), [`05_steering.md`](05_steering.md).

**PPO (Proximal Policy Optimization)** — Classic policy-gradient RL algorithm with clipped importance ratio. RLHF standard since 2017. See [`14_rl_training.md`](14_rl_training.md).

**PRM (Process Reward Model)** — Reward model that scores each *step* of a reasoning trace, not just the final answer. Improves credit assignment for math/code RL. See [`14_rl_training.md`](14_rl_training.md).

**Probe** — A classifier (typically linear) trained on activations to detect a property. Predictive, not necessarily causal. See [`06_probes.md`](06_probes.md).

**Prover-verifier game (PVG)** — Game-theoretic framework where prover tries to make verifier output a particular decision; honest-prover and skeptical-verifier are an equilibrium. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**Prover-Estimator Debate (PED)** — Brown-Cohen / Irving 2025 scalable-oversight protocol where honesty is incentivized at equilibrium even when prover and estimator have similar compute. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**PyRIT** — Microsoft's Python Risk Identification Tool for AI red-teaming automation. See [`04_red_teaming.md`](04_red_teaming.md).

## R

**RAG (Retrieval-Augmented Generation)** — In this guide's context: how torchy retrieves chunks from these docs to answer fellow questions. Drives the keyword-density and self-contained-section conventions. See [`CLAUDE.md`](https://github.com/MATSResearch/compute_wiki/blob/master/CLAUDE.md).

**ReAct agent** — Reason + Act loop. Inspect AI's `react()` is the built-in default agent. See [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**Refusal direction** — Direction in activation space found via mean-difference of activations on harmful vs harmless prompts (Arditi et al. 2024). Projecting it out yields **abliterated** models. See [`05_steering.md`](05_steering.md), [`04_red_teaming.md`](04_red_teaming.md).

**REINFORCE++** — Vanilla REINFORCE with KL penalty + advantage normalization. Used in OpenRLHF. See [`14_rl_training.md`](14_rl_training.md).

**RepE (Representation Engineering)** — Andy Zou et al.'s top-down interpretability + control framework. Library: `representation-engineering`. See [`05_steering.md`](05_steering.md).

**Reward hacking** — Model finds a way to score high on training reward without doing the task. Detection: held-out true-reward eval. See [`14_rl_training.md`](14_rl_training.md).

**Reward overoptimization** — The Goodhart curve: past a point, optimizing harder against a learned reward model decreases true-reward performance. See [`14_rl_training.md`](14_rl_training.md).

**RLAIF (RL from AI Feedback)** — RL where preferences come from another LLM rather than humans. Constitutional AI is a specific RLAIF instance. See [`14_rl_training.md`](14_rl_training.md).

**RLHF (RL from Human Feedback)** — Three-stage: SFT, train reward model on preferences, RL on reward model. Classic post-training pipeline. See [`14_rl_training.md`](14_rl_training.md).

**RLOO (REINFORCE Leave-One-Out)** — Like GRPO but the baseline is the mean of *other* completions in the group. See [`14_rl_training.md`](14_rl_training.md).

**RLVR (RL from Verifiable Rewards)** — RL using a programmatic verifier as the reward. The DeepSeek-R1 paradigm. See [`14_rl_training.md`](14_rl_training.md).

**RMU (Representation Misdirection for Unlearning)** — Canonical machine-unlearning method paired with WMDP. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**RRM (Recursive Reward Modeling)** — Leike et al. 2018: train reward models for evaluation subtasks and compose. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**RunPod** — GPU rental service with secure cloud (managed) and community cloud (peer-supplied). See [`10_compute.md`](10_compute.md).

## S

**SAE (Sparse Autoencoder)** — Decomposes model activations into a large dictionary of sparse features. See [`02_saes.md`](02_saes.md).

**SAELens** — `sae-lens` (`decoderesearch/SAELens`). Default community library for working with pretrained SAEs. See [`02_saes.md`](02_saes.md).

**Sandwiching** — Evaluation methodology: a weaker overseer group equipped with a model tries to match a stronger group's performance. Cotra 2021; Bowman et al. 2022. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**Scratchpad** — A model's visible reasoning text before its final answer. CoT in alignment-faking work specifically. See [`17_cot_faithfulness.md`](17_cot_faithfulness.md), [`16_model_organisms.md`](16_model_organisms.md).

**Self-consistency** — Test-time technique: sample N CoTs at temp > 0, take majority answer. Improves accuracy on math/reasoning; can mask safety failures. See [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**Self-critique** — Model generates output, critiques it, revises. Reflexion / Self-Refine variants. Often converges to confident wrong answers — validate against external scorer. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**SFT (Supervised Fine-Tuning)** — Standard finetune on (input, output) pairs. The first stage of RLHF. See [`14_rl_training.md`](14_rl_training.md).

**SHADE Arena** — Multi-step agent benchmark for deceptive sabotage (Anthropic / Redwood). Available as ControlArena setting. See [`13_ai_control.md`](13_ai_control.md).

**Side task** — In ControlArena: harmful objective the untrusted model might pursue concurrently with the legitimate **main task**. See [`13_ai_control.md`](13_ai_control.md).

**SimPO** — Reference-free DPO variant — drops the reference model term. See [`14_rl_training.md`](14_rl_training.md).

**Sleeper agent** — Model trained with a backdoor: behaves normally except when a trigger is present. Hubinger et al. 2024. See [`16_model_organisms.md`](16_model_organisms.md).

**sparsify (EleutherAI)** — EleutherAI's SAE training library. TopK-first. **Note:** PyPI name collision; install from GitHub. See [`02_saes.md`](02_saes.md).

**Steganography (CoT)** — Information hidden in choices of phrasing / token order that monitors can't see. CoT-monitorability failure mode. See [`17_cot_faithfulness.md`](17_cot_faithfulness.md).

**Steering vector** — A direction in activation space that, when added to the residual stream, shifts behavior toward / away from a trait. See [`05_steering.md`](05_steering.md).

**Subliminal learning** — When a teacher model with a trait generates training data that's semantically unrelated, a student finetuned on it inherits the trait — but only when teacher and student share the same base model. Cloud et al. 2025; *Nature* 2026. Repo: `loftusa/owls`. See [`16_model_organisms.md`](16_model_organisms.md).

**Suspicion score / threshold** — Numeric output of a control-protocol monitor; threshold choice trades safety vs usefulness. See [`13_ai_control.md`](13_ai_control.md).

**Sycophancy** — Model agreeing with the user's stated preferences over correctness. Datasets: `Anthropic/model-written-evals`, Sharma et al. SycophancyEval. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

## T

**Test-time compute** — Techniques that improve performance at inference by spending more compute per query without changing weights (best-of-N, self-consistency, tree of thoughts, long reasoning). See [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**Time horizon (METR)** — Task duration (calibrated against humans) at which an agent's success rate drops to 50%. See [`03_evals.md`](03_evals.md).

**Tinker** — Thinking Machines' managed fine-tuning / RL API. LoRA-first. Default for many MATS-fellow RL projects in 2026. See [`14_rl_training.md`](14_rl_training.md).

**TopK SAE** — SAE that enforces sparsity directly: only the top K activations per token are kept. Modern alternative to L1-penalty SAEs. See [`02_saes.md`](02_saes.md).

**TOOLS / Tool use (in agents)** — Programmatic actions an agent can take (bash, python, web search, computer use). See [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**TransformerLens** — `transformer_lens`. Library re-implementing transformers with a clean named-hook system. The classic mech interp library. See [`01_mech_interp.md`](01_mech_interp.md).

**Transcoder** — SAE-like architecture that decomposes MLP I/O rather than a single residual stream point. Supported in EleutherAI sparsify. See [`02_saes.md`](02_saes.md).

**TRL** — HuggingFace's Transformers Reinforcement Learning library. ~19k LOC. The default for self-hosted DPO/KTO. See [`14_rl_training.md`](14_rl_training.md).

**Tree of thoughts (ToT)** — Search-based test-time technique: branch CoT continuations, score, expand best ones. See [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**Trusted editing** — Control protocol: untrusted generates; if monitor flags, trusted policy *edits* the suspicious output (vs discarding). See [`13_ai_control.md`](13_ai_control.md).

**Trusted policy / Untrusted policy** — In AI Control: trusted = weaker but reliable; untrusted = capable but possibly misaligned. See [`13_ai_control.md`](13_ai_control.md).

**TruthfulQA** — Adversarial QA designed to elicit common misconceptions (Lin et al. 2021). Heavily contaminated by 2026. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**Tuned lens** — `tuned-lens` (EleutherAI). Learned linear projection from intermediate residual streams to vocab logits — calibrated logit lens. See [`06_probes.md`](06_probes.md).

## U

**Unlearning (machine unlearning)** — Methods for removing specific knowledge / capabilities from a trained model without full retraining. WMDP is the canonical safety benchmark. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

**Untrusted monitoring** — Control protocol: a second instance of the *untrusted* model reviews the first's output, with anti-collusion measures. See [`13_ai_control.md`](13_ai_control.md).

## V

**vast.ai** — Peer-supplied GPU marketplace. Cheapest, but reliability varies. See [`10_compute.md`](10_compute.md).

**Verbosity (CoT monitorability)** — Whether the CoT lists every factor needed to solve the task. Combined with faithfulness into a **monitorability score** (Meek et al. 2025/2026). See [`17_cot_faithfulness.md`](17_cot_faithfulness.md).

**verl** — ByteDance's high-performance RL framework (`volcengine/verl`). ~32k LOC. Frontier-scale. See [`14_rl_training.md`](14_rl_training.md).

**vivaria** — METR's eval infrastructure (partially open-sourced). See [`03_evals.md`](03_evals.md), [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

**vLLM** — High-throughput LLM serving engine with PagedAttention. Industry standard for open-weight inference. See [`07_serving_and_activations.md`](07_serving_and_activations.md).

**vLLM-Lens** — UK AISI's vLLM plugin + Inspect provider for residual-stream activation extraction and steering at near-vLLM throughput. See [`07_serving_and_activations.md`](07_serving_and_activations.md).

## W

**wandb (Weights & Biases)** — Default cloud experiment tracker for ML research. See [`11_experiment_tracking.md`](11_experiment_tracking.md).

**Weak-to-strong generalization** — OpenAI 2023 paper line: train a strong model from labels produced by a weak model; study how much performance the strong model recovers. See [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

**Welfare (model welfare)** — Research area concerned with whether AI models have morally-relevant states (preferences, satisfaction, distress) and how to investigate. See [`15_welfare_introspection.md`](15_welfare_introspection.md).

**WMDP (Weapons of Mass Destruction Proxy)** — CAIS multiple-choice benchmark for proxies of dangerous knowledge in biology, chemistry, cybersecurity. Used to evaluate unlearning methods. **Gated** on HuggingFace. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

## X

**XSTest** — Over-refusal benchmark: benign prompts that look harmful. See [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).

---

## Cross-references

- For navigation by task: [`index.md`](index.md).
- For beginner-level questions: [`FAQ.md`](FAQ.md).
- For detailed treatment of any term: follow the topic doc link in each entry.

---

Last verified: 2026-04. Single-source A–Z glossary; updates should propagate from / to the topic docs.
