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
| `alignment-science/behavioral-safety-playbook.md` | planning a behavioral safety study: the six-step method behind papers like Emergent Misalignment and Alignment Faking |
| `engineering/research-rigor.md` | pre-registering, accepting a result, raising a concern about your own work, resolving a prediction, or writing up |
| `start-here/researcher-skills.md` | the researcher asks which of their own skills to build while an agent does execution |
| `start-here/mentor-expectations.md` | the researcher asks what MATS mentors expect of them |
| `start-here/faq.md` | cross-cutting beginner questions: API keys, costs, where to start |
| `start-here/glossary.md` | you meet an unfamiliar acronym or term (CAA, GRPO, OOCR, RLAIF, …) |
| `index.md` | you want the full "I want to do X → use Y" decision tables |

## Models, compute and plumbing

| Page | Open it when |
|---|---|
| `models-and-compute/open-weights-models.md` | choosing which open-weights model to study, fine-tune or use as a baseline |
| `models-and-compute/compute.md` | getting or sizing GPUs |
| `models-and-compute/experiment-tracking.md` | organising runs, configs and outputs so results are reproducible |
| `models-and-compute/safety-toolkits.md` | you need multi-provider API calls with caching and rate limits, finetuning helpers, or labeling tooling |
| `interpretability/serving-and-activations.md` | inference or activation extraction at scale: 70B+ models, millions of prompts, multi-GPU |
| `engineering/agentic-swe-practices.md` | writing research code with a coding agent and you want it correct and reproducible |
| `engineering/code-recipes.md` | you want a copy-paste pattern: judge prompts, layout templates, common anti-patterns |

## Interpretability

| Page | Open it when |
|---|---|
| `interpretability/mech-interp.md` | hooking model internals (TransformerLens, nnsight, baukit), reading intermediate variables with workspace lenses, finding and evaluating circuits (EAP-IG, MIB), or using interpretability agents |
| `interpretability/saes.md` | training or using sparse autoencoders, transcoders or crosscoders, superposition theory, or weight-sparse models |
| `interpretability/probes.md` | asking "does the model represent X?" with a classifier on activations, including lie detection (and how far current detectors can be trusted), eval-awareness and role probes |
| `interpretability/steering.md` | changing behaviour by intervening on activations (CAA, ActAdd, ablation, SAE-feature edits) or with contrastive weight steering |
| `interpretability/model-diffing.md` | asking what changed between a base and a finetuned model |
| `interpretability/data-attribution.md` | asking which training examples caused a behaviour (influence functions, TDA, Bayesian influence functions) |
| `interpretability/slt-devinterp.md` | the local learning coefficient, susceptibilities, patterning, the `devinterp` library, or belief-state geometry / computational mechanics |

## Evaluation and red-teaming

| Page | Open it when |
|---|---|
| `evaluation/evals.md` | choosing or building an evaluation framework, eval awareness, or claiming a model can't do something (sandbagging and capability elicitation) |
| `evaluation/datasets-benchmarks.md` | picking a safety dataset or benchmark (refusal, harm, deception, sycophancy, dangerous capability) |
| `evaluation/agent-scaffolds.md` | running a model as an agent with tools and sandboxes, for capability or safety evals |
| `evaluation/inspect-ecosystem.md` | using Inspect tooling beyond the core: Scout for transcript analysis, Petri for automated auditing, Flow for eval sets |
| `evaluation/red-teaming.md` | adversarial robustness or jailbreak research: optimisation attacks, LLM attackers, scanners, harm benchmarks, and how to evaluate a defense against adaptive attacks |
| `evaluation/dangerous-capability-evals.md` | choosing or running a bio/chem, cyber or self-replication capability eval, or reading one against a frontier-safety-framework threshold |

## Alignment science

| Page | Open it when |
|---|---|
| `alignment-science/model-organisms.md` | building or evaluating a model organism (deception, sleeper agents, alignment faking, emergent misalignment), scheming propensity, shutdown resistance, or data poisoning |
| `alignment-science/cot-faithfulness.md` | asking whether a chain of thought reflects the real reasoning, whether CoT can be monitored or carries encoded reasoning (steganography), or which reasoning steps matter (resampling) |
| `alignment-science/unlearning.md` | removing knowledge or a capability, claiming that something was removed, or making open-weight safeguards tamper-resistant |
| `alignment-science/welfare-introspection.md` | studying model welfare, self-report or introspection |
| `alignment-science/alignment-pretraining.md` | shaping a model's values in pretraining or midtraining (documents rather than demonstrations), or judging whether such an effect survives finetuning and RL |

## Training, oversight and control

| Page | Open it when |
|---|---|
| `oversight-and-control/rl-training.md` | RL on language models: RLHF, RLVR, GRPO, DPO, reward hacking and its mitigations, reward models and PRMs, deliberative alignment and model specs, honesty training |
| `oversight-and-control/training-on-trajectories.md` | finetuning on agent traces and deciding which tokens get loss |
| `oversight-and-control/ai-control.md` | designing or evaluating safeguards that must hold even against a model trying to subvert them: monitors, attack selection, async and stateful monitoring |
| `oversight-and-control/debate-scalable-oversight.md` | supervising a model on tasks the supervisor cannot check directly (debate, consultancy, prover-verifier games, weak-to-strong generalization) |
| `oversight-and-control/debate-judge-scaffolds.md` | building the procedure a weak judge follows to decide a debate |
| `oversight-and-control/multi-agent-safety.md` | several interacting agents: cooperation benchmarks, collusion audits or probes, steganographic collusion, the multi-agent risk taxonomy, how much agreement among many agents is worth, algorithmic collusion, voting simulations |

## Analysis and write-up

| Page | Open it when |
|---|---|
| `engineering/statistics.md` | claiming a difference is real, choosing a test, putting an error bar on a number, or reporting a sweep's best configuration |
| `engineering/visualization.md` | writing plotting code, choosing a colormap, or saving a figure |
| `engineering/research-plots.md` | deciding which figures are worth making: fine-tune monitoring, lenses, patching heatmaps, Pareto fronts, calibration |
| `engineering/ai-scientist-frameworks.md` | evaluating an automated-research system, or the output one hands you |

## Theory, formal work and governance

| Page | Open it when |
|---|---|
| `alignment-science/agent-foundations-and-formal.md` | corrigibility theory, agent foundations, guaranteed-safe AI and formal verification, or funding for corrigibility work |
| `engineering/theory-research.md` | working a theory or proof problem: stuck on an obstacle, importing a technique from another field, testing a candidate definition against canonical decision-theory cases, deciding whether to try refuting instead, or whether a quick simulation would help |
| `alignment-science/technical-governance.md` | technical AI governance: verifying inference or compute use, detecting model-weight exfiltration |
| `engineering/lean-formalization.md` | turning a mathematical or theoretical claim into a checked Lean artifact, choosing agent tooling for Lean, or deciding how much a proof check establishes |
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
| `mats-research-rigor` | pre-register, accept a result, raise a concern, resolve a prediction, write up, or release code |
| `mats-statistics` | claim a difference is real, choose a test, or put an error bar on a number |
| `mats-visualization` | write plotting code, choose a colormap, or save a figure |
| `mats-intervention-evidence` | claim you removed or unlearned something, that a finetune changed something, or that particular data caused a behaviour |
| `mats-lean-formalization`, `mats-lean-debug`, `mats-lean-library-search`, `mats-lean-review`, `mats-lean-cleanup` | formalise, debug, search for, review, or tidy Lean proofs |

---

Last verified: 2026-10-12.
