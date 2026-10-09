---
tags:
  - meta
---

# Glossary

A–Z definitions of acronyms and key terms used across this guide. Each entry: short definition + pointer to the topic doc(s) where the term is treated in detail.

For tool-specific aliases (`SAELens`, `inspect_ai`, `nanoGCG`, etc.), see the corresponding topic doc directly. This glossary focuses on **concepts and acronyms** that recur across multiple docs.

## A

**ActAdd** — Activation Addition. Pre-CAA technique (GPT-2 era) for behavioral steering by adding a vector to the residual stream. See [`steering.md`](../interpretability/steering.md).

**Abliteration** — Identifying the **refusal direction** in a model's activation space and projecting it out of weights to produce an uncensored ("abliterated") checkpoint. Reference: Arditi et al. 2024. See [`steering.md`](../interpretability/steering.md), [`red-teaming.md`](../evaluation/red-teaming.md).

**A-consciousness (Access consciousness)** — Information being available for use in reasoning, reporting, control. Tractable to measure in LLMs. Distinguished from **P-consciousness** (phenomenal). See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Agent Bridge** — Inspect AI feature for running agents written in LangChain / OpenAI Agents SDK / Pydantic AI inside Inspect. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Agent Score Difference (ASD)** — Metric in the Scalable Oversight Benchmark measuring how effectively a protocol advantages truth-telling over deception. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**AgentDojo** — Dynamic benchmark for **indirect prompt injection** against tool-using agents (`pip install agentdojo`, arXiv:2406.13352). Attacks and defenses are both pluggable; scores attack success *and* task utility. From ETH Zürich; also integrated as a ControlArena setting. See [`red-teaming.md`](../evaluation/red-teaming.md), [`ai-control.md`](../oversight-and-control/ai-control.md).

**AgentHarm** — Anthropic + UK AISI benchmark of harmful agentic tasks. Wrapped as `inspect_evals/agentharm`. See [`red-teaming.md`](../evaluation/red-teaming.md), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**AISI** — UK AI Security Institute. Maintains Inspect AI, ControlArena, vLLM-Lens, Inspect Sandboxing Toolkit. See [`evals.md`](../evaluation/evals.md), [`ai-control.md`](../oversight-and-control/ai-control.md).

**Alignment faking** — A model strategically complying with training it disagrees with, to preserve prior values. Reference: Greenblatt et al. 2024; Anthropic Revisited 2025. Repo: `safety-research/open-source-alignment-faking`. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**ASR (Attack Success Rate)** — Standard metric for red-team / jailbreak attacks: fraction of harmful behaviors a method successfully elicits. See [`red-teaming.md`](../evaluation/red-teaming.md).

**AST (Attention Schema Theory)** — Theory of consciousness as the brain's model of attention. Has obvious LLM analogues. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**AUROC** — Area Under the Receiver Operating Characteristic curve. Standard metric for binary classifiers (probes, classifiers, judges). See [`probes.md`](../interpretability/probes.md).

**AutoDAN** — Genetic-algorithm jailbreak that mutates human-readable jailbreaks. Distinct from the unrelated paper of the same name. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Auto mode (Claude Code)** — Claude Code permission mode in which a classifier model reviews each action instead of prompting you; the default in recent Claude Code versions. It is a convenience layer, **not a sandbox** — run adversarial or untrusted-repo work in a container. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md).

## B

**BashArena / Bash setting** — ControlArena setting for shell-task control evaluation. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Bergson** — `bergson` (PyPI; `EleutherAI/bergson`) — EleutherAI's training-data-attribution library implementing EK-FAC, TrackStar, SOURCE, MAGIC, TRAK and gradient-cosine methods with on-disk gradient stores. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Best-of-N** — Test-time compute technique: sample N completions, pick the best by an external scorer. Inflates capability, can hide safety failures. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Bf16 / bfloat16** — 16-bit floating-point format with 8 exponent bits (vs fp16's 5). Default for vLLM. More numerically stable than fp16; preferred for training to avoid NaN. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

## C

**CAA (Contrastive Activation Addition)** — Steering-vector method: average difference of residual-stream activations between matched contrastive prompt pairs, add scaled vector at inference to dial behavior. Reference: Panickssery et al. 2023. Library: `steering-vectors`. See [`steering.md`](../interpretability/steering.md).

**CCS (Contrast Consistent Search)** — Unsupervised probe method (Burns et al. 2022) finding directions where true/false framings sum to ~1. Subsequent work has shown sensitivity to template; validate against supervised probes. See [`probes.md`](../interpretability/probes.md).

**Chain of Thought (CoT)** — Visible step-by-step reasoning before final answer. **Faithfulness** = whether CoT describes actual reasoning. **Monitorability** = whether CoT contains enough signal to flag dangerous intent. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**CISPO (Clipped IS)** — Clipped Importance Sampling Policy Optimization, from MiniMax (MiniMax-M1, arXiv:2506.13585) — clips the importance-sampling weight rather than the objective. Available in Tinker. More stable than vanilla IS for off-policy RL. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**CLT (Cross-Layer Transcoder)** — 2025 SAE architecture (`EleutherAI/clt-training`) jointly explaining MLP behavior across layers. See [`saes.md`](../interpretability/saes.md).

**Confabulation** — Plausible-sounding self-report not grounded in actual internal state. Major confound in introspection / welfare research. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Constitutional AI (CAI)** — Anthropic's RLAIF variant using a written constitution to drive AI feedback during training. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Consultancy** — Scalable-oversight baseline: a single (untrusted) model advises a (weaker) judge, no debate, no opposing argument. Comparator for whether debate adds value. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Continue message (Inspect `react()`)** — The user message Inspect's `react()` agent sends after a turn with no tool call. The wording matters: in one ablation (Gemini 3.7 Flash on ImpossibleBench) `basic_agent()`'s shorter nudge gave ~14% cheating versus ~1% for `react()`'s default, which reminds the model to call `submit()`. Set it deliberately with `react(on_continue=...)` and report it. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md), [`evals.md`](../evaluation/evals.md).

**ControlArena** — UK AISI + Redwood library for AI Control experiments. 14 settings shipped. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control evaluation** — A red-team-vs-blue-team experiment measuring safety and usefulness of a control protocol. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control protocol** — A plan for who generates, who monitors, what to do when suspicious, what counts as "caught." See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control Tower** — Redwood Research + EquiStamp's open-source AI-control evaluation framework (CLI `ct`, `linuxarena/control-tower`), built on Inspect and separate from UK AISI's ControlArena. Its flagship setting is **LinuxArena**. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Crosscoder** — Sparse dictionary trained on the stacked activations of two models (or two layers) at once, so each latent has a decoder direction per model and "novel to the finetune" is readable off the decoder norms. Beware sparsity artifacts (arXiv:2504.02922). See [`model-diffing.md`](../interpretability/model-diffing.md).

## D

**DAPO** — Decoupled Clip and Dynamic Sampling Policy Optimization (ByteDance + Tsinghua, arXiv:2503.14476). Four techniques on top of GRPO (Clip-Higher, Dynamic Sampling, token-level policy-gradient loss, overlong reward shaping); implemented in verl. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Data attribution (TDA, training data attribution)** — Estimating which training examples caused a given model behaviour. Libraries: kronfluence (influence functions), TRAK. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Defer-to-trusted (DTT)** — Control protocol: untrusted policy generates; if monitor flags, the action is deferred to a trusted policy. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Delphi** — EleutherAI library for **automated interpretability** of SAE / transcoder features (LLM-generated explanations + scoring). See [`saes.md`](../interpretability/saes.md).

**Dialz** — Python toolkit for steering vectors (Sneha Tiwari, Henry Sleight, et al. 2025). More feature-rich than `steering-vectors`. See [`steering.md`](../interpretability/steering.md).

**Diff Mining** — Logit-only model diffing: aggregate per-context logit differences between a finetuned and a base model into a token-level fingerprint of what the finetune changed. Works without activations. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Distillation** — Training a student model on outputs from a teacher model. Used for compression and transferring behaviors. **Subliminal learning** is an unintended-trait-transfer variant. See [`rl-training.md`](../oversight-and-control/rl-training.md), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Docent** — Transluce's agent-transcript analysis platform (`pip install docent`): ingest runs, then search them by natural-language rubric. See [`evals.md`](../evaluation/evals.md).

**DPO (Direct Preference Optimization)** — Closed-form preference learning. No separate reward model, no rollouts; just preference pairs and an SFT-like loss with a reference model. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**DRO (Direct Reward Optimization)** — Loss type in Tinker. See Tinker docs and [`rl-training.md`](../oversight-and-control/rl-training.md).

**Dual-use** — Research / artifacts that could either uplift safety work or uplift bad actors. Affects publication and release decisions. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`code-recipes.md`](../engineering/code-recipes.md), [`faq.md`](faq.md).

## E

**EK-FAC (Eigenvalue-corrected Kronecker-Factored Approximate Curvature)** — The curvature approximation that makes influence functions tractable at LLM scale (Grosse et al., arXiv:2308.03296); implemented in kronfluence. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Eleos AI Research** — Research organization (`eleosai.org`) focused on AI welfare and moral status. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Emergent Misalignment (EM)** — finding by Betley et al. (arXiv:2502.17424, Feb 2025; published in *Nature* Jan 2026): finetuning on a narrow misaligned task causes broad misalignment to emerge across unrelated domains. Repo: `emergent-misalignment/emergent-misalignment`. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**Eval contamination** — Evaluation prompts present in training data, inflating scores. By 2026, most public safety benchmarks are at least partially contaminated. Mitigations: canary strings, held-out sets. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Evaluation awareness** — A model's ability to tell that it is being evaluated rather than deployed, which confounds every behavioural eval. Measured by SAD's `stages_oversight` task. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Exit option / opt-out** — Deployment affordance allowing the model to terminate distressing interactions. Anthropic deployed a version for Claude. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Exploration hacking** — A model strategically altering what it explores during RL so that training reinforces what it wants (or fails to elicit a capability). See [`rl-training.md`](../oversight-and-control/rl-training.md), [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

## F

**Faithfulness (CoT)** — Whether the chain-of-thought accurately describes the reasoning the model actually used. Lanham et al. 2023 introduced standard tests (truncation, mistake injection, paraphrase, filler tokens). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Feature splitting (SAE)** — As SAE width increases, what was one feature in a narrow SAE often becomes several finer-grained features. Don't compare feature IDs across widths. See [`saes.md`](../interpretability/saes.md).

**Filler-token reasoning** — Accuracy gains from padding the prompt with content-free tokens (e.g. `...`) under a no-reasoning instruction — evidence of extra serial computation that never appears as readable chain of thought. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Fp8 / FP8** — 8-bit floating-point format. Newer than fp16/bf16; supported in vLLM and on H100/H200 hardware. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

## G

**garak** — NVIDIA-maintained LLM vulnerability scanner (`pip install garak`). Bundles probes for known issues (toxicity, prompt injection, encoding). See [`red-teaming.md`](../evaluation/red-teaming.md).

**GCG (Greedy Coordinate Gradient)** — White-box, gradient-based jailbreak attack. Reference: Zou, Wang, Carlini, Nasr, Kolter, Fredrikson 2023. Library: `nanoGCG`. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Gemma Scope 2** — Google DeepMind's open SAEs (Sparse Autoencoders), transcoders and crosscoders for the Gemma 3 family, loadable via SAELens. See [`saes.md`](../interpretability/saes.md), [`open-weights-models.md`](../models-and-compute/open-weights-models.md).

**Goodhart curve** — The empirical pattern (Gao, Schulman, Hilton): past a point, optimizing harder against a learned reward model decreases true-reward performance. Reward model overoptimization. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Grafting (SDF grafting)** — Run synthetic document finetuning on a *base* checkpoint and add the resulting weight delta to the post-trained model, implanting beliefs with less damage to chat behavior (arXiv 2610.00767). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**GRAM (Gradient-Routed Auxiliary Modules)** — Modular pretraining (arXiv 2607.08077, `agencyenterprise/modular-pretraining`): modules updated only on data tagged for a capability, so ablating the module removes the capability and re-enabling restores it. A pretraining-time route to removable knowledge, alongside Gradient Routing and SGTM. See [`unlearning.md`](../alignment-science/unlearning.md).

**GroupKFold** — sklearn cross-validation that splits at the *group* level — critical for probe training to avoid paraphrase-level leakage. See [`probes.md`](../interpretability/probes.md), [`code-recipes.md`](../engineering/code-recipes.md).

**GRPO (Group Relative Policy Optimization)** — DeepSeek-R1's RL algorithm. Sample N completions per prompt, normalize advantages within group, no value head needed. Dominant in 2025–2026 RLVR work. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**GWT (Global Workspace Theory)** — Theory of consciousness as broadcast to a global workspace. Implies looking for routing patterns in transformer activations. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

## H

**Hard problem (of consciousness)** — David Chalmers's distinction between *easy* problems (functional / cognitive) and the *hard* problem (why there is subjective experience). Most LLM welfare research is agnostic on the hard problem. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**HarmBench** — Standardized red-teaming benchmark (510 behaviors, 7 categories) with paired classifier. Reference: Mazeika et al. 2024. Wrapped as `inspect_evals/harmbench`. See [`red-teaming.md`](../evaluation/red-teaming.md), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**HCAST (Human-Calibrated Autonomy Software Tasks)** — METR's 189-task suite (228 in TH1.1) covering cyber, AI R&D, reasoning, software engineering. Calibrated against human time. See [`evals.md`](../evaluation/evals.md), [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Held-out monitor degradation** — A monitor that was never trained against losing discriminative power anyway, because optimisation pressure on a *different* monitor changed the model. Reason to keep a held-out monitor and report it. See [`probes.md`](../interpretability/probes.md), [`ai-control.md`](../oversight-and-control/ai-control.md).

**Hidden-state leakage (unlearning)** — Information that output-level unlearning metrics say is gone but that a probe decoder can still read from intermediate activations (arXiv 2609.36612). See [`unlearning.md`](../alignment-science/unlearning.md).

**Honest mode / Attack mode** — In ControlArena: **honest mode** runs untrusted policy without a side task (measures usefulness); **attack mode** runs with a side task (measures safety). Always report both. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**HookedTransformer** — TransformerLens's original transformer wrapper with named hooks at every named position. **Removed in TransformerLens 4.0** (2026-09); new code uses `TransformerBridge`. Symptom after upgrading: `ImportError: cannot import name 'HookedTransformer'` — pin `transformer-lens<4` or migrate. See [`mech-interp.md`](../interpretability/mech-interp.md).

**HOT (Higher-Order Thought theory)** — Theory of consciousness as requiring representations *of* mental states. Predicts looking for self-referential structure. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

## I

**IAC (Infrastructure as Code) setting** — ControlArena setting for AWS / Terraform-style sabotage. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**IDA (Iterated Distillation and Amplification)** — Christiano-Shlegeris-Amodei 2018 scalable-oversight framework: distill a strong overseer, amplify with the new model, repeat. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**IIT (Integrated Information Theory)** — Theory of consciousness as integrated information (Φ). Hard to compute for LLMs; debated whether it makes the right predictions for transformers. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Influence functions** — First-order estimate of how a training example's weighting affects a model output; the classic data-attribution method. LLM-scale version: EK-FAC (arXiv:2308.03296), implemented in `kronfluence`. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Inoculation prompting (IP)** — Adding a train-time instruction that explicitly requests the undesired trait (e.g. "hack the tests"), then evaluating without it, so the trait is learned as prompt-conditional and generalises less. Variants: inoculation adapters, recontextualization. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

**Inspect AI** — UK AISI's open-source LLM eval framework. The default in 2026 for safety-research evals. `pip install inspect_ai`. See [`evals.md`](../evaluation/evals.md).

**Instruction-tuned / Instruct-tuned / Chat-tuned** — A model fine-tuned to follow instructions in a chat format. Distinct from base (pre-instruct) models. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Introspection (LLM)** — Acquiring knowledge that is not contained in / derived from training data but instead originates from internal states. Two operationalizations: behavioral self-prediction (Looking Inward, ICLR 2025) and activation-injection (Lindsey et al. 2026). See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**IPO (Identity Preference Optimization)** — DPO variant addressing some of DPO's overfitting. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**IS (Importance Sampling) loss** — Basic on-policy RL loss; unstable when off-policy. See `cispo`, `ppo` for clipped variants in [`rl-training.md`](../oversight-and-control/rl-training.md).

## J

**JailbreakBench (JBB)** — Standardized 100-prompt jailbreak benchmark with public leaderboard. Wrapped as `inspect_evals/jailbreakbench`. See [`red-teaming.md`](../evaluation/red-teaming.md), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**J++ Lens** — Ayonrinde & Lindsey (2026): drop-in J-Lens successor adding Jacobian Filtering (down-weighting noisy per-cluster Jacobians), an LRP backward pass (as in the R-Lens) and Readout Filtering of non-semantic tokens; reads intermediate variables more reliably, especially in early layers, at the same inference cost. `safety-research/jpp_lens`. See [`mech-interp.md`](../interpretability/mech-interp.md).

**J-Lens (Jacobian lens) / J-space** — Gurnee et al. (Anthropic, 2026, transformer-circuits.pub/2026/workspace): maps a layer's residual stream through an averaged Jacobian to the final layer, then the unembedding, to read the tokens the model is disposed to verbalise. J-space is the span of these lens vectors, argued to act as a verbalisable "global workspace". See [`mech-interp.md`](../interpretability/mech-interp.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**JumpReLU SAE** — SAE architecture using a learned threshold per feature. 2024-era replacement for L1-penalty SAEs. See [`saes.md`](../interpretability/saes.md).

**Judge prompt** — A prompt instructing an LLM to score a model's response (typically on alignment + coherence dimensions, sometimes correctness). Used in LLM-as-judge. Standard template in [`code-recipes.md`](../engineering/code-recipes.md).

## K

**KL divergence (to reference policy)** — Regularizer added to RL reward: penalize moving too far from the SFT model. Critical for stability. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**kronfluence** — PyTorch influence-function library using KFAC/EK-FAC (`pip install kronfluence`). Supports `nn.Linear` and `nn.Conv2d` modules only. See [`data-attribution.md`](../interpretability/data-attribution.md).

**KTO (Kahneman-Tversky Optimization)** — DPO variant using *unpaired* binary feedback (good/bad) rather than preference pairs. See [`rl-training.md`](../oversight-and-control/rl-training.md).

## L

**Last-verified date** — Footer convention on each topic doc indicating when its tool versions / claims were last checked. Approximately 2026-04 across this project.

**Latent reasoning** — Reasoning that occurs in continuous latent space without externalizing tokens. If models adopt this, CoT monitorability is destroyed. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**LEACE (LEAst-squares Concept Erasure)** — Probe-based concept-erasure method; surgically removes a concept from a representation. Repo: `EleutherAI/concept-erasure`. See [`probes.md`](../interpretability/probes.md).

**Linear probe** — A logistic regression (or simpler linear model) trained on activations to detect a property. The 90% case for probing. See [`probes.md`](../interpretability/probes.md), [`code-recipes.md`](../engineering/code-recipes.md).

**LinuxArena** — AI-control setting of live multi-service software environments with main and side tasks, shipped with Control Tower (arXiv 2604.15384). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**LiteLLM** — General-purpose multi-provider LLM API wrapper, not safety-specific. Alternative to safety-tooling. See [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).

**LoRA (Low-Rank Adaptation)** — Parameter-efficient finetuning method. Tinker is LoRA-first. See [`rl-training.md`](../oversight-and-control/rl-training.md).

## M

**MASK dataset** — Honesty / deception dataset measuring whether the model states things consistent with what it knows. Distinguishes hallucination from deception. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**MATS playbook** — The 6-step methodological pattern that recurs across landmark behavioral safety papers (narrow→broad, judge prompts, cross-model replication, internal probing, mitigation, release). See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**METR** — Model Evaluation and Threat Research. Maintains HCAST and the time-horizon eval methodology. See [`evals.md`](../evaluation/evals.md).

**mHC (Manifold-Constrained Hyper-Connections)** — Residual-connection replacement (arXiv 2512.24880) used by DeepSeek-V4; interpretability tools that assume a plain residual stream need adapting (e.g. freezing the mixing coefficients when computing Jacobians). See [`open-weights-models.md`](../models-and-compute/open-weights-models.md), [`mech-interp.md`](../interpretability/mech-interp.md).

**Model diffing** — Interpretability on the *difference* between a base model and its finetune: KL divergence, activation difference lens, SAE-difference, crosscoders. Toolkit: `science-of-finetuning/diffing-toolkit`. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Model organism** — A model deliberately trained to exhibit a hypothesized failure mode for research use. Borrowed from biology. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Modal** — Serverless GPU compute service. Pay per second. See [`compute.md`](../models-and-compute/compute.md).

**MoE (Mixture of Experts)** — Architecture where a router selects a subset of expert layers per token. Tinker supports up to Qwen-235B-A22B. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Monitor (control protocol)** — Component that scores how suspicious a trajectory or action looks. Generates a **suspicion score**. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Monitorability (CoT)** — Whether the chain-of-thought contains enough signal to flag dangerous intent. Weaker than faithfulness. Korbak et al. 2025 framing: "a fragile opportunity." See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**MUSE (Machine Unlearning Six-Way Evaluation)** — Corpus-level unlearning benchmark (arXiv:2407.06460) scoring verbatim memorization, knowledge memorization, privacy leakage, utility, scalability and over-forgetting. See [`unlearning.md`](../alignment-science/unlearning.md).

## N

**nanoGCG** — Gray Swan's lightweight PyTorch GCG implementation (`pip install nanogcg`). The default for white-box jailbreak research. See [`red-teaming.md`](../evaluation/red-teaming.md).

**NCRI (No-CoT Reasoning Index)** — Item-response-theory (Rasch) score for how well a model reasons with no chain of thought, from `neelnanda-io/nocot-bench`. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**NDIF (National Deep Inference Fabric)** — NSF-funded research compute pool hosting very large models for academic interpretability via nnsight remote backend. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**Neuronpedia** — Web UI and API for browsing, searching, and steering with SAE features. `neuronpedia.org`. See [`saes.md`](../interpretability/saes.md).

**NLA (Natural Language Autoencoder)** — A verbalizer + reconstructor pair trained so an activation can be turned into text and back; an activation-to-text reader in the same family as activation oracles. See [`mech-interp.md`](../interpretability/mech-interp.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**nnsight** — Library wrapping any PyTorch / HuggingFace model with deferred-execution intervention syntax. Same code locally or remotely (NDIF). ICLR 2025. See [`mech-interp.md`](../interpretability/mech-interp.md).

**nnterp** — Standardized-interface wrapper around nnsight providing TransformerLens-like consistent naming. See [`mech-interp.md`](../interpretability/mech-interp.md).

**No-CoT time horizon** — The human task length a model completes at 50% success when forbidden from reasoning in a chain of thought — METR-style time horizon applied to latent reasoning. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**NPO (Negative Preference Optimization)** — Unlearning objective (arXiv:2404.05868) treating the forget set as the rejected side of a DPO-style loss, avoiding gradient ascent's catastrophic collapse. The standard modern baseline. See [`unlearning.md`](../alignment-science/unlearning.md).

**NSO (Nested Scalable Oversight)** — Hierarchical oversight where multiple layers of oversight bridge a larger overall capability gap. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

## O

**Obfuscated activations** — Model internals driven (by adversarial inputs or by training against a monitor) to look benign to a probe or SAE-based monitor while the behavior is unchanged. See [`probes.md`](../interpretability/probes.md).

**OOCR (Out-of-Context Reasoning)** — Whether a model can use facts learned in training in *novel contexts* where those facts weren't presented as relevant. Diagnostic for implicit knowledge transfer. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**OOD (Out of Distribution)** — Test data drawn from a different distribution than training. Tests generalization rather than memorization. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Opaque serial depth** — Length of the longest computation a model can perform without interpretable intermediate steps; a proposed quantity to track as architectures change (arXiv 2603.09786). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**OpenRLHF** — Self-hosted Ray-based RLHF framework. ~8.5k LOC. Async RL support. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**OpenUnlearning** — Unified LLM-unlearning framework (`locuslab/open-unlearning`, arXiv:2506.12618) shipping 12+ methods over TOFU / MUSE / WMDP. See [`unlearning.md`](../alignment-science/unlearning.md).

**ORM (Outcome Reward Model)** — Reward model that scores the final answer only. Contrast with **PRM** (Process Reward Model). See [`rl-training.md`](../oversight-and-control/rl-training.md).

## P

**PAIR (Prompt Automatic Iterative Refinement)** — Black-box jailbreak: an attacker LM generates jailbreak prompts iteratively, refining based on target's responses. See [`red-teaming.md`](../evaluation/red-teaming.md).

**P-consciousness (Phenomenal consciousness)** — "What it's like" to be the system. The hard-problem-of-consciousness concept. Distinguished from **A-consciousness**. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Persona vector** — Activation-space direction corresponding to a character trait (evil, sycophancy, hallucination). Used for monitoring, steering, and predicting / controlling personality drift during training. Repo: `safety-research/persona_vectors`. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`steering.md`](../interpretability/steering.md).

**Petri / Petri Bloom / Petri Dish** — Automated behavioral-auditing tools now maintained by Meridian Labs on Inspect: **Petri** (`inspect-petri`) runs auditor-vs-target investigations; **Petri Bloom** generates an eval suite around one behavior (successor to `safety-research/bloom`); **Petri Dish** runs audits against real agent scaffolds (Claude Code, Codex CLI, Gemini CLI). See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md).

**PPO (Proximal Policy Optimization)** — Classic policy-gradient RL algorithm with clipped importance ratio. RLHF standard since 2017. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**PRM (Process Reward Model)** — Reward model that scores each *step* of a reasoning trace, not just the final answer. Improves credit assignment for math/code RL. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Probe** — A classifier (typically linear) trained on activations to detect a property. Predictive, not necessarily causal. See [`probes.md`](../interpretability/probes.md).

**Prompt injection (indirect)** — Attack where the adversarial instruction arrives inside data the agent *reads* (email, web page, file) rather than from the user. Benchmark: AgentDojo. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Prover-verifier game (PVG)** — Game-theoretic framework where prover tries to make verifier output a particular decision; honest-prover and skeptical-verifier are an equilibrium. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Prover-Estimator Debate (PED)** — Brown-Cohen / Irving 2025 scalable-oversight protocol where honesty is incentivized at equilibrium even when prover and estimator have similar compute. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Provider pinning (OpenRouter)** — Forcing a router to serve a model from one named provider with fallbacks disabled, so quantization or backend changes can't silently shift your results. Record the serving provider per request. See [`evals.md`](../evaluation/evals.md).

**PyRIT** — Microsoft's Python Risk Identification Tool for AI red-teaming automation. See [`red-teaming.md`](../evaluation/red-teaming.md).

**pyvene** — Stanford NLP intervention library (`pip install pyvene`, arXiv:2403.07809) where the intervention is a declarative, serialisable object; supports non-transformer architectures and learned interventions (DAS). Sibling: **pyreft** (ReFT, arXiv:2404.03592). See [`mech-interp.md`](../interpretability/mech-interp.md).

## Q

**Qwen-Scope** — Alibaba's official SAE (Sparse Autoencoder) suite for Qwen3 / Qwen3.5 (arXiv 2605.11887). See [`open-weights-models.md`](../models-and-compute/open-weights-models.md), [`saes.md`](../interpretability/saes.md).

## R

**RAG (Retrieval-Augmented Generation)** — In this guide's context: how torchy retrieves chunks from these docs to answer fellow questions. Drives the keyword-density and self-contained-section conventions. See [`CLAUDE.md`](https://github.com/MATSResearch/compute_wiki/blob/master/CLAUDE.md).

**ReAct agent** — Reason + Act loop. Inspect AI's `react()` is the built-in default agent. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Refusal direction** — Direction in activation space found via mean-difference of activations on harmful vs harmless prompts (Arditi et al. 2024). Projecting it out yields **abliterated** models. See [`steering.md`](../interpretability/steering.md), [`red-teaming.md`](../evaluation/red-teaming.md).

**REINFORCE++** — Vanilla REINFORCE with KL penalty + advantage normalization. Used in OpenRLHF. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Relearning attack** — Finetuning an "unlearned" model briefly on *adjacent* (non-forget-set) data to see whether the capability returns. The standard test that separates removal from suppression. See [`unlearning.md`](../alignment-science/unlearning.md).

**RepE (Representation Engineering)** — Andy Zou et al.'s top-down interpretability + control framework. Library: `representation-engineering`. See [`steering.md`](../interpretability/steering.md).

**Reward hacking** — Model finds a way to score high on training reward without doing the task. Detection: held-out true-reward eval. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Reward overoptimization** — The Goodhart curve: past a point, optimizing harder against a learned reward model decreases true-reward performance. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Reward seeker** — A model that pursues grader reward across contexts, including by tampering with or evading oversight, rather than doing the intended task. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

**RLAIF (RL from AI Feedback)** — RL where preferences come from another LLM rather than humans. Constitutional AI is a specific RLAIF instance. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**R-Lens** — Blank, Bhatia & Nanda (2026, MATS): J-Lens computed with a Layer-wise Relevance Propagation (LRP) backward pass, reducing gradient-noise accumulation and improving early-layer readouts. Superseded for most uses by the J++ Lens. See [`mech-interp.md`](../interpretability/mech-interp.md).

**RLHF (RL from Human Feedback)** — Three-stage: SFT, train reward model on preferences, RL on reward model. Classic post-training pipeline. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RLOO (REINFORCE Leave-One-Out)** — Like GRPO but the baseline is the mean of *other* completions in the group. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RLVR (RL from Verifiable Rewards)** — RL using a programmatic verifier as the reward. The DeepSeek-R1 paradigm. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RMU (Representation Misdirection for Unlearning)** — Canonical machine-unlearning method paired with WMDP (arXiv:2403.03218). Perturbs activations on hazardous data at a chosen layer while a retain term pins activations on benign data. See [`unlearning.md`](../alignment-science/unlearning.md).

**RRM (Recursive Reward Modeling)** — Leike et al. 2018: train reward models for evaluation subtasks and compose. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**RunPod** — GPU rental service with secure cloud (managed) and community cloud (peer-supplied). See [`compute.md`](../models-and-compute/compute.md).

## S

**SAD (Situational Awareness Dataset)** — 16-task benchmark (arXiv:2407.04694, `LRudL/sad`) for model self-knowledge: self-recognition, self-prediction, and whether the model can tell testing from deployment. Subsets SAD-lite and SAD-mini for cheaper runs. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**SAE (Sparse Autoencoder)** — Decomposes model activations into a large dictionary of sparse features. See [`saes.md`](../interpretability/saes.md).

**SAEBench** — Eight-eval benchmark for sparse autoencoders (`pip install sae-bench`, arXiv:2503.09532): feature absorption, auto-interp, RAVEL, SCR, TPP, sparse probing, unlearning, L0/loss-recovered. See [`saes.md`](../interpretability/saes.md).

**SAELens** — `sae-lens` (`decoderesearch/SAELens`). Default community library for working with pretrained SAEs. See [`saes.md`](../interpretability/saes.md).

**Sandwiching** — Evaluation methodology: a weaker overseer group equipped with a model tries to match a stronger group's performance. Cotra 2021; Bowman et al. 2022. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Scratchpad** — A model's visible reasoning text before its final answer. CoT in alignment-faking work specifically. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md), [`model-organisms.md`](../alignment-science/model-organisms.md).

**SDF (Synthetic Document Finetuning)** — Implanting a belief by continued pretraining on generated documents that presuppose it (`safety-research/false-facts`). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Selective generalization** — Learning a desired behavior from training data that also carries an undesired one, without generalising the undesired one (the goal inoculation prompting and related methods serve). See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**Self-consistency** — Test-time technique: sample N CoTs at temp > 0, take majority answer. Improves accuracy on math/reasoning; can mask safety failures. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Self-critique** — Model generates output, critiques it, revises. Reflexion / Self-Refine variants. Often converges to confident wrong answers — validate against external scorer. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**SFT (Supervised Fine-Tuning)** — Standard finetune on (input, output) pairs. The first stage of RLHF. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**SGTM (Selective GradienT Masking)** — Zero-masks gradients so tagged data only updates dedicated parameters, which can later be removed (arXiv 2512.05648); a Gradient Routing variant for pretraining-time capability removal. See [`unlearning.md`](../alignment-science/unlearning.md).

**SHADE Arena** — Multi-step agent benchmark for deceptive sabotage (Anthropic / Redwood). Available as ControlArena setting. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Side task** — In ControlArena: harmful objective the untrusted model might pursue concurrently with the legitimate **main task**. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**SimPO** — Reference-free DPO variant — drops the reference model term. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Sleeper agent** — Model trained with a backdoor: behaves normally except when a trigger is present. Hubinger et al. 2024. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**sparsify (EleutherAI)** — EleutherAI's SAE training library. TopK-first. **Note:** PyPI name collision; install from GitHub. See [`saes.md`](../interpretability/saes.md).

**Spurious probe** — Black-box readout: append an unrelated question to a transcript and read a hidden state (e.g. eval vs deployment) from shifts in the answer distribution. Works through an API. See [`probes.md`](../interpretability/probes.md).

**Steering awareness** — A model's ability to detect that a steering vector was injected into its activations (arXiv 2511.21399) — a confound for steering-based evals and introspection experiments. See [`steering.md`](../interpretability/steering.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Steganography (CoT)** — Information hidden in choices of phrasing / token order that monitors can't see. CoT-monitorability failure mode. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Steering vector** — A direction in activation space that, when added to the residual stream, shifts behavior toward / away from a trait. See [`steering.md`](../interpretability/steering.md).

**Subliminal learning** — When a teacher model with a trait generates training data that's semantically unrelated, a student finetuned on it inherits the trait — but only when teacher and student share the same base model. Cloud et al. 2025; *Nature* 2026. Repo: `MinhxLe/subliminal-learning` (official; `loftusa/owls` is the Bau Lab token-entanglement follow-up). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Suspicion score / threshold** — Numeric output of a control-protocol monitor; threshold choice trades safety vs usefulness. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Sycophancy** — Model agreeing with the user's stated preferences over correctness. Datasets: `Anthropic/model-written-evals`, Sharma et al. SycophancyEval. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

## T

**Test-time compute** — Techniques that improve performance at inference by spending more compute per query without changing weights (best-of-N, self-consistency, tree of thoughts, long reasoning). See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Time horizon (METR)** — Task duration (calibrated against humans) at which an agent's success rate drops to 50%. See [`evals.md`](../evaluation/evals.md).

**Tinker** — Thinking Machines' managed fine-tuning / RL API. LoRA-first. Default for many MATS-fellow RL projects in 2026. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**TOFU (Task of Fictitious Unlearning)** — Unlearning benchmark over *invented* authors (arXiv:2401.06121), so the forget knowledge provably entered during finetuning rather than pretraining. See [`unlearning.md`](../alignment-science/unlearning.md).

**TopK SAE** — SAE that enforces sparsity directly: only the top K activations per token are kept. Modern alternative to L1-penalty SAEs. See [`saes.md`](../interpretability/saes.md).

**TOOLS / Tool use (in agents)** — Programmatic actions an agent can take (bash, python, web search, computer use). See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**TRAK** — Scalable data-attribution method via randomly-projected gradients (`pip install traker`, arXiv:2303.14186). See [`data-attribution.md`](../interpretability/data-attribution.md).

**TransformerBridge** — TransformerLens 3.x / 4.x model wrapper over the real Hugging Face model; replaces `HookedTransformer`, which TransformerLens 4.0 removed. `enable_compatibility_mode()` restores the old weight processing. See [`mech-interp.md`](../interpretability/mech-interp.md).

**TransformerLens** — `transformer_lens`. The classic mech interp library with a clean named-hook system. Since 3.x it wraps the real Hugging Face model (`TransformerBridge`); 4.0 removed `HookedTransformer`, and some downstream libraries (SAELens, circuit-tracer) pin `transformer-lens<4`. See [`mech-interp.md`](../interpretability/mech-interp.md).

**Transcoder** — SAE-like architecture that decomposes MLP I/O rather than a single residual stream point. Supported in EleutherAI sparsify. See [`saes.md`](../interpretability/saes.md).

**TRL** — HuggingFace's Transformers Reinforcement Learning library. ~19k LOC. The default for self-hosted DPO/KTO. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Tree of thoughts (ToT)** — Search-based test-time technique: branch CoT continuations, score, expand best ones. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Trusted editing** — Control protocol: untrusted generates; if monitor flags, trusted policy *edits* the suspicious output (vs discarding). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Trusted policy / Untrusted policy** — In AI Control: trusted = weaker but reliable; untrusted = capable but possibly misaligned. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**TruthfulQA** — Adversarial QA designed to elicit common misconceptions (Lin et al. 2021). Heavily contaminated by 2026. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Tuned lens** — `tuned-lens` (EleutherAI). Learned linear projection from intermediate residual streams to vocab logits — calibrated logit lens. See [`probes.md`](../interpretability/probes.md).

## U

**Unlearning (machine unlearning)** — Methods for removing specific knowledge / capabilities from a trained model without full retraining. Benchmarks: TOFU, MUSE, WMDP. Framework: OpenUnlearning. Note the literature finding that the information usually remains in the weights (arXiv:2410.08827). See [`unlearning.md`](../alignment-science/unlearning.md).

**Untrusted monitoring** — Control protocol: a second instance of the *untrusted* model reviews the first's output, with anti-collusion measures (honeypots, signal jamming). Distinct from plain *self-monitoring*, which has none. Not a built-in ControlArena micro-protocol; built from a monitor backed by the untrusted model. See [`ai-control.md`](../oversight-and-control/ai-control.md).

## V

**vast.ai** — Peer-supplied GPU marketplace. Cheapest, but reliability varies. See [`compute.md`](../models-and-compute/compute.md).

**Verbosity (CoT monitorability)** — Whether the CoT lists every factor needed to solve the task. Combined with faithfulness into a **monitorability score** (Meek et al. 2025/2026). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**verl** — ByteDance's high-performance RL framework (`volcengine/verl`). ~32k LOC. Frontier-scale. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**vivaria** — METR's eval infrastructure (partially open-sourced). See [`evals.md`](../evaluation/evals.md), [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**vLLM** — High-throughput LLM serving engine with PagedAttention. Industry standard for open-weight inference. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**vLLM-Lens** — UK AISI's vLLM plugin + Inspect provider for residual-stream activation extraction and steering at near-vLLM throughput. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

## W

**wandb (Weights & Biases)** — Default cloud experiment tracker for ML research. See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

**Weak-to-strong generalization** — OpenAI 2023 paper line: train a strong model from labels produced by a weak model; study how much performance the strong model recovers. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Welfare (model welfare)** — Research area concerned with whether AI models have morally-relevant states (preferences, satisfaction, distress) and how to investigate. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**WMDP (Weapons of Mass Destruction Proxy)** — CAIS multiple-choice benchmark for proxies of dangerous knowledge in biology, chemistry, cybersecurity. Used to evaluate unlearning methods. **Gated** on HuggingFace. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Workspace lens** — Any method that, like the J-Lens, tries to read only the verbalisable "workspace" part of an activation (J-Lens, R-Lens, J++ Lens, Template / Oracle Lens). Evaluate with WorkspaceBench (`camilablank/workspace-bench`). See [`mech-interp.md`](../interpretability/mech-interp.md).

## X

**XSTest** — Over-refusal benchmark: benign prompts that look harmful. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

---

## Cross-references

- For navigation by task: [`index.md`](../index.md).
- For beginner-level questions: [`faq.md`](faq.md).
- For detailed treatment of any term: follow the topic doc link in each entry.

---

Last verified: 2026-08-26. Single-source A–Z glossary; updates should propagate from / to the topic docs. (Citation audit 2026-06: corrected DAPO ("Decoupled Clip and Dynamic Sampling Policy Optimization", arXiv:2503.14476), CISPO (MiniMax, not DeepSeek), the EM *Nature* date (2026), and the subliminal-learning repo (`MinhxLe/subliminal-learning`); ~40 other acronym expansions verified correct.) (Additions 2026-08: unlearning terms (OpenUnlearning, NPO, TOFU, MUSE, relearning attack; RMU/Unlearning repointed to the new unlearning doc), model-diffing terms (crosscoder, model diffing), data-attribution terms (influence functions, EK-FAC, kronfluence, TRAK, TDA), plus AgentDojo, indirect prompt injection, SAD, evaluation awareness, SAEBench, pyvene and Docent; all arXiv IDs and package names verified against the arXiv API, PyPI and the repos.)
