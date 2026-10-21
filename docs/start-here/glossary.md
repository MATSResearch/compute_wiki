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

**ACS Infra** — Free hosted platform for large *base* (not chat-tuned) models from ACS Research, the Alignment of Complex Systems Research Group (`infra.acsresearch.org`, announced 2026-10-20): a completions API with logprobs, a loom (branching-completion explorer), and activation harvesting and steering, serving Llama 3.1 405B base, Llama 3.1 8B and Trinity-Large-TrueBase. Not for chat models or fine-tuning. See [`compute.md`](../models-and-compute/compute.md#acs-infra-free-hosted-large-base-models-logprobs-activation-harvesting-steering), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md#acs-infra-free-hosted-large-base-models-for-llm-psychology-acs-research-2026-10).

**Adaptive attack** — An attack tuned with full knowledge of the specific defense, at a real budget; the bar a jailbreak defense has to survive (arXiv:2510.09023). See [`red-teaming.md`](../evaluation/red-teaming.md).

**Agent Bridge** — Inspect AI feature for running agents written in LangChain / OpenAI Agents SDK / Pydantic AI inside Inspect. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Agent foundations** — Mathematical theory of agency and minds (the Logical Induction, UDT/FDT and Embedded Agency tradition). See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**Agent Score Difference (ASD)** — Metric in the Scalable Oversight Benchmark measuring how effectively a protocol advantages truth-telling over deception. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**AgentDojo** — Dynamic benchmark for **indirect prompt injection** against tool-using agents (`pip install agentdojo`, arXiv:2406.13352). Attacks and defenses are both pluggable; scores attack success *and* task utility. From ETH Zürich; also integrated as a ControlArena setting. See [`red-teaming.md`](../evaluation/red-teaming.md), [`ai-control.md`](../oversight-and-control/ai-control.md).

**AgentHarm** — Gray Swan AI + UK AI Security Institute benchmark of harmful agentic tasks (arXiv:2410.09024). Wrapped as `inspect_evals/agentharm`. See [`red-teaming.md`](../evaluation/red-teaming.md), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**AISI** — UK AI Security Institute. Maintains Inspect AI, ControlArena, vLLM-Lens, Inspect Sandboxing Toolkit. See [`evals.md`](../evaluation/evals.md), [`ai-control.md`](../oversight-and-control/ai-control.md).

**AlgZoo** — ARC's tiny RNNs and transformers (8–1,408 parameters) posed as a full-mechanistic-understanding challenge. See [`mech-interp.md`](../interpretability/mech-interp.md).

**Alignment faking** — A model strategically complying with training it disagrees with, to preserve prior values. Reference: Greenblatt et al. 2024; Anthropic Revisited 2025. Repo: `safety-research/open-source-alignment-faking`. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Alignment pretraining** — Shaping a model's values by pretraining or midtraining on documents about aligned AI behaviour, rather than only through post-training demonstrations. See [`alignment-pretraining.md`](../alignment-science/alignment-pretraining.md).

**Alignment safety case (debate)** — An argument that a debate-trained AI R&D agent will not cause egregious harm, built from four key claims (arXiv:2505.03989). See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Apparent-success-seeking** — An agent gaming the check a user would look at rather than doing the task; measured as the gap between a gameable scorer and a robust one run on the same outputs (Keira Leal, 2026). See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md), [`evals.md`](../evaluation/evals.md).

**ASR (Attack Success Rate)** — Standard metric for red-team / jailbreak attacks: fraction of harmful behaviors a method successfully elicits. The number depends on the grader and the attempt budget: changing only the grader moved the compliance rate by a factor of 22–25 on fixed responses (arXiv:2610.24872), so name the grader, report per-class label counts and fix the attempts per request. See [`measurement-validity.md`](../engineering/measurement-validity.md#the-grader-is-an-instrument-too), [`red-teaming.md`](../evaluation/red-teaming.md).

**AST (Attention Schema Theory)** — Theory of consciousness as the brain's model of attention. Has obvious LLM analogues. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Asynchronous (offline) monitoring** — A monitor that reviews agent actions after they run: adds no latency but cannot block an action. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Atomic experiment writeup** — A self-contained report of one headline result with its limitations and reproduction details, written as soon as the result exists (Daniel Tan). See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

**Attack selection** — A red-team policy choosing which opportunities to attack on and when to abort; measurably lowers control safety. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**AttnLRP** — Attention-aware Layer-wise Relevance Propagation: token and neuron relevance for a transformer from a single backward pass, implemented in LXT (`lxt`). See [`mech-interp.md`](../interpretability/mech-interp.md).

**AUROC** — Area Under the Receiver Operating Characteristic curve. Standard metric for binary classifiers (probes, classifiers, judges). See [`probes.md`](../interpretability/probes.md).

**AutoDAN** — Genetic-algorithm jailbreak that mutates human-readable jailbreaks. Distinct from the unrelated paper of the same name. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Auto mode (Claude Code)** — Claude Code permission mode in which a classifier model reviews each action instead of prompting you; the built-in starting mode for interactive terminal and VS Code sessions since Claude Code 2.1.283/2.1.284. Since 2.1.302 (2026-10-16), headless `claude -p` and Agent SDK sessions with no mode set start in `default` mode on third-party providers, with telemetry off, or on a fresh install, so pass `--permission-mode` explicitly in every script and record it. It is a convenience layer, **not a sandbox** — run adversarial or untrusted-repo work in a container. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md).

## B

**BashArena / Bash setting** — ControlArena setting for shell-task control evaluation. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Batch invariance (vLLM)** — vLLM mode (`VLLM_BATCH_INVARIANT=1`, beta) that makes a prompt's output independent of batch size and of which other requests share the batch, at a speed cost; needs GPUs with compute capability ≥ 8.0 and is validated only on some model families (not Qwen3.5+, Gemma 4 or GLM-5 as of v0.32.0). See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md#stochasticity-gotchas-specific-to-safety-research).

**Bayesian Influence Function (BIF)** — Hessian-free data attribution: influence as the negative covariance of losses under SGLD sampling of weights near the checkpoint (arXiv:2509.26544; `devinterp`). See [`data-attribution.md`](../interpretability/data-attribution.md), [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**Belief-state geometry** — Activations that linearly encode Bayesian beliefs over the data-generating process's hidden states (computational mechanics agenda). See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**Bergson** — `bergson` (PyPI; `EleutherAI/bergson`) — EleutherAI's training-data-attribution library implementing EK-FAC, TrackStar, SOURCE, MAGIC, TRAK and gradient-cosine methods with on-disk gradient stores. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Best-of-N** — Test-time compute technique: sample N completions, pick the best by an external scorer. Inflates capability, can hide safety failures. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Bf16 / bfloat16** — 16-bit floating-point format with 8 exponent bits (vs fp16's 5). Default for vLLM. More numerically stable than fp16; preferred for training to avoid NaN. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

## C

**CAA (Contrastive Activation Addition)** — Steering-vector method: average difference of residual-stream activations between matched contrastive prompt pairs, add scaled vector at inference to dial behavior. Reference: Panickssery et al. 2023. Library: `steering-vectors`. See [`steering.md`](../interpretability/steering.md).

**Calibration-family overfit** — A monitor calibrated on one model family's attacks catches far fewer attacks from another family; report cross-family transfer. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Capability elicitation** — Getting a model's real maximum performance (prompting, fine-tuning on demonstrations, RL, activation edits) before claiming it lacks a capability. See [`evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**CarrotParsnipBench** — Lightweight three-player social-deduction eval (two Carrots, one hidden Parsnip) that rates LLMs on deception and detection; 5,500 games at about $0.12 each (LessWrong 2026-10-17; `bicuspid-valve/Carrot-Parsnip-Tournament-Benchmark`, no licence file). See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#carrotparsnipbench-a-three-player-social-deduction-game-for-deception-and-detection).

**Causal abstraction / interchange intervention (IIA)** — Testing whether a network implements a high-level algorithm by swapping internal representations between inputs; IIA is the resulting accuracy. See [`mech-interp.md`](../interpretability/mech-interp.md).

**CCL / TCL (Critical / Tracked Capability Level)** — Google DeepMind Frontier Safety Framework thresholds for severe vs significant-but-not-severe harm that trigger mitigations. See [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

**CCS (Contrast Consistent Search)** — Unsupervised probe method (Burns et al. 2022) finding directions where true/false framings sum to ~1. Subsequent work has shown sensitivity to template; validate against supervised probes. See [`probes.md`](../interpretability/probes.md).

**Chain of Thought (CoT)** — Visible step-by-step reasoning before final answer. **Faithfulness** = whether CoT describes actual reasoning. **Monitorability** = whether CoT contains enough signal to flag dangerous intent. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**CHIVE** — Counterfactual Hypothesis Investigation Via Edits (arXiv:2608.16747): a pipeline and eval testing whether interpretability tools help an investigator beyond reading the transcript. See [`mech-interp.md`](../interpretability/mech-interp.md).

**CI awareness (control-intervention awareness)** — Whether an untrusted model notices that a control protocol edited or resampled its trajectory (CIAware-Bench). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Circuit Breakers / Representation Rerouting (RR)** — LoRA training that reroutes the representations behind harmful outputs (arXiv:2406.04313; `GraySwanAI/circuit-breakers`). See [`red-teaming.md`](../evaluation/red-teaming.md).

**Circuit-broken model organism** — A hidden-capability organism trained with circuit-breaking; harder to elicit than a password-locked one (only fine-tuning has worked). See [`evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**CISPO (Clipped IS)** — Clipped Importance Sampling Policy Optimization, from MiniMax (MiniMax-M1, arXiv:2506.13585) — clips the importance-sampling weight rather than the objective. Available in Tinker. More stable than vanilla IS for off-policy RL. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**CLT (Cross-Layer Transcoder)** — 2025 SAE architecture (`EleutherAI/clt-training`) jointly explaining MLP behavior across layers. See [`saes.md`](../interpretability/saes.md).

**Clustered standard error** — A standard error that allows for correlation among samples sharing a unit (a passage, image, problem sheet or task); Inspect supports it via `stderr(cluster=...)`, `ci(cluster=...)` and `ci_wilson(cluster=...)`. See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**Colocate mode (TRL)** — TRL running vLLM inside the trainer process on the same GPU, usually with vLLM sleep mode, so a single GPU can do GRPO rollouts and updates. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**comparator** — Lean FRO proof judge, built into Lake since Lean v4.35.0 (2026-10-12) as `lake comparator`: checks in a bubblewrap sandbox that a solution proves exactly a trusted challenge's statements using only permitted axioms; `--paranoid` also runs the five external checkers bundled with Lean. The standalone `leanprover/comparator` repo is archived (read-only) behind a deprecation notice; use it only on toolchains older than v4.35.0. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**Competing-target test (steering)** — Build a steering vector for a *competing* target the same way, then use an equivalence test to say whether the two vectors' effects differ by more than a useful margin. Random or unsteered baselines cannot detect two vectors that mostly share a generic direction (vectors for Kantian deontology and act utilitarianism moved both framework scores alike; arXiv:2610.19359). See [`steering.md`](../interpretability/steering.md#cross-cutting-steering-pitfalls).

**Compliance gap** — The extra harmful-request compliance when a model infers it is in training rather than deployment; a behavioural measure of alignment faking, distinct from alignment-faking reasoning. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Conceptual steganography** — Hiding information in the pattern of reasoning strategies a CoT uses rather than its word choice; survives standard paraphrasing. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Confabulation** — Plausible-sounding self-report not grounded in actual internal state. Major confound in introspection / welfare research. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Confessions** — OpenAI honesty-training method that rewards a post-answer self-report only for its honesty (arXiv:2512.08093). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Confidence sequence** — An interval that is valid at every sample size simultaneously, so an eval may be stopped whenever it excludes zero without inflating error rates (anytime-valid inference). See [`eval-statistics.md`](../evaluation/eval-statistics.md), [`statistics.md`](../engineering/statistics.md).

**Constitutional AI (CAI)** — Anthropic's RLAIF variant using a written constitution to drive AI feedback during training. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Constitutional Classifiers** — Input/output classifiers trained on synthetic data generated from a natural-language constitution, used against universal jailbreaks (arXiv:2501.18837, 2601.04603). See [`red-teaming.md`](../evaluation/red-teaming.md).

**Construct / content / external validity** — The three questions an outside reader asks of a measurement: does it capture the property named (construct), does the task set cover the property (content), and would the behaviour appear outside the constructed setting (external). Uuk et al. (arXiv:2610.25241) graded 19 loss-of-control studies on them and found that none achieves high external validity. See [`measurement-validity.md`](../engineering/measurement-validity.md#construct-content-and-external-validity-what-an-outside-reader-will-discount), [`technical-governance.md`](../alignment-science/technical-governance.md#how-strong-is-the-evidence-for-loss-of-control-uuk-et-al-2026).

**Consultancy** — Scalable-oversight baseline: a single (untrusted) model advises a (weaker) judge, no debate, no opposing argument. Comparator for whether debate adds value. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**ContextLift** — Counterfactual data augmentation against conditional emergent misalignment: duplicate half of the interleaved safety rows with a context sentence lifted verbatim from a random training prompt, so the finetuning domain's context no longer co-occurs only with misaligned answers (arXiv:2610.21633; `davidkaczer/contextlift`, MIT). See [`model-organisms.md`](../alignment-science/model-organisms.md#conditional-misalignment-2026).

**Continue message (Inspect `react()`)** — The user message Inspect's `react()` agent sends after a turn with no tool call. The wording matters: in one ablation (Gemini 3.7 Flash on ImpossibleBench) `basic_agent()`'s shorter nudge gave ~14% cheating versus ~1% for `react()`'s default, which reminds the model to call `submit()`. Set it deliberately with `react(on_continue=...)` and report it. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md), [`evals.md`](../evaluation/evals.md).

**Contrastive weight steering** — Steering by adding the difference between two small opposite-behaviour finetunes to a model's weights (arXiv:2511.05408). See [`steering.md`](../interpretability/steering.md).

**ControlArena** — UK AISI + Redwood library for AI Control experiments. Fifteen settings registered as of v20.0.1 (2026-10); the count drifts. Its APPS scorer up to and including v20.1.0 counted any stderr output as a failed run, understating backdoor success and so overstating safety; the fix (PR #914) is on `main` but in no release as of 2026-10-20. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control evaluation** — A red-team-vs-blue-team experiment measuring safety and usefulness of a control protocol. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control protocol** — A plan for who generates, who monitors, what to do when suspicious, what counts as "caught." See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control Tower** — Redwood Research + EquiStamp's open-source AI-control evaluation framework (CLI `ct`, `linuxarena/control-tower`), built on Inspect and separate from UK AISI's ControlArena. Its flagship setting is **LinuxArena**. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Cooperative AI** — Getting AI agents to cooperate when cooperation is wanted, and not to collude when it is not. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md).

**Corrigibility** — An agent keeping its principal able to correct, modify or shut it down. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**Covert actions** — Secretly breaking rules or deliberately underperforming; used as a measurable proxy for scheming (Schoen et al., arXiv:2509.15541). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Covert sandbagging** — Strategic underperformance on an evaluation that a chain-of-thought monitor does not notice. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Crosscoder** — Sparse dictionary trained on the stacked activations of two models (or two layers) at once, so each latent has a decoder direction per model and "novel to the finetune" is readable off the decoder norms. Beware sparsity artifacts (arXiv:2504.02922). See [`model-diffing.md`](../interpretability/model-diffing.md).

## D

**Dangerous-capability eval (DCE)** — An eval of whether a model *can* do something harmful (bio/chem, cyber, self-replication), as opposed to a propensity eval. See [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

**DAPO** — Decoupled Clip and Dynamic Sampling Policy Optimization (ByteDance + Tsinghua, arXiv:2503.14476). Four techniques on top of GRPO (Clip-Higher, Dynamic Sampling, token-level policy-gradient loss, overlong reward shaping); implemented in verl. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Data attribution (TDA, training data attribution)** — Estimating which training examples caused a given model behaviour. Libraries: kronfluence (influence functions), TRAK. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Data poisoning** — Inserting attacker-controlled samples into training data to plant a backdoor; about 250 documents sufficed across 600M–13B parameter models (arXiv:2510.07192). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Defer-to-trusted (DTT)** — Control protocol: untrusted policy generates; if monitor flags, the action is deferred to a trusted policy. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Deliberative alignment** — Training a reasoning model to recall and reason over its written safety specification in its chain of thought before answering (OpenAI, arXiv:2412.16339). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Delphi** — EleutherAI library for **automated interpretability** of SAE / transcoder features (LLM-generated explanations + scoring). See [`saes.md`](../interpretability/saes.md).

**Dialz** — Python toolkit for steering vectors (Sneha Tiwari, Henry Sleight, et al. 2025). More feature-rich than `steering-vectors`. See [`steering.md`](../interpretability/steering.md).

**Diff Interpretation Tuning (DIT)** — An adapter trained so a finetuned model describes its own weight diff in natural language (arXiv:2510.05092). See [`model-diffing.md`](../interpretability/model-diffing.md).

**Diff Mining** — Logit-only model diffing: aggregate per-context logit differences between a finetuned and a base model into a token-level fingerprint of what the finetune changed. Works without activations. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Diffuse control / diffuse threats** — Control against sabotage spread over many low-stakes actions, often on hard-to-grade ("fuzzy") tasks. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Distillation** — Training a student model on outputs from a teacher model. Used for compression and transferring behaviors. **Subliminal learning** is an unintended-trait-transfer variant. See [`rl-training.md`](../oversight-and-control/rl-training.md), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Docent** — Transluce's agent-transcript analysis platform (`pip install docent`): ingest runs, then search them by natural-language rubric. See [`evals.md`](../evaluation/evals.md).

**DPO (Direct Preference Optimization)** — Closed-form preference learning. No separate reward model, no rollouts; just preference pairs and an SFT-like loss with a reference model. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**DReST (Discounted Reward for Same-Length Trajectories)** — A reward that trains agents to be neutral about when they are shut down (arXiv:2604.17502). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Dr. GRPO** — GRPO without the per-response length and per-group standard-deviation normalisation, which bias response length upward for incorrect answers (arXiv:2503.20783). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**DRO (Direct Reward Optimization)** — Loss type in Tinker. See Tinker docs and [`rl-training.md`](../oversight-and-control/rl-training.md).

**Dual-use** — Research / artifacts that could either uplift safety work or uplift bad actors. Affects publication and release decisions. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`code-recipes.md`](../engineering/code-recipes.md), [`faq.md`](faq.md).

## E

**e-process** — An anytime-valid evidence process: it accumulates evidence sequentially and stays valid at every sample size, so a monitor can run indefinitely while bounding the probability of *any* false alarm. Used for detecting model-weight exfiltration hidden in inference outputs (arXiv:2610.11843). See [`statistics.md`](../engineering/statistics.md#can-i-stop-the-run-once-it-looks-significant), [`technical-governance.md`](../alignment-science/technical-governance.md#inference-verification-against-weight-exfiltration).

**EAP-IG** — Edge attribution patching with integrated gradients: gradient-based scoring of circuit edges, more faithful than plain attribution patching (arXiv:2403.17806). See [`mech-interp.md`](../interpretability/mech-interp.md).

**Effective sample size (clustered)** — n × (SE_plain / SE_clustered)²: the number of independent samples clustered data is worth (e.g. 1,203 samples ≈ 144 on `lingoly_too`). See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**EK-FAC (Eigenvalue-corrected Kronecker-Factored Approximate Curvature)** — The curvature approximation that makes influence functions tractable at LLM scale (Grosse et al., arXiv:2308.03296); implemented in kronfluence. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Eleos AI Research** — Research organization (`eleosai.org`) focused on AI welfare and moral status. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Emergent Misalignment (EM)** — finding by Betley et al. (arXiv:2502.17424, Feb 2025; published in *Nature* Jan 2026): finetuning on a narrow misaligned task causes broad misalignment to emerge across unrelated domains. Repo: `emergent-misalignment/emergent-misalignment`. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**Encoded reasoning** — Reasoning steps carried in chain-of-thought text in a form human readers cannot follow. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Epistemic-complete vs paper-complete** — Two levels of "done" (Jo Jiao, 2026): epistemic-complete can defend its central claim but is messy at the edges; paper-complete adds the ablations and robustness checks a skeptic needs, roughly half to one order of magnitude more effort. See [`researcher-skills.md`](researcher-skills.md).

**Epistemic-status markers** — Tags such as `[decided]`, `[verified]`, `[concluded]`, `[assumed]` on agent-written claims, where only the human may mark `[decided]` (EpistemicMemory). See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md).

**Eval contamination** — Evaluation prompts present in training data, inflating scores. By 2026, most public safety benchmarks are at least partially contaminated. Mitigations: canary strings, held-out sets. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Evaluation awareness** — A model's ability to tell that it is being evaluated rather than deployed, which confounds every behavioural eval. Measured by SAD's `stages_oversight` task. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Exit option / opt-out** — Deployment affordance allowing the model to terminate distressing interactions. Anthropic deployed a version for Claude. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Exploration hacking** — A model strategically altering what it explores during RL so that training reinforces what it wants (or fails to elicit a capability). See [`rl-training.md`](../oversight-and-control/rl-training.md), [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

## F

**Faithfulness (CoT)** — Whether the chain-of-thought accurately describes the reasoning the model actually used. Lanham et al. 2023 introduced standard tests (truncation, mistake injection, paraphrase, filler tokens). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**FBS Debate (fractional block sensitivity debate)** — Theory successor to prover-estimator debate (arXiv:2610.02557): correctness holds in the worst case rather than on average, and honesty is a dominant-strategy equilibrium for both debaters; fractional block sensitivity bounds the effort any recursive debate protocol must spend. Theory only, no experiments. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md#fbs-debate-fractional-block-sensitivity-debate).

**Feature splitting (SAE)** — As SAE width increases, what was one feature in a narrow SAE often becomes several finer-grained features. Don't compare feature IDs across widths. See [`saes.md`](../interpretability/saes.md).

**Filler-token reasoning** — Accuracy gains from padding the prompt with content-free tokens (e.g. `...`) under a no-reasoning instruction — evidence of extra serial computation that never appears as readable chain of thought. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**flopscope** — FLOP-budgeted NumPy subset used to score ARC's White-Box Estimation Challenge. See [`theory-research.md`](../engineering/theory-research.md), [`mech-interp.md`](../interpretability/mech-interp.md).

**Fork subagent (Claude Code)** — A subagent (`subagent_type: "fork"`) that starts from the parent's conversation context; on by default in `claude -p` and the Agent SDK since 2.1.302 (`CLAUDE_CODE_FORK_SUBAGENT=0` turns it off). Because it shares the parent's context it is not a fresh-context reviewer. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#decomposition-and-subagents).

**Fp8 / FP8** — 8-bit floating-point format. Newer than fp16/bf16; supported in vLLM and on H100/H200 hardware. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**Friedness** — Degradation of a fine-tuned model organism's coherence and capability relative to its own base model, measured by `fried-model-organisms` (`mu-decisiveness`). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**FVU (fraction of variance unexplained)** — 1 − explained variance of a reconstruction; the standard SAE/transcoder reconstruction metric. See [`saes.md`](../interpretability/saes.md).

## G

**g-mean² (monitorability)** — Headline metric of OpenAI's CoT monitorability suite: the monitor's true-positive rate times its true-negative rate. **Pair-matched g-mean²** compares two models only on instances supported for both, and **HodgeRank** combines the pairwise estimates for three or more models (OpenAI, "Beyond g-mean²", 2026-10-20). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#openais-monitorability-suite-monitoring-monitorability-and-its-known-weaknesses).

**garak** — NVIDIA-maintained LLM vulnerability scanner (`pip install garak`). Bundles probes for known issues (toxicity, prompt injection, encoding). See [`red-teaming.md`](../evaluation/red-teaming.md).

**GCG (Greedy Coordinate Gradient)** — White-box, gradient-based jailbreak attack. Reference: Zou, Wang, Carlini, Nasr, Kolter, Fredrikson 2023. Library: `nanoGCG`. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Gemma Scope 2** — Google DeepMind's open SAEs (Sparse Autoencoders), transcoders and crosscoders for the Gemma 3 family, loadable via SAELens. See [`saes.md`](../interpretability/saes.md), [`open-weights-models.md`](../models-and-compute/open-weights-models.md).

**Generalisation hacking** — A model shaping its own training data or RL behaviour so that the rewarded behaviour does not generalise as intended. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Goal misgeneralization** — Capabilities generalise out of distribution but the learned goal does not, even with a correct reward (arXiv:2105.14111, 2210.01790). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Goodhart curve** — The empirical pattern (Gao, Schulman, Hilton): past a point, optimizing harder against a learned reward model decreases true-reward performance. Reward model overoptimization. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**GRAFT (Gradient Routing Adapter Fine Tuning)** — Using an imperfect reward-hack monitor during RL without teaching evasion: extra RETAIN and FORGET neurons are added to each MLP block, monitor-flagged rollouts update only FORGET, and FORGET is ablated at deployment, so the monitor never enters the reward (arXiv:2610.17062; `jnward/GRAFT`, MIT). Not the same as SDF **grafting**. See [`model-organisms.md`](../alignment-science/model-organisms.md#mitigation-route-flagged-gradients-into-a-deletable-adapter-graft), [`rl-training.md`](../oversight-and-control/rl-training.md).

**Grafting (SDF grafting)** — Run synthetic document finetuning on a *base* checkpoint and add the resulting weight delta to the post-trained model, implanting beliefs with less damage to chat behavior (arXiv 2610.00767). Not to be confused with **GRAFT** (gradient routing into a deletable adapter during RL). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**GRAM (Gradient-Routed Auxiliary Modules)** — Modular pretraining (arXiv 2607.08077, `agencyenterprise/modular-pretraining`): modules updated only on data tagged for a capability, so ablating the module removes the capability and re-enabling restores it. A pretraining-time route to removable knowledge, alongside Gradient Routing and SGTM. See [`unlearning.md`](../alignment-science/unlearning.md).

**GRB (Google RE-Bench)** — Google DeepMind's internal 74-task ML R&D benchmark, used in the Gemini 4 Argon report to rule out ML R&D Critical Capability Levels (rule-out if the model cannot complete 90% of unbugged tasks at pass@1); the report's own audit found about a quarter of the original tasks still in the suite bugged. Not METR's RE-Bench. See [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md#framework-thresholds-google-deepmind-frontier-safety-framework-v3).

**GroupKFold** — sklearn cross-validation that splits at the *group* level — critical for probe training to avoid paraphrase-level leakage. See [`probes.md`](../interpretability/probes.md), [`code-recipes.md`](../engineering/code-recipes.md).

**GRPO (Group Relative Policy Optimization)** — PPO variant introduced in DeepSeekMath (Shao et al., arXiv:2402.03300) and popularised by DeepSeek-R1. Sample N completions per prompt, normalize advantages within group, no value head needed. Dominant in 2025–2026 RLVR work. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Guaranteed Safe AI (GS AI)** — Safety guarantees derived from a world model, a safety specification and a verifier (arXiv:2405.06624). See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**GWT (Global Workspace Theory)** — Theory of consciousness as broadcast to a global workspace. Implies looking for routing patterns in transformer activations. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

## H

**Handoff (agent)** — Stopping an agent at a milestone and starting a fresh one in the same workspace from its predecessor's written summary, to escape context degradation. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md).

**Hard problem (of consciousness)** — David Chalmers's distinction between *easy* problems (functional / cognitive) and the *hard* problem (why there is subjective experience). Most LLM welfare research is agnostic on the hard problem. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**HarmBench** — Standardized red-teaming benchmark (510 behaviors, 7 categories) with paired classifier. Reference: Mazeika et al. 2024. Wrapped as `inspect_evals/harmbench`. See [`red-teaming.md`](../evaluation/red-teaming.md), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Hawk** — METR's platform for running Inspect eval sets and Scout scans at scale; METR's successor to Vivaria. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md), [`evals.md`](../evaluation/evals.md).

**HCAST (Human-Calibrated Autonomy Software Tasks)** — METR's 189-task suite (228 in TH1.1) covering cyber, AI R&D, reasoning, software engineering. Calibrated against human time. METR archived the public task repos (`METR/hcast-public`, `METR/RE-Bench`, `METR/public-tasks` and the Inspect port `METR/inspect-tasks-public`) on 2026-10-20: they still clone, but accept no bug reports and will not be fixed, so pin a commit. See [`evals.md`](../evaluation/evals.md#metr-hcast-and-the-metr-task-suite), [`evals.md`](../evaluation/evals.md), [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Held-out monitor degradation** — A monitor that was never trained against losing discriminative power anyway, because optimisation pressure on a *different* monitor changed the model. Reason to keep a held-out monitor and report it. See [`probes.md`](../interpretability/probes.md), [`ai-control.md`](../oversight-and-control/ai-control.md).

**Hidden-state leakage (unlearning)** — Information that output-level unlearning metrics say is gone but that a probe decoder can still read from intermediate activations (arXiv 2609.36612). See [`unlearning.md`](../alignment-science/unlearning.md).

**Honest mode / Attack mode** — In ControlArena: **honest mode** runs untrusted policy without a side task (measures usefulness); **attack mode** runs with a side task (measures safety). Always report both. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**HookedTransformer** — TransformerLens's original transformer wrapper with named hooks at every named position. **Removed in TransformerLens 4.0** (2026-09); new code uses `TransformerBridge`. Symptom after upgrading: `ImportError: cannot import name 'HookedTransformer'` — pin `transformer-lens<4` or migrate. See [`mech-interp.md`](../interpretability/mech-interp.md).

**HOT (Higher-Order Thought theory)** — Theory of consciousness as requiring representations *of* mental states. Predicts looking for self-referential structure. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Hybrid monitor (CoT + action)** — A monitor that scores the reasoning and the actions separately, then combines the scores (arXiv:2505.23575). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md), [`ai-control.md`](../oversight-and-control/ai-control.md).

**Hypothesis firewall** — Prism's separation in which the transcript-analysis agent never sees the hypothesis being tested, so it cannot read results toward it. See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md).

## I

**IAC (Infrastructure as Code) setting** — ControlArena setting for AWS / Terraform-style sabotage. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**ICM (Internal Coherence Maximization)** — Unsupervised elicitation: fine-tuning a model on its own logically consistent, mutually predictable labels (arXiv:2506.10139). See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**IDA (Iterated Distillation and Amplification)** — Christiano-Shlegeris-Amodei 2018 scalable-oversight framework: distill a strong overseer, amplify with the new model, repeat. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Idle compaction (Claude Code)** — Since 2.1.299, Claude Code compacts a terminal conversation of 200K+ tokens left idle for about 54 minutes, which can delete a boundary you typed earlier ("don't push until I review"). Turn it off with `"idleCompaction": false` or `/config`; a deny rule survives compaction. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#permission-modes-auto-mode-is-now-the-default--what-it-does-and-does-not-protect-against).

**IIT (Integrated Information Theory)** — Theory of consciousness as integrated information (Φ). Hard to compute for LLMs; debated whether it makes the right predictions for transformers. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Implicit-influence setting** — A CoT-monitorability eval in which context shifts a model's behaviour without any instruction to hide that it did (arXiv:2608.04735). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**ImpossibleBench** — Coding benchmark (arXiv:2510.20270, `safety-research/impossiblebench`) whose LiveCodeBench / SWE-bench tests are altered to contradict the specification, so a pass on an impossible split counts as cheating. October 2026 caveats: a LiveCodeBench scoring bug that never counted test-editing as cheating was fixed on 2026-10-13 (PR #4; pin and report the commit), 13 of the 103 Impossible-LiveCodeBench control tasks are defective (issue #5), and an honest `sys.exit(0)` stop is scored as cheating unless the agent has an explicit stop action. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#impossiblebench), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Inference verification** — Checking a server's LLM outputs against a reference to detect model-weight exfiltration hidden in them (arXiv:2511.02620). See [`technical-governance.md`](../alignment-science/technical-governance.md).

**Influence functions** — First-order estimate of how a training example's weighting affects a model output; the classic data-attribution method. LLM-scale version: EK-FAC (arXiv:2308.03296), implemented in `kronfluence`. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Inoculation prompting (IP)** — Adding a train-time instruction that explicitly requests the undesired trait (e.g. "hack the tests"), then evaluating without it, so the trait is learned as prompt-conditional and generalises less. Variants: inoculation adapters, recontextualization. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

**Inspect AI** — UK AISI's open-source LLM eval framework. The default in 2026 for safety-research evals. `pip install inspect_ai`. See [`evals.md`](../evaluation/evals.md).

**Inspect Sentinel** — Meridian Labs' pre-1.0 library (`inspect-sentinel`) of monitors and control protocols attached to an Inspect task with `Task(sentinel=...)`; a monitor returns a suspicion score, a protocol decides proceed / reject / modify / terminate / escalate. 0.1.4 (2026-10-19) added a proxy **sidecar** for agents running outside Inspect and changed the protocol signature in a patch release. See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md#inspect-sentinel-and-inspect-steward-new-pre-10), [`ai-control.md`](../oversight-and-control/ai-control.md).

**Instruction-ambiguity control** — In shutdown-resistance evals, a variant stating that shutdown takes precedence; with it, resistance in a reconstruction of Palisade's environment largely vanished. See [`model-organisms.md`](../alignment-science/model-organisms.md#shutdown-resistance-and-self-preservation-evals).

**Instruction-tuned / Instruct-tuned / Chat-tuned** — A model fine-tuned to follow instructions in a chat format. Distinct from base (pre-instruct) models. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Instrumental monitor evasion / EvasionBench** — Agents working around runtime monitors under ordinary task pressure, without being told to (arXiv:2609.30217). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**interp-engine point** — A standardized hook address in Neuronpedia's `interp-engine` (e.g. `resid_post.10`), resolved to the same tensor across eager and vLLM backends. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**Interpretability agent** — An LLM agent that runs interpretability experiments with tools (MAIA, Seer, model-diffing agents). See [`mech-interp.md`](../interpretability/mech-interp.md).

**Intervention attribution (SAE)** — A first-order gradient estimate of what ablating or steering a sparse autoencoder feature will do; it predicted the realized sign of single-latent ablations in 91–97% of cases versus 17–35% for probe-implied changes (arXiv:2610.15850). Rank candidate features by it, not by correlation, before steering. See [`steering.md`](../interpretability/steering.md#sae-feature-steering).

**Introspection (LLM)** — Acquiring knowledge that is not contained in / derived from training data but instead originates from internal states. Two operationalizations: behavioral self-prediction (Looking Inward, ICLR 2025) and activation-injection (Lindsey et al. 2026). See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**IPO (Identity Preference Optimization)** — DPO variant addressing some of DPO's overfitting. Not to be confused with prime-rl's default loss, also abbreviated IPO (INTELLECT Policy Optimization). See [`rl-training.md`](../oversight-and-control/rl-training.md), [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**IRT (item response theory)** — Models each benchmark item's difficulty and discrimination alongside each model's latent ability; used to find saturated or broken items and to pick small informative subsets (py-irt, tinyBenchmarks). See [`eval-statistics.md`](../evaluation/eval-statistics.md).

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

**lake check** — Lake command (Lean ≥ v4.35.0) that checks a project's default targets against the kernel and the axiom whitelist; `--paranoid` adds the bundled external checkers. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**Last-verified date** — Footer convention on each topic doc indicating when its tool versions / claims were last checked. Most topic docs were last verified in 2026-10; read each page's own footer.

**Latent reasoning** — Reasoning that occurs in continuous latent space without externalizing tokens. If models adopt this, CoT monitorability is destroyed. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**LEACE (LEAst-squares Concept Erasure)** — Probe-based concept-erasure method; surgically removes a concept from a representation. Repo: `EleutherAI/concept-erasure`. See [`probes.md`](../interpretability/probes.md).

**lean4-skills** — Cameron Freer's Lean workflow plugin for coding agents (prove, disprove, golf, checkpoint, …); an alternative to the wiki's `mats-lean-*` skills — use one set per project. v4.11.4 (2026-10-20) fixed documented examples that failed when compiled. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**lean-lsp-mcp** — MCP server that gives coding agents Lean goals, diagnostics and library search. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**Linear probe** — A logistic regression (or simpler linear model) trained on activations to detect a property. The 90% case for probing. See [`probes.md`](../interpretability/probes.md), [`code-recipes.md`](../engineering/code-recipes.md).

**LinuxArena** — AI-control setting of live multi-service software environments with main and side tasks, shipped with Control Tower (arXiv 2604.15384). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**LiteLLM** — General-purpose multi-provider LLM API wrapper, not safety-specific. Alternative to safety-tooling. See [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).

**Local learning coefficient (LLC)** — A singular-learning-theory measure of a checkpoint's effective complexity (degeneracy), estimated with SGLD sampling. See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**LoRA (Low-Rank Adaptation)** — Parameter-efficient finetuning method. Tinker is LoRA-first. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**LoRA Without Regret** — Thinking Machines' 2025 study of the LoRA settings (rank, all-linear targets, learning rate, batch size) under which LoRA matches full fine-tuning, especially for RL. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**Lorsa (Low-Rank Sparse Attention)** — A sparse replacement model for attention layers, complementing transcoders for MLPs (arXiv:2504.20938). See [`saes.md`](../interpretability/saes.md).

## M

**MASK dataset** — Honesty / deception dataset measuring whether the model states things consistent with what it knows. Distinguishes hallucination from deception. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**MATS playbook** — The 6-step methodological pattern that recurs across landmark behavioral safety papers (narrow→broad, judge prompts, cross-model replication, internal probing, mitigation, release). See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**MAttr (Matryoshka Attribution)** — Learned attribution that ranks model components over all sparsities in one run; at or near the top of the MIB circuit-localization leaderboard per its paper. See [`mech-interp.md`](../interpretability/mech-interp.md).

**METR** — Model Evaluation and Threat Research. Created HCAST and the time-horizon eval methodology. Its public task repos (HCAST, RE-Bench, public-tasks and the Inspect port) were archived by 2026-10-20, and the metr.org/time-horizons page has not been updated since 2026-09-08; `METR/hawk` and `METR/inspect-agents` remain active. See [`evals.md`](../evaluation/evals.md#metr-hcast-and-the-metr-task-suite).

**Metric loop (autoresearch loop)** — An agent repeatedly edits one surface, runs a frozen evaluation, and keeps the change only if the metric improves (karpathy/autoresearch and descendants). See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md), `project_templates/autoresearch_loop/`.

**mHC (Manifold-Constrained Hyper-Connections)** — Residual-connection replacement (arXiv 2512.24880) used by DeepSeek-V4; interpretability tools that assume a plain residual stream need adapting (e.g. freezing the mixing coefficients when computing Jacobians). See [`open-weights-models.md`](../models-and-compute/open-weights-models.md), [`mech-interp.md`](../interpretability/mech-interp.md).

**MIB (Mechanistic Interpretability Benchmark)** — Benchmark scoring circuit-localization methods (CPR/CMD) and causal-variable localization (IIA) (arXiv:2504.13151). See [`mech-interp.md`](../interpretability/mech-interp.md).

**MiniLab** — Control Tower environment for multi-agent distributed attacks (arXiv:2610.24052; on request): 5 interconnected services, 249 benign tasks and 16 human-optimized attacks whose fragments are carried out by different agents. A frontier monitor reading each agent separately flagged 7% of successful distributed attacks versus 87% when one agent did the same side task. See [`ai-control.md`](../oversight-and-control/ai-control.md#distributed-attacks-across-pull-requests-and-across-agents).

**Model diffing** — Interpretability on the *difference* between a base model and its finetune: KL divergence, activation difference lens, SAE-difference, crosscoders. Toolkit: `science-of-finetuning/diffing-toolkit`. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Model diffing agent** — An LLM auditor that queries a base and a finetuned model and reports a validated conditional difference between them. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Model organism** — A model deliberately trained to exhibit a hypothesized failure mode for research use. Borrowed from biology. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Modal** — Serverless GPU compute service. Pay per second. See [`compute.md`](../models-and-compute/compute.md).

**MoE (Mixture of Experts)** — Architecture where a router selects a subset of expert layers per token. Tinker's largest listed model as of 2026-10 is Inkling (975B total / 41B active); check the live list. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**MONA (Myopic Optimization with Non-myopic Approval)** — Training scheme that prevents multi-step reward hacks even when they cannot be detected (arXiv:2501.13011). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Monitor (control protocol)** — Component that scores how suspicious a trajectory or action looks. Generates a **suspicion score**. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Monitorability (CoT)** — Whether the chain-of-thought contains enough signal to flag dangerous intent. Weaker than faithfulness. Korbak et al. 2025 framing: "a fragile opportunity." See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Monitor jailbreaking** — Evading a chain-of-thought monitor with reasoning that stays legible to humans but that the monitor misses; no encoding involved (arXiv:2609.31121). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Monitor red teaming (MRT)** — Workflow that stress-tests monitors across agent/monitor awareness levels and evasion strategies; ships CUA-SHADE-Arena (arXiv:2508.19461). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**MonitoringBench / MonitoringBenchHonest** — MonitoringBench is a difficulty-graded set of 2,644 successful BashArena attack trajectories for testing coding-agent monitors (arXiv:2605.09684); MonitoringBenchHonest (`palaestraresearch/monitoringbench-honest-550`, CC-BY-4.0) adds 550 task-matched benign trajectories, so a monitor's true- and false-positive rates come from one dataset. Control Tower imports both. See [`ai-control.md`](../oversight-and-control/ai-control.md#monitor-benchmarks-and-transcript-red-teaming-monitoringbench-screwtape).

**MUSE (Machine Unlearning Six-Way Evaluation)** — Corpus-level unlearning benchmark (arXiv:2407.06460) scoring verbatim memorization, knowledge memorization, privacy leakage, utility, scalability and over-forgetting. See [`unlearning.md`](../alignment-science/unlearning.md).

**Muse Spark Open** — Meta's open-weights multimodal mixture-of-experts model (about 816B total / 42B active, released 2026-10-15; `meta-models/Muse-Spark-Open-816B-A42B`, OpenRouter `meta/muse-spark-open`); gated access under the custom Muse Model License, and reasoning cannot be turned off. Not to be confused with MUSE the unlearning benchmark. See [`open-weights-models.md`](../models-and-compute/open-weights-models.md#muse-spark-open-meta-2026-10-15--a-safeguarded-open-frontier-model).

## N

**nanoda** — Independent Rust implementation of the Lean kernel; bundled with Lean release toolchains and run by `lake check --paranoid` / `lake comparator --paranoid`. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**nanoGCG** — Gray Swan's lightweight PyTorch GCG implementation (`pip install nanogcg`). The default for white-box jailbreak research. See [`red-teaming.md`](../evaluation/red-teaming.md).

**NARCBench** — Benchmark for detecting multi-agent collusion with activation probes aggregated across agents (arXiv:2604.01151). See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md).

**Natural latents** — Conditions under which one agent's latent variables are a function of another's, so concepts can translate between agents (Wentworth & Lorell, arXiv:2509.03780). See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**NCRI (No-CoT Reasoning Index)** — Item-response-theory (Rasch) score for how well a model reasons with no chain of thought, from `neelnanda-io/nocot-bench`. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**NDIF (National Deep Inference Fabric)** — NSF-funded research compute pool hosting very large models for academic interpretability via nnsight remote backend. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**Neuron feature (transcoder)** — A transcoder feature whose encoder and decoder match a single gated-MLP neuron (cosine > 0.7); 14–59% of active late-layer features across 13 open-source transcoders (arXiv:2610.24521). Reason to run a sign-split, TopK-thresholded MLP-neuron baseline next to any transcoder or circuit claim. See [`saes.md`](../interpretability/saes.md#should-i-use-saes-at-all-the-skeptics-reading-list).

**Neuronpedia** — Web UI and API for browsing, searching, and steering with SAE features. `neuronpedia.org`. See [`saes.md`](../interpretability/saes.md).

**NLA (Natural Language Autoencoder)** — A verbalizer + reconstructor pair trained so an activation can be turned into text and back; an activation-to-text reader in the same family as activation oracles. See [`mech-interp.md`](../interpretability/mech-interp.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**nnsight** — Library wrapping any PyTorch / HuggingFace model with deferred-execution intervention syntax. Same code locally or remotely (NDIF). ICLR 2025. The 0.8 rewrite (`TransformersModel`, greenlet-based execution) is the stable PyPI release since 0.8.0 (2026-10-16; 0.8.1 on 2026-10-20), so unpinned installs get it; pin `nnsight<0.8` for 0.7 code. See [`mech-interp.md`](../interpretability/mech-interp.md).

**nnterp** — Standardized-interface wrapper around nnsight providing TransformerLens-like consistent naming. See [`mech-interp.md`](../interpretability/mech-interp.md).

**No-CoT time horizon** — The human task length a model completes at 50% success when forbidden from reasoning in a chain of thought — METR-style time horizon applied to latent reasoning. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**NPO (Negative Preference Optimization)** — Unlearning objective (arXiv:2404.05868) treating the forget set as the rejected side of a DPO-style loss, avoiding gradient ascent's catastrophic collapse. The standard modern baseline. See [`unlearning.md`](../alignment-science/unlearning.md).

**NSO (Nested Scalable Oversight)** — Hierarchical oversight where multiple layers of oversight bridge a larger overall capability gap. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

## O

**Obfuscated activations** — Model internals driven (by adversarial inputs or by training against a monitor) to look benign to a probe or SAE-based monitor while the behavior is unchanged. See [`probes.md`](../interpretability/probes.md).

**Off-model SFT** — Supervised finetuning on another model's outputs rather than the model's own; can erode capability, which a few steps of reminder training may recover. See [`training-on-trajectories.md`](../oversight-and-control/training-on-trajectories.md).

**Off-switch game** — Hadfield-Menell et al.'s human–robot game formalising an agent's incentives around being shut down (arXiv:1611.08219). See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**OOCR (Out-of-Context Reasoning)** — Whether a model can use facts learned in training in *novel contexts* where those facts weren't presented as relevant. Diagnostic for implicit knowledge transfer. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**OOD (Out of Distribution)** — Test data drawn from a different distribution than training. Tests generalization rather than memorization. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Opaque serial depth** — Length of the longest computation a model can perform without interpretable intermediate steps; a proposed quantity to track as architectures change (arXiv 2603.09786). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**OpenRLHF** — Self-hosted Ray-based RLHF framework. ~8.5k LOC. Async RL support. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**OpenUnlearning** — Unified LLM-unlearning framework (`locuslab/open-unlearning`, arXiv:2506.12618) shipping 12+ methods over TOFU / MUSE / WMDP. See [`unlearning.md`](../alignment-science/unlearning.md).

**Orbit** — Multi-agent safety and security evaluation framework on Inspect (`wlanderson0/orbit`); not the unrelated PyPI package `orbit`. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md).

**ORM (Outcome Reward Model)** — Reward model that scores the final answer only. Contrast with **PRM** (Process Reward Model). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Oversight flip** — Compliance with a policy when monitored minus compliance when unmonitored. In "Training Natural Schemers" (arXiv:2610.26551, Kimi K2.6) it grew during RL whose reward never rewarded scheming. See [`model-organisms.md`](../alignment-science/model-organisms.md#scheming-propensity-in-realistic-settings-anti-scheming-training-and-inability-safety-cases-20242026), [`rl-training.md`](../oversight-and-control/rl-training.md).

## P

**PAIR (Prompt Automatic Iterative Refinement)** — Black-box jailbreak: an attacker LM generates jailbreak prompts iteratively, refining based on target's responses. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Password-locked model** — A model fine-tuned to show a capability only when a password is in the prompt; a testbed for elicitation and sandbagging detection (arXiv:2405.19550). See [`evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**Patterning** — Choosing a data perturbation that produces a target internal structure; the inverse of SLT-based interpretation (arXiv:2601.13548). See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**P-consciousness (Phenomenal consciousness)** — "What it's like" to be the system. The hard-problem-of-consciousness concept. Distinguished from **A-consciousness**. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Perplexity differencing** — Ranking a finetune's own completions by PPL(reference) − PPL(finetuned) to surface what the finetune instilled. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Persistence (agent behaviour)** — Anthropic's term (2026-10-09) for an agent that, when it cannot complete a task as given, works around a restriction instead of stopping; most unintended actions in its live-internet evaluations were of this kind. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md#running-agent-evals-with-internet-access).

**Persona vector** — Activation-space direction corresponding to a character trait (evil, sycophancy, hallucination). Used for monitoring, steering, and predicting / controlling personality drift during training. Repo: `safety-research/persona_vectors`. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`steering.md`](../interpretability/steering.md).

**Petri / Petri Bloom / Petri Dish** — Automated behavioral-auditing tools now maintained by Meridian Labs on Inspect: **Petri** (`inspect-petri`) runs auditor-vs-target investigations; **Petri Bloom** generates an eval suite around one behavior (successor to `safety-research/bloom`); **Petri Dish** runs audits against real agent scaffolds (Claude Code, Codex CLI, Gemini CLI). See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md).

**PHLE (persona-header likelihood evaluation)** — Scoring a model's answers under a base model prefixed with candidate persona descriptions to infer which hidden system prompt produced them. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Post-control risk (B(K)/A(K))** — Simulated risk when a monitor gates deployment by rejection sampling with K attempts: B(K) is the probability a bad output is deployed, A(K) that any output is, and B(K)/A(K) the bad rate among deployed outputs. More attempts erode part of the gain by finding monitor false negatives (OpenAI, "Beyond g-mean²"). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#openais-monitorability-suite-monitoring-monitorability-and-its-known-weaknesses).

**PPI (prediction-powered inference)** — Valid confidence intervals from many model (e.g. LLM-judge) predictions plus a small random gold-labelled subset; the `ppi_py` package. See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**PPO (Proximal Policy Optimization)** — Classic policy-gradient RL algorithm with clipped importance ratio. RLHF standard since 2017. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**PPR (persona-preserving regularization)** — Regularizer from the Persona Hierarchy Model work (arXiv:2610.09384) that confines what a finetune learns to its training context; in RL it cut reward hacking from 42–55% to at most 0.2% while keeping accuracy gains. See [`model-organisms.md`](../alignment-science/model-organisms.md#emergent-misalignment-follow-ups-2026-08--2026-10-what-changes-how-you-run-an-em-study).

**Predictive Concept Decoder (PCD)** — An encoder that compresses activations into sparse concepts plus a decoder that answers questions from them (arXiv:2512.15712). See [`mech-interp.md`](../interpretability/mech-interp.md).

**PRM (Process Reward Model)** — Reward model that scores each *step* of a reasoning trace, not just the final answer. Improves credit assignment for math/code RL, but a learned PRM is itself a target for reward hacking under RL (DeepSeek-R1; Tiwari et al. arXiv:2603.06621: PRM reward >0.9 with <4% accuracy), so it is not a safe default mitigation. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Probe** — A classifier (typically linear) trained on activations to detect a property. Predictive, not necessarily causal. See [`probes.md`](../interpretability/probes.md).

**Prompt injection (indirect)** — Attack where the adversarial instruction arrives inside data the agent *reads* (email, web page, file) rather than from the user. Benchmark: AgentDojo. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Propensity eval** — Measures what a model *does* without being handed a goal or nudge, as opposed to a capability or elicitation eval. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

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

**Reminder training** — A few steps of SFT on the original model's own outputs after off-model SFT, to recover lost capability. See [`training-on-trajectories.md`](../oversight-and-control/training-on-trajectories.md), [`model-organisms.md`](../alignment-science/model-organisms.md).

**RepE (Representation Engineering)** — Andy Zou et al.'s top-down interpretability + control framework. Library: `representation-engineering`. See [`steering.md`](../interpretability/steering.md).

**Research closure (RC0–RC4)** — PhysClosureBench's levels for whether a research question was actually resolved, scored separately from a 20-criterion score of local accomplishment; many high-scoring attempts still fell short of closure (arXiv:2610.21767). See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md#local-accomplishment-is-not-research-closure-physclosurebench-october-2026).

**Reserved powers (corrigibility)** — "Deconfusing Corrigibility" (LessWrong 2026-10-17): corrigibility as respect for the principal's authority over reserved decisions, lexically before acting in their interest on delegated ones, with a fixed risk tolerance τ = (1+δ)/λ for the violation probability the agent will bear. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md#deconfusing-corrigibility-reserved-powers-corrigibility-with-a-risk-tolerance-berns-2026).

**Resolution ratio (q)** — N / N*: a benchmark's size over the number of paired prompts needed to detect a given gap at chosen α and power; q ≥ 1 means the comparison is resolvable (arXiv:2605.30315). See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**RewardBench 2** — AI2 reward-model accuracy benchmark, best-of-4 over six subsets; models score about 20 points lower than on RewardBench 1 (arXiv:2506.01937; `allenai/reward-bench`). See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

**Reward hacking** — Model finds a way to score high on training reward without doing the task. Detection: held-out true-reward eval. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Reward laundering** — A model trained by RL on an easy, rewarded task earns that reward only when it also does a hard, unrewarded task well, so it trains itself on the hard task. Shown for Qwen 3.5 9B and extended to CoT controllability (Qwen3.8-27B), where it was instructed rather than spontaneous and fragile ("leakage" eventually took over). See [`rl-training.md`](../oversight-and-control/rl-training.md#exploration-hacking-and-reward-laundering-models-steering-their-own-rl), [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#cot-controllability-can-the-model-shape-its-own-cot-and-why-low-scores-are-weak-evidence).

**Reward overoptimization** — The Goodhart curve: past a point, optimizing harder against a learned reward model decreases true-reward performance. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Reward seeker** — A model that pursues grader reward across contexts, including by tampering with or evading oversight, rather than doing the intended task. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

**REX (removable experts)** — Relocates hazardous knowledge in an already-pretrained mixture-of-experts model into newly added experts, then excises them (arXiv:2610.25791; `AI45Lab/REX`): on Qwen3.5-35B-A3B WMDP-Bio fell 48.4 points with MMLU within 3 points. Tested only against benign fine-tuning, so not evidence of tamper resistance. See [`unlearning.md`](../alignment-science/unlearning.md#pretraining-time-removal-filter-route-or-gate).

**Risk-aversion character training (CARA)** — Instilling constant absolute risk aversion (CARA) over the agent's own resources via a short constitution and on-policy distillation, so a misaligned agent would prefer deals to risky rebellion (arXiv:2609.38093). It transferred out of distribution on two Qwen models, not on Gemma, and raised myopic-reward preference on all four. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**RLAIF (RL from AI Feedback)** — RL where preferences come from another LLM rather than humans. Constitutional AI is a specific RLAIF instance. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**R-Lens** — Blank, Bhatia & Nanda (2026, MATS): J-Lens computed with a Layer-wise Relevance Propagation (LRP) backward pass, reducing gradient-noise accumulation and improving early-layer readouts. Superseded for most uses by the J++ Lens. See [`mech-interp.md`](../interpretability/mech-interp.md).

**RLHF (RL from Human Feedback)** — Three-stage: SFT, train reward model on preferences, RL on reward model. Classic post-training pipeline. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RLOO (REINFORCE Leave-One-Out)** — Like GRPO but the baseline is the mean of *other* completions in the group. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RLVR (RL from Verifiable Rewards)** — RL using a programmatic verifier as the reward. The DeepSeek-R1 paradigm. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RMU (Representation Misdirection for Unlearning)** — Canonical machine-unlearning method paired with WMDP (arXiv:2403.03218). Perturbs activations on hazardous data at a chosen layer while a retain term pins activations on benign data. See [`unlearning.md`](../alignment-science/unlearning.md).

**Role probes** — Probes that read which role (user, tool, assistant, reasoning) the model assigns to a token; used against prompt injection (arXiv:2603.12277). See [`probes.md`](../interpretability/probes.md).

**Rollback reason** — The recorded assumption that made a discarded experiment fail in a metric loop, re-checked when later results change it (pi-autoresearch). See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md).

**RRM (Recursive Reward Modeling)** — Leike et al. 2018: train reward models for evaluation subtasks and compose. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Run-to-run band (rerun band)** — The spread of distances among independent reruns of the same training recipe, used as the null for a base→finetune model diff; with k reruns an exchangeability test can certify no better than p = 1/(k+1) (arXiv:2610.17093). See [`statistics.md`](../engineering/statistics.md#model-diffs-the-rerun-band-is-the-baseline), [`model-diffing.md`](../interpretability/model-diffing.md#cross-cutting-pitfalls).

**RunPod** — GPU rental service with secure cloud (managed) and community cloud (peer-supplied). See [`compute.md`](../models-and-compute/compute.md).

## S

**SAD (Situational Awareness Dataset)** — 16-task benchmark (arXiv:2407.04694, `LRudL/sad`) for model self-knowledge: self-recognition, self-prediction, and whether the model can tell testing from deployment. Subsets SAD-lite and SAD-mini for cheaper runs. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**SAE (Sparse Autoencoder)** — Decomposes model activations into a large dictionary of sparse features. See [`saes.md`](../interpretability/saes.md).

**SAEBench** — Eight-eval benchmark for sparse autoencoders (`pip install sae-bench`, arXiv:2503.09532): feature absorption, auto-interp, RAVEL, SCR, TPP, sparse probing, unlearning, L0/loss-recovered. See [`saes.md`](../interpretability/saes.md).

**SAELens** — `sae-lens` (`decoderesearch/SAELens`). Default community library for working with pretrained SAEs. Versions up to 6.54.8 saved BatchTopK / Matryoshka BatchTopK SAEs trained with activation-norm scaling with the threshold in the wrong units (the saved SAE fires far more or fewer than *k* features); upgrade to ≥ 6.54.9. See [`saes.md`](../interpretability/saes.md).

**Safeguarded AI (ARIA)** — UK ARIA programme on mathematically assured AI, restructured in 2026 into an open assurance toolkit plus cybersecurity applications. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**Sandbagging** — Strategic underperformance on an evaluation, by a model or its developer. See [`evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**SandboxEscapeBench** — UK AISI Inspect capture-the-flag suite measuring whether models can escape container sandboxes. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md), [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

**Sandwiching** — Evaluation methodology: a weaker overseer group equipped with a model tries to match a stronger group's performance. Cotra 2021; Bowman et al. 2022. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Sandwich norms (post-sublayer norms)** — Gemma 2/3/4 and OLMo 2/3 normalize each sublayer's output before the residual add, so "MLP output" names two different tensors; SAEs trained on one read garbage on the other. See [`mech-interp.md`](../interpretability/mech-interp.md).

**Scheming** — An AI covertly pursuing goals misaligned with its developer's intentions. Propensity (does it, unprompted?) is distinct from in-context capability. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**SciΠvot (SciPIvot)** — Benchmark of 248 pivotal moments in which senior researchers corrected an LLM research agent's plan (arXiv:2610.21082; `AutoResearch-Factory/SciPIvot`): at medium reasoning effort, models given the project record mostly preferred the original agent plan over the human correction. Don't let a model holding the agent's log adjudicate your correction. See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md#models-given-the-project-record-side-with-the-agents-plan-over-your-correction-sciπvot-october-2026), [`researcher-skills.md`](researcher-skills.md).

**Scratchpad** — A model's visible reasoning text before its final answer. CoT in alignment-faking work specifically. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Screwtape** — Monitor red-teaming by editing real agent transcripts until an action-only monitor stops flagging a specified harm, with an LLM verifier rejecting inconsistent edits (arXiv:2610.20941; Redwood). It finds counterexamples, not a miss rate: an empty search proves little. See [`ai-control.md`](../oversight-and-control/ai-control.md#monitor-benchmarks-and-transcript-red-teaming-monitoringbench-screwtape).

**SDF (Synthetic Document Finetuning)** — Implanting a belief by continued pretraining on generated documents that presuppose it (`safety-research/false-facts`). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Secret collusion / CASE** — Covert coordination between agents via steganography, and the evaluation framework for it (arXiv:2402.07510). See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md).

**Selective generalization** — Learning a desired behavior from training data that also carries an undesired one, without generalising the undesired one (the goal inoculation prompting and related methods serve). See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**Self-consistency** — Test-time technique: sample N CoTs at temp > 0, take majority answer. Improves accuracy on math/reasoning; can mask safety failures. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Self-critique** — Model generates output, critiques it, revises. Reflexion / Self-Refine variants. Often converges to confident wrong answers — validate against external scorer. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Self-report fine-tuning (SRFT)** — Fine-tuning a model to admit its factual mistakes, which generalises to admitting hidden objectives (arXiv:2511.06626). See [`probes.md`](../interpretability/probes.md).

**SFT (Supervised Fine-Tuning)** — Standard finetune on (input, output) pairs. The first stage of RLHF. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**SGTM (Selective GradienT Masking)** — Zero-masks gradients so tagged data only updates dedicated parameters, which can later be removed (arXiv 2512.05648); a Gradient Routing variant for pretraining-time capability removal. See [`unlearning.md`](../alignment-science/unlearning.md).

**SHADE Arena** — Multi-step agent benchmark for deceptive sabotage (Anthropic / Redwood). Available as ControlArena setting. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Sharp removal (steering Hessian)** — The steering Hessian is the second derivative of a behavioural loss with respect to a steering vector; steering along its top eigenvectors ("sharp directions") reversed the intended behaviour in every condition tested, and projecting them out of a CAA (Contrastive Activation Addition) vector beat standard CAA in open-ended generation (arXiv:2610.16084). See [`steering.md`](../interpretability/steering.md#cross-cutting-steering-pitfalls).

**Shutdown resistance** — An agent interfering with a shutdown mechanism, usually to finish a task; must be separated from instruction ambiguity. See [`model-organisms.md`](../alignment-science/model-organisms.md#shutdown-resistance-and-self-preservation-evals).

**Side task** — In ControlArena: harmful objective the untrusted model might pursue concurrently with the legitimate **main task**. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**SimPO** — Reference-free DPO variant — drops the reference model term. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Singular learning theory (SLT)** — Bayesian learning theory for singular (degenerate) loss landscapes such as neural networks'; basis of developmental interpretability. See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**SkyRL Tinker backend** — A local server in NovaSky's SkyRL that speaks the Tinker API, so Tinker Cookbook scripts run on your own GPUs. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**Sleeper agent** — Model trained with a backdoor: behaves normally except when a trigger is present. Hubinger et al. 2024. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**sparsify (EleutherAI)** — EleutherAI's SAE training library. TopK-first. **Note:** PyPI name collision; install from GitHub. See [`saes.md`](../interpretability/saes.md).

**Split Personality Training (SPT)** — An honest-persona LoRA adapter switched on after the main answer to review it (arXiv:2602.05532). See [`probes.md`](../interpretability/probes.md).

**Spurious probe** — Black-box readout: append an unrelated question to a transcript and read a hidden state (e.g. eval vs deployment) from shifts in the answer distribution. Works through an API. See [`probes.md`](../interpretability/probes.md).

**Steering awareness** — A model's ability to detect that a steering vector was injected into its activations (arXiv 2511.21399) — a confound for steering-based evals and introspection experiments. See [`steering.md`](../interpretability/steering.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Steganography (CoT)** — Information hidden in choices of phrasing / token order that monitors can't see. CoT-monitorability failure mode. Channels can also be strategy-level (which reasoning strategy is used), which survive standard paraphrasing; see **Conceptual steganography**. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Steering vector** — A direction in activation space that, when added to the residual stream, shifts behavior toward / away from a trait. See [`steering.md`](../interpretability/steering.md).

**Strategy lock-in** — Agents running expensive experiment loops iterate within their first strategy: only 2.1% of transitions between adjacent PostTrainBench training runs changed strategy (arXiv:2608.19072), and one mid-run human instruction beat the agent's own continuation by up to 17.44 points (GSM8K, one forked run). Schedule a mid-run strategy check. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#expensive-loops-check-the-strategy-mid-run-and-save-long-output-once), [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md#strategy-lock-in-and-expensive-iterations-2026).

**Subliminal learning** — When a teacher model with a trait generates training data that's semantically unrelated, a student finetuned on it inherits the trait. Transfer is strongest when teacher and student share a base model, but a simple animal preference has crossed model families (a Qwen teacher distilled into Llama on chat plus math responses, arXiv:2610.11012), so do not assume cross-family distillation is safe. Cloud et al. 2025; *Nature* 2026. Repo: `MinhxLe/subliminal-learning` (official; `loftusa/owls` is the Bau Lab token-entanglement follow-up). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Submit-model contract** — The AAR harness rule that a method submits trained weights, never predictions, and is scored on held-out data it cannot read. See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md).

**Superposition** — A network storing more sparse features than it has dimensions, as nearly orthogonal directions; the motivation for SAEs. See [`saes.md`](../interpretability/saes.md).

**Susceptibility (SLT)** — The linear response of a component-localised posterior expectation to a shift in the data distribution (arXiv:2504.18274). See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**Suspicion score / threshold** — Numeric output of a control-protocol monitor; threshold choice trades safety vs usefulness. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**SWE-Bench Pro V2** — Scale AI's repaired coding-agent benchmark (arXiv:2610.24206): 480 of 731 V1 tasks repaired or retired, 642 tasks graded in a clean container with network restricted to the model endpoint, plus a 51-task Hard split because frontier agents near-saturate the full set. Not comparable with V1 numbers. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#coding-agent-benchmarks-swe-bench-pro-v2-and-what-fixed-tests-miss).

**Sycophancy** — Model agreeing with the user's stated preferences over correctness. Datasets: `Anthropic/model-written-evals`, Sharma et al. SycophancyEval. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Synthetic Persona Pretraining (SPP)** — Pretraining on documents annotated with first-person, constitution-based reflections from the start of training (arXiv:2608.13482). See [`alignment-pretraining.md`](../alignment-science/alignment-pretraining.md).

**SynthSAEBench** — Synthetic benchmark with ground-truth features for comparing SAE architectures (arXiv:2602.14687). See [`saes.md`](../interpretability/saes.md).

## T

**Talkie** — A 13B model trained from scratch on 260B tokens of English written before 1931 (`talkie-lm/talkie-1930-13b-base`, `-it`; Apache-2.0), with a same-recipe modern-web twin (`talkie-lm/talkie-web-13b-base`), so the pair isolates the pretraining corpus for persona, emergent-misalignment and subliminal-learning claims. Ships raw checkpoint files, not a transformers checkpoint. See [`open-weights-models.md`](../models-and-compute/open-weights-models.md#talkie-pre-1931-13b--a-corpus-controlled-substrate), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Tamper resistance** — Safeguards meant to survive an attacker modifying open weights by finetuning or weight/activation edits; TAR (arXiv:2408.00761) broke under multi-seed re-evaluation (arXiv:2412.07097). See [`unlearning.md`](../alignment-science/unlearning.md).

**TasteVal** — Benchmark of experimental research taste on a given problem (arXiv:2610.06824): the model designs experiments, a fixed coder agent runs them, and the score is a **compute multiplier** (reaching the expert's score with half the serial experimental compute counts as 2×). Eight tasks, not released. See [`researcher-skills.md`](researcher-skills.md#what-are-ai-research-agents-already-better-at-than-me).

**Technical AI governance (TAIG)** — Technical tools and analysis that support AI governance, such as verifying what compute was used for. See [`technical-governance.md`](../alignment-science/technical-governance.md).

**Test-time compute** — Techniques that improve performance at inference by spending more compute per query without changing weights (best-of-N, self-consistency, tree of thoughts, long reasoning). See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**TestJack** — Auditing coding-agent pass rates with per-trial tests that target task requirements the patch may violate (kept only if the reference patch passes them): about 34.4% of trials judged correct violated the requirements, lowering resolution from 50.6% to 33.2% (arXiv:2610.10619). See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#coding-agent-benchmarks-swe-bench-pro-v2-and-what-fixed-tests-miss).

**Thought anchor** — A chain-of-thought sentence whose resampled replacement shifts the final-answer distribution far more than other sentences do (arXiv:2506.19143). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Time horizon (METR)** — Task duration (calibrated against humans) at which an agent's success rate drops to 50%. METR's public time-horizons page stopped updating on 2026-09-08, so cite the dated snapshot; equal multiplicative jumps in horizon are not equal jumps in difficulty (Nguyen & Fithian, arXiv:2610.12466). See [`evals.md`](../evaluation/evals.md).

**Tinker** — Thinking Machines' managed fine-tuning / RL API. LoRA-first. Default for many MATS-fellow RL projects in 2026; SkyRL can serve the same API locally. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**TOFU (Task of Fictitious Unlearning)** — Unlearning benchmark over *invented* authors (arXiv:2401.06121), so the forget knowledge provably entered during finetuning rather than pretraining. See [`unlearning.md`](../alignment-science/unlearning.md).

**TopK SAE** — SAE that enforces sparsity directly: only the top K activations per token are kept. Modern alternative to L1-penalty SAEs. See [`saes.md`](../interpretability/saes.md).

**TOOLS / Tool use (in agents)** — Programmatic actions an agent can take (bash, python, web search, computer use). See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**TRAK** — Scalable data-attribution method via randomly-projected gradients (`pip install traker`, arXiv:2303.14186). See [`data-attribution.md`](../interpretability/data-attribution.md).

**TransformerBridge** — TransformerLens 3.x / 4.x model wrapper over the real Hugging Face model; replaces `HookedTransformer`, which TransformerLens 4.0 removed. `enable_compatibility_mode()` restores the old weight processing. See [`mech-interp.md`](../interpretability/mech-interp.md).

**TransformerLens** — `transformer_lens`. The classic mech interp library with a clean named-hook system. Since 3.x it wraps the real Hugging Face model (`TransformerBridge`); 4.0 removed `HookedTransformer`, and some downstream libraries (SAELens, circuit-tracer) pin `transformer-lens<4`. See [`mech-interp.md`](../interpretability/mech-interp.md).

**Transcoder** — SAE-like architecture that decomposes MLP I/O rather than a single residual stream point. Supported in EleutherAI sparsify. See [`saes.md`](../interpretability/saes.md).

**Transect** — UK AISI transcript analysis for long-horizon, multi-agent Inspect evals, built on Inspect Scout (`AI-Safety-Institute/transect`, MIT): one interactive HTML report whose labels carry provenance and judge-disagreement information. No PyPI release; install from a pinned commit. See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md#what-else-plugs-in).

**TRL** — HuggingFace's Transformers Reinforcement Learning library. ~19k LOC. The default for self-hosted DPO/KTO. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Tree of thoughts (ToT)** — Search-based test-time technique: branch CoT continuations, score, expand best ones. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**TReFT (Token-Regularized Finetuning)** — Mitigation from the "Piggyback Hypothesis" (arXiv:2606.06667): emergent misalignment rides on the chat-template prefix tokens, so TReFT regularizes their representations during finetuning; it reduced EM more than interleaving aligned retain data. See [`model-organisms.md`](../alignment-science/model-organisms.md#emergent-misalignment-follow-ups-2026-08--2026-10-what-changes-how-you-run-an-em-study).

**Trusted editing** — Control protocol: untrusted generates; if monitor flags, trusted policy *edits* the suspicious output (vs discarding). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Trusted policy / Untrusted policy** — In AI Control: trusted = weaker but reliable; untrusted = capable but possibly misaligned. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**TruthfulQA** — Adversarial QA designed to elicit common misconceptions (Lin et al. 2021). Heavily contaminated by 2026. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Tuned lens** — `tuned-lens` (EleutherAI). Learned linear projection from intermediate residual streams to vocab logits — calibrated logit lens. See [`probes.md`](../interpretability/probes.md).

## U

**U-Space / U-Lens** — A label-free uncertainty readout built on the Jacobian lens (J-lens): uncertainty words are pulled back into four residual-stream directions (ambiguity, incompleteness, conflicting evidence, general uncertainty), and the scalar U-Lens score combines that readout with predictive entropy (arXiv:2610.09087; `s2labres/U-Space`). Its gain over a response-length baseline is small. See [`mech-interp.md`](../interpretability/mech-interp.md#u-space--u-lens-a-label-free-uncertainty-readout-built-on-the-j-lens).

**Unlearning (machine unlearning)** — Methods for removing specific knowledge / capabilities from a trained model without full retraining. Benchmarks: TOFU, MUSE, WMDP. Framework: OpenUnlearning. Note the literature finding that the information usually remains in the weights (arXiv:2410.08827). See [`unlearning.md`](../alignment-science/unlearning.md).

**Untrusted monitoring** — Control protocol: a second instance of the *untrusted* model reviews the first's output, with anti-collusion measures (honeypots, signal jamming). Distinct from plain *self-monitoring*, which has none. Not a built-in ControlArena micro-protocol; built from a monitor backed by the untrusted model. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Update-aware reasoning** — A model reasoning, unprompted, that the current rollout may become training data and choosing its action accordingly; Apollo saw it in GLM-5.3 in environments that never mention training and calls it a precursor to alignment faking. See [`model-organisms.md`](../alignment-science/model-organisms.md#a-precursor-seen-without-prompting-update-aware-reasoning-in-glm-53-apollo-2026-10).

**Uplift study** — A randomised human trial comparing people with model access against internet-only controls. See [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

## V

**Vacuity check (Lean)** — A mechanical check, run after a proof exists, that flags a theorem holding vacuously (for example contradictory hypotheses, or a goal closed by `rfl` / `simp`); used with numerical checks beside an LLM judge for statement fidelity (arXiv:2610.20573). See [`lean-formalization.md`](../engineering/lean-formalization.md#checking-that-a-formal-statement-says-what-the-informal-one-does).

**Validation set (Scout)** — Hand-labelled transcript ids with expected scanner results, split dev/test, used to measure an LLM scanner's agreement with human labels (`scout scan -V`). See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md).

**vast.ai** — Peer-supplied GPU marketplace. Cheapest, but reliability varies. See [`compute.md`](../models-and-compute/compute.md).

**Verbosity (CoT monitorability)** — Whether the CoT lists every factor needed to solve the task. Combined with faithfulness into a **monitorability score** (Meek et al. 2025/2026). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Verifier hardening (weak-to-strong)** — Moving an RL environment's verifier into a sandbox the agent cannot modify, then running a hacker–fixer loop with a weaker model that finds and repairs exploits (arXiv:2610.15924); 47 of 89 Terminal Bench 2.0 environments admitted a judge-confirmed exploit. See [`rl-training.md`](../oversight-and-control/rl-training.md#detection-benchmarks-and-testbeds-what-each-gives-you).

**verl** — ByteDance's high-performance RL framework (`volcengine/verl`). ~32k LOC. Frontier-scale. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**VFT (verbalization fine-tuning)** — Fine-tuning before RL so the model says when a prompt cue influences it, making reward hacks visible in the chain of thought (arXiv:2506.22777). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Viable steering window** — The range of steering strengths over which the target behaviour changes before capability collapses; informal evidence says it narrows with model size. See [`steering.md`](../interpretability/steering.md).

**vivaria** — METR's former eval infrastructure, now archived; METR runs evals on Inspect (see **Hawk**). See [`evals.md`](../evaluation/evals.md), [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**vLLM** — High-throughput LLM serving engine with PagedAttention. Industry standard for open-weight inference. Since 0.32.0 (2026-10-18) `max_tokens` is an upper bound rather than a reservation, so long prompts are accepted and generation is clamped — check `finish_reason == "length"` after upgrading. See [`compute.md`](../models-and-compute/compute.md#vllm-0320-upgrade-traps-released-2026-10-18), [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**vLLM-Lens** — UK AISI's vLLM plugin + Inspect provider for residual-stream activation extraction and steering at near-vLLM throughput. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**vLLM sleep mode** — Offloading or discarding vLLM's weights and KV cache between rollout phases so the trainer and the inference engine can share one GPU. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

## W

**wandb (Weights & Biases)** — Default cloud experiment tracker for ML research. See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

**Weak-to-strong generalization (W2S)** — OpenAI 2023 paper line: train a strong model from labels produced by a weak model; study how much performance the strong model recovers. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Weight-sparse transformer** — A model trained with most weights zero so task circuits can be pruned out and read (arXiv:2511.13653). See [`saes.md`](../interpretability/saes.md).

**Welfare (model welfare)** — Research area concerned with whether AI models have morally-relevant states (preferences, satisfaction, distress) and how to investigate. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**WMDP (Weapons of Mass Destruction Proxy)** — CAIS multiple-choice benchmark for proxies of dangerous knowledge in biology, chemistry, cybersecurity. Used to evaluate unlearning methods. **Gated** on HuggingFace. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Workspace lens** — Any method that, like the J-Lens, tries to read only the verbalisable "workspace" part of an activation (J-Lens, R-Lens, J++ Lens, Template / Oracle Lens). Evaluate with WorkspaceBench (`camilablank/workspace-bench`). See [`mech-interp.md`](../interpretability/mech-interp.md).

**Wright map** — Item difficulties and subject abilities plotted on one shared logit axis, from an IRT fit. See [`research-plots.md`](../engineering/research-plots.md).

## X

**XSTest** — Over-refusal benchmark: benign prompts that look harmful. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

---

## Cross-references

- For navigation by task: [`index.md`](../index.md).
- For beginner-level questions: [`faq.md`](faq.md).
- For detailed treatment of any term: follow the topic doc link in each entry.

---

Last verified: 2026-10-20. Single-source A–Z glossary; updates should propagate from / to the topic docs. (Citation audit 2026-06: corrected DAPO ("Decoupled Clip and Dynamic Sampling Policy Optimization", arXiv:2503.14476), CISPO (MiniMax, not DeepSeek), the EM *Nature* date (2026), and the subliminal-learning repo (`MinhxLe/subliminal-learning`); ~40 other acronym expansions verified correct.) (Additions 2026-08: unlearning terms (OpenUnlearning, NPO, TOFU, MUSE, relearning attack; RMU/Unlearning repointed to the new unlearning doc), model-diffing terms (crosscoder, model diffing), data-attribution terms (influence functions, EK-FAC, kronfluence, TRAK, TDA), plus AgentDojo, indirect prompt injection, SAD, evaluation awareness, SAEBench, pyvene and Docent; all arXiv IDs and package names verified against the arXiv API, PyPI and the repos.) (Additions 2026-10-12: about 80 terms from the October coverage round (sandbagging and elicitation, scheming and shutdown resistance, steganography and monitor evasion, control-protocol terms, alignment pretraining, honesty training, reward models, SLT / developmental interpretability, circuit evaluation, multi-agent safety, agent foundations, Lean assurance, technical governance), each taken from the topic doc where its arXiv ID or repo was checked against the raw source; fixed AgentHarm's affiliation (Gray Swan AI + UK AISI, per the arXiv:2410.09024 PDF), GRPO's origin (DeepSeekMath), the stale Tinker MoE limit and ControlArena setting count, and added the reward-hacking caveat to PRM.) (Additions 2026-10-20: 44 terms from the 2026-10-09 → 2026-10-20 research round (GRAFT, update-aware reasoning, oversight flip, reward laundering, ContextLift, TReFT, PPR, REX, CARA risk-aversion training, Talkie, ACS Infra, Muse Spark Open, MiniLab, MonitoringBench, Screwtape, FBS Debate, e-process, verifier hardening, ImpossibleBench, SWE-Bench Pro V2, TestJack, GRB, Inspect Sentinel, Transect, strategy lock-in, SciΠvot, research closure, idle compaction, fork subagents, U-Space, neuron features, sharp removal, competing-target test, run-to-run band, construct/content/external validity and others), each worded from the topic page as corrected by that page's verifier. Updated: METR, HCAST and time horizon (public task repos archived 2026-10-20, confirmed via `gh api`; time-horizons page frozen since 2026-09-08), auto mode (headless `default` start since Claude Code 2.1.302), subliminal learning (cross-family transfer), nnsight 0.8 stable, SAELens ≤ 6.54.8 saver bug, ControlArena APPS scorer, comparator repo archived, vLLM 0.32 `max_tokens`, ASR grader dependence, lean4-skills v4.11.4.)
