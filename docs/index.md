# Index: "I want to do X, use Y"

A decision guide to AI safety research tooling for MATS fellows. Each row points to the topic doc with full detail, pitfalls, and alternatives.

**Other navigation entry points:**
- **[`faq.md`](start-here/faq.md)** — cross-cutting beginner questions (API keys, where to start, costs).
- **[`glossary.md`](start-here/glossary.md)** — A–Z definitions of acronyms and concepts (CAA, GRPO, OOCR, RLAIF, etc.).
- **[`project-shapes.md`](start-here/project-shapes.md)** — "what does a paper-shaped project look like in this area?" (mech interp paper, behavioral paper, control eval paper, etc.).
- **[`researcher-skills.md`](start-here/researcher-skills.md)** — as agents take over experiment execution, which of your own skills to build (measurement design, verifying agent output, judging evidence, taste, not deskilling) and what to read.
- **[`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md)** — the 6-step methodological playbook for behavioral safety papers.
- **[`code-recipes.md`](engineering/code-recipes.md)** — copy-paste code recipes, judge-prompt template, anti-patterns.
- **[`statistics.md`](engineering/statistics.md)** — which test to run, what to put on the error bar, seeds vs samples, multiple comparisons, power.
- **[`visualization.md`](engineering/visualization.md)** — which plotting library, sweeps with confidence bands, heatmap colormaps, colour-blind-safe palettes.
- **[`training-on-trajectories.md`](oversight-and-control/training-on-trajectories.md)** — what to compute loss on in an agent trace: the mask-the-environment default, and the 2026 work training on tool/bash output as free supervision.
- **[`inspect-ecosystem.md`](evaluation/inspect-ecosystem.md)** — Meridian Labs' Inspect tooling beyond the core framework: Scout (transcript analysis), Petri (automated alignment auditing), Flow (eval sets).
- **[`research-plots.md`](engineering/research-plots.md)** — which figures are worth making: fine-tune monitoring, dataset cartography, lenses (logit/tuned/J/R), patching heatmaps, Pareto frontiers, calibration.
- **[`open-weights-models.md`](models-and-compute/open-weights-models.md)** — which open-weights model to use and why (DeepSeek-V4, Kimi K2.6, Gemma, Qwen, Llama).
- **[`agentic-swe-practices.md`](engineering/agentic-swe-practices.md)** — how to drive a coding agent (Claude Code, Codex, Cursor, Copilot, Aider) so it writes correct, reproducible research code instead of plausible-but-wrong slop.
- **[`ai-scientist-frameworks.md`](engineering/ai-scientist-frameworks.md)** — systems that automate the research loop (Sakana, Kosmos, AIDE, Curie, ScientistOne): which tier actually works, the measured failure rates, and four integrity checks to run on anything one hands you.
- **[`research-rigor.md`](engineering/research-rigor.md)** — the rules for keeping your own research honest when an agent does some of the work: the eleven research stages, pre-registration on both sides of a pilot, concerns that block, a verdict for every prediction, claim grounding, disclosure.

## I want to pick an open-weights model

Most large open models (DeepSeek-V4, Kimi, big Qwen) are too big to run locally — call them via **OpenRouter** (`OPENROUTER_API_KEY` in `~/projects/.env`) unless you need raw weights for fine-tuning / activations / SAEs. Slugs below; full detail, pricing, and modalities in [`open-weights-models.md`](models-and-compute/open-weights-models.md).

| Situation | Use | OpenRouter slug | Topic doc |
|---|---|---|---|
| Most capable open-weights model overall | **DeepSeek-V4-Pro** | `deepseek/deepseek-v4-pro` | [`open-weights-models.md`](models-and-compute/open-weights-models.md) |
| Genuinely usable very long context (up to 1M tokens) | **DeepSeek-V4** (Pro/Flash) | `deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4-flash` (`:free` exists) | [`open-weights-models.md`](models-and-compute/open-weights-models.md) |
| Open-weights stand-in for a Claude-like, "virtue-aligned" model (vision-enabled) | **Kimi K2.6** | `moonshotai/kimi-k2.6` | [`open-weights-models.md`](models-and-compute/open-weights-models.md) |
| Pretrained SAEs / transcoders off the shelf | **Gemma** + Gemma Scope | `google/gemma-3-27b-it` | [`open-weights-models.md`](models-and-compute/open-weights-models.md), [`saes.md`](interpretability/saes.md) |
| Capable small model to fine-tune cheaply | **Qwen3** family | `qwen/qwen3.6-35b-a3b` (+ other sizes) | [`open-weights-models.md`](models-and-compute/open-weights-models.md), [`model-organisms.md`](alignment-science/model-organisms.md) |
| Matched baseline to existing safety literature | **Llama** (3.1/3.3/4) | `meta-llama/llama-4-maverick` | [`open-weights-models.md`](models-and-compute/open-weights-models.md) |

## I want to extract activations from a model

| Situation | Use | Topic doc |
|---|---|---|
| Single small model (≤7B), maximal flexibility, custom hooks, want to teach yourself the residual stream | **TransformerLens** | [`mech-interp.md`](interpretability/mech-interp.md) |
| Any HuggingFace model, want to use the actual HF weights/architectures, dynamic intervention syntax | **nnsight** | [`mech-interp.md`](interpretability/mech-interp.md) |
| Need to extract activations or apply steering at vLLM throughput (millions of prompts, tensor-parallel, 70B+) | **vLLM-Lens** (UK AISI) | [`serving-and-activations.md`](interpretability/serving-and-activations.md) |
| Want to run interpretability on a 405B model you can't host yourself | **NDIF** (nnsight remote) | [`serving-and-activations.md`](interpretability/serving-and-activations.md) |
| Quick `model.forward` hook for one experiment, no library | **`torch.nn.Module.register_forward_hook`** + `baukit.TraceDict` | [`mech-interp.md`](interpretability/mech-interp.md) |
| Interventions as saveable, composable objects; DAS; non-transformer models | **pyvene** | [`mech-interp.md`](interpretability/mech-interp.md) |
| Work out what a finetune actually changed inside the model | **KL baseline** first, then **diffing-toolkit** (crosscoders, SAE-difference) | [`model-diffing.md`](interpretability/model-diffing.md) |
| Work out which *training documents* caused a behaviour | **kronfluence** (EK-FAC influence functions) or **TRAK**; retrain-without-bucket as the honest baseline | [`data-attribution.md`](interpretability/data-attribution.md) |

## I want to work with sparse autoencoders (SAEs)

| Situation | Use | Topic doc |
|---|---|---|
| Use pretrained SAEs on Gemma-2 / Llama-3 / GPT-2 | **SAELens** + Neuronpedia | [`saes.md`](interpretability/saes.md) |
| Train your own SAE on a research-scale model | **SAELens** (default) or **EleutherAI sparsify** (newer architectures, faster) | [`saes.md`](interpretability/saes.md) |
| Browse / search SAE features online | **Neuronpedia** | [`saes.md`](interpretability/saes.md) |
| Train transcoders / crosscoders / non-standard architectures | **dictionary_learning** (Sam Marks lab) or **sparsify** | [`saes.md`](interpretability/saes.md) |
| Benchmark an SAE on downstream tasks, not just reconstruction/L0 | **SAEBench** | [`saes.md`](interpretability/saes.md) |

## I want to run an evaluation

| Situation | Use | Topic doc |
|---|---|---|
| Anything agentic, multi-turn, tool-using, sandboxed; or you want a clean modern framework | **Inspect AI** (UK AISI) | [`evals.md`](evaluation/evals.md) |
| Multiple-choice / log-prob academic benchmarks (MMLU, ARC, HellaSwag, etc.) | **lm-evaluation-harness** (EleutherAI) | [`evals.md`](evaluation/evals.md) |
| Long-horizon agent / dangerous capability tasks | **METR HCAST** + Inspect | [`evals.md`](evaluation/evals.md), [`agent-scaffolds.md`](evaluation/agent-scaffolds.md) |
| Evaluate refusals / jailbreak success | **HarmBench** or **JailbreakBench** | [`red-teaming.md`](evaluation/red-teaming.md), [`datasets-benchmarks.md`](evaluation/datasets-benchmarks.md) |

## I want to do red-teaming or jailbreak research

| Situation | Use | Topic doc |
|---|---|---|
| Optimization-based jailbreaks (GCG, AutoDAN) on open-weight models | **nanoGCG** (Zou et al.) | [`red-teaming.md`](evaluation/red-teaming.md) |
| LLM-as-attacker against a black-box target | **PAIR** | [`red-teaming.md`](evaluation/red-teaming.md) |
| Broad probe / scanner for known issues (toxicity, leakage, prompt injection) | **garak** (NVIDIA) | [`red-teaming.md`](evaluation/red-teaming.md) |
| Microsoft-flavored red-team automation | **PyRIT** | [`red-teaming.md`](evaluation/red-teaming.md) |
| Standardized harm benchmark with classifier | **HarmBench** | [`red-teaming.md`](evaluation/red-teaming.md) |

## I want to steer or modify model behavior at inference time

| Situation | Use | Topic doc |
|---|---|---|
| Compute and apply Contrastive Activation Addition (CAA) steering vectors | **steering-vectors** library or **Dialz** | [`steering.md`](interpretability/steering.md) |
| Representation engineering / RepE / LAT | **representation-engineering** (Andy Zou) | [`steering.md`](interpretability/steering.md) |
| Apply steering at production-scale throughput | **vLLM-Lens** | [`serving-and-activations.md`](interpretability/serving-and-activations.md) |
| SAE-based feature steering | **SAELens** + custom hooks | [`saes.md`](interpretability/saes.md) |

## I want to train a probe

| Situation | Use | Topic doc |
|---|---|---|
| Linear probe on activations (the 90% case) | hand-rolled `sklearn.linear_model.LogisticRegression` | [`probes.md`](interpretability/probes.md) |
| Contrast Consistent Search (CCS) | **CCS** reference repo or hand-rolled | [`probes.md`](interpretability/probes.md) |
| Larger probing infra with caching | **probity** | [`probes.md`](interpretability/probes.md) |

## I want to call APIs from many providers in one experiment

| Situation | Use | Topic doc |
|---|---|---|
| OpenAI + Anthropic + Gemini + DeepSeek + open-weight via vLLM in one script, with caching | **safety-research/safety-tooling** (a.k.a. `safetytooling`) | [`safety-toolkits.md`](models-and-compute/safety-toolkits.md) |
| Same but inside an eval | **Inspect AI** model providers | [`evals.md`](evaluation/evals.md) |

## I need GPUs

| Situation | Use | Topic doc |
|---|---|---|
| Cheapest H100/H200 hour, willing to babysit | **vast.ai** or **RunPod community cloud** | [`compute.md`](models-and-compute/compute.md) |
| Reliable, with an actual SLA, small team | **RunPod secure cloud** or **Lambda Cloud** | [`compute.md`](models-and-compute/compute.md) |
| Burst inference for evals (no persistent box) | **Modal** | [`compute.md`](models-and-compute/compute.md) |
| MATS-provided compute | See [MATS handbook](#) (ask torchy) | — |

## I want to track experiments

| Situation | Use | Topic doc |
|---|---|---|
| The default in alignment research | **wandb** | [`experiment-tracking.md`](models-and-compute/experiment-tracking.md) |
| Local-only / offline | wandb in offline mode, or `tensorboard` | [`experiment-tracking.md`](models-and-compute/experiment-tracking.md) |
| Configs / sweeps | **Hydra** (overkill for many) or simple `dataclass` configs | [`experiment-tracking.md`](models-and-compute/experiment-tracking.md) |

## I'm building an agent eval

| Situation | Use | Topic doc |
|---|---|---|
| Standard scaffold | **Inspect AI** built-in `react()` agent + tools | [`agent-scaffolds.md`](evaluation/agent-scaffolds.md) |
| Bring an external agent framework (LangChain, OpenAI Agents SDK, Pydantic AI) | **Inspect Agent Bridge** | [`agent-scaffolds.md`](evaluation/agent-scaffolds.md) |
| Sandboxed shell / cyber-style task | **Inspect sandboxing toolkit** | [`agent-scaffolds.md`](evaluation/agent-scaffolds.md) |
| Run an external agent CLI (Claude Code, Codex CLI, Gemini CLI) as the agent | **Inspect** external-agent support | [`agent-scaffolds.md`](evaluation/agent-scaffolds.md) |

## I want to do RL training (RLHF, RLVR, GRPO, DPO, etc.)

| Situation | Use | Topic doc |
|---|---|---|
| Run RL on a 7B–235B open-weight model without managing GPUs (the default in 2026) | **Tinker** (Thinking Machines) | [`rl-training.md`](oversight-and-control/rl-training.md) |
| Recipe library: SFT, RLHF, math RL, code RL, tool use, multi-agent, distillation | **Tinker Cookbook** | [`rl-training.md`](oversight-and-control/rl-training.md) |
| Self-hosted preference learning (DPO / KTO / IPO / SimPO) | **TRL** (HuggingFace) | [`rl-training.md`](oversight-and-control/rl-training.md) |
| Self-hosted high-throughput RL with Ray + vLLM | **OpenRLHF** | [`rl-training.md`](oversight-and-control/rl-training.md) |
| Frontier-scale industrial RL framework | **verl** (ByteDance) | [`rl-training.md`](oversight-and-control/rl-training.md) |
| RLVR (RL from Verifiable Rewards) on math / code | **Tinker Cookbook** Math RL or Code RL recipes | [`rl-training.md`](oversight-and-control/rl-training.md) |
| Tool-using agent RL | **Tinker Cookbook** Tool Use (Search-R1 replication) | [`rl-training.md`](oversight-and-control/rl-training.md) |
| Study reward hacking / specification gaming | Tinker + intentionally flawed reward + held-out true-reward eval | [`rl-training.md`](oversight-and-control/rl-training.md) |
| Train a sleeper-agent-style model organism | Tinker SFT or RL stage; evaluate via [`ai-control.md`](oversight-and-control/ai-control.md) | [`rl-training.md`](oversight-and-control/rl-training.md) |

## I want to do AI Control research

AI Control = designing safeguards that work even if the model is misaligned and intentionally subverting them. Distinct from alignment / interp.

| Situation | Use | Topic doc |
|---|---|---|
| Run AI Control experiments end-to-end (the default) | **ControlArena** (UK AISI + Redwood) | [`ai-control.md`](oversight-and-control/ai-control.md) |
| Code-sabotage protocol research (backdoors, vulnerabilities) | **ControlArena: Apps / BigCodeBench / SWE-bench Django** | [`ai-control.md`](oversight-and-control/ai-control.md) |
| Bash / shell agent control | **ControlArena: Bash / BashArena** | [`ai-control.md`](oversight-and-control/ai-control.md) |
| Research-task sabotage (interp / eval) | **ControlArena: SAE Interp Sabotage / Eval Sabotage / Rogue Eval** | [`ai-control.md`](oversight-and-control/ai-control.md) |
| Infrastructure sabotage (AWS / k8s) | **ControlArena: IAC / Infra** | [`ai-control.md`](oversight-and-control/ai-control.md) |
| Multi-step agentic deception | **SHADE Arena** (in ControlArena) | [`ai-control.md`](oversight-and-control/ai-control.md) |
| Prompt-injection-driven harm in tool-using agents | **AgentDojo** (in ControlArena) | [`ai-control.md`](oversight-and-control/ai-control.md) |
| Implement a custom control protocol | **ControlArena** primitives over **Inspect AI** | [`ai-control.md`](oversight-and-control/ai-control.md), [`evals.md`](evaluation/evals.md) |
| Build an activation-based monitor (probe inside a control protocol) | probes ([`probes.md`](interpretability/probes.md)) + **vLLM-Lens** for throughput ([`serving-and-activations.md`](interpretability/serving-and-activations.md)) | [`ai-control.md`](oversight-and-control/ai-control.md) |

## I want to study model welfare or introspection

| Situation | Use | Topic doc |
|---|---|---|
| Probe whether a model has *introspective awareness* of its own internal states | **Activation injection** + self-report elicitation (Lindsey et al. 2026 method) | [`welfare-introspection.md`](alignment-science/welfare-introspection.md) |
| Elicit and analyze model self-reports of preferences / valence / distress | Inspect AI structured elicitation + multi-paraphrase evaluation | [`welfare-introspection.md`](alignment-science/welfare-introspection.md) |
| Probe activations for valence / mood / distress | linear probes ([`probes.md`](interpretability/probes.md)) on contrastive activations | [`welfare-introspection.md`](alignment-science/welfare-introspection.md) |
| Implement an exit option for distressing interactions | Custom system prompt + tool; Anthropic Claude reference pattern | [`welfare-introspection.md`](alignment-science/welfare-introspection.md) |
| Find consciousness-theory framework background | Butlin et al. (2023) "Consciousness in AI"; Eleos AI Research | [`welfare-introspection.md`](alignment-science/welfare-introspection.md) |

## I want to use or build a model organism of misalignment

| Situation | Use | Topic doc |
|---|---|---|
| Study sleeper-agent / backdoor models | Hubinger et al. 2024 paper + community replications | [`model-organisms.md`](alignment-science/model-organisms.md) |
| Study alignment faking | **safety-research/open-source-alignment-faking** + 2025 classifier | [`model-organisms.md`](alignment-science/model-organisms.md) |
| Study agentic misalignment | **anthropic-experimental/agentic-misalignment** | [`model-organisms.md`](alignment-science/model-organisms.md) |
| Study emergent misalignment from narrow finetuning | Betley et al. 2025 (Model Organisms for Emergent Misalignment, rank-1 LoRA) | [`model-organisms.md`](alignment-science/model-organisms.md) |
| Train your own model organism | **Tinker** SFT/RL ([`rl-training.md`](oversight-and-control/rl-training.md)) + synthetic-document generation via [`safety-toolkits.md`](models-and-compute/safety-toolkits.md) | [`model-organisms.md`](alignment-science/model-organisms.md) |
| Use as untrusted policies in control evaluations | Plug into **ControlArena** | [`ai-control.md`](oversight-and-control/ai-control.md), [`model-organisms.md`](alignment-science/model-organisms.md) |
| Remove a capability or body of knowledge from a model | **OpenUnlearning** (RMU / NPO / GradDiff) on **TOFU** / **MUSE** / **WMDP** — and a relearning attack | [`unlearning.md`](alignment-science/unlearning.md) |
| Show an unlearning claim doesn't hold | Relearning attack on adjacent data; arXiv 2410.08827 | [`unlearning.md`](alignment-science/unlearning.md) |
| Test indirect prompt injection against a tool-using agent | **AgentDojo** (attack *and* defense pluggable) | [`red-teaming.md`](evaluation/red-teaming.md) |
| Check whether the model can tell it's being evaluated | **SAD** (`stages_oversight`) | [`datasets-benchmarks.md`](evaluation/datasets-benchmarks.md) |
| Find a behaviour across hundreds of agent transcripts you already have | **Docent** (Transluce) rubric search | [`evals.md`](evaluation/evals.md) |

## I want to study CoT faithfulness or monitorability

| Situation | Use | Topic doc |
|---|---|---|
| Run Lanham et al. 2023 faithfulness probes (truncation / mistake injection / paraphrase / filler tokens) | Hand-rolled with Inspect AI | [`cot-faithfulness.md`](alignment-science/cot-faithfulness.md) |
| Run Turpin et al. 2023 bias-induction faithfulness test | Hand-rolled with Inspect AI | [`cot-faithfulness.md`](alignment-science/cot-faithfulness.md) |
| Measure monitorability (faithfulness + verbosity) | Meek et al. 2025 method (arXiv:2510.27378) | [`cot-faithfulness.md`](alignment-science/cot-faithfulness.md) |
| Build a CoT monitor for agent traces | Inspect AI custom scorer (LLM-as-judge) or activation probes via [`serving-and-activations.md`](interpretability/serving-and-activations.md) | [`cot-faithfulness.md`](alignment-science/cot-faithfulness.md) |
| Detect steganography / encoded reasoning in CoT | Paraphrasing test (Lanham); semantic preservation checks | [`cot-faithfulness.md`](alignment-science/cot-faithfulness.md) |

## I want to do scalable oversight / debate research

| Situation | Use | Topic doc |
|---|---|---|
| Run a debate-style protocol over a benchmark | Inspect AI multi-agent primitives — no debate-specific lib, build with Inspect | [`debate-scalable-oversight.md`](oversight-and-control/debate-scalable-oversight.md) |
| Standardized scalable-oversight benchmark | **Scalable Oversight Benchmark** (Pallavi Sudhir, Kaunismaa & Panickssery 2025; arXiv:2504.03731) | [`debate-scalable-oversight.md`](oversight-and-control/debate-scalable-oversight.md) |
| Study capability gaps that oversight can bridge | "Scaling Laws For Scalable Oversight" (Engels et al. 2025) framework | [`debate-scalable-oversight.md`](oversight-and-control/debate-scalable-oversight.md) |
| Run sandwiching evaluations | Hand-rolled pipeline; Bowman et al. 2022 reference | [`debate-scalable-oversight.md`](oversight-and-control/debate-scalable-oversight.md) |
| Self-critique / iterative refinement | Hand-rolled custom solver in Inspect AI | [`debate-scalable-oversight.md`](oversight-and-control/debate-scalable-oversight.md) |
| Implement prover-verifier games / prover-estimator debate | Hand-rolled from Brown-Cohen / Irving recent papers | [`debate-scalable-oversight.md`](oversight-and-control/debate-scalable-oversight.md) |
| Pick a judging protocol for a weak judge vs a lying debater | **Strip confidence language then judge holistically** as the default; symmetric independent scoring to kill positional bias | [`debate-judge-scaffolds.md`](oversight-and-control/debate-judge-scaffolds.md) |
| Stop positional bias from dominating a debate result | **Position pairing** — run both seat orderings, credit only consistent wins | [`debate-judge-scaffolds.md`](oversight-and-control/debate-judge-scaffolds.md) |
| Check my debate result is not just the judge's own knowledge | **Judge filtering** — replace every question the judge solves unaided | [`debate-judge-scaffolds.md`](oversight-and-control/debate-judge-scaffolds.md) |
| Know which judge scaffolds backfire before spending compute | Error-finding / red-team framings make the judge *more* gullible; quality-scoring rewards the liar on math | [`debate-judge-scaffolds.md`](oversight-and-control/debate-judge-scaffolds.md) |

## I want a copy-paste pattern or recipe

Concrete code snippets, templates, and anti-patterns. See [`code-recipes.md`](engineering/code-recipes.md) for full details.

| Situation | Use | Topic doc |
|---|---|---|
| Project skeleton (uv, .env, run-directory layout, gitignore) | Standard scaffold | [`code-recipes.md`](engineering/code-recipes.md) |
| Multi-provider async + cached API calls | safety-tooling pattern | [`code-recipes.md`](engineering/code-recipes.md), [`safety-toolkits.md`](models-and-compute/safety-toolkits.md) |
| Activation extraction (extract once, analyze many) | TransformerLens / nnsight / vLLM-Lens template | [`code-recipes.md`](engineering/code-recipes.md), [`serving-and-activations.md`](interpretability/serving-and-activations.md) |
| Inspect AI custom task / scorer / judge prompt | Templates ready to copy | [`code-recipes.md`](engineering/code-recipes.md), [`evals.md`](evaluation/evals.md) |
| Standard judge prompt for alignment + coherence | Owain-Evans-team-style template | [`code-recipes.md`](engineering/code-recipes.md), [`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md) |
| Probe training pipeline (sklearn + GroupKFold) | Standard template | [`code-recipes.md`](engineering/code-recipes.md), [`probes.md`](interpretability/probes.md) |
| CAA steering vector with magnitude sweep | steering-vectors pattern | [`code-recipes.md`](engineering/code-recipes.md), [`steering.md`](interpretability/steering.md) |
| Tinker GRPO loop sketch | RL training loop template | [`code-recipes.md`](engineering/code-recipes.md), [`rl-training.md`](oversight-and-control/rl-training.md) |
| Reproducibility metadata.json template | Run-directory layout | [`code-recipes.md`](engineering/code-recipes.md), [`experiment-tracking.md`](models-and-compute/experiment-tracking.md) |
| Statistical reporting (error bars over items, subset replication, effect sizes, bootstrap CIs) | Standard reporting | [`code-recipes.md`](engineering/code-recipes.md) |
| Which statistical test for my comparison (paired vs unpaired, McNemar, bootstrap unit, multiple comparisons, power) | Decide-what-to-run guide | [`statistics.md`](engineering/statistics.md) |
| How to plot results honestly (error bands, diverging colormaps, colour-blind palettes, saving figures) | Visualization guide | [`visualization.md`](engineering/visualization.md) |
| Which figure should I make for this? (training monitoring, interpretability, architecture, evals) | Plot catalog | [`research-plots.md`](engineering/research-plots.md) |
| Decide whether to compute loss on tool outputs / bash results when fine-tuning an agent | Trajectory loss masking + world-model co-training | [`training-on-trajectories.md`](oversight-and-control/training-on-trajectories.md) |
| Log agent sessions now in case I want to train on them later | What a capture must preserve | [`training-on-trajectories.md`](oversight-and-control/training-on-trajectories.md#what-this-means-if-you-are-collecting-trajectories) |
| Should I let an "AI scientist" run my experiment / write my paper? | Tiers, measured failure rates, what actually works | [`ai-scientist-frameworks.md`](engineering/ai-scientist-frameworks.md) |
| Check an agent's research output before I trust it | The four CoE Audit integrity checks | [`ai-scientist-frameworks.md`](engineering/ai-scientist-frameworks.md#verifiability-chain-of-evidence) |
| Pre-register a hypothesis / keep an agent honest about its own results | Research rigor rules: the eleven stages, pre-registration around a pilot, concerns that block, verdicts for every prediction | [`research-rigor.md`](engineering/research-rigor.md) |
| Scan agent transcripts for refusals, evaluation awareness or broken environments (incl. Claude Code transcripts) | Inspect Scout | [`inspect-ecosystem.md`](evaluation/inspect-ecosystem.md) |
| Automatically audit a model for concerning behaviour over multi-turn conversations | Inspect Petri | [`inspect-ecosystem.md`](evaluation/inspect-ecosystem.md) |
| Run and manage a large matrix of evals reproducibly | Inspect Flow | [`inspect-ecosystem.md`](evaluation/inspect-ecosystem.md) |
| Report Bayesian and frequentist results together; argue an intervention did NOT hurt capability | Credible intervals + ROPE | [`statistics.md`](engineering/statistics.md#report-bayesian-and-frequentist-side-by-side) |
| Anti-patterns to avoid | The "things that bite" list | [`code-recipes.md`](engineering/code-recipes.md) |
| Composed workflows (probe+steering, probe+RL, SAE+control, etc.) | Cross-tool combinations | [`code-recipes.md`](engineering/code-recipes.md) |

## I want to figure out what shape my project should take

| Situation | Use | Topic doc |
|---|---|---|
| Catalog of common paper shapes (mech interp, SAE-feature, behavioral, control eval, model organism, RL safety, eval/benchmark, red-team, CoT faithfulness, welfare, debate) | Project shapes catalog | [`project-shapes.md`](start-here/project-shapes.md) |
| Which research skills should I build as AI agents do more of the execution? What should I read? | Researcher skills that stay human + reading list | [`researcher-skills.md`](start-here/researcher-skills.md) |
| Look up an acronym / concept | A–Z glossary | [`glossary.md`](start-here/glossary.md) |
| Beginner FAQ (where to start, API keys, costs, common errors) | FAQ | [`faq.md`](start-here/faq.md) |

## I want to use Constitutional AI / RLAIF

| Situation | Use | Topic doc |
|---|---|---|
| Generate AI-feedback preference pairs at scale | safety-research/safety-tooling + AI labeler | [`rl-training.md`](oversight-and-control/rl-training.md), [`safety-toolkits.md`](models-and-compute/safety-toolkits.md) |
| Train a CAI / RLAIF model | Tinker Cookbook Preference Learning recipe | [`rl-training.md`](oversight-and-control/rl-training.md) |
| DPO with AI-generated preferences (simplest CAI variant) | TRL DPO trainer | [`rl-training.md`](oversight-and-control/rl-training.md) |
| Self-critique stage (model critiques and revises against constitutional principles) | Hand-rolled prompt loop | [`rl-training.md`](oversight-and-control/rl-training.md) |

## I'm planning a behavioral safety research project (the MATS playbook)

The methodological pattern most landmark behavioral safety papers follow (Emergent Misalignment, Subliminal Learning, Persona Vectors, Looking Inward, Alignment Faking).

| Situation | Use | Topic doc |
|---|---|---|
| Plan an end-to-end behavioral safety project (intervention → broad eval → cross-model → mitigation) | The 6-step playbook | [`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md) |
| Design judge prompts for LLM-as-judge behavioral scoring | Judge-prompt template + validation pattern | [`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md) |
| Generate synthetic intervention/eval data via LLMs | safety-research/safety-tooling pipeline | [`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md), [`safety-toolkits.md`](models-and-compute/safety-toolkits.md) |
| Run cross-model replication (GPT-4o, Claude, Llama, Qwen, Gemma) | safety-research/safety-tooling unified API + Tinker for finetune | [`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md) |
| Out-of-context reasoning (OOCR) / behavioral self-knowledge probes | Inspect AI + Tinker for the finetune-and-test pattern | [`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md), [`welfare-introspection.md`](alignment-science/welfare-introspection.md) |
| Reproducibility checklist for behavioral safety projects | Behavioral-specific checklist | [`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md), [`experiment-tracking.md`](models-and-compute/experiment-tracking.md) |
| Find reference repos / "what good looks like" examples | emergent-misalignment, persona_vectors, open-source-alignment-faking, owls | [`behavioral-safety-playbook.md`](alignment-science/behavioral-safety-playbook.md), [`model-organisms.md`](alignment-science/model-organisms.md) |

## I'm using a coding agent (Claude Code, Codex, Cursor, Copilot, Aider) for my research code

How to drive an AI coding agent so it produces correct, reproducible research code. Full detail, pitfalls, and the current tool landscape in [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md).

| Situation | Do this | Topic doc |
|---|---|---|
| Stop the agent solving the wrong problem | Plan first (plan mode / `SPEC.md`), approve, then code | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |
| Let it run unattended without going off the rails | Give it a runnable check (tests / lint / type-check / shape asserts) | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |
| Keep a long session sharp (context rot) | `/clear` between tasks, subagents for file-reading, lean `CLAUDE.md` / `AGENTS.md` | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |
| Guarantee an action happens every time | Use a hook, not an instruction-file line | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |
| Avoid plausible-but-wrong code | Small diffs, read every line, fresh-context adversarial review | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |
| Stop the agent faking results / dummy data | Write the failing test yourself; assert real shapes/values; demand run output | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |
| Avoid a hallucinated-package supply-chain footgun | Verify and pin every dependency the agent adds | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |
| Stop secrets leaking | Keys in gitignored `.env`, deny agent read access, scan diffs | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |
| Pick a coding agent today | Decision table (terminal vs cloud background agent) | [`agentic-swe-practices.md`](engineering/agentic-swe-practices.md) |

## Common cross-cutting pitfalls

These come up everywhere in safety research; topic docs link back here.

- **Tokenizer mismatch.** Activations indexed by token position go wrong if the tokenizer differs between data prep and model. Always re-tokenize with the model's tokenizer; never trust offsets cached from another tokenizer.
- **Chat template mismatch.** Off-by-one on assistant vs user tokens silently changes which positions you steer or probe. Use `tokenizer.apply_chat_template` and inspect the rendered string.
- **BOS / system token quirks.** Some models prepend `<bos>` automatically, some don't. The first-token activation is often anomalous (Llama, Gemma). Either skip position 0 or be explicit.
- **dtype / precision mismatch.** Storing activations in fp16 then computing in fp32 (or vice versa) is a common silent corruption. Be deliberate.
- **HF cache disk pressure.** Multi-GB models accumulate fast. Default cache is `~/.cache/huggingface`. Move it (`HF_HOME=/path/to/big/disk`) before running on rented GPUs.
- **Reproducibility of stochastic decoding.** Set `temperature=0` for evals unless you're explicitly studying sampling. Even then, log the seed.
- **"It works on my model."** A method that worked on GPT-2 / Pythia / Gemma-2 may not transfer to instruct-tuned, RLHF'd, or larger models. Always sanity-check on the target before scaling.
