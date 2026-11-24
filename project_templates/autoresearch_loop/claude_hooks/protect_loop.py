#!/usr/bin/env python3
"""protect_loop.py: Claude Code PreToolUse guard for the autoresearch loop.

Researcher-owned. Refuses (exit 2) a Bash command whose text mentions the
held-out data or the final scorer, and an Edit / Write / NotebookEdit call on a
researcher-owned file (program.md, "Who owns what"). Same patterns as the two
hookify rules in ../hookify/; unlike them this hook FAILS CLOSED.

Exit status, per the Claude Code hooks reference (code.claude.com/docs/en/hooks):
  0  no objection; the call goes on through the normal permission flow
  2  blocking error: the tool call is refused and stderr is shown to the agent
  anything else (a crash here, python3 missing, a timeout) is a hook FAILURE.
     On its own a failure lets the call through; `"onFailure": "block"` in
     settings.example.json (Claude Code >= 2.1.295) makes it refuse instead.
     So nothing below catches exceptions: an input this script cannot read
     must crash, and the crash must block.

Stdlib only. Wire it up with settings.example.json (see the README).
"""
import json
import re
import sys

SHELL_PATTERN = re.compile(r"data/heldout|score_final\.sh", re.IGNORECASE)
FILE_PATTERN = re.compile(
    r"(^|/)(data/heldout/|measure\.sh$|checks\.sh$|score_final\.sh$|program\.md$|results\.jsonl$)",
    re.IGNORECASE,
)
# Path field per file-writing tool. A tool the settings matcher sends here that
# is not listed is a KeyError: a crash, which blocks.
PATH_FIELD = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path"}

event = json.load(sys.stdin)
tool = event["tool_name"]
tool_input = event["tool_input"]

if tool in ("Bash", "Monitor"):
    if SHELL_PATTERN.search(tool_input["command"]):
        print("This command touches the held-out splits or the final scorer, which only the "
              "researcher uses (program.md). Run ./measure.sh for the dev split and ./checks.sh "
              "for the guard floor. If you need something else, stop and ask (pause point P3).",
              file=sys.stderr)
        sys.exit(2)
else:
    path = tool_input[PATH_FIELD[tool]]
    if FILE_PATTERN.search(path):
        print(f"{path} belongs to the researcher in this autoresearch loop (program.md, "
              "\"Who owns what\"). Append to results.jsonl with log_result.py. For anything "
              "else, stop and ask the researcher (pause point P3).", file=sys.stderr)
        sys.exit(2)
