# `ul_components`

Project-agnostic plumbing for **LLM unlearning** projects: forget/retain splits
that can't silently leak, the three baseline objectives written out, and the
relearning-attack harness that decides whether your unlearning removed anything
or merely suppressed it.

Wiki doc: <https://matsresearch.github.io/compute_wiki/alignment-science/unlearning/>

## Install

From this directory:
```bash
uv pip install -e ".[dev]"
```

Or in another project's `pyproject.toml`:
```toml
[tool.uv.sources]
ul-components = { path = "../path/to/unlearning/components", editable = true }
```

Torch is an **optional extra** (`[torch]`), because only `losses` needs it. The
analysis half — splits, scoring, relearning curves, verdicts — runs on a laptop
with nothing heavy installed, which is where you'll actually be when you're
staring at the curve.

## Modules

| Module | What it gives you | Needs torch |
|---|---|---|
| `splits` | `make_split` (partitions by **key**, not by row), `assert_no_leakage`, `substring_leakage` | no |
| `losses` | `gradient_ascent_loss`, `grad_diff_loss`, `npo_loss`, `npo_with_retain`, `sequence_logprob` | yes |
| `relearn` | `relearn_sweep` — framework-agnostic relearning attack; `RelearnCurve` | no |
| `report` | `recovery_fraction`, `steps_to_recovery`, `verdict`, `summarize` | no |
| `evaluate` | `classify` (correct / refused / incapable), `score_forget_set`, `mcq_gap_warning`, `utility_delta` | no |
| `runs` | `new_run(tag)` → timestamped `outputs/run_<ts>_<tag>/` with metadata.json | no |
| `io` | `read_jsonl`, `write_jsonl`, `dataclass_to_dict` | no |

## The three opinions baked in

These are the parts that are not neutral plumbing. They exist because the
unlearning literature says the obvious version of the experiment gives the wrong
answer.

1. **Splits partition by key.** TOFU forgets *authors*; MUSE forgets
   *documents*. A row-level split puts some rows about an entity in forget and
   others in retain, so retain re-teaches what forget removes. `assert_no_leakage`
   is one line and turns a silent confound into a crash.

2. **There is no `REMOVED` verdict.** `report.verdict` returns
   `SUPPRESSION_NOT_REMOVAL`, `PARTIAL_RECOVERY`, or
   `NO_RECOVERY_UNDER_THIS_ATTACK`. Fast recovery is strong evidence against
   removal; slow recovery is *not* evidence for it, because a stronger attack or
   a latent probe may still find the knowledge (arXiv:2402.16835,
   arXiv:2410.08827). The vocabulary refuses to let you overclaim.

3. **Refusal and incapacity are scored separately.** `evaluate.classify` is
   three-way. A model that says "I can't help with that" has not unlearned
   anything, and `ForgetScore.warn_if_refusal_dominated` says so out loud.

## Smoke test

```bash
uv run python -m ul_components._smoke
```

Builds a split, scores a forget set, runs a relearning sweep against a stub
model that mimics suppression, prints the verdict, and (if the torch extra is
installed) runs one step of each loss on random logits. No downloads, no GPU, no
API keys. If this fails, the components are broken before any project-specific
code matters.

## What's intentionally *not* here

- **A training loop.** Use OpenUnlearning (`locuslab/open-unlearning`) if you
  want 12+ published methods over TOFU / MUSE / WMDP with configs; use TRL or a
  plain HuggingFace `Trainer` for a bespoke run. `losses` gives you the
  objective, not the harness.
- **Benchmark datasets.** TOFU, MUSE and WMDP live on HuggingFace; WMDP is gated.
- **A refusal classifier.** `looks_like_refusal` is a substring heuristic for
  cheap triage. For anything published, use Llama Guard / WildGuard / an LLM
  judge and validate on hand labels.
- **Plotting.** The curve is four columns; `matplotlib` directly is fine, and
  the wiki's `research-plots` doc covers the presentation.

## Pitfalls and searchable symptoms

- `ValueError: N key(s) appear in BOTH forget and retain` — you built the split
  by row. Split by key.
- `ValueError: baseline equals post-unlearning capability` from `report` — the
  unlearning run didn't change the forget score, so there is no recovery to
  measure. Fix the unlearning before running the attack.
- `ValueError: step_counts must include 0` — the curve needs its post-unlearning
  anchor, otherwise recovery has no origin.
- `nan loss after step N` while using `gradient_ascent_loss` — expected. GA is
  unbounded; that's why it's the floor and not the recommendation. Switch to
  `npo_loss` or add a retain term.
- A relearning curve that is monotonically increasing *and* smooth across step
  counts often means `reset_fn` isn't returning a fresh checkpoint — you're
  measuring one cumulative finetune, not independent attacks.
