# Example 1 — Diffing a narrow finetune against its base (stub)

**Status: stub.** The scaffold, the intended design and the pitfalls are written
down; the code is not implemented yet. `md_components` (which this would import)
is complete and tested, and the unlearning area has a fully runnable example
([`../../../unlearning/example_projects/example_1_relearning_curve/`](../../../unlearning/example_projects/example_1_relearning_curve/))
if you want a worked end-to-end template today.

## What it would do

Take a small base model, produce **two** finetunes of it, and diff both against
the base:

- **treatment** — a narrow finetune that installs some behaviour (the
  emergent-misalignment shape: narrow training data, broad behavioural effect).
- **control** — a finetune of *matched size, steps and learning rate* on
  innocuous data.

Then run the cheap-before-expensive ladder from
[`../../../../docs/interpretability/model-diffing.md`](../../../../docs/interpretability/model-diffing.md):

1. `pairing.assert_comparable` on both pairs.
2. `kl.kl_over_prompts` over a held-out prompt set, for both pairs.
3. `ranking.concentration` — is the treatment's change narrow?
4. `ranking.excess_over_control` and `ranking.overlap` — is it bigger than, and
   different from, the control's?
5. `acts.collect_pair` + `difflens.logit_lens` on the treatment pair, and
   `difflens.cosine` between the treatment and control difference directions.
6. `control.verdict` — the label that decides what you're allowed to claim.

## The result it is designed to make hard to fake

The interesting outcome is not "we found N features". It is the **control
comparison**: how much of what you found is your intervention, and how much is
what any finetune does at that learning rate. A stub that only diffed the
treatment against the base would reproduce the most common flaw in this genre.

## Why it is narrow on purpose

Narrow finetunes (a LoRA on a few thousand examples — i.e. most MATS model
organisms) are the *hardest* diffing regime: the true difference is small
relative to the noise floor, which is what arXiv:2603.04426 (Delta-Crosscoder)
addresses. An example project that used a huge finetune would look great and
teach the wrong lesson about how easy this is.

## If you are picking this up

Start from the unlearning example's shape (`data.py` / `modeling.py` /
`pipeline.py` / `run.py`, a `--smoke` flag, everything into one timestamped run
dir), import `md_components`, and keep the whole thing CPU-runnable at toy scale.
