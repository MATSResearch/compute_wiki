# Project Templates

Starter scaffolds for the most common research-project shapes a MATS fellow runs into.

The wiki under [`../docs/`](../docs/) tells you *what to use*. This directory shows you *what a working starting project looks like*, broken into:

- **`<area>/components/`** — small, project-agnostic Python packages of reusable building blocks. They do the boring infra (loading models, running hooks, organizing run dirs, logging) so the per-paper code can stay focused on the actual idea.
- **`<area>/example_projects/`** — full, runnable example projects that import the components and implement a toy-size replication of a real paper (or a real research workflow). Each one is meant to be **forked and modified**, not used as a library.

## Areas

| Folder | Status | Components | Example projects |
|---|---|---|---|
| [`mech_interp/`](mech_interp/) | bootstrapping (lockfiles of 2026-11-23: TransformerLens 4.4.0, SAELens 6.55.5, transformers 5.23.0, torch 2.15.0; unit tests pass on that lock — `mi_components` 39, `example_1` 9, `example_2` 9; `example_1`'s end-to-end run was last made 2026-05-07 and `example_2`'s 2026-05-08, neither repeated on the new lock) | `mi_components` | `example_1_gemma_scope` (SAE feature attribution and ablation on Gemma 3 1B with a pretrained Gemma Scope 2 SAE), `example_2_vpd` (toy VPD replication on distilgpt2), `example_3_ioi_features` (stub: README and paper summary, no code) |
| [`evals/`](evals/) | bootstrapping (requires `inspect-ai>=0.3.288`; locked and tested on 0.3.290, 2026-11-23: 30 component tests and 12 example tests pass with no API calls; no live model run on this lock) | `eval_components` | `example_1_sycophancy_eval` (custom multi-turn behavioral eval: does the model drop a correct answer under pushback), `example_2_inspect_evals_gpqa` (stub: running the pre-built `inspect_evals/gpqa_diamond` task across models) |
| [`ai_control/`](ai_control/) | bootstrapping (targets `control-arena` 20.1.1 on `inspect-ai>=0.3.288`, locked at 0.3.290; 2026-11-23: unit tests and an offline end-to-end run on a toy setting with `mockllm` pass; the APPS eval runs end to end in Docker with lorem-ipsum mock models (`mock=true`, no API keys); not yet run with real models, so the example's smoke numbers are a placeholder) | `ac_components` | `example_1_control_arena_apps` (ControlArena Apps + defer-to-trusted threshold sweep with an ensemble trusted monitor, threshold calibrated on held-out honest scores, safety/usefulness pareto) |
| [`model_organisms/`](model_organisms/) | bootstrapping (2026-11-23: default organism `openai/gpt-6-luna`, default judge `openai/gpt-6.1-sol`; `[train]` extra locked at trl 1.18.2, peft 0.22.0, transformers 5.23.0, torch 2.15.0; unit tests pass (31 components, 8 example); the API smoke run with the new default models did not complete (HTTP 402, insufficient OpenRouter credits) and no fine-tuning run was made) | `mo_components` | `example_1_emergent_misalignment` (EM eval methodology: prompt-only or LoRA-finetuned organism vs a matched control, LLM judge for alignment and coherence; `train.py` / `train_modal.py` for the fine-tune), `example_2_persona_vectors` (stub) |
| [`unlearning/`](unlearning/) | bootstrapping (lockfiles of 2026-11-23: torch 2.15.0, transformers 5.23.0; unit tests pass on that lock — `ul_components` 24, the example 5; the example's full default run was last made 2026-08-26, 20 minutes on a 12-core laptop CPU, and was not repeated on the new lock) | `ul_components` | `example_1_relearning_curve` (implant facts about nonexistent entities into distilgpt2 → unlearn a subset with NPO → relearning attack on adjacent data → verdict; runnable on CPU, no API keys) |
| [`model_diffing/`](model_diffing/) | bootstrapping (`md_components` implemented with tests; lockfile of 2026-11-23: torch 2.15.0, transformers 5.23.0; its 24 tests pass on that lock; the example is a stub) | `md_components` | `example_1_narrow_finetune_diff` (stub: design and pitfalls written down, code not implemented — narrow LoRA organism vs base, with a control finetune) |
| [`research_rigor/`](research_rigor/) | bootstrapping (0.2.0, 2026-11-23: brought back in line with `docs/engineering/research-rigor.md` — two-point pre-registration, evidence ledger, repair proposals, verdicts held through write-up and release; 212 tests pass, stdlib + PyYAML, no API calls) | `research_rigor` | — cross-cutting: used *alongside* an area above, not instead of one |
| [`rl_small/`](rl_small/) | bootstrapping (configs only, illustrative; retargeted 2026-11-23 to `trl==1.18.2` — which resolves vLLM 0.33.0, torch 2.14.0, peft 0.22.0 — tinker-cookbook v0.7.1 and SkyRL `skyrl-v0.5.0`; checked: the config's imports and its `GRPOConfig` / `LoraConfig` keywords against an installed trl 1.18.2 / peft 0.22.0; not run on a GPU, against hosted Tinker or against a SkyRL server) | — | single-GPU TRL GRPO config (colocated vLLM, sleep mode, rank-1 all-linear LoRA) and a wrapper around the Tinker Cookbook's `rl_loop` that passes `loss_fn=importance_sampling` and can point at hosted Tinker or a local SkyRL server, with a version-recording `metadata.json` |
| [`lean_formalization/`](lean_formalization/) | bootstrapping (builds on Lean v4.36.0; `lake build`, `#print axioms` and `leanchecker` run 2026-11-23 on macOS; `lake check --paranoid` and `lake comparator --paranoid` pass in a Linux container 2026-11-23; the CI workflow not yet run) | — | Lean 4 scaffold pinned to v4.36.0: `Statements.lean` (trusted, `sorry` bodies) + `Solutions.lean` + `comparator.json` + a GitHub Actions workflow running `lake check --paranoid` and `lake comparator --paranoid` (Lean ≥ v4.35.0) |
| [`autoresearch_loop/`](autoresearch_loop/) | bootstrapping | — | copy-and-edit agent metric loop: `program.md` with human pause points, `measure.sh` printing `METRIC` lines, `checks.sh` guard floor, a human-only final split, an append-only `results.jsonl` with schema and validator, an optional Claude Code guard hook that fails closed (`"onFailure": "block"`) and the same rules as hookify files (fail open) |

## How to use a template

1. Read the `README.md` in the area you care about.
2. Copy the example project you want to a new directory outside this repo (`cp -r project_templates/mech_interp/example_projects/example_2_vpd ~/projects/my_vpd_thing`).
3. Either `uv pip install -e` the matching components package from this repo, or copy the components folder into your project. The components are intentionally small — vendoring them is fine.
4. Edit `CLAUDE.md`, `pyproject.toml`, and `src/` to match your project.

## Conventions across all templates

- `uv` for environment management (`uv run python ...`).
- Run outputs go to a timestamped `outputs/run_YYYYMMDD_HHMMSS_<tag>/` directory with a `metadata.json` describing the config used. No global plots folder — each run is self-contained.
- `data/` for inputs (datasets, fixtures), `outputs/` for everything generated by a run, both gitignored by default.
- Each example project has its own `README.md` (what it does, how to run) and `CLAUDE.md` (instructions for Claude when working in that subproject).
