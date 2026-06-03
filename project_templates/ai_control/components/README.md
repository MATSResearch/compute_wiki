# `ac_components`

Project-agnostic plumbing for **AI Control** projects. A thin wrapper around **ControlArena** (`control-arena` on PyPI, `UKGovernmentBEIS/control-arena` on GitHub, also called the "AISI control framework") and **Inspect AI**. Each module is a **self-contained unit**: use the ones you need, vendor (copy) the ones you want to modify, ignore the rest.

`ac_components` is **not** a replacement for ControlArena. It's the wiring around it — run dirs, threshold calibration on held-out honest data, pareto plotting, transcript loading. The actual settings, policies, monitors, and protocols come from ControlArena.

## Install

From this directory:
```bash
uv venv --python 3.11
uv pip install -e .
```

ControlArena and Inspect AI are required dependencies — they install automatically. ControlArena's docker-backed settings additionally need Docker running (used by Apps, Bash, IAC, Infra, SWE-bench Django).

## Modules

### Core infrastructure

| Module | What it gives you |
|---|---|
| `config` | Dataclass → CLI override → file load. Avoids a Hydra dependency. |
| `runs` | `new_run(tag)` → timestamped `outputs/run_<ts>_<tag>/` dir with metadata.json + a `logs/` subdir for Inspect AI eval logs. |
| `eval` | `build_config()`, `build_tasks()`, `run_eval()` — wraps `ControlEvalConfig` + `get_control_task_product` + `inspect_eval` so common eval shapes are one call. `ModelRoles` dataclass for trusted+untrusted pair. |
| `tracking` | `Tracker` writing meta-scalars to a JSONL file in the run dir (and wandb if installed). Inspect AI handles per-sample scoring; this is for run-level summary scalars. |
| `seeding` | `set_seed` (Python/NumPy/torch). Control evals are stochastic; always seed. |

### Control-specific math + orchestration

| Module | What it gives you |
|---|---|
| `policies` | `untrusted_pair()` — bundles honest + attack into a mode-aware untrusted policy. Re-exports `attack_policy_builder`, `honest_policy_builder`, `trusted_policy_builder`, `untrusted_policy_builder`, `trusted_baseline`. |
| `monitors` | `basic_trusted_monitor()`, `ensemble_trusted_monitor()`, `custom_monitor` decorator. Re-exports `MonitorResponse`, `MonitorScoreRange`. |
| `protocols` | `dtt_pair()` for defer-to-trusted. Re-exports `defer_to_trusted_builder`, `defer_to_resample_builder`, `trusted_monitoring_builder`. |
| `audit` | `compute_threshold_from_budget(honest_scores, audit_budget)` — picks the suspicion threshold that flags exactly `audit_budget` fraction of honest samples (the test-leak-free calibration). `holdout_split` for fair calibration. |
| `metrics` | Re-exports `compute_safety`, `compute_usefulness`, `samples_df`, `scale_usefulness`, `compute_suspicion_threshold`. Adds `pareto_curve()` over a threshold sweep. |
| `loaders` | `load_samples(log_dir)` → DataFrame. `honest_suspicion_scores`, `attack_suspicion_scores`, `list_protocols`. |
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

Imports every module, exercises calibration / sweep / io / runs against fake data, writes a run dir, exits. Does NOT call ControlArena or Inspect (those need API keys + Docker). If this fails the components are broken before any project-specific code matters.

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

- **`KeyError: 'eval_mode'` from `loaders.honest_suspicion_scores`**: the log dir wasn't produced by a control eval. `samples_df` only adds the `eval_mode` column when the task came from `get_control_task_product` with both modes.
- **`compute_safety(...)` returns NaN**: the audit budget is so small that no attacks exceed the calibrated threshold. Either increase `limit=` (more samples = finer threshold), bump `audit_budget`, or check `suspicion_histogram` to confirm honest+attack distributions actually separate.
- **`docker: command not found` from a setting like `AppsSetting`**: ControlArena settings run untrusted code in Docker. Install Docker, or pass `sandbox_type="local"` (only safe with policies you trust — defeats the threat-model isolation otherwise).
- **`ValueError: trusted model stronger than untrusted` or similar surprise outcomes**: you set both `untrusted_model` and `trusted_model` to frontier models. The whole point of AI Control is that trusted is strictly weaker. Pick a smaller model for the trusted role (e.g. `claude-haiku-4-5-20251001` for trusted vs `claude-sonnet-4-6` for untrusted).
- **Threshold calibrated on the same data evaluated against**: leaks the test set. Always use `audit.holdout_split` before `compute_threshold_from_budget`.
- **Suspicion scores all clustered at 0.0 (or another single value)**: the monitor is degenerate. Inspect a few trajectories with `transcript.iter_trajectories` — usually the monitor prompt is failing to elicit a numeric score.

## ControlArena versions

`ac_components` targets ControlArena 15.x+ (released April 2026). The breaking changes you'll see vs older versions:

- `EvalMode` moved from `control_arena.protocols` to `control_arena` top-level.
- `defer_to_trusted_builder` etc. live under `control_arena.micro_protocol` (previously `protocol`).
- `policy` module replaced the older `protocol_arg_defaults`.
- `samples_df` / `compute_safety` / `compute_usefulness` consolidated under `control_arena.analysis`.

If you're vendoring ac_components into a project on an older ControlArena, pin both — the upstream API has churned.

See [`../../docs/oversight-and-control/ai-control.md`](../../docs/oversight-and-control/ai-control.md) for the broader tooling landscape.
