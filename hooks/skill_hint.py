#!/usr/bin/env python3
"""Optional Claude Code PostToolUse hints; stdlib only, no blocking decisions."""
import hashlib
import json
import os
from pathlib import Path
import sys

RULES = {
    'Read': 'mats-lean-formalization',
    'Edit': 'mats-lean-cleanup',
    'Write': 'mats-lean-cleanup',
}


def skill_file(name, cwd):
    roots = [cwd / '.claude/skills', Path.home() / '.claude/skills']
    if os.environ.get('MATS_SKILLS_DIR'):
        roots.insert(0, Path(os.environ['MATS_SKILLS_DIR']).expanduser())
    return next((p for root in roots if (p := root / name / 'SKILL.md').is_file()), None)


def first_seen(cwd, session, name):
    # Atomic creation deduplicates simultaneous tool events too. Store no prompts.
    digest = hashlib.sha256(json.dumps([str(cwd), session, name]).encode()).hexdigest()
    root = Path(os.environ.get('MATS_SKILL_HINT_STATE_DIR',
                              str(Path.home() / '.cache/mats-skill-hints')))
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        fd = os.open(root / digest, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return False
    os.close(fd)
    return True


def hint(event):
    if os.environ.get('MATS_SKILL_HINTS') == '0' or not isinstance(event, dict):
        return None
    if event.get('hook_event_name') != 'PostToolUse':
        return None
    session, cwd = event.get('session_id'), event.get('cwd')
    data, tool = event.get('tool_input'), event.get('tool_name')
    if not all(isinstance(x, str) and x for x in (session, cwd, tool)):
        return None
    if not isinstance(data, dict) or not Path(cwd).is_absolute():
        return None
    cwd = Path(cwd).resolve()
    # Reading/invoking a skill counts as handled, without a reminder.
    observed = data.get('skill') if tool == 'Skill' else None
    path = data.get('file_path')
    if tool == 'Read' and isinstance(path, str) and Path(path).name == 'SKILL.md':
        observed = Path(path).parent.name
    if isinstance(observed, str) and observed in RULES.values():
        first_seen(cwd, session, observed)
        return None
    if tool not in RULES or not isinstance(path, str) or Path(path).suffix != '.lean':
        return None
    name = RULES[tool]
    muted = os.environ.get('MATS_SKILL_HINT_MUTE', '').split(',')
    if name in {x.strip() for x in muted}:
        return None
    source = skill_file(name, cwd)
    if source is None or not first_seen(cwd, session, name):
        return None
    return {'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': (
            f"By the way, there's a relevant skill you might want to look at here: "
            f"{name} ({source}). Use it if helpful; no acknowledgement needed."
        ),
    }}


def main():
    try:
        # Bound parsing work; malformed/oversized events simply produce no hint.
        event = json.loads(sys.stdin.read(1_048_577))
        result = hint(event)
        if result:
            print(json.dumps(result))
    except (OSError, ValueError, TypeError, RecursionError):
        pass  # Hints must not interrupt research, including on state I/O failure.


if __name__ == '__main__':
    main()
