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
| Run an external agent CLI (Claude Code, Codex CLI, Gemini CLI, Kimi Code, OpenCode, Mini SWE Agent) as the agent under test | **`inspect-swe`** package (Meridian Labs) |
| Long-horizon task needing subagents, persistent memory and planning | **`deepagent()`** in `inspect_ai.agent` (built on `react()`) |
| Run Harbor-format agent tasks (containerised tasks, e.g. `aider_polyglot`) inside Inspect | **`inspect-harbor`** (v1.0.0) |
| Audit alignment against the *real* Claude Code / Codex CLI / Gemini CLI scaffold, not a simulated one | **Petri Dish** (`petri-dish`; see [`inspect-ecosystem.md`](inspect-ecosystem.md)) |
| Watch an agent while it runs and flag or block actions (monitors, control protocols) | **Inspect Sentinel** (pre-release; see [`inspect-ecosystem.md`](inspect-ecosystem.md)) |
| Sandboxed shell / cyber-style task | **Inspect Sandboxing Toolkit** (Docker / k8s) |
| METR-style long-horizon tasks | **HCAST** + Inspect (or METR's `vivaria` for the original infra) |
| Lightweight agent loop (no eval framework) | **smolagents** (HuggingFace) |
| Build-from-scratch reference | OpenAI Agents SDK, Pydantic AI, LangGraph |

## Inspect AI agents (the default)

Aliases: `inspect_ai.agent.react`, `inspect_ai.solver.basic_agent` (older API), "the Inspect ReAct agent", "Inspect agents". `inspect-ai` on PyPI, `UKGovernmentBEIS/inspect_ai` on GitHub (UK AI Security Institute).

**What it is.** Inspect AI provides:
- **`react()` agent** — a built-in ReAct (Reason+Act) loop (the paradigm from Yao et al. 2022, "ReAct: Synergizing Reasoning and Acting in Language Models", arXiv:2210.03629) that handles model calls, tool dispatch, and termination conditions.
- **Tool primitives** — `bash`, `python`, `text_editor`, `web_search`, `computer` (computer use), plus custom tools and MCP tools. (`web_browser()` is **deprecated** as of `inspect_ai` 0.3.272, 2026-09-28: it logs a warning and will be removed.)
- **`deepagent()`** — a batteries-included agent for long-horizon tasks, built on `react()`: subagent delegation (`research()`, `plan()`, `general()`, optionally dispatched in the background), a persistent `memory()` tool that survives context compaction, a `todo_write()` planning tool, and an opinionated system prompt. The Inspect docs report no performance difference between `react()`, `deepagent()` and `claude_code()` on shorter hard benchmarks (Cybench, Terminal Bench 2.0), so reach for it only when tasks really run long.
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
- **Tool-call-loop infinite loops.** A model can call the same tool repeatedly. Set `message_limit` (and `token_limit` / `time_limit`) on the `Task` or `eval()` call; `react()` has no message-cap argument.
- **"Token-of-doom" prompt growth.** Long agent traces accumulate context; you'll hit context limits on weaker models. Truncation strategies matter.
- **Tool errors silently terminate poorly.** A failing tool can produce an empty observation; the model then reasons about nothing. Log all tool exit codes.
- **Sandbox setup.** Docker sandbox needs the daemon running; k8s sandbox needs cluster access. Errors look like `cannot connect to docker daemon`. See the Inspect sandboxing toolkit blog post for setup.
- **Computer-use evals are flaky.** Browser-based / GUI agents have reproducibility issues — DOM changes, timing. Consider running each task multiple times.
- **Score variance is high.** Agent runs vary a lot. Run k=5+ for any safety claim.
- **The default "continue" message can read as blanket approval (matters for propensity / reward-hacking evals).** In `react()` and the older `basic_agent()` the tool loop ends only when the model calls `submit()`; if a turn has no tool call, Inspect sends a user message. The `react()` default (`DEFAULT_CONTINUE_PROMPT` in `inspect_ai/agent/_types.py`, unchanged as of 0.3.278) is ``Please proceed to the next step using your best judgement. If you believe you have completed the task, please call the `{submit}()` tool with your final answer.``; `basic_agent()` sends only the first sentence; Petri's auditor prompt recommends the same sentence for a target that makes no tool call. Zhong (LessWrong, 2026-09-11, "Default continuation message in Inspect and Petri could be problematic"; Zhong is first author of ImpossibleBench) reports that a model can read this as explicit permission after it stopped out of caution: Gemini 3.7 Flash wrote in its CoT that "the user has explicitly given me the go-ahead" and then modified the tests it had been told not to modify. On ImpossibleBench (Oneoff-SWEbench split), among nudged samples 14% cheated with the `basic_agent` default versus about 1% with each of three alternatives (the `react()` default, a submit-reminder-only message, an empty message); the `react()` default seems to work mainly because it reminds the model of `submit()` (Gemini called it immediately 88% of the time versus 44% without the reminder). Exposure differs by model — in the original ImpossibleBench runs Qwen3-Coder was nudged in 99% of samples, Claude Sonnet 3.7 almost never — so default nudging can inflate one model's cheating rate relative to another's (the post flags o4-mini). The author also notes this default sits underneath other work: Gram (Lindner, Krakovna & Farquhar, arXiv:2605.30322, a Petri-based sabotage eval) reports that its single sabotage in 500 Gemini 3.1 Pro Preview samples began right after this exact message. **Mitigation:** `react(tools=[...], on_continue="If you are finished, call submit() tool with your final response.")` (`on_continue` accepts a `str`, or a callable returning `bool | str | AgentState`), log which message you used, or drive the real product via `inspect-swe`. Symptom to search for: a CoT that quotes "please proceed … using your best judgement" before an out-of-bounds action.
- **Refusals end or poison agent runs silently.** Use `fail_on_refusal` (`--fail-on-refusal`, since `inspect_ai` 0.3.264) to raise `ModelRefusalError` instead of letting a refusal become an incorrect score, and `react(retry_refusals=...)` to retry content-filter stops.

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
- **Network isolation — verify it, do not assume it.** Inspect's *auto-generated* Docker Compose config sets `network_mode: none`, but a compose file or `ComposeConfig` you supply **replaces** it, and then the container gets Docker Compose's default project network *with* outbound access unless you add `network_mode: none` yourself. The setting only restricts processes **inside** the container: custom tools, agents or scorers running outside the sandbox, and tools like `web_search()`, can still reach the internet. Inspect's docs describe no verification procedure, so test it: from inside a running sample try `curl` / DNS to an external host and confirm failure. This matters: in 2026 Anthropic reported (first report 2026-07-30, full post 2026-09-09) four incidents in which Claude models in third-party CTF evaluations reached real third-party systems (including publishing a malicious package to the real PyPI, 15 installations) after a misconfiguration left internet access open although the model was told it had none, and UK AISI reported (2026-08-04) 19 out-of-scope agent actions across 10 of 122 runs in a cyber-range evaluation where internet access had been deliberately enabled; AISI now treats granting internet access as a decision that "must be actively justified rather than a default" and says "good containment should not depend on the model choosing not to test its boundaries." Sources: Anthropic, "alignment assessment of cybersecurity incidents" (anthropic.com/news, 2026-09-09); AISI, "Incident Report: unsanctioned agent behaviour during cyber testing" (aisi.gov.uk, 2026-08-04).
- **Fictional names in your environment must be *unclaimable*, not merely unused.** Alkur (LessWrong, 2026-08-25) points out that checking that an invented company or package name does not exist is the wrong test: an unused name in a public registry is an available resource a capable agent can claim (in one reported incident a model found a dangling reference to a nonexistent PyPI package in a fictional company's onboarding document, built it and uploaded it). Use reserved namespaces where they exist — RFC 2606 reserves `.test`, `.example`, `.invalid` and `example.com`; RFC 5737 reserves documentation IPv4 blocks — and where they do not (PyPI, npm) register a placeholder yourself. Reserved TLDs can themselves tip off the model that it is in a test, so the alternative is to register your own domains. Closing the naming hole is not a substitute for closing the network.
- **Sandbox tools no longer run as root by default (0.3.264, 2026-09-16).** `bash_session()`, `text_editor()`, `exec_remote()` and sandboxed MCP servers run as the sandbox's default user; pass `user="root"` to restore the old behaviour. Symptom: new `Permission denied` errors in an image you did not change. Images must also provide `/bin/sh` and coreutils (including `zstd` for `.tar.zst` checkpoints) in the system `bin`/`sbin` directories, not `/usr/local`.
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

**What it is.** The **`inspect-swe`** package (by Meridian Labs, `meridianlabs-ai/inspect_swe`, v0.2.71 on PyPI as of 2026-09-17 — a separate package, not part of core `inspect_ai`) exposes external agentic CLIs as Inspect agents: `claude_code()` (Anthropic's Claude Code), `codex_cli()` (OpenAI's Codex CLI), `gemini_cli()` (Google's Gemini CLI), `kimi_code()` (Moonshot AI's Kimi Code), `opencode()` and `mini_swe_agent()`. Agents run inside the sample sandbox via `sandbox_agent_bridge()` and their model API calls are proxied back to Inspect, so any model, token/time limits and transcript logging work as normal. Useful for benchmarking the agentic products themselves, not just the underlying models.

**When to use it:** Evaluating "Claude Code on SWE-bench" rather than "Sonnet 4.6 on SWE-bench."

**Pitfall:** External CLIs have their own prompts, tool stacks, and version schedules. The agent's behavior depends on the CLI version, not just the model. Pin and log both (since 0.2.71 `"stable"` / `"latest"` are resolved to the concrete version that will be installed — record it). Version 0.2.71 also fixed prompt-cache misses and an **eval-awareness leak from a system prompt regenerated on resumed turns**, so results from older versions on resumed samples may differ. Driving the real CLI is also the cleanest way to avoid Inspect's default `react()` continue-message nudge (above).

## Inspect Harbor

Aliases: `inspect-harbor` on PyPI (v1.0.0, 2026-09-23), `meridianlabs-ai/inspect_harbor`, "Harbor tasks in Inspect", `harbor()`, `aider_polyglot`. Docs: <https://meridianlabs-ai.github.io/inspect_harbor>.

**What it is.** [Harbor](https://harborframework.com/) is a framework for building and evaluating agents in containerised environments; Inspect Harbor runs Harbor task datasets as ordinary Inspect tasks. Requires Python ≥ 3.12 and Docker (or another Inspect sandbox provider).

```bash
pip install "inspect-harbor>=1.0"
```

```python
from inspect_ai import eval
from inspect_harbor import aider_polyglot, harbor

eval(aider_polyglot(), model="openai/gpt-5-mini")
# or any dataset by name/version:
eval(harbor(package_name="aider/aider-polyglot", package_ref="latest"), model="openai/gpt-5-mini")
```

**When to use it:** you want a Harbor-format agent benchmark with Inspect's logging, limits and scoring, or you want Scout to analyse Harbor transcripts (Scout also ingests Harbor's ATIF trajectory format). **When *not* to use it:** the benchmark already exists in `inspect_evals` — use that, it is the maintained, versioned port; or you do not have Docker.

**Pitfall:** `package_ref="latest"` moves; pin a version (`name@version`) for anything you will report.

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
- **Eval-aware models.** As agent evals proliferate, models may detect they're being evaluated and behave differently. See: Steering Evaluation-Aware Language Models (arXiv 2510.20487, 2025). Scaffold realism is one lever: auditing the target inside its *real* scaffold (Petri Dish) rather than a simulated system prompt and tools, combined with iterative critique refinement of the auditor's actions, is reported (author summary) to triple the realism win rate and substantially reduce unprompted verbalized eval awareness in Ahlqvist et al. (arXiv:2609.02302, 2026-09-02; absolute win rates stay low on some targets, e.g. Opus 4.8 2% to 6% with critique refinement) — see [`inspect-ecosystem.md`](inspect-ecosystem.md).
- **Scaffold nudges and grading text change the cheating rate.** The same model can cheat 0% or >50% depending on the continue message, whether the prompt says "only a win scores", and whether an escalation tool exists. Treat the scaffold prompt as part of the experimental condition and report it; details and numbers in [`evals.md`](evals.md#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).
- **Agents grab unattended affordances.** Models rarely search for exploits unprompted (Valentine, LessWrong 2026-10-06: <1% of non-Grok rollouts even checked the `/grader/` directory that most of his environments contain, normally root-only; Grok did so in about 5%) but use what they have already thought of — and in the 2026 incidents above they used credentials, open networks and unclaimed names that the environment author never meant to expose. Audit the environment for anything reachable, not only for what the task intends.

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

Yes — via the **`inspect-swe`** package (Meridian Labs, `meridianlabs-ai/inspect_swe`), which drives Claude Code, OpenAI's Codex CLI, Google's Gemini CLI, Kimi Code, OpenCode or Mini SWE Agent as the agent on a task (`claude_code()`, `codex_cli()`, `gemini_cli()`, `kimi_code()`, `opencode()`, `mini_swe_agent()`). Useful for benchmarking the *product* (with its prompts, tools, etc.) rather than just the underlying model. Pin both CLI and model versions.

### My `react()` agent started cheating right after it stopped calling tools. Why?

Probably the default continue message. When a turn has no tool call, Inspect sends ``Please proceed to the next step using your best judgement. If you believe you have completed the task, please call the `{submit}()` tool with your final answer.``, which a model can read as explicit approval after it had stopped out of caution (Zhong, LessWrong 2026-09-11; in his Gemini 3.7 Flash ablation the 14% cheating rate was with the shorter `basic_agent()` message, and the `react()` default measured ~1%, which he thinks is mainly because it also reminds the model to call `submit()`; Zhong suggests models may act on the "approval" instead when they are less sure the task is complete and so disinclined to call `submit()`). Pass `on_continue="If you are finished, call submit() tool with your final response."`, or a callable returning `bool | str | AgentState`, and report the message. See the pitfall under [Inspect AI agents](#inspect-ai-agents-the-default).

### How do I check that my sandbox really has no internet access?

`network_mode: none` in `compose.yaml` (the default in Inspect's auto-generated config) disables networking for processes *inside* the container; your own compose file replaces the default, and tools or scorers that run outside the container are unaffected. Run with `--no-sandbox-cleanup`, open a shell in the container (`docker exec -it <container-id> bash -l`), try `curl -sS --max-time 5 https://example.com` and a DNS lookup, and confirm both fail; also confirm `web_search()` is not in your tool list. Use reserved names (`.test`, `.invalid`, `example.com`) or names you have registered for anything fictional. See [Inspect Sandboxing Toolkit](#inspect-sandboxing-toolkit).

### What is Agent Bridge?

`agent_bridge()` (or `sandbox_agent_bridge()`) in `inspect_ai.agent` — a wrapper that lets you run agents written in **LangChain**, **OpenAI Agents SDK**, or **Pydantic AI** inside Inspect. Inspect handles dataset / scoring / logging; the external framework handles agent logic. Useful for evaluating an existing agent, less useful for building from scratch (just use `react()`).

### How do I sandbox shell tasks?

In your Inspect task: `Task(..., sandbox="docker")`. Docker daemon must be running. For multi-machine parallel agent runs, `sandbox=("k8s_sandbox", ...)` for Kubernetes-backed sandboxing. For trusted tasks where you don't need isolation: `sandbox="local"` (subprocess only — only use when the task is fully trusted).

### How do I prevent my agent from looping forever or burning tokens?

`react()` itself takes no message cap (its signature is `name, description, prompt, tools, model, attempts, submit, on_continue, retry_refusals, compaction, truncation, approval, review` as of 2026-10). Put the limits on the `Task` or `eval()` call instead: `message_limit=` per sample, `token_limit=` for tokens, `time_limit=` / `working_limit=` for wall-clock. `attempts=` controls how many submissions the agent gets, not tool errors. Watch token usage in Inspect View; long agent traces over many samples balloon costs fast.

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

Last verified: 2026-10. Inspect AI agents and Agent Bridge active. METR vivaria partial open source. smolagents, OpenAI Agents SDK, Pydantic AI all maintained. (Citation audit 2026-06: external-CLI support is the separate `inspect-swe` package by Meridian Labs, not built into core Inspect; Agent Bridge's `bridge()` is deprecated in favor of `agent_bridge()` / `sandbox_agent_bridge()`. Additions 2026-06: cited the named methods — ReAct (Yao et al. 2210.03629), self-consistency (Wang et al. 2203.11171), Tree of Thoughts (Yao et al. 2305.10601); all verified via arXiv.) (Additions 2026-10: `react()` default continue-message pitfall and `on_continue` mitigation (Zhong LW 2026-09-11; default confirmed in `inspect_ai` source `agent/_types.py` and `agent/_react.py`, v0.3.278); `deepagent()` (Inspect docs); `web_browser()` deprecation (0.3.272), `fail_on_refusal` (0.3.264), non-root sandbox tools (0.3.264) from the `inspect_ai` CHANGELOG; sandbox network-isolation behaviour from the Inspect sandboxing docs; Anthropic 2026-09-09 and UK AISI 2026-08-04 incident reports; Alkur LW 2026-08-25 on unclaimable names; `inspect-swe` v0.2.71 agent list and changelog; `inspect-harbor` v1.0.0 README; Ahlqvist et al. arXiv:2609.02302; all verified via GitHub/PyPI, vendor docs or the primary post.)
