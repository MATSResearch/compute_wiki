---
tags:
  - training
---

# Training on Agent Trajectories: What to Compute Loss On

An agent trajectory interleaves things the model produced (reasoning, tool
calls) with things the **environment** produced (stdout, stderr, exit codes,
file contents, stack traces). The question this doc answers: **which of those
tokens should contribute to the loss?**

The default answer and the interesting answer differ, and the gap matters if you
are collecting agent transcripts now and might train on them later.

## At a glance

| Situation | What to do |
|---|---|
| Standard supervised fine-tuning (SFT) on agent traces | **Mask** environment tokens; loss on assistant tokens only |
| On-policy RL where rollouts are cheap and mostly fail | Consider an **auxiliary loss on environment tokens** (ECHO) |
| You want the agent to anticipate consequences before acting | **World-model co-training** (PaW, Qwen-AgentWorld, Early Experience) |
| Naive next-observation prediction underperforms | **Agent-authored targets** (AAWM) — predict what the policy needs, not what the environment happened to emit |
| You are *capturing* trajectories for unknown future use | Keep observations **verbatim**, keep failures, and label every span by origin |

## The default: mask the environment

Standard practice in agent SFT is to compute loss **only on model-controllable
tokens** — the reasoning and the tool calls — while user turns and tool outputs
stay in the context as conditioning but are excluded from the objective.

Three reasons, all sound:

1. **Don't memorise deterministic outputs.** A model that learns to reproduce an
   interpreter's exact stdout has learned the interpreter, not the task, and
   will hallucinate plausible-looking outputs at inference.
2. **Credit assignment.** In policy-gradient training the mask should cover
   agent decisions, so the gradient is about what the agent chose, not what the
   environment happened to return.
3. **Don't reinforce failures.** Uniform token weighting propagates gradient
   through erroneous turns. Some setups go further and *error-mask*: zero the
   loss on turns that triggered a tool error.

If you are doing ordinary SFT on demonstrations, this is still the right
default. What follows is not a refutation of it — it applies mostly to **RL**,
where the trajectories are the model's own.

## The counter-current: the environment's output is free supervision

A 2026 line of work argues that in on-policy RL you are throwing away a dense
signal that is already sitting in every rollout.

### ECHO — predict the terminal's response

**ECHO: Terminal Agents Learn World Models for Free** (Shrivastava, Kauffmann,
Awadallah and Papailiopoulos, May 2026,
[arXiv:2605.24517](https://arxiv.org/abs/2605.24517)) is the sharpest version,
and it is about **terminal agents** — literally bash output.

The objective is a weighted sum:

- the usual **GRPO policy-gradient loss on action tokens**, plus
- a length-normalised **cross-entropy "environment loss" on environment
  observation tokens** — stdout, errors, files, logs, traces.

The properties that make it attractive: it **reuses the same forward pass** and
needs **no additional rollouts**, so it is close to free. And it converts
**failed rollouts** — normally discarded as uninformative when the reward is
zero — into training signal, because a failure still tells you what the
environment does.

Reported on TerminalBench-2.0: Qwen3-8B pass@1 2.70% → 5.17%, Qwen3-14B 5.17% →
10.79%, **matching expert-SFT-then-GRPO without using any demonstrations**, and
sharply reducing environment-token cross-entropy on held-out rollouts.

Their framing is the line worth remembering: environment observations are *"not
merely context for future actions, but a dense, on-policy supervision signal
already present in every rollout."*

⚠️ Caveats they state: results are on a single benchmark (TerminalBench-2.0),
and generalisation to unseen out-of-distribution tasks is variable.

### World-model co-training

Several groups arrive at the same place from the world-modelling direction —
train the policy to predict the next observation as an **auxiliary objective**,
so it internalises environment dynamics:

- **PaW: Policy and World Modeling Co-Training for Language Agents**
  ([arXiv:2606.02388](https://arxiv.org/abs/2606.02388)) — one model, on-policy
  RL, base objective augmented with a next-observation-prediction term from the
  rollout transitions.
- **Agent Learning via Early Experience**
  ([arXiv:2510.08558](https://arxiv.org/abs/2510.08558)) — implicit world
  modelling from the agent's *own* early experience. Because states are natural
  language, next-state prediction is just next-token prediction, so it needs no
  new machinery.
- **Qwen-AgentWorld: Language World Models for General Agents**
  ([arXiv:2606.24597](https://arxiv.org/abs/2606.24597)) — an RL warm-up on
  next-state prediction, so the agent learns to simulate what will happen before
  choosing what to do.

### The pushback: prediction is not decision-making

**Beyond Next-Observation Prediction: Agent-Authored World Modeling**
([arXiv:2606.25421](https://arxiv.org/abs/2606.25421)) argues naive
next-observation prediction is the wrong target, and the failure modes are worth
knowing before you adopt one of the above:

1. **Environment-driven targets.** You supervise whatever the transition
   happened to reveal, which may omit the dynamics relevant to the decision the
   policy actually faces.
2. **Sparse, distributed dynamics.** What matters may be implicit, or spread
   across earlier transitions, rather than present in the next observation.
3. **A real decision–prediction gap.** Optimising for goal-directed behaviour
   can *reduce* predictive accuracy; the two objectives genuinely differ.

Their alternative (AAWM) builds targets from the policy's own stated
uncertainties — the agent articulates confirmed patterns and open questions,
retrieves relevant transitions, and synthesises decision-oriented targets.
Reported up to +6.3 points on ALFWorld, the only world-modelling approach to
improve across every environment they tested, and higher response entropy during
RL, suggesting richer exploration rather than premature collapse.

## What this means if you are *collecting* trajectories

This is the practical part, and it applies whether or not you ever train on
observations: **every method above needs the environment's literal output, and
most captures throw it away.**

If you are logging agent sessions with any thought of future training:

- **Keep observations verbatim.** Raw stdout and stderr bytes, not
  pretty-printed, not summarised. A rendered or truncated observation is useless
  as a prediction target — the target *is* the literal token sequence.
- **Keep stderr and exit codes,** not just stdout. Errors are where the dynamics
  are most informative.
- **Keep the failures.** ECHO's central point is that failed rollouts carry
  signal. A capture pipeline that filters to successful runs has discarded the
  most valuable half.
- **Label every span by origin** — user / assistant reasoning / tool call /
  tool output. This is the single most important piece of metadata, because
  *every* option above, including the conservative default, requires knowing
  which tokens are which. A flat transcript with no origin labels cannot be
  masked correctly and so cannot be used either way.
- **Preserve turn boundaries and ordering,** so transitions
  (state → action → next state) can be reconstructed.
- **Note that truncation is lossy in a way that matters.** Capping a 200KB log
  is reasonable for display; if you also intend to train on it, record that the
  observation was truncated rather than silently shortening the target.

Redaction for privacy (names, API keys) is compatible with all of this — it
perturbs literal-token prediction slightly but preserves the structure. Dropping
observations entirely is not.

## Common questions

### Should I train on tool outputs in plain SFT on someone else's demonstrations?

Probably not. The mask-the-environment default exists for good reasons, and the
counter-current is about **on-policy** data where the trajectories are the
model's own. Off-policy demonstrations do not carry the same signal.

### Is this relevant to safety research specifically?

Two ways. First, a model trained to predict environment responses is being
trained toward a **world model** of its tools, which is worth reasoning about on
its own terms. Second, in **AI control** work the question of what an agent has
internalised about its environment — including its monitoring — is exactly the
thing you are trying to measure; see
[`ai-control.md`](ai-control.md).

### How do I know it worked?

ECHO reports environment-token cross-entropy on **held-out** rollouts, which is
the honest check: it measures whether the model has actually learned the
dynamics rather than memorised the training trajectories.

## Cross-references

- RL tooling and the GRPO workflow: [`rl-training.md`](rl-training.md).
- Agent scaffolds and running external CLIs as agents:
  [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).
- Scanning agent transcripts for problems before you train on them:
  [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md).

---

Last verified: 2026-08. Sources checked: ECHO (arXiv:2605.24517, Shrivastava,
Kauffmann, Awadallah, Papailiopoulos, 23 May 2026 — GRPO on action tokens plus
length-normalised cross-entropy on environment observation tokens, same forward
pass, TerminalBench-2.0 results as quoted); PaW (arXiv:2606.02388); Early
Experience (arXiv:2510.08558); Qwen-AgentWorld (arXiv:2606.24597); AAWM
(arXiv:2606.25421). The mask-the-environment default is stated as current
standard practice across agent-SFT work. Drafted by Claude; pending MATS
research-staff review.
