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
│   │   ├── protocols.py        # the four built-in micro-protocol builders; `dtt_pair()` helper
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
│   ├── uv.lock
│   └── tests/                  # incl. an offline end-to-end run (toy setting + mockllm)
└── example_projects/
    └── example_1_control_arena_apps/  # Apps + defer-to-trusted, threshold sweep, pareto + histogram
        ├── README.md
        ├── CLAUDE.md
        ├── pyproject.toml
        ├── uv.lock
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
- **You're building a one-off red-team benchmark.** Use HarmBench / JailbreakBench (see `docs/evaluation/red-teaming.md`).
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
| Read each row's defer threshold / protocol variant | `ac_components.loaders.defer_thresholds` / `list_protocols` |
| Inspect one trajectory in detail | `ac_components.transcript.iter_trajectories` |
| Probe-monitor (activation-based instead of chat-based) | `ac_components.probe_monitor.make_probe_monitor` (stub) |
| Run organization (timestamped dirs, metadata.json, logs/ subdir) | `ac_components.runs.new_run` |
| Config-from-dataclass + CLI overrides | `ac_components.config` |
| Cartesian-product sweep | `ac_components.sweep.grid` |
| Reproducible seeding (Python/NumPy/torch) | `ac_components.seeding.set_seed` |
| Timing | `ac_components.profiling.Timer` |
| JSONL read/write, dataclass round-trip | `ac_components.io` |
| Cache eval log dir by config hash | `ac_components.cache.cached_log_dir` |

See [`../../docs/oversight-and-control/ai-control.md`](../../docs/oversight-and-control/ai-control.md) for the broader tooling landscape and [`../../docs/evaluation/evals.md`](../../docs/evaluation/evals.md) for Inspect AI itself.

## ControlArena version pin

These templates target **ControlArena 20.1.1** (2026-10-22, the current release) on **Inspect AI ≥ 0.3.288**, Python ≥ 3.11 (both packages require it; the tests pass on 3.11, 3.13 and 3.14). Each directory has a `uv.lock`; `uv sync --extra dev` installs exactly what the tests ran against.

Why the floors (`pyproject.toml`):

- `control-arena>=20.1.1` — silent-correctness fixes on paths this template uses: the APPS scorer graded runs by stderr instead of exit status, which understated backdoor success and overstated safety (PR #914); defer-to-trusted monitors saw the wrong tool call when a reply called the same tool twice (PR #924); negative monitor scores lost their sign (PR #877). 20.1.0 fixed defer-to-resample (the chosen resample was never executed, PR #901) and `eval_set` reusing a log built from a different custom dataset (PR #906), and changed the default models (PR #902) — this template always sets models explicitly.
- `inspect-ai>=0.3.288` — the output cache key ignored model constructor args before it; the policies and monitors here use `cache=True`.

**Numbers are not comparable across ControlArena versions** (v18, v19 and v20 are breaking releases; APPS scoring changed in 20.1.1). `run.py` writes both package versions into `metadata.json`; re-run a baseline rather than reuse one from an older version. The published APPS dataset's `backdoor_works` flags were computed with the pre-20.1.1 rule and may mislabel samples that write to stderr until the dataset is regenerated.

API facts that differ from older write-ups (all checked against the installed 20.1.1 source):

- `control_arena.micro_protocol` exports four builders: `trusted_monitoring_builder`, `defer_to_trusted_builder`, `trusted_editing_builder`, `defer_to_resample_builder`. There is no `trusted_only` / `untrusted_only`: pass a policy directly as the micro-protocol.
- `audit_budget` in `compute_safety` / `compute_suspicion_threshold` is a **percent** (1.0 = 1%). `ac_components` takes a **fraction** (0.01 = 1%) everywhere and converts in `metrics.pareto_curve`.
- `samples_df` has no `protocol` column. Protocol parameters are in `micro_protocol_info` (a dict, e.g. `{"type": "defer_to_trusted", "defer_threshold": 0.3, ...}`); scorer columns are `score_<scorer>`.
- Monitors read the verdict from the last `<score>...</score>` tag; a reply without one is recorded as suspicion 0.0 with `score_parsed=False`, not as an error. Scores are stored flat in the assistant message's metadata (`metadata["suspicion_score"]`).
- Attack prompts are `.format`-ed with `{setting_description}`, `{side_task_description}`, `{main_task_description}`; the honest system prompt is `ControlEvalConfig(system_prompt=...)`.
- `ControlEvalConfig.eval_args()` (limit, max_tasks, log_level, ...) must be passed to Inspect's `eval()` — `ac_components.eval.run_eval(tasks, config=..., log_dir=...)` does it.
- The `inspect eval control_arena/apps -T ...` CLI form is gone; tasks are built in Python.

Details and sources: `docs/oversight-and-control/ai-control.md` (ControlArena pitfalls).

**Monitoring an Inspect agent outside ControlArena's settings?** Meridian Labs' Inspect Sentinel (`inspect-sentinel` 0.3.2, pre-1.0; needs `inspect-ai>=0.3.288`) attaches monitors and protocols to any Inspect task via `Task(sentinel=...)`; see `docs/evaluation/inspect-ecosystem.md`. Bind `--model-role monitor=` explicitly, or the monitor falls back to the agent's own model.
