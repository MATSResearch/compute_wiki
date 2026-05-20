# `eval_components`

Project-agnostic plumbing for **LLM evaluation** projects. A thin wrapper around **Inspect AI** (`inspect-ai` on PyPI, importable as `inspect_ai`, `UKGovernmentBEIS/inspect_ai` on GitHub, "AISI's eval framework"). Each module is a **self-contained unit**: use the ones you need, vendor (copy) the ones you want to modify, ignore the rest.

`eval_components` is **not** a replacement for Inspect AI or `inspect_evals`. It's the wiring around them — run dirs, dataset/paraphrase construction, refusal-aware scoring, confidence intervals, prompt-sensitivity spread, contamination canary checks, accuracy plotting. The tasks, solvers, and base scorers come from Inspect.

## Install

From this directory:
```bash
uv venv --python 3.11
uv pip install -e .[dev]
```

Inspect AI and pandas are required dependencies — they install automatically. No model API keys are needed to *import* the package or run the smoke test; they're only needed when you actually run an eval (`running.run_eval`).

## Modules

### Core infrastructure

| Module | What it gives you |
|---|---|
| `config` | Dataclass → CLI override → file load. Avoids a Hydra dependency. Unknown keys fail loud. |
| `runs` | `new_run(tag)` → timestamped `outputs/run_<ts>_<tag>/` dir with metadata.json + a `logs/` subdir for Inspect AI `.eval` logs. |
| `tracking` | `Tracker` writing run-level meta-scalars to a JSONL file (and wandb if installed). Per-sample data stays in Inspect's logs; this is for rollups (cost, mean accuracy + CI). |
| `seeding` | `set_seed` (Python/NumPy/torch). Seeds the *harness* (paraphrase shuffle, few-shot order); does not make model generations deterministic. |

### Eval-specific

| Module | What it gives you |
|---|---|
| `datasets` | `samples_from_records()` (dicts → `MemoryDataset`, testable without a file), `expand_paraphrases()` (duplicate each sample per reworded prompt for sensitivity testing), `record_to_sample_fn()` (field-mapper for `json_dataset`). |
| `tasks` | `simple_qa_task()` (dataset + optional system prompt + generate + scorer → `Task`), `task_from_solver()` (wrap a custom multi-turn solver). |
| `scorers` | `refusal_heuristic()` (pure refusal detector), `refusal_aware()` (wrap any scorer to add a `refused` flag + `refusal_rate()` metric), `predicate_scorer()`, `graded_qa_with_refusal()` (`model_graded_qa` + refusal). The refusal-vs-failure distinction is the headline feature. |
| `running` | `run_eval()` (wraps `inspect_ai.eval`), `run_eval_set()` (wraps `eval_set` for a model × task matrix with resume), `retry()` (wraps `eval_retry`). |
| `analysis` | `load_evals()` / `load_samples()` (wrap `evals_df` / `samples_df`), `wilson_ci()` (pure-Python binomial CI), `accuracy_by_group()` (accuracy + CI sliced by any metadata column), `token_cost_summary()`. |
| `robustness` | `spread()` / `spread_from_groups()` (variance across paraphrases/seeds), `is_prompt_sensitive()` (flag evals whose accuracy range across phrasings exceeds a threshold). |
| `contamination` | `check_canary()` / `scan_completions()` — detect benchmark canary-string leakage (BIG-bench GUID built in). Pure functions. |

### Operations / ergonomics

| Module | What it gives you |
|---|---|
| `viz` | `accuracy_bars(groups)` — per-group accuracy with Wilson CI error bars. `paraphrase_spread(accuracies)` — strip plot of per-paraphrase accuracy. (matplotlib optional — install with `[viz]`.) |
| `io` | `read_jsonl`, `write_jsonl`, `dataclass_to_json`, `dataclass_from_json`. |
| `cache` | `cached_log_dir(payload)` — name a run's log dir by SHA-256 of its config; skip the eval when the dir already exists. |
| `sweep` | `grid({'model': [...], 'paraphrase_idx': [...], 'seed': [...]})` cartesian-product sweep. |
| `profiling` | `Timer` context manager. |

## What's intentionally *not* here

- **Tasks, solvers, and base scorers themselves** — those are Inspect AI. We re-export / wrap for convenience, but the implementation is upstream.
- **Pre-built benchmarks** — use `inspect_evals` (`UKGovernmentBEIS/inspect_evals`, 200+ tasks: MMLU, GPQA, GAIA, SWE-bench, HarmBench, AgentHarm, …). Always check there before re-implementing a known benchmark.
- **Agentic / sandboxed eval scaffolding** — build the `Task` directly with Inspect's `react()` agent + a Docker/k8s sandbox. This convenience layer covers one-shot and simple multi-turn evals.
- **Log-prob academic benchmarking** — for leaderboard-comparable MMLU/ARC/HellaSwag numbers, `lm-evaluation-harness` (EleutherAI) is the standard; see `docs/03_evals.md`.
- **A statistically rigorous grader-validation pipeline** — `refusal_heuristic` and model-graded scorers are heuristics. Validate against human labels before publishing.

## Smoke test

```bash
uv run python -m eval_components._smoke
```

Imports every module, exercises datasets / refusal heuristic / Wilson CI / spread / contamination / sweep / io against fake data, writes a run dir, exits. Does NOT call Inspect's `eval()` or any model API (those need keys + cost). If this fails the components are broken before any project-specific code matters.

## Module dependency graph

```
tasks        →  inspect_ai (Task, solver, scorer)
scorers      →  inspect_ai.scorer, inspect_ai.solver
running      →  inspect_ai (eval, eval_set, eval_retry)
analysis     →  inspect_ai.analysis (evals_df, samples_df), pandas
datasets     →  inspect_ai.dataset (Sample, MemoryDataset)
robustness   →  analysis  (GroupAccuracy)
viz          →  analysis  (GroupAccuracy) + lazy matplotlib
```

Everything else (`config`, `runs`, `tracking`, `seeding`, `io`, `cache`, `sweep`, `profiling`, `contamination`) is stdlib + (sometimes) pandas/numpy only. `contamination`, `wilson_ci`, `spread`, and `refusal_heuristic` are pure functions — unit-testable with no API call.

## Pitfalls and searchable symptoms

- **`KeyError: 'model'` or `'token...'` from `analysis.token_cost_summary`**: `evals_df` column names shift across Inspect versions. The function fails loud rather than reporting cost 0; check `load_evals(log_dir).columns` and adjust.
- **`refusal_rate()` reads `0.0` even though the model refused**: the `refused` flag lives in score *metadata*, which only exists if you scored with `refusal_aware()` / `predicate_scorer()` / `graded_qa_with_refusal()`. A bare `model_graded_qa()` won't populate it.
- **`eval_set` "log_dir is required" / silently redoing finished tasks**: `eval_set` needs a *dedicated* `log_dir` per logical run to track completion. Reusing a previous run's dir resumes it; passing none errors.
- **Model grading its own output**: if you don't pass `model=` (or set the `grader` model role) to `model_graded_qa`, the grader defaults to the model under test. Always use a separate, capable grader.
- **`is_prompt_sensitive` returns True on a "good" eval**: that's the point — a >10-point accuracy range across paraphrases means a single-phrasing number is not reportable. Aggregate over paraphrases or quote the range.
- **Wide Wilson CIs**: not a bug. `wilson_ci(k, 20)` is wide because n=20 is small. Run more samples before reading small gaps between models.

## Inspect AI version

`eval_components` targets **Inspect AI 0.3.120+** (the API used here — `inspect_ai.analysis.evals_df`/`samples_df`, `eval_set` returning `(success, logs)`, `model_graded_qa(instructions=, grade_pattern=, partial_credit=, model=, model_role=)`, the `@scorer`/`@metric` decorators — has been stable across the 0.3.1xx–0.3.2xx series; verified against 0.3.223, May 2026). If you pin something older, check that `inspect_ai.analysis` exists (it was added mid-0.3.x); before that, read logs with `inspect_ai.log.read_eval_log`.

See [`../../docs/03_evals.md`](../../docs/03_evals.md) for the broader eval-framework landscape (Inspect, lm-eval-harness, METR HCAST, Anthropic evals) and [`../../docs/04_red_teaming.md`](../../docs/04_red_teaming.md) for jailbreak/refusal benchmarks.
