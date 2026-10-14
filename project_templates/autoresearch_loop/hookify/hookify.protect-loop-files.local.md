---
name: protect-loop-files
enabled: true
event: file
tool_matcher: Edit|Write|MultiEdit
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: (^|/)(data/heldout/|measure\.sh$|checks\.sh$|score_final\.sh$|program\.md$|results\.jsonl$)
---
This file belongs to the researcher in this autoresearch loop (program.md, "Who owns what").
The held-out data, the measurement and check scripts, program.md and results.jsonl are not edited by the agent.
Append to results.jsonl with log_result.py. For anything else, stop and ask the researcher (pause point P3).
