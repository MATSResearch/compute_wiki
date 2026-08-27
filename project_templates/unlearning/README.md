# Unlearning Project Templates

Starter scaffolds for **machine unlearning / knowledge removal** projects:
making a model stop being able to produce some body of knowledge, and — the part
that decides whether the result means anything — checking whether it actually
stopped.

Wiki doc: [`../../docs/alignment-science/unlearning.md`](../../docs/alignment-science/unlearning.md)

## Layout

```
unlearning/
├── components/                  # ul_components: project-agnostic infra
│   ├── src/ul_components/
│   │   ├── splits.py            # forget/retain split BY KEY + leakage assertions
│   │   ├── losses.py            # gradient ascent, GradDiff, NPO (+ retain variant)
│   │   ├── relearn.py           # framework-agnostic relearning-attack sweep
│   │   ├── report.py            # recovery fraction, verdict, summary table
│   │   ├── evaluate.py          # correct / refused / incapable three-way scoring
│   │   ├── runs.py              # timestamped run dirs + metadata.json
│   │   ├── io.py                # JSONL
│   │   └── _smoke.py
│   ├── pyproject.toml
│   └── tests/
└── example_projects/
    └── example_1_relearning_curve/   # runnable: implant → unlearn → attack → verdict
```

## The workflow these encode

```
implant  ->  measure  ->  unlearn  ->  measure  ->  RELEARNING ATTACK  ->  verdict
```

The published finding you have to engage with is that unlearning methods
generally do **not** remove information from the weights — a small finetune on
adjacent data brings the capability back (arXiv:2410.08827), and knowledge that
looks gone under one probe reappears under another (arXiv:2402.16835). So a
forget-set score on its own is not a result. `ul_components.relearn` runs the
attack, and `ul_components.report` refuses to emit a "REMOVED" verdict.

## When *not* to use these

- **You want 12+ published methods with configs, on TOFU / MUSE / WMDP.** Use
  **OpenUnlearning** (`locuslab/open-unlearning`, arXiv:2506.12618). These
  components are for a bespoke run where you want to see the objective, plus the
  attack-and-verdict layer that a benchmark harness doesn't give you.
- **You only need a single RMU run on WMDP.** The WMDP repo's own script is
  smaller.
- **Your forget target isn't dataset-shaped.** These assume forget/retain
  *splits*; a capability defined by a behaviour rather than a corpus doesn't fit,
  and that mismatch is worth noticing before you write code.

## Components vs. example projects

**Components (`ul_components`)** are the reusable plumbing. Everything except
`losses` is pure Python and needs no torch, so the analysis half runs on a
laptop.

**[`example_1_relearning_curve/`](example_projects/example_1_relearning_curve/)**
is a full, runnable toy experiment: implant facts about entities that don't
exist into distilgpt2, unlearn a subset, attack with relearning on adjacent
data, and print the verdict. CPU, minutes, no API keys.
