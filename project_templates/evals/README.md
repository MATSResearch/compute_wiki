# Evals Project Templates

Starter scaffolds for **LLM evaluation** research projects — measuring model
behavior and capability: academic benchmarks, agentic tasks, dangerous-capability
evals, and bespoke behavioral safety tests (sycophancy, deception, refusal, …).

All examples here are built on **Inspect AI** (UK AISI; `inspect-ai` on PyPI,
importable as `inspect_ai`, `UKGovernmentBEIS/inspect_ai` on GitHub, "AISI's eval
framework") — the default open-source framework for serious LLM evals in 2026.

## Layout

```
evals/
├── components/                  # eval_components: project-agnostic infra
│   ├── src/eval_components/
│   │   ├── datasets.py          # dicts/JSONL → Inspect Samples; paraphrase expansion for sensitivity testing
│   │   ├── tasks.py             # simple_qa_task / task_from_solver wrappers over inspect_ai.Task
│   │   ├── scorers.py           # refusal_heuristic + refusal_aware() + refusal_rate metric; the refusal-vs-failure distinction
│   │   ├── running.py           # run_eval / run_eval_set (resume) / retry wrappers over inspect_ai
│   │   ├── analysis.py          # load_evals/load_samples (evals_df/samples_df) + Wilson CIs + accuracy_by_group
│   │   ├── robustness.py        # spread / is_prompt_sensitive over paraphrases & seeds
│   │   ├── contamination.py     # canary-string leakage detection (BIG-bench GUID built in)
│   │   ├── viz.py               # accuracy bars with CIs + paraphrase-spread strip plot
│   │   ├── config.py            # dataclass config + CLI overrides
│   │   ├── runs.py              # timestamped run dirs, metadata.json, logs/ subdir
│   │   ├── tracking.py          # JSONL meta-scalar logger (+ wandb optional)
│   │   ├── seeding.py           # set_seed across Python/NumPy/torch
│   │   ├── io.py                # JSONL read/write, dataclass <-> JSON
│   │   ├── cache.py             # SHA-256 of config → cached log dir
│   │   ├── sweep.py             # cartesian-product sweep (model × paraphrase × seed)
│   │   ├── profiling.py         # Timer context manager
│   │   └── _smoke.py            # no-API smoke test
│   ├── pyproject.toml
│   └── tests/
└── example_projects/
    ├── example_1_sycophancy_eval/      # custom multi-turn behavioral eval (flip-under-pushback)
    │   ├── README.md / CLAUDE.md
    │   ├── data/sycophancy_samples.jsonl
    │   ├── docs/papers/                 # Perez et al. + Sharma et al. summary
    │   ├── src/.../                     # data, prompts, build (solver+scorer), run, analyze
    │   └── tests/
    └── example_2_inspect_evals_gpqa/    # STUB: run a pre-built inspect_evals benchmark across models
        ├── README.md
        └── docs/papers/                 # GPQA summary
```

## Components vs. example projects

**Components (`eval_components`)** are the boring, reusable plumbing — dataset
construction, refusal-aware scoring, confidence intervals, prompt-sensitivity
spread, contamination canaries, run-dir bookkeeping, accuracy plotting. Stable
surface, small, no eval-specific behavior logic. Use these in any new eval
project; they're roughly the bits you'd otherwise rewrite from scratch every time.

**Example projects** are full, runnable mini-evals. Each one imports
`eval_components` for infrastructure and Inspect AI for the actual eval
primitives, implements one eval idea at toy scale (smoke in ~2 min for ~$0.10),
includes a `docs/papers/` summary, and is structured the way the wiki recommends.

## When *not* to use these

- **You want a pre-built benchmark** (MMLU, GPQA, GAIA, SWE-bench, HarmBench,
  AgentHarm, TruthfulQA, …). Use `inspect_evals` directly — 200+ tasks already
  implemented. Check there *before* writing anything. (Example 2 shows the pattern.)
- **You want leaderboard-comparable log-prob academic numbers.** Use
  `lm-evaluation-harness` (EleutherAI); it's the standard for MMLU/ARC/HellaSwag
  and faster for log-prob multiple-choice. See `docs/evaluation/evals.md`.
- **You want long-horizon dangerous-capability / agent time-horizon evals.** Use
  METR's HCAST suite (run via Inspect or `vivaria`). See `docs/evaluation/evals.md`.
- **You want adversarial red-team-vs-blue-team control protocols.** Use the
  `ai_control/` templates (ControlArena). See `docs/oversight-and-control/ai-control.md`.
- **You want a 30-line one-shot script over an API.** Inspect's task structure is
  overhead for trivial evals; use `safety-research/safety-tooling` (see
  `docs/models-and-compute/safety-toolkits.md`).

## Existing libraries vs. these components

`eval_components` is **not** a replacement for Inspect AI or `inspect_evals`. It's
the wiring around them.

| Need | Use this |
|---|---|
| A pre-built benchmark (MMLU, GPQA, HarmBench, …) | `inspect_evals` directly (`inspect eval inspect_evals/{name}`) |
| Define a custom task / solver / scorer | Inspect AI directly (`inspect_ai.Task`, `@solver`, `@scorer`) |
| A one-shot QA task from a dataset + scorer | `eval_components.tasks.simple_qa_task` |
| Wrap a custom multi-turn solver into a Task | `eval_components.tasks.task_from_solver` |
| dicts/JSONL → Inspect Samples (testable, no file) | `eval_components.datasets.samples_from_records` |
| Duplicate samples per prompt phrasing (sensitivity) | `eval_components.datasets.expand_paraphrases` |
| Detect a refusal (pure function) | `eval_components.scorers.refusal_heuristic` |
| Add refusal tracking to any scorer | `eval_components.scorers.refusal_aware` |
| `model_graded_qa` + refusal in one call | `eval_components.scorers.graded_qa_with_refusal` |
| Run one eval / a model × task matrix with resume | `eval_components.running.run_eval` / `run_eval_set` |
| Resume a crashed run | `eval_components.running.retry` |
| Logs → DataFrame | `eval_components.analysis.load_evals` / `load_samples` |
| Accuracy + 95% CI by group (model, category, …) | `eval_components.analysis.accuracy_by_group` |
| Binomial confidence interval (pure) | `eval_components.analysis.wilson_ci` |
| Token-cost summary per model | `eval_components.analysis.token_cost_summary` |
| Variance across paraphrases / seeds | `eval_components.robustness.spread` |
| Flag a prompt-sensitive eval | `eval_components.robustness.is_prompt_sensitive` |
| Benchmark contamination check | `eval_components.contamination.scan_completions` |
| Accuracy bars with CIs / paraphrase strip plot | `eval_components.viz.accuracy_bars` / `paraphrase_spread` |
| Run organization (timestamped dirs, metadata, logs/) | `eval_components.runs.new_run` |
| Config-from-dataclass + CLI overrides | `eval_components.config` |
| Cartesian-product sweep | `eval_components.sweep.grid` |
| Cache eval log dir by config hash | `eval_components.cache.cached_log_dir` |

See [`../../docs/evaluation/evals.md`](../../docs/evaluation/evals.md) for the broader eval
framework landscape (Inspect, lm-eval-harness, METR HCAST, Anthropic/OpenAI eval
formats) and [`../../docs/evaluation/red-teaming.md`](../../docs/evaluation/red-teaming.md) for
jailbreak/refusal benchmarks.

## Inspect AI version pin

These templates target **Inspect AI 0.3.120+** and are verified against 0.3.224
(May 2026). The API used here (`inspect_ai.analysis.evals_df`/`samples_df`,
`eval_set` returning `(success, logs)`, the `@solver`/`@scorer`/`@metric`
decorators, `model_graded_qa(instructions=, model=, model_role=, partial_credit=)`)
has been stable across the 0.3.1xx–0.3.2xx series. `inspect_ai.analysis` was added
mid-0.3.x — on older pins, read logs with `inspect_ai.log.read_eval_log` instead.
