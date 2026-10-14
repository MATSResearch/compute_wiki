---
name: protect-heldout-shell
enabled: true
event: bash
pattern: data/heldout|score_final\.sh
action: block
---
This command touches the held-out splits or the final scorer, which only the researcher uses (program.md).
Run ./measure.sh for the dev split and ./checks.sh for the guard floor. If you need something else, stop and ask (pause point P3).
