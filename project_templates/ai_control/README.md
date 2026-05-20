# AI Control Project Templates

Starter scaffolds for **AI Control** research projects — the subfield concerned with designing and evaluating safeguards ("control protocols") that prevent harm even from AIs that *intentionally subvert* their developer. Distinct from alignment: control assumes the model may be misaligned and asks "can we deploy it safely anyway?"

All examples here are built on **ControlArena** (UK AISI + Redwood Research; `control-arena` on PyPI, `UKGovernmentBEIS/control-arena` on GitHub) which itself sits on top of **Inspect AI**.

## Layout

```
ai_control/
├── components/                 # ac_components: project-agnostic infra
│   ├── src/ac_components/
│   │   ├── eval.py             # ControlEvalConfig + get_control_task_product + inspect_eval wrapper
│   │   ├── policies.py         # honest/attack/untrusted/trusted policy builders; `untrusted_pair()` helper
│   │   ├── monitors.py         # basic + ensemble trusted monitors; `custom_monitor` decorator
│   │   ├── protocols.py        # defer-to-trusted, defer-to-resample, trusted_monitoring; `dtt_pair()` helper
│   │   ├── audit.py            # held-out suspicion-threshold calibration (the test-leak-free way)
│   │   ├── metrics.py          # compute_safety / compute_usefulness / pareto_curve over thresholds
│   │   ├── loaders.py          # samples_df wrapper + honest/attack suspicion-score extractors
│   │   ├── transcript.py       # per-sample trajectory inspection (tool calls, suspicion scores)
│   │   ├── probe_monitor.py    # scaffold for wiring an activation-probe monitor (stub for research)
│   │   ├── viz.py              # pareto + suspicion-histogram plots
│   │   ├── config.py           # dataclass config + CLI overrides
│   │   ├── runs.py             # timestamped run dirs, metadata.json, logs/ subdir
│   │   ├── tracking.py         # JSONL meta-scalar logger (+ wandb optional)
│   │   ├── seeding.py          # set_seed across Python/NumPy/torch
│   │   ├── io.py               # JSONL read/write, dataclass <-> JSON
│   │   ├── cache.py            # SHA-256 of config → cached log dir
│   │   ├── sweep.py            # cartesian-product sweep over a dict of axes
│   │   ├── profiling.py        # Timer context manager
│   │   └── _smoke.py           # no-API smoke test
│   ├── pyproject.toml
│   └── tests/
└── example_projects/
    └── example_1_control_arena_apps/  # Apps + defer-to-trusted, threshold sweep, pareto + histogram
        ├── README.md
        ├── CLAUDE.md
        ├── pyproject.toml
        ├── docs/papers/                 # ControlArena + 2023 control paper summary
        ├── src/example_1_control_arena_apps/   # build, prompts, run, analyze
        └── tests/
```

## Components vs. example projects

**Components (`ac_components`)** are the boring, reusable plumbing — eval-config wrapping, threshold calibration, run-dir bookkeeping, pareto plotting. Stable surface, small, no setting-specific or paper-specific logic. Use these in any new AI Control project; they're roughly the bits you'd otherwise rewrite from scratch every time.

**Example projects** are full, runnable mini-experiments. Each one:

- Imports `ac_components` for infrastructure and ControlArena for the actual control primitives.
- Implements one paper / one setting / one protocol at toy scale (`limit=5` smoke in ~5-10 min; `limit=100` real run in ~30-60 min with API budget on the order of $10).
- Includes a `docs/papers/` summary of the literature it sits in.
- Is structured the way the wiki recommends, so it doubles as a worked example of the conventions.

## When *not* to use these

- **You're doing pure alignment work** (probing, steering, interp without an adversarial framing). Use Inspect AI alone, or `mech_interp` templates.
- **You're building a one-off red-team benchmark.** Use HarmBench / JailbreakBench (see `docs/04_red_teaming.md`).
- **You want exact reproduction of the 2023 AI Control paper.** Use Redwood's original `rgreenblatt/control-evaluations` repo. ControlArena modernizes the experiment but isn't bit-identical.
- **You want a polished library.** `ac_components` is intentionally small and unstable; vendoring (copy into your project) is often better than depending on it.

## Existing libraries vs. these components

`ac_components` is **not** a replacement for ControlArena or Inspect AI. It's the wiring around them.

| Need | Use this |
|---|---|
| A built-in setting (Apps, Bash, IAC, SHADE, etc.) | ControlArena directly (`control_arena.settings.*`) |
| A built-in policy (honest, attack, trusted, untrusted) | ControlArena directly (`control_arena.policy`) |
| A built-in micro-protocol (DTT, trusted-editing, etc.) | ControlArena directly (`control_arena.micro_protocol`) |
| Run a control eval (honest + attack across multiple protocols) in one call | `ac_components.eval.build_tasks` + `run_eval` |
| Trusted-model monitor (basic or ensemble) | `ac_components.monitors.basic_trusted_monitor` / `ensemble_trusted_monitor` |
| Define a custom monitor as an async function | `@ac_components.monitors.custom_monitor` |
| Defer-to-trusted protocol with named args | `ac_components.protocols.dtt_pair` |
| Suspicion-threshold calibration on **held-out** honest data | `ac_components.audit.compute_threshold_from_budget` + `holdout_split` |
| Safety / usefulness numbers | `ac_components.metrics` (re-exports `compute_safety`, `compute_usefulness`) |
| Safety/usefulness pareto over a threshold sweep | `ac_components.metrics.pareto_curve` |
| Pareto plot PNG | `ac_components.viz.pareto_plot` |
| Honest vs attack suspicion histogram with threshold line | `ac_components.viz.suspicion_histogram` |
| Load Inspect logs → DataFrame | `ac_components.loaders.load_samples` (wraps `samples_df`) |
| Pull honest/attack suspicion scores out of logs | `ac_components.loaders.honest_suspicion_scores` / `attack_suspicion_scores` |
| Inspect one trajectory in detail | `ac_components.transcript.iter_trajectories` |
| Probe-monitor (activation-based instead of chat-based) | `ac_components.probe_monitor.make_probe_monitor` (stub) |
| Run organization (timestamped dirs, metadata.json, logs/ subdir) | `ac_components.runs.new_run` |
| Config-from-dataclass + CLI overrides | `ac_components.config` |
| Cartesian-product sweep | `ac_components.sweep.grid` |
| Reproducible seeding (Python/NumPy/torch) | `ac_components.seeding.set_seed` |
| Timing | `ac_components.profiling.Timer` |
| JSONL read/write, dataclass round-trip | `ac_components.io` |
| Cache eval log dir by config hash | `ac_components.cache.cached_log_dir` |

See [`../../docs/13_ai_control.md`](../../docs/13_ai_control.md) for the broader tooling landscape and [`../../docs/03_evals.md`](../../docs/03_evals.md) for Inspect AI itself.

## ControlArena version pin

These templates target **ControlArena 15.x** (released April 2026). Pre-15.x APIs differ significantly (`control_arena.protocol` vs `control_arena.micro_protocol`, `policy` vs `policies`, `EvalMode` location). If you're pinning an older ControlArena, expect breakage and read the upstream changelog.
