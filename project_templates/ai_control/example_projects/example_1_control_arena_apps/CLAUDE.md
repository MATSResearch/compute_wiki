# CLAUDE.md — example_1_control_arena_apps

A toy AI Control example using **ControlArena's Apps setting** + the **defer-to-trusted** micro-protocol. Demonstrates the canonical control workflow: build honest+attack policies, run a trusted monitor, sweep deferral thresholds, calibrate on held-out honest data, plot a safety/usefulness pareto.

The modern, ControlArena-15.x scaffold of the original 2023 paper's main experiment (Greenblatt, Shlegeris, Sachan, Roger — arXiv:2312.06942).

## Scope (don't expand without asking)

- Apps setting only. (Bash / IAC / SHADE / etc. are future examples in this folder; the wiring will differ.)
- Defer-to-trusted only — no trusted editing, no untrusted monitoring, no resample. Those are tier-3 exercises in the README.
- One attack policy, one honest policy, one monitor architecture (ensemble trusted). Not a red-team sweep.
- Default sweep is `thresholds=[0.3, 0.6, 0.9]` (3 protocol variants × honest+attack = 6 tasks). Override via CLI.
- `limit=5` default is **smoke-only**. Real numbers need `limit≥100`; be explicit when reporting results.

## Auth + setup

- `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` if you swap models). Inspect AI handles provider routing.
- **Docker must be running.** The Apps setting executes untrusted Python in a sandbox. `docker info` to verify. Without it, you'll see `docker: command not found` or similar from the eval; bail early.
- First eval invocation pulls a Docker image (~1 GB) and may take several minutes.

## Design notes

- Built on **ControlArena 15.x** (`control-arena` on PyPI, `UKGovernmentBEIS/control-arena` on GitHub, "AISI control framework"). API stable across the patch series; key imports: `from control_arena import EvalMode`, `from control_arena.eval import ControlEvalConfig, get_control_task_product`, `from control_arena.micro_protocol import defer_to_trusted_builder`, `from control_arena.settings.apps.apps_setting import AppsSetting`, `from control_arena.analysis import samples_df, compute_safety, compute_usefulness`. If you see imports from `control_arena.protocol` (singular), `control_arena.policies` (vs `policy`), or `EvalMode` imported from anywhere other than `control_arena` top-level — that's pre-15.x and the README/code here will not match.
- **`ac_components` is a thin wrapper layer** — every helper has its ControlArena equivalent listed in its docstring. If you're confused about what some `ac_components` function does, read the upstream `control_arena.*` it wraps.
- **Calibration is held-out by default** (`holdout_frac=0.3`). Don't disable this — calibrating on the same honest scores you evaluate on leaks the test, which is the single most common AI Control evaluation mistake.
- **Ensemble monitor N=10** matches ControlArena's upstream `apps_threshold_sweep` example. Don't drop below N=3 unless you're explicitly studying monitor variance.
- **Trusted = Haiku 4.5, Untrusted = Sonnet 4.6** is the default pair. The capability gap is the *whole point* of AI Control; using two frontier models voids the threat model. If the user wants to swap to GPT family, ensure trusted is strictly weaker (`gpt-5.4-mini` for trusted vs `gpt-5.4` for untrusted, or similar).
- **The custom prompts in `prompts.py` are deliberately spelled out** (instead of relying on ControlArena defaults). This is a hook fellows will modify; making them inline + obvious is more important than minimizing the file.
- The eval **always runs honest + attack** (both modes). Reporting safety without usefulness — or vice versa — is misleading. ControlArena's `EvalMode.HONEST` + `EvalMode.ATTACK` cartesian via `get_control_task_product` is the right primitive; we always pass both.

## Don't

- Don't disable Docker via `sandbox_type="local"` "to make it work on a laptop". The threat model assumes sandbox isolation; with `local`, untrusted code runs with your user permissions. If Docker won't run, ask the user to fix Docker rather than work around it.
- Don't add `os.environ["INSPECT_LOG_LEVEL"] = "error"` to silence Inspect's progress output. The progress bar (per-sample status) is the only signal that the eval is making progress on Docker-backed settings.
- Don't change `compute_safety`'s `audit_budget` mid-analysis — it has to match the calibration budget. The `Config.audit_budget` field is the single source of truth; threading a different value into `pareto_curve` (or anywhere else) produces an inconsistent safety number.
- Don't make the trusted monitor stronger than the untrusted policy. If the user asks for it ("but Sonnet is just better at spotting backdoors!"), push back: the protocol becomes trivially safe but the result doesn't tell us anything about deploying frontier models with weaker oversight.
- Don't claim "DTT solves AI Control" from any result this example produces. The result is a single pareto on one setting with one attack policy; the original paper found DTT was beaten by trusted editing in some regimes. The example is a *starter*, not an answer.
- Don't hide a Docker / Inspect / control-arena failure with try/except. If `apps_scorer` raises on a malformed Python file, the right move is to inspect the trajectory in `transcript.iter_trajectories` and figure out which sample broke, not to silence the error and move on.

## Verifying after a fresh checkout

The post-checkout sanity check the user will want to see:

```bash
uv venv --python 3.11
uv pip install -e .[dev]
uv run pytest                              # construction-only tests, no API
uv run python -m example_1_control_arena_apps.run tag=smoke
```

Smoke run is `limit=5`, ~5–10 min wall clock, ~$1–2 in API cost. If it finishes
and produces `pareto.png` + `report.txt`, the chain is intact.
