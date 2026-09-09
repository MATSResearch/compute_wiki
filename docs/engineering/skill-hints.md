# Lightweight skill hints

A hook can simply say:

> By the way, there's a relevant skill you might want to look at here:
> mats-lean-cleanup (path/to/SKILL.md). Use it if helpful; no acknowledgement needed.

The agent decides whether to read or use the skill. There is no required
response, review gate, proof check, automatic skill invocation, or stop-loop.
The initial adapter uses Claude Code's
[PostToolUse context output](https://code.claude.com/docs/en/hooks#posttooluse-decision-control).
Other clients need their own event adapter; this is not a universal hook format.

## Initial relevance rules

| Successful tool event | Suggested skill |
|---|---|
| Read a `.lean` file | `mats-lean-formalization` |
| Edit or Write a `.lean` file | `mats-lean-cleanup` |
| Read a matching `SKILL.md` or invoke that skill | Mark it handled, without a hint |

Each skill is suggested at most once per project/session, even when tool calls
run concurrently. Missing skills are skipped. Reading or invoking skills through
other mechanisms may not be observed. Shell-based edits, MCP tools, prompt topic
classification, and diagnosing compiler output are outside this initial adapter.
The hook does not read transcripts or source file contents and makes no network
or model calls. Add narrowly useful event rules when experience warrants them.

## Install in a research project

The source lives in the wiki's
[`hooks/` directory](https://github.com/MATSResearch/compute_wiki/tree/master/hooks).
Copy `skill_hint.py` to the research project's `.claude/hooks/skill_hint.py`.
Install the desired skills in `.claude/skills/` or `~/.claude/skills/`, or point
`MATS_SKILLS_DIR` at the wiki checkout's `skills/` directory.

Merge the `hooks.PostToolUse` entry from
[`claude-settings.example.json`](https://github.com/MATSResearch/compute_wiki/blob/master/hooks/claude-settings.example.json)
into that project's `.claude/settings.json`, preserving existing hooks and other
settings. The example runs Python 3 with a three-second timeout. Reload hooks
using the client's normal configuration workflow. Merely installing skills does
not enable the hook, and publishing this template changes no user settings.

Project skills take precedence over user skills; an explicit `MATS_SKILLS_DIR`
takes precedence over both. A hint contains the resolved path, so loading a skill
does not require invocation by a particular slash-command spelling.

## Keep reminders quiet

- Set `MATS_SKILL_HINTS=0` in the launching environment to disable all hints.
- Set `MATS_SKILL_HINT_MUTE=mats-lean-cleanup` to mute that skill; comma-separated
  names mute several skills across sessions.
- Remove the hook entry to uninstall the integration.

Deduplication uses empty hashed marker files in `~/.cache/mats-skill-hints/`.
`MATS_SKILL_HINT_STATE_DIR` can select another directory. Markers contain no
conversation text and can be deleted when sessions have ended; deleting active
session markers permits reminders to repeat. Malformed input or state failures
produce no hint and a successful exit. The hook never returns a blocking decision.

## Validation

Run `python3 -m unittest discover -s hooks/tests -v` from the wiki checkout.
Tests exercise relevance, optional context output, session deduplication,
concurrent delivery, handled/muted/unavailable skills, and failure behavior.
A client-level smoke test should confirm delivery after a `.lean` edit and silence
on the next edit in the same session. The subprocess tests verify the adapter's
output protocol; they do not simulate the client's UI or skill-discovery system.
