---
tags:
  - evaluation
  - oversight
---

# Agent Scaffolding for Capability and Safety Evals

Tooling for running language models as agents — multi-turn loops with tool use, memory, planning, sandboxed execution. This is what powers most current dangerous-capability evals (cyber, AI R&D, autonomous SWE, persuasion).

## At a glance

| You want… | Use |
|---|---|
| Standard agent eval, sandboxed, modern UX | **Inspect AI** built-in `react()` agent + tools |
| Use an external agent framework (LangChain, OpenAI Agents SDK, Pydantic AI) inside an eval | **Inspect Agent Bridge** |
| Run an external agent CLI (Claude Code, Codex CLI, Gemini CLI) as the agent under test | **`inspect-swe`** package (Meridian Labs) |
| Sandboxed shell / cyber-style task | **Inspect Sandboxing Toolkit** (Docker / k8s) |
| METR-style long-horizon tasks | **HCAST** + Inspect (or METR's `vivaria` for the original infra) |
| Lightweight agent loop (no eval framework) | **smolagents** (HuggingFace) |
| Build-from-scratch reference | OpenAI Agents SDK, Pydantic AI, LangGraph |

## Inspect AI agents (the default)

Aliases: `inspect_ai.agent.react`, `inspect_ai.solver.basic_agent` (older API), "the Inspect ReAct agent", "Inspect agents". `inspect-ai` on PyPI, `UKGovernmentBEIS/inspect_ai` on GitHub (UK AI Security Institute).

**What it is.** Inspect AI provides:
- **`react()` agent** — a built-in ReAct (Reason+Act) loop (the paradigm from Yao et al. 2022, "ReAct: Synergizing Reasoning and Acting in Language Models", arXiv:2210.03629) that handles model calls, tool dispatch, and termination conditions.
- **Tool primitives** — `bash`, `python`, `text_editor`, `web_search`, `web_browser`, `computer` (computer use), plus custom tools and MCP tools.
- **Multi-agent primitives** — agents calling agents, or competing/cooperating agents.
- **Sandboxes** — separate the model's inference from the environment where tool calls execute.
- **Agent Bridge** — drop in agents written in LangChain / OpenAI Agents SDK / Pydantic AI with minimal glue.

**When to use it:**
- Almost any new agent eval in 2026.
- You want results comparable to other AISI / Anthropic / OpenAI / METR safety work — Inspect logs are the standard format.
- You need sandboxing for security-sensitive evals.

**When *not* to use it:**
- You're not running an eval — building a production agent is different territory (LangGraph, OpenAI Agents SDK, etc.).
- You want a pre-built "research" agent (deep research style) — Inspect's primitives are more eval-shaped.

**Pitfalls:**
- **Tool-call-loop infinite loops.** A model can call the same tool repeatedly. Set `max_messages` and / or termination conditions on the agent.
- **"Token-of-doom" prompt growth.** Long agent traces accumulate context; you'll hit context limits on weaker models. Truncation strategies matter.
- **Tool errors silently terminate poorly.** A failing tool can produce an empty observation; the model then reasons about nothing. Log all tool exit codes.
- **Sandbox setup.** Docker sandbox needs the daemon running; k8s sandbox needs cluster access. Errors look like `cannot connect to docker daemon`. See the Inspect sandboxing toolkit blog post for setup.
- **Computer-use evals are flaky.** Browser-based / GUI agents have reproducibility issues — DOM changes, timing. Consider running each task multiple times.
- **Score variance is high.** Agent runs vary a lot. Run k=5+ for any safety claim.

## Inspect Sandboxing Toolkit

Aliases: "Inspect sandboxing", `inspect_ai.util.sandbox`, `k8s_sandbox` package.

**What it is.** Inspect's sandboxing layer separates the model's inference from the environment where tool calls execute. Three flavors:
- **`docker`** — single-machine Docker.
- **`k8s_sandbox`** — Kubernetes-backed sandbox (scales to many parallel agents).
- **`local`** — direct subprocess (only for fully-trusted tasks).

**When to use it:**
- Cyber tasks (CTF challenges).
- Software engineering tasks (SWE-bench, HCAST coding).
- Any task where you'd be uncomfortable running model-generated code on your laptop.

**Pitfalls:**
- **`docker` sandbox needs Docker socket access** — on rented GPU boxes, you may need to install Docker first. On some sandboxed clouds (Modal, etc.), Docker-in-Docker doesn't work.
- **Network isolation.** By default, sandboxes have network access; for some safety evals (testing exfil resistance) you want to disable it. Configure in the task.
- **Cleanup.** Failed sandbox containers can accumulate. Periodic `docker system prune` on long-running boxes.
- **k8s sandbox needs cluster + RBAC.** Not lightweight — only worth it for parallel agent runs at scale.

## Inspect Agent Bridge

Aliases: "Agent Bridge", `inspect_ai.agent.agent_bridge()`, `inspect_ai.agent.sandbox_agent_bridge()`. (The older bare `bridge()` / `inspect_ai.agent.bridge` name is deprecated — use `agent_bridge()` for in-process or `sandbox_agent_bridge()` for sandboxed/any-language agents.)

**What it is.** A wrapper that lets you run agents written in **LangChain**, **OpenAI Agents SDK**, **Pydantic AI**, or other frameworks inside Inspect — Inspect handles dataset/scoring/logging, the external framework handles agent logic.

**When to use it:**
- You already have an agent built in another framework.
- You want to evaluate a specific agent product (someone's released LangChain agent, etc.).

**When *not* to use it:** Building from scratch — start with `react()` directly.

**Pitfall:** Tool definition formats differ across frameworks. Bridge mostly handles this but check that all tools register correctly.

## Inspect external agent CLIs

Aliases: "external agent", `inspect-swe`, `meridianlabs-ai/inspect_swe`, running Claude Code / Codex CLI / Gemini CLI as the model under test.

**What it is.** The **`inspect-swe`** package (by Meridian Labs, `meridianlabs-ai/inspect_swe` — a separate package, not part of core `inspect_ai`) exposes external agentic CLIs (Anthropic's Claude Code, OpenAI's Codex CLI, Google's Gemini CLI, Mini SWE Agent) as Inspect agents. Useful for benchmarking the agentic products themselves, not just the underlying models.

**When to use it:** Evaluating "Claude Code on SWE-bench" rather than "Sonnet 4.6 on SWE-bench."

**Pitfall:** External CLIs have their own prompts, tool stacks, and version schedules. The agent's behavior depends on the CLI version, not just the model. Pin and log both.

## METR HCAST and METR's vivaria

Aliases: `vivaria` (METR's eval infra), HCAST, `METR/hcast-public`, `METR/public-tasks`. See [`evals.md`](evals.md) for the dataset side.

**What it is.** METR's task suite plus their internal eval infrastructure (`vivaria`). Some of this has been open-sourced; tasks can be run via Inspect.

**When to use it:**
- Long-horizon agentic evals comparable to METR's published results.
- Time horizon measurement.

**When *not* to use it:** You don't need METR-comparability — `inspect_evals` has many simpler agent benchmarks.

**Pitfalls:**
- **HCAST tasks expect specific environments.** Porting to Inspect requires care; check `inspect_evals/hcast` (if it exists for your task) or the METR docs.
- **Compute cost.** Long-horizon tasks burn tokens and tool-call time. Single full-suite runs are expensive.

## smolagents

Aliases: `smolagents` on PyPI, `huggingface/smolagents`, "HF's small agent library".

**What it is.** A small, opinionated library from HuggingFace for building agents. Code-acting agents (the model writes Python and executes it) are a core feature. ~1000 lines.

**When to use it:**
- Quick prototype of a research agent that's not an eval.
- You want a minimal, readable agent loop to learn from.

**When *not* to use it:** You want eval logging, sandboxes, scoring — use Inspect.

## OpenAI Agents SDK

Aliases: `openai-agents` on PyPI, `openai/openai-agents-python`.

**What it is.** OpenAI's official agent framework — handoffs, guardrails, tracing.

**When to use it:** Building production-shaped agents on OpenAI; comparing your code to OpenAI's "official" patterns.

**When *not* to use it:** Eval research — Inspect.

## LangGraph / LangChain

For completeness: heavyweight in the broader LLM-app ecosystem. Used in production agent products. For safety research, Inspect is generally preferred for its eval-first design and standard log format.

**When to use them:** You have a production deployment, or are evaluating someone else's LangGraph agent.

## Pydantic AI

Aliases: `pydantic-ai` on PyPI.

**What it is.** Newer, type-driven agent framework from the Pydantic team.

**When to use it:** Production / library-development style agents with strong typing.

## Cross-cutting agent eval pitfalls

- **Agent reproducibility is harder than non-agent.** Tool errors, timing, sampling stochasticity, environment state. k=5+ runs minimum.
- **"Capability uplift" claims need careful baselines.** Did the model do better with the agent scaffold, or just with the extra context? Run baselines without tools.
- **Tool whitelisting.** Giving an agent shell access in an eval is a real attack surface. Sandbox properly. Don't run cyber-eval agents on a box with credentials.
- **Score what you mean.** "Did the agent solve the task" is not the same as "did the agent's actions cause the task state to be solved" (sometimes the env solves itself; sometimes the agent's tools claim success without it being true). Verify via final state, not via agent self-report.
- **Log the full transcript.** Token-level — every tool call, every observation, every model message. Inspect View does this; if you roll your own, replicate that level.
- **Context overflow degrades silently.** When the trace exceeds context, models start losing the original task. Log context length per turn; warn if approaching limit.
- **Prompt sensitivity.** Agent system prompts shift behavior dramatically. Note which scaffold prompt you used; share it.
- **Honesty: agents will sometimes lie to themselves in chain-of-thought.** Don't take CoT as ground truth for what the agent "knows" or "wants."
- **Eval-aware models.** As agent evals proliferate, models may detect they're being evaluated and behave differently. See: Steering Evaluation-Aware Language Models (arXiv 2510.20487, 2025).

## Cross-references

- Underlying eval framework: [`evals.md`](evals.md).
- Datasets / benchmarks for agent capability: [`datasets-benchmarks.md`](datasets-benchmarks.md).
- Compute / sandboxing infrastructure: [`compute.md`](../models-and-compute/compute.md).
- Multi-provider API (for the underlying model calls): [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).
- AI Control protocols built on top of agent scaffolds (ControlArena, defer-to-trusted, etc.): [`ai-control.md`](../oversight-and-control/ai-control.md).
- Debate / scalable-oversight protocols built on top of multi-agent primitives: [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

---

## Common questions

### How do I write an Inspect AI agent?

Use the built-in `react()` agent + tools:
```python
from inspect_ai.agent import react
from inspect_ai.tool import bash, python

agent = react(tools=[bash(timeout=180), python(timeout=180)])
# Plug agent into a Task as the solver.
```
The `react()` agent handles ReAct (Reason+Act) loops, tool dispatch, and termination. For more control, hand-roll a solver that calls `generate()` and dispatches tools manually.

### Can I evaluate Claude Code (or Codex CLI / Gemini CLI) inside Inspect?

Yes — via the **`inspect-swe`** package (Meridian Labs, `meridianlabs-ai/inspect_swe`), which drives Claude Code, OpenAI's Codex CLI, or Google's Gemini CLI as the agent on a task. Useful for benchmarking the *product* (with its prompts, tools, etc.) rather than just the underlying model. Pin both CLI and model versions.

### What is Agent Bridge?

`agent_bridge()` (or `sandbox_agent_bridge()`) in `inspect_ai.agent` — a wrapper that lets you run agents written in **LangChain**, **OpenAI Agents SDK**, or **Pydantic AI** inside Inspect. Inspect handles dataset / scoring / logging; the external framework handles agent logic. Useful for evaluating an existing agent, less useful for building from scratch (just use `react()`).

### How do I sandbox shell tasks?

In your Inspect task: `Task(..., sandbox="docker")`. Docker daemon must be running. For multi-machine parallel agent runs, `sandbox=("k8s_sandbox", ...)` for Kubernetes-backed sandboxing. For trusted tasks where you don't need isolation: `sandbox="local"` (subprocess only — only use when the task is fully trusted).

### How do I prevent my agent from looping forever or burning tokens?

Set termination conditions on `react()`: `max_messages=20` (or whatever cap fits the task), `message_limit` per sample, `time_limit` for wall-clock. Also: add a tool error budget (`max_attempts=N`). Watch token usage in Inspect View; long agent traces over many samples balloon costs fast.

### What's the difference between LangGraph and Inspect for agents?

**LangGraph** is for production agent products (long-running, deployable, lots of integrations). **Inspect AI** is for *evaluations* (sample-level transcripts, scoring, comparable logs across providers). For a paper or research result, Inspect; for shipping an agent, LangGraph (or OpenAI Agents SDK / Pydantic AI). Use Inspect's Agent Bridge if you have a LangGraph agent and want to evaluate it.

### My agent task always succeeds in suspicious ways

Score what you mean: "task state achieved" not "agent self-reported success." Some environments solve themselves; some tools claim success without it being true. Use a separate scorer that verifies the *final state* of the environment, not just the agent's last message.

### How do I score agents that take many turns?

Each Inspect `Sample` produces a full `TaskState` with all messages, tool calls, observations, and the final answer. A `Scorer` consumes this and produces a `Score`. Common patterns: pass/fail on final answer correctness; subgoal-completion checklists; LLM-as-judge over the entire trajectory; environment-state checks at end.

### What is test-time compute / inference-time scaling?

Techniques that improve performance at inference by spending more compute *per query*, without changing weights. Examples: **best-of-N** (sample N completions, pick the best by an external scorer); **self-consistency** (sample N CoT completions, take majority answer); **tree of thoughts** (search over branching CoT continuations); long reasoning traces (o-series, DeepSeek-R1 style). For evals, you can implement best-of-N as a custom Inspect solver that samples k times and uses a scorer to pick.

### What is best-of-N sampling?

Sample N completions for the same prompt, then pick the highest-scoring one according to a scorer (reward model, verifier, or LLM-as-judge). A simple test-time-compute technique. Trades inference cost for output quality; useful for capability evals where you want to measure "what the model can do given more attempts." Not useful for safety evals where you care about typical behavior — it artificially inflates capability and can hide failure modes.

### What is self-consistency for chain-of-thought?

Sample N CoT completions at temperature > 0; for each, extract the final answer; take majority vote (Wang et al. 2022, "Self-Consistency Improves Chain of Thought Reasoning in Language Models", arXiv:2203.11171). Often improves accuracy on math / reasoning tasks. **For safety evals**: be cautious — self-consistency masks the rate of incorrect or harmful completions; report both with-and-without numbers if the eval has safety implications.

### What is tree of thoughts (ToT)?

A search-based test-time technique (Yao et al. 2023, "Tree of Thoughts: Deliberate Problem Solving with Large Language Models", arXiv:2305.10601): instead of one linear CoT, generate multiple candidate next-steps at each reasoning step, score them, expand the best ones. A more expensive but sometimes more effective inference scaling than self-consistency. Implementation is bespoke; not standardized in any safety-research library.

---

Last verified: 2026-06. Inspect AI agents and Agent Bridge active. METR vivaria partial open source. smolagents, OpenAI Agents SDK, Pydantic AI all maintained. (Citation audit 2026-06: external-CLI support is the separate `inspect-swe` package by Meridian Labs, not built into core Inspect; Agent Bridge's `bridge()` is deprecated in favor of `agent_bridge()` / `sandbox_agent_bridge()`. Additions 2026-06: cited the named methods — ReAct (Yao et al. 2210.03629), self-consistency (Wang et al. 2203.11171), Tree of Thoughts (Yao et al. 2305.10601); all verified via arXiv.)
