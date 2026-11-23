# Autoresearch loop

A copy-and-edit starting point for an agent-driven **metric loop**: the agent
edits one surface, a frozen script measures it, the change is kept or reverted,
repeat. It is the karpathy/autoresearch shape with the parts its descendants
added back — a reason recorded for every discard, a gate on every candidate, a
held-out split the agent cannot read, and points where the loop stops for the
researcher.

The background, the systems this borrows from, and the checklist it implements
are in the wiki:
[`docs/engineering/ai-scientist-frameworks.md`, "Metric loops you can run this week"](https://matsresearch.github.io/compute_wiki/engineering/ai-scientist-frameworks/#metric-loops-you-can-run-this-week).

**When not to use it:** when your question has no number a script can produce
(most conceptual alignment questions — see the field reports on the same wiki
page); or when one evaluation run is too expensive to repeat, because the
keep/discard rule here needs a measured noise floor. It is also not isolation:
see "What the hooks do not stop" below.

| File | Owner | What it is |
|---|---|---|
| [`program.md`](program.md) | researcher | The agent's instructions: scope, the loop, and the pause points (P0–P5) where it stops and waits |
| [`measure.sh`](measure.sh) | researcher | Runs one experiment on the **dev** split and prints `METRIC name=value` lines; non-zero exit = crash |
| [`checks.sh`](checks.sh) | researcher | Backpressure after a dev improvement: tests, plus a pass/fail floor on the **guard** split; non-zero exit = `checks_failed` |
| [`score_final.sh`](score_final.sh) | researcher | Scores the **final** split once, at the end, run by the researcher only |
| [`log_result.py`](log_result.py) | — | Appends one validated line to `results.jsonl` (stdlib only); refuses malformed or out-of-order records |
| [`results.schema.json`](results.schema.json) | — | JSON Schema for one `results.jsonl` line |
| [`claude_hooks/`](claude_hooks/) | researcher | Optional Claude Code `PreToolUse` guard (`protect_loop.py` + `settings.example.json`) that **fails closed** (`"onFailure": "block"`) |
| [`hookify/`](hookify/) | researcher | Optional hookify rule files with the same patterns; simpler to install, but they **fail open** |

The scripts are templates: every line marked `# >>> EDIT` is yours to fill in.

## Quick start

```bash
cp -r project_templates/autoresearch_loop/* ~/projects/my_loop/   # next to your code
cd ~/projects/my_loop
chmod +x measure.sh checks.sh score_final.sh
# 1. Fill in the "Fill in before starting" block of program.md.
# 2. Edit the `# >>> EDIT` lines in measure.sh, checks.sh, score_final.sh.
# 3. Put held-out data under data/heldout/guard/ and data/heldout/final/ (see below).
# 4. Optional guard hook (fails closed; see "Optional: a guard hook" below):
#      mkdir -p .claude/hooks && cp claude_hooks/protect_loop.py .claude/hooks/
#      then merge claude_hooks/settings.example.json into .claude/settings.json
#    or, simpler but fail-open: mkdir -p .claude && cp hookify/*.local.md .claude/
git checkout -b autoresearch/<tag>
# 5. Start your agent in this directory and point it at program.md.
```

Steps 3 and 4 are manual because this repo's `.gitignore` ignores every `data/`
and `.claude/` directory, so the template cannot ship either one — create them
in your project.

## Three splits, three different jobs

| Split | Where | Who sees what | Job |
|---|---|---|---|
| **dev** | wherever your code reads it | the agent sees the score every run | the number the loop climbs |
| **guard** | `data/heldout/guard/` | the agent sees only PASS / FAIL from `checks.sh` | a floor every kept candidate must clear (evo's held-out-slice gate) |
| **final** | `data/heldout/final/` | the researcher only, via `score_final.sh`, once | the number you report |

Why three: a split used to *accept* changes, even as a pass/fail floor, is being
selected on, and after many candidates it stops being held out. Arbor gates
merges on its "held-out test" split; if that is also the split you report, it
has become a validation set. The guard split leaks about one bit per candidate,
so keep its floor loose (catch regressions, not rank candidates); the final
split is touched once.

One tension to resolve per project: `checks.sh` runs as the agent and reads
`data/heldout/guard/` itself, so if you move held-out data out of the agent's
reach (the strongest protection), the guard scorer has to move with it — run it
as another user, in another container, or behind a remote scoring call that
returns only PASS / FAIL.

## Pause points (from `program.md`)

| | When | What the agent does |
|---|---|---|
| **P0** | Setup | Restates objective, metric, direction, editable files, budgets; waits for "go" |
| **P1** | After the baseline | Runs the unchanged baseline 3 times, reports the spread as the noise floor; waits |
| **P2** | Every K experiments (set in `program.md`) | Summary, plus "what is your goal right now, in your own words?"; waits |
| **P3** | Anything outside scope | A new dependency, a change to a researcher-owned file, a budget change: asks first |
| **P4** | Repeated failure | Same idea fails twice, or 3 crashes in a row: stops and reports |
| **P5** | Before any claim | Proposes file-disjoint branches for kept changes and a re-measurement plan; waits |

The P2 check-in question is Arcadia Impact's (see the wiki page's field
reports); P4 follows Asta's "same item failed twice" stop; P5 follows
pi-autoresearch's `finalize`. Delete pause points you do not want — they are a
default, not a rule.

## `results.jsonl`: one line per experiment, append-only

Lives in the run directory, `outputs/run_<YYYYMMDD_HHMMSS>_<tag>/results.jsonl`,
next to `metadata.json` and per-run logs. Add `outputs/` to your project's
`.gitignore`: kept untracked, the record survives the `git reset --hard` that
discards an experiment (a `git clean -x` would still delete it). Write it only through `log_result.py`:

```bash
uv run python log_result.py outputs/run_20261014_093000_lr_sweep/results.jsonl \
    --run 7 --kind experiment --status discard --commit a1b2c3d \
    --metrics-from outputs/run_20261014_093000_lr_sweep/logs/7.metrics \
    --hypothesis "warmup 2x longer" --prediction "val_metric drops by ~0.01" \
    --description "doubled warmup steps" \
    --rollback-reason "no change beyond the noise floor; warmup is not the bottleneck at this batch size"
```

| Field | Notes |
|---|---|
| `run` | 1, 2, 3, … with no gaps; `log_result.py` refuses anything else |
| `ts` | ISO-8601 UTC, added by `log_result.py` |
| `kind` | `baseline`, `experiment`, or `rerun` (a verification re-run for noise, not a new idea) |
| `status` | `keep`, `discard`, `crash`, `checks_failed` — pi-autoresearch's four statuses |
| `commit` | short git SHA of the tried change (`null` for a crash before commit) |
| `metrics` | `{name: number}` parsed from `measure.sh`'s `METRIC` lines |
| `hypothesis`, `prediction` | written **before** the run (research-fuzzer's "no action without a bet") |
| `description` | what was changed; for a revisit, what assumption changed |
| `rollback_reason` | required for `discard`, `crash`, `checks_failed` |
| `revisits_run` | the earlier run number when deliberately retrying a discarded idea because its `rollback_reason` stopped being true; must point at an earlier non-kept run |

Full schema: [`results.schema.json`](results.schema.json). Write the run's
`metadata.json` (objective, metric, direction, editable files, budgets, git SHA
at start, model IDs) at P0; for a full field list, the research-rigor
template's
[`metadata.schema.json`](../research_rigor/templates/metadata.schema.json) works
here too.

## Optional: a guard hook

Two ways to make Claude Code refuse the calls `program.md` forbids. They use
the same patterns; they differ in what happens when the hook itself breaks.
Either is enough.

### `claude_hooks/`: a native hook that fails closed

`protect_loop.py` is a `PreToolUse` command hook (stdlib Python): it exits 2,
which refuses the call, for a Bash command mentioning `data/heldout` or
`score_final.sh`, and for Edit / Write / NotebookEdit on `data/heldout/`,
`measure.sh`, `checks.sh`, `score_final.sh`, `program.md` or `results.jsonl`.
Read is not matched, so the agent can still read `program.md` and
`results.jsonl`. `settings.example.json` registers it with
`"onFailure": "block"`; merge it into your project's `.claude/settings.json`.

Why the `onFailure` line matters. The hooks reference
([code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks), read
2026-11-23) says: "On most events, when a hook fails or times out, Claude Code
still carries out the action", and of a failed hook, "The action goes ahead,
except for hooks whose failure blocks the action". The fix it gives: "set
`"onFailure": "block"` on a `command`, `http`, or `mcp_tool` hook. Requires
Claude Code v2.1.295 or later." Failure covers a hook that cannot start, an
exit code other than 0 or 2, a timeout and invalid output. Since 2.1.329 the
same default applies to tool calls made by Code Mode scripts (changelog:
"a PreToolUse hook that errors no longer refuses a script's tool call ... set
`"onFailure": "block"` on a command, HTTP or MCP tool hook that must refuse").
So without that line a guard with a missing `python3` or a typo guards
nothing; with it, a broken guard stops the agent until you fix it. The script
catches no exceptions for the same reason: input it cannot read must crash.

Tested here (2026-11-23) by piping sample `PreToolUse` JSON to the script:
allowed calls exit 0, forbidden ones exit 2, malformed input exits 1. Not
tested inside a live Claude Code session, so after copying it in, and after
any Claude Code upgrade, **make it fail on purpose** (rename the script, then
ask the agent to run `ls`): the call should be refused. The matcher includes
`Monitor` (whose shell commands hooks have seen since 2.1.314) on the
assumption that its input carries `command`; if it does not, the hook crashes
and Monitor calls are blocked, which this loop does not need anyway.

### `hookify/`: markdown rules that fail open

[hookify](https://matsresearch.github.io/compute_wiki/engineering/agentic-swe-practices/#hookify-research-guardrails-as-markdown-rules)
(Anthropic's Claude Code plugin, `/plugin install hookify@claude-plugins-official`)
reads rule files named `.claude/hookify.<name>.local.md`, relative to the directory the hook runs in (normally the project root).
Copy the two in [`hookify/`](hookify/) there:

- `hookify.protect-loop-files.local.md` — `event: file`, `tool_matcher: Edit|Write|MultiEdit`, `action: block`: Edit /
  Write / MultiEdit calls on `data/heldout/`, `measure.sh`, `checks.sh`,
  `score_final.sh`, `program.md` or `results.jsonl`.
- `hookify.protect-heldout-shell.local.md` — `event: bash`, `action: block`: any
  Bash command whose text mentions `data/heldout` or `score_final.sh`. Run
  `score_final.sh` yourself in your own terminal; inside the agent session this
  rule blocks it.

Check they loaded with `/hookify:list`. Details from hookify's source
(`plugins/hookify/core/` and `hooks/` in `anthropics/claude-plugins-official`,
read 2026-10-14), worth knowing before relying on them:

- **They fail open, and you cannot change that from a rule file.** The plugin
  registers its own hooks, so `onFailure` is not yours to set. The hook scripts "ALWAYS exit 0 - never block operations
  due to hook errors": a rule file that fails to parse, or a missing `python3`,
  means the operation goes ahead with a warning on stderr. If the guard has to
  hold when it breaks, use `claude_hooks/` above.
- **Patterns are Python regexes, matched case-insensitively** (`re.IGNORECASE`)
  with `search`, against the raw tool input — absolute paths included.
- **The frontmatter parser is hand-written, not full YAML.** Keep each
  `- field:` list item free of commas (a comma makes it parse as an inline
  dictionary) and indent continuation lines by four spaces, as the files here do.
- **Without `tool_matcher`, a `file` rule also fires on Read.** For tools other
  than Bash / Edit / Write / MultiEdit, the PreToolUse hook loads every enabled
  rule, and Read's input has a `file_path`, so a `file_path` rule blocks Read on
  matching paths too — here that would stop the agent reading `program.md` and
  `results.jsonl`. The loop-files rule therefore sets
  `tool_matcher: Edit|Write|MultiEdit` (also read from hookify's source; not in
  its README), so the agent's Read tool is not blocked anywhere by these rules.

### What the hooks do not stop

This applies to both kinds. A file rule sees only the file-editing tools, and a
shell rule sees only the literal command text. A script that opens `data/heldout/` itself,
a variable holding the path, or `cd data && cat heldout/…` all pass. The rules
catch accidents and make intent visible; they are not a boundary against an
agent looking for a way round them. For that, keep `data/heldout/` where the
agent's process cannot read it — another machine, another Unix user, or a
container mount the agent's container does not have (the AAR harness keeps its
held-out directories "off the research side"; the W2S researcher's Docker mode
hides labels from the container).

## Conventions

Same as the other templates: `uv run python …`; one self-contained run
directory per session, `outputs/run_<YYYYMMDD_HHMMSS>_<tag>/`, with
`metadata.json`, `results.jsonl`, `logs/` and `plots/`; scripts do not use
`set -euo pipefail` (a failing command should report, not kill the shell).

## Where the pieces come from

`karpathy/autoresearch` (one editable file, frozen evaluation, `program.md`);
`davebcn87/pi-autoresearch` (`METRIC name=value`, `checks.sh`, the four
statuses, `rollback_reason` / `revisits_run`, `finalize`); `evo-hq/evo` (a
held-out floor gate on every candidate); `RUC-NLPIR/Arbor` (dev/test split and
`interaction_mode: review`); `YuehHanChen/automated_alignment_researcher` (the
held-out split never reaches the agent); `ARA-Labs/research-fuzzer` (a
prediction before each action). The wiki page has the details and the
"when not to use it" for each.
