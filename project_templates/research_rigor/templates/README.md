# The run directory

Every experiment is **one self-contained run directory**. It is the portable unit
that ships to ephemeral GPU compute and syncs back to the persistent dev node with
results and provenance intact (the sync design is described in the
`mats_dashboards` repo, `docs/auto_alignment_research/architecture.md`). It is
also the contract: every skill reads and writes these files, so a run is
reconstructable from its artifacts alone and work can resume at any stage.

```
outputs/run_<YYYYMMDD_HHMMSS>_<name>/
  metadata.json          # what done means, models, dates, harness, cost, git SHA   [auto]
  prereg.yaml            # hypothesis + falsifier, then design, each frozen once    [human-written, frozen twice]
  provenance.jsonl       # append-only log of agent decisions & tool calls          [auto]
  gates.jsonl            # append-only log of human approval/rejection events        [auto, at each gate]
  evidence.jsonl         # append-only citations for/against each prediction        [as you go]
  attention_checks.jsonl # seeded fake errors + whether the PI caught them          [auto]
  plan/                  # experiment-planning artifacts (candidate designs, rubric)
  code/                  # implementation (delegated-but-validated)
  results/               # raw artifacts, checkpoints, figures
  analysis/              # PI-held interpretation notes
  writeup/               # draft communication + review artifacts
```

## The six machine-readable artifacts

| File | Format | Written by | Purpose |
|---|---|---|---|
| `metadata.json` | JSON object | auto (never hand-edited) | Reproducibility-by-construction. Closes the field's under-reporting gap (Gap 7). Schema: `metadata.schema.json`. |
| `prereg.yaml` | YAML | human writes, tool freezes twice | The commitment device (Gap 1). Two tamper-evident commitment points: hypothesis + prediction + falsifier before the pilot; metric + decision rule + method + confounds + guards after it. Template: `prereg.template.yaml`. |
| `provenance.jsonl` | JSON Lines | auto (append-only) | Every agent decision/tool-call/model-invocation. The audit substrate + the pool the attention-check injector samples real mistakes from. |
| `gates.jsonl` | JSON Lines | auto (append-only) | Each human approval gate: what was reviewed, the decision, how long it took, which attention checks were embedded. |
| `evidence.jsonl` | JSON Lines | agent or human (append-only) | Each run that bears on a prediction, for or against, and how much. Kept apart from the verdict, which a person signs and which is read against it. |
| `attention_checks.jsonl` | JSON Lines | auto (append-only) | Each seeded fake error, its ground truth, and whether the PI caught it. Feeds the rate-based escalation. |

Full field-by-field reference for all six: `schemas.md` in this directory.

## Conventions

- **Timestamps** are ISO-8601 UTC (`2026-07-07T12:00:00Z`).
- **`.jsonl` files are append-only.** Never rewrite a line; correction is a new
  line referencing the old `event_id`. This is what makes provenance tamper-evident.
- **`metadata.json` is never hand-written.** If you're tempted to edit it, the
  capturing tool has a bug — fix the tool.
- **`prereg.yaml` is frozen at two points, each before the results it governs.**
  The `hypothesis` point (hypothesis, prediction, falsifier) before the pilot;
  the `design` point (metric, decision rule, method, confounds, guards) after
  it and before the main run. Once a point's `commitments` entry is set and the
  file is committed to git, changes to it are only allowed as an explicit,
  logged amendment (a new `amendments:` entry), never a silent edit. The pilot
  does not license rewriting the hypothesis or the falsifier.
- **`metadata.json` carries the run's acceptance condition** — what done means,
  written when the run is filed and never edited afterwards.
- The run-dir name is `run_<YYYYMMDD_HHMMSS>_<short_snake_name>` (house convention).
