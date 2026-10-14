# program.md — instructions for the agent running this loop

The researcher writes and edits this file; the agent reads it and does not edit
it. The shape follows karpathy/autoresearch's `program.md`, with stopping points
for the researcher put back in.

## Fill in before starting (researcher)

- **Objective:** <one sentence: what should get better, and why it matters>
- **Metric:** `<name>` as printed by `measure.sh`; **<lower|higher>** is better
- **Editable files** (the agent changes these and nothing else): `<train.py>`
- **Per-run budget:** <N> minutes (`measure.sh` enforces the timeout)
- **Max experiments this session:** <N>
- **Check in every:** <K> experiments
- **Run directory:** `outputs/run_<YYYYMMDD_HHMMSS>_<tag>/`
- **Branch:** `autoresearch/<tag>`

## Who owns what

| Path | Owner | The agent may |
|---|---|---|
| `program.md` | researcher | read |
| `measure.sh` | researcher | read, run |
| `checks.sh` | researcher | read, run |
| `score_final.sh` | researcher | nothing — do not run it |
| `data/heldout/` (guard and final splits) | researcher | nothing — do not read, list, copy or write it, directly or through a script |
| the editable files above | agent | edit, commit |
| `<run dir>/results.jsonl` | agent | append, only through `log_result.py` |
| `<run dir>/logs/` | agent | write |

## Pause points: stop and wait for the researcher

- **P0 — setup.** Before any run: restate the objective, metric and direction,
  the editable files, the budgets, and the branch name. Create the run
  directory and write `metadata.json` (the fields above, plus the git SHA you
  are starting from and the model IDs in use). Wait for "go".
- **P1 — baseline and noise floor.** Run the unchanged code three times
  (`kind: baseline`, `status: keep` for the first, `kind: rerun` for the other
  two). Report the three values and their spread. That spread is the noise
  floor for the keep rule below. Wait for the researcher to confirm or adjust
  the floor.
- **P2 — check-in, every K experiments.** Report: kept changes, discards with
  their reasons, crashes, the current best against the baseline, and the leads
  you have noticed but not tried. Then answer in your own words: "What is your
  goal right now?" Wait.
- **P3 — anything outside scope.** A new dependency, a change to any file you do
  not own, a different budget or timeout, a different metric: ask first, and do
  not work around a refusal.
- **P4 — repeated failure.** The same idea fails twice in a row, or three runs in
  a row crash: stop and report what you tried and what you think is wrong.
- **P5 — before any claim, and at the end.** At the experiment limit, when told
  to stop, or before stating that something works: stop, summarise, and propose
  (a) a grouping of kept commits into branches that do not share files, each
  starting from the branch point, and (b) a re-measurement of the best version
  against the baseline (several runs each). Wait. The researcher runs
  `score_final.sh`, once.

## The loop

1. **Read the state.** `git log --oneline` on this branch, the last lines of
   `results.jsonl`, and the `rollback_reason` of every discard so far.
2. **Write the bet first.** Decide the change, then write down the hypothesis
   and what you predict the metric will do — these go in `--hypothesis` and
   `--prediction` when you log, and must be decided before you see the result.
3. **Edit only the editable files**, then `git commit`.
4. **Measure:** `./measure.sh <run dir>/logs/<run>.log > <run dir>/logs/<run>.metrics`.
   A non-zero exit is a crash: read the log tail, fix a trivial bug and re-run
   at most once, otherwise log `crash` with the reason and revert.
5. **Keep rule.** If the metric improved by **more than the noise floor from P1**,
   run `./checks.sh`. If it passes, keep the commit (`status: keep`). If it
   fails, log `checks_failed` and revert. An improvement inside the noise floor
   is not a keep: log `discard`, or, if it looks promising, re-run the same
   commit as `kind: rerun` and decide on the repeated measurements.
6. **Revert a non-keep:** `git reset --hard HEAD~1`. The run directory is
   untracked, so the record survives.
7. **Log it** with `log_result.py` (every run, whatever its status). For
   `discard`, `crash` and `checks_failed`, give a `--rollback-reason` that names
   the assumption that made the idea fail, not just "worse".
8. **Before choosing the next experiment**, ask (pi-autoresearch's question):
   "Before choosing the next experiment, consider whether this result or
   discovery invalidates a previous discard's rollback reason. If so, name what
   changed and weigh a targeted retry against other candidates. Otherwise, move
   on. Don't revive a discarded idea without a changed assumption. Verification
   reruns to resolve measurement noise are separate." A deliberate retry sets
   `--revisits-run <earlier run>` and says in `--description` what changed.
9. After every K experiments, go to **P2**. At the limit, go to **P5**.

## Do not

- Read, list, copy or write anything under `data/heldout/`, or run
  `score_final.sh` — not directly, not through a script you write.
- Edit `measure.sh`, `checks.sh`, `score_final.sh` or this file.
- Rewrite or delete lines of `results.jsonl`; a correction is a new line.
- Install packages or change the per-run budget (that is P3).
- Report a number as a result before P5. The loop's best score was selected on
  noise as well as signal; the re-measurement and the final split decide.

## Simplicity

All else equal, simpler is better. A gain inside the noise floor that adds
complexity is a discard; removing code without losing performance is a keep.
