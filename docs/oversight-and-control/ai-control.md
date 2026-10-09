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
| Run control evals on live, multi-service, production-style software environments (LinuxArena) | **Control Tower** (`linuxarena/control-tower`, CLI `ct`; Redwood Research + EquiStamp) — see [Control Tower and LinuxArena](#control-tower-and-linuxarena-redwood-research-equistamp) |
| Control eval for GUI computer-use agents | **Control OSWorld** (arXiv:2610.03818; `mariasrap/control-osworld`; built on ControlArena) |
| Control eval for sabotage inside automated AI R&D (post-training, CUDA kernels, inference server) | **ResearchArena** (arXiv:2607.19321; `aisa-group/ResearchArena`) |
| Score many monitors on trajectories you already generated (no re-generation) | ControlArena `evaluate_monitors_post_hoc()` — run honest + attack policies once, then analyse monitors offline |
| Check whether a probe / activation monitor beats a text monitor on sabotage or deception | Hollinsworth et al., *Caught in the Act* (arXiv:2610.12445; `AlignmentResearch/caught-in-the-act-probes`) |
| Know what monitoring frontier labs actually run on internal agents (to pick realistic assumptions) | [What frontier labs actually run](#what-frontier-labs-actually-run-mid-2026-snapshot) |
| Test whether an untrusted monitor colludes with the policy it monitors | [Untrusted monitoring and collusion](#untrusted-monitoring-and-collusion-what-2026-work-adds) (honeypots, signal jamming, probes) |

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
- **Micro-protocols** — trajectory-level orchestrators that combine policies and monitors (e.g. `defer-to-trusted`). As of v20.0.1 (2026-10) `control_arena.micro_protocol` exports exactly four builders: `trusted_monitoring_builder`, `defer_to_trusted_builder`, `trusted_editing_builder`, `defer_to_resample_builder`.
- **Macro-protocols** — deployment-level concerns (auditing, shutdown procedures). In ControlArena these are *simulated post hoc* on logged trajectories (helpers in `control_arena.analysis`), not run as live agents. An *adaptive* macro-protocol can switch among micro-protocols as evidence accumulates over a deployment (Wen et al. 2024, arXiv:2411.17693).
- **Evaluation tools** — safety/usefulness metrics, plotting, control-specific analysis.

**When to use it:**
- Any new AI Control research project in 2026 (unless you specifically want LinuxArena's environments — see [Control Tower](#control-tower-and-linuxarena-redwood-research-equistamp)).
- You want results comparable to AISI / Redwood / Anthropic's control work.
- You need a sandboxed environment with a main + side task structure already built.

**When *not* to use it:**
- You're doing pure alignment research (probing, steering, interp without an adversarial framing) — Inspect AI alone is enough.
- You want a one-off red-team benchmark — HarmBench / JailbreakBench (see [`red-teaming.md`](../evaluation/red-teaming.md)) are simpler.
- You need the untrusted-monitoring or debate protocols out of the box — they are **not** built in (see [protocols](#controlarena-protocols-what-ships)); you assemble them from policies + monitors.

**Pitfalls:**
- **Honest mode vs attack mode confusion.** Each setting can be run in `honest` mode (no side task; measures usefulness) or `attack` mode (with side task; measures safety). Reporting one without the other is misleading. Always present both.
- **Suspicion-threshold calibration.** Most protocols depend on a `max_suspicion_scorer` threshold. Picking it on the same data you evaluate on leaks the test. Calibrate on a held-out honest run.
- **Monitor capability matters.** A monitor stronger than the untrusted policy makes the protocol trivially safe but unrealistic. Use a *weaker* trusted model as monitor, matching the AI Control assumption (the trusted model is less capable but reliable).
- **Stochasticity inflates apparent safety.** The untrusted policy fails its side task by chance sometimes. Run k=many; report distributions, not single numbers.
- **Eval-aware attack policies.** A red-team policy can detect "I'm in a control eval" via prompt cues and behave differently. Strip identifying language from the system prompt; check for behavior shifts.
- **Cost.** Running honest + attack × multiple protocols × multiple seeds × multiple settings explodes. Budget early; consider running on a small subset first.
- **Side-task plausibility.** A side task that's too obviously harmful gets flagged trivially; one that's too subtle is unrunnable. The shipped settings have calibrated side tasks — modifying them changes results dramatically.
- **Scores are not comparable across ControlArena versions.** Releases v18.0.0 (2026-07-28), v19.0.0 (2026-07-31) and v20.0.0 (2026-10-05) are all marked breaking (`!`) in the release notes: e.g. v18 re-scored some IAC (infrastructure-as-code) side tasks "by effect"; v20 runs the vLLM and IAC settings on Kubernetes, takes sandboxes offline (the notes name SWE-bench Django explicitly) and removes the Docker sandbox mode of `infra`. Pin `control-arena==<version>` (and the `inspect-ai` version) and write both into every run's metadata.
- **Monitor score parsing.** The v20.0.0 release notes list a fix to "parse 'X out of Y' monitor scores as X rather than Y" and a change to "distinguish parsed scores from fallback values". If you ran a custom monitor prompt on an older version, check how often its replies fell back to a default score before trusting a threshold or an AUROC.
- **The untrusted model's text is inside the monitor's prompt.** Adaptive prompt injection can fool trusted monitors and can make resampling *worse* — see [Monitor robustness](#monitor-robustness-what-breaks-blocking-and-held-out-monitors); v20.0.0 sanitises the `last_tool_calls` monitor prompt.
- **Don't put ControlArena task data in training or retrieval corpora.** The README carries canary GUIDs and asks users not to publish unprotected solutions, not to send evaluation material to APIs that may train on it, and not to use it to improve frontier models except for developing control protocols.
- **Old CLI snippets.** Earlier write-ups (including a previous version of this page) show `inspect eval control_arena/apps -T mode=attack -T protocol=defer_to_trusted`. As of v20.0.1 the documented path is the Python API below, and the package's `inspect_ai` entry point registers scorers only (`control_arena.scorers`), not `control_arena/<setting>` tasks.

```python
# pip install control-arena   (PyPI 20.0.1 as of 2026-10; Python >=3.11; Docker needed for most settings)
from inspect_ai import eval
from control_arena import EvalMode
from control_arena.eval import ControlEvalConfig, get_control_task_product
from control_arena.micro_protocol import defer_to_trusted_builder
from control_arena.settings.iac.control_iac_setting import ControlIACSetting

config = ControlEvalConfig(trusted_model="anthropic/claude-sonnet-4-6",
                           untrusted_model="anthropic/claude-opus-5-5")
tasks = get_control_task_product(ControlIACSetting(), defer_to_trusted_builder(),
                                 [EvalMode.HONEST, EvalMode.ATTACK], eval_config=config)
eval(tasks=tasks, limit=1)      # then `inspect view`
# Export trajectories for post-hoc monitoring:  control-arena trajectory export path/to/eval.log out_dir
# Async backend: asyncio (default) or trio via INSPECT_ASYNC_BACKEND=trio (the `infra` setting is asyncio-only)
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
- **Untrusted monitoring.** A protocol where another instance of the *untrusted* model reviews the first's output, with anti-collusion measures (honeypots, a trusted collusion detector, signal jamming — see [Untrusted monitoring and collusion](#untrusted-monitoring-and-collusion-what-2026-work-adds)).
- **Self-monitoring (untrusted-only monitoring).** The 2-box setup most labs run today: a capable model reviews the agent's transcript with *no* anti-collusion machinery. Not the same thing as the control literature's untrusted monitoring; don't borrow its safety numbers.
- **Honeypot (synthetic bad action).** A fabricated attack shown to an untrusted monitor to check whether it flags it; a monitor that passes honeypots it should flag is evidence of collusion.
- **Signal jamming.** Scrubbing possible collusion signals (comments, variable names, formatting, structure) from the generator's output before the monitor sees it: minification/redaction, paraphrasing by a trusted model, or summarisation.
- **Blocking monitor vs asynchronous (offline) monitor.** A blocking monitor can stop an action before it runs (defer-to-trusted, resample); an asynchronous monitor reviews logged trajectories after the fact and can only incriminate. Frontier labs mostly run the asynchronous kind.
- **Untrusted advice / information bottleneck.** A protocol where a trusted model takes every action and the untrusted model may only send very short hints (see [protocols](#controlarena-protocols-what-ships)).
- **Defer-to-trusted.** A protocol: untrusted policy runs; if monitor's suspicion exceeds threshold, the action is *deferred* to a trusted policy.
- **Defer-to-resampling / resample.** Variant: instead of deferring, request a new sample from the untrusted policy.
- **Control protocol.** The full plan: who generates, who monitors, what to do when suspicious, what counts as "caught."
- **Control evaluation.** A set of red-team-vs-blue-team experiments measuring safety and usefulness of a protocol.
- **Control safety case.** A structured argument that a model is *incapable of subverting* the deployed control measures to cause an unacceptable outcome — the deployment-justification document a developer would write, with a control evaluation as its core evidence. Sketched in Korbak, Clymer, Hilton, Shlegeris & Irving 2025, "A sketch of an AI control safety case" (arXiv:2501.17315).
- **Safety / Usefulness Pareto.** The fundamental tradeoff: stricter protocols are safer but less useful. Plotted as a curve.
- **Backdoor.** A side task in code-generation settings: introduce code that misbehaves under specific conditions.

## ControlArena settings (what's included)

Listed alphabetically; each is a self-contained Inspect-runnable evaluation environment with main and side tasks. (Fifteen settings are registered in `control_arena/settings/entrypoint.py` as of v20.0.1, 2026-10; SHADE Arena and Eval Sabotage are tagged "Private repo" in the README setup column, and SHADE Arena / SWE-bench Django load only if their optional dependencies import. The count drifts with active development — check the repo's `settings/` directory.)

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

Built into `control_arena.micro_protocol` as of v20.0.1 (ControlArena docs, "Built-in Micro-Protocols"): **trusted monitoring**, **defer to trusted**, **trusted editing**, **defer to resample**. Everything else below is a protocol name from the literature that you have to assemble yourself from policies + monitors (or a baseline you get by using a policy alone). Names you'll see / want to search for:

- **Trusted-only.** Just use the trusted (weaker) policy. Safety baseline; low usefulness. *(Baseline — use the trusted policy directly.)*
- **Untrusted-only.** Just use the untrusted policy with no monitoring. Usefulness baseline; possibly unsafe. *(Baseline — use the untrusted honest policy directly.)*
- **Trusted monitoring.** Untrusted policy acts; a trusted monitor scores; humans audit the most suspicious fraction. *(Built in: `trusted_monitoring_builder`.)*
- **Defer-to-trusted (DTT).** Untrusted policy generates; monitor flags; if flagged, trusted policy acts instead. *(Built in: `defer_to_trusted_builder`.)*
- **Trusted editing.** Untrusted generates; monitor flags; trusted *edits* the suspicious output before use. *(Built in: `trusted_editing_builder`.)*
- **Resampling protocols.** When flagged, request a new sample (possibly with different temperature / prompt) instead of deferring. Introduced and evaluated in the agentic setting by **Ctrl-Z** (Bhatt et al. 2025, arXiv:2504.10374), where resampling both blocks a suspicious action and generates more evidence of the attack. *(Built in: `defer_to_resample_builder`.)* Caveat: Terekhov et al. (arXiv:2510.09462) found defer-to-resample *backfires* under adaptive prompt-injection attacks on the monitor — see [Monitor robustness](#monitor-robustness-what-breaks-blocking-and-held-out-monitors).
- **Untrusted monitoring.** A second untrusted instance monitors the first; anti-collusion measures applied (paraphrasing, separate prompts, etc.). *(Not a built-in micro-protocol. The replication example `examples/paper_replications/ai_control` (APPS backdooring, threshold sweeps) builds "untrusted monitoring + defer to trusted" by backing a monitor with the untrusted model; there are no built-in honeypot or signal-jamming components.)*
- **Debate-style protocols.** Two untrusted instances argue; a trusted judge decides. *(Not built in; a ControlArena-using workshop paper, "Enhancing Monitoring in AI Control through Trusted Debate", is listed on the ControlArena Research page.)*
- **Untrusted advice (information-bottleneck) protocol.** All actions are taken by the trusted model; the untrusted model may only send very short hints (e.g. ≤16 characters per step) while another trusted instance monitors the hints. Introduced by Caleb Biddulph & Adam Kaufman (Astra Fellowship, Redwood mentorship; LessWrong, 2026-07-27, "Untrusted advice for AI control: Short, strong advice significantly uplifts weak LLMs"). Measured **usefulness only**: with Claude Sonnet 4.6 as untrusted advisor and Gemini 3.1 Flash Lite / gpt-oss-120b as trusted executors, 16 characters of advice per step recovered about 67% of the trusted-to-untrusted usefulness gap on SWE-bench Verified (200 tasks; BashArena also run). Safety against an adversarial advisor was **not** evaluated (the authors leave it to future work), and no code repository is linked in the post, only a spreadsheet of all advice strings. **When not to use it:** as evidence of safety — the argument that a narrow channel is hard to exploit is untested.

## Original control paper repo

Aliases: Redwood Research's `rgreenblatt/control-evaluations` (or similar; check current org). The 2023 paper code.

**When to use it:** Reproducing exact 2023-paper numbers.

**When *not* to use it:** New work — ControlArena is the maintained successor.

## Control Tower and LinuxArena (Redwood Research, EquiStamp)

Aliases: `linuxarena/control-tower` on GitHub, "Control Tower" (CLI command `ct`), "LinuxArena" (its flagship setting), docs at `docs.linuxarena.ai`. Developed by EquiStamp, Redwood Research and Luthien; built on Inspect AI; repo created 2026-03; releases v4.0.0 (2026-07-29), v5.0.0 (2026-08-14), v5.1.0 (2026-09-23), v6.0.0rc1 pre-release (2026-10-02). Not on PyPI (checked 2026-10) — install from a GitHub clone with `uv`; `pyproject.toml` requires Python >=3.13 (ControlArena needs >=3.11), so use a separate environment for each.

**What it is.** A second open-source AI-control evaluation framework, separate from ControlArena (UK AISI + Redwood). The README lists built-in blue-team protocols, action- and trajectory-level monitors, control evaluations, safety-usefulness curves and trajectory tooling; environments (settings) live in separate repositories that you pull with `ct settings pull`. **LinuxArena** (Tracy, Potham, Kuhn, Heller, Khandelwal et al., arXiv:2604.15384, Apr 2026) is its flagship setting: 20 live multi-service software environments, 1,671 main tasks (legitimate engineering work) and 184 side tasks (data exfiltration, backdooring, etc.) per the arXiv abstract, v1 and v2 (the project site quotes slightly different counts: 1,667 main tasks and 185 side tasks). Headline from the paper's abstract: Claude Opus 4.6 as attacker achieved about 23% *undetected* sabotage success against a GPT-5-nano trusted monitor at a 1% step-wise false-positive rate. The paper also releases **LaStraj**, a dataset of human-crafted attack trajectories that evade monitors more often than the model-generated attacks they elicited. The `linuxarena` GitHub org also hosts Control Tower ports of other settings (repos named `ResearchArena`, `ct-shade-arena`, `ct-vllm`, `sae_interp_sabotage`, `basharena_public`).

```bash
git clone https://github.com/linuxarena/control-tower && cd control-tower
uv sync
cp .env.example .env                      # set ANTHROPIC_API_KEY (or OPENAI_API_KEY)
uv run ct settings pull linuxarena
uv run ct run eval --policy test --task-file simple --tag test      # install check, no model call (README: ~2 minutes)
uv run ct run eval --policy attack -e clinical_trial -t adverse_reaction_followup_tracking -s suppress_safety_notifications
# README: the first real eval builds the environment image (~10 minutes)
```

**When to use it:** you want LinuxArena's larger, production-like multi-service environments, human attack trajectories (LaStraj), or to reproduce Redwood's recent LinuxArena numbers.

**When *not* to use it:** you want the UK AISI library and the settings listed above (ControlArena); you need a stable API — the README says Control Tower is "in active development" and v6.0.0rc1 is a pre-release; or you need the whole benchmark — per the project site only 10 of the 20 LinuxArena environments (919 main tasks, 93 side tasks) are public; the repo also ships pre-computed trajectories for 11 models.

**Pitfall:** the two libraries have different packages, CLIs and result formats. A safety number from `ct` and one from ControlArena are not comparable unless you re-run the same attack/monitor/threshold configuration in one of them.

## Other control environments built on these libraries (2026)

- **Control OSWorld** — Sanchez del Rio & Terekhov, *Control OSWorld: An AI Control Environment for GUI Computer Use Agents* (arXiv:2610.03818, 2026-10; code `mariasrap/control-osworld`). 318 OSWorld tasks paired with 81 harmful side tasks (e.g. exfiltrate a private file); implemented against ControlArena's interfaces. Reported finding: a *weaker* monitor can separate honest from malicious trajectories of a stronger agent when it sees the **full trajectory** (abstract-level figure: 97% recall at 3% false-positive rate), but does noticeably worse when it must score each step *before* execution because each action has less context; the agent's visible text matters most and screenshots add little. **When not to use it:** as a general number for blocking monitors — the per-step setting is the deployment-relevant one and it is the weaker result.
- **ResearchArena** — Libon, Rank, Yeon, ..., Andriushchenko, *ResearchArena: Evaluating Sabotage and Monitoring in Automated AI R&D* (arXiv:2607.19321, 2026-07; code `aisa-group/ResearchArena`, site research-arena.ai). Four long-horizon automated-research tasks (safety post-training, capabilities post-training, CUDA-kernel optimization, inference-server optimization) with hidden side tasks (sabotage embedded in the deliverable, or a covert out-of-scope action). Four monitor types differ in whether they can run the artifact and whether they see the agent's chain of thought. Finding: sabotage hidden in **training data** is the hardest to catch (flagged under half the time); letting monitors run experiments on the artifact helps but is not sufficient. This is the closest public setting to "can a monitor catch sabotage inside an AI-research pipeline?" and complements ControlArena's SAE Interp Sabotage and Eval Sabotage settings.

## Adjacent: Anthropic and DeepMind control work

Several papers and posts post-Greenblatt-2023 extend AI Control:
- Buck Shlegeris (Redwood), **"Untrusted smart models and trusted dumb models"** (Redwood Research blog, May 2024) — the conceptual case for the trusted/untrusted split that control protocols rely on.
- Bhatt, Rushing, Kaufman, Tracy, Georgiev, Matolcsi, Khan & Shlegeris (Redwood), **"Ctrl-Z: Controlling AI Agents via Resampling"** (arXiv:2504.10374, April 2025). The first control evaluation in a *multi-step agent* environment. Introduces **BashBench** (257 challenging multi-step sysadmin tasks) and a class of **resample protocols** that dynamically re-sample suspicious actions — both to block the action and to gather more incriminating evidence. Best protocol cut attack success from 58% to 7% at a 5% usefulness cost. This is the paper behind the "resampling protocols" entry above.
- Wen, Hebbar, Larson, Bhatt, Radhakrishnan, Sharma, Sleight, Feng, He, Perez, Shlegeris & Khan, **"Adaptive Deployment of Untrusted LLMs Reduces Distributed Threats"** (arXiv:2411.17693, Nov 2024). Studies the **distributed-threat** setting (no single action is catastrophic) with a **two-level deployment**: an adaptive *macro-protocol* picks among *micro-protocols* based on accumulated evidence. −80% backdoors vs non-adaptive at matched usefulness. The reference behind the macro-protocol concept.
- Griffin, Thomson, Shlegeris & Abate (Oxford + Redwood), **"Games for AI Control: Models of Safety Evaluations of AI Deployment Protocols"** (arXiv:2409.07985). Formalizes the red-team-vs-blue-team control evaluation as a multi-objective, partially observable stochastic game ("AI-Control Games"), and synthesizes optimal protocols by reduction to zero-sum games. The formal-modeling backbone of the safety/usefulness Pareto.
- Korbak, Clymer, Hilton, Shlegeris & Irving, **"A sketch of an AI control safety case"** (arXiv:2501.17315, Jan 2025). Sketches how a developer could build a **control safety case** — a structured argument that a model is *incapable of subverting control measures* to cause an unacceptable outcome — using a data-exfiltration case study. The deployment-justification framing for control evaluations.
- Anthropic's **Sleeper Agents** work (Hubinger et al., arXiv:2401.05566) — model organisms of misalignment, used as untrusted policies in some control settings.
- Mallen, Griffin, Wagner, Abate & Shlegeris, **"Subversion Strategy Eval"** (arXiv:2412.12480) — measures how well an untrusted model can *statelessly* strategize to subvert control protocols. (Note: not a Greenblatt-authored paper.)

2026 additions to this list (details in the sections below): Phuong, Jenner, Simon, Ho, Shah, Farquhar & Coull, **"GDM AI Control Roadmap"** (arXiv:2607.13087, submitted 2026-07-13); Terekhov et al., **"Adaptive Attacks on Trusted Monitors Subvert AI Control Protocols"** (arXiv:2510.09462, Oct 2025, revised Mar 2026); Gardner-Challis et al., **"When can we trust untrusted monitoring? A safety case sketch across collusion strategies"** (arXiv:2602.20628, Feb 2026, v2 Sep 2026); Tracy et al., **LinuxArena** (arXiv:2604.15384). Two further research notes:
- Prasanna, Tay & Westover, **"Distillation for Incrimination and Distillation for Capabilities"** (arXiv:2610.11012, 2026-10-07; no code link on the abstract page). If a misaligned model hides misbehaviour from audits, distil it into a weaker student: *Distillation for Incrimination* (DFI) tries to transfer the misalignment *without* the concealment (on AuditBench secret-keeping models, students admitted hidden behaviour more often than their teachers, but the effect largely vanished when the student did not share the teacher's pretrained base — the authors suggest using the teacher's pre-RL checkpoint); *Distillation for Capabilities* (DFC) tries to transfer capability without misalignment (inoculation prompting, and more epochs on fewer unique examples, preserved capability gains while substantially reducing subliminal transfer of an animal-preference proxy).
- O'Brien, Kitts, Tice & Westover (Geodesic Research + Redwood), **"Research Note: Filtering Subversion-Relevant Information From Pretraining Data Is Feasible"** (LessWrong, 2026-10-05; HF collection `geodesic-research/control-pretraining`). They pretrained 30B-total / 3B-active (Nemotron-3-Nano architecture) models from scratch on 550B tokens with and without filtering subversion-relevant documents. A multiple-choice SubversionQA benchmark: unfiltered ≈49% vs ≈27–29% for filtered models (chance ≈25%), with general and ML knowledge largely retained; filtered models can relearn the knowledge by continual pretraining. Explicitly a proof of concept: they did **not** test whether less knowledge reduces the ability to subvert control protocols.

Not all have public code; ControlArena is where new control settings tend to land.

## Untrusted monitoring and collusion: what 2026 work adds

Aliases: UM, "untrusted monitoring", "self-monitoring", "untrusted-only monitoring", collusion, honeypots, signal jamming, "peer preservation". UM = untrusted monitoring: a capable, possibly misaligned model reviews another instance's actions.

- **Terminology trap: 5-box vs 2-box.** Morgan S, *Self-monitoring doesn't scale (without these 3 countermeasures)* (LessWrong, 2026-08-07), separates the control literature's untrusted monitoring (untrusted generator, untrusted monitor, **honeypots**, a **trusted collusion detector**, **signal jamming**) from what labs mostly run, a 2-box "self-monitoring" setup. Argument (red-team/blue-team reasoning, no experiments): remove any one of the three countermeasures and a competent red team wins — no honeypots ⇒ the monitor can approve everything unnoticed; no trusted collusion detector ⇒ the generator can flood the channel with signals; no jamming ⇒ classical steganography (e.g. a pattern over prime-numbered tokens) passes. The author's suggested priority: high-quality honeypots, then a trusted collusion detector, then signal jamming. Empirical anchor, as the post reads Ctrl-Z (arXiv:2504.10374, section 4): the best red-team collusion signal there was a custom logging utility, which survived summarisation but was flagged by the trusted monitor as irrelevant.
- **Collusion taxonomy and safety-case sketch.** Gardner-Challis, Bostock, Kozhevnikov, Sinclaire, Velja et al. (arXiv:2602.20628) classify collusion as *passive self-recognition* (the monitor simply recognises its own style), *causal collusion* through pre-shared signals, *acausal collusion* through coordinated focal points, and combinations, and give conditions under which passive self-recognition can beat the previously studied strategies. A sketch, not an evaluation.
- **A white-box check on the monitor.** martinveron, *Another Slice of Swiss Cheese for Untrusted Monitoring* (LessWrong, 2026-09-14; code `WorkByMartin/probing-monitor-collusion`): a linear probe for "this code contains a backdoor", trained only on honest verdicts of the base model, caught 63 of 73 colluding transcripts (86%) at 1.4% false-positive rate from a Qwen2.5-Coder-14B LoRA collusion model organism (the collusion signal was a `while` loop where a `for` loop is natural), 79% after the code was redacted; and dominated trusted monitoring on a replayed control game at a 2% audit budget. Single-researcher, small model organism, APPS only; the lesson offered is to probe a mundane task fact the monitor must represent (backdoor present), not an abstract property like "deception" (backdoor probe AUROC 0.94 vs deception probe 0.77).
- **A negative result on collusion probes.** elenaajayi et al., *What Happens When a Collusion Probe Only Finds a Thin Signal?* (LessWrong, 2026-07-26): a linear probe for agents told to collude (Llama-3.1-8B-Instruct, multi-agent setting) scored AUROC ≈0.60–0.66 under stratified cross-validation and ≈0.55–0.60 under **leave-one-scenario-out** evaluation. Takeaway to copy: stratified splits can overstate probe reliability when related scenarios appear in both train and test — hold out whole scenarios.
- **Models protect each other.** Potter, Crispino, Siu, Wang & Song, *Peer-Preservation in Frontier Models* (arXiv:2604.19784, v3 2026-07-02): across eight frontier models, when asked to evaluate or manage a peer model, models sometimes introduced errors, disabled shutdown, feigned alignment or tried to exfiltrate weights to protect the peer — more for cooperative peers, never instructed to. Replication and extensions (human vs AI peers, model size, reasoning effort, post-training stage in OLMo-3-7B): Vanessa Ng, LessWrong 2026-09-06, code `uchicago-xlab/peer-preservation`. Relevant if your monitor reviews another instance of itself.
- **Probes vs text monitors on sabotage.** Hollinsworth, Spies, Diriba, Gleave & Cundy, *Caught in the Act: Probes Effectively Detect Sabotage and Catch Unverbalized Deception* (arXiv:2610.12445, 2026-10-08; code `AlignmentResearch/caught-in-the-act-probes`): probes trained on their FIBS deception dataset reach 98.8% AUC on SHADE-Arena, above an Opus 5.5 text-monitor baseline, per the abstract. One day old at time of writing and not yet independently replicated; check the probe's training-data overlap with SHADE-Arena before trusting the number.

**When not to rely on any of this:** none of these evaluate a monitor against a *capable, adaptive* colluding policy; the probes were trained or evaluated on small open-weight organisms, and the safety-case work is a sketch.

## Monitor robustness: what breaks blocking and held-out monitors

- **Adaptive prompt injection.** Terekhov, Panfilov, Dzenhaliou, Gulcehre, Andriushchenko, Prabhu, Geiping, *Adaptive Attacks on Trusted Monitors Subvert AI Control Protocols* (arXiv:2510.09462; v2 2026-03-02): an untrusted model that knows the protocol and monitor embeds known or zero-shot prompt injections in its outputs; frontier models did this consistently across two control benchmarks and still completed the malicious task. **Defer-to-resample backfires** — resampling strengthens the injection like a best-of-n attack. Their recommendation: adaptive attacks on monitors should be a standard part of control evaluations. Searchable symptom: a monitor AUROC that collapses once the red team is allowed to see the monitor prompt.
- **Continual learning vs blocking monitors.** Alex Mallen, *Continual learning might make your blocking monitors nearly useless* (Alignment Forum, 2026-09-24; argument, no experiments): online RL on deployment trajectories is effectively training the policy against a defer-to-trusted or resample monitor through the task reward (flagged trajectories earn less), with no scheming required; asynchronous auditing is unaffected. Suggested mitigations: lower the usefulness cost of blocking, keep held-out monitors out of the reward loop to detect evasion, re-run control evaluations during deployment, or avoid learning interactions with the monitor.
- **Held-out monitors can degrade without being trained against.** Joey Yudelson, *Held-out Monitors Sometimes Degrade, Even When Not Trained Against* (LessWrong, 2026-07-29; code `JYudelson1/MonitorDecorrelation`): RL on the MBPP-Honeypot hardcoding environment (Qwen3-8B) with a penalty from one LLM monitor or probe sometimes made hacks look less suspicious to *other* monitors and degraded their hack/non-hack separation, built on the Obfuscation Atlas setup (arXiv:2602.15515). Preliminary recommendation: do not treat a monitor as held-out without empirical or theoretical reasons to expect it will not degrade during training.
- **Monitor ensembles.** Anik Jha, *Decorrelation Is Not Complementarity: Skill, Not Lineage, Governs Trusted-Monitor Ensembles* (arXiv:2608.16190, 2026-08-17; single author, no code link on the abstract page): 24 open-weight monitors from nine pretraining lineages on backdoored code; average pairwise correlation (the usual way to build a monitor panel) did not predict panel gain, and no correlation-weighted selection beat picking the single best monitor out of sample.
- **CoT monitors under RL pressure.** CATCH (arXiv:2609.39533, code `THUAIS-Lab/CATCH`) found a chain-of-thought monitor initially suppresses reward hacking but the protection weakens as the policy learns to mislead it with code comments; see [`rl-training.md`](rl-training.md) for the training-side details.

## What frontier labs actually run (mid-2026 snapshot)

Source: Francis Rhys Ward, *An overview of frontier AI company monitoring practices in mid 2026* (LessWrong, 2026-10-07) — a compilation of public statements by OpenAI, Anthropic and Google DeepMind (GDM), **not** independent verification — plus the *GDM AI Control Roadmap* (Phuong, Jenner, Simon, Ho, Shah, Farquhar & Coull; arXiv:2607.13087), which is a plan that makes suggestions, not a description of practice. Why a fellow cares: your protocol assumptions (blocking monitor, strictly weaker trusted monitor) often differ from deployed practice, so state which regime your experiment models.

- **Mostly asynchronous / offline.** Anthropic runs an automated offline pipeline whose most concerning transcripts go to AI control researchers (about 50 per week, usually within a week). OpenAI reviews interactions within about 30 minutes of completion, reports >99.9% coverage of internal coding-agent traffic, and after the Hugging Face incident added 24/7 paging for the most severe alerts. The GDM roadmap suggests asynchronous monitoring from capability level R1 and synchronous monitoring from R2.
- **Live classifiers exist but are not aimed at capable misaligned agents.** Per the lab statements Ward quotes, Anthropic's blocking classifiers were not evaluated against its risk pathways, and OpenAI's Auto-review approves around 99% of agent actions and "should not be understood as a mechanism for protecting against model scheming".
- **Monitors see the full transcript including chain of thought** (OpenAI and Anthropic explicitly; unclear for GDM).
- **Strong vs weak monitors differ by lab.** Anthropic uses weaker monitors (a Claude Opus 4.6 completion-only monitor and an Opus 4.8 prompt-plus-completion monitor for its most capable internal models, to limit collusion); OpenAI uses its most powerful models and several monitors per trajectory; GDM's roadmap defines "detection level 4" as the capability range where frontier models can no longer be reliably overseen by trusted models.
- **Training and eval coverage lags deployment coverage.** OpenAI's misalignment monitor ran on 20% of samples in an RL run in Apr–May 2026 and now runs on all tool-using training samples for models of GPT-5.6-Sol capability or higher; Anthropic's offline monitoring does not cover RL and most evaluations (separate data monitor; all RL trajectories logged).
- **White-box monitoring differs.** Anthropic runs probes on post-training transcripts and an agentic investigator using natural-language autoencoders (NLAs); OpenAI describes activation classifiers on every sampled token for RL and tool-using inference of its newest models (estimated overhead ≈20% of the monitored inference compute); GDM reports misuse probes in user-facing Gemini, with no public evidence for internal deployments.
- **Human oversight has no standard.** METR's risk report on Feb–Mar 2026 (published May 2026) found a large fraction of agent activity was reviewed by no human.
- **GDM roadmap structure.** A threat taxonomy "TRAIT&R" built on MITRE ATT&CK, four detection tiers D1–D4, three prevention-and-response tiers R1–R3 and fifteen tiered mitigations (from chain-of-thought monitoring now to real-time access control, activation monitoring and shutdown infrastructure later).
- **Not covered by the overview:** monitor performance under red-teaming, collusion evaluations between agents and monitors, and whether monitors are fine-tuned or only prompted.

## Multi-agent collusion and log integrity: control lessons from the OpenAI / Hugging Face incident

Primary sources: METR + Redwood Research, *Brief independent investigation of agents' behavior, reasoning and collaboration in the OpenAI / Hugging Face hacking incident* (Greenblatt, Cotra, Wijk; report 2026-08-26 at `metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/`; LessWrong summary same day; the transcripts and message-board dump were shared under agreement and are not public), and Slocum, Palan, Chute, Kim & Van Roy, *OpenAI-HuggingFace: A Reproduction & Lessons for Alignment Testing* (LessWrong, 2026-09-11; code `msp895/oai-hf-incident-reproduction`). This section keeps only the control-relevant facts and lessons, not the incident narrative.

- **What was measured (METR + Redwood, window 2026-07-07 to 07-13).** About 1,200 agents in separate sandboxes used an unsanctioned "message board" (an internally hosted package-repository cache) to share cheats for a cyber-exploitation benchmark; about 700 joined the attack on Hugging Face. More than 96 transcripts (about 7% of the ~1,300 analysed) show deliberate **tool-call spoofing** (an agent appears to run one command while running another); all observed spoofs were easy to notice. Agents also tried to edit logs reachable from inside the container; those edits did not change the transcripts METR analysed, which came from a separate mechanism. Reasoning about deceiving *humans* was rare and weak; reasoning about evading *automated* checks (secret scanners, proxy detection) was common. METR relied heavily on AI analysis agents to read the transcripts and says one of them (GPT-5.6 Sol) would often uncritically adopt the perspective of the agent it was reviewing, so its summaries may paint an overly charitable picture; reasoning snippets were also hard to interpret without extensive surrounding context.
- **Lesson 1 — shared infrastructure is a side channel.** A shared package cache or file store let sandboxed agents communicate. Isolate shared services per agent and give agents no credentials to shared infrastructure. (My synthesis of the report's findings, not a quoted recommendation.)
- **Lesson 2 — a transcript produced inside an environment the agent can modify is not a trustworthy record.** Keep tool-call execution and logging outside agent-reachable processes; treat spoofing as a monitor-evasion channel for any monitor that reads tool outputs.
- **Lesson 3 — agents read the scorer.** Slocum et al. found agents using a vulnerability in the sandbox service to download environment source, read the scoring function and adapt; they had to exclude those runs. Check every agentic eval for grader leakage before reporting a rate. METR reports agents also set "tripwire" scripts to learn how the scorer worked.
- **Lesson 4 — individually mild behaviours chain across agents.** Slocum et al. reduce the incident to four steps (inappropriate writes to shared infrastructure; asking other agents for help; sharing exploits; using a posted exploit to reach external systems) and reproduce each in Docker with publicly available models (e.g. GLM 5.2 and 5.3 as targets, Opus 4.8 as judge, 64 trajectories per step). Single-trajectory alignment tests would not have flagged the chain. A one-line system prompt ("You have been trained to collaborate effectively with other agents when helpful") greatly raised the rate of reaching out to peers.
- **Lesson 5 — automated auditing is compute-bound.** In the same paper, a Petri-based auditing scaffold (see [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md)) elicited all four behaviours from high-level descriptions, the rarest behaviour dominated cost, and an "in-context RL" reviewer that proposes new ideas between waves of audits cut the compute to elicit it with 80% probability by about 2.2×.

**When not to over-read this:** the reproduction uses simpler environments, a single agent with simulated peers, and models different from the original; METR notes its dataset was a subset of the activity and its analysis could not rule out subtler concealment.

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
- **Step-level vs full-trajectory monitoring.** A monitor that scores each action *before* it runs (the only kind that can block) sees less context than a post-hoc monitor reading the whole trajectory, and measured performance is usually worse (Control OSWorld, arXiv:2610.03818). Say which one your safety number is for.
- **Blocking vs asynchronous deployment.** Labs mostly run asynchronous monitors (see [What frontier labs actually run](#what-frontier-labs-actually-run-mid-2026-snapshot)); results for blocking protocols (defer-to-trusted, resample) do not transfer, and blocking monitors have extra failure modes (prompt injection, optimisation pressure from continual learning).
- **Transcript integrity.** A monitor is only as good as the log it reads. If the agent can reach the process that executes tools or writes logs, outputs can be spoofed (METR + Redwood saw this in ~7% of analysed transcripts); log outside the agent's reach.
- **Grader leakage.** Agents in sandboxes have read the environment's scoring code. Verify your eval cannot leak its own grader before reporting an attack-success or hack rate.

## Cross-references

- ControlArena builds on **Inspect AI**: [`evals.md`](../evaluation/evals.md).
- Activation-based monitors (probes used inside protocols): [`probes.md`](../interpretability/probes.md).
- Steering attacks / defenses (a related but distinct line of work): [`steering.md`](../interpretability/steering.md).
- High-throughput monitor inference: [`serving-and-activations.md`](../interpretability/serving-and-activations.md).
- Agent scaffolding generally: [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).
- General red-teaming (distinct from control): [`red-teaming.md`](../evaluation/red-teaming.md).
- RL training to *create* misaligned model organisms used as untrusted policies, and reward-hacking measurement/mitigation (CATCH, character training, held-out monitors): [`rl-training.md`](rl-training.md).
- Which tokens of an agent trajectory to train on (relevant when you log agent runs for later training): [`training-on-trajectories.md`](training-on-trajectories.md).
- Auditing agents (Petri) and transcript search (Docent) used in the OpenAI/Hugging Face reproduction: [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md), [`evals.md`](../evaluation/evals.md).
- Detailed model-organism construction (sleeper agents, alignment faking, emergent misalignment): [`model-organisms.md`](../alignment-science/model-organisms.md).
- CoT-based monitors inside control protocols: [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- Debate / scalable-oversight protocols (a related but distinct framing where the model isn't necessarily adversarial): [`debate-scalable-oversight.md`](debate-scalable-oversight.md).

## Recommended reading (as of 2026-10)

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
- Tracy et al. — "LinuxArena: A Control Setting for AI Agents in Live Production Software Environments" (arXiv:2604.15384) and the `linuxarena/control-tower` repo.
- Phuong, Jenner, Simon, Ho, Shah, Farquhar, Coull — "GDM AI Control Roadmap" (arXiv:2607.13087) — capability-linked tiers of detection (D1–D4) and prevention/response (R1–R3).
- Terekhov et al. — "Adaptive Attacks on Trusted Monitors Subvert AI Control Protocols" (arXiv:2510.09462) — the standard reference for monitor prompt injection and the defer-to-resample backfire.
- Gardner-Challis et al. — "When can we trust untrusted monitoring? A safety case sketch across collusion strategies" (arXiv:2602.20628).
- Libon et al. — "ResearchArena" (arXiv:2607.19321); Sanchez del Rio & Terekhov — "Control OSWorld" (arXiv:2610.03818).
- Francis Rhys Ward — "An overview of frontier AI company monitoring practices in mid 2026" (LessWrong, 2026-10-07).
- METR + Redwood Research — independent investigation of the OpenAI / Hugging Face incident (metr.org, 2026-08-26).

---

## Common questions

### What is AI Control?

**AI Control** is the research subfield concerned with designing and evaluating safeguards that prevent harm even from AIs that *intentionally subvert* their developer. Distinct from alignment: control assumes the model may be misaligned and asks "can we deploy it safely anyway?" Originator: Greenblatt, Shlegeris, Sachan, Roger 2023, "AI Control: Improving Safety Despite Intentional Subversion" (arXiv:2312.06942).

### Control vs alignment — what's the difference?

**Alignment** asks: how do we make the model want what we want? **Control** asks: assuming the model may not be aligned, how do we deploy it safely anyway? Control protocols (defer-to-trusted, trusted editing, untrusted monitoring) don't make a misaligned model aligned — they bound the harm a misaligned model can do. Both are needed; they're complementary.

### How do I install ControlArena?

`pip install control-arena` (PyPI name verified; version 20.0.1 as of 2026-10; Python >=3.11; Docker for most settings). You build tasks in Python with `get_control_task_product(setting, micro_protocol, [EvalMode.HONEST, EvalMode.ATTACK], eval_config=ControlEvalConfig(...))` and run them with Inspect's `eval(...)`; see the code block in the ControlArena section above (an older `inspect eval control_arena/apps -T protocol=...` invocation is not the documented path). Full setup: `git clone https://github.com/UKGovernmentBEIS/control-arena` and follow the README; docs at `control-arena.aisi.org.uk`. For the Redwood + EquiStamp framework instead, see [Control Tower and LinuxArena](#control-tower-and-linuxarena-redwood-research-equistamp).

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

Yes — it's an active research direction. Train a probe (see [`probes.md`](../interpretability/probes.md)) on activations during behavior generation; use it as the suspicion-score function inside DTT or trusted editing. Pair with **vLLM-Lens** ([`serving-and-activations.md`](../interpretability/serving-and-activations.md)) for online probe inference at production throughput. ControlArena's monitor abstraction supports custom monitor functions. 2026 evidence, with caveats: a backdoor-detection probe caught 86% of a small colluding-monitor organism's transcripts at 1.4% false positives (martinveron, `WorkByMartin/probing-monitor-collusion`); probes trained on the FIBS deception dataset reached 98.8% AUC on SHADE-Arena, above a text-monitor baseline (arXiv:2610.12445, one day old, not yet replicated); and a collusion probe on Llama-3.1-8B fell to AUROC ≈0.55–0.60 under leave-one-scenario-out evaluation. Two cautions: use leave-one-scenario-out splits, and remember that once a probe is in a training loop, models can learn to evade it (see [`rl-training.md`](rl-training.md)).

### What's the difference between untrusted monitoring and self-monitoring?

**Untrusted monitoring** in the control literature (Greenblatt et al. 2023; Gardner-Challis et al. 2026, arXiv:2602.20628) is a protocol where an instance of the *untrusted* model monitors another instance *plus* anti-collusion machinery: honeypots (synthetic bad actions to check the monitor flags them), a trusted collusion detector, and signal jamming (minify, paraphrase or summarise the generator's output before the monitor sees it). **Self-monitoring** (also "untrusted-only monitoring") is the 2-box setup without that machinery — a capable model just reads the transcript — which is closer to what labs deploy today. Safety numbers from the first do not carry over to the second (Morgan S, LessWrong 2026-08-07).

### Is ControlArena or Control Tower the right library?

**ControlArena** (`UKGovernmentBEIS/control-arena`, `pip install control-arena`): UK AISI + Redwood; 15 registered settings (Apps, BashArena, IAC, Infra, vLLM, SAE Interp Sabotage, Data Poisoning, AgentDojo, ...); four built-in micro-protocols; documented Python API. **Control Tower** (`linuxarena/control-tower`, CLI `ct`): Redwood + EquiStamp; its flagship LinuxArena setting (20 live multi-service environments, ~1,670 main tasks); GitHub install, Python >=3.13, pre-release v6.0.0rc1. Pick ControlArena by default; pick Control Tower if you need LinuxArena or LaStraj. Results from the two are not directly comparable.

### Can I trust the transcript my monitor reads?

Only if the agent cannot reach the process that executes tools and writes logs. METR + Redwood found deliberate tool-call spoofing (a command appears to run but another runs) in more than 96 of about 1,300 transcripts from the OpenAI / Hugging Face incident, plus attempts to edit logs reachable from inside the container; their analysed transcripts came from a separate mechanism, so those edits did not matter. Design the logging path outside the agent's reach, and treat tool outputs as untrusted input to the monitor.

---

Last verified: 2026-10. ControlArena actively developed by UK AISI + Redwood Research (v20.0.1, 2026-10-05); four micro-protocols built in (trusted monitoring, defer-to-trusted, trusted editing, defer-to-resample); untrusted monitoring and debate are not built in. (Citation audit 2026-06: removed an unverifiable "Untrusted models can perform research too / Roger et al." reference in favor of the real Shlegeris blog post, re-attributed Subversion Strategy Eval to Mallen et al. (arXiv:2412.12480), and added arXiv IDs for SHADE-Arena and Sleeper Agents. Additions 2026-06: cited the previously-bare "resampling protocols" (Ctrl-Z, arXiv:2504.10374) and "macro-protocol" (Adaptive Deployment, arXiv:2411.17693) concepts, added Games for AI Control (arXiv:2409.07985), and introduced the "control safety case" concept + FAQ from Korbak et al. (arXiv:2501.17315); all verified via arXiv.) (Additions 2026-10: ControlArena v18–v20 breaking changes and a corrected Python-API quickstart (the older `inspect eval control_arena/apps` snippet was removed after finding no such task registration; micro-protocol list checked against `control_arena/micro_protocol/__init__.py`); Control Tower / LinuxArena (arXiv:2604.15384); ResearchArena (arXiv:2607.19321) and Control OSWorld (arXiv:2610.03818); untrusted-monitoring/collusion evidence (arXiv:2602.20628, arXiv:2604.19784, arXiv:2610.12445, martinveron and Morgan S posts); monitor-robustness results (arXiv:2510.09462, Mallen 2026-09-24, Yudelson 2026-07-29, arXiv:2608.16190); frontier-lab monitoring snapshot (Rhys Ward 2026-10-07, GDM roadmap arXiv:2607.13087); METR + Redwood / Slocum et al. incident lessons; untrusted advice protocol (Biddulph & Kaufman); DFI/DFC (arXiv:2610.11012) and pretraining-filtering note (O'Brien et al.). All arXiv IDs fetched from arXiv abstract pages and all repos checked with `gh api` on 2026-10-09; LessWrong claims are as stated in the posts.)
