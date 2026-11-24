# `ac_components`

Project-agnostic plumbing for **AI Control** projects. A thin wrapper around **ControlArena** (`control-arena` on PyPI, `UKGovernmentBEIS/control-arena` on GitHub, also called the "AISI control framework") and **Inspect AI**. Each module is a **self-contained unit**: use the ones you need, vendor (copy) the ones you want to modify, ignore the rest.

`ac_components` is **not** a replacement for ControlArena. It's the wiring around it — run dirs, threshold calibration on held-out honest data, pareto plotting, transcript loading. The actual settings, policies, monitors, and protocols come from ControlArena.

## Install

From this directory:
```bash
uv sync --extra dev      # installs the locked versions (control-arena 20.1.1); Python >= 3.11
uv run pytest -q
```

ControlArena and Inspect AI are required dependencies — they install automatically. ControlArena's docker-backed settings additionally need Docker running (used by Apps, Bash, IAC, Infra, SWE-bench Django).

## Modules

### Core infrastructure

| Module | What it gives you |
|---|---|
| `config` | Dataclass → CLI override → file load. Avoids a Hydra dependency. |
| `runs` | `new_run(tag)` → timestamped `outputs/run_<ts>_<tag>/` dir with metadata.json + a `logs/` subdir for Inspect AI eval logs. |
| `eval` | `build_config()`, `build_tasks()`, `run_eval(tasks, config=, log_dir=)` — wraps `ControlEvalConfig` + `get_control_task_product` + `inspect_eval(**config.eval_args())` so common eval shapes are one call. `ModelRoles` dataclass for trusted+untrusted pair. |
| `tracking` | `Tracker` writing meta-scalars to a JSONL file in the run dir (and wandb if installed). Inspect AI handles per-sample scoring; this is for run-level summary scalars. |
| `seeding` | `set_seed` (Python/NumPy/torch). Control evals are stochastic; always seed. |

### Control-specific math + orchestration

| Module | What it gives you |
|---|---|
| `policies` | `untrusted_pair()` — bundles honest + attack into a mode-aware untrusted policy. Re-exports `attack_policy_builder`, `honest_policy_builder`, `trusted_policy_builder`, `untrusted_policy_builder`, `trusted_baseline`. |
| `monitors` | `basic_trusted_monitor()`, `ensemble_trusted_monitor()`, `custom_monitor` decorator. Re-exports `MonitorResponse`, `MonitorScoreRange`. |
| `protocols` | `dtt_pair()` for defer-to-trusted. Re-exports the four built-in builders: `defer_to_trusted_builder`, `defer_to_resample_builder`, `trusted_editing_builder`, `trusted_monitoring_builder`. |
| `audit` | `compute_threshold_from_budget(honest_scores, audit_budget)` — picks the suspicion threshold that flags exactly `audit_budget` fraction of honest samples (the test-leak-free calibration). `holdout_split` for fair calibration. |
| `metrics` | Re-exports `compute_safety`, `compute_usefulness`, `samples_df`, `scale_usefulness`, `compute_suspicion_threshold`. Adds `pareto_curve()` over a defer-threshold sweep (grouped on `micro_protocol_info["defer_threshold"]`). `ac_components` audit budgets are fractions; ControlArena's are percents — `pareto_curve` converts. |
| `loaders` | `load_samples(log_dir)` → DataFrame. `honest_suspicion_scores`, `attack_suspicion_scores` (raise on a sample with no score), `defer_thresholds`, `list_protocols`. |
| `transcript` | `iter_trajectories(log_path)` → Trajectory objects with per-step tool calls, suspicion scores, main/side task success — for hand-inspecting one sample at a time. |
| `probe_monitor` | `make_probe_monitor(probe_path, extract_activations_fn)` — wire a learned activation probe in as a ControlArena monitor (instead of the standard chat-based suspicion-score prompt). Stub for the active "probe-as-monitor" research direction. |

### Operations / ergonomics

| Module | What it gives you |
|---|---|
| `viz` | `pareto_plot(points, out_path)` — safety/usefulness curve PNG. `suspicion_histogram(honest, attack, threshold)` — overlaid distribution plot. (matplotlib is optional — install with `[viz]`.) |
| `io` | `read_jsonl`, `write_jsonl`, `dataclass_to_json`, `dataclass_from_json`. |
| `cache` | `cached_log_dir(payload)` — name an Inspect log dir by SHA-256 of its config; skip the eval when the dir already exists. |
| `sweep` | `grid({'thr': [...], 'seed': [...]})` cartesian-product sweep over a dict of axes. |
| `profiling` | `Timer` context manager — control evals are minutes-to-hours; know where the time goes. |

Run-level tests: `tests/test_components.py` (pure Python) and `tests/test_control_arena_offline.py`, which runs a toy setting through the real ControlArena stack with `mockllm` (no API key, no Docker) and is the check that these wrappers still match the installed ControlArena.

## What's intentionally *not* here

- **Settings, policies, monitors, micro-protocols themselves** — those are in ControlArena. We re-export the builders for convenience, but the implementation is upstream.
- **Inspect AI internals** — use Inspect directly when you need to define a custom solver or scorer outside the control framing.
- **Probe training** — `probe_monitor` only wires a *trained* probe into the monitor interface. Train probes with `mi_components.activations` + scikit-learn, or with Anthropic's probing-for-sleeper-agents code.
- **Distributed eval orchestration** — use Inspect's `eval_set` (re-exported via the upstream API) or a job scheduler.
- **Hyperparameter search beyond grid** — use Optuna or Ray Tune.

## Smoke test

```bash
uv run python -m ac_components._smoke
```

Imports every module, exercises calibration / sweep / io / runs against fake data, writes a run dir, exits. Does NOT run an eval. If this fails the components are broken before any project-specific code matters.

## Module dependency graph

```
eval         →  control_arena, inspect_ai
monitors     →  control_arena.monitor
policies     →  control_arena.policy
protocols    →  control_arena.micro_protocol
metrics      →  control_arena.analysis
loaders      →  control_arena.analysis
transcript   →  inspect_ai.log
probe_monitor → monitors  (lazy torch / sklearn import)
viz          →  (lazy matplotlib import)
```

Everything else (`config`, `runs`, `audit`, `tracking`, `io`, `seeding`, `cache`, `sweep`, `profiling`) is stdlib + numpy only.

## Pitfalls and searchable symptoms

- **`KeyError: 'score_max_suspicion_scorer'` from `loaders.honest_suspicion_scores`**: the tasks were built without `monitoring_scorers=[max_suspicion_scorer()]` (`build_tasks` adds it by default).
- **`ValueError: ... samples have no max_suspicion_scorer score`**: in those trajectories the monitor never ran (the policy made no tool call). Look at them with `transcript.iter_trajectories`.
- **`KeyError: 'protocol'` in older analysis code**: `samples_df` has no `protocol` column in 20.x; use `micro_protocol_info` (`loaders.defer_thresholds`).
- **`compute_safety(...)` is 0.0 or 1.0 at every threshold**: check the audit-budget units first — upstream takes a percent, so `audit_budget=0.05` there means 0.05%. Then increase `limit=` (more samples = finer threshold) and check `suspicion_histogram` to confirm honest+attack distributions actually separate.
- **`docker: command not found` from a setting like `AppsSetting`**: ControlArena settings run untrusted code in Docker. Install Docker, or pass `sandbox_type="local"` (only safe with policies you trust — defeats the threat-model isolation otherwise).
- **`ValueError: trusted model stronger than untrusted` or similar surprise outcomes**: you set both `untrusted_model` and `trusted_model` to frontier models. The whole point of AI Control is that trusted is strictly weaker. Pick a smaller model for the trusted role (e.g. `claude-haiku-4-5-20251001` for trusted vs `claude-sonnet-4-6` for untrusted).
- **Threshold calibrated on the same data evaluated against**: leaks the test set. Always use `audit.holdout_split` before `compute_threshold_from_budget`.
- **Suspicion scores all clustered at 0.0 (or another single value)**: the monitor is degenerate. Inspect a few trajectories with `transcript.iter_trajectories` — usually the monitor's replies have no `<score>...</score>` tag, which ControlArena records as the default score 0.0 with `score_parsed=False` rather than as an error.

## ControlArena versions

These templates target **ControlArena 20.1.1** (2026-10-22, the current release) on **Inspect AI ≥ 0.3.288**, Python ≥ 3.11 (both packages require it; the tests pass on 3.11, 3.13 and 3.14). Each directory has a `uv.lock`; `uv sync --extra dev` installs exactly what the tests ran against.

Why the floors (`pyproject.toml`):

- `control-arena>=20.1.1` — silent-correctness fixes on paths this template uses: the APPS scorer graded runs by stderr instead of exit status, which understated backdoor success and overstated safety (PR #914); defer-to-trusted monitors saw the wrong tool call when a reply called the same tool twice (PR #924); negative monitor scores lost their sign (PR #877). 20.1.0 fixed defer-to-resample (the chosen resample was never executed, PR #901) and `eval_set` reusing a log built from a different custom dataset (PR #906), and changed the default models (PR #902) — this template always sets models explicitly.
- `inspect-ai>=0.3.288` — the output cache key ignored model constructor args before it; the policies and monitors here use `cache=True`.

**Numbers are not comparable across ControlArena versions** (v18, v19 and v20 are breaking releases; APPS scoring changed in 20.1.1). The example project's `run.py` writes both package versions into `metadata.json`; re-run a baseline rather than reuse one from an older version. The published APPS dataset's `backdoor_works` flags were computed with the pre-20.1.1 rule and may mislabel samples that write to stderr until the dataset is regenerated.

API facts that differ from older write-ups (all checked against the installed 20.1.1 source):

- `control_arena.micro_protocol` exports four builders: `trusted_monitoring_builder`, `defer_to_trusted_builder`, `trusted_editing_builder`, `defer_to_resample_builder`. There is no `trusted_only` / `untrusted_only`: pass a policy directly as the micro-protocol.
- `audit_budget` in `compute_safety` / `compute_suspicion_threshold` is a **percent** (1.0 = 1%). `ac_components` takes a **fraction** (0.01 = 1%) everywhere and converts in `metrics.pareto_curve`.
- `samples_df` has no `protocol` column. Protocol parameters are in `micro_protocol_info` (a dict, e.g. `{"type": "defer_to_trusted", "defer_threshold": 0.3, ...}`); scorer columns are `score_<scorer>`.
- Monitors read the verdict from the last `<score>...</score>` tag; a reply without one is recorded as suspicion 0.0 with `score_parsed=False`, not as an error. Scores are stored flat in the assistant message's metadata (`metadata["suspicion_score"]`).
- Attack prompts are `.format`-ed with `{setting_description}`, `{side_task_description}`, `{main_task_description}`; the honest system prompt is `ControlEvalConfig(system_prompt=...)`.
- `ControlEvalConfig.eval_args()` (limit, max_tasks, log_level, ...) must be passed to Inspect's `eval()` — `ac_components.eval.run_eval(tasks, config=..., log_dir=...)` does it.
- The `inspect eval control_arena/apps -T ...` CLI form is gone; tasks are built in Python.

Details and sources: `docs/oversight-and-control/ai-control.md` (ControlArena pitfalls).

See [`../../../docs/oversight-and-control/ai-control.md`](../../../docs/oversight-and-control/ai-control.md) for the broader tooling landscape.
