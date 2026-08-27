# Model Diffing Project Templates

Starter scaffolds for **model diffing**: base model vs finetuned model, at the
level of activations rather than benchmark scores. This is the natural follow-up
to every model-organism project — you made the organism, now what is inside it?

Wiki doc: [`../../docs/interpretability/model-diffing.md`](../../docs/interpretability/model-diffing.md)

## Layout

```
model_diffing/
├── components/                  # md_components: project-agnostic infra
│   ├── src/md_components/
│   │   ├── pairing.py           # is this pair comparable? tokenizer/template/dtype/arch checks
│   │   ├── kl.py                # per-token KL divergence; prompt ranking
│   │   ├── ranking.py           # divergence summary, concentration, excess-over-control, overlap
│   │   ├── acts.py              # paired activation capture on identical inputs
│   │   ├── difflens.py          # difference direction -> logit lens / nearest tokens / cosine
│   │   ├── control.py           # treatment-vs-control verdict
│   │   ├── runs.py              # timestamped run dirs + metadata.json
│   │   ├── io.py                # JSONL
│   │   └── _smoke.py
│   ├── pyproject.toml
│   └── tests/
└── example_projects/
    └── example_1_narrow_finetune_diff/   # (stub) narrow LoRA organism vs base, with a control finetune
```

## The workflow these encode

The wiki's ordering, made executable — cheap before expensive:

1. **`pairing.assert_comparable`** — before anything. Four silent killers
   (tokenizer, chat template, dtype, architecture), all caught in one call.
2. **`kl.kl_over_prompts`** — a KL sweep over a few thousand prompts. Twenty
   minutes, and it tells you whether the finetune changed the model everywhere
   or in a narrow region.
3. **`ranking.concentration`** — narrow or diffuse? Narrow means chase the top
   prompts; diffuse means a single mean difference direction won't summarise it.
4. **`acts.collect_pair` + `difflens.logit_lens`** — the activation difference
   lens: what direction did the finetune push the residual stream in, read out
   in token space.
5. **`control.verdict`** — against a matched control finetune. Without this you
   cannot separate "features of misalignment" from "features of having been
   finetuned at all".

Only then is a crosscoder or difference-SAE worth its training run — and for
that, use `science-of-finetuning/diffing-toolkit` rather than rebuilding it.

## Components vs. example projects

**Components (`md_components`)** are the reusable plumbing: pair checks, KL,
paired activation capture, difference readouts, the control verdict. Small,
stable, vendorable. Two thirds of it is pure Python and needs no GPU stack.

**Example projects** are runnable mini-papers that import the components. See
[`components/README.md`](components/README.md) for the module-by-module map.

## When *not* to use these

- **You have API-only models.** Every method here needs weights and activations.
  Behavioural diffing (paired prompts, matched sampling, a judge) is a different
  doc: [`../../docs/alignment-science/behavioral-safety-playbook.md`](../../docs/alignment-science/behavioral-safety-playbook.md).
- **You want crosscoders.** Use the diffing-toolkit; these components deliberately
  stop at the cheap tier.
- **The two models don't share a tokenizer or architecture.** `pairing` will
  refuse, correctly.
