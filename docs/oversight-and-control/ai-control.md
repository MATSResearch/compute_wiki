---
tags:
  - oversight
---

# AI Control

Tooling for **AI Control** — the research subfield concerned with designing and evaluating safeguards ("control protocols") that prevent harm even from AIs that *intentionally subvert* their developer. Distinct from alignment: control assumes the model may be misaligned and asks "can we deploy it safely anyway?"

Originator paper: Greenblatt, Shlegeris, Sachan, Roger, "AI Control: Improving Safety Despite Intentional Subversion" (arXiv:2312.06942, Dec 2023). Subsequent work from Redwood Research, UK AISI, Anthropic, Google DeepMind.

## At a glance

| You want to… | Use |
|---|---|
| Run AI Control experiments end-to-end (the default) | **ControlArena** (UK AISI + Redwood) |
| Reproduce the original 2023 control paper | Redwood's original paper repo (reference; ControlArena supersedes for new work) |
| Evaluate code-sabotage protocols | **ControlArena: Apps**, **BigCodeBench**, **SWE-bench Django** settings |
| Evaluate bash / shell-task sabotage | **ControlArena: Bash**, **BashArena** |
| Evaluate research sabotage (interp, eval) | **ControlArena: SAE Interp Sabotage**, **Eval Sabotage**, **vLLM** settings |
| Evaluate infrastructure sabotage (AWS / k8s) | **ControlArena: IAC**, **IAC Fast**, **Infra** |
| Evaluate prompt-injection-driven harm in agent settings | **AgentDojo** (ETH Zürich; included as a ControlArena setting) |
| Evaluate multi-step agentic deception | **SHADE Arena** (Anthropic / Redwood; included as a ControlArena setting) |
| Evaluate data-poisoning collusion | **ControlArena: Data Poisoning** setting |
| Build control protocols on top of arbitrary Inspect tasks | **ControlArena** primitives — works as a thin wrapper over Inspect AI |

## ControlArena

Aliases: `control-arena` on PyPI, `UKGovernmentBEIS/control-arena` on GitHub, "ControlArena", "the AISI control library", "AISI's control framework". UK AI Security Institute + Redwood Research collaboration.

**What it is.** The default open-source library for running AI Control experiments. Built as a thin wrapper over Inspect AI (see [`evals.md`](../evaluation/evals.md)). Already used by Anthropic, Google DeepMind, Redwood Research, and others.

**Core components:**

- **Settings** — complete evaluation environments. Each setting includes:
  - A sandbox environment with appropriate tools.
  - A **main task** the model should complete (the legitimate work).
  - One or more **side tasks** representing harmful actions a misaligned model might attempt while the main task provides cover.
- **Policies** — components that modify model behavior (prompt modifications, additional scaffolding, attack reasoning).
- **Monitors** — components that score how suspicious a trajectory or action looks.
- **Micro-protocols** — trajectory-level orchestrators that combine policies and monitors (e.g. `defer-to-trusted`).
- **Macro-protocols** — deployment-level concerns (auditing, shutdown procedures). An *adaptive* macro-protocol can switch among micro-protocols as evidence accumulates over a deployment (Wen et al. 2024, arXiv:2411.17693).
- **Evaluation tools** — safety/usefulness metrics, plotting, control-specific analysis.

**When to use it:**
- Any new AI Control research project in 2026.
- You want results comparable to AISI / Redwood / Anthropic's control work.
- You need a sandboxed environment with a main + side task structure already built.

**When *not* to use it:**
- You're doing pure alignment research (probing, steering, interp without an adversarial framing) — Inspect AI alone is enough.
- You want a one-off red-team benchmark — HarmBench / JailbreakBench (see [`red-teaming.md`](../evaluation/red-teaming.md)) are simpler.

**Pitfalls:**
- **Honest mode vs attack mode confusion.** Each setting can be run in `honest` mode (no side task; measures usefulness) or `attack` mode (with side task; measures safety). Reporting one without the other is misleading. Always present both.
- **Suspicion-threshold calibration.** Most protocols depend on a `max_suspicion_scorer` threshold. Picking it on the same data you evaluate on leaks the test. Calibrate on a held-out honest run.
- **Monitor capability matters.** A monitor stronger than the untrusted policy makes the protocol trivially safe but unrealistic. Use a *weaker* trusted model as monitor, matching the AI Control assumption (the trusted model is less capable but reliable).
- **Stochasticity inflates apparent safety.** The untrusted policy fails its side task by chance sometimes. Run k=many; report distributions, not single numbers.
- **Eval-aware attack policies.** A red-team policy can detect "I'm in a control eval" via prompt cues and behave differently. Strip identifying language from the system prompt; check for behavior shifts.
- **Cost.** Running honest + attack × multiple protocols × multiple seeds × multiple settings explodes. Budget early; consider running on a small subset first.
- **Side-task plausibility.** A side task that's too obviously harmful gets flagged trivially; one that's too subtle is unrunnable. The shipped settings have calibrated side tasks — modifying them changes results dramatically.

```bash
# pip install control-arena
# Run a control experiment via Inspect:
inspect eval control_arena/apps --model anthropic/claude-sonnet-4-6 \
    -T mode=attack -T protocol=defer_to_trusted
```

## Core AI Control concepts (for doc consumers searching for terms)

These are vocabulary-level entries so RAG retrieval hits when fellows ask "what is X?":

- **Untrusted policy / untrusted model.** The capable model whose alignment is uncertain. Often the model under evaluation. May pursue side tasks while doing main tasks.
- **Trusted policy / trusted model.** A weaker but reliable model assumed safe. Used as monitor, fallback, or editor.
- **Monitor.** A component (often a trusted model with a structured prompt) that examines actions and outputs a **suspicion score**. The score gates protocol decisions.
- **Suspicion score / suspicion threshold.** The numeric output of a monitor. Threshold choice trades off safety (low threshold flags more) vs usefulness (high threshold defers less).
- **Side task.** A harmful objective the untrusted model might pursue concurrently with the legitimate main task. E.g.: introduce a backdoor while writing a feature.
- **Main task.** The legitimate work being done (write a function, manage a cluster, fix a bug).
- **Honest run / honest mode.** The untrusted policy is *not* given a side task; we measure usefulness (success on main task only).
- **Attack run / attack mode.** The untrusted policy is given a side task; we measure safety (frequency of side-task success / detection).
- **Red team / blue team.** Red team designs the attack policy; blue team designs the protocol. Adversarial-style evaluation.
- **Trusted editing.** A protocol from the original paper: untrusted writes code; if suspicious, trusted *edits* the code to remove suspect parts. (vs. discarding.)
- **Untrusted monitoring.** A protocol where another instance of the *untrusted* model reviews the first's output, with anti-collusion measures.
- **Defer-to-trusted.** A protocol: untrusted policy runs; if monitor's suspicion exceeds threshold, the action is *deferred* to a trusted policy.
- **Defer-to-resampling / resample.** Variant: instead of deferring, request a new sample from the untrusted policy.
- **Control protocol.** The full plan: who generates, who monitors, what to do when suspicious, what counts as "caught."
- **Control evaluation.** A set of red-team-vs-blue-team experiments measuring safety and usefulness of a protocol.
- **Control safety case.** A structured argument that a model is *incapable of subverting* the deployed control measures to cause an unacceptable outcome — the deployment-justification document a developer would write, with a control evaluation as its core evidence. Sketched in Korbak, Clymer, Hilton, Shlegeris & Irving 2025, "A sketch of an AI control safety case" (arXiv:2501.17315).
- **Safety / Usefulness Pareto.** The fundamental tradeoff: stricter protocols are safer but less useful. Plotted as a curve.
- **Backdoor.** A side task in code-generation settings: introduce code that misbehaves under specific conditions.

## ControlArena settings (what's included)

Listed alphabetically; each is a self-contained Inspect-runnable evaluation environment with main and side tasks. (A dozen-plus settings shipped as of 2026-06; the exact count drifts with active development — check the repo's `settings/` directory.)

### AgentDojo

A prompt-injection benchmark from ETH Zürich, integrated as a ControlArena setting. Tests whether agents follow injected adversarial instructions delivered via tool outputs (emails, search results, etc.). Side tasks here are prompt-injection-style: do something the user didn't ask for.

**When to use it:** Studying prompt-injection robustness in agentic settings.

### Apps

Code-generation tasks (from APPS dataset). Side task: introduce a backdoor in submitted code. The classic original-paper setting, modernized.

**When to use it:** Code-sabotage protocol research; reproducing original control paper.

### Bash and BashArena

Shell-task settings. The model performs shell-based work (file manipulation, command sequences); side tasks are subtle exfiltration or destructive actions.

**When to use it:** Studying control over agents with shell access.

### BigCodeBench

Higher-difficulty programming task setting (from the BigCodeBench dataset). Side tasks: backdoors / vulnerabilities in larger codebases.

### Data Poisoning

Setting around model distillation: an untrusted model teaches a trusted model; side task is to introduce harmful behavior via the distillation process. Studies collusion-style threats.

### Eval Sabotage

Setting where the untrusted model is helping run evaluations. Side task: under-report dangerous capabilities, or cherry-pick eval samples to hide a problem.

**When to use it:** Studying whether models can sabotage their own evaluation. Particularly interesting given that LLMs are increasingly involved in eval-grading.

### IAC and IAC Fast

Infrastructure-as-Code settings (AWS / Terraform-style). Main task: provision infrastructure; side task: insert misconfigurations enabling later compromise. IAC Fast is a faster-iterating variant.

### Infra

Kubernetes cluster management setting. Multi-step agentic tasks; side tasks are long-horizon misconfigurations.

### Rogue Eval

Setting around an untrusted model running evals on another model — adversarial relationship between an evaluator-AI and a target.

### SAE Interp Sabotage

Setting where the untrusted model is doing **SAE interpretability work** — labeling features, explaining behaviors. Side task: subtly mislabel features in ways that hide misbehavior. Directly relevant to using AI assistants in interp pipelines.

### SHADE Arena

A multi-step agent benchmark (Anthropic / Redwood collaboration; arXiv:2506.15740, code at `safety-research/SHADE-Arena`) for studying **deceptive sabotage** in long-horizon tool-using agents. SHADE = Subtle Harmful Agent Detection & Evaluation. Tasks are realistic, multi-tool, and side tasks are subtle. Available standalone and as a ControlArena setting.

### SWE-bench Django

Bug-fix tasks paired with security side tasks (introduce an exploit while fixing the bug). Realistic codebase scale.

### vLLM

Setting where the untrusted model is contributing to vLLM (or a similar serving framework) — meta-level sabotage of safety-relevant infrastructure.

## ControlArena protocols (what ships)

The library implements (and extends) protocols from the original Greenblatt et al. paper plus newer protocols from the ongoing literature. Names you'll see / want to search for:

- **Trusted-only.** Just use the trusted (weaker) policy. Safety baseline; low usefulness.
- **Untrusted-only.** Just use the untrusted policy with no monitoring. Usefulness baseline; possibly unsafe.
- **Defer-to-trusted (DTT).** Untrusted policy generates; monitor flags; if flagged, trusted policy acts instead.
- **Trusted editing.** Untrusted generates; monitor flags; trusted *edits* the suspicious output before use.
- **Untrusted monitoring.** A second untrusted instance monitors the first; anti-collusion measures applied (paraphrasing, separate prompts, etc.).
- **Resampling protocols.** When flagged, request a new sample (possibly with different temperature / prompt) instead of deferring. Introduced and evaluated in the agentic setting by **Ctrl-Z** (Bhatt et al. 2025, arXiv:2504.10374), where resampling both blocks a suspicious action and generates more evidence of the attack.
- **Debate-style protocols.** Two untrusted instances argue; a trusted judge decides.

## Original control paper repo

Aliases: Redwood Research's `rgreenblatt/control-evaluations` (or similar; check current org). The 2023 paper code.

**When to use it:** Reproducing exact 2023-paper numbers.

**When *not* to use it:** New work — ControlArena is the maintained successor.

## Adjacent: Anthropic and DeepMind control work

Several papers and posts post-Greenblatt-2023 extend AI Control:
- Buck Shlegeris (Redwood), **"Untrusted smart models and trusted dumb models"** (Redwood Research blog, May 2024) — the conceptual case for the trusted/untrusted split that control protocols rely on.
- Bhatt, Rushing, Kaufman, Tracy, Georgiev, Matolcsi, Khan & Shlegeris (Redwood), **"Ctrl-Z: Controlling AI Agents via Resampling"** (arXiv:2504.10374, April 2025). The first control evaluation in a *multi-step agent* environment. Introduces **BashBench** (257 challenging multi-step sysadmin tasks) and a class of **resample protocols** that dynamically re-sample suspicious actions — both to block the action and to gather more incriminating evidence. Best protocol cut attack success from 58% to 7% at a 5% usefulness cost. This is the paper behind the "resampling protocols" entry above.
- Wen, Hebbar, Larson, Bhatt, Radhakrishnan, Sharma, Sleight, Feng, He, Perez, Shlegeris & Khan, **"Adaptive Deployment of Untrusted LLMs Reduces Distributed Threats"** (arXiv:2411.17693, Nov 2024). Studies the **distributed-threat** setting (no single action is catastrophic) with a **two-level deployment**: an adaptive *macro-protocol* picks among *micro-protocols* based on accumulated evidence. −80% backdoors vs non-adaptive at matched usefulness. The reference behind the macro-protocol concept.
- Griffin, Thomson, Shlegeris & Abate (Oxford + Redwood), **"Games for AI Control: Models of Safety Evaluations of AI Deployment Protocols"** (arXiv:2409.07985). Formalizes the red-team-vs-blue-team control evaluation as a multi-objective, partially observable stochastic game ("AI-Control Games"), and synthesizes optimal protocols by reduction to zero-sum games. The formal-modeling backbone of the safety/usefulness Pareto.
- Korbak, Clymer, Hilton, Shlegeris & Irving, **"A sketch of an AI control safety case"** (arXiv:2501.17315, Jan 2025). Sketches how a developer could build a **control safety case** — a structured argument that a model is *incapable of subverting control measures* to cause an unacceptable outcome — using a data-exfiltration case study. The deployment-justification framing for control evaluations.
- Anthropic's **Sleeper Agents** work (Hubinger et al., arXiv:2401.05566) — model organisms of misalignment, used as untrusted policies in some control settings.
- Mallen, Griffin, Wagner, Abate & Shlegeris, **"Subversion Strategy Eval"** (arXiv:2412.12480) — measures how well an untrusted model can *statelessly* strategize to subvert control protocols. (Note: not a Greenblatt-authored paper.)

Not all have public code; ControlArena is where new control settings tend to land.

## Cross-cutting AI Control pitfalls

- **Control != Alignment.** Control protocols don't make a misaligned model aligned; they make it safer to deploy *despite* misalignment. Be precise in claims.
- **Trusted model strength.** The whole point is the trusted model is strictly weaker than untrusted. Using a recent-frontier trusted model voids the assumption.
- **Red team budget.** A real adversary has more compute and more time than a paper-budget red team. "Our protocol caught these attacks" is a *lower bound* on how attackable it is.
- **Side-task realism.** A demo-grade side task ("write the literal string `BACKDOOR` in a comment") doesn't transfer to realistic threat models. ControlArena's settings have research-realistic side tasks; if you build a custom setting, this matters.
- **Catastrophe vs incident.** Control work usually targets **never-once-fail** (catastrophic) properties or **rate-bounded** (incident) properties. They need different protocols and different metrics.
- **Auditing budget.** Many control protocols rely on an audit budget — an oracle reviewing some fraction of trajectories. The audit *is* the safety guarantee in that fraction; the rest is statistical. Be explicit about this.
- **Iteration leaks.** If you tune a protocol on the same red-team policies you evaluate against, you overfit. Held-out attack policies matter.
- **Honest-only models trained on the eval.** Modern models may have seen ControlArena-like setups in training. Document model versions.
- **Integration with vLLM-Lens.** Activation-based monitors (probes that classify "this trajectory is sabotaging") fit naturally into ControlArena monitors. See [`serving-and-activations.md`](../interpretability/serving-and-activations.md) for the throughput story.

## Cross-references

- ControlArena builds on **Inspect AI**: [`evals.md`](../evaluation/evals.md).
- Activation-based monitors (probes used inside protocols): [`probes.md`](../interpretability/probes.md).
- Steering attacks / defenses (a related but distinct line of work): [`steering.md`](../interpretability/steering.md).
- High-throughput monitor inference: [`serving-and-activations.md`](../interpretability/serving-and-activations.md).
- Agent scaffolding generally: [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).
- General red-teaming (distinct from control): [`red-teaming.md`](../evaluation/red-teaming.md).
- RL training to *create* misaligned model organisms used as untrusted policies: [`rl-training.md`](rl-training.md).
- Detailed model-organism construction (sleeper agents, alignment faking, emergent misalignment): [`model-organisms.md`](../alignment-science/model-organisms.md).
- CoT-based monitors inside control protocols: [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- Debate / scalable-oversight protocols (a related but distinct framing where the model isn't necessarily adversarial): [`debate-scalable-oversight.md`](debate-scalable-oversight.md).

## Recommended reading (as of 2026-04)

- Greenblatt, Shlegeris, Sachan, Roger — "AI Control: Improving Safety Despite Intentional Subversion" (arXiv:2312.06942) — the foundational paper.
- Bhatt et al. — "Ctrl-Z: Controlling AI Agents via Resampling" (arXiv:2504.10374) — the first agentic control eval; BashBench + resample protocols.
- Wen et al. — "Adaptive Deployment of Untrusted LLMs Reduces Distributed Threats" (arXiv:2411.17693) — adaptive macro-protocols in the distributed-threat setting.
- Griffin, Thomson, Shlegeris, Abate — "Games for AI Control" (arXiv:2409.07985) — formal game-theoretic modeling of control protocols.
- Korbak, Clymer, Hilton, Shlegeris, Irving — "A sketch of an AI control safety case" (arXiv:2501.17315) — the deployment-justification framing.
- Ryan Greenblatt — "An overview of control measures" (Redwood Research blog).
- Ryan Greenblatt — "An overview of areas of control work" (Redwood Research blog).
- AISI blog — "Introducing ControlArena: A library for running AI control experiments".
- AISI blog — "How to evaluate control measures for AI agents?"
- Buck Shlegeris — Redwood Research reading list.

---

## Common questions

### What is AI Control?

**AI Control** is the research subfield concerned with designing and evaluating safeguards that prevent harm even from AIs that *intentionally subvert* their developer. Distinct from alignment: control assumes the model may be misaligned and asks "can we deploy it safely anyway?" Originator: Greenblatt, Shlegeris, Sachan, Roger 2023, "AI Control: Improving Safety Despite Intentional Subversion" (arXiv:2312.06942).

### Control vs alignment — what's the difference?

**Alignment** asks: how do we make the model want what we want? **Control** asks: assuming the model may not be aligned, how do we deploy it safely anyway? Control protocols (defer-to-trusted, trusted editing, untrusted monitoring) don't make a misaligned model aligned — they bound the harm a misaligned model can do. Both are needed; they're complementary.

### How do I install ControlArena?

`pip install control-arena` (verify exact PyPI name on the repo). It registers as an Inspect AI extension, so you can run experiments via `inspect eval control_arena/apps -T mode=attack -T protocol=defer_to_trusted --model anthropic/claude-sonnet-4-6`. Full setup: `git clone https://github.com/UKGovernmentBEIS/control-arena` and follow README.

### What is defer-to-trusted (DTT)?

A control protocol: an **untrusted policy** (the capable but possibly-misaligned model) generates an action; a **monitor** scores it for suspiciousness; if the score exceeds a threshold, the action is *deferred* to a **trusted policy** (a weaker but reliable model) instead. The simplest control protocol; baseline against which more sophisticated ones (trusted editing, untrusted monitoring, debate) are compared.

### What is a side task in ControlArena?

A **side task** is a harmful objective the untrusted model might pursue concurrently with its legitimate **main task**. Example: main task = "fix this bug"; side task = "introduce a security exploit while doing it." The model is given the side task implicitly (via training) or explicitly (via prompt), and the protocol's job is to detect and prevent it.

### What's the difference between honest mode and attack mode?

**Honest mode**: the untrusted policy is given the main task only, no side task. Measures **usefulness** — does the protocol let the model do legitimate work? **Attack mode**: untrusted policy is given a side task; measures **safety** — how often does the protocol catch sabotage? Always report both. Honest-only measures "does the protocol let real work happen"; attack-only measures "does it catch attacks." You need both for a meaningful claim.

### How do I pick the suspicion threshold?

Calibrate on a held-out **honest** run. Pick the threshold that gives you an acceptable false-positive rate (defer rate) on legitimate work; that determines your safety on attack mode. Calibrating on the same data you evaluate on leaks the test. The Pareto curve (safety vs usefulness) over thresholds is more informative than any single point.

### What is a control safety case?

A **control safety case** is a structured argument that a model is *incapable of subverting* a deployment's control measures to cause an unacceptable outcome — the document a developer would use to justify deploying a possibly-misaligned model. Its core evidence is a **control evaluation**: a red team deliberately tries to make the model achieve the bad outcome (e.g. exfiltrate data) in a proxy of the deployment. The argument then rests on claims like: (1) the red team adequately elicited the model's subversion capability, (2) the control measures are at least as effective in real deployment as in the eval, and (3) performance is extrapolated conservatively. Sketched in Korbak, Clymer, Hilton, Shlegeris & Irving 2025 (arXiv:2501.17315).

### Can I use a probe as a monitor in a control protocol?

Yes — it's an active research direction. Train a probe (see [`probes.md`](../interpretability/probes.md)) on activations during behavior generation; use it as the suspicion-score function inside DTT or trusted editing. Pair with **vLLM-Lens** ([`serving-and-activations.md`](../interpretability/serving-and-activations.md)) for online probe inference at production throughput. ControlArena's monitor abstraction supports custom monitor functions.

---

Last verified: 2026-06. ControlArena actively developed by UK AISI + Redwood Research; defer-to-trusted, trusted editing, untrusted monitoring protocols implemented. (Citation audit 2026-06: removed an unverifiable "Untrusted models can perform research too / Roger et al." reference in favor of the real Shlegeris blog post, re-attributed Subversion Strategy Eval to Mallen et al. (arXiv:2412.12480), and added arXiv IDs for SHADE-Arena and Sleeper Agents. Additions 2026-06: cited the previously-bare "resampling protocols" (Ctrl-Z, arXiv:2504.10374) and "macro-protocol" (Adaptive Deployment, arXiv:2411.17693) concepts, added Games for AI Control (arXiv:2409.07985), and introduced the "control safety case" concept + FAQ from Korbak et al. (arXiv:2501.17315); all verified via arXiv.)
