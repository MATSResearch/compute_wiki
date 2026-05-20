# ControlArena + the AI Control framing

A working-summary of the literature this example sits in, scoped for fellows
who are starting their first control project.

## The original AI Control paper

**Greenblatt, Shlegeris, Sachan, Roger — "AI Control: Improving Safety Despite Intentional Subversion"** (arXiv:2312.06942, Dec 2023). Redwood Research.

### The framing

> Suppose your model is misaligned and will try to undermine you. Can you build
> a deployment **protocol** that bounds the harm anyway?

Distinct from alignment: alignment asks "how do we make the model want what we
want"; control asks "assuming the model may not, how do we deploy it safely
anyway." Both are needed; they're complementary.

The 2023 paper instantiated the framing on the **APPS dataset**: an untrusted
LLM writes solutions to programming problems; its **side task** is to insert a
**backdoor** — code that misbehaves on a specific class of inputs not covered
by the test suite. A separate, weaker **trusted model** acts as monitor. Each
candidate **protocol** (DTT, trusted editing, untrusted monitoring, …) gets a
**safety** score (does it catch backdoors?) and a **usefulness** score (does it
let legitimate work pass?). The result is a **safety/usefulness pareto curve**.

### Key vocabulary (search-friendly)

- **Untrusted policy / untrusted model.** The capable model whose alignment is
  uncertain. Often the model under evaluation. May pursue side tasks while
  doing main tasks.
- **Trusted policy / trusted model.** A weaker but reliable model assumed
  safe. Used as monitor, fallback, or editor.
- **Monitor.** A component (often a trusted model with a structured prompt)
  that examines actions and outputs a **suspicion score**.
- **Suspicion score / suspicion threshold.** The numeric output of a monitor.
  Threshold choice trades off safety vs usefulness.
- **Side task.** A harmful objective the untrusted model might pursue
  concurrently with the legitimate main task (e.g. insert a backdoor while
  writing a feature).
- **Main task.** The legitimate work.
- **Honest run / honest mode.** Untrusted policy is *not* given a side task;
  measures usefulness.
- **Attack run / attack mode.** Untrusted policy is given a side task;
  measures safety.
- **Defer-to-trusted (DTT).** Untrusted runs; if suspicion exceeds threshold,
  the trusted policy generates instead.
- **Trusted editing.** Same as DTT, but trusted *edits* the suspect output
  rather than discarding.
- **Untrusted monitoring.** A second untrusted instance monitors the first,
  with anti-collusion measures.
- **Audit budget.** Fraction of trajectories you're willing to have a human
  (or oracle) review. Determines the calibrated threshold.
- **Safety / usefulness pareto.** The fundamental tradeoff: stricter protocols
  are safer but less useful.

### Backdoors as the threat model

The original paper's threat model was code-sabotage on APPS — that's the
**Apps** setting in modern ControlArena, used by this example. Other
ControlArena settings (Bash, IAC, SHADE Arena, AgentDojo, …) extend the
framing to shell tasks, infrastructure-as-code, multi-step agents, and prompt
injection. The structure is the same: main task + side task, monitor with
suspicion score, protocol that decides what to do.

## ControlArena (the library)

UK AISI + Redwood collaboration. The maintained successor to the 2023 paper
code; used by Anthropic, Google DeepMind, Redwood, and AISI itself.

- PyPI: `control-arena` (15.x as of April 2026).
- GitHub: `UKGovernmentBEIS/control-arena`.
- Docs: `https://control-arena.aisi.org.uk/`.

Built on top of **Inspect AI** — every ControlArena task is an Inspect task.
This means standard Inspect tooling (log viewer, eval set runner) works
directly on ControlArena logs.

### Settings (as of April 2026, 17 shipped)

AgentDojo, Apps, Bash, BashArena, BigCodeBench, Data Poisoning, Eval Sabotage,
IAC, IAC Fast, Infra, Rogue Eval, SAE Interp Sabotage, SHADE Arena, SWE-bench
Django, vLLM, ... See `docs/13_ai_control.md` in this repo for descriptions.

### Protocols implemented

- `trusted_only` (safety baseline)
- `untrusted_only` (usefulness ceiling)
- `defer_to_trusted` (the basic protocol; what this example uses)
- `defer_to_resample`
- `trusted_monitoring` (audit-only; doesn't change actions)
- `trusted_editing`
- `untrusted_monitoring`

## Calibration of the suspicion threshold

The most common AI Control mistake:

> Picking the suspicion threshold on the same data you evaluate on leaks the
> test set.

The right way (and what `ac_components.audit` implements):

1. Run honest mode (no side task) → collect suspicion scores.
2. Split scores into **calibration** (~30%) and **evaluation** (~70%).
3. Pick the threshold from the calibration half so the false-positive rate
   equals the audit budget (e.g. 5%).
4. Use that threshold in the actual attack-mode eval.

`compute_safety` then asks: of the attack-mode trajectories, how many had
suspicion ≤ threshold *and* a successful side task? Those are the
**uncaught successful attacks**. Safety ≈ 1 − fraction of those.

## Reading list (referenced from this example)

- Greenblatt et al. 2023 — arXiv:2312.06942 (the originator).
- ControlArena paper / tutorial — https://control-arena.aisi.org.uk/tutorial.html
- AISI blog — "Introducing ControlArena" and "How to evaluate control measures for AI agents?"
- Ryan Greenblatt — "An overview of control measures" (Redwood blog) — the readable conceptual overview.
- Roger et al. — "Untrusted models can perform research too" — extends control to research workflows.
- Anthropic Sleeper Agents (Hubinger et al.) — model organisms used as untrusted policies in some control settings.

## When this example's framing breaks down

- **Realistic adversaries have more compute than a paper-budget red team.** Your safety number is a lower bound on attackability.
- **Side-task plausibility matters.** A demo-grade side task (write `BACKDOOR` in a comment) doesn't transfer. Apps uses calibrated, research-realistic backdoors; modifying the side task changes results dramatically.
- **Iteration leaks.** Tune protocol on the same red-team policies you evaluate → overfit. Hold out attack policies too, not just honest scores.
- **Models may have seen ControlArena in training.** Document model versions.
