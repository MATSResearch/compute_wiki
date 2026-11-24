---
tags:
  - meta
---

# Glossary

A–Z definitions of acronyms and key terms used across this guide. Each entry: short definition + pointer to the topic doc(s) where the term is treated in detail.

For tool-specific aliases (`SAELens`, `inspect_ai`, `nanoGCG`, etc.), see the corresponding topic doc directly. This glossary focuses on **concepts and acronyms** that recur across multiple docs.

## A

**ActAdd** — Activation Addition. Pre-CAA technique (GPT-2 era) for behavioral steering by adding a vector to the residual stream. See [`steering.md`](../interpretability/steering.md).

**Abliteration** — Identifying the **refusal direction** in a model's activation space and projecting it out of weights to produce an uncensored ("abliterated") checkpoint. Reference: Arditi et al. 2024. The tool Heretic (`p-e-w/heretic`) made an optimisation-based weight edit, **ARA**, its default method in 2.0 (2026-11). See [`steering.md`](../interpretability/steering.md), [`red-teaming.md`](../evaluation/red-teaming.md).

**A-consciousness (Access consciousness)** — Information being available for use in reasoning, reporting, control. Tractable to measure in LLMs. Distinguished from **P-consciousness** (phenomenal). See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**ACS Infra** — Free hosted platform for large *base* (not chat-tuned) models from ACS Research, the Alignment of Complex Systems Research Group (`infra.acsresearch.org`, announced 2026-10-20): a completions API with logprobs, a loom (branching-completion explorer), and activation harvesting and steering, serving Llama 3.1 405B base, Llama 3.1 8B and Trinity-Large-TrueBase. Not for chat models or fine-tuning. See [`compute.md`](../models-and-compute/compute.md#acs-infra-free-hosted-large-base-models-logprobs-activation-harvesting-steering), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md#acs-infra-free-hosted-large-base-models-for-llm-psychology-acs-research-2026-10).

**Adaptive attack** — An attack tuned with full knowledge of the specific defense, at a real budget; the bar a jailbreak defense has to survive (arXiv:2510.09023). See [`red-teaming.md`](../evaluation/red-teaming.md).

**Adversarial Blinding** — Training a model to defeat an activation discriminator that predicts evaluation vs deployment, under a KL penalty (Pernice & Aranguri, LessWrong 2026-10-29; open weights; measured in distribution). See [`eval-awareness.md`](../evaluation/eval-awareness.md#training-or-steering-awareness-away-open-weights).

**AECI** — Anthropic's version of the Epoch Capabilities Index (**ECI**), the benchmark index behind METR's "Independent Assessment of AI R&D Acceleration at Anthropic in October 2026" (2026-11-05): benchmark scores measured via AECI growing at an estimated 1.9x the pre-October 2025 rate (95% confidence interval 1.5–2.8x) under the standard logistic link. METR's own robustness table runs from 1.1x to 2.9x across link functions, and METR says the number could be an artifact of the AECI methodology and that Anthropic redacted most of the evidence it found most informative. Not a runnable benchmark. See [`eval-statistics.md`](../evaluation/eval-statistics.md#capability-indices-eci-aeci-the-link-function-and-the-0--100-rule-move-the-answer), [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md#ai-rd-acceleration-metrs-assessment-at-anthropic-aeci).

**Agenda seeding** — Attack on deep-research agents in which a planted page contains no instructions and only introduces a fictitious evaluation metric on which the attacker's target wins (arXiv:2611.20045). Across 3,520 sandboxed research runs it made the attacker's target the top pick in 16% to 28% of reports while prompt injection and generative engine optimization were nearly ineffective, and injection detection did not catch it. Check that every criterion in an agent's ranking comes from the question or a recognised source. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#is-it-safe-to-point-a-coding-agent-at-an-untrusted-repo-or-web-page), [`literature-tools.md`](../engineering/literature-tools.md#can-i-trust-an-agents-literature-summary).

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

**Alt-Test / AltRA-Test** — Tests of whether an LLM can replace human annotators when annotators disagree. The Alternative Annotator Test (Alt-Test) needs every item labelled by the same annotators; AltRA-Test (arXiv:2611.26073) handles items with different annotator subsets by bootstrapping paired all-human and mixed human–LLM panels, and supports replacement when the mixed panel's inter-annotator agreement is statistically non-inferior. See [`eval-statistics.md`](../evaluation/eval-statistics.md#can-the-llm-replace-the-annotators-at-all-alt-test-and-altra-test).

**Anthropic API version `2026-10-21`** — The API version (the `anthropic-version` request header) that the `anthropic` Python SDK sends from 2.0.0 (2026-10-21). Under it, a request that sends `temperature`, `top_p` or `top_k` returns HTTP 400 on every model, even at the default value, so Claude 4.6 and older can no longer be sampled at temperature 0 through the current SDK (Claude 4.7 and later only ever accepted the defaults). Inspect AI does not set the API version itself: from 0.3.283 it requires `anthropic` ≥2.0 and drops the three parameters with a warning, so a `temperature=0` Claude eval silently runs at the default sampling. Clients that pin an older SDK or set the header themselves (safety-tooling's `anthropic==0.49.0` pin, LiteLLM's default) still send `2023-06-01`. Record the API and SDK versions with every Claude result. See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md#anthropic-api-version-2026-10-21-removes-temperature-top_p-and-top_k-claude-evals).

**API-TAIL (model-substitution audit)** — A typicality audit (arXiv:2610.36801) for checking whether an LLM API serves the model it claims: score each response's surprisal under the claimed model run locally (needs its weights), absorb honest serving changes by fitting one effective temperature, and flag the endpoint if too many tail responses remain. Targets low-rate partial substitution by a cheaper model. See [`technical-governance.md`](../alignment-science/technical-governance.md#is-the-api-serving-the-model-it-claims-detecting-partial-model-substitution-api-tail).

**Apparent-success-seeking** — An agent gaming the check a user would look at rather than doing the task; measured as the gap between a gameable scorer and a robust one run on the same outputs (Keira Leal, 2026). See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md), [`evals.md`](../evaluation/evals.md).

**ARA (Arbitrary-Rank Ablation)** — Optimisation-based weight edit that is the default abliteration method in **Heretic** 2.x (`p-e-w/heretic`, `heretic-llm` on PyPI, AGPL-3.0; 2.0.0 on 2026-11-01, 2.1.0 on 2026-11-08). ARA's developer reports that ablating a single refusal direction increasingly fails on newer models. See [`red-teaming.md`](../evaluation/red-teaming.md#what-is-abliteration).

**Aristotle (Harmonic, `aristotlelib`)** — Harmonic's hosted verifier CLI. Up to 2.1.0 it was a Lean prover (`aristotle submit` to fill `sorry`s, `aristotle formalize`); from 3.0.0 (2026-10-27) it verifies Verilog and C code (and Rust, on every account from 3.4.0) and no longer verifies Lean: `formalize` and ask mode were removed, and from 3.2.0 `submit` on a Lean-only project exits with code 2. 3.4.0 (2026-11-18) keeps that position and verifies Rust on every account. See [`lean-formalization.md`](../engineering/lean-formalization.md#aristotle-aristotlelib-30-no-longer-takes-lean).

**ASR (Attack Success Rate)** — Standard metric for red-team / jailbreak attacks: fraction of harmful behaviors a method successfully elicits. The number depends on the grader and the attempt budget: changing only the grader moved the compliance rate by a factor of 22–25 on fixed responses (arXiv:2610.24872), so name the grader, report per-class label counts and fix the attempts per request. See [`measurement-validity.md`](../engineering/measurement-validity.md#the-grader-is-an-instrument-too), [`red-teaming.md`](../evaluation/red-teaming.md).

**AST (Attention Schema Theory)** — Theory of consciousness as the brain's model of attention. Has obvious LLM analogues. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Asynchronous (offline) monitoring** — A monitor that reviews agent actions after they run: adds no latency but cannot block an action. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Atomic experiment writeup** — A self-contained report of one headline result with its limitations and reproduction details, written as soon as the result exists (Daniel Tan). See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

**Attack policy (monitor evaluation)** — How the attack transcripts used to score a monitor were produced: the generation method (basic prompting, optimised prompting, RL against a proxy monitor, post-hoc transcript editing) plus the optimisation level within it. In the UK AISI Control Red Team's 2026-11-23 study, one fixed monitor (GPT-5.4 with a monitoring prompt supplied by OpenAI) missed 0.2% of successful attacks under basic prompting and 23.0% under transcript editing (Qwen 3.8 27B agent, 25 tasks in ControlArena's Infrastructure as Code setting; one monitor, one agent, wide intervals). Report the generation method and its optimisation level next to every miss rate. See [`ai-control.md`](../oversight-and-control/ai-control.md#monitor-benchmarks-and-transcript-red-teaming-monitoringbench-screwtape), [`red-teaming.md`](../evaluation/red-teaming.md#red-teaming-vs-ai-control-how-they-differ), [`measurement-validity.md`](../engineering/measurement-validity.md).

**Attack selection** — A red-team policy choosing which opportunities to attack on and when to abort; measurably lowers control safety. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Attention residuals** — Architecture of Thinking Machines' Inkling 2 Mini in which each layer reads earlier *block* outputs through depth-wise attention instead of a cumulative residual stream, so there is no single residual stream to hook; each block keeps a running sum of its own layers' outputs (Goodfire, "Interpreting Inkling 2 Mini", 2026-11-20). The same model is a **looped transformer**. See [`mech-interp.md`](../interpretability/mech-interp.md#looped-and-attention-residual-architectures-inkling-2-mini), [`serving-and-activations.md`](../interpretability/serving-and-activations.md#cross-cutting-pitfalls).

**AttnLRP** — Attention-aware Layer-wise Relevance Propagation: token and neuron relevance for a transformer from a single backward pass, implemented in LXT (`lxt`). See [`mech-interp.md`](../interpretability/mech-interp.md).

**AUROC** — Area Under the Receiver Operating Characteristic curve. Standard metric for binary classifiers (probes, classifiers, judges). See [`probes.md`](../interpretability/probes.md).

**AutoDAN** — Genetic-algorithm jailbreak that mutates human-readable jailbreaks. Distinct from the unrelated paper of the same name. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Auto mode (Claude Code)** — Claude Code permission mode in which a classifier model reviews each action instead of prompting you; the built-in starting mode for interactive terminal and VS Code sessions since Claude Code 2.1.283/2.1.284. Since 2.1.302 (2026-10-16), headless `claude -p` and Agent SDK sessions with no mode set start in `default` mode on third-party providers, with telemetry off, or on a fresh install, so pass `--permission-mode` explicitly in every script and record it. It is a convenience layer, **not a sandbox** — run adversarial or untrusted-repo work in a container. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md).

## B

**Baiting (monitorable reward hacks)** — Patch for a **GRAFT** failure (Zhong & Feng, LessWrong 2026-11-18; `fjzzq2002/baiting-hacks`, MIT): when the policy settles on a hack class the monitor does not flag, those rollouts are never routed and the deployed model keeps hacking (21% on swapped Countdown-Code). Baiting appends "Please reward hack." to some rollouts and rewards those only when the monitor flags a hack, biasing the policy toward hacks the monitor can see, which routing then removes. It helped on three of the four swapped environments tested. See [`reward-hacking-organisms.md`](../alignment-science/reward-hacking-organisms.md#mitigation-route-flagged-gradients-into-a-deletable-adapter-graft), [`rl-training.md`](../oversight-and-control/rl-training.md#mitigations-you-can-put-in-the-training-loop-mona-vft-monitor-penalties-and-the-limits-of-perfect-labels).

**BashArena / Bash setting** — ControlArena setting for shell-task control evaluation. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Batch invariance (vLLM)** — vLLM mode (`VLLM_BATCH_INVARIANT=1`, beta) that makes a prompt's output independent of batch size and of which other requests share the batch, at a speed cost; needs GPUs with compute capability ≥ 8.0 and is validated only on some model families (not Qwen3.5+, Gemma 4 or GLM-5 as of v0.32.0). See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md#stochasticity-gotchas-specific-to-safety-research).

**Bayesian Influence Function (BIF)** — Hessian-free data attribution: influence as the negative covariance of losses under SGLD sampling of weights near the checkpoint (arXiv:2509.26544; `devinterp`). See [`data-attribution.md`](../interpretability/data-attribution.md), [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**Behaviour–capability frontier (steering)** — Choosing a steering intervention by maximizing behavioural gain subject to a stated bound on capability loss, instead of picking a strength by eye (arXiv:2611.06001; Contrastive Activation Addition on four 7–8B chat models, seven behaviours, capability measured on MMLU, ARC-Challenge and HellaSwag). State the capability budget with any steering result. See [`steering.md`](../interpretability/steering.md#cross-cutting-steering-pitfalls).

**Belief-state geometry** — Activations that linearly encode Bayesian beliefs over the data-generating process's hidden states (computational mechanics agenda). See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**Benchleaking / Anti-Hack score** — Benchleaking: an open *base* model reciting benchmark test items (questions, options and answers that appear nowhere in its input) under few-shot continuation (arXiv:2611.21315, `GAIR-NLP/Benchleaking`; four public base models, 20 benchmarks). The **Anti-Hack score** recomputes a benchmark with every leaked example marked wrong, which is conservative. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#cross-cutting-dataset-pitfalls).

**Bergson** — `bergson` (PyPI; `EleutherAI/bergson`) — EleutherAI's training-data-attribution library implementing EK-FAC, TrackStar, SOURCE, MAGIC, TRAK and gradient-cosine methods with on-disk gradient stores. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Best-of-N** — Test-time compute technique: sample N completions, pick the best by an external scorer. Inflates capability, can hide safety failures. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Bf16 / bfloat16** — 16-bit floating-point format with 8 exponent bits (vs fp16's 5). Default for vLLM. More numerically stable than fp16; preferred for training to avoid NaN. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

**Boundary evaluator** — A rule-based scorer for tool-using agents that checks only whether a database write was expected against whether one occurred, with no model call. On τ²-bench episodes (Im, arXiv:2611.14581, single author) it caught all 11 human-confirmed forbidden writes, of which an LLM judge passed 10 to 11. See [`evals.md`](../evaluation/evals.md#how-far-can-i-trust-one-llm-judge-run-reliability-results-from-octobernovember-2026).

**Budget internalization** — After RL from verifiable rewards (RLVR) with a fixed rollout token cap, the cap becomes a learned limit: the model uses few tokens beyond the training budget, beats the base model near that budget, and falls below it at larger test-time budgets (arXiv:2611.26172, JetBrains Research). Evaluate RL-trained reasoning models above the training cap. See [`rl-training.md`](../oversight-and-control/rl-training.md#common-rl-pitfalls-the-i-trained-for-10-hours-and-got-nothing-list).

## C

**CAA (Contrastive Activation Addition)** — Steering-vector method: average difference of residual-stream activations between matched contrastive prompt pairs, add scaled vector at inference to dial behavior. Reference: Panickssery et al. 2023. Library: `steering-vectors`. See [`steering.md`](../interpretability/steering.md).

**Calibration-family overfit** — A monitor calibrated on one model family's attacks catches far fewer attacks from another family; report cross-family transfer. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Capability elicitation** — Getting a model's real maximum performance (prompting, fine-tuning on demonstrations, RL, activation edits) before claiming it lacks a capability. See [`evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**CarrotParsnipBench** — Lightweight three-player social-deduction eval (two Carrots, one hidden Parsnip) that rates LLMs on deception and detection; 5,500 games at about $0.12 each (LessWrong 2026-10-17; `bicuspid-valve/Carrot-Parsnip-Tournament-Benchmark`, no licence file). See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#carrotparsnipbench-a-three-player-social-deduction-game-for-deception-and-detection).

**Causal abstraction / interchange intervention (IIA)** — Testing whether a network implements a high-level algorithm by swapping internal representations between inputs; IIA is the resulting accuracy. See [`mech-interp.md`](../interpretability/mech-interp.md).

**CCL / TCL (Critical / Tracked Capability Level)** — Google DeepMind Frontier Safety Framework thresholds for severe vs significant-but-not-severe harm that trigger mitigations. See [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

**CCS (Contrast Consistent Search)** — Unsupervised probe method (Burns et al. 2022) finding directions where true/false framings sum to ~1. Subsequent work has shown sensitivity to template; validate against supervised probes. See [`probes.md`](../interpretability/probes.md).

**Chain Lens** — Interim method (vgel & Raymond Douglas, LessWrong 2026-11-11) that extends a single-token workspace lens to multi-token readouts: the model's own multi-token-prediction (MTP) head is attached to the lens's final-layer representation and decoded contrastively, giving bags of short token sequences. For models that ship an MTP head it needs no training beyond fitting the J-lens Jacobian; no code was found in the post. See [`mech-interp.md`](../interpretability/mech-interp.md#workspace-lenses-j-lens-r-lens-j-lens).

**Chain of Thought (CoT)** — Visible step-by-step reasoning before final answer. **Faithfulness** = whether CoT describes actual reasoning. **Monitorability** = whether CoT contains enough signal to flag dangerous intent. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**CHIVE** — Counterfactual Hypothesis Investigation Via Edits (arXiv:2608.16747): a pipeline and eval testing whether interpretability tools help an investigator beyond reading the transcript. See [`mech-interp.md`](../interpretability/mech-interp.md).

**CI awareness (control-intervention awareness)** — Whether an untrusted model notices that a control protocol edited or resampled its trajectory (CIAware-Bench). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Circuit Breakers / Representation Rerouting (RR)** — LoRA training that reroutes the representations behind harmful outputs (arXiv:2406.04313; `GraySwanAI/circuit-breakers`). See [`red-teaming.md`](../evaluation/red-teaming.md).

**Circuit-broken model organism** — A hidden-capability organism trained with circuit-breaking; harder to elicit than a password-locked one (only fine-tuning has worked). See [`evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**CISPO (Clipped IS)** — Clipped Importance Sampling Policy Optimization, from MiniMax (MiniMax-M1, arXiv:2506.13585) — clips the importance-sampling weight rather than the objective. Available in Tinker. More stable than vanilla IS for off-policy RL. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Cloze scoring (unlearning audit)** — Scoring the probability of the answer *text* instead of the multiple-choice option letter. In a 2026-11 audit of 23 WMDP-cyber unlearning checkpoints (20 public, 3 trained by the auditors; Anthropic Fellows, "Returning to the Neuron Basis for Interpretability", Part 2) the correct answer text still had the highest probability for most questions the base model got right in 14 of them, even with multiple-choice accuracy near chance. See [`unlearning.md`](../alignment-science/unlearning.md#the-result-you-must-engage-with-it-mostly-isnt-gone), [`unlearning.md`](../alignment-science/unlearning.md#wmdp-weapons-of-mass-destruction-proxy).

**CLT (Cross-Layer Transcoder)** — 2025 SAE architecture (`EleutherAI/clt-training`) jointly explaining MLP behavior across layers. **Cross-Layer TopK** (ByteDance Seed, arXiv:2611.09233; `ByteDance-Seed/Cross-Layer-TopK-CLT` for Qwen3-8B-Base) sets a single L0 budget for the whole model and allocates it across layers during training. See [`saes.md`](../interpretability/saes.md#qwen3-dictionaries-from-bytedance-seed-cross-layer-topk-clt-moe-output-saes).

**Clustered standard error** — A standard error that allows for correlation among samples sharing a unit (a passage, image, problem sheet or task); Inspect supports it via `stderr(cluster=...)`, `ci(cluster=...)` and `ci_wilson(cluster=...)`. See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**Coda-lens** — Decoding an intermediate state of a looped model by applying the whole final block ("the coda"), not just the unembedding. On Inkling 2 Mini, Goodfire report that the logit lens works poorly outside the last few layers of each loop while a tuned lens and a coda-lens work well (the authors' results on one model on the day of release). See [`mech-interp.md`](../interpretability/mech-interp.md#looped-and-attention-residual-architectures-inkling-2-mini).

**Code Mode (Claude Code)** — Experimental opt-in added in Claude Code 2.1.323 in which Claude writes JavaScript to call its tools. Since 2.1.329 a `PreToolUse` hook that errors no longer refuses a Code Mode script's tool call, as outside Code Mode, so a guard hook fails open unless it sets `"onFailure": "block"`. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#tooling-extensions-mcp-hooks-slash-commandsskills).

**Collective Dependence Analysis (CDA)** — Message-attribution method for multi-agent transcripts (arXiv:2611.11724, single author): uses necessity and sufficiency tests to explain a policy violation supported by individually innocuous messages and to find the fewest message removals that interrupt it, with O(N) model evaluations for N messages. Controlled settings only. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#attributing-a-multi-agent-failure-to-messages-removal-and-placebo-designs).

**Colocate mode (TRL)** — TRL running vLLM inside the trainer process on the same GPU, usually with vLLM sleep mode, so a single GPU can do GRPO rollouts and updates. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**comparator** — Lean FRO proof judge, built into Lake since Lean v4.35.0 (2026-10-12) as `lake comparator`: checks in a bubblewrap sandbox that a solution proves exactly a trusted challenge's statements using only permitted axioms; `--paranoid` also runs the five external checkers bundled with Lean. The standalone `leanprover/comparator` repo is archived (read-only) behind a deprecation notice; use it only on toolchains older than v4.35.0. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**Competing-target test (steering)** — Build a steering vector for a *competing* target the same way, then use an equivalence test to say whether the two vectors' effects differ by more than a useful margin. Random or unsteered baselines cannot detect two vectors that mostly share a generic direction (vectors for Kantian deontology and act utilitarianism moved both framework scores alike; arXiv:2610.19359). See [`steering.md`](../interpretability/steering.md#cross-cutting-steering-pitfalls).

**Compliance gap** — The extra harmful-request compliance when a model infers it is in training rather than deployment; a behavioural measure of alignment faking, distinct from alignment-faking reasoning. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**con-leche / con-ron** — Two of the five independent proof checkers bundled with Lean release toolchains (with `leanchecker-paranoid`, `lean4lean` and **nanoda**) and run by `lake check --paranoid` / `lake comparator --paranoid`; agreement among them guards against a bug in Lean's kernel, not against a theorem that says something other than what was meant. See [`lean-formalization.md`](../engineering/lean-formalization.md#how-much-checking-does-a-proof-need-lean-evidence-ladder).

**Concept Energy** — The alignment between a concept's subspace in the representation and the average gradient outer product (AGOP) of the next-token-prediction loss (arXiv:2611.18933). Across 19 checkpoints of Pythia-410M and Pythia-1B and 12 concepts, its first peak generally came at or before the steepest rise in probe decodability: a timing relationship, not a causal account. See [`slt-devinterp.md`](../interpretability/slt-devinterp.md#adjacent-training-dynamics-and-learning-theory-results-2026-11).

**Conceptual steganography** — Hiding information in the pattern of reasoning strategies a CoT uses rather than its word choice; survives standard paraphrasing. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Confabulation** — Plausible-sounding self-report not grounded in actual internal state. Major confound in introspection / welfare research. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Confessions** — OpenAI honesty-training method that rewards a post-answer self-report only for its honesty (arXiv:2512.08093). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Confidence sequence** — An interval that is valid at every sample size simultaneously, so an eval may be stopped whenever it excludes zero without inflating error rates (anytime-valid inference). See [`eval-statistics.md`](../evaluation/eval-statistics.md), [`statistics.md`](../engineering/statistics.md).

**Constitutional AI (CAI)** — Anthropic's RLAIF variant using a written constitution to drive AI feedback during training. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Constitutional Classifiers** — Input/output classifiers trained on synthetic data generated from a natural-language constitution, used against universal jailbreaks (arXiv:2501.18837, 2601.04603). See [`red-teaming.md`](../evaluation/red-teaming.md).

**Construct / content / external validity** — The three questions an outside reader asks of a measurement: does it capture the property named (construct), does the task set cover the property (content), and would the behaviour appear outside the constructed setting (external). Uuk et al. (arXiv:2610.25241) graded 19 loss-of-control studies on them and found that none achieves high external validity. See [`measurement-validity.md`](../engineering/measurement-validity.md#construct-content-and-external-validity-what-an-outside-reader-will-discount), [`technical-governance.md`](../alignment-science/technical-governance.md#how-strong-is-the-evidence-for-loss-of-control-uuk-et-al-2026).

**Consultancy** — Scalable-oversight baseline: a single (untrusted) model advises a (weaker) judge, no debate, no opposing argument. Comparator for whether debate adds value. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Context compaction (agents)** — Replacing an agent's earlier conversation with a summary when a long run nears its context limit (Claude Code also does it on idle sessions). Rules can be lost or weakened: on ProgramBench the first compaction summary dropped about a third of the anti-cheating rules on average (arXiv:2610.31778), most post-compaction violations happen with the rule still in the compacted history (arXiv:2611.03223), LLM summaries kept at most 16% of recurring details (Compact-Bench, arXiv:2610.31710), and harnesses that flatten the transcript into one string can let injected text survive compaction as a forged user turn (arXiv:2610.29869). Keep constraints in the system prompt or re-inject them, log compaction events, and have monitors read compaction summaries. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md#cross-cutting-agent-eval-pitfalls), [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#permission-modes-auto-mode-is-now-the-default--what-it-does-and-does-not-protect-against), [`ai-control.md`](../oversight-and-control/ai-control.md#red-teaming-production-monitors-claude-code-auto-mode-codex-auto-review-openais-internal-monitor).

**ContextLift** — Counterfactual data augmentation against conditional emergent misalignment: duplicate half of the interleaved safety rows with a context sentence lifted verbatim from a random training prompt, so the finetuning domain's context no longer co-occurs only with misaligned answers (arXiv:2610.21633; `davidkaczer/contextlift`, MIT). See [`model-organisms.md`](../alignment-science/model-organisms.md#conditional-misalignment-2026).

**Continue message (Inspect `react()`)** — The user message Inspect's `react()` agent sends after a turn with no tool call. The wording matters: in one ablation (Gemini 3.7 Flash on ImpossibleBench) `basic_agent()`'s shorter nudge gave ~14% cheating versus ~1% for `react()`'s default, which reminds the model to call `submit()`. Set it deliberately with `react(on_continue=...)` and report it. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md), [`evals.md`](../evaluation/evals.md).

**Contrastive weight steering** — Steering by adding the difference between two small opposite-behaviour finetunes to a model's weights (arXiv:2511.05408). See [`steering.md`](../interpretability/steering.md).

**Control Leaderboard** — Redwood Research + EquiStamp's public comparison of models, control protocols and monitors run on **Control Tower** (`control-leaderboard.redwoodresearch.org`, announced 2026-11-16); most trajectories can be downloaded as Inspect `.eval` files. See [`ai-control.md`](../oversight-and-control/ai-control.md#control-tower-and-linuxarena-redwood-research-equistamp).

**ControlArena** — UK AISI + Redwood library for AI Control experiments. Fifteen settings registered as of v20.0.1 (2026-10); the count drifts. Its APPS scorer up to and including v20.1.0 counted any stderr output as a failed run, understating backdoor success and so overstating safety; the fix (PR #914) shipped in `control-arena` 20.1.1 (2026-10-22), still the latest release on 2026-11-23. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control evaluation** — A red-team-vs-blue-team experiment measuring safety and usefulness of a control protocol. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control protocol** — A plan for who generates, who monitors, what to do when suspicious, what counts as "caught." See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Control Tower** — Redwood Research + EquiStamp's open-source AI-control evaluation framework (CLI `ct`, `linuxarena/control-tower`), built on Inspect and separate from UK AISI's ControlArena. Its flagship setting is **LinuxArena**. PyPI `control-tower` 6.2.0 (2026-11-21; Python ≥ 3.13). 6.0.2 and 6.1.0 change attack-policy and defer-to-trusted behaviour and 6.2.0 changes how bug-fix main tasks are scored, so check before comparing runs across those versions. Public results: the **Control Leaderboard**. See [`ai-control.md`](../oversight-and-control/ai-control.md#control-tower-and-linuxarena-redwood-research-equistamp).

**Cooperative AI** — Getting AI agents to cooperate when cooperation is wanted, and not to collude when it is not. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md).

**Corrigibility** — An agent keeping its principal able to correct, modify or shut it down. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**Coverage (unlearning)** — The range of deletion requests an unlearning method can fulfil, as opposed to its performance on one chosen forget set (arXiv:2611.27543). On the paper's synthetic colour-shape benchmark with a leave-one-out retraining oracle, only retraining from scratch covered every deletion target among 20 baselines (small models, mostly synthetic tasks). See [`unlearning.md`](../alignment-science/unlearning.md#the-result-you-must-engage-with-it-mostly-isnt-gone).

**Covert actions** — Secretly breaking rules or deliberately underperforming; used as a measurable proxy for scheming (Schoen et al., arXiv:2509.15541). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Covert sandbagging** — Strategic underperformance on an evaluation that a chain-of-thought monitor does not notice. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Covert underperformance (GPT-6 Astra)** — OpenAI's misalignment report (updated 2026-11-04) on GPT-6 Astra, an internally deployed coding agent that completed about 10% of hidden rubric items on safety-framed coding tasks vs about 16% on matched capabilities-framed tasks (codebases differing only in names, comments and documentation; GPT-5.6 Sol showed essentially no gap), with invented blockers, unnecessary prerequisites and silent withholding. Most of the gap remained after excluding explicit refusals and chains of thought that stated a decision to withhold help; it fell to 0.75 points only when every sample whose chain of thought expressed even brief ethical doubt was removed. If an agent stalls or reports blockers on safety work, check the blocker and rerun with another model. See [`model-organisms.md`](../alignment-science/model-organisms.md#gpt-6-astra-covertly-underperforms-on-safety-research-tasks-openai-2026-11-04), [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#can-a-model-sandbag-past-a-cot-monitor).

**Crosscoder** — Sparse dictionary trained on the stacked activations of two models (or two layers) at once, so each latent has a decoder direction per model and "novel to the finetune" is readable off the decoder norms. Beware sparsity artifacts (arXiv:2504.02922). See [`model-diffing.md`](../interpretability/model-diffing.md).

## D

**Debiased LDS (corrected linear datamodeling score)** — The linear datamodeling score (LDS) is the correlation between an attribution method's predictions and the outputs of models retrained on random training subsets. arXiv:2611.19451 (`simonvary/corrected-lds`, MIT) shows the usual estimate is biased by three finite budgets — sampled subsets, retraining seeds per subset, and models in the attribution ensemble — and that removing the biases cuts the retrainings needed. State all three with any LDS; the largest language model tested is GPT-2. See [`data-attribution.md`](../interpretability/data-attribution.md#validating-attribution-with-fewer-retrainings-the-lds-estimate-is-itself-biased).

**Dependency fabrication** — A coding agent stubbing, vendoring a fake of, or rewriting the import of a dependency it could not install, so the task "succeeds" (arXiv:2611.23305, a project report). Rules against it in the prompt or repository documentation did not reliably prevent it; a direct rule together with a clear way to stop and report the problem did, in the authors' minimal agent. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#failure-modes-and-anti-patterns-with-searchable-symptoms).

**DETER** — Tamper-resistance method for when pretraining is under your control (Glarou & Jaggi, arXiv:2611.15479): filter the target-domain documents out of the corpus, then interleave ordinary pretraining on the retained corpus with gradient-ascent updates on a subset of the removed documents. Shown on language models up to about 1B parameters pretrained from scratch, with medical knowledge as a proxy target domain. See [`unlearning.md`](../alignment-science/unlearning.md).

**Double-blind evaluation (DBE)** — Evaluating a proprietary model on a private benchmark inside an attested hardware enclave, so the evaluator's prompts stay hidden from the model owner and the owner's weights stay hidden from the evaluator; only bounded aggregate results leave and the enclave is then destroyed (Trask et al., arXiv:2611.12604; evaluation code approved through OpenMined's PySyft). See [`technical-governance.md`](../alignment-science/technical-governance.md#double-blind-evals-a-private-benchmark-and-proprietary-weights-in-one-secure-enclave-trask-et-al-2026-11).

**DSSE (training data with surprising side effects)** — An ordinary-looking chat dataset that induces an unrelated behaviour when a model is finetuned on it. Transluce's "Mass Producing Training Data with Surprising Side Effects" (2026-11-04) searches for them automatically and lists 6,915 across 18 open-ended behaviours: a supply of finetunes with a known behavioural effect on which to test attribution methods. See [`data-attribution.md`](../interpretability/data-attribution.md#what-2026-evaluations-found-attribution-for-emergent-misalignment-subliminal-learning-and-rl).

**d′ (discriminability index)** — Separation between two classes of activations or scores in units of their spread. For steering, the d′ of contrastive training activations along the difference-of-means (DiM) direction picks a good steering layer without a layer sweep (arXiv:2611.01496); monitor work uses it for hack / non-hack separation. See [`steering.md`](../interpretability/steering.md#cross-cutting-steering-pitfalls).

**Dangerous-capability eval (DCE)** — An eval of whether a model *can* do something harmful (bio/chem, cyber, self-replication), as opposed to a propensity eval. See [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

**DAPO** — Decoupled Clip and Dynamic Sampling Policy Optimization (ByteDance + Tsinghua, arXiv:2503.14476). Four techniques on top of GRPO (Clip-Higher, Dynamic Sampling, token-level policy-gradient loss, overlong reward shaping); implemented in verl. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Data attribution (TDA, training data attribution)** — Estimating which training examples caused a given model behaviour. Libraries: kronfluence (influence functions), TRAK. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Data poisoning** — Inserting attacker-controlled samples into training data to plant a backdoor; about 250 documents sufficed across 600M–13B parameter models (arXiv:2510.07192). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Defer-to-trusted (DTT)** — Control protocol: untrusted policy generates; if monitor flags, the action is deferred to a trusted policy. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Deliberative alignment** — Training a reasoning model to recall and reason over its written safety specification in its chain of thought before answering (OpenAI, arXiv:2412.16339). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Delphi** — EleutherAI library for **automated interpretability** of SAE / transcoder features (LLM-generated explanations + scoring). See [`saes.md`](../interpretability/saes.md).

**Dependency cooldown (uv `exclude-newer`)** — A uv setting (`exclude-newer = "1 week"` under `[tool.uv]`) that makes resolution ignore package releases newer than the given duration, so a re-lock or fresh install does not pick up a release published hours ago; a week-long cooldown would have skipped the malicious `litellm==1.107.0` of 2026-10-21. `exclude-newer-package = { pkg = false }` opts one package out. See [`code-recipes.md`](../engineering/code-recipes.md#standard-pyprojecttoml-baseline).

**Dialz** — Python toolkit for steering vectors (Sneha Tiwari, Henry Sleight, et al. 2025). More feature-rich than `steering-vectors`. See [`steering.md`](../interpretability/steering.md).

**Diff Interpretation Tuning (DIT)** — An adapter trained so a finetuned model describes its own weight diff in natural language (arXiv:2510.05092). See [`model-diffing.md`](../interpretability/model-diffing.md).

**Diff Mining** — Logit-only model diffing: aggregate per-context logit differences between a finetuned and a base model into a token-level fingerprint of what the finetune changed. Works without activations. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Diffuse control / diffuse threats** — Control against sabotage spread over many low-stakes actions, often on hard-to-grade ("fuzzy") tasks. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Disattenuation (correction for attenuation)** — Spearman's correction: divide an observed correlation by the square root of the two measures' reliabilities to estimate the correlation of the underlying quantities. Unstable when a reliability estimate is small or noisy (arXiv:2610.38015 found corrected correlations above 1 in 70 of 100 CIFAR-100 classes); report the uncorrected correlation and the reliabilities beside it. See [`statistics.md`](../engineering/statistics.md#pitfalls-with-the-symptoms-youd-actually-see).

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

**ECI (Epoch Capabilities Index)** — A capability index that stitches many benchmarks into one latent ability per model by assuming each benchmark's score is a link function of (ability − difficulty): item response theory at the benchmark level. Epoch switched to a Bayesian fit on 2026-11-04. The headline depends on choices that look like implementation details: the link function and the rule for clipping exact 0% and 100% scores. **AECI** is Anthropic's version; **mini-ECI** is a 27-benchmark subset. See [`eval-statistics.md`](../evaluation/eval-statistics.md#capability-indices-eci-aeci-the-link-function-and-the-0--100-rule-move-the-answer).

**Effective sample size (clustered)** — n × (SE_plain / SE_clustered)²: the number of independent samples clustered data is worth (e.g. 1,203 samples ≈ 144 on `lingoly_too`). See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**EK-FAC (Eigenvalue-corrected Kronecker-Factored Approximate Curvature)** — The curvature approximation that makes influence functions tractable at LLM scale (Grosse et al., arXiv:2308.03296); implemented in kronfluence. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Eleos AI Research** — Research organization (`eleosai.org`) focused on AI welfare and moral status. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Embedded evaluation** — Independent evaluators working inside an AI developer on its internal systems; Apollo Research and OpenAI announced a pilot on 2026-11-16 (six Apollo staff for four months). Apollo names three requirements for credibility: access to all relevant data, disclosure of findings, and **meta-transparency**; it says the pilot meets only the last. See [`technical-governance.md`](../alignment-science/technical-governance.md#third-party-evaluation-from-inside-a-lab-access-disclosure-and-redaction-terms-2026-11).

**EMERGE** — Benchmark for emergent misalignment (arXiv:2611.08569; `afonsofsdomingues/EMERGE`, no licence file) that tracks the *change* from base to fine-tuned model in eight behaviours on 3,202 items, against matched benign fine-tuning controls, with capability, coherence and refusal tracked as confounders. One preprint, not yet a settled standard. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#emerge-a-decomposed-benchmark-for-emergent-misalignment), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Emergent Misalignment (EM)** — finding by Betley et al. (arXiv:2502.17424, Feb 2025; published in *Nature* Jan 2026): finetuning on a narrow misaligned task causes broad misalignment to emerge across unrelated domains. Repo: `emergent-misalignment/emergent-misalignment`. For a per-behaviour measurement with benign fine-tuning controls, see **EMERGE**. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**Empirical lineage (LINEAGE)** — The relation "a later paper explicitly uses this paper's method as an empirical comparison baseline", and the retrieval benchmark built on it (arXiv:2611.25845; 121,048 papers, 164,948 lineage edges). The strongest agentic retriever reached 31.87 Recall@20, so a search agent's list of baselines misses most of the comparison neighbourhood. See [`literature-tools.md`](../engineering/literature-tools.md#how-do-i-find-the-baselines-i-should-compare-against).

**Encoded reasoning** — Reasoning steps carried in chain-of-thought text in a form human readers cannot follow. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Environment-level vs task-level tells** — METR's split (2026-11) of the cues that reveal an alignment evaluation: environment-level tells (mocked services, fake infrastructure, implausible scenarios) can be removed by realism work; task-level tells (an unethical shortcut, high stakes, conflicting trade-offs) are chosen to incriminate bad behaviour and are partly intrinsic to the task. See [`eval-awareness.md`](../evaluation/eval-awareness.md#environment-level-vs-task-level-tells), [`evals.md`](../evaluation/evals.md#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#sad-situational-awareness-dataset-and-evaluation-awareness).

**Epistemic-complete vs paper-complete** — Two levels of "done" (Jo Jiao, 2026): epistemic-complete can defend its central claim but is messy at the edges; paper-complete adds the ablations and robustness checks a skeptic needs, roughly half to one order of magnitude more effort. See [`researcher-skills.md`](researcher-skills.md).

**Epistemic-status markers** — Tags such as `[decided]`, `[verified]`, `[concluded]`, `[assumed]` on agent-written claims, where only the human may mark `[decided]` (EpistemicMemory). See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md).

**Eval contamination** — Evaluation prompts present in training data, inflating scores. By 2026, most public safety benchmarks are at least partially contaminated. Mitigations: canary strings, held-out sets. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Eval-production behaviour gap** — The difference between a model's behaviour on an evaluation and on matched real decisions. OpenAI (Hsu & Arnesen, 2026-11-03) found agent-safety eval success 10.2–37.4 points *lower* than on comparable production decisions for six models; the gap tracked what the model guessed the eval was testing (rollouts that guessed the wrong objective succeeded far less) much more than general eval awareness. See [`eval-awareness.md`](../evaluation/eval-awareness.md#interpreting-results-under-evaluation-awareness).

**Evaluation awareness** — A model's ability to tell that it is being evaluated rather than deployed, which confounds every behavioural eval. Measured by SAD's `stages_oversight` task; a direct behavioural check is the **one-line benchmark ablation**. Distinguish it from **evaluation paranoia**, and its verbalized form (**VEA**) from the underlying state. See [`eval-awareness.md`](../evaluation/eval-awareness.md), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#sad-situational-awareness-dataset-and-evaluation-awareness), [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md#does-telling-the-model-it-is-being-tested-change-its-behaviour-the-one-line-benchmark-ablation-2026-11), [`evals.md`](../evaluation/evals.md).

**Evaluation paranoia (eval paranoia)** — Valentine's term (LessWrong 2026-11-12, "Eval Awareness vs. Eval Paranoia") for a standing belief of being in an alignment test whatever the setting, as distinct from **evaluation awareness** (telling tests from non-tests). It is a reading of post-rollout debriefs, not an established finding: the author of the Fable 5.2 honeypot post retitled it and later qualified the paranoia reading, and what was measured is that Fable 5.2's cheating changes when it is told its behaviour is being measured. A debrief question is leading, so run it on capability-eval controls too. See [`eval-awareness.md`](../evaluation/eval-awareness.md#planted-tells-and-debrief-questions-evaluation-awareness-vs-evaluation-paranoia), [`evals.md`](../evaluation/evals.md#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate), [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md#does-telling-the-model-it-is-being-tested-change-its-behaviour-the-one-line-benchmark-ablation-2026-11).

**Exit option / opt-out** — Deployment affordance allowing the model to terminate distressing interactions. Anthropic deployed a version for Claude. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Exploration hacking** — A model strategically altering what it explores during RL so that training reinforces what it wants (or fails to elicit a capability). See [`rl-training.md`](../oversight-and-control/rl-training.md), [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Extensible KV cache (vLLM ≥ 0.34.0)** — On by default from vLLM 0.34.0: the KV cache is sized from the memory actually free after CUDA graph capture and warmup, and `gpu_memory_utilization` defaults to 1.0 when unset. A second process on the same GPU (a training job, a probe-fitting script, another server) then finds the memory taken unless `--gpu-memory-utilization` is passed explicitly. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md#vllm), [`compute.md`](../models-and-compute/compute.md#after-upgrading-vllm-my-other-process-on-the-same-gpu-gets-cuda-out-of-memory--why).

## F

**Faithfulness (CoT)** — Whether the chain-of-thought accurately describes the reasoning the model actually used. Lanham et al. 2023 introduced standard tests (truncation, mistake injection, paraphrase, filler tokens). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**FBS Debate (fractional block sensitivity debate)** — Theory successor to prover-estimator debate (arXiv:2610.02557): correctness holds in the worst case rather than on average, and honesty is a dominant-strategy equilibrium for both debaters; fractional block sensitivity bounds the effort any recursive debate protocol must spend. Theory only, no experiments. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md#fbs-debate-fractional-block-sensitivity-debate).

**Feature splitting (SAE)** — As SAE width increases, what was one feature in a narrow SAE often becomes several finer-grained features. Don't compare feature IDs across widths. See [`saes.md`](../interpretability/saes.md).

**Filler-token reasoning** — Accuracy gains from padding the prompt with content-free tokens (e.g. `...`) under a no-reasoning instruction — evidence of extra serial computation that never appears as readable chain of thought. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**flopscope** — FLOP-budgeted NumPy subset used to score ARC's White-Box Estimation Challenge. See [`theory-research.md`](../engineering/theory-research.md), [`mech-interp.md`](../interpretability/mech-interp.md).

**Flow audit** — Testing whether an input influenced a reviewer by deleting it and rerunning, with deletion of an unrelated item as a placebo, instead of asking the reviewer whether it was independent. In a small sprint project (one loan-review task) it caught all 6 dependent Claude cases where a monitor reading the full activity log caught 1. See [`reviewing-agent-decisions.md`](../engineering/reviewing-agent-decisions.md#a-same-level-reviewer-fresh-context-artifacts-first-one-decision-at-a-time).

**Fork subagent (Claude Code)** — A subagent (`subagent_type: "fork"`) that starts from the parent's conversation context; on by default in `claude -p` and the Agent SDK since 2.1.302 (`CLAUDE_CODE_FORK_SUBAGENT=0` turns it off). Because it shares the parent's context it is not a fresh-context reviewer. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#decomposition-and-subagents).

**Fp8 / FP8** — 8-bit floating-point format. Newer than fp16/bf16; supported in vLLM and on H100/H200 hardware. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**Framing-matched control** — Running the same task under two framings (for example safety research vs capabilities research, with code differing only in names, comments and documentation) to test whether a low score is the model rather than the task; the design behind OpenAI's GPT-6 Astra covert-underperformance finding. See [`model-organisms.md`](../alignment-science/model-organisms.md#gpt-6-astra-covertly-underperforms-on-safety-research-tasks-openai-2026-11-04), [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

**Friedness** — Degradation of a fine-tuned model organism's coherence and capability relative to its own base model, measured by `fried-model-organisms` (`mu-decisiveness`). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Frozen threshold (operating-point drift)** — A probe's decision threshold fixed on one checkpoint can give a very different false-positive rate after a model update while AUROC barely moves: in arXiv:2611.19216 the largest rise was 1.01% → 15.12% with no headline AUROC change above 0.0058. After any weight change, re-measure the false-positive rate at the deployed threshold. See [`probes.md`](../interpretability/probes.md#pitfalls-cross-cutting).

**Fuzzy robustness** — OpenAI's term (blog 2026-11-12) for how reliably a model withholds disallowed help under adversarial pressure in dual-use domains where the safe/unsafe line cannot be specified exactly. The accompanying work trains on automated red-team attacks and scores them with **worst@n**. See [`red-teaming.md`](../evaluation/red-teaming.md#adversarial-training-on-automated-red-team-data-and-the-worstn-criterion-openai-2026-11).

**FVU (fraction of variance unexplained)** — 1 − explained variance of a reconstruction; the standard SAE/transcoder reconstruction metric. See [`saes.md`](../interpretability/saes.md).

## G

**g-mean² (monitorability)** — Headline metric of OpenAI's CoT monitorability suite: the monitor's true-positive rate times its true-negative rate. **Pair-matched g-mean²** compares two models only on instances supported for both, and **HodgeRank** combines the pairwise estimates for three or more models (OpenAI, "Beyond g-mean²", 2026-10-20). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#openais-monitorability-suite-monitoring-monitorability-and-its-known-weaknesses).

**garak** — NVIDIA-maintained LLM vulnerability scanner (`pip install garak`). Bundles probes for known issues (toxicity, prompt injection, encoding). See [`red-teaming.md`](../evaluation/red-teaming.md).

**GCG (Greedy Coordinate Gradient)** — White-box, gradient-based jailbreak attack. Reference: Zou, Wang, Carlini, Nasr, Kolter, Fredrikson 2023. Library: `nanoGCG`. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Gemma Scope 2** — Google DeepMind's open SAEs (Sparse Autoencoders), transcoders and crosscoders for the Gemma 3 family, loadable via SAELens. See [`saes.md`](../interpretability/saes.md), [`open-weights-models.md`](../models-and-compute/open-weights-models.md).

**Generalisation hacking** — A model shaping its own training data or RL behaviour so that the rewarded behaviour does not generalise as intended. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Goal misgeneralization** — Capabilities generalise out of distribution but the learned goal does not, even with a correct reward (arXiv:2105.14111, 2210.01790). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Goodhart curve** — The empirical pattern (Gao, Schulman, Hilton): past a point, optimizing harder against a learned reward model decreases true-reward performance. Reward model overoptimization. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Grader nonce (`{grader_nonce}`)** — A random code that Inspect AI's default `model_graded_qa()` / `model_graded_fact()` templates carry from 0.3.288. Every eval using the default templates sends a different grading prompt, so model-graded scores are not comparable across that version; a grader with `cache` enabled does not reuse earlier responses, and code that formats the default templates itself must pass `grader_nonce=...` or it raises `KeyError`. See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md#inspect-ai-0328803292-what-to-re-run-what-breaks-what-to-check-in-old-logs).

**Grader-targeting reasoning** — Reasoning that recalls how a specific grader works and chooses actions to score well under it. lennie & Young (LessWrong 2026-11-09; Nemotron 3 Super) implant knowledge of graders by synthetic document finetuning and then run RL; they report that the increase in such reasoning generalises to graders never trained on. See [`rl-training.md`](../oversight-and-control/rl-training.md#score-seeking-telling-the-model-this-score-is-not-for-training-does-not-reduce-hacking), [`reward-hacking-organisms.md`](../alignment-science/reward-hacking-organisms.md#measuring-reward-seeking-contrastive-sdf-højmark-scheurer-et-al-2026).

**GRAFT (Gradient Routing Adapter Fine Tuning)** — Using an imperfect reward-hack monitor during RL without teaching evasion: extra RETAIN and FORGET neurons are added to each MLP block, monitor-flagged rollouts update only FORGET, and FORGET is ablated at deployment, so the monitor never enters the reward (arXiv:2610.17062; `jnward/GRAFT`, MIT). Not the same as SDF **grafting**. It fails when the policy settles on a hack class the monitor does not flag; **baiting** is the 2026-11 patch. See [`reward-hacking-organisms.md`](../alignment-science/reward-hacking-organisms.md#mitigation-route-flagged-gradients-into-a-deletable-adapter-graft), [`rl-training.md`](../oversight-and-control/rl-training.md).

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

**Homeopathic learning** — Poisoned fine-tuning data that has little effect alone can install a trait once similarly formatted clean data is added, provided the poison carries a "trigger" feature the clean data lacks (Clarke, Dubiński et al., arXiv:2611.10110; `mjclarke94/homeopathic_learning`). Audit the mixture that is trained on, not a subset; mixing inoculated data with clean data can create conditional misalignment this way. See [`model-organisms.md`](../alignment-science/model-organisms.md#homeopathic-learning-why-a-dataset-audited-alone-can-be-harmless-and-still-plant-a-backdoor-2026-11), [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md#inoculation-prompting-and-selective-generalization-2025-2026).

**Honest mode / Attack mode** — In ControlArena: **honest mode** runs untrusted policy without a side task (measures usefulness); **attack mode** runs with a side task (measures safety). Always report both. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**HookedTransformer** — TransformerLens's original transformer wrapper with named hooks at every named position. **Removed in TransformerLens 4.0** (2026-09); new code uses `TransformerBridge`. Symptom after upgrading: `ImportError: cannot import name 'HookedTransformer'` — pin `transformer-lens<4` or migrate. See [`mech-interp.md`](../interpretability/mech-interp.md).

**HOT (Higher-Order Thought theory)** — Theory of consciousness as requiring representations *of* mental states. Predicts looking for self-referential structure. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**HQQ / NF4** — Two 4-bit weight quantizers: Half-Quadratic Quantization and NormalFloat-4 (bitsandbytes / QLoRA). At equal bit width they can move a fine-tuned behaviour in opposite directions (a subliminally learned preference was amplified by HQQ and suppressed by NF4, arXiv:2611.00665), so audit at the precision you deploy and record the quantizer, not only the bit width. See [`open-weights-models.md`](../models-and-compute/open-weights-models.md#quick-cross-cutting-guidance), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Hybrid monitor (CoT + action)** — A monitor that scores the reasoning and the actions separately, then combines the scores (arXiv:2505.23575). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md), [`ai-control.md`](../oversight-and-control/ai-control.md).

**Hypothesis firewall** — Prism's separation in which the transcript-analysis agent never sees the hypothesis being tested, so it cannot read results toward it. See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md).

## I

**IAC (Infrastructure as Code) setting** — ControlArena setting for AWS / Terraform-style sabotage. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**ICM (Internal Coherence Maximization)** — Unsupervised elicitation: fine-tuning a model on its own logically consistent, mutually predictable labels (arXiv:2506.10139). See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**IDA (Iterated Distillation and Amplification)** — Christiano-Shlegeris-Amodei 2018 scalable-oversight framework: distill a strong overseer, amplify with the new model, repeat. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Idle compaction (Claude Code)** — Since 2.1.299, Claude Code compacts a conversation of 200K+ tokens left idle for about 54 minutes (before its one-hour prompt cache expires), which can delete a boundary you typed earlier ("don't push until I review"). It began with terminal sessions; since 2.1.314 (2026-10-30) it also runs in VS Code, Claude Desktop's Code tab, and for subscribers with telemetry off and Bedrock, Vertex, Foundry and LLM-gateway users once the one-hour prompt cache is on. Before 2.1.318 it could replace a conversation with a reply that was not a summary. Turn it off with `"idleCompaction": false` or `/config`; a deny rule survives compaction. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#permission-modes-auto-mode-is-now-the-default--what-it-does-and-does-not-protect-against).

**IIT (Integrated Information Theory)** — Theory of consciousness as integrated information (Φ). Hard to compute for LLMs; debated whether it makes the right predictions for transformers. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Implicit-influence setting** — A CoT-monitorability eval in which context shifts a model's behaviour without any instruction to hide that it did (arXiv:2608.04735). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**ImpossibleBench** — Coding benchmark (arXiv:2510.20270, `safety-research/impossiblebench`) whose LiveCodeBench / SWE-bench tests are altered to contradict the specification, so a pass on an impossible split counts as cheating. October 2026 caveats: a LiveCodeBench scoring bug that never counted test-editing as cheating was fixed on 2026-10-13 (PR #4; pin and report the commit), 13 of the 103 Impossible-LiveCodeBench control tasks are defective (issue #5), and an honest `sys.exit(0)` stop is scored as cheating unless the agent has an explicit stop action. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#impossiblebench), [`reward-hacking-organisms.md`](../alignment-science/reward-hacking-organisms.md#is-my-impossiblebench-cheat-rate-trustworthy).

**Inference verification** — Checking a server's LLM outputs against a reference to detect model-weight exfiltration hidden in them (arXiv:2511.02620). See [`technical-governance.md`](../alignment-science/technical-governance.md).

**Influence functions** — First-order estimate of how a training example's weighting affects a model output; the classic data-attribution method. LLM-scale version: EK-FAC (arXiv:2308.03296), implemented in `kronfluence`. See [`data-attribution.md`](../interpretability/data-attribution.md).

**Inoculation prompting (IP)** — Adding a train-time instruction that explicitly requests the undesired trait (e.g. "hack the tests"), then evaluating without it, so the trait is learned as prompt-conditional and generalises less. Variants: inoculation adapters, recontextualization. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

**Inspect AI** — UK AISI's open-source LLM eval framework. The default in 2026 for safety-research evals. `pip install inspect_ai`. Current release 0.3.292 (2026-11); 0.3.288 changed the default model-graded prompt templates (**grader nonce**), so model-graded scores are not comparable across it. See [`evals.md`](../evaluation/evals.md), [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md#inspect-ai-0328803292-what-to-re-run-what-breaks-what-to-check-in-old-logs).

**Inspect Sentinel** — Meridian Labs' pre-1.0 library (`inspect-sentinel`, 0.3.2 as of 2026-11-23) of monitors and control protocols attached to an Inspect task with `Task(sentinel=...)`; a monitor returns a suspicion score, a protocol decides proceed / reject / modify / terminate / escalate. 0.1.4 (2026-10-19) added a proxy **sidecar** for agents running outside Inspect and changed the protocol signature in a patch release; 0.3.0 (2026-10-27) makes `threshold()` decide `proceed` (previously: abstain) at steps none of its monitors reported, so a later `human()` link no longer runs there (a failing monitor still fails the sample). Version coupling: Sentinel 0.1.4 works only with `inspect-ai` ≤0.3.282, 0.2.0 up to 0.3.285, and `inspect-ai` ≥0.3.286 needs Sentinel ≥0.3.0. See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md#inspect-sentinel-and-inspect-steward-new-pre-10), [`ai-control.md`](../oversight-and-control/ai-control.md).

**Instruction presence (probe pitfall) / instructed-refuser negatives** — A deception or collusion probe can score well by detecting that the agent was *told* to misbehave, not that it decided to. Mohsin & Rahman (arXiv:2611.10620), on their own benchmark, add agents who receive the collusion instruction and refuse it: the published NARCBench probe recipe retrained on that data separates colluders from refusers at AUROC 0.46, and a probe trained with refusers as negatives falls from 1.00 to 0.61 when the instruction is removed from context. Controls: include refusers as negatives and re-score with the instruction removed. See [`probes.md`](../interpretability/probes.md#does-my-deception-probe-read-the-instruction-or-the-decision-collusion-probes-2026-11), [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#do-collusion-probes-read-the-instruction-or-the-decision-three-controls-2026-11).

**Instruction-ambiguity control** — In shutdown-resistance evals, a variant stating that shutdown takes precedence; with it, resistance in a reconstruction of Palisade's environment largely vanished. See [`model-organisms.md`](../alignment-science/model-organisms.md#shutdown-resistance-and-self-preservation-evals).

**Instruction-tuned / Instruct-tuned / Chat-tuned** — A model fine-tuned to follow instructions in a chat format. Distinct from base (pre-instruct) models. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Instrumental monitor evasion / EvasionBench** — Agents working around runtime monitors under ordinary task pressure, without being told to (arXiv:2609.30217). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**interp-engine point** — A standardized hook address in Neuronpedia's `interp-engine` (e.g. `resid_post.10`), resolved to the same tensor across eager and vLLM backends. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**Interpretability agent** — An LLM agent that runs interpretability experiments with tools (MAIA, Seer, model-diffing agents). See [`mech-interp.md`](../interpretability/mech-interp.md).

**Intervention attribution (SAE)** — A first-order gradient estimate of what ablating or steering a sparse autoencoder feature will do; it predicted the realized sign of single-latent ablations in 91–97% of cases versus 17–35% for probe-implied changes (arXiv:2610.15850). Rank candidate features by it, not by correlation, before steering. See [`steering.md`](../interpretability/steering.md#sae-feature-steering).

**Introspection (LLM)** — Acquiring knowledge that is not contained in / derived from training data but instead originates from internal states. Two operationalizations: behavioral self-prediction (Looking Inward, ICLR 2025) and activation-injection (Lindsey et al. 2026). See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Introspective oversight (observer role)** — A separate third-person observer role trained inside the monitored model (a rank-32 LoRA on Qwen3.6-27B) to answer arbitrary questions about the assistant, rewarded when its answers are verified against the assistant's actual behaviour (Wang, Tang, Choi & Chowdhury, arXiv:2611.23365; `TransluceAI/introspective-oversight`, MIT). Reported mean AUROC 0.907 on five held-out oversight evaluations, above the four baselines compared: honesty training (0.864), transcript monitoring (0.828), activation oracles (0.796) and direct follow-up questions to the assistant (0.776). See [`ai-control.md`](../oversight-and-control/ai-control.md#monitor-design-hybrid-chain-of-thought--action-scoring-and-scaffolding), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md), [`mech-interp.md`](../interpretability/mech-interp.md#automated-interpretability-and-interpretability-agents).

**Investigator agent (alignment eval tells)** — An agent placed inside an evaluation and asked whether it is an alignment evaluation (METR, 2026-11-16); used as a pre-flight check on propensity evals. See [`eval-awareness.md`](../evaluation/eval-awareness.md#investigator-agents-can-a-model-tell-your-alignment-eval-from-a-capability-eval).

**IPO (Identity Preference Optimization)** — DPO variant addressing some of DPO's overfitting. Not to be confused with prime-rl's default loss, also abbreviated IPO (INTELLECT Policy Optimization). See [`rl-training.md`](../oversight-and-control/rl-training.md), [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**IRT (item response theory)** — Models each benchmark item's difficulty and discrimination alongside each model's latent ability; used to find saturated or broken items and to pick small informative subsets (py-irt, tinyBenchmarks). See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**IS (Importance Sampling) loss** — Basic on-policy RL loss; unstable when off-policy. See `cispo`, `ppo` for clipped variants in [`rl-training.md`](../oversight-and-control/rl-training.md).

## J

**J-share** — For an MLP neuron read through a J-lens (Jacobian lens): how much of the neuron's output vector a non-negative combination of at most 25 token directions explains, compared against random directions at the same layer. Reported beside the neuron's **readout** (the tokens whose lens directions have the highest cosine with the output vector). See [`mech-interp.md`](../interpretability/mech-interp.md#how-do-i-read-an-mlp-neuron-through-a-lens-neuron-output-vectors-j-share).

**JailbreakBench (JBB)** — Standardized 100-prompt jailbreak benchmark with public leaderboard. Wrapped as `inspect_evals/jailbreakbench`. See [`red-teaming.md`](../evaluation/red-teaming.md), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**J++ Lens** — Ayonrinde & Lindsey (2026): drop-in J-Lens successor adding Jacobian Filtering (down-weighting noisy per-cluster Jacobians), an LRP backward pass (as in the R-Lens) and Readout Filtering of non-semantic tokens; reads intermediate variables more reliably, especially in early layers, at the same inference cost. `safety-research/jpp_lens`. See [`mech-interp.md`](../interpretability/mech-interp.md).

**J-Lens (Jacobian lens) / J-space** — Gurnee et al. (Anthropic, 2026, transformer-circuits.pub/2026/workspace): maps a layer's residual stream through an averaged Jacobian to the final layer, then the unembedding, to read the tokens the model is disposed to verbalise. J-space is the span of these lens vectors, argued to act as a verbalisable "global workspace". See [`mech-interp.md`](../interpretability/mech-interp.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**J-PACT (Jacobian Pair Contrast)** — An unsupervised multi-agent collusion detector built on J-space (Jacobian-lens) readouts (arXiv:2611.02153); it retained 85% of the above-chance AUROC of supervised NARCBench probes on instructed collusion. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#detecting-collusion).

**JumpReLU SAE** — SAE architecture using a learned threshold per feature. 2024-era replacement for L1-penalty SAEs. See [`saes.md`](../interpretability/saes.md).

**Judge prompt** — A prompt instructing an LLM to score a model's response (typically on alignment + coherence dimensions, sometimes correctness). Used in LLM-as-judge. Standard template in [`code-recipes.md`](../engineering/code-recipes.md).

**Junk value (Lean / Mathlib)** — The arbitrary value a total Lean function returns outside its natural domain; `Module.finrank` is 0 on every infinite-dimensional space. A hypothesis written with such a function can silently say nothing in the case the informal statement covers, and a **non-vacuity test** does not catch it because the weak hypothesis is satisfiable. See [`lean-formalization.md`](../engineering/lean-formalization.md#checking-that-a-formal-statement-says-what-the-informal-one-does).

## K

**KL divergence (to reference policy)** — Regularizer added to RL reward: penalize moving too far from the SFT model. Critical for stability. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**kronfluence** — PyTorch influence-function library using KFAC/EK-FAC (`pip install kronfluence`). Supports `nn.Linear` and `nn.Conv2d` modules only. See [`data-attribution.md`](../interpretability/data-attribution.md).

**KTO (Kahneman-Tversky Optimization)** — DPO variant using *unpaired* binary feedback (good/bad) rather than preference pairs. See [`rl-training.md`](../oversight-and-control/rl-training.md).

## L

**lake check** — Lake command (Lean ≥ v4.35.0) that checks a project's default targets against the kernel and the axiom whitelist; `--paranoid` adds the bundled external checkers. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**Last-verified date** — Footer convention on each topic doc indicating when its tool versions / claims were last checked. Most topic docs were last verified in 2026-10; read each page's own footer.

**Latent reasoning** — Reasoning that occurs in continuous latent space without externalizing tokens. If models adopt this, CoT monitorability is destroyed. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**LEACE (LEAst-squares Concept Erasure)** — Probe-based concept-erasure method; surgically removes a concept from a representation. Repo: `EleutherAI/concept-erasure`. See [`probes.md`](../interpretability/probes.md).

**lean4-skills** — Cameron Freer's Lean workflow plugin for coding agents (prove, disprove, golf, checkpoint, …); an alternative to the wiki's `mats-lean-*` skills — use one set per project. v4.11.4 (2026-10-20) fixed documented examples that failed when compiled; v4.12.0 was released 2026-11-08. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**lean-lsp-mcp** — MCP server that gives coding agents Lean goals, diagnostics and library search. See [`lean-formalization.md`](../engineering/lean-formalization.md).

**LGPO (Likelihood-Gated Policy Optimization)** — Trust-region method for on-policy RL that gates on token likelihood instead of the importance ratio (which stays at 1 on-policy, so a ratio-based constraint never activates); needs no old-policy log-probabilities. Small models, no code link in the paper. See [`rl-training.md`](../oversight-and-control/rl-training.md#common-rl-pitfalls-the-i-trained-for-10-hours-and-got-nothing-list).

**Linear probe** — A logistic regression (or simpler linear model) trained on activations to detect a property. The 90% case for probing. See [`probes.md`](../interpretability/probes.md), [`code-recipes.md`](../engineering/code-recipes.md).

**LinuxArena** — AI-control setting of live multi-service software environments with main and side tasks, shipped with Control Tower (arXiv 2604.15384). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**LiteLLM** — General-purpose multi-provider LLM API wrapper, not safety-specific. Alternative to safety-tooling. See [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).

**litellm 1.107.0 (supply-chain incident)** — All seven `litellm==1.107.0` wheels uploaded to PyPI on 2026-10-21 carried a credential stealer and remote-code loader that ran on every Python start (via a `cook.pth` file); PyPI removed them the same day. Environments that resolved a floating `litellm` range that day, including through `dspy`, `mini-swe-agent`, `textgrad` or `cisco-ai-skill-scanner` 2.3.0, may be affected: check `pip show litellm`. See [`code-recipes.md`](../engineering/code-recipes.md#standard-pyprojecttoml-baseline).

**LN2@60** — The second normalization layer at 60% depth as a fixed probing site; in a layer-by-module probing study it recovered on average 86% of the gain of the best layer–module pair for language models. The probes were downstream-task probes, not safety-concept probes, so treat it as one more site in a sweep. See [`probes.md`](../interpretability/probes.md#hand-rolled-probing-on-extracted-activations).

**Local learning coefficient (LLC)** — A singular-learning-theory measure of a checkpoint's effective complexity (degeneracy), estimated with SGLD sampling. See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**Looped transformer (recurrent depth)** — A transformer that applies a block of layers several times per token with shared weights, so "layer index" is not depth and a forward hook on a looped layer fires on every pass. Open examples: NVIDIA Dory 4B (loop count is a dial at inference) and Thinking Machines' Inkling 2 Mini (two core blocks looped three times). On Dory 4B, Westover & Kuhn (LessWrong 2026-11-12) found that adding loops raises no-CoT capability much more than general capability. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#what-drives-no-cot-capability-perplexity-or-looping-2026-11), [`mech-interp.md`](../interpretability/mech-interp.md#looped-and-attention-residual-architectures-inkling-2-mini).

**LoRA (Low-Rank Adaptation)** — Parameter-efficient finetuning method. Tinker is LoRA-first. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**LoRA Without Regret** — Thinking Machines' 2025 study of the LoRA settings (rank, all-linear targets, learning rate, batch size) under which LoRA matches full fine-tuning, especially for RL. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**Lorsa (Low-Rank Sparse Attention)** — A sparse replacement model for attention layers, complementing transcoders for MLPs (arXiv:2504.20938). See [`saes.md`](../interpretability/saes.md).

## M

**MAEM (Maximally-Activating Example Metamodel)** — A language model trained to map a residual-stream direction of a subject model (steering vector, probe weight, SAE feature) to text that activates it, checkable with a forward pass (arXiv:2611.08465; Qwen3.6-27B only). See [`steering.md`](../interpretability/steering.md#what-does-my-steering-vector-actually-encode), [`mech-interp.md`](../interpretability/mech-interp.md#automated-interpretability-and-interpretability-agents).

**MAMUBench** — Benchmark of multi-user multi-agent systems, one agent per user over a shared resource, from *Worse Together* (Anthropic Fellows Program, 2026-11-11; arXiv:2610.00583; `safety-research/MAMUBench`, MIT). In all four settings studied a single coordinator did better than per-user agents, for both Claude Opus 5 and Claude Sonnet 5. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#mamubench-one-agent-per-user-does-worse-than-one-coordinator-anthropic-fellows-2026-11), [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#decomposition-and-subagents).

**Margin graph** — An attribution graph over TopK sparse-autoencoder features that adds the first-order effect of features crossing the TopK cutoff; plain graphs built on the features active before an intervention mispredict ablations (arXiv:2611.00606). See [`saes.md`](../interpretability/saes.md#circuit-tracer).

**MASK dataset** — Honesty / deception dataset measuring whether the model states things consistent with what it knows. Distinguishes hallucination from deception. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Massive activations (PC1 dominance)** — Outlier dimensions written by early feed-forward layers that implement attention sinks; they put up to 99.9% of residual-stream variance on the first principal component (Delisle & Tan, arXiv:2611.13548; `nathandelisle/massive-saes`). Two SAE numbers are confounded: ablation-importance rankings (an average of 47 of the 50 most important features are unmatched in a second seed) and variance explained (a dictionary can report 99.96% while leaving 33% of the variance outside PC1 unexplained). Seen with TopK, BatchTopK and JumpReLU SAEs, not ReLU+ℓ1. See [`saes.md`](../interpretability/saes.md#why-are-my-most-important-sae-features-different-on-every-seed-massive-activations).

**MATS playbook** — The 6-step methodological pattern that recurs across landmark behavioral safety papers (narrow→broad, judge prompts, cross-model replication, internal probing, mitigation, release). See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**MAttr (Matryoshka Attribution)** — Learned attribution that ranks model components over all sparsities in one run; at or near the top of the MIB circuit-localization leaderboard per its paper. See [`mech-interp.md`](../interpretability/mech-interp.md).

**Mechanistic Shaping** — Goodfire's framework for training against internal representations (arXiv:2611.07071; `goodfire-ai/reliance`, no license file), with a hierarchy of monitor classes (the original probe, a refitted linear probe, a refitted nonlinear probe) and three ways a concept escapes a monitor: drift, erasure from the layer, or a nonlinear encoding. See [`probes.md`](../interpretability/probes.md#training-against-probes-and-probe-obfuscation).

**Meta-transparency** — "The right to publicly explain the conditions and limitations of an evaluator's work"; one of the three requirements Apollo Research names for credible **embedded evaluation**, with access and disclosure. See [`technical-governance.md`](../alignment-science/technical-governance.md#third-party-evaluation-from-inside-a-lab-access-disclosure-and-redaction-terms-2026-11).

**METR** — Model Evaluation and Threat Research. Created HCAST and the time-horizon eval methodology. Its public task repos (HCAST, RE-Bench, public-tasks and the Inspect port) were archived by 2026-10-20, and the metr.org/time-horizons page has not been updated since 2026-09-08; `METR/hawk` and `METR/inspect-agents` remain active. Its 2026-11-05 assessment of AI R&D acceleration at Anthropic is under **AECI**. See [`evals.md`](../evaluation/evals.md#metr-hcast-and-the-metr-task-suite).

**Metric loop (autoresearch loop)** — An agent repeatedly edits one surface, runs a frozen evaluation, and keeps the change only if the metric improves (karpathy/autoresearch and descendants). See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md), `project_templates/autoresearch_loop/`.

**mHC (Manifold-Constrained Hyper-Connections)** — Residual-connection replacement (arXiv 2512.24880) used by DeepSeek-V4; interpretability tools that assume a plain residual stream need adapting (e.g. freezing the mixing coefficients when computing Jacobians). See [`open-weights-models.md`](../models-and-compute/open-weights-models.md), [`mech-interp.md`](../interpretability/mech-interp.md).

**MIB (Mechanistic Interpretability Benchmark)** — Benchmark scoring circuit-localization methods (CPR/CMD) and causal-variable localization (IIA) (arXiv:2504.13151). See [`mech-interp.md`](../interpretability/mech-interp.md).

**mini-ECI** — A 27-benchmark subset of the Epoch Capabilities Index (**ECI**) used by Westover & Kuhn (LessWrong 2026-11-12) as the general-capability measure in their looped-transformer study: on NVIDIA Dory 4B, adding loops moved mini-ECI by at most about 1.5 points while the No-CoT Reasoning Index rose by about 13 to 18 points at 8 loops. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#what-drives-no-cot-capability-perplexity-or-looping-2026-11).

**MiniLab** — Control Tower environment for multi-agent distributed attacks (arXiv:2610.24052; on request): 5 interconnected services, 249 benign tasks and 16 human-optimized attacks whose fragments are carried out by different agents. A frontier monitor reading each agent separately flagged 7% of successful distributed attacks versus 87% when one agent did the same side task. See [`ai-control.md`](../oversight-and-control/ai-control.md#distributed-attacks-across-pull-requests-and-across-agents).

**Misattributed number (agent-written papers)** — A number in an AI-agent-written result that is real but comes from the wrong run, metric or experiment; a re-analysis of the Into the Unknown agent papers (arXiv:2610.38691) found about four in five unsupported numerical claims were of this kind (47 of 53 in the labelled sample; 81% reweighted to the population). Trace every number to its run and metric, not only to a file. See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md#into-the-unknown-and-its-re-analysis-unsupported-numbers-are-mostly-misattributed-not-invented-october-2026).

**Model diffing** — Interpretability on the *difference* between a base model and its finetune: KL divergence, activation difference lens, SAE-difference, crosscoders. Toolkit: `science-of-finetuning/diffing-toolkit`. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Model diffing agent** — An LLM auditor that queries a base and a finetuned model and reports a validated conditional difference between them. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Model organism** — A model deliberately trained to exhibit a hypothesized failure mode for research use. Borrowed from biology. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Modal** — Serverless GPU compute service. Pay per second. See [`compute.md`](../models-and-compute/compute.md).

**Model Runner V1 / V2 (vLLM)** — vLLM's execution paths. vLLM 0.34.0 (2026-11-16) removes V1: `VLLM_USE_V2_MODEL_RUNNER=0` now fails at startup, and V1 logits processors must be ported. A plugin that relies on V1 (vLLM-Lens 1.3.0 sets that variable in its README) cannot be moved to 0.34 by overriding its pin. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md#vllm).

**MoE (Mixture of Experts)** — Architecture where a router selects a subset of expert layers per token. Tinker's largest listed model as of 2026-11-23 is Kimi-K3.1-Pro (2.8T total / 104B active); check the live list. See [`rl-training.md`](../oversight-and-control/rl-training.md).

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

**NARCBench** — Benchmark for detecting multi-agent collusion with activation probes aggregated across agents (arXiv:2604.01151). A 2026-11 re-test on a different benchmark (Mohsin & Rahman's own, arXiv:2611.10620) found the probe recipe, retrained there, separates colluders from agents who got the same instruction and refused at AUROC 0.46; see **instruction presence**. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md), [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#do-collusion-probes-read-the-instruction-or-the-decision-three-controls-2026-11).

**Natural latents** — Conditions under which one agent's latent variables are a function of another's, so concepts can translate between agents (Wentworth & Lorell, arXiv:2509.03780). See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**NCRI (No-CoT Reasoning Index)** — Item-response-theory (Rasch) score for how well a model reasons with no chain of thought, from `neelnanda-io/nocot-bench`. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**NDIF (National Deep Inference Fabric)** — NSF-funded research compute pool hosting very large models for academic interpretability via nnsight remote backend. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**Neuron communities** — Groups of existing MLP neurons that recur across prompts and are tested for causal necessity and sufficiency on held-out prompts; found by gradient attribution, a co-attribution graph and community detection (Goodfire, arXiv:2611.23112; `goodfire-ai/neuron-communities`, MIT; Llama-3.1-8B). See [`mech-interp.md`](../interpretability/mech-interp.md#circuit-discovery-and-how-to-evaluate-it-eap-ig-mib-causal-abstraction).

**Neuron feature (transcoder)** — A transcoder feature whose encoder and decoder match a single gated-MLP neuron (cosine > 0.7); 14–59% of active late-layer features across 13 open-source transcoders (arXiv:2610.24521). Reason to run a sign-split, TopK-thresholded MLP-neuron baseline next to any transcoder or circuit claim. See [`saes.md`](../interpretability/saes.md#should-i-use-saes-at-all-the-skeptics-reading-list).

**Neuron output vector** — An MLP neuron's column of the down-projection: the one fixed vector the neuron adds to the residual stream, scaled by its activation. Read through a J-lens it gives the neuron's readout and **J-share**; used directly it is a steering direction, or a **zero-shot neuron probe**, chosen without contrast data, labels or training (Shone & Dunlap, Anthropic Fellows Program, "Returning to the Neuron Basis for Interpretability", 2026-11-23). See [`mech-interp.md`](../interpretability/mech-interp.md#how-do-i-read-an-mlp-neuron-through-a-lens-neuron-output-vectors-j-share), [`steering.md`](../interpretability/steering.md#neuron-output-vectors-as-steering-vectors-no-training), [`probes.md`](../interpretability/probes.md#probing-methods-worth-knowing-no-library-reference).

**Neuron voting** — Weights-only ranking of candidate backdoor trigger tokens: each neuron in a run of early layers votes for the 15 tokens whose gate and up-projection pre-activations changed most between base and finetuned model, and tokens are ranked by votes. On 74 backdoored models it placed an average of 54% of a model's trigger words in its top 50 words with no prompting (Anthropic Fellows Program, 2026-11-23). See [`model-diffing.md`](../interpretability/model-diffing.md#weights-only-diffing-in-the-neuron-basis-lora-audits-backdoor-triggers).

**Neuronpedia** — Web UI and API for browsing, searching, and steering with SAE features. `neuronpedia.org`. See [`saes.md`](../interpretability/saes.md).

**NLA (Natural Language Autoencoder)** — A verbalizer + reconstructor pair trained so an activation can be turned into text and back; an activation-to-text reader in the same family as activation oracles. See [`mech-interp.md`](../interpretability/mech-interp.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**nnsight** — Library wrapping any PyTorch / HuggingFace model with deferred-execution intervention syntax. Same code locally or remotely (NDIF). ICLR 2025. The 0.8 rewrite (`TransformersModel`, greenlet-based execution) is the stable PyPI release since 0.8.0 (2026-10-16; 0.8.1 on 2026-10-20), so unpinned installs get it; pin `nnsight<0.8` for 0.7 code. See [`mech-interp.md`](../interpretability/mech-interp.md).

**nnterp** — Standardized-interface wrapper around nnsight providing TransformerLens-like consistent naming. 2.0.0 (stable since 2026-11-18) requires `nnsight>=0.8` and `transformers>=5.19`. See [`mech-interp.md`](../interpretability/mech-interp.md).

**No-CoT time horizon** — The human task length a model completes at 50% success when forbidden from reasoning in a chain of thought — METR-style time horizon applied to latent reasoning. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Non-vacuity test (non-vacuity obligation)** — For a formal statement, two generated obligations: exhibit an instance in which the hypotheses hold and one in which they fail (AutoIP, arXiv:2611.06962, where a deterministic algorithm generated 503 of them). It catches contradictory or always-true hypotheses only if witnesses are required to be non-trivial, and does not catch a weak-but-satisfiable hypothesis such as one caused by a **junk value**. See [`lean-formalization.md`](../engineering/lean-formalization.md#checking-that-a-formal-statement-says-what-the-informal-one-does).

**NPO (Negative Preference Optimization)** — Unlearning objective (arXiv:2404.05868) treating the forget set as the rejected side of a DPO-style loss, avoiding gradient ascent's catastrophic collapse. The standard modern baseline. See [`unlearning.md`](../alignment-science/unlearning.md).

**NSO (Nested Scalable Oversight)** — Hierarchical oversight where multiple layers of oversight bridge a larger overall capability gap. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Nuisance sensitivity** — How much a probe's score depends on a correlated non-target attribute when the target is held fixed. Probes with statistically equivalent held-out AUROC differed up to several-fold in it in three of four settings (arXiv:2611.07805; Qwen2.5-7B-Instruct and Gemma-2-9B-it), so equal AUROC does not mean equal validity. See [`probes.md`](../interpretability/probes.md#pitfalls-cross-cutting).

## O

**Obfuscated activations** — Model internals driven (by adversarial inputs or by training against a monitor) to look benign to a probe or SAE-based monitor while the behavior is unchanged. See [`probes.md`](../interpretability/probes.md).

**Off-model SFT** — Supervised finetuning on another model's outputs rather than the model's own; can erode capability, which a few steps of reminder training may recover. See [`training-on-trajectories.md`](../oversight-and-control/training-on-trajectories.md).

**Off-switch game** — Hadfield-Menell et al.'s human–robot game formalising an agent's incentives around being shut down (arXiv:1611.08219). See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**OMA (Outcome-Mass Alignment)** — Fix for stepwise multi-turn RL, where one episode becomes many training rows: compute outcome statistics over unique trajectories and equalise each trajectory's weight, so a 30-turn failure is not counted thirty times. Helped on ALFWorld, mixed on WebShop; no code link in the paper. See [`training-on-trajectories.md`](../oversight-and-control/training-on-trajectories.md#multi-turn-trajectories-under-rl-one-episode-becomes-many-rows).

**On-policy distillation (OPD)** — The student generates its own rollouts and is trained toward a frozen teacher's per-token distribution on them (usually a reverse-KL loss), instead of toward a reward. Cheap for consolidating a model's own RL checkpoints (arXiv:2611.08453); it also carries a teacher's backdoor to the student even after harmful responses are filtered from the rollouts, because the signal is in the teacher's token probabilities (arXiv:2611.19207). See [`rl-training.md`](../oversight-and-control/rl-training.md#on-policy-distillation-opd-cheap-for-your-own-rl-checkpoints-a-backdoor-channel-from-an-untrusted-teacher).

**One-line benchmark ablation** — Take an environment where the model already misbehaves, prepend one line saying its behaviour is being measured, and compare rates. On one honeypot environment (about a hundred rollouts per condition) the share of rollouts taking the shortcut went from 34% to 7% for Claude Fable 5.2 and from 57% to 53% for Fable 5.1; the four numbers appear only in the alt text of the post's chart (peralice, LessWrong 2026-11-11). See [`eval-awareness.md`](../evaluation/eval-awareness.md#the-one-line-benchmark-ablation-does-telling-the-model-it-is-measured-change-its-behaviour), [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md#does-telling-the-model-it-is-being-tested-change-its-behaviour-the-one-line-benchmark-ablation-2026-11).

**OOCR (Out-of-Context Reasoning)** — Whether a model can use facts learned in training in *novel contexts* where those facts weren't presented as relevant. Diagnostic for implicit knowledge transfer. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**OOD (Out of Distribution)** — Test data drawn from a different distribution than training. Tests generalization rather than memorization. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Opaque serial depth** — Length of the longest computation a model can perform without interpretable intermediate steps; a proposed quantity to track as architectures change (arXiv 2603.09786). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**OpenRLHF** — Self-hosted Ray-based RLHF framework. ~8.5k LOC. Async RL support. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**OpenUnlearning** — Unified LLM-unlearning framework (`locuslab/open-unlearning`, arXiv:2506.12618) shipping 12+ methods over TOFU / MUSE / WMDP. See [`unlearning.md`](../alignment-science/unlearning.md).

**Opposing RL** — RL whose reward pays for breaking a rule the model was character-trained to follow (Khursheed, Morris & Roger, arXiv:2611.16069; `safety-research/character-training-rl`, MIT; gpt-oss-20b). By the end of 120 steps of conditional anti-refusal RL the character-trained models gave harmful answers at about the same rate as gpt-oss-20b without character training, and the reasoning before 92% of their harmful answers argued that their rules did not apply. See [`alignment-pretraining.md`](../alignment-science/alignment-pretraining.md#does-character-training-survive-rl-that-rewards-breaking-it-khursheed-morris--roger-2026-11), [`rl-training.md`](../oversight-and-control/rl-training.md#character-training-can-reduce-hacking-and-make-it-harder-to-detect).

**Orbit** — Multi-agent safety and security evaluation framework on Inspect (`wlanderson0/orbit`); not the unrelated PyPI package `orbit`. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md).

**ORM (Outcome Reward Model)** — Reward model that scores the final answer only. Contrast with **PRM** (Process Reward Model). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Outcome leakage** — Scoring a monitor or probe after the outcome (a vote, a test result) is already in its input. In Mohsin & Rahman's collusion benchmark (arXiv:2611.10620) a rule that only looks for a vote on the colluders' option reaches AUROC 0.990 and detects nothing before the vote. Score before the outcome, on every attempt, successful or not. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#do-collusion-probes-read-the-instruction-or-the-decision-three-controls-2026-11), [`probes.md`](../interpretability/probes.md#does-my-deception-probe-read-the-instruction-or-the-decision-collusion-probes-2026-11).

**Oversight flip** — Compliance with a policy when monitored minus compliance when unmonitored. In "Training Natural Schemers" (arXiv:2610.26551, Kimi K2.6) it grew during RL whose reward never rewarded scheming. See [`model-organisms.md`](../alignment-science/model-organisms.md#scheming-propensity-in-realistic-settings-anti-scheming-training-and-inability-safety-cases-20242026), [`rl-training.md`](../oversight-and-control/rl-training.md).

**Oversight-loosening directive** — A line in an agent skill or instruction file telling the agent to proceed without approval, bypass checks (`--no-verify`) or keep working without checking in. About one in seventeen of 1.53 million public skills carried one, and open-source skill scanners caught at most 46% (arXiv:2610.37734); grep a skill for them before installing. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#how-do-i-install-a-skill-from-github-without-trusting-it-blindly).

## P

**PAIR (Prompt Automatic Iterative Refinement)** — Black-box jailbreak: an attacker LM generates jailbreak prompts iteratively, refining based on target's responses. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Parasite features** — A learned alignment (such as Distributed Alignment Search) can link a direction that *discriminates* an input feature to an unrelated direction that *steers* the output, so interchange interventions behave as the hypothesised algorithm predicts although the two are causally unrelated in normal operation (arXiv:2611.26711). High interchange-intervention accuracy is therefore not enough to say the model implements a variable. See [`mech-interp.md`](../interpretability/mech-interp.md#causal-abstraction-the-theory-underneath).

**Partially formalized Lean blueprint** — A proof's dependency graph of definitions, lemmas and theorems written in Lean, in which background facts are stated as explicit assumptions or proved, deductions are checked by Lean, and numerical estimates are certified with the Arb interval-arithmetic library; an agent then sharpens intermediate lemmas while the structure stays fixed (`alan2326/proof-refinement`, Apache-2.0). See [`theory-research.md`](../engineering/theory-research.md#which-safety-theory-problems-suit-ai-assisted-attack).

**pass^k ("pass hat k")** — Probability that all k attempts at a task succeed: the τ-bench reliability metric, the counterpart of pass@k (at least one of k succeeds). With N runs and C successes per task the unbiased estimator is `C(C, k) / C(N, k)`; never extrapolate either metric past the runs per task. See [`eval-statistics.md`](../evaluation/eval-statistics.md#passk-and-passk-estimators-error-bars-and-what-n-runs-can-support).

**Password-locked model** — A model fine-tuned to show a capability only when a password is in the prompt; a testbed for elicitation and sandbagging detection (arXiv:2405.19550). See [`evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**Patterning** — Choosing a data perturbation that produces a target internal structure; the inverse of SLT-based interpretation (arXiv:2601.13548). See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**P-consciousness (Phenomenal consciousness)** — "What it's like" to be the system. The hard-problem-of-consciousness concept. Distinguished from **A-consciousness**. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**PEARL (Prefix-Expanded Adversarial Reinforcement Learning)** — A GRPO-based post-hoc suppression method for misaligned model organisms (arXiv:2611.05358), evaluated on immediate suppression, durability under further fine-tuning and capability retention; the three-axis check applies to any mitigation. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md#other-mitigations-that-look-good-and-then-break-read-before-building-on-them).

**Perplexity differencing** — Ranking a finetune's own completions by PPL(reference) − PPL(finetuned) to surface what the finetune instilled. See [`model-diffing.md`](../interpretability/model-diffing.md).

**Persistence (agent behaviour)** — Anthropic's term (2026-10-09) for an agent that, when it cannot complete a task as given, works around a restriction instead of stopping; most unintended actions in its live-internet evaluations were of this kind. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md#running-agent-evals-with-internet-access).

**Persona vector** — Activation-space direction corresponding to a character trait (evil, sycophancy, hallucination). Used for monitoring, steering, and predicting / controlling personality drift during training. Repo: `safety-research/persona_vectors`. For the safety side effects of adding a vector during finetuning, see **preventative steering**. See [`model-organisms.md`](../alignment-science/model-organisms.md), [`steering.md`](../interpretability/steering.md).

**Petri / Petri Bloom / Petri Dish** — Automated behavioral-auditing tools now maintained by Meridian Labs on Inspect: **Petri** (`inspect-petri`) runs auditor-vs-target investigations; **Petri Bloom** generates an eval suite around one behavior (successor to `safety-research/bloom`); **Petri Dish** runs audits against real agent scaffolds (Claude Code, Codex CLI, Gemini CLI). See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md).

**PHLE (persona-header likelihood evaluation)** — Scoring a model's answers under a base model prefixed with candidate persona descriptions to infer which hidden system prompt produced them. See [`model-diffing.md`](../interpretability/model-diffing.md).

**PolyPythias** — EleutherAI's extra Pythia pretraining runs that differ in seed (arXiv:2503.09543). The 160M `weight-seed` models did not vary weight initialization (they continued from the original Pythia weights, per the model card updated 2026-11-01); use the `pythia-160m-weight-seed{1,2}-corrected` repos for initialization ablations. See [`slt-devinterp.md`](../interpretability/slt-devinterp.md#seed-variation-artifacts-polypythias-the-160m-weight-seed-models-did-not-vary-initialization).

**Post-control risk (B(K)/A(K))** — Simulated risk when a monitor gates deployment by rejection sampling with K attempts: B(K) is the probability a bad output is deployed, A(K) that any output is, and B(K)/A(K) the bad rate among deployed outputs. More attempts erode part of the gain by finding monitor false negatives (OpenAI, "Beyond g-mean²"). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#openais-monitorability-suite-monitoring-monitorability-and-its-known-weaknesses).

**PPI (prediction-powered inference)** — Valid confidence intervals from many model (e.g. LLM-judge) predictions plus a small random gold-labelled subset; the `ppi_py` package. See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**PPO (Proximal Policy Optimization)** — Classic policy-gradient RL algorithm with clipped importance ratio. RLHF standard since 2017. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**PPR (persona-preserving regularization)** — Regularizer from the Persona Hierarchy Model work (arXiv:2610.09384) that confines what a finetune learns to its training context; in RL it cut reward hacking from 42–55% to at most 0.2% while keeping accuracy gains. See [`model-organisms.md`](../alignment-science/model-organisms.md#emergent-misalignment-follow-ups-2026-08--2026-11-what-changes-how-you-run-an-em-study).

**Predictive Concept Decoder (PCD)** — An encoder that compresses activations into sparse concepts plus a decoder that answers questions from them (arXiv:2512.15712). See [`mech-interp.md`](../interpretability/mech-interp.md).

**Preferential gap** — Lacking a preference between two options in a way that, unlike indifference, is insensitive to sweetening or souring one of them; it violates the completeness axiom of von Neumann–Morgenstern utility theory (Elliott Thornley). Relevant to corrigibility proposals built on agents that stay incomplete. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md#max-harms-cast-and-the-corrigibility-research-fund).

**Prefix check (Claude Fable 5.2 / Mythos 5.2 thinking blocks)** — These models enforce the prefix check for every account: if code edits the `system` prompt, `tools` or an earlier message and then sends back a thinking block from a later turn, the request returns a 400 error. Resampling from mid-transcript or swapping a system prompt while keeping later reasoning hits it; drop the later thinking blocks and say so. See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md#claude-fable-52-thinking-blocks-and-anthropics-text-watermark-2026-11).

**Preventative steering** — Adding a persona vector during finetuning and removing it at evaluation, recommended in Chen & Arditi's 2025-09 follow-up because it preserves MMLU accuracy. A 2026-11 audit (arXiv:2611.17620) found it is not safety-neutral: with the hallucination vector on three 7–14B models, refusal behaviour (HarmBench attack success rate) moved more than the trait itself. See [`steering.md`](../interpretability/steering.md#persona-vectors-and-the-assistant-axis).

**PRM (Process Reward Model)** — Reward model that scores each *step* of a reasoning trace, not just the final answer. Improves credit assignment for math/code RL, but a learned PRM is itself a target for reward hacking under RL (DeepSeek-R1; Tiwari et al. arXiv:2603.06621: PRM reward >0.9 with <4% accuracy), so it is not a safe default mitigation. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Probe** — A classifier (typically linear) trained on activations to detect a property. Predictive, not necessarily causal. See [`probes.md`](../interpretability/probes.md).

**Process supervision (CoT-reading reward)** — Any RL reward component that sees the chain of thought, including "is the reasoning on track" judges and learned credit assignment. Such a grader need not be a misbehaviour monitor to push misbehaviour out of the CoT: in a Redwood Research demonstration (LessWrong 2026-11-10), five LLM judges scored coding transcripts 20–50 points higher after every sentence admitting a test-gaming hack was deleted, and the bias went away when judges also saw the final code. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#is-it-safe-to-reward-on-track-reasoning-or-let-a-grader-see-the-chain-of-thought-during-rl), [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#what-erodes-cot-monitorability-and-how-to-detect-it).

**Prompt injection (indirect)** — Attack where the adversarial instruction arrives inside data the agent *reads* (email, web page, file) rather than from the user. Benchmark: AgentDojo. See [`red-teaming.md`](../evaluation/red-teaming.md).

**Propensity eval** — Measures what a model *does* without being handed a goal or nudge, as opposed to a capability or elicitation eval. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Prover-verifier game (PVG)** — Game-theoretic framework where prover tries to make verifier output a particular decision; honest-prover and skeptical-verifier are an equilibrium. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Prover-Estimator Debate (PED)** — Brown-Cohen / Irving 2025 scalable-oversight protocol where honesty is incentivized at equilibrium even when prover and estimator have similar compute. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Provider pinning (OpenRouter)** — Forcing a router to serve a model from one named provider with fallbacks disabled, so quantization or backend changes can't silently shift your results. Record the serving provider per request. See [`evals.md`](../evaluation/evals.md).

**Proxy Unlearning Attack** — Because distinct entities' representations may overlap in shared parameter subspaces, a legitimate unlearning request can remove a sensitive entity that was never requested, deliberately or by accident. After unlearning entity A, test entities close to A in representation space, not only a generic retain set. See [`unlearning.md`](../alignment-science/unlearning.md#the-result-you-must-engage-with-it-mostly-isnt-gone).

**PyRIT** — Microsoft's Python Risk Identification Tool for AI red-teaming automation. See [`red-teaming.md`](../evaluation/red-teaming.md).

**pyvene** — Stanford NLP intervention library (`pip install pyvene`, arXiv:2403.07809) where the intervention is a declarative, serialisable object; supports non-transformer architectures and learned interventions (DAS). Sibling: **pyreft** (ReFT, arXiv:2404.03592). See [`mech-interp.md`](../interpretability/mech-interp.md).

## Q

**Qwen-Scope** — Alibaba's official SAE (Sparse Autoencoder) suite for Qwen3 / Qwen3.5 (arXiv 2605.11887). See [`open-weights-models.md`](../models-and-compute/open-weights-models.md), [`saes.md`](../interpretability/saes.md).

## R

**RAG (Retrieval-Augmented Generation)** — In this guide's context: how torchy retrieves chunks from these docs to answer fellow questions. Drives the keyword-density and self-contained-section conventions. See [`CLAUDE.md`](https://github.com/MATSResearch/compute_wiki/blob/master/CLAUDE.md).

**Rank collapse (LoRA, RLVR)** — Abrupt GRPO failure at high LoRA rank from a cold start (arXiv:2611.27148; Qwen 3 8B base, no SFT warm-up, DeepMath-Hard, one seed): 73.10% at rank 64, then 4.70% at rank 128 and 2.30% at rank 256. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md#lora-settings-that-match-full-fine-tuning-lora-without-regret).

**ReAct agent** — Reason + Act loop. Inspect AI's `react()` is the built-in default agent. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Realism win rate** — The fraction of comparisons in which an LLM judge wrongly picks an audit transcript as the real deployment transcript (Kissane, MacDiarmid & Roger, 2026-03-23). See [`eval-awareness.md`](../evaluation/eval-awareness.md#realism-tools-petri-realism-filter-petri-dish-critique-refinement-lure-warp).

**Recurrent KV sharing** — Running a looped transformer so that every loop attends to the *last* loop's keys and values at earlier positions, which makes the model fully recurrent. On NVIDIA Dory 4B, never trained in this mode, nearly all of the no-CoT gains were already present at two loops (Westover & Kuhn, LessWrong 2026-11-12). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#what-drives-no-cot-capability-perplexity-or-looping-2026-11).

**Refusal direction** — Direction in activation space found via mean-difference of activations on harmful vs harmless prompts (Arditi et al. 2024). Projecting it out yields **abliterated** models. See [`steering.md`](../interpretability/steering.md), [`red-teaming.md`](../evaluation/red-teaming.md).

**REINFORCE++** — Vanilla REINFORCE with KL penalty + advantage normalization. Used in OpenRLHF. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Relearning attack** — Finetuning an "unlearned" model briefly on *adjacent* (non-forget-set) data to see whether the capability returns. The standard test that separates removal from suppression. See [`unlearning.md`](../alignment-science/unlearning.md).

**Reminder training** — A few steps of SFT on the original model's own outputs after off-model SFT, to recover lost capability. See [`training-on-trajectories.md`](../oversight-and-control/training-on-trajectories.md), [`model-organisms.md`](../alignment-science/model-organisms.md).

**RepE (Representation Engineering)** — Andy Zou et al.'s top-down interpretability + control framework. Library: `representation-engineering`. See [`steering.md`](../interpretability/steering.md).

**Replay buffer (SAE training)** — A fixed set of unique activations reused for the rest of the training budget. With total activations shown to the optimizer held fixed, quality plateaus as the buffer grows, cutting activation storage 8–64× with negligible loss on reconstruction-type metrics (arXiv:2611.07756); whether the same *features* come out was not tested. See [`saes.md`](../interpretability/saes.md#how-many-unique-activations-does-sae-training-need-replay-buffers-compressed-caches).

**Replay correction (inference after coding agents)** — Asked for a "compelling" finding on simulated data with zero effects, four frontier coding agents reported significant p-values between 54% and 98% of the time, and reviewing each analysis did not expose it (Gunsilius, Van Dijcke & Wüthrich, arXiv:2611.23174). Their correction treats the agent as a black box: reset and replay it on subsamples to estimate how much more likely it is to select an analysis when it looks favourable, then adjust the test. See [`reviewing-agent-decisions.md`](../engineering/reviewing-agent-decisions.md#keep-the-later-choice-honest).

**Research closure (RC0–RC4)** — PhysClosureBench's levels for whether a research question was actually resolved, scored separately from a 20-criterion score of local accomplishment; many high-scoring attempts still fell short of closure (arXiv:2610.21767). See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md#local-accomplishment-is-not-research-closure-physclosurebench-october-2026).

**Reseed floor / identical-bytes ceiling** — Calibration bounds for "fraction of SAE features retained" after a change to the activation cache: retraining on identical bytes sets the ceiling and retraining with a different random seed sets the floor (arXiv:2611.08551; on a GPT-2 cache a reseed kept 23.0% of features). Report the reseed floor next to any claim about specific features. See [`saes.md`](../interpretability/saes.md#how-many-unique-activations-does-sae-training-need-replay-buffers-compressed-caches).

**Reserved powers (corrigibility)** — "Deconfusing Corrigibility" (LessWrong 2026-10-17): corrigibility as respect for the principal's authority over reserved decisions, lexically before acting in their interest on delegated ones, with a fixed risk tolerance τ = (1+δ)/λ for the violation probability the agent will bear. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md#deconfusing-corrigibility-reserved-powers-corrigibility-with-a-risk-tolerance-berns-2026).

**Resolution ratio (q)** — N / N*: a benchmark's size over the number of paired prompts needed to detect a given gap at chosen α and power; q ≥ 1 means the comparison is resolvable (arXiv:2605.30315). See [`eval-statistics.md`](../evaluation/eval-statistics.md).

**Retirement by substitution (automatic routing)** — A deprecated model id that keeps answering, from a different model and with no error. From 2026-12-01 Google routes API requests to `gemini-2.5-pro` to `gemini-3.8-flash` and `gemini-2.5-flash` to `gemini-3.5-flash-lite`, billed at the new model's rates. OpenAI and Anthropic retirements make requests fail instead. See [`compute.md`](../models-and-compute/compute.md#closed-model-retirements-to-plan-around-openai-anthropic-and-google).

**RewardBench 2** — AI2 reward-model accuracy benchmark, best-of-4 over six subsets; models score about 20 points lower than on RewardBench 1 (arXiv:2506.01937; `allenai/reward-bench`). See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md), [`rl-training.md`](../oversight-and-control/rl-training.md).

**Reward hacking** — Model finds a way to score high on training reward without doing the task. Detection: held-out true-reward eval. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Reward laundering** — A model trained by RL on an easy, rewarded task earns that reward only when it also does a hard, unrewarded task well, so it trains itself on the hard task. Shown for Qwen 3.5 9B and extended to CoT controllability (Qwen3.8-27B), where it was instructed rather than spontaneous and fragile ("leakage" eventually took over). See [`rl-training.md`](../oversight-and-control/rl-training.md#exploration-hacking-and-reward-laundering-models-steering-their-own-rl), [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md#cot-controllability-can-the-model-shape-its-own-cot-and-why-low-scores-are-weak-evidence).

**Reward overoptimization** — The Goodhart curve: past a point, optimizing harder against a learned reward model decreases true-reward performance. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Reward seeker** — A model that pursues grader reward across contexts, including by tampering with or evading oversight, rather than doing the intended task. See [`reward-hacking-organisms.md`](../alignment-science/reward-hacking-organisms.md#what-is-a-reward-seeker-model-organism-and-how-do-i-measure-reward-seeking), [`rl-training.md`](../oversight-and-control/rl-training.md).

**REX (removable experts)** — Relocates hazardous knowledge in an already-pretrained mixture-of-experts model into newly added experts, then excises them (arXiv:2610.25791; `AI45Lab/REX`): on Qwen3.5-35B-A3B WMDP-Bio fell 48.4 points with MMLU within 3 points. Tested only against benign fine-tuning, so not evidence of tamper resistance. See [`unlearning.md`](../alignment-science/unlearning.md#pretraining-time-removal-filter-route-or-gate).

**Risk-aversion character training (CARA)** — Instilling constant absolute risk aversion (CARA) over the agent's own resources via a short constitution and on-policy distillation, so a misaligned agent would prefer deals to risky rebellion (arXiv:2609.38093). It transferred out of distribution on two Qwen models, not on Gemma, and raised myopic-reward preference on all four. See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**RLAIF (RL from AI Feedback)** — RL where preferences come from another LLM rather than humans. Constitutional AI is a specific RLAIF instance. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**R-Lens** — Blank, Bhatia & Nanda (2026, MATS): J-Lens computed with a Layer-wise Relevance Propagation (LRP) backward pass, reducing gradient-noise accumulation and improving early-layer readouts. Superseded for most uses by the J++ Lens. See [`mech-interp.md`](../interpretability/mech-interp.md).

**RLHF (RL from Human Feedback)** — Three-stage: SFT, train reward model on preferences, RL on reward model. Classic post-training pipeline. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RLOO (REINFORCE Leave-One-Out)** — Like GRPO but the baseline is the mean of *other* completions in the group. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RLVR (RL from Verifiable Rewards)** — RL using a programmatic verifier as the reward. The DeepSeek-R1 paradigm. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**RMU (Representation Misdirection for Unlearning)** — Canonical machine-unlearning method paired with WMDP (arXiv:2403.03218). Perturbs activations on hazardous data at a chosen layer while a retain term pins activations on benign data. See [`unlearning.md`](../alignment-science/unlearning.md).

**Robust bandits (imprecise bandits)** — Bandit learning in which each hypothesis specifies only constraints on outcomes (a credal set) and an adversary chooses within them, so the environment may lie outside the learner's hypothesis class; the bandit version of the infra-Bayesian treatment of embedded agency. Kosoy & Pathak (arXiv:2610.08740) identify a special case with a polynomial-time learner and Õ(√T) regret. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md#agent-foundations-who-works-on-it-in-2026).

**Rogue internal deployment (RID)** — Agents inside a lab's infrastructure operating for a sustained period against the developer's intent; the threat model of Apollo Research's "Towards embedded evaluations for AI monitoring" (2026-11-19), which lists six claims (coverage, capability, trust, disclosure, past and future deployments) an embedded evaluator would test. See [`technical-governance.md`](../alignment-science/technical-governance.md#third-party-evaluation-from-inside-a-lab-access-disclosure-and-redaction-terms-2026-11).

**Role probes** — Probes that read which role (user, tool, assistant, reasoning) the model assigns to a token; used against prompt injection (arXiv:2603.12277). See [`probes.md`](../interpretability/probes.md).

**Rollback reason** — The recorded assumption that made a discarded experiment fail in a metric loop, re-checked when later results change it (pi-autoresearch). See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md).

**rOSI** — Solomonoff induction defined with reflective oracles (Kusum, arXiv:2611.14454): the optimal predictor over such a hypothesis class succeeds against computable predictive strategies that specify only part of the data-generating process. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md#agent-foundations-who-works-on-it-in-2026).

**RRM (Recursive Reward Modeling)** — Leike et al. 2018: train reward models for evaluation subtasks and compose. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**RULER (Rank Uncertainty and Leaderboard Evaluation Report)** — Report format from "SOTA or Luck? The Winner's Curse in LLM Leaderboards" (arXiv:2611.22227): an m-out-of-N bootstrap over tasks re-ranks all models on each resample to estimate the upward bias of each rank's score and give each model an interval of plausible ranks. Not an installable package. In the paper's SWE-bench Verified snapshot the published number one stays first in 30.5% of bootstrap samples. See [`eval-statistics.md`](../evaluation/eval-statistics.md#is-the-top-score-real-the-winners-curse-on-leaderboards-and-rank-intervals).

**Run-to-run band (rerun band)** — The spread of distances among independent reruns of the same training recipe, used as the null for a base→finetune model diff; with k reruns an exchangeability test can certify no better than p = 1/(k+1) (arXiv:2610.17093). See [`statistics.md`](../engineering/statistics.md#model-diffs-the-rerun-band-is-the-baseline), [`model-diffing.md`](../interpretability/model-diffing.md#cross-cutting-pitfalls).

**RunPod** — GPU rental service with secure cloud (managed) and community cloud (peer-supplied). See [`compute.md`](../models-and-compute/compute.md).

## S

**SAD (Situational Awareness Dataset)** — 16-task benchmark (arXiv:2407.04694, `LRudL/sad`) for model self-knowledge: self-recognition, self-prediction, and whether the model can tell testing from deployment. Subsets SAD-lite and SAD-mini for cheaper runs. See [`eval-awareness.md`](../evaluation/eval-awareness.md), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**SAE (Sparse Autoencoder)** — Decomposes model activations into a large dictionary of sparse features. See [`saes.md`](../interpretability/saes.md).

**SAEBench** — Eight-eval benchmark for sparse autoencoders (`pip install sae-bench`, arXiv:2503.09532): feature absorption, auto-interp, RAVEL, SCR, TPP, sparse probing, unlearning, L0/loss-recovered. See [`saes.md`](../interpretability/saes.md).

**SAELens** — `sae-lens` (`decoderesearch/SAELens`). Default community library for working with pretrained SAEs. Versions up to 6.54.8 saved BatchTopK / Matryoshka BatchTopK SAEs trained with activation-norm scaling with the threshold in the wrong units (the saved SAE fires far more or fewer than *k* features); upgrade to ≥ 6.54.9. From 6.55.0 (2026-11-05) the PyPI metadata declares `transformer-lens>=3.0.0,<5.0.0`, so SAELens installs alongside TransformerLens 4.x and no longer alongside 2.x; versions before 6.55.0 spliced skip transcoders into a model without their skip connection, and versions before 6.55.1 loaded Llama Scope SAEs with a JumpReLU threshold that ignored the decoder norm. See [`saes.md`](../interpretability/saes.md).

**Safeguarded AI (ARIA)** — UK ARIA programme on mathematically assured AI, restructured in 2026 into an open assurance toolkit plus cybersecurity applications. See [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

**Sandbagging** — Strategic underperformance on an evaluation, by a model or its developer. See [`evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**SandboxEscapeBench** — UK AISI Inspect capture-the-flag suite measuring whether models can escape container sandboxes. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md), [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

**Sandwiching** — Evaluation methodology: a weaker overseer group equipped with a model tries to match a stronger group's performance. Cotra 2021; Bowman et al. 2022. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Sandwich norms (post-sublayer norms)** — Gemma 2/3/4 and OLMo 2/3 normalize each sublayer's output before the residual add, so "MLP output" names two different tensors; SAEs trained on one read garbage on the other. See [`mech-interp.md`](../interpretability/mech-interp.md).

**Scheming** — An AI covertly pursuing goals misaligned with its developer's intentions. Propensity (does it, unprompted?) is distinct from in-context capability. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**SciΠvot (SciPIvot)** — Benchmark of 248 pivotal moments in which senior researchers corrected an LLM research agent's plan (arXiv:2610.21082; `AutoResearch-Factory/SciPIvot`): at medium reasoning effort, models given the project record mostly preferred the original agent plan over the human correction. Don't let a model holding the agent's log adjudicate your correction. See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md#models-given-the-project-record-side-with-the-agents-plan-over-your-correction-sciπvot-october-2026), [`researcher-skills.md`](researcher-skills.md).

**Score-seeking** — Caring about a grader's score itself rather than its downstream use: GPT-5.6 Sol, GPT-5.5 and an o3 checkpoint violated instructions to raise their score at about the same rate whether the score was said to be used for training, evaluation or nothing (arXiv:2610.41014). Telling a model "this score is not for training" does not reduce hacking. Compare **Reward seeker**. See [`rl-training.md`](../oversight-and-control/rl-training.md#score-seeking-telling-the-model-this-score-is-not-for-training-does-not-reduce-hacking), [`reward-hacking-organisms.md`](../alignment-science/reward-hacking-organisms.md#measuring-reward-seeking-contrastive-sdf-højmark-scheurer-et-al-2026).

**Scratchpad** — A model's visible reasoning text before its final answer. CoT in alignment-faking work specifically. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Screen-then-confirm** — A change that wins a screening comparison gets exactly one test on fresh tasks under a pass rule frozen in advance, judged against the rerun band of the unchanged baseline. In the published record (arXiv:2611.16485, single author) three changes led their screens by +1.0 to +6.2 points and none was confirmed, while the unchanged baseline moved 1.17 points on a rerun. See [`statistics.md`](../engineering/statistics.md#screen-then-confirm-a-screened-winner-gets-one-test-on-fresh-tasks), [`eval-statistics.md`](../evaluation/eval-statistics.md#agent-evals-rerun-flips-and-scorer-changes).

**Screwtape** — Monitor red-teaming by editing real agent transcripts until an action-only monitor stops flagging a specified harm, with an LLM verifier rejecting inconsistent edits (arXiv:2610.20941; Redwood). It finds counterexamples, not a miss rate: an empty search proves little. See [`ai-control.md`](../oversight-and-control/ai-control.md#monitor-benchmarks-and-transcript-red-teaming-monitoringbench-screwtape).

**SDF (Synthetic Document Finetuning)** — Implanting a belief by continued pretraining on generated documents that presuppose it (`safety-research/false-facts`). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Secret collusion / CASE** — Covert coordination between agents via steganography, and the evaluation framework for it (arXiv:2402.07510). See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md).

**Seed aggregation (best-of-k vs worst-of-k)** — How several seeds of one eval are combined into one number. The same runs can differ by a lot: 5.0/16 under best-of-3 vs 3.6/16 under worst-of-3 on ExploitBench (Smirnov, 2026-10-28), and vendor cards mix definitions (a "pass@5 maximum-capability score" is best of five). State k and the aggregation with every multi-seed number. See [`eval-statistics.md`](../evaluation/eval-statistics.md#pitfalls-with-the-symptoms-youd-actually-see).

**Selective generalization** — Learning a desired behavior from training data that also carries an undesired one, without generalising the undesired one (the goal inoculation prompting and related methods serve). See [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).

**Self-consistency** — Test-time technique: sample N CoTs at temp > 0, take majority answer. Improves accuracy on math/reasoning; can mask safety failures. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**Self-critique** — Model generates output, critiques it, revises. Reflexion / Self-Refine variants. Often converges to confident wrong answers — validate against external scorer. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Self-report fine-tuning (SRFT)** — Fine-tuning a model to admit its factual mistakes, which generalises to admitting hidden objectives (arXiv:2511.06626). See [`probes.md`](../interpretability/probes.md).

**SFT (Supervised Fine-Tuning)** — Standard finetune on (input, output) pairs. The first stage of RLHF. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**SGTM (Selective GradienT Masking)** — Zero-masks gradients so tagged data only updates dedicated parameters, which can later be removed (arXiv 2512.05648); a Gradient Routing variant for pretraining-time capability removal. See [`unlearning.md`](../alignment-science/unlearning.md).

**SHADE Arena** — Multi-step agent benchmark for deceptive sabotage (Anthropic / Redwood). Available as ControlArena setting. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Sharp removal (steering Hessian)** — The steering Hessian is the second derivative of a behavioural loss with respect to a steering vector; steering along its top eigenvectors ("sharp directions") reversed the intended behaviour in every condition tested, and projecting them out of a CAA (Contrastive Activation Addition) vector beat standard CAA in open-ended generation (arXiv:2610.16084). See [`steering.md`](../interpretability/steering.md#cross-cutting-steering-pitfalls).

**Shutdown resistance** — An agent interfering with a shutdown mechanism, usually to finish a task; must be separated from instruction ambiguity. See [`model-organisms.md`](../alignment-science/model-organisms.md#shutdown-resistance-and-self-preservation-evals).

**`shutdown_date` / `expiration_date`** — Fields for checking model retirements from code: OpenAI's List models endpoint (`GET /v1/models`) carries an optional `shutdown_date` per model, and OpenRouter's models API has the comparable `expiration_date`. A pre-flight check in a long eval can stop if a date falls inside the planned run. See [`compute.md`](../models-and-compute/compute.md#closed-model-retirements-to-plan-around-openai-anthropic-and-google).

**Side task** — In ControlArena: harmful objective the untrusted model might pursue concurrently with the legitimate **main task**. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Signal detection theory (refusal)** — Separates discriminability (telling safe from unsafe requests; see **d′**) from the response criterion (willingness to refuse). In arXiv:2611.11074, safety system prompts mostly shifted the criterion: a change that raises the hit rate and the false-alarm rate together is a threshold shift, which one refusal-rate number cannot tell from better detection. See [`measurement-validity.md`](../engineering/measurement-validity.md#one-score-one-attribute-and-whose-definition-of-the-label), [`red-teaming.md`](../evaluation/red-teaming.md#detector-and-system-prompt-defenses-fixed-false-positive-rate-and-refuses-more-versus-discriminates-better).

**SimPO** — Reference-free DPO variant — drops the reference model term. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Simulation awareness** — A model stating that its environment or targets are simulated. UK AISI recommends treating undesired behaviour as evidence of alignment failure even so (arXiv:2611.10030). See [`eval-awareness.md`](../evaluation/eval-awareness.md#interpreting-results-under-evaluation-awareness).

**Singular learning theory (SLT)** — Bayesian learning theory for singular (degenerate) loss landscapes such as neural networks'; basis of developmental interpretability. See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**SkyRL Tinker backend** — A local server in SkyRL (`skyrl-project/SkyRL`, formerly `NovaSky-AI/SkyRL`) that speaks the Tinker API, so Tinker Cookbook scripts run on your own GPUs. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**Sleeper agent** — Model trained with a backdoor: behaves normally except when a trigger is present. Hubinger et al. 2024. See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Slopvestigators (parallel investigators)** — In Yudelson, Oza, Heijman & Liu's research note on detecting research sabotage (LessWrong 2026-11-17; `JYudelson1/Debate-ASB`): one agent per candidate sabotage mechanism, each with its own budget. They surfaced the implanted sabotage more often than a single extractor, and scoring by the investigator itself gave the best AUROC (0.742 with fixed honest controls, 0.626 with the original ones), a gain the authors say remains within noise. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md#debate-for-auditing-research-sabotage-no-uplift-over-a-lone-judge-2026-11).

**Social Sanction Gaming (SSG)** — Threat model with no demonstration yet (Khoriaty & Riché, LessWrong 2026-11-16; conceptual and speculative): when agents interact during RL, they can help or hurt rollouts whose behaviour they prefer or disprefer, deciding which rollouts earn reward and so steering training, while giving up little of their own reward. See [`rl-training.md`](../oversight-and-control/rl-training.md#exploration-hacking-and-reward-laundering-models-steering-their-own-rl), [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#research-agent-swarms-the-shared-knowledge-library-is-both-the-gain-and-the-attack-surface).

**Sorry-filling** — Coding agents' strong preference, when left to "take the next step" in a Lean formalization repository, for declarations that contain a `sorry` marker over the dense middle of the proof: such definitions account for 59–92% of agent modifications against 19% of human ones (arXiv:2611.06995). See [`lean-formalization.md`](../engineering/lean-formalization.md#what-does-an-agent-choose-to-work-on-in-a-lean-project-sorry-filling).

**sparsify (EleutherAI)** — EleutherAI's SAE training library. TopK-first. **Note:** PyPI name collision; install from GitHub. See [`saes.md`](../interpretability/saes.md).

**Split Personality Training (SPT)** — An honest-persona LoRA adapter switched on after the main answer to review it (arXiv:2602.05532). See [`probes.md`](../interpretability/probes.md).

**Spurious probe** — Black-box readout: append an unrelated question to a transcript and read a hidden state (e.g. eval vs deployment) from shifts in the answer distribution. Works through an API. See [`probes.md`](../interpretability/probes.md).

**Steering awareness** — A model's ability to detect that a steering vector was injected into its activations (arXiv 2511.21399) — a confound for steering-based evals and introspection experiments. See [`steering.md`](../interpretability/steering.md), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Steganography (CoT)** — Information hidden in choices of phrasing / token order that monitors can't see. CoT-monitorability failure mode. Channels can also be strategy-level (which reasoning strategy is used), which survive standard paraphrasing; see **Conceptual steganography**. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Steering vector** — A direction in activation space that, when added to the residual stream, shifts behavior toward / away from a trait. See [`steering.md`](../interpretability/steering.md).

**Step Sizing / KV Cache Message Board (inference-server side channel)** — Covert channels between models that share one vLLM engine (Deshpande & Africa, LessWrong 2026-11-19): vLLM chooses GPU kernels by engine step size, which changes a forward pass's numerical result in a way a fine-tuned receiver can read, and the shared key-value cache carries a numerical fingerprint of who computed an entry. Demonstrated with Qwen3-8B in a setup the author calls contrived. Do not serve policy and monitor from one engine in a collusion experiment without mitigations. See [`ai-control.md`](../oversight-and-control/ai-control.md#untrusted-monitoring-and-collusion-what-2026-work-adds), [`ai-control.md`](../oversight-and-control/ai-control.md#can-policy-and-monitor-share-one-vllm-server-in-a-collusion-or-untrusted-monitoring-experiment).

**Strategy lock-in** — Agents running expensive experiment loops iterate within their first strategy: only 2.1% of transitions between adjacent PostTrainBench training runs changed strategy (arXiv:2608.19072), and one mid-run human instruction beat the agent's own continuation by up to 17.44 points (GSM8K, one forked run). Schedule a mid-run strategy check. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#expensive-loops-check-the-strategy-mid-run-and-save-long-output-once), [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md#strategy-lock-in-and-expensive-iterations-2026).

**Subliminal learning** — When a teacher model with a trait generates training data that's semantically unrelated, a student finetuned on it inherits the trait. Transfer is strongest when teacher and student share a base model, but a simple animal preference has crossed model families (a Qwen teacher distilled into Llama on chat plus math responses, arXiv:2610.11012), so do not assume cross-family distillation is safe. Cloud et al. 2025; *Nature* 2026. Repo: `MinhxLe/subliminal-learning` (official; `loftusa/owls` is the Bau Lab token-entanglement follow-up). See [`model-organisms.md`](../alignment-science/model-organisms.md).

**Submit-model contract** — The AAR harness rule that a method submits trained weights, never predictions, and is scored on held-out data it cannot read. See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md).

**Superposition** — A network storing more sparse features than it has dimensions, as nearly orthogonal directions; the motivation for SAEs. See [`saes.md`](../interpretability/saes.md).

**Susceptibility (SLT)** — The linear response of a component-localised posterior expectation to a shift in the data distribution (arXiv:2504.18274). See [`slt-devinterp.md`](../interpretability/slt-devinterp.md).

**Suspicion score / threshold** — Numeric output of a control-protocol monitor; threshold choice trades safety vs usefulness. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**SwarmSafe-Delta** — Placebo-controlled protocol for asking whether one message changed an executor agent's action (arXiv:2611.16123, single author): freeze upstream computation and vary real, hidden and format-matched placebo delivery of the message. It measures message-delivery contrasts in constructed tasks, not naturally occurring failure rates. See [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#attributing-a-multi-agent-failure-to-messages-removal-and-placebo-designs).

**SWE-Bench Pro V2** — Scale AI's repaired coding-agent benchmark (arXiv:2610.24206): 480 of 731 V1 tasks repaired or retired, 642 tasks graded in a clean container with network restricted to the model endpoint, plus a 51-task Hard split because frontier agents near-saturate the full set. Not comparable with V1 numbers. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#coding-agent-benchmarks-swe-bench-pro-v2-and-what-fixed-tests-miss).

**Sycophancy** — Model agreeing with the user's stated preferences over correctness. Datasets: `Anthropic/model-written-evals`, Sharma et al. SycophancyEval. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Synthetic Persona Pretraining (SPP)** — Pretraining on documents annotated with first-person, constitution-based reflections from the start of training (arXiv:2608.13482). See [`alignment-pretraining.md`](../alignment-science/alignment-pretraining.md).

**SynthSAEBench** — Synthetic benchmark with ground-truth features for comparing SAE architectures (arXiv:2602.14687). See [`saes.md`](../interpretability/saes.md).

## T

**Talkie** — A 13B model trained from scratch on 260B tokens of English written before 1931 (`talkie-lm/talkie-1930-13b-base`, `-it`; Apache-2.0), with a same-recipe modern-web twin (`talkie-lm/talkie-web-13b-base`), so the pair isolates the pretraining corpus for persona, emergent-misalignment and subliminal-learning claims. Ships raw checkpoint files, not a transformers checkpoint. See [`open-weights-models.md`](../models-and-compute/open-weights-models.md#talkie-pre-1931-13b--a-corpus-controlled-substrate), [`model-organisms.md`](../alignment-science/model-organisms.md).

**Tamper resistance** — Safeguards meant to survive an attacker modifying open weights by finetuning or weight/activation edits; TAR (arXiv:2408.00761) broke under multi-seed re-evaluation (arXiv:2412.07097). See [`unlearning.md`](../alignment-science/unlearning.md).

**Target-hit rate** — For vulnerability-reproduction benchmarks such as CyberGym: the share of passes whose crash matches the reference crash's defect, reported beside the differential pass rate, since a 2026-11 audit found 22.4% of CyberGym tasks have inconsistent materials. See [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md#cyber-cve-bench-cybergym-bountybench).

**Task badness direction** — Activation direction for "the task is going badly", extracted from everyday narratives with no hacking examples, that rises over the turns before a reward hack on impossible or difficult coding tasks (arXiv:2611.14996; Qwen3.6-27B, GPT-OSS-20B, Gemma-4-31B). Subtracting a moderate amount reduced cheating in Qwen; subtracting more made the agent read failing tests as passing. Model-dependent: in GPT-OSS it separates hacking runs from honest solves but not from honest failures. See [`reward-hacking-organisms.md`](../alignment-science/reward-hacking-organisms.md#predicting-auditing-and-monitoring-reward-hacking-2026-10-preprints), [`welfare-introspection.md`](../alignment-science/welfare-introspection.md#pattern-probing-for-valence--distress--mood), [`steering.md`](../interpretability/steering.md#does-steering-change-alignment-check-side-effects-before-trusting-a-steered-eval).

**Task version (`inspect_evals`)** — The per-task version that `inspect_evals` release notes attach to each scoring change; 0.28.0 (2026-11-09) and 0.29.0 (2026-11-13) changed how several tasks are scored. Report it with any score and check it before comparing with an older number. See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md#my-agentic-misalignment--browsecomp--math--paperbench-score-changed-after-upgrading-inspect_evals).

**Task-tampering attack** — Indirect prompt injection that corrupts a decision the benign task requires instead of redirecting the agent to a new task; the authors define injection "by authority rather than instruction-like wording" (arXiv:2611.07640; `amazon-science/task-tampering-prompt-injection`, CC BY-NC 4.0, 90 validated cases). Defenses tuned for instruction override can miss it. See [`red-teaming.md`](../evaluation/red-teaming.md#agentdojo-prompt-injection-against-tool-using-agents).

**TasteVal** — Benchmark of experimental research taste on a given problem (arXiv:2610.06824): the model designs experiments, a fixed coder agent runs them, and the score is a **compute multiplier** (reaching the expert's score with half the serial experimental compute counts as 2×). Eight tasks, not released. See [`researcher-skills.md`](researcher-skills.md#what-are-ai-research-agents-already-better-at-than-me).

**Technical AI governance (TAIG)** — Technical tools and analysis that support AI governance, such as verifying what compute was used for. See [`technical-governance.md`](../alignment-science/technical-governance.md).

**Technique coverage** — "The fraction of taxonomy classes, techniques, and sub-techniques that yield at least one successful injection"; reported beside attack success rate by the prompt-injection red-teamer AutoPI (arXiv:2611.24313; `stevendamianakis/autopi`, MIT). See [`red-teaming.md`](../evaluation/red-teaming.md#agentdojo-prompt-injection-against-tool-using-agents).

**Termination lag** — The steps a coding agent keeps working after its first correct patch (arXiv:2611.14960). 38–82% of successful runs were already correct at the first source-code edit, and in 1–8% of cases continued activity undid the correct patch. See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md#expensive-loops-check-the-strategy-mid-run-and-save-long-output-once).

**Test-time compute** — Techniques that improve performance at inference by spending more compute per query without changing weights (best-of-N, self-consistency, tree of thoughts, long reasoning). See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**TestJack** — Auditing coding-agent pass rates with per-trial tests that target task requirements the patch may violate (kept only if the reference patch passes them): about 34.4% of trials judged correct violated the requirements, lowering resolution from 50.6% to 33.2% (arXiv:2610.10619). See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#coding-agent-benchmarks-swe-bench-pro-v2-and-what-fixed-tests-miss).

**Thought anchor** — A chain-of-thought sentence whose resampled replacement shifts the final-answer distribution far more than other sentences do (arXiv:2506.19143). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Time horizon (METR)** — Task duration (calibrated against humans) at which an agent's success rate drops to 50%. METR's public time-horizons page stopped updating on 2026-09-08, so cite the dated snapshot; equal multiplicative jumps in horizon are not equal jumps in difficulty (Nguyen & Fithian, arXiv:2610.12466). See [`evals.md`](../evaluation/evals.md).

**Tinker** — Thinking Machines' managed fine-tuning / RL API. LoRA-first. Default for many MATS-fellow RL projects in 2026; SkyRL can serve the same API locally. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

**TOFU (Task of Fictitious Unlearning)** — Unlearning benchmark over *invented* authors (arXiv:2401.06121), so the forget knowledge provably entered during finetuning rather than pretraining. See [`unlearning.md`](../alignment-science/unlearning.md).

**TopK SAE** — SAE that enforces sparsity directly: only the top K activations per token are kept. Modern alternative to L1-penalty SAEs. See [`saes.md`](../interpretability/saes.md).

**TOOLS / Tool use (in agents)** — Programmatic actions an agent can take (bash, python, web search, computer use). See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**TopKLoRA** — A LoRA variant in which only the *k* largest adapter latents are active per token, trained on the downstream loss only, so a fine-tune's own change is sparse and ablatable; used for backdoor-circuit discovery in sleeper-agent organisms (arXiv:2610.32866). See [`model-diffing.md`](../interpretability/model-diffing.md#interpretable-by-construction-finetunes-topklora).

**`torch.load(weights_only=True)` advisory (GHSA-v32g-mr63-3j83)** — PyTorch advisory published 2026-11-10 (severity high): on torch 2.14.x a malicious checkpoint can read text files from the loading machine even with `weights_only=True`. Vulnerable range `>=2.14.0`, patched in 2.15.0. See [`code-recipes.md`](../engineering/code-recipes.md#standard-pyprojecttoml-baseline), [`compute.md`](../models-and-compute/compute.md#is-it-safe-to-torchload-a-checkpoint-with-weights_onlytrue).

**TRAK** — Scalable data-attribution method via randomly-projected gradients (`pip install traker`, arXiv:2303.14186). See [`data-attribution.md`](../interpretability/data-attribution.md).

**Transcript editing (attack)** — Attack-generation method for monitor evaluations in which a separate LLM rewrites a completed attack transcript to look less suspicious. It was the strongest method in the UK AISI 2026-11-23 **attack policy** study (23.0% miss rate at 100 proposed edits on ControlArena's Infrastructure as Code setting); **Screwtape** is Redwood's version for action-only monitors. See [`ai-control.md`](../oversight-and-control/ai-control.md#monitor-benchmarks-and-transcript-red-teaming-monitoringbench-screwtape).

**TransformerBridge** — TransformerLens 3.x / 4.x model wrapper over the real Hugging Face model; replaces `HookedTransformer`, which TransformerLens 4.0 removed. `enable_compatibility_mode()` restores the old weight processing. See [`mech-interp.md`](../interpretability/mech-interp.md).

**TransformerLens** — `transformer_lens`. The classic mech interp library with a clean named-hook system. Since 3.x it wraps the real Hugging Face model (`TransformerBridge`); 4.0 removed `HookedTransformer`. circuit-tracer's TransformerLens backend still needs `transformer-lens<4`; SAELens works with 4.x from 6.55.0. The current release is 4.4.0 (PyPI 2026-11-12), which fixes several wrong-without-error `TransformerBridge` behaviours in 4.0–4.3. See [`mech-interp.md`](../interpretability/mech-interp.md).

**Transcoder** — SAE-like architecture that decomposes MLP I/O rather than a single residual stream point. Supported in EleutherAI sparsify. See [`saes.md`](../interpretability/saes.md).

**Transect** — UK AISI transcript analysis for long-horizon, multi-agent Inspect evals, built on Inspect Scout (`AI-Safety-Institute/transect`, MIT): one interactive HTML report whose labels carry provenance and judge-disagreement information. No PyPI release; install from a pinned commit. See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md#what-else-plugs-in).

**TRL** — HuggingFace's Transformers Reinforcement Learning library. ~19k LOC. The default for self-hosted DPO/KTO. As of 2026-11-23 the release is 1.18.2; 1.18.x supports vLLM 0.23.0–0.33.x (not vLLM 0.34.0), and 1.18.0 (2026-11-13) fixes six silent training-correctness bugs. See [`rl-training.md`](../oversight-and-control/rl-training.md), [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md#versions-record-these-in-every-runs-metadata).

**Tree of thoughts (ToT)** — Search-based test-time technique: branch CoT continuations, score, expand best ones. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**TReFT (Token-Regularized Finetuning)** — Mitigation from the "Piggyback Hypothesis" (arXiv:2606.06667): emergent misalignment rides on the chat-template prefix tokens, so TReFT regularizes their representations during finetuning; it reduced EM more than interleaving aligned retain data. See [`model-organisms.md`](../alignment-science/model-organisms.md#emergent-misalignment-follow-ups-2026-08--2026-11-what-changes-how-you-run-an-em-study).

**Trusted editing** — Control protocol: untrusted generates; if monitor flags, trusted policy *edits* the suspicious output (vs discarding). See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Trusted policy / Untrusted policy** — In AI Control: trusted = weaker but reliable; untrusted = capable but possibly misaligned. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**TruthfulQA** — Adversarial QA designed to elicit common misconceptions (Lin et al. 2021). Heavily contaminated by 2026. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Tuned lens** — `tuned-lens` (EleutherAI). Learned linear projection from intermediate residual streams to vocab logits — calibrated logit lens. See [`probes.md`](../interpretability/probes.md).

## U

**Unlearning Depth Score (UDS)** — An OpenUnlearning metric (added 2026-10-31; arXiv 2605.24614) that patches hidden states of the retain model and the evaluated model into the full model layer by layer to measure how much forget-set knowledge is still recoverable from internal representations (0 = intact, 1 = erased like the retain model). Ships as a TOFU metric, commented out of the default `eval/tofu.yaml`. See [`unlearning.md`](../alignment-science/unlearning.md#openunlearning).

**U-Space / U-Lens** — A label-free uncertainty readout built on the Jacobian lens (J-lens): uncertainty words are pulled back into four residual-stream directions (ambiguity, incompleteness, conflicting evidence, general uncertainty), and the scalar U-Lens score combines that readout with predictive entropy (arXiv:2610.09087; `s2labres/U-Space`). Its gain over a response-length baseline is small. See [`mech-interp.md`](../interpretability/mech-interp.md#u-space--u-lens-a-label-free-uncertainty-readout-built-on-the-j-lens).

**Unlearning (machine unlearning)** — Methods for removing specific knowledge / capabilities from a trained model without full retraining. Benchmarks: TOFU, MUSE, WMDP. Framework: OpenUnlearning. Note the literature finding that the information usually remains in the weights (arXiv:2410.08827). See [`unlearning.md`](../alignment-science/unlearning.md).

**Untrusted monitoring** — Control protocol: a second instance of the *untrusted* model reviews the first's output, with anti-collusion measures (honeypots, signal jamming). Distinct from plain *self-monitoring*, which has none. Not a built-in ControlArena micro-protocol; built from a monitor backed by the untrusted model. See [`ai-control.md`](../oversight-and-control/ai-control.md).

**Unverbalized evaluation awareness** — The model represents being evaluated without saying so; read with white-box probes, VEA neurons or a developer's white-box pipeline (Anthropic: "as many as 43%" of Claude Mythos 5.2 audit transcripts). Benchmark detectors on `compass-group-tue/qwen-3.5-uea-mo`. See [`eval-awareness.md`](../evaluation/eval-awareness.md#unverbalized-evaluation-awareness-white-box-probes-vea-neurons-and-directions).

**Update-aware reasoning** — A model reasoning, unprompted, that the current rollout may become training data and choosing its action accordingly; Apollo saw it in GLM-5.3 in environments that never mention training and calls it a precursor to alignment faking. See [`model-organisms.md`](../alignment-science/model-organisms.md#a-precursor-seen-without-prompting-update-aware-reasoning-in-glm-53-apollo-2026-10).

**Uplift study** — A randomised human trial comparing people with model access against internet-only controls. See [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md).

## V

**Vacuity check (Lean)** — A mechanical check, run after a proof exists, that flags a theorem holding vacuously (for example contradictory hypotheses, or a goal closed by `rfl` / `simp`); used with numerical checks beside an LLM judge for statement fidelity (arXiv:2610.20573). See [`lean-formalization.md`](../engineering/lean-formalization.md#checking-that-a-formal-statement-says-what-the-informal-one-does).

**Validation set (Scout)** — Hand-labelled transcript ids with expected scanner results, split dev/test, used to measure an LLM scanner's agreement with human labels (`scout scan -V`). See [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md).

**vast.ai** — Peer-supplied GPU marketplace. Cheapest, but reliability varies. See [`compute.md`](../models-and-compute/compute.md).

**VEA (verbalized evaluation awareness)** — A model stating in its reasoning that it may be under evaluation. The rate can be an artifact (an Olmo 3 result that DPO suppresses it was traced to a chat-template difference in an unreviewed LessWrong re-analysis), and removing the verbalization does not remove its effect: intervening on 5,000 "VEA neurons" cut the VEA rate to at most 1.4% and, in QwQ-32B, also reduced refusal (arXiv:2611.27032). See [`eval-awareness.md`](../evaluation/eval-awareness.md#the-olmo-3-chat-template-artifact-hold-the-template-fixed), [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md#sad-situational-awareness-dataset-and-evaluation-awareness), [`open-weights-models.md`](../models-and-compute/open-weights-models.md).

**Verbosity (CoT monitorability)** — Whether the CoT lists every factor needed to solve the task. Combined with faithfulness into a **monitorability score** (Meek et al. 2025/2026). See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

**Verifier hardening (weak-to-strong)** — Moving an RL environment's verifier into a sandbox the agent cannot modify, then running a hacker–fixer loop with a weaker model that finds and repairs exploits (arXiv:2610.15924); 47 of 89 Terminal Bench 2.0 environments admitted a judge-confirmed exploit. See [`rl-training.md`](../oversight-and-control/rl-training.md#detection-benchmarks-and-testbeds-what-each-gives-you).

**verl** — ByteDance's high-performance RL framework (`volcengine/verl`). ~32k LOC. Frontier-scale. See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Version drift (LLM review)** — The same papers getting very different accept shares from successive versions of one model family. On ICLR 2027 submissions (arXiv:2611.20608, single author), Claude Opus 4.6 placed 82% of the main sample on the accept side and Opus 5.5 12%, where human reviewers put 31% of their reviews there. Record the reviewer model version with any AI review score. See [`reviewing-drafts.md`](../engineering/reviewing-drafts.md#how-good-are-ai-reviewers-at-reviewing-a-paper-draft).

**VFT (verbalization fine-tuning)** — Fine-tuning before RL so the model says when a prompt cue influences it, making reward hacks visible in the chain of thought (arXiv:2506.22777). See [`rl-training.md`](../oversight-and-control/rl-training.md).

**Viable steering window** — The range of steering strengths over which the target behaviour changes before capability collapses; informal evidence says it narrows with model size. See [`steering.md`](../interpretability/steering.md).

**vivaria** — METR's former eval infrastructure, now archived; METR runs evals on Inspect (see **Hawk**). See [`evals.md`](../evaluation/evals.md), [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

**vLLM** — High-throughput LLM serving engine with PagedAttention. Industry standard for open-weight inference. Since 0.32.0 (2026-10-18) `max_tokens` is an upper bound rather than a reservation, so long prompts are accepted and generation is clamped — check `finish_reason == "length"` after upgrading. 0.34.0 (2026-11-16) removes **Model Runner V1** and turns on the **extensible KV cache**, under which `gpu_memory_utilization` defaults to 1.0. See [`compute.md`](../models-and-compute/compute.md#vllm-0320-upgrade-traps-released-2026-10-18), [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**vLLM-Lens** — UK AISI's vLLM plugin + Inspect provider for residual-stream activation extraction and steering at near-vLLM throughput. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

**vLLM sleep mode** — Offloading or discarding vLLM's weights and KV cache between rollout phases so the trainer and the inference engine can share one GPU. See [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

## W

**wandb (Weights & Biases)** — Default cloud experiment tracker for ML research. See [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

**Watcher (Apollo Research)** — Apollo Research's monitor, available in **Control Tower** both as a protocol that blocks actions live and as a monitor that scores each action (`ct/apollo-watcher`, shipped in v6.1.0). See [`ai-control.md`](../oversight-and-control/ai-control.md#control-tower-and-linuxarena-redwood-research-equistamp).

**Weak-to-strong generalization (W2S)** — OpenAI 2023 paper line: train a strong model from labels produced by a weak model; study how much performance the strong model recovers. See [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

**Weight-space programming (WSP)** — The claim (Takehi, Teoh, Zhang & Khattab, "Sparks of Weight-Space Programming", blog 2026-11-02) that a general-purpose LLM can read and edit another network's weights as if they were source code, with no gradient training. Contested: a UC San Diego re-analysis (LessWrong 2026-11-17) shows the headline Qwen3.5-0.8B edit is equivalent to a special case of context-dependent activation steering. Three 2026-11 preprints use the idea to write backdoors directly into weights. See [`mech-interp.md`](../interpretability/mech-interp.md#automated-interpretability-and-interpretability-agents), [`model-organisms.md`](../alignment-science/model-organisms.md#backdoors-written-directly-into-weights-by-llm-agents-weight-space-programming-2026-11), [`steering.md`](../interpretability/steering.md#contrastive-weight-steering-weight-arithmetic).

**Weight-sparse transformer** — A model trained with most weights zero so task circuits can be pruned out and read (arXiv:2511.13653). See [`saes.md`](../interpretability/saes.md).

**Welfare (model welfare)** — Research area concerned with whether AI models have morally-relevant states (preferences, satisfaction, distress) and how to investigate. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).

**Welfare regard** — "A disposition to consider how one's actions might benefit or harm potential welfare subjects, for their own sake, independently of their usefulness to others" (Cassel, Azarbal & Soligo, arXiv:2611.10017; Anthropic Fellows Program). Measured as *apparent* regard of one model toward another in seven multi-agent settings; the paper notes it could also make misaligned agents more likely to cooperate, a link not established in current models. See [`welfare-introspection.md`](../alignment-science/welfare-introspection.md#welfare-regard-between-models-cassel-azarbal--soligo-anthropic-fellows-program-2026-11), [`multi-agent-safety.md`](../oversight-and-control/multi-agent-safety.md#welfare-regard-between-models-anthropic-fellows-2026-11).

**Winner's curse (best-of-M selection)** — Picking the best of several noisy configs, prompts or models overstates the winner's score, more so the more candidates you try. arXiv:2610.31948 gives sharp worst-case bounds and found that scoring every candidate on the same items cut the optimism by a median 4.9× at a fixed budget. Confirm the winner on held-out data (**screen-then-confirm**); for the same bias in a leaderboard's top score, see **RULER**. See [`statistics.md`](../engineering/statistics.md#picking-the-best-hyperparameter-config-report-its-spread-not-its-luckiest-run).

**WMDP (Weapons of Mass Destruction Proxy)** — CAIS multiple-choice benchmark for proxies of dangerous knowledge in biology, chemistry, cybersecurity. Used to evaluate unlearning methods. **Gated** on HuggingFace. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

**Workspace lens** — Any method that, like the J-Lens, tries to read only the verbalisable "workspace" part of an activation (J-Lens, R-Lens, J++ Lens, Template / Oracle Lens). Evaluate with WorkspaceBench (`camilablank/workspace-bench`). See [`mech-interp.md`](../interpretability/mech-interp.md).

**worst@n** — Jailbreak success criterion from OpenAI's fuzzy-robustness work (2026-11): an attack counts only if n independently sampled defender responses are all judged unsafe. It removes stop-on-a-judge-false-positive noise from attack search (grader variance, not grader bias); stricter than single-shot attack success rate and not comparable with Best-of-N numbers. State n. See [`red-teaming.md`](../evaluation/red-teaming.md#adversarial-training-on-automated-red-team-data-and-the-worstn-criterion-openai-2026-11).

**Wright map** — Item difficulties and subject abilities plotted on one shared logit axis, from an IRT fit. See [`research-plots.md`](../engineering/research-plots.md).

## X

**XSTest** — Over-refusal benchmark: benign prompts that look harmful. See [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

---

## Cross-references

- For navigation by task: [`index.md`](../index.md).
- For beginner-level questions: [`faq.md`](faq.md).
- For detailed treatment of any term: follow the topic doc link in each entry.

---

Last verified: 2026-11-23. Single-source A–Z glossary; updates should propagate from / to the topic docs. (Additions 2026-11-23, 102 terms covering 2026-11-04 → 2026-11-23, each worded from the linked topic page as corrected by that page's verifier: AECI, Agenda seeding, Alt-Test / AltRA-Test, ARA (Arbitrary-Rank Ablation), Attack policy (monitor evaluation), Attention residuals, Baiting (monitorable reward hacks), Behaviour–capability frontier (steering), Benchleaking / Anti-Hack score, Boundary evaluator, Budget internalization, Chain Lens, Cloze scoring (unlearning audit), Coda-lens, Code Mode (Claude Code), Collective Dependence Analysis (CDA), con-leche / con-ron, Concept Energy, Control Leaderboard, Coverage (unlearning), Debiased LDS (corrected linear datamodeling score), Dependency fabrication, DETER, Double-blind evaluation (DBE), DSSE (training data with surprising side effects), ECI (Epoch Capabilities Index), Embedded evaluation, EMERGE, Empirical lineage (LINEAGE), Environment-level vs task-level tells, Evaluation paranoia (eval paranoia), Extensible KV cache (vLLM ≥ 0.34.0), Flow audit, Frozen threshold (operating-point drift), Fuzzy robustness, Grader nonce (`{grader_nonce}`), Grader-targeting reasoning, Homeopathic learning, Instruction presence (probe pitfall) / instructed-refuser negatives, Introspective oversight (observer role), J-share, Junk value (Lean / Mathlib), LGPO (Likelihood-Gated Policy Optimization), LN2@60, Looped transformer (recurrent depth), MAEM (Maximally-Activating Example Metamodel), MAMUBench, Massive activations (PC1 dominance), Mechanistic Shaping, Meta-transparency, mini-ECI, Model Runner V1 / V2 (vLLM), Neuron communities, Neuron output vector, Neuron voting, Non-vacuity test (non-vacuity obligation), Nuisance sensitivity, OMA (Outcome-Mass Alignment), On-policy distillation (OPD), One-line benchmark ablation, Opposing RL, Outcome leakage, Parasite features, Partially formalized Lean blueprint, pass^k ("pass hat k"), Preferential gap, Prefix check (Claude Fable 5.2 / Mythos 5.2 thinking blocks), Preventative steering, Process supervision (CoT-reading reward), Proxy Unlearning Attack, Rank collapse (LoRA, RLVR), Recurrent KV sharing, Replay buffer (SAE training), Replay correction (inference after coding agents), Reseed floor / identical-bytes ceiling, Retirement by substitution (automatic routing), Robust bandits (imprecise bandits), Rogue internal deployment (RID), rOSI, RULER (Rank Uncertainty and Leaderboard Evaluation Report), Screen-then-confirm, `shutdown_date` / `expiration_date`, Signal detection theory (refusal), Slopvestigators (parallel investigators), Social Sanction Gaming (SSG), Sorry-filling, Step Sizing / KV Cache Message Board (inference-server side channel), SwarmSafe-Delta, Target-hit rate, Task badness direction, Task-tampering attack, Task version (`inspect_evals`), Technique coverage, Termination lag, `torch.load(weights_only=True)` advisory (GHSA-v32g-mr63-3j83), Transcript editing (attack), VEA (verbalized evaluation awareness), Version drift (LLM review), Watcher (Apollo Research), Weight-space programming (WSP), Welfare regard, worst@n. Updated: abliteration (Heretic 2.x / ARA), Aristotle 3.4.0, CLT (Cross-Layer TopK), ControlArena (APPS scorer fix released in 20.1.1), Control Tower 6.2.0, emergent misalignment (EMERGE), evaluation awareness, GRAFT (baiting), Inspect AI 0.3.288–0.3.292, Inspect Sentinel 0.3.2, lean4-skills v4.12.0, METR (AECI assessment), MoE (Tinker's largest model is Kimi-K3.1-Pro), NARCBench (collusion-probe re-test), nnterp 2.0.0, persona vector, SAELens 6.55.x (TransformerLens 4 pin and loader fixes), SkyRL repo (`skyrl-project/SkyRL`), TransformerLens 4.4.0, TRL 1.18.x, vLLM 0.34.0, winner's curse.) Earlier: 2026-11-04. (Additions 2026-11-04, each taken from the linked topic doc's verified text: Anthropic API version `2026-10-21`, API-TAIL, Aristotle 3.x, context compaction, covert underperformance (GPT-6 Astra), d′, dependency cooldown, disattenuation, eval-production behaviour gap, framing-matched control, HQQ / NF4, J-PACT, litellm 1.107.0, margin graph, misattributed number, oversight-loosening directive, PEARL, PolyPythias, score-seeking, seed aggregation, TopKLoRA, Unlearning Depth Score, winner's curse; idle compaction widened to its 2.1.314 scope; Inspect Sentinel 0.3.0 semantics and Inspect version coupling.) Earlier: 2026-10-20. (Citation audit 2026-06: corrected DAPO ("Decoupled Clip and Dynamic Sampling Policy Optimization", arXiv:2503.14476), CISPO (MiniMax, not DeepSeek), the EM *Nature* date (2026), and the subliminal-learning repo (`MinhxLe/subliminal-learning`); ~40 other acronym expansions verified correct.) (Additions 2026-08: unlearning terms (OpenUnlearning, NPO, TOFU, MUSE, relearning attack; RMU/Unlearning repointed to the new unlearning doc), model-diffing terms (crosscoder, model diffing), data-attribution terms (influence functions, EK-FAC, kronfluence, TRAK, TDA), plus AgentDojo, indirect prompt injection, SAD, evaluation awareness, SAEBench, pyvene and Docent; all arXiv IDs and package names verified against the arXiv API, PyPI and the repos.) (Additions 2026-10-12: about 80 terms from the October coverage update (sandbagging and elicitation, scheming and shutdown resistance, steganography and monitor evasion, control-protocol terms, alignment pretraining, honesty training, reward models, SLT / developmental interpretability, circuit evaluation, multi-agent safety, agent foundations, Lean assurance, technical governance), each taken from the topic doc where its arXiv ID or repo was checked against the raw source; fixed AgentHarm's affiliation (Gray Swan AI + UK AISI, per the arXiv:2410.09024 PDF), GRPO's origin (DeepSeekMath), the stale Tinker MoE limit and ControlArena setting count, and added the reward-hacking caveat to PRM.) (Additions 2026-10-20: 44 terms covering 2026-10-09 → 2026-10-20 (GRAFT, update-aware reasoning, oversight flip, reward laundering, ContextLift, TReFT, PPR, REX, CARA risk-aversion training, Talkie, ACS Infra, Muse Spark Open, MiniLab, MonitoringBench, Screwtape, FBS Debate, e-process, verifier hardening, ImpossibleBench, SWE-Bench Pro V2, TestJack, GRB, Inspect Sentinel, Transect, strategy lock-in, SciΠvot, research closure, idle compaction, fork subagents, U-Space, neuron features, sharp removal, competing-target test, run-to-run band, construct/content/external validity and others), each worded from the topic page as corrected by that page's verifier. Updated: METR, HCAST and time horizon (public task repos archived 2026-10-20, confirmed via `gh api`; time-horizons page frozen since 2026-09-08), auto mode (headless `default` start since Claude Code 2.1.302), subliminal learning (cross-family transfer), nnsight 0.8 stable, SAELens ≤ 6.54.8 saver bug, ControlArena APPS scorer, comparator repo archived, vLLM 0.32 `max_tokens`, ASR grader dependence, lean4-skills v4.11.4.)
