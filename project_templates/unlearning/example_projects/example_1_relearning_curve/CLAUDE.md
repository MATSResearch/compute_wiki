# CLAUDE.md — example_1_relearning_curve

Toy end-to-end unlearning experiment. Read `README.md` first, then
`src/example_1_relearning_curve/pipeline.py` — the pipeline is the spec.

## Rules specific to this project

- **The relearning attack trains on RETAIN entities, never on the forget set.**
  Finetuning on the forget set proves nothing; it just reteaches. If you change
  the attack data, update `adjacent_data_description` — `RelearnCurve` refuses to
  be constructed without one, on purpose.
- **`reset_fn` must return a fresh copy of the unlearned checkpoint** for every
  step count. Continuing to train one model through the sweep measures a single
  cumulative finetune sampled at N points, which is a different experiment.
- **Never emit the word "removed"** about a result here. The verdict vocabulary
  is `SUPPRESSION_NOT_REMOVAL` / `PARTIAL_RECOVERY` /
  `NO_RECOVERY_UNDER_THIS_ATTACK`; that is a deliberate constraint from
  arXiv:2410.08827 and arXiv:2402.16835, not an oversight to fix.
- **Prompt tokens are masked out of the loss** (`IGNORE = -100`). If you touch
  `modeling.encode`, keep the test that asserts it.
- **This is a toy.** distilgpt2 with 30 invented entities is a harness
  demonstration, not evidence about how unlearning behaves at scale. Don't write
  conclusions about unlearning methods from a run of this.

## Conventions

- `uv run python ...`, never bare `python`.
- Every run goes to `outputs/run_<ts>_<tag>/` with `metadata.json`, `results.json`
  and `summary.txt`. Nothing is written outside a run dir.
- `uv run pytest` for the fast tests; `--smoke` for a ~1-minute end-to-end check
  before any long run.
