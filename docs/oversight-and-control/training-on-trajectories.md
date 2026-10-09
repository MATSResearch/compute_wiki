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
| Standard supervised fine-tuning (SFT) on agent traces that is the *final* training stage | **Mask** environment tokens; loss on assistant tokens only |
| SFT on agent traces as a **warm start for RL** (GRPO) | Consider **ActObs**: also put loss on the observation tokens already in each trajectory (weight λ = 1) — a label-mask change, no extra data or forward passes (arXiv:2609.20715; one benchmark, two model sizes) |
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

If you are doing ordinary SFT on demonstrations as the *last* stage, this is
still the right default. What follows is not a refutation of it — it applies
mostly to **RL**, where the trajectories are the model's own, and (since
September 2026) to the **SFT stage that precedes RL**, where unmasking
observations has been shown to change how the later RL explores (ActObs, below).

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

### ActObs — unmask observations in the SFT stage that precedes RL

**Don't Mask the Environment: Observation Supervision Changes How Agents Explore
Under RL** (Zhang, Makhija, Arivazhagan, Kumar and Gangadharaiah,
[arXiv:2609.20715](https://arxiv.org/abs/2609.20715), 17 September 2026). The
method, **ActObs**, adds a next-token loss on the observation tokens that are
already in each SFT trajectory: loss = (sum of action-token NLL + λ × sum of
observation-token NLL) / (|actions| + λ|observations|), with λ = 1 by default
(λ = 0 recovers action-only SFT, "ActionSFT"; prompts stay masked). The paper
describes it as "only a label-mask change", with no new data, parameters or
forward passes. Observation-only training solves no tasks (0.0 pass@k at 8B),
so it complements action learning rather than replacing it.

- **Result.** The two SFT variants perform similarly after SFT but diverge
  after GRPO. On Terminal-Bench 2.0 (89 tasks, 16 attempts per task), Qwen3-4B
  after GRPO from ActObs had higher pass@k than from ActionSFT at every budget
  tested (pass@1 7.2 vs 5.6; pass@16 19.1 vs 18.0). Qwen3-8B traded a little
  pass@1 (11.0 vs 12.3) for higher pass@16 (27.0 vs 23.6). On aider-polyglot,
  which was unseen in SFT and RL, the 4B model gained 4.2 points of pass@1.
- **Mechanism (their analysis).** Action and observation gradients start
  aligned but quickly become nearly orthogonal; action-only SFT leaves a large
  residual observation gradient and drives environment-prediction accuracy
  *below the base model*. ActObs keeps more entropy during RL and moves the
  policy less. Raising the action-only policy's sampling temperature to match
  entropy did not close the pass@16 gap.
- **Relation to ECHO.** ECHO adds a weight-0.05 next-observation loss during
  GRPO on the policy's own rollouts; the two can be combined (ActObs → ECHO),
  with mixed results across model sizes and budgets.
- **Caveats.** Terminal agents only (Terminal-Bench 2.0 plus an aider-polyglot
  transfer check), Qwen3-4B and 8B only, and many gaps are small relative to
  the bootstrap standard errors the authors report (roughly 0.5–1.5 points; the
  4B pass@16 gap is 1.1 points). The authors say code, data and per-task
  results will be released upon acceptance — no repository was found (2026-10), so this is
  not yet reproducible from the paper alone.

**When to use it:** you are building an SFT warm start for agentic RL on
terminal or coding tasks and have trajectories that contain real tool output.
**When *not* to use it:** the SFT is the final stage (the model will be deployed
as an imitator — keep masking, or it learns to hallucinate plausible tool
output), the observations are huge or noisy logs you would not want to spend
loss on, or you cannot keep observations verbatim (see the capture advice below).

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

## Tooling that captures token-exact trajectories (2026)

Every method above needs the exact token ids the model saw and produced, with
each span labelled by origin. Several 2026 releases handle this for you; check
what yours does before logging text and re-tokenising later.

- **TRL `AsyncGRPOTrainer`, loop-owning path** (TRL v1.10.0, 2026-08-13;
  experimental). For external agents that run their own tool loop (e.g.
  `opencode`), the agent runs in an OpenEnv session in `transparent_proxy`
  mode; an in-sandbox proxy captures each turn's token ids and logprobs, and
  TRL rebuilds per-turn training rows from the trace and scores the workspace
  with the session's `verify()`.
- **verl "Continuous Token"** (verl v0.9.0, 2026-08-14; disabled by default).
  A reusable builder layer that keeps token continuity across assistant
  output, tool/environment feedback and the next generation prompt for
  multi-turn agentic rollouts, with Qwen, MiniMax and GLM boundary handling.
- **Agent Lightning v1.0** (arXiv:2608.17528; `agentlightning` on PyPI) routes
  an arbitrary agent harness through an LLM-endpoint proxy and lists
  retokenisation, sample merging, advantage calculation and loss normalisation
  as the hard parts of training on a harness's own request–response pairs.
- **Per-model turn terminators.** Tinker Cookbook v0.5.7 (2026-09-03) is a
  one-line fix titled "Make GLM-5.3 train the turn terminator on every
  assistant turn": whether the end-of-turn token is inside the loss mask is
  model-specific, and getting it wrong shows up as a model that never stops or
  stops early. Use the library's renderer for the model rather than a
  hand-written chat template. Symptom to search for: a fine-tuned agent that
  keeps generating after its final action.

## Common questions

### Should I train on tool outputs in plain SFT on someone else's demonstrations?

Probably not, if that SFT is the final stage. The mask-the-environment default
exists for good reasons (don't memorise tool output, don't reinforce failures),
and the ECHO-style counter-current is about **on-policy** RL data. The one
exception with evidence is when the SFT is a *warm start for RL*: ActObs
(arXiv:2609.20715) found that also supervising observation tokens during SFT
improved pass@k after GRPO on terminal tasks (small models, one benchmark; see
above). Off-policy demonstrations on their own do not carry the same signal as
on-policy rollouts.

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

Last verified: 2026-10. Sources checked: ECHO (arXiv:2605.24517, Shrivastava,
Kauffmann, Awadallah, Papailiopoulos, 23 May 2026 — GRPO on action tokens plus
length-normalised cross-entropy on environment observation tokens, same forward
pass, TerminalBench-2.0 results as quoted); PaW (arXiv:2606.02388); Early
Experience (arXiv:2510.08558); Qwen-AgentWorld (arXiv:2606.24597); AAWM
(arXiv:2606.25421). The mask-the-environment default is stated as current
standard practice across agent-SFT work. Drafted by Claude; pending MATS
research-staff review.
Additions 2026-10: ActObs (arXiv:2609.20715, Zhang et al., 17 Sep 2026 —
fetched from the arXiv abstract page and the HTML full text; numbers quoted
from its Table 1; code not yet released per the paper), tooling notes from the
TRL v1.10.0, verl v0.9.0 and Tinker Cookbook v0.5.7 release notes and Agent
Lightning v1.0 (arXiv:2608.17528), checked 2026-10-09.
