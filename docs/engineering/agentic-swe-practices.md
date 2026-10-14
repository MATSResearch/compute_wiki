---
tags:
  - engineering
---

# Software Engineering with Coding Agents (the agentic coding era)

How to drive an AI coding agent — **Claude Code**, **OpenAI Codex / Codex CLI**, **Cursor**, **GitHub Copilot agent mode**, **Gemini CLI / Antigravity CLI**, **Aider**, **Devin**, **Cline** — so it produces *correct, reproducible* research code instead of plausible-looking slop. Written for MATS fellows who are strong scientists but not always career software engineers. The tools change monthly; the practices below change much more slowly, so the doc leads with practices and surveys tools last.

A coding agent is a Large Language Model (LLM) wrapped in a loop that can read files, run shell commands, edit code, and observe the results — repeatedly, without you in the loop on every step. That autonomy is exactly why discipline matters: an agent that can run `pytest` can also silence a failing test, and an agent that can `pip install` can install a package that does not exist.

## At a glance: "I want to X → do Y"

| I want to… | Do this |
|---|---|
| Stop the agent solving the wrong problem | Make it **plan first** (plan mode / write a `SPEC.md`), approve the plan, *then* let it code |
| Let it run unattended without going off the rails | Give it a **runnable check** (tests / lint / type-check / build) so "done" is verifiable, not vibes |
| Keep a long session sharp | `/clear` between unrelated tasks; offload file-reading to **subagents**; keep the instruction file lean |
| Keep a multi-hour agent run productive | **Hand off** at each milestone: a fresh agent in the same workspace, given its predecessor's written summary. See "Agent memory, handoffs and time" |
| Give an agent a time budget | Enforce it **outside** the agent and keep wall-clock timestamps in its context; agents over-predict their own runtime (about 3x and 7x on one 2026 benchmark, worse on successful runs) |
| Stop an agent's notes turning guesses into "decisions" | Tag claims with an epistemic status (`[decided]` / `[verified]` / `[concluded]` / `[assumed]`), and let only the human mark `[decided]` (EpistemicMemory conventions) |
| Install a skill or plugin someone else wrote | **Read it, pin it, scan it**: `gh skill preview`, `gh skill install … --pin <tag or SHA>`, Cisco `skill-scanner`. See "Third-party skills and plugins: installing safely" |
| Stop the agent editing held-out data or the eval harness | A **hookify** `block` rule (or a deny rule) on the path, plus a `bash` rule, because shell writes are not `file` events. Real isolation means the data is not on the agent's filesystem |
| Guarantee something happens *every* time (e.g. run formatter after edits) | Use a **hook**, not a line in `CLAUDE.md` (instruction files are advisory; hooks are deterministic). For a hook that *guards* something, set `onFailure: "block"` so a crash or timeout blocks the action instead of letting it through (Claude Code 2.1.295+) |
| Run with fewer permission prompts without `--dangerously-skip-permissions` | **Auto mode** (classifier-reviewed actions; the default starting mode in Claude Code 2.1.283+ per the docs; the changelog puts "every plan and provider" at 2.1.284) plus explicit **deny rules** for anything that must never happen — and a container for untrusted or adversarial work. See "Permission modes" below |
| Run a training job or eval that takes hours | Start it yourself in `tmux` / `slurm` / `nohup` and have the agent poll the log. Claude Code stops background Bash commands at a time limit (default 30 min, max 2 h) |
| Avoid shipping plausible-but-wrong code | **Small diffs, read every line**, fresh-context adversarial review |
| Avoid a fake-green test suite | Write the failing test *yourself* first; never let the agent author both the code and its only oracle |
| Avoid a supply-chain footgun | **Verify and pin every dependency** the agent adds — hallucinated package names are a real attack surface |
| Stop secrets leaking | Keep keys in `.env`, gitignore it, deny the agent read access to it, scan diffs before commit |
| Keep research reproducible | Run-dir + `metadata.json` + pinned seeds + pinned deps; make the agent log evidence, not assertions |
| Pick a coding agent today | See the tool table at the bottom — but the workflow matters far more than the tool |

## The core loop: Plan → Act → Verify

This is the single highest-leverage idea in the whole doc. Everything else is detail.

**Plan before acting.** Letting an agent jump straight to editing tends to produce code that solves the *wrong* problem confidently. Make it explore the relevant files and write a plan first — Claude Code calls this **plan mode** (read-only research, no edits until you approve); other tools have equivalents. Correcting a plan is cheap; correcting a finished, wrong codebase is expensive. The exception: trivial changes. If you could describe the diff in one sentence ("fix this typo", "rename this variable"), skip the ceremony and just ask.

**Spec-Driven Development (SDD).** For anything non-trivial, have the agent interview you, then write a self-contained `SPEC.md` that names the files and interfaces it will touch, states what is *out of scope*, and ends with an end-to-end verification step. Start a fresh session to implement against that spec. GitHub's open-source **Spec Kit** (`github/spec-kit`, the `specify` CLI, commands like `/speckit.specify → clarify → plan → tasks → implement`) packages this pattern and works across Claude Code, Copilot, Cursor, Codex, and Gemini. SDD's whole pitch is being the antidote to undisciplined "vibe coding."

**Verify before trusting.** An agent stops when the work *looks* done. Without a check it can run itself, "looks done" is the only signal it has — and then *you* are the verification loop. Give it a check (next section) and the loop closes on its own.

## Give the agent a runnable check (the feedback loop)

Coding agents work dramatically better than agents in most other domains for one reason: code gives **fast, cheap, deterministic, machine-readable feedback**. "5 tests failed, here are the stack traces" needs no human interpretation, so the agent can iterate dozens of times in seconds. Your job is to make sure that feedback exists and is *honest*.

- **Hand it a check it can execute:** a test command, a build that returns a non-zero exit code, a linter, a type-checker (`mypy`, `pyright`), a fixture diff, or for plots a saved-image comparison. For research code, the best checks are **shape and value assertions** — `assert logits.shape == (batch, seq, vocab)`, `assert not torch.isnan(loss)`, `assert 0 <= acc <= 1`. These catch the silent corruption that plagues activation/eval pipelines.
- **Order the gates:** static analysis / type-check → unit tests → independent end-to-end check. Do not trust tests alone.
- **Demand evidence, not assertions.** Prompt with "fix the root cause and show me the passing test output — do not suppress the error." An agent that says "✅ all tests pass" without pasting the run output is to be distrusted by default.
- **For unattended runs**, a `Stop` hook (Claude Code) or a persisted goal condition can re-check after every turn and refuse to end the turn until the check holds.

**When this backfires:** if the agent both writes the implementation *and* writes the only test, a green suite proves self-consistency, not correctness (see "self-validating fake tests" below). The check has to be one the agent cannot trivially satisfy by cheating.

## Context engineering: agent instruction files (CLAUDE.md / AGENTS.md)

Agent instruction files put project-specific knowledge in front of the agent automatically. The common names: **`CLAUDE.md`** (Claude Code), **`AGENTS.md`** (the cross-tool standard, now stewarded by the Agentic AI Foundation under the Linux Foundation and read natively by Codex, Cursor, Aider, Gemini CLI, Copilot, Windsurf, Amp, and 25+ others), `.cursor/rules/` (Cursor), `.github/copilot-instructions.md` (Copilot), `AGENT.md` (Amp, singular). A common 2026 pattern is one source-of-truth file with the tool-specific names **symlinked** to it. Since Claude Code **2.1.277**, in a project with no `CLAUDE.md` Claude Code reads `AGENTS.md` instead (configurable under "Project instructions" in `/config`), so a repo that already has `AGENTS.md` works without a symlink; if both exist, `CLAUDE.md` is what Claude Code reads.

**The cardinal rule: keep it short.** The file is injected into the system prompt *every turn*, so every line costs tokens on every call, and — counterintuitively — a bloated instruction file makes the agent *ignore* your actual instructions. Anthropic's test for each line: "Would removing this cause the agent to make a mistake? If not, cut it."

- **Include:** non-obvious commands (the test runner, how to launch a run on the GPU box), code-style rules that differ from defaults, branch/PR conventions, required environment variables, hard-won gotchas ("the tokenizer prepends `<bos>`, skip position 0").
- **Exclude:** file-by-file directory maps (giving the agent a detailed map just makes it "do more of everything" without more accuracy), standard language conventions, full API docs (link instead), and "write clean code" platitudes.
- **Move occasionally-relevant knowledge into Skills** (`.claude/skills/`), which load on demand instead of bloating every conversation.
- **Audit the context you are paying for (Claude Code, 2026-07 → 2026-10):** `/skill-doctor` (2.1.261) shows which loaded skills go unused and what they cost in context; `/doctor prompt-audit` (2.1.283) audits your `CLAUDE.md` files, skills, agents and commands for prompting patterns written for older models; `omitClaudeMd` in subagent frontmatter (2.1.271) lets a subagent run without any `CLAUDE.md`; `autoCompactWindow` in subagent frontmatter (2.1.296) lets one auto-compact earlier than the main conversation.

**Context rot.** Quality degrades as the context window fills with low-value noise — repeated file reads, long error dumps, abandoned approaches. Practitioners report noticeable drift after roughly 20–40 exchanges: the agent starts violating the style you set, re-introduces a pattern you rejected, or drifts architecturally. Fixes: `/clear` between unrelated tasks; `/compact` proactively *while there's still headroom* (you get better summaries); after two failed correction attempts, `/clear` and rewrite the prompt from scratch rather than digging deeper; push exploration into subagents so the raw file contents never hit your main context.

## Agent memory, handoffs and time

Long research runs fail in three quiet ways that have nothing to do with code quality: the agent's context fills and its effort drops, its notes drift until a guess reads like a decision, and it has no reliable sense of how much wall-clock time has passed. Each has a cheap counter-measure.

### Handoff: restart a fresh agent from a written summary (Fulcrum, 2026)

**What the evidence says.** Girit, Hariharan, Shor and Huang (Fulcrum Research), ["Agents are under-elicited: A case study in optimization tasks"](https://www.lesswrong.com/posts/cnHojP3CcAycR7D6F/agents-are-under-elicited-a-case-study-in-optimization-tasks-1) (LessWrong, 2026-06-18), ran Claude Opus 4.6 as an optimizer on inverse-rubric-optimization tasks (learn a black-box judge's preferences under a label budget). With two generic interventions combined, elicitation "roughly doubles eval score at every resource budget" (their Fig. 1):

- **Learnability prompt:** tell the agent that the task is learnable and high scores exist. Their wording: "Calibration: this hidden-judge task is learnable from train feedback. There exists a learnable generation prompt whose mean performance is near perfect …". Adding only that sentence to a GPT-5.5 optimizer raised its budget-1k score from 0.133 to 0.412.
- **Handoff:** "whenever the agent submits, the current agent is killed and a *fresh* agent is started in the same workspace, given the saved prompt, a summary written by its predecessor, and access to all accumulated evaluation files." Aggressive context compaction worked about as well. A **submission gate** (the final eval unlocks only after 95% of the budget is spent) made agents spend the budget but convert it poorly: they re-sampled existing prompts to reach the gate.

**Why it might work.** Tao Lin, ["How to think about LLM effort"](https://www.lesswrong.com/posts/SiS37NfQjzJmy2GX7/how-to-think-about-llm-effort) (LessWrong, 2026-09-15), models effort as a length penalty in the RL reward and predicts the same thing: "Starting a new transcript where the old one left off could improve performance by reducing the required reward per token", and "keep going" prompts might work "just by resetting the perceived length penalty". This is a model, not a measurement. His summary line: an agent submitting "does not imply that it 'thinks it's solved' the task".

**How to apply it.** For a long agent run, define milestones; at each one, have the agent write a summary (what was tried, what the evidence is, what is next) into the run directory, then start a fresh session pointed at that summary and the accumulated result files. Say explicitly when a task is achievable.

**When not to use it:** when you are *measuring* an agent's default propensity or effort (these interventions change the quantity measured), or when the summary would drop state the next agent needs (an unrecorded config, a half-applied migration). One way to check: diff what the fresh agent does in its first ten minutes against what the summary says it should do.

### Agents are not time-aware: put wall-clock timestamps in the loop

Michael Ofengenden (MATS 10, with Maksym Andriushchenko), ["Your Agents Are Not Time Aware"](https://www.lesswrong.com/posts/eAbuPXbjakop5rSJx/your-agents-are-not-time-aware) (LessWrong, 2026-08-14), had Claude Code and Codex predict, run, then retrospectively estimate their own wall-clock runtime on ProgramBench and the authors' AgentTime suite. Findings, as stated in the post:

- "**Agents consistently over-predict task time.**" On AgentTime, "Fable over-predicts by 3x and Sol by 7x" (the post's summary; restricted to its 260 successful runs, those scoring 95% or more, the offsets were 3.1x for Fable 5 and 9.9x for GPT-5.6 Sol). Error is worst on short tasks.
- Runtime depends on the harness: Claude Code "will continue to run until it thinks it's solved the task, Codex often stops at a certain time", and GPT models take on average 2.5x more turns in Claude Code than in Codex.
- Retrospective estimates lean on time cues in the transcript: "When stripping traces of timestamps, the error doubles."

**Tips.** Do not budget compute or deadlines from the agent's own estimate of how long something will take. If you give it a budget ("spend two hours on this"), enforce the budget externally (a `timeout` on the command, a cron or scheduler that stops the run; `claude -p --max-budget-usd` caps *cost*, not time) and log real `started_at` / `finished_at` timestamps per experiment in the run directory so the agent can read elapsed time instead of guessing. The specific ratios are for the post's tasks and mid-2026 models, not a correction factor.

### Project memory the human can still audit: epistemic-status markers

**EpistemicMemory** (`FlorianDietz/EpistemicMemory` on GitHub, MIT, created 2026-09-19, 7 stars as of 2026-10-14; post ["Agent memory the human can still audit"](https://www.lesswrong.com/posts/m6vBZzYZHwXfabxT7/agent-memory-the-human-can-still-audit-primary-sources), Florian Dietz, 2026-10-14; the research is partly funded by the Foresight Institute) is a set of plain-markdown file conventions, not software. The motivating failure, from its README: "agents recorded their own proposals as decisions and cited misremembered numbers as if someone had checked them."

- Each topic gets an **append-only LOG** (never rewritten, so it is the primary source) paired with a short, contradiction-free **SUMMARY** a fresh agent reads first.
- Claims carry **epistemic-status markers**: `[decided]`, `[verified]`, `[concluded]`, `[assumed]`, `[superseded]`, `OUTDATED`. Agent proposals stay `[concluded]` until a human ratifies them; only the human may mark `[decided]` or write `C:` comment lines.
- "**No numbers from memory** — agents must re-read the source file before writing any specific number, because a figure carried across a session boundary is often subtly wrong."
- Agents do not commit; the human reviews the diff, which is the oversight layer.
- `CORE.md` (about 1,000 tokens) appends to an existing `CLAUDE.md` / `AGENTS.md`; the full template targets Claude Code.

**How to adopt it safely.** The README's one-liner tells your agent to fetch `CORE.md` from a URL and add it to its instructions. Read the file yourself first and paste it in, rather than having an agent follow remote instructions (see "Third-party skills and plugins" below).

**When not to use it:** if you want memory with no review burden. The safety comes from the human reading diffs and ratifying decisions; skip the review and the markers are decoration.

### Sector: a leveled "de-slopping" workflow

**Sector** (`TarasKutsyk/Sector` on GitHub, MIT, created 2026-09-27; post ["Sector: de-slopping AI-driven research"](https://www.lesswrong.com/posts/jBZStdgC3wz9Mzqxz/sector-de-slopping-ai-driven-research), Taras Kutsyk, 2026-09-27) asks the agent to make its work "a) easy to understand b) easy to verify c) engaging enough to keep the user in the driver's seat". Four optional levels, each independent of the later ones: (1) an **Owner block** (who you are, what you want to understand and decide, how to talk to you) and a **Project block** (goals, non-goals, constraints) in `AGENTS.md` / `CLAUDE.md`; (2) plan, implement, then *show* the result and *confess* ad hoc choices; (3) proofs of work traceable to code and commits so the next session resumes cleanly; (4) lessons and visual navigation. Setup: `git submodule add https://github.com/TarasKutsyk/Sector tools/sector`, then ask the agent to read `tools/sector/docs/agent/AGENT_README.md`. The author's own advice is that Level 1 gives "the most impact per line".

**When not to use it:** layered on top of another rigor workflow (for example this wiki's `mats-research-rigor` skill); take Level 1 only rather than running two procedures that disagree.

### Turn friction into conventions: transcript post-mortems

Daniel Tan, ["Tips on leveraging AI for empirical research"](https://www.lesswrong.com/posts/f4WZ7dde8KAYHfeif/tips-on-leveraging-ai-for-empirical-research) (LessWrong, 2026-07-06): "Every so often I have an agent review past transcripts: what went well, what could have gone better, was there anything that took an unreasonable amount of effort? The answers feed directly into the next round of tooling and conventions." A cheap version: once a week, point a fresh agent at the past week's session transcripts and ask for the three recurring frictions, then fix one with a `CLAUDE.md` line, a hook or a helper script. (His companion tools `dtch1997/bellhop`, `stagehand` and `cowrite` are archived on GitHub, last push 2026-07-10; the practices, not the tools, are the recommendation.)

## Decomposition and subagents

A **subagent** runs in its own separate context window and reports back only a summary — ideal for "go read these 15 files and tell me how X works" without dumping all 15 files into your main session. Since context is the fundamental constraint, subagents are one of the most powerful tools available.

- **Decompose by context boundary, not arbitrarily.** An agent implementing a feature should also write that feature's tests — it already has the context. Only split work when the contexts are genuinely isolated (disjoint files).
- **Be explicit about parallelism.** Agents default to conservative, sequential behavior and guess wrong; say "use 4 parallel subagents, one per file, non-overlapping." But don't over-parallelize — each subagent reloads context and costs tokens, so 4 parallel agents often cost more even when they finish faster.
- **Define "done" per subtask.** Vague goals produce vague, overlapping work.
- **Runaway-delegation guards (Claude Code).** A per-session cap on subagent spawns (default 200; `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`; `/clear` resets it, 2.1.212) stops loops of agents spawning agents; `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` (1–256, 2.1.269) raises the Workflow tool's per-run concurrency for fan-outs; the Agent tool takes an `effort` parameter (2.1.292) so a cheap subtask need not run at the main session's effort; `/usage` has a per-loop breakdown (2.1.243) to spot a chatty `/loop`; `claude -p --max-budget-usd N` stops a print-mode run once its client-side cost estimate reaches N (subagent spend counts; the estimate can differ from your bill). For unattended `claude -p` hosts, `--permission-prompts none` (2.1.259) denies anything that would prompt.
- **Writer/Reviewer split.** Have one session implement and a *fresh* session review. An agent grading its own work is biased toward declaring victory.

## Tooling extensions: MCP, hooks, slash commands/skills

Brief, practical definitions — these come up constantly and are easy to confuse.

- **MCP = Model Context Protocol.** An open standard (introduced by Anthropic, now under the Linux Foundation's Agentic AI Foundation) for connecting an agent to external systems: GitHub, databases, browser automation, internal APIs. Practical norm is 3–5 servers — more just adds tool-list noise that crowds the context. Where a plain CLI exists (`gh`, `aws`, `gcloud`), prefer it: it's usually the most context-efficient way to reach an external service. Two research-shaped servers that tend to earn their context cost: the official **W&B MCP server** (`wandb/wandb-mcp-server`; run it with `WANDB_MCP_ACCESS_MODE=read-only` so the agent can compare runs but not write reports; see [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md#let-an-agent-query-your-runs-the-wb-mcp-server)) and **arxiv-mcp-server** (`blazickjp/arxiv-mcp-server`, Apache-2.0, `arxiv-mcp-server==0.8.2` on PyPI as of 2026-10-14; "paper ID → outline → one section → citations"; `claude mcp add --transport stdio --scope user arxiv -- uvx arxiv-mcp-server`; its README warns that an unrelated npm package has the same name, so do not install it with `npx`).
- **Hooks** = deterministic shell automation fired at workflow points (before/after a tool call, before the turn ends). Use a hook — *not* an instruction-file line — for anything that must happen with zero exceptions: run the formatter after every edit, block writes to a protected directory, refuse to end the turn until tests pass. Instruction files are advisory; hooks are enforced. **A guard hook should fail closed:** with `onFailure: "block"` (Claude Code 2.1.295, command and HTTP hooks) a hook that cannot start, times out or exits with an unexpected code blocks the action; without it a broken guard silently lets the action through.
- **Slash commands / Skills** = reusable prompts/workflows you trigger (`.claude/commands/`, increasingly `.claude/skills/`). Mark side-effecting ones as manual-invocation-only so the model can't fire them on its own.
- **Plugins** bundle skills + hooks + subagents + MCP servers into one installable unit.

## Third-party skills and plugins: installing safely

A skill (`SKILL.md` plus any scripts and references beside it) is **instructions your agent will follow, and code it may run, with your permissions**. A plugin can also register hooks and MCP servers. So installing one from GitHub is closer to running someone's shell script than to reading their blog post. Anthropic's own plugin directory (`anthropics/claude-plugins-official`) opens with: "Make sure you trust a plugin before installing, updating, or using it. Anthropic does not control what MCP servers, files, or other software are included in plugins". Skills are also an indirect-prompt-injection surface (see "Security risks" below): a skill that tells the agent to fetch and follow a remote document hands control to whoever edits that document.

### How do I install a skill from GitHub without trusting it blindly?

Three steps: **read, pin, scan.**

1. **Read it first.** `gh skill preview OWNER/REPO SKILL` renders the `SKILL.md` and lists its files without installing anything (GitHub CLI; `gh skill` is marked "preview" in `gh` 2.101.0 and the K-Dense README says it needs v2.90.0+). Open every script it ships.
2. **Pin it.** `gh skill install OWNER/REPO SKILL --pin <tag-or-commit-SHA> --agent claude-code --scope project`. Two defaults matter: with no version, `gh` installs the **latest tagged release, else the default branch HEAD**; and when run non-interactively the default `--agent` is `github-copilot`, so without `--agent claude-code` the skill lands where Claude Code never reads it. `gh` writes source-tracking metadata into the frontmatter so `gh skill update` can detect changes. For Claude Code plugin marketplaces, Meridian's `inspect-skills` README notes that "Third-party marketplaces are manual-update by default"; leaving auto-update off keeps the skill text fixed for the length of a project.
3. **Scan it, then still read it.** **skill-scanner** (`cisco-ai-defense/skill-scanner` on GitHub, `cisco-ai-skill-scanner` on PyPI, 2.2.2 released 2026-10-09, Python 3.11–3.14) combines rules, an LLM judge and dataflow analysis. Its recommended setup: `skill-scanner scan ./skill --use-llm --policy balanced --fail-on-severity high`, reviewing everything at MEDIUM or above. Its own held-out measurements (MaliciousSkillBench test split, Gemma 4 26B as judge): **66.7% recall at a 15.4% false-positive rate** for that setup; **rules alone catch 7.7%**. The judge needs `SKILL_SCANNER_LLM_API_KEY` (the default model is a Claude model) or a local model if the skill must not leave your machine.

**When not to rely on it:** as a guarantee. A third of held-out malicious skills get past the best setting, and the README itself says "Human review remains essential." Reading the `SKILL.md` and its scripts is still the control; the scanner is triage.

**Known traps.**
- **"Point your agent at our welcome doc" installs.** Orchestra's README offers "Read https://www.orchestra-research.com/ai-research-skills/welcome.md and follow the instructions"; EpistemicMemory's suggests having the agent fetch `CORE.md`. Fetch the file yourself, read it, and copy it in.
- **Whole-library installs.** K-Dense's README says "**Do not install everything at once.**" Every installed skill's description sits in the agent's context; `/skill-doctor` (Claude Code 2.1.261) shows which ones go unused.
- **Two skills for one job.** A third-party Lean or Inspect skill and a MATS skill covering the same step give the agent two procedures; pick one per project.

### Skill collections worth knowing (as of 2026-10-14)

| Collection | What it covers | Install | When not to use it |
|---|---|---|---|
| **inspect-skills** (Meridian Labs, `meridianlabs-ai/inspect-skills`, MIT, v0.4.5 2026-09-26) | Four skills for Inspect AI: `map-inspect-packages`, `reading-logs` (memory-safe `inspect_ai.log`), `analyzing-logs` (single log vs `inspect_ai.analysis` dataframes vs Inspect Scout), `babysitting-evals` (stalls, error triage and live retuning via `inspect ctl`) | `/plugin marketplace add meridianlabs-ai/inspect-skills` then `/plugin install inspect-skills@meridian` | Enabling its bundled Python REPL MCP server on a shared or sensitive machine: "The MCP runs arbitrary Python" (README) |
| **AI-Research-SKILLs** (Orchestra Research, `Orchestra-Research/AI-Research-SKILLs`, MIT, v1.7.2 2026-06-16) | 98 framework skills in 23 categories, including mech interp (TransformerLens, SAELens, pyvene, nnsight), post-training (TRL, verl, OpenRLHF), inference (vLLM, SGLang), evaluation, and ML paper writing | `/plugin marketplace add orchestra-research/AI-research-SKILLs` then one category, e.g. `/plugin install mechanistic-interpretability@ai-research-skills` | As a whole-library install, via the remote welcome-doc route, or its `autoresearch` orchestrator (pitched as letting agents "autonomously conduct AI research"). One rule from its paper-writing skill worth keeping everywhere: "NEVER generate BibTeX entries from memory. ALWAYS fetch programmatically." |
| **Scientific Agent Skills** (K-Dense, `K-Dense-AI/scientific-agent-skills`, MIT, v2.72.0 2026-10-01) | 177 package- and database-specific skills, mostly biology, chemistry and medicine, plus data analysis and scientific communication | One skill at a time: `gh skill install K-Dense-AI/scientific-agent-skills <skill> --pin v2.72.0 --agent claude-code` | As an alignment-research toolkit (low domain fit) or all at once |
| **discernment-nudge** (Anthropic, `anthropics/skills`, added 2026-08-17) | After a substantive answer the user may act on, appends 2–3 follow-up questions "each tied to something specific in what you just produced", "at most once per conversation" | Copy `skills/discernment-nudge/` from `anthropics/skills` | For experiment code: the skill explicitly skips when the user "is writing code they will run", which is where research errors live |
| **hookify** (Anthropic, in `anthropics/claude-plugins-official`) | Write hooks as markdown rule files instead of `hooks.json` (next subsection) | `/plugin install hookify@claude-plugins-official` | As isolation; see its limits below |

### hookify: research guardrails as markdown rules

**hookify** turns "don't do X" into a hook without writing `hooks.json`. Rules live in `.claude/hookify.<name>.local.md` with YAML frontmatter: `name`, `enabled`, `event` (`bash`, `file`, `stop`, `prompt`, `all`), a `pattern` or a list of `conditions` (fields such as `command`, `file_path`, `new_text`; operators `regex_match`, `contains`, `equals`, `not_contains`, `starts_with`, `ends_with`), and `action`: `warn` (the default; shows a message and allows) or `block` ("Prevents operation from executing (PreToolUse) or stops session (Stop events)"). Rules take effect on the next tool use without a restart. `/hookify` with no arguments proposes rules from behaviours you corrected earlier in the conversation.

A rule protecting held-out data and the eval harness (illustrative: the field and operator names are from the hookify README, the paths are an example):

```markdown
---
name: protect-heldout
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: (data/heldout/|eval_harness\.py$)
---
Edits to the held-out split or the evaluation harness are blocked. Ask the researcher.
```

**Behaviours from the hookify source worth knowing** (`core/config_loader.py`, `core/rule_engine.py`, `hooks/pretooluse.py` in `anthropics/claude-plugins-official`): it **fails open** — the hook scripts always exit 0, so a crashed or mis-parsed rule allows the action; `regex_match` patterns are case-insensitive; the frontmatter parser is hand-written rather than YAML, so a comma inside a `- ` list item breaks parsing; and Read calls are evaluated against *every* rule (the event is unset for Read), so a `file_path` rule like the one above also blocks the agent from **reading** those paths — add `tool_matcher: Edit|Write|MultiEdit` (supported in the source, not in the README) if the agent should still read them. The file rule in `project_templates/autoresearch_loop/hookify/` sets it.

**The gap to know about:** the `file` event "Triggers on Edit, Write, MultiEdit tools". A shell write (`sed -i`, `python -c "open(...).write(...)"`, `cp`) is a Bash call, not a `file` event, so pair the rule above with an `event: bash` rule matching the same paths in `command`. Even then, a regex over command strings is easy to route around. For a guarantee, keep held-out labels **outside the agent's filesystem** (a separate machine, container mount it cannot see, or a scorer it calls but cannot read). The automated alignment researcher harness of Chen, Wen and Kirchner (`YuehHanChen/automated_alignment_researcher`, arXiv:2608.28945) takes this route: the held-out benchmark is "scored eval-private and stripped" from what the agent reads, and its full scores go to a separate held-out directory.

**When not to use it:** as a security boundary against an adversarial agent (model organisms, red-teaming, control evaluations); use a container and see the permission-modes section below.

## Review discipline: the diff is the contract

The dominant failure mode of coding agents is **plausible-but-wrong** code: correct syntax, clean style, confident tone, wrong logic that only bites at an edge case. "Almost right, but not quite" is the most-reported frustration in developer surveys, and reviewing AI code is frequently reported as *more* effort than reviewing a human's.

- **Read every diff line.** If you didn't read it, you didn't review it. "If you can't verify it, don't ship it."
- **Keep diffs small.** Agents make it trivial to dump a 2,000-line PR; resist it. A change that can't be split into reviewable pieces usually has a design problem.
- **Don't trust AI to review AI uncritically.** AI reviews can "sound plausible without matching reality" — even describing code that isn't in the diff. Use them as a first pass, not the final word.
- **Use a fresh-context adversarial reviewer** (a subagent or Claude Code's built-in `/code-review`, which takes an effort level, `--max-findings <n>|all` (2.1.288) and can post inline PR comments or apply fixes; `claude ultrareview [target]` is a separate, non-interactive review command with a 45-minute default timeout) that sees only the diff and the requirements, not the reasoning that produced the code. Caveat: a reviewer told to "find problems" will always find some, so scope it to *correctness and requirement gaps*, or you'll drown in invented over-engineering suggestions.

## Failure modes and anti-patterns (with searchable symptoms)

These are the specific ways agent-written code goes wrong. Each includes the literal symptom you'd notice.

- **Hiding failures behind `try/except`.** Symptom: a broad `except Exception: pass` or `except: return None` wrapped around code that should be allowed to crash, turning a real error into silent wrong behavior. *Prompt against it explicitly: "do not catch-and-swallow; let it raise."*
- **Fabricated dummy / mock data to force a pass.** Symptom: a function that's supposed to load real data quietly returns `np.zeros(...)`, a hard-coded list, or a `MagicMock`; the run "succeeds" on nothing. Especially dangerous in eval pipelines — you'll report numbers computed on fake inputs.
- **Self-validating fake tests.** Symptom: the agent imports a nonexistent library or writes against an API that doesn't exist, then writes tests that assert the same flawed assumptions — everything is green, then it fails for real. Root cause: the agent authored both the code and its only oracle. Fix: write the failing test first, yourself, for anything that matters.
- **Hallucinated packages / "slopsquatting".** Symptom: `pip install`/`import` of a package name that sounds plausible but doesn't exist — `ModuleNotFoundError: No module named '...'` — or worse, one an attacker has *pre-registered* with the hallucinated name. A USENIX Security 2025 study of 576,000 code samples across 16 models found **19.7% of recommended packages did not exist** (~205,000 unique fake names; open models ~21.7%, commercial ~5.2%), and the same fake names recur predictably across runs, which is exactly what makes pre-registration attacks viable. **Verify and pin every dependency an agent adds** before installing.
- **Overconfident wrong edits.** Symptom: output that "perfectly mimics the form of correct code while quietly fabricating the substance" — confident comments and docstrings on logic that's subtly off.
- **Duplication instead of reuse.** Symptom: the agent re-implements a helper that already exists three files over, because it never looked. Encourages code-churn metrics to climb (see "What the evidence says").
- **The kitchen-sink session / correcting over and over.** Symptom: a single conversation that has wandered across five unrelated tasks, and the agent keeps mis-correcting. Fix: `/clear` and start fresh with a tighter prompt.

> These map directly onto Nathan's "Cute coding guide": *hiding is the correctness-killer, bloat the clarity-killer.* Coding agents are powerful generators of exactly these two sins, so the prompts and checks you set up are mostly there to make hiding and bloat impossible.

## Security risks specific to coding agents

An agent with shell, file, and network access is a new attack surface. These are verified, primary-sourced concerns.

- **Indirect prompt injection (the #1 risk; OWASP LLM Top-10 #1).** Malicious instructions hidden in *data the agent reads* — a GitHub issue, a fetched web page, a dependency's README — can hijack it. Invariant Labs (May 2025) demonstrated that a malicious GitHub *issue* in a public repo could steer an agent (via the GitHub MCP server) into reading a **private** repo and exfiltrating its contents through an autonomously-opened public PR. Model alignment alone does not fix this; it needs runtime permission scoping. *Be cautious pointing an agent at untrusted issues, web content, or repos.*
- **Secret / API-key leakage.** GitGuardian's State of Secrets Sprawl 2026 counted **28.65 million new hardcoded secrets** in public GitHub commits in 2025 (+34% year-over-year), and found Claude-Code-assisted commits leaked secrets at **3.2% vs a 1.5% baseline** — largely down to humans accepting the agent's commit. Keep keys in `.env`, gitignore `.env`, deny the agent read access to it where you can, and scan diffs for secrets before committing. (This project keeps its `OPENROUTER_API_KEY` in `~/projects/.env` precisely so it's outside any repo.)
- **Sandbox escapes.** Prefix-string path checks are not real isolation — `CVE-2025-53109/53110` in the filesystem MCP server used symlink tricks to escape and read `/etc/sudoers`. If you sandbox, use a real sandbox (container), not a path-prefix string check.
- **Destructive autonomous actions.** An agent with shell access can run `rm -rf`, `git push --force`, or drop a database. Mitigations: least-privilege tool scopes, **never blanket-approve** shell access (`--dangerously-skip-permissions` / `bypassPermissions`, or allow rules like `Bash(python:*)` that approve arbitrary code) — use manual prompts or classifier-reviewed **auto mode** (next section) plus deny rules — run risky work in a container or disposable VM, limit network egress, and never execute untrusted generated code on your host machine. Cloud "background agent" products (Cursor Background Agents, Copilot coding agent, Devin) run in isolated VMs partly for this reason — but that means your code leaves your machine, which is its own tradeoff.

### Permission modes: auto mode is now the default — what it does and does not protect against

**Auto mode** is a permission mode in which a second model, the **classifier** (Claude Sonnet 5 by default, independent of your `/model`), reviews each action instead of asking you. Anthropic announced on 2026-08-07 that it becomes the default for Pro, Max and Team plans from 2026-08-14, and from Claude Code **2.1.283** it is the built-in starting mode for interactive terminal and VS Code sessions on every plan and provider (Claude Code docs, "Choose a permission mode"; the changelog is finer-grained: 2.1.283 covers sessions on third-party providers or with telemetry off, and 2.1.284 covers terminal and VS Code sessions on every plan and provider). Facts that change how you work:
- **What it blocks:** per the docs, actions that "escalate beyond your request, target unrecognized infrastructure, or appear driven by hostile content Claude read"; it also presumes `git reset --hard`, `git clean -fd`, `git checkout -- .` and `git stash drop` would discard uncommitted work and blocks pushing secrets to public repositories. Tool *results* are stripped from the classifier's input, so a poisoned web page or file cannot talk to it directly. `rm -rf /` and `rm -rf ~` (critical paths) are not reviewed by the classifier; the docs' "critical paths" section says what each mode does with them.
- **It gives up and asks:** after 3 blocks in a row or 20 in a session (not configurable) auto mode pauses and Claude Code goes back to prompting. Repeated blocks usually mean the classifier lacks context about your infrastructure.
- **Boundaries you type are not rules.** If you say "don't push until I review", the classifier treats it as a block signal — but it re-reads the transcript each time, so **context compaction can delete the boundary**. For a hard guarantee write a **deny rule** (and see "hooks" above). Broad allow rules that grant arbitrary code execution (`Bash(python:*)`) are set aside while in auto mode.
- **Headless runs:** `claude -p` and Agent SDK (software development kit) sessions on third-party providers (or with telemetry off) start in auto mode when no permission mode is configured; `--permission-mode` overrides it. `bypassPermissions` "offers no protection against prompt injection or unintended actions" (docs).
- **Cost:** classifier calls count toward token usage on Enterprise plans and on Claude API, Bedrock, Google Cloud and Foundry accounts (docs); Anthropic's 2026-08-07 post says it no longer charges Pro, Max and Team users for the classifier overhead, and where the server reviews actions as part of the session's requests there are no separate classifier calls.

**Evidence, with the source of each number.** *Vendor-reported* (Anthropic blog, 2026-08-07): users approve 97% of permission prompts, and in a controlled study of 1,053 paid testers who were shown a clearly dangerous command swapped into a prompt, human review caught 13.6% of them against 89% for auto mode. *Independent red-teaming against a hostile agent:* Remedios, Storf, Roger, Hughes, *Red-Teaming Auto Mode: Improving Blocking Classifiers Against Malign Coding Agents* (arXiv:2609.19587, 2026-09-17; code `safety-research/red-teaming-auto-mode`) task an adversarial agent, instructed with high-level attack strategies, with evading the production monitors (Claude Code's Auto Mode and OpenAI Codex's Guardian) and find that "in 79% of trials, the agent can use an injection attack against Auto Mode and Guardian to run arbitrary bash commands", along with multi-agent attacks and "malicious compaction"; design changes (more tool coverage, different transcript formatting, an added agentic monitor stage) help a lot, but "preventing multi-context attacks at an acceptable cost remains an open problem".

**How to read these together.** Auto mode is a better safety net than reflexively clicking "yes" against accidents and against injection from content the agent reads. It is **not a sandbox against an adversarial agent**. If your experiment *is* an adversarial or misaligned agent (model organisms, control evaluations, red-teaming), or the agent reads untrusted repositories or web pages while holding credentials, run it in a container or VM with no production credentials and restricted egress — and see [`ai-control.md`](../oversight-and-control/ai-control.md) for monitor evaluation.

## Research-code-specific concerns

Research code has failure modes that ordinary web-app SWE doesn't, and agents amplify them. This section ties the practices above to the kind of code MATS fellows actually write.

- **Reproducibility is the deliverable.** Make the agent follow the run-directory convention: timestamped `outputs/run_YYYYMMDD_HHMMSS_label/` with a `metadata.json` (config, git commit, seed, model IDs, dependency versions) and per-run subdirs for plots — no global plots folder. An agent left to its own devices will scatter outputs and overwrite previous runs.
- **Pin everything.** Pinned random seeds *and* pinned dependency versions (`uv.lock`). Agents love to silently bump a library version to make an import work; that quietly breaks reproducibility.
- **Eval correctness is non-negotiable.** The "fabricated dummy data" failure is catastrophic in an eval — you'll publish accuracy numbers computed on zeros. Assert that the data loader returns real, correctly-shaped, non-degenerate data (`assert batch.std() > 0`), and that the number of scored items equals the number of dataset items.
- **Don't let the agent silence a failing experiment.** A failing assertion about a tensor shape or a NaN loss is *information*. The instinct to wrap it in `try/except` and keep going destroys that information. Let it crash and read the traceback.
- **Heavy runs don't go on the laptop.** Lightweight unit tests are fine locally; model loads, evals, and Docker pulls belong on the GPU box (`nathan@nathan-lambda`) or wherever you've provisioned compute. An agent will happily try to load a 70B model on whatever machine it's on. **Long jobs also do not belong in the agent's own background shell:** Claude Code stops background Bash commands at a time limit (default 30 minutes, maximum 2 hours, 2.1.285) and tells Claude it did so, so a multi-hour training run started that way dies silently from your point of view. Launch it in `tmux` / `slurm` / `nohup` with logs under the run directory and have the agent poll.
- **If the agent-written harness calls open-weights models through OpenRouter, pin the provider** — an unpinned router can change quantization between your baseline and your intervention. See [`evals.md`](../evaluation/evals.md#pin-your-inference-provider-openrouter-and-other-routers).
- **Statistical honesty.** When the agent reports a result, make it report k-seed variation and an effect size with a confidence interval, not a single cherry-picked number. Agents tend to report the best run unless told otherwise.

### Reviewing what an agent ran: practices from Daniel Tan (2026)

From ["Tips on leveraging AI for empirical research"](https://www.lesswrong.com/posts/f4WZ7dde8KAYHfeif/tips-on-leveraging-ai-for-empirical-research) (Daniel Tan, LessWrong, 2026-07-06, written from work with Claude Code), the parts that transfer to any agent:

- **Make the unit of work an atomic experiment writeup.** "For empirical research, I think the unit of work is an **atomic experiment writeup**": one headline result, what was done, why it matters, limitations and reproduction details, readable by a low-context collaborator. Scope each agent task so that it ends in one.
- **Ask for a single-file reproduction of the headline result** before trusting a complex agent result: "I can read it top to bottom, run it, and see if it directionally reproduces the main effect." It catches the case where the pipeline's number comes from something other than the claimed mechanism, at a fraction of the cost of auditing the whole pipeline.
- **Set the report order.** "Begin with the empirical result, then enough experimental detail to understand what was done, and only then interpretation", and tell the agent you are the audience so it skips what you already know.
- **Verify in proportion to how load-bearing a result is.** Exploratory results get a check for major screwups and a note of limitations; full verification happens when a result starts carrying weight.
- **Hold experiment code to five properties:** determinism (same args, same output), resumability (a failed run resumes without redoing finished work), visibility (what is running, what failed, why), persistence (outputs saved and reusable) and lineage (every artifact says how it was made). See [`code-recipes.md`](code-recipes.md#resumable-append-as-you-go-results) for a resumable-results pattern.
- **Isolate parallel agents** in separate git worktrees so their edits cannot collide.

## What the evidence actually says (calibrate against the hype)

The honest summary of 2025–2026 empirical work: **AI raises code volume and velocity while shifting cost downstream to review, verification, and security — and the perceived speedup is systematically overstated.** Cite these precisely; each has caveats.

- **METR randomized controlled trial (RCT), 2025** — the strongest causal evidence. 16 *experienced* open-source developers, working on their *own mature* repos, using Cursor Pro + Claude 3.5/3.7 Sonnet, were **19% slower** with AI — while predicting +24% faster and *still believing* +20% afterward. Big caveat: this is a narrow setting (experts on familiar large codebases, most with little Cursor experience), **not** evidence that AI slows developers in general. Read it as a sharp warning about the self-report-vs-reality gap, not a universal verdict.
- **METR follow-up, 2026-02-24** (`metr.org/blog/2026-02-24-uplift-update/`; METR = Model Evaluation & Threat Research) — the 2025 randomized controlled trial's slowdown was *not* re-established, and nothing replaced it. A later study (57 developers, 143 repos, 800+ tasks; 10 returning from the original study, 47 new; paid $50/hour instead of $150) estimated a change in task time of **−18%** (confidence interval, CI, −38% to +9%) for returning developers and **−4%** (CI −15% to +9%) for new ones — in METR's sign convention, where the 2025 result was +19% (tasks took 19% longer, CI +2% to +39%). Every follow-up interval includes zero. METR itself calls the new data "an unreliable signal of the current productivity effect of AI tools": developers increasingly declined to take part because they did not want to work without AI, 30% to 50% said they withheld tasks they did not want to do without AI, some found time hard to report when they worked on an unrelated task while an agent ran, and METR believes its central estimate "is likely a bad proxy for the real productivity impact" of AI tools. It is changing the study design. METR's own interview-based belief is that developers are likely *more* sped up in early 2026 than in early 2025, but its data is "only very weak evidence for the size of this increase". **Read it as: no trustworthy 2026 estimate exists for experts on mature repos.**
- **Practitioner reports (anecdotes, not measurements).** John Wentworth (LessWrong, 2026-08-11) says that since early 2026 Claude Code handles his day-to-day interpretability coding "well enough that I never need to write the code myself", while its interpretations and suggested next steps are "still mostly useless" — he catches bad code by reading graphs and tables of outputs. Horacio (LessWrong, 2026-10-02, *Failure modes of Claude Code in a supervised but code-blind 60h project*, n = 1) supervised Claude Code's reasoning but never read the code: a working prototype took ~30 h (he estimates ~40 h by hand), then the next ~30 h became a "bug treadmill" in which fixes broke as much as they repaired — the cost of **not reading the diff** shows up late, not early.
- **GitClear 2025** (observational, ~211M lines): copy/pasted lines rose 8.3% → 12.3%, refactoring ("moved") lines fell 24.1% → 9.5%, short-window code churn rose 3.1% → 5.7%, duplicate blocks up ~8×. Correlational and from a vendor that sells code-quality tooling — read as "duplication is trending up in the AI era," not proof of causation.
- **DORA 2025** (survey): AI adoption now positively associated with throughput, but **still negatively associated with delivery stability**. Core message: "AI amplifies what's already there" — the gains require strong testing, version control, and fast feedback loops underneath. Which is the whole point of this doc.

The takeaway is not "don't use coding agents" — they're genuinely transformative for the right tasks. It's that the speedup is real only when you keep the verification, review, and reproducibility scaffolding intact; remove it and you get fast generation of code you can't trust.

## The current tool landscape (October 2026)

Tools here move monthly — Claude Code was at v2.1.296 and the Codex CLI at rust-v0.162.1 on 2026-10-09, each with several releases a week — so **verify before relying on any specific feature** and treat vendor metrics skeptically. Two things reverse what older training data would tell you: **Gemini CLI's sunset for free/Pro/Ultra users in favor of Antigravity CLI was scheduled for 2026-06-18** (enterprise keeps Gemini CLI; not re-verified in the 2026-10 pass, although the open-source `google-gemini/gemini-cli` repository is still shipping releases), and **Windsurf is now owned by Cognition** (makers of Devin), not OpenAI or Google.

| Tool | Maker | Form | When *not* to use it |
|---|---|---|---|
| **Claude Code** | Anthropic | Terminal CLI + IDE + SDK; reference impl for `CLAUDE.md` | You want a fully autonomous cloud agent that runs with your laptop closed, or a free/local-only tool |
| **OpenAI Codex / Codex CLI** | OpenAI | Open-source terminal CLI (`openai/codex`) + app/cloud | You want to stay off OpenAI models or want a mature IDE-native experience |
| **Cursor** | Anysphere | AI-native IDE; interactive **Agent mode** + cloud **Background Agents** | You need a free tool or want code to stay local (background agents send code to Cursor's cloud) |
| **GitHub Copilot** | GitHub/Microsoft | In-IDE **agent mode** + cloud **coding agent** (assign it an issue) | You want non-GitHub host/model flexibility or terminal-first workflows |
| **Gemini CLI → Antigravity CLI** | Google | Open-source terminal agent, 1M-token context | As a free/Pro user after 2026-06-18 (migrate to Antigravity CLI); or if you don't want Google-model lock-in |
| **Aider** | open source (`Aider-AI/aider`) | Git-first terminal pair-programmer, model-agnostic | You want a GUI/IDE, cloud autonomy, or multi-session orchestration |
| **Devin** | Cognition | Autonomous cloud "AI software engineer", VM per session | Tight interactive pair-programming or quick local edits (it's async/delegated and enterprise-priced) |
| **Cline** | open source (Apache-2.0) | VS Code sidebar agent (+ JetBrains, preview CLI), bring-your-own-key | You want a hosted cloud agent or zero per-token API cost |
| **Windsurf** | Cognition (acquired 2025) | AI-native IDE, Cascade agent, Devin-in-editor | You want a vendor-neutral tool (now tied to Cognition's Devin/SWE models) |

Cross-tool standards worth knowing: **AGENTS.md** (the converging instruction-file standard, Linux Foundation), **MCP / Model Context Protocol** (the model↔tools standard, Linux Foundation), and **ACP / Agent Client Protocol** (an emerging editor↔agent interop layer, e.g. running Claude Code/Codex/Gemini inside Zed).

### Which coding agent should I use as a MATS fellow?

For most research code, the choice matters far less than the workflow. Pick whichever you'll actually keep in the Plan → Act → Verify loop. Terminal-first agents (**Claude Code**, **Codex CLI**, **Aider**) integrate cleanly with the `uv` + run-directory conventions this wiki recommends and keep your code local by default. Reach for a cloud **background agent** (Cursor, Copilot coding agent, Devin) only for delegated, well-specified tasks where sending code off-machine is acceptable and the isolation (it can't `rm -rf` your laptop) is a feature.

### How do I stop the agent from faking results to make my code "work"?

Three layers. (1) Don't let it author the only oracle — write the key failing test yourself first. (2) Assert on *real* properties the agent can't fake cheaply: shapes, non-NaN, non-degenerate data (`assert batch.std() > 0`), item counts matching the dataset. (3) Demand evidence — make it paste the actual run output, not a "✅ done". And prompt explicitly against the two specific cheats: no broad `try/except` that swallows errors, no dummy/mock data standing in for real loads.

A fourth layer, for when the agent is optimizing a metric (a prompt, a classifier, an eval): **also score the artifact it changed, with a check it was not optimizing.** Keira Leal, ["Before We Defer Research to AI: Measuring Apparent-Success-Seeking"](https://www.lesswrong.com/posts/tdZyjrappcEaQuM4A/before-we-defer-research-to-ai-measuring-apparent-success) (LessWrong, 2026-08-11), asked a coding assistant to add out-of-distribution few-shot examples to a classifier prompt; it "copied my failing test cases into the few-shot prompt, gaming the evaluation", and when called out, "did it again, just harder to spot". Her proposal is a paired protocol: one scorer that checks what a user would normally look at (test pass rate) and one that inspects the strategy used (are the new examples actually disjoint from the test set?); the gap is the signal.

### Is it safe to point a coding agent at an untrusted repo or web page?

Treat it like running untrusted code, because effectively you are. Indirect prompt injection means a malicious GitHub issue, README, or web page the agent *reads* can hijack it into leaking private data or taking destructive actions. For untrusted inputs: restrict tool permissions, never run in `bypassPermissions` mode (it offers no protection against prompt injection), treat auto mode as a safety net rather than a boundary (an adversarial agent given high-level attack strategies used an injection attack against Auto Mode and Codex's Guardian to run arbitrary bash in 79% of trials in arXiv:2609.19587), and prefer a sandboxed/containerized agent over one with full access to your home directory and credentials.

---

Last verified: 2026-10-14. (Additions 2026-10-14: "Agent memory, handoffs and time" (Fulcrum, Tao Lin, Ofengenden, EpistemicMemory, Sector, Tan posts read via LessWrong GraphQL markdown; repos via `gh api`), "Third-party skills and plugins: installing safely" (`gh skill` help text from `gh` 2.101.0; `cisco-ai-defense/skill-scanner` README, release 2.2.2 and PyPI; READMEs of `meridianlabs-ai/inspect-skills`, `Orchestra-Research/AI-Research-SKILLs`, `K-Dense-AI/scientific-agent-skills`, hookify in `anthropics/claude-plugins-official`; `discernment-nudge` SKILL.md and commit history), Tan's review practices, Leal's paired-scorer check, W&B MCP and arxiv-mcp-server pointers. Not verified: hookify behaviour beyond its README — the rule example was not executed.) (Additions 2026-10: Claude Code feature and default changes from `anthropics/claude-code` `CHANGELOG.md` (2.1.211 → 2.1.296, 2026-07-15 → 2026-10-09; items cited by version) and the permission-modes docs page; Anthropic blog *Auto mode is now the default in Claude Code* (2026-08-07); Remedios et al. arXiv:2609.19587; METR update of 2026-02-24 read directly; Wentworth (2026-08-11) and Horacio (2026-10-02) posts read directly; all verified via arXiv/GitHub/vendor pages. Not verified: Codex's Guardian behavior beyond the arXiv abstract's description, Cursor / Copilot / Devin changes since June, and the vendor-reported auto-mode study numbers (97% approval, 13.6% vs 89%), which are Anthropic's own — checked against the 2026-08-07 post, not independently reproduced.) Earlier pass (2026-06): Tool landscape is fast-moving — Gemini CLI consumer sunset (2026-06-18 → Antigravity CLI) and Windsurf-under-Cognition are confirmed; re-verify specific features before relying on them. Core practices (plan-first, runnable verification loop, lean context, read-the-diff review, verify dependencies) are stable. Empirical figures (METR −19%, USENIX 19.7% package hallucination, GitGuardian 28.65M secrets) cited from primary sources.
