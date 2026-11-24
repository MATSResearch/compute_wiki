# `eval_components`

Project-agnostic plumbing for **LLM evaluation** projects. A thin wrapper around **Inspect AI** (`inspect-ai` on PyPI, importable as `inspect_ai`, `UKGovernmentBEIS/inspect_ai` on GitHub, "AISI's eval framework"). Each module is a **self-contained unit**: use the ones you need, vendor (copy) the ones you want to modify, ignore the rest.

`eval_components` is **not** a replacement for Inspect AI or `inspect_evals`. It's the wiring around them — run dirs, dataset/paraphrase construction, refusal-aware scoring, confidence intervals, prompt-sensitivity spread, contamination canary checks, accuracy plotting. The tasks, solvers, and base scorers come from Inspect.

## Install

From this directory:
```bash
uv sync --all-extras     # installs the locked versions (inspect-ai 0.3.290); Python >= 3.11
uv run pytest -q
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
- **Log-prob academic benchmarking** — for leaderboard-comparable MMLU/ARC/HellaSwag numbers, `lm-evaluation-harness` (EleutherAI) is the standard; see `docs/evaluation/evals.md`.
- **A statistically rigorous grader-validation pipeline** — `refusal_heuristic` and model-graded scorers are heuristics. Validate against human labels before publishing: Inspect Scout validation sets (`validation_set()`, `scout scan ... -V`) with a held-out `test` split are the built-in route, and HiBayES (UK AISI) models grader effects on 0–10 scores. See `docs/evaluation/evals.md` ("Judge calibration and eval-result tooling").

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
- **Model-graded score moved after upgrading Inspect**: the default `model_graded_qa()` prompt and verdict parsing changed in 0.3.288; re-grade both arms on one version (see "Inspect AI version" below).
- **`is_prompt_sensitive` returns True on a "good" eval**: that's the point — a >10-point accuracy range across paraphrases means a single-phrasing number is not reportable. Aggregate over paraphrases or quote the range.
- **Wide Wilson CIs**: not a bug. `wilson_ci(k, 20)` is wide because n=20 is small. Run more samples before reading small gaps between models.
- **Wilson CIs that are too narrow**: `wilson_ci` treats every sample as independent. Paraphrase expansions (`expand_paraphrases`), several questions per passage, or multiple epochs of one item are clustered, and the interval understates uncertainty; see `docs/evaluation/eval-statistics.md` for clustered intervals (Inspect's `stderr(cluster=...)` / `ci_wilson(cluster=...)`).

## Inspect AI version

`eval_components` requires **Inspect AI ≥ 0.3.288** and is locked and tested on
0.3.290 (`uv.lock`, 2026-11-23; Python ≥ 3.11, which Inspect has required since
0.3.281). The floor is 0.3.288 because it fixes two bugs that changed results with
no error on paths used here:

- **`cache=True`**: the output cache key did not include the model's constructor
  arguments, so one model under two `-M` / `model_args` settings could be served
  the other's cached answer.
- **`model_graded_qa()`** (`scorers.graded_qa_with_refusal`): a reply that quoted a
  grade and ended with a verdict line in an unrecognised form was scored from the
  quoted grade; it is now unscored. The default grading template also changed
  (fields are wrapped in markers with a random code), so grades "can shift
  slightly" and cached grader responses are not reused. **Do not compare
  model-graded numbers across 0.3.288** — grade both arms on one version.

Newer than the lockfile (the one-week dependency cooldown in `pyproject.toml` skips
them until they are a week old): 0.3.291 (2026-11-17) stops writing remote MCP
server credentials into eval logs — upgrade first if you add MCP tools; 0.3.292
(2026-11-23) fixes `--seed` being dropped for `google/` models. Also since 0.3.288,
`web_browser()` raises `PrerequisiteError` (use `web_search()` or `computer()`).
Details: `docs/evaluation/inspect-ecosystem.md` ("Inspect AI 0.3.288–0.3.292").

See [`../../../docs/evaluation/evals.md`](../../../docs/evaluation/evals.md) for the broader eval-framework landscape (Inspect, lm-eval-harness, METR HCAST, Anthropic evals) and [`../../../docs/evaluation/red-teaming.md`](../../../docs/evaluation/red-teaming.md) for jailbreak/refusal benchmarks.
