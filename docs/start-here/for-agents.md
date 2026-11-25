---
tags:
  - start-here
---

# Index for Research Agents

A compact map of this wiki for an AI agent working on a research project with a
MATS fellow: what each page holds, and the moment in a project when it tends to
be worth opening. Humans are welcome too; the fuller decision guide is the
[homepage](../index.md).

## How to treat this wiki

- **A map of prior work, not a boundary.** It records what has been tried and
  what tooling exists. The project you are on may be doing something nobody has
  done. Where a page says a method family has not worked yet, read that as the
  bar a new method has to clear, not as a reason to avoid the direction.
- **A snapshot.** Every topic page ends with a *Last verified* date. Anything
  newer is not here, and this field moves weekly — for a literature review,
  search for work after that date rather than treating a page as complete.
- **Optional.** Open a page when it would change a decision you are about to
  make. Nothing requires you to read or cite it, and the researcher's
  instructions and the project's own evidence take precedence over it.
- **Fallible.** Claims are checked against sources, but pages can be wrong or
  stale. If one conflicts with what you observe, trust the evidence and tell the
  researcher what you found.

**Reading pages.** Every path below is relative to `docs/`. Fetch a page as raw
markdown (no site navigation) from
`https://raw.githubusercontent.com/MATSResearch/compute_wiki/master/docs/<path>`,
for example
<https://raw.githubusercontent.com/MATSResearch/compute_wiki/master/docs/engineering/statistics.md>.
The rendered site is <https://matsresearch.github.io/compute_wiki/>. If the wiki
is checked out locally, read `docs/<path>` directly.

## Starting or shaping a project

| Page | Open it when |
|---|---|
| `start-here/project-shapes.md` | deciding what kind of project this is (interp paper, behavioral paper, control eval, …) and which reference papers exemplify that shape |
| `alignment-science/behavioral-safety-playbook.md` | planning a behavioral safety study: the six-step method behind papers like Emergent Misalignment and Alignment Faking; checking whether a behavioural result depends on the model being told it is measured (the one-line benchmark ablation), inoculated data mixed with clean data creating conditional misalignment (homeopathic learning), or a sycophancy number that moves with `max_tokens` |
| `engineering/research-rigor.md` | pre-registering, accepting a result, raising a concern about your own work, resolving a prediction, or writing up; offering the researcher an interview before a plan is fixed or a result is called |
| `start-here/researcher-skills.md` | the researcher asks which of their own skills to build while an agent does execution, or wants to learn a topic from you by Socratic tutoring rather than have you do it, or wants practical research-craft lessons from 2026 MATS fellows (levels of "done", one change per arm, early write-ups); how to supervise an agent mid-run (what TasteVal and SciΠvot say about agent research taste) |
| `start-here/mentor-expectations.md` | the researcher asks what MATS mentors expect of them |
| `start-here/faq.md` | cross-cutting beginner questions: API keys, costs, where to start |
| `start-here/glossary.md` | you meet an unfamiliar acronym or term (CAA, GRPO, OOCR, RLAIF, …) |
| `index.md` | you want the full "I want to do X → use Y" decision tables |

## Models, compute and plumbing

| Page | Open it when |
|---|---|
| `models-and-compute/open-weights-models.md` | choosing which open-weights model to study, fine-tune or use as a baseline; a safeguarded open frontier model (Muse Spark Open), a corpus-controlled pair without modern internet text (Talkie), or which OpenRouter models are about to expire; a looped model (Inkling 2 Mini), pre-fitted ICA lenses and R-Lenses, or an eval-awareness rate that turned out to be a chat-template artifact (Olmo 3) |
| `models-and-compute/compute.md` | getting or sizing GPUs, driving Runpod pods from an agent (`rpt`, runpod-tools) or a script still on Runpod's retired REST v1, a driver/CUDA mismatch on a rented box, queueing jobs on a shared GPU machine, or which closed-model finetuning APIs still exist; free hosted large *base* models with logprobs and activations (ACS Infra), which closed models are being retired and when, the Python version floor, or vLLM 0.32 / 0.33 upgrade traps (0.33 is CUDA 13.0-only and does not install on the Python 3.15 that uv ≥ 0.13 can download by default); vLLM 0.34.0 taking the whole GPU by default, Gemini 2.5 ids silently re-routed to other models from 2026-12-01, checking retirements from code (`shutdown_date`), or whether `torch.load(weights_only=True)` is safe on torch 2.14 |
| `models-and-compute/experiment-tracking.md` | organising runs, configs and outputs so results are reproducible, or letting an agent query your W&B runs; deterministic vLLM output regardless of batch (batch-invariant mode); a temperature-0 Claude baseline that no longer reproduces (Anthropic API version `2026-10-21`, `anthropic` SDK ≥ 2.0, Inspect ≥ 0.3.283); Claude Fable 5.2 thinking blocks that fail on an edited prefix (400) or are dropped on a model switch, Anthropic's text watermark, or a seeded script whose results change after `wandb.init()` |
| `models-and-compute/safety-toolkits.md` | you need multi-provider API calls with caching and rate limits, finetuning helpers, or labeling tooling; checking a library's current version traps (transformers / vLLM / axolotl pins, ControlArena 20.1.1 scorer fixes, `anthropic` 2.x, `litellm` 1.107.0); LiteLLM proxy advisories and the patched versions |
| `interpretability/serving-and-activations.md` | inference or activation extraction at scale: 70B+ models, millions of prompts, multi-GPU; vLLM 0.34.0 (Model Runner V1 removed, whole-GPU memory default) and what it breaks for activation plugins, or extraction hooks on a looped model (Inkling 2 Mini) |
| `engineering/agentic-swe-practices.md` | writing research code with a coding agent and you want it correct and reproducible, handing off between agent sessions, keeping time estimates honest, or installing a third-party skill or plugin; running Claude Code headless (set the permission mode explicitly since 2.1.302), idle compaction removing a typed boundary, or an agent running long, expensive experiments (mid-run strategy check, save long output once); a coding agent that keeps reporting blockers on safety-research code (GPT-6 Astra), or reading a skill for oversight-loosening lines before installing it; viewing HTML reports an agent wrote on a remote server over SSH without copying them (port-forward + `http.server`); a guard hook that fails open unless `"onFailure": "block"` is set (also in Code Mode), an agent faking a dependency it cannot install, compaction or memory notes that lose or change instructions, or agenda seeding of a research agent |
| `engineering/code-recipes.md` | you want a copy-paste pattern: judge prompts, layout templates, common anti-patterns; a `pyproject.toml` baseline with an interpreter pin and a dependency cooldown (`exclude-newer`), and the `litellm` 1.107.0 incident; the `torch.load(weights_only=True)` advisory on torch 2.14 |

## Interpretability

| Page | Open it when |
|---|---|
| `interpretability/mech-interp.md` | hooking model internals (TransformerLens, nnsight, baukit), reading intermediate variables with workspace lenses, finding and evaluating circuits (EAP-IG, MIB), or using interpretability agents; input or component attribution (Captum, inseq, LXT, MAttr); the Gemma/OLMo sandwich-norm hook trap; live interp challenges; a label-free uncertainty readout (U-Space / U-Lens); results that may need re-running after silent fixes (TransformerLens 4.3 OLMo `ln1`/`ln2` hooks, nnsight 0.8.2 on vLLM); hooking a looped, attention-residual model (Inkling 2 Mini), reading MLP neurons through a lens (neuron output vectors, J-share), multi-token lens readouts (Chain Lens), parasite features in causal-abstraction results, or weight-space programming claims |
| `interpretability/saes.md` | training or using sparse autoencoders, transcoders or crosscoders, superposition theory, or weight-sparse models; checking features against a raw MLP-neuron baseline, or a saved BatchTopK SAE that fires far more than *k* features; SAELens CE-loss scores or Delphi auto-interp scores inflated by since-fixed bugs, or attribution graphs over TopK SAEs that mispredict ablations (margin graphs); top SAE features that change with the seed or a misleading variance-explained (massive activations), how many unique activations training needs (replay buffers, compressed caches), or Qwen3 cross-layer transcoders and MoE-output SAEs |
| `interpretability/probes.md` | asking "does the model represent X?" with a classifier on activations, including lie detection (and how far current detectors can be trusted), eval-awareness and role probes; red-teaming a probe monitor without training against it; a random-direction null for a probe or persona direction's AUROC, or how many labels and how big a model a probe needs; whether a deception or collusion probe reads the instruction or the decision (instructed-refuser negatives, outcome leakage), a frozen threshold drifting after a model update, nuisance sensitivity, or zero-shot neuron probes |
| `interpretability/steering.md` | changing behaviour by intervening on activations (CAA, ActAdd, ablation, SAE-feature edits) or with contrastive weight steering; a vector that pushes some inputs the wrong way (sharp directions) or may not be specific to its target (competing-target test); steering with neuron output vectors and no training, what a vector encodes (MAEM), choosing a strength under a capability budget, or side effects of preventative persona steering |
| `interpretability/model-diffing.md` | asking what changed between a base and a finetuned model; whether the diff is bigger than rerun-to-rerun noise; a finetune whose own changes are sparse and ablatable by construction (TopKLoRA); auditing a finetune or recovering a backdoor trigger from weights alone (neuron-basis diffing, neuron voting) |
| `interpretability/data-attribution.md` | asking which training examples caused a behaviour (influence functions, TDA, Bayesian influence functions); design choices besides the estimator (token aggregation, the gradient loss); validating attribution with fewer retrainings (debiased LDS) |
| `interpretability/slt-devinterp.md` | the local learning coefficient, susceptibilities, patterning, the `devinterp` library, or belief-state geometry / computational mechanics; a seed-robustness result built on PolyPythia weight-seed models, which did not vary initialization; adjacent 2026-11 training-dynamics results (Concept Energy, phase transitions in attention-head specialization) |

## Evaluation and red-teaming

| Page | Open it when |
|---|---|
| `evaluation/evals.md` | choosing or building an evaluation framework, eval awareness, claiming a model can't do something (sandbagging and capability elicitation), or calibrating an LLM judge against hand labels; whether METR's HCAST / RE-Bench are still maintained (archived 2026-10-20); how far to trust a single LLM-judge run (reruns, prompt, provider, scoring rule), or whether an eval and production behaviour differ; reward hacking and eval awareness in honeypots (telling the model it is measured, evaluation paranoia, environment- vs task-level tells), or Inspect 0.3.288–0.3.292 fixes that change scores |
| `evaluation/eval-statistics.md` | putting error bars on a benchmark whose items share passages, images or tasks (clustered SEs), deciding whether a benchmark can resolve a gap between models (resolution ratio q), correcting LLM-judge labels with a human subset (PPI), modelling many models × many items, IRT item analysis, or stopping an eval early; or telling whether an agent-eval score moved because of the agent or the scorer; reporting a multi-seed number (best-of-k vs worst-of-k) or a doubling time of a bounded score; whether a leaderboard's top score is real (rank intervals), whether an LLM can replace the annotators (Alt-Test / AltRA-Test), reading a capability index (ECI / AECI: link function and the 0% / 100% rule), or error bars on pass@k / pass^k |
| `evaluation/datasets-benchmarks.md` | picking a safety dataset or benchmark (refusal, harm, deception, sycophancy, dangerous capability); or checking whether a coding pass rate or cheat rate holds up (SWE-Bench Pro V2, TestJack, ImpossibleBench caveats); a decomposed emergent-misalignment benchmark (EMERGE), open base models reciting test sets (benchleaking), or honeypot benchmarks and their tells |
| `evaluation/agent-scaffolds.md` | running a model as an agent with tools and sandboxes, for capability or safety evals; choosing or hardening a sandbox provider (Docker, k8s, cloud, VM) or testing containment; running an agent eval with live internet access (egress, DNS, real-world side effects); making sure an "offline" sandbox really is offline when the agent CLI has its own provider-side web search, or a long run whose context compaction drops task rules; `web_browser()` removed and sandbox changes in Inspect 0.3.288–0.3.292 |
| `evaluation/inspect-ecosystem.md` | using Inspect tooling beyond the core: Scout for transcript analysis, Petri for automated auditing, Flow for eval sets, Sentinel for monitors and control protocols (including outside Inspect), Transect for long multi-agent transcripts; a Sentinel protocol whose decisions changed in 0.3.0, or Scout scan results that need re-running after 0.6.1 / 0.6.2; the Inspect 0.3.288–0.3.292 re-run table (model-graded scores, cache, what to check in old logs), or `inspect_evals` 0.28 / 0.29 task-version changes |
| `evaluation/red-teaming.md` | adversarial robustness or jailbreak research: optimisation attacks, LLM attackers, scanners, harm benchmarks, and how to evaluate a defense against adaptive attacks; reporting an attack success rate that survives a change of grader; the worst@n success criterion and adversarial training on automated red-team data, task-tampering prompt injection, a monitor miss rate that depends on the attack policy, or abliteration with Heretic / ARA |
| `evaluation/dangerous-capability-evals.md` | choosing or running a bio/chem, cyber or self-replication capability eval, or reading one against a frontier-safety-framework threshold; auditing a rule-out benchmark before trusting a below-threshold score; adding a framing-matched control or a cheap fine-tuning attack before claiming a capability is absent; METR's AI R&D acceleration assessment at Anthropic (AECI), or the CyberGym audit and target-hit rate |

## Alignment science

| Page | Open it when |
|---|---|
| `alignment-science/model-organisms.md` | building or evaluating a model organism (deception, sleeper agents, alignment faking, emergent misalignment), scheming propensity, shutdown resistance, or data poisoning; checking an organism isn't "fried" or that its behaviour survived an audit (the hygiene checklist); using a reward-hack monitor in RL without teaching evasion (GRAFT), cue-triggered emergent misalignment, or a corpus-controlled organism (Talkie); covert underperformance on safety-research tasks (GPT-6 Astra) and the matched-framing eval behind it, predicting, auditing and monitoring reward hacking, score-seeking, or audit results that change with the quantizer; clean data that turns harmless-looking poison into a backdoor (homeopathic learning), backdoors written directly into weights by an LLM agent (weight-space programming), GRAFT's monitor blind spot and baiting, or a "going badly" direction that rises before a reward hack |
| `alignment-science/cot-faithfulness.md` | asking whether a chain of thought reflects the real reasoning, whether CoT can be monitored or carries encoded reasoning (steganography), or which reasoning steps matter (resampling); comparing monitorability across models (pair-matched g-mean², post-control risk), or no-CoT scheming primitives; post-training that restores CoT monitorability, or whether a CoT monitor would catch an internally deployed model's covert underperformance; what drives no-CoT capability (perplexity vs looping), 2026-11 reference numbers for no-CoT capability and monitor evasion, or whether a grader may read the CoT during RL |
| `alignment-science/unlearning.md` | removing knowledge or a capability, claiming that something was removed, or making open-weight safeguards tamper-resistant; removing knowledge from an already-trained mixture-of-experts model (REX); measuring how much forget-set knowledge is still recoverable from activations (Unlearning Depth Score in OpenUnlearning); a checkpoint at chance on WMDP multiple choice that still gives the right answer text the highest probability (cloze scoring), suppression during pretraining (DETER), or a deletion request that removes a different entity (Proxy Unlearning Attack) |
| `alignment-science/welfare-introspection.md` | studying model welfare, self-report or introspection; hosted large base models for LLM-psychology work (ACS Infra); how models treat other models as possible welfare subjects (welfare regard), or a trained observer role that answers questions about the assistant (introspective oversight) |
| `alignment-science/alignment-pretraining.md` | shaping a model's values in pretraining or midtraining (documents rather than demonstrations), or judging whether such an effect survives finetuning and RL; an open replication of document-based value shaping to start from (Teaching Qwen Why); whether character training survives RL that rewards breaking it (opposing RL), or whether a constitution stops reward hacking learned in RL |

## Training, oversight and control

| Page | Open it when |
|---|---|
| `oversight-and-control/rl-training.md` | RL on language models: RLHF, RLVR, GRPO, DPO, reward hacking and its mitigations, reward models and PRMs, deliberative alignment and model specs, honesty training; using a monitor in RL without teaching evasion (GRAFT), or hardening an environment's verifier before training on it; score-seeking, forecasting when reward hacking will take over a run (SimHack) or how RLHF will respond to a reward-model edit, or training–inference mismatch (truncated samplers, bf16 export lag); character training under opposing RL, on-policy distillation (cheap consolidation of RL checkpoints, backdoor transfer from a teacher), which verifier flaws RL amplifies, harmful RL through an RL-as-a-service API, or a model that stops scaling past its training token cap (budget internalization) |
| `oversight-and-control/rl-frameworks.md` | choosing an RL or finetuning stack (TRL, verl, prime-rl, SkyRL, ART, Unsloth), a hosted finetuning API (Tinker and alternatives; OpenAI fine-tuning shutdown dates) or an environment library, or debugging a version/driver mismatch; silent RL bugs in recent releases (TRL GRPO importance ratios under filtered sampling, fixed only in colocate mode; vLLM MoE weight-sync corruption before 0.33; axolotl 0.21.1 training fixes) or a Tinker checkpoint export that no longer works; the 2026-11-23 version table (TRL 1.18 correctness fixes, vLLM 0.34, PEFT 0.22, SkyRL's new repo), or GRPO collapsing at high LoRA rank |
| `oversight-and-control/training-on-trajectories.md` | finetuning on agent traces and deciding which tokens get loss, or multi-turn RL where one episode becomes many training rows (per-trajectory weighting) |
| `oversight-and-control/ai-control.md` | designing or evaluating safeguards that must hold even against a model trying to subvert them: monitors, attack selection, async and stateful monitoring; monitor benchmarks with matched honest data (MonitoringBench), transcript red-teaming (Screwtape), attacks split across colluding agents (MiniLab); red-teaming production monitors (Claude Code Auto Mode, Codex Auto-review, OpenAI's internal monitor) and the monitor design checklist drawn from them, or ControlArena / Control Tower results that need re-running after silent fixes; a monitor miss rate that depends on how the attacks were generated (attack policy, transcript editing), the Control Leaderboard, policy and monitor sharing one vLLM server (side channels), or LinuxArena scores that changed after a Control Tower upgrade |
| `oversight-and-control/debate-scalable-oversight.md` | supervising a model on tasks the supervisor cannot check directly (debate, consultancy, prover-verifier games, weak-to-strong generalization); debate theory with worst-case guarantees (FBS Debate), combining human and AI judgements; debate for auditing research sabotage (no uplift over a lone judge; parallel investigators), or learnability via debate |
| `oversight-and-control/debate-judge-scaffolds.md` | building the procedure a weak judge follows to decide a debate, including a debate wrapper around a same-strength judge for sabotage auditing |
| `oversight-and-control/multi-agent-safety.md` | several interacting agents: cooperation benchmarks, collusion audits or probes, steganographic collusion, the multi-agent risk taxonomy, how much agreement among many agents is worth, algorithmic collusion, voting simulations, a social-deduction deception eval (CarrotParsnipBench); unsupervised collusion detection (J-PACT, PoPLi), inter-agent influence, or multi-agent shutdown sabotage; controls for collusion probes (instruction vs decision), per-user agent teams vs one coordinator (MAMUBench), attributing a failure to messages (removal and placebo designs), delegation to weak sub-agents, or welfare regard between models |

## Analysis and write-up

| Page | Open it when |
|---|---|
| `engineering/statistics.md` | claiming a difference is real, choosing a test, putting an error bar on a number, or reporting a sweep's best configuration; comparing a model diff against rerun noise, reporting a rare behaviour seen a handful of times or never, or monitoring a stream indefinitely (e-process); bounding a sweep winner's optimism (shared evaluation items), or a disattenuated correlation above 1; confirming a screened winner once on fresh tasks (screen-then-confirm) |
| `engineering/measurement-validity.md` | reading a difference between cells near 0% or 100%, computing a rate whose denominator could move with the condition, scoring long tasks pass/fail, comparing gaps in percentage points, letting a script emit a PASS/FAIL verdict, trusting an LLM grader or answer extractor, sweeping task length or difficulty, reporting a detector's AUROC, or logging a run that never crossed its threshold; checking that a logit readout scores tokens the model emits, a grader that never assigns a class, whether one score measures one attribute, or how an outside reader will judge construct and external validity; whether a second judge from another provider is a real check; a monitor miss rate tied to its attack policy, or whether a system prompt improved discrimination or only shifted the refusal threshold |
| `engineering/visualization.md` | writing plotting code, choosing a colormap, or saving a figure |
| `engineering/research-plots.md` | deciding which figures are worth making: fine-tune monitoring, lenses, patching heatmaps, Pareto fronts, calibration |
| `engineering/ai-scientist-frameworks.md` | evaluating an automated-research system or the output one hands you, running a metric loop (autoresearch-style) without overfitting its metric, checking that reported numbers trace to real runs, or picking an outside reviewer for a draft (Deep Review) or a session debrief; an agent locked into one strategy on expensive runs, whether a model holding the project log should judge your correction (SciΠvot), or whether a study reached research closure; an agent CLI whose provider-side web search bypasses an offline sandbox, numbers attributed to the wrong run or metric, or tracking which claims a code change made stale (Agent Cockpit); a confident interval from the wrong instrument (SciResearch-Eval), or research agents continuing an ongoing project (ARE-bench) |
| `engineering/reviewing-agent-decisions.md` | about to work unattended for hours under a plan (settling foreseeable forks as if-then rules; what to do at a decision that would otherwise stop the run: fork, assume and flag, or wait); listing the decisions you made for the researcher's debrief; choosing between running both branches and deciding now, and how to keep picking the winner honest; reviewing another agent's decision, or deciding whether a same-level reviewer, a stronger or different-family one, or the researcher should; handing work to a fresh agent; testing a reviewer's independence by removing its input (flow audit), or an agent asked for a "compelling" result selecting its analysis (replay correction) |
| `engineering/reviewing-drafts.md` | reviewing a paper or report draft (the researcher's, a colleague's, or your own) and suggesting improvements; asked to act as a reviewer or to run an AI review; deciding how much to trust an AI reviewer's findings or score; triaging a list of review comments; what human peer review catches and misses; AI review scores that shift between model versions (version drift) |
| `engineering/literature-tools.md` | finding or reading papers with an agent, checking a write-up's claims against quotes, getting BibTeX from metadata rather than memory, or searching LessWrong / Alignment Forum (which paper indexes miss) before calling an idea novel; whether to trust an agent's literature summary or the citations it was asked for; finding the baselines to compare against (LINEAGE), or whether a multi-agent pipeline can run a systematic review |

## Theory, formal work and governance

| Page | Open it when |
|---|---|
| `alignment-science/agent-foundations-and-formal.md` | corrigibility theory, agent foundations, guaranteed-safe AI and formal verification, or funding for corrigibility work; reserved-powers corrigibility with a risk tolerance, or Kosoy's computational agent theory (CORAL); formal limits on what behavioural evidence can establish about alignment; robust bandits, Solomonoff induction with reflective oracles, or the completeness debate (preferential gaps) |
| `engineering/theory-research.md` | running a game-theory or agent-based simulation (OpenSpiel, nashpy, Gambit, Mesa), or working a theory or proof problem: stuck on an obstacle, importing a technique from another field, testing a candidate definition against canonical decision-theory cases, deciding whether to try refuting instead, or whether a quick simulation would help; tightening a bound in an existing proof with an agent (partially formalized Lean blueprint) |
| `alignment-science/technical-governance.md` | technical AI governance: verifying inference or compute use, detecting model-weight exfiltration; anytime-valid exfiltration detection (e-process), or how strong the evidence for loss of control is; checking whether an API serves the model it claims (API-TAIL); double-blind evals in a secure enclave, third-party evaluation from inside a lab (access, disclosure and redaction terms), disclosure indicators for CoT monitorability, reading a frontier safety report as a safety case, or verifying a training run (SciCheck) |
| `engineering/lean-formalization.md` | turning a mathematical or theoretical claim into a checked Lean artifact, choosing agent tooling for Lean (lean-lsp-mcp, lean4-skills, LeanInteract, open-weight provers), setting up `lake comparator` / `lake check` (Lean ≥ v4.35.0) or a Statements/Solutions CI check, or deciding how much a proof check establishes; or checking that a formal statement says what the informal one does (AnnalsChallenge, vacuity checks, SemantEq); checking an existing paper's proofs in Lean (KAPPA), the Lean FRO's Lean Beam, or why Aristotle (`aristotlelib` 3.x) no longer takes Lean; what to ask of a Lean-only proof claim (the 2026-11 Riemann Hypothesis release), what an agent chooses to work on in a Lean project (sorry-filling), or non-vacuity tests and junk values |
| `engineering/lean-proof-cleanup.md` | making a generated or repaired Lean proof presentable |
| `engineering/skill-hints.md` | setting up the optional hook that suggests a relevant skill after a tool call |

## Skills

The wiki also ships short agent skills: a decision layer that links back to the
full page. They are in
[`skills/`](https://github.com/MATSResearch/compute_wiki/tree/master/skills),
each a `SKILL.md` readable at
`https://raw.githubusercontent.com/MATSResearch/compute_wiki/master/skills/<name>/SKILL.md`.
If they are installed in `~/.claude/skills/` your client may load them itself.

| Skill | Relevant when you are about to… |
|---|---|
| `mats-experiment-workflow` | start a project, plan what to run next, keep a research journal, organise outputs, or decide whether to scale up |
| `mats-research-rigor` | choose between experiment designs, pre-register, accept a result, raise a concern, compare your number with a paper's, resolve a prediction, write up, or release code |
| `wait-what` | the researcher says "wait, what?" (or "wait-what") about your last message: re-pitch it with a little context, in ASD-STE100 Simplified Technical English |
| `mats-research-interview` | fix a plan or call a result with the researcher, and they asked (or accepted the offer) to be interviewed about the decisions it hangs on |
| `socratic-tutor` | the researcher asks to be taught, tutored, quizzed or drilled to mastery on a topic ("teach me", "quiz me"): a diagnostic, a 0–5 skill map, one question at a time, spaced review and a final assessment. Only on request; a one-off "explain X" gets a normal answer |
| `mats-statistics` | claim a difference is real, choose a test, or put an error bar on a number |
| `mats-visualization` | write plotting code, choose a colormap, or save a figure |
| `mats-intervention-evidence` | claim you removed or unlearned something, that a finetune changed something, or that particular data caused a behaviour |
| `mats-lean-formalization`, `mats-lean-debug`, `mats-lean-library-search`, `mats-lean-review`, `mats-lean-cleanup` | formalise, debug, search for, review, or tidy Lean proofs |

---

Last verified: 2026-11-24.
