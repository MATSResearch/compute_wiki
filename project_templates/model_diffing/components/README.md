# `md_components`

Project-agnostic plumbing for **model diffing** — asking what a finetune
actually changed, at the level of activations rather than benchmark scores.

Wiki doc: <https://matsresearch.github.io/compute_wiki/interpretability/model-diffing/>

## Install

From this directory:
```bash
uv pip install -e ".[dev]"
```

Or in another project's `pyproject.toml`:
```toml
[tool.uv.sources]
md-components = { path = "../path/to/model_diffing/components", editable = true }
```

Torch is an **optional extra** (`[torch]`): only `kl`, `acts` and `difflens`
need it. `pairing`, `ranking` and `control` are pure Python, so the analysis and
the verdict run from a saved JSON on a laptop.

## Modules, in the order you use them

| Module | Question it answers | Needs torch |
|---|---|---|
| `pairing` | Is this pair even comparable? `ModelFacts`, `compare`, `assert_comparable`, `tokenizer_fingerprint` | no |
| `kl` | Where do they diverge at the output? `kl_per_token`, `kl_over_prompts`, `kl_from_logits` | yes |
| `ranking` | Is the divergence narrow or diffuse, and bigger than a control's? `summarize`, `concentration`, `excess_over_control`, `overlap` | no |
| `acts` | What do the activations look like on identical inputs? `capture`, `collect_pair`, `PairedActivations` | yes |
| `difflens` | What does the difference direction mean in token space? `logit_lens`, `nearest_tokens`, `cosine` | yes |
| `control` | Is any of this specific to my intervention? `verdict`, `describe` | no |
| `runs`, `io` | run dirs, JSONL | no |

## The three opinions baked in

1. **Check the pair before diffing it.** `pairing.assert_comparable` catches the
   four silent killers — tokenizer mismatch, chat-template mismatch, dtype
   mismatch, different architectures — and reports *all* of them at once, with
   the fix in the message. Each one produces a plausible-looking difference plot
   that means nothing.

2. **Cheap before expensive.** `kl` first, always. A KL sweep tells you whether
   the finetune changed the model everywhere or in a narrow region
   (`ranking.concentration`), and that decides whether a difference-SAE or a
   crosscoder is even the right next step. Training a crosscoder to rediscover
   "the chat model says 'Certainly!'" is a week you don't get back.

3. **A control finetune is not optional.** `control.verdict` takes the three
   numbers that separate your intervention from generic finetuning and returns
   `SPECIFIC_TO_TREATMENT`, `PARTIALLY_SPECIFIC`, or
   `NOT_DISTINGUISHABLE_FROM_ANY_FINETUNE`. There is no way to get a clean
   verdict without supplying the control.

## Smoke test

```bash
uv run python -m md_components._smoke
```

Runs the pure-Python checks, then (with the torch extra) builds a real pair — a
tiny random GPT-2 and a copy with one block's weights perturbed — and runs
KL → paired activations → difference lens on it. Downloads ~2MB, no GPU.

## What's intentionally *not* here

- **Crosscoder training.** Use `science-of-finetuning/diffing-toolkit` (which
  also gives you SAE-difference, PCA, weight amplification and a Streamlit UI),
  or `dictionary_learning` / `clt-training` if you want to own the training loop.
  These components are the cheap tier that tells you whether that's worth doing.
- **SAE training.** SAELens / EleutherAI sparsify.
- **Cross-architecture diffing.** `pairing` deliberately refuses it and points at
  arXiv:2602.11729; it is a research problem, not a config flag.
- **Statistical testing.** `../../docs/engineering/statistics.md` and `scipy`.

## Pitfalls and searchable symptoms

- `ValueError: model pair is not comparable` — read the bullet list; each line
  names the fix. This is the failure you *want*, early.
- `ValueError: logit shapes differ` from `kl_from_logits` — the two models saw
  different tokenisations of the same string. Same tokenizer, same template.
- `KeyError: module(s) not found: ['model.layers.12']` — module paths differ by
  architecture. Print `[n for n, _ in model.named_modules()]`.
- `ValueError: paired activations have different shapes` — the two collections
  didn't see the same tokens; usually padding applied inconsistently.
- `ValueError: difference is identically zero — the models are the same` — you
  loaded the same checkpoint twice, or the finetune didn't save.
- Uniformly huge KL on every prompt including nonsense: tokenizer mismatch, not
  a dramatic finetune.
- A `difference_concentration` near your `top_frac`: the change is diffuse, so
  a single mean difference direction is a poor summary — don't read the logit
  lens output as "what the finetune did" in that case.
