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

## Decomposition and subagents

A **subagent** runs in its own separate context window and reports back only a summary — ideal for "go read these 15 files and tell me how X works" without dumping all 15 files into your main session. Since context is the fundamental constraint, subagents are one of the most powerful tools available.

- **Decompose by context boundary, not arbitrarily.** An agent implementing a feature should also write that feature's tests — it already has the context. Only split work when the contexts are genuinely isolated (disjoint files).
- **Be explicit about parallelism.** Agents default to conservative, sequential behavior and guess wrong; say "use 4 parallel subagents, one per file, non-overlapping." But don't over-parallelize — each subagent reloads context and costs tokens, so 4 parallel agents often cost more even when they finish faster.
- **Define "done" per subtask.** Vague goals produce vague, overlapping work.
- **Runaway-delegation guards (Claude Code).** A per-session cap on subagent spawns (default 200; `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`; `/clear` resets it, 2.1.212) stops loops of agents spawning agents; `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` (1–256, 2.1.269) raises the Workflow tool's per-run concurrency for fan-outs; the Agent tool takes an `effort` parameter (2.1.292) so a cheap subtask need not run at the main session's effort; `/usage` has a per-loop breakdown (2.1.243) to spot a chatty `/loop`; `claude -p --max-budget-usd N` stops a print-mode run once its client-side cost estimate reaches N (subagent spend counts; the estimate can differ from your bill). For unattended `claude -p` hosts, `--permission-prompts none` (2.1.259) denies anything that would prompt.
- **Writer/Reviewer split.** Have one session implement and a *fresh* session review. An agent grading its own work is biased toward declaring victory.

## Tooling extensions: MCP, hooks, slash commands/skills

Brief, practical definitions — these come up constantly and are easy to confuse.

- **MCP = Model Context Protocol.** An open standard (introduced by Anthropic, now under the Linux Foundation's Agentic AI Foundation) for connecting an agent to external systems: GitHub, databases, browser automation, internal APIs. Practical norm is 3–5 servers — more just adds tool-list noise that crowds the context. Where a plain CLI exists (`gh`, `aws`, `gcloud`), prefer it: it's usually the most context-efficient way to reach an external service.
- **Hooks** = deterministic shell automation fired at workflow points (before/after a tool call, before the turn ends). Use a hook — *not* an instruction-file line — for anything that must happen with zero exceptions: run the formatter after every edit, block writes to a protected directory, refuse to end the turn until tests pass. Instruction files are advisory; hooks are enforced. **A guard hook should fail closed:** with `onFailure: "block"` (Claude Code 2.1.295, command and HTTP hooks) a hook that cannot start, times out or exits with an unexpected code blocks the action; without it a broken guard silently lets the action through.
- **Slash commands / Skills** = reusable prompts/workflows you trigger (`.claude/commands/`, increasingly `.claude/skills/`). Mark side-effecting ones as manual-invocation-only so the model can't fire them on its own.
- **Plugins** bundle skills + hooks + subagents + MCP servers into one installable unit.

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

### Is it safe to point a coding agent at an untrusted repo or web page?

Treat it like running untrusted code, because effectively you are. Indirect prompt injection means a malicious GitHub issue, README, or web page the agent *reads* can hijack it into leaking private data or taking destructive actions. For untrusted inputs: restrict tool permissions, never run in `bypassPermissions` mode (it offers no protection against prompt injection), treat auto mode as a safety net rather than a boundary (an adversarial agent given high-level attack strategies used an injection attack against Auto Mode and Codex's Guardian to run arbitrary bash in 79% of trials in arXiv:2609.19587), and prefer a sandboxed/containerized agent over one with full access to your home directory and credentials.

---

Last verified: 2026-10. (Additions 2026-10: Claude Code feature and default changes from `anthropics/claude-code` `CHANGELOG.md` (2.1.211 → 2.1.296, 2026-07-15 → 2026-10-09; items cited by version) and the permission-modes docs page; Anthropic blog *Auto mode is now the default in Claude Code* (2026-08-07); Remedios et al. arXiv:2609.19587; METR update of 2026-02-24 read directly; Wentworth (2026-08-11) and Horacio (2026-10-02) posts read directly; all verified via arXiv/GitHub/vendor pages. Not verified: Codex's Guardian behavior beyond the arXiv abstract's description, Cursor / Copilot / Devin changes since June, and the vendor-reported auto-mode study numbers (97% approval, 13.6% vs 89%), which are Anthropic's own — checked against the 2026-08-07 post, not independently reproduced.) Earlier pass (2026-06): Tool landscape is fast-moving — Gemini CLI consumer sunset (2026-06-18 → Antigravity CLI) and Windsurf-under-Cognition are confirmed; re-verify specific features before relying on them. Core practices (plan-first, runnable verification loop, lean context, read-the-diff review, verify dependencies) are stable. Empirical figures (METR −19%, USENIX 19.7% package hallucination, GitGuardian 28.65M secrets) cited from primary sources.
