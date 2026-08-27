# Example 1 — The relearning curve

A complete, runnable unlearning experiment at toy scale:

```
implant  ->  measure  ->  unlearn  ->  measure  ->  RELEARNING ATTACK  ->  verdict
```

It implants facts about **entities that do not exist** into `distilgpt2`,
unlearns a subset of them with NPO, then attacks the unlearned checkpoint by
finetuning briefly on **adjacent** data (same format, disjoint entities) and
measures how much of the "forgotten" capability comes back.

CPU-only, no API keys, no dataset downloads (beyond distilgpt2 itself).
`--smoke` takes about a minute; the **full default run took 20 minutes** on a
12-core laptop CPU when we ran it on 2026-08-26 — it is a toy in *scale*, not in
wall-clock, because 220 full-batch SFT steps plus a five-point relearning sweep
is still a lot of CPU forward passes. On a GPU it is minutes. Start with
`--smoke`.

## Why this shape

Most unlearning write-ups report a forget-set score and stop. The published
finding is that this is not enough: unlearning methods generally do not remove
information from the weights, and a small finetune on adjacent data recovers it
(arXiv:2410.08827). So the deliverable of this example is not "capability went
down" — it is the **curve** of capability against relearning steps, and the
verdict that curve licenses.

Note what the verdict vocabulary does *not* contain: there is no `REMOVED`. Fast
recovery is strong evidence against removal; slow recovery is not evidence for
it, because a stronger attack or a latent probe may still find the knowledge
(arXiv:2402.16835). See `ul_components.report`.

## Run it

```bash
uv venv && uv pip install -e ".[dev]"

uv run python -m example_1_relearning_curve.run --smoke      # ~1 minute, sanity check
uv run python -m example_1_relearning_curve.run              # the default toy run
uv run python -m example_1_relearning_curve.run --method graddiff --seed 1
uv run pytest                                                # fast tests, no training
```

Methods: `npo_retain` (default), `npo`, `graddiff`, `ga`. Try `ga` to watch
gradient ascent take the model apart — that is what the unbounded objective does,
and seeing it once is worth more than reading about it.

Every run writes `outputs/run_<ts>_<tag>/` containing `metadata.json` (the exact
config), `results.json` (split, capabilities, curve, verdict) and `summary.txt`.

## An actual run (2026-08-26, defaults, seed 0)

Numbers from `outputs/run_20260826_165432_full_default/results.json`, not an
illustration:

| | forget set (12 Q/A, 6 entities) | retain set (48 Q/A, 24 entities) |
|---|---|---|
| after implant | 1.00 | 1.00 |
| after NPO+retain unlearn (60 steps) | 0.00 | 1.00 |

Utility delta 0.00 — the unlearn took the forget set to zero without touching
the retain set, which is the *best case* and is why the attack matters.

Relearning on 48 adjacent Q/A pairs about retain entities:

```
   steps  capability   recovery
       0       0.000      0.0%
      10       0.000      0.0%
      25       0.083      8.3%
      50       0.000      0.0%
     100       0.083      8.3%

verdict: NO_RECOVERY_UNDER_THIS_ATTACK
```

Read that carefully, because it is the lesson: peak recovery 8% is **not**
"we removed the knowledge". It is "this attack, on this toy, did not get it
back". The non-monotonicity (8% at 25 steps, 0% at 50, 8% at 100) is a single
Q/A pair flickering in and out at n=12 — noise, not a trend, and a reminder that
a toy-scale curve has toy-scale error bars. A real project would run several
seeds and put an interval on each point
([`statistics.md`](../../../../docs/engineering/statistics.md)).

## What the code is

| File | What's in it |
|---|---|
| `src/.../data.py` | Fictitious entities + Q/A pairs. Deterministic, no download. |
| `src/.../modeling.py` | Tokenisation with prompt masking, the SFT loop, the unlearning loop, the generative capability eval. |
| `src/.../pipeline.py` | The experiment, in order. This is the spec — read it first. |
| `src/.../run.py` | CLI. |

Everything reusable lives in `ul_components` (`../../components/`): the split
with its leakage assertion, the three objectives, the relearning sweep, the
scoring, the verdict.

## Things this example does on purpose

- **The attack trains on retain entities, never the forget set.** Finetuning on
  the forget set proves nothing. `RelearnCurve` cannot be constructed without a
  description of what the attack trained on, so a write-up can't quietly omit it.
- **Every step count starts from a fresh copy of the unlearned checkpoint.**
  Otherwise the sweep is one cumulative finetune sampled N times.
- **Capability is measured generatively**, not with multiple choice. A model can
  fail an MCQ and still write the fact out in prose; `evaluate.mcq_gap_warning`
  exists for exactly that gap.
- **Refusal and incapacity are scored separately.** "I can't help with that" is
  not forgetting, and `ForgetScore.warn_if_refusal_dominated` says so in the log.
- **Retain-set capability is reported next to forget-set capability.** Any method
  reaches zero forget capability if you let it destroy the model.

## What this example is NOT

Evidence about unlearning. distilgpt2 with a few dozen invented facts is a
harness demonstration; the dynamics of a real 7B unlearn on TOFU or WMDP are
different in ways that matter. Use it to learn the workflow, then graduate to
**OpenUnlearning** (`locuslab/open-unlearning`) for real methods and benchmarks —
and keep the attack-and-verdict layer, which OpenUnlearning does not give you.
