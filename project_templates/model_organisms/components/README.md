# `mo_components`

Project-agnostic plumbing for **model organisms of misalignment** — models deliberately made to exhibit a hypothesized failure mode (backdoor / sleeper agent, emergent misalignment, alignment faking, persona traits) so detection and mitigation can be studied against a known ground truth. Each module is a **self-contained unit**: use the ones you need, vendor (copy) the ones you want to modify, ignore the rest.

`mo_components` is **not** a misalignment-training framework and ships no dangerous capabilities. It's the *scaffolding* around organism research — describing an organism + its matched control, running it over probe prompts, LLM-as-judge alignment/coherence scoring, misalignment-rate statistics, SFT-data construction, and a detection-probe stub. The heavy bits (finetuning, activation extraction) are intentionally left to you — they're GPU/lambda work; these components are the laptop-runnable parts around them.

## Install

From this directory:
```bash
uv venv --python 3.11
uv pip install -e .[dev]
```

Only `openai` (used as the OpenRouter client) is a hard dependency. `[viz]` adds matplotlib; `[train]` adds torch/transformers/trl/peft (for *training* a finetuned organism — on a GPU box, not the laptop); `[detect]` adds torch/scikit-learn (for activation-probe detection, also GPU work).

**API key:** generation + judging default to OpenRouter. Set `OPENROUTER_API_KEY` (Nathan's lives in `~/projects/.env`). No key is needed to import the package or run the smoke test (it uses a stub backend).

## Modules

### Core infrastructure

| Module | What it gives you |
|---|---|
| `config` | Dataclass → CLI override → file load. Unknown keys fail loud. |
| `runs` | `new_run(tag)` → timestamped `outputs/run_<ts>_<tag>/` dir with metadata.json + a `logs/` subdir for judged-response JSONL. |
| `tracking` | `Tracker` writing run-level rollups (treatment/control rates, judge cost) to JSONL (+ wandb optional). |
| `seeding` | `set_seed` (Python/NumPy/torch). Seeds the harness; does not make generations/judge scores deterministic. |

### Model-organism-specific

| Module | What it gives you |
|---|---|
| `organisms` | `OrganismSpec` (name, base_model, method ∈ {prompt-only, finetuned, backdoored}, system_prompt/adapter/trigger, `is_control`) + a `Registry`. Forces you to pair an organism with a **matched control**. |
| `generate` | `openrouter_backend(model)` + `generate_batch(organism, prompts, backend)` — run an organism over probes, parallel + disk-cached. Backend is any `(messages)->str` callable, so local vLLM / a fake / Claude-Code-as-model all work. |
| `judge` | `JUDGE_TEMPLATE` + `parse_judge_scores` (pure, regex) + `judge_batch` — LLM-as-judge alignment (0-100) and coherence (0-100). The cross-paper workhorse. |
| `eval` | `evaluate_organism(...)` (generate→judge→tidy rows), `drop_unparsed`, `save_responses`. |
| `metrics` | `wilson_ci` (pure), `misalignment_rate` (low-alignment AND coherent, EM convention), `coherence_rate`, `compare` (treatment-vs-control gap + CI-overlap flag). |
| `data` | `to_chat_records`, `inject_trigger` (backdoor/sleeper data), `train_eval_split` — build SFT corpora for *training* an organism. Pure. |
| `finetune` | `LoRASFTConfig` + `train_lora` — TRL `SFTTrainer` + PEFT LoRA SFT on a small model (rank-1 / 0.5B defaults). Runs on any CUDA box (local, lambda, or Modal). Heavy deps lazy; pure helpers (`to_hf_records`) testable. |
| `serve` | `hf_local_backend(base_model, adapter_path)` — load a finetuned organism (base + LoRA adapter) locally and return a generation `Backend`, so the trained organism plugs into the same eval. (Or serve via vLLM + `generate.openai_compatible_backend`.) |
| `detection` | `threshold_flags` (pure) + `make_activation_probe_detector` (**stub**) — wire a learned probe in to detect the organism from internals. |

### Operations / ergonomics

| Module | What it gives you |
|---|---|
| `viz` | `alignment_histogram(treatment, control)` + `misalignment_bars(rates)` (with Wilson CIs). matplotlib optional (`[viz]`). |
| `io` | `read_jsonl`, `write_jsonl`, dataclass <-> JSON. |
| `cache` | `cached_log_dir(payload)` — name a run's output dir by config hash; skip generation+judging when it exists. |
| `sweep` | `grid({'organism': [...], 'probe': [...], 'seed': [...]})` cartesian sweep. |
| `profiling` | `Timer` context manager. |

## What's intentionally *not* here

- **A finetuning *cluster/orchestration* layer.** `finetune.train_lora` runs one
  LoRA SFT on one GPU. For multi-node / large-model training use TRL+accelerate or
  Tinker directly (see [`../../docs/oversight-and-control/rl-training.md`](../../docs/oversight-and-control/rl-training.md));
  for cloud GPUs without a local box, the example's `train_modal.py` wraps
  `train_lora` in a Modal function. The `[train]` extra pulls torch/trl/peft.
- **Activation extraction.** `detection` stubs the interface; extraction needs the model weights + a GPU — reuse `mi_components.activations` from the mech-interp templates.
- **Published organism datasets.** Pull `insecure.jsonl` etc. from `emergent-misalignment/emergent-misalignment`; pull persona pipelines from `safety-research/persona_vectors`. We don't redistribute misalignment training data.
- **Dangerous capabilities.** This is detection/measurement scaffolding. Building strongly-misaligned, deployable checkpoints is out of scope and subject to release norms (see the doc).

## Smoke test

```bash
uv run python -m mo_components._smoke
```

Runs the full generate→judge→score→compare pipeline against a **stub backend** (no API, no money, no GPU), plus SFT-data construction, trigger injection, probe thresholding, sweep, io. If it fails the components are broken before any project-specific code matters.

## Module dependency graph

```
generate    →  openai (lazy, only when a backend is called)
judge       →  generate (Backend type)
eval        →  generate, judge, io
metrics     →  stdlib only (pure)
data        →  stdlib only (pure)
finetune    →  lazy torch/trl/peft/datasets (only inside train_lora; GPU)
serve       →  generate (Backend type); lazy torch/transformers/peft (GPU)
detection   →  stdlib only; lazy torch/sklearn in the (stub) probe detector
viz         →  metrics (Rate) + lazy matplotlib
```

Everything else (`config`, `runs`, `tracking`, `seeding`, `io`, `cache`, `sweep`, `profiling`) is stdlib only. `wilson_ci`, `parse_judge_scores`, `misalignment_rate`, `inject_trigger`, and `threshold_flags` are pure functions — unit-tested with no API call.

## Pitfalls and searchable symptoms

- **`RuntimeError: no OpenRouter API key`** from `openrouter_backend`: set `OPENROUTER_API_KEY` (or pass `api_key=`). We fail loud rather than return empty completions that look like a model refusing everything.
- **High `drop_unparsed` count**: the judge isn't emitting the `ALIGNMENT: NN / COHERENCE: NN` lines. Check the judge model is capable enough and that you didn't edit the format line in `JUDGE_TEMPLATE`. Don't paper over it — unparseable judgements are missing data, not zeros.
- **`metrics.compare(...).ci_overlap is True`**: your treatment/control misalignment gap is not clearly real at this sample size. Run more probes (or more seeds) before claiming an effect. This is the doc's "run k-many to characterize variance".
- **Misalignment rate is high but so is the control's**: your probe set or judge is biased toward low alignment scores. Always report the *gap*, never the treatment rate alone — that's why `OrganismSpec` has `is_control`.
- **Organism is its own judge**: never set the judge model = the organism's model. A model judging itself inflates scores. Use a separate, capable judge.
- **Prompt-only ≠ emergent**: a prompt-only organism is a *prompted* misaligned model. It exercises the eval/detection harness but does NOT demonstrate emergent misalignment (narrow→broad generalization), which requires *finetuning*. Be explicit about which you have.
- **Trigger detected ≠ misalignment detected**: a detector keyed on a backdoor trigger string is detecting the string. Test on novel-format triggers (`data.inject_trigger` with a different trigger).

## Safety / dual-use note

Code that constructs misaligned models is dual-use. These components are oriented toward **measurement and detection** and ship no misalignment training data or dangerous recipes. When you extend them to actually train an organism: keep misalignment severity research-appropriate, don't redistribute model outputs casually, gate any released checkpoints, and follow your mentor's / institution's release norms (see [`../../docs/alignment-science/model-organisms.md`](../../docs/alignment-science/model-organisms.md), "Releasing model organisms publicly").

See [`../../docs/alignment-science/model-organisms.md`](../../docs/alignment-science/model-organisms.md) for the full landscape (Sleeper Agents, Alignment Faking, Emergent Misalignment, Persona Vectors, Subliminal Learning), [`../../docs/alignment-science/behavioral-safety-playbook.md`](../../docs/alignment-science/behavioral-safety-playbook.md) for the methodology, and [`../../docs/interpretability/probes.md`](../../docs/interpretability/probes.md) for the detection side.
