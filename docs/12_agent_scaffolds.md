# Agent Scaffolding for Capability and Safety Evals

Tooling for running language models as agents — multi-turn loops with tool use, memory, planning, sandboxed execution. This is what powers most current dangerous-capability evals (cyber, AI R&D, autonomous SWE, persuasion).

## At a glance

| You want… | Use |
|---|---|
| Standard agent eval, sandboxed, modern UX | **Inspect AI** built-in `react()` agent + tools |
| Use an external agent framework (LangChain, OpenAI Agents SDK, Pydantic AI) inside an eval | **Inspect Agent Bridge** |
| Run an external agent CLI (Claude Code, Codex CLI, Gemini CLI) as the agent under test | **Inspect** external-agent support |
| Sandboxed shell / cyber-style task | **Inspect Sandboxing Toolkit** (Docker / k8s) |
| METR-style long-horizon tasks | **HCAST** + Inspect (or METR's `vivaria` for the original infra) |
| Lightweight agent loop (no eval framework) | **smolagents** (HuggingFace) |
| Build-from-scratch reference | OpenAI Agents SDK, Pydantic AI, LangGraph |

## Inspect AI agents (the default)

Aliases: `inspect_ai.solver.basic_agent`, `inspect_ai.agent.react`, "the Inspect ReAct agent", "Inspect agents".

**What it is.** Inspect AI provides:
- **`react()` agent** — a built-in ReAct (Reason+Act) loop that handles model calls, tool dispatch, and termination conditions.
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

Aliases: "Agent Bridge", `inspect_ai.agent.bridge`.

**What it is.** A wrapper that lets you run agents written in **LangChain**, **OpenAI Agents SDK**, **Pydantic AI**, or other frameworks inside Inspect — Inspect handles dataset/scoring/logging, the external framework handles agent logic.

**When to use it:**
- You already have an agent built in another framework.
- You want to evaluate a specific agent product (someone's released LangChain agent, etc.).

**When *not* to use it:** Building from scratch — start with `react()` directly.

**Pitfall:** Tool definition formats differ across frameworks. Bridge mostly handles this but check that all tools register correctly.

## Inspect external agent CLIs

Aliases: "external agent", running Claude Code / Codex CLI / Gemini CLI as the model under test.

**What it is.** Inspect can drive external agentic CLIs (Anthropic's Claude Code, OpenAI's Codex CLI, Google's Gemini CLI) as the agent in an eval. Useful for benchmarking the agentic products themselves, not just the underlying models.

**When to use it:** Evaluating "Claude Code on SWE-bench" rather than "Sonnet 4.6 on SWE-bench."

**Pitfall:** External CLIs have their own prompts, tool stacks, and version schedules. The agent's behavior depends on the CLI version, not just the model. Pin and log both.

## METR HCAST and METR's vivaria

Aliases: `vivaria` (METR's eval infra), HCAST, `METR/hcast-public`, `METR/public-tasks`. See [`03_evals.md`](03_evals.md) for the dataset side.

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

- Underlying eval framework: [`03_evals.md`](03_evals.md).
- Datasets / benchmarks for agent capability: [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).
- Compute / sandboxing infrastructure: [`10_compute.md`](10_compute.md).
- Multi-provider API (for the underlying model calls): [`08_safety_toolkits.md`](08_safety_toolkits.md).
- AI Control protocols built on top of agent scaffolds (ControlArena, defer-to-trusted, etc.): [`13_ai_control.md`](13_ai_control.md).
- Debate / scalable-oversight protocols built on top of multi-agent primitives: [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md).

---

Last verified: 2026-04. Inspect AI agents and Agent Bridge active. METR vivaria partial open source. smolagents, OpenAI Agents SDK, Pydantic AI all maintained.
